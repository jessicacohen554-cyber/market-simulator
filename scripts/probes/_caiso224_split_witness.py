"""caiso-224 — the FSNO arm SPLIT WITNESS + F1/F2 falsifier measurements.

Pre-registered by `PRECOMMIT-caiso224-fsno-arm-2026-08-30.md` §5 (primary
structural outcome + the two falsifiers). Self-contained rather than a
re-point of the committed caiso-215 instrument because that instrument's
zone→hub map is 6-zone (FSNO has no trading hub to score against); this
probe measures the ARM's structural engagement from the two bundles' own
committed sidecars and never reads an actual price series as an input:

* North–south split witness (the caiso-220 gate-table object): hours with
  |NP15 − SP15_rest| > $15, model vs the committed reality record
  1310/1691/1347 (caiso-220 keeper note / caiso-216 §G).
* Pocket-boundary separation: hours with |FSNO − NP15| and |FSNO − ZP26|
  above $15 and above $0.01 (engagement), plus FSNO negative-price and
  ≤ −$5 hours — the caiso-221 §E.1 strandedness channel's direct trace.
* Load-weighted ISO mean price per bundle-year (the C3a-level movement at
  witness grain; the scorer's official number comes from
  calibration_verdict, never from here).
* F1 (over-trapping): binding share of the two NEW boundaries from the
  network sidecar (hours at limit or with positive dual, over 8760),
  reported against the DMM record's own observed ceilings (Moss Landing–
  Las Aguilas 24–27 % of ALL hours 2024/Q3-2025; Gates–Midway 9 % of hours
  2024) — boundary binding far beyond that record fires F1.
* F2 (static-vintage): is the arm's split-hour vector strictly year-ordered
  while reality's (1310/1691/1347) is non-monotone (the caiso-218 §C kill
  signature)?

Usage::

    python scripts/probes/_caiso224_split_witness.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CONTROL = REPO / "results/calibration/caiso224_a0_control"
ARM = REPO / "results/calibration/caiso224_b1_fsno"
OUT = REPO / "results/calibration/_caiso224_split_witness.json"
YEARS = [2023, 2024, 2025]

# Committed reality record for the Path-15-family north-south break (hours of
# material N-over-S separation; caiso-215 instrument via the caiso-220 keeper
# note: model 50/40/17 vs reality 1310/1691/1347).
REALITY_NS_SPLIT = {2023: 1310, 2024: 1691, 2025: 1347}
# DMM-record observed element binding-share ceilings (share of ALL hours):
# Moss Landing-Las Aguilas 24 %/27 % (2024/Q3-2025), Gates-Midway 9 % (2024).
F1_CEILING = 0.27


def _prices(bundle: Path, year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (price pivot hour×zone, demand pivot hour×zone) for P1 rows."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"] if "pass" in df.columns else df
    return (
        df.pivot(index="hour", columns="zone", values="price"),
        df.pivot(index="hour", columns="zone", values="demand"),
    )


def _bundle_year(bundle: Path, year: int) -> dict:
    """Witness measurements for one bundle-year (price side)."""
    px, dm = _prices(bundle, year)
    out: dict = {}
    ns = (px["NP15"] - px["SP15_rest"]).abs()
    out["ns_split_gt15_h"] = int((ns > 15.0).sum())
    out["reality_ns_split_h"] = REALITY_NS_SPLIT[year]
    w = dm.fillna(0.0).to_numpy()
    p = px.to_numpy()
    out["lw_price"] = round(float((p * w).sum() / w.sum()), 4)
    if "FSNO" in px.columns:
        d_np = (px["FSNO"] - px["NP15"]).abs()
        d_zp = (px["FSNO"] - px["ZP26"]).abs()
        out["fsno_np15_gt15_h"] = int((d_np > 15.0).sum())
        out["fsno_zp26_gt15_h"] = int((d_zp > 15.0).sum())
        out["fsno_np15_engaged_h"] = int((d_np > 0.01).sum())
        out["fsno_zp26_engaged_h"] = int((d_zp > 0.01).sum())
        out["fsno_neg_h"] = int((px["FSNO"] < 0.0).sum())
        out["fsno_le_m5_h"] = int((px["FSNO"] <= -5.0).sum())
        out["fsno_mean_price"] = round(float(px["FSNO"].mean()), 4)
    out["np15_neg_h"] = int((px["NP15"] < 0.0).sum())
    return out


def _boundary_binding(year: int) -> dict:
    """F1 side: binding share of the two NEW boundaries in the arm bundle."""
    nw = pd.read_parquet(ARM / "hourly" / f"network_{year}.parquet")
    nw = nw[(nw["kind"] == "link") if "kind" in nw.columns else slice(None)]
    out: dict = {}
    for pair, names in {
        "NP15<->FSNO": ("NP15>FSNO", "FSNO>NP15"),
        "FSNO<->ZP26": ("FSNO>ZP26", "ZP26>FSNO"),
    }.items():
        rows = nw[nw["name"].isin(names)]
        if rows.empty:
            out[pair] = {"missing": True}
            continue
        # A boundary-hour binds when any of its directional legs sits at its
        # limit (0.1 % tolerance). The sidecar's ``dual`` column is NOT a
        # congestion test: under the armed zonal loss surface every link-hour
        # carries the loss toll in it (measured p50 $0.002 on the NP15<->FSNO
        # legs across all hours), so a dual-based criterion reads 1.0
        # everywhere — the first run of this probe made exactly that error
        # and is superseded by this at-cap-only measure.
        at_cap = (rows["mw"].abs() >= 0.999 * rows["limit_up"].abs()) & (
            rows["limit_up"].abs() > 0
        )
        share = rows.assign(b=at_cap).groupby("hour")["b"].any().mean()
        out[pair] = {
            "binding_share": round(float(share), 4),
            "f1_ceiling": F1_CEILING,
            "fires_f1": bool(share > F1_CEILING),
        }
    return out


def main() -> None:
    """Measure the witness + falsifiers over both caiso-224 bundles."""
    result: dict = {
        "precommit": "PRECOMMIT-caiso224-fsno-arm-2026-08-30.md",
        "control": CONTROL.name,
        "arm": ARM.name,
        "per_year": {},
    }
    for year in YEARS:
        result["per_year"][year] = {
            "control": _bundle_year(CONTROL, year),
            "arm": _bundle_year(ARM, year),
            "arm_boundaries": _boundary_binding(year),
        }
    arm_ns = [result["per_year"][y]["arm"]["ns_split_gt15_h"] for y in YEARS]
    real_ns = [REALITY_NS_SPLIT[y] for y in YEARS]
    strictly_ordered = arm_ns == sorted(arm_ns) or arm_ns == sorted(arm_ns)[::-1]
    real_monotone = real_ns == sorted(real_ns) or real_ns == sorted(real_ns)[::-1]
    result["f2"] = {
        "arm_ns_split_vector": arm_ns,
        "reality_vector": real_ns,
        "arm_strictly_year_ordered": bool(
            strictly_ordered and len(set(arm_ns)) == len(arm_ns)
        ),
        "reality_monotone": bool(real_monotone),
        "fires_f2": bool(
            strictly_ordered and len(set(arm_ns)) == len(arm_ns) and not real_monotone
        ),
    }
    OUT.write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
