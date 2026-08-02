import httpx
from bs4 import BeautifulSoup, NavigableString, Tag

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_SEARCH_URL = "https://utaten.com/search"
_BASE_URL = "https://utaten.com"


class UtaTenPlugin(LyricsPlugin):
    """Fetches lyrics from utaten.com.

    A song page renders its lyrics as two parallel ruby-annotated
    transcriptions inside `div.medium`: `div.hiragana` (kanji as
    `span.rb`, its kana reading as `span.rt`) and `div.romaji` (kanji
    again as `span.rb`, its romaji reading as `span.rt`). Combined, these
    give three usable texts: the raw kanji original, an all-kana reading,
    and a romaji reading, tagged via `lang` as "ja", "ja-Hira", and
    "ja-Latn" respectively. Some `<br>` line breaks end up in the parsed
    tree with sibling content nested as their children rather than
    following them (an artifact of the source markup), so extraction
    walks the whole subtree rather than just direct children.

    Songs without furigana (e.g. non-Japanese lyrics) have no `span.ruby`
    annotations at all, so `.rb`/`.rt` extraction from both divs
    degenerates to the same plain text; that case is detected up front
    and returns a single untagged (`lang=None`) result instead of three
    identical ones.
    """

    id = "utaten"
    name = "UtaTen"

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

        response = await client.get(song_url)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        hiragana = soup.select_one("div.lyricBody div.medium div.hiragana")
        romaji = soup.select_one("div.lyricBody div.medium div.romaji")
        if hiragana is None or romaji is None:
            return []

        original = self._extract(hiragana, "rb")
        if not original:
            return []

        has_furigana = bool(hiragana.select("span.ruby"))
        if not has_furigana:
            return [LyricsResult(source=self.name, url=song_url, lyrics=original)]

        results = [
            LyricsResult(source=self.name, url=song_url, lyrics=original, lang="ja")
        ]

        kana = self._extract(hiragana, "rt")
        if kana:
            results.append(
                LyricsResult(
                    source=self.name, url=song_url, lyrics=kana, lang="ja-Hira"
                )
            )

        romaji_text = self._extract(romaji, "rt")
        if romaji_text:
            results.append(
                LyricsResult(
                    source=self.name,
                    url=song_url,
                    lyrics=romaji_text,
                    lang="ja-Latn",
                )
            )

        return results

    async def _find_song_url(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> str | None:
        response = await client.get(
            _SEARCH_URL,
            params={
                "sort": "popular_sort_asc",
                "artist_name": artist,
                "title": title,
                "show_artists": 0,
            },
        )
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        for row in soup.select("table.searchResult tr"):
            title_link = row.select_one("p.searchResult__title a")
            artist_link = row.select_one(
                "td.searchResult__artist a[href^='/artist/']"
            )
            if title_link is None or artist_link is None:
                continue
            if (
                title_link.get_text(strip=True).lower() == title.lower()
                and artist_link.get_text(strip=True).lower() == artist.lower()
            ):
                href = title_link.get("href")
                if href:
                    return _BASE_URL + href
        return None

    @staticmethod
    def _extract(container: Tag, ruby_child_class: str) -> str:
        parts: list[str] = []

        def walk(node: object) -> None:
            if isinstance(node, NavigableString):
                text = str(node).strip()
                if text:
                    parts.append(text)
                return
            if not isinstance(node, Tag):
                return
            if node.name == "br":
                parts.append("\n")
                for child in node.children:
                    walk(child)
                return
            if node.name == "span" and "ruby" in (node.get("class") or []):
                target = node.find(
                    "span", class_=ruby_child_class, recursive=False
                )
                if target:
                    parts.append(target.get_text())
                return
            for child in node.children:
                walk(child)

        for child in container.contents:
            walk(child)

        lines = [line.strip() for line in "".join(parts).splitlines()]
        while lines and not lines[-1]:
            lines.pop()
        return "\n".join(lines).strip()
