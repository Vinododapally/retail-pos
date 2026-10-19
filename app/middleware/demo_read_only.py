from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.dbconfig.database import get_db
from app.utils.security import decode_access_token


class DemoReadOnlyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path.startswith("/api/") and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            authorization = request.headers.get("authorization", "")
            if authorization.startswith("Bearer "):
                try:
                    payload = decode_access_token(authorization[7:])
                except HTTPException:
                    payload = {}
                if payload.get("identity_type", "tenant") == "tenant":
                    with get_db() as connection:
                        demo_user = connection.execute(
                            """SELECT 1 FROM users u JOIN tenants t ON t.id = u.tenant_id
                               WHERE u.id = ? AND u.tenant_id = ? AND u.is_demo = 1 AND t.is_demo = 1""",
                            (payload.get("id"), payload.get("tenant_id")),
                        ).fetchone()
                    if demo_user:
                        return JSONResponse(
                            status_code=403,
                            content={"detail": "The public demo shop is read-only. Create a retailer workspace to make changes."},
                        )
        return await call_next(request)
