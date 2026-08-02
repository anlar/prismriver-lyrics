import difflib

import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_AUTH_URL = "https://auth.deezer.com/login/anonymous?jo=p"
_API_URL = "https://pipe.deezer.com/api"
_MIN_TITLE_SIMILARITY = 0.5

# Deezer's public API doesn't have a documented lyrics endpoint; this is
# the internal GraphQL query the deezer.com web player itself uses.
_SEARCH_QUERY = """
query Search($query: String) {
  search(query: $query) {
    results {
      tracks {
        edges {
          node {
            id
            title
            lyrics {
              text
            }
          }
        }
      }
    }
  }
}
"""


class DeezerPlugin(LyricsPlugin):
    """Fetches lyrics from deezer.com via its internal GraphQL API.

    Authenticates anonymously for a short-lived JWT, then runs a Search
    query (artist + title as free text) and picks the track whose title
    best matches the requested one, among results that carry lyrics text.
    """

    id = "deezer"
    name = "Deezer"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        auth_response = await client.get(_AUTH_URL)
        if auth_response.status_code != 200:
            return []
        jwt = auth_response.json().get("jwt")
        if not jwt:
            return []

        body = {
            "operationName": "Search",
            "variables": {"query": f"{artist} {title}"},
            "query": _SEARCH_QUERY,
        }
        response = await client.post(
            _API_URL, json=body, headers={"Authorization": f"Bearer {jwt}"}
        )
        if response.status_code != 200:
            return []

        edges = (
            response.json()
            .get("data", {})
            .get("search", {})
            .get("results", {})
            .get("tracks", {})
            .get("edges", [])
        )

        best_node = None
        best_score = 0.0
        for edge in edges:
            node = edge.get("node")
            if not node:
                continue
            lyrics_text = (node.get("lyrics") or {}).get("text")
            if not lyrics_text:
                continue
            score = difflib.SequenceMatcher(
                None, (node.get("title") or "").lower(), title.lower()
            ).ratio()
            if score > best_score:
                best_score = score
                best_node = node

        if best_node is None or best_score < _MIN_TITLE_SIMILARITY:
            return []

        lyrics = best_node["lyrics"]["text"].strip()
        if not lyrics:
            return []

        url = f"https://www.deezer.com/track/{best_node['id']}"
        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]
