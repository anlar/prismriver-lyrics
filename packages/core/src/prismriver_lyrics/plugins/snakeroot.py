import re

import httpx
from bs4 import BeautifulSoup

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_NON_ALNUM = re.compile(r"[^a-zA-Z0-9]+")


class SnakerootPlugin(LyricsPlugin):
    """Fetches lyrics from lyrics.snakeroot.ru.

    URL shape: https://lyrics.snakeroot.ru/{Letter}/{Artist_Title_Cased}/
    {artist_lower}_{title_lower}.html, e.g.
    .../H/Hayashibara_Megumi/hayashibara_megumi_successful_mission.html.
    The lyrics live in a bare (no class) <p>, one of several direct
    children of #content; it's identified by being the one with <br> line
    breaks (the others are empty spacer paragraphs).
    """

    name = "lyrics.snakeroot.ru"

    def _words(self, value: str) -> list[str]:
        return [w for w in _NON_ALNUM.split(value.strip()) if w]

    def build_url(self, artist: str, title: str) -> str:
        artist_dir = "_".join(w.capitalize() for w in self._words(artist))
        letter = artist_dir[0] if artist_dir else "A"
        artist_slug = "_".join(w.lower() for w in self._words(artist))
        title_slug = "_".join(w.lower() for w in self._words(title))
        return (
            f"https://lyrics.snakeroot.ru/{letter}/{artist_dir}/"
            f"{artist_slug}_{title_slug}.html"
        )

    async def search(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> LyricsResult | None:
        url = self.build_url(artist, title)
        response = await client.get(url)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.select_one("#content")
        if content is None:
            return None

        container = None
        best_br_count = 0
        for p in content.find_all("p", recursive=False):
            br_count = len(p.find_all("br"))
            if br_count > best_br_count:
                best_br_count = br_count
                container = p
        if container is None:
            return None

        lyrics = self.extract_lyrics(container)
        if not lyrics:
            return None

        return LyricsResult(source=self.name, url=url, lyrics=lyrics)
