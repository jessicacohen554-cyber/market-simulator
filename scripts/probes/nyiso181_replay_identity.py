"""nyiso-181 — gate I1: is the control replay bit-identical to the committed keeper?

``results/calibration/*/hourly/unit_hourly_*.parquet`` is gitignored, so the
reduced-cost instrument nyiso-181 adjudicates on exists only in a fresh replay
of the keeper's own recipe. **Every gate in
``results/calibration/PREREG-nyiso181-itm-degeneracy.md`` §2 is therefore
conditional on that replay BEING the keeper**, and §2 G-I I1 states the bar
before the replay was run: hourly zonal prices differing in 0 of 52,560 cells
and class-hour cells in 0 of 122,640, per year — the figures nyiso-180 §8
published for this exact replay at this exact HEAD.

A non-zero count is stop condition S1: the instrument is reported as failed and
no gate is adjudicated.

Usage:
    python scripts/probes/nyiso181_replay_identity.py <committed> <replay> [--out FILE]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]

YEARS = (2023, 2024, 2025)
# The two artifacts whose identity nyiso-180 §8 published, with their keys.
SIDECARS = {
    "system": (["zone", "hour"], "price"),
    "class_hourly": (["klass", "hour"], "mw"),
}


def _compare(a: Path, b: Path, keys: list[str], val: str) -> dict:
    """Cell-level diff of one sidecar pair, keyed by name (never by position)."""
    if not a.exists() or not b.exists():
        return {"available": False, "committed": a.exists(), "replay": b.exists()}
    da, db = pd.read_parquet(a), pd.read_parquet(b)
    for d in (da, db):
        if "pass" in d.columns:
            d.drop(d.index[d["pass"].astype(str) != "P1"], inplace=True)
        for k in keys:
            if d[k].dtype == object:
                d[k] = d[k].astype(str)
    j = da[keys + [val]].merge(
        db[keys + [val]], on=keys, how="outer", suffixes=("_c", "_r")
    )
    unmatched = int(j[f"{val}_c"].isna().sum() + j[f"{val}_r"].isna().sum())
    both = j.dropna(subset=[f"{val}_c", f"{val}_r"])
    differ = int((both[f"{val}_c"] != both[f"{val}_r"]).sum())
    return {
        "available": True,
        "cells_compared": int(len(both)),
        "cells_unmatched": unmatched,
        "cells_differing": differ,
        "max_abs_delta": (
            float((both[f"{val}_c"] - both[f"{val}_r"]).abs().max()) if len(both) else 0.0
        ),
        "IDENTICAL": bool(differ == 0 and unmatched == 0),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("committed", type=Path)
    ap.add_argument("replay", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    c = args.committed if args.committed.is_absolute() else REPO / args.committed
    r = args.replay if args.replay.is_absolute() else REPO / args.replay

    report: dict = {
        "committed": str(c.relative_to(REPO)),
        "replay": str(r.relative_to(REPO)),
        "years": {},
    }
    for year in YEARS:
        yr: dict = {}
        for name, (keys, val) in SIDECARS.items():
            yr[name] = _compare(
                c / "hourly" / f"{name}_{year}.parquet",
                r / "hourly" / f"{name}_{year}.parquet",
                list(keys),
                val,
            )
        yr["I1_PASS"] = all(
            v.get("IDENTICAL") for v in yr.values() if isinstance(v, dict)
        )
        report["years"][str(year)] = yr
    report["I1_PASS_ALL_YEARS"] = all(
        y["I1_PASS"] for y in report["years"].values()
    )

    out = args.out or (REPO / "results/calibration/_nyiso181_replay_identity.json")
    out.write_text(json.dumps(report, indent=2))
    json.dump(report, sys.stdout, indent=2)
    print(f"\n\nwrote {out}")


if __name__ == "__main__":
    main()
