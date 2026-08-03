"""Aegean Twin design: theme, CSS, and the full Gradio layout.

Hero-centric portfolio chat in two moods: a bright off-white canvas and a
deep-navy night mode, both accented Aegean sky. One typeface (Inter);
hierarchy comes from weight, size, and letter-spacing. The visitor's OS
preference picks the initial theme; a top-bar toggle overrides it and is
remembered in localStorage.
"""

from __future__ import annotations

import base64
import inspect
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import gradio as gr

from askgeorge.core.config import ASSETS_DIR, booking_url
from askgeorge.core.instant import INSTANT_ENTRIES, InstantFAQ
from askgeorge.core.ratelimit import RateLimiter

logger = logging.getLogger(__name__)

CHAT_HEIGHT: int = 460
CALENDAR_HEIGHT: int = 620

REPO_URL: str = "https://github.com/gtraskas/agentic-ai-engineering"

PROJECT_LINKS: list[tuple[str, str]] = [
    ("MolekitChen", "https://apps.apple.com/us/app/molekitchen/id6773031788"),
    ("Wine-VFM", "https://gtraskas--wine-vfm-app-web.modal.run"),
    ("AskGeorge · code", REPO_URL),
]

CV_FILES: list[tuple[str, str]] = [
    ("AI/ML CV", "Georgios_Traskas_AI_ML_Engineer.pdf"),
    ("Data CV", "Georgios_Traskas_Data_Scientist.pdf"),
]

# Questions that showcase the live RAG + LLM pipeline. Each appears in the
# retrieval golden set (tests/retrieval_eval.py), so retrieval is known-good.
LIVE_AI_QUESTIONS: list[str] = [
    "How did you reduce alert noise at Predictive Fitness?",
    "Do you know Kubernetes?",
    "How does the job-fit analysis work?",
]

# The four pills shown under the input: two instant, two live-AI. The full
# catalog stays one click away in the "More questions" expander.
CURATED_QUESTIONS: list[str] = [
    "What do you do?",
    "Can I talk to the real George?",
    "How did you reduce alert noise at Predictive Fitness?",
    "Do you know Kubernetes?",
]

CHAT_PLACEHOLDER: str = "Ask about my experience and projects. I answer as George."

