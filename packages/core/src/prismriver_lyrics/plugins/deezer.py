import base64
import difflib
import json
import time

import httpx

from prismriver_lyrics.kv_cache import KeyValueCache
from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_AUTH_URL = "https://auth.deezer.com/login/anonymous?jo=p"
_API_URL = "https://pipe.deezer.com/api"
_MIN_TITLE_SIMILARITY = 0.5

# Namespace/key this plugin's anonymous JWT is cached under (see
# KeyValueCache) so a fresh one isn't fetched on every single search.
_JWT_CACHE_NAMESPACE = "deezer"
_JWT_CACHE_KEY = "anonymous_jwt"

# Fallback cache TTL for the JWT when its own "exp" claim can't be read
# (see _jwt_ttl) — short enough that a bad guess here just means one
# avoidable re-auth, not a long stretch of failed searches.
_JWT_FALLBACK_TTL = 300.0

_jwt_cache = KeyValueCache()


def _jwt_ttl(jwt: str) -> float:
    """Seconds until `jwt`'s own "exp" claim, or _JWT_FALLBACK_TTL if it
    doesn't have one (or isn't parseable) — a JWT is safe to inspect like
    this without verifying its signature, since it's only ever used here
    to size a cache entry, not to authenticate anything on our side."""
    try:
        payload_b64 = jwt.split(".")[1]
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        exp = json.loads(base64.urlsafe_b64decode(padded))["exp"]
    except Exception:
        return _JWT_FALLBACK_TTL
    return max(exp - time.time(), 0.0)


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

    The JWT is cached on disk (see _jwt_cache), keyed to its own "exp"
    claim, since anonymous auth doesn't depend on anything request-
    specific (no per-user identity) and a fresh one otherwise costs an
    extra request-response round trip on every single search. If a
    cached JWT turns out to already be stale server-side (the Search
    call itself fails), it's dropped and one fresh-auth retry is made
    before giving up.
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
        jwt = await self._get_jwt(client)
        if jwt is None:
            return []

        edges = await self._search_tracks(client, jwt, artist, title)
        if edges is None:
            # Possibly a cached JWT that's expired server-side ahead of
            # its recorded TTL; drop it and retry once with a fresh one.
            await _jwt_cache.adelete(_JWT_CACHE_NAMESPACE, _JWT_CACHE_KEY)
            jwt = await self._get_jwt(client)
            if jwt is None:
                return []
            edges = await self._search_tracks(client, jwt, artist, title)
            if edges is None:
                return []

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

    async def _get_jwt(self, client: httpx.AsyncClient) -> str | None:
        cached = await _jwt_cache.aget(_JWT_CACHE_NAMESPACE, _JWT_CACHE_KEY)
        if cached is not None:
            return cached

        auth_data = await self.fetch_json(client, _AUTH_URL)
        if auth_data is None:
            return None
        jwt = auth_data.get("jwt")
        if not jwt:
            return None

        await _jwt_cache.aset(
            _JWT_CACHE_NAMESPACE, _JWT_CACHE_KEY, jwt, _jwt_ttl(jwt)
        )
        return jwt

    @staticmethod
    async def _search_tracks(
        client: httpx.AsyncClient, jwt: str, artist: str, title: str
    ) -> list[dict] | None:
        body = {
            "operationName": "Search",
            "variables": {"query": f"{artist} {title}"},
            "query": _SEARCH_QUERY,
        }
        response = await client.post(
            _API_URL, json=body, headers={"Authorization": f"Bearer {jwt}"}
        )
        if response.status_code != 200:
            return None

        return (
            response.json()
            .get("data", {})
            .get("search", {})
            .get("results", {})
            .get("tracks", {})
            .get("edges", [])
        )
