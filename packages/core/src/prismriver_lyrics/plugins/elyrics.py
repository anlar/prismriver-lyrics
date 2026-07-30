import httpx
from bs4 import BeautifulSoup

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.slug import slugify


class ElyricsPlugin(LyricsPlugin):
    """Fetches lyrics from elyrics.net.

    URL shape: https://www.elyrics.net/read/{letter}/{artist}-lyrics/{title}-lyrics.html
    """

    name = "elyrics.net"

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = slugify(artist)
        title_slug = slugify(title)
        letter = artist_slug[0] if artist_slug else "a"
        return (
            f"https://www.elyrics.net/read/{letter}/"
            f"{artist_slug}-lyrics/{title_slug}-lyrics.html"
        )

    async def search(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> LyricsResult | None:
        url = self.build_url(artist, title)
        response = await client.get(url)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        container = soup.select_one("div#lyr.ly div#inlyr.translate")
        if container is None:
            return None

        lyrics = self.extract_lyrics(container)
        if not lyrics:
            return None

        return LyricsResult(source=self.name, url=url, lyrics=lyrics)
