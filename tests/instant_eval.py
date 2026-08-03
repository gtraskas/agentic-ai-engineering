"""Instant FAQ eval: assert the matcher hits its targets and nothing else.

Runs without any LLM call or RAG index. Two golden sets: phrasings that must
return an instant answer (exact triggers, chip questions, typos, paraphrases
within the fuzzy bar) and messages that must fall through to the full
pipeline (substantive, off-topic, or merely similar-looking questions).
A false positive here means a visitor gets a canned answer to a question it
does not fit — worse than no instant answer at all.

Run locally with::

    uv run python tests/instant_eval.py
"""

from __future__ import annotations

import sys

from askgeorge.core.instant import InstantFAQ

# Messages that must return an instant answer, with a substring the
# answer must contain — guards against triggers mapped to the wrong entry.
MUST_MATCH: list[tuple[str, str]] = [
    ("What do you do?", "8 years"),
    ("what do you do", "8 years"),
    ("What's your professional background?", "Predictive Fitness"),
    ("Are you open to remote roles?", "remote is my default"),
    ("are you open to remote roles??", "remote is my default"),
    ("Where are you based?", "Thessaloniki"),
    ("What is your notice period?", "one month"),
    ("When can you start?", "four weeks"),
    ("What is your availability and notice period?", "one month"),
    ("Tell me about your most recent project.", "AskGeorge"),
    ("Tell me about your most recent project", "AskGeorge"),
    ("What do your clients say about working with you?", "Top Rated Plus"),
    ("Why should we hire you as an AI engineer?", "survive production"),
    ("What is your experience with RAG in production?", "MolekitChen"),
    ("What is your experiense with RAG in production?", "MolekitChen"),
    ("Can I talk to the real George?", "Book an intro call"),
    ("How can I contact George?", "georgiost77@gmail.com"),
]

# Messages that must NOT match: substantive questions deserving the full
# RAG pipeline, off-topic input, and near-miss phrasings whose intent
# differs from any canned answer.
MUST_PASS_THROUGH: list[str] = [
    "What is your experience with Kubernetes?",
    "Why should we hire you as a data scientist over other candidates with PhD?",
    "Tell me about your most difficult project.",
    "What do you think about the future of AI?",
    "Are you open to relocating to Berlin?",
    "How does the MCP server you built work?",
    "What is RAG?",
    "Can you tell me about your salary expectations?",
    "hello",
    "",
]


def main() -> int:
    """Run both golden sets and report failures.

    Returns:
        Process exit code: 0 when every case behaves, 1 otherwise.
    """
    faq = InstantFAQ()
    failures: list[str] = []
    from askgeorge.ui.theme import FAQ_PILLS, LIVE_AI_QUESTIONS

    for pill in FAQ_PILLS:
        if faq.match(pill) is None:
            failures.append(f"UI DRIFT: FAQ pill {pill!r} has no instant answer")
    for pill in LIVE_AI_QUESTIONS:
        if faq.match(pill) is not None:
            failures.append(f"UI DRIFT: live-AI pill {pill!r} is answered instantly")
    for message, needle in MUST_MATCH:
        reply = faq.match(message)
        if reply is None:
            failures.append(f"NO MATCH: {message!r} - expected an instant answer")
        elif needle not in reply:
            failures.append(f"WRONG ANSWER: {message!r} - expected needle {needle!r}")
    for message in MUST_PASS_THROUGH:
        if faq.match(message) is not None:
            failures.append(f"FALSE POSITIVE: {message!r} - must reach the LLM")
    total = (
        len(MUST_MATCH)
        + len(MUST_PASS_THROUGH)
        + len(FAQ_PILLS)
        + len(LIVE_AI_QUESTIONS)
    )
    print(f"instant eval: {total - len(failures)}/{total} passed")
    for failure in failures:
        print(f"  {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
