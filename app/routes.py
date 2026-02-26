import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ReverseImageRequest, UploadResponse
from app.services.generator_service import GeneratorService

router = APIRouter(prefix="/api", tags=["Images"])

STORAGE_PATH = os.getenv("APP_STORAGE_BASE_PATH", "storage")


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
            db=db, storage_path=STORAGE_PATH
        ).process_uploaded_image(contents)

        return result

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@router.post("/api/reverse/{modification_id}")
async def reverse_modification(
    modification_id: int,
    body: ReverseImageRequest,
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    Reverse a specific modification by ID and save the result to the reverses folder.

    Args:
        modification_id: ID of the modification to reverse

    Returns:
        JSON response with the path to the reversed image
    """
    try:
        result = GeneratorService(
            db=db, storage_path=STORAGE_PATH
        ).reverse_modification(
            modification_id=modification_id,
            should_save_reversed_img=body.should_save_reversed_img,
        )
        return JSONResponse(result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reversing modification: {str(e)}"
        )
