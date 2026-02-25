import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routes.routes import router
from .services.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Image Modification Service")

app.mount(
    "/storage",
    StaticFiles(directory=os.getenv("APP_STORAGE_BASE_PATH", "storage")),
    name="storage",
)
app.include_router(router)
