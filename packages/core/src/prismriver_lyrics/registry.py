from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.plugins.elyrics import ElyricsPlugin
from prismriver_lyrics.plugins.letras import LetrasPlugin
from prismriver_lyrics.plugins.lyrics_ovh import LyricsOvhPlugin
from prismriver_lyrics.plugins.lyricsmania import LyricsManiaPlugin
from prismriver_lyrics.plugins.paroles import ParolesPlugin


def default_plugins() -> list[LyricsPlugin]:
    """Plugins queried by default, one instance per lyrics source."""
    return [
        ElyricsPlugin(),
        LetrasPlugin(),
        LyricsManiaPlugin(),
        LyricsOvhPlugin(),
        ParolesPlugin(),
    ]
