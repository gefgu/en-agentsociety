import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Optional

from fastapi import APIRouter, FastAPI, HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette.middleware.sessions import SessionMiddleware

from .api import api_router
from .models._base import Base
from ..configs import EnvConfig

__all__ = ["create_app", "empty_get_tenant_id"]

_script_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_script_dir)


async def empty_get_tenant_id(_: Request) -> str:
    return ""


def create_app(
    pg_dsn: str,
    mlflow_url: str,
    read_only: bool,
    env: EnvConfig,
    get_tenant_id: Callable[[Request], Awaitable[str]] = empty_get_tenant_id,
    more_router: Optional[APIRouter] = None,
    more_state: Dict[str, Any] = {},
    session_secret_key: str = "agentsociety-session",
):

    # https://fastapi.tiangolo.com/advanced/events/#use-case
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Init database when app starts
        engine = create_async_engine(pg_dsn)
        session_factory = async_sessionmaker(engine)
        # test the postgres connection
        try:
            async with engine.connect() as conn:
                pass
        except Exception as e:
            raise Exception(
                f"Failed to connect to postgresql database: {e}. Please check the connection string: {pg_dsn}"
            )
        # save session_factory to app state
        app.state.get_db = session_factory

        # save read_only to app state
        app.state.read_only = read_only
        # save mlflow_url to app state
        app.state.mlflow_url = mlflow_url
        # save env to app state
        app.state.env = env

        # Hook to get tenant_id
        app.state.get_tenant_id = get_tenant_id

        # save more_state to app state
        for k, v in more_state.items():
            setattr(app.state, k, v)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield

    # 创建FastAPI应用
    app = FastAPI(
        title="AgentSociety WebUI API",
        lifespan=lifespan,
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # https://stackoverflow.com/questions/75958222/can-i-return-400-error-instead-of-422-error
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(ValidationError)
    async def validation_pydantic_exception_handler(
        request: Request, exc: ValidationError
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": jsonable_encoder(exc.errors())},
        )

    app.include_router(api_router)
    if more_router is not None:
        app.include_router(more_router)

    app.add_middleware(
        SessionMiddleware,
        secret_key=session_secret_key,
        session_cookie="agentsociety-session",
    )

    # serve frontend files
    frontend_path = Path(_parent_dir) / "_dist"
    app.mount("/", StaticFiles(directory=frontend_path, html=True))

    # 404 handler, redirect all 404 to index.html except /api
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: HTTPException):
        if not request.url.path.startswith("/api"):
            return FileResponse(frontend_path / "index.html")
        # change the exception to JSONResponse
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": jsonable_encoder(exc.detail)},
        )

    return app
