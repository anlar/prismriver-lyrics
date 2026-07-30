from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LyricsResult:
    """A successful lyrics match returned by a plugin."""

    source: str
    url: str
    lyrics: str
