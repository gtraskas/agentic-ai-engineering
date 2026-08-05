"""Terracotta design: theme, CSS, and the full Gradio layout.

A warm off-white canvas and a deep-brown night mode, both accented
terracotta. Three typefaces with one job each: Newsreader for the headline
and the proof-card titles, Public Sans for everything else, IBM Plex Mono
for the all-caps eyebrows. Six type sizes, no more. Borders carry the
structure; there is effectively one shadow on the page.

The visitor's OS preference picks the initial theme; a top-bar toggle
overrides it and is remembered in localStorage.
"""

from __future__ import annotations

import asyncio
import base64
import inspect
import logging
import re
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import gradio as gr

from askgeorge.core.config import ASSETS_DIR, PUBLIC_BASE_URL, booking_url
from askgeorge.core.ratelimit import RateLimiter

logger = logging.getLogger(__name__)

CHAT_HEIGHT: int = 460

REPO_URL: str = "https://github.com/gtraskas/agentic-ai-engineering"
MOLEKITCHEN_URL: str = "https://apps.apple.com/us/app/molekitchen/id6773031788"
LINKEDIN_URL: str = "https://www.linkedin.com/in/george-traskas/"
GITHUB_URL: str = "https://github.com/gtraskas"
EMAIL_ADDRESS: str = "georgiost77@gmail.com"

CV_FILES: list[tuple[str, str]] = [
    ("AI/ML CV", "Georgios_Traskas_AI_ML_Engineer.pdf"),
    ("Data CV", "Georgios_Traskas_Data_Scientist.pdf"),
]

# The six suggestions under the composer. Every one goes through the live
# RAG + LLM path, so every one is asserted to be in the retrieval golden
# set (tests/retrieval_eval.py) — retrieval for them is known-good.
PROMPT_PILLS: list[str] = [
    "What do you do?",
    "Tell me about your most recent project.",
    "How did you reduce alert noise at Predictive Fitness?",
    "What went wrong with tool selection in the MCP server?",
    "What is your notice period?",
    "Can I talk to the real George?",
]

# The heading _render puts on a finished report. Progress lines and error
# messages never carry it, so it is the signal that a real report exists.
REPORT_MARKER: str = "## Fit assessment"
REPORT_FILENAME: str = "george-traskas-fit-report.md"

CHAT_PLACEHOLDER: str = "Ask about my experience and projects. I answer as George."
COMPOSER_PLACEHOLDER: str = "Ask anything"

