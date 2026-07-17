"""Modal deployment for AskGeorge.

Deploy with::

    modal deploy askgeorge/deploy_modal.py

Requires a Modal secret named ``askgeorge-secret`` holding GOOGLE_API_KEY and,
optionally, PUSHOVER_TOKEN / PUSHOVER_USER::

    modal secret create askgeorge-secret GOOGLE_API_KEY=... PUSHOVER_TOKEN=... PUSHOVER_USER=...
"""

from __future__ import annotations

from pathlib import Path

import modal

APP_NAME: str = "askgeorge"
LOCAL_DIR: Path = Path(__file__).parent

app = modal.App(APP_NAME)

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "gradio>=5.0",
        "openai>=1.60",
        "requests>=2.32",
        "python-dotenv>=1.0",
        "fastapi[standard]>=0.115",
    )
    .add_local_file(LOCAL_DIR / "app.py", remote_path="/root/app.py")
    .add_local_dir(LOCAL_DIR / "me", remote_path="/root/me")
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

    from app import build_demo

    return gr.mount_gradio_app(app=FastAPI(), blocks=build_demo(), path="/")
