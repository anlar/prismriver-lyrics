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
