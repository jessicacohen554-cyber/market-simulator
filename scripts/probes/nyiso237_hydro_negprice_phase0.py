"""nyiso-237 phase 0 (ZERO LP): does MEASURED NYISO hydro hold up or fall back at the
bottom of the real WEST-zone RT price distribution, and what sets the model's
non-positive Upstate_West prices?

Falsification test for the "use it or lose it was implemented as only lose it"
hypothesis (RESULT-nyiso236 A3): if measured hydro holds up in hours where the
real WEST RT LBMP is <= $0 the repair (period budget as an EQUALITY for a
no-pondage plant) is warranted; if it falls back, the hypothesis is refuted.

Every input is committed:

* ``data/raw/eia-930-hourly/NYIS hourly.parquet`` column ``NG: WAT`` (the fleet
  meter; NYIS is NOT in ``EIA930_PS_FOLDED_INTO_WAT``).
* ``data/raw/lmp-data/NYISO/<yyyymm>01realtime_zone_csv.zip`` 5-minute zonal RT
  LBMP, averaged to the hour (all 12 months of 2022; 2023-06/12, 2024-02..06/09,
  2025-08).
* ``data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet`` hub hourly RT.
* the keeper's committed ``hourly/system_<y>.parquet`` +
  ``hourly/class_hourly_<y>.parquet``; optionally a nyiso-236 arm leg bundle
  (``--arm-bundle``) carrying the bundle-root ``system.parquet``, ``flows.parquet``,
  ``storage.parquet`` and ``dispatch/<y>_P1.parquet``.

All comparisons are (year x month x hour-of-day) matched, so neither the seasonal
water path nor the Treaty's diurnal scenic-flow schedule can confound them.

Usage::

    python3 scripts/probes/nyiso237_hydro_negprice_phase0.py \\
        --keeper results/calibration/nyiso235_gasrepair_span \\
        [--arm-bundle <dir of the nyiso-236 2022 leg>] [--year 2022]

Record: docs/RESULT-nyiso237-hydro-negative-price-phase0-2026-09-16.md.
"""
from __future__ import annotations

import argparse
import glob
import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

ZONE_MAP = {
    "WEST": "Upstate_West",
    "GENESE": "Upstate_West",
    "CENTRL": "Upstate_West",
    "NORTH": "Upstate_West",
    "MHK VL": "Upstate_West",
    "CAPITL": "Capital_Hudson",
    "HUD VL": "Capital_Hudson",
    "MILLWD": "Lower_Hudson",
    "DUNWOD": "Lower_Hudson",
    "N.Y.C.": "NYC",
    "LONGIL": "Long_Island",
}
MODEL_ZONES = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]


def load_eia930_hydro() -> pd.DataFrame:
    """Return the NYIS ``NG: WAT`` / ``Demand`` / ``Total interchange`` series by local hour."""
    h = pd.read_parquet(ROOT / "data/raw/eia-930-hourly/NYIS hourly.parquet")
    h = h.sort_values("UTC time")
    h["ts"] = pd.to_datetime(h["Local time"])
    h = h[["ts", "NG: WAT", "NG: WND", "NG: NUC", "Demand", "Total interchange"]]
    h = h.rename(columns={"NG: WAT": "wat"})
    h = h.groupby("ts", as_index=False).mean()  # DST fall-back duplicate local hour
    h["year"], h["month"], h["hod"] = h.ts.dt.year, h.ts.dt.month, h.ts.dt.hour
    return h


