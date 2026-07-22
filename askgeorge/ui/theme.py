"""Aegean Minimal design: theme, CSS, and the full Gradio layout.

Off-white canvas, deep navy ink, Aegean sky accent — a calm, bright
professional portfolio look. Inter for text, JetBrains Mono for code.
"""

from __future__ import annotations

import base64
import inspect
import logging
from pathlib import Path
from typing import Any, Callable

import gradio as gr

from askgeorge.core.config import ASSETS_DIR, booking_url
from askgeorge.core.ratelimit import RateLimiter

logger = logging.getLogger(__name__)

ACCENT: str = "#0EA5E9"
INK: str = "#0F172A"
CANVAS: str = "#FAFAF8"
CHAT_HEIGHT: int = 440
CALENDAR_HEIGHT: int = 620

REPO_URL: str = "https://github.com/gtraskas/agentic-ai-engineering"

PROJECT_LINKS: list[tuple[str, str]] = [
    ("MolekitChen · App Store", "https://apps.apple.com/us/app/molekitchen/id6773031788"),
    ("MolekitChen · site", "https://molekitchen-landing.pages.dev"),
    ("Wine-VFM · live demo", "https://gtraskas--wine-vfm-app-web.modal.run"),
    ("Wine-VFM · code", "https://github.com/gtraskas/wine-vfm"),
    ("AskGeorge · code", REPO_URL),
]

CV_FILES: list[tuple[str, str]] = [
    ("Download CV — AI/ML Engineer", "Georgios_Traskas_AI_ML_Engineer.pdf"),
    ("Download CV — Data Scientist", "Georgios_Traskas_Data_Scientist.pdf"),
]

TECH_CHIPS: list[str] = [
    "Python",
    "OpenAI Agents SDK",
    "Hybrid RAG · Qdrant + BM25",
    "FastEmbed",
    "LLM Guardrails",
    "Rate Limiting",
    "Golden-set Evals",
    "OpenRouter",
    "Gradio",
    "Modal",
    "GitHub Actions CI/CD",
    "uv",
]

AEGEAN_CSS: str = f"""
.gradio-container {{
    max-width: 880px !important;
    margin: 0 auto !important;
}}
#ag-header {{
    display: flex;
    align-items: center;
    gap: 24px;
    padding: 26px 30px;
    background: linear-gradient(160deg, #FFFFFF 0%, #F8FAFC 70%, #F0F9FF 100%);
    border: 1px solid #E8EDF3;
    border-radius: 18px;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 24px rgba(15, 23, 42, 0.04);
}}
#ag-header img.ag-photo {{
    width: 92px;
    height: 92px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid #FFFFFF;
    outline: 2px solid {ACCENT};
    outline-offset: 2px;
}}
#ag-header .ag-name {{
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: -0.02em;
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
#ag-header .ag-projects {{
    margin-top: 8px;
}}
#ag-header a.ag-chip,
#ag-stack .ag-tech {{
    display: inline-block;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.01em;
    color: #334155;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 4px 12px;
    margin: 2px 6px 2px 0;
    text-decoration: none;
    transition: border-color 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
}}
#ag-header a.ag-chip:hover {{
    border-color: {ACCENT};
    color: {ACCENT};
    box-shadow: 0 2px 8px rgba(14, 165, 233, 0.15);
}}
.ag-label {{
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: #64748B;
    margin: 0 0 12px 0;
}}
#ag-subtitle {{
    text-align: center;
    font-size: 0.95rem;
    color: #475569;
    padding: 2px 0 6px 0;
}}
/* One uniform chat box: hide label, strip per-message chrome (selectors
   verified against Gradio 6's rendered DOM: .message-row.panel.user-row/.bot-row) */
#ag-chat .label-wrap, #ag-chat label {{
    display: none !important;
}}
#ag-chat {{
    background: #FFFFFF;
}}
#ag-chat .message-row.panel {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    margin: 0 !important;
    padding: 8px 12px !important;
}}
#ag-chat .message-row.panel .flex-wrap,
#ag-chat .message-row.panel .role,
#ag-chat .message-row .message {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
/* Same side, same box for both roles; a slim accent bar marks the visitor */
#ag-chat .user-row {{
    justify-content: flex-start !important;
}}
#ag-chat .user-row > * {{
    border-left: 3px solid {ACCENT} !important;
    padding-left: 12px !important;
}}
#ag-chat .user-row * {{
    color: #334155 !important;
    font-weight: 600;
}}
/* Example questions: chip-styled, pinned to the bottom of the empty chat.
   panel-wrap needs full height or placeholder-content's 100% resolves to 0. */
#ag-chat .panel-wrap {{
    height: 100% !important;
}}
#ag-chat .placeholder-content {{
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-end !important;
    height: 100% !important;
}}
#ag-chat .examples {{
    justify-content: center !important;
    gap: 8px;
    padding-bottom: 10px;
}}
#ag-chat .example {{
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 999px;
    padding: 6px 14px;
}}
#ag-chat .example:hover {{
    border-color: {ACCENT};
}}
#ag-book {{
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 18px 22px;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}}
#ag-book {{
    border-radius: 18px;
}}
#ag-book iframe {{
    width: 100%;
    height: {CALENDAR_HEIGHT}px;
    border: 0;
    border-radius: 10px;
}}
#ag-stack {{
    text-align: center;
    padding: 14px 0 4px 0;
}}
#ag-stack .ag-stack-line {{
    font-size: 0.82rem;
    color: #64748B;
    margin-bottom: 8px;
}}
#ag-stack a {{
    color: {ACCENT};
    text-decoration: none;
    font-weight: 600;
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


def serve_kwargs() -> dict[str, Any]:
    """Return the theme/css kwargs for ``launch()`` or ``mount_gradio_app()``.

    Gradio 6 applies theme and CSS at serve time, not at Blocks construction.
    """
    return {"theme": build_theme(), "css": AEGEAN_CSS}


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
    """Build the header card: photo, name, headline, badge, links, and projects."""
    photo_uri = _photo_data_uri()
    photo_tag = f'<img class="ag-photo" src="{photo_uri}" alt="George Traskas" />' if photo_uri else ""
    project_chips = "".join(
        f'<a class="ag-chip" href="{url}" target="_blank" rel="noopener">{label}</a>'
        for label, url in PROJECT_LINKS
    )
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
            <div class="ag-projects">{project_chips}</div>
        </div>
    </div>
    """


