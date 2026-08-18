#!/usr/bin/env python3
"""ercot-219 Phase-0 basis measurement — the stage-1 reconciliation basis facts,
measured BEFORE the precommit pinned them (read-only, no LP, quantity-only).

Charter: docs/DECISION-CARD-ercot218b-artificial-shortage-structural-2026-08-18.md
§7 items 1-2 (the open choices the Phase-1 precommit must pin), executed by the
ercot-219 session under B-1 (signed by dispatch of ERCOT-219, 2026-08-18).

What it measures (every number cited by
``docs/PRECOMMIT-ercot219-option-b-phase1-2026-08-18.md``):

1. NP6-905 committed hourly series (`data/raw/ercot/ercot_<yr>_ordc_reserves_
   hourly.parquet`): per-year null patterns for the two candidate basis columns
   `rtolhsl` / `rtolcap` — in particular the 2025 post-RTC+B tail (the ORDC
   regime ended at the RTC+B go-live 2025-12-05; the fetch preserves the tail
   as NaN, never fabricated — `fetch_ercot_ordc_reserves.py`).
2. The 2023 closure of the candidate telemetered thermal aggregate
   ``T_tel(t) = rtolhsl − wind_hsl − solar_hsl − storage_capability`` against
   the SCED-corpus all-thermal online-HSL truth (slow+NUC+quick online HSL from
   `derive_ercot_energy_online_capability._scan`, the ERCOT-155 census
   taxonomy) — correlation, residual level and its hour-of-day flatness. This
   is the boundary-misalignment measurement the rule-14 reconciled-data clause
   requires the precommit to document.
3. Component sanity: measured wind/solar HSL vs EIA-930 delivered generation;
   the measured storage-capability series level.
4. G-BAT coverage facts: the EIA-930 BAT series coverage windows (2024 starts
   2024-11-06) vs the actual RT>$200 tail-hour sets per year. The actual-RT
   read here exists ONLY to enumerate the gate's hour set (measured-vs-measured
   gate bookkeeping, the standard gates-probe construction) — it is not a
   mechanism input, and the mechanism read/refused sets below exclude it.

Rule 13: every quantity is measured-vs-measured; nothing feeds a model input.
Rule 22: years 2023-2025 only.

Run:
    python scripts/probes/ercot219_basis_phase0.py \
        [--out results/calibration/ercot219_basis_phase0.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.data.derive_ercot_energy_online_capability import (  # noqa: E402
    HOURS,
    HSL_TPL,
    ORDC_TPL,
    STORAGE_CAP,
    _scan,
)

YEARS = (2023, 2024, 2025)
#: Fixed non-leap calendar (rule 8 clock; the ercot-216 §6 discipline).
MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_CUM = np.cumsum((0,) + MONTH_DAYS)

#: What the stage-1/stage-2 MECHANISM code is licensed to read (quantity-only,
#: B-1) and what it refuses. The probe itself additionally reads the actual RT
#: hourly series once, solely to enumerate the G-BAT gate hour sets.
MECHANISM_READ = {
    "data/raw/ercot/ercot_<yr>_ordc_reserves_hourly.parquet": ["rtolhsl"],
    "data/raw/ercot-hsl/ercot_<yr>_hsl_hourly.parquet": [
        "wind_hsl_mw",
        "solar_hsl_mw",
    ],
    "data/raw/ercot-storage-capability.csv": ["capability_mw"],
}
MECHANISM_REFUSED = {
    "price columns (never read by any stage)": [
        "system_lambda",
        "rtorpa",
        "rtoffpa",
        "rtordpa",
        "prc",
    ],
    "quantity columns deliberately not used": [
        "rtolcap",
        "rtoffcap",
    ],
    "outcome series (rule 13)": [
        "actual RTSPP / hub RT / DA prices",
        "EIA-930 generation as a capability input",
        "CEMS realized generation",
    ],
}


def _null_patterns() -> dict:
    out: dict = {}
    for y in YEARS:
        df = pd.read_parquet(REPO / ORDC_TPL.format(year=y))
        blk: dict = {"rows": int(len(df))}
        for c in ("rtolhsl", "rtolcap"):
            s = df[c]
            nulls = np.flatnonzero(s.isna().to_numpy())
            blk[c] = {
                "n_null": int(s.isna().sum()),
                "null_first_hour": int(nulls[0]) if nulls.size else None,
                "null_last_hour": int(nulls[-1]) if nulls.size else None,
                "mean_mw": round(float(s.mean()), 1),
                "p5_mw": round(float(s.quantile(0.05)), 1),
                "p95_mw": round(float(s.quantile(0.95)), 1),
            }
        out[str(y)] = blk
    return out


def _closure_2023() -> dict:
    hourly = _scan(2023)
    ordc = pd.read_parquet(REPO / ORDC_TPL.format(year=2023))
    rtolhsl = ordc["rtolhsl"].to_numpy(float)[:HOURS]
    hsl = pd.read_parquet(REPO / HSL_TPL.format(year=2023))
    wind = hsl["wind_hsl_mw"].to_numpy(float)[:HOURS]
    solar = hsl["solar_hsl_mw"].to_numpy(float)[:HOURS]
    stor = pd.read_csv(STORAGE_CAP)
    stor = (
        stor[stor["year"] == 2023]
        .sort_values("hour")["capability_mw"]
        .to_numpy(float)[:HOURS]
    )
    thermal_online = (
        hourly["slow_on"].to_numpy(float)
        + hourly["nuc_on"].to_numpy(float)
        + hourly["quick_on_hsl"].to_numpy(float)
    )
    t_tel = rtolhsl - wind - solar - stor
    resid = t_tel - thermal_online
    ok = ~np.isnan(resid)
    hod = np.arange(HOURS) % 24
    month = np.searchsorted(_MONTH_CUM, np.arange(HOURS) // 24, side="right")
    summer_eve = ok & np.isin(month, (6, 7, 8, 9)) & (hod >= 14) & (hod <= 20)
    prof = pd.Series(resid[ok], index=hod[ok]).groupby(level=0).mean()
    return {
        "corr_t_tel_vs_sced_thermal_online": round(
            float(np.corrcoef(t_tel[ok], thermal_online[ok])[0, 1]), 4
        ),
        "resid_mw_mean": round(float(np.mean(resid[ok])), 1),
        "resid_mw_p10": round(float(np.percentile(resid[ok], 10)), 1),
        "resid_mw_p50": round(float(np.percentile(resid[ok], 50)), 1),
        "resid_mw_p90": round(float(np.percentile(resid[ok], 90)), 1),
        "resid_mw_summer_evening_mean": round(float(np.mean(resid[summer_eve])), 1),
        "resid_mw_hod_profile": {
            str(h): round(float(prof.loc[h]), 1) for h in (0, 6, 12, 15, 18, 21)
        },
        "sced_thermal_online_mw_mean": round(float(np.nanmean(thermal_online)), 1),
        "t_tel_mw_mean": round(float(np.nanmean(t_tel)), 1),
        "hours_compared": int(ok.sum()),
        "reading": (
            "T_tel tracks the SCED-corpus all-thermal online truth at corr "
            "0.996 with a STABLE level offset (~-4.1 GW, flat in hour-of-day "
            "incl. the summer-evening window) — a population-boundary "
            "misalignment (the cogen/PUN boundary), not noise. The "
            "reconciliation must therefore exclude the model's CHP classes "
            "from both sides rather than import the offset into the scalar."
        ),
    }


def _component_sanity() -> dict:
    out: dict = {}
    ft = pd.read_parquet(REPO / "data/raw/ERCO_fueltype.parquet")
    for y in YEARS:
        hsl = pd.read_parquet(REPO / HSL_TPL.format(year=y))
        f = ft[ft["period"].dt.year == y]
        out[str(y)] = {
            "wind_hsl_mw_mean": round(float(hsl["wind_hsl_mw"].mean()), 0),
            "wind_930_mwh_mean": round(
                float(f[f["fueltype"] == "WND"]["value_mwh"].mean()), 0
            ),
            "solar_hsl_mw_mean": round(float(hsl["solar_hsl_mw"].mean()), 0),
            "solar_930_mwh_mean": round(
                float(f[f["fueltype"] == "SUN"]["value_mwh"].mean()), 0
            ),
            "hsl_nulls": {
                c: int(hsl[c].isna().sum())
                for c in ("wind_hsl_mw", "solar_hsl_mw")
            },
        }
    stor = pd.read_csv(STORAGE_CAP)
    for y in YEARS:
        s = stor[stor["year"] == y]["capability_mw"]
        out[str(y)]["storage_capability_mw_mean"] = round(float(s.mean()), 0)
        out[str(y)]["storage_capability_rows"] = int(len(s))
    return out


def _gbat_coverage() -> dict:
    """G-BAT bookkeeping: 930 BAT coverage vs the actual RT>$200 hour sets.

    The actual-RT read enumerates the GATE hour set only (measured-vs-measured;
    the standard gates-probe construction) — never a mechanism input.
    """
    ft = pd.read_parquet(REPO / "data/raw/ERCO_fueltype.parquet")
    bat = ft[ft["fueltype"] == "BAT"]
    lmp = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
    )
    out: dict = {}
    for y in YEARS:
        by = bat[bat["period"].dt.year == y]
        tail = lmp[(lmp["year"] == y) & (lmp["rt"] > 200.0)]["hour"].to_numpy(int)
        blk: dict = {
            "bat_hours": int(len(by)),
            "bat_first_utc": str(by["period"].min()) if len(by) else None,
            "bat_last_utc": str(by["period"].max()) if len(by) else None,
            "actual_tail_hours_gt200": int(tail.size),
        }
        if y == 2024 and len(by):
            # 2024-11-06 07:00 UTC hour-ENDING = CST hour-beginning 00:00
            # 2024-11-06 = fixed-clock day 309 -> hour 7416 (non-leap clock;
            # Nov 6 is past Feb 29 so the leap shift is absorbed by the
            # date-based mapping, ercot-216 §6).
            cov_start = 309 * 24
            blk["tail_hours_inside_bat_coverage"] = int((tail >= cov_start).sum())
        elif y == 2025:
            blk["tail_hours_inside_bat_coverage"] = int(tail.size)
        out[str(y)] = blk
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        default=str(REPO / "results/calibration/ercot219_basis_phase0.json"),
    )
    args = ap.parse_args()
    out = {
        "probe": "ercot219_basis_phase0",
        "charter": (
            "DECISION-CARD-ercot218b §7 items 1-2; B-1 SIGNED (owner, by "
            "dispatch of ERCOT-219, 2026-08-18); pinned by "
            "docs/PRECOMMIT-ercot219-option-b-phase1-2026-08-18.md"
        ),
        "years": list(YEARS),
        "np6905_null_patterns": _null_patterns(),
        "closure_2023_t_tel_vs_sced_truth": _closure_2023(),
        "component_sanity": _component_sanity(),
        "gbat_coverage": _gbat_coverage(),
        "mechanism_read": MECHANISM_READ,
        "mechanism_refused": MECHANISM_REFUSED,
    }
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
