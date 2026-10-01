"""R-CAISO-26 probe: what moved CAISO's NW interchange over MLK 2024. Zero LP.

Two measured reads, no model artifact needed:

(A) EIA-930 BA-to-BA interchange for CISO (committed, ``data/raw/eia-930-interchange``),
    evening h17-22 local, Jan 8-21 2024: per-neighbour mean, net, gross import, gross export.
(B) CAISO OASIS ``TRNS_USAGE`` (DAM), the NW interties (MALIN500_ISL, NOB_ITC, COTPISO_ITC),
    evening OPR_HR 18-23: hourly OTC by direction (the operating limit net of outage
    derates), seasonal TTC, and DAM scheduled net energy. Fetched live; nothing committed.

Usage: ``python3 scripts/probes/_rcaiso26_nw_intertie.py [--no-oasis]``.
Record: ``docs/handoffs/r-caiso-26/PRECOMMIT-r-caiso-26-nw-import-driver-2026-10-01.md``.
"""

from __future__ import annotations

import argparse
import io
import urllib.request
import zipfile

import pandas as pd

from market_sim.config.paths import RAW_DIR

OASIS = (
    "https://oasis.caiso.com/oasisapi/SingleZip?queryname=TRNS_USAGE&market_run_id=DAM"
    "&startdatetime={a}T08:00-0000&enddatetime={b}T08:00-0000&version=1&resultformat=6"
)
NW_TIES = ["MALIN500_ISL", "NOB_ITC", "COTPISO_ITC"]


def eia930_table() -> pd.DataFrame:
    """Return per-day evening CISO interchange by neighbour (+ = import into CISO)."""
    d = pd.read_parquet(
        RAW_DIR / "eia-930-interchange" / "CISO interchange hourly.parquet"
    )
    d["t"] = pd.to_datetime(d.local_time)
    w = d[(d.t >= "2024-01-08") & (d.t < "2024-01-22")].copy()
    w["mw"] = -w.mw  # EIA sign: + = CISO exports to the DIBA
    w = w[w.t.dt.hour.between(17, 22)]
    w["day"] = w.t.dt.strftime("%m-%d")
    p = w.pivot_table(index="day", columns="diba", values="mw", aggfunc="mean")
    by_h = w.groupby(["day", w.t.dt.hour])
    p["NET"] = p.sum(axis=1)
    p["GROSS_IMP"] = (
        by_h.mw.apply(lambda s: s.clip(lower=0).sum()).groupby("day").mean()
    )
    p["GROSS_EXP"] = (
        by_h.mw.apply(lambda s: (-s).clip(lower=0).sum()).groupby("day").mean()
    )
    return p.round(0)


def oasis_table() -> pd.DataFrame:
    """Return per-day evening OTC / TTC / scheduled net for the NW interties."""
    with urllib.request.urlopen(
        OASIS.format(a="20240108", b="20240119"), timeout=300
    ) as r:
        z = zipfile.ZipFile(io.BytesIO(r.read()))
    d = pd.read_csv(z.open(z.namelist()[0]))
    d = d[d.TI_ID.isin(NW_TIES) & d.OPR_HR.between(18, 23)]
    d = d[d.XML_DATA_ITEM.isin(["OTC_MW", "TTC_MW", "ENE_IMPORT_MW"])]
    p = d.pivot_table(
        index="OPR_DT",
        columns=["XML_DATA_ITEM", "TI_ID", "TI_DIRECTION"],
        values="MW",
        aggfunc="mean",
    )
    otc = p["OTC_MW"]
    return pd.DataFrame(
        {
            "imp_OTC": otc.xs("I", axis=1, level=1).sum(axis=1),
            "imp_seasonal_TTC": p["TTC_MW"].xs("I", axis=1, level=1).sum(axis=1),
            "exp_OTC": otc.xs("E", axis=1, level=1).sum(axis=1),
            "NOB_exp_OTC": otc[("NOB_ITC", "E")],
            "sched_net_import": p["ENE_IMPORT_MW"].xs("I", axis=1, level=1).sum(axis=1),
        }
    ).round(0)


def main() -> None:
    """Print both tables."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-oasis", action="store_true")
    a = ap.parse_args()
    pd.set_option("display.width", 200)
    print(eia930_table().to_string())
    if not a.no_oasis:
        print(oasis_table().to_string())


if __name__ == "__main__":
    main()
