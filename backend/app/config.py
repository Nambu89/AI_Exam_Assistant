"""Central configuration.

The app runs in two modes, selected by ``MODEL_PROVIDER``:

* ``local``       — no Azure required. Uses a deterministic echo client so the
                    full agent graph, API and tests run offline. Great for a
                    first clone-and-run experience and for CI.
* ``openai``      — OpenAI-hosted GPT-5 family (needs ``OPENAI_API_KEY``).
* ``azure_openai``— Azure OpenAI deployment (key or Entra credential).
* ``foundry``     — Azure AI Foundry project (Hosted Agents + Foundry IQ),
                    authenticated with a Microsoft Entra credential.

Microsoft Agent Framework does NOT auto-load ``.env`` (documented behaviour),
so we load it explicitly here at import time.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from the backend root before Settings is instantiated.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_BACKEND_ROOT / ".env")

REPO_ROOT = _BACKEND_ROOT.parent


class ModelProvider(str, Enum):
    LOCAL = "local"
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    FOUNDRY = "foundry"


class KnowledgeBackend(str, Enum):
    """Which retrieval engine powers grounding.

    * ``graphrag`` — local GraphRAG project (works offline, powers the concept
      map and global "what are the main topics" queries).
    * ``foundry_iq`` — Azure AI Foundry knowledge base with agentic retrieval.
    * ``auto`` — prefer Foundry IQ when a Foundry endpoint is configured,
      otherwise fall back to GraphRAG.
    """

    GRAPHRAG = "graphrag"
    FOUNDRY_IQ = "foundry_iq"
    AUTO = "auto"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    app_name: str = "AI Exam Assistant"
    environment: str = Field(default="development")
    cors_origins: str = Field(default="http://localhost:5173,http://localhost:3000")

    # --- Provider selection ---
    model_provider: ModelProvider = Field(default=ModelProvider.LOCAL)
    knowledge_backend: KnowledgeBackend = Field(default=KnowledgeBackend.AUTO)

    # --- Model deployments (GPT-5 family; never GPT-4, per project policy) ---
    # Tutor / general reasoning.
    chat_model: str = Field(default="gpt-5.4-mini")
    # Cheap classification / routing (coordinator) and GraphRAG entity extraction.
    router_model: str = Field(default="gpt-5-nano")
    # Deep reasoning: essay correction, hard-question validation.
    reasoning_model: str = Field(default="gpt-5.5")
    # Judge model for evaluations (Microsoft's documented recommendation).
    judge_model: str = Field(default="gpt-5-mini")
    embedding_model: str = Field(default="text-embedding-3-large")

    # --- OpenAI provider ---
    openai_api_key: str = Field(default="")

    # --- Azure OpenAI provider ---
    azure_openai_endpoint: str = Field(default="")
    azure_openai_api_key: str = Field(default="")
    azure_openai_api_version: str = Field(default="2024-10-21")

    # --- Azure AI Foundry provider (Hosted Agents + Foundry IQ) ---
    # e.g. https://<resource>.services.ai.azure.com/api/projects/<project>
    foundry_project_endpoint: str = Field(default="")
    # Azure AI Search service backing the Foundry IQ knowledge base.
    azure_search_endpoint: str = Field(default="")
    foundry_knowledge_base: str = Field(default="")

    # --- GraphRAG ---
    graphrag_root: Path = Field(default=_BACKEND_ROOT / "graphrag")

    # --- Guardrails ---
    enable_content_safety: bool = Field(default=True)
    azure_content_safety_endpoint: str = Field(default="")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_offline(self) -> bool:
        return self.model_provider == ModelProvider.LOCAL


@lru_cache
def get_settings() -> Settings:
    return Settings()
