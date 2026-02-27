import os
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session, joinedload, load_only

from app.database import get_db
from app.models import DBImageModification
from app.schemas import (
    ModificationResponse,
    ReverseImageRequest,
    ReverseModificationResponse,
    UploadResponse,
)
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


@router.post("/reverse/{modification_id}", response_model=ReverseModificationResponse)
async def reverse_modification(
    modification_id: int,
    body: ReverseImageRequest,
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    Reverse a specific modification by ID
    and optionally save the result to the reversed folder.
    """
    try:
        result = GeneratorService(
            db=db, storage_path=STORAGE_PATH
        ).reverse_modification(
            modification_id=modification_id,
            should_save_reversed_img=body.should_save_reversed_img,
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reversing modification: {str(e)}"
        )


@router.get("/modifications", response_model=list[ModificationResponse])
async def get_modifications(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = Query(None),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """Get list of modifications."""
    print(status)
    query = db.query(DBImageModification).options(
        load_only(
            DBImageModification.id,
            DBImageModification.image_id,
            DBImageModification.modified_image_path,
            DBImageModification.num_modifications,
            DBImageModification.verification_status,
            DBImageModification.created_at,
            DBImageModification.verified_at,
        ),
        joinedload(DBImageModification.image),
    )

    if status:
        query = query.filter(DBImageModification.verification_status == status)

    modifications = query.offset(skip).limit(limit).all()

    return modifications
