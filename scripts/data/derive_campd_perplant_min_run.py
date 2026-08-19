"""Derive each bridge plant's own measured minimum-run duration from CAMPD.

The per-PLANT identification for the NYISO gas commitment bridge's minimum-run
extension (``ScenarioConfig.nyiso_gas_bridge_plant_min_run``), replacing the
two per-class scalars (``nyiso_gas_bridge_cc_min_run_hours`` /
``..._st_min_run_hours``) for every plant the meter can identify. nyiso-146
phase 0 (``scripts/probes/_nyiso146_perplant_minrun_phase0.py``, record
``results/calibration/_nyiso146_perplant_minrun_phase0.json``) measured that
the CC_REGULAR class is NOT one run-length population: per-plant p25 spans
7 h (Carr Street, a true cycler) to 646 h (Caithness, near-baseload) — a 92x
spread that no class scalar can describe. Bethlehem Energy Center (2539), the
nyiso-145 over-cycling object, measures p25 = 134.8 h against the keeper's
class scalar of 21 h.

BASIS — plant-summed series, not per-unit. A facility's units are summed to
ONE series per year BEFORE the online threshold (the lay-up artifact's own
construction, ``derive_campd_bridge_layup_exclusions.py``: "units summed to
one PLANT series"), so unit rotation inside a continuously-online plant is not
a restart. This is the basis the mechanism itself lives on: the bridge floors
``min_load_frac x PLANT capacity`` per LP row, the LP's per-plant tranches
share one plant dispatch pattern (the model has no unit rotation), and the
nyiso-145 starts-vs-metered object is measured at 0.05 x plant nameplate. The
per-unit basis conflates rotation with cycling — Bethlehem's per-unit p25 is
13 h while its plant series starts 6-7 times a year in runs of median
487-1,217 h.

STATISTIC — p25 of the plant's own within-year run-length distribution,
pre-registered at phase 0 BEFORE any solve
(``results/calibration/PREREG-nyiso146-perplant-min-run-2026-08-19.md``):

* An OBSERVED run length is an upper-ish bound on a minimum-run CONSTRAINT
  (a unit that ran 21 h because it was economic does not prove a 21 h floor),
  so the observed distribution bounds the constraint from ABOVE and a LOW
  order statistic is the correct estimator — the keeper's class p50
  overstates by its own field docstring's reasoning.
* p25 rather than p10 because runs are computed WITHIN a year (the class
  artifact's convention, so runs never stitch across a vintage boundary):
  every run spanning a year boundary splits into two spurious short ones and
  p10 absorbs that truncation artifact. Same reasoning, same choice, as the
  pre-registered CT leg (``nyiso_gas_bridge_ct_min_run_hours`` = p25,
  docs/handoffs/nyiso90-preregistration.md §2).

EXCLUSION — the Astoria campus facility-ID collision. CAMPD reports Astoria
Energy (EIA 55375) and Astoria Energy II (EIA 57664) under ONE facilityId
(55375, all four CTs), so the "plant" series there is two EIA plants summed —
a boundary misaligned to the model's representation, which carries both
separately. Rule 14 [R-ACCURATE]'s misalignment clause applies: using the
campus series literally would identify either plant's minimum run from the
other plant's conduct, so BOTH are left out of the artifact and fall back to
the class scalar (57664 has no CAMPD rows of its own and falls back anyway).
The campus benchmark attribution itself is a separate chartered object
(nyiso-145 §5) and is NOT touched here.

Output: ``data/raw/_processed-legacy/campd_perplant_min_run_{ISO}.csv`` — one
row per measured plant (lay-up-excluded plants included: the bridge's
membership gate scopes them out at consumption, so their rows are inert but
keep the artifact a complete record of the measurement).

Governance (rules 13 [R-MEASURED] / 23 [R-FROZEN-DERIVE]): a measured
unit-conduct statistic in the same admissibility class as the bridge's
min-load fractions and the lay-up plant-code set — it regenerates from the
CAMPD pipeline for any new vintage, responds to changed conduct (a plant that
starts cycling shortens its own measured runs), and re-derives ONLY when the
source data updates, never because a residual moved.

Usage::

    python scripts/data/derive_campd_perplant_min_run.py --iso NYISO
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

from derive_campd_gas_commitment_params import (  # noqa: E402
    _HSL_PCTILE,
    _ONLINE_FRAC,
    TARGET_CLASSES,
    class_plant_codes,
    unit_run_lengths,
)
from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data.campd import _ONLINE_MW, states_for_iso  # noqa: E402

UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"

# The identification percentile — pre-registered at nyiso-146 phase 0, see the
# module docstring. Never swept (rules 5 / 21 / 23).
_MIN_RUN_PCTILE: float = 25.0

# EIA plant codes whose CAMPD facility series is NOT that plant's own conduct:
# the Astoria campus facility-ID collision (nyiso-145 §5 — CAMPD folds Astoria
# Energy II, EIA 57664, into facilityId 55375). Excluded from the artifact so
# a misaligned boundary can never identify a per-plant value; both plants fall
# back to the class scalar at consumption. Keyed per ISO so the derivation
# stays ISO-generic.
MISALIGNED_FACILITIES: dict[str, frozenset[int]] = {
    "NYISO": frozenset({55375}),
}


def per_plant_min_run(iso: str, years: list[int]) -> pd.DataFrame:
    """Measure each target-class plant's own run-length distribution.

    Args:
        iso: The ISO name.
        years: CAMPD vintages to pool (runs computed within each year).

    Returns:
        One row per measured facility with its plant-basis run statistics and
        the identified ``min_run_hours`` (the pre-registered p25).
    """
    mapping, ambiguous = class_plant_codes(iso, TARGET_CLASSES)
    if not mapping:
        raise SystemExit(f"{iso}: model fleet has no {TARGET_CLASSES} plants")
    if ambiguous:
        print(
            f"  (dropping {len(ambiguous)} mixed-class plant code(s), "
            f"unattributable at CAMPD facility level: {ambiguous})"
        )
    misaligned = MISALIGNED_FACILITIES.get(iso.upper(), frozenset())
    codes = set(mapping) - misaligned
    if misaligned & set(mapping):
        print(
            f"  (excluding misaligned CAMPD facility id(s) "
            f"{sorted(misaligned & set(mapping))} — series spans more than "
            "one EIA plant; class-scalar fallback applies)"
        )

    # {facility: {year: [unit chunks]}} — summed to one plant series per year.
    by_plant: dict[int, dict[int, list[np.ndarray]]] = {}
    names: dict[int, str] = {}
    for state in states_for_iso(iso):
        for year in years:
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
            for (fid, _uid), g in df.groupby(["facilityId", "unitId"], sort=False):
                fid = int(fid)
                by_plant.setdefault(fid, {}).setdefault(year, []).append(
                    g["grossLoad"].fillna(0.0).to_numpy(dtype=float)
                )
                names[fid] = str(g["facilityName"].iloc[0])

    if not by_plant:
        raise SystemExit(f"{iso}: no CAMPD hours found for {TARGET_CLASSES}")

    years_tag = "-".join(str(y) for y in years)
    rows = []
    for fid in sorted(by_plant):
        # Sum the facility's units to ONE series per year. Unit chunks within
        # a (facility, year) can differ in length when a unit reports fewer
        # hours; align by truncating to the shortest (the summed series is
        # only defined where all reporting units have hours).
        yearly: list[np.ndarray] = []
        for year in sorted(by_plant[fid]):
            chunks = by_plant[fid][year]
            n = min(c.size for c in chunks)
            yearly.append(np.sum([c[:n] for c in chunks], axis=0))
        pooled = np.concatenate(yearly)
        hsl = float(np.percentile(pooled, _HSL_PCTILE))
        if hsl <= _ONLINE_MW:
            continue  # never meaningfully online in the window
        thresh = max(_ONLINE_MW, _ONLINE_FRAC * hsl)
        runs: list[int] = []
        runs_by_year: list[int] = []
        for series in yearly:
            r = unit_run_lengths(series >= thresh)
            runs.extend(r)
            runs_by_year.append(len(r))
        if not runs:
            continue  # online hours exist but never form a run (degenerate)
        arr = np.asarray(runs, dtype=float)
        rows.append(
            {
                "iso": iso,
                "plant_code": fid,
                "plant_name": names[fid],
                "plant_class": mapping[fid],
                "plant_hsl_mw": round(hsl, 1),
                "n_runs": int(arr.size),
                "runs_by_year": "/".join(str(n) for n in runs_by_year),
                "online_share": round(float((pooled >= thresh).mean()), 4),
                "min_run_hours": float(np.percentile(arr, _MIN_RUN_PCTILE)),
                "run_h_p10": float(np.percentile(arr, 10)),
                "run_h_p25": float(np.percentile(arr, 25)),
                "run_h_p50": float(np.percentile(arr, 50)),
                "run_h_p75": float(np.percentile(arr, 75)),
                "years": years_tag,
                "source": (
                    "EPA CAMPD unit-level hourly grossLoad "
                    "(data/raw/campd-unit-level), units summed to one PLANT "
                    f"series per year; online >= max({_ONLINE_MW} MW, "
                    f"{_ONLINE_FRAC} x plant HSL=p{_HSL_PCTILE}); runs within "
                    f"a year; min_run_hours = p{_MIN_RUN_PCTILE:.0f} of the "
                    "plant's own run lengths (pre-registered, "
                    "PREREG-nyiso146-perplant-min-run-2026-08-19.md)"
                ),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    """Derive and write the per-plant minimum-run artifact."""
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

    df = per_plant_min_run(iso, args.years)
    if df.empty:
        raise SystemExit(f"{iso}: no plants measured — nothing to write")
    out_path = (
        Path(args.out)
        if args.out
        else (PROCESSED_DIR / f"campd_perplant_min_run_{iso}.csv")
    )
    df.to_csv(out_path, index=False)
    print(f"wrote {out_path} ({len(df)} rows)")
    print(
        df[
            [
                "plant_code",
                "plant_name",
                "plant_class",
                "plant_hsl_mw",
                "n_runs",
                "online_share",
                "min_run_hours",
                "run_h_p50",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
