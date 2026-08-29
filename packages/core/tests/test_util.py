import pytest
from prismriver_lyrics.util import (
    parse_duration,
    slugify,
    split_artist_title,
    strip_artist_postfix,
    strip_title_postfix,
)


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


def test_split_artist_title_basic():
    assert split_artist_title("Metallica - Master of Puppets") == (
        "Metallica",
        "Master of Puppets",
    )


def test_split_artist_title_unicode():
    assert split_artist_title("大黒摩季 - リーマンブルース") == (
        "大黒摩季",
        "リーマンブルース",
    )


def test_split_artist_title_splits_on_first_separator_only():
    assert split_artist_title("A - B - C") == ("A", "B - C")


def test_split_artist_title_strips_surrounding_whitespace():
    assert split_artist_title("  Metallica - Master of Puppets  ") == (
        "Metallica",
        "Master of Puppets",
    )


def test_split_artist_title_rejects_no_separator():
    assert split_artist_title("Master of Puppets") is None


def test_split_artist_title_rejects_hyphen_without_spaces():
    assert split_artist_title("well-known title") is None


def test_split_artist_title_rejects_empty_side():
    assert split_artist_title(" - Master of Puppets") is None
    assert split_artist_title("Metallica - ") is None


@pytest.mark.parametrize(
    "value, expected",
    [
        (
            "Master of Puppets (Official Music Video)",
            "Master of Puppets",
        ),
        (
            "Master of Puppets (official music video)",
            "Master of Puppets",
        ),
        (
            "Master of Puppets [Official Music Video]",
            "Master of Puppets",
        ),
        ("Master of Puppets", "Master of Puppets"),
        (
            "(Official Music Video) Master of Puppets",
            "(Official Music Video) Master of Puppets",
        ),
    ],
)
def test_strip_title_postfix(value, expected):
    assert strip_title_postfix(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("RadioheadVEVO", "Radiohead"),
        ("Radiohead VEVO", "Radiohead"),
        ("Radiohead", "Radiohead"),
        # Case-sensitive: only the shouted form is a channel postfix.
        ("RadioheadVevo", "RadioheadVevo"),
        ("Radioheadvevo", "Radioheadvevo"),
        # Only a postfix, not anywhere in the name.
        ("VEVO Radiohead", "VEVO Radiohead"),
        # Nothing but the postfix: an empty artist is worse than a wrong one.
        ("VEVO", "VEVO"),
    ],
)
def test_strip_artist_postfix(value, expected):
    assert strip_artist_postfix(value) == expected
