"""PJM-NEXT-12 cards 1-2 (zero LP): does coal SELF-SCHEDULING or coal's MARGINAL share discriminate the years?

Measured side = the PJM IMM (Monitoring Analytics) State of the Market rows curated into
``som-competitive-conduct`` (``iso == PJM``): the share of DA offered coal MW that is must-run
(self-scheduled), coal's share of RT marginal resources, and the coal / gas fuel shares of the
IMM's RT LMP decomposition. Over-run side = PJM-NEXT-11's
audit (a) (``results/phase0/pjm/_pjmnext11_margin_audit.json``): the COAL_BIT energy gap and its
RESPONSE part. Price side = the keeper's committed P1 price vs PJM RT, both divided by the same
daily delivered gas series (as in ``_pjmnext11_bulk_price.py``): the share of hours priced below
an efficient gas CC's fuel cost is the share in which something cheaper than gas must be setting
price. The HR thresholds are REPORTING lines only (a sensitivity trio), never a model input.

The model's zone-hour marginal emission rate blends units across binding constraints and is NOT
a class label; its coal-band share is printed only to show that caveat in numbers.
Writes ``results/phase0/pjm/_pjmnext12_selfsched_marginal.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
from scripts.data.derive_pjm_offer_surface import _pjm_fuel_daily  # noqa: E402
from scripts.lib import clean_io  # noqa: E402

BUNDLE = REPO / "results/calibration/pjmnext8_xf_span"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
AUDIT = REPO / "results/phase0/pjm/_pjmnext11_margin_audit.json"
OUT = REPO / "results/phase0/pjm/_pjmnext12_selfsched_marginal.json"
# Reporting lines (MMBtu/MWh): an efficient F/H-class CC's full-load heat rate sits ~6.3-6.6;
# the trio brackets it so no conclusion hangs on one line.
HR_LINES = (6.0, 6.5, 7.0)
MER_COAL = 0.85  # t/MWh, the same coal band as _pjmnext11_bulk_price.py


def som_rows() -> pd.DataFrame:
    """PJM rows of the curated SOM datatype."""
    d = clean_io.read_clean("som-competitive-conduct", iso="PJM")
    return d[d.iso == "PJM"]


def model_series(y: int) -> pd.DataFrame:
    """Hourly load-weighted keeper P1 price and marginal emission rate."""
    d = pd.read_parquet(BUNDLE / f"hourly/system_{y}.parquet")
    d = d[d["pass"] == "P1"]
    d = d.assign(pw=d.price * d.demand, ew=d.marginal_emission_rate * d.demand)
    g = d.groupby("hour")[["pw", "ew", "demand"]].sum().sort_index()
    return pd.DataFrame({"price": g.pw / g.demand, "mer": g.ew / g.demand})


def main() -> None:
    """Assemble the per-year comparison table."""
    som = som_rows()
    audit = json.loads(AUDIT.read_text())
    act = pd.read_parquet(ACTUAL)
    gas = _pjm_fuel_daily()

    def som_val(y: int, seg: str, metric: str) -> float | None:
        r = som[(som.year == y) & (som.fleet_segment == seg) & (som.metric == metric)]
        return round(float(r.value.iloc[0]), 4) if len(r) else None

    out = {}
    for y in range(2019, 2026):
        m = model_series(y)
        n = len(m)
        a = act[act.year == y].sort_values("hour").rt.to_numpy()[:n]
        days = pd.date_range(f"{y}-01-01", periods=n, freq="h").normalize()
        g = gas.reindex(days).to_numpy(float)
        hr_m, hr_a = m.price.to_numpy() / g, a / g
        mustrun = som_val(y, "steam_coal", "da_offer_mustrun_share")
        if y == 2019:  # fixed + self-committed eco-min = the 2020-21 definition
            mustrun = round(
                som_val(y, "steam_coal", "da_offer_selfsched_fixed_share")
                + som_val(y, "steam_coal", "da_offer_selfsched_ecomin_share"),
                4,
            )
        rec = {
            "c1_gap_twh": audit[str(y)]["gap_twh"],
            "response_part_twh": audit[str(y)]["response_part_twh"],
            "som_coal_mustrun_share": mustrun,
            "som_coal_mustrun_definition": (
                "2019 fixed+selfsched eco-min"
                if y == 2019
                else "eco-min MW of must-run units"
                if y <= 2021
                else "submitted MW of must-run units"
                if y <= 2024
                else "n/a (2025 table redesigned)"
            ),
            "som_coal_rt_marginal_share": som_val(
                y, "coal", "rt_marginal_resource_share"
            ),
            "som_wind_rt_marginal_share": som_val(
                y, "wind", "rt_marginal_resource_share"
            ),
            "som_coal_fuel_lmp_share": som_val(
                y, "coal_fuel", "rt_lmp_component_share"
            ),
            "som_gas_fuel_lmp_share": som_val(y, "gas_fuel", "rt_lmp_component_share"),
            "share_hours_below_gas_cc": {
                f"hr<{h}": {
                    "model": round(float(np.nanmean(hr_m < h)), 3),
                    "actual": round(float(np.nanmean(hr_a < h)), 3),
                }
                for h in HR_LINES
            },
            "model_mer_coal_band_share_all_hours": round(
                float((m.mer >= MER_COAL).mean()), 3
            ),
        }
        out[str(y)] = rec
        print(y, json.dumps(rec), flush=True)
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
