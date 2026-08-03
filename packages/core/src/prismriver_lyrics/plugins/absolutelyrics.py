from prismriver_lyrics.plugins.base import SimpleLyricsPlugin
from prismriver_lyrics.util import slugify


class AbsoluteLyricsPlugin(SimpleLyricsPlugin):
    """Fetches lyrics from absolutelyrics.com.

    URL shape: http://www.absolutelyrics.com/lyrics/view/{artist}/{title},
    where artist/title are snake_cased (lowercased, non-alphanumeric runs
    collapsed to a single underscore).
    """

    id = "absolutelyrics"
    name = "AbsoluteLyrics"

    SELECTOR = "p#view_lyrics"

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = slugify(artist, sep="_")
        title_slug = slugify(title, sep="_")
        return f"http://www.absolutelyrics.com/lyrics/view/{artist_slug}/{title_slug}"
