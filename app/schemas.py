from typing import Tuple

from PIL import Image
from pydantic import BaseModel


class ModifiedPixel(BaseModel):
    img: Image.Image
    x: int
    y: int
    og_pixel_value: Tuple[int, int, int]
    new_pixel_value: Tuple[int, int, int]

    model_config = {"arbitrary_types_allowed": True}
