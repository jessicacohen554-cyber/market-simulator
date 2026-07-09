"""Quick C3a/C3b/C3c scorer for throwaway offer-curve sweep probes.

Reproduces calibration_verdict.py's price criteria directly from a solved
bundle's ``system.parquet`` (P1 pass) against the COMMITTED actuals — the
per-(ISO, year) bench parts (``frontend/data/backcast/bench/<ISO>/<year>.json.gz``,
C3a/C3b) and the DA-expressible actual tail
(``frontend/data/backcast/tail/actual_tail.json``, C3c) — so a single-year
sweep iteration can be scored in seconds without registering a throwaway run
on the dashboard. Uses the exact same formulas as the verdict scorer
(load-weighted zone means, monthly NRMSE normalized by the actual mean,
max-across-zones tail count at the ISO threshold). Diagnostic only: dashboard
candidates are still scored by scripts/calibration_verdict.py on committed
artifacts (rules 14/16).

Usage: python scripts/probes/_score_probe.py results/calibration/<bundle> [...]
"""

import gzip
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BENCH = REPO / "frontend" / "data" / "backcast" / "bench"
TAIL = REPO / "frontend" / "data" / "backcast" / "tail" / "actual_tail.json"

_MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_CUM = np.cumsum([0] + [d * 24 for d in _MONTH_DAYS])


def score_bundle(bundle: Path, iso: str = "ERCOT", thr: float = 200.0) -> None:
    """Print per-year C3a/C3b/C3c for one solved bundle."""
    sysdf = pd.read_parquet(bundle / "system.parquet")
    if "pass" in sysdf.columns and (sysdf["pass"] == "P1").any():
        sysdf = sysdf[sysdf["pass"] == "P1"]
    tail_part = json.loads(TAIL.read_text()).get("isos", {}).get(iso, {})
    for year in sorted(sysdf["year"].unique()):
        sy = sysdf[sysdf["year"] == year]
        bpath = BENCH / iso / f"{year}.json.gz"
        bench = json.loads(gzip.open(bpath, "rt").read())["bench"]["avgLMP"]
        # Rubric v2.4 like-for-like basis: the load-weighted actual gates when
        # committed (same ladder as calibration_verdict.score_price_mean);
        # legacy equal-hour fields otherwise.
        rt = bench.get("rt_lw", bench.get("rt"))
        rt_mon = bench.get("rt_lw_mon") or bench.get("rt_mon")
        # per-zone load-weighted annual + monthly means (render logic)
        pairs, model_mon_pairs = [], [[] for _ in range(12)]
        price_by_zone = {}
        for zone, zg in sy.groupby("zone", observed=True):
            price = zg["price"].to_numpy(float)
            dem = zg["demand"].to_numpy(float)
            hr = zg["hour"].to_numpy()
            full = np.full(8760, np.nan)
            full[hr] = price
            price_by_zone[str(zone)] = full
            d_tot = float(dem.sum())
            if d_tot > 0:
                pairs.append((float((price * dem).sum()) / d_tot, d_tot))
            midx = np.clip(np.searchsorted(_CUM, hr, side="right") - 1, 0, 11)
            for m in range(12):
                sel = midx == m
                dd = float(dem[sel].sum())
                if sel.any() and dd > 0:
                    model_mon_pairs[m].append(
                        (float((price[sel] * dem[sel]).sum()) / dd, dd)
                    )
        model = sum(v * w for v, w in pairs) / sum(w for _, w in pairs)
        model_mon = [
            (sum(v * w for v, w in mp) / sum(w for _, w in mp)) if mp else None
            for mp in model_mon_pairs
        ]
        # C3a
        err = (model - rt) / rt if rt else float("nan")
        # C3b
        cells = [
            (m, a)
            for m, a in zip(model_mon, rt_mon or [])
            if m is not None and a is not None
        ]
        mean_a = sum(a for _, a in cells) / len(cells)
        nrmse = math.sqrt(sum((m - a) ** 2 for m, a in cells) / len(cells)) / mean_a
        # C3c (energy-only fallback branch: max across zones > thr)
        stack = np.nan_to_num(np.vstack(list(price_by_zone.values())), nan=-np.inf)
        gt = int((stack.max(axis=0) > thr).sum())
        gt500 = int((stack.max(axis=0) > 500).sum())
        trec = tail_part.get(str(year), {})
        da_gt = trec.get("da_gt")
        print(
            f"{bundle.name} {year}: "
            f"C3a mean {model:7.2f} vs RT {rt:6.2f} ({err * 100:+6.1f}%) | "
            f"C3b NRMSE {nrmse:5.3f} | "
            f"C3c >$200 {gt}h (>$500 {gt500}h) vs DA actual {da_gt}h"
        )


if __name__ == "__main__":
    for b in sys.argv[1:]:
        score_bundle(Path(b))
