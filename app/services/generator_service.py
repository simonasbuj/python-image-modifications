"""
Service layer for image modification operations.
Handles business logic for image processing, database operations, and file management.
"""
import io
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

from fastapi import HTTPException
from PIL import Image as PILImage
from sqlalchemy.orm import Session, joinedload

from app.models import DBImage, DBImageModification
from app.schemas import Modification, Paths, ReverseModificationResponse, UploadResponse
from app.services.image_processor import (
    apply_pixel_color_modifications,
    compare_images_pixelwise,
    reverse_pixel_color_modifications,
)
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
        self.log.info("Processing image")
        og_image = self._load_and_validate_image(file_contents)
        width, height = og_image.size
        max_pixels = width * height

        image_record = self._create_image_record()

        paths = self._prepare_storage_paths(image_record.id)

        og_image.save(paths.og_image_path, "PNG")

        image_record.original_image_path = paths.og_image_path

        created_modifications: list[Modification] = []

        for variant_num in range(100):
            num_modifications = random.randint(100, min(max_pixels, 1000000))

            self.log.info(
                f"Creating {num_modifications} modifications, "
                f"image_id: {image_record.id}, variant: {variant_num}"
            )

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

    def reverse_modification(
        self,
        modification_id: int,
        should_save_reversed_img: bool = False,
    ) -> ReverseModificationResponse:
        """
        Reverse a specific modification and save the result.

        Args:
            modification_id: ID of the modification to reverse
            db: Database session

        Returns:
            Dictionary with modification_id, message, paths, and URLs

        Raises:
            HTTPException: If modification not found or error occurs
        """
        self.log.info(f"Reversing modification #{modification_id}")
        modification = self._get_modification_with_image(modification_id)

        original_path = modification.image.original_image_path
        reversed_path = self._prepare_reversed_image_path(
            original_path, modification_id
        )

        modified_image = self._load_modified_image(modification.modified_image_path)

        modification_params = self._parse_and_convert_modification_params(
            modification.modification_params
        )

        reversed_image = reverse_pixel_color_modifications(
            modified_image, modification_params
        )

        if should_save_reversed_img:
            reversed_image.save(reversed_path, "PNG")

        og_image = PILImage.open(original_path)
        is_reversible = compare_images_pixelwise(og_image, reversed_image)
        modification.verification_status = "true" if is_reversible else "false"
        modification.verified_at = datetime.now(timezone.utc)
        self.db.commit()

        return ReverseModificationResponse(
            modification_id=modification_id,
            message="Successfully reversed modification",
            reversed_path=reversed_path if should_save_reversed_img else None,
            original_path=original_path,
            modified_path=modification.modified_image_path,
            is_reversible=is_reversible,
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

    def _get_modification_with_image(
        self,
        modification_id: int,
    ) -> DBImageModification:
        """
        Get modification from database with image relationship loaded.

        Args:
            modification_id: ID of the modification
            db: Database session

        Returns:
            ImageModification object

        Raises:
            HTTPException: If modification not found
        """
        modification = (
            self.db.query(DBImageModification)
            .options(joinedload(DBImageModification.image))
            .filter(DBImageModification.id == modification_id)
            .first()
        )

        if not modification:
            raise HTTPException(
                status_code=404, detail=f"Modification {modification_id} not found"
            )

        return modification

    def _prepare_reversed_image_path(
        self, original_path: str, modification_id: int
    ) -> str:
        """
        Prepare path for reversed image.

        Args:
            image_id: ID of the image
            modification_id: ID of the modification

        Returns:
            Tuple of (reversed_folder, reversed_path)
        """
        reversed_filename = f"reversed_{modification_id}.png"
        reversed_path = os.path.join(
            Path(original_path).parent / "reversed", reversed_filename
        )

        return reversed_path

    def _load_modified_image(self, modified_image_path: str) -> PILImage.Image:
        """
        Load and validate modified image from path.

        Args:
            modified_image_path: Path to modified image

        Returns:
            PIL Image object in RGB mode

        Raises:
            HTTPException: If image file not found
        """
        if not os.path.exists(modified_image_path):
            raise HTTPException(
                status_code=404,
                detail=f"Modified image not found: {modified_image_path}",
            )

        image = PILImage.open(modified_image_path)
        if image.mode != "RGB":
            image = image.convert("RGB")

        return image

    def _parse_and_convert_modification_params(
        self, modification_params_json: str
    ) -> dict[str, str]:
        """
        Parse modification parameters from JSON and convert lists to tuples.

        Args:
            modification_params_json: JSON string of modification parameters

        Returns:
            Dictionary with converted modification parameters
        """
        modification_params = json.loads(modification_params_json)

        original_pixels = modification_params.get("original_pixels", [])
        if original_pixels:
            original_pixels = [
                (int(p[0]), int(p[1]), tuple(int(c) for c in p[2]))
                if isinstance(p[2], list)
                else (int(p[0]), int(p[1]), p[2])
                for p in original_pixels
            ]
            modification_params["original_pixels"] = original_pixels

        return modification_params
