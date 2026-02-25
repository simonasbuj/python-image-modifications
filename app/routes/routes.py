import os
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.services.database import get_db
from app.services.storage import Storage

router = APIRouter(prefix="/api", tags=["Users"])

storage = Storage(os.getenv("APP_STORAGE_BASE_PATH", "storage"))


@router.post(
    "/modify",
)
def modify_image(
    name: str = Form(...),  # noqa: B008
    image: UploadFile = File(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    print(f"Received file: {image.filename}")
    ext = Path(image.filename).suffix.lower()
    saved_img_path = storage.save(image.file, f"{name}/og{ext}")
    return {
        "data": {
            "message": "modified",
            "filename": image.filename,
            "saved_path": saved_img_path,
        }
    }


@router.post(
    "/validate",
)
def validate_image(filename: str, db: Session = Depends(get_db)):  # noqa: B008
    try:
        image_data = storage.get(filename)
        ext = filename.split(".")[-1].lower()
        content_type = f"image/{ext if ext != 'jpg' else 'jpeg'}"
        return Response(content=image_data, media_type=content_type)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Image not found")
