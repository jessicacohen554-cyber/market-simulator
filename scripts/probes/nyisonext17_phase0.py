"""NYISO-NEXT-17 phase 0 (ZERO LP): where the 2021 C3a over-pricing sits.

Reads only the keeper's committed bundles (``results/calibration/nyisonext16_2021``
and ``nyisonext16_span``), the committed NYISO bench, the measured NYISO DA zonal
LBMP proxy (``data/raw/seam-neighbour-price/nyiso``) and the curated
``nyiso-interface-flows`` datatype (run ``scripts/regenerate_clean.py
nyiso-interface-flows`` first).

Per year:

* ``c3a``: model vs RT/DA LW annual, and each (zone, month) cell's contribution
  to the system LW mean error vs measured DA, in $/MWh of the system mean.
* ``ce_regime``: Upstate_West and Capital_Hudson model-minus-measured-DA, split by
  measured CENTRAL EAST loading (flow / posted limit >= 0.85 vs < 0.70), and the
  measured vs model E->F (Capital minus Mohawk Valley / Upstate_West) spread.

Usage::

    python3 scripts/probes/nyisonext17_phase0.py --out <json>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in ("scripts", "scripts/probes", "scripts/data", "."):
    sys.path.insert(0, str(REPO / p))

import nyisonext13_ch_pricing_phase0 as p13  # noqa: E402
import score_bundle_price_shape as sps  # noqa: E402

from scripts.lib.clean_io import read_clean  # noqa: E402

CAL = REPO / "results/calibration"
BUNDLE = {2021: "nyisonext16_2021", **{y: "nyisonext16_span" for y in range(2022, 2026)}}
p13.BUNDLE = BUNDLE
YEARS = (2021, 2022, 2023, 2024, 2025)


def _mon() -> np.ndarray:
    """Hour-of-year -> month 0..11 on the scorer's month edges."""
    return np.clip(np.searchsorted(sps.rch._CUM, np.arange(8760), side="right") - 1, 0, 11)


def _ce_ratio(y: int) -> np.ndarray:
    """Measured CENTRAL EAST flow / posted limit on the hour-of-year clock (nan if absent)."""
    f = read_clean("nyiso-interface-flows", iso="NYISO", year=y)
    f = f[f.interface == "CENTRAL EAST - VC"].copy()
    f["lh"] = pd.to_datetime(f.interval_start_local).dt.floor("h")
    g = f.groupby("lh").agg(fl=("flow_mw", "mean"), lim=("positive_limit_mw", "mean"))
    g = g[g.index.year == y]
    hoy = ((g.index - pd.Timestamp(f"{y}-01-01")) / pd.Timedelta("1h")).astype(int).to_numpy()
    out = np.full(8760, np.nan)
    ok = (hoy >= 0) & (hoy < 8760)
    out[hoy[ok]] = (g.fl / g.lim).to_numpy()[ok]
    return out


def year_block(y: int) -> dict:
    """Decomposition for one year."""
    meas, mod = p13.meas_da(y), p13.model_prices(y)
    sy = pd.read_parquet(CAL / BUNDLE[y] / "hourly" / f"system_{y}.parquet")
    sy = sy[sy["pass"] == "P1"]
    dem = sy.pivot_table(index="hour", columns="zone", values="demand").reindex(range(8760))
    zones = list(p13.MODEL_TO_MEAS)
    W = dem[zones].to_numpy()
    PM = mod[zones].to_numpy()
    PA = np.column_stack([meas[list(c)].mean(axis=1).to_numpy() for c in p13.MODEL_TO_MEAS.values()])
    ok = np.isfinite(PA).all(axis=1)
    wtot = W[ok].sum()
    mon = _mon()
    contrib = {}
    for j, z in enumerate(zones):
        contrib[z] = [
            round(float(((PM[:, j] - PA[:, j]) * W[:, j])[ok & (mon == m)].sum() / wtot), 3)
            for m in range(12)
        ]
    bench = sps.bench_year("NYISO", y)["avgLMP"]
    mod_lw = float((PM * W)[ok].sum() / wtot)
    da_lw_meas = float((PA * W)[ok].sum() / wtot)
    ratio = _ce_ratio(y)
    hi, lo = ratio >= 0.85, ratio < 0.70
    uw, ch = zones.index("Upstate_West"), zones.index("Capital_Hudson")
    mhk = meas["MHK VL"].to_numpy()

    def lwmean(x, m, j):
        s = m & np.isfinite(x)
        return round(float((x[s] * W[s, j]).sum() / W[s, j].sum()), 2) if s.any() else None

    ce = {}
    for name, m in (("ce_ge_085", hi), ("ce_070_085", ~hi & ~lo & np.isfinite(ratio)), ("ce_lt_070", lo)):
        ce[name] = {
            "share_h_pct": round(float(m.mean()) * 100, 1),
            "uw_err": lwmean(PM[:, uw] - PA[:, uw], m, uw),
            "ch_err": lwmean(PM[:, ch] - PA[:, ch], m, ch),
            "ef_spread_meas": lwmean(PA[:, ch] - mhk, m, ch),
            "ch_uw_spread_meas": lwmean(PA[:, ch] - PA[:, uw], m, ch),
            "ch_uw_spread_model": lwmean(PM[:, ch] - PM[:, uw], m, ch),
            "uw_err_contrib_sys": round(float(((PM[:, uw] - PA[:, uw]) * W[:, uw])[ok & m].sum() / wtot), 3),
        }
    return {
        "rt_lw": bench.get("rt_lw"),
        "da_lw": bench.get("da_lw"),
        "model_lw": round(mod_lw, 2),
        "meas_da_lw_proxy": round(da_lw_meas, 2),
        "contrib_vs_da": contrib,
        "zone_total": {z: round(sum(v), 3) for z, v in contrib.items()},
        "month_total": [round(sum(contrib[z][m] for z in zones), 3) for m in range(12)],
        "ce_regime": ce,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    rec = {str(y): year_block(y) for y in YEARS}
    Path(a.out).write_text(json.dumps(rec, indent=1) + "\n")
    for y, r in rec.items():
        print(y, {k: r[k] for k in ("rt_lw", "da_lw", "model_lw", "meas_da_lw_proxy")})
        print("  zone", r["zone_total"])
        print("  month", r["month_total"])
        for k, v in r["ce_regime"].items():
            print("  ", k, v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
