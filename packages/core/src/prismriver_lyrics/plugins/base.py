import importlib.metadata
from abc import ABC, abstractmethod
from collections.abc import Iterable

import httpx
from bs4 import BeautifulSoup, Comment
from bs4.element import Tag

from prismriver_lyrics.models import LyricsResult

# Some APIs (e.g. lrclib.net) ask clients to self-identify via User-Agent
# rather than pose as a browser, so plugins that talk to such APIs use this
# instead of the shared client's browser-spoofing default.
APP_USER_AGENT = (
    f"Prismriver Lyrics v{importlib.metadata.version('prismriver-lyrics')} "
    "(https://github.com/anlar/prismriver-lyrics)"
)

# LyricsPlugin.lang / registry filter_* token standing in for
# LyricsResult.lang=None (language not tagged/unknown), since the real
# value isn't a valid lang code to type.
UNKNOWN_LANG = "?"

# Two uses: as a LyricsPlugin.lang hint, "results may carry any language
# code, varies per search" (e.g. musixmatch); as a registry filter_lang
# token, "any *tagged* language, whichever code it is" (i.e. not
# UNKNOWN_LANG). Either way it subsumes specific codes; only UNKNOWN_LANG
# is distinct from it.
ANY_LANG = "*"


class LyricsPlugin(ABC):
    """A single lyrics source. Implementations must be safe to run
    concurrently."""

    # Short lower-case identifier (e.g. "lrclib"), stable for scripting/CLI
    # use.
    id: str

    # Human-readable resource name (e.g. "LRCLIB"), shown in results lists.
    name: str

    # Filter hints: describe what this plugin's results *could* look
    # like, so callers (see registry.filter_plugins()) can skip querying
    # a plugin that provably can't satisfy an active lang/translated/sync
    # filter instead of making the request and discarding the result.
    # Advisory only, not authoritative — a search can still legitimately
    # return fewer variants than the hints allow, or nothing at all.

    # Language codes this plugin's results may carry, matched against
    # LyricsResult.lang (not the actual song's language, for plugins that
    # never tag it). UNKNOWN_LANG stands in for untagged (lang=None);
    # ANY_LANG means "varies, could be any code" (e.g. musixmatch, whose
    # original_lang depends on whichever song is found) and subsumes
    # UNKNOWN_LANG too.
    lang: list[str] = [UNKNOWN_LANG]

    # 0 if this plugin only ever returns original lyrics, 1 if it may
    # also return translated results (LyricsResult.translation=True) —
    # always alongside the original, never translated-only.
    translated: int = 0

    # 0 if this plugin only ever returns plain-text lyrics, 1 if it may
    # also return time-synced lyrics (a SyncedLyrics).
    sync: int = 0

    # <p> wraps a verse on some sources (e.g. letras.mus.br); it's real
    # content, so it's recursed into, and its close also marks a
    # paragraph/verse break (blank line).
    _PARAGRAPH_TAGS = frozenset({"p"})

    # Tags that wrap real lyric text purely for styling/linking (e.g. Genius
    # wraps individual lines in <a> tags for its referent/annotation
    # system). Recursed into like _PARAGRAPH_TAGS, but transparently: no
    # line boundary is inserted, since the tag isn't a real content break.
    _INLINE_TAGS: frozenset[str] = frozenset()

    @abstractmethod
    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        """Look up lyrics for artist/title, returning every result this
        source has (usually one, but e.g. a source with a translation may
        return more), or an empty list if nothing was found."""

    @staticmethod
    async def fetch_soup(
        client: httpx.AsyncClient,
        url: str,
        *,
        encoding: str | None = None,
        **request_kwargs: object,
    ) -> BeautifulSoup | None:
        """GET url and parse it, or None on a non-200 response.
        `request_kwargs` (e.g. `headers=`, `follow_redirects=`) are passed
        through to `client.get()`. `encoding`, if given, overrides the
        response's own (header-declared or guessed) charset before
        parsing — for sites that don't reliably declare one, or declare
        the wrong one."""
        response = await client.get(url, **request_kwargs)
        if response.status_code != 200:
            return None
        if encoding is not None:
            response.encoding = encoding
        return BeautifulSoup(response.text, "html.parser")

    @staticmethod
    async def fetch_json(
        client: httpx.AsyncClient, url: str, **request_kwargs: object
    ) -> dict | list | None:
        """GET url and parse its JSON body, or None on a non-200
        response. `request_kwargs` (e.g. `params=`, `headers=`) are
        passed through to `client.get()`."""
        response = await client.get(url, **request_kwargs)
        if response.status_code != 200:
            return None
        return response.json()

    @staticmethod
    def find_matching_href(
        rows: Iterable[Tag],
        title_selector: str,
        artist_selector: str,
        title: str,
        artist: str,
    ) -> str | None:
        """Scan `rows` (e.g. search-result rows) for the first one whose
        title_selector/artist_selector text matches title/artist
        case-insensitively, returning that row's title element's href, or
        None if no row matches."""
        for row in rows:
            title_el = row.select_one(title_selector)
            artist_el = row.select_one(artist_selector)
            if title_el is None or artist_el is None:
                continue
            if (
                title_el.get_text(strip=True).lower() == title.lower()
                and artist_el.get_text(strip=True).lower() == artist.lower()
            ):
                href = title_el.get("href")
                if href:
                    return str(href)
        return None

    @classmethod
    async def fetch_lyrics(
        cls,
        client: httpx.AsyncClient,
        url: str,
        selector: str,
        **request_kwargs: object,
    ) -> str | None:
        """fetch_soup() + select_one(selector) + extract_lyrics(), or None
        if any step comes up empty."""
        soup = await cls.fetch_soup(client, url, **request_kwargs)
        if soup is None:
            return None
        container = soup.select_one(selector)
        if container is None:
            return None
        return cls.extract_lyrics(container) or None

    @classmethod
    def extract_lyrics(cls, container: Tag) -> str:
        """Extract lyrics text from a container, keeping only text, <br> line
        breaks, and a handful of known content-wrapping tags (e.g. <p>).

        Any other element (ads, scripts, unrecognized wrapper divs, ...) is
        skipped entirely along with its contents, but still counts as a line
        boundary so it doesn't glue the text on either side of it together.
        A single <br> becomes a newline; consecutive <br> tags, and <p>
        boundaries, are preserved as blank lines rather than being collapsed
        away. A trailing copyright line (starting with "©"), often tacked on
        after the lyrics themselves, is dropped.
        """
        parts: list[str] = []
        for child in container.contents:
            cls._walk(child, parts)

        lines = [line.strip() for line in "".join(parts).splitlines()]

        while lines and not lines[-1]:
            lines.pop()
        if lines and lines[-1].startswith("©"):
            lines.pop()
            while lines and not lines[-1]:
                lines.pop()

        return "\n".join(lines).strip()

    @classmethod
    def _walk(cls, node: object, parts: list[str]) -> None:
        if isinstance(node, Comment):
            return

        if isinstance(node, Tag):
            if node.name == "br":
                parts.append("\n")
            elif node.name in cls._PARAGRAPH_TAGS:
                for child in node.contents:
                    cls._walk(child, parts)
                parts.append("\n\n")
            elif node.name in cls._INLINE_TAGS:
                for child in node.contents:
                    cls._walk(child, parts)
            else:
                # Unknown element (ad, script, wrapper div, ...): drop its
                # contents entirely but keep the line boundary.
                parts.append("\n")
            return

        text = str(node).strip()
        if text:
            parts.append(text)


class SimpleLyricsPlugin(LyricsPlugin):
    """Base for plugins whose lyrics live at one predictable URL, picked
    out by a single CSS selector. A subclass only needs to implement
    build_url() and set SELECTOR; this provides search() in terms of
    those two."""

    # CSS selector for the lyrics container, passed to fetch_lyrics().
    SELECTOR: str

    def build_url(self, artist: str, title: str) -> str:
        raise NotImplementedError

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        url = self.build_url(artist, title)
        lyrics = await self.fetch_lyrics(client, url, self.SELECTOR)
        if not lyrics:
            return []
        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]