TERRACOTTA_CSS: str = """
/* ---------- Tokens ---------- */
:root {
    --ag-canvas:  #FBF9F5;
    --ag-surface: #FFFFFF;
    --ag-ink:     #181614;
    --ag-body:    #4A443D;
    --ag-muted:   #6E665D;
    --ag-subtle:  #A09789;
    --ag-border:  #E6E0D6;
    --ag-line:    #F0EBE2;
    --ag-accent:  #B4501E;
    --ag-shadow:  rgba(24, 22, 20, 0.05);

    --ag-serif: Newsreader, Georgia, 'Times New Roman', serif;
    --ag-sans:  'Public Sans', Helvetica, Arial, sans-serif;
    --ag-mono:  'IBM Plex Mono', ui-monospace, monospace;

    /* Type scale — do not introduce sizes outside this set */
    --ag-t-micro: 10px;   /* mono eyebrows, all-caps labels */
    --ag-t-small: 13px;   /* quiet actions */
    --ag-t-ui:    14px;   /* nav, buttons, prompt pills */
    --ag-t-body:  16px;   /* chat, paragraphs, input */
    --ag-t-lead:  19px;   /* proof-card titles */
    --ag-t-h1:    33px;   /* hero */

    --ag-r-sm: 4px;
    --ag-r-md: 6px;
    --ag-r-pill: 999px;
}
.dark {
    --ag-canvas:  #17140F;
    --ag-surface: #201C16;
    --ag-ink:     #F3EEE5;
    --ag-body:    #C9C0B2;
    --ag-muted:   #A0968A;
    --ag-subtle:  #7A7168;
    --ag-border:  #302A22;
    --ag-line:    #262019;
    --ag-accent:  #E0793C;
    --ag-shadow:  rgba(0, 0, 0, 0.4);
}
/* ---------- Shell ---------- */
/* The two tabs differ in height; without a reserved gutter the vertical
   scrollbar pops in and out on tab switch and shifts the whole layout */
html {
    scrollbar-gutter: stable;
}
body, .gradio-container {
    background: var(--ag-canvas) !important;
    color: var(--ag-body);
    font-family: var(--ag-sans) !important;
}
/* gradio-app is a flex container, so without an explicit width the page
   column sizes to each tab's intrinsic content width and jumps on tab
   switch; width: 100% pins it to max-width on every tab */
.gradio-container {
    max-width: 820px !important;
    width: 100% !important;
    margin: 0 auto !important;
}
/* Hide Gradio's own footer chrome */
footer {
    display: none !important;
}
/* Gradio pads every anchor 2px 8px, which opens a visible gap before the
   punctuation that follows a link ("Email me ." instead of "Email me.") */
#ag-topbar a, #ag-proof a, #ag-footer a {
    padding: 0 !important;
}
/* Shared all-caps mono label */
.ag-label {
    font-family: var(--ag-mono);
    font-size: var(--ag-t-micro);
    font-weight: 500;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--ag-subtle);
    margin: 44px 0 14px 0;
}
/* ---------- Top bar: wordmark + 2 CVs + links + theme ---------- */
#ag-topbar {
    display: flex;
    flex-wrap: wrap !important;
    align-items: center;
    gap: 8px;
    padding: 26px 2px 0 2px;
}
#ag-topbar > * {
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: 0 !important;
}
/* The wordmark takes the slack so everything else groups to the right */
#ag-topbar .ag-grow {
    flex: 1 1 auto !important;
    overflow: hidden;
}
#ag-topbar .ag-wordmark {
    font-family: var(--ag-serif);
    font-size: 20px;
    font-weight: 500;
    letter-spacing: -0.01em;
    color: var(--ag-ink);
    margin: 0;
    white-space: nowrap;
}
#ag-topbar .ag-topbar-right {
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
}
#ag-topbar a.ag-link {
    font-size: var(--ag-t-ui);
    font-weight: 500;
    color: var(--ag-muted);
    text-decoration: none;
}
#ag-topbar a.ag-link:hover {
    color: var(--ag-accent);
}
/* The two CV downloads — the ONLY place CVs appear */
#ag-topbar button.ag-cv {
    width: auto;
    flex: 0 0 auto;
    font-family: var(--ag-sans) !important;
    font-size: var(--ag-t-ui) !important;
    font-weight: 500 !important;
    color: var(--ag-muted) !important;
    background: transparent !important;
    border: 1px solid var(--ag-border) !important;
    border-radius: var(--ag-r-pill) !important;
    padding: 5px 13px !important;
    box-shadow: none !important;
}
#ag-topbar button.ag-cv:hover {
    color: var(--ag-accent) !important;
    border-color: var(--ag-accent) !important;
}
#ag-topbar .ag-divider {
    width: 1px;
    height: 16px;
    background: var(--ag-border);
}
#ag-theme-btn {
    cursor: pointer;
    font-size: 13px;
    line-height: 1;
    color: var(--ag-muted);
    background: transparent;
    border: 1px solid var(--ag-border);
    border-radius: var(--ag-r-pill);
    padding: 6px 9px;
    transition: color 0.15s ease, border-color 0.15s ease;
}
#ag-theme-btn:hover {
    color: var(--ag-accent);
    border-color: var(--ag-accent);
}
/* ---------- Hero: compact, photo beside the line ---------- */
#ag-hero {
    display: grid;
    grid-template-columns: 64px 1fr;
    gap: 20px;
    align-items: center;
    padding: 40px 0 0 0;
    text-align: left;
}
#ag-hero img.ag-photo {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    object-fit: cover;
    border: 1px solid var(--ag-border);
    box-shadow: none;
    outline: none;
}
#ag-hero h1.ag-hl {
    font-family: var(--ag-serif);
    font-size: clamp(26px, 4.2vw, var(--ag-t-h1));
    font-weight: 400;
    letter-spacing: -0.02em;
    line-height: 1.12;
    color: var(--ag-ink);
    margin: 0 0 8px 0;
    text-wrap: pretty;
}
#ag-hero h1.ag-hl em {
    font-style: italic;
    color: var(--ag-accent);
}
#ag-hero .ag-support {
    font-size: var(--ag-t-body);
    line-height: 1.55;
    color: var(--ag-muted);
    max-width: 54ch;
    margin: 0;
    text-wrap: pretty;
}
/* ---------- Tabs ----------
   No width override: Gradio 6 measures the tablist for its overflow
   menu, and a fit-content width collapses the tabs into a "..." menu. */
.gradio-container [role="tablist"] {
    justify-content: flex-start;
    gap: 28px;
    margin: 34px 0 0 0;
    background: transparent;
    border: none !important;
    border-bottom: 1px solid var(--ag-border) !important;
}
.gradio-container button[role="tab"] {
    border: none !important;
    border-radius: 0 !important;
    background: transparent !important;
    font-family: var(--ag-sans) !important;
    font-size: var(--ag-t-body) !important;
    font-weight: 600 !important;
    color: var(--ag-subtle) !important;
    padding: 0 0 12px 0 !important;
    margin-bottom: -1px !important;
}
.gradio-container button[role="tab"]::after {
    display: none !important;
}
.gradio-container button[role="tab"]:hover {
    color: var(--ag-ink) !important;
}
.gradio-container button[role="tab"][aria-selected="true"] {
    color: var(--ag-ink) !important;
    box-shadow: inset 0 -2px 0 var(--ag-accent) !important;
}
/* ---------- Chat: open surface, no bubbles ---------- */
#ag-chat, #ag-chat .label-wrap, #ag-chat label {
    border: none !important;
}
#ag-chat .label-wrap, #ag-chat label {
    display: none !important;
}
#ag-chat {
    background: transparent !important;
    box-shadow: none !important;
    min-height: 240px;
}
#ag-chat .message-row.panel,
#ag-chat .message-row.panel .flex-wrap,
#ag-chat .message-row.panel .role,
#ag-chat .message-row .message {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
#ag-chat .message-row.panel {
    margin: 0 !important;
    padding: 11px 0 !important;
}
#ag-chat .message-row, #ag-chat .message-row * {
    color: var(--ag-body);
    font-size: var(--ag-t-body);
    line-height: 1.65;
}
/* Both roles left-aligned; a slim accent rule marks the visitor.
   The selector carries every class Gradio puts on the row: the blanket
   "border: none" above is more specific than a plain .user-row rule and
   would otherwise erase the accent rule even with !important */
#ag-chat .user-row {
    justify-content: flex-start !important;
}
#ag-chat .message-row.panel.user-row > .flex-wrap {
    border-left: 2px solid var(--ag-accent) !important;
    padding-left: 14px !important;
}
#ag-chat .user-row * {
    color: var(--ag-ink) !important;
    font-weight: 600;
}
#ag-chat .bot-row > * {
    padding-left: 16px !important;
}
/* The empty-chat line and the job-fit intro (#ag-jobfit-intro) are the
   same kind of text in the same slot on their respective tabs, so they
   share one spec: 16px, 1.6, muted, 58ch measure, sitting at the top of
   the panel against the column edge. Gradio stacks this placeholder in a
   COLUMN flexbox, so align-items is the horizontal axis here and
   justify-content the vertical one. */
#ag-chat .placeholder-content {
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    justify-content: flex-start !important;
    height: 100% !important;
    /* matches the 10px 12px Gradio puts on the padded block that holds
       #ag-jobfit-intro, so the two lines start at the same point */
    padding: 10px 12px !important;
    text-align: left !important;
}
#ag-chat .placeholder-content .placeholder {
    align-items: flex-start !important;
    justify-content: flex-start !important;
    text-align: left !important;
    margin: 0 !important;
    max-width: 58ch !important;
}
#ag-chat .placeholder-content * {
    color: var(--ag-muted) !important;
    font-size: var(--ag-t-body) !important;
    line-height: 1.6 !important;
}
/* Safety net for model-emitted tables: scroll inside the message instead
   of blowing up the narrow chat column */
#ag-chat .message table {
    display: block;
    max-width: 100%;
    overflow-x: auto;
    font-size: var(--ag-t-ui);
    border-collapse: collapse;
}
#ag-chat .message th, #ag-chat .message td {
    border: 1px solid var(--ag-border);
    padding: 6px 10px;
    white-space: nowrap;
}
/* ---------- Composer: pill + circular arrow ---------- */
/* Gradio wraps every input in a .form block carrying its own fill and
   padding; the composer and the job-fit textarea draw their own borders,
   so the wrapper has to disappear or it reads as a slab behind them */
.form:has(> #ag-chat-input), .form:has(> #ag-jobfit-box) {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
#ag-chat-input, #ag-jobfit-box {
    padding: 0 !important;
}
#ag-chat-input {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
#ag-chat-input .input-container {
    background: var(--ag-surface) !important;
    border: 1px solid var(--ag-border) !important;
    border-radius: var(--ag-r-pill) !important;
    box-shadow: 0 1px 2px var(--ag-shadow) !important;
    padding: 8px 8px 8px 20px !important;
    align-items: center !important;
}
#ag-chat-input .input-container:focus-within {
    border-color: var(--ag-accent) !important;
}
#ag-chat-input textarea {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: var(--ag-ink) !important;
    font-family: var(--ag-sans) !important;
    font-size: var(--ag-t-body) !important;
    line-height: 1.6 !important;
    padding: 4px 0 !important;
    order: 0;
}
#ag-chat-input textarea::placeholder {
    color: var(--ag-subtle) !important;
}
/* The keyboard hint is a pseudo-element so it can sit inside Gradio's own
   input container without a wrapper component; flex order puts it left of
   the submit button */
#ag-chat-input .input-container::after {
    content: "\\21B5";
    font-family: var(--ag-mono);
    font-size: 11px;
    color: var(--ag-subtle);
    order: 1;
    margin: 0 12px 0 4px;
}
/* Circular dark submit; hover flips to accent */
#ag-chat-input button.submit-button {
    order: 2;
    width: 34px !important;
    height: 34px !important;
    min-width: 34px !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    border-radius: 50% !important;
    background: var(--ag-ink) !important;
    color: var(--ag-canvas) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
#ag-chat-input button.submit-button:hover {
    background: var(--ag-accent) !important;
}
/* Gradio ships a paper-plane glyph; the design calls for a plain up arrow,
   drawn as a pseudo-element so no SVG has to be shipped or themed */
#ag-chat-input button.submit-button svg {
    display: none !important;
}
#ag-chat-input button.submit-button::after {
    content: "\\2191";
    font-family: var(--ag-sans);
    font-size: 17px;
    font-weight: 500;
    line-height: 1;
}
/* ---------- Quiet clear actions ---------- */
#ag-chat-actions {
    justify-content: flex-end;
    margin-top: 12px;
}
button.ag-clear {
    width: auto;
    flex: 0 0 auto !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    font-family: var(--ag-sans) !important;
    font-size: var(--ag-t-small) !important;
    font-weight: 500 !important;
    color: var(--ag-subtle) !important;
    padding: 2px 4px !important;
}
button.ag-clear:hover {
    color: var(--ag-accent) !important;
}
/* ---------- Prompt pills: one unlabelled set, 2 x 3 ---------- */
#ag-qcols {
    display: grid !important;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-top: 0;
}
button.ag-q {
    width: 100%;
    text-align: left;
    justify-content: flex-start !important;
    font-family: var(--ag-sans) !important;
    font-size: var(--ag-t-ui) !important;
    font-weight: 500 !important;
    line-height: 1.4 !important;
    color: var(--ag-muted) !important;
    background: transparent !important;
    border: 1px solid var(--ag-border) !important;
    border-radius: var(--ag-r-md) !important;
    padding: 9px 13px !important;
    box-shadow: none !important;
    transition: border-color 0.15s ease, color 0.15s ease;
}
button.ag-q:hover {
    border-color: var(--ag-accent) !important;
    color: var(--ag-accent) !important;
}
/* ---------- Job-fit tab ---------- */
#ag-jobfit-intro {
    font-size: var(--ag-t-body);
    line-height: 1.6;
    color: var(--ag-muted);
    max-width: 58ch;
    margin: 0 0 16px 0;
}
#ag-jobfit-box textarea {
    height: 260px !important;
    background: var(--ag-surface) !important;
    color: var(--ag-ink) !important;
    border: 1px solid var(--ag-border) !important;
    border-radius: var(--ag-r-md) !important;
    font-family: var(--ag-sans) !important;
    font-size: 15px !important;
    line-height: 1.6 !important;
    padding: 16px !important;
}
#ag-jobfit-box textarea:focus {
    border-color: var(--ag-accent) !important;
}
#ag-jobfit-box label span {
    color: var(--ag-subtle) !important;
}
#ag-jobfit-actions {
    align-items: center;
    gap: 16px;
    margin-top: 14px;
}
button.ag-primary {
    width: auto;
    flex: 0 0 auto !important;
    background: var(--ag-ink) !important;
    color: var(--ag-canvas) !important;
    border: none !important;
    border-radius: var(--ag-r-sm) !important;
    font-family: var(--ag-sans) !important;
    font-size: var(--ag-t-ui) !important;
    font-weight: 600 !important;
    padding: 10px 18px !important;
    box-shadow: none !important;
}
button.ag-primary:hover {
    background: var(--ag-accent) !important;
}
/* Hide the report card until it holds actual content */
#ag-jobfit-report:not(:has(p, table, h1, h2, h3, ul, ol)) {
    display: none;
}
#ag-jobfit-report {
    background: var(--ag-surface);
    border: 1px solid var(--ag-border);
    border-radius: var(--ag-r-md);
    padding: 4px 22px 18px 22px;
    box-shadow: none;
    color: var(--ag-body);
    margin-top: 24px;
}
#ag-jobfit-report.generating, #ag-jobfit-report .generating {
    border-color: var(--ag-accent) !important;
}
#ag-jobfit-report table {
    width: 100%;
    border-collapse: collapse;
    font-size: 15px;
}
#ag-jobfit-report th {
    font-family: var(--ag-mono);
    font-size: var(--ag-t-micro);
    font-weight: 500;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--ag-subtle);
    text-align: left;
    padding: 14px 10px 10px 10px;
    border-bottom: 1px solid var(--ag-border);
}
#ag-jobfit-report td {
    padding: 11px 10px;
    border-bottom: 1px solid var(--ag-line);
    line-height: 1.45;
    text-align: left;
}
#ag-jobfit-report th:first-child, #ag-jobfit-report td:first-child {
    padding-left: 0;
}
#ag-jobfit-report th:last-child, #ag-jobfit-report td:last-child {
    padding-right: 0;
}
#ag-jobfit-report td:nth-child(2) {
    color: var(--ag-subtle);
    font-size: var(--ag-t-ui);
}
#ag-jobfit-report td:nth-child(3) {
    font-weight: 600;
    color: var(--ag-ink);
}
/* Type and My fit columns shrink to their content on one line;
   the Requirement column takes all remaining width */
#ag-jobfit-report th:nth-child(2), #ag-jobfit-report td:nth-child(2),
#ag-jobfit-report th:nth-child(3), #ag-jobfit-report td:nth-child(3) {
    white-space: nowrap;
    width: 1%;
}
/* Quiet outline action under the report, in the CV-pill idiom */
button.ag-download {
    width: auto;
    /* it sits directly in the tab's column flexbox, where a plain width:auto
       still stretches the full width; align-self shrinks it to its label */
    align-self: flex-start !important;
    flex: 0 0 auto !important;
    margin-top: 16px;
    font-family: var(--ag-sans) !important;
    font-size: var(--ag-t-ui) !important;
    font-weight: 500 !important;
    color: var(--ag-muted) !important;
    background: transparent !important;
    border: 1px solid var(--ag-border) !important;
    border-radius: var(--ag-r-pill) !important;
    padding: 7px 16px !important;
    box-shadow: none !important;
    transition: color 0.15s ease, border-color 0.15s ease;
}
button.ag-download:hover {
    color: var(--ag-accent) !important;
    border-color: var(--ag-accent) !important;
}
/* ---------- Booking accordion ---------- */
#ag-book {
    background: transparent !important;
    border: 1px solid var(--ag-border) !important;
    border-radius: var(--ag-r-md) !important;
    box-shadow: none !important;
    margin-top: 52px;
}
#ag-book > button {
    background: transparent !important;
    font-family: var(--ag-sans) !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    color: var(--ag-body) !important;
    padding: 15px 18px !important;
}
#ag-book > button:hover {
    color: var(--ag-accent) !important;
}
#ag-book iframe {
    width: 100%;
    height: 620px;
    border: 0;
    border-radius: var(--ag-r-sm);
    background: #FFFFFF; /* Google's booking page is light-only */
}
/* ---------- Proof strip: 3 cells, hairline grid ---------- */
#ag-proof {
    display: grid !important;
    grid-template-columns: repeat(3, 1fr);
    gap: 1px;
    background: var(--ag-border);
    border: 1px solid var(--ag-border);
    margin-top: 52px;
}
#ag-proof .ag-proof-cell {
    background: var(--ag-canvas);
    padding: 20px 22px;
}
#ag-proof .ag-proof-eyebrow {
    font-family: var(--ag-mono);
    font-size: var(--ag-t-micro);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--ag-subtle);
    margin: 0 0 10px 0;
}
#ag-proof .ag-proof-title {
    font-family: var(--ag-serif);
    font-size: var(--ag-t-lead);
    line-height: 1.25;
    color: var(--ag-ink);
    margin: 0 0 6px 0;
}
#ag-proof .ag-proof-body {
    font-size: var(--ag-t-ui);
    line-height: 1.5;
    color: var(--ag-muted);
    margin: 0;
}
#ag-proof .ag-proof-body strong {
    color: var(--ag-ink);
    font-weight: 600;
}
#ag-proof a {
    color: var(--ag-accent);
    text-decoration: none;
    font-weight: 600;
    /* keeps the arrow on the same line as its label */
    white-space: nowrap;
}
/* ---------- Footer ---------- */
#ag-footer {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 16px;
    border-top: 1px solid var(--ag-border);
    margin-top: 52px;
    padding: 24px 0 10px 0;
    text-align: left;
}
#ag-footer .ag-foot-line {
    font-size: var(--ag-t-ui);
    color: var(--ag-subtle);
    margin: 0;
}
#ag-footer a {
    color: var(--ag-accent);
    text-decoration: none;
    font-weight: 600;
}
#ag-footer .ag-disclosure {
    font-family: var(--ag-mono);
    font-size: 11px;
    letter-spacing: 0.04em;
    color: var(--ag-subtle);
    margin: 0;
    text-transform: uppercase;
}
/* ---------- Responsive ---------- */
@media (max-width: 768px) {
    #ag-proof {
        grid-template-columns: 1fr;
    }
    #ag-qcols {
        grid-template-columns: 1fr !important;
    }
}
@media (max-width: 480px) {
    /* The headline and support line wrap to five or six lines on a phone,
       and centring leaves the portrait stranded beside their midpoint;
       aligning to the top pairs it with the first line of the headline */
    #ag-hero {
        grid-template-columns: 56px 1fr;
        gap: 16px;
        padding-top: 28px;
        align-items: start;
    }
    #ag-hero img.ag-photo {
        width: 56px;
        height: 56px;
    }
    /* The wordmark takes its own row, so the CV pills group together */
    #ag-topbar .ag-grow {
        flex: 1 1 100% !important;
    }
    #ag-topbar .ag-topbar-right {
        flex-wrap: wrap;
        white-space: normal;
    }
    /* The links wrap onto their own row, where the separator that divided
       them from the CV pills reads as a stray character */
    #ag-topbar .ag-divider {
        display: none;
    }
    #ag-jobfit-report {
        padding: 4px 14px 14px 14px;
    }
}
"""