def _booking_embed_src(url: str) -> str:
    """Return an embeddable form of a Google Calendar booking link.

    Short share links (calendar.app.google/...) redirect to a long URL that
    Google blocks inside iframes (X-Frame-Options: SAMEORIGIN). The embeddable
    form — verified against Google's response headers — is
    ``calendar.google.com/calendar/appointments/schedules/<id>?gv=true``, so
    short links are resolved once at startup and rewritten to it.
    """
    resolved = url
    if "calendar.app.google" in url:
        try:
            import httpx

            response = httpx.head(url, follow_redirects=False, timeout=10)
            location = response.headers.get("location", "")
            if "/appointments/schedules/" in location:
                schedule_id = location.rsplit("/", 1)[-1]
                resolved = (
                    "https://calendar.google.com/calendar/appointments/"
                    f"schedules/{schedule_id}"
                )
        except httpx.HTTPError as exc:
            logger.warning("Could not resolve booking short link: %s", exc)
    separator = "&" if "?" in resolved else "?"
    return resolved if "gv=true" in resolved else f"{resolved}{separator}gv=true"


def _booking_html(url: str) -> str:
    """Build the embedded Google Calendar booking section."""
    return f"""
    <div id="ag-book">
        <p class="ag-label">Book an intro call</p>
        <iframe src="{_booking_embed_src(url)}" title="Book an intro call with George"></iframe>
    </div>
    """


def _stack_html() -> str:
    """Build the tech chip strip: one-line pitch + linked technology chips."""
    chips = "".join(f'<span class="ag-tech">{chip}</span>' for chip in TECH_CHIPS)
    return f"""
    <div id="ag-stack">
        <p class="ag-label">Under the hood</p>
        <div class="ag-stack-line">
            This assistant is itself one of my projects — an
            <a href="{REPO_URL}" target="_blank" rel="noopener">open-source</a>
            production agentic AI system.
        </div>
        {chips}
    </div>
    """


def _visitor_ip(request: gr.Request | None) -> str:
    """Best-effort visitor identifier: forwarded header first, else socket IP."""
    if request is None:
        return "unknown"
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _rate_limited(chat_fn: Callable[..., Any], limiter: RateLimiter) -> Callable[..., Any]:
    """Wrap the chat function so every message passes the rate limiter first."""
    if inspect.isasyncgenfunction(chat_fn):

        async def async_wrapper(message: str, history: list, request: gr.Request):
            refusal = limiter.check(_visitor_ip(request))
            if refusal:
                yield refusal
                return
            async for partial in chat_fn(message, history):
                yield partial

        return async_wrapper

    def sync_wrapper(message: str, history: list, request: gr.Request):
        refusal = limiter.check(_visitor_ip(request))
        if refusal:
            yield refusal
            return
        yield from chat_fn(message, history)

    return sync_wrapper


def build_ui(chat_fn: Callable[..., Any]) -> gr.Blocks:
    """Assemble the complete AskGeorge page around the chat function.

    Args:
        chat_fn: Streaming chat callable (sync or async generator) with the
            Gradio ChatInterface signature (message, history).

    Returns:
        A :class:`gr.Blocks` page; serve it with :func:`serve_kwargs` applied.
    """
    chat_fn = _rate_limited(chat_fn, RateLimiter())
    available_cvs = [
        (label, ASSETS_DIR / filename)
        for label, filename in CV_FILES
        if (ASSETS_DIR / filename).exists()
    ]
    with gr.Blocks(title="AskGeorge") as demo:
        gr.HTML(_header_html())
        if available_cvs:
            with gr.Row():
                for label, path in available_cvs:
                    gr.DownloadButton(label, value=str(path), size="sm")
        gr.HTML(
            '<div id="ag-subtitle">Ask me anything about my experience, '
            "projects, and skills.</div>"
        )
        gr.ChatInterface(
            fn=chat_fn,
            chatbot=gr.Chatbot(
                layout="panel",
                show_label=False,
                height=CHAT_HEIGHT,
                elem_id="ag-chat",
            ),
            examples=[
                "What is your experience with RAG in production?",
                "Tell me about your most recent project.",
                "Why should we hire you as an AI engineer?",
                "What do your clients say about working with you?",
                "Are you open to remote roles?",
            ],
        )
        calendar_url = booking_url()
        if calendar_url:
            gr.HTML(_booking_html(calendar_url))
        gr.HTML(_stack_html())
        gr.HTML('<div id="ag-footer">AskGeorge — AI representative of George Traskas</div>')
    return demo
