#!/usr/bin/env python3
"""miso-262 phase 0: is MISO's seam a SOURCE of volume error, or a TRANSDUCER of the price residual?

ZERO LP (rule 32 ``[R-SHARD]`` (a)).  Every number below is read from committed
artifacts — the designated keeper's own hourly sidecars, the committed bench
parts, the committed seam ladders, and two measured on-disk series.  Nothing is
fetched and no solve is replayed.

Sources, all committed
----------------------
* ``results/calibration/miso260_seam_span/hourly/{class_hourly,system}_<y>.parquet``
  — the keeper's per-class and per-zone hourlies.  ``klass='import'`` is the
  priced import/export node's net injection into MISO, i.e. net IMPORTS in MW
  (``run_calibration_full.py`` computes net interchange as ``-(that sum)``).
* ``frontend/data/backcast/bench/MISO/<y>.json.gz`` — ``classFull`` (the C1
  gating basis, grid-delivered per class) and the per-plant ``campd`` blob
  (uint8 CF% of ``npl``), which gives MEASURED hourly MW per model class without
  touching ``data/raw/campd-unit-level``.
* ``derive_miso_seam_ladders.load_joined()`` — the same import-positive per-seam
  EIA-930 series, on the LP's clock, that the armed ladder is itself derived
  from.  Re-using the derive script's own loader means the measured side cannot
  drift from the mechanism's own definition.
* ``interchange_config.MISO_SEAM_LADDER_BY_YEAR`` — the 32 committed band prices.
* ``data/raw/eia-930/EIA930_BALANCE_<y>_*.parquet`` — MISO's own measured demand,
  used to check the model's load basis independently of the bench.

What each section answers
-------------------------
A  per-class model-vs-bench TWh on the C1 gating basis, all six years.
B  model net imports vs measured, annual level + hourly fidelity + hour-of-day.
C  the COAL_BIT / COAL_PRB deficit resolved by hour-of-day and by load decile,
   against MEASURED CEMS hourly for the same classes.
D  the cross-year relation between the model's own price bias and the seam's
   volume error — the finding this probe exists for.
E  how often a seam band is the marginal (price-setting) offer.
F  the model's load basis against MISO's measured EIA-930 demand.

Usage::

    uv run python scripts/probes/_miso262_seam_price_transducer.py
    uv run python scripts/probes/_miso262_seam_price_transducer.py --sections A D
"""

from __future__ import annotations

import argparse
import base64
import glob
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "data"))

from derive_miso_seam_ladders import load_joined  # noqa: E402
from market_sim.config.interchange_config import (  # noqa: E402
    MISO_SEAM_LADDER_BY_YEAR,
)

BUNDLE = ROOT / "results/calibration/miso260_seam_span"
YEARS = (2020, 2021, 2022, 2023, 2024, 2025)
SEAMS = ("PJM", "SPP", "South", "Manitoba")
T = 8760
TWH = 1e6
C1_CLASSES = (
    "COAL_BIT",
    "COAL_PRB",
    "COAL_LIGNITE",
    "CC_REGULAR",
    "CT_PEAKER",
    "ST_GAS",
    "CC_CHP",
    "CT_CHP",
    "ST_CHP",
    "OTHER_FOSSIL",
)


# --------------------------------------------------------------------------- #
# readers
# --------------------------------------------------------------------------- #
def bench(year: int) -> dict:
    """Return the committed bench part's ``bench`` block for one year."""
    with gzip.open(ROOT / f"frontend/data/backcast/bench/MISO/{year}.json.gz") as fh:
        return json.load(fh)["bench"]


def payload_model_twh(year: int) -> dict[str, float]:
    """Return the registered run payload's per-class model TWh (the scored basis).

    This is the dual-fuel-reattributed view the scorer compares against
    ``classFull``; it is NOT the raw ``class_hourly`` sum, which books a
    dual-fuel class's oil leg under the gas class.
    """
    p = ROOT / "frontend/data/backcast/runs/2026-09-16-miso-260-seam-ladder.js"
    s = p.read_text()
    blob = s[s.index(']="') + 3 : s.rindex('"')]
    d = json.loads(gzip.decompress(base64.b64decode(blob)))
    return d["years"][str(year)]["gmModel"]


def class_hourly(year: int, klass: str) -> np.ndarray:
    """Return the keeper's P1 hourly MW for one class."""
    d = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    d = d[(d["pass"] == "P1") & (d["klass"] == klass)]
    return d.sort_values("hour")["mw"].to_numpy(dtype=float)


def measured_class_hourly(year: int, klass: str) -> tuple[np.ndarray, int]:
    """Return measured CEMS hourly MW for one model class, and the plant count.

    Decoded from the bench part's own per-plant ``campd`` blob, so the plant set
    and the class map are the bench's, not a re-derivation.
    """
    out = np.zeros(T)
    n = 0
    for p in bench(year)["plants"].values():
        if p.get("group") != klass or p.get("nodata"):
            continue
        cf = np.frombuffer(base64.b64decode(p["campd"]), dtype=np.uint8).astype(float)
        out += cf / 100.0 * float(p["npl"])
        n += 1
    return out, n