def load_zonal_rt() -> pd.DataFrame:
    """Return hourly-mean zonal RT LBMP for every committed NYISO 5-minute zip."""
    frames = []
    for z in sorted(glob.glob(str(ROOT / "data/raw/lmp-data/NYISO/*realtime_zone_csv.zip"))):
        with zipfile.ZipFile(z) as zf:
            for name in zf.namelist():
                if not name.endswith(".csv"):
                    continue
                df = pd.read_csv(io.BytesIO(zf.read(name)))
                df = df[df["Name"].isin(ZONE_MAP)]
                frames.append(df[["Time Stamp", "Name", "LBMP ($/MWHr)"]])
    d = pd.concat(frames)
    d["ts"] = pd.to_datetime(d["Time Stamp"], format="%m/%d/%Y %H:%M:%S")
    d["hts"] = (d.ts - pd.Timedelta(seconds=1)).dt.floor("h")  # interval-ending stamps
    d["mz"] = d.Name.map(ZONE_MAP)
    a = d.groupby(["hts", "mz"])["LBMP ($/MWHr)"].mean().unstack("mz").reset_index()
    return a.rename(columns={"hts": "ts"})


def anomaly(df: pd.DataFrame, val: str) -> pd.Series:
    """``val`` minus its (year, month, hour-of-day) mean."""
    return df[val] - df.groupby(["year", "month", "hod"])[val].transform("mean")


def matched_table(df: pd.DataFrame, price: str, val: str, thr: float, by: tuple[str, ...]) -> pd.DataFrame:
    """Mean of ``val`` in hours ``price <= thr`` against the matched mean of the other hours."""
    d = df.copy()
    d["low"] = d[price] <= thr
    rows = []
    for key, g in d.groupby(list(by)):
        n = int(g.low.sum())
        if n == 0:
            rows.append(dict(key=key, n=0))
            continue
        cell = g[~g.low].groupby(["year", "month", "hod"])[val].mean().rename("ref")
        gl = g[g.low].join(cell, on=["year", "month", "hod"]).dropna(subset=["ref"])
        rows.append(
            dict(
                key=key,
                n=n,
                low_mean=gl[val].mean(),
                matched=gl.ref.mean(),
                ratio=gl[val].mean() / gl.ref.mean(),
                delta_mw=(gl[val] - gl.ref).mean(),
            )
        )
    return pd.DataFrame(rows)


def model_frame(system: pd.DataFrame, klass: pd.DataFrame, year: int) -> pd.DataFrame:
    """Upstate_West P1 price + fleet hydro MW on the model clock, with (month, hod)."""
    s = system[(system.year == year) & (system["pass"] == "P1")]
    pw = s[s.zone == "Upstate_West"].set_index("hour")["price"].rename("p")
    hy = klass[(klass.year == year) & (klass["pass"] == "P1") & (klass.klass == "hydro")]
    hy = hy.set_index("hour")["mw"].rename("wat")
    m = pd.concat([pw, hy], axis=1).reset_index()
    m["ts"] = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(m.hour, unit="h")
    m["year"], m["month"], m["hod"] = m.ts.dt.year, m.ts.dt.month, m.ts.dt.hour
    return m