def build_theme() -> gr.themes.Base:
    """Return the Terracotta Gradio theme with light and dark token pairs."""
    return gr.themes.Soft(
        primary_hue="orange",
        neutral_hue="stone",
        font=[gr.themes.GoogleFont("Public Sans"), "system-ui", "sans-serif"],
        font_mono=[gr.themes.GoogleFont("IBM Plex Mono"), "monospace"],
    ).set(
        body_background_fill="#FBF9F5",
        body_background_fill_dark="#17140F",
        body_text_color="#4A443D",
        body_text_color_dark="#C9C0B2",
        background_fill_primary="#FFFFFF",
        background_fill_primary_dark="#201C16",
        background_fill_secondary="#FBF9F5",
        background_fill_secondary_dark="#17140F",
        border_color_primary="#E6E0D6",
        border_color_primary_dark="#302A22",
        button_primary_background_fill="#B4501E",
        button_primary_background_fill_dark="#E0793C",
        button_primary_text_color="#FFFFFF",
        button_primary_text_color_dark="#17140F",
    )


# Rich link previews: OpenGraph and Twitter-card tags so the URL unfurls
# as a proper card in LinkedIn, WhatsApp, and Slack. og:image must be an
# absolute URL to a real file; deploy_modal.py serves it from /static.
OG_TITLE: str = "AskGeorge"
OG_DESCRIPTION: str = (
    "Ask George Traskas about his AI/ML and data science work, "
    "or paste a job description and get an honest fit report."
)
OG_IMAGE_URL: str = f"{PUBLIC_BASE_URL}/media/og_card.jpg"

