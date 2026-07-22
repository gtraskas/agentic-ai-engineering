"""George's background documents: the knowledge the assistant is allowed to claim."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from askgeorge.core.config import DATA_DIR

SUMMARY_FILENAME: str = "summary.md"
SUPPORTED_SUFFIXES: tuple[str, ...] = (".md", ".txt")


@dataclass(frozen=True)
class Profile:
    """George's background corpus.

    Attributes:
        summary: Distilled professional summary, always pinned in the prompt.
        documents: Remaining background documents, keyed by relative file path.
    """

    summary: str
    documents: dict[str, str]

    @classmethod
    def load(cls, data_dir: Path = DATA_DIR) -> Profile:
        """Load the summary and every other document under ``data_dir``.

        Includes the gitignored ``private/`` subdirectory when present, so
        personal extras feed the assistant without being published to GitHub.

        Args:
            data_dir: Directory containing summary.md and background documents.

        Returns:
            A populated :class:`Profile`.

        Raises:
            FileNotFoundError: If summary.md is missing.
        """
        summary = (data_dir / SUMMARY_FILENAME).read_text(encoding="utf-8")
        documents: dict[str, str] = {}
        for path in sorted(data_dir.rglob("*")):
            if path.suffix not in SUPPORTED_SUFFIXES or path.name == SUMMARY_FILENAME:
                continue
            documents[str(path.relative_to(data_dir))] = path.read_text(encoding="utf-8")
        return cls(summary=summary, documents=documents)

    def full_corpus(self) -> str:
        """Return every non-summary document merged into one context block."""
        return "\n\n".join(
            f"## {name}\n\n{content}" for name, content in self.documents.items()
        )
