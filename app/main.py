from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from app.adapters.ai_coach import AiCoach, AiProvider, MockAiProvider, OllamaProvider
from app.application.review_service import ReviewService
from app.domain.errors import DomainError
from app.storage.repository import ReviewRepository


APP_DIR = Path(__file__).resolve().parent
WEB_DIR = APP_DIR / "web"


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    goal: str = Field(default="", max_length=200)
    request_ai: bool = True


class CompareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str


def _default_provider() -> AiProvider:
    if os.getenv("CODE_COACH_AI_PROVIDER", "mock").lower() == "ollama":
        return OllamaProvider(
            endpoint=os.getenv(
                "CODE_COACH_OLLAMA_ENDPOINT",
                "http://127.0.0.1:11435/api/chat",
            ),
            model=os.getenv("CODE_COACH_OLLAMA_MODEL", "qwen3.5:4b"),
        )
    return MockAiProvider()


def create_app(
    *,
    database_path: str | Path | None = None,
    ai_provider: AiProvider | None = None,
) -> FastAPI:
    if database_path is None:
        database_path = os.getenv("CODE_COACH_DB_PATH", "data/code_coach.db")
    repository = ReviewRepository(database_path)
    service = ReviewService(
        repository=repository,
        ai_coach=AiCoach(provider=ai_provider or _default_provider()),
    )

    application = FastAPI(
        title="code_coach",
        version="0.3.0",
        description="Local C++ to Python learning assistant",
    )
    application.state.review_service = service
    application.mount(
        "/static",
        StaticFiles(directory=WEB_DIR / "static"),
        name="static",
    )

    @application.exception_handler(DomainError)
    async def handle_domain_error(
        request: Request,
        error: DomainError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content={"error": error.error, "message": error.message},
        )

    @application.get("/", include_in_schema=False)
    def web_entrypoint() -> FileResponse:
        return FileResponse(WEB_DIR / "index.html", media_type="text/html")

    @application.get("/favicon.ico", include_in_schema=False)
    def favicon() -> Response:
        return Response(status_code=204)

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "code_coach"}

    @application.post("/api/reviews", status_code=201)
    def create_review(payload: ReviewRequest) -> dict:
        review = service.review(
            payload.code,
            goal=payload.goal,
            request_ai=payload.request_ai,
        )
        return review.to_dict()

    @application.post("/api/reviews/{review_id}/compare")
    def compare_review(review_id: str, payload: CompareRequest) -> dict:
        comparison = service.compare(review_id, payload.code)
        return comparison.to_dict()

    @application.get("/api/reviews/{review_id}/report")
    def review_report(review_id: str) -> Response:
        markdown = service.report(review_id)
        return Response(
            content=markdown,
            media_type="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="code_coach_{review_id}.md"'
                )
            },
        )

    return application


app = create_app()
