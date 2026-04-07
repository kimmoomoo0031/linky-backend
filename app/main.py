from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.error_handlers import register_error_handlers
from app.core.middleware import TraceIdMiddleware, setup_logging


def create_app() -> FastAPI:
    setup_logging()

    application = FastAPI(title="Linky API", version="0.1.0")

    application.add_middleware(TraceIdMiddleware)
    register_error_handlers(application)
    application.include_router(api_router, prefix="/api/v1")

    @application.get("/health")
    def health_check():
        return {"status": "ok"}

    return application


app = create_app()