AEGEAN_CSS: str = f"""
/* ---------- Palette: light by default, .dark overrides ---------- */
:root {{
    --ag-canvas: #FAFAF8;
    --ag-surface: #FFFFFF;
    --ag-ink: #0F172A;
    --ag-body: #334155;
    --ag-muted: #64748B;
    --ag-subtle: #94A3B8;
    --ag-border: #E2E8F0;
    --ag-accent: #0EA5E9;
    --ag-accent-strong: #0284C7;
    --ag-accent-soft: rgba(14, 165, 233, 0.14);
    --ag-shadow: rgba(15, 23, 42, 0.06);
}}
.dark {{
    --ag-canvas: #0B1220;
    --ag-surface: #121B2E;
    --ag-ink: #E6EBF4;
    --ag-body: #C3CCDB;
    --ag-muted: #8B98AC;
    --ag-subtle: #5F7091;
    --ag-border: #223047;
    --ag-accent: #38BDF8;
    --ag-accent-strong: #7DD3FC;
    --ag-accent-soft: rgba(56, 189, 248, 0.16);
    --ag-shadow: rgba(0, 0, 0, 0.35);
}}
body, .gradio-container {{
    background: var(--ag-canvas) !important;
    color: var(--ag-body);
}}
.gradio-container {{
    max-width: 820px !important;
    margin: 0 auto !important;
}}
/* Hide Gradio's own footer chrome */
footer {{
    display: none !important;
}}
.ag-label {{
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--ag-subtle);
    margin: 0 0 10px 0;
}}
/* ---------- Top bar ---------- */
#ag-topbar {{
    display: flex;
    flex-wrap: nowrap !important;
    align-items: center;
    gap: 10px;
    padding: 4px 2px 0 2px;
}}
#ag-topbar > * {{
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: 0 !important;
}}
#ag-topbar .ag-grow {{
    flex: 1 1 auto !important;
}}
#ag-topbar .ag-wordmark {{
    font-size: 1.05rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: var(--ag-ink);
    margin: 0;
    white-space: nowrap;
}}
#ag-topbar .ag-tagline {{
    font-size: 0.66rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--ag-subtle);
    margin: 2px 0 0 0;
    white-space: nowrap;
}}
#ag-hero .ag-status {{
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #10B981;
    margin: 18px 0 0 0;
}}
#ag-topbar a.ag-link {{
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--ag-muted);
    text-decoration: none;
    margin-left: 12px;
    white-space: nowrap;
}}
#ag-topbar a.ag-link:hover {{
    color: var(--ag-accent);
}}
#ag-topbar button.ag-cv {{
    width: auto;
    flex: 0 0 auto;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    color: var(--ag-muted) !important;
    background: transparent !important;
    border: 1px solid var(--ag-border) !important;
    border-radius: 999px !important;
    padding: 4px 12px !important;
    box-shadow: none !important;
}}
#ag-topbar button.ag-cv:hover {{
    color: var(--ag-accent) !important;
    border-color: var(--ag-accent) !important;
}}
#ag-theme-btn {{
    cursor: pointer;
    font-size: 0.95rem;
    line-height: 1;
    color: var(--ag-muted);
    background: transparent;
    border: 1px solid var(--ag-border);
    border-radius: 999px;
    padding: 6px 10px;
    margin-left: 12px;
    transition: color 0.15s ease, border-color 0.15s ease;
}}
#ag-theme-btn:hover {{
    color: var(--ag-accent);
    border-color: var(--ag-accent);
}}
/* ---------- Hero ---------- */
#ag-hero {{
    text-align: center;
    padding: 30px 0 6px 0;
}}
#ag-hero img.ag-photo {{
    display: block;
    margin: 0 auto;
    width: 96px;
    height: 96px;
    border-radius: 50%;
    object-fit: cover;
    border: 3px solid var(--ag-canvas);
    outline: 2px solid var(--ag-accent);
    outline-offset: 3px;
    box-shadow: 0 0 34px var(--ag-accent-soft);
}}
#ag-hero h1.ag-hl {{
    font-size: clamp(1.9rem, 5vw, 2.7rem);
    font-weight: 750;
    letter-spacing: -0.03em;
    line-height: 1.14;
    color: var(--ag-ink);
    margin: 10px 0 14px 0;
}}
#ag-hero h1.ag-hl em {{
    font-style: normal;
    color: var(--ag-accent);
}}
#ag-hero .ag-support {{
    font-size: 0.98rem;
    color: var(--ag-muted);
    max-width: 34rem;
    margin: 0 auto;
    line-height: 1.55;
}}
/* ---------- Tabs: minimal centered switch ----------
   No width override: Gradio 6 measures the tablist for its overflow
   menu, and a fit-content width collapses the tabs into a "..." menu. */
.gradio-container [role="tablist"] {{
    justify-content: center;
    margin: 18px auto 6px auto;
    background: transparent;
    border: none !important;
    gap: 26px;
}}
.gradio-container button[role="tab"] {{
    border: none !important;
    padding: 8px 2px !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    color: var(--ag-subtle) !important;
    background: transparent !important;
    border-radius: 0 !important;
}}
.gradio-container button[role="tab"]:hover {{
    color: var(--ag-ink) !important;
}}
.gradio-container button[role="tab"]::after {{
    display: none !important;
}}
.gradio-container button[role="tab"][aria-selected="true"] {{
    color: var(--ag-accent) !important;
    box-shadow: inset 0 -2px 0 var(--ag-accent) !important;
}}
/* ---------- Chat: open surface, no card ---------- */
#ag-chat .label-wrap, #ag-chat label {{
    display: none !important;
}}
#ag-chat {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
#ag-chat .message-row.panel {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    margin: 0 !important;
    padding: 9px 4px !important;
}}
#ag-chat .message-row.panel .flex-wrap,
#ag-chat .message-row.panel .role,
#ag-chat .message-row .message {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
#ag-chat .message-row, #ag-chat .message-row * {{
    color: var(--ag-body);
}}
/* Same side, same box for both roles; a slim accent bar marks the visitor */
#ag-chat .user-row {{
    justify-content: flex-start !important;
}}
#ag-chat .user-row > * {{
    border-left: 3px solid var(--ag-accent) !important;
    padding-left: 12px !important;
}}
#ag-chat .user-row * {{
    color: var(--ag-ink) !important;
    font-weight: 600;
}}
#ag-chat .placeholder-content {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    height: 100% !important;
}}
#ag-chat .placeholder-content * {{
    color: var(--ag-subtle) !important;
}}
/* ---------- Input ---------- */
#ag-chat-input {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
#ag-chat-input .input-container {{
    background: var(--ag-surface) !important;
    border: 1px solid var(--ag-border) !important;
    border-radius: 16px !important;
    box-shadow: 0 2px 10px var(--ag-shadow) !important;
}}
#ag-chat-input textarea {{
    background: transparent !important;
    color: var(--ag-ink) !important;
    padding: 13px 16px !important;
}}
#ag-chat-input textarea::placeholder {{
    color: var(--ag-subtle) !important;
}}
#ag-chat-input button.submit-button {{
    background: var(--ag-accent) !important;
    color: #FFFFFF !important;
    border-radius: 12px !important;
    margin: 6px !important;
}}
/* ---------- Question pills ---------- */
.ag-q-row {{
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 7px;
    margin: 4px 0 2px 0;
}}
#ag-more-q .ag-q-row {{
    justify-content: flex-start;
    margin-bottom: 12px;
}}
button.ag-q {{
    flex: 0 0 auto;
    width: auto;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    color: var(--ag-muted) !important;
    background: transparent !important;
    border: 1px solid var(--ag-border) !important;
    border-radius: 999px !important;
    padding: 5px 13px !important;
    box-shadow: none !important;
    transition: border-color 0.15s ease, color 0.15s ease;
}}
button.ag-q:hover {{
    border-color: var(--ag-accent) !important;
    color: var(--ag-accent) !important;
}}
/* "More questions" expander: quiet, borderless */
#ag-more-q {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
#ag-more-q > button {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: var(--ag-subtle) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    justify-content: center !important;
}}
#ag-more-q > button:hover {{
    color: var(--ag-accent) !important;
}}
/* ---------- Job-fit tab ---------- */
#ag-jobfit-box textarea {{
    height: {CHAT_HEIGHT}px !important;
    background: var(--ag-surface) !important;
    color: var(--ag-ink) !important;
    border: 1px solid var(--ag-border) !important;
    border-radius: 16px !important;
}}
#ag-jobfit-box label span {{
    color: var(--ag-subtle) !important;
}}
/* Hide the report card until it holds actual content */
#ag-jobfit-report:not(:has(p, table, h1, h2, h3, ul, ol)) {{
    display: none;
}}
#ag-jobfit-report.generating,
#ag-jobfit-report .generating {{
    border-color: var(--ag-accent) !important;
    animation: ag-pulse 1.6s ease-in-out infinite;
}}
@keyframes ag-pulse {{
    0%, 100% {{ box-shadow: 0 0 0 0 var(--ag-accent-soft); }}
    50% {{ box-shadow: 0 0 0 7px transparent; }}
}}
#ag-jobfit-report {{
    background: var(--ag-surface);
    border: 1px solid var(--ag-border);
    border-radius: 16px;
    padding: 6px 22px;
    box-shadow: 0 1px 3px var(--ag-shadow);
    color: var(--ag-body);
}}
#ag-jobfit-report table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.86rem;
}}
#ag-jobfit-report th, #ag-jobfit-report td {{
    border-bottom: 1px solid var(--ag-border);
    padding: 6px 10px;
    text-align: left;
}}
/* Type and My fit columns shrink to their content on one line;
   the Requirement column takes all remaining width */
#ag-jobfit-report th:nth-child(2), #ag-jobfit-report td:nth-child(2),
#ag-jobfit-report th:nth-child(3), #ag-jobfit-report td:nth-child(3) {{
    white-space: nowrap;
    width: 1%;
}}
/* ---------- Booking accordion ---------- */
#ag-book {{
    background: transparent !important;
    border: 1px solid var(--ag-border) !important;
    border-radius: 16px !important;
    box-shadow: none !important;
    margin-top: 18px;
}}
#ag-book > button {{
    background: transparent !important;
    color: var(--ag-muted) !important;
    font-weight: 600 !important;
}}
#ag-book iframe {{
    width: 100%;
    height: {CALENDAR_HEIGHT}px;
    border: 0;
    border-radius: 10px;
    background: #FFFFFF; /* Google's booking page is light-only */
}}
/* ---------- Footer ---------- */
#ag-footer {{
    text-align: center;
    padding: 26px 0 10px 0;
}}
#ag-footer .ag-foot-line {{
    font-size: 0.82rem;
    color: var(--ag-muted);
    margin-bottom: 8px;
}}
#ag-footer a {{
    color: var(--ag-accent);
    text-decoration: none;
    font-weight: 600;
}}
#ag-footer .ag-foot-links a {{
    font-size: 0.8rem;
    color: var(--ag-subtle);
    font-weight: 500;
    margin: 0 8px;
}}
#ag-footer .ag-foot-links a:hover {{
    color: var(--ag-accent);
}}
"""


