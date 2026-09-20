"""pjm-h14 phase 0 — localise PJM's COAL_BIT over-run at ZERO LP.

Reads ONLY committed artifacts: the designated keeper pair's ``hourly/`` sidecars
(rule 15 ``[R-DASHBOARD]`` commits them so a diagnostic need not replay a solve)
and the committed benchmark payloads ``frontend/data/backcast/bench/PJM/<y>.json.gz``.

The benchmark's per-plant ``campd`` field is the measured CEMS hourly gross load
encoded as ``round(100 * cn / nameplate)`` in uint8, so decoding it back to MW
costs a 1 %-of-nameplate quantisation per plant-hour — fine for localising a
28 TWh error by season / hour / zone / load decile, and explicitly NOT used here
for any level claim.

Usage: .venv/bin/python scripts/probes/pjm_h14_coal_phase0.py
"""

from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "frontend/data/backcast/bench/PJM"
BUNDLES = {
    2020: ROOT / "results/calibration/pjm_h13_meritalloc_touchpoint",
    2021: ROOT / "results/calibration/pjm_h13_meritalloc_touchpoint",
    2022: ROOT / "results/calibration/pjm_h13_meritalloc_touchpoint",
    2023: ROOT / "results/calibration/pjm_h13_meritalloc_span",
    2024: ROOT / "results/calibration/pjm_h13_meritalloc_span",
    2025: ROOT / "results/calibration/pjm_h13_meritalloc_span",
}
YEARS = sorted(BUNDLES)


def decode_campd(rec: dict) -> np.ndarray:
    """Measured hourly MW for one benchmark plant record (zeros if no CEMS)."""
    if rec.get("nodata"):
        return np.zeros(8760)
    cf = np.frombuffer(base64.b64decode(rec["campd"]), dtype=np.uint8).astype(float)
    return cf / 100.0 * float(rec.get("npl") or 0.0)


