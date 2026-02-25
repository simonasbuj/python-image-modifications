import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routes import router
from .database import Base, engine
from .models import DBImage, DBImageModification

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Image Modification Service")

storage_path = os.getenv("APP_STORAGE_BASE_PATH", "storage")
os.makedirs(storage_path, exist_ok=True)

app.mount(
    f"/{storage_path}",
    StaticFiles(directory=os.getenv("APP_STORAGE_BASE_PATH", storage_path)),
    name=storage_path,
)
app.include_router(router)