# The <title> travels with the meta set: Gradio 6 sets the tab title only
# from JavaScript, so crawlers and search engines see no title tag at all.
_META_HEAD: str = (
    f"<title>{OG_TITLE}</title>"
    f'<meta name="description" content="{OG_DESCRIPTION}">'
    '<meta property="og:type" content="website">'
    f'<meta property="og:title" content="{OG_TITLE}">'
    f'<meta property="og:description" content="{OG_DESCRIPTION}">'
    f'<meta property="og:url" content="{PUBLIC_BASE_URL}/">'
    f'<meta property="og:site_name" content="{OG_TITLE}">'
    f'<meta property="og:image" content="{OG_IMAGE_URL}">'
    '<meta property="og:image:width" content="1200">'
    '<meta property="og:image:height" content="630">'
    '<meta property="og:image:alt" content="George Traskas, AI/ML and data science">'
    '<meta name="twitter:card" content="summary_large_image">'
    f'<meta name="twitter:title" content="{OG_TITLE}">'
    f'<meta name="twitter:description" content="{OG_DESCRIPTION}">'
    f'<meta name="twitter:image" content="{OG_IMAGE_URL}">'
)

# Newsreader for the headline, Public Sans for the UI, IBM Plex Mono for
# eyebrows. Loaded here rather than through the Gradio theme so the exact
# weights and the serif italic are available to the custom CSS.
_FONTS_HEAD: str = (
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    "family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400"
    "&family=Public+Sans:wght@400;500;600"
    "&family=IBM+Plex+Mono:wght@400;500"
    '&display=swap">'
)

