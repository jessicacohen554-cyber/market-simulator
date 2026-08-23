#!/usr/bin/env python3
"""nyiso-154 phase-0: type the Flynn/Bethlehem start-conduct residual.

Measured on the COMMITTED keeper bundle (`nyiso152_armSE` ≡
`2026-08-22-nyiso-152-duty-complete`) plus the committed actual-LMP series —
no solve, no holdout spend (2023–2025 only).

Four measurements:

1. **The corrected start-conduct table** — model P1 starts / median run vs the
   metered counts (`_nyiso146_perplant_minrun_phase0.json`) for Bethlehem 2539,
   Caithness 56234, Flynn 7314, Poletti 56196. (The nyiso-150 assessment's
   "Flynn (56234)" row was a name/code mislabel — 56234 is Caithness and its
   3/2/4-vs-4/6/8 numbers are Caithness's; Flynn 7314 is a genuine cycler,
   metered 115/78/103 starts, that the model over-cycles 2.0–3.7×.)
2. **Outage vs economic gap decomposition** — Bethlehem's >24 h off-gaps by
   mean availability (cap<50% = outage-driven).
3. **Trough-typing cross** — the naive revealed threshold (p05 of zone price
   over ALL on-hours) is CONTAMINATED by the 146c state floor (floored
   on-hours drag it down); the floor-clean offer estimate is p10 of zone price
   over ABOVE-FLOOR on-hours (dispatch > min_gen and > 20% cap).
4. **The da_horizon control-side capture** — per economic >24 h gap, the
   restart inequality `startup_per_mw > (offer − mean gap price) × 0.523 ×
   gap_h` at the NREL CC band $35–50/MW: how many gaps would the UNCAPPED
   economic bridge (`nyiso_gas_bridge_da_horizon=False`) glue, and the
   predicted start counts.

Output: ``results/calibration/_nyiso154_phase0.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "results" / "calibration" / "nyiso152_armSE"
MINRUN = ROOT / "results" / "calibration" / "_nyiso146_perplant_minrun_phase0.json"
OUT = ROOT / "results" / "calibration" / "_nyiso154_phase0.json"

YEARS = (2023, 2024, 2025)
PLANTS = {2539: "Bethlehem", 56234: "Caithness", 7314: "Flynn", 56196: "Poletti"}
BETH = 2539
ZONE = "Capital_Hudson"
FRAC = 0.523  # measured CC min-load (nyiso_gas_bridge_cc_min_load_frac)
STARTUP_BAND = (35.0, 50.0)  # NREL CC startup $/MW band


def _runs(flag: np.ndarray) -> list[tuple[int, int]]:
    idx = np.flatnonzero(np.diff(np.concatenate(([0], flag.astype(np.int8), [0]))) != 0)
    return list(zip(idx[0::2], idx[1::2]))


def _plant_hourly(year: int, code: int) -> pd.DataFrame:
    return pd.read_parquet(
        B / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "plant_code", "unit_id", "hour", "mw", "cap_mw"],
        filters=[("plant_code", "==", code), ("pass", "==", "P1")],
    )


def main() -> None:
    metered = {
        int(p["plant_code"]): p.get("plant_runs_by_year")
        for p in json.loads(MINRUN.read_text())["plants"]
    }
    out: dict = {"probe": "nyiso154_phase0", "bundle": B.name, "plants": {}, "bethlehem": {}}

    for code, name in PLANTS.items():
        rows = []
        for i, year in enumerate(YEARS):
            df = _plant_hourly(year, code)
            g = df.groupby("hour")[["mw", "cap_mw"]].sum().sort_index()
            s = g["mw"].to_numpy()
            capmax = g["cap_mw"].to_numpy().max()
            r = _runs(s > 0.05 * capmax)
            lens = [e - s0 for s0, e in r]
            m = metered.get(code)
            rows.append({
                "year": year,
                "model_starts": len(r),
                "model_median_run_h": float(np.median(lens)) if lens else 0.0,
                "metered_starts": m[i] if m and i < len(m) else None,
            })
        out["plants"][f"{code}_{name}"] = rows

    for year in YEARS:
        fl = np.load(B / "floors" / f"{year}_P1.npz", allow_pickle=True)
        i = np.flatnonzero(fl["plant_code"] == BETH)
        mg = fl["min_gen"][i].astype(float).sum(axis=0)
        df = _plant_hourly(year, BETH)
        g = df.groupby("hour")[["mw", "cap_mw"]].sum().sort_index()
        s = g["mw"].to_numpy()
        cap = g["cap_mw"].to_numpy()
        capmax = cap.max()
        sysdf = pd.read_parquet(B / "hourly" / f"system_{year}.parquet")
        sysdf = sysdf[(sysdf["pass"] == "P1") & (sysdf["zone"] == ZONE)]
        mp = sysdf.sort_values("hour")["price"].to_numpy()
        on = s > 0.05 * capmax
        above = on & (s > mg + 0.5) & (s > 0.2 * capmax)
        offer = float(np.percentile(mp[above], 10))
        gaps_all = [(s0, e) for s0, e in _runs(~on) if e - s0 > 24]
        econ = [g_ for g_ in gaps_all if cap[g_[0]:g_[1]].mean() >= 0.5 * capmax]
        deficits = [
            max(0.0, offer - float(mp[s0:e].mean())) for s0, e in econ
        ]
        glued = {}
        for su in STARTUP_BAND:
            glued[str(su)] = sum(
                1
                for (s0, e), d in zip(econ, deficits)
                if su > d * FRAC * (e - s0)
            )
        n_starts = len(_runs(on))
        out["bethlehem"][str(year)] = {
            "starts": n_starts,
            "offer_est_above_floor_p10": offer,
            "gaps_gt24h": len(gaps_all),
            "gaps_gt24h_outage": len(gaps_all) - len(econ),
            "gaps_gt24h_economic": len(econ),
            "gap_deficit_per_mwh": {
                "p50": float(np.percentile(deficits, 50)) if deficits else 0.0,
                "p90": float(np.percentile(deficits, 90)) if deficits else 0.0,
            },
            "glued_at_startup_band": glued,
            "predicted_starts_uncapped": {
                su: n_starts - n for su, n in glued.items()
            },
        }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
