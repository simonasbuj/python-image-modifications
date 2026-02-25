import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from PIL import Image

from app.database import get_db
from app.models import DBImage, DBImageModification
from app.service import Service


router = APIRouter(prefix="/api", tags=["Images"])


@router.post(
    "/modify",
)
def modify_image(
    name: str = Form(...),  # noqa: B008
    image: UploadFile = File(...),  # noqa: B008
    variants: int = Form(100, ge=1, le=100),
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


# @router.post(
#     "/validate",
# )
# def validate_image(name: str, db: Session = Depends(get_db)):  # noqa: B008

#     db_image = db.query(DBImage).filter(DBImage.name == name).first()
#     if db_image is None:
#         raise HTTPException(status_code=404, detail="Image not found in database")

#     try:
#         img = Image.open(db_image.path)
#     except FileNotFoundError:
#         raise HTTPException(status_code=404, detail="Image not found in storage")
    
#     base_path = Path(db_image.path).parent

#     db_img_modification = DBImageModification(
#         image_id=db_image.id,
#         modification_number=1
#     )
#     db.add(db_img_modification)
#     db.flush()

#     for i in range(100):
#         x = 10 + i
#         y = 20 + i
#         modified_pixel = modify_pixel(img, x, y)
#         db_img_modification_step = DBImageModificationStep(
#             modification_id=db_img_modification.id,
#             pixel_x=x,
#             pixel_y=y,
#             og_pixel_value=modified_pixel.og_pixel_value,
#             new_pixel_value=modified_pixel.new_pixel_value
#         )
#         db.add(db_img_modification_step)
    
#     save_image(modified_pixel.image, f"{base_path}/modified_{i}.{img.format.lower()}")
#     db.commit()

#     return {
#         "data":
#         {
#             "modified": True
#         }
#     }
