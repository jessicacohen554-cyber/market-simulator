"""NWPP-NEXT-25 phase 0 (zero LP): where the served schedule lands, load-share spread vs reporting-member zones.

For each year: the served schedule (envelopes.nwpp_unpriced_residual_interchange, keeper flags) placed
by the load-share spread (keeper) and by nwpp_served_schedule_zone_interchange (the armed key), per
zone, and the shift in each zone's local generation need. Then the keeper's zonal gas against the
member BAs' EIA-930 NG:NG (SNV = NEVP, EAST = PACE). FINDING-nwppnext25-cc-served-schedule-phase0-2026-10-03.md.

Usage: PYTHONPATH=src:. python scripts/probes/_nwppnext25_served_schedule_phase0.py
"""

import numpy as np
import pandas as pd

from market_sim.data.eia930.envelopes import (
    nwpp_served_schedule_zone_interchange,
    nwpp_unpriced_residual_interchange,
)
from market_sim.data.eia930.frames import _eia_hourly_frame_filled
from market_sim.data.eia_loader import load_zonal_shares

ZONES = ["NWPP-NW", "NWPP-OR", "NWPP-INLAND", "NWPP-EAST", "NWPP-SNV"]
H = "results/calibration/nwppnext24_span/hourly/"


def main() -> None:
    """Print the per-zone placement and the zonal gas check."""
    rows = []
    for y in range(2019, 2026):
        res = nwpp_unpriced_residual_interchange(
            y, grid_carried_wind_served=True, plant_basis=True
        )
        w = np.asarray(load_zonal_shares("NWPP", y, ZONES))
        att = nwpp_served_schedule_zone_interchange(y, ZONES, res, w)
        u = pd.read_parquet(
            H + f"unit_marginal_{y}.parquet", columns=["fuel", "zone", "mw"]
        )
        gas = (
            u[u.fuel.isin(["gas_cc", "gas_ct", "gas_st"])].groupby("zone").mw.sum()
            / 1e6
        )
        for i, z in enumerate(ZONES):
            rows.append(
                dict(
                    year=y,
                    zone=z,
                    spread=(w[i] * res).sum() / 1e6,
                    attributed=att[i].sum() / 1e6,
                    model_gas=gas.get(z, 0.0),
                )
            )
        ba = {"NWPP-SNV": "NEVP", "NWPP-EAST": "PACE"}
        for z, b in ba.items():
            f = _eia_hourly_frame_filled(b, y)
            rows[-5 + ZONES.index(z)]["meas_gas_930"] = float(f["NG: NG"].sum()) / 1e6
        assert abs(att.sum() - res.sum()) < 1.0, (
            "column sums must equal the served total"
        )
    df = pd.DataFrame(rows)
    df["shift"] = df.attributed - df.spread  # + = more local generation needed
    print(df.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
