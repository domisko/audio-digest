"""Claude-backed Summarizer using structured (tool-forced) JSON output."""

import json
import logging
from datetime import date

import anthropic

from audio_digest.models import Article, Script
from audio_digest.summarizer.base import Summarizer
from audio_digest.summarizer.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, render_article

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-5"
MAX_RETRIES = 2

# Anthropic tool schemas don't want the top-level "title"/"$defs" noise that
# model_json_schema() emits for nested models is fine to keep; Claude tool-use
# accepts standard JSON Schema.
_SCRIPT_TOOL_NAME = "emit_script"


class ClaudeSummarizer(Summarizer):
    def __init__(
        self, api_key: str, model: str = DEFAULT_MODEL, client: anthropic.Anthropic | None = None
    ):
        self._client = client or anthropic.Anthropic(api_key=api_key)
        self._model = model

    def summarize(self, articles: list[Article], digest_date: date) -> Script:
        schema = Script.model_json_schema()
        system_prompt = SYSTEM_PROMPT.format(schema=json.dumps(schema))
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
                raw_json = self._request_script_json(system_prompt, user_prompt)
                return Script.model_validate_json(raw_json)
            except Exception as exc:  # validation error or malformed tool call
                last_error = exc
                logger.warning("Summarizer attempt %d/%d failed: %s", attempt, MAX_RETRIES + 1, exc)

        raise RuntimeError("Claude summarizer failed to produce a valid Script") from last_error

    def _request_script_json(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system_prompt,
            tools=[
                {
                    "name": _SCRIPT_TOOL_NAME,
                    "description": "Emit the finished digest script.",
                    "input_schema": Script.model_json_schema(),
                }
            ],
            tool_choice={"type": "tool", "name": _SCRIPT_TOOL_NAME},
            messages=[{"role": "user", "content": user_prompt}],
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == _SCRIPT_TOOL_NAME:
                return json.dumps(block.input)
        raise RuntimeError("Claude response did not include the expected tool_use block")
