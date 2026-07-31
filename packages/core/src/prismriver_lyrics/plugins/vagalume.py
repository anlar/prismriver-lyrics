import httpx
from bs4 import BeautifulSoup

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.slug import slugify


class VagalumePlugin(LyricsPlugin):
    """Fetches lyrics from vagalume.com.br.

    URL shape: https://www.vagalume.com.br/{artist}/{title}.html
    """

    name = "vagalume.com.br"

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = slugify(artist)
        title_slug = slugify(title)
        return f"https://www.vagalume.com.br/{artist_slug}/{title_slug}.html"

    async def search(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> list[LyricsResult]:
        url = self.build_url(artist, title)
        response = await client.get(url)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        container = soup.select_one("#lyrics")
        if container is None:
            return []

        lyrics = self.extract_lyrics(container)
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]
