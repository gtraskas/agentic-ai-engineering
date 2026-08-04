"""Retrieval golden-set eval: assert the RAG layer finds the right chunks.

Runs without any LLM call — each golden question must retrieve a context
containing its expected needle string. Wired into CI so a chunking, corpus,
or retrieval change that silently breaks recall fails the build.

Every prompt pill offered in the UI is also asserted to be in the golden
set. The pills are the first thing most visitors click, and every one of
them now goes through the live RAG + LLM path, so a pill whose retrieval
is unproven is a pill that can embarrass the page on first contact.

Run locally with::

    uv run python tests/retrieval_eval.py
"""

from __future__ import annotations

import sys

from askgeorge.core.knowledge import build_knowledge
from askgeorge.core.profile import Profile
from askgeorge.ui.theme import PROMPT_PILLS

# (recruiter-style question, substring that must appear in retrieved context)
GOLDEN_SET: list[tuple[str, str]] = [
    ("What is your notice period and when can you start?", "one month"),
    ("What do your clients say about working with you?", "[source: testimonials.md]"),
    ("How did you reduce alert noise at Predictive Fitness?", "Evidence gates"),
    ("Why did you choose an in-memory vector store for AskGeorge?", "In-memory Qdrant over a hosted"),
    ("How does MolekitChen manage its token budget?", "7,000"),
    ("How do you prevent hallucinations in production?", "citation cross-validation"),
    ("Do you know Kubernetes?", "ECS Fargate"),
    ("Do you have Terraform or infrastructure-as-code experience?", "SST"),
    ("Can you overlap with US timezones?", "Central time"),
    ("What agents make up Wine-VFM?", "ScannerAgent"),
    ("How do you roll out a new model to production safely?", "shadow"),
    ("Tell me about your embedded machine learning experience.", "quantization"),
    ("How does your causal inference work help marketing teams?", "Double Machine Learning"),
    ("Do you have scientific publications?", "Separation Science"),
    ("How do you structure a FastAPI application?", "routers per domain"),
    ("What is your university education?", "Aristotle"),
    ("What went wrong with tool selection in the MCP server?", "golden query set"),
    ("What did you do at CERTH?", "throughput"),
    ("How do you handle imbalanced datasets?", "SMOTE"),
    ("How do you keep LLM API costs under control?", "Two-tier"),
    ("How do you test non-deterministic agent behaviour?", "semantic similarity"),
    ("What certifications do you hold?", "[source: linkedin.md]"),
    ("How does the job-fit analysis work?", "anti-flattery"),
    # UI prompt pills, verbatim — see PROMPT_PILLS.
    ("Tell me about your most recent project.", "[source: projects.md]"),
    ("What is your notice period?", "one month"),
]

# Prompt pills that no retrieval assertion can cover, because retrieval is
# not what answers them: "What do you do?" is served by the pinned profile
# summary in the system prompt, and "Can I talk to the real George?" by the
# contact rule and the contact tool. Listing them explicitly means adding a
# seventh pill still forces a deliberate choice rather than silently
# shipping a question nothing verifies.
PROMPT_ANSWERED_PILLS: set[str] = {
    "What do you do?",
    "Can I talk to the real George?",
}


def _uncovered_pills() -> list[str]:
    """Return UI prompt pills that are neither in the golden set nor waived."""
    covered = {question for question, _ in GOLDEN_SET} | PROMPT_ANSWERED_PILLS
    return [pill for pill in PROMPT_PILLS if pill not in covered]


def main() -> int:
    """Run every golden question and report misses.

    Returns:
        Process exit code: 0 when all needles are retrieved and every UI
        prompt pill is covered by the golden set, 1 otherwise.
    """
    drifted = _uncovered_pills()
    for pill in drifted:
        print(f"  UI DRIFT: prompt pill {pill!r} is not in the golden set")

    knowledge = build_knowledge(Profile.load())
    failures: list[tuple[str, str]] = []
    for question, needle in GOLDEN_SET:
        context = knowledge.context_for(question)
        if needle not in context:
            failures.append((question, needle))
    passed = len(GOLDEN_SET) - len(failures)
    print(f"retrieval eval: {passed}/{len(GOLDEN_SET)} passed")
    for question, needle in failures:
        print(f"  MISS: {question!r} — expected needle {needle!r}")
    return 1 if failures or drifted else 0


if __name__ == "__main__":
    sys.exit(main())
