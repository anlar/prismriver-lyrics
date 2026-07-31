from abc import ABC, abstractmethod

import httpx
from bs4 import Comment
from bs4.element import Tag

from prismriver_lyrics.models import LyricsResult

# Some APIs (e.g. lrclib.net) ask clients to self-identify via User-Agent
# rather than pose as a browser, so plugins that talk to such APIs use this
# instead of the shared client's browser-spoofing default.
APP_USER_AGENT = "Prismriver Lyrics (https://github.com/anlar/prismriver-lyrics)"


class LyricsPlugin(ABC):
    """A single lyrics source. Implementations must be safe to run
    concurrently."""

    name: str

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
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> list[LyricsResult]:
        """Look up lyrics for artist/title, returning every result this
        source has (usually one, but e.g. a source with a translation may
        return more), or an empty list if nothing was found."""

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
