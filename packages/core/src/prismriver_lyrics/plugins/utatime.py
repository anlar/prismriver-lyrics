import httpx
from bs4 import BeautifulSoup, Tag
from curl_cffi.requests import AsyncSession

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.util import slugify

_BASE_URL = "https://www.utatime.com"


class UtaTimePlugin(LyricsPlugin):
    """Fetches lyrics from utatime.com (formerly lyrical-nonsense.com), a
    Japanese/anime lyrics site.

    Cloudflare TLS-fingerprints requests (403 on httpx, 200 via curl_cffi
    impersonate="chrome").

    The site's own search is a Google Custom Search widget, not something
    queryable directly, so this walks the site's listing pages instead:

    1. /lyrics/directory/{letter}/ lists every artist starting with that
       letter as `<a>` text inside `ul.sortablelistdir`, matched
       case-insensitively against `artist` to get the artist's page url.
    2. The artist page has one `<a>` per song inside `table.aptp_table`,
       matched case-insensitively against `title` to get the song url.
    3. The song page's original lyrics sit in `#PriLyr`, one `<span
       class="line-text">` per line (some blank, marking verse breaks),
       each preceded by a `<span class="line-number">` sibling that's
       skipped by selecting only `.line-text`.
    """

    id = "utatime"
    name = "UtaTime"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        letter = slugify(artist)[:1]
        if not letter:
            return []

        async with AsyncSession() as session:
            artist_url = await self._find_artist_url(session, letter, artist)
            if artist_url is None:
                return []

            song_url = await self._find_song_url(session, artist_url, title)
            if song_url is None:
                return []

            response = await session.get(song_url, impersonate="chrome")
            if response.status_code != 200:
                return []
            soup = BeautifulSoup(response.text, "html.parser")

        container = soup.select_one("#PriLyr")
        if container is None:
            return []

        lyrics = self._render(container)
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=song_url, lyrics=lyrics)]

    @staticmethod
    async def _find_artist_url(
        session: AsyncSession, letter: str, artist: str
    ) -> str | None:
        response = await session.get(
            f"{_BASE_URL}/lyrics/directory/{letter}/", impersonate="chrome"
        )
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.select("ul.sortablelistdir a"):
            if link.get_text(strip=True).lower() == artist.lower():
                return str(link.get("href"))
        return None

    @staticmethod
    async def _find_song_url(
        session: AsyncSession, artist_url: str, title: str
    ) -> str | None:
        response = await session.get(artist_url, impersonate="chrome")
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.select("table.aptp_table a"):
            if link.get_text(strip=True).lower() == title.lower():
                return str(link.get("href"))
        return None

    @staticmethod
    def _render(container: Tag) -> str:
        lines = [
            span.get_text(strip=True)
            for span in container.select("span.line-text")
        ]
        while lines and not lines[-1]:
            lines.pop()
        while lines and not lines[0]:
            lines.pop(0)
        return "\n".join(lines)
