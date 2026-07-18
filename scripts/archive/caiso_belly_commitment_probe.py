#!/usr/bin/env python
"""Model-vs-actual CAISO gas-CC belly + evening commitment probe (no re-solve).

Quantifies the belly-commitment posture that the seam-tz forensics
(``results/calibration/FINDING-caiso-seam-tz-correction-2026-07-07.md`` §4.3/§6)
reattributed the C3a body overprice to, using the committed ``caiso65`` keeper
run payload for the model side (no LP re-solve) and CAMPD CEMS for actual.

For each 2023-2025 it reports the combined CC_REGULAR + CC_CHP gas fleet's mean
online output (GW) in the solar belly (h9-15) and the evening ramp (h18-21),
model vs actual, so the belly-vs-evening leverage split is explicit:

  * Model: per-plant hourly MW decoded from the keeper's run-payload sidecar
    (``frontend/data/backcast/runs/<id>.js``) via the scorer's own
    ``legitimacy_diagnostics.load_payload_plants`` — the same source the D-1/D-2
    diagnostics use, so this probe is byte-consistent with the committed scores.
  * Actual: CAMPD CA unit-level gross load routed to the model CC classes via the
    canonical EIA-923 dominant-class map (same routing as the CT-drag derivation).

This is a DIAGNOSTIC probe (rule 15 visibility), not a mechanism and not a floor:
it derives nothing, writes nothing, and touches no keeper. It exists to ground the
G-15 residual-(a) belly-commitment question in model-vs-actual numbers before any
mechanism is built.

Usage:
    python scripts/archive/caiso_belly_commitment_probe.py
    python scripts/archive/caiso_belly_commitment_probe.py --run-id <keeper-id>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

import scripts.legitimacy_diagnostics as L  # noqa: E402
from market_sim.data.campd import CAMPD_UNIT_PLANT_REMAP  # noqa: E402
from market_sim.data.fleet import eia923_dominant_class_by_plant  # noqa: E402

HOURS = 8760
_CC_CLASSES = ("CC_REGULAR", "CC_CHP")
BELLY_HOURS = (9, 16)  # [9,16) — the solar belly / duck neck
EVENING_HOURS = (18, 22)  # [18,22) — the evening net-load ramp

# Cumulative hours at the start of each month (non-leap), date+hour -> hour-of-year.
_MONTH_START_HOUR = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016]


def _hoy(date: pd.Series, hour: pd.Series) -> np.ndarray:
    """Map (date, 0-based hour) to non-leap hour-of-year (Feb 29 -> -1)."""
    m = date.dt.month.to_numpy(dtype=int)
    d = date.dt.day.to_numpy(dtype=int)
    h = np.asarray(hour, dtype=int)
    base = np.array(_MONTH_START_HOUR)[m - 1]
    return np.where((m == 2) & (d == 29), -1, base + (d - 1) * 24 + h)


def actual_cc_mw(year: int, bench: dict[str, dict]) -> np.ndarray:
    """Measured CAISO CC_REGULAR+CC_CHP fleet MW per hour (8760), from CAMPD.

    RESTRICTED to the model's own CAISO bench fleet (2026-07-11 correction):
    the CAMPD ``CA_<year>`` parquet is the whole CEMS *state* extract and the
    dominant-class map is not ISO-filtered, so the unrestricted sum counted
    16.6-18.5 TWh/yr of NON-CAISO California CC (LADWP Haynes / Scattergood /
    Valley, SMUD Cosumnes, TID Walnut, Burbank Magnolia, IID El Centro, the
    BANC-area plants, ...) as "actual" — inflating the apparent belly/evening
    commitment gap by ~1.9-2.1 GW mean. Filtering the effective plant code to
    the bench plant set makes both sides the SAME fleet (the bench is the
    CAISO model fleet with CAMPD coverage), which is the comparison the
    probe's committed users (the evening-CC design's §0 gate) assumed.
    """
    dom = eia923_dominant_class_by_plant(year)
    bench_ids = {int(pid) for pid in bench if str(pid).isdigit()}
    path = REPO / "data" / "raw" / "campd-unit-level" / f"CA_{year}.parquet"
    raw = pd.read_parquet(
        path, columns=["facilityId", "unitId", "date", "hour", "grossLoad"]
    ).dropna(subset=["grossLoad"])
    raw["fac"] = pd.to_numeric(raw["facilityId"], errors="coerce").astype("Int64")
    raw = raw.dropna(subset=["fac"])
    eff = [
        CAMPD_UNIT_PLANT_REMAP.get((int(f), str(u)), int(f))
        for f, u in zip(raw["fac"], raw["unitId"])
    ]
    raw["eff"] = eff
    raw["klass"] = [dom.get(pc) for pc in eff]
    raw = raw[raw["klass"].isin(_CC_CLASSES) & raw["eff"].isin(bench_ids)]
    hoy = _hoy(pd.to_datetime(raw["date"]), raw["hour"].astype(int))
    ok = (hoy >= 0) & (hoy < HOURS)
    raw = raw[ok].copy()
    raw["hoy"] = hoy[ok]
    return (
        raw.groupby("hoy")["grossLoad"]
        .sum()
        .reindex(range(HOURS), fill_value=0.0)
        .to_numpy()
    )


def model_cc_mw(sidecar: dict, year: int, bench: dict[str, dict]) -> np.ndarray:
    """Model CC fleet MW per hour (8760), decoded from the run-payload sidecar."""
    plants = L.load_payload_plants(REPO, sidecar, year, bench)
    out = np.zeros(HOURS)
    for pid, arr in plants.items():
        if bench.get(pid, {}).get("group") in _CC_CLASSES:
            out[: min(len(arr), HOURS)] += arr[:HOURS]
    return out


def _window_mean_gw(mw: np.ndarray, window: tuple[int, int]) -> float:
    """Mean GW across a half-open hour-of-day window over the full year."""
    lo, hi = window
    return float(mw.reshape(HOURS // 24, 24)[:, lo:hi].mean() / 1000.0)


def main() -> None:
    """CLI: print the model-vs-actual CC belly/evening commitment table."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-id", default="2026-07-07-caiso65-seam-envelope-clock")
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    args = ap.parse_args()

    sidecar = {"file": f"frontend/data/backcast/runs/{args.run_id}.js"}
    print(f"CAISO gas-CC (CC_REGULAR+CC_CHP) commitment — model={args.run_id}")
    print(
        f"{'year':4s} | {'belly h9-15':>11s} | {'evening h18-21':>14s}   "
        "(GW online, model / actual / actual-model)"
    )
    for year in args.years:
        bench = L.load_bench(REPO, "CAISO", year)
        m = model_cc_mw(sidecar, year, bench)
        a = actual_cc_mw(year, bench)
        mb, ab = _window_mean_gw(m, BELLY_HOURS), _window_mean_gw(a, BELLY_HOURS)
        me, ae = _window_mean_gw(m, EVENING_HOURS), _window_mean_gw(a, EVENING_HOURS)
        print(
            f"{year:4d} | {mb:4.1f}/{ab:4.1f}/{ab - mb:+4.1f} | "
            f"{me:4.1f}/{ae:4.1f}/{ae - me:+4.1f}"
        )


if __name__ == "__main__":
    main()
