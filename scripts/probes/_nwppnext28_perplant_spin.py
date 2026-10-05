"""NWPP-NEXT-28 zero-LP check: per-plant online spin available at keeper dispatch vs BAL-002 spin requirement.

For each zone-hour, on keeper 2026-10-03-nwpp-next-27-path76 P1 dispatch (``unit_marginal``), the spin a pool
can back under ``_nwpp_design``'s rows is ``min(cap - P, rho * P, ramp10 * cap)``: per thermal (plant, fuel)
pool, zone-pooled for hydro. Under the old (zone, fuel-class) pooling, the same terms are summed before the min,
so idle plants' capacity counted. Reports the spin shortfall (TWh) the LP must close by re-dispatch in each layout.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from market_sim.config.paths import REPO_ROOT
from market_sim.data.eia930.envelopes import nwpp_ba_contingency_basis
from market_sim.data.fleet import RAMP10_FRAC_BY_FUEL, RAMP10_FRAC_BY_GROUP
from market_sim.data.online_reserve_rho import load_online_rho
from market_sim.model.reserves.spec import (
    BAL002_WECC_GEN_FRAC,
    BAL002_WECC_LOAD_FRAC,
    BAL002_WECC_SPIN_SHARE,
    NWPP_HYDRO_RAMP10_FRAC,
)

ZONES = ["NWPP-NW", "NWPP-OR", "NWPP-INLAND", "NWPP-EAST", "NWPP-SNV"]
BUNDLE = REPO_ROOT / "results/calibration/nwppnext27_span/hourly"


def pool_spin(g: pd.DataFrame, rho: float) -> np.ndarray:
    """Spin a set of pools can back, hourly: sum over pools of min(cap - P, rho P, ramp)."""
    a = g.groupby(["pool", "hour"], observed=True).agg(
        mw=("mw", "sum"), cap=("cap_mw", "sum"), ramp=("ramp", "sum")
    )
    s = np.minimum(np.minimum(a.cap - a.mw, rho * a.mw), a.ramp).clip(lower=0)
    return s.groupby(level="hour").sum().reindex(range(8760), fill_value=0).to_numpy()


def main() -> None:
    """Run 2019 and 2022-2025 and write the JSON."""
    rho = load_online_rho("NWPP", "nwpp_spin").rho_used
    out = {}
    for y in (2019, 2022, 2023, 2024, 2025):
        um = pd.read_parquet(BUNDLE / f"unit_marginal_{y}.parquet")
        um = um[
            (um["pass"] == "P1")
            & um.fuel.isin(sorted(set(RAMP10_FRAC_BY_FUEL) | {"hydro"}))
        ].copy()
        um["frac"] = [
            NWPP_HYDRO_RAMP10_FRAC
            if f == "hydro"
            else RAMP10_FRAC_BY_GROUP.get(str(gp), RAMP10_FRAC_BY_FUEL.get(f, 0.0))
            for f, gp in zip(um.fuel.astype(str), um.plant_group.astype(str))
        ]
        um["ramp"] = um.frac * um.cap_mw
        load, gen = nwpp_ba_contingency_basis(y, ZONES)
        spin_req = BAL002_WECC_SPIN_SHARE * (
            BAL002_WECC_LOAD_FRAC * load + BAL002_WECC_GEN_FRAC * gen
        )
        for z, zone in enumerate(ZONES):
            g = um[um.zone == zone].copy()
            hyd = g.fuel.astype(str) == "hydro"
            g["pool"] = np.where(
                hyd, "hydro", g.plant_code.astype(str) + "|" + g.fuel.astype(str)
            )
            per_plant = pool_spin(g, rho)
            g["pool"] = g.fuel.astype(str)
            pooled = pool_spin(g, rho)
            r = spin_req[z]
            out[f"{zone}|{y}"] = {
                "spin_req_mw": round(float(r.mean()), 1),
                "perplant_avail_mw": round(float(per_plant.mean()), 1),
                "pooled_avail_mw": round(float(pooled.mean()), 1),
                "perplant_short_twh": round(
                    float(np.clip(r - per_plant, 0, None).sum()) / 1e6, 3
                ),
                "pooled_short_twh": round(
                    float(np.clip(r - pooled, 0, None).sum()) / 1e6, 3
                ),
                "perplant_short_hours": int((per_plant < r).sum()),
            }
            print(zone, y, out[f"{zone}|{y}"])
    (REPO_ROOT / "results/phase0/nwpp/_nwppnext28_perplant_spin.json").write_text(
        json.dumps(out, indent=1)
    )


if __name__ == "__main__":
    main()
