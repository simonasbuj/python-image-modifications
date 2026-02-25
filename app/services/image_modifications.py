import datetime as dt
from pathlib import Path
import random
import csv

from PIL import Image

from app.models import DBImageModification
from app.schemas import ModifiedPixel
from app.services.repo import Repo
from sqlalchemy.orm import Session


def modify_pixel(img: Image.Image, x: int, y: int, color: tuple = (0, 255, 0)) -> ModifiedPixel:
    """
    Modify a single pixel in an image.

    Args:
        img (PIL.Image.Image): The image to modify.
        x (int): X coordinate of the pixel.
        y (int): Y coordinate of the pixel.
        color (tuple): RGB color to set (default is light green).

    Returns:
        PIL.Image.Image: The modified image.
    """
    if x >= img.width or y >= img.height:
        raise ValueError("Pixel coordinates out of bounds")

    if img.mode != "RGB":
        img = img.convert("RGB")

    original_pixel = img.getpixel((x, y))

    img.putpixel((x, y), color)

    return ModifiedPixel(
        img=img, 
        x=x,
        y=y,
        og_pixel_value=original_pixel,
        new_pixel_value=color,
    )

def modify_random_pixels(
    img: Image.Image, 
    img_id: int, 
    mod_number: int,
    img_base_path: str,
    img_extension: str,
    db: Session, 
    min_mods: int = 100
) -> None:
    max_mods = img.width * img.height

    mods_number = random.randint(min_mods, max_mods)
    print(f"Going to modify {mods_number} pixels for {mod_number}")
    # pixels = _get_random_pixels(img.width, img.height, 100000)
    pixels = _get_cluster_pixels(img.width, img.height, 200000)

    print(len(pixels))

    steps_file_path = Path(img_base_path) / f"steps_{mod_number}.csv"
    _create_modification_csv(steps_file_path)

    rows_to_write = []
    for pixel in pixels:
        x = pixel[0]
        y = pixel[1]

        modified_pixel = modify_pixel(img, x, y)
        old_r, old_g, old_b = modified_pixel.og_pixel_value
        new_r, new_g, new_b = modified_pixel.new_pixel_value
        rows_to_write.append((x, y, old_r, old_g, old_b, new_r, new_g, new_b))

    _append_modification_rows(steps_file_path, rows_to_write)
    final_img = modified_pixel.img
    saved_img_path = save_image(final_img, f"{img_base_path}/mod_{mod_number}.{img_extension}")
        
    return DBImageModification(
        image_id=img_id,
        modification_number=mod_number,
        path=saved_img_path,
        steps_file_path=str(steps_file_path)
    )

    print(f"Finished modifying {mods_number} pixels for {mod_number}")


def save_image(img: Image.Image, path: str) -> str:
    if img.mode != "RGB":
        img = img.convert("RGB")

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)

    return str(path)

def _get_timestamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")

def _get_random_pixels(width: int, height: int, n: int) -> list[tuple[int, int]]:
    """
    Return a list of n unique random pixel coordinates (x, y)
    within the given height and width.
    
    Args:
        width (int): Image width
        height (int): Image height
        n (int): Number of unique pixels to select
    
    Returns:
        List[Tuple[int, int]]: List of (x, y) coordinates
    """
    if n > height * width:
        raise ValueError("n cannot be larger than total number of pixels")
    
    all_pixels = [(x, y) for x in range(width) for y in range(height)]
    
    selected = random.sample(all_pixels, n)
    
    return selected

def _get_cluster_pixels(width: int, height: int, n: int) -> list[tuple[int, int]]:
    """
    Return n pixel coordinates that are spatially close
    by sampling a square region.
    """
    if n > width * height:
        raise ValueError("n too large")

    # approximate square size
    side = int(n ** 0.5)

    # random top-left corner
    start_x = random.randint(0, max(0, width - side))
    start_y = random.randint(0, max(0, height - side))

    pixels = []

    for x in range(start_x, min(start_x + side, width)):
        for y in range(start_y, min(start_y + side, height)):
            pixels.append((x, y))
            if len(pixels) == n:
                return pixels

    return pixels


def _create_modification_csv(file_path: Path) -> None:
    """
    Create a CSV file with header for pixel modifications.
    Overwrites file if it already exists.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "x",
            "y",
            "old_r",
            "old_g",
            "old_b",
            "new_r",
            "new_g",
            "new_b",
        ])

def _append_modification_rows(
    file_path: Path,
    rows: list[tuple]
) -> None:
    """
    Append pixel modification rows to CSV file.
    """
    with open(file_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
