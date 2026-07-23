"""AskGeorge entry point: wire the configured agent into the Aegean Minimal UI.

Run locally with::

    uv run python -m askgeorge.app
"""

from __future__ import annotations

import logging

import gradio as gr
from dotenv import load_dotenv

from askgeorge.core import create_app_components
from askgeorge.ui.theme import build_ui, serve_kwargs


def build_demo() -> gr.Blocks:
    """Create the complete AskGeorge Gradio app.

    Returns:
        A :class:`gr.Blocks` page; serve it with ``serve_kwargs()`` applied.
    """
    load_dotenv(override=True)
    logging.basicConfig(level=logging.INFO)
    agent, analyzer = create_app_components()
    return build_ui(agent.chat, analyzer.analyze)


if __name__ == "__main__":
    build_demo().launch(**serve_kwargs())
