import sqlite3
from datetime import datetime, timezone

from fastapi import HTTPException

from app.repositories import platform_repository
from app.utils.security import hash_password


class PlatformService:
    @staticmethod
    def list_stores():
        return platform_repository.list_stores()

    @staticmethod
    def create_store(data):
        values = data.model_dump()
        values["store_name"] = values["store_name"].strip()
        values["owner_name"] = values["owner_name"].strip()
        values["owner_email"] = values["owner_email"].strip().lower()
        password_hash = hash_password(values.pop("owner_password"))
        try:
            return platform_repository.create_store(
                values,
                password_hash,
                datetime.now(timezone.utc).isoformat(),
            )
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="That owner email is already in use. Each shop owner needs a unique login email.") from exc

    @staticmethod
    def set_store_status(store_id: int, status: str):
        result = platform_repository.set_store_status(store_id, status)
        if not result:
            raise HTTPException(status_code=404, detail="Retail workspace not found.")
        return result
