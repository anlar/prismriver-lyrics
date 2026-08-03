import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.util import split_words


class SnakerootPlugin(LyricsPlugin):
    """Fetches lyrics from lyrics.snakeroot.ru.

    URL shape: https://lyrics.snakeroot.ru/{Letter}/{Artist_Title_Cased}/
    {artist_lower}_{title_lower}.html, e.g.
    .../H/Hayashibara_Megumi/hayashibara_megumi_successful_mission.html.
    The lyrics live in a bare (no class) <p>, one of several direct
    children of #content; it's identified by being the one with <br> line
    breaks (the others are empty spacer paragraphs).
    """

    id = "snakeroot"
    name = "Snakeroot"

    def build_url(self, artist: str, title: str) -> str:
        artist_dir = "_".join(w.capitalize() for w in split_words(artist))
        letter = artist_dir[0] if artist_dir else "A"
        artist_slug = "_".join(w.lower() for w in split_words(artist))
        title_slug = "_".join(w.lower() for w in split_words(title))
        return (
            f"https://lyrics.snakeroot.ru/{letter}/{artist_dir}/"
            f"{artist_slug}_{title_slug}.html"
        )

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        url = self.build_url(artist, title)
        soup = await self.fetch_soup(client, url)
        if soup is None:
            return []

        content = soup.select_one("#content")
        if content is None:
            return []

        container = None
        best_br_count = 0
        for p in content.find_all("p", recursive=False):
            br_count = len(p.find_all("br"))
            if br_count > best_br_count:
                best_br_count = br_count
                container = p
        if container is None:
            return []

        lyrics = self.extract_lyrics(container)
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]
