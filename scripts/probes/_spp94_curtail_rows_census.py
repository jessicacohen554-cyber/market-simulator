"""SPP-94 zero-LP census: the 2020 / 2021 published wind-curtailment rows.

Input side ONLY — reads no model output (no bundle, no sidecar, no payload).
For each SPP year it rebuilds the keeper's wind upper bound two ways through the
production seam (``renewables._oversupply_uncurtailed_cf``, the construction the
keeper arms via ``vre_curtailment_oversupply_allocation``, with
``vre_reference_rate_year_own``):

* CONTROL — the committed ``spp_wind_curtailment_annual.csv`` (2020 / 2021 carry
  no ``avg_hourly_curtailment_mw`` row, so they fall back to the 2023-25
  reference mean);
* ARM — the same table plus the two rows SPP-94 transcribed from the SPP MMU
  Annual State of the Market reports (2020 = 244 MW, ASOM 2022 p. 53;
  2021 = 725 MW, ASOM 2021 p. 60).

and reports, per year: the rate each side uses, the annual headroom energy
(potential - delivered), the fill level, the allocated-hour count, and the
maximum hourly change in wind potential inside the 500 highest-net-load hours
(the pre-solve adequacy leg: removing headroom that was only ever placed in
low-net-load hours cannot tighten a peak hour).

Run: ``python scripts/probes/_spp94_curtail_rows_census.py`` (needs DATA
PROFILE spp). Writes ``docs/handoffs/spp94/census.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.paths import REPO_ROOT
from market_sim.data import renewables as R

YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
# The two rows this lane transcribed (PRECOMMIT-spp-94 §1). Average-MW basis,
# identical to the committed 2019 / 2022-2025 rows.
ARM_ROWS = {2020: 244.0, 2021: 725.0}
OUT = REPO_ROOT / "docs" / "handoffs" / "spp94" / "census.json"


def _rates_with(extra: dict[int, float]) -> dict[int, float]:
    """Return the per-year rate map with ``extra`` curtailment rows added."""
    table = pd.read_csv(R._SPP_WIND_CURTAILMENT_ANNUAL)
    deliv = {
        int(r.year): float(r.value)
        for r in table.itertuples()
        if r.metric == R._SPP_DELIVERED_METRIC
    }
    curt = {
        int(r.year): float(r.value)
        for r in table.itertuples()
        if r.metric == R._SPP_CURTAILED_METRIC
    }
    curt.update(extra)
    return {y: curt[y] / (deliv[y] + curt[y]) for y in curt if y in deliv}


def _monthly_capacity(year: int, zone_names: list[str]) -> np.ndarray:
    """Return the EIA-860 ``(n_zones, 12)`` wind capacity (census grade: the
    loader's default vintage; it only caps the per-hour headroom)."""
    return R._eia860_monthly_capacity("SPP", "wind", zone_names, year)


def main() -> None:
    """Build both bounds per year and write the census."""
    iso_cfg = get_iso_config("SPP")
    arm_rates = _rates_with(ARM_ROWS)
    ctl_rates = _rates_with({})
    orig = R._spp_wind_annual_rates
    out: dict[str, dict] = {}
    from market_sim.data.eia930.demand import load_demand

    for year in YEARS:
        cap = _monthly_capacity(year, [z.name for z in iso_cfg.zones])
        rows = {}
        for side, rates in (("control", ctl_rates), ("arm", arm_rates)):
            R._spp_wind_annual_rates = lambda r=rates: dict(r)  # noqa: E731
            try:
                rate = R._curtailment_rate_for_year("SPP", "wind", year, True)
                cf = R._oversupply_uncurtailed_cf("SPP", year, "wind", cap, iso_cfg, True)
            finally:
                R._spp_wind_annual_rates = orig
            potential = (cf * cap.sum(axis=0)[R._hour_to_month_index(R.HOURS_PER_YEAR)]
                         if cf is not None else None)
            rows[side] = {"rate": rate[0], "rate_year": rate[1], "potential": potential}
        gen = R.load_eia_hourly_renewable_gen("SPP", year)
        delivered = np.asarray(gen["wind"], dtype=float)
        nl = load_demand("SPP", year, iso_cfg).sum(axis=0).astype(float)
        for other in ("wind", "solar"):
            if other in gen:
                nl = nl - np.asarray(gen[other], dtype=float)
        top = np.argsort(nl)[-500:]
        pc, pa = rows["control"]["potential"], rows["arm"]["potential"]
        out[str(year)] = {
            "rate_control": round(rows["control"]["rate"], 6),
            "rate_control_source_year": rows["control"]["rate_year"],
            "rate_arm": round(rows["arm"]["rate"], 6),
            "rate_arm_source_year": rows["arm"]["rate_year"],
            "delivered_twh": round(delivered.sum() / 1e6, 4),
            "headroom_control_twh": round((pc - delivered).clip(min=0).sum() / 1e6, 4),
            "headroom_arm_twh": round((pa - delivered).clip(min=0).sum() / 1e6, 4),
            "delta_potential_twh": round((pa - pc).sum() / 1e6, 4),
            "hours_headroom_control": int(((pc - delivered) > 1e-6).sum()),
            "hours_headroom_arm": int(((pa - delivered) > 1e-6).sum()),
            "max_abs_delta_mw_top500_netload": round(float(np.abs(pa - pc)[top].max()), 3),
            "max_abs_delta_mw_all": round(float(np.abs(pa - pc).max()), 3),
            "byte_identical": bool(np.array_equal(pa, pc)),
        }
        print(year, out[str(year)])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
