"""Summarizer interface — implementations are interchangeable via SUMMARIZER_PROVIDER."""

from abc import ABC, abstractmethod
from datetime import date

from audio_digest.models import Article, Script


class Summarizer(ABC):
    @abstractmethod
    def summarize(self, articles: list[Article], digest_date: date) -> Script:
        """Turn today's articles into a spoken-style Script with structured segments."""
        raise NotImplementedError
