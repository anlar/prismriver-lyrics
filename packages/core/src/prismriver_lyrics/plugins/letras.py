from prismriver_lyrics.plugins.base import SimpleLyricsPlugin
from prismriver_lyrics.util import slugify


class LetrasPlugin(SimpleLyricsPlugin):
    """Fetches lyrics from letras.mus.br.

    URL shape: https://www.letras.mus.br/{artist}/{title}/
    """

    id = "letras"
    name = "Letras"

    SELECTOR = "div.lyric-original"

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = slugify(artist)
        title_slug = slugify(title)
        return f"https://www.letras.mus.br/{artist_slug}/{title_slug}/"
