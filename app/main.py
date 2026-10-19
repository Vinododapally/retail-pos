from pathlib import Path
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.controllers import api_router
from app.dbconfig.database import initialize_database
from app.logger.logging_config import configure_logging
from app.middleware.demo_read_only import DemoReadOnlyMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

configure_logging()
initialize_database()

app = FastAPI(title="Counterpoint POS API", version="1.0.0")
app.add_middleware(DemoReadOnlyMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,https://pos.openkarts.in",
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")

if DIST.is_dir() and (DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")


@app.get("/{path:path}", include_in_schema=False)
def serve_frontend(path: str):
    requested = (DIST / path).resolve()
    if DIST.is_dir() and requested.is_relative_to(DIST.resolve()) and requested.is_file():
        return FileResponse(requested)
    if DIST.is_dir() and (DIST / "index.html").is_file():
        return FileResponse(DIST / "index.html")
    raise HTTPException(status_code=404, detail="Frontend is not built yet. Run npm run build.")
