import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, replace
from typing import Any

from dbus_next import BusType
from dbus_next.aio import MessageBus, ProxyInterface

logger = logging.getLogger(__name__)

MPRIS_PREFIX = "org.mpris.MediaPlayer2."
MPRIS_PATH = "/org/mpris/MediaPlayer2"
ROOT_IFACE = "org.mpris.MediaPlayer2"
PLAYER_IFACE = "org.mpris.MediaPlayer2.Player"
PROPS_IFACE = "org.freedesktop.DBus.Properties"
DBUS_SERVICE = "org.freedesktop.DBus"
DBUS_PATH = "/org/freedesktop/DBus"

# Player properties (outside of Metadata) that carry useful, non-continuous
# info. Position is deliberately excluded: it changes every tick and MPRIS
# players signal it via a separate Seeked signal rather than
# PropertiesChanged, so it doesn't fit this change-driven model.
_PLAYER_PROPERTY_GETTERS = {
    "playback_status": "get_playback_status",
}


@dataclass(frozen=True, slots=True)
class TrackInfo:
    """A snapshot of what a single MPRIS player reports as currently playing."""

    player: str = ""
    player_short: str = ""
    artist: str = ""
    title: str = ""
    album: str = ""
    album_artist: str = ""
    genre: str = ""
    track_number: int | None = None
    disc_number: int | None = None
    length_us: int | None = None
    art_url: str = ""
    playback_status: str = ""


_PLAYBACK_STATUS_EMOJI = {
    "Playing": "[>]",
    "Paused": "[=]",
    "Stopped": "[x]",
}


def playback_status_emoji(playback_status: str) -> str:
    """Single-glyph icon for an MPRIS PlaybackStatus value."""
    return _PLAYBACK_STATUS_EMOJI.get(playback_status, "[?]")


def player_short_name(bus_name: str) -> str:
    """Fallback display name derived from the D-Bus bus name.

    Some players (e.g. mpv) append a per-process suffix to their bus name
    (`org.mpris.MediaPlayer2.mpv.instance24901`) to allow multiple running
    instances. That suffix is an implementation detail, not a player name,
    so prefer the MPRIS `Identity`/`DesktopEntry` properties when available
    and only fall back to this for players that don't expose either.
    """
    return bus_name.removeprefix(MPRIS_PREFIX)


def format_duration(length_us: int | None) -> str:
    """Format a track length (given in microseconds, as MPRIS reports it)
    as m:ss."""
    if length_us is None:
        return "-"
    total_seconds = length_us // 1_000_000
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"


def _variant_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _metadata_fields(metadata: dict[str, Any]) -> dict[str, Any]:
    """Pull out the MPRIS Metadata entries we care about as plain Python
    values."""
    fields: dict[str, Any] = {}

    def text(key: str, field: str, separator: str = ", ") -> None:
        value = metadata.get(key)
        if value is None:
            return
        unwrapped = _variant_value(value)
        if isinstance(unwrapped, list):
            fields[field] = separator.join(unwrapped)
        else:
            fields[field] = str(unwrapped)

    def integer(key: str, field: str) -> None:
        value = metadata.get(key)
        if value is not None:
            fields[field] = int(_variant_value(value))

    text("xesam:artist", "artist")
    text("xesam:title", "title")
    text("xesam:album", "album")
    text("xesam:albumArtist", "album_artist")
    text("xesam:genre", "genre", separator=" · ")
    text("mpris:artUrl", "art_url")
    integer("xesam:trackNumber", "track_number")
    integer("xesam:discNumber", "disc_number")
    integer("mpris:length", "length_us")

    return fields


def _player_property_fields(changed: dict[str, Any]) -> dict[str, Any]:
    """Pull out playback-state Player properties from a PropertiesChanged
    payload."""
    fields: dict[str, Any] = {}

    if "PlaybackStatus" in changed:
        fields["playback_status"] = str(
            _variant_value(changed["PlaybackStatus"])
        )

    return fields


