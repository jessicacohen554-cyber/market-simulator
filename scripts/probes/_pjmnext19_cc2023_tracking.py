"""PJM-NEXT-19 card 2 (zero LP): why the keeper's CC_REGULAR is flat 2023 -> 2024 while actual rises.

Reads committed artifacts only:

1. **Zonal split** — keeper CC_REGULAR TWh by zone (``unit_marginal_<y>``) vs the C1 bench
   per-plant EIA-923 energy (``frontend/data/backcast/bench/PJM/<y>.json.gz``), plus the
   keeper's capacity-weighted CC offer (``mc``) and capacity factor by zone.
2. **Energy identity, year over year** — NEXT-16's ``model gen - classFull = export
   shortfall + losses + U_a`` (``_pjmnext16_fleet_boundary.json``), differenced 2023 -> 2024.
3. **Gas operand** — the EIA-923 own-receipt gas price of the CC plants that report one
   (quantity-weighted, by zone) against Henry Hub and the IMM's Platts monthly spot
   series (``som-competitive-conduct``: east / production / west gas), annual means.
4. **Benchmark gas vs EIA-930 gas, and vs CAMPD** — ``classFull`` gas families, the bench
   per-plant 923 sum and CAMPD sum, against the bench's own ``e930`` gas row.

Writes ``results/phase0/pjm/_pjmnext19_cc2023_tracking.json``.
Run: ``python3 scripts/probes/_pjmnext19_cc2023_tracking.py``
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
HOURLY = REPO / "results/calibration/pjmnext16_A_span/hourly"
BENCH = REPO / "frontend/data/backcast/bench/PJM"
F923 = REPO / "data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet"
SOM = REPO / "data/raw/som-competitive-conduct/som_competitive_conduct.csv"
HH = REPO / "data/raw/gas-prices/henry_hub_monthly.csv"
BOUNDARY = REPO / "results/phase0/pjm/_pjmnext16_fleet_boundary.json"
OUT = REPO / "results/phase0/pjm/_pjmnext19_cc2023_tracking.json"
YEARS = range(2019, 2026)
T = 8760
GAS_GROUPS = ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_CHP", "ST_GAS")


def _bench(y: int) -> dict:
    """The C1 bench payload for ``y``."""
    return json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]


def _pid(k: str) -> int:
    """Plant code from a bench plant key."""
    return int(str(k).split(":")[0])


def zonal_split() -> dict:
    """Keeper vs bench CC_REGULAR by zone, with offer level and capacity factor."""
    out = {}
    for y in YEARS:
        b = _bench(y)["plants"]
        act: dict[str, float] = {}
        for k, p in b.items():
            if p.get("group") == "CC_REGULAR":
                z = p.get("zone")
                act[z] = act.get(z, 0.0) + float(p.get("e_ann") or 0.0)
        cols = ["plant_group", "zone", "mc", "cap_mw", "mw", "hour"]
        u = pd.read_parquet(HOURLY / f"unit_marginal_{y}.parquet", columns=cols)
        u = u[
            (u.plant_group.astype(str) == "CC_REGULAR") & (u.hour < T) & (u.cap_mw > 0)
        ]
        rows = {}
        for z, x in u.groupby(u.zone.astype(str)):
            rows[z] = {
                "model_twh": round(float(x.mw.sum()) / 1e6, 2),
                "actual_twh": round(act.get(z, 0.0), 2),
                "mc_capw": round(float(np.average(x.mc, weights=x.cap_mw)), 2),
                "cf": round(float(x.mw.sum() / x.cap_mw.sum()), 3),
            }
        out[str(y)] = rows
    return out


def identity_delta() -> dict:
    """NEXT-16 energy identity terms and their 2023 -> 2024 change."""
    d = json.loads(BOUNDARY.read_text())["years"]
    keys = ("model_gen", "classFull", "d_gen", "d_export", "losses_model", "U_a")
    rows = {y: {k: d[y][k] for k in keys} for y in d}
    rows["delta_2023_2024"] = {k: round(d["2024"][k] - d["2023"][k], 2) for k in keys}
    return rows


def gas_operand(cc_zone: dict[int, str]) -> dict:
    """EIA-923 own-receipt CC gas price by zone vs Henry Hub and IMM spot."""
    f = pd.read_parquet(F923)
    f = f[
        (f.fuel_group == "Natural Gas") & f.plant_id.isin(cc_zone) & f.year.isin(YEARS)
    ]
    f = f.assign(zone=f.plant_id.map(cc_zone))
    own = (
        f.groupby(["zone", "year"])
        .apply(lambda x: np.average(x.price_per_mmbtu, weights=x.quantity))
        .unstack()
    )
    n = f.groupby(["zone", "year"]).plant_id.nunique().unstack()
    hh = pd.read_csv(HH).groupby("year").price_usd_mmbtu.mean()
    s = pd.read_csv(SOM)
    s = s[
        (s.iso == "PJM")
        & (s.metric == "spot_price_digitized_usd_per_mmbtu")
        & s.period.str.startswith("month_")
    ]
    spot = s.pivot_table(index="year", columns="fleet_segment", values="value")
    out = {}
    for y in YEARS:
        out[str(y)] = {
            "henry_hub": round(float(hh[y]), 2),
            "imm_east_gas": round(float(spot.loc[y, "east_gas"]), 2),
            "imm_production_gas": round(float(spot.loc[y, "production_gas"]), 2),
            "imm_west_gas": round(float(spot.loc[y, "west_gas"]), 2),
            "own_923_by_zone": {
                z: {"price": round(float(own.loc[z, y]), 2), "plants": int(n.loc[z, y])}
                for z in own.index
                if y in own.columns and np.isfinite(own.loc[z, y])
            },
        }
    return out


def gas_basis() -> dict:
    """classFull gas vs EIA-930 gas, per-plant 923 sum and CAMPD sum."""
    out = {}
    for y in YEARS:
        b = _bench(y)
        cf = sum(b["classFull"].get(g, 0.0) for g in GAS_GROUPS)
        e = c = 0.0
        for p in b["plants"].values():
            if p.get("group") in GAS_GROUPS:
                e += float(p.get("e_ann") or 0.0)
                c += float(p.get("c_ann") or 0.0)
        out[str(y)] = {
            "classFull_gas": round(cf, 1),
            "e930_gas": round(float(b["e930"]["gas"]), 1),
            "classFull_minus_e930": round(cf - float(b["e930"]["gas"]), 1),
            "bench_plants_923_gas": round(e, 1),
            "bench_plants_campd_gas": round(c, 1),
        }
    return out


def main() -> None:
    """Write the card-2 artifact."""
    cc_zone: dict[int, str] = {}
    for y in YEARS:
        for k, p in _bench(y)["plants"].items():
            if p.get("group") == "CC_REGULAR":
                cc_zone[_pid(k)] = p.get("zone")
    res = {
        "what": "PJM-NEXT-19 card 2: CC_REGULAR 2023 -> 2024 tracking. ZERO LP.",
        "zonal_split": zonal_split(),
        "identity": identity_delta(),
        "gas_operand": gas_operand(cc_zone),
        "gas_basis": gas_basis(),
    }
    OUT.write_text(json.dumps(res, indent=1, sort_keys=True))
    zs = res["zonal_split"]
    for y in ("2023", "2024"):
        print(
            y, {z: round(v["model_twh"] - v["actual_twh"], 1) for z, v in zs[y].items()}
        )
    print(json.dumps(res["identity"]["delta_2023_2024"]))
    for y, v in res["gas_operand"].items():
        dom = v["own_923_by_zone"].get("PJM_Dominion", {}).get("price")
        print(y, v["henry_hub"], v["imm_east_gas"], dom)


if __name__ == "__main__":
    main()
