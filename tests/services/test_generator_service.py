import json
import os
from pathlib import Path
from typing import Iterator

import pytest
from fastapi import HTTPException
from PIL import Image as PILImage
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.models import DBImage, DBImageModification
from app.services.generator_service import GeneratorService


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        future=True,
    )

    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )

    with SessionLocal() as session:
        yield session


@pytest.fixture
def generator_service(tmp_path: Path, db_session: Session) -> GeneratorService:
    return GeneratorService(db=db_session, storage_path=str(tmp_path))


def test_prepare_storage_paths(
    generator_service: GeneratorService, tmp_path: Path
) -> None:
    paths = generator_service._prepare_storage_paths(123)

    assert Path(paths.image_folder).is_dir()
    assert Path(paths.modified_folder).is_dir()
    assert Path(paths.reversed_folder).is_dir()

    assert paths.image_folder == os.path.join(tmp_path, "123")
    assert paths.modified_folder == os.path.join(tmp_path, "123/modified")
    assert paths.reversed_folder == os.path.join(tmp_path, "123/reversed")
    assert paths.og_image_path == os.path.join(tmp_path, "123/original.png")


def test_create_image_record(generator_service: GeneratorService) -> None:
    image_record: DBImage = generator_service._create_image_record()

    assert image_record.id == 1
    assert isinstance(image_record.id, int)
    assert image_record.original_image_path == ""


def test_generate_and_save_variant(
    generator_service: GeneratorService, tmp_path: Path
) -> None:
    original = PILImage.new("RGB", (32, 32), (10, 20, 30))
    modified_folder = str(tmp_path)

    out_path, params = generator_service._generate_and_save_variant(
        original_image=original,
        variant_num=7,
        num_modifications=9,
        modified_folder=modified_folder,
        modification_color=(255, 0, 0),
    )

    assert out_path == os.path.join(modified_folder, "variant_007.png")
    assert Path(out_path).is_file()

    saved = PILImage.open(out_path)
    assert saved.format == "PNG"
    assert saved.size == original.size

    assert isinstance(params, dict)
    assert params.get("num_modifications") == 9


def test_get_modification_with_image_found(generator_service: GeneratorService) -> None:
    image_record = DBImage(original_image_path="storage/1/original.png")
    generator_service.db.add(image_record)
    generator_service.db.flush()

    modification_record = DBImageModification(
        image_id=image_record.id,
        modified_image_path="storage/1/variant_001.png",
        modification_algorithm="color_change",
        modification_params="params",
        num_modifications=100,
    )

    generator_service.db.add(modification_record)
    generator_service.db.commit()

    fetched_modification = generator_service._get_modification_with_image(
        modification_record.id
    )

    assert fetched_modification.id == modification_record.id
    assert fetched_modification.image_id == image_record.id
    assert fetched_modification.image is not None
    assert fetched_modification.image.id == image_record.id
    assert fetched_modification.image.original_image_path == "storage/1/original.png"

    generator_service.db.expunge(fetched_modification)
    assert fetched_modification.image.id == image_record.id
    assert (
        fetched_modification.image.original_image_path
        == image_record.original_image_path
    )


def test_get_modification_with_image_not_found(
    generator_service: GeneratorService,
) -> None:
    non_existent_id = 999

    with pytest.raises(HTTPException) as exc_info:
        generator_service._get_modification_with_image(non_existent_id)

    assert exc_info.value.status_code == 404


def test_prepare_reversed_image_path(
    generator_service: GeneratorService, tmp_path: Path
) -> None:
    image_dir = tmp_path / "123"
    reversed_dir = image_dir / "reversed"

    original_path = str(image_dir / "original.png")
    modification_id = 42

    out_path = generator_service._prepare_reversed_image_path(
        original_path, modification_id
    )

    expected = os.path.join(str(reversed_dir), f"reversed_{modification_id}.png")
    assert out_path == expected


def test_load_modified_image_ok_converts_to_rgb(
    generator_service: GeneratorService, tmp_path: Path
) -> None:
    img = PILImage.new("RGBA", (10, 10), (255, 0, 0, 128))
    img_path = tmp_path / "modified.png"
    img.save(img_path, "PNG")

    loaded = generator_service._load_modified_image(str(img_path))

    assert isinstance(loaded, PILImage.Image)
    assert loaded.mode == "RGB"
    assert loaded.size == (10, 10)


def test_load_modified_image_missing_raises_404(
    generator_service: GeneratorService, tmp_path: Path
) -> None:
    missing_path = tmp_path / "does_not_exist.png"

    with pytest.raises(HTTPException) as exc:
        generator_service._load_modified_image(str(missing_path))

    assert exc.value.status_code == 404
    assert "Modified image not found" in exc.value.detail


def test_parse_and_convert_modification_params(
    generator_service: GeneratorService,
) -> None:
    payload: dict[str, object] = {
        "algorithm": "pixel_color",
        "original_pixels": [
            [10, 20, [255, 1, 2]],
            [11, 21, [1, 255, 2]],
        ],
    }
    params_json = json.dumps(payload)

    out = generator_service._parse_and_convert_modification_params(params_json)

    assert out["algorithm"] == "pixel_color"
    assert isinstance(out["original_pixels"], list)
    assert out["original_pixels"][0] == (10, 20, (255, 1, 2))
    assert out["original_pixels"][1] == (11, 21, (1, 255, 2))
