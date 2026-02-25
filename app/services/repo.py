from sqlalchemy.orm import Session

from app.models import DBImageModification


class Repo:
    def __init__(self, db: Session):
        self.db = db

    def save_modification(self, mod: DBImageModification, commit: bool = False) -> DBImageModification:
        self.db.add(mod)
        self.db.flush()

        if commit:
            self.db.commit()

        return mod
