from prismriver_lyrics.plugins.base import SimpleLyricsPlugin
from prismriver_lyrics.util import split_words


def _slug(value: str) -> str:
    return "-".join(w.capitalize() for w in split_words(value))


class ShowMeLyricsPlugin(SimpleLyricsPlugin):
    """Fetches lyrics from showmelyrics.com.

    URL shape: https://showmelyrics.com/lyrics/{Artist}-{Title}, where
    artist/title are split into words and each word is title-cased
    (capitalized, not lowercased), joined by hyphens. The site sometimes
    redirects this guessed slug to a disambiguated one (e.g. suffixed
    with "-2"); httpx's client follows that automatically.
    """

    id = "showmelyrics"
    name = "ShowMeLyrics"

    SELECTOR = ".editable-content[itemprop='text']"

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = _slug(artist)
        title_slug = _slug(title)
        return f"https://showmelyrics.com/lyrics/{artist_slug}-{title_slug}"
