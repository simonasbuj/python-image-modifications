from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DBImage(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    original_image_path: Mapped[str] = mapped_column(nullable=False)
    created_at = Column(DateTime, default=func.now())

    modifications = relationship("DBImageModification", back_populates="image")


class DBImageModification(Base):
    __tablename__ = "image_modifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False, index=True)
    modified_image_path: Mapped[str] = mapped_column(nullable=False)
    modification_algorithm = Column(String, nullable=False)
    modification_params: Mapped[str] = mapped_column(nullable=False)
    num_modifications = Column(Integer, nullable=False)
    verification_status: Mapped[str] = mapped_column(default="pending")
    created_at = Column(DateTime, default=func.now())
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    image = relationship("DBImage", back_populates="modifications")
