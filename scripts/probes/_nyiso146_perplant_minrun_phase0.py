#!/usr/bin/env python3
"""nyiso-146 phase 0 — is the CC class ONE run-length population? (no solve)

The keeper (`2026-08-18-nyiso-144-layup-exclusion`) sets the NYISO gas
commitment bridge's minimum-run extension from TWO CLASS SCALARS:
``nyiso_gas_bridge_cc_min_run_hours = 21.0`` and ``..._st_min_run_hours =
13.0`` — the capacity-weighted CAMPD p50 of the pooled class run-length
distribution. nyiso-145 measured that the LP starts Bethlehem Energy Center
(2539) 262-302 times a year in runs of median 5-9 h against 5-7 metered starts
in runs of median 487-1,217 h, while Richard M Flynn (7314) has the RIGHT run
length and only ~3x the start count. One class scalar cannot describe both —
IF the per-plant distributions really are that far apart.

This probe makes that measurement, per plant, from CAMPD 2023-2025, using the
IDENTICAL construction the class artifact uses
(``scripts/data/derive_campd_gas_commitment_params.py``: online threshold
``max(_ONLINE_MW, 0.05 x unit HSL)``, runs computed WITHIN a year, each run
weighted by its unit's HSL) — the only change is that runs are aggregated per
FACILITY instead of pooled per class. It gates the nyiso-146 lever:

* (a) if the per-plant p25/p50 spread across the bridge population is wide
  (orders of magnitude), the class scalar is provably not a description of the
  population and the per-plant identification proceeds;
* if the spread is narrow, the class scalar is NOT the defect and the lever is
  REFUSED with no solve spent.

NO SOLVE, NO MODEL OUTPUT — pure measured-conduct data (rule 13
[R-MEASURED] admissible: regenerates for any CAMPD vintage, responds to
changed conduct). Years 2023-2025 only (rule 22; holdout freeze ACTIVE).

Usage::

    python scripts/probes/_nyiso146_perplant_minrun_phase0.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

from derive_campd_gas_commitment_params import (  # noqa: E402
    _HSL_PCTILE,
    _ONLINE_FRAC,
    TARGET_CLASSES,
    class_plant_codes,
    unit_run_lengths,
    weighted_percentile,
)
from market_sim.config.paths import RAW_DIR  # noqa: E402
from market_sim.data.campd import _ONLINE_MW, states_for_iso  # noqa: E402

ISO = "NYISO"
YEARS = [2023, 2024, 2025]
UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"
LAYUP_CSV = RAW_DIR / "_processed-legacy" / "campd_bridge_layup_exclusions_NYISO.csv"
OUT = REPO / "results/calibration/_nyiso146_perplant_minrun_phase0.json"

# The keeper's class scalars (run_config.json of
# results/calibration/nyiso144_layup_arm): the values under test.
KEEPER_CLASS_SCALAR = {"CC_REGULAR": 21.0, "ST_GAS": 13.0}


def per_plant_runs() -> pd.DataFrame:
    """Return one row per plant with its own run-length distribution.

    Identical construction to ``derive_campd_gas_commitment_params.
    unit_statistics`` (same online threshold, same within-year run split, same
    HSL run weights) — only the aggregation key changes from class to
    facility.
    """
    mapping, ambiguous = class_plant_codes(ISO, TARGET_CLASSES)
    codes = set(mapping)
    # {(facility, unit): [per-year load arrays]}
    loads: dict[tuple[int, str], list[np.ndarray]] = {}
    names: dict[tuple[int, str], str] = {}
    for state in states_for_iso(ISO):
        for year in YEARS:
            path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                continue
            df = pd.read_parquet(
                path,
                columns=[
                    "facilityId",
                    "facilityName",
                    "unitId",
                    "date",
                    "hour",
                    "grossLoad",
                ],
            )
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            df = df[df["facilityId"].isin(codes)]
            if df.empty:
                continue
            df = df.sort_values(["facilityId", "unitId", "date", "hour"])
            for (fid, uid), g in df.groupby(["facilityId", "unitId"], sort=False):
                key = (int(fid), str(uid))
                loads.setdefault(key, []).append(
                    g["grossLoad"].fillna(0.0).to_numpy(dtype=float)
                )
                names[key] = str(g["facilityName"].iloc[0])

    # Per-plant pooled (run_hours, unit HSL) pairs — the UNIT basis (one
    # CEMS unit's own on-blocks, unit rotation inside a committed plant
    # counts as cycling).
    plant_runs: dict[int, list[tuple[float, float]]] = {}
    plant_name: dict[int, str] = {}
    plant_hsl: dict[int, float] = {}
    plant_online: dict[int, list[tuple[int, int]]] = {}
    # {facility: {year_index: [unit chunks]}} — for the PLANT basis the
    # facility's units are summed to ONE series per year BEFORE the threshold
    # (the lay-up artifact's own construction, "units summed to one PLANT
    # series"), so unit rotation inside a continuously-on plant is NOT a
    # restart. This is the basis of the nyiso-145 starts-vs-metered object
    # (0.05 x plant npl) and of the floor itself (min_load x PLANT capacity).
    plant_series: dict[int, dict[int, list[np.ndarray]]] = {}
    for (fid, uid), chunks in loads.items():
        pooled = np.concatenate(chunks)
        hsl = float(np.percentile(pooled, _HSL_PCTILE))
        if hsl <= _ONLINE_MW:
            continue
        thresh = max(_ONLINE_MW, _ONLINE_FRAC * hsl)
        runs: list[int] = []
        for chunk in chunks:
            runs.extend(unit_run_lengths(chunk >= thresh))
        plant_runs.setdefault(fid, []).extend((float(r), hsl) for r in runs)
        plant_name[fid] = names[(fid, uid)]
        plant_hsl[fid] = plant_hsl.get(fid, 0.0) + hsl
        plant_online.setdefault(fid, []).append(
            (int((pooled >= thresh).sum()), int(pooled.size))
        )
        for yi, chunk in enumerate(chunks):
            plant_series.setdefault(fid, {}).setdefault(yi, []).append(chunk)

    # PLANT-basis runs: sum unit series per (facility, year), threshold at
    # max(_ONLINE_MW, _ONLINE_FRAC x plant HSL) where plant HSL is p99.5 of
    # the summed series pooled over the window — the same statistic, plant
    # basis. Unit chunks within a (facility, year) can differ in length when
    # a unit reports fewer hours; align by truncating to the shortest (the
    # summed series is only defined where all reporting units have hours).
    plant_basis_runs: dict[int, list[float]] = {}
    plant_basis_nruns_by_year: dict[int, list[int]] = {}
    for fid, by_year in plant_series.items():
        yearly: list[np.ndarray] = []
        for yi in sorted(by_year):
            chunks = by_year[yi]
            n = min(c.size for c in chunks)
            yearly.append(np.sum([c[:n] for c in chunks], axis=0))
        pooled = np.concatenate(yearly)
        hsl = float(np.percentile(pooled, _HSL_PCTILE))
        if hsl <= _ONLINE_MW:
            continue
        thresh = max(_ONLINE_MW, _ONLINE_FRAC * hsl)
        runs = []
        nby = []
        for series in yearly:
            r = unit_run_lengths(series >= thresh)
            runs.extend(r)
            nby.append(len(r))
        plant_basis_runs[fid] = [float(r) for r in runs]
        plant_basis_nruns_by_year[fid] = nby

    layup = set()
    if LAYUP_CSV.exists():
        layup = set(
            pd.read_csv(LAYUP_CSV)["plant_code"].astype(int).tolist()
        )

    mapping = class_plant_codes(ISO, TARGET_CLASSES)[0]
    rows = []
    for fid, pairs in sorted(plant_runs.items()):
        arr = np.asarray(pairs, dtype=float).reshape(-1, 2)
        rh, rw = arr[:, 0], arr[:, 1]
        on = plant_online[fid]
        pb = np.asarray(plant_basis_runs.get(fid, []), dtype=float)
        rows.append(
            {
                "plant_code": int(fid),
                "plant_name": plant_name[fid],
                "plant_class": mapping[fid],
                "layup_excluded": bool(fid in layup),
                "n_units": int(len(on)),
                "hsl_sum_mw": round(plant_hsl[fid], 1),
                "n_runs": int(rh.size),
                "online_share": round(
                    sum(o for o, _ in on) / max(1, sum(t for _, t in on)), 4
                ),
                "run_h_p10": round(weighted_percentile(rh, rw, 10.0), 1),
                "run_h_p25": round(weighted_percentile(rh, rw, 25.0), 1),
                "run_h_p50": round(weighted_percentile(rh, rw, 50.0), 1),
                "run_h_p75": round(weighted_percentile(rh, rw, 75.0), 1),
                "run_h_p25_eq": round(float(np.percentile(rh, 25)), 1),
                "run_h_p50_eq": round(float(np.percentile(rh, 50)), 1),
                "plant_runs_n": int(pb.size),
                "plant_runs_by_year": plant_basis_nruns_by_year.get(fid, []),
                "plant_run_h_p10": (
                    round(float(np.percentile(pb, 10)), 1) if pb.size else None
                ),
                "plant_run_h_p25": (
                    round(float(np.percentile(pb, 25)), 1) if pb.size else None
                ),
                "plant_run_h_p50": (
                    round(float(np.percentile(pb, 50)), 1) if pb.size else None
                ),
                "plant_run_h_p75": (
                    round(float(np.percentile(pb, 75)), 1) if pb.size else None
                ),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    """Measure, print, and record the per-plant run-length distributions."""
    df = per_plant_runs()
    live = df[~df["layup_excluded"]]
    print(f"{ISO} bridge population (lay-up-excluded rows shown but scoped out "
          f"of the keeper's bridge):\n")
    cols = [
        "plant_code", "plant_name", "plant_class", "layup_excluded", "n_units",
        "hsl_sum_mw", "online_share", "n_runs", "run_h_p25", "run_h_p50",
        "plant_runs_n", "plant_run_h_p10", "plant_run_h_p25",
        "plant_run_h_p50", "plant_run_h_p75",
    ]
    print(df.sort_values(["plant_class", "plant_run_h_p50"])[cols].to_string(index=False))

    verdict = {}
    for klass, scalar in KEEPER_CLASS_SCALAR.items():
        sel = live[live["plant_class"] == klass]
        if sel.empty:
            continue
        p25 = sel["run_h_p25"]
        pp25 = sel["plant_run_h_p25"].dropna()
        verdict[klass] = {
            "keeper_class_scalar_p50_capwtd": scalar,
            "n_plants": int(len(sel)),
            "unit_basis_p25_min": float(p25.min()),
            "unit_basis_p25_max": float(p25.max()),
            "plant_basis_p25_min": float(pp25.min()),
            "plant_basis_p25_max": float(pp25.max()),
            "plant_basis_p25_spread_ratio": float(pp25.max() / max(pp25.min(), 0.1)),
            "plant_basis_p50_min": float(sel["plant_run_h_p50"].dropna().min()),
            "plant_basis_p50_max": float(sel["plant_run_h_p50"].dropna().max()),
        }
    print("\nPhase-0(a) spread verdict (live bridge population only):")
    print(json.dumps(verdict, indent=2))

    OUT.write_text(
        json.dumps(
            {
                "probe": "_nyiso146_perplant_minrun_phase0",
                "iso": ISO,
                "years": YEARS,
                "construction": (
                    "derive_campd_gas_commitment_params.unit_statistics "
                    "verbatim (online >= max(_ONLINE_MW, 0.05 x unit HSL), "
                    "runs within-year, HSL run weights), aggregated per "
                    "facility instead of per class"
                ),
                "keeper_class_scalars": KEEPER_CLASS_SCALAR,
                "plants": df.to_dict(orient="records"),
                "spread_verdict": verdict,
            },
            indent=1,
        )
        + "\n"
    )
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
