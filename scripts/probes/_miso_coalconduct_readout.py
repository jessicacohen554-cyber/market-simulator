"""Readout for the throwaway coal-conduct probes (_miso_coalconduct_probe.py).

Compares each probe bundle year against (a) the registered miso-65 keeper
payload (class TWh, zonal monthly LMP) and (b) the measured actuals (bundle
metrics.json C1 records; the DA Indiana-hub monthly record). Prints, per year:

- C1-relevant class TWh: probe vs miso-65 vs actual (COAL_PRB/BIT/LIGNITE,
  CT_PEAKER, CC_REGULAR, ST_GAS, CC_CHP, total coal);
- Indiana-zone monthly LMP: probe vs miso-65 vs DA actual, with the C3a-style
  annual demand-weighted %err proxy and a monthly-NRMSE C3b proxy;
- trough diagnostics: annual P10 zonal price, overnight (h02-04) means;
- hours > $200 (any zone / Indiana).

Usage: PYTHONPATH=.:src .venv/bin/python scripts/probes/_miso_coalconduct_readout.py <probe_dir> [<probe_dir> ...]
"""

import base64
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PAYLOAD = ROOT / "frontend/data/backcast/runs/2026-07-14-miso-65-outage-regen.js"
METRICS = ROOT / "results/calibration/miso65_outage_regen/metrics.json"

CLASSES = [
    "COAL_PRB",
    "COAL_BIT",
    "COAL_LIGNITE",
    "CT_PEAKER",
    "CC_REGULAR",
    "ST_GAS",
    "CC_CHP",
]


def _payload() -> dict:
    s = PAYLOAD.read_text()
    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', s)
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def _actual_class_twh() -> dict[tuple[int, str], float]:
    s = (ROOT / "frontend/data/backcast/status.js").read_text()
    m = re.search(r"window\.BC\.status=(\{.*\})", s, re.S)
    d = json.loads(m.group(1).rstrip(";\n"))
    miso = [k for k in d["keepers"] if k.get("iso") == "MISO"][0]
    out = {}
    for r in miso["criteria"]["fuelmix"]["records"]:
        if r.get("key") and r.get("actual") is not None:
            out[(int(r["year"]), str(r["key"]))] = float(r["actual"])
    return out


def _actual_indiana_monthly(year: int) -> np.ndarray:
    df = pd.read_csv(ROOT / f"data/raw/lmp-data/MISO/miso_hub_lmp_{year}_da.csv.gz")
    df = df[(df.node == "INDIANA.HUB") & (df["value"] == "LMP")]
    he = [c for c in df.columns if c.startswith("he")]
    long = df.melt(id_vars=["date"], value_vars=he, value_name="da_lmp")
    long["month"] = pd.to_datetime(long.date).dt.month
    return long.groupby("month").da_lmp.mean().reindex(range(1, 13)).to_numpy()


def _probe_year(pdir: Path, year: int, payload: dict, actual_cls: dict) -> None:
    disp = pd.read_parquet(pdir / "dispatch" / f"{year}_P1.parquet")
    mwcol = "mw" if "mw" in disp.columns else "dispatch_mw"
    cls_twh = disp.groupby("klass")[mwcol].sum() / 1e6

    ypay = payload["years"][str(year)]
    gm = ypay["gmModel"]

    print(f"\n===== {pdir.name} — {year} =====")
    print(f"{'class':13s} {'probe':>8s} {'miso-65':>8s} {'delta':>7s} {'actual':>8s}")
    tot_probe = tot_keep = tot_act = 0.0
    for k in CLASSES:
        p = float(cls_twh.get(k, 0.0))
        b = float(gm.get(k, 0.0))
        a = actual_cls.get((year, k), float("nan"))
        if k.startswith("COAL"):
            tot_probe += p
            tot_keep += b
            tot_act += 0.0 if np.isnan(a) else a
        print(f"{k:13s} {p:8.2f} {b:8.2f} {p - b:+7.2f} {a:8.2f}")
    print(
        f"{'total coal':13s} {tot_probe:8.2f} {tot_keep:8.2f} {tot_probe - tot_keep:+7.2f} {tot_act:8.2f}"
    )

    system = pd.read_parquet(pdir / "system.parquet")
    sy = system[(system.year == year) if "year" in system.columns else slice(None)]
    if "pass" in sy.columns:
        sy = sy[sy["pass"] == "P1"]
    zcol = "zone" if "zone" in sy.columns else "zone_name"
    pcol = "price" if "price" in sy.columns else "lmp"
    ind = sy[sy[zcol] == "MISO-Indiana"].sort_values("hour")
    prices = ind[pcol].to_numpy()
    hours = ind["hour"].to_numpy()
    month = (
        pd.date_range(f"{year}-01-01", periods=len(prices), freq="h").month
        if len(prices) in (8760, 8784)
        else None
    )
    pm = (
        pd.Series(prices).groupby(month).mean().reindex(range(1, 13)).to_numpy()
        if month is not None
        else np.full(12, np.nan)
    )
    act = _actual_indiana_monthly(year)
    keep_pm = np.array(ypay["lmp"]["MISO-Indiana"]["pMon"], dtype=float)

    print("\nIndiana monthly LMP (probe / miso-65 / DA actual):")
    for mth in range(12):
        print(f"  {mth + 1:2d}  {pm[mth]:7.2f}  {keep_pm[mth]:7.2f}  {act[mth]:7.2f}")
    wa = np.nanmean  # simple monthly-mean aggregation for the proxy
    c3a_probe = (wa(pm) - wa(act)) / wa(act) * 100
    c3a_keep = (wa(keep_pm) - wa(act)) / wa(act) * 100
    nrmse_probe = float(np.sqrt(np.nanmean((pm - act) ** 2)) / wa(act))
    nrmse_keep = float(np.sqrt(np.nanmean((keep_pm - act) ** 2)) / wa(act))
    print(
        f"  C3a proxy (ann mean %err): probe {c3a_probe:+.1f}% vs miso-65 {c3a_keep:+.1f}%"
    )
    print(
        f"  C3b proxy (monthly NRMSE): probe {nrmse_probe:.3f} vs miso-65 {nrmse_keep:.3f}"
    )

    overnight = np.isin((hours % 24), [2, 3, 4])
    p10 = float(np.percentile(prices, 10))
    print(
        f"  trough: P10 {p10:.2f}; overnight(h02-04) mean {prices[overnight].mean():.2f}"
    )
    anyz = sy.groupby("hour")[pcol].max()
    print(
        f"  hours > $200: Indiana {(prices > 200).sum()}, any-zone {(anyz > 200).sum()}"
    )


def main(dirs: list[str]) -> None:
    payload = _payload()
    actual_cls = _actual_class_twh()
    for d in dirs:
        pdir = Path(d)
        for yq in sorted((pdir / "dispatch").glob("*_P1.parquet")):
            year = int(yq.name.split("_")[0])
            _probe_year(pdir, year, payload, actual_cls)


if __name__ == "__main__":
    main(sys.argv[1:])
