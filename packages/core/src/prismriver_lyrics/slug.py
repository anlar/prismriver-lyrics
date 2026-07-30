import re

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    """Lowercase and hyphenate a string for use in a lyrics-site URL path."""
    value = _NON_ALNUM.sub("-", value.strip().lower())
    return value.strip("-")
