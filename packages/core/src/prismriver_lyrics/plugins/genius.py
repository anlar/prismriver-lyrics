import asyncio

import httpx
from bs4 import BeautifulSoup

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_SEARCH_URL = "https://api.genius.com/search"
_SONG_URL = "https://api.genius.com/songs/{song_id}"
_TOKEN = "V_3MoK-nWNF2VKm_zG6qoH8mLnQsr4BU79c4sSNypbLXoXVQZXQI9Dl2Gg9tWed8"


class GeniusPlugin(LyricsPlugin):
    """Fetches lyrics and community translations from genius.com.

    Genius's Search API only returns song metadata and a link to the
    song's page, not lyrics text itself, so this plugin scrapes lyrics out
    of a song page's `data-lyrics-container` blocks. The song-detail API
    (`/songs/:id`) additionally reports the song's own `language` and a
    `translation_songs` list — other Genius pages that are full
    translations of the song, each with its own language code — which are
    fetched the same way to produce the translated results.
    """

    name = "genius.com"

    # Genius wraps most lyric lines in <a> (referent/annotation) tags and
    # some styled spans in <span>; both wrap real lyric text, not chrome.
    _INLINE_TAGS = frozenset({"a", "span"})

    async def search(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> list[LyricsResult]:
        response = await client.get(
            _SEARCH_URL,
            params={"q": f"{artist} {title}"},
            headers={"Authorization": f"Bearer {_TOKEN}"},
        )
        if response.status_code != 200:
            return []

        hits = response.json().get("response", {}).get("hits", [])
        song = next(
            (
                hit["result"]
                for hit in hits
                if hit.get("type") == "song"
                and hit.get("result", {}).get("url")
            ),
            None,
        )
        if song is None:
            return []

        url = song["url"]
        lang, translation_songs = await self._song_details(client, song["id"])

        results: list[LyricsResult] = []

        lyrics = await self._scrape_lyrics(client, url)
        if lyrics:
            results.append(
                LyricsResult(
                    source=self.name, url=url, lyrics=lyrics, lang=lang
                )
            )

        translations = await asyncio.gather(
            *(
                self._scrape_lyrics(client, entry["url"])
                for entry in translation_songs
                if entry.get("url")
            )
        )
        for entry, translated_lyrics in zip(
            translation_songs, translations, strict=False
        ):
            if translated_lyrics:
                results.append(
                    LyricsResult(
                        source=self.name,
                        url=entry["url"],
                        lyrics=translated_lyrics,
                        translation=True,
                        lang=entry.get("language"),
                        original_lang=lang,
                    )
                )

        return results

    async def _song_details(
        self, client: httpx.AsyncClient, song_id: int
    ) -> tuple[str | None, list[dict]]:
        response = await client.get(
            _SONG_URL.format(song_id=song_id),
            headers={"Authorization": f"Bearer {_TOKEN}"},
        )
        if response.status_code != 200:
            return None, []

        song = response.json().get("response", {}).get("song", {})
        return song.get("language"), song.get("translation_songs") or []

    async def _scrape_lyrics(
        self, client: httpx.AsyncClient, url: str
    ) -> str | None:
        response = await client.get(url)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        containers = soup.select("div[data-lyrics-container='true']")
        if not containers:
            return None

        lyrics = "\n\n".join(
            self.extract_lyrics(container) for container in containers
        ).strip()
        return lyrics or None
