import httpx
from bs4 import BeautifulSoup

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.slug import slugify


class LetrasPlugin(LyricsPlugin):
    """Fetches lyrics from letras.mus.br.

    URL shape: https://www.letras.mus.br/{artist}/{title}/
    """

    name = "letras.mus.br"

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = slugify(artist)
        title_slug = slugify(title)
        return f"https://www.letras.mus.br/{artist_slug}/{title_slug}/"

    async def search(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> LyricsResult | None:
        url = self.build_url(artist, title)
        response = await client.get(url)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        container = soup.select_one("div.lyric-original")
        if container is None:
            return None

        lyrics = self.extract_lyrics(container)
        if not lyrics:
            return None

        return LyricsResult(source=self.name, url=url, lyrics=lyrics)
