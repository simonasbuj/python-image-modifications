from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.services.database import Base


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
        order_by="DBImageModification.created_at"
    )


class DBImageModification(Base):
    __tablename__ = "image_modifications"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False)
    modification_number = Column(Integer, nullable=False)
    path = Column(String, nullable=False)
    steps_file_path = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    image = relationship("DBImage", back_populates="modifications")

    # steps = relationship(
    #     "DBImageModificationStep",
    #     back_populates="modification",
    #     cascade="all, delete-orphan",
    #     order_by="DBImageModificationStep.created_at"
    # )


# class DBImageModificationStep(Base):
#     __tablename__ = "image_modification_steps"

#     id = Column(Integer, primary_key=True, index=True)
#     modification_id = Column(Integer, ForeignKey("image_modifications.id"), nullable=False)

#     pixel_x = Column(Integer, nullable=False)
#     pixel_y = Column(Integer, nullable=False)
#     og_pixel_value = Column(JSON, nullable=False)
#     new_pixel_value = Column(JSON, nullable=False)

#     created_at = Column(DateTime(timezone=True), server_default=func.now())

#     modification = relationship("DBImageModification", back_populates="steps")
