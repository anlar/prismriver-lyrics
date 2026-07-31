from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SyncedLine:
    """A single line of synchronized lyrics, timestamped to when it should
    be shown."""

    time_ms: int
    text: str


@dataclass(frozen=True, slots=True)
class SyncedLyrics:
    """Line-synchronized lyrics: a track's lines paired with the offset (in
    milliseconds from the start of the track) each one starts at, ordered
    by that offset."""

    lines: tuple[SyncedLine, ...]


@dataclass(frozen=True, slots=True)
class LyricsResult:
    """A successful lyrics match returned by a plugin.

    `lyrics` is plain text for most sources; a source that also has line
    timestamps (e.g. lrclib.net) instead returns a second LyricsResult
    whose `lyrics` is a SyncedLyrics.
    """

    source: str
    url: str
    lyrics: str | SyncedLyrics
    translation: bool = False
    lang: str | None = None
    original_lang: str | None = None