def main() -> None:
    """Run the phase-0 census and print every table the RESULT cites."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--keeper", default="results/calibration/nyiso235_gasrepair_span")
    ap.add_argument("--arm-bundle", default=None, help="a nyiso-236 per-year leg bundle dir")
    ap.add_argument("--year", type=int, default=2022)
    args = ap.parse_args()
    pd.set_option("display.width", 220)

    h = load_eia930_hydro()
    z = load_zonal_rt()
    act = h.merge(z, on="ts", how="inner")
    print("zonal-joined hours by year:", act.groupby("year").size().to_dict())

    # ---- A. measured hydro at the bottom of the real WEST price distribution
    print("\n=== A. ACTUAL: EIA-930 hydro vs real Upstate_West (5-zone mean) RT price, matched ===")
    for thr in (0.0, 5.0, 10.0, 15.0):
        t = matched_table(act, "Upstate_West", "wat", thr, ("year",))
        print(f"p <= ${thr:.0f}:")
        print(t.round(3).to_string(index=False))
    a = act[act.year == args.year].copy()
    a["anom"] = anomaly(a, "wat")
    a["pq"] = a.groupby("month")["Upstate_West"].transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=False))
    a["dq"] = a.groupby("month")["Demand"].transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=False))
    print(f"\n{args.year} actual hydro anomaly by within-month WEST price quintile:", a.groupby("pq").anom.mean().round(0).to_dict())
    print(f"{args.year} actual hydro anomaly by within-month demand quintile:  ", a.groupby("dq").anom.mean().round(0).to_dict())
    print(f"{args.year} actual WEST price <= $0 values:", sorted(a.loc[a.Upstate_West <= 0, "Upstate_West"].round(1).tolist()))

    # ---- B. the model's non-positive Upstate_West hours vs the real ones
    keeper = ROOT / args.keeper
    ks = pd.read_parquet(keeper / f"hourly/system_{args.year}.parquet")
    kc = pd.read_parquet(keeper / f"hourly/class_hourly_{args.year}.parquet")
    km = model_frame(ks, kc, args.year)
    print(f"\n=== B. {args.year} hours <= $0 / <= $5 in Upstate_West: actual vs keeper, by month ===")
    cen = pd.DataFrame(
        {
            "actual_le0": a.groupby("month").apply(lambda g: int((g.Upstate_West <= 0).sum())),
            "actual_le5": a.groupby("month").apply(lambda g: int((g.Upstate_West <= 5).sum())),
            "keeper_le0": km.groupby("month").apply(lambda g: int((g.p <= 0).sum())),
            "keeper_le5": km.groupby("month").apply(lambda g: int((g.p <= 5).sum())),
            "actual_mean": a.groupby("month").Upstate_West.mean().round(1),
            "keeper_mean": km.groupby("month").p.mean().round(1),
        }
    )
    print(cen.to_string())
    print("keeper price values in its <= $0 hours (rounded):", km[km.p <= 0].p.round(0).value_counts().sort_index().to_dict())
    print("\nkeeper hydro in its own <= $0 hours, matched:")
    print(matched_table(km, "p", "wat", 0.0, ("year",)).round(3).to_string(index=False))

    # monthly zonal error, every zone, every month with zonal data
    kall = []
    for y in sorted(act.year.unique()):
        f = keeper / f"hourly/system_{y}.parquet"
        if not f.exists():
            continue
        s = pd.read_parquet(f)
        s = s[s["pass"] == "P1"]
        s["ts"] = pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(s.hour, unit="h")
        s["year"], s["month"] = y, s.ts.dt.month
        kall.append(s)
    kall = pd.concat(kall)
    kmz = kall.groupby(["year", "month", "zone"]).price.mean().unstack("zone")
    amz = act.groupby(["year", "month"])[MODEL_ZONES].mean()
    err = (kmz[MODEL_ZONES] - amz).dropna().round(1)
    print("\n=== C. keeper minus actual monthly mean RT price by model zone ($/MWh) ===")
    print(err.to_string())

    # ---- D. the arm leg: what the West is doing in its non-positive hours
    if args.arm_bundle:
        B = Path(args.arm_bundle)
        sy = pd.read_parquet(B / "system.parquet")
        sy = sy[(sy["pass"] == "P1") & (sy.zone == "Upstate_West")].set_index("hour")
        T = len(sy)
        ts = pd.Timestamp(f"{args.year}-01-01") + pd.to_timedelta(np.arange(T), unit="h")
        d = pd.read_parquet(B / f"dispatch/{args.year}_P1.parquet", columns=["zone", "klass", "hour", "mw"])
        duw = d[d.zone == "Upstate_West"].groupby(["klass", "hour"]).mw.sum().unstack("klass").reindex(range(T)).fillna(0)
        fl = pd.read_parquet(B / "flows.parquet")
        fl = fl[fl["pass"] == "P1"]
        fw = fl.pivot_table(index="hour", columns=["from_zone", "to_zone"], values="mw").reindex(range(T))
        fw.columns = [f"{x}->{y}" for x, y in fw.columns]
        st = pd.read_parquet(B / "storage.parquet")
        st = st[(st["pass"] == "P1") & (st.zone == "Upstate_West")].groupby("hour")[["charge_mw", "discharge_mw"]].sum().reindex(range(T)).fillna(0)
        X = pd.concat([duw, fw[[c for c in fw.columns if "Upstate_West" in c]], st, sy[["price", "demand", "dump", "slack"]]], axis=1)
        X["month"], X["hod"] = ts.month, ts.hour
        X["neg"] = X.price <= 0
        cell = X[~X.neg].groupby(["month", "hod"]).mean(numeric_only=True)
        Xn = X[X.neg]
        ref = cell.reindex(pd.MultiIndex.from_arrays([Xn.month, Xn.hod])).reset_index(drop=True)
        ref.index = Xn.index
        cols = [c for c in X.columns if c not in ("month", "hod", "neg")]
        out = pd.DataFrame({"neg_mean": Xn[cols].mean(), "matched": ref[cols].mean()})
        out["delta"] = out.neg_mean - out.matched
        print(f"\n=== D. ARM {args.year} Upstate_West in its {len(Xn)} hours price <= $0 vs matched (MW) ===")
        print(out.round(0).to_string())
        ce = X["Upstate_West->Capital_Hudson"]
        cap = ce.groupby(X.month).max()
        print("\nCentral-East monthly cap (MW):", cap.round(0).to_dict())
        print("hours at cap by month:", (ce >= cap.reindex(X.month).values - 0.5).groupby(X.month).sum().to_dict())
        # per-plant Niagara / St Lawrence
        dp = pd.read_parquet(B / f"dispatch/{args.year}_P1.parquet", columns=["plant_code", "hour", "mw", "lmp"])
        for pc, nm in ((2693, "Niagara"), (2694, "St Lawrence")):
            u = dp[dp.plant_code == pc].groupby("hour").agg(mw=("mw", "sum"), p=("lmp", "first")).reindex(range(T))
            u["year"], u["month"], u["hod"] = args.year, ts.month, ts.hour
            print(f"\n{nm} (arm {args.year}) MW in hours own-zone price <= $0, matched:")
            print(matched_table(u, "p", "mw", 0.0, ("year", "month")).round(3).to_string(index=False))
        # G2 loss by month vs the keeper
        ah = pd.read_parquet(B / f"hourly/class_hourly_{args.year}.parquet")
        ah = ah[(ah["pass"] == "P1") & (ah.klass == "hydro")].sort_values("hour")
        kh = kc[(kc["pass"] == "P1") & (kc.klass == "hydro")].sort_values("hour")
        loss = pd.DataFrame({"m": ts.month, "arm": ah.mw.values, "keeper": kh.mw.values}).groupby("m").sum() / 1e3
        loss["loss_GWh"] = (loss.arm - loss.keeper).round(1)
        print(f"\narm minus keeper hydro by month, {args.year} (GWh):", loss.loss_GWh.to_dict(), " total", round(loss.loss_GWh.sum(), 1))

    # ---- E. the real system in the model's non-positive hours
    hy = h[h.year == args.year].sort_values("ts").head(len(km)).reset_index(drop=True)
    hy["negm"] = (km.sort_values("hour").p.values <= 0)[: len(hy)]
    print(f"\n=== E. ACTUAL NYIS series in the keeper's {int(hy.negm.sum())} non-positive Upstate_West hours (matched) ===")
    for col in ("Total interchange", "wat", "NG: WND", "NG: NUC", "Demand"):
        c = hy[~hy.negm].groupby(["month", "hod"])[col].mean().rename("ref")
        g = hy[hy.negm].join(c, on=["month", "hod"])
        print(f"  {col:18s} {g[col].mean():8.0f}  matched {g.ref.mean():8.0f}  delta {(g[col] - g.ref).mean():7.0f}")


if __name__ == "__main__":
    main()
