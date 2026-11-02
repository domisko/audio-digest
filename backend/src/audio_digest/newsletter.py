"""Renders a Script as plain-text newsletter copy — the same content as the
audio, for anyone who'd rather read the digest (via the API or Telegram).
"""

from audio_digest.models import Script


def render_newsletter_text(script: Script) -> str:
    lines = [script.intro, ""]
    for segment in script.segments:
        lines.append(segment.headline)
        lines.append(segment.summary_short)
        if len(segment.sources) > 1:
            lines.extend(f"({source.name}) {source.url}" for source in segment.sources)
        elif segment.source_name:
            lines.append(f"({segment.source_name}) {segment.source_article_url}")
        else:
            lines.append(str(segment.source_article_url))
        lines.append("")
    lines.append(script.outro)
    return "\n".join(lines)
