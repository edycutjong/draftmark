"""The mini-barge: an analytic "booklet" for a straight-sided box (program_author: analytic).

displacement = rho * A * T with A = L * B (OUTER dimensions at the waterline), T = draft
from the keel (the strip's zero edge sits at the box's outer bottom edge, offset z0).
The bucket evaluation proves the MEASUREMENT against a kitchen scale; this code is not
written by a model and is never counted in the Trieste self-test.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Barge:
    L_m: float
    B_m: float
    light_kg: float
    zero_offset_m: float = 0.0  # strip zero above (+) / below (-) the outer bottom edge
    rho_kg_m3: float = 997.0  # fresh water at 25 C unless a temperature reading says otherwise

    @property
    def area_m2(self) -> float:
        return self.L_m * self.B_m


def displacement_kg(b: Barge, strip_draft_m: float) -> float:
    t = strip_draft_m + b.zero_offset_m
    if t <= 0 or t > 0.40:
        raise ValueError(f"draft {t:.4f} m outside the box (0-0.40 m)")
    return b.rho_kg_m3 * b.area_m2 * t


def survey(b: Barge, strip_draft_m: float, u_draft_m: float | None = None, u_geom: dict | None = None) -> dict:
    """Cargo (sand) mass = displacement - light weight; u by quadrature (draft + geometry)."""
    disp = displacement_kg(b, strip_draft_m)
    cargo = disp - b.light_kg
    out = {"draft_m": strip_draft_m, "T_m": strip_draft_m + b.zero_offset_m, "area_m2": b.area_m2,
           "rho": b.rho_kg_m3, "disp_kg": disp, "light_kg": b.light_kg, "cargo_kg": cargo,
           "program_author": "analytic"}
    if u_draft_m is not None:
        g = u_geom or {}
        t = out["T_m"]
        rel2 = ((g.get("u_L", 0.0) / b.L_m) ** 2 + (g.get("u_B", 0.0) / b.B_m) ** 2
                + (g.get("u_rho", 0.0) / b.rho_kg_m3) ** 2 + (g.get("u_zero", 0.0) / t) ** 2
                + (g.get("u_taper", 0.0) / b.L_m) ** 2)
        u_disp = math.sqrt((b.rho_kg_m3 * b.area_m2 * u_draft_m) ** 2 + (disp ** 2) * rel2
                           + g.get("u_scale_kg", 0.001) ** 2)
        out["u_disp_kg"] = u_disp
        out["u_cargo_kg"] = math.sqrt(u_disp ** 2 + g.get("u_scale_kg", 0.001) ** 2)
    return out


def table(b: Barge, t0: float = 0.01, t1: float = 0.30, step: float = 0.005) -> list[dict]:
    """The analytic hydrostatic table (strip draft -> displacement), for display and the oracle self-test."""
    n = int(round((t1 - t0) / step))
    return [{"draft_m": round(t0 + i * step, 4), "disp_kg": round(displacement_kg(b, t0 + i * step), 4),
             "kg_per_mm": round(b.rho_kg_m3 * b.area_m2 / 1000, 5)} for i in range(n + 1)]
