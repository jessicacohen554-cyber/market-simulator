#!/usr/bin/env python
"""FFR-3V-FIX: extract the pre-registered reads R1-R6 from a hindcast arm.

Reads ONLY committed run artifacts (``meta.json`` + the bundle's
``year_<Y>.parquet`` / ``evolution_<Y>.json``) — never a re-solve and never a
measured actual. One arm per invocation; the handoff's §5 table is the two
outputs side by side.

The reads are pre-registered in ``docs/handoffs/ffr-3v-fix-2026-08-08.md`` §4:

* **R1** base-year wind/solar pool MW — the bridge year's ``evolution_*.json``
  ``wind_cap_mw`` / ``solar_cap_mw``, which the ledger records from the PRIOR
  year's result, i.e. the base seed itself.
* **R2** annual VRE energy (TWh) per solved year.
* **R3** mean energy price ($/MWh) per solved year.
* **R4** cumulative evolution additions / retirements by tech.
* **R5** ``cache_key`` from the run meta (must match across arms).
* **R6** solved / bridged year sets.

Usage::

    python scripts/probes/_ffr3v_fix_pair_reads.py results/hindcast/<arm-out-dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_MWH_PER_TWH = 1.0e6


def _bundle_dir(out_dir: Path, meta: dict) -> Path:
    """Resolve the bundle directory for a run, preferring the recorded path."""
    recorded = Path(meta["bundle"])
    if recorded.is_dir():
        return recorded
    return out_dir / meta["iso"] / meta["cache_key"]


def _stack(df: pd.DataFrame, col: str) -> np.ndarray:
    """Stack one per-hour object column of per-zone vectors into ``(T, n_zones)``."""
    return np.vstack([np.asarray(v, dtype=float).ravel() for v in df[col]])


def _year_reads(path: Path) -> dict:
    """Return the per-year R2/R3 reads from one ``year_<Y>.parquet``.

    Each column holds one per-zone vector per hour, so every read stacks to a
    ``(T, n_zones)`` array first. The price read is given BOTH ways — the plain
    zone-mean and the demand-weighted system price — because the two answer
    different questions and neither is the obvious default.
    """
    df = pd.read_parquet(path)
    out: dict[str, float] = {}
    price = _stack(df, "price")
    demand = _stack(df, "demand")
    out["mean_price_zone_mean"] = float(price.mean())
    weight = demand.sum()
    out["mean_price_load_wtd"] = (
        float((price * demand).sum() / weight) if weight else 0.0
    )
    out["demand_twh"] = float(demand.sum()) / _MWH_PER_TWH
    for tech in ("wind", "solar"):
        out[f"{tech}_twh"] = float(_stack(df, tech).sum()) / _MWH_PER_TWH
    out["vre_twh"] = out["wind_twh"] + out["solar_twh"]
    out["vre_share_of_load"] = out["vre_twh"] / out["demand_twh"]
    for tech in ("slack", "dump"):
        out[f"{tech}_twh"] = float(_stack(df, tech).sum()) / _MWH_PER_TWH
    return out


def main(argv: list[str]) -> int:
    """Print the R1-R6 reads for one arm as JSON."""
    if len(argv) != 2:
        print(__doc__)
        return 2
    out_dir = Path(argv[1])
    meta = json.loads((out_dir / "meta.json").read_text())
    bundle = _bundle_dir(out_dir, meta)

    reads: dict = {
        "out_dir": str(out_dir),
        "bundle": str(bundle),
        # R5 / R6 -- the comparability and bridge-contract checks.
        "R5_cache_key": meta["cache_key"],
        "R6_solved_years": meta["solved_years"],
        "R6_bridged_years": meta["bridged_years"],
        "leakage_violations": meta["leakage_violations"],
    }

    ledgers = {
        int(p.stem.split("_")[-1]): json.loads(p.read_text())
        for p in sorted(bundle.glob("evolution_*.json"))
    }
    # R1: the EARLIEST ledger carries the prior (base) year's pools -- the base
    # year itself never evolves, so no ledger is written for it.
    if ledgers:
        first = min(ledgers)
        reads["R1_base_pool_mw"] = {
            "from_ledger_year": first,
            "wind": ledgers[first].get("wind_cap_mw"),
            "solar": ledgers[first].get("solar_cap_mw"),
        }
    # R4: cumulative additions / retirements by tech over the window.
    adds: dict[str, float] = {}
    rets: dict[str, float] = {}
    for _yr, led in sorted(ledgers.items()):
        for zone_acc in (led.get("renewable_additions") or {}).values():
            for tech, mw in zone_acc.items():
                adds[tech] = adds.get(tech, 0.0) + float(mw)
        for ev in led.get("thermal_additions") or []:
            tech = ev.get("fuel") or ev.get("tech") or "unknown"
            adds[tech] = adds.get(tech, 0.0) + float(ev.get("mw", 0.0) or 0.0)
        for ev in led.get("retirements") or []:
            tech = ev.get("fuel") or ev.get("tech") or "unknown"
            rets[tech] = rets.get(tech, 0.0) + float(ev.get("mw", 0.0) or 0.0)
    reads["R4_additions_mw"] = {k: round(v, 1) for k, v in sorted(adds.items())}
    reads["R4_retirements_mw"] = {k: round(v, 1) for k, v in sorted(rets.items())}
    reads["R4_pool_trajectory"] = {
        yr: {
            "wind_cap_mw": led.get("wind_cap_mw"),
            "solar_cap_mw": led.get("solar_cap_mw"),
            "bridge": bool(led.get("bridge")),
        }
        for yr, led in sorted(ledgers.items())
    }

    # R2 / R3 per solved year.
    reads["R2_R3_by_year"] = {
        int(p.stem.split("_")[-1]): _year_reads(p)
        for p in sorted(bundle.glob("year_*.parquet"))
        if "_p1" not in p.stem
    }

    print(json.dumps(reads, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
