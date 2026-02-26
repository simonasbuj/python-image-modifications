"""
Service layer for image modification operations.
Handles business logic for image processing, database operations, and file management.
"""
import io
import json
import os
import random
from typing import Tuple

from PIL import Image as PILImage
from sqlalchemy.orm import Session

from app.models import DBImage, DBImageModification
from app.schemas import Modification, Paths, UploadResponse
from app.services.image_processor import apply_pixel_color_modifications
from app.utils.logging import get_json_logger


class GeneratorService:
    def __init__(self, db: Session, storage_path: str):
        self.db = db
        self.storage_path = storage_path
        self.log = get_json_logger(__name__)

    def process_uploaded_image(
        self,
        file_contents: bytes,
        modification_color: Tuple[int, int, int] = (0, 255, 0),
    ) -> UploadResponse:
        """
        Process an uploaded image and generate 100 variants.

        Args:
            file_contents: Raw image file contents
            db: Database session
            modification_color: RGB color for modifications (default: green)

        Returns:
            Dictionary with image_id, message, original_image path,
            and modifications list
        """
        og_image = self._load_and_validate_image(file_contents)
        width, height = og_image.size
        max_pixels = width * height

        image_record = self._create_image_record()

        paths = self._prepare_storage_paths(image_record.id)

        og_image.save(paths.og_image_path, "PNG")

        image_record.original_image_path = paths.og_image_path

        created_modifications: list[Modification] = []

        for variant_num in range(100):
            num_modifications = random.randint(100, min(max_pixels, 600000))

            modified_path, modification_params = self._generate_and_save_variant(
                original_image=og_image,
                variant_num=variant_num,
                num_modifications=num_modifications,
                modified_folder=paths.modified_folder,
                modification_color=modification_color,
            )

            modification_record = DBImageModification(
                image_id=image_record.id,
                modified_image_path=modified_path,
                modification_algorithm=modification_params["algorithm"],
                modification_params=json.dumps(modification_params),
                num_modifications=modification_params["num_modifications"],
                verification_status="pending",
            )
            self.db.add(modification_record)
            self.db.flush()

            created_modifications.append(
                Modification(
                    id=modification_record.id,
                    variant_num=variant_num,
                    num_modifications=num_modifications,
                )
            )

        self.db.commit()

        return UploadResponse(
            image_id=image_record.id,
            message="Successfully created 100 image variants",
            original_image=paths.og_image_path,
            modifications=created_modifications,
        )

    def _load_and_validate_image(self, file_contents: bytes) -> PILImage.Image:
        """
        Load and validate image from file contents.

        Args:
            file_contents: Raw image file contents

        Returns:
            PIL Image object in RGB mode
        """
        image = PILImage.open(io.BytesIO(file_contents))
        if image.mode != "RGB":
            image = image.convert("RGB")
        return image

    def _create_image_record(self) -> DBImage:
        """
        Create Image record in database and return it with ID assigned.

        Args:
            db: Database session

        Returns:
            Image record with ID assigned
        """
        image_record = DBImage(original_image_path="")
        self.db.add(image_record)
        self.db.flush()
        return image_record

    def _prepare_storage_paths(self, image_id: int) -> Paths:
        """
        Prepare directory structure and return paths for a new image upload.

        Args:
            image_id: ID of the image

        Returns:
            Dictionary with image_folder, modified_folder, reversed_folder,
            and original_path
        """
        image_folder = os.path.join(self.storage_path, str(image_id))
        modified_folder = os.path.join(image_folder, "modified")
        reversed_folder = os.path.join(image_folder, "reversed")

        os.makedirs(image_folder, exist_ok=True)
        os.makedirs(modified_folder, exist_ok=True)
        os.makedirs(reversed_folder, exist_ok=True)

        og_image_path = os.path.join(image_folder, "original.png")

        return Paths(
            image_folder=image_folder,
            modified_folder=modified_folder,
            reversed_folder=reversed_folder,
            og_image_path=og_image_path,
        )

    def _generate_and_save_variant(
        self,
        original_image: PILImage.Image,
        variant_num: int,
        num_modifications: int,
        modified_folder: str,
        modification_color: Tuple[int, int, int],
    ) -> Tuple[str, dict[str, object]]:
        """
        Generate a single variant, save it, and return path and modification params.

        Args:
            original_image: Original PIL Image
            variant_num: Variant number (0-99)
            num_modifications: Number of modifications to apply
            modified_folder: Folder to save modified image
            modification_color: RGB color for modifications

        Returns:
            Tuple of (modified_path, modification_params)
        """
        modified_image, modification_params = apply_pixel_color_modifications(
            original_image, num_modifications, color=modification_color
        )

        modified_filename = f"variant_{variant_num:03d}.png"
        modified_path = os.path.join(modified_folder, modified_filename)
        modified_image.save(modified_path, "PNG")

        return modified_path, modification_params
