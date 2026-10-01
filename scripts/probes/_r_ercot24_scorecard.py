#!/usr/bin/env python3
"""R-ERCOT-24 per-year scorecard: incumbent keeper vs the published-ORDC-curve arm.

Zero LP. For each bundle and year it reads the span-restricted verdict
(``calibration_verdict --years <Y> --json``) and the committed hourly sidecars,
and reports the PRECOMMIT §5 quantities: determination, C3a / C3b / C3c, C8
ST_GAS, C1 CC_REGULAR / COAL_PRB / COAL_LIGNITE / ST_GAS, load-weighted price,
the load-weighted ORDC adder against measured RTORPA on the same weights,
slack, and hours above $1k / $200.

Usage:
    python scripts/probes/_r_ercot24_scorecard.py \
        --bundle keeper=results/calibration/r_ercot23_span \
        --bundle arm=results/calibration/r_ercot24_span \
        --out docs/records/ercot/r-ercot/r_ercot24_scorecard.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
MEAS = REPO / "data" / "raw" / "ercot"
YEARS = tuple(range(2019, 2026))
C1_KEYS = ("CC_REGULAR", "COAL_PRB", "COAL_LIGNITE", "ST_GAS")


def verdict(bundle: Path, year: int) -> dict:
    """Return the span-restricted machine verdict for one year of ``bundle``."""
    out = subprocess.run(
        [sys.executable, "scripts/calibration_verdict.py", str(bundle),
         "--years", str(year), "--json"],
        cwd=REPO, capture_output=True, text=True,
        env={"PYTHONPATH": ".:src:scripts", **_env()},
    )
    return json.loads(out.stdout)


def _env() -> dict:
    """The caller's environment minus PYTHONPATH (set explicitly above)."""
    import os

    return {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}


def _rec(v: dict, crit: str, key: str | None) -> dict | None:
    """The record of ``crit`` keyed ``key`` (None = the headline record)."""
    c = v["criteria"].get(crit)
    if not c:
        return None
    for r in c["records"]:
        if r.get("key") == key:
            return r
    return None


def _fmt(r: dict | None) -> str | None:
    """``STATUS magnitude`` for a verdict record."""
    return None if r is None else f"{r['status']} {r.get('magnitude', '')}".strip()


def hourly(bundle: Path, year: int) -> dict:
    """Price, ORDC adder vs measured RTORPA, slack and tail counts (P1)."""
    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    dz = s.pivot(index="hour", columns="zone", values="demand").to_numpy()
    pz = s.pivot(index="hour", columns="zone", values="price").to_numpy()
    w = dz.sum(1) / dz.sum()
    sysp = (pz * dz).sum(1) / dz.sum(1)
    oa = s.groupby("hour").ordc_adder.first().to_numpy()
    m = pd.read_parquet(MEAS / f"ercot_{year}_ordc_reserves_hourly.parquet").iloc[: len(w)]
    f = pd.read_parquet(bundle / "hourly" / f"reserve_family_{year}.parquet")
    f = f[(f["pass"] == "P1") & (f.family == "ercot_ordc_total")].sort_values("hour")
    return {
        "LW": round(float((pz * dz).sum() / dz.sum()), 2),
        "ordc_adder_LW": round(float((oa * w).sum()), 2),
        "measured_rtorpa_LW": round(float(np.nansum(m.rtorpa.to_numpy() * w)), 2),
        "ordc_family_dual_LW": round(float((f.dual.to_numpy()[: len(w)] * w).sum()), 2),
        "slack_mwh": round(float(s.slack.sum()), 1),
        "h_gt_1k": int((sysp > 1000).sum()),
        "h_gt_200": int((sysp > 200).sum()),
        "max": round(float(sysp.max()), 0),
    }


def row(bundle: Path, year: int) -> dict:
    """One scorecard row for ``bundle`` / ``year``."""
    v = verdict(bundle, year)
    out = {
        "det": v["determination"],
        "C3a": _fmt(_rec(v, "price_mean", None)),
        "C3b": _fmt(_rec(v, "price_shape", None)),
        "C3c": _fmt(_rec(v, "price_tail", None)),
        "C8_ST_GAS": _fmt(_rec(v, "forced_share", "ST_GAS")),
    }
    for k in C1_KEYS:
        out[f"C1_{k}"] = _fmt(_rec(v, "fuelmix", k))
    out.update(hourly(bundle, year))
    return out


def main() -> None:
    """CLI: score every bundle on every year and write the JSON."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", action="append", required=True, help="NAME=path")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    card: dict[str, dict] = {}
    for spec in args.bundle:
        name, _, path = spec.partition("=")
        bundle = REPO / path
        for y in YEARS:
            card[f"{name}|{y}"] = row(bundle, y)
            print(name, y, json.dumps(card[f"{name}|{y}"]))
    Path(REPO / args.out).write_text(json.dumps(card, indent=1) + "\n")


if __name__ == "__main__":
    main()
