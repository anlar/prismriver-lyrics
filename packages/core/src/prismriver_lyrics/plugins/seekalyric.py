from prismriver_lyrics.plugins.base import SimpleLyricsPlugin
from prismriver_lyrics.util import split_words


def _slug(value: str) -> str:
    return "_".join(w.capitalize() for w in split_words(value))


class SeekALyricPlugin(SimpleLyricsPlugin):
    """Fetches lyrics from seekalyric.com.

    URL shape: https://www.seekalyric.com/song/{Artist}/{Title}, where
    artist/title are split into words and each word is title-cased
    (capitalized, not lowercased), joined by underscores.
    """

    id = "seekalyric"
    name = "SeekALyric"

    SELECTOR = "#contentt"

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = _slug(artist)
        title_slug = _slug(title)
        return f"https://www.seekalyric.com/song/{artist_slug}/{title_slug}"
