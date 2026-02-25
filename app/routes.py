import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from app.database import get_db
from app.service import Service

router = APIRouter(prefix="/api", tags=["Images"])


@router.post(
    "/modify",
)
def modify_image(
    name: str = Form(...),  # noqa: B008
    image: UploadFile = File(...),  # noqa: B008
    variants: int = Form(100, ge=1, le=100),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    img = Image.open(image.file)

    service = Service(db, os.getenv("APP_STORAGE_BASE_PATH", "storage"))

    try:
        service.modify_image(img, name, variants)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "data": {
            "message": "modified",
        }
    }