def model_price_demand(year: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (load-weighted hourly price, hourly system demand) for the keeper."""
    s = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    g = (
        s.assign(w=s["price"] * s["demand"])
        .groupby("hour")[["w", "demand"]]
        .sum()
        .sort_index()
    )
    return (g["w"] / g["demand"]).to_numpy(dtype=float), g["demand"].to_numpy(dtype=float)


def measured_seam(joined: pd.DataFrame, year: int) -> np.ndarray:
    """Return measured import-positive net flow over the four priced seams."""
    sub = joined.loc[year]
    cols = [c for c in SEAMS if c in sub.columns]
    return sub[cols].sum(axis=1).to_numpy(dtype=float)


# --------------------------------------------------------------------------- #
# sections
# --------------------------------------------------------------------------- #
def section_a() -> None:
    print("\nA. C1 GATING BASIS — model vs bench classFull, TWh (band +/-8 TWh)")
    head = "".join(f"{y:>23}" for y in YEARS)
    print(f"{'class':<14}{head}")
    for k in C1_CLASSES:
        line = f"{k:<14}"
        for y in YEARS:
            m = payload_model_twh(y).get(k)
            a = bench(y)["classFull"].get(k)
            if m is None or a is None:
                line += f"{'-':>23}"
                continue
            line += f"{m:7.2f} /{a:7.2f} /{m - a:+6.2f}"
        print(line)
    print(f"\n{'coal3 (BIT+PRB+LIG)':<20}")
    for y in YEARS:
        gm, cf = payload_model_twh(y), bench(y)["classFull"]
        ks = ("COAL_BIT", "COAL_PRB", "COAL_LIGNITE")
        m = sum(gm[k] for k in ks)
        a = sum(cf[k] for k in ks)
        print(f"  {y}  model {m:8.3f}  bench {a:8.3f}  d {m - a:+7.3f}")


def section_b(joined: pd.DataFrame) -> None:
    print("\nB. SEAM VOLUME AND SCHEDULE — model net imports vs measured EIA-930")
    rows = []
    for y in YEARS:
        m = class_hourly(y, "import")
        a = measured_seam(joined, y)
        ok = np.isfinite(a)
        rows.append(
            dict(
                year=y,
                model_twh=m.sum() / TWH,
                meas_twh=np.nansum(a) / TWH,
                d_twh=(m.sum() - np.nansum(a)) / TWH,
                hourly_r=float(np.corrcoef(m[ok], a[ok])[0, 1]),
                mae_mw=float(np.mean(np.abs(m[ok] - a[ok]))),
                sched_mismatch_twh=float(np.abs(m - np.nan_to_num(a)).sum()) / 2 / TWH,
                dur_mismatch_twh=float(
                    np.abs(np.sort(m) - np.sort(np.nan_to_num(a))).sum()
                )
                / 2
                / TWH,
            )
        )
    df = pd.DataFrame(rows).set_index("year")
    df["ordering_only_twh"] = df["sched_mismatch_twh"] - df["dur_mismatch_twh"]
    print(df.round(3).to_string())
    print("\n   hour-of-day mean MW (model | measured)")
    for y in (2020, 2023):
        m = class_hourly(y, "import").reshape(-1, 24).mean(axis=0)
        a = np.nanmean(np.nan_to_num(measured_seam(joined, y)).reshape(-1, 24), axis=0)
        print(f"   {y} model " + " ".join(f"{v:6.0f}" for v in m))
        print(f"   {y} meas  " + " ".join(f"{v:6.0f}" for v in a))


def section_c(joined: pd.DataFrame) -> None:
    print("\nC. WHICH HOURS IS COAL SHORT IN — model vs MEASURED CEMS hourly")
    for y in (2020, 2023):
        mb, nb = measured_class_hourly(y, "COAL_BIT")
        mp, npr = measured_class_hourly(y, "COAL_PRB")
        b, p = class_hourly(y, "COAL_BIT"), class_hourly(y, "COAL_PRB")
        cf = bench(y)["classFull"]
        # CEMS is gross; rescale to the bench's grid-delivered level so only the
        # SHAPE is compared. The level question is section A's.
        sb = mb * (cf["COAL_BIT"] * TWH / mb.sum())
        sp = mp * (cf["COAL_PRB"] * TWH / mp.sum())
        db, dp = b - sb, p - sp
        imp = class_hourly(y, "import")
        a = np.nan_to_num(measured_seam(joined, y))
        _, dem = model_price_demand(y)
        print(
            f"\n   {y}: COAL_BIT {nb} plants, COAL_PRB {npr}; hourly r(model,meas) "
            f"BIT {np.corrcoef(b, sb)[0, 1]:.3f} PRB {np.corrcoef(p, sp)[0, 1]:.3f}; "
            f"corr(BIT deficit, import error) {np.corrcoef(db, imp - a)[0, 1]:+.3f}"
        )
        q = pd.qcut(pd.Series(dem), 10, labels=False, duplicates="drop")
        t = (
            pd.DataFrame(
                {
                    "BIT_model": b,
                    "BIT_meas": sb,
                    "BIT_def": db,
                    "PRB_def": dp,
                    "imp_model": imp,
                    "imp_meas": a,
                    "imp_err": imp - a,
                    "q": q,
                }
            )
            .groupby("q")
            .mean()
        )
        print("   mean MW by decile of model load:")
        print(t.round(0).to_string())


def section_d(joined: pd.DataFrame) -> None:
    print("\nD. THE SEAM AS A PRICE TRANSDUCER — price bias vs seam volume error")
    bias_rt, bias_da, err = [], [], []
    for y in YEARS:
        p, _ = model_price_demand(y)
        sub = joined.loc[y]
        a = measured_seam(joined, y)
        rt = sub["rt"].to_numpy(dtype=float)
        da = sub["da"].to_numpy(dtype=float)
        bias_rt.append(100 * (np.mean(p) / np.nanmean(rt) - 1))
        bias_da.append(100 * (np.mean(p) / np.nanmean(da) - 1))
        err.append(float(np.nansum(class_hourly(y, "import") - a)) / TWH)
        print(
            f"   {y}  model ${np.mean(p):6.2f}  RT ${np.nanmean(rt):6.2f}  "
            f"DA ${np.nanmean(da):6.2f}   bias vs RT {bias_rt[-1]:+7.2f}%   "
            f"seam volume error {err[-1]:+7.3f} TWh"
        )
    e = np.asarray(err)
    for nm, b in (("RT", np.asarray(bias_rt)), ("DA", np.asarray(bias_da))):
        r = float(np.corrcoef(b, e)[0, 1])
        slope, icept = np.polyfit(b, e, 1)
        loo = [
            np.polyfit(np.delete(b, k), np.delete(e, k), 1)[0] for k in range(len(b))
        ]
        print(
            f"   vs {nm}: r = {r:+.4f}   slope = {slope:.4f} TWh per +1 pp of price "
            f"bias   intercept = {icept:+.3f} TWh"
        )
        print(
            f"           residuals TWh "
            + " ".join(f"{v:+.2f}" for v in e - (slope * b + icept))
            + f"   leave-one-out slopes "
            + " ".join(f"{v:.3f}" for v in loo)
        )
    print("\n   price duration, model vs measured RT ($/MWh)")
    qs = (1, 5, 10, 25, 50, 75, 90, 95, 99)
    print("   " + f"{'year':<6}{'src':<7}" + "".join(f"{f'p{q}':>9}" for q in qs))
    for y in YEARS:
        p, _ = model_price_demand(y)
        rt = joined.loc[y]["rt"].to_numpy(dtype=float)
        print(f"   {y:<6}{'model':<7}" + "".join(f"{np.percentile(p, q):9.2f}" for q in qs))
        print(f"   {'':<6}{'RT':<7}" + "".join(f"{np.nanpercentile(rt, q):9.2f}" for q in qs))


def section_e() -> None:
    print("\nE. IS A SEAM BAND THE MARGINAL OFFER? (zone-hours whose dual equals a band)")
    for y in YEARS:
        vals = np.array(
            sorted(
                {
                    float(v)
                    for d in MISO_SEAM_LADDER_BY_YEAR[y].values()
                    for key in ("import", "export")
                    for v in d.get(key, ())
                }
            )
        )
        s = pd.read_parquet(BUNDLE / "hourly" / f"system_{y}.parquet")
        s = s[(s["pass"] == "P1")]
        s = s[~s["zone"].astype(str).str.startswith("MISO_external")]
        p = s["price"].to_numpy(dtype=float)
        hit = np.isclose(p[:, None], vals[None, :], atol=0.011).any(axis=1)
        print(f"   {y}: {100 * hit.mean():5.1f}% of internal zone-hours")


def section_f() -> None:
    print("\nF. LOAD BASIS — model demand vs MISO's measured EIA-930 demand")
    for y in YEARS:
        fs = sorted(glob.glob(str(ROOT / f"data/raw/eia-930/EIA930_BALANCE_{y}_*.parquet")))
        d = pd.concat([pd.read_parquet(f) for f in fs])
        d = d[d["Balancing Authority"] == "MISO"]
        adj = float(d["Demand (MW) (Adjusted)"].sum()) / TWH
        _, dem = model_price_demand(y)
        m = dem.sum() / TWH
        print(
            f"   {y}: model {m:8.3f} TWh   EIA-930 adjusted {adj:8.3f} TWh   "
            f"d {m - adj:+6.3f} ({100 * (m / adj - 1):+.3f}%)"
        )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sections", nargs="*", default=list("ABCDEF"))
    args = ap.parse_args()
    want = {s.upper() for s in args.sections}
    joined = load_joined() if want & set("BCD") else None
    if "A" in want:
        section_a()
    if "B" in want:
        section_b(joined)
    if "C" in want:
        section_c(joined)
    if "D" in want:
        section_d(joined)
    if "E" in want:
        section_e()
    if "F" in want:
        section_f()


if __name__ == "__main__":
    main()
