"""ERCOT-99 quick probe scorer: C3a mean-price error + C3c tail counts from a
bundle's committed system sidecar, vs the committed actuals.  Approximates the
registration scorer (demand-weighted settlement LMP tail count) for fast probe
triage — the authoritative gate is calibration_verdict on the registered bundle.

Usage: python -m scripts.probes.ercot99_score_probe <bundle> [--year 2023]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
TAIL = 200.0


def score(bundle: Path, year: int) -> dict:
    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    p1 = s[s["pass"] == "P1"]
    price = p1.pivot(index="hour", columns="zone", values="price")
    dem = p1.pivot(index="hour", columns="zone", values="demand")
    # settlement = energy LMP + published scarcity/reserve overlay (what C3c scores)
    overlay = np.zeros_like(price.to_numpy())
    for c in ("ordc_adder", "rtordpa_overlay"):
        if c in p1.columns:
            overlay = overlay + p1.pivot(index="hour", columns="zone", values=c).to_numpy()
    settle = price.to_numpy() + overlay
    w = dem.to_numpy()
    hub_e = (price.to_numpy() * w).sum(1) / w.sum(1)
    hub_s = (settle * w).sum(1) / w.sum(1)
    # C3c model count = the scorer uses the demand-weighted settlement tail count
    lmp = pd.read_parquet(REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet")
    ry = lmp[lmp["year"] == year].set_index("hour")
    rt = ry["rt"].reindex(range(8760)).to_numpy()
    actual_mean = float(np.nanmean(rt))
    return {
        "year": year,
        "actual_tail": int((rt > TAIL).sum()),
        "model_tail_energy": int((hub_e > TAIL).sum()),
        "model_tail_settle": int((hub_s > TAIL).sum()),
        "model_mean": round(float(hub_s.mean()), 1),
        "actual_mean": round(actual_mean, 1),
        "c3a_pct": round(100 * (hub_s.mean() - actual_mean) / actual_mean, 1),
        "caught_settle": int(((rt > TAIL) & (hub_s > TAIL)).sum()),
        "missed_settle": int(((rt > TAIL) & (hub_s <= TAIL)).sum()),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ercot99_score_probe")
    ap.add_argument("bundle")
    ap.add_argument("--year", type=int, nargs="+", default=[2023])
    args = ap.parse_args(argv)
    b = Path(args.bundle) if Path(args.bundle).is_absolute() else REPO / args.bundle
    for y in args.year:
        try:
            r = score(b, y)
        except FileNotFoundError:
            print(f"{y}: no sidecar")
            continue
        ratio = r["model_tail_settle"] / max(1, r["actual_tail"])
        c3c = "PASS" if 0.5 <= ratio <= 2.0 else "FAIL"
        print(f"{y}: C3a {r['c3a_pct']:+.1f}% (model ${r['model_mean']} vs ${r['actual_mean']}) | "
              f"C3c settle {r['model_tail_settle']}/{r['actual_tail']} "
              f"({ratio:.2f}x {c3c}) [energy-only {r['model_tail_energy']}] | "
              f"caught {r['caught_settle']} missed {r['missed_settle']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
