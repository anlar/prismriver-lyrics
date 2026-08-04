import httpx
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_BASE_URL = "https://www.uta-net.com"


class UtaNetPlugin(LyricsPlugin):
    """Fetches lyrics from uta-net.com (歌ネット), a major Japanese lyrics
    site.

    Cloudflare blocks curl_cffi's Chrome fingerprint here but not Firefox, so
    this uses impersonate="firefox" specifically.

    1. /search/?target=art&type=in&Keyword={artist} lists matching
       artists as rows in `table.songlist-table`, each row's `<a>`
       holding a `span.fw-bold` with the artist name; matched
       case-insensitively against `artist` to get the artist's page url.
    2. The artist page lists every song the same way, in
       `table.songlist-table` rows whose `<a>` holds a
       `span.songlist-title`; matched case-insensitively against `title`
       to get the song url.
    3. The song page's lyrics sit in `#kashi_area`, plain text with
       `<br>` line breaks.
    """

    id = "utanet"
    name = "Uta-Net"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        async with AsyncSession() as session:
            response = await session.get(
                f"{_BASE_URL}/search/",
                params={"target": "art", "type": "in", "Keyword": artist},
                impersonate="firefox",
            )
            if response.status_code != 200:
                return []
            soup = BeautifulSoup(response.text, "html.parser")
            artist_url = self._find_link(soup, "fw-bold", artist)
            if artist_url is None:
                return []

            response = await session.get(
                artist_url, impersonate="firefox"
            )
            if response.status_code != 200:
                return []
            soup = BeautifulSoup(response.text, "html.parser")
            song_url = self._find_link(soup, "songlist-title", title)
            if song_url is None:
                return []

            response = await session.get(song_url, impersonate="firefox")
            if response.status_code != 200:
                return []
            soup = BeautifulSoup(response.text, "html.parser")

        container = soup.select_one("#kashi_area")
        if container is None:
            return []

        lyrics = self.extract_lyrics(container)
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=song_url, lyrics=lyrics)]

    @staticmethod
    def _find_link(
        soup: BeautifulSoup, span_class: str, value: str
    ) -> str | None:
        for link in soup.select("table.songlist-table a"):
            name = link.select_one(f"span.{span_class}")
            if (
                name is not None
                and name.get_text(strip=True).lower() == value.lower()
            ):
                return f"{_BASE_URL}{link.get('href')}"
        return None
