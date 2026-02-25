
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import random
from PIL import Image

from app.models import DBImage, DBImageModification
from sqlalchemy.orm import Session
from pathlib import Path

from app.schemas import ModifiedPixel
from app.utils.logging import get_json_logger

class Service:
    def __init__(self, db: Session, storage_path: str):
        self.db = db
        self.storage_path = storage_path

        self.log = get_json_logger(__name__)

    def modify_image(self, img: Image, name: str, variants: int = 10, max_workers: int = 10):
        saved_img_path = self._save_image(img, f"{self.storage_path}/{name}/og.{img.format.lower()}")

        db_img = DBImage(
            name=name,
            path=saved_img_path,
        )

        self.db.add(db_img)
        self.db.flush()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    self.modify_random_pixels,
                    img.copy(),
                    db_img.id,
                    i,
                    Path(db_img.path).parent,
                    img.format.lower(),
                )
                for i in range(variants)
            ]

            results = []
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    self.log.error(f"Error in thread: {e}")
                    raise
            
            for r in results:
                self.db.add(r)

        self.db.commit()

    def modify_random_pixels(
        self,
        img: Image.Image, 
        img_id: int, 
        variant_number: int,
        img_base_path: str,
        img_extension: str,
        min_mods: int = 100,
        max_mods: int = 200000,
    ) -> None:
        img_pixels = img.width * img.height

        mods_amount = random.randint(min_mods, min(max_mods, img_pixels))
        pixels = self._get_cluster_pixels(img.width, img.height, mods_amount)

        self.log.info(f"Going to modify {len(pixels)} for variant #{variant_number}")

        steps_file_path = Path(img_base_path) / f"steps_{variant_number}.csv"
        self._create_modification_csv(steps_file_path)

        rows_to_write = []
        for pixel in pixels:
            x = pixel[0]
            y = pixel[1]

            modified_pixel = self.modify_pixel(img, x, y)
            old_r, old_g, old_b = modified_pixel.og_pixel_value
            new_r, new_g, new_b = modified_pixel.new_pixel_value
            rows_to_write.append((x, y, old_r, old_g, old_b, new_r, new_g, new_b))

        self._append_modification_rows(steps_file_path, rows_to_write)
        final_img = modified_pixel.img
        saved_img_path = self._save_image(final_img, f"{img_base_path}/mod_{variant_number}.{img_extension}")
        
        self.log.info(f"Finished modifying variant #{variant_number}")

        return DBImageModification(
            image_id=img_id,
            variant_number=variant_number,
            path=saved_img_path,
            steps_file_path=str(steps_file_path)
        )
    
    def modify_pixel(self, img: Image.Image, x: int, y: int, color: tuple = (0, 255, 0)) -> ModifiedPixel:
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

    def _save_image(self, img: Image.Image, path: str) -> str:
        if img.mode != "RGB":
            img = img.convert("RGB")

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path)

        return str(path)
    
    def _get_cluster_pixels(self, width: int, height: int, n: int) -> list[tuple[int, int]]:
        """
        Return n pixel coordinates that are spatially close
        by sampling a square region.
        """
        if n > width * height:
            raise ValueError(f"Image has less pixels than {n}")

        side = int(n ** 0.5)

        start_x = random.randint(0, max(0, width - side))
        start_y = random.randint(0, max(0, height - side))

        pixels = []

        for x in range(start_x, min(start_x + side, width)):
            for y in range(start_y, min(start_y + side, height)):
                pixels.append((x, y))
                if len(pixels) == n:
                    return pixels

        return pixels

    def _create_modification_csv(self, file_path: Path) -> None:
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

    def _append_modification_rows(self, file_path: Path, rows: list[tuple]) -> None:
        """
        Append pixel modification rows to CSV file.
        """
        with open(file_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
