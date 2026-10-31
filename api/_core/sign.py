"""Server signatures on station outputs, so /survey only certifies what this server measured.

The browser still carries the JSON between the stateless endpoints; each station signs what it produced
(HMAC-SHA256 under a key derived from the deployment's own secret, never sent) and the next station verifies
it. /measure seals the geometry, /labels issues a labels token bound to that geometry, /draft issues the
measure token bound to both; /survey takes the draft, uncertainty, label checks and called models from the
token, never from the request body. Numbers are normalised to float before hashing, so a JSON round trip
through the browser (5.0 -> 5) verifies.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os


def _key() -> bytes:
    base = os.environ.get("DRAFTMARK_SIGNING_KEY") or os.environ.get("MODEL_API_KEY") or ""
    return hmac.new(base.encode(), b"draftmark-station-sign-v1", hashlib.sha256).digest() if base else b""


def _norm(x):
    if x is None or isinstance(x, (bool, str)):
        return x
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, dict):
        return {str(k): _norm(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_norm(v) for v in x]
    return str(x)


def _mac(kind: str, obj) -> str:
    k = _key()
    if not k:
        return ""
    msg = json.dumps([kind, _norm(obj)], sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(k, msg, hashlib.sha256).hexdigest()


def _ok(kind: str, obj, sig) -> bool:
    want = _mac(kind, obj)
    return bool(want) and isinstance(sig, str) and hmac.compare_digest(want, sig)


def seal_geometry(geom: dict) -> dict:
    g = {k: v for k, v in geom.items() if k != "sig"}
    g["sig"] = _mac("geometry", g)
    return g


def geometry_ok(geom) -> bool:
    return isinstance(geom, dict) and _ok("geometry", {k: v for k, v in geom.items() if k != "sig"}, geom.get("sig"))


def token(kind: str, payload: dict) -> dict:
    return {"payload": payload, "sig": _mac(kind, payload)}


def token_ok(kind: str, tok) -> dict | None:
    """The payload if the token was issued by this deployment for `kind`, else None."""
    if isinstance(tok, dict) and isinstance(tok.get("payload"), dict) and _ok(kind, tok["payload"], tok.get("sig")):
        return tok["payload"]
    return None
