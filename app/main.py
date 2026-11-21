from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo

import httpx
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.logging_config import configure_logging
from app.platforms import build_platforms
from app.routers import posting
from app.schemas import ValidationErrorDetail, ValidationErrorResponse
from app.services.posting_service import PostingService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_file)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # One shared HTTP client for every platform call, closed cleanly on shutdown.
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as http:
            app.state.posting_service = PostingService(
                platforms=build_platforms(settings, http),
                timezone=ZoneInfo(settings.app_timezone),
            )
            yield

    app = FastAPI(
        title=settings.app_name,
        description="Publish one short message with a CTA link to several platforms in a single request.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.include_router(posting.router)
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        return {"service": settings.app_name, "docs": "/docs"}

    @app.get("/health", tags=["Health"], summary="Check that the service is running")
    async def health() -> dict:
        return {"status": "ok"}

    return app


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Turn FastAPI's validation errors into a short list of field and message pairs."""
    errors = []
    for error in exc.errors():
        location = [str(part) for part in error["loc"] if part != "body"]
        message = error["msg"].removeprefix("Value error, ")
        if error["type"] == "missing":
            message = "This field is required."
        elif error["type"] == "string_too_long":
            message = f"Must not exceed {error['ctx']['max_length']} characters."
        elif error["type"] == "string_too_short":
            message = "Must not be empty."
        elif error["type"] == "extra_forbidden":
            message = "Unexpected field. Platforms are selected by the server, so only 'message' is accepted."
        elif error["type"] == "json_invalid":
            message = "Request body is not valid JSON."
        errors.append(ValidationErrorDetail(field=".".join(location) or "body", message=message))

    body = ValidationErrorResponse(errors=errors)
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content=body.model_dump())


app = create_app()
