"""PJM-NEXT-21 card 1 (zero LP, no scoring change): size a rule-14 C1 reconciliation.

NEXT-20 card 2 found that the C1 benchmark (EIA-923, ``classFull``) and PJM's own
fuel-mix telemetry (EIA-930 by fuel, equal to PJM ``gen_by_fuel``) disagree by fuel:
930 gas sits 0.1-15.7 TWh BELOW the benchmark and 930 coal 3.4-12.5 TWh ABOVE it, every
year. The model's load is the EIA-930 demand, so the model's total energy is on the 930
boundary while C1 scores it against the 923 boundary.

This probe re-scores the keeper's C1 (``calibration_verdict.score_fuelmix``, unchanged)
against a benchmark re-bounded to the telemetry, month by month, and reports C1 by class
and the determination for every year. Variants (each a scoring-side what-if only):

* ``base``  - the committed benchmark (reproduces the keeper's C1).
* ``gas``   - each month, benchmark gas plants (``GAS_GROUPS``) are scaled so their
  grid-delivered sum equals EIA-930 gas. Explicit handling (NEXT-20 card 2):
  Hopewell Cogeneration (absent from 930 gas) and Martins Creek / Montour (booked by
  PJM as oil / "Multiple Fuels") are held at their EIA-923 value and taken out of both
  the pool and the target's residual. The remaining gap is apportioned pro rata.
* ``gas_all`` - as ``gas`` with no explicit handling (every gas plant in the pool).
* ``gas_coal`` - ``gas`` plus coal plants scaled to EIA-930 coal the same way.

A plant's grid-delivered monthly actual is ``e_mon x (1 - btm / e_ann)``; a class's
re-bounded actual is ``classFull + sum(rescaled - original)`` over its plants, so
``base`` is exact. Writes ``results/phase0/pjm/_pjmnext21_c1_reconcile.json``.
Run: ``.venv/bin/python scripts/probes/_pjmnext21_c1_reconcile.py``
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "scripts"), str(REPO / "scripts" / "probes")):
    if p not in sys.path:
        sys.path.insert(0, p)

import _pjmnext20_ua_census as U  # noqa: E402
import calibration_verdict as cv  # noqa: E402

RUN_ID = "2026-09-30-pjm-next16-ovec"
OUT = REPO / "results/phase0/pjm/_pjmnext21_c1_reconcile.json"
YEARS = tuple(range(2019, 2026))
T = 8760
GAS_GROUPS = U.GAS_GROUPS
COAL_GROUPS = ("COAL_BIT", "COAL_PRB", "COAL_WC", "COAL_LIGNITE")
#: NEXT-20 card 2: Martins Creek, Montour (PJM books as oil / "Multiple Fuels"),
#: Hopewell Cogeneration (absent from 930 gas, hourly coefficient -0.9..-1.5).
HELD = {3148: "Martins Creek", 3149: "Montour", 10633: "Hopewell Cogeneration"}


def _e930_monthly(y: int) -> dict[str, np.ndarray]:
    """EIA-930 PJM gas and coal by month (TWh), NEXT-20's fixed-EST 8760 axis."""
    a = U._e930_fuel(y)
    mon = pd.date_range(f"{y}-01-01 01:00", periods=T, freq="h").month.values
    out = {}
    for f in ("gas", "coal"):
        v = a[f].to_numpy(float)[:T]
        out[f] = np.array([v[mon == m].sum() for m in range(1, 13)]) / 1e6
    return out


def _grid_mon(p: dict) -> np.ndarray:
    """A bench plant's grid-delivered monthly actual (TWh): e_mon net of BTM pro rata."""
    em = p.get("e_mon")
    em = json.loads(em) if isinstance(em, str) else (em or [0.0] * 12)
    em = np.asarray(em, float) / 1e3
    e_ann = float(p.get("e_ann") or 0.0)
    btm = float(p.get("btm") or 0.0)
    f = 1.0 - btm / e_ann if e_ann > 0 else 1.0
    return em * max(f, 0.0)


