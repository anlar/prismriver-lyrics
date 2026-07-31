from prismriver_lyrics.models import SyncedLine, SyncedLyrics
from prismriver_lyrics.plugins.lrclib import parse_synced_lyrics


def test_parse_synced_lyrics_basic():
    text = "[00:12.00]First line\n[00:17.30]Second line"

    assert parse_synced_lyrics(text) == SyncedLyrics(
        lines=(
            SyncedLine(time_ms=12_000, text="First line"),
            SyncedLine(time_ms=17_300, text="Second line"),
        )
    )


def test_parse_synced_lyrics_sorts_out_of_order_lines():
    text = "[01:00.00]Second line\n[00:30.00]First line"

    assert parse_synced_lyrics(text) == SyncedLyrics(
        lines=(
            SyncedLine(time_ms=30_000, text="First line"),
            SyncedLine(time_ms=60_000, text="Second line"),
        )
    )


def test_parse_synced_lyrics_handles_repeated_line_timestamps():
    text = "[00:10.00][00:40.00]Chorus line"

    assert parse_synced_lyrics(text) == SyncedLyrics(
        lines=(
            SyncedLine(time_ms=10_000, text="Chorus line"),
            SyncedLine(time_ms=40_000, text="Chorus line"),
        )
    )


def test_parse_synced_lyrics_skips_metadata_tags():
    text = "[ar:Some Artist]\n[ti:Some Title]\n[00:05.00]Only real line"

    assert parse_synced_lyrics(text) == SyncedLyrics(
        lines=(SyncedLine(time_ms=5_000, text="Only real line"),)
    )


def test_parse_synced_lyrics_returns_none_without_timestamps():
    assert parse_synced_lyrics("") is None
    assert parse_synced_lyrics("[ar:Some Artist]\n[ti:Some Title]") is None
