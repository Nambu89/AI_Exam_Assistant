"""FastAPI application entry point.

Run locally (offline, no credentials):
    MODEL_PROVIDER=local uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import router
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description=(
        "Open-source multi-agent AI Exam Assistant — Microsoft Agent Framework, "
        "Azure AI Foundry (Foundry IQ) and GraphRAG."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root() -> dict:
    return {"name": settings.app_name, "version": __version__, "docs": "/docs", "api": "/api"}
