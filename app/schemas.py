import datetime as dt
from typing import Optional, Tuple

from PIL import Image
from pydantic import BaseModel, ConfigDict


class ModifiedPixel(BaseModel):
    img: Image.Image
    x: int
    y: int
    og_pixel_value: Tuple[int, int, int]
    new_pixel_value: Tuple[int, int, int]

    model_config = {"arbitrary_types_allowed": True}


class Paths(BaseModel):
    image_folder: str
    modified_folder: str
    reversed_folder: str
    og_image_path: str


class Modification(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    variant_num: int
    num_modifications: int


class UploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    image_id: int
    message: str
    original_image: str
    modifications: list[Modification]


class ReverseImageRequest(BaseModel):
    should_save_reversed_img: bool = False


class ReverseModificationResponse(BaseModel):
    modification_id: int
    message: str
    reversed_path: Optional[str] = None
    original_path: str
    modified_path: str
    is_reversible: bool


class ModificationResponse(BaseModel):
    id: int
    image_id: int
    modified_image_path: str
    modification_algorithm: str
    num_modifications: int
    verification_status: str
    created_at: dt.datetime
    verified_at: Optional[dt.datetime]
