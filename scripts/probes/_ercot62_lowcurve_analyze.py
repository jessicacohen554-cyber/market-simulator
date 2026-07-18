"""ERCOT-62 A/B analysis: the low-curve probe vs the keeper reconstruction.

Compares ``ercot62_lowcurve_2023`` (keeper + ercot_offer_surface_lowcurve)
against ``ercot62_keeper_2023`` (zero-delta reconstruction) on the quantities
the storage/price-formation circle is about:

* price scores (C3a/C3b proxies) and the DAILY top4-bottom4 spread vs measured
  RT/DA (the battery-arbitrage driver);
* trough price-band occupancy (h below $10/$15/$20 overnight+midday);
* storage throughput, binding-hour discharge, discharge hour-of-day profile;
* binding-regime (top-30% net-load) class mix — does the ST_GAS/thermal excess
  narrow endogenously (the ERCOT-61 conservation shadow);
* class annual energy shifts (the C1 coal<->gas shuffle gate);
* LP health (slack/dump).

No LP solve — reads the two bundles. Rule-16 diagnostic; never registered.

Usage::

    python scripts/probes/_ercot62_lowcurve_analyze.py \
        [--a ercot62_keeper_2023] [--b ercot62_lowcurve_2023] [--year 2023]
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))
sys.path.insert(0, str(REPO / "src"))

from derive_ercot_rtolcap_forward import _net_load  # noqa: E402


def lw_price(bundle: Path, year: int) -> np.ndarray:
    sysdf = pd.read_parquet(bundle / "system.parquet")
    sysdf = sysdf[(sysdf["pass"] == "P1") & (sysdf["year"] == year)]
    pw = sysdf.groupby("hour").apply(
        lambda d: (d["price"] * d["demand"]).sum() / d["demand"].sum(),
        include_groups=False,
    )
    return pw.reindex(range(8760)).to_numpy()


def sys_frame(bundle: Path, year: int) -> pd.DataFrame:
    sysdf = pd.read_parquet(bundle / "system.parquet")
    return sysdf[(sysdf["pass"] == "P1") & (sysdf["year"] == year)]


def daily_spread(x: np.ndarray) -> np.ndarray:
    d = x[:8760].reshape(365, 24)
    s = np.sort(d, axis=1)
    return s[:, -4:].mean(1) - s[:, :4].mean(1)


def class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    disp = pd.read_parquet(
        bundle / "dispatch" / f"{year}_P1.parquet",
        columns=["pass", "klass", "hour", "mw"],
    )
    disp = disp[disp["pass"] == "P1"]
    return (
        disp.groupby(["klass", "hour"], observed=True)["mw"]
        .sum()
        .unstack(fill_value=0.0)
    )


def storage_series(bundle: Path, year: int):
    p = bundle / "storage" / f"{year}_P1.parquet"
    if not p.exists():
        p = bundle / "storage.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    if "pass" in df.columns:
        df = df[df["pass"] == "P1"]
    if "year" in df.columns:
        df = df[df["year"] == year]
    return df


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--a", default="ercot62_keeper_2023")
    ap.add_argument("--b", default="ercot62_lowcurve_2023")
    ap.add_argument("--year", type=int, default=2023)
    args = ap.parse_args()
    year = args.year

    A = REPO / "results" / "calibration" / args.a
    B = REPO / "results" / "calibration" / args.b
    nl = _net_load(year)[:8760]
    bind = nl >= np.percentile(nl, 70.0)
    hod = np.arange(8760) % 24

    lmp = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_zonal_ERCOT.parquet"
    )
    hub = lmp[(lmp["year"] == year) & (lmp["settlement_point"] == "HB_HUBAVG")]
    hub = hub.set_index("hour")
    rt = hub["rt"].reindex(range(8760)).to_numpy()

    pa, pb = lw_price(A, year), lw_price(B, year)

    print(f"== ERCOT-62 A/B — {args.a} vs {args.b}, {year} ==")
    print(
        f"lw mean price: A {np.nanmean(pa):.2f}  B {np.nanmean(pb):.2f}  RT {np.nanmean(rt):.2f}"
    )

    sa, sb, sr = daily_spread(pa), daily_spread(pb), daily_spread(rt)
    print("\n-- daily top4-bottom4 spread ($/MWh) --")
    for name, s in (("A (keeper)", sa), ("B (lowcurve)", sb), ("RT actual", sr)):
        print(
            f"  {name:<12} median {np.nanmedian(s):6.1f}  p25 {np.nanpercentile(s, 25):6.1f}"
            f"  p75 {np.nanpercentile(s, 75):6.1f}  days>24.25 {(s > 24.25).sum():3d}"
            f"  days>40 {(s > 40).sum():3d}"
        )

    trough = np.isin(hod, [0, 1, 2, 3, 4, 5, 23]) | ((hod >= 9) & (hod <= 15))
    print("\n-- trough (overnight+midday) hours below price bands --")
    for thr in (0, 10, 15, 20):
        # <$0 (ERCOT-65): the NEGATIVE band — RT 2023 spent 137 lw-hours
        # below zero; the flat-PTC keeper never does at the lw hub.
        print(
            f"  <${thr}: A {int(((pa < thr) & trough).sum()):4d}  "
            f"B {int(((pb < thr) & trough).sum()):4d}  RT {int(((rt < thr) & trough).sum()):4d}"
        )
    print(
        "  <$0 all-hours: "
        f"A {int((pa < 0).sum()):4d}  B {int((pb < 0).sum()):4d}  "
        f"RT {int((rt < 0).sum()):4d}"
    )

    # storage
    for name, bundle in (("A", A), ("B", B)):
        st = storage_series(bundle, year)
        if st is None:
            print(f"  {name}: no storage parquet")
            continue
        dis_col = "discharge_mw" if "discharge_mw" in st.columns else "discharge"
        g = st.groupby("hour")[dis_col].sum().reindex(range(8760)).fillna(0.0)
        dis = g.to_numpy()
        prof = [dis[hod == h].mean() for h in range(24)]
        print(
            f"\n  storage {name}: throughput {dis.sum() / 1e6:.2f} TWh, "
            f"binding-hr mean {dis[bind].mean():,.0f} MW, "
            f"HE18/19 {prof[17]:,.0f}/{prof[18]:,.0f} MW, morning HE06-08 "
            f"{np.mean(prof[5:8]):,.0f} MW, midday HE11-15 {np.mean(prof[10:15]):,.0f} MW"
        )

    # binding-regime class mix + annual energies
    ka, kb = class_hourly(A, year), class_hourly(B, year)
    ka = ka.reindex(columns=range(8760), fill_value=0.0)
    kb = kb.reindex(columns=range(8760), fill_value=0.0)
    print("\n-- class binding-hour mean MW (A -> B) / annual TWh (A -> B) --")
    for cls in (
        "ST_GAS",
        "CC_REGULAR",
        "CC_CHP",
        "CT_PEAKER",
        "COAL_PRB",
        "COAL_LIGNITE",
        "wind",
        "solar",
    ):
        rows_a = [c for c in ka.index if c == cls]
        rows_b = [c for c in kb.index if c == cls]
        va = ka.loc[rows_a].sum(0).to_numpy() if rows_a else np.zeros(8760)
        vb = kb.loc[rows_b].sum(0).to_numpy() if rows_b else np.zeros(8760)
        print(
            f"  {cls:<13} bind {va[bind].mean():8,.0f} -> {vb[bind].mean():8,.0f} "
            f"({vb[bind].mean() - va[bind].mean():+6,.0f})   "
            f"ann {va.sum() / 1e6:6.2f} -> {vb.sum() / 1e6:6.2f} TWh "
            f"({(vb.sum() - va.sum()) / 1e6:+5.2f})"
        )

    # LP health
    for name, bundle in (("A", A), ("B", B)):
        s = sys_frame(bundle, year)
        print(
            f"  {name}: slack {s['slack'].sum() / 1e3:.1f} GWh, dump {s['dump'].sum() / 1e3:.1f} GWh"
        )


if __name__ == "__main__":
    main()
