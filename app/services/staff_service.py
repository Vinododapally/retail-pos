import sqlite3
from datetime import datetime, timezone

from fastapi import HTTPException

from app.repositories import staff_repository
from app.utils.security import hash_password


class StaffService:
    @staticmethod
    def list_staff(user):
        return staff_repository.list_staff(user["tenant_id"])

    @staticmethod
    def create_staff(user, data):
        try:
            return staff_repository.create_staff(
                user["tenant_id"], data.name.strip(), data.email.strip().lower(),
                hash_password(data.password), data.permissions.model_dump(),
                datetime.now(timezone.utc).isoformat(),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=409,
                detail="That email is already used by an account in this store.",
            )

    @staticmethod
    def update_permissions(user, staff_id: int, data):
        staff = staff_repository.update_permissions(
            user["tenant_id"], staff_id, data.permissions.model_dump()
        )
        if not staff:
            raise HTTPException(status_code=404, detail="Staff member not found.")
        return staff
