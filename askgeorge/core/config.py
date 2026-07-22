"""Central configuration: paths, model settings, and environment accessors."""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_DIR: Path = Path(__file__).parent.parent
DATA_DIR: Path = PACKAGE_DIR / "me"
ASSETS_DIR: Path = PACKAGE_DIR / "ui" / "assets"

OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
DEFAULT_CHAT_MODEL: str = "google/gemini-3.1-flash-lite"
DEFAULT_REASONING_EFFORT: str = "low"
DEFAULT_TEMPERATURE: float = 0.2
MAX_TOOL_ROUNDS: int = 3

EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
RAG_COLLECTION: str = "background"
RAG_TOP_K: int = 8
CHUNK_MAX_CHARS: int = 1_200

SMTP_HOST: str = "smtp.gmail.com"
SMTP_PORT: int = 465


def openrouter_api_key() -> str | None:
    """Return the OpenRouter API key, if configured."""
    return os.getenv("OPENROUTER_API_KEY")


def chat_model() -> str:
    """Return the chat model id, honoring the OPENROUTER_MODEL override."""
    return os.getenv("OPENROUTER_MODEL", DEFAULT_CHAT_MODEL)


def reasoning_extra_body() -> dict[str, dict[str, str]]:
    """Return OpenRouter extra body capping hidden 'thinking' for fast replies.

    Reasoning-capable models (Gemini 3.x, GPT-5 family) think silently before
    writing, which delays the first streamed token. Low effort keeps replies
    snappy; override with ASKGEORGE_REASONING (e.g. 'medium', 'high').
    """
    effort = os.getenv("ASKGEORGE_REASONING", DEFAULT_REASONING_EFFORT)
    return {"reasoning": {"effort": effort}}


def temperature() -> float:
    """Return the sampling temperature: low keeps grounded answers consistent."""
    return float(os.getenv("ASKGEORGE_TEMPERATURE", str(DEFAULT_TEMPERATURE)))


def agent_backend() -> str:
    """Return the selected agent backend: 'sdk' (default) or 'scratch'."""
    return os.getenv("AGENT_BACKEND", "sdk").strip().lower()


def rag_enabled() -> bool:
    """Return True unless RAG is disabled with ASKGEORGE_RAG=0."""
    return os.getenv("ASKGEORGE_RAG", "1") != "0"


def booking_url() -> str | None:
    """Return the Google Calendar booking-page URL, if configured."""
    return os.getenv("CALENDAR_BOOKING_URL")
