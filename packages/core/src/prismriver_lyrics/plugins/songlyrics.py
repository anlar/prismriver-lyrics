import httpx
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_BASE_URL = "https://www.songlyrics.com"
_SUGGEST_URL = f"{_BASE_URL}/_suggest"


class SongLyricsPlugin(LyricsPlugin):
    """Fetches lyrics from songlyrics.com.

    Cloudflare TLS-fingerprints requests (403 on httpx, 200 via curl_cffi
    impersonate="chrome").

    /_suggest?q={artist} {title} is the site's own autocomplete endpoint,
    returning JSON with a "songs" list of {s: title, a: artist, u: url}
    matches; the first entry with an exact (case-insensitive) title/artist
    match gives the song's page url. Lyrics sit in `#songLyricsDiv`, one
    `<p class="lyrics-verse">` per verse with `<br>`-separated lines.
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
        async with AsyncSession() as session:
            response = await session.get(
                _SUGGEST_URL,
                params={"q": f"{artist} {title}"},
                impersonate="chrome",
            )
            if response.status_code != 200:
                return []

            path = self._find_song_path(response.json(), artist, title)
            if path is None:
                return []
            url = f"{_BASE_URL}{path}"

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

    @staticmethod
    def _find_song_path(
        data: dict, artist: str, title: str
    ) -> str | None:
        for song in data.get("songs", []):
            if (
                song.get("s", "").strip().lower() == title.lower()
                and song.get("a", "").strip().lower() == artist.lower()
            ):
                return song.get("u")
        return None
