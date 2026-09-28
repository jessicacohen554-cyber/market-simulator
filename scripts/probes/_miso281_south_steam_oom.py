#!/usr/bin/env python3
"""miso-281 phase 0 (ZERO LP): how much MISO-South gas-steam energy ran OUT OF MERIT?

Reads the per-unit frames written by ``_miso281_south_steam_2019.py`` (the
keeper's fleet-only rebuild) and joins, per MISO-South ST_GAS plant:

* EIA-923 Page 1 net generation and fuel (prime mover ST, fuel NG);
* the keeper's committed run payload (plant model TWh; a plant key that is not
  class-split also carries its CC units, so plant ``model`` is reported but the
  price-taker ``attain`` of the ST_GAS units is the comparison used);
* CEMS hourly gross load and heat input of the plant's gas-fired steam units;
* the measured MISO hub RT LMP of the plant's state hub (LA -> LOUISIANA.HUB,
  MS -> MS.HUB, AR -> ARKANSAS.HUB, TX -> TEXAS.HUB).

A plant-hour is OUT OF MERIT when the measured hub LMP is below the plant's own
measured marginal cost: hourly net heat rate (CEMS heat input / CEMS gross x
the plant's EIA-923 net/gross ratio) x the model's delivered gas for the plant
+ the model's non-fuel offer component. Two sensitivities drop the non-fuel
component and add a $5/MWh nodal allowance to the hub price.

Rule 13: nothing here is fed back into a solve; it classifies measured conduct.

Usage::

    uv run python scripts/probes/_miso281_south_steam_oom.py --in-dir X --years 2019 2023 --out J
"""

from __future__ import annotations

import argparse
import base64
import glob
import gzip
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

KEEPER_ID = "2026-09-28-miso-280-splitremap"
PAYLOAD = REPO / f"frontend/data/backcast/runs/{KEEPER_ID}.js"
E923 = REPO / "data/raw/eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv"
HUB = {"LA": "LOUISIANA.HUB", "MS": "MS.HUB", "AR": "ARKANSAS.HUB", "TX": "TEXAS.HUB"}
NODAL_ALLOWANCE = (
    5.0  # $/MWh, a deliberately generous hub-to-node sensitivity, not a model input
)


def plant_table(in_dir: Path, year: int, payload: dict) -> pd.DataFrame:
    """ST_GAS plants of the keeper fleet with EIA-923 actuals and offer components."""
    u = pd.read_parquet(in_dir / f"units_{year}.parquet")
    st = u[u.group == "ST_GAS"].copy()
    st["adder"] = st.mc_mean - st.heat_rate * st.fuel_price_mean
    e = pd.read_csv(E923)
    e = e[(e.year == year) & (e.prime_mover == "ST") & (e.fuel_type == "NG")]
    act = e.groupby("plant_id").net_generation_mwh.sum() / 1e6
    pl = payload["years"][str(year)]["plants"]

    def wmean(x: pd.DataFrame, c: str) -> float:
        return float((x[c] * x.pmax).sum() / x.pmax.sum())

    rows = []
    for (pc, zone), x in st.groupby(["plant_code", "zone"]):
        key = f"{pc}:ST_GAS" if f"{pc}:ST_GAS" in pl else str(pc)
        rows.append(
            {
                "plant_code": int(pc),
                "zone": zone,
                "pmax": float(x.pmax.sum()),
                "avail_twh": float(x.avail_twh.sum()),
                "floor_twh": float(x.floor_twh.sum()),
                "attain_twh": float(x.attain_twh.sum()),
                "model_plant_twh": float(pl.get(key, {}).get("m_ann") or np.nan),
                "model_key_split": key.endswith(":ST_GAS"),
                "hr": wmean(x, "heat_rate"),
                "gas": wmean(x, "fuel_price_mean"),
                "offer_mean": wmean(x, "mc_mean"),
                "nonfuel": wmean(x, "adder"),
                "zone_price_mean": float(x.zone_price_mean.mean()),
                "act_net_twh": float(act.get(pc, 0.0)),
            }
        )
    return pd.DataFrame(rows)


def hub_rt(year: int) -> pd.DataFrame:
    """Hourly RT hub LMP, one column per hub."""
    fs = sorted(
        glob.glob(str(REPO / f"data/raw/lmp-data/MISO/miso_hub_lmp_{year}_rt*"))
    )
    d = pd.concat([pd.read_csv(x) for x in fs])
    d = d[(d.type == "Hub") & (d.value == "LMP")]
    hs = [f"he{i:02d}" for i in range(1, 25)]
    m = d.melt(id_vars=["date", "node"], value_vars=hs, var_name="he", value_name="lmp")
    m["hour"] = m.he.str[2:].astype(int) - 1
    m = m.pivot_table(
        index=["date", "hour"], columns="node", values="lmp"
    ).reset_index()
    m["date"] = m.date.astype(str)
    return m


