from datetime import UTC, datetime

import httpx

from prismriver_lyrics.models import LyricsResult, SyncedLine, SyncedLyrics
from prismriver_lyrics.plugins.base import LyricsPlugin

_BASE_URL = "https://music.youtube.com/youtubei/v1"

# Restricts /search results to the "Songs" category of YouTube Music's
# internal search; lifted from the site's own web client.
_SEARCH_FILTER_PARAMS = "EgWKAQIIAWoMEA4QChADEAQQCRAF"

_LYRICS_PAGE_TYPE = "MUSIC_PAGE_TYPE_TRACK_LYRICS"


def _web_context() -> dict:
    return {
        "client": {
            "clientName": "WEB_REMIX",
            "clientVersion": datetime.now(UTC).strftime("1.%Y%m%d.01.00"),
        },
        "user": {},
    }


def _android_context() -> dict:
    return {
        "client": {"clientName": "ANDROID_MUSIC", "clientVersion": "7.21.50"},
        "user": {},
    }


class YTMusicPlugin(LyricsPlugin):
    """Fetches line-synced lyrics from YouTube Music's internal
    (unofficial) `youtubei` API, in three steps against
    music.youtube.com/youtubei/v1:

    1. `search` with the "Songs" filter, walking
       `contents.tabbedSearchResultsRenderer.tabs[].tabRenderer.content
       .sectionListRenderer.contents[].musicShelfRenderer.contents[]
       .musicResponsiveListItemRenderer` for the first item whose title
       (flex column 0) and artist (flex column 1's first run) match, to
       get its video ID.
    2. `next` (YT Music's "what's playing" panel, keyed off that video
       ID) to find the watch page's Lyrics tab and its browse ID, via
       `contents.singleColumnMusicWatchNextResultsRenderer.tabbedRenderer
       .watchNextTabbedResultsRenderer.tabs[].tabRenderer`, filtered to
       the tab whose `endpoint.browseEndpoint
       .browseEndpointContextSupportedConfigs
       .browseEndpointContextMusicConfig.pageType` is
       "MUSIC_PAGE_TYPE_TRACK_LYRICS" and that isn't `unselectable`
       (present-but-disabled when a track has no lyrics).
    3. `browse` with that browse ID and an Android client context (the
       web client serves an older, unsynced lyrics format from this same
       endpoint), reading line text and start times from
       `contents.elementRenderer.newElement.type.componentType.model
       .timedLyricsModel.lyricsData.timedLyricsData[]`
       (`.lyricLine`, `.cueRange.startTimeMilliseconds`).

    Both `search` and `next` use a web client context; only `browse`
    needs the Android one, to get timed rather than plain lyrics.
    """

    id = "ytmusic"
    name = "YouTube Music"

    sync = 1

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        video_id = await self._find_video_id(client, artist, title)
        if video_id is None:
            return []

        browse_id = await self._find_lyrics_browse_id(client, video_id)
        if browse_id is None:
            return []

        lines = await self._fetch_lyrics(client, browse_id)
        if not lines:
            return []

        url = f"https://music.youtube.com/watch?v={video_id}"
        lyrics = "\n".join(line.text for line in lines)
        return [
            LyricsResult(source=self.name, url=url, lyrics=lyrics),
            LyricsResult(
                source=self.name,
                url=url,
                lyrics=SyncedLyrics(lines=tuple(lines)),
            ),
        ]

    async def _post(
        self, client: httpx.AsyncClient, endpoint: str, body: dict
    ) -> dict | None:
        response = await client.post(
            f"{_BASE_URL}/{endpoint}", params={"alt": "json"}, json=body
        )
        if response.status_code != 200:
            return None
        return response.json()

    async def _find_video_id(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> str | None:
        data = await self._post(
            client,
            "search",
            {
                "query": f"{artist} {title}",
                "params": _SEARCH_FILTER_PARAMS,
                "context": _web_context(),
            },
        )
        if data is None:
            return None

        tabs = (
            data.get("contents", {})
            .get("tabbedSearchResultsRenderer", {})
            .get("tabs")
            or []
        )
        for tab in tabs:
            sections = (
                tab.get("tabRenderer", {})
                .get("content", {})
                .get("sectionListRenderer", {})
                .get("contents")
                or []
            )
            for section in sections:
                items = (
                    section.get("musicShelfRenderer", {}).get("contents")
                    or []
                )
                for item in items:
                    renderer = item.get("musicResponsiveListItemRenderer")
                    if renderer is None:
                        continue
                    video_id = self._match_search_item(
                        renderer, artist, title
                    )
                    if video_id is not None:
                        return video_id
        return None

    @staticmethod
    def _match_search_item(
        renderer: dict, artist: str, title: str
    ) -> str | None:
        video_id = (
            renderer.get("overlay", {})
            .get("musicItemThumbnailOverlayRenderer", {})
            .get("content", {})
            .get("musicPlayButtonRenderer", {})
            .get("playNavigationEndpoint", {})
            .get("watchEndpoint", {})
            .get("videoId")
        )
        if not video_id:
            return None

        flex_columns = renderer.get("flexColumns") or []
        item_title = YTMusicPlugin._flex_column_text(flex_columns, 0)
        item_artist = YTMusicPlugin._flex_column_text(flex_columns, 1)
        if item_title is None or item_title.lower() != title.lower():
            return None
        if item_artist is not None and item_artist.lower() != artist.lower():
            return None
        return video_id

    @staticmethod
    def _flex_column_text(flex_columns: list, index: int) -> str | None:
        if index >= len(flex_columns):
            return None
        runs = (
            flex_columns[index]
            .get("musicResponsiveListItemFlexColumnRenderer", {})
            .get("text", {})
            .get("runs")
            or []
        )
        return runs[0].get("text") if runs else None

    async def _find_lyrics_browse_id(
        self, client: httpx.AsyncClient, video_id: str
    ) -> str | None:
        data = await self._post(
            client,
            "next",
            {
                "videoId": video_id,
                "playlistId": f"RDAMVM{video_id}",
                "enablePersistentPlaylistPanel": True,
                "isAudioOnly": True,
                "tunerSettingValue": "AUTOMIX_SETTING_NORMAL",
                "watchEndpointMusicSupportedConfigs": {
                    "watchEndpointMusicConfig": {
                        "hasPersistentPlaylistPanel": True,
                        "musicVideoType": "MUSIC_VIDEO_TYPE_ATV",
                    }
                },
                "context": _web_context(),
            },
        )
        if data is None:
            return None

        tabs = (
            data.get("contents", {})
            .get("singleColumnMusicWatchNextResultsRenderer", {})
            .get("tabbedRenderer", {})
            .get("watchNextTabbedResultsRenderer", {})
            .get("tabs")
            or []
        )
        for tab in tabs:
            tab_renderer = tab.get("tabRenderer", {})
            if tab_renderer.get("unselectable"):
                continue
            browse_endpoint = tab_renderer.get("endpoint", {}).get(
                "browseEndpoint", {}
            )
            page_type = (
                browse_endpoint.get(
                    "browseEndpointContextSupportedConfigs", {}
                )
                .get("browseEndpointContextMusicConfig", {})
                .get("pageType")
            )
            if page_type == _LYRICS_PAGE_TYPE:
                return browse_endpoint.get("browseId")
        return None

    async def _fetch_lyrics(
        self, client: httpx.AsyncClient, browse_id: str
    ) -> list[SyncedLine]:
        data = await self._post(
            client,
            "browse",
            {"browseId": browse_id, "context": _android_context()},
        )
        if data is None:
            return []

        entries = (
            data.get("contents", {})
            .get("elementRenderer", {})
            .get("newElement", {})
            .get("type", {})
            .get("componentType", {})
            .get("model", {})
            .get("timedLyricsModel", {})
            .get("lyricsData", {})
            .get("timedLyricsData")
            or []
        )

        lines = []
        for entry in entries:
            text = (entry.get("lyricLine") or "").strip()
            if not text:
                continue
            start = entry.get("cueRange", {}).get("startTimeMilliseconds")
            if start is None:
                continue
            lines.append(SyncedLine(time_ms=int(start), text=text))
        return lines