def build_theme() -> gr.themes.Base:
    """Return the Aegean Twin Gradio theme with light and dark token pairs."""
    return gr.themes.Soft(
        primary_hue="sky",
        neutral_hue="slate",
        font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
        font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "monospace"],
    ).set(
        body_background_fill="#FAFAF8",
        body_background_fill_dark="#0B1220",
        body_text_color="#0F172A",
        body_text_color_dark="#E6EBF4",
        background_fill_primary="#FFFFFF",
        background_fill_primary_dark="#121B2E",
        background_fill_secondary="#F8FAFC",
        background_fill_secondary_dark="#0F1728",
        border_color_primary="#E2E8F0",
        border_color_primary_dark="#223047",
        button_primary_background_fill="#0EA5E9",
        button_primary_background_fill_dark="#0EA5E9",
        button_primary_text_color="#FFFFFF",
        button_primary_text_color_dark="#FFFFFF",
    )


# Theme bootstrapping: saved choice wins, otherwise the OS preference.
# Gradio initializes its own theme class late, so the state is re-applied
# after startup ticks; the toggle persists to localStorage.
_THEME_HEAD: str = (
    '<meta name="color-scheme" content="light dark">'
    "<script>"
    "window.agApplyTheme = function () {"
    'var saved = localStorage.getItem("ag-theme");'
    'var dark = saved ? saved === "dark" : '
    'window.matchMedia("(prefers-color-scheme: dark)").matches;'
    'document.documentElement.classList.toggle("dark", dark);'
    'if (document.body) { document.body.classList.toggle("dark", dark); }'
    'var icon = document.getElementById("ag-theme-icon");'
    'if (icon) { icon.textContent = dark ? "☀" : "☾"; }'
    "};"
    "window.agToggleTheme = function () {"
    'var dark = document.documentElement.classList.contains("dark");'
    'localStorage.setItem("ag-theme", dark ? "light" : "dark");'
    "window.agApplyTheme();"
    "};"
    "window.agApplyTheme();"
    'document.addEventListener("DOMContentLoaded", window.agApplyTheme);'
    "setTimeout(window.agApplyTheme, 500);"
    "setTimeout(window.agApplyTheme, 1500);"
    "</script>"
)


