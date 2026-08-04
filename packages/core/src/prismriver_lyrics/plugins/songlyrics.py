import httpx
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.util import slugify

_BASE_URL = "https://www.songlyrics.com"


class SongLyricsPlugin(LyricsPlugin):
    """Fetches lyrics from songlyrics.com.

    Cloudflare TLS-fingerprints requests (403 on httpx, 200 via curl_cffi
    impersonate="chrome").

    No search: URLs are predictable, /{artist-slug}/{title-slug}-lyrics/, both
    dash-slugified (e.g. "Sad but True" -> sad-but-true-lyrics). Lyrics sit in
    `#songLyricsDiv`, one `<p class="lyrics-verse">` per verse with
    `<br>`-separated lines.
    """

    id = "songlyrics"
    name = "SongLyrics"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        url = f"{_BASE_URL}/{slugify(artist)}/{slugify(title)}-lyrics/"

        async with AsyncSession() as session:
            response = await session.get(url, impersonate="chrome")
            if response.status_code != 200:
                return []
            soup = BeautifulSoup(response.text, "html.parser")

        container = soup.select_one("#songLyricsDiv")
        if container is None:
            return []

        lyrics = self.extract_lyrics(container)
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]