def measured_class_hourly(year: int, klass: str) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Measured hourly MW for ``klass``, system total and by model zone."""
    payload = json.load(gzip.open(BENCH / f"{year}.json.gz"))
    plants = payload["bench"]["plants"]
    total = np.zeros(8760)
    by_zone: dict[str, np.ndarray] = {}
    for rec in plants.values():
        if rec.get("group") != klass:
            continue
        mw = decode_campd(rec)
        total += mw
        by_zone.setdefault(rec.get("zone", "?"), np.zeros(8760))
        by_zone[rec["zone"]] += mw
    return total, by_zone


def model_class_hourly(year: int, klass: str) -> np.ndarray:
    df = pd.read_parquet(BUNDLES[year] / f"hourly/class_hourly_{year}.parquet")
    df = df[(df["pass"] == "P1") & (df["klass"] == klass)]
    out = np.zeros(8760)
    out[df["hour"].to_numpy()] = df["mw"].to_numpy()
    return out


def model_band_hourly(year: int, klass: str) -> dict[str, np.ndarray]:
    df = pd.read_parquet(BUNDLES[year] / f"hourly/class_band_hourly_{year}.parquet")
    df = df[(df["pass"] == "P1") & (df["klass"] == klass)]
    out: dict[str, np.ndarray] = {}
    for band, sub in df.groupby("band"):
        a = np.zeros(8760)
        a[sub["hour"].to_numpy()] = sub["mw"].to_numpy()
        out[str(band)] = a
    return out


def system_load(year: int) -> np.ndarray:
    s = pd.read_parquet(BUNDLES[year] / f"hourly/system_{year}.parquet")
    s = s[(s["pass"] == "P1") & (s["zone"] != "PJM_external")]
    return s.groupby("hour")["demand"].sum().reindex(range(8760), fill_value=0.0).to_numpy()


def system_price(year: int) -> np.ndarray:
    s = pd.read_parquet(BUNDLES[year] / f"hourly/system_{year}.parquet")
    s = s[(s["pass"] == "P1") & (s["zone"] != "PJM_external")]
    num = (s["price"] * s["demand"]).groupby(s["hour"]).sum()
    den = s.groupby("hour")["demand"].sum()
    return (num / den).reindex(range(8760), fill_value=np.nan).to_numpy()


def month_of_hour(year: int) -> np.ndarray:
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    return idx.month.to_numpy()


def main() -> None:
    print("=" * 100)
    print("pjm-h14 PHASE 0 — COAL_BIT over-run localisation (zero LP, committed artifacts only)")
    print("=" * 100)

    rows = []
    store: dict[int, dict] = {}
    for y in YEARS:
        meas, meas_z = measured_class_hourly(y, "COAL_BIT")
        mod = model_class_hourly(y, "COAL_BIT")
        bands = model_band_hourly(y, "COAL_BIT")
        load = system_load(y)
        price = system_price(y)
        store[y] = dict(meas=meas, mod=mod, bands=bands, load=load, price=price, meas_z=meas_z)
        rows.append(
            dict(
                year=y,
                meas_TWh=meas.sum() / 1e6,
                model_TWh=mod.sum() / 1e6,
                delta_TWh=(mod - meas).sum() / 1e6,
                meas_max=meas.max(),
                model_max=mod.max(),
                hrs_model_gt=(mod > meas).sum(),
            )
        )
    df = pd.DataFrame(rows)
    print("\n### 1. Annual, measured (CEMS via bench) vs model\n")
    print(df.to_string(index=False, float_format=lambda v: f"{v:10.3f}"))

    print("\n### 2. Where in the year (Δ TWh by month)\n")
    tab = {}
    for y in YEARS:
        m = month_of_hour(y)
        d = store[y]["mod"] - store[y]["meas"]
        tab[y] = [d[m == k].sum() / 1e6 for k in range(1, 13)]
    print(pd.DataFrame(tab, index=[f"M{k:02d}" for k in range(1, 13)]).to_string(float_format=lambda v: f"{v:8.3f}"))

    print("\n### 3. Where in the day (Δ TWh by hour-of-day)\n")
    tab = {}
    for y in YEARS:
        hod = np.arange(8760) % 24
        d = store[y]["mod"] - store[y]["meas"]
        tab[y] = [d[hod == k].sum() / 1e6 for k in range(24)]
    print(pd.DataFrame(tab, index=[f"h{k:02d}" for k in range(24)]).to_string(float_format=lambda v: f"{v:8.3f}"))

    print("\n### 4. Where on the load curve (Δ TWh by MODEL load decile, d1 = lowest load)\n")
    tab = {}
    for y in YEARS:
        load = store[y]["load"]
        dec = pd.qcut(pd.Series(load), 10, labels=False, duplicates="drop").to_numpy()
        d = store[y]["mod"] - store[y]["meas"]
        tab[y] = [d[dec == k].sum() / 1e6 for k in range(10)]
    print(pd.DataFrame(tab, index=[f"d{k+1}" for k in range(10)]).to_string(float_format=lambda v: f"{v:8.3f}"))

    print("\n### 5. Which BAND carries the model's coal (model TWh by band)\n")
    allb = sorted({b for y in YEARS for b in store[y]["bands"]})
    tab = {y: [store[y]["bands"].get(b, np.zeros(8760)).sum() / 1e6 for b in allb] for y in YEARS}
    print(pd.DataFrame(tab, index=allb).to_string(float_format=lambda v: f"{v:8.3f}"))

    print("\n### 6. CT_PEAKER and CC_REGULAR — the counterparties\n")
    rows = []
    for y in YEARS:
        for kl in ("CT_PEAKER", "CC_REGULAR", "ST_GAS", "COAL_PRB"):
            meas, _ = measured_class_hourly(y, kl)
            mod = model_class_hourly(y, kl)
            rows.append(dict(year=y, klass=kl, meas_TWh=meas.sum() / 1e6,
                             model_TWh=mod.sum() / 1e6, delta_TWh=(mod - meas).sum() / 1e6))
    print(pd.DataFrame(rows).pivot(index="klass", columns="year", values="delta_TWh")
          .to_string(float_format=lambda v: f"{v:8.3f}"))

    print("\n### 7. HOURLY MIRROR TEST — is coal's excess the same hour as CT/CC's deficit?\n")
    print("corr(Δcoal_h, Δother_h) over 8760 h; a strong NEGATIVE r = a pure merit-order swap.\n")
    rows = []
    for y in YEARS:
        dcoal = store[y]["mod"] - store[y]["meas"]
        for kl in ("CT_PEAKER", "CC_REGULAR", "ST_GAS"):
            meas, _ = measured_class_hourly(y, kl)
            mod = model_class_hourly(y, kl)
            dk = mod - meas
            rows.append(dict(year=y, vs=kl, r=float(np.corrcoef(dcoal, dk)[0, 1]),
                             sum_ratio=float(dk.sum() / dcoal.sum()) if dcoal.sum() else np.nan))
    print(pd.DataFrame(rows).pivot(index="vs", columns="year", values="r").to_string(float_format=lambda v: f"{v:8.3f}"))

    print("\n### 8. Coal fleet UTILISATION — model vs measured capacity factor on COAL_BIT\n")
    rows = []
    for y in YEARS:
        payload = json.load(gzip.open(BENCH / f"{y}.json.gz"))
        cap = sum(float(r.get("npl") or 0.0) for r in payload["bench"]["plants"].values()
                  if r.get("group") == "COAL_BIT")
        meas, mod = store[y]["meas"], store[y]["mod"]
        rows.append(dict(year=y, bench_cap_MW=cap,
                         meas_CF=meas.mean() / cap, model_CF=mod.mean() / cap,
                         meas_p95_MW=np.percentile(meas, 95), model_p95_MW=np.percentile(mod, 95),
                         meas_p05_MW=np.percentile(meas, 5), model_p05_MW=np.percentile(mod, 5),
                         meas_min=meas.min(), model_min=mod.min()))
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:10.3f}"))

    print("\n### 9. Zone split of the over-run (Δ TWh; model zones from the bundle's own class rows are\n"
          "    not zone-resolved, so this reports the MEASURED zonal shares for context only)\n")
    for y in (2020, 2021, 2025):
        _, mz = measured_class_hourly(y, "COAL_BIT")
        s = {z: v.sum() / 1e6 for z, v in sorted(mz.items())}
        print(f"  {y} measured COAL_BIT TWh by zone: " + ", ".join(f"{z.replace('PJM_','')}={v:.2f}" for z, v in s.items()))


if __name__ == "__main__":
    main()