def serve_kwargs() -> dict[str, Any]:
    """Return the theme/css/head kwargs for ``launch()`` or ``mount_gradio_app()``.

    Gradio 6 applies theme and CSS at serve time, not at Blocks construction.
    """
    return {
        "theme": build_theme(),
        "css": AEGEAN_CSS,
        "head": _THEME_HEAD,
    }


def _photo_data_uri(assets_dir: Path = ASSETS_DIR) -> str | None:
    """Return the profile photo as a base64 data URI, if present."""
    for name in ("photo.jpg", "photo.jpeg", "photo.png"):
        path = assets_dir / name
        if path.exists():
            suffix = "png" if path.suffix == ".png" else "jpeg"
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            return f"data:image/{suffix};base64,{encoded}"
    return None


def _topbar_left_html() -> str:
    """Build the wordmark side of the top bar."""
    return """
    <div>
        <p class="ag-wordmark">George Traskas</p>
        <p class="ag-tagline">Data Scientist · AI/ML Engineer</p>
    </div>
    """


def _topbar_right_html() -> str:
    """Build the links + theme-toggle side of the top bar."""
    return """
    <div style="text-align: right; white-space: nowrap;">
        <a class="ag-link" href="https://www.linkedin.com/in/george-traskas/" target="_blank" rel="noopener">LinkedIn</a>
        <a class="ag-link" href="https://github.com/gtraskas" target="_blank" rel="noopener">GitHub</a>
        <a class="ag-link" href="mailto:georgiost77@gmail.com">Email</a>
        <button id="ag-theme-btn" onclick="agToggleTheme()" title="Switch light / dark"><span id="ag-theme-icon">☾</span></button>
    </div>
    """


