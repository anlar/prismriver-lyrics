import re

# Default for every "how long should cached results stay valid" knob (CLI
# args, TUI args, the module-level default cache), so they can't drift out
# of sync with each other.
DEFAULT_CACHE_TTL = "1w"

_UNITS = {"w": 604800, "d": 86400, "h": 3600, "m": 60, "s": 1}
_CHUNK = re.compile(r"(\d+)([wdhms])")


def parse_duration(value: str) -> int:
    """Parse a compound duration string (e.g. "1w", "1d5h", "90m") into
    seconds. Chunks are <number><unit> pairs, concatenated with no
    separator; supported units are w(eek)/d(ay)/h(our)/m(inute)/s(econd).
    Raises ValueError if `value` isn't entirely made up of such chunks.
    """
    if not value or _CHUNK.sub("", value) != "":
        raise ValueError(f"invalid duration: {value!r}")
    return sum(int(n) * _UNITS[unit] for n, unit in _CHUNK.findall(value))


_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(value: str, sep: str = "-") -> str:
    """Lowercase and join a string's words with `sep` for use in a
    lyrics-site URL path."""
    value = _NON_ALNUM.sub(sep, value.strip().lower())
    return value.strip(sep)


_NON_ALNUM_CI = re.compile(r"[^a-zA-Z0-9]+")


def split_words(value: str) -> list[str]:
    """Split a string into its alphanumeric words, discarding separators
    and empty chunks, preserving case (unlike slugify)."""
    return [w for w in _NON_ALNUM_CI.split(value.strip()) if w]


_TITLE_POSTFIXES = (
    "official music video",
    "official hd music video",
)

_TITLE_POSTFIX_RE = re.compile(
    r"\s*(?:\((?:"
    + "|".join(_TITLE_POSTFIXES)
    + r")\)|\[(?:"
    + "|".join(_TITLE_POSTFIXES)
    + r")\])\s*$",
    re.IGNORECASE,
)


def _strip_title_postfix(title: str) -> str:
    """Remove a trailing (round- or square-bracketed) postfix (e.g. "(Official
    Music Video)" or "[Official Music Video]") that some sources append to a
    track title. Matching is case-insensitive."""
    return _TITLE_POSTFIX_RE.sub("", title).strip()


# Words marking a bracketed block as describing a particular *release* of a
# song (a live take, a remix, a session recording, a bonus track) rather
# than naming a different song. The lyrics are the base song's either way,
# so the block only stops sources from matching.
_TITLE_VARIANT_WORDS = (
    "live",
    "remix",
    "session",
    "reboot",
    "bonus",
)

# Whole words only, so e.g. "Deliverance" isn't read as "live".
_TITLE_VARIANT_WORD_RE = re.compile(
    r"\b(?:" + "|".join(_TITLE_VARIANT_WORDS) + r")\b",
    re.IGNORECASE,
)

# A round- or square-bracketed block, with any whitespace running up to it.
_BRACKET_BLOCK_RE = re.compile(r"\s*(?:\([^)]*\)|\[[^\]]*\])")


def _strip_title_variants(title: str) -> str:
    """Remove bracketed blocks naming an alternate take of a song rather
    than a different song (e.g. "Creep (Live at Glastonbury)" -> "Creep"),
    since the lyrics are the base song's. Every such block is dropped, not
    just a trailing one. Matching is case-insensitive and on whole words.
    Left alone if the title is nothing but these blocks, since an empty
    title searches worse than a noisy one."""
    stripped = _BRACKET_BLOCK_RE.sub(
        lambda m: "" if _TITLE_VARIANT_WORD_RE.search(m.group()) else m.group(),
        title.strip(),
    ).strip()
    return stripped or title.strip()


# YouTube's official-artist channels are named "<artist>VEVO", so a track
# played from one reports e.g. "RadioheadVEVO" as its artist. Matched
# case-sensitively: "Vevo" is a plausible tail for a real name in a way the
# shouted form isn't.
_ARTIST_POSTFIX_RE = re.compile(r"\s*VEVO$")


def _strip_artist_postfix(artist: str) -> str:
    """Remove the trailing "VEVO" that YouTube artist-channel names carry
    (e.g. "RadioheadVEVO" -> "Radiohead"), so the name matches what lyrics
    sites index. Left alone if the artist is nothing but the postfix, since
    an empty artist searches worse than a wrong one."""
    stripped = _ARTIST_POSTFIX_RE.sub("", artist.strip())
    return stripped or artist.strip()


def clear_artist(artist: str) -> str:
    """Normalise a player-reported artist into the name lyrics sites index,
    dropping the noise a source added rather than anything naming the
    artist: currently the YouTube artist-channel postfix ("RadioheadVEVO"
    -> "Radiohead")."""
    return _strip_artist_postfix(artist)


def clear_title(title: str) -> str:
    """Normalise a player-reported title into the name lyrics sites index,
    dropping both bracketed blocks naming an alternate take ("Creep (Live at
    Glastonbury)" -> "Creep") and known source noise ("Master of Puppets
    (Official Music Video)" -> "Master of Puppets").

    Variants are stripped before the postfix so that either order of the
    two blocks ("... (Live) (Official Music Video)" and the reverse) ends
    up at the same bare title.
    """
    return _strip_title_postfix(_strip_title_variants(title))


_ARTIST_TITLE_SEP = re.compile(r"\s+-\s+")


def split_artist_title(title: str) -> tuple[str, str] | None:
    """Split a combined "<artist> - <title>" string, as reported by some
    MPRIS players (notably radio streams) when they have no separate artist
    field. Returns None if `title` doesn't contain such a separator."""
    parts = _ARTIST_TITLE_SEP.split(title.strip(), maxsplit=1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None
    return parts[0], parts[1]
