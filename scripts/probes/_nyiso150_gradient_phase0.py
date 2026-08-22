#!/usr/bin/env python3
"""nyiso-150 phase 0 — the zonal-gradient/2025-level object, measured (no LP).

Three measurements on committed artifacts only, backing
``PREREG-nyiso150-gradient-winter-and-reserve-rearm-2026-08-22.md`` §1:

1. The keeper's zone-level annual errors and the annual eqh zonal gradient
   (max−min over the five zones) vs actual, per year — the "no gradient"
   object.
2. The winter event-month table: model vs actual per zone-month, and the
   downstate−Upstate_West spread per gated month (Feb-2023, Dec-2024,
   Feb-2025; Jan-2025 reported) — the gate baselines for W-K3.
3. The construction evaluation at both flag settings of
   ``nyiso_iroquois_winter_spread`` (pure function evaluation, no solve):
   per-zone monthly gas flag-off vs flag-on, the NYC identity (bit-equal
   every month), and annual conservation on the reference zone.

Writes ``results/calibration/_nyiso150_gradient_phase0.json``. Exit 0 always —
this reports, it does not gate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fuel.basis.nyiso import (  # noqa: E402
    nyiso_zonal_gas_offsets,
    nyiso_zonal_gas_ratios_monthly,
)
from market_sim.data.fuel.hubs import iso_hub_monthly_gas_prices  # noqa: E402

KEEPER = REPO / "results/calibration/nyiso149_armF"
REF = REPO / "data/raw/_validation-source/actual_lmp.json"
OUT = REPO / "results/calibration/_nyiso150_gradient_phase0.json"
ZONES = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]
YEARS = (2023, 2024, 2025)
# Gated winter months (W-K3a): the nyiso-82 decisively-fixed three, plus
# Jan-2025 reported-not-gated (Algonquin-ceiling stubbornness known).
GATED_MONTHS = {2023: [2], 2024: [12], 2025: [2]}
REPORTED_MONTHS = {2025: [1, 6, 7, 12], 2024: [1, 7], 2023: [1, 12]}


def _zone_month(df: pd.DataFrame, year: int) -> pd.DataFrame:
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    df = df.copy()
    df["month"] = df["hour"].map(dict(enumerate(idx.month)))
    return df.groupby(["zone", "month"])["price"].mean().unstack("month")


def main() -> None:
    ref = json.loads(REF.read_text())["NYISO"]
    out: dict = {"session": "nyiso-150", "phase": 0, "zones": ZONES}

    # ── 1 + 2: keeper zone errors, gradient, winter tables ──────────────────
    annual: dict = {}
    winter: dict = {}
    for year in YEARS:
        df = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
        df = df[(df["pass"] == "P1") & (df["zone"].isin(ZONES))]
        act = ref[str(year)]["zones"]
        zm = _zone_month(df, year)
        ann_mod = df.groupby("zone")["price"].mean()
        annual[year] = {
            "zones": {
                z: {
                    "model_eqh": round(float(ann_mod[z]), 2),
                    "actual_rt": round(float(act[z]["rt"]), 2),
                    "err_pct": round(
                        100 * (float(ann_mod[z]) - act[z]["rt"]) / act[z]["rt"], 1
                    ),
                }
                for z in ZONES
            },
            "gradient_model": round(
                float(ann_mod[ZONES].max() - ann_mod[ZONES].min()), 2
            ),
            "gradient_actual": round(
                max(act[z]["rt"] for z in ZONES) - min(act[z]["rt"] for z in ZONES), 2
            ),
        }
        months = sorted(set(GATED_MONTHS.get(year, [])) | set(REPORTED_MONTHS.get(year, [])))
        wtab: dict = {}
        for m in months:
            row: dict = {}
            for z in ZONES:
                row[z] = {
                    "model": round(float(zm.loc[z, m]), 1),
                    "actual": round(float(act[z]["rt_mon"][m - 1]), 1),
                }
            uw_m, uw_a = row["Upstate_West"]["model"], row["Upstate_West"]["actual"]
            row["spread_vs_uw"] = {
                z: {
                    "model": round(row[z]["model"] - uw_m, 1),
                    "actual": round(row[z]["actual"] - uw_a, 1),
                }
                for z in ("Capital_Hudson", "NYC", "Long_Island")
            }
            row["gated"] = m in GATED_MONTHS.get(year, [])
            wtab[m] = row
        winter[year] = wtab
    out["annual"] = annual
    out["winter_months"] = winter

    # ── 3: construction evaluation at both flag settings ────────────────────
    cfg_off = ScenarioConfig(iso="NYISO", mode="backcast")
    cfg_on = ScenarioConfig(
        iso="NYISO", mode="backcast", nyiso_iroquois_winter_spread=True
    )
    cons: dict = {}
    for year in YEARS:
        off = iso_hub_monthly_gas_prices(cfg_off, year)
        on = iso_hub_monthly_gas_prices(cfg_on, year)
        ratios = nyiso_zonal_gas_ratios_monthly(cfg_on, year)
        offs = nyiso_zonal_gas_offsets(year)
        nyc_off = off + offs["NYC"]
        nyc_on = on * ratios["NYC"]
        uw_off = off + offs["Upstate_West"]
        uw_on = on * ratios["Upstate_West"]
        cons[year] = {
            "reference_off": [round(float(x), 3) for x in off],
            "reference_on": [round(float(x), 3) for x in on],
            "nyc_off": [round(float(x), 3) for x in nyc_off],
            "nyc_on": [round(float(x), 3) for x in nyc_on],
            "uw_off": [round(float(x), 3) for x in uw_off],
            "uw_on": [round(float(x), 3) for x in uw_on],
            "nyc_identity_max_abs": round(float(np.abs(nyc_on - nyc_off).max()), 6),
            "reference_annual_conservation": round(
                float(np.mean(on) - np.mean(off)), 6
            ),
        }
    out["construction"] = cons
    ok_nyc = all(cons[y]["nyc_identity_max_abs"] < 0.005 for y in YEARS)
    ok_ann = all(abs(cons[y]["reference_annual_conservation"]) < 0.005 for y in YEARS)
    out["construction_checks"] = {"nyc_identity": ok_nyc, "annual_conservation": ok_ann}

    OUT.write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT}")
    for year in YEARS:
        a = annual[year]
        print(
            f"{year}: gradient model {a['gradient_model']} vs actual "
            f"{a['gradient_actual']}; "
            + " ".join(
                f"{z}:{a['zones'][z]['err_pct']:+.1f}%" for z in ZONES
            )
        )
    print(f"construction checks: NYC identity {ok_nyc}, conservation {ok_ann}")


if __name__ == "__main__":
    main()
