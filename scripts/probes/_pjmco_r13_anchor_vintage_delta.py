"""PJM close-out wave 1, R-13 retest phase 0: per-year anchor delta (ZERO LP).

``gas_offer_margin_anchor_vintage`` (pjm-169 F4, cell R) resolves the PJM
gas-offer margin anchor to the solve year's own delivered-gas mean instead of
the frozen 2023-2025 window mean ``GAS_OFFER_MARGIN_ANCHOR_BY_ISO['PJM']``.
This probe computes, for every keeper year 2019-2025, the resolved anchor the
arm would use (mean of ``_gas_series`` on the PJM keeper gas recipe with that
year's measured Henry Hub, exactly as ``derive_gas_offer_margin_anchor``
builds it) and the pre-solve algebraic offer shift
``markup_hr x (anchor_year - anchor_frozen)`` using pjm-169 section 7.3's
median ``markup_hr`` (2.804 MMBtu/MWh). Writes
``results/phase0/pjm/_pjmco_r13_anchor_vintage_delta.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "data"))

from market_sim.config.constants import (  # noqa: E402
    GAS_OFFER_MARGIN_ANCHOR_BY_ISO,
    HOURS_PER_YEAR,
)
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fuel.trajectories import _gas_series  # noqa: E402

from derive_gas_offer_margin_anchor import GAS_SERIES_FLAGS  # noqa: E402

BUNDLE = ROOT / "results" / "calibration" / "pjmnext16_A_span"
OUT = ROOT / "results" / "phase0" / "pjm" / "_pjmco_r13_anchor_vintage_delta.json"
#: pjm-169 PRECOMMIT section 7.3: median gas-tranche markup at the frozen anchor.
MARKUP_HR_PJM169 = 2.804


def main() -> None:
    """Compute the per-year resolved anchor and predicted median offer shift."""
    frozen = float(GAS_OFFER_MARGIN_ANCHOR_BY_ISO["PJM"])
    base = ScenarioConfig(
        iso="PJM", mode="backcast", hours=HOURS_PER_YEAR, **GAS_SERIES_FLAGS["PJM"]
    )
    rows = {}
    for year in range(2019, 2026):
        rc = json.loads((BUNDLE / f"run_config_{year}.json").read_text())
        hh = float(rc["scenario_config"]["gas_price_override"])
        series = _gas_series(base.with_overrides(gas_price_override=hh), year, HOURS_PER_YEAR)
        mean = float(np.nanmean(series))
        rows[year] = {
            "henry_hub": hh,
            "resolved_anchor": round(mean, 4),
            "frozen_anchor": frozen,
            "anchor_delta": round(mean - frozen, 4),
            "predicted_median_gas_offer_shift_usd_mwh": round(
                MARKUP_HR_PJM169 * (mean - frozen), 2
            ),
        }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"what": __doc__.splitlines()[0], "markup_hr": MARKUP_HR_PJM169, "years": rows}, indent=1))
    for y, r in rows.items():
        print(y, r)


if __name__ == "__main__":
    main()
