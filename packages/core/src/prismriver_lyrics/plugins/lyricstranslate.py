import urllib.parse

import httpx
from bs4 import BeautifulSoup, Tag

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.util import slugify

_BASE_URL = "https://lyricstranslate.com"

# Requires some non-browser UA
_USER_AGENT = "User-Agent"


class LyricsTranslatePlugin(LyricsPlugin):
    """Fetches lyrics from lyricstranslate.com.

    The site's Cloudflare bot-management rule blocks requests that claim
    to be a browser but don't behave fully like one: the shared client's
    browser-spoofing default User-Agent gets a 403, while a plain, non-
    browser one passes — the opposite of the usual "looks like a bot"
    block — so every request here explicitly overrides the header to a
    per-process random value (see `_USER_AGENT`) instead.

    1. An artist's page, `/en/{artist_slug}-lyrics.html` (artist_slug
       drops a leading "the", matching azlyrics.com's convention — e.g.
       "The Clash" -> `/en/clash-lyrics.html`), lists every song by that
       artist as `<a class="table-songs__title" href="...">{Title}</a>`,
       matched case-insensitively against the requested title.
    2. A song page carries one `div.translate__block` per lyrics variant
       present (the original, plus any community translations); the one
       whose `h2.translate__title` equals the song's own title is the
       original, which is what gets returned (translations aren't
       fetched).

    A block's lines aren't `<br>`-separated flat text like most sites
    here — each line is its own `div` (`div.par > div` per line, one
    `div.par` per verse), with blank lines between verses as sibling
    `div.emptyline` elements — so this walks that structure directly
    instead of using the shared `extract_lyrics()`.
    """

    id = "lyricstranslate"
    name = "LyricsTranslate"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        song_url = await self._find_song_url(client, artist, title)
        if song_url is None:
            return []

        soup = await self.fetch_soup(
            client, song_url, headers={"User-Agent": _USER_AGENT}
        )
        if soup is None:
            return []

        lyrics = self._extract_lyrics(soup, title)
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=song_url, lyrics=lyrics)]

    async def _find_song_url(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> str | None:
        artist = artist.strip()
        if artist.lower().startswith("the "):
            artist = artist[4:]
        artist_slug = slugify(artist)
        if not artist_slug:
            return None

        artist_url = f"{_BASE_URL}/en/{artist_slug}-lyrics.html"
        soup = await self.fetch_soup(
            client, artist_url, headers={"User-Agent": _USER_AGENT}
        )
        if soup is None:
            return None

        for link in soup.select("a.table-songs__title[href]"):
            if link.get_text(strip=True).lower() == title.lower():
                return urllib.parse.urljoin(artist_url, link["href"])

        return None

    @staticmethod
    def _extract_lyrics(soup: BeautifulSoup, title: str) -> str | None:
        for block in soup.select("div.translate__block"):
            heading = block.select_one("h2.translate__title")
            if heading is None:
                continue
            if heading.get_text(strip=True).lower() != title.lower():
                continue

            container = block.select_one("div.translate__text div.ltf")
            if container is None:
                return None
            return LyricsTranslatePlugin._render(container)

        return None

    @staticmethod
    def _render(container: Tag) -> str | None:
        lines: list[str] = []
        for div in container.find_all("div", recursive=False):
            classes = div.get("class") or []
            if "emptyline" in classes:
                lines.append("")
            elif "par" in classes:
                for line_div in div.find_all("div", recursive=False):
                    lines.append(line_div.get_text(strip=True))

        while lines and not lines[-1]:
            lines.pop()
        while lines and not lines[0]:
            lines.pop(0)

        return "\n".join(lines).strip() or None
