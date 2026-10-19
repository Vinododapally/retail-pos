import base64
import hashlib
import hmac
import json
import os
import secrets
import time

from fastapi import HTTPException

SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-before-production")


def demo_mode_enabled() -> bool:
    return os.environ.get("DEMO_MODE", "true").strip().lower() in {"1", "true", "yes"}


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 180_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        salt_hex, expected = encoded.split("$", 1)
        actual = hash_password(password, bytes.fromhex(salt_hex)).split("$", 1)[1]
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def platform_owner_credentials() -> tuple[str, str]:
    email = os.environ.get("PLATFORM_OWNER_EMAIL", "").strip().lower()
    password = os.environ.get("PLATFORM_OWNER_PASSWORD", "")
    if email and password:
        return email, password
    if demo_mode_enabled():
        return email or "owner@demo.com", password or "owner1234"
    return email, password


def create_access_token(user: dict, expires_in: int = 60 * 60 * 24 * 7) -> str:
    payload = {
        "id": user["id"],
        "tenant_id": user.get("tenant_id"),
        "role": user["role"],
        "identity_type": user.get("identity_type", "tenant"),
        "email": user["email"],
        "exp": int(time.time()) + expires_in,
    }
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature = hmac.new(SECRET_KEY.encode(), body.encode(), hashlib.sha256).digest()
    return f"{body}.{base64.urlsafe_b64encode(signature).decode().rstrip('=')}"


def decode_access_token(token: str) -> dict:
    try:
        body, signature = token.split(".", 1)
        expected = hmac.new(SECRET_KEY.encode(), body.encode(), hashlib.sha256).digest()
        supplied = base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4))
        if not hmac.compare_digest(expected, supplied):
            raise ValueError("Invalid signature")
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        if payload["exp"] < time.time():
            raise ValueError("Expired token")
        return payload
    except (ValueError, KeyError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Your session has expired. Please sign in again.")