# Gradio's SPA shell hardcodes its own og:/twitter: tags (Gradio branding,
# an empty thumbnail) ahead of any custom head content, and link crawlers
# honor the first tag they meet, so injecting via ``head`` is not enough.
_SOCIAL_META_RE: re.Pattern[str] = re.compile(
    r'<meta[^>]*(?:property="og:|name="twitter:|name="description")[^>]*>\s*'
    r"|<title[^>]*>[^<]*</title>\s*"
)


def rewrite_social_meta(html: str) -> str:
    """Replace a page's social meta tags with the AskGeorge set.

    Strips every og:/twitter:/description meta tag (Gradio's stock ones and
    any injected copy of ours) and re-inserts the AskGeorge set as the first
    content of ``<head>``, where link crawlers expect it.

    Args:
        html: The full HTML document as served by Gradio.

    Returns:
        The document with exactly one, correctly ordered set of social tags.
    """
    stripped = _SOCIAL_META_RE.sub("", html)
    return stripped.replace("<head>", f"<head>{_META_HEAD}", 1)


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


# Follow the conversation as it streams.
#
# The chatbot is built with no fixed height and a max height, which makes
# the OUTER block the scrolling element. Gradio's own auto-scroll drives an
# inner wrapper it expects to own, so it scrolls a node that does not
# scroll and the view stays pinned to the top: every reply after the first
# rendered below the visible area and never came into view. This drives the
# element that actually scrolls.
#
# Sticks to the newest text only while the visitor is already at the bottom,
# so scrolling up to re-read an earlier answer is not yanked back down. A
# new question re-arms it and pulls the composer into view, which matters on
# a laptop where the hero leaves the input below the fold.
_CHAT_SCROLL_HEAD: str = """
<script>
window.agInitChatScroll = function () {
  var chat = document.getElementById("ag-chat");
  if (!chat || chat.dataset.agScroll === "1") { return; }
  chat.dataset.agScroll = "1";
  var stick = true;
  var pullComposer = false;
  var seenQuestions = chat.querySelectorAll(".user-row").length;
  var atBottom = function () {
    return chat.scrollTop + chat.clientHeight >= chat.scrollHeight - 24;
  };
  chat.addEventListener("scroll", function () { stick = atBottom(); });
  // Our own nudges only ever scroll down, so an upward move is the visitor
  // taking over; stop pulling the page until they ask the next question
  var lastPageY = window.scrollY;
  window.addEventListener("scroll", function () {
    if (window.scrollY < lastPageY - 2) { pullComposer = false; }
    lastPageY = window.scrollY;
  }, { passive: true });
  var follow = function () {
    var questions = chat.querySelectorAll(".user-row").length;
    if (questions < seenQuestions) {
      // Clear chat empties the transcript; without this the counter stays
      // high and no later question ever counts as new
      seenQuestions = questions;
    } else if (questions > seenQuestions) {
      seenQuestions = questions;
      stick = true;
      pullComposer = true;
    }
    if (stick) { chat.scrollTop = chat.scrollHeight; }
    // Checked on every tick, not once per question: when the question lands
    // the box is still short and the composer is on screen, and it is the
    // growing answer that pushes the composer below the fold
    if (pullComposer) {
      var composer = document.getElementById("ag-chat-input");
      if (composer) {
        var below = composer.getBoundingClientRect().bottom + 16 - window.innerHeight;
        if (below > 0) { window.scrollBy(0, below); }
      }
    }
  };
  new MutationObserver(follow).observe(
    chat, { childList: true, subtree: true, characterData: true }
  );
  follow();
};
setTimeout(window.agInitChatScroll, 600);
setTimeout(window.agInitChatScroll, 1600);
setTimeout(window.agInitChatScroll, 3200);
</script>
"""


