"""NYISO-NEXT-30 phase 0: is there a public, forward-reproducible driver of the Zone-K import limit?

Zero LP. Open item 2 (NEXT-29): 69-100 % of the annual K-over-J spread miss
sits in hours the model's ``NYC>Long_Island`` link is below its 940 MW cap,
while NYISO's DAM binds the Zone-K import set (Y49 / Y50 / Shore Road) there.
This probe tests the two public candidate drivers named in the handoff:

1. **Transmission outage windows** - MIS P-33 ``outSched`` (scheduled out/in
   per facility PTID, daily postings) for Y49 Sprain Brook-East Garden City,
   Y50 Dunwoodie-Shore Road and the 138 kV J-K ties 901 / 903.
2. **PAR schedules** - MIS P-34 ``ParFlows`` (5-minute measured flow per PAR
   PTID) for Lake Success (903), Valley Stream (901) and the two East Garden
   City 345 kV PARs (on Y49); the PTID identity comes from ``outSched``'s
   ``Equipment Name``, as in ``scripts/data/fetch_nyiso_par_data.py``.

Against: the DA K-over-J congestion spread (LBMP net of the loss component,
LONGIL minus N.Y.C.) and the DAM limiting-constraint posting.

The MIS archives are cached under ``--cache-dir`` (not committed); the DA and
DLC archives are read from ``data/raw/lmp-data/NYISO`` (stage them with
``scripts/data/fetch_nyiso_zonal_lmp.py --kind da|dlc``).

Usage::

    uv run python scripts/probes/nyisonext30_zone_k_import_drivers.py \
        --cache-dir <scratch>/mis --json-out results/phase0/nyiso/_nyisonext30_zone_k_import_drivers.json
"""

from __future__ import annotations

import argparse
import glob
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from market_sim.config.paths import RAW_DIR

MIS = "http://mis.nyiso.com/public/csv"
YEARS = range(2021, 2026)
LMP_DIR = RAW_DIR / "lmp-data" / "NYISO"
TS_FMT = "%m/%d/%Y %H:%M:%S"

# Zone-K import elements, by their P-33 Equipment Name.
OUTAGE_ELEMENTS = {
    "Y49": "SPRNBRK_-EGRDNCTR_345_Y49",
    "Y50": "DUNWODIE-SHORE_RD_345_Y50",
    "901": "JAMAICA_-VALLYSTR_138_901 L_M",
    "903": "JAMAICA_-LAKSUCSS_138_903",
}
# PAR PTIDs, identified by P-33 Equipment Name (LAKSUCSS / VALLYSTR / EGRDNCTY PARs).
PAR_PTIDS = {
    "25593": "LS_903",
    "25607": "VS_901",
    "25678": "EGC_PAR1",
    "25679": "EGC_PAR2",
}
# DAM limiting facilities of the Zone-K import set (NEXT-26 FINDING sec. 2).
KSET_PATTERN = "DUNWODIE 345 SHORE_RD|SPRNBRK  345 EGRDNCTR|SHORE_RD 345 SHORE_RD"


def fetch_mis(report: str, cache: Path) -> list[Path]:
    """Download the monthly MIS archives of one report for 2021-2025, skipping cached files."""
    out = []
    for y in YEARS:
        for m in range(1, 13):
            dest = cache / report / f"{y}{m:02d}01{report}_csv.zip"
            if not (dest.exists() and dest.stat().st_size > 0):
                resp = requests.get(f"{MIS}/{report}/{dest.name}", timeout=300)
                resp.raise_for_status()
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(resp.content)
            out.append(dest)
    return out


def read_zips(paths, **kw) -> pd.DataFrame:
    """Concatenate every CSV inside a list of zip archives."""
    frames = []
    for p in paths:
        with zipfile.ZipFile(p) as zf:
            frames += [pd.read_csv(zf.open(n), **kw) for n in zf.namelist()]
    return pd.concat(frames, ignore_index=True)


def outage_hours(os_zips, idx: pd.DatetimeIndex) -> pd.DataFrame:
    """Hourly out-of-service flags per element; each (element, start) takes its latest posting."""
    d = read_zips(os_zips, dtype=str)
    d.columns = ["ts", "ptid", "name", "out", "inn"]
    for c in ("ts", "out", "inn"):
        d[c] = pd.to_datetime(d[c], format=TS_FMT)
    d = d.sort_values("ts").groupby(["name", "out"], as_index=False).last()
    flags = pd.DataFrame(False, index=idx, columns=list(OUTAGE_ELEMENTS))
    for col, name in OUTAGE_ELEMENTS.items():
        for _, r in d[d.name == name].iterrows():
            flags.loc[(idx >= r.out) & (idx < r.inn), col] = True
    return flags


def par_hourly(pf_zips) -> pd.DataFrame:
    """Hourly mean measured flow on the Zone-K PARs."""
    frames = []
    for p in pf_zips:
        d = read_zips([p], dtype={"Point ID": str})
        d.columns = ["t", "ptid", "mw"]
        frames.append(d[d.ptid.isin(PAR_PTIDS)])
    d = pd.concat(frames)
    d["t"] = pd.to_datetime(d.t, format=TS_FMT).dt.floor("h")
    return d.pivot_table(index="t", columns="ptid", values="mw", aggfunc="mean").rename(
        columns=PAR_PTIDS
    )


def da_spread() -> pd.Series:
    """Hourly DA K-over-J congestion spread: (LBMP - loss) at LONGIL minus N.Y.C."""
    da = read_zips(sorted(glob.glob(str(LMP_DIR / "202[1-5]??01damlbmp_zone_csv.zip"))))
    da.columns = ["t", "zone", "ptid", "lbmp", "loss", "cong"]
    da = da[da.zone.isin(["LONGIL", "N.Y.C."])]
    da["t"] = pd.to_datetime(da.t, format="%m/%d/%Y %H:%M")
    da["x"] = da.lbmp - da.loss
    p = da.pivot_table(index="t", columns="zone", values="x", aggfunc="first")
    return (p["LONGIL"] - p["N.Y.C."]).rename("sp")


