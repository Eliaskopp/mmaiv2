"""Maps domain exceptions to HTTP responses.

Called once at startup via add_exception_handlers(app).
"""

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    EntityNotFoundError,
    QuotaExceededError,
    ValidationError,
)


def add_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(EntityNotFoundError)
    async def _entity_not_found(_request, exc: EntityNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.detail},
        )

    @app.exception_handler(AuthenticationError)
    async def _authentication_error(_request, exc: AuthenticationError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": exc.detail},
        )

    @app.exception_handler(ConflictError)
    async def _conflict_error(_request, exc: ConflictError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": exc.detail},
        )

    @app.exception_handler(ValidationError)
    async def _validation_error(_request, exc: ValidationError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.detail},
        )

    @app.exception_handler(QuotaExceededError)
    async def _quota_exceeded(_request, exc: QuotaExceededError):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": exc.detail},
        )
