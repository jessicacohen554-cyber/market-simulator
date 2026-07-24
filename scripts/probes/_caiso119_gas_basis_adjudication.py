"""caiso-119 ADJUDICATION: which series is the honest CAISO "actual gas", and
what is the model's REAL gas gap once the right one is used? NO LP.

`FINDING-caiso118-belly-price-undercommit-2026-07-24.md` (and the caiso-118b
RA-commitment-paradigm redirect that follows from it) rest on:

    "reality runs 2-3.6x MORE belly gas than the model"
    actual belly gas 8,461 / 9,633 / 10,537 MW  vs  model 4,260 / 3,721 / 2,947

`_caiso119_belly_gas_recheck.py` could not reproduce the ACTUAL side from CEMS
(it measured 5,084 / 4,435 / 3,535 MW gross, a 1.19-1.23x ratio) and traced the
caiso-118 numbers to EIA-930 CISO `NG: NG` at local hod 10-15 — the same raw 930
gas cell caiso-109 had ALREADY adjudicated as corrupted ("the caiso-108 -13.66
was the corrupted 930 NG cell") and replaced with the CEMS basis
(`gas_cems_grid + gas_cogen_grid`).

This probe settles it on three independent tests and then re-measures the true
gap so the lane can be re-pointed:

  T1  ANNUAL LEVEL. EIA-930 `NG: NG` annual TWh vs the committed bench CEMS
      basis (`gas_cems_grid + gas_cogen_grid`) vs raw CEMS gross. A series that
      exceeds metered CEMS grid gas by ~40% is carrying something that is not
      CAISO gas generation.

  T2  DIURNAL SHAPE — the decisive test. CAISO is a solar-belly ISO: gas MUST
      trough midday and peak in the evening ramp (the duck). Any candidate
      "actual" whose belly EXCEEDS its evening is inverted and cannot be a gas
      generation series, whatever its level.

  T3  ENERGY BALANCE. Does the candidate actual fit inside CAISO's belly supply
      stack (demand - solar - wind - nuclear - hydro - imports - storage)? A gas
      level that overfills the belly by many GW is refuted by construction.

  Then: the model's TRUE gas gap by class and hour-of-day on the surviving
  basis, which is what any commitment mechanism must actually close.

Run:  .venv/bin/python scripts/probes/_caiso119_gas_basis_adjudication.py
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BENCH = REPO / "frontend" / "data" / "backcast" / "bench" / "CAISO"
CAMPD = REPO / "data" / "raw" / "campd-unit-level"
KEEPER = REPO / "results" / "calibration" / "caiso_netrev_margin" / "hourly"
CISO_930 = REPO / "data" / "raw" / "eia-930-hourly" / "CISO hourly.parquet"
YEARS = (2023, 2024, 2025)
BELLY = (10, 11, 12, 13, 14, 15)
EVENING = (17, 18, 19, 20, 21)
GAS_CLASSES = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "CC_CHP", "CT_CHP")


def _930(year: int) -> pd.DataFrame:
    df = pd.read_parquet(CISO_930)
    df["lt"] = pd.to_datetime(df["Local time"])
    df = df[df["lt"].dt.year == year].copy()
    df["hod"] = df["lt"].dt.hour
    for c in ("NG: NG", "NG: SUN", "NG: WND", "NG: NUC", "NG: WAT", "NG: GEO",
              "NG: OTH", "NG: OIL", "NG: COL", "Demand", "Total interchange",
              "Net generation"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _cems(year: int) -> pd.DataFrame:
    with gzip.open(BENCH / f"{year}.json.gz") as fh:
        plants = {int(k): v for k, v in json.load(fh)["bench"]["plants"].items()}
    df = pd.read_parquet(CAMPD / f"CA_{year}.parquet")
    df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
    df = df.dropna(subset=["facilityId"])
    df = df[df["facilityId"].astype(int).isin(plants)].copy()
    df["group"] = df["facilityId"].astype(int).map(lambda f: plants[f]["group"])
    df["grossLoad"] = pd.to_numeric(df["grossLoad"], errors="coerce").fillna(0.0)
    return df


def _bench_annual(year: int) -> dict:
    with gzip.open(BENCH / f"{year}.json.gz") as fh:
        return json.load(fh)["bench"]["e930"]


def _model(year: int) -> pd.DataFrame:
    df = pd.read_parquet(KEEPER / f"class_hourly_{year}.parquet")
    df = df[df["pass"] == "P1"].copy()
    df["hod"] = df["hour"] % 24
    return df


def t1_annual() -> None:
    print("=" * 92)
    print("T1  ANNUAL LEVEL — is EIA-930 `NG: NG` a CAISO gas generation series?")
    print("=" * 92)
    print(f"{'year':>6}{'930 NG TWh':>13}{'bench CEMS grid TWh':>21}"
          f"{'CEMS gross TWh':>16}{'930 / CEMS-grid':>17}")
    for year in YEARS:
        n = _930(year)
        hrs = len(n)
        ng_twh = float(n["NG: NG"].mean()) * hrs / 1e6
        b = _bench_annual(year)
        cems_grid = b["gas_cems_grid"] + b["gas_cogen_grid"]
        c = _cems(year)
        gross_twh = float(c["grossLoad"].sum()) / 1e6
        print(f"{year:>6}{ng_twh:>13,.1f}{cems_grid:>21,.1f}{gross_twh:>16,.1f}"
              f"{ng_twh/cems_grid:>17.2f}")
    print("\n  READ: metered CEMS covers essentially all CAISO gas capacity >25 MW.")
    print("  A 930 series ~40% above metered gas GROSS output is not gas generation.")


def t2_shape() -> None:
    print("\n" + "=" * 92)
    print("T2  DIURNAL SHAPE — the decisive test (CAISO gas must trough midday)")
    print("=" * 92)
    print(f"{'year':>6}  {'series':<22}{'belly MW':>11}{'evening MW':>12}"
          f"{'annual MW':>11}{'belly/evening':>15}{'duck?':>8}")
    for year in YEARS:
        n = _930(year)
        c = _cems(year)
        m = _model(year)
        rows = []
        ng = n["NG: NG"]
        rows.append(("EIA-930 NG: NG",
                     ng[n["hod"].isin(BELLY)].mean(),
                     ng[n["hod"].isin(EVENING)].mean(), ng.mean()))
        nb = c[c["hour"].isin(BELLY)].groupby(["date", "hour"])["grossLoad"].sum().mean()
        ne = c[c["hour"].isin(EVENING)].groupby(["date", "hour"])["grossLoad"].sum().mean()
        na = c.groupby(["date", "hour"])["grossLoad"].sum().mean()
        rows.append(("CEMS gas (gross)", nb, ne, na))
        g = m[m["klass"].isin(GAS_CLASSES)]
        gb = g[g["hod"].isin(BELLY)].groupby("hour")["mw"].sum().mean()
        ge = g[g["hod"].isin(EVENING)].groupby("hour")["mw"].sum().mean()
        ga = g.groupby("hour")["mw"].sum().mean()
        rows.append(("MODEL keeper gas", gb, ge, ga))
        for i, (lab, b, e, a) in enumerate(rows):
            duck = "YES" if b < e else "INVERTED"
            yr = f"{year:>6}" if i == 0 else " " * 6
            print(f"{yr}  {lab:<22}{b:>11,.0f}{e:>12,.0f}{a:>11,.0f}"
                  f"{b/e:>15.2f}{duck:>8}")
        print()
    print("  READ: an INVERTED series (belly > evening) cannot be CAISO gas —")
    print("  it is the 930 residual/plug category, not metered generation.")


def t3_balance() -> None:
    print("=" * 92)
    print("T3  ENERGY BALANCE — does the candidate actual fit the belly supply stack?")
    print("=" * 92)
    for year in YEARS:
        n = _930(year)
        b = n[n["hod"].isin(BELLY)]
        dem = b["Demand"].mean()
        sun, wnd = b["NG: SUN"].mean(), b["NG: WND"].mean()
        nuc, wat = b["NG: NUC"].mean(), b["NG: WAT"].mean()
        geo, oth = b["NG: GEO"].mean(), b["NG: OTH"].mean()
        imp = -b["Total interchange"].mean()          # +ve = net import
        ng = b["NG: NG"].mean()
        resid = dem - (sun + wnd + nuc + wat + geo + oth + imp)
        c = _cems(year)
        cems_b = c[c["hour"].isin(BELLY)].groupby(["date", "hour"])["grossLoad"].sum().mean()
        print(f"\n  {year} belly (hod 10-15), EIA-930 CISO, MW:")
        print(f"    demand {dem:>9,.0f}   solar {sun:>8,.0f}  wind {wnd:>7,.0f}  "
              f"nuc {nuc:>6,.0f}  hydro {wat:>7,.0f}  geo {geo:>6,.0f}  oth {oth:>7,.0f}")
        print(f"    net import {imp:>6,.0f}")
        print(f"    -> RESIDUAL for gas (+ storage charge/export): {resid:>8,.0f} MW")
        print(f"       930 `NG: NG` claims      : {ng:>8,.0f} MW  "
              f"({'FITS' if ng <= resid + 500 else 'OVERFILLS by %.0f MW' % (ng - resid)})")
        print(f"       CEMS gas (gross) measures: {cems_b:>8,.0f} MW  "
              f"({'FITS' if cems_b <= resid + 500 else 'OVERFILLS'})")


def gap() -> None:
    print("\n" + "=" * 92)
    print("THE MODEL'S TRUE GAS GAP on the surviving (CEMS) basis, by class")
    print("=" * 92)
    for year in YEARS:
        c, m = _cems(year), _model(year)
        print(f"\n  --- {year} ---   {'class':<13}{'model MW':>11}{'CEMS MW':>10}"
              f"{'gap MW':>10}{'ratio':>8}   [annual, all hours]")
        tot_m = tot_c = 0.0
        for k in GAS_CLASSES:
            cm = c[c["group"] == k].groupby(["date", "hour"])["grossLoad"].sum().mean()
            cm = 0.0 if np.isnan(cm) else float(cm)
            mm = float(m[m["klass"] == k].groupby("hour")["mw"].sum().mean())
            tot_m += mm
            tot_c += cm
            r = cm / mm if mm > 1 else float("nan")
            print(f"{'':>17}{k:<13}{mm:>11,.0f}{cm:>10,.0f}{cm-mm:>10,.0f}{r:>8.2f}")
        print(f"{'':>17}{'TOTAL':<13}{tot_m:>11,.0f}{tot_c:>10,.0f}"
              f"{tot_c-tot_m:>10,.0f}{tot_c/tot_m:>8.2f}")

    print("\n" + "=" * 92)
    print("GAP BY HOUR-OF-DAY (CEMS gross minus model, all gas classes, MW)")
    print("=" * 92)
    print(f"{'hod':>5}" + "".join(f"{y:>10}" for y in YEARS))
    prof = {}
    for year in YEARS:
        c, m = _cems(year), _model(year)
        cc = c.groupby("hour")["grossLoad"].sum() / c.groupby(["date", "hour"]).ngroups * 24
        ch = c.groupby(["date", "hour"])["grossLoad"].sum().groupby(level=1).mean()
        g = m[m["klass"].isin(GAS_CLASSES)]
        mh = g.groupby("hod")["mw"].sum() / (len(g["hour"].unique()) / 24)
        prof[year] = (ch, mh)
    for h in range(24):
        row = f"{h:>5}"
        for year in YEARS:
            ch, mh = prof[year]
            row += f"{ch.get(h, 0) - mh.get(h, 0):>10,.0f}"
        print(row)


def main() -> None:
    t1_annual()
    t2_shape()
    t3_balance()
    gap()


if __name__ == "__main__":
    main()
