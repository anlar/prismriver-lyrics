import httpx
from bs4.element import Tag

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import UNKNOWN_LANG, LyricsPlugin

_SEARCH_URL = "https://www.songtexte.com/search"
_BASE_URL = "https://www.songtexte.com/"


class SongtextePlugin(LyricsPlugin):
    """Fetches lyrics, and a German translation if the site has one, from
    songtexte.com.

    Search: https://www.songtexte.com/search?q={artist} {title}&c=songs.
    Each result row is a `div.songResultTable > div > div` holding the
    title link (`span.song a`), artist link (`span.artist a span`), and,
    if a translation exists, a translation link
    (`span.translations a[href^='uebersetzung/']`) side by side; song and
    translation URLs both carry an opaque hash suffix, so they can't be
    built directly and have to be resolved via search. Both page types
    share the same lyrics container, `div#lyrics`.
    """

    id = "songtexte"
    name = "Songtexte"

    # Original results are untagged; translations are always into German.
    lang = [UNKNOWN_LANG, "de"]
    translated = 1

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        row = await self._find_song_row(client, artist, title)
        if row is None:
            return []

        song_link = row.select_one("span.song a")
        song_href = song_link.get("href") if song_link else None
        if not song_href:
            return []

        results: list[LyricsResult] = []

        song_url = _BASE_URL + str(song_href)
        lyrics = await self.fetch_lyrics(client, song_url, "div#lyrics")
        if lyrics:
            results.append(
                LyricsResult(source=self.name, url=song_url, lyrics=lyrics)
            )

        translation_link = row.select_one(
            "span.translations a[href^='uebersetzung/']"
        )
        translation_href = (
            translation_link.get("href") if translation_link else None
        )
        if translation_href:
            translation_url = _BASE_URL + str(translation_href)
            translated_lyrics = await self.fetch_lyrics(
                client, translation_url, "div#lyrics"
            )
            if translated_lyrics:
                results.append(
                    LyricsResult(
                        source=self.name,
                        url=translation_url,
                        lyrics=translated_lyrics,
                        translation=True,
                        lang="de",
                    )
                )

        return results

    async def _find_song_row(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> Tag | None:
        soup = await self.fetch_soup(
            client,
            _SEARCH_URL,
            params={"q": f"{artist} {title}", "c": "songs"},
        )
        if soup is None:
            return None

        for row in soup.select("div.songResultTable > div > div"):
            title_el = row.select_one("span.song a")
            artist_el = row.select_one("span.artist a span")
            if title_el is None or artist_el is None:
                continue
            if (
                title_el.get_text(strip=True).lower() == title.lower()
                and artist_el.get_text(strip=True).lower() == artist.lower()
            ):
                return row

        return None
