import os
from pathlib import Path
from typing import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.models import DBImage
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


def test_prepare_storage_paths(generator_service: GeneratorService) -> None:
    paths = generator_service._prepare_storage_paths(123)

    assert Path(paths.image_folder).is_dir()
    assert Path(paths.modified_folder).is_dir()
    assert Path(paths.reversed_folder).is_dir()

    assert paths.modified_folder == os.path.join(paths.image_folder, "modified")
    assert paths.reversed_folder == os.path.join(paths.image_folder, "reversed")
    assert paths.og_image_path == os.path.join(paths.image_folder, "original.png")


def test_create_image_record(generator_service: GeneratorService) -> None:
    image_record: DBImage = generator_service._create_image_record()

    assert image_record.id == 1
    assert isinstance(image_record.id, int)
    assert image_record.original_image_path == ""
