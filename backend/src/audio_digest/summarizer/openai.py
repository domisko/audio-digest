"""OpenAI Summarizer — not yet implemented.

Would use `response_format={"type": "json_schema", "json_schema": Script.model_json_schema()}`
with the Chat Completions or Responses API to get the same structured Script output
as the Claude implementation.
"""

from datetime import date

from audio_digest.models import Article, Script
from audio_digest.summarizer.base import Summarizer


class OpenAISummarizer(Summarizer):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self._api_key = api_key
        self._model = model

    def summarize(self, articles: list[Article], digest_date: date) -> Script:
        raise NotImplementedError("OpenAI summarizer is not implemented yet")