def _hero_html() -> str:
    """Build the hero: portrait in an accent ring, headline, support line."""
    photo_uri = _photo_data_uri()
    photo_tag = (
        f'<img class="ag-photo" src="{photo_uri}" alt="George Traskas" />'
        if photo_uri
        else ""
    )
    return f"""
    <div id="ag-hero">
        {photo_tag}
        <p class="ag-status">● Open to work</p>
        <h1 class="ag-hl">Ask me anything.<br>I'm George, <em>in AI form</em>.</h1>
        <p class="ag-support">Recruiters welcome: ask about my experience and
        projects, or paste a job description and get my honest fit for the role.</p>
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


def _booking_iframe_html(url: str) -> str:
    """Build the embedded Google Calendar iframe for the booking accordion."""
    return (
        f'<iframe src="{_booking_embed_src(url)}" '
        'title="Book an intro call with George"></iframe>'
    )


def _footer_html() -> str:
    """Build the footer: open-source note plus quiet project links."""
    links = " · ".join(
        f'<a href="{url}" target="_blank" rel="noopener">{label}</a>'
        for label, url in PROJECT_LINKS
    )
    return f"""
    <div id="ag-footer">
        <div class="ag-foot-line">
            This assistant is itself one of my projects: an
            <a href="{REPO_URL}" target="_blank" rel="noopener">open-source</a>
            production agentic AI system.
        </div>
        <div class="ag-foot-links">{links}</div>
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


def _wrap_chat(
    chat_fn: Callable[..., Any], limiter: RateLimiter, instant: InstantFAQ
) -> Callable[..., Any]:
    """Wrap the chat function with instant answers and rate limiting.

    Instant FAQ matches are checked first and served immediately — they cost
    nothing, so they bypass the rate limiter and never consume a visitor's
    message budget. Everything else passes the limiter, then the agent.
    """
    if inspect.isasyncgenfunction(chat_fn):

        async def async_wrapper(message: str, history: list, request: gr.Request):
            instant_reply = instant.match(message)
            if instant_reply:
                yield instant_reply
                return
            refusal = limiter.check(_visitor_ip(request))
            if refusal:
                yield refusal
                return
            async for partial in chat_fn(message, history):
                yield partial

        return async_wrapper

    def sync_wrapper(message: str, history: list, request: gr.Request):
        instant_reply = instant.match(message)
        if instant_reply:
            yield instant_reply
            return
        refusal = limiter.check(_visitor_ip(request))
        if refusal:
            yield refusal
            return
        yield from chat_fn(message, history)

    return sync_wrapper


def _jobfit_handler(
    jobfit_fn: Callable[[str], Any], limiter: RateLimiter
) -> Callable[..., Any]:
    """Wrap the job-fit analyzer with the shared rate limiter.

    Yields (report_markdown, button_update) pairs so the Analyze button reads
    "Analyzing…" and is disabled while the pipeline runs — visible feedback
    and double-click protection in one.
    """
    busy = gr.Button(value="Analyzing…", interactive=False)
    ready = gr.Button(value="Analyze fit", interactive=True)

    async def handler(job_description: str, request: gr.Request):
        refusal = limiter.check(_visitor_ip(request))
        if refusal:
            yield refusal, ready
            return
        last = ""
        async for markdown in jobfit_fn(job_description):
            last = markdown
            yield markdown, busy
        yield last, ready

    return handler


def _make_responder(chat_fn: Callable[..., Any]) -> Callable[..., Any]:
    """Build the streaming chat handler for the custom chat panel.

    Args:
        chat_fn: The wrapped chat callable (message, history, request).

    Returns:
        A generator (async when the backend streams asynchronously) taking
        (message, history, request) and yielding (chatbot history, textbox
        value) pairs as the reply streams in.
    """

    if inspect.isasyncgenfunction(chat_fn):

        async def respond_async(message: str, history: list | None, request: gr.Request):
            message = (message or "").strip()
            history = history or []
            if not message:
                yield history, ""
                return
            shown = [*history, {"role": "user", "content": message}]
            yield shown, ""
            async for partial in chat_fn(message, history, request):
                yield [*shown, {"role": "assistant", "content": partial}], ""

        return respond_async

    def respond_sync(message: str, history: list | None, request: gr.Request):
        message = (message or "").strip()
        history = history or []
        if not message:
            yield history, ""
            return
        shown = [*history, {"role": "user", "content": message}]
        yield shown, ""
        for partial in chat_fn(message, history, request):
            yield [*shown, {"role": "assistant", "content": partial}], ""

    return respond_sync


