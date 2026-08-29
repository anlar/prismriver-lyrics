import re

from prismriver_lyrics.models import LyricsResult, SyncedLyrics
from prismriver_lyrics.plugins.base import DEFAULT_QUALITY
from prismriver_lyrics.registry import default_plugins

# Accepted values for the CLI/TUI --sort option.
SORT_CHOICES = ("rank", "source")
DEFAULT_SORT = "rank"

# How much each signal contributes to a result's score. Text quality
# outweighs the source prior on purpose: a truncated stub from a
# well-regarded site is still useless, and should lose to full lyrics from
# an average one.
_SOURCE_WEIGHT = 0.35
_TEXT_WEIGHT = 0.65

# Flat bonus for time-synced lyrics.
_SYNCED_BONUS = 0.05

# Length credit is a trapezoid over the character count: nothing below
# _MIN_LENGTH, full credit from _FULL_LENGTH to _MAX_LENGTH, nothing again at
# _ABSURD_LENGTH, ramping linearly at both ends.
#
# The low end catches an "instrumental" note or a couple of teaser lines; real
# lyrics run well past _FULL_LENGTH, so a result that lands short when other
# sources return much more is usually truncated rather than a genuinely short
# song.
#
# The high end catches a source that matched something that isn't a song at
# all, e.g.  annotated books.
_MIN_LENGTH = 80
_FULL_LENGTH = 600
_MAX_LENGTH = 10_000
_ABSURD_LENGTH = 30_000

# Phrases sites put on a page that has no lyrics yet, in place of the
# lyrics themselves — the request succeeds and the container is found, so
# only the text gives it away.
_JUNK_MARKERS = (
    "we do not have",
    "we don't have",
    "lyrics not available",
    "no lyrics available",
    "submit lyrics",
    "add these lyrics",
    "be the first to add",
)

# Signatures of UTF-8 bytes that were decoded as Latin-1/CP1252 (the
# classic "Ã©"/"â€™" mangling), plus the replacement character itself.
# Plugins carry per-site `encoding` overrides to avoid this, so a result
# showing it is one the override didn't cover.
_MOJIBAKE = re.compile(
    "\ufffd|\u00e2\u20ac|[\u00c3\u00c2][\u0080-\u00bf]"
)

_JUNK_PENALTY = 0.1
_MOJIBAKE_PENALTY = 0.5

# A blank line inside the (already stripped) text - verse break.
_VERSE_BREAK = re.compile(r"\n[^\S\n]*\n")

# How _text_quality() splits between "is there enough clean text" and "is it
# laid out in verses". Structure is worth much less than the text itself --
# it's a tie-breaker between sources that are otherwise comparable, not
# something that should outrank a fuller result. The two scale the length
# score rather than being added to it, so formatting earns nothing on a
# result that has no usable text to format.
_LENGTH_WEIGHT = 0.9
_VERSE_BREAK_BONUS = 0.1


def _plain_text(lyrics: str | SyncedLyrics) -> str:
    """The lyrics as plain text, dropping timestamps for a SyncedLyrics so
    both kinds can be scored by the same text heuristics."""
    if isinstance(lyrics, SyncedLyrics):
        return "\n".join(line.text for line in lyrics.lines)
    return lyrics


def _length_score(text: str) -> float:
    length = len(text)
    if length <= _MIN_LENGTH or length >= _ABSURD_LENGTH:
        return 0.0
    if length < _FULL_LENGTH:
        return (length - _MIN_LENGTH) / (_FULL_LENGTH - _MIN_LENGTH)
    if length <= _MAX_LENGTH:
        return 1.0
    return (_ABSURD_LENGTH - length) / (_ABSURD_LENGTH - _MAX_LENGTH)


def _text_quality(lyrics: str | SyncedLyrics) -> float:
    """Score the lyrics text itself, 0 (useless) to 1 (looks like full,
    clean lyrics), from the content alone.

    Catches the failure modes that otherwise reach the user looking like a
    real hit: teaser/truncated text, a "no lyrics yet" placeholder page,
    and text mangled by a wrong charset. Penalties multiply, so a short
    *and* mojibake'd result scores below either alone.

    Mostly a judgement on the amount of usable text, plus a small bonus for
    keeping the verse breaks, since length alone saturates for almost every
    real result and can't separate two otherwise-equal sources.
    """
    text = _plain_text(lyrics).strip()
    if not text:
        return 0.0

    # LRC has no blank lines -- it carries the song's structure in its
    # timestamps instead -- so synced lyrics aren't marked down for
    # lacking verse breaks. Without this every synced source loses the
    # bonus by construction, cancelling most of _SYNCED_BONUS.
    structured = isinstance(lyrics, SyncedLyrics) or bool(
        _VERSE_BREAK.search(text)
    )
    score = _length_score(text) * (
        _LENGTH_WEIGHT + _VERSE_BREAK_BONUS if structured else _LENGTH_WEIGHT
    )
    lowered = text.lower()
    if any(marker in lowered for marker in _JUNK_MARKERS):
        score *= _JUNK_PENALTY
    if _MOJIBAKE.search(text):
        score *= _MOJIBAKE_PENALTY
    return score


def _score_result(
    result: LyricsResult, quality: int = DEFAULT_QUALITY
) -> float:
    """Combine the source prior (`quality`, see LyricsPlugin.quality) with
    the result's own text quality and sync bonus into a single sortable
    score. Higher is better.

    Scores are deliberately never stored on the result or in the cache:
    they're recomputed at display time, so changing the weights here
    re-ranks everything already cached instead of needing the cache
    invalidated.
    """
    score = _SOURCE_WEIGHT * (quality / 100)
    score += _TEXT_WEIGHT * _text_quality(result.lyrics)
    if isinstance(result.lyrics, SyncedLyrics):
        score += _SYNCED_BONUS
    return score


def _quality_by_source() -> dict[str, int]:
    """Map each plugin's `name` to its `quality`, since results carry the
    source name rather than the plugin id (same reasoning as
    registry.filter_results())."""
    return {plugin.name: plugin.quality for plugin in default_plugins()}


def _rank_results(results: list[LyricsResult]) -> list[LyricsResult]:
    """Sort results best-first by _score_result(). Ties break on source
    name so the order stays stable across runs, matching the ordering
    guarantee search_lyrics() makes. A source with no registered plugin
    (e.g. a stale cache entry from a build that had one) scores neutral."""
    quality = _quality_by_source()
    return sorted(
        results,
        key=lambda r: (
            -_score_result(r, quality.get(r.source, DEFAULT_QUALITY)),
            r.source.lower(),
        ),
    )


def sort_results(
    results: list[LyricsResult], sort: str = DEFAULT_SORT
) -> list[LyricsResult]:
    """Order results for display by the given --sort mode: "rank" (best
    first, see _rank_results()) or "source" (alphabetical)."""
    if sort == "source":
        return sorted(results, key=lambda r: r.source.lower())
    return _rank_results(results)
