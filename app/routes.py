import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import UploadResponse
from app.services.generator_service import GeneratorService

router = APIRouter(prefix="/api", tags=["Images"])


@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...), db: Session = Depends(get_db)  # noqa: B008
):
    """
    Accept an image file and generate 100 variants with random modifications.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        contents = await file.read()

        result = GeneratorService(
            os.getenv("APP_STORAGE_BASE_PATH", "storage")
        ).process_uploaded_image(contents, db)

        return result

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
