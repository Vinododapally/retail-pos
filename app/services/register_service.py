from datetime import datetime, timezone

from fastapi import HTTPException

from app.repositories import register_repository


class RegisterService:
    @staticmethod
    def current(user):
        return register_repository.current_session(user["tenant_id"], user["id"])

    @staticmethod
    def open(user, data):
        session_id = register_repository.open_session(
            user["tenant_id"], user["id"], data.opening_cash, datetime.now(timezone.utc).isoformat()
        )
        if not session_id:
            raise HTTPException(status_code=409, detail="Your register already has an open shift.")
        return register_repository.current_session(user["tenant_id"], user["id"])

    @staticmethod
    def close(user, data):
        result = register_repository.close_session(
            user["tenant_id"], user["id"], data.counted_cash, datetime.now(timezone.utc).isoformat()
        )
        if not result:
            raise HTTPException(status_code=409, detail="You don't have an open register shift.")
        return result
