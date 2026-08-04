import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import UNKNOWN_LANG, LyricsPlugin

_SEARCH_URL = "https://www.tekstowo.pl/js/completeSongSearch"
_SONG_URL = "https://www.tekstowo.pl/piosenka,{song_id}.html"


class TekstowoPlugin(LyricsPlugin):
    """Fetches lyrics, and a Polish translation if the site has one, from
    tekstowo.pl.

    Search is a POST to an autocomplete endpoint that returns "Artist -
    Title" candidates keyed by a slug id (e.g. "metallica,enter-sandman");
    this picks the id whose artist/title match, then scrapes that song's
    page. The original lyrics live in `div.song-text .inner-text`; a
    community-submitted Polish translation, when present, lives
    alongside it on the same page in `div#translation .inner-text`.
    """

    id = "tekstowo"
    name = "Tekstowo"

    # Original results are untagged; translations are always into Polish.
    lang = [UNKNOWN_LANG, "pl"]
    translated = 1

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        song_id = await self._find_song_id(client, artist, title)
        if song_id is None:
            return []

        url = _SONG_URL.format(song_id=song_id)
        soup = await self.fetch_soup(client, url)
        if soup is None:
            return []

        results: list[LyricsResult] = []

        original_container = soup.select_one("div.song-text .inner-text")
        lyrics = (
            self.extract_lyrics(original_container)
            if original_container
            else None
        )
        if lyrics:
            results.append(
                LyricsResult(source=self.name, url=url, lyrics=lyrics)
            )

        translation_container = soup.select_one(
            "div#translation .inner-text"
        )
        translated_lyrics = (
            self.extract_lyrics(translation_container)
            if translation_container
            else None
        )
        if translated_lyrics:
            results.append(
                LyricsResult(
                    source=self.name,
                    url=url,
                    lyrics=translated_lyrics,
                    translation=True,
                    lang="pl",
                )
            )

        return results

    async def _find_song_id(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> str | None:
        response = await client.post(
            _SEARCH_URL, data={"search-query": f"{artist} {title}"}
        )
        if response.status_code != 200:
            return None

        for candidate in response.json():
            candidate_artist, _, candidate_title = candidate.get(
                "text", ""
            ).partition(" - ")
            if (
                candidate_artist.strip().lower() == artist.lower()
                and candidate_title.strip().lower() == title.lower()
            ):
                return candidate.get("id")
        return None
