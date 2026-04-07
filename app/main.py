from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.error_handlers import register_error_handlers
from app.core.middleware import TraceIdMiddleware, setup_logging


def create_app() -> FastAPI:
    setup_logging()

    application = FastAPI(title="Linky API", version="0.1.0")

    application.add_middleware(TraceIdMiddleware)
    register_error_handlers(application)
    application.include_router(api_router, prefix="/api/v1")

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    application.mount("/static/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

    @application.get("/health")
    def health_check():
        return {"status": "ok"}

    return application


app = create_app()
