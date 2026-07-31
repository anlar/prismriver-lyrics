from types import SimpleNamespace

from prismriver_lyrics_tui.mpris import (
    MprisWatcher,
    _metadata_fields,
    _player_property_fields,
    format_duration,
    player_short_name,
)


def test_player_short_name_strips_prefix():
    assert player_short_name("org.mpris.MediaPlayer2.mpv") == "mpv"


def test_player_short_name_keeps_instance_suffix_as_fallback():
    # mpv's bus name includes a per-process suffix; this is only the
    # fallback used when the player doesn't expose an Identity property.
    bus_name = "org.mpris.MediaPlayer2.mpv.instance24901"
    assert player_short_name(bus_name) == "mpv.instance24901"


def test_metadata_fields_with_variant_values():
    metadata = {
        "xesam:artist": SimpleNamespace(value=["Artist Name"]),
        "xesam:title": SimpleNamespace(value="Song Title"),
        "xesam:album": SimpleNamespace(value="Album Title"),
        "xesam:albumArtist": SimpleNamespace(value=["Artist Name"]),
        "xesam:genre": SimpleNamespace(value=["Thrash Metal", "Metal"]),
        "xesam:trackNumber": SimpleNamespace(value=3),
        "xesam:discNumber": SimpleNamespace(value=1),
        "mpris:length": SimpleNamespace(value=332_000_000),
        "mpris:artUrl": SimpleNamespace(value="file:///cover.jpg"),
    }
    fields = _metadata_fields(metadata)

    assert fields == {
        "artist": "Artist Name",
        "title": "Song Title",
        "album": "Album Title",
        "album_artist": "Artist Name",
        "genre": "Thrash Metal, Metal",
        "track_number": 3,
        "disc_number": 1,
        "length_us": 332_000_000,
        "art_url": "file:///cover.jpg",
    }


def test_metadata_fields_with_plain_values():
    metadata = {"xesam:artist": ["A", "B"], "xesam:title": "Song"}
    fields = _metadata_fields(metadata)

    assert fields == {"artist": "A, B", "title": "Song"}


def test_metadata_fields_missing_fields():
    assert _metadata_fields({}) == {}


def test_player_property_fields():
    changed = {
        "PlaybackStatus": SimpleNamespace(value="Playing"),
        "Metadata": SimpleNamespace(value={}),
    }
    fields = _player_property_fields(changed)

    assert fields == {"playback_status": "Playing"}


def test_player_property_fields_empty_when_nothing_relevant_changed():
    changed = {"Metadata": SimpleNamespace(value={})}
    assert _player_property_fields(changed) == {}


def test_format_duration():
    assert format_duration(None) == "-"
    assert format_duration(0) == "0:00"
    assert format_duration(65_000_000) == "1:05"
    assert format_duration(332_000_000) == "5:32"


def test_display_name_falls_back_to_bus_name_without_identity():
    watcher = MprisWatcher()
    bus_name = "org.mpris.MediaPlayer2.mpv.instance24901"

    assert watcher._display_name(bus_name) == "mpv.instance24901"


def test_display_name_prefers_cached_identity():
    watcher = MprisWatcher()
    bus_name = "org.mpris.MediaPlayer2.mpv.instance24901"
    watcher._identities[bus_name] = "mpv"

    assert watcher._display_name(bus_name) == "mpv"


def test_display_short_name_falls_back_to_bus_name_without_desktop_entry():
    watcher = MprisWatcher()
    bus_name = "org.mpris.MediaPlayer2.firefox.instance_1_244"

    assert (
        watcher._display_short_name(bus_name) == "firefox.instance_1_244"
    )


def test_display_short_name_prefers_cached_desktop_entry():
    watcher = MprisWatcher()
    bus_name = "org.mpris.MediaPlayer2.firefox.instance_1_244"
    watcher._desktop_entries[bus_name] = "firefox"

    assert watcher._display_short_name(bus_name) == "firefox"


def test_emit_merges_partial_updates_onto_existing_state():
    watcher = MprisWatcher()
    bus_name = "org.mpris.MediaPlayer2.mpv"
    watcher._identities[bus_name] = "mpv"

    watcher._emit(bus_name, artist="Artist Name", title="Song Title")
    watcher._emit(bus_name, playback_status="Paused")

    track = watcher._states[bus_name]
    assert track.player == "mpv"
    assert track.artist == "Artist Name"
    assert track.title == "Song Title"
    assert track.playback_status == "Paused"
