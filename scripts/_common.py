"""Shared helpers for the offline spike/eval scripts (not imported by the app)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CACHE = ROOT / ".cache"
EVIDENCE = ROOT / "evidence"

from api._core import meta  # noqa: E402

meta.load_local_env()
