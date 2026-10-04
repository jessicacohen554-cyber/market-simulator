"""Close-out CAISO w5, phase 0 (ZERO LP): did the missed CT_PEAKER / ST_GAS energy clear the MEASURED price?

For every plant-hour where a CT_PEAKER / ST_GAS plant ran in reality above its
w3 model output while the model priced it out (cheapest available offer above
the model lambda, see ``_closeout_caiso_w5_intragas_census.py``), compare the
plant's cheapest available P1 offer with the MEASURED CAISO trading-hub price
of its zone in that hour (OASIS ``TH_NP15_GEN`` for NP15, ``TH_ZP26_GEN`` for
ZP26, ``TH_SP15_GEN`` for SP15_rest / LA_BASIN / SDGE; DAM and RTM hourly,
``data/raw/lmp-data/CAISO``; fixed-PST clock, Feb 29 dropped):

* ``da_clears``   DA print >= offer: the unit was economic in the measured DA
                  market, so the MODEL lambda is too low in that hour;
* ``rt_only``     DA < offer <= RT: an RT dispatch the DA-only LP cannot carry;
* ``neither``     both prints below the offer: an out-of-market run (exceptional
                  dispatch / RUC / AS-backed energy / self-schedule) or a bid
                  below the modelled offer.

Also the model lambda vs the DA print in the ``da_clears`` hours.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_closeout_caiso_w5_peaker_price_test.py [--years ...] [--out PATH]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path[:0] = [".", "src", "scripts", str(Path(__file__).resolve().parent)]

from _closeout_caiso_w5_intragas_census import (  # noqa: E402
    LEG,
    MCOLS,
    ON_MW,
    T,
    _levelled,
    _shared,
)

ROOT = Path(__file__).resolve().parents[2]
HUB_OF_ZONE = {
    "NP15": "TH_NP15_GEN-APND",
    "ZP26": "TH_ZP26_GEN-APND",
    "SP15_rest": "TH_SP15_GEN-APND",
    "LA_BASIN": "TH_SP15_GEN-APND",
    "SDGE": "TH_SP15_GEN-APND",
}
CLASSES = ("CT_PEAKER", "ST_GAS")


def measured_hub(year: int, market: str) -> dict:
    """Hourly hub LMP on the fixed-PST 8760 clock, per trading hub."""
    p = ROOT / f"data/raw/lmp-data/CAISO/CAISO_{market}_hourly_{year}.csv"
    d = pd.read_csv(p, usecols=["interval_start_gmt", "node", "LMP"])
    d = d[d.node.str.startswith("TH_")]
    t = pd.to_datetime(d.interval_start_gmt, utc=True).dt.tz_convert(
        None
    ) - pd.Timedelta(hours=8)
    d = d.assign(t=t)
    d = d[(d.t.dt.year == year) & ~((d.t.dt.month == 2) & (d.t.dt.day == 29))]
    doy = d.t.dt.dayofyear - ((d.t.dt.month > 2) & d.t.dt.is_leap_year).astype(int) - 1
    d = d.assign(h=(doy * 24 + d.t.dt.hour).astype(int))
    return {
        n: g.groupby("h").LMP.mean().reindex(range(T)).to_numpy(float)
        for n, g in d.groupby("node")
    }


def year_test(year: int, e923: pd.DataFrame, campd: pd.DataFrame) -> dict:
    """Split the priced-out missed energy by the measured DA / RT prints."""
    leg = Path(LEG.as_posix().format(y=year))
    um = pd.read_parquet(
        leg / f"hourly/unit_marginal_{year}.parquet",
        columns=[
            "unit_id",
            "plant_code",
            "plant_group",
            "zone",
            "hour",
            "mw",
            "cap_mw",
            "mc",
        ],
    )
    um["plant_group"] = um.plant_group.astype(str)
    um["zone"] = um.zone.astype(str)
    sysh = pd.read_parquet(leg / f"hourly/system_{year}.parquet")
    sysh = sysh[sysh["pass"] == "P1"]
    lam = {
        z: g.set_index("hour").price.reindex(range(T)).to_numpy(float)
        for z, g in sysh.groupby("zone")
    }
    da, rt = measured_hub(year, "dam"), measured_hub(year, "rtm")
    ey = e923[e923.year == year]
    cy = campd[campd.year == year]
    cmap = {
        int(p): g.set_index("hour").net_mw.reindex(range(T)).fillna(0).to_numpy(float)
        for p, g in cy.groupby("plant_id")
    }
    out = {}
    for klass in CLASSES:
        e = ey[ey.klass == klass].groupby("plant_id")[MCOLS].sum()
        acc = {"da_clears": 0.0, "rt_only": 0.0, "neither": 0.0, "no_print": 0.0}
        lam_gap, da_gap = [], []
        for p, g in um[um.plant_group == klass].groupby("plant_code"):
            p = int(p)
            if p not in e.index:
                continue
            act = _levelled(cmap.get(p, np.zeros(T)), e.loc[p].to_numpy(float))
            mw = (
                g.pivot_table(
                    index="hour", columns="unit_id", values="mw", aggfunc="sum"
                )
                .reindex(range(T))
                .fillna(0)
            )
            cap = (
                g.pivot_table(
                    index="hour", columns="unit_id", values="cap_mw", aggfunc="sum"
                )
                .reindex(range(T))
                .fillna(0)
            )
            mc = g.pivot_table(
                index="hour", columns="unit_id", values="mc", aggfunc="mean"
            ).reindex(range(T))
            zone = g.zone.iat[0]
            lz = lam.get(zone, lam["SP15_rest"])
            hub = HUB_OF_ZONE.get(zone, "TH_SP15_GEN-APND")
            pd_, pr_ = da.get(hub), rt.get(hub)
            short = np.clip(act - mw.sum(axis=1).to_numpy(), 0, None) * (act > ON_MW)
            head = ((cap.to_numpy() - mw.to_numpy()) > 1.0) & (cap.to_numpy() > 1.0)
            offer = np.where(head, mc.to_numpy(), np.inf).min(axis=1)
            priced = np.isfinite(offer) & (offer > lz + 0.01) & (short > 0)
            nop = priced & (~np.isfinite(pd_) | ~np.isfinite(pr_))
            ok = priced & ~nop
            dac = ok & (pd_ >= offer)
            rto = ok & ~dac & (pr_ >= offer)
            nei = ok & ~dac & ~rto
            acc["no_print"] += short[nop].sum()
            acc["da_clears"] += short[dac].sum()
            acc["rt_only"] += short[rto].sum()
            acc["neither"] += short[nei].sum()
            lam_gap.append((lz - pd_)[dac])
            da_gap.append((offer - pd_)[nei])
        lg = np.concatenate(lam_gap) if lam_gap else np.array([])
        dg = np.concatenate(da_gap) if da_gap else np.array([])
        out[klass] = {
            "priced_out_missed_twh": {k: round(v / 1e6, 3) for k, v in acc.items()},
            "da_clears_hours_model_lambda_minus_da_p25_p50_p75": [
                round(float(np.percentile(lg, q)), 2) for q in (25, 50, 75)
            ]
            if lg.size
            else None,
            "neither_hours_offer_minus_da_p25_p50_p75": [
                round(float(np.percentile(dg, q)), 2) for q in (25, 50, 75)
            ]
            if dg.size
            else None,
        }
    return out


def main() -> None:
    """Run the price test for the printed years."""
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--years", nargs="+", type=int, default=[2021, 2022, 2023, 2024, 2025]
    )
    ap.add_argument(
        "--out",
        default=str(
            ROOT / "docs/records/caiso/closeout-caiso-w5/_peaker_price_test.json"
        ),
    )
    a = ap.parse_args()
    e923, campd = _shared("eia923"), _shared("campd")
    res = {}
    for y in a.years:
        res[str(y)] = year_test(y, e923, campd)
        print(y, json.dumps(res[str(y)], default=float), flush=True)
        Path(a.out).write_text(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
