"""Retrieval golden-set eval: assert the RAG layer finds the right chunks.

Runs without any LLM call — each golden question must retrieve a context
containing its expected needle string. Wired into CI so a chunking, corpus,
or retrieval change that silently breaks recall fails the build.

Run locally with::

    uv run python tests/retrieval_eval.py
"""

from __future__ import annotations

import sys

from askgeorge.core.knowledge import build_knowledge
from askgeorge.core.profile import Profile

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
]


def main() -> int:
    """Run every golden question and report misses.

    Returns:
        Process exit code: 0 when all needles are retrieved, 1 otherwise.
    """
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
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
