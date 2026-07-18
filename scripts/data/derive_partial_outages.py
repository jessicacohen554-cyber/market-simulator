#!/usr/bin/env python3
"""Derive partial (unit-level) outage derates from CAMPD capacity-factor ceilings.

For plants without unit-level data, a partial outage shows up as a sustained
*ceiling plateau*: the plant keeps running but its daily-max CF drops to a level
well below its normal capability (e.g. ~half capacity = half the units out),
then recovers. This detects those plateaus and emits a multiplicative
availability derate (ceiling / normal-ceiling) over the window, approximating
the lost capacity until unit-level data confirms it.

Restricted to plants where the signal is reliable: baseload units (annual mean
CF above :data:`_BASELOAD_CF`) that are COAL — all-or-nothing, so a depressed
ceiling is an outage, not economic part-load — plus a confirmed combined-cycle
allowlist. Economic single-train CC operation looks identical to a partial
outage from CF alone, so other CC plants are excluded until confirmed.

Writes ``data/raw/campd-partial-outages.csv``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
import sys

sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_campd_bins  # noqa: E402

# The plateau detector and its frozen plateau constants live in the shared
# outage-detection lib (formerly defined here); the unit-level deriver
# (scripts/data/derive_campd_unit_outages.py --partial-windows) reuses the same
# _detect verbatim from there.
from scripts.lib.outage_detect import _detect  # noqa: E402

# Plant groups eligible for partial-outage detection: baseload COAL (all-or-
# nothing) and CC_REGULAR. The baseload-CF filter below excludes cyclic units
# where a depressed CF ceiling is economic part-load rather than an outage.
_DETECT_GROUPS: frozenset[str] = frozenset({"COAL", "CC_REGULAR"})
_BASELOAD_CF = 0.55  # only plants that normally run near their ceiling


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--iso", default="ERCOT")
    ap.add_argument(
        # W1 collapsed inputs/raw-data into data/raw — this is the location
        # the historic-outage overlay actually reads (outages.py).
        "--out",
        default=str(REPO / "data" / "raw" / "campd-partial-outages.csv"),
    )
    args = ap.parse_args()

    bins = load_campd_bins("data/raw/reference/custom-bin-assignments.csv")
    cap = dict(zip(bins["Plant_Code"].astype(int), bins["capacity_mw"]))
    name = dict(zip(bins["Plant_Code"].astype(int), bins["Plant_Name"]))
    group = dict(zip(bins["Plant_Code"].astype(int), bins["Plant_Group"]))
    candidates = [c for c in cap if group.get(c) in _DETECT_GROUPS]

    rows = []
    for yr in args.years:
        df = campd.load_campd_hourly(campd.states_for_iso(args.iso), [yr])
        if df.empty:
            continue
        # Clip an in-progress year's clock at the CAMPD publication horizon so
        # unpublished months are not zero-filled into a phantom full outage
        # (same fix as derive_campd_unit_outages.py / derive_campd_outages.py).
        end = min(
            pd.Timestamp(f"{yr}-12-31 23:00"),
            df["date"].max() + pd.Timedelta(hours=23),
        )
        full = pd.date_range(f"{yr}-01-01", end, freq="h")
        for code in candidates:
            g = campd.plant_hourly_grid(df, code, yr)
            if g.empty or cap[code] <= 0:
                continue
            cf = (g["gross_mw"].reindex(full).fillna(0.0) / cap[code]).to_numpy(
                dtype=float
            )
            # Coal is all-or-nothing per unit, and a derate cap only binds when
            # the model wants to run above the observed ceiling, so it is safe
            # to detect even on cyclic coal. CC part-loads economically, so its
            # depressed ceilings are only trustworthy on baseload units.
            if group.get(code) == "CC_REGULAR" and cf.mean() < _BASELOAD_CF:
                continue
            for s, e, factor in _detect(cf):
                rows.append(
                    {
                        "oris_code": code,
                        "plant_name": name.get(code, code),
                        "plant_group": group.get(code, ""),
                        "year": yr,
                        "outage_start": full[s * 24].strftime("%Y-%m-%d %H:00:00"),
                        "outage_stop": (full[min(e * 24, len(full) - 1)]).strftime(
                            "%Y-%m-%d %H:00:00"
                        ),
                        "derate_factor": factor,
                    }
                )
    out = pd.DataFrame(
        rows,
        columns=[
            "oris_code",
            "plant_name",
            "plant_group",
            "year",
            "outage_start",
            "outage_stop",
            "derate_factor",
        ],
    ).sort_values(["year", "oris_code", "outage_start"])
    out.to_csv(args.out, index=False)
    print(f"wrote {len(out)} partial-outage windows to {args.out}")
    for yr in args.years:
        print(
            f"  {yr}: {(out['year'] == yr).sum()} windows, "
            f"{out[out['year'] == yr]['oris_code'].nunique()} plants"
        )


if __name__ == "__main__":
    main()
