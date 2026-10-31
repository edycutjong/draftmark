"""Thin client for the Meta Model API (Responses API) with a usage ledger.

Every call returns (json, usage_row). Scripts append usage rows to
evidence/api-usage.md; the deployed site returns them per run (it cannot write to
the repo). The key comes from the environment only (MODEL_API_KEY); local scripts
may load ~/.config/meta/meta.env via load_local_env().
"""
from __future__ import annotations

import base64
import mimetypes
import os
import random
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import httpx

BASE = os.environ.get("MODEL_API_BASE", "https://api.meta.ai/v1")
WONDER = "muse-wonder-1.0"
SPARK = "muse-spark-1.3"
SAM = "sam-3.1"
ALLOWED_MODELS = {WONDER, SPARK, SAM}

# Price list (USD), _docs/meta-model-api.md, 2026-10: per 1M tokens / per 1k frames.
PRICES = {
    WONDER: {"cached": 0.20, "in": 4.00, "out": 20.00},
    SPARK: {"cached": 0.15, "in": 1.25, "out": 4.25},
}
SAM_IMAGE_USD = 2.50 / 1000
SAM_VIDEO_FRAME_USD = 0.20 / 1000

DEV_CAP_USD = float(os.environ.get("DRAFTMARK_DEV_CAP_USD", "30"))
LEDGER = Path(__file__).resolve().parents[2] / "evidence" / "api-usage.md"


class BudgetError(RuntimeError):
    """402/429-billing or the local dev cap: stop calling, never loop."""


class MetaError(RuntimeError):
    def __init__(self, status: int, body: str):
        super().__init__(f"HTTP {status}: {body[:300]}")
        self.status = status


@dataclass
class UsageRow:
    ts: str
    model: str
    feature: str
    latency_ms: int
    est_usd: float
    tokens_in: int | None = None
    tokens_cached: int | None = None
    tokens_out: int | None = None
    frames: int | None = None
    response_id: str | None = None
    run_id: str = ""
    extra: dict = field(default_factory=dict)


def load_local_env(path: str = "~/.config/meta/meta.env") -> None:
    p = Path(path).expanduser()
    if os.environ.get("MODEL_API_KEY") or not p.exists():
        return
    for line in p.read_text().splitlines():
        m = re.match(r"\s*(?:export\s+)?([A-Z_]+)\s*=\s*['\"]?([^'\"]*)['\"]?\s*$", line)
        if m:
            os.environ.setdefault(m.group(1), m.group(2))


def key_present() -> bool:
    return bool(os.environ.get("MODEL_API_KEY"))


def redact(s: str) -> str:
    k = os.environ.get("MODEL_API_KEY", "")
    return s.replace(k, "<REDACTED>") if k else s


def data_url(path: str | Path, mime: str | None = None) -> str:
    mt = mime or mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    return f"data:{mt};base64," + base64.b64encode(Path(path).read_bytes()).decode()


def bytes_data_url(b: bytes, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(b).decode()


def estimate_usd(model: str, usage: dict | None, frames: int | None = None, images: int | None = None) -> float:
    if model == SAM:
        return round((frames or 0) * SAM_VIDEO_FRAME_USD + (images or 0) * SAM_IMAGE_USD, 6)
    p = PRICES.get(model)
    if not p or not usage:
        return 0.0
    tin = int(usage.get("input_tokens") or 0)
    cached = int((usage.get("input_tokens_details") or {}).get("cached_tokens") or 0)
    tout = int(usage.get("output_tokens") or 0)
    return round(((tin - cached) * p["in"] + cached * p["cached"] + tout * p["out"]) / 1e6, 6)


def ledger_total(path: Path = LEDGER) -> float:
    """Sum of the est_usd column of the markdown ledger."""
    if not path.exists():
        return 0.0
    total = 0.0
    for line in path.read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 6 and re.fullmatch(r"~?\d+(\.\d+)?", cells[5] or ""):
            total += float(cells[5].lstrip("~"))
    return round(total, 4)


LEDGER_HEADER = (
    "| ts (WIB) | run_id | model | feature | tokens in (cached) / out · frames | est_usd | latency_ms | response_id |\n"
    "|---|---|---|---|---|---|---|---|\n"
)


def append_ledger(row: UsageRow, path: Path = LEDGER) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            "# Meta API usage ledger\n\nPrice-list estimates from `api/_core/meta.py` PRICES "
            "(not an invoice). Appended by the scripts; rule-5 budget: whole chain <= $40, dev cap "
            f"${DEV_CAP_USD:.0f} enforced by `ledger_total()`.\n\n" + LEDGER_HEADER
        )
    toks = (
        f"{row.tokens_in} ({row.tokens_cached or 0}) / {row.tokens_out}" if row.tokens_in is not None else ""
    )
    if row.frames:
        toks = (toks + " · " if toks else "") + f"{row.frames} frames"
    with path.open("a") as f:
        f.write(
            f"| {row.ts} | {row.run_id} | {row.model} | {row.feature} | {toks} | {row.est_usd:.4f} | "
            f"{row.latency_ms} | {row.response_id or ''} |\n"
        )


