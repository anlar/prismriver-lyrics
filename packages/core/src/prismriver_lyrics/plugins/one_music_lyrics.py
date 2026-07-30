import re

import httpx
from bs4 import BeautifulSoup

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


class OneMusicLyricsPlugin(LyricsPlugin):
    """Fetches lyrics from 1musiclyrics.net.

    URL shape: https://www.1musiclyrics.net/m/{artist}/{title}.html, where
    artist/title are snake_cased (lowercased, non-alphanumeric runs
    collapsed to a single underscore).
    """

    name = "1musiclyrics.net"

    def _slug(self, value: str) -> str:
        return _NON_ALNUM.sub("_", value.lower()).strip("_")

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = self._slug(artist)
        title_slug = self._slug(title)
        return f"https://www.1musiclyrics.net/m/{artist_slug}/{title_slug}.html"

    async def search(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> LyricsResult | None:
        url = self.build_url(artist, title)
        response = await client.get(url)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        container = self._find_lyrics_container(soup)
        if container is None:
            return None

        lyrics = self.extract_lyrics(container)
        if not lyrics:
            return None

        return LyricsResult(source=self.name, url=url, lyrics=lyrics)

    @staticmethod
    def _find_lyrics_container(soup: BeautifulSoup):
        # The lyrics <p> carries no class/id (unlike the surrounding
        # disclaimer/notice paragraphs), but there's more than one bare
        # <p> in the box. Some songs also have "related songs" widgets in
        # the same shape (bare <p>, many <br> line breaks between
        # "<a>Song</a> by <a>Artist</a>" entries), so a plain <br>-count
        # heuristic alone can pick a navigation list instead of the real
        # lyrics. Reject candidates whose text is mostly hyperlinks.
        container = None
        best_br_count = 0
        for p in soup.select("#welcomeBox p"):
            if p.get("class") or p.get("id"):
                continue
            br_count = len(p.find_all("br"))
            if br_count <= best_br_count:
                continue
            text = p.get_text(strip=True)
            if not text:
                continue
            link_text_len = sum(
                len(a.get_text(strip=True)) for a in p.find_all("a")
            )
            if link_text_len / len(text) > 0.3:
                continue
            best_br_count = br_count
            container = p
        return container
