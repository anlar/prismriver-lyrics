from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.plugins.elyrics import ElyricsPlugin
from prismriver_lyrics.plugins.letras import LetrasPlugin
from prismriver_lyrics.plugins.lyrics_ovh import LyricsOvhPlugin


def default_plugins() -> list[LyricsPlugin]:
    """Plugins queried by default, one instance per lyrics source."""
    return [ElyricsPlugin(), LetrasPlugin(), LyricsOvhPlugin()]
