"""Search-query normalization: make non-English questions findable.

The background corpus is English and the embedding model
(``BAAI/bge-small-en-v1.5``) is English-only, so a question asked in Greek
or German embeds poorly against it. Retrieval returns weak chunks and the
model then answers fluently from thin context, which reads worse than an
honest "that is not something I have written up here".

This translates the question into English for the retrieval step only. The
visitor's own words still reach the model, which replies in their language.

Questions that are already English skip the call entirely, so the common
case costs nothing and adds no latency.
"""

from __future__ import annotations

import logging
import re

from openai import OpenAI, OpenAIError

from askgeorge.core.config import (
    CHAT_MODEL,
    OPENROUTER_BASE_URL,
    openrouter_api_key,
    openrouter_extra_body,
)

logger = logging.getLogger(__name__)

MAX_QUERY_CHARS: int = 600

_TRANSLATE_INSTRUCTIONS: str = (
    "Translate the user's message into English. Return ONLY the translation, "
    "with no quotes, notes, or explanation. Keep names of people, companies, "
    "products, and technologies exactly as written. If the message is already "
    "English, return it unchanged."
)

# Function words that appear in almost every natural English question and
# are not shared with the languages most likely to turn up here. A single
# hit is enough to treat the message as English and skip the call. Words
# that also occur in German or Dutch ("in", "of", "for", "is") are left out
# on purpose: a false "English" verdict silently degrades retrieval, while
# a false "not English" verdict only costs one cheap call that returns the
# text unchanged.
_ENGLISH_MARKERS: frozenset[str] = frozenset(
    {
        "the", "what", "what's", "how", "why", "when", "where", "which", "who",
        "you", "your", "you're", "yourself", "do", "does", "did", "don't",
        "are", "aren't", "was", "were", "can", "can't", "could", "would",
        "should", "have", "haven't", "has", "had", "tell", "about", "me",
        "my", "i", "i'm", "please", "any", "some", "there", "their", "they",
        "much", "many", "most", "been", "being", "know", "think", "want",
    }
)

_WORDS = re.compile(r"[a-z][a-z']*")


class SearchQueryTranslator:
    """Turns a visitor's question into an English query for retrieval.

    Attributes:
        model: The OpenRouter model used for the translation call.
    """

    def __init__(self, client: OpenAI | None = None) -> None:
        self.model = CHAT_MODEL
        self._client = client or OpenAI(
            base_url=OPENROUTER_BASE_URL, api_key=openrouter_api_key()
        )

    def to_english(self, message: str) -> str:
        """Return an English form of ``message`` for the retrieval step.

        Fails open: any error returns the original text, so a translation
        outage degrades retrieval rather than breaking the answer.

        Args:
            message: The visitor's raw question, in any language.

        Returns:
            The English translation, or the original text when it is
            already English or the translation call fails.
        """
        text = (message or "").strip()
        if not text or self.looks_english(text):
            return text
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _TRANSLATE_INSTRUCTIONS},
                    {"role": "user", "content": text[:MAX_QUERY_CHARS]},
                ],
                temperature=0.0,
                extra_body=openrouter_extra_body(),
            )
            translated = (response.choices[0].message.content or "").strip()
        except (OpenAIError, OSError) as exc:
            logger.warning("Query translation failed, searching as typed: %s", exc)
            return text
        if not translated:
            return text
        logger.info("Translated a non-English question for retrieval.")
        return translated

    @staticmethod
    def looks_english(text: str) -> bool:
        """Return True when the text carries a common English function word.

        Args:
            text: The visitor's raw question.

        Returns:
            True if the message is confidently English and needs no
            translation before retrieval.
        """
        return bool(set(_WORDS.findall(text.lower())) & _ENGLISH_MARKERS)
