import base64
import json
import time

from prismriver_lyrics.plugins.deezer import _JWT_FALLBACK_TTL, _jwt_ttl


def _make_jwt(payload: dict) -> str:
    payload_b64 = (
        base64.urlsafe_b64encode(json.dumps(payload).encode())
        .rstrip(b"=")
        .decode()
    )
    return f"header.{payload_b64}.signature"


def test_jwt_ttl_reads_exp_claim():
    jwt = _make_jwt({"exp": time.time() + 120})

    assert 115 < _jwt_ttl(jwt) <= 120


def test_jwt_ttl_clamps_already_expired_exp_to_zero():
    jwt = _make_jwt({"exp": time.time() - 120})

    assert _jwt_ttl(jwt) == 0.0


def test_jwt_ttl_falls_back_without_exp_claim():
    jwt = _make_jwt({"user_id": 123})

    assert _jwt_ttl(jwt) == _JWT_FALLBACK_TTL


def test_jwt_ttl_falls_back_for_malformed_jwt():
    assert _jwt_ttl("not-a-jwt") == _JWT_FALLBACK_TTL
    assert _jwt_ttl("") == _JWT_FALLBACK_TTL
