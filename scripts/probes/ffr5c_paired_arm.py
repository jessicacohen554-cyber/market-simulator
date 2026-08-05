"""FFR-5C: paired-arm measurement of ``entry_pipeline_aware_signal`` (E-1 half).

Same instrument as ``scripts/probes/ffr4a_harness.py`` -- the REAL
``apply_economic_new_entry``, the real step-4.5 pipeline commissioning
(``evolve.py``) and the real prior-max ladder update (``runner.py``) -- with
one difference that is the whole point of this lane: the arm is selected by the
SHIPPED ``ScenarioConfig`` field, not by editing source. FFR-4A had to delete
the netting terms by hand and ``git checkout --`` afterwards; the arms here are
two configs of one tree, so the measurement is reproducible from a clean
checkout.

Both measured cells from FFR-4A §5 are run:

* MISO **solar** -- the ladder-first cell (seed 0.618 GW ⇒ ladder 1,236 MW/yr
  below the 6,000 MW/yr static cap), where the netting freezes the ratchet;
* MISO **wind** -- the static-cap-first cell (seed 4.367 GW ⇒ ladder 8,734
  MW/yr above the 4,000 MW/yr static cap), where the ladder never binds and the
  netting shows up instead as the ``C, 0, C, 0`` alternation whose mean is
  ``C / L``.

Other techs are suppressed with a zero ladder row so MISO's shared 10 GW/yr ISO
budget cannot mask the cell under study (FFR-4A's isolation, unchanged).

NOTE (scope): this harness forces every tech profitable with a flat high price,
so every number it prints is a **cap CEILING the arithmetic permits, not a
build**. It measures the E-1 half only; the E-2 half changes the price signal,
which this instrument bypasses by construction (its price is exogenous). E-2 is
covered by ``tests/unit/model/test_entry_pipeline_aware_signal.py``.

Usage:
    uv run python scripts/probes/ffr5c_paired_arm.py
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
# Measured EIA-860 vintage_2020 seeds (data.build_throughput), FFR-4A §2.
SEEDS_GW = {"solar": 0.618, "wind": 4.367}
FIRST_DECISION_YEAR = 2022
LAST_DECISION_YEAR = 2033
COMMISSION_WINDOW = (2021, 2025)  # FFR-3V's scored additions window


def run(tech: str, armed: bool) -> dict:
    """Drive the real entry screen for one tech under one arm.

    Args:
        tech: ``"solar"`` or ``"wind"`` -- the MISO cell under study.
        armed: ``entry_pipeline_aware_signal``. False reproduces the shipped
            path (FFR-4A Arm 0); True is the relocated guard (FFR-4A Arm B).

    Returns:
        The decision series plus the summary statistics FFR-4A §5.2 reports.
    """
    config = ScenarioConfig(
        iso=ISO,
        entry_commissioning_lag=True,
        entry_pipeline_aware_signal=armed,
        h2_available_year=2099,
        ccs_available_year=2099,
        egs_available_year=2099,
        offshore_wind_available_year=2099,
    )
    prices = np.full(8760, 250.0)  # every tech profitable: caps are the subject
    prior_max_gw = {tech: SEEDS_GW[tech]}
    pipeline: list[dict] = []
    rows = []
    commissioned_by_year: dict[int, float] = {}

    for year in range(FIRST_DECISION_YEAR, LAST_DECISION_YEAR + 1):
        # --- step 4.5: commission rows whose COD year has arrived (evolve.py) ---
        due = [r for r in pipeline if int(r["cod_year"]) <= year]
        for r in due:
            pipeline.remove(r)
            if r["tech"] != tech:
                continue
            commissioned_by_year[year] = commissioned_by_year.get(year, 0.0) + float(
                r["mw"]
            )
        pending_before = sum(float(r["mw"]) for r in pipeline if r["tech"] == tech)

        # --- step 5: the real economic entry screen ---
        caps = {t: 0.0 for t in ("wind", "solar", "gas_cc", "gas_ct")}
        caps[tech] = K * prior_max_gw[tech] * 1000.0
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
            if id(r) not in before and r["tech"] == tech
        )

        rows.append(
            {
                "year": year,
                "pending": round(pending_before, 1),
                "ladder_cap": round(caps[tech], 1),
                "decided": round(decided, 1),
                "cod": year
                + ENTRY_COD_LAG_YEARS.get(tech, ENTRY_COD_LAG_DEFAULT_YEARS),
            }
        )
        # --- runner.py prior-max update: rises on DECISION-grain builds ---
        if decided / 1000.0 > prior_max_gw[tech]:
            prior_max_gw[tech] = decided / 1000.0

    lo, hi = COMMISSION_WINDOW
    return {
        "iso": ISO,
        "tech": tech,
        "arm": "armed (entry_pipeline_aware_signal)" if armed else "shipped",
        "rows": rows,
        "series_2022_2026_mw": [r["decided"] for r in rows[:5]],
        "commissioned_in_window_gw": round(
            sum(mw for y, mw in commissioned_by_year.items() if lo <= y <= hi) / 1000.0,
            3,
        ),
        "decisions_2022_2033_gw": round(sum(r["decided"] for r in rows) / 1000.0, 3),
        "steady_state_mean_mw": round(sum(r["decided"] for r in rows[-4:]) / 4.0, 1),
    }


if __name__ == "__main__":
    out = [run(tech, armed) for tech in ("solar", "wind") for armed in (False, True)]
    print(json.dumps(out, indent=1))
