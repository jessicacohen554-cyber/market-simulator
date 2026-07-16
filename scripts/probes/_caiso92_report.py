"""caiso-92 report-back harness: A/B grid vs the same-machine caiso-90 repro.

Computes, for one bundle, the 2026-07-16 handoff's report-back rows:
C1 grid (CC_REGULAR / CT_PEAKER / CT_CHP / ST_GAS model-vs-bench TWh +
Panoche 56803 GWh), the hod price ladder (demand-weighted model lambda -
actual RT by hod block), C3c counts AND dates (model max-zonal >$200 vs the
DA/RT actual tails), and the monthly WATCH map (single construction:
system.parquet price, overlay included in both A and B).

Usage: python scripts/probes/_caiso92_report.py <bundle_dir> [<bundle_dir_B>]
With two bundles, prints A/B side by side.
"""

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BENCH = REPO / "frontend" / "data" / "backcast" / "bench" / "CAISO"
ACTUAL_LMP = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_CAISO.parquet"
)
YEARS = (2023, 2024, 2025)
CLASSES = ("CC_REGULAR", "CT_PEAKER", "CT_CHP", "ST_GAS")
HOD_BLOCKS = {
    "overnight(0-5)": range(0, 6),
    "belly(10-14)": range(10, 15),
    "evening(17-21)": range(17, 22),
}
PANOCHE = 56803


def bench_class_twh(year: int) -> dict[str, float]:
    """Actual class TWh from the committed bench sidecar (classFull)."""
    doc = json.loads(gzip.open(BENCH / f"{year}.json.gz").read())
    fm = doc["bench"]["classFull"]
    return {cls: fm.get(cls) for cls in CLASSES}


def analyze(bundle: Path) -> dict:
    out: dict = {}
    disp = {
        y: pd.read_parquet(
            bundle / "dispatch" / f"{y}_P1.parquet",
            columns=["klass", "plant_code", "hour", "mw", "zone"],
        )
        for y in YEARS
    }
    sys_df = pd.read_parquet(bundle / "system.parquet")

    # --- C1 grid -------------------------------------------------------
    c1 = {}
    for y, d in disp.items():
        model = d.groupby("klass", observed=True).mw.sum() / 1e6
        bench = bench_class_twh(y)
        c1[y] = {
            cls: {
                "model": round(float(model.get(cls, 0.0)), 2),
                "actual": bench[cls],
                "miss": (
                    None
                    if bench[cls] is None
                    else round(float(model.get(cls, 0.0)) - bench[cls], 2)
                ),
            }
            for cls in CLASSES
        }
        c1[y]["Panoche_GWh"] = round(
            float(d[d.plant_code == PANOCHE].mw.sum() / 1e3), 1
        )
    out["c1_twh"] = c1

    # --- demand-weighted model lambda per hour (CA zones), per year ----
    act = pd.read_parquet(ACTUAL_LMP)

    def model_lambda(y: int) -> tuple[np.ndarray, np.ndarray]:
        s = sys_df[(sys_df.year == y) & (sys_df["pass"] == "P1")]
        ca = s[~s.zone.str.startswith("WECC")]
        dw = (
            ca.assign(pw=ca.price * ca.demand)
            .groupby("hour")[["pw", "demand"]]
            .sum()
            .sort_index()
        )
        return (dw.pw / dw.demand).to_numpy(), dw.demand.to_numpy()

    ladder = {}
    monthly = {}
    for y in YEARS:
        model_l, wts = model_lambda(y)
        a = act[act.year == y].sort_values("hour")
        rt = a.rt.to_numpy()[: len(model_l)]
        resid = model_l - rt
        hod = np.arange(len(model_l)) % 24
        row = {}
        for name, hrs in HOD_BLOCKS.items():
            m = np.isin(hod, list(hrs)) & np.isfinite(rt)
            row[name] = round(float(np.average(resid[m], weights=wts[m])), 1)
        ladder[y] = row
        idx = pd.date_range(f"{y}-01-01", periods=len(model_l), freq="h")
        mm = pd.DataFrame({"m": model_l, "a": rt}, index=idx).resample("MS").mean()
        monthly[y] = {
            ts.strftime("%b"): round(float(r.m - r.a), 1) for ts, r in mm.iterrows()
        }
    out["hod_ladder_model_minus_rt"] = ladder
    out["monthly_resid"] = monthly

    # --- C3c: model tail = max ZONAL price > $200, with dates; actual DA/RT
    c3c = {}
    for y in YEARS:
        s = sys_df[(sys_df.year == y) & (sys_df["pass"] == "P1")]
        mx = s.groupby("hour").price.max()
        tail_hours = mx[mx > 200.0]
        days = (
            pd.to_datetime(f"{y}-01-01")
            + pd.to_timedelta(tail_hours.index.to_numpy() // 24, unit="D")
        ).strftime("%m-%d")
        vc = pd.Series(days).value_counts().sort_index()
        a = act[act.year == y]
        c3c[y] = {
            "model_hours": int(len(tail_hours)),
            "model_days": vc.to_dict(),
            "actual_da_hours": int((a.da > 200.0).sum()),
            "actual_rt_hours": int((a.rt > 200.0).sum()),
        }
    out["c3c"] = c3c
    return out


def main() -> int:
    bundles = [Path(p) for p in sys.argv[1:]]
    if not bundles:
        print(__doc__)
        return 2
    docs = {b.name: analyze(b) for b in bundles}
    print(json.dumps(docs, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
