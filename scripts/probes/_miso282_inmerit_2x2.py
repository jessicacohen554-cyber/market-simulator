#!/usr/bin/env python3
"""miso-282 phase 0 (ZERO LP): why is MISO-South gas steam short IN MERIT in 2021-22?

Joins, per MISO-South ST_GAS plant and hour, the keeper's fleet-only rebuild
(``_miso282_stgas_fleet.py``: per-unit hourly P0 offer ``mc``, capacity,
floor, delivered fuel and the keeper's own committed zone price) to measured
conduct (CEMS hourly gross load / heat input, EIA-923 net/gross) and the
measured MISO hub RT LMP of the plant's state hub.

Two prices x two costs give four price-taker envelopes per plant
(``E = sum_t max(floor[t], cap[t] * 1[price[t] >= cost[t]])``):

* ``MM`` model price  vs model offer   (the keeper's own envelope; ~= realized)
* ``HM`` hub price    vs model offer   (offer side held, price measured)
* ``MC`` model price  vs measured cost (price side held, cost measured)
* ``HC`` hub price    vs measured cost

Measured cost = the plant's annual CEMS net heat rate (heat input / (gross x
EIA-923 net/gross)) x the MODEL's own hourly delivered gas for the plant + the
model's gas-steam VOM (``constants.VOM["gas_st"]``). Only the heat rate is
measured; gas and VOM are the model's, so ``MC`` vs ``MM`` isolates the
offer-construction difference (heat rate + margin mechanism), and ``HM`` vs
``MM`` isolates the price level/shape.

Actual in-merit energy = CEMS net MWh in on-hours with hub >= measured cost.
Model in-merit energy = envelope minus its floor. All sums are restricted to
hours where the hub price exists (2022 has ~1,200 missing RT hours); coverage
is reported.

Rule 13: nothing here is fed back into a solve; it classifies measured conduct
and localizes a residual. Rule 23: artifacts are read, never re-derived.

Usage::

    uv run python scripts/probes/_miso282_inmerit_2x2.py --in-dir X --years 2021 2022 --out J
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from market_sim.config.constants import VOM  # noqa: E402
from scripts.probes._miso281_south_steam_oom import E923, HUB, hub_rt  # noqa: E402

KEEPER_ID = "2026-09-28-miso-280-splitremap"
C1_EXCLUDED = {1403}  # Ninemile: a mixed_fossil_plants() plant, OTHER_FOSSIL in C1


def hour_index(year: int) -> pd.DataFrame:
    """(date, hour) for the model's 8760 hours (Dec 31 dropped in a leap year)."""
    ts = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    return pd.DataFrame({"date": ts.strftime("%Y-%m-%d"), "hour": ts.hour})


def cems_plant_hourly(
    year: int, plants: set[int]
) -> dict[int, tuple[str, pd.DataFrame]]:
    """Per plant: (state, 8760 frame of gross load / heat input of gas steam units)."""
    idx = hour_index(year)
    out: dict[int, tuple[str, pd.DataFrame]] = {}
    for stc in HUB:
        c = pd.read_parquet(REPO / f"data/raw/campd-unit-level/{stc}_{year}.parquet")
        c["facilityId"] = pd.to_numeric(c.facilityId, errors="coerce")
        c = c[c.facilityId.isin(plants)]
        fuel = c.primaryFuelInfo.astype(str)
        ut = c.unitType.astype(str).str.lower()
        c = c[
            fuel.str.contains("Gas")
            & ~fuel.str.contains("Coal")
            & ~ut.str.contains("combined|combustion")
        ]
        c["date"] = c.date.astype(str)
        for pc, g in c.groupby("facilityId"):
            ph = (
                g.assign(gl=g.grossLoad.fillna(0.0), hi=g.heatInput.fillna(0.0))
                .groupby(["date", "hour"])[["gl", "hi"]]
                .sum()
                .reset_index()
            )
            out[int(pc)] = (
                stc,
                idx.merge(ph, on=["date", "hour"], how="left").fillna(0.0),
            )
    return out


def envelope(price, cost, cap, floor) -> np.ndarray:
    """Hourly price-taker energy (MW) of units (rows) at ``price`` vs ``cost``."""
    return np.maximum(floor, cap * (price >= cost))


