"""PJM-NEXT-20 card 1d (zero LP): the keeper's own COAL_* ladder read at actual RT.

Per coal unit-hour (keeper P1, ``unit_marginal_<y>``): available MW whose model offer
``mc`` <= PJM actual RT (``Mrt``), and <= the unit's own zone price (``Mp``, what the LP
clears). Year shares of available coal MW, set beside PJM's own LONG_RUN offers read at
the actual DA price (NEXT-11 ``D/E``) and the C1 bench energy. If Mrt sits far above D/E
in the over-run years only, the miss is the keeper's coal offer level against PJM's.
Also: coal MWh the keeper dispatches from tranches priced above actual RT (the price-gap
volume), and the median within-plant $ spread of the econ tranches (ladder steepness).

Writes ``results/phase0/pjm/_pjmnext20_coal_ladder_at_rt.json``.
Run: ``python3 scripts/probes/_pjmnext20_coal_ladder_at_rt.py``
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
HOURLY = REPO / "results/calibration/pjmnext16_A_span/hourly"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
OUT = REPO / "results/phase0/pjm/_pjmnext20_coal_ladder_at_rt.json"
T = 8760
# NEXT-11 FINDING §1 (PJM LONG_RUN offers at actual DA LMP, D/E), quoted for the table.
NEXT11_D_OVER_E = {
    2019: 0.55,
    2020: 0.45,
    2021: 0.60,
    2022: 0.57,
    2023: 0.43,
    2024: 0.49,
    2025: 0.63,
}


SPREAD_STRIDE = (
    97  # hour sample for the econ-ladder spread (every 97th hour, ~90 hours/yr)
)


def _econ_spread(u: pd.DataFrame) -> float:
    """Median within-plant $ spread (max - min mc) across the econ tranches, sampled hours."""
    e = u[(u.hour % SPREAD_STRIDE == 0) & (u.cap_mw > 0)]
    e = e[e.unit_id.astype(str).str.contains(r"_econ", regex=True)]
    g = e.groupby(["plant_code", "hour"], observed=True).mc
    sp = (g.max() - g.min())[g.size() >= 2]
    return round(float(sp.median()), 1)


def main() -> None:
    """Every year."""
    out: dict = {
        "what": "PJM-NEXT-20 card 1d: keeper coal ladder at actual RT. ZERO LP."
    }
    act = pd.read_parquet(ACTUAL)
    for y in range(2019, 2026):
        cols = [
            "plant_code",
            "unit_id",
            "plant_group",
            "zone",
            "hour",
            "mw",
            "cap_mw",
            "mc",
        ]
        u = pd.read_parquet(HOURLY / f"unit_marginal_{y}.parquet", columns=cols)
        u = u[u.plant_group.astype(str).str.startswith("COAL") & (u.hour < T)]
        s = pd.read_parquet(
            HOURLY / f"system_{y}.parquet", columns=["zone", "hour", "price"]
        )
        u = u.merge(s, on=["zone", "hour"], how="left")
        rt = act[act.year == y].sort_values("hour").rt.to_numpy()[:T]
        h = u.hour.to_numpy()
        cap, mc, mw = u.cap_mw.to_numpy(), u.mc.to_numpy(), u.mw.to_numpy()
        e = cap.sum()
        r = {
            "avail_twh": round(float(e) / 1e6, 1),
            "model_twh": round(float(mw.sum()) / 1e6, 1),
            "model_loading": round(mw.sum() / e, 3),
            "Mp_ladder_at_model_price": round(
                cap[mc <= u.price.to_numpy()].sum() / e, 3
            ),
            "Mrt_ladder_at_actual_rt": round(cap[mc <= rt[h]].sum() / e, 3),
            "next11_pjm_offers_D_over_E": NEXT11_D_OVER_E[y],
            "econ_ladder_spread_usd": _econ_spread(u),
            "price_gap_tranche_twh": round(float(mw[mc > rt[h]].sum()) / 1e6, 1),
            "price_gap_tranche_twh_rt_lt_25": round(
                float(mw[(mc > rt[h]) & (rt[h] < 25)].sum()) / 1e6, 1
            ),
        }
        r = {
            k: (float(v) if not isinstance(v, (int, str)) else v) for k, v in r.items()
        }
        out[str(y)] = r
        print(y, r)
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
