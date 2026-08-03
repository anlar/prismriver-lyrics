from prismriver_lyrics.plugins.base import SimpleLyricsPlugin
from prismriver_lyrics.util import slugify


class ElyricsPlugin(SimpleLyricsPlugin):
    """Fetches lyrics from elyrics.net.

    URL shape: https://www.elyrics.net/read/{letter}/{artist}-lyrics/{title}-lyrics.html
    """

    id = "elyrics"
    name = "eLyrics"

    SELECTOR = "div#lyr.ly div#inlyr.translate"

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = slugify(artist)
        title_slug = slugify(title)
        letter = artist_slug[0] if artist_slug else "a"
        return (
            f"https://www.elyrics.net/read/{letter}/"
            f"{artist_slug}-lyrics/{title_slug}-lyrics.html"
        )