class MprisWatcher:
    """Watches MPRIS-compliant media players over the D-Bus session bus.

    `watch()` is an async generator that yields a (bus_name, TrackInfo) pair
    every time a known player's metadata or playback state changes, a new
    player appears, or one goes away (reported as an empty-track update).
    """

    def __init__(self) -> None:
        self._bus: MessageBus | None = None
        self._queue: asyncio.Queue[tuple[str, TrackInfo]] = asyncio.Queue()
        self._known: set[str] = set()
        self._identities: dict[str, str] = {}
        self._desktop_entries: dict[str, str] = {}
        self._states: dict[str, TrackInfo] = {}
        self._player_ifaces: dict[str, ProxyInterface] = {}

    def known_players(self) -> dict[str, TrackInfo]:
        """Snapshot of every currently known player's latest TrackInfo."""
        return dict(self._states)

    async def get_position(self, bus_name: str) -> int | None:
        """Current playback position (microseconds) for a known player, or
        None if it can't be read (player gone, or doesn't support the
        Position property).

        Queried on demand rather than cached like the rest of TrackInfo:
        position changes continuously during playback, so a cached value
        goes stale immediately and MPRIS players don't push updates for it
        (see the module-level note by _PLAYER_PROPERTY_GETTERS).
        """
        iface = self._player_ifaces.get(bus_name)
        if iface is None:
            return None
        try:
            return await iface.get_position()
        except Exception:
            logger.debug(
                "failed to get position for %r", bus_name, exc_info=True
            )
            return None

    def _display_name(self, bus_name: str) -> str:
        return self._identities.get(bus_name, player_short_name(bus_name))

    def _display_short_name(self, bus_name: str) -> str:
        return self._desktop_entries.get(bus_name, player_short_name(bus_name))

    def _emit(self, bus_name: str, **fields: Any) -> None:
        display_name = self._display_name(bus_name)
        short_name = self._display_short_name(bus_name)
        current = self._states.get(
            bus_name, TrackInfo(player=display_name, player_short=short_name)
        )
        updated = replace(
            current, player=display_name, player_short=short_name, **fields
        )
        self._states[bus_name] = updated
        self._queue.put_nowait((bus_name, updated))

    async def watch(self) -> AsyncIterator[tuple[str, TrackInfo]]:
        self._bus = await MessageBus(bus_type=BusType.SESSION).connect()

        dbus_iface = await self._interface(
            DBUS_SERVICE, DBUS_PATH, DBUS_SERVICE
        )
        dbus_iface.on_name_owner_changed(self._on_name_owner_changed)

        names = await dbus_iface.call_list_names()
        for name in names:
            if name.startswith(MPRIS_PREFIX):
                await self._subscribe(name)

        while True:
            yield await self._queue.get()

    def _on_name_owner_changed(
        self, name: str, old_owner: str, new_owner: str
    ) -> None:
        if not name.startswith(MPRIS_PREFIX):
            return
        if new_owner and name not in self._known:
            asyncio.ensure_future(self._subscribe(name))
        elif not new_owner and name in self._known:
            self._known.discard(name)
            player = self._display_name(name)
            player_short = self._display_short_name(name)
            self._identities.pop(name, None)
            self._desktop_entries.pop(name, None)
            self._states.pop(name, None)
            self._player_ifaces.pop(name, None)
            self._queue.put_nowait(
                (name, TrackInfo(player=player, player_short=player_short))
            )

    async def _interface(
        self, bus_name: str, path: str, iface_name: str
    ) -> ProxyInterface:
        assert self._bus is not None
        introspection = await self._bus.introspect(bus_name, path)
        obj = self._bus.get_proxy_object(bus_name, path, introspection)
        return obj.get_interface(iface_name)

    async def _subscribe(self, bus_name: str) -> None:
        self._known.add(bus_name)

        try:
            root_iface = await self._interface(bus_name, MPRIS_PATH, ROOT_IFACE)

            try:
                self._identities[bus_name] = await root_iface.get_identity()
            except Exception:
                logger.debug(
                    "failed to get identity for %r", bus_name, exc_info=True
                )

            try:
                self._desktop_entries[bus_name] = (
                    await root_iface.get_desktop_entry()
                )
            except Exception:
                logger.debug(
                    "failed to get desktop entry for %r",
                    bus_name,
                    exc_info=True,
                )
        except Exception:
            logger.debug(
                "failed to get root interface for %r", bus_name, exc_info=True
            )

        try:
            props_iface = await self._interface(
                bus_name, MPRIS_PATH, PROPS_IFACE
            )
        except Exception:
            logger.debug(
                "failed to get properties interface for %r",
                bus_name,
                exc_info=True,
            )
            self._known.discard(bus_name)
            self._identities.pop(bus_name, None)
            self._desktop_entries.pop(bus_name, None)
            return

        def on_properties_changed(
            interface_name: str, changed: dict[str, Any], invalidated: list[str]
        ) -> None:
            if interface_name != PLAYER_IFACE:
                return

            fields: dict[str, Any] = {}
            metadata = changed.get("Metadata")
            if metadata is not None:
                fields.update(_metadata_fields(_variant_value(metadata)))
            fields.update(_player_property_fields(changed))

            if fields:
                self._emit(bus_name, **fields)

        props_iface.on_properties_changed(on_properties_changed)

        try:
            player_iface = await self._interface(
                bus_name, MPRIS_PATH, PLAYER_IFACE
            )
        except Exception:
            logger.debug(
                "failed to get player interface for %r",
                bus_name,
                exc_info=True,
            )
            return

        self._player_ifaces[bus_name] = player_iface

        fields: dict[str, Any] = {}

        try:
            fields.update(_metadata_fields(await player_iface.get_metadata()))
        except Exception:
            logger.debug(
                "failed to get metadata for %r", bus_name, exc_info=True
            )

        for field, getter_name in _PLAYER_PROPERTY_GETTERS.items():
            try:
                fields[field] = await getattr(player_iface, getter_name)()
            except Exception:
                logger.debug(
                    "failed to get %r for %r",
                    field,
                    bus_name,
                    exc_info=True,
                )

        if fields:
            self._emit(bus_name, **fields)
