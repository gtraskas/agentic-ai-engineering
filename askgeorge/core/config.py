"""Central configuration: paths, model settings, and environment accessors."""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_DIR: Path = Path(__file__).parent.parent
DATA_DIR: Path = PACKAGE_DIR / "me"
PRIVATE_DATA_DIR: Path = DATA_DIR / "private"
ASSETS_DIR: Path = PACKAGE_DIR / "ui" / "assets"

OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
DEFAULT_CHAT_MODEL: str = "google/gemini-3.5-flash"
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


def agent_backend() -> str:
    """Return the selected agent backend: 'scratch' (default) or 'sdk'."""
    return os.getenv("AGENT_BACKEND", "scratch").strip().lower()


def rag_enabled() -> bool:
    """Return True unless RAG is disabled with ASKGEORGE_RAG=0."""
    return os.getenv("ASKGEORGE_RAG", "1") != "0"


def booking_url() -> str | None:
    """Return the Google Calendar booking-page URL, if configured."""
    return os.getenv("CALENDAR_BOOKING_URL")