def analyse_year(in_dir: Path, year: int) -> dict:
    """The 2x2 per plant, plus South totals by month and hour of day."""
    u = pd.read_parquet(in_dir / f"units_{year}.parquet")
    u = u[(u.group == "ST_GAS") & (u.zone == "MISO-South")]
    z = np.load(in_dir / f"stgas_hourly_{year}.npz")
    uid = list(z["unit_ids"])
    pos = {k: i for i, k in enumerate(uid)}
    e = pd.read_csv(E923)
    e = e[(e.year == year) & (e.prime_mover == "ST") & (e.fuel_type == "NG")]
    act = e.groupby("plant_id").net_generation_mwh.sum()
    lm = hub_rt(year)
    idx = hour_index(year)
    cems = cems_plant_hourly(year, set(u.plant_code.astype(int)))
    mon = pd.to_datetime(idx.date).dt.month.to_numpy()
    hod = idx.hour.to_numpy()
    vom = VOM["gas_st"]
    keys = ("MM", "HM", "MC", "HC")
    rows, by_m, by_h = [], {}, {}
    tot = {k: 0.0 for k in (*keys, "floor", "act", "act_in", "act_all")}
    for pc, g in u.groupby("plant_code"):
        pc = int(pc)
        if pc not in cems or act.get(pc, 0.0) <= 0:
            continue
        stc, ch = cems[pc]
        hub = idx.merge(
            lm[["date", "hour", HUB[stc]]], on=["date", "hour"], how="left"
        )[HUB[stc]].to_numpy()
        ok = ~np.isnan(hub)
        ii = [pos[k] for k in g.unit_id if k in pos]
        mc, cap, fl = z["mc"][ii], z["cap"][ii], z["floor"][ii]
        pm, fuel, hr = z["price"][ii][0], z["fuel"][ii], z["heat_rate"][ii]
        gross = ch.gl.to_numpy()
        if gross.sum() <= 0:
            continue  # no CEMS conduct for the plant's gas steam units this year
        netf = act[pc] / gross.sum()
        net = gross * netf
        hr_meas = ch.hi.sum() / net.sum()
        w = cap.sum(axis=1, keepdims=True).clip(1e-9)
        gas = (fuel * w).sum(axis=0) / w.sum()  # plant hourly delivered gas
        cost = hr_meas * gas + vom
        hub_f = np.where(ok, hub, -np.inf)  # masked hours are excluded below anyway
        env = {
            "MM": envelope(pm, mc, cap, fl),
            "HM": envelope(hub_f, mc, cap, fl),
            "MC": envelope(pm, cost, cap, fl),
            "HC": envelope(hub_f, cost, cap, fl),
        }
        on = gross > 0
        a_in = net * (on & (hub_f >= cost))
        flh = fl.sum(axis=0)
        rec = {
            "plant_code": pc,
            "state": stc,
            "c1_basis": pc not in C1_EXCLUDED,
            "pmax": float(g.pmax.sum()),
            "hr_model": float((hr * w[:, 0]).sum() / w.sum()),
            "hr_meas": float(hr_meas),
            # A legacy gas-steam net heat rate below 9 MMBtu/MWh is not physical:
            # it flags a CEMS/EIA-923 fuel mismatch (co-fired coal or petcoke
            # units in the gas filter), so that plant's measured-cost columns
            # are excluded from the *_hrok totals.
            "hr_plausible": bool(9.0 <= hr_meas <= 16.0),
            "gas_mean": float(gas.mean()),
            "offer_econ_min": float(np.median(mc.min(axis=0))),
            "cost_meas_mean": float(cost[ok].mean()),
            "pmod_mean": float(pm[ok].mean()),
            "hub_mean": float(hub[ok].mean()),
            "act_twh": float(net[ok].sum() / 1e6),
            "act_in_twh": float(a_in[ok].sum() / 1e6),
            "floor_twh": float(flh[ok].sum() / 1e6),
            "h_in_model": int((ok & (pm >= mc.min(axis=0))).sum()),
            "h_in_meas": int((ok & (hub >= cost)).sum()),
            "coverage": float(ok.mean()),
        }
        for k in keys:
            rec[f"E_{k}_twh"] = float(env[k].sum(axis=0)[ok].sum() / 1e6)
            tot[k] += rec[f"E_{k}_twh"]
        tot["floor"] += rec["floor_twh"]
        tot["act"] += rec["act_twh"]
        tot["act_in"] += rec["act_in_twh"]
        rows.append(rec)
        if rec["c1_basis"]:
            for lab, grp, store, n in (("m", mon, by_m, 12), ("h", hod, by_h, 24)):
                for b in range(n):
                    sel = ok & (grp == (b + 1 if lab == "m" else b))
                    s = store.setdefault(b, {"MM_above": 0.0, "act_in": 0.0, "dp": []})
                    s["MM_above"] += float(
                        (env["MM"].sum(axis=0) - flh)[sel].sum() / 1e6
                    )
                    s["act_in"] += float(a_in[sel].sum() / 1e6)
                    s["dp"].append((pm - hub)[sel])
    for store in (by_m, by_h):
        for s in store.values():
            s["pmod_minus_hub"] = round(float(np.concatenate(s.pop("dp")).mean()), 2)
            s["MM_above"] = round(s["MM_above"], 3)
            s["act_in"] = round(s["act_in"], 3)
    df = pd.DataFrame(rows).sort_values("act_twh", ascending=False)
    c1 = df[df.c1_basis]
    c1_tot = {
        k: round(float(c1[c].sum()), 3)
        for k, c in (
            ("act", "act_twh"),
            ("act_in", "act_in_twh"),
            ("floor", "floor_twh"),
            *((k, f"E_{k}_twh") for k in keys),
        )
    }
    ok_hr = c1[c1.hr_plausible]
    for k in ("MC", "HC"):
        c1_tot[f"{k}_hrok"] = round(float(ok_hr[f"E_{k}_twh"].sum()), 3)
    c1_tot["MM_hrok"] = round(float(ok_hr["E_MM_twh"].sum()), 3)
    return {
        "south_all": {k: round(v, 3) for k, v in tot.items() if k != "act_all"},
        "south_c1_basis": c1_tot,
        "by_month_c1": by_m,
        "by_hour_c1": by_h,
        "plants": json.loads(df.round(3).to_json(orient="records")),
    }


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--in-dir", required=True)
    ap.add_argument("--years", nargs="+", type=int, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    res = {"keeper": KEEPER_ID, "vom_gas_st": VOM["gas_st"], "years": {}}
    for y in args.years:
        res["years"][str(y)] = r = analyse_year(Path(args.in_dir), y)
        print(y, json.dumps(r["south_c1_basis"]))
    Path(args.out).write_text(json.dumps(res, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
