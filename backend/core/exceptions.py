from fastapi import HTTPException, Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from typing import cast


class AppException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, extra: dict | None = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.extra = extra or {}

async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    app_exc = cast(AppException, exc)
    content = {
        "code": app_exc.code,
        "message": app_exc.message,
        "status": app_exc.status_code,
    }
    content.update(app_exc.extra)
    return JSONResponse(
        status_code=app_exc.status_code,
        content=content,
    )
