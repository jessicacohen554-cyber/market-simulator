"""G-COAL148 scorer for an ercot-185 A/B pair (read-only, no LP).

The gate the 2026-08-09 owner ruling carries LIVE: *the ERCOT-148 coal
adjudication must survive — coal dispatch above the measured-window ceiling may
not rise more than 0.5 TWh in any year* (PRECOMMIT-ercot172 §5). Scored on the
ercot-173 basis: **per plant, from the bundles' own dispatch parquets, against
the loader's INCUMBENT PRODUCT ceiling** — i.e. the ceiling composed exactly as
``fleet/arrays.py`` composes it with every ercot-185/173/174 gate OFF, so the
reference is fixed and identical for control and arm:

    ceiling(code, t) = unit_outage_derate_factors[(code, "COAL")][t]
                     x partial_outage_derate_factors[code][t]        # FLAT extract
    excess(code, t)  = max(0, dispatch_mw(code, t) - ceiling(code, t) x capacity_mw(code))

summed over the plant's COAL-class tranches and all 8760 hours. The comparison
basis is the ERCOT-148 quantification's own (4.36 / 4.98 / 5.01 TWh coal).

The arm may only be compared against a same-HEAD control: the run181 keeper is
known not to reproduce at current main (ercot-173 §5, carried through ercot-174
§5 item 4), so an absolute above-ceiling number is not a gate — the RISE is.

Usage::

    python scripts/probes/ercot185_coal148.py \
        --base results/calibration/ercot185_shapedcontrol_A \
        --arm  results/calibration/ercot185_shapedarm_B \
        [--out results/calibration/ercot185_coal148.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import CAMPD_BINS_CSV  # noqa: E402
from market_sim.data.fleet import load_campd_bins  # noqa: E402
from market_sim.data.outages import (  # noqa: E402
    partial_outage_derate_factors,
    unit_outage_derate_factors,
)

HOURS = 8760
YEARS = (2023, 2024, 2025)
BAR_TWH = 0.5  # PRECOMMIT-ercot172 §5: the rise may not exceed this in ANY year


def coal_dispatch_by_plant(bundle: Path, year: int) -> dict[int, np.ndarray]:
    """P1 hourly MW per plant, summed over the plant's COAL-class tranches.

    P1 is the scored pass (CLAUDE.md: "P1 is THE main run"). Classes are the
    LP's COAL_* families; the ceiling is keyed on the bins sheet's COAL plant
    group, which is their union at plant grain.
    """
    paths = sorted((bundle / "dispatch").glob(f"{year}_*.parquet"))
    if not paths:
        raise SystemExit(f"no dispatch parquet for {year} in {bundle}")
    df = pd.concat(
        [
            pd.read_parquet(p, columns=["pass", "klass", "plant_code", "hour", "mw"])
            for p in paths
        ],
        ignore_index=True,
    )
    df = df[(df["pass"] == "P1") & df["klass"].astype(str).str.startswith("COAL")]
    df = df[df["plant_code"] > 0]
    out: dict[int, np.ndarray] = {}
    g = df.groupby(["plant_code", "hour"], observed=True)["mw"].sum()
    for code, sub in g.groupby(level=0):
        arr = np.zeros(HOURS)
        idx = sub.index.get_level_values(1).to_numpy(dtype=int)
        np.add.at(arr, idx[idx < HOURS], sub.to_numpy(float)[idx < HOURS])
        out[int(code)] = arr
    return out


def incumbent_ceiling(year: int, cap: dict[int, float]) -> dict[int, np.ndarray]:
    """The loader's INCUMBENT PRODUCT ceiling in MW, per coal plant."""
    ufac = unit_outage_derate_factors(year, HOURS, str(CAMPD_BINS_CSV), iso="ERCOT")
    pfac = partial_outage_derate_factors(year, HOURS)  # FLAT extract, gate off
    out: dict[int, np.ndarray] = {}
    for code, pmax in cap.items():
        w = ufac.get((code, "COAL"))
        p = pfac.get(code)
        if w is None and p is None:
            continue
        f = np.ones(HOURS)
        if w is not None:
            f = f * np.asarray(w, dtype=float)
        if p is not None:
            f = f * np.asarray(p, dtype=float)
        out[code] = f * pmax
    return out


def above_ceiling_twh(
    disp: dict[int, np.ndarray], ceil: dict[int, np.ndarray]
) -> tuple[float, dict[str, float]]:
    """Total and per-plant coal energy above the incumbent product ceiling."""
    per: dict[str, float] = {}
    total = 0.0
    for code, d in disp.items():
        c = ceil.get(code)
        if c is None:
            continue  # no measured window/plateau: the ceiling never binds
        e = float(np.clip(d - c, 0.0, None).sum())
        total += e
        if e > 0:
            per[str(code)] = round(e / 1e6, 4)
    return total / 1e6, per


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--arm", type=Path, required=True)
    ap.add_argument(
        "--out", type=Path, default=REPO / "results/calibration/ercot185_coal148.json"
    )
    args = ap.parse_args()

    bins = load_campd_bins(str(CAMPD_BINS_CSV))
    cap = {
        int(c): float(m)
        for c, g, m in zip(bins["Plant_Code"], bins["Plant_Group"], bins["capacity_mw"])
        if str(g) == "COAL" and m and m > 0
    }

    out: dict = {
        "_provenance": {
            "scorer": "scripts/probes/ercot185_coal148.py",
            "base": str(args.base),
            "arm": str(args.arm),
            "gate": (
                "G-COAL148 (PRECOMMIT-ercot172 §5, carried LIVE by the 2026-08-09 "
                "owner ruling): coal dispatch above the incumbent PRODUCT ceiling "
                "may not rise more than 0.5 TWh in any year"
            ),
            "reference": "ERCOT-148 quantification basis 4.36/4.98/5.01 TWh",
        },
        "years": {},
    }
    rises: list[float] = []
    for year in YEARS:
        ceil = incumbent_ceiling(year, cap)
        b, b_per = above_ceiling_twh(coal_dispatch_by_plant(args.base, year), ceil)
        a, a_per = above_ceiling_twh(coal_dispatch_by_plant(args.arm, year), ceil)
        rises.append(a - b)
        out["years"][str(year)] = {
            "base_above_ceiling_TWh": round(b, 4),
            "arm_above_ceiling_TWh": round(a, 4),
            "rise_TWh": round(a - b, 4),
            "bar_TWh": BAR_TWH,
            "PASS": bool((a - b) <= BAR_TWH),
            "base_per_plant_TWh": b_per,
            "arm_per_plant_TWh": a_per,
        }
    out["G-COAL148"] = {
        "PASS": bool(all(r <= BAR_TWH for r in rises)),
        "max_rise_TWh": round(max(rises), 4),
        "by_year_rise_TWh": {str(y): round(r, 4) for y, r in zip(YEARS, rises)},
        "ercot173_rejected_arm_for_comparison_TWh": {
            "2023": 0.98,
            "2024": 1.95,
            "2025": 2.73,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1))
    print(json.dumps(out["G-COAL148"], indent=1))


if __name__ == "__main__":
    main()
