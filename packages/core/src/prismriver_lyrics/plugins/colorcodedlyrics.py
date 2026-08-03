import html

import httpx
from bs4 import BeautifulSoup, Tag

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import ANY_LANG, LyricsPlugin

_API_URL = "https://colorcodedlyrics.com/wp-json/wp/v2/posts"

# A post title is "{Artist} {en dash} {Title}" (WordPress renders the
# separator as an HTML entity, "&#8211;", i.e. U+2013).
_TITLE_SEP = "–"

def _normalize(value: str) -> str:
    """Lowercase and fold typographic quote/apostrophe variants (post
    titles use curly "’", queries typically a plain "'") so title
    matching isn't tripped up by which one either side happens to use."""
    return value.strip().lower().replace("’", "'")


# Maps a lyrics column's own label (its leading <strong> text) to the
# language of its *original-script* content. Used both directly, and to
# infer the base language of a same-post "Romanization"/"Translation"
# column from a sibling "Hangul"/"Kanji"/"Hanzi" column (see
# `_detect_lang`) — colorcodedlyrics.com covers multiple Asian-pop
# scenes, not just K-pop, so this isn't hardcoded to Korean.
_SCRIPT_LANGS = {"hangul": "ko", "kanji": "ja", "hanzi": "zh"}


class ColorCodedLyricsPlugin(LyricsPlugin):
    """Fetches lyrics from colorcodedlyrics.com, which for many (mostly
    K-pop) songs carries the original-script lyrics, a romanization, and
    an English translation side by side, but for others (e.g. songs
    already in English) just the plain lyrics.

    Search uses the site's WordPress REST API
    (`/wp-json/wp/v2/posts?search=...`) rather than the HTML search page:
    a post's `content.rendered` field turns out to already carry the
    exact same lyrics markup as the live page, so no second page fetch
    is needed once a matching post is found. Matches are titled
    "{Artist} – {Title}", compared case-insensitively.

    The lyrics content itself is Gutenberg block markup: each language
    variant sits in its own `div.wp-block-group__inner-container` full
    of `<p>` paragraphs (`<br>`-separated lines within each), and for a
    multi-language post each of those containers is wrapped in a
    `div.wp-block-column` labeled by a leading `<strong>` ("Hangul",
    "Romanization", "Translation", ...). Gutenberg's group/columns
    nesting means some of these containers are wrappers around another,
    smaller one rather than lyrics themselves (see the module's real
    HTML for exact shapes), so `_find_lyric_leaves` keeps only the
    innermost text-bearing containers — the ones that don't themselves
    enclose another such container — which also transparently handles
    the single-language case, where there's no `wp-block-column` at all
    and thus no label (returned as an untagged, non-translated result).
    """

    id = "colorcodedlyrics"
    name = "ColorCodedLyrics"

    # Varies per song: some are untagged originals, some carry a script
    # code (ko/ja/zh) or its romanization, some an English translation.
    lang = [ANY_LANG]
    translated = 1

    # Each line's text is wrapped in <strong><span style="color:...">
    # (an artifact of whatever rich-text editor these posts are authored
    # in), purely for styling — recursed into transparently rather than
    # treated as a line break.
    _INLINE_TAGS = frozenset({"strong", "span"})

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        post = await self._find_post(client, artist, title)
        if post is None:
            return []

        content_html = (post.get("content") or {}).get("rendered") or ""
        if not content_html:
            return []

        url = post.get("link") or _API_URL
        soup = BeautifulSoup(content_html, "html.parser")

        results = []
        for leaf in self._find_lyric_leaves(soup):
            lyrics = self.extract_lyrics(leaf)
            if not lyrics:
                continue
            lang, translation, original_lang = self._detect_lang(leaf)
            results.append(
                LyricsResult(
                    source=self.name,
                    url=url,
                    lyrics=lyrics,
                    translation=translation,
                    lang=lang,
                    original_lang=original_lang,
                )
            )
        return results

    async def _find_post(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> dict | None:
        response = await client.get(
            _API_URL, params={"search": f"{artist} {title}", "per_page": "5"}
        )
        if response.status_code != 200:
            return None

        for post in response.json():
            raw_title = html.unescape(
                (post.get("title") or {}).get("rendered") or ""
            )
            found_artist, sep, found_title = raw_title.partition(
                f" {_TITLE_SEP} "
            )
            if not sep:
                continue
            if (
                _normalize(found_artist) == _normalize(artist)
                and _normalize(found_title) == _normalize(title)
            ):
                return post

        return None

    @staticmethod
    def _find_lyric_leaves(soup: BeautifulSoup) -> list[Tag]:
        containers = soup.select("div.wp-block-group__inner-container")
        candidates = [
            c
            for c in containers
            if c.find("p") is not None and len(c.get_text(strip=True)) > 20
        ]
        return [
            c
            for c in candidates
            if not any(
                other is not c and other in candidates
                for other in c.select("div.wp-block-group__inner-container")
            )
        ]

    @staticmethod
    def _detect_lang(
        container: Tag,
    ) -> tuple[str | None, bool, str | None]:
        column = container.find_parent("div", class_="wp-block-column")
        if column is None:
            return None, False, None

        strong = column.find("strong")
        label = strong.get_text(strip=True).lower() if strong else ""

        for key, code in _SCRIPT_LANGS.items():
            if key in label:
                return code, False, None

        if "romaniz" not in label and "translat" not in label:
            return None, False, None

        base_lang = None
        columns_block = column.find_parent("div", class_="wp-block-columns")
        if columns_block is not None:
            for sibling in columns_block.select(
                ":scope > div.wp-block-column"
            ):
                sib_strong = sibling.find("strong")
                sib_label = (
                    sib_strong.get_text(strip=True).lower()
                    if sib_strong
                    else ""
                )
                base_lang = next(
                    (
                        code
                        for key, code in _SCRIPT_LANGS.items()
                        if key in sib_label
                    ),
                    None,
                )
                if base_lang:
                    break

        if "romaniz" in label:
            return (f"{base_lang}-Latn" if base_lang else None), False, None
        return "en", True, base_lang
