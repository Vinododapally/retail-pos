import json
import hmac
from fastapi import HTTPException

from app.repositories import auth_repository
from app.utils.security import create_access_token, platform_owner_credentials, verify_password


class AuthService:
    @staticmethod
    def register():
        raise HTTPException(status_code=403, detail="Public store registration is disabled. Contact the product owner to open a shop account.")

    @staticmethod
    def platform_login(data):
        owner_email, owner_password = platform_owner_credentials()
        email = data.email.strip().lower()
        if not owner_email or not owner_password:
            raise HTTPException(status_code=503, detail="Product-owner access is not configured. Set PLATFORM_OWNER_EMAIL and PLATFORM_OWNER_PASSWORD.")
        if not hmac.compare_digest(email.encode("utf-8"), owner_email.encode("utf-8")) or not hmac.compare_digest(data.password.encode("utf-8"), owner_password.encode("utf-8")):
            raise HTTPException(status_code=401, detail="That product-owner email and password don't match.")
        owner = {
            "id": 0,
            "tenant_id": None,
            "email": owner_email,
            "role": "platform_owner",
            "identity_type": "platform_owner",
        }
        return {"token": create_access_token(owner, expires_in=60 * 60 * 8), "user": {**owner, "name": "Product owner", "permissions": {}}}

    @staticmethod
    def login(data):
        user = auth_repository.find_by_email(data.email.strip().lower())
        if not user or not verify_password(data.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="That email and password don't match.")
        result = {key: user[key] for key in (
            "id", "tenant_id", "name", "email", "role", "store_name", "business_type", "currency"
        )}
        result["permissions"] = json.loads(user["permissions"] or "{}")
        result["is_demo"] = bool(user["is_demo"] or user["tenant_is_demo"])
        return {"token": create_access_token(result), "user": result}

    @staticmethod
    def current_user(authorization=None):
        from fastapi import HTTPException

        from app.utils.security import decode_access_token

        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Please sign in to continue.")
        payload = decode_access_token(authorization[7:])
        if payload.get("identity_type") == "platform_owner":
            owner_email, _ = platform_owner_credentials()
            if not owner_email or not hmac.compare_digest(payload.get("email", "").encode("utf-8"), owner_email.encode("utf-8")):
                raise HTTPException(status_code=401, detail="Product-owner access is no longer valid.")
            return {"id": payload["id"], "email": owner_email, "name": "Product owner", "role": "platform_owner", "permissions": {}, "platform_owner": True}
        if payload.get("identity_type", "tenant") != "tenant":
            raise HTTPException(status_code=401, detail="Your session has expired. Please sign in again.")
        user = auth_repository.find_user(payload["id"], payload["tenant_id"])
        if not user:
            raise HTTPException(status_code=401, detail="This account is no longer available.")
        result = dict(user)
        result["permissions"] = json.loads(result["permissions"] or "{}")
        result["is_demo"] = bool(result["is_demo"] or result["tenant_is_demo"])
        return result

    @staticmethod
    def get_current_user(user):
        store = auth_repository.find_store_name(user["tenant_id"])
        return {**user, **store}
