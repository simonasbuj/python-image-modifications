import datetime as dt
import os
import shutil
from typing import BinaryIO


class Storage:
    def __init__(self, storage_path: str):
        self.storage_path = storage_path

    def save(self, file: BinaryIO, path: str) -> str:
        full_path = os.path.join(self.storage_path, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "wb") as buffer:
            shutil.copyfileobj(file, buffer)

        return full_path

    def get(self, path: str) -> bytes:
        """
        Read a file from storage and return its binary content.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"File {path} not found")

        with open(path, "rb") as f:
            return f.read()

    def _get_timestamp(self) -> str:
        return dt.datetime.now().strftime("%Y%m%d_%H%M%S")
