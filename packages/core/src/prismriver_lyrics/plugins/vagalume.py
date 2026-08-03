from prismriver_lyrics.plugins.base import SimpleLyricsPlugin
from prismriver_lyrics.util import slugify


class VagalumePlugin(SimpleLyricsPlugin):
    """Fetches lyrics from vagalume.com.br.

    URL shape: https://www.vagalume.com.br/{artist}/{title}.html
    """

    id = "vagalume"
    name = "Vagalume"

    SELECTOR = "#lyrics"

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = slugify(artist)
        title_slug = slugify(title)
        return f"https://www.vagalume.com.br/{artist_slug}/{title_slug}.html"