def rebound(bench: dict, tgt: dict[str, np.ndarray], fuels: dict, hold: bool) -> dict:
    """``classFull`` re-bounded to the 930 telemetry; returns {class: delta TWh} and k."""
    delta: dict[str, float] = {}
    kmon = {}
    for fuel, groups in fuels.items():
        pool = np.zeros(12)
        held = np.zeros(12)
        rows = []
        for k, p in bench["plants"].items():
            if p.get("group") not in groups:
                continue
            gm = _grid_mon(p)
            is_held = hold and int(str(k).split(":")[0]) in HELD
            (held if is_held else pool).__iadd__(gm)
            rows.append((p["group"], gm, is_held))
        # Held plants stay at 923 and are outside the telemetry's fuel; the pool
        # carries the 930 fuel total.
        k_m = np.where(pool > 0, tgt[fuel] / np.where(pool > 0, pool, 1.0), 1.0)
        kmon[fuel] = k_m
        for g, gm, is_held in rows:
            if not is_held:
                delta[g] = delta.get(g, 0.0) + float((gm * (k_m - 1.0)).sum())
    return {"delta": delta, "k": kmon}


VARIANTS = {
    "base": None,
    "gas": ({"gas": GAS_GROUPS}, True),
    "gas_all": ({"gas": GAS_GROUPS}, False),
    "gas_coal": ({"gas": GAS_GROUPS, "coal": COAL_GROUPS}, True),
}


def main() -> None:
    """Re-score C1 for every year and variant; write the JSON."""
    arts = cv.load_artifacts(RUN_ID)
    tgt = {y: _e930_monthly(y) for y in YEARS}
    out: dict = {
        "what": "PJM-NEXT-21 card 1: C1 against a benchmark re-bounded to PJM "
        "fuel-mix telemetry (EIA-930). ZERO LP. Scoring what-if only.",
        "run_id": RUN_ID,
        "held_plants": {str(k): v for k, v in HELD.items()},
        "variants": {},
    }
    for name, spec in VARIANTS.items():
        a2 = copy.deepcopy(arts)
        per_year = {}
        for y in YEARS:
            b = a2["bench"][y]
            if spec is not None:
                r = rebound(b, tgt[y], *spec)
                for g, d in r["delta"].items():
                    if g in b["classFull"]:
                        b["classFull"][g] = float(b["classFull"][g]) + d
                per_year[y] = {
                    "class_delta_twh": {g: round(d, 2) for g, d in r["delta"].items()},
                    "k_month": {
                        f: [round(float(v), 3) for v in k] for f, k in r["k"].items()
                    },
                }
        v = cv.determine_from_artifacts(RUN_ID, a2, years=list(YEARS))
        c1 = {}
        for rec in v["criteria"]["fuelmix"].get("records") or []:
            c1.setdefault(str(rec["year"]), {})[rec["key"]] = {
                "status": rec["status"],
                "d_twh": round(rec["model"] - rec["actual"], 2),
                "share_pp": rec.get("share_pp"),
                "tol": rec.get("tol"),
            }
        fails = {
            cid: sorted(
                {
                    f"{r['year']}:{r.get('key')}"
                    for r in (c.get("records") or [])
                    if r.get("status") == cv.FAIL
                }
            )
            for cid, c in v["criteria"].items()
        }
        tier = cv.determine_from_artifacts(RUN_ID, a2, years=[2023, 2024, 2025])
        out["variants"][name] = {
            "rebound": {str(y): r for y, r in per_year.items()},
            "c1": c1,
            "fails_by_criterion": {k: f for k, f in fails.items() if f},
            "determination_run": v.get("determination"),
            "determination_2023_2025": tier.get("determination"),
        }
        print(name, v.get("determination"), tier.get("determination"))
        for y in YEARS:
            row = c1.get(str(y), {})
            print(
                " ",
                y,
                " ".join(
                    f"{k}:{r['d_twh']:+.1f}{'*' if r['status'] == cv.FAIL else ''}"
                    for k, r in row.items()
                ),
            )
    OUT.write_text(json.dumps(out, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
