import asyncio
import json

import httpx
from bs4 import BeautifulSoup

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.slug import slugify

_BASE_URL = "https://www.musixmatch.com"


class MusixmatchPlugin(LyricsPlugin):
    """Fetches lyrics and community translations from musixmatch.com.

    The site is a Next.js app: both lyrics and translations are embedded
    as JSON in a `<script id="__NEXT_DATA__">` blob rather than rendered
    into visible markup, so this parses that instead of scraping HTML.

    A song's base page (`/lyrics/{artist}/{title}`) carries the original
    lyrics text plus `translationStatuses` (the 3-letter language codes
    with a translation available) and a `languagesGet` list mapping those
    codes to the English language name used in translation page URLs
    (`/lyrics/{artist}/{title}/translation/{name}`). Each translation
    page's own `crowdTranslationGet` blob maps individual original-
    language lines to their translated text; crowd translations aren't
    guaranteed to cover every line, so lines missing from that map fall
    back to the original line rather than being dropped.
    """

    name = "musixmatch.com"

    def build_url(self, artist: str, title: str) -> str:
        return f"{_BASE_URL}/lyrics/{slugify(artist)}/{slugify(title)}"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        url = self.build_url(artist, title)
        data = await self._fetch_next_data(client, url)
        if data is None:
            return []

        page_props = data.get("props", {}).get("pageProps", {}).get("data", {})
        track = page_props.get("trackInfo", {}).get("data", {})
        lyrics_info = track.get("lyrics") or {}
        original = (lyrics_info.get("body") or "").strip()
        if not original:
            return []

        original_lang = lyrics_info.get("language") or None
        results = [
            LyricsResult(
                source=self.name,
                url=url,
                lyrics=original,
                lang=original_lang,
            )
        ]

        lang_by_code3 = {
            item["language_iso_code_3"]: item
            for item in page_props.get("languagesGet", {}).get("data", [])
            if "language_iso_code_3" in item
        }
        translation_statuses = track.get("translationStatuses") or {}

        translations = await asyncio.gather(
            *(
                self._fetch_translation(
                    client, url, original, original_lang, lang_by_code3[code]
                )
                for code in translation_statuses
                if code in lang_by_code3
            )
        )
        results.extend(t for t in translations if t is not None)
        return results

    async def _fetch_translation(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        original: str,
        original_lang: str | None,
        lang_info: dict,
    ) -> LyricsResult | None:
        translation_url = f"{base_url}/translation/{lang_info['language_name']}"
        data = await self._fetch_next_data(client, translation_url)
        if data is None:
            return None

        page_props = data.get("props", {}).get("pageProps", {}).get("data", {})
        translation_map = page_props.get("crowdTranslationGet", {}).get("data") or {}
        if not translation_map:
            return None

        lines = [translation_map.get(line, line) for line in original.splitlines()]
        text = "\n".join(lines).strip()
        if not text or text == original:
            return None

        return LyricsResult(
            source=self.name,
            url=translation_url,
            lyrics=text,
            translation=True,
            lang=lang_info.get("language_iso_code_1"),
            original_lang=original_lang,
        )

    @staticmethod
    async def _fetch_next_data(
        client: httpx.AsyncClient, url: str
    ) -> dict | None:
        response = await client.get(url)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        if script is None:
            return None

        try:
            return json.loads(script.get_text())
        except json.JSONDecodeError:
            return None
