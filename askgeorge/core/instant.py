"""Instant FAQ answers: canned first-person replies with zero LLM latency.

The most common recruiter questions ("what do you do?", "are you open to
remote?") have stable, authoritative answers in George's background corpus.
Matching them here returns a curated reply immediately — no retrieval, no
model call, no API cost — and leaves the rate-limit budget untouched.

Matching is deliberately conservative: a normalized exact match against a
curated trigger list, plus a high-similarity fuzzy match to absorb typos.
Anything below the bar goes to the full RAG + LLM pipeline, because a canned
answer to a question it does not quite fit reads worse than a slower real one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

INSTANT_MARKER: str = "⚡ *Instant answer*\n\n"

_FUZZY_THRESHOLD: float = 0.90

_NON_ALNUM = re.compile(r"[^a-z0-9\s]+")
_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class InstantEntry:
    """One canned answer and the visitor phrasings that trigger it.

    Attributes:
        triggers: Question phrasings that map to this answer; matched
            after normalization, so punctuation and case do not matter.
        answer: The full first-person reply, in Markdown.
    """

    triggers: tuple[str, ...]
    answer: str


class InstantFAQ:
    """Matches visitor messages against curated instant answers.

    Attributes:
        entries: The instant-answer catalog this matcher searches.
    """

    def __init__(self, entries: tuple[InstantEntry, ...] | None = None) -> None:
        self.entries = entries if entries is not None else INSTANT_ENTRIES
        self._catalog: list[tuple[str, str]] = [
            (self._normalize(trigger), entry.answer)
            for entry in self.entries
            for trigger in entry.triggers
        ]

    def match(self, message: str) -> str | None:
        """Return the instant answer for a message, or None to use the LLM.

        Args:
            message: The visitor's raw chat message.

        Returns:
            The matched answer prefixed with the instant marker, or None
            when no trigger matches closely enough.
        """
        normalized = self._normalize(message)
        if not normalized:
            return None
        for trigger, answer in self._catalog:
            if normalized == trigger:
                return INSTANT_MARKER + answer
        for trigger, answer in self._catalog:
            if SequenceMatcher(None, normalized, trigger).ratio() >= _FUZZY_THRESHOLD:
                return INSTANT_MARKER + answer
        return None

    @staticmethod
    def _normalize(text: str) -> str:
        """Lowercase, strip punctuation, and collapse whitespace."""
        lowered = _NON_ALNUM.sub(" ", text.lower())
        return _WHITESPACE.sub(" ", lowered).strip()


INSTANT_ENTRIES: tuple[InstantEntry, ...] = (
    InstantEntry(
        triggers=(
            "What do you do?",
            "What's your professional background?",
            "Tell me about yourself.",
            "Who are you?",
            "Introduce yourself.",
        ),
        answer=(
            "I'm George Traskas, a Data Scientist and AI/ML Engineer based in "
            "Thessaloniki, Greece, with 8 years of experience building "
            "production-grade data science and AI systems in Python. For the "
            "last four years I've worked with Predictive Fitness (US, remote), "
            "building ML pipelines and AWS data workflows over athlete fitness "
            "telemetry, plus agentic infrastructure like their MCP server. "
            "Alongside that I've completed 90+ consulting engagements on "
            "Upwork with a 100% Job Success Score.\n\n"
            "I'm now looking for a full-time senior AI/ML role with real "
            "end-to-end ownership. Ask me about any of my projects — or paste "
            "a job description in the **Analyze a job fit** tab and I'll give "
            "you an honest, evidence-backed read on how well I match."
        ),
    ),
    InstantEntry(
        triggers=(
            "Are you open to remote roles?",
            "Do you work remotely?",
            "Where are you based?",
            "What is your location?",
        ),
        answer=(
            "Yes — remote is my default. I've worked fully remote for four "
            "years with a US team on Central time, so my schedule already "
            "overlaps with US mornings. I'm based in Thessaloniki, Greece "
            "(EU citizen), with a dedicated home office and stable fiber.\n\n"
            "For intro calls I'm available weekday evenings 18:00–22:00 "
            "Athens time — that's 11:00–15:00 US Eastern and 08:00–12:00 US "
            "Pacific, so both European and US teams can book comfortably "
            "using the calendar at the bottom of this page."
        ),
    ),
    InstantEntry(
        triggers=(
            "What is your notice period?",
            "What's your availability?",
            "When can you start?",
            "How soon can you start?",
            "What is your availability and notice period?",
        ),
        answer=(
            "My notice period is one month — I can start about four weeks "
            "after an offer. I'm currently with Predictive Fitness part-time "
            "(full time May 2022 to May 2026), and my consulting engagements "
            "stop for a full-time role: the goal is to go deep on one hard "
            "problem with a strong team. Contractor or employee both work "
            "for me — I've contracted for years; the terms just need to be "
            "clear before signing."
        ),
    ),
    InstantEntry(
        triggers=(
            "Tell me about your most recent project.",
            "What is your latest project?",
            "What are you working on now?",
            "What have you built recently?",
        ),
        answer=(
            "My most recent project is the assistant you're talking to right "
            "now — **AskGeorge**, a production agentic AI app with two "
            "switchable backends (a from-scratch tool-calling loop and the "
            "OpenAI Agents SDK), hybrid BM25 + dense RAG in Qdrant, a "
            "parallel LLM guardrail, a structured job-fit pipeline, and "
            "CI/CD onto serverless Modal. The code is open source.\n\n"
            "Just before it: **Wine-VFM**, an autonomous multi-agent bargain "
            "hunter combining a QLoRA fine-tuned Llama 3.2 3B, RAG over ~88K "
            "tasting notes, and a neural network under an LLM planner (live "
            "demo on Modal); and **MolekitChen**, a RAG food-science iOS app "
            "grounded in peer-reviewed research, live on the App Store. "
            "Links to all three are in the header above — happy to go deep "
            "on any of them."
        ),
    ),
    InstantEntry(
        triggers=(
            "What do your clients say about working with you?",
            "Do you have references?",
            "Do you have testimonials?",
        ),
        answer=(
            "I'm Top Rated Plus on Upwork — top 3% of performers — with a "
            "100% Job Success Score across 90+ engagements. The tags clients "
            "choose most often: Clear Communicator, Committed to Quality, "
            "Collaborative, Solution Oriented, Reliable.\n\n"
            "A few in their own words: a Houston healthcare CEO wrote \"He is "
            "prompt, extremely competent, gets it right very quickly, and "
            "does a very very high quality job.\" Another client highlighted "
            "what I value most: \"Best of all is Georgios' honesty regarding "
            "his limitations — which is sadly rare in freelancing.\" My "
            "largest engagement — four years with Predictive Fitness, "
            "thousands of hours — is rated 5.0. Ask me about testimonials "
            "for any specific kind of work."
        ),
    ),
    InstantEntry(
        triggers=(
            "Why should we hire you as an AI engineer?",
            "Why should we hire you?",
            "What makes you a good fit?",
        ),
        answer=(
            "Because I build AI systems that survive production. Domains "
            "change — sports science, food science, energy, healthcare — but "
            "the work is the same: get the data right, ground the model, "
            "monitor it, know how it fails. My single strongest area is "
            "production retrieval and agent systems in Python on AWS.\n\n"
            "The evidence is shipped and public: an MCP server taken from "
            "Python proof-of-concept to production, a causal scoring pipeline "
            "running daily, a RAG iOS app live on the App Store, a "
            "multi-agent system with a fine-tuned LLM, and this assistant "
            "itself. And I'm honest about limits — clients call that out in "
            "reviews — so when I say something will work, it does. Paste "
            "your job description in the **Analyze a job fit** tab for a "
            "requirement-by-requirement answer."
        ),
    ),
    InstantEntry(
        triggers=(
            "What is your experience with RAG in production?",
            "Have you built RAG systems?",
            "Do you have RAG experience?",
        ),
        answer=(
            "Four shipped systems, each with a different production "
            "constraint:\n\n"
            "- **MolekitChen** (live on the App Store): hybrid BM25 + vector "
            "retrieval with Reciprocal Rank Fusion over 1,600+ peer-reviewed "
            "papers in pgvector, sub-50ms retrieval, a golden-dataset "
            "evaluation gate that blocks deployment if faithfulness drops.\n"
            "- **Predictive Fitness MCP server** (in production): a RAG "
            "layer for training-metric knowledge inside a TypeScript MCP "
            "server serving real athletes.\n"
            "- **Wine-VFM** (live demo): RAG over ~88K embedded tasting "
            "notes feeding a frontier LLM, as one estimator in a fitted "
            "ensemble.\n"
            "- **AskGeorge** (this app): hybrid dense + BM25 retrieval fused "
            "in Qdrant with local FastEmbed embeddings and a retrieval "
            "golden-set eval gating every deploy.\n\n"
            "Ask me about any design decision — chunking, hybrid fusion, "
            "hallucination control, or evaluation."
        ),
    ),
    InstantEntry(
        triggers=(
            "Can I talk to the real George?",
            "How can I contact George?",
            "How do I get in touch?",
            "How can I contact you?",
        ),
        answer=(
            "Three ways, pick what suits you:\n\n"
            "- **Book an intro call** directly in the calendar at the bottom "
            "of this page — weekday evenings 18:00–22:00 Athens time, which "
            "works for both European and US teams.\n"
            "- **Email** [georgiost77@gmail.com](mailto:georgiost77@gmail.com) "
            "or message me on "
            "[LinkedIn](https://www.linkedin.com/in/george-traskas/).\n"
            "- **Leave your email here in chat** with a line about your role "
            "and company — I get notified immediately and reply personally."
        ),
    ),
)