def serve_kwargs() -> dict[str, Any]:
    """Return the theme/css/head kwargs for ``launch()`` or ``mount_gradio_app()``.

    Gradio 6 applies theme and CSS at serve time, not at Blocks construction.
    """
    return {
        "theme": build_theme(),
        "css": TERRACOTTA_CSS,
        "head": _META_HEAD + _FONTS_HEAD + _THEME_HEAD + _CHAT_SCROLL_HEAD,
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
    return '<p class="ag-wordmark">George Traskas</p>'


def _topbar_right_html() -> str:
    """Build the links + theme-toggle side of the top bar."""
    return f"""
    <div class="ag-topbar-right">
        <span class="ag-divider"></span>
        <a class="ag-link" href="{LINKEDIN_URL}" target="_blank" rel="noopener">LinkedIn</a>
        <a class="ag-link" href="{GITHUB_URL}" target="_blank" rel="noopener">GitHub</a>
        <button id="ag-theme-btn" onclick="agToggleTheme()" title="Switch light / dark"><span id="ag-theme-icon">☾</span></button>
    </div>
    """


def _hero_html() -> str:
    """Build the hero: portrait, headline, support line."""
    photo_uri = _photo_data_uri()
    photo_tag = (
        f'<img class="ag-photo" src="{photo_uri}" alt="George Traskas" />'
        if photo_uri
        else "<span></span>"
    )
    return f"""
    <div id="ag-hero">
        {photo_tag}
        <div>
            <h1 class="ag-hl">Talk to me. Or rather, to <em>my AI</em>.</h1>
            <p class="ag-support">It answers from my own notes. Ask anything,
            or paste a job description for an honest fit report.</p>
        </div>
    </div>
    """


def _proof_strip_html() -> str:
    """Build the three-cell proof strip: current role, shipped app, this page."""
    return f"""
    <div id="ag-proof">
        <div class="ag-proof-cell">
            <p class="ag-proof-eyebrow">Now</p>
            <p class="ag-proof-title">Predictive Fitness</p>
            <p class="ag-proof-body">Cut false alert noise <strong>over 90%</strong>
            with an evidence-gated redesign.</p>
        </div>
        <div class="ag-proof-cell">
            <p class="ag-proof-eyebrow">Shipped</p>
            <p class="ag-proof-title">MolekitChen</p>
            <p class="ag-proof-body">On the App Store.
            <a href="{MOLEKITCHEN_URL}" target="_blank" rel="noopener">See it →</a></p>
        </div>
        <div class="ag-proof-cell">
            <p class="ag-proof-eyebrow">This page</p>
            <p class="ag-proof-title">AskGeorge</p>
            <p class="ag-proof-body">Open-source RAG agent.
            <a href="{REPO_URL}" target="_blank" rel="noopener">Code →</a></p>
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


def _booking_iframe_html(url: str) -> str:
    """Build the embedded Google Calendar iframe for the booking accordion."""
    return (
        f'<iframe src="{_booking_embed_src(url)}" '
        'title="Book an intro call with George"></iframe>'
    )


def _footer_html() -> str:
    """Build the footer: the human route out, plus the AI disclosure."""
    return f"""
    <div id="ag-footer">
        <p class="ag-foot-line">Prefer a human?
        <a href="mailto:{EMAIL_ADDRESS}">Email me</a>.
        Open to senior AI/ML roles, one month notice.</p>
        <p class="ag-disclosure">Answers are AI-generated from my own notes</p>
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
    chat_fn: Callable[..., Any], limiter: RateLimiter
) -> Callable[..., Any]:
    """Wrap the chat function with rate limiting.

    Every visitor message reaches the model: there are no canned replies,
    because the page exists to show how the assistant actually answers.
    """
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


