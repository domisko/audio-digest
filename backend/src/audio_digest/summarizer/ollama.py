"""Ollama Summarizer — not yet implemented.

Would run against a local model using Ollama's `format=` JSON-mode parameter,
passing Script.model_json_schema() to constrain the output the same way.
"""

from datetime import date

from audio_digest.models import Article, Script
from audio_digest.summarizer.base import Summarizer


class OllamaSummarizer(Summarizer):
    def __init__(self, model: str = "llama3.1", host: str = "http://localhost:11434"):
        self._model = model
        self._host = host

    def summarize(self, articles: list[Article], digest_date: date) -> Script:
        raise NotImplementedError("Ollama summarizer is not implemented yet")
