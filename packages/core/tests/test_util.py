import pytest
from prismriver_lyrics.util import parse_duration, slugify


def test_parse_duration_single_unit():
    assert parse_duration("1w") == 604800
    assert parse_duration("90s") == 90


def test_parse_duration_compound():
    assert parse_duration("1d5h") == 104400
    assert parse_duration("1w2d3h4m5s") == 788645


def test_parse_duration_rejects_missing_unit():
    with pytest.raises(ValueError):
        parse_duration("5")


def test_parse_duration_rejects_garbage():
    with pytest.raises(ValueError):
        parse_duration("5x")
    with pytest.raises(ValueError):
        parse_duration("")


def test_slugify_basic():
    assert slugify("Chuck Strangers") == "chuck-strangers"


def test_slugify_strips_punctuation():
    assert slugify("Master of Puppets!") == "master-of-puppets"


def test_slugify_collapses_whitespace_and_symbols():
    assert slugify("  Guns N' Roses  ") == "guns-n-roses"
