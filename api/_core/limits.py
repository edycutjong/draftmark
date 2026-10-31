"""Spend protection for the live endpoints (no DB on Hobby, so no global cap exists).

- Open class (measure + labels on a committed fixture): per IP and per instance per hour.
- Uploads and Wonder generation: JUDGE_CODE (compared in constant time).
- Fail-closed: a 402 / billing 429 from Meta sets a per-instance BUDGET flag until the instance recycles.
- Kill switch: LIVE_MODE=off -> every live call answers BUDGET and the recorded run is served.
"""
from __future__ import annotations

import hmac
import os
import threading
import time

PER_IP_H = int(os.environ.get("LIVE_PER_IP_H", "5"))
PER_INSTANCE_H = int(os.environ.get("LIVE_PER_INSTANCE_H", "15"))
JUDGE_PER_IP_H = int(os.environ.get("JUDGE_PER_IP_H", "15"))  # judge-code uploads: a judge tries several clips
FREE_PER_IP_H = int(os.environ.get("FREE_PER_IP_H", "60"))  # no-API endpoints that still burn function CPU (sandbox)
_lock = threading.Lock()
_hits: dict[str, list[float]] = {}
_budget_tripped: dict[str, str] = {}
_runs: dict[str, list] = {}  # run id measured here -> [ts, free label calls left]: labels ride on the measure hit


def live_mode() -> bool:
    return os.environ.get("LIVE_MODE", "on").lower() != "off"


def judge_ok(code: str | None) -> bool:
    want = os.environ.get("JUDGE_CODE", "")
    return bool(want) and bool(code) and hmac.compare_digest(want, code)


def trip_budget(why: str) -> None:
    _budget_tripped["reason"] = why[:200]


def budget_reason() -> str | None:
    if not live_mode():
        return "LIVE_MODE=off"
    return _budget_tripped.get("reason")


def take(ip: str, now: float | None = None, run_id: str | None = None, ride: bool = False,
         per_ip: int | None = None) -> tuple[bool, str | None]:
    """Count one live run for ip; (allowed, reason when not). ride=True (labels): the first label call of a run
    measured on this instance within the hour is free; /measure never rides."""
    now = now or time.time()
    with _lock:
        r = _runs.get(run_id) if (ride and run_id) else None
        if r and now - r[0] < 3600 and r[1] > 0:
            r[1] -= 1
            return True, None
        for k in (f"ip:{ip}", "instance"):
            _hits[k] = [t for t in _hits.get(k, []) if now - t < 3600]
        cap = per_ip or PER_IP_H
        if len(_hits[f"ip:{ip}"]) >= cap:
            return False, f"{cap} live runs per IP per hour"
        if len(_hits["instance"]) >= PER_INSTANCE_H:
            return False, f"{PER_INSTANCE_H} live runs per instance per hour"
        _hits[f"ip:{ip}"].append(now)
        _hits["instance"].append(now)
        if run_id and not ride:
            for k in [k for k, v in _runs.items() if now - v[0] >= 3600]:
                del _runs[k]  # a run's free label ride expires after an hour
            _runs[run_id] = [now, 1]
    return True, None


def take_free(ip: str, now: float | None = None) -> tuple[bool, str | None]:
    """Count one call to a no-API endpoint that launches the sandbox (/survey, /selftest/rerun)."""
    now = now or time.time()
    k = f"free:{ip}"
    with _lock:
        _hits[k] = [t for t in _hits.get(k, []) if now - t < 3600]
        if len(_hits[k]) >= FREE_PER_IP_H:
            return False, f"{FREE_PER_IP_H} sandbox runs per IP per hour"
        _hits[k].append(now)
    return True, None


def probes_open(code: str | None) -> bool:
    """Deployed-runtime probes hold a function (sleep up to 300 s): judge code only on production."""
    return os.environ.get("VERCEL_ENV") != "production" or judge_ok(code)


def reset() -> None:  # tests
    with _lock:
        _hits.clear()
        _budget_tripped.clear()
        _runs.clear()
