from typing import Tuple

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
