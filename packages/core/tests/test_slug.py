from prismriver_lyrics.slug import slugify


def test_slugify_basic():
    assert slugify("Chuck Strangers") == "chuck-strangers"


def test_slugify_strips_punctuation():
    assert slugify("Master of Puppets!") == "master-of-puppets"


def test_slugify_collapses_whitespace_and_symbols():
    assert slugify("  Guns N' Roses  ") == "guns-n-roses"