def _write_report_file(markdown: str) -> Path:
    """Write a finished report to its own temp directory for download.

    Each report gets a fresh directory so concurrent visitors can never be
    served each other's analysis, while the file inside keeps a fixed,
    meaningful name because the browser saves it under its basename.

    Args:
        markdown: The completed report.

    Returns:
        Path to the written Markdown file.
    """
    directory = Path(tempfile.mkdtemp(prefix="askgeorge-report-"))
    path = directory / REPORT_FILENAME
    path.write_text(markdown, encoding="utf-8")
    return path


def _jobfit_handler(
    jobfit_fn: Callable[[str], Any], limiter: RateLimiter
) -> Callable[..., Any]:
    """Wrap the job-fit analyzer with the shared rate limiter.

    Yields (report_markdown, analyze_button, download_button) triples. The
    Analyze button reads "Analyzing…" and is disabled while the pipeline
    runs — visible feedback and double-click protection in one — and the
    download appears only once a real report exists, so it never offers a
    progress line or an error message as a file.
    """
    busy = gr.Button(value="Analyzing…", interactive=False)
    ready = gr.Button(value="Analyze fit", interactive=True)
    no_download = gr.DownloadButton(visible=False)

    async def handler(job_description: str, request: gr.Request):
        refusal = limiter.check(_visitor_ip(request))
        if refusal:
            yield refusal, ready, no_download
            return
        last = ""
        async for markdown in jobfit_fn(job_description):
            last = markdown
            yield markdown, busy, no_download
        if REPORT_MARKER not in last:
            yield last, ready, no_download
            return
        path = await asyncio.to_thread(_write_report_file, last)
        yield last, ready, gr.DownloadButton(value=str(path), visible=True)

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

        async def respond_async(
            message: str, history: list | None, request: gr.Request
        ):
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