class Client:
    def __init__(self, key: str | None = None, ledger: Path | None = LEDGER, run_id: str = "",
                 enforce_cap: bool = True, timeout: float = 300.0):
        self.key = key or os.environ.get("MODEL_API_KEY", "")
        if not self.key:
            raise RuntimeError("MODEL_API_KEY not set")
        self.ledger = ledger
        self.run_id = run_id
        self.enforce_cap = enforce_cap
        self.timeout = timeout
        self.rows: list[UsageRow] = []
        self._http = httpx.Client(base_url=BASE, timeout=timeout,
                                  headers={"Authorization": f"Bearer {self.key}"})

    # -- low level -------------------------------------------------------------
    def _check_cap(self) -> None:
        if self.enforce_cap and self.ledger is not None and ledger_total(self.ledger) >= DEV_CAP_USD:
            raise BudgetError(f"dev cap ${DEV_CAP_USD} reached in {self.ledger}")

    def request(self, method: str, path: str, body: dict | None = None, retries: int = 3,
                timeout: float | None = None) -> tuple[dict, int]:
        self._check_cap()
        model = (body or {}).get("model")
        if model and model not in ALLOWED_MODELS:
            raise ValueError(f"model {model} not allowed (standard models only)")
        last: Exception | None = None
        for attempt in range(retries + 1):
            t0 = time.time()
            try:
                r = self._http.request(method, path, json=body, timeout=timeout or self.timeout)
            except httpx.TransportError as e:  # timeouts, resets
                last = e
                time.sleep(min(30, 2 ** attempt + random.random()))
                continue
            ms = int((time.time() - t0) * 1000)
            if r.status_code == 200:
                return r.json(), ms
            text = redact(r.text)
            if r.status_code == 402 or (r.status_code == 429 and re.search(r"billing|credit|quota|balance", text, re.I)):
                raise BudgetError(f"HTTP {r.status_code}: {text[:200]}")
            if r.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                ra = r.headers.get("retry-after")
                time.sleep(float(ra) if ra and ra.replace(".", "").isdigit() else min(30, 2 ** attempt + random.random()))
                continue
            raise MetaError(r.status_code, text)
        raise MetaError(0, f"transport: {last}")

    def _log(self, model: str, feature: str, resp: dict, ms: int, frames: int | None = None,
             images: int | None = None, **extra) -> UsageRow:
        u = resp.get("usage") or {}
        row = UsageRow(
            ts=time.strftime("%Y-%m-%d %H:%M"), model=model, feature=feature, latency_ms=ms,
            est_usd=estimate_usd(model, u, frames, images),
            tokens_in=u.get("input_tokens"), tokens_out=u.get("output_tokens"),
            tokens_cached=(u.get("input_tokens_details") or {}).get("cached_tokens"),
            frames=frames or images, response_id=resp.get("id"), run_id=self.run_id, extra=extra,
        )
        self.rows.append(row)
        if self.ledger is not None:
            append_ledger(row, self.ledger)
        return row

    # -- Responses API ---------------------------------------------------------
    def responses(self, body: dict, feature: str, frames: int | None = None, images: int | None = None,
                  timeout: float | None = None) -> dict:
        resp, ms = self.request("POST", "/responses", body, timeout=timeout)
        self._log(body["model"], feature, resp, ms, frames=frames, images=images)
        return resp

    def get_response(self, response_id: str) -> dict:
        resp, _ = self.request("GET", f"/responses/{response_id}")
        return resp

    def poll(self, response_id: str, feature: str, every: float = 5.0, max_wait: float = 1800.0) -> dict:
        """Poll a background response; logs usage once when it completes."""
        t0 = time.time()
        while True:
            resp = self.get_response(response_id)
            st = resp.get("status")
            if st not in ("queued", "in_progress"):
                model = resp.get("model") or WONDER
                self._log(model if model in ALLOWED_MODELS else WONDER, feature, resp,
                          int((time.time() - t0) * 1000))
                return resp
            if time.time() - t0 > max_wait:
                raise MetaError(0, f"background {response_id} still {st} after {max_wait}s")
            time.sleep(every)

    def sam(self, concept: str, media_url: str, video: bool, frames: int | None = None,
            feature: str | None = None) -> dict:
        part = ({"type": "input_video", "video_url": media_url} if video
                else {"type": "input_image", "image_url": media_url})
        body = {"model": SAM, "input": [{"type": "message", "role": "user",
                                         "content": [{"type": "input_text", "text": concept}, part]}]}
        return self.responses(body, feature or f"sam {'video' if video else 'image'} '{concept}'",
                              frames=frames if video else None, images=None if video else 1)

    def close(self) -> None:
        self._http.close()


def output_text(resp: dict) -> str:
    out = []
    for o in resp.get("output", []) or []:
        content = o.get("content")
        if isinstance(content, list):
            for c in content:
                if c.get("type") == "output_text":
                    out.append(c.get("text", ""))
    return "".join(out)


def function_calls(resp: dict) -> list[dict]:
    return [o for o in resp.get("output", []) or [] if o.get("type") == "function_call"]


def as_dict(row: UsageRow) -> dict:
    return asdict(row)
