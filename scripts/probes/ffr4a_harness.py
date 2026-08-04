"""FFR-4A: multi-year harness driving the REAL apply_economic_new_entry.

Reproduces the runner's year loop for the entry screen alone: the real ladder
cap (ENTRY_GROWTH_LIMIT_MULTIPLE x prior_max), the real pending-queue netting,
the real step-4.5 pipeline commissioning, and the real prior-max update from
runner.py:1153-1160. Other techs are suppressed with a zero ladder row so the
ISO budget cannot mask the solar cell under study (the same isolation FFR-3V
used analytically).

Run once per arm; the arm is whatever netting the working tree currently has.
"""

from __future__ import annotations

import json
import sys

import numpy as np

sys.path.insert(0, "src")

from market_sim.config.entry_config import (  # noqa: E402
    ENTRY_COD_LAG_DEFAULT_YEARS,
    ENTRY_COD_LAG_YEARS,
    ENTRY_GROWTH_LIMIT_MULTIPLE as K,
)
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.model.capacity import apply_economic_new_entry  # noqa: E402

ISO = "MISO"
TECH = "solar"
SEED_GW = 0.618  # measured, EIA-860 vintage_2020, MISO solar (build_throughput)
FIRST_DECISION_YEAR = 2022
LAST_DECISION_YEAR = 2033
COMMISSION_WINDOW = (2021, 2025)  # FFR-3V's scored additions window


def run(label: str) -> dict:
    config = ScenarioConfig(
        iso=ISO,
        entry_commissioning_lag=True,
        h2_available_year=2099,
        ccs_available_year=2099,
        egs_available_year=2099,
        offshore_wind_available_year=2099,
    )
    prices = np.full(8760, 250.0)  # every tech profitable: caps are the subject
    prior_max_gw = {TECH: SEED_GW}
    pipeline: list[dict] = []
    rows = []
    commissioned_by_year: dict[int, float] = {}

    for year in range(FIRST_DECISION_YEAR, LAST_DECISION_YEAR + 1):
        # --- step 4.5: commission rows whose COD year has arrived (evolve.py) ---
        due = [r for r in pipeline if int(r["cod_year"]) <= year]
        for r in due:
            pipeline.remove(r)
            if r["tech"] != TECH:
                continue
            commissioned_by_year[year] = commissioned_by_year.get(year, 0.0) + float(
                r["mw"]
            )
        pending_before = sum(float(r["mw"]) for r in pipeline if r["tech"] == TECH)

        # --- step 5: the real economic entry screen ---
        caps = {t: 0.0 for t in ("wind", "gas_cc", "gas_ct")}  # isolate the cell
        caps[TECH] = K * prior_max_gw[TECH] * 1000.0
        before = {id(r) for r in pipeline}
        apply_economic_new_entry(
            [],
            prices,
            year,
            config,
            ISO,
            entry_rate_caps_mw=caps,
            entry_pipeline=pipeline,
        )
        decided = sum(
            float(r["mw"])
            for r in pipeline
            if id(r) not in before and r["tech"] == TECH
        )

        rows.append(
            {
                "year": year,
                "pending": round(pending_before, 1),
                "ladder_cap": round(caps[TECH], 1),
                "decided": round(decided, 1),
                "cod": year + ENTRY_COD_LAG_YEARS.get(TECH, ENTRY_COD_LAG_DEFAULT_YEARS),
            }
        )
        # --- runner.py:1153-1160: prior max rises on DECISION-grain builds ---
        if decided / 1000.0 > prior_max_gw[TECH]:
            prior_max_gw[TECH] = decided / 1000.0

    lo, hi = COMMISSION_WINDOW
    return {
        "arm": label,
        "rows": rows,
        "commissioned_in_window_gw": round(
            sum(mw for y, mw in commissioned_by_year.items() if lo <= y <= hi) / 1000.0,
            3,
        ),
        "decisions_2022_2033_gw": round(
            sum(r["decided"] for r in rows) / 1000.0, 3
        ),
        "steady_state_mean_mw": round(
            sum(r["decided"] for r in rows[-4:]) / 4.0, 1
        ),
    }


if __name__ == "__main__":
    out = run(sys.argv[1] if len(sys.argv) > 1 else "unlabelled")
    print(json.dumps(out, indent=1))
