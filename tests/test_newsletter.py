from datetime import date

from audio_digest.models import Script, ScriptSegment
from audio_digest.newsletter import render_newsletter_text


def test_render_newsletter_text_includes_intro_segments_and_outro() -> None:
    script = Script(
        digest_date=date.today(),
        intro="Guten Morgen",
        segments=[
            ScriptSegment(
                source_article_url="https://example.com/a",
                source_name="Tagesschau",
                headline="Headline A",
                narration="N",
                summary_short="Summary A",
            )
        ],
        outro="Bis morgen",
        full_text="Guten Morgen N Bis morgen",
    )

    text = render_newsletter_text(script)

    assert "Guten Morgen" in text
    assert "Headline A" in text
    assert "Summary A" in text
    assert "(Tagesschau) https://example.com/a" in text
    assert "Bis morgen" in text
