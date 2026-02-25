from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class DBImage(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    modifications = relationship(
        "DBImageModification",
        back_populates="image",
        cascade="all, delete-orphan",
        order_by="DBImageModification.created_at",
    )


class DBImageModification(Base):
    __tablename__ = "image_modifications"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False)
    variant_number = Column(Integer, nullable=False)
    path = Column(String, nullable=False)
    steps_file_path = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    image = relationship("DBImage", back_populates="modifications")
