import re

import httpx
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_SEARCH_URL = (
    "https://www.metal-archives.com/search/ajax-advanced/searching/songs/"
)
_LYRICS_URL = "https://www.metal-archives.com/release/ajax-view-lyrics/id/{}"

# Song id lives in the row's lyrics-toggle cell, e.g. `id="lyricsLink_5845662"`.
_SONG_ID_RE = re.compile(r"lyricsLink_(\d+)")

# Each song has a lot of releases, prefer full-length, as it will most probably
# have fullest transcription.
_PREFERRED_TYPE = "Full-length"


class MetalArchivesPlugin(LyricsPlugin):
    """Fetches lyrics from metal-archives.com (Encyclopaedia Metallum).

    Cloudflare TLS-fingerprints requests here (403 on every httpx call, with
    any headers) but not curl, so using separate curl_cffi session
    (impersonate="chrome") instead of the shared httpx client.

    A song's lyrics live per (band, release, title) row, not globally, and some
    releases has no lyrics, so try each release/ajax-view-lyrics/id/{song_id}
    match from songs/ajax-advanced (full-length first) until one is non-empty.
    A blank entry renders as `<em>(lyrics not available)</em>`, which
    extract_lyrics() reduces to "".
    """

    id = "metalarchives"
    name = "Metal Archives"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        async with AsyncSession() as session:
            response = await session.get(
                _SEARCH_URL,
                params={
                    "songTitle": title,
                    "exactSongMatch": "1",
                    "bandName": artist,
                    "exactBandMatch": "1",
                },
                impersonate="chrome",
            )
            if response.status_code != 200:
                return []

            candidates = [
                candidate
                for row in response.json().get("aaData", [])
                if (candidate := self._parse_row(row)) is not None
            ]
            candidates.sort(
                key=lambda candidate: candidate[2] != _PREFERRED_TYPE
            )

            for song_id, album_url, _release_type in candidates:
                lyrics = await self._fetch_lyrics(session, song_id)
                if lyrics:
                    return [
                        LyricsResult(
                            source=self.name, url=album_url, lyrics=lyrics
                        )
                    ]

        return []

    @staticmethod
    def _parse_row(row: list[str]) -> tuple[str, str, str] | None:
        song_id_match = _SONG_ID_RE.search(row[4])
        if song_id_match is None:
            return None

        album_link = BeautifulSoup(row[1], "html.parser").find("a")
        album_url = album_link.get("href") if album_link else None
        if not album_url:
            return None

        return song_id_match.group(1), str(album_url), row[2].strip()

    @classmethod
    async def _fetch_lyrics(
        cls, session: AsyncSession, song_id: str
    ) -> str | None:
        response = await session.get(
            _LYRICS_URL.format(song_id), impersonate="chrome"
        )
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.text, "html.parser")
        return cls.extract_lyrics(soup) or None
