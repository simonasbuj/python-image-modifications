import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from PIL import Image

from app.services.database import get_db
from app.services.image_modifications import _get_timestamp, modify_pixel, save_image, modify_random_pixels
from app.models import DBImage, DBImageModification


router = APIRouter(prefix="/api", tags=["Images"])


@router.post(
    "/modify",
)
def modify_image(
    name: str = Form(...),  # noqa: B008
    image: UploadFile = File(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    print(f"Received file: {image.filename}")
    img = Image.open(image.file)

    saved_img_path = save_image(img, f"storage/{name}/{_get_timestamp()}/og.{img.format.lower()}")

    db_img = DBImage(
        name=name,
        path=saved_img_path,
    )

    db.add(db_img)
    db.flush()

    # for i in range(10):
    #     img_copy = img.copy()

    #     modify_random_pixels(
    #         img=img_copy, 
    #         img_id=db_img.id, 
    #         mod_number=i,
    #         img_base_path=Path(db_img.path).parent,
    #         img_extension=img.format.lower(),
    #         db=db
    #     )

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(
                modify_random_pixels,
                img.copy(),
                db_img.id,
                i,
                Path(db_img.path).parent,
                img.format.lower(),
                db
            )
            for i in range(10)
        ]

        results = []
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                print(f"Error in thread: {e}")
        
        for r in results:
            db.add(r)

    db.commit()

    return {
        "data": {
            "message": "modified",
            "image": db_img.__dict__
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
