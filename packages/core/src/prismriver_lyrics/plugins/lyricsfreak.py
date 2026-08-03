import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_SEARCH_URL = "https://www.lyricsfreak.com/search.php"
_BASE_URL = "https://www.lyricsfreak.com"


class LyricsFreakPlugin(LyricsPlugin):
    """Fetches lyrics from lyricsfreak.com.

    Song URLs embed a numeric id the site assigns internally (e.g.
    /s/system+of+a+down/shame_20465737.html), so this searches by title
    first and picks the result whose artist matches, then scrapes that
    song's page.
    """

    id = "lyricsfreak"
    name = "LyricsFreak"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        url = await self._find_song_url(client, artist, title)
        if url is None:
            return []

        lyrics = await self.fetch_lyrics(client, url, "div#content.lyrictxt")
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]

    async def _find_song_url(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> str | None:
        soup = await self.fetch_soup(
            client,
            _SEARCH_URL,
            params={"a": "search", "type": "song", "q": f"{artist} {title}"},
        )
        if soup is None:
            return None

        for row in soup.select(
            "div.colortable.green .lf-list__row.js-sort-table-content-item"
        ):
            row_artist = row.get("data-sorting-artist", "")
            row_title = row.get("data-sorting-song", "")
            if (
                row_artist.lower() == artist.lower()
                and row_title.lower() == title.lower()
            ):
                link = row.select_one("a.song")
                href = link.get("href") if link else None
                if href:
                    return _BASE_URL + href
        return None
