import urllib.parse

import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_BASE_URL = "https://tekstovi.net"
_SEARCH_URL = f"{_BASE_URL}/search.php"

# How many search hits to check (by fetching each and comparing its own
# artist/title heading) before giving up.
_MAX_CANDIDATES = 5


class TekstoviNetPlugin(LyricsPlugin):
    """Fetches lyrics from tekstovi.net, a large ex-Yugoslav (Serbian,
    Croatian, Bosnian, Montenegrin) lyrics archive.

    A song's URL isn't derivable from its artist/title (paths are
    opaque numeric ids, e.g. `/2,435,25407.html`), so this searches via
    `GET /search.php?q={artist} {title}&ch_izv=1&ch_ime=1&ch_tek=1`
    first, collecting hit urls from `a.song-hit-card[href]`.

    Each hit's own title text (`.hit-title-row h4` on the search page)
    isn't reliable for matching: the site wraps the query's matched
    words in `<b>` for highlighting, but does so at the substring
    level, sometimes splitting a title's words apart at a matched
    fragment's boundaries (e.g. "Ne lomite mi bagrenje" rendered as
    "Ne lo mi te mi bagrenje" once "mi" gets highlighted inside
    "lomite" too) - not a stable text to compare against the query. So
    instead, each candidate's own song page is fetched in turn and
    matched against its own clean `#php-artist`/`#php-title` elements,
    up to `_MAX_CANDIDATES` hits; the first match's lyrics
    (`#php-lyrics`, plain text with literal newlines, no inner markup)
    are returned.
    """

    id = "tekstovinet"
    name = "Tekstovi.net"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        for url in await self._find_candidates(client, artist, title):
            soup = await self.fetch_soup(client, url)
            if soup is None:
                continue

            artist_el = soup.select_one("#php-artist")
            title_el = soup.select_one("#php-title")
            lyrics_el = soup.select_one("#php-lyrics")
            if artist_el is None or title_el is None or lyrics_el is None:
                continue

            if (
                artist_el.get_text(strip=True).lower()
                != artist.strip().lower()
                or title_el.get_text(strip=True).lower()
                != title.strip().lower()
            ):
                continue

            lyrics = self.extract_lyrics(lyrics_el)
            if not lyrics:
                continue

            return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]

        return []

    async def _find_candidates(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> list[str]:
        soup = await self.fetch_soup(
            client,
            _SEARCH_URL,
            params={
                "q": f"{artist} {title}",
                "ch_izv": "1",
                "ch_ime": "1",
                "ch_tek": "1",
            },
        )
        if soup is None:
            return []

        urls = []
        for link in soup.select("a.song-hit-card[href]"):
            href = link.get("href")
            if href:
                urls.append(urllib.parse.urljoin(_BASE_URL, str(href)))
        return urls[:_MAX_CANDIDATES]
