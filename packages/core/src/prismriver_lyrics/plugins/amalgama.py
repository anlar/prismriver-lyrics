import re

import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_NON_ALNUM = re.compile(r"[^a-z0-9]+")

# A single blank `div.empty_container` is a normal stanza break within one
# translation. When a song has been translated by more than one contributor,
# amalgama-lab.com separates each contributor's complete pass at the song
# with a run of (at least) this many consecutive empty_container elements
# instead, so that's used as the section boundary.
_SECTION_BREAK_RUN = 3


def _slugify(value: str) -> str:
    """Lowercase and underscore a string for amalgama-lab.com's URL path
    (unlike most sources here, it uses underscores rather than hyphens)."""
    return _NON_ALNUM.sub("_", value.strip().lower()).strip("_")


class AmalgamaPlugin(LyricsPlugin):
    """Fetches lyrics and their Russian translation(s) from
    amalgama-lab.com.

    URL shape: https://www.amalgama-lab.com/songs/{first_letter}/{artist}/
    {title}.html. Each lyric line is laid out as a `div.string_container`
    holding a `div.original` and a matching `div.translate`, in document
    order. A song translated by more than one contributor repeats this
    original+translation structure once per contributor, each pass
    separated by a run of empty_container spacers (see
    _SECTION_BREAK_RUN); every such section is returned as its own
    translated result, alongside a single original-lyrics result taken
    from the first section.
    """

    name = "amalgama-lab.com"

    # amalgama-lab.com bolds some words within a line via <strong>; that's
    # real lyric text, not chrome, so it's recursed into transparently.
    _INLINE_TAGS = frozenset({"strong"})

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = _slugify(artist)
        title_slug = _slugify(title)
        first_letter = artist_slug[:1] or "0"
        return (
            f"https://www.amalgama-lab.com/songs/{first_letter}/"
            f"{artist_slug}/{title_slug}.html"
        )

    async def search(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> list[LyricsResult]:
        url = self.build_url(artist, title)
        response = await client.get(url)
        if response.status_code != 200:
            return []

        # The site doesn't reliably declare its charset in the HTTP
        # header (only in a <meta> tag), so httpx's own guess can default
        # to UTF-8 and mangle the Cyrillic translation; force it instead.
        response.encoding = "windows-1251"

        soup = BeautifulSoup(response.text, "html.parser")
        click_area = soup.select_one("#click_area")
        if click_area is None:
            return []

        sections = self._split_sections(click_area)
        if not sections:
            return []

        results: list[LyricsResult] = []

        original_lyrics = self._extract_column(sections[0], "original")
        if original_lyrics:
            results.append(
                LyricsResult(source=self.name, url=url, lyrics=original_lyrics)
            )

        for section in sections:
            translated_lyrics = self._extract_column(section, "translate")
            if translated_lyrics:
                results.append(
                    LyricsResult(
                        source=self.name,
                        url=url,
                        lyrics=translated_lyrics,
                        translation=True,
                    )
                )

        return results

    @staticmethod
    def _split_sections(click_area: Tag) -> list[list[Tag]]:
        """Split click_area's `string_container`/`empty_container`
        children into per-contributor sections, dropping the boundary
        runs themselves but keeping normal (shorter) spacer runs as blank
        lines within a section."""
        section_classes = (["string_container"], ["empty_container"])
        children = [
            child
            for child in click_area.children
            if isinstance(child, Tag) and child.get("class") in section_classes
        ]

        sections: list[list[Tag]] = []
        current: list[Tag] = []
        i = 0
        while i < len(children):
            if children[i].get("class") == ["empty_container"]:
                j = i
                while (
                    j < len(children)
                    and children[j].get("class") == ["empty_container"]
                ):
                    j += 1
                if j - i >= _SECTION_BREAK_RUN:
                    sections.append(current)
                    current = []
                else:
                    current.extend(children[i:j])
                i = j
            else:
                current.append(children[i])
                i += 1
        sections.append(current)

        return [
            section
            for section in sections
            if any(
                child.get("class") == ["string_container"] for child in section
            )
        ]

    def _extract_column(self, section: list[Tag], css_class: str) -> str:
        lines = []
        for child in section:
            if child.get("class") != ["string_container"]:
                lines.append("")
                continue
            line_div = child.select_one(f".{css_class}")
            lines.append(self.extract_lyrics(line_div) if line_div else "")
        return "\n".join(lines).strip()