def oom(year: int, south: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Per-plant out-of-merit energy from CEMS hourly conduct at measured hub prices."""
    lm = hub_rt(year)
    per, tot = [], {"E": 0.0, "oom_full": 0.0, "oom_fuel": 0.0, "oom_fuel_nodal": 0.0}
    for stc, hub in HUB.items():
        path = REPO / f"data/raw/campd-unit-level/{stc}_{year}.parquet"
        c = pd.read_parquet(path)
        c["facilityId"] = pd.to_numeric(c.facilityId, errors="coerce")
        c = c[c.facilityId.isin(south.plant_code)]
        fuel = c.primaryFuelInfo.astype(str)
        ut = c.unitType.astype(str).str.lower()
        c = c[
            fuel.str.contains("Gas")
            & ~fuel.str.contains("Coal")
            & ~ut.str.contains("combined|combustion")
        ]
        if c.empty:
            continue
        c["date"] = c.date.astype(str)
        c = c.merge(
            lm[["date", "hour", hub]].rename(columns={hub: "lmp"}),
            on=["date", "hour"],
            how="left",
        )
        for pc, g in c.groupby("facilityId"):
            p = south[south.plant_code == pc].iloc[0]
            ph = (
                g.assign(gl=g.grossLoad.fillna(0.0), hi=g.heatInput.fillna(0.0))
                .groupby(["date", "hour"])
                .agg(gl=("gl", "sum"), hi=("hi", "sum"), lmp=("lmp", "first"))
            )
            gross = ph.gl.sum() / 1e6
            if gross <= 0 or p.act_net_twh <= 0:
                continue
            netf = p.act_net_twh / gross
            on = (ph.gl > 0).to_numpy()
            gl = ph.gl.to_numpy()
            hr = np.where(on, ph.hi.to_numpy() / np.where(on, gl, 1.0) / netf, np.nan)
            fuelc = hr * p.gas
            full = fuelc + p.nonfuel
            lmp = ph.lmp.to_numpy()
            e = gl * netf
            f = {
                "oom_full": on & (lmp < full),
                "oom_fuel": on & (lmp < fuelc),
                "oom_fuel_nodal": on & (lmp + NODAL_ALLOWANCE < fuelc),
            }
            pmax_obs = gl.max()
            rec = {
                "plant_code": int(pc),
                "name": str(g.facilityName.iloc[0]),
                "state": stc,
                "on_hours": int(on.sum()),
                "cost_full_mean": float(np.nanmean(np.where(on, full, np.nan))),
                "lmp_when_on": float(np.nanmean(np.where(on, lmp, np.nan))),
                "lowload_share": float(e[on & (gl < 0.5 * pmax_obs)].sum() / e.sum()),
            }
            for k, m in f.items():
                rec[f"{k}_twh"] = float(e[m].sum() / 1e6)
                tot[k] += float(e[m].sum() / 1e6)
            tot["E"] += float(e.sum() / 1e6)
            per.append(rec)
    return pd.DataFrame(per), tot


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--in-dir", required=True)
    ap.add_argument("--years", nargs="+", type=int, default=[2019, 2023])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    s = PAYLOAD.read_text()
    payload = json.loads(
        gzip.decompress(base64.b64decode(re.search(r'="([^"]+)"', s).group(1)))
    )
    res = {"keeper": KEEPER_ID, "nodal_allowance_usd_mwh": NODAL_ALLOWANCE, "years": {}}
    for y in args.years:
        pt = plant_table(Path(args.in_dir), y, payload)
        south = pt[pt.zone == "MISO-South"]
        per, tot = oom(y, south)
        t = per.merge(south, on="plant_code", how="left").sort_values(
            "act_net_twh", ascending=False
        )
        res["years"][str(y)] = {
            "south_totals": {
                "avail_twh": round(float(south.avail_twh.sum()), 3),
                "floor_twh": round(float(south.floor_twh.sum()), 3),
                "attain_twh": round(float(south.attain_twh.sum()), 3),
                "act_net_twh": round(float(south.act_net_twh.sum()), 3),
                **{k: round(v, 3) for k, v in tot.items()},
            },
            "stgas_all_zones": {
                "attain_twh": round(float(pt.attain_twh.sum()), 3),
                "floor_twh": round(float(pt.floor_twh.sum()), 3),
                "act_net_twh": round(float(pt.act_net_twh.sum()), 3),
            },
            "plants": json.loads(t.round(3).to_json(orient="records")),
        }
        print(y, json.dumps(res["years"][str(y)]["south_totals"]))
    Path(args.out).write_text(json.dumps(res, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