def kset_binding_hours() -> pd.DatetimeIndex:
    """DAM hours in which a Zone-K import-set facility is a limiting constraint."""
    dl = read_zips(
        sorted(glob.glob(str(LMP_DIR / "202[1-5]??01DAMLimitingConstraints_csv.zip")))
    )
    dl.columns = ["t", "tz", "fac", "ptid", "cont", "cost"]
    dl = dl[dl.fac.str.contains(KSET_PATTERN, regex=True)]
    return pd.DatetimeIndex(pd.to_datetime(dl.t, format="%m/%d/%Y %H:%M").unique())


def month_matched(df: pd.DataFrame, flag: str) -> dict:
    """Per year: mean over months with both states of (mean spread out - mean spread in)."""
    g = df.groupby([df.index.to_period("M"), flag]).sp.mean().unstack().dropna()
    if g.empty or True not in g or False not in g:
        return {}
    d = (g[True] - g[False]).groupby(g.index.year)
    return {
        int(y): {
            "mean": round(float(s.mean()), 2),
            "median": round(float(s.median()), 2),
            "months": int(s.size),
        }
        for y, s in d
    }


def main() -> None:
    """Run the probe and write the JSON record."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cache-dir", type=Path, required=True)
    ap.add_argument("--json-out", type=Path, required=True)
    a = ap.parse_args()

    idx = pd.date_range("2021-01-01", "2025-12-31 23:00", freq="h")
    flags = outage_hours(fetch_mis("outSched", a.cache_dir), idx)
    par = par_hourly(fetch_mis("ParFlows", a.cache_dir))
    par["wheel_901_903"] = par.LS_903 + par.VS_901
    par["egc_y49"] = par.EGC_PAR1 + par.EGC_PAR2

    df = da_spread().to_frame()
    df = df[~df.index.duplicated()].join(flags, how="left").join(par, how="left")
    df[list(OUTAGE_ELEMENTS)] = df[list(OUTAGE_ELEMENTS)].fillna(False).astype(bool)
    df["y49_or_y50"] = df.Y49 | df.Y50
    df["bind"] = df.index.isin(kset_binding_hours())
    df["y"] = df.index.year

    rec: dict = {"lane": "NYISO-NEXT-30", "solves": 0, "years": list(YEARS)}
    rec["outage_hours"] = {
        c: {int(y): int(v) for y, v in flags[c].groupby(flags.index.year).sum().items()}
        for c in OUTAGE_ELEMENTS
    }
    mass = df.groupby(["y", "y49_or_y50"]).sp.sum().unstack()
    rec["share_of_kj_mass_in_y49_y50_out_hours"] = {
        int(y): round(float(v), 3) for y, v in (mass[True] / mass.sum(axis=1)).items()
    }
    rec["raw_spread_out_vs_in"] = {
        c: {
            int(y): {
                "out": round(float(g[g[c]].sp.mean()), 2) if g[c].any() else None,
                "in": round(float(g[~g[c]].sp.mean()), 2),
            }
            for y, g in df.groupby("y")
        }
        for c in ("Y49", "Y50")
    }
    rec["month_matched_spread_out_minus_in"] = {
        c: month_matched(df, c) for c in ("Y49", "Y50")
    }
    rec["par_mean_std_mw"] = {
        c: {
            int(y): [round(float(s.mean()), 1), round(float(s.std()), 1)]
            for y, s in par[c].groupby(par.index.year)
        }
        for c in ("LS_903", "VS_901", "wheel_901_903", "egc_y49")
    }
    corr = {}
    for y, g in df.groupby("y"):
        corr[int(y)] = {
            "wheel_vs_spread": round(
                float(g[["wheel_901_903", "sp"]].corr().iloc[0, 1]), 3
            ),
            "egc_y49_vs_spread": round(
                float(g[["egc_y49", "sp"]].corr().iloc[0, 1]), 3
            ),
            "wheel_vs_kset_binding": round(
                float(g[["wheel_901_903", "bind"]].astype(float).corr().iloc[0, 1]), 3
            ),
        }
    ym = df.index.to_period("M")
    dm = df[["wheel_901_903", "egc_y49", "sp"]] - df[
        ["wheel_901_903", "egc_y49", "sp"]
    ].groupby(ym).transform("mean")
    corr["pooled_month_demeaned"] = {
        "wheel_vs_spread": round(
            float(dm[["wheel_901_903", "sp"]].corr().iloc[0, 1]), 3
        ),
        "egc_y49_vs_spread": round(float(dm[["egc_y49", "sp"]].corr().iloc[0, 1]), 3),
    }
    rec["correlations"] = corr
    rec["kset_binding_hours"] = {
        int(y): int(v) for y, v in df.groupby("y").bind.sum().items()
    }
    rec["mean_kj_spread_da"] = {
        int(y): round(float(v), 2) for y, v in df.groupby("y").sp.mean().items()
    }
    rec["kj_spread_when_kset_not_binding"] = {
        int(y): round(float(g[~g.bind].sp.mean()), 2) for y, g in df.groupby("y")
    }

    a.json_out.parent.mkdir(parents=True, exist_ok=True)
    a.json_out.write_text(
        json.dumps(
            rec,
            indent=1,
            default=lambda o: o.item() if isinstance(o, np.generic) else str(o),
        )
    )
    print(json.dumps(rec, indent=1, default=str))


if __name__ == "__main__":
    main()
