import base64
import html
import re
import zlib

import httpx

from prismriver_lyrics.models import LyricsResult, SyncedLine, SyncedLyrics
from prismriver_lyrics.plugins.base import LyricsPlugin

_SEARCH_URL = "http://krcs.kugou.com/search"
_DOWNLOAD_URL = "https://lyrics.kugou.com/download"
_HOMEPAGE_URL = "https://kugou.com"

# XOR key applied to the KRC payload after stripping its 4-byte magic
# prefix and before zlib-decompressing it. Fixed and public: this is how
# every KRC client (including KuGou's own) decodes the format.
_KRC_KEY = bytes(
    [64, 71, 97, 119, 94, 50, 116, 71, 81, 54, 49, 45, 206, 210, 110, 105]
)

# A KRC line: "[<start_ms>,<duration_ms>]<word timings...>".
_LINE_RE = re.compile(r"^\[(\d+),(\d+)\](.*)$")
# A word within a line: "<offset_ms,duration_ms,0>word ".
_WORD_RE = re.compile(r"<(\d+),(\d+),\d+>([^<]*)")
# Brackets (incl. full-width) used for a fallback search retry with
# parenthetical annotations like "(Live)" or "(feat. X)" stripped out.
_BRACKETS_RE = re.compile(r"[(\[（【][^)\]）】]*[)\]）】]")


def _decode_krc(content: str) -> str:
    """Decode a base64 KRC payload into its underlying KRC text."""
    raw = base64.b64decode(content)
    encrypted = raw[4:]
    decrypted = bytes(
        byte ^ _KRC_KEY[i % len(_KRC_KEY)] for i, byte in enumerate(encrypted)
    )
    return zlib.decompress(decrypted).decode("utf-8")


def parse_krc(text: str) -> SyncedLyrics | None:
    """Parse KuGou's word-timed KRC format into line-level SyncedLyrics
    (only line start times are kept, since SyncedLyrics doesn't track
    per-word timing), or None if it carries no lyric lines.
    """
    lines: list[SyncedLine] = []

    for raw_line in text.splitlines():
        match = _LINE_RE.match(raw_line)
        if not match:
            continue

        start_ms = int(match.group(1))
        words = [
            html.unescape(word_text)
            for _offset, _duration, word_text in _WORD_RE.findall(
                match.group(3)
            )
        ]
        text_line = "".join(words).strip()
        if text_line:
            lines.append(SyncedLine(time_ms=start_ms, text=text_line))

    lines = _strip_credits(lines)
    return SyncedLyrics(lines=tuple(lines)) if lines else None


def _strip_credits(lines: list[SyncedLine]) -> list[SyncedLine]:
    """KuGou sometimes embeds writer/producer credits (e.g. "Written
    by：Lars Ulrich/...") as ordinary timed lines up front, rather than in
    the file's `[tag:...]` header. Drop everything up to and including the
    last such line found within the first 30, since it isn't lyrics.
    """
    limit = min(30, len(lines))
    for i in range(limit - 1, -1, -1):
        if ":" in lines[i].text or "：" in lines[i].text:
            return lines[i + 1 :]
    # No credit line found; drop a leading "Title - Artist" separator
    # line if present (KuGou sometimes embeds this as the first line,
    # without a colon, so the scan above won't catch it).
    if lines and "-" in lines[0].text:
        return lines[1:]
    return lines


def _best_candidate(
    candidates: list[dict], duration_ms: int | None
) -> dict | None:
    """Pick the best non-"ugc" candidate.

    KuGou's search often returns several same-titled candidates that are
    actually different versions (remixes, live cuts, ...) mislabeled with
    the plain song/artist name — its own `score` field doesn't reflect
    this, so with a known track duration the candidate whose reported
    duration is closest to it is preferred (score only breaks ties),
    matching the reference lrcmux implementation. Without a known
    duration, the first (highest-scored) candidate is used as-is.
    """
    non_ugc = [c for c in candidates if c.get("product_from") != "ugc"]
    if not non_ugc:
        return None
    if duration_ms is None:
        return non_ugc[0]

    def diff(candidate: dict) -> int:
        return abs(candidate.get("duration", 0) - duration_ms)

    best = non_ugc[0]
    for candidate in non_ugc[1:]:
        candidate_diff = diff(candidate)
        if candidate_diff < diff(best) or (
            candidate_diff == diff(best)
            and candidate.get("score", 0) > best.get("score", 0)
        ):
            best = candidate
    return best


class KuGouPlugin(LyricsPlugin):
    """Fetches word-level synced lyrics from KuGou's public, undocumented
    lyrics search/download API.

    Searches by "artist - title" (retrying with parenthetical annotations
    like "(Live)" stripped if that finds nothing), skips unverified
    user-upload ("ugc") candidates, and downloads the best-matching
    candidate's KRC file (see _best_candidate). Unlike the reference
    lrcmux implementation, this doesn't independently re-verify the
    candidate's artist/title against the query: no other plugin in this
    codebase second-guesses its source's own search ranking either, and
    (unlike duration) KuGou's search results don't expose anything more
    trustworthy to re-verify against than the query itself.

    Only produces a SyncedLyrics result (plus its plain-text flattening);
    KuGou's word-level timing is discarded down to one timestamp per line,
    since that's all SyncedLyrics represents.
    """

    name = "kugou.com"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        stripped_artist = _BRACKETS_RE.sub("", artist).strip()
        stripped_title = _BRACKETS_RE.sub("", title).strip()

        candidate = None
        for attempt_artist, attempt_title in (
            (artist, title),
            (stripped_artist, stripped_title),
        ):
            if not attempt_artist or not attempt_title:
                continue
            candidate = await self._find_candidate(
                client, attempt_artist, attempt_title, duration_ms
            )
            if candidate is not None:
                break

        if candidate is None:
            return []

        synced = await self._download(client, candidate)
        if synced is None:
            return []

        lyrics = "\n".join(line.text for line in synced.lines)
        return [
            LyricsResult(source=self.name, url=_HOMEPAGE_URL, lyrics=lyrics),
            LyricsResult(source=self.name, url=_HOMEPAGE_URL, lyrics=synced),
        ]

    async def _find_candidate(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None,
    ) -> dict | None:
        response = await client.get(
            _SEARCH_URL,
            params={
                "ver": "1",
                "man": "yes",
                "client": "mobi",
                "keyword": f"{artist} - {title}",
                "hash": "",
                "album_audio_id": "",
                "duration": str(duration_ms or 0),
            },
        )
        if response.status_code != 200:
            return None

        candidates = response.json().get("candidates") or []
        return _best_candidate(candidates, duration_ms)

    async def _download(
        self, client: httpx.AsyncClient, candidate: dict
    ) -> SyncedLyrics | None:
        response = await client.get(
            _DOWNLOAD_URL,
            params={
                "ver": "1",
                "client": "pc",
                "id": candidate["id"],
                "accesskey": candidate["accesskey"],
                "fmt": "krc",
                "charset": "utf8",
            },
        )
        if response.status_code != 200:
            return None

        data = response.json()
        content = data.get("content")
        if data.get("status") != 200 or not content:
            return None

        return parse_krc(_decode_krc(content))