def _build_chat_panel(chat_fn: Callable[..., Any]) -> None:
    """Assemble the chat tab: chatbot, input, curated pills, and the expander.

    A custom Blocks chat rather than gr.ChatInterface: the question pills
    must submit on click, and external components cannot trigger a
    ChatInterface submission. Four curated pills sit under the input; the
    full catalog lives in a collapsed "More questions" accordion whose
    instant group renders straight from the InstantFAQ catalog, so the UI
    can never offer a question the matcher does not answer.
    """
    respond = _make_responder(chat_fn)
    chatbot = gr.Chatbot(
        layout="panel",
        show_label=False,
        height=None,
        min_height=90,
        max_height=CHAT_HEIGHT,
        elem_id="ag-chat",
        placeholder=CHAT_PLACEHOLDER,
    )
    textbox = gr.Textbox(
        placeholder="Ask about my experience, projects, or availability…",
        show_label=False,
        submit_btn=True,
        elem_id="ag-chat-input",
    )
    textbox.submit(respond, inputs=[textbox, chatbot], outputs=[chatbot, textbox])

    def _chip_handler(question: str) -> Callable[..., Any]:
        if inspect.isasyncgenfunction(respond):

            async def handler_async(history: list | None, request: gr.Request):
                async for update in respond(question, history, request):
                    yield update

            return handler_async

        def handler_sync(history: list | None, request: gr.Request):
            yield from respond(question, history, request)

        return handler_sync

    def _chip_row(questions: list[str]) -> None:
        with gr.Row(elem_classes="ag-q-row"):
            for question in questions:
                chip = gr.Button(
                    question, size="sm", scale=0, min_width=0, elem_classes="ag-q"
                )
                chip.click(
                    _chip_handler(question),
                    inputs=[chatbot],
                    outputs=[chatbot, textbox],
                )

    _chip_row(CURATED_QUESTIONS)
    with gr.Accordion("More questions", open=False, elem_id="ag-more-q"):
        gr.HTML('<p class="ag-label">Quick answers</p>')
        _chip_row([entry.triggers[0] for entry in INSTANT_ENTRIES])
        gr.HTML('<p class="ag-label">Ask the AI live</p>')
        _chip_row(LIVE_AI_QUESTIONS)


def build_ui(
    chat_fn: Callable[..., Any], jobfit_fn: Callable[[str], Any]
) -> gr.Blocks:
    """Assemble the complete AskGeorge page: chat plus job-fit analysis.

    Args:
        chat_fn: Streaming chat callable with the (message, history) signature.
        jobfit_fn: Async generator taking a job description and yielding
            Markdown progress then the final report.

    Returns:
        A :class:`gr.Blocks` page; serve it with :func:`serve_kwargs` applied.
    """
    limiter = RateLimiter()
    chat_fn = _wrap_chat(chat_fn, limiter, InstantFAQ())
    jobfit_handler = _jobfit_handler(jobfit_fn, limiter)
    available_cvs = [
        (label, ASSETS_DIR / filename)
        for label, filename in CV_FILES
        if (ASSETS_DIR / filename).exists()
    ]
    with gr.Blocks(title="AskGeorge") as demo:
        with gr.Row(elem_id="ag-topbar"):
            gr.HTML(_topbar_left_html(), elem_classes="ag-grow")
            for label, path in available_cvs:
                gr.DownloadButton(
                    label, value=str(path), size="sm", elem_classes="ag-cv"
                )
            gr.HTML(_topbar_right_html())
        gr.HTML(_hero_html())
        with gr.Tabs():
            with gr.Tab("Chat with me"):
                _build_chat_panel(chat_fn)
            with gr.Tab("Analyze a job fit"):
                job_description = gr.Textbox(
                    show_label=False,
                    placeholder="Paste the full job description here…",
                    lines=16,
                    elem_id="ag-jobfit-box",
                )
                with gr.Row():
                    analyze_button = gr.Button(
                        "Analyze fit", variant="primary", scale=1
                    )
                    clear_button = gr.ClearButton(
                        value="Clear for a new analysis", variant="secondary", scale=1
                    )
                report = gr.Markdown(elem_id="ag-jobfit-report")
                clear_button.add([job_description, report])
                analyze_button.click(
                    fn=jobfit_handler,
                    inputs=[job_description],
                    outputs=[report, analyze_button],
                )
        calendar_url = booking_url()
        if calendar_url:
            with gr.Accordion("Book an intro call", open=False, elem_id="ag-book"):
                gr.HTML(_booking_iframe_html(calendar_url))
        gr.HTML(_footer_html())
    return demo
