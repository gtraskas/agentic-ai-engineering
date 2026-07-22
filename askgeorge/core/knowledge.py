"""Background knowledge retrieval: in-memory Qdrant RAG with a full-context fallback."""

from __future__ import annotations

import logging

from askgeorge.core.config import (
    CHUNK_MAX_CHARS,
    EMBEDDING_MODEL,
    RAG_COLLECTION,
    RAG_TOP_K,
    rag_enabled,
)
from askgeorge.core.profile import Profile

logger = logging.getLogger(__name__)


class BackgroundKnowledge:
    """Provides the background context for a visitor question.

    Base implementation returns the full corpus every time — correct at any
    corpus size, at the cost of prompt tokens.
    """

    def __init__(self, profile: Profile) -> None:
        self._profile = profile

    def context_for(self, query: str) -> str:
        """Return the background context relevant to ``query``."""
        del query
        return self._profile.full_corpus()


class QdrantKnowledge(BackgroundKnowledge):
    """Retrieves top-k background chunks from an in-memory Qdrant collection.

    Documents are chunked by paragraph, embedded locally with FastEmbed
    (no API calls), and indexed at startup — nothing is persisted to disk.
    """

    def __init__(self, profile: Profile) -> None:
        super().__init__(profile)
        from qdrant_client import QdrantClient

        self._client = QdrantClient(":memory:")
        self._client.set_model(EMBEDDING_MODEL)
        chunks = self._chunk_corpus(profile)
        self._client.add(
            collection_name=RAG_COLLECTION,
            documents=[chunk_text for _, chunk_text in chunks],
            metadata=[{"source": source} for source, _ in chunks],
        )
        logger.info("Indexed %d background chunks in Qdrant (:memory:)", len(chunks))

    def context_for(self, query: str) -> str:
        """Return the top-k chunks most relevant to ``query``."""
        hits = self._client.query(
            collection_name=RAG_COLLECTION, query_text=query, limit=RAG_TOP_K
        )
        return "\n\n---\n\n".join(
            f"[source: {hit.metadata.get('source', 'unknown')}]\n{hit.document}"
            for hit in hits
        )

    @staticmethod
    def _chunk_corpus(profile: Profile) -> list[tuple[str, str]]:
        """Split every document into paragraph-aligned chunks of bounded size."""
        chunks: list[tuple[str, str]] = []
        for source, content in profile.documents.items():
            current = ""
            for paragraph in content.split("\n\n"):
                if current and len(current) + len(paragraph) > CHUNK_MAX_CHARS:
                    chunks.append((source, current.strip()))
                    current = ""
                current += paragraph + "\n\n"
            if current.strip():
                chunks.append((source, current.strip()))
        return chunks


def build_knowledge(profile: Profile) -> BackgroundKnowledge:
    """Build the configured knowledge provider, degrading gracefully.

    Args:
        profile: The loaded background corpus.

    Returns:
        :class:`QdrantKnowledge` when RAG is enabled and its dependencies are
        available; the full-context :class:`BackgroundKnowledge` otherwise.
    """
    if not rag_enabled():
        logger.info("RAG disabled via ASKGEORGE_RAG=0; using full-context mode.")
        return BackgroundKnowledge(profile)
    try:
        return QdrantKnowledge(profile)
    except ImportError as exc:
        logger.warning("Qdrant/FastEmbed unavailable (%s); using full context.", exc)
        return BackgroundKnowledge(profile)
