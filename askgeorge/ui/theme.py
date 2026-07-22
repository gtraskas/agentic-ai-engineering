"""Aegean Minimal design: theme, CSS, and the full Gradio layout.

Off-white canvas, deep navy ink, Aegean sky accent — a calm, bright
professional portfolio look. Inter for text, JetBrains Mono for code.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Callable

import gradio as gr

from askgeorge.core.config import ASSETS_DIR

ACCENT: str = "#0EA5E9"
INK: str = "#0F172A"
CANVAS: str = "#FAFAF8"

AEGEAN_CSS: str = f"""
.gradio-container {{
    max-width: 880px !important;
    margin: 0 auto !important;
}}
#ag-header {{
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 22px 26px;
    background: linear-gradient(135deg, #FFFFFF 0%, #F0F9FF 100%);
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}}
#ag-header img.ag-photo {{
    width: 84px;
    height: 84px;
    border-radius: 50%;
    object-fit: cover;
    border: 3px solid {ACCENT};
}}
#ag-header .ag-name {{
    font-size: 1.45rem;
    font-weight: 700;
    color: {INK};
    margin: 0;
}}
#ag-header .ag-headline {{
    font-size: 0.92rem;
    color: #475569;
    margin: 4px 0 10px 0;
}}
#ag-header .ag-badge {{
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #047857;
    background: #ECFDF5;
    border: 1px solid #A7F3D0;
    border-radius: 999px;
    padding: 3px 10px;
    margin-right: 8px;
}}
#ag-header a.ag-link {{
    font-size: 0.85rem;
    font-weight: 600;
    color: {ACCENT};
    text-decoration: none;
    margin-right: 14px;
}}
#ag-header a.ag-link:hover {{
    text-decoration: underline;
}}
#ag-footer {{
    text-align: center;
    font-size: 0.8rem;
    color: #94A3B8;
    padding-top: 6px;
}}
"""


def build_theme() -> gr.themes.Base:
    """Return the Aegean Minimal Gradio theme."""
    return gr.themes.Soft(
        primary_hue="sky",
        neutral_hue="slate",
        font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
        font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "monospace"],
    ).set(
        body_background_fill=CANVAS,
        body_text_color=INK,
        button_primary_background_fill=ACCENT,
        button_primary_text_color="#FFFFFF",
    )


def _photo_data_uri(assets_dir: Path = ASSETS_DIR) -> str | None:
    """Return the profile photo as a base64 data URI, if present."""
    for name in ("photo.jpg", "photo.jpeg", "photo.png"):
        path = assets_dir / name
        if path.exists():
            suffix = "png" if path.suffix == ".png" else "jpeg"
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            return f"data:image/{suffix};base64,{encoded}"
    return None


def _header_html() -> str:
    """Build the header card: photo, name, headline, badge, and links."""
    photo_uri = _photo_data_uri()
    photo_tag = f'<img class="ag-photo" src="{photo_uri}" alt="George Traskas" />' if photo_uri else ""
    return f"""
    <div id="ag-header">
        {photo_tag}
        <div>
            <p class="ag-name">George Traskas</p>
            <p class="ag-headline">Data Scientist &amp; AI/ML Engineer · Python · LLMs · RAG · Agentic AI · AWS</p>
            <span class="ag-badge">Open to work</span>
            <a class="ag-link" href="https://www.linkedin.com/in/george-traskas/" target="_blank" rel="noopener">LinkedIn</a>
            <a class="ag-link" href="https://github.com/gtraskas" target="_blank" rel="noopener">GitHub</a>
            <a class="ag-link" href="mailto:georgiost77@gmail.com">Email</a>
        </div>
    </div>
    """


def serve_kwargs() -> dict[str, Any]:
    """Return the theme/css kwargs for ``launch()`` or ``mount_gradio_app()``.

    Gradio 6 applies theme and CSS at serve time, not at Blocks construction.
    """
    return {"theme": build_theme(), "css": AEGEAN_CSS}


def build_ui(chat_fn: Callable[..., Any]) -> gr.Blocks:
    """Assemble the complete AskGeorge page around the chat function.

    Args:
        chat_fn: Streaming chat callable (sync or async generator) with the
            Gradio ChatInterface signature (message, history).

    Returns:
        A :class:`gr.Blocks` page; serve it with :func:`serve_kwargs` applied.
    """
    cv_path = ASSETS_DIR / "cv.pdf"
    with gr.Blocks(title="AskGeorge") as demo:
        gr.HTML(_header_html())
        if cv_path.exists():
            gr.DownloadButton("Download CV (PDF)", value=str(cv_path), size="sm")
        gr.ChatInterface(
            fn=chat_fn,
            description=(
                "Hi, I'm George's AI representative — ask me anything about his "
                "experience, projects, and skills."
            ),
            examples=[
                "What is your experience with RAG in production?",
                "Tell me about your most recent project.",
                "Why should we hire you as an AI engineer?",
                "Are you open to remote roles?",
            ],
        )
        gr.HTML('<div id="ag-footer">AskGeorge — AI representative of George Traskas</div>')
    return demo
