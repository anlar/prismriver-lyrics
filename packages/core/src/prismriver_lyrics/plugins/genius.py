import asyncio

import httpx
from bs4 import BeautifulSoup

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_SEARCH_URL = "https://genius.com/api/search/multi"
_SONG_URL = "https://api.genius.com/songs/{song_id}"
_TOKEN = "V_3MoK-nWNF2VKm_zG6qoH8mLnQsr4BU79c4sSNypbLXoXVQZXQI9Dl2Gg9tWed8"

_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:151.0) Gecko/20100101 Firefox/151.0"
)

# genius.com's own search-embed widget calls this unauthenticated endpoint;
# it needs to look like a same-site XHR (Referer/X-Requested-With) to avoid
# being blocked, unlike the official api.genius.com/search, which requires
# a bearer token we don't own.
_SEARCH_HEADERS = {
    "User-Agent": _USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://genius.com/search/embed",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

# Sent on the lyrics-page scrape too, since Genius's anti-bot checks aren't
# limited to the search XHR above.
_SCRAPE_HEADERS = {
    "User-Agent": _USER_AGENT,
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}


class GeniusPlugin(LyricsPlugin):
    """Fetches lyrics and community translations from genius.com.

    Genius has no lyrics API: even search only returns song metadata and a
    link to the song's page, so this plugin scrapes lyrics out of a song
    page's `data-lyrics-container` blocks. Search itself uses the same
    unauthenticated endpoint genius.com's own site-search widget calls,
    rather than the official api.genius.com/search, which requires a
    bearer token we don't own. The song-detail API (`/songs/:id`, which
    does require that token) additionally reports the song's own
    `language` and a `translation_songs` list — other Genius pages that
    are full translations of the song, each with its own language code —
    which are fetched the same way to produce the translated results.
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
            params={"per_page": 5, "q": f"{artist} {title}"},
            headers=_SEARCH_HEADERS,
        )
        if response.status_code != 200:
            return []

        sections = response.json().get("response", {}).get("sections", [])
        song = next(
            (
                hit["result"]
                for section in sections
                for hit in section.get("hits", [])
                if hit.get("type") == "song"
                and hit.get("result", {}).get("url")
            ),
            None,
        )
        if song is None or song.get("instrumental"):
            return []

        url = song["url"]
        lang, translation_songs = await self._song_details(
            client, song["id"]
        )

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
        response = await client.get(url, headers=_SCRAPE_HEADERS)
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
