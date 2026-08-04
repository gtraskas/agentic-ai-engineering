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

from collections.abc import Callable
from pathlib import Path
from typing import Any

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


class RootHtmlRewriter:
    """ASGI middleware that post-processes the landing page HTML.

    Gradio's SPA shell hardcodes its own og:/twitter: meta tags ahead of any
    custom head content, and link crawlers honor the first tag they meet, so
    the served HTML itself must be rewritten. Only ``GET /`` is buffered and
    rewritten; every other path, including Gradio's streaming queue, passes
    through untouched.
    """

    def __init__(self, app: Any, rewrite: Callable[[str], str]) -> None:
        self._app = app
        self._rewrite = rewrite

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        """Serve one ASGI request, rewriting the root page's HTML body."""
        if scope.get("type") != "http" or scope.get("path") != "/":
            await self._app(scope, receive, send)
            return
        start_message: dict[str, Any] = {}
        body_chunks: list[bytes] = []

        async def capture(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                start_message.update(message)
            elif message["type"] == "http.response.body":
                body_chunks.append(message.get("body", b""))

        await self._app(scope, receive, capture)
        body = b"".join(body_chunks)
        headers = [
            (name, value)
            for name, value in start_message.get("headers", [])
            if name.lower() != b"content-length"
        ]
        is_html = any(
            value.startswith(b"text/html")
            for name, value in headers
            if name.lower() == b"content-type"
        )
        if is_html:
            body = self._rewrite(body.decode("utf-8")).encode("utf-8")
        headers.append((b"content-length", str(len(body)).encode("ascii")))
        await send({**start_message, "headers": headers})
        await send({"type": "http.response.body", "body": body})


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("askgeorge-secret")],
    # One container stays warm so no visitor ever waits for a boot and
    # index build (~$10/month, inside the Starter plan's free credits).
    min_containers=1,
    timeout=600,
)
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def web() -> FastAPI:  # noqa: F821 — imported inside the Modal container
    """Serve the Gradio chat UI as an ASGI app on Modal."""
    import gradio as gr
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles

    from askgeorge.app import build_demo
    from askgeorge.core.config import ASSETS_DIR
    from askgeorge.ui.theme import rewrite_social_meta, serve_kwargs

    # /media serves the link-preview card (og_card.jpg). Not /static:
    # Gradio serves its own frontend assets there.
    fastapi_app = FastAPI()
    fastapi_app.mount("/media", StaticFiles(directory=ASSETS_DIR), name="media")
    fastapi_app.add_middleware(RootHtmlRewriter, rewrite=rewrite_social_meta)
    return gr.mount_gradio_app(
        app=fastapi_app, blocks=build_demo(), path="/", **serve_kwargs()
    )
