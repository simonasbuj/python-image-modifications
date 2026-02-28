import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Image Modification Service")

storage_path = os.getenv("APP_STORAGE_BASE_PATH", "storage")
os.makedirs(storage_path, exist_ok=True)

app.mount(
    f"/{storage_path}",
    StaticFiles(directory=storage_path),
    name=storage_path,
)

app.mount(
    "/frontend",
    StaticFiles(directory="frontend", html=True),
    name="frontend",
)
app.include_router(router)
