"""FastAPI entrypoint for Local Planner."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

from config import settings
from ollama_client import PlannerBackendError, check_ollama
from schemas import FinalPlan, UserQueryRequest
from state_manager import PlannerStateManager

BASE_DIR = Path(__file__).resolve().parent

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        summary="Local-first hierarchical planning with Ollama.",
        description=(
            "Convert a fuzzy objective into a validated Epic → Story → Task → Sub-task plan "
            "without sending prompts to a hosted LLM provider."
        ),
        docs_url=None,
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

    @app.get("/docs", include_in_schema=False)
    async def custom_docs():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=f"{settings.app_name} API Docs",
            swagger_js_url="/static/swagger/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger/swagger-ui.css",
        )

    @app.get("/health/live", tags=["health"])
    async def liveness() -> dict[str, str]:
        return {"status": "ok", "version": settings.app_version}

    @app.get("/health/ready", tags=["health"])
    async def readiness() -> dict[str, object]:
        backend = await check_ollama()
        if not backend["ok"]:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"status": "not_ready", "ollama": backend},
            )
        return {"status": "ready", "ollama": backend}

    @app.post("/api/v1/plan-query", response_model=FinalPlan, tags=["planning"])
    async def plan_user_query(request: UserQueryRequest) -> FinalPlan:
        try:
            return await PlannerStateManager(request).build_plan()
        except PlannerBackendError as exc:
            logger.warning("Planner backend failure: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        except Exception as exc:
            logger.exception("Unexpected planning failure")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Planning failed unexpectedly. Check server logs for details.",
            ) from exc

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
