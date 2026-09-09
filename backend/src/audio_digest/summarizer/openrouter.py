"""OpenRouter-backed Summarizer: one API key, many swappable models.

Uses the OpenAI-compatible chat completions endpoint OpenRouter exposes, with
JSON-schema-constrained structured output so the response validates directly
against the Script model, same as the Claude implementation.
"""

import logging
from datetime import date

from openai import OpenAI

from audio_digest.models import Article, Script
from audio_digest.summarizer.base import Summarizer
from audio_digest.summarizer.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, render_article

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "google/gemini-2.5-flash"
MAX_RETRIES = 2


class OpenRouterSummarizer(Summarizer):
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, client: OpenAI | None = None):
        self._client = client or OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)
        self._model = model

    def summarize(self, articles: list[Article], digest_date: date) -> Script:
        schema = Script.model_json_schema()
        system_prompt = SYSTEM_PROMPT.format(schema=schema)
        articles_block = "\n".join(
            render_article(
                i,
                article.title,
                article.source,
                article.full_text or article.summary_raw,
                str(article.url),
            )
            for i, article in enumerate(articles, start=1)
        )
        user_prompt = USER_PROMPT_TEMPLATE.format(
            digest_date=digest_date.isoformat(), articles_block=articles_block
        )

        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 2):
            try:
                raw_json = self._request_script_json(system_prompt, user_prompt, schema)
                return Script.model_validate_json(raw_json)
            except Exception as exc:  # validation error or malformed response
                last_error = exc
                logger.warning("Summarizer attempt %d/%d failed: %s", attempt, MAX_RETRIES + 1, exc)

        raise RuntimeError("OpenRouter summarizer failed to produce a valid Script") from last_error

    def _request_script_json(
        self, system_prompt: str, user_prompt: str, schema: dict[str, object]
    ) -> str:
        # Not every model routed through OpenRouter supports structured
        # outputs; an unsupported model surfaces as an API error here, which
        # the retry loop in summarize() catches and reports like any other
        # failure. Pick a model with structured-output support (Gemini and
        # GPT families both have it) to avoid burning retries on this.
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "digest_script", "schema": schema, "strict": True},
            },
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("OpenRouter response had no content")
        return content
