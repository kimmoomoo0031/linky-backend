import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.core.exceptions import AppError
from app.core.middleware import get_trace_id

logger = logging.getLogger(__name__)


def _build_error_body(
    trace_id: str,
    path: str,
    method: str,
    code: str,
    message: str,
    details: list[dict] | None = None,
) -> dict:
    body: dict = {
        "success": False,
        "trace_id": trace_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "path": path,
        "method": method,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if details:
        body["error"]["details"] = details
    return body


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    body = _build_error_body(
        trace_id=get_trace_id(),
        path=request.url.path,
        method=request.method,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )
    logger.warning("AppError %s %s: %s", exc.status_code, exc.code, exc.message)
    return JSONResponse(status_code=exc.status_code, content=body)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err.get("loc", []) if loc != "body")
        details.append({"field": field, "message": err.get("msg", "")})

    body = _build_error_body(
        trace_id=get_trace_id(),
        path=request.url.path,
        method=request.method,
        code="COMMON_BAD_REQUEST",
        message="入力値を確認してください。",
        details=details,
    )
    return JSONResponse(status_code=400, content=body)


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    body = _build_error_body(
        trace_id=get_trace_id(),
        path=request.url.path,
        method=request.method,
        code="COMMON_INTERNAL_ERROR",
        message="サーバー内部エラーが発生しました。",
    )
    return JSONResponse(status_code=500, content=body)


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code_map = {
        400: "COMMON_BAD_REQUEST",
        404: "COMMON_NOT_FOUND",
        405: "COMMON_METHOD_NOT_ALLOWED",
    }
    body = _build_error_body(
        trace_id=get_trace_id(),
        path=request.url.path,
        method=request.method,
        code=code_map.get(exc.status_code, f"COMMON_HTTP_{exc.status_code}"),
        message=str(exc.detail) if exc.detail else "エラーが発生しました。",
    )
    return JSONResponse(status_code=exc.status_code, content=body)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
