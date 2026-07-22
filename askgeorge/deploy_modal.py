"""Modal deployment for AskGeorge.

Deploy with::

    modal deploy askgeorge/deploy_modal.py

Requires a Modal secret named ``askgeorge-secret`` holding OPENROUTER_API_KEY
and, optionally, GMAIL_ADDRESS / GMAIL_APP_PASSWORD (email notifications) and
CALENDAR_BOOKING_URL (intro-call booking link)::

    modal secret create askgeorge-secret OPENROUTER_API_KEY=... \
        GMAIL_ADDRESS=... GMAIL_APP_PASSWORD=... CALENDAR_BOOKING_URL=...
"""

from __future__ import annotations

from pathlib import Path

import modal

APP_NAME: str = "askgeorge"
PACKAGE_DIR: Path = Path(__file__).parent
EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"

app = modal.App(APP_NAME)

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "gradio>=6.0,<7",
        "openai>=1.60",
        "openai-agents>=0.2",
        "qdrant-client[fastembed]>=1.12",
        "python-dotenv>=1.0",
        "fastapi[standard]>=0.115",
    )
    # Bake both embedding models into the image so cold starts skip downloads.
    .run_commands(
        "python -c \"from fastembed import TextEmbedding, SparseTextEmbedding; "
        f"TextEmbedding('{EMBEDDING_MODEL}'); SparseTextEmbedding('Qdrant/bm25')\""
    )
    .add_local_dir(
        PACKAGE_DIR,
        remote_path="/root/askgeorge",
        ignore=["__pycache__", "*.pyc", ".DS_Store"],
    )
)


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("askgeorge-secret")],
    min_containers=0,
    timeout=600,
)
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def web() -> "FastAPI":  # noqa: F821 — imported inside the Modal container
    """Serve the Gradio chat UI as an ASGI app on Modal."""
    import gradio as gr
    from fastapi import FastAPI

    from askgeorge.app import build_demo
    from askgeorge.ui.theme import serve_kwargs

    return gr.mount_gradio_app(
        app=FastAPI(), blocks=build_demo(), path="/", **serve_kwargs()
    )
