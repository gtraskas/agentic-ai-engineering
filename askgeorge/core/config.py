"""Central configuration: paths, model settings, and environment accessors."""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_DIR: Path = Path(__file__).parent.parent
DATA_DIR: Path = PACKAGE_DIR / "me"
ASSETS_DIR: Path = PACKAGE_DIR / "ui" / "assets"

OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
# Fast, consistent, and cheap (~$0.10/M input tokens); with the global
# 100-messages/day rate cap the worst-case spend is pennies. The fallback
# is the best free model from the Aug 2026 benchmark (gemma: 4/4 clean
# runs, obeys formatting rules, correct tool calls, valid guardrail
# structured output), covering paid-model outages at zero cost.
DEFAULT_CHAT_MODEL: str = "google/gemini-3.1-flash-lite"
DEFAULT_FALLBACK_MODEL: str = "google/gemma-4-26b-a4b-it:free"
DEFAULT_REASONING_EFFORT: str = "low"
DEFAULT_TEMPERATURE: float = 0.7
MAX_TOOL_ROUNDS: int = 3

EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
SPARSE_EMBEDDING_MODEL: str = "Qdrant/bm25"
RAG_COLLECTION: str = "background"
RAG_TOP_K: int = 10
CHUNK_MAX_CHARS: int = 1_200

JOBFIT_MIN_CHARS: int = 120
JOBFIT_MAX_CHARS: int = 8_000

SMTP_HOST: str = "smtp.gmail.com"
SMTP_PORT: int = 465


def openrouter_api_key() -> str | None:
    """Return the OpenRouter API key, if configured."""
    return os.getenv("OPENROUTER_API_KEY")


def chat_model() -> str:
    """Return the chat model id, honoring the OPENROUTER_MODEL override."""
    return os.getenv("OPENROUTER_MODEL", DEFAULT_CHAT_MODEL)


def jobfit_model() -> str:
    """Return the job-fit model id (defaults to the chat model)."""
    return os.getenv("JOBFIT_MODEL", chat_model())


def fallback_model() -> str:
    """Return the paid fallback model id, honoring OPENROUTER_FALLBACK_MODEL.

    Used when the free primary model is rate-limited or its provider pool is
    down. The default is the model the app shipped with before the free
    default: one of the cheapest paid models on OpenRouter.
    """
    return os.getenv("OPENROUTER_FALLBACK_MODEL", DEFAULT_FALLBACK_MODEL)


def openrouter_extra_body(primary: str | None = None) -> dict[str, object]:
    """Return the OpenRouter extra body shared by every LLM call.

    Two concerns travel here. ``reasoning``: reasoning-capable models think
    silently before writing, which delays the first streamed token, so the
    effort is capped low (override with ASKGEORGE_REASONING). ``models``:
    OpenRouter's server-side fallback chain, so a rate-limited or unavailable
    free model silently falls through to the cheap paid fallback instead of
    failing the visitor's request.

    Args:
        primary: Model id the caller sends the request with; defaults to the
            chat model. The fallback is appended unless it is the primary.
    """
    effort = os.getenv("ASKGEORGE_REASONING", DEFAULT_REASONING_EFFORT)
    first = primary or chat_model()
    chain = [first] if first == fallback_model() else [first, fallback_model()]
    return {"reasoning": {"effort": effort}, "models": chain}


def temperature() -> float:
    """Return the sampling temperature: low keeps grounded answers consistent."""
    return float(os.getenv("ASKGEORGE_TEMPERATURE", str(DEFAULT_TEMPERATURE)))


def agent_backend() -> str:
    """Return the selected agent backend: 'sdk' (default) or 'scratch'."""
    return os.getenv("AGENT_BACKEND", "sdk").strip().lower()


def rag_enabled() -> bool:
    """Return True unless RAG is disabled with ASKGEORGE_RAG=0."""
    return os.getenv("ASKGEORGE_RAG", "1") != "0"


def guardrail_enabled() -> bool:
    """Return True unless the input guardrail is disabled with ASKGEORGE_GUARDRAIL=0."""
    return os.getenv("ASKGEORGE_GUARDRAIL", "1") != "0"


def booking_url() -> str | None:
    """Return the Google Calendar booking-page URL, if configured."""
    return os.getenv("CALENDAR_BOOKING_URL")