def _build_chat_panel(
    chat_fn: Callable[..., Any],
) -> tuple[gr.Chatbot, gr.BrowserState]:
    """Assemble the chat tab: chatbot, composer, clear action, prompt pills.

    A custom Blocks chat rather than gr.ChatInterface: the prompt pills must
    submit on click, and external components cannot trigger a ChatInterface
    submission.

    The conversation persists in the visitor's own browser (localStorage
    via gr.BrowserState) — nothing is stored server-side. Each completed
    exchange saves the history; Clear chat wipes screen and storage both.

    Args:
        chat_fn: The wrapped chat callable.

    Returns:
        The chatbot and its browser-persisted history state, so the caller
        can restore the conversation on page load.
    """
    respond = _make_responder(chat_fn)
    # The secret must be stable across server restarts (Modal restarts
    # containers routinely); Gradio's default random secret would make every
    # restart silently wipe visitors' saved conversations.
    saved_history = gr.BrowserState(
        [], storage_key="ag-chat-history", secret="askgeorge-browser-state-v1"
    )
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
        placeholder=COMPOSER_PLACEHOLDER,
        show_label=False,
        submit_btn=True,
        elem_id="ag-chat-input",
    )

    def _save_history(history: list | None) -> list:
        """Persist the finished exchange to the visitor's browser."""
        return history or []

    textbox.submit(respond, inputs=[textbox, chatbot], outputs=[chatbot, textbox]).then(
        _save_history, inputs=[chatbot], outputs=[saved_history]
    )
    with gr.Row(elem_id="ag-chat-actions"):
        clear_button = gr.Button("Clear chat", size="sm", elem_classes="ag-clear")

    def _clear_chat() -> tuple[list, str, list]:
        """Wipe the conversation, the input box, and the stored history."""
        return [], "", []

    clear_button.click(_clear_chat, outputs=[chatbot, textbox, saved_history])

    def _pill_handler(question: str) -> Callable[..., Any]:
        if inspect.isasyncgenfunction(respond):

            async def handler_async(history: list | None, request: gr.Request):
                async for update in respond(question, history, request):
                    yield update

            return handler_async

        def handler_sync(history: list | None, request: gr.Request):
            yield from respond(question, history, request)

        return handler_sync

    gr.HTML('<p class="ag-label">Try one of these</p>')
    with gr.Row(elem_id="ag-qcols"):
        for question in PROMPT_PILLS:
            pill = gr.Button(question, size="sm", elem_classes="ag-q")
            pill.click(
                _pill_handler(question),
                inputs=[chatbot],
                outputs=[chatbot, textbox],
            ).then(_save_history, inputs=[chatbot], outputs=[saved_history])
    return chatbot, saved_history


def build_ui(chat_fn: Callable[..., Any], jobfit_fn: Callable[[str], Any]) -> gr.Blocks:
    """Assemble the complete AskGeorge page: chat plus job-fit analysis.

    Args:
        chat_fn: Streaming chat callable with the (message, history) signature.
        jobfit_fn: Async generator taking a job description and yielding
            Markdown progress then the final report.

    Returns:
        A :class:`gr.Blocks` page; serve it with :func:`serve_kwargs` applied.
    """
    limiter = RateLimiter()
    chat_fn = _wrap_chat(chat_fn, limiter)
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
                gr.DownloadButton(label, value=str(path), size="sm", elem_classes="ag-cv")
            gr.HTML(_topbar_right_html())
        gr.HTML(_hero_html())
        with gr.Tabs():
            with gr.Tab("Ask me anything"):
                chatbot, saved_history = _build_chat_panel(chat_fn)
            with gr.Tab("Check a job fit"):
                gr.HTML(
                    '<p id="ag-jobfit-intro">Paste a job description. You get a '
                    "requirement-by-requirement read on where I fit, where I "
                    "don't, and what I'd need to learn.</p>"
                )
                job_description = gr.Textbox(
                    show_label=False,
                    placeholder="Paste the full job description here…",
                    lines=12,
                    elem_id="ag-jobfit-box",
                )
                with gr.Row(elem_id="ag-jobfit-actions"):
                    analyze_button = gr.Button("Analyze fit", elem_classes="ag-primary")
                    clear_button = gr.ClearButton(
                        value="Clear for a new analysis", elem_classes="ag-clear"
                    )
                report = gr.Markdown(elem_id="ag-jobfit-report")
                download_button = gr.DownloadButton(
                    "Download report (.md)",
                    visible=False,
                    elem_classes="ag-download",
                )
                clear_button.add([job_description, report])
                clear_button.click(
                    lambda: gr.DownloadButton(visible=False),
                    outputs=[download_button],
                )
                analyze_button.click(
                    fn=jobfit_handler,
                    inputs=[job_description],
                    outputs=[report, analyze_button, download_button],
                )
        calendar_url = booking_url()
        if calendar_url:
            with gr.Accordion("Book an intro call", open=False, elem_id="ag-book"):
                gr.HTML(_booking_iframe_html(calendar_url))
        gr.HTML(_proof_strip_html())
        gr.HTML(_footer_html())

        def _restore_session(saved: list | None) -> list:
            """Bring the stored conversation back on page load."""
            return saved or []

        demo.load(_restore_session, inputs=[saved_history], outputs=[chatbot])
    return demo
