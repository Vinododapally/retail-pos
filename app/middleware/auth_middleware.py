import json
import hmac
from typing import Annotated

from fastapi import Depends, Header, HTTPException

from app.dbconfig.database import get_db
from app.utils.security import decode_access_token, platform_owner_credentials


def get_current_user(authorization: Annotated[str | None, Header()] = None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Please sign in to continue.")
    payload = decode_access_token(authorization[7:])
    if payload.get("identity_type", "tenant") != "tenant":
        raise HTTPException(status_code=403, detail="Platform-owner sessions cannot access a retailer workspace.")
    with get_db() as connection:
        user = connection.execute(
            """SELECT u.id, u.tenant_id, u.name, u.email, u.role, u.permissions
               FROM users u JOIN tenants t ON t.id = u.tenant_id
               WHERE u.id = ? AND u.tenant_id = ? AND t.status = 'active'""",
            (payload["id"], payload["tenant_id"]),
        ).fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="This account is no longer available.")
    result = dict(user)
    try:
        result["permissions"] = json.loads(result["permissions"] or "{}")
    except (TypeError, json.JSONDecodeError):
        result["permissions"] = {}
    return result


CurrentUser = Annotated[dict, Depends(get_current_user)]


def get_platform_owner(authorization: Annotated[str | None, Header()] = None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Please sign in as the product owner.")
    payload = decode_access_token(authorization[7:])
    if payload.get("identity_type") != "platform_owner" or payload.get("role") != "platform_owner":
        raise HTTPException(status_code=403, detail="Only the product owner can manage retailer workspaces.")
    owner_email, _ = platform_owner_credentials()
    if not owner_email or not hmac.compare_digest(payload.get("email", "").encode("utf-8"), owner_email.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Product-owner access is no longer valid.")
    return {"id": payload["id"], "email": owner_email, "name": "Product owner", "role": "platform_owner"}


PlatformOwner = Annotated[dict, Depends(get_platform_owner)]


def require_admin(user: CurrentUser):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only an admin can perform this action.")
    return user


def require_admin_or_permission(permission: str):
    def check(user: CurrentUser):
        if user["role"] != "admin" and not user.get("permissions", {}).get(permission, False):
            raise HTTPException(status_code=403, detail="Your account doesn't have permission for this action.")
        return user
    return check
