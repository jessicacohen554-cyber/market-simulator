"""Derive measured simple-cycle CT start-to-stop run lengths from CAMPD.

Source basis for the fast-start amortization v3
(``ScenarioConfig.tranche_startup_measured_runs``): the v2 lever amortizes a
fast-start tranche's NREL start cost over the tranche's own P0 run lengths,
which is circular when the offer level itself is wrong — offers too cheap →
P0 runs the CTs in long blocks → per-MWh amortized start cost ≈ 0 → the lever
self-disables (the nyiso-44 probe finding). Real GT offers form the other way
round: start recovery is amortized over the unit's EX-ANTE expected run, which
is a measured operating statistic, not a model output.

This script measures that statistic. For every simple-cycle combustion-turbine
unit in the ISO's CAMPD unit-level extracts
(``data/raw/campd-unit-level/{STATE}_{YEAR}.parquet``), a *run* is a maximal
block of consecutive hours with gross load at or above the online threshold
(:data:`market_sim.data.campd._ONLINE_MW`, the same convention as the CAMPD
start/stop factor machinery). Runs are pooled across the requested years
(default 2023-2025) and aggregated per facility; an ISO-class fallback row
(``plant_code = 0``) pools every run in the ISO so plants without CEMS
coverage inherit the class-median horizon.

Rows are restricted to facilities present in the ISO's model fleet with a
``CT_PEAKER`` / ``CT_CHP`` unit (so e.g. New Jersey PJM-side plants can never
leak into the NYISO artifact through the shared NJ state extract), and to
CAMPD ``unitType`` "Combustion turbine" (simple cycle) — combined-cycle
blocks are a different commitment object and are excluded.

Output: ``data/raw/_processed-legacy/campd_ct_run_lengths_{ISO}.csv``,
consumed by :func:`market_sim.data.fleet.campd_ct_run_lengths`.

Governance (CLAUDE.md rules #12/#23): a measured market-behaviour parameter in
the same admissibility class as the CAMPD committed shares / min-stable loads
— it regenerates from the CAMPD pipeline for any new vintage and re-derives
only when its source data updates, never because a residual moved.

Usage::

    python scripts/derive_campd_ct_run_lengths.py --iso NYISO
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data.campd import _ONLINE_MW, states_for_iso  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"

# Model classes whose fast-start tranches consume the measured horizon.
CT_CLASSES: frozenset[str] = frozenset({"CT_PEAKER", "CT_CHP"})


def unit_run_lengths(on: np.ndarray) -> list[int]:
    """Return the lengths (hours) of maximal True-blocks in ``on``."""
    if not on.any():
        return []
    d = np.diff(np.concatenate([[0], on.astype(np.int8), [0]]))
    starts = np.where(d == 1)[0]
    ends = np.where(d == -1)[0]
    return (ends - starts).tolist()


def facility_runs(df: pd.DataFrame) -> dict[str, list[int]]:
    """Pool per-unit run lengths by facility from one unit-level frame."""
    out: dict[str, list[int]] = {}
    for (fid, _uid), g in df.groupby(["facilityId", "unitId"], sort=False):
        g = g.sort_values(["date", "hour"])
        on = (g["grossLoad"].fillna(0.0) >= _ONLINE_MW).to_numpy()
        runs = unit_run_lengths(on)
        if runs:
            out.setdefault(str(fid), []).extend(runs)
    return out


def main() -> None:
    """Derive and write the per-facility measured CT run-length artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, help="ISO name, e.g. NYISO")
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2023, 2024, 2025],
        help="CAMPD vintages to pool (default 2023 2024 2025)",
    )
    parser.add_argument("--out", default=None, help="Output CSV path override")
    args = parser.parse_args()
    iso = args.iso.upper()

    # The ISO's own CT-class plants — the fleet filter that keeps shared-state
    # extracts (e.g. NJ for NYISO) from leaking other-ISO plants in.
    fleet = load_fleet_from_csv(iso, get_iso_config(iso))
    ct_plants = {int(g.plant_code) for g in fleet if g.plant_group in CT_CLASSES} - {0}
    if not ct_plants:
        raise SystemExit(f"{iso}: model fleet has no CT-class plants")

    pooled: dict[str, list[int]] = {}
    names: dict[str, str] = {}
    n_units: dict[str, set] = {}
    for state in states_for_iso(iso):
        for year in args.years:
            path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                print(f"  (skip {path.name}: not on disk)")
                continue
            df = pd.read_parquet(
                path,
                columns=[
                    "facilityId",
                    "facilityName",
                    "unitId",
                    "unitType",
                    "date",
                    "hour",
                    "grossLoad",
                ],
            )
            # Simple-cycle combustion turbines only; the ISO's own CT plants.
            df = df[
                df["unitType"].str.contains("combustion turbine", case=False, na=False)
            ]
            df = df[pd.to_numeric(df["facilityId"], errors="coerce").isin(ct_plants)]
            if df.empty:
                continue
            for fid, runs in facility_runs(df).items():
                pooled.setdefault(fid, []).extend(runs)
            for fid, g in df.groupby("facilityId"):
                names[str(fid)] = str(g["facilityName"].iloc[0])
                n_units.setdefault(str(fid), set()).update(g["unitId"].unique())

    if not pooled:
        raise SystemExit(f"{iso}: no CAMPD CT runs found — nothing to write")

    years_tag = "-".join(str(y) for y in args.years)
    rows = []
    for fid, runs in sorted(pooled.items(), key=lambda kv: int(kv[0])):
        arr = np.asarray(runs, dtype=float)
        rows.append(
            {
                "plant_code": int(fid),
                "plant_name": names.get(fid, ""),
                "n_units": len(n_units.get(fid, ())),
                "n_runs": arr.size,
                "median_run_hours": float(np.median(arr)),
                "mean_run_hours": float(arr.mean()),
                "p90_run_hours": float(np.percentile(arr, 90)),
                "years": years_tag,
                "source": "EPA CAMPD unit-level hourly grossLoad "
                "(data/raw/campd-unit-level), simple-cycle CT units, "
                f"online >= {_ONLINE_MW} MW",
            }
        )
    # ISO-class fallback (plant_code 0): every run in the ISO pooled, the
    # horizon for CT plants without CEMS coverage.
    all_runs = np.asarray([r for runs in pooled.values() for r in runs], dtype=float)
    rows.append(
        {
            "plant_code": 0,
            "plant_name": f"{iso} CT class fallback (all runs pooled)",
            "n_units": sum(len(v) for v in n_units.values()),
            "n_runs": all_runs.size,
            "median_run_hours": float(np.median(all_runs)),
            "mean_run_hours": float(all_runs.mean()),
            "p90_run_hours": float(np.percentile(all_runs, 90)),
            "years": years_tag,
            "source": "pooled ISO CT class fallback",
        }
    )

    out_path = (
        Path(args.out)
        if args.out
        else (PROCESSED_DIR / f"campd_ct_run_lengths_{iso}.csv")
    )
    out = pd.DataFrame(rows)
    out.to_csv(out_path, index=False)
    print(f"wrote {out_path} ({len(out)} rows)")
    print(
        out[
            ["plant_code", "plant_name", "n_runs", "median_run_hours", "p90_run_hours"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
