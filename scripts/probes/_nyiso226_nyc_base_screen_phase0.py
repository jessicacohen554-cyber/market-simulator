"""nyiso-226 phase 0 — the PER-YEAR LP-input footprint of re-basing the NYC ST_GAS
persistent-base floor coefficient, and the screen year that footprint names.

ZERO LP. Two ``run_year(fleet_only=True)`` rebuilds per year — the keeper's own recipe
with the frozen coefficient, and the same recipe with the basis-matched one — differenced
at the ``min_gen`` array. No solve, no price, no residual is opened at any point
(rule 29 ``[R-SCREEN]``: the screen year is named on the mechanism's own measured
FOOTPRINT, never on where the residual is largest).

THE OBJECT — the one live ``NYISO,NYC,ST_GAS,tmax,-50.0`` row of
``data/raw/reference/reliability_floor_coeffs_NYISO.csv``, ``floor_pct`` frozen at
**0.1750** (a fleet-aggregate DAILY-MEAN cool-day when-available CF p25) against the
basis-matched **0.16629202320362052** (the same statistic aggregated HOURLY, which is the
grain ``_apply_frac`` applies it on). nyiso-203 measured the pair and reported the gap;
the owner ruled 2026-09-10 that it is screened on one year before the span is spent.

Reported per year:

  * ``delta_min_gen_twh`` — the LP-input energy the re-basing REMOVES from the floor.
  * ``rows_touched`` / ``hours_touched`` — the CONFINEMENT leg: the delta must live on
    NYC ST_GAS rows and nowhere else, or the artifact edit reaches further than it claims.
  * ``ratio_to_frozen`` — must equal ``1 - 0.16629.../0.1750`` on every touched cell, which
    is the identity a pro_rata coefficient change asserts.

Writes ``results/calibration/_nyiso226_nyc_base_phase0.json``.
Reproduce with ``PYTHONPATH=.:src uv run python scripts/probes/_nyiso226_nyc_base_screen_phase0.py``.
"""

from __future__ import annotations

import csv as _csv
import json
import shutil
import tempfile
from pathlib import Path

import numpy as np

from market_sim.config.paths import REFERENCE_DIR, REPO_ROOT

BUNDLE = REPO_ROOT / "results" / "calibration" / "nyiso_fuelvintage_A"
YEARS = (2023, 2024, 2025)
ISO = "NYISO"
FROZEN = 0.175
# nyiso-203 results/calibration/_nyiso203_nyc_base_phase0.json applied_basis.fleet_hourly_p25
REBASED = 0.16629202320362052
ZONE, PLANT_CLASS, DRIVER, THRESHOLD = "NYC", "ST_GAS", "tmax", "-50.0"
COEFFS = REFERENCE_DIR / f"reliability_floor_coeffs_{ISO}.csv"
OUT = REPO_ROOT / "results" / "calibration" / "_nyiso226_nyc_base_phase0.json"


def rewrite_coefficient(value: float) -> None:
    """Rewrite the ONE target row's ``floor_pct`` in place, leaving every other byte."""
    with COEFFS.open(newline="") as fh:
        reader = _csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    hits = 0
    for row in rows:
        if (
            row["zone"] == ZONE
            and row["plant_class"] == PLANT_CLASS
            and row["driver"] == DRIVER
            and row["threshold"].strip() == THRESHOLD
        ):
            row["floor_pct"] = repr(value)
            hits += 1
    if hits != 1:
        raise SystemExit(f"expected exactly 1 target row, matched {hits}")
    with COEFFS.open("w", newline="") as fh:
        w = _csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def rebuild(year: int, work: Path) -> dict:
    """Return the ``fleet_only`` floor arrays for ``year`` on a scratch bundle copy."""
    import importlib

    import market_sim.config.iso_configs as iso_configs

    importlib.reload(iso_configs)
    import scripts.legitimacy_diagnostics as ld

    importlib.reload(ld)
    arrays, _ = ld.load_or_rebuild_floors(work, ISO, year, force_rebuild=True)
    return arrays


def main() -> None:
    """Difference the two rebuilds per year and name the screen year."""
    original = COEFFS.read_bytes()
    rec: dict = {
        "object": {
            "csv": str(COEFFS.relative_to(REPO_ROOT)),
            "zone": ZONE,
            "plant_class": PLANT_CLASS,
            "driver": DRIVER,
            "threshold_c": float(THRESHOLD),
            "frozen_floor_pct": FROZEN,
            "rebased_floor_pct": REBASED,
            "relative_change": REBASED / FROZEN - 1.0,
        },
        "keeper_bundle": str(BUNDLE.relative_to(REPO_ROOT)),
        "years": {},
    }
    try:
        for year in YEARS:
            per: dict[str, dict] = {}
            for leg, value in (("frozen", FROZEN), ("rebased", REBASED)):
                with tempfile.TemporaryDirectory() as td:
                    work = Path(td) / "bundle"
                    work.mkdir()
                    shutil.copy(BUNDLE / "meta.json", work / "meta.json")
                    rewrite_coefficient(value)
                    per[leg] = rebuild(year, work)
            a, b = per["frozen"], per["rebased"]
            if not np.array_equal(a["unit_ids"], b["unit_ids"]):
                raise SystemExit(f"{year}: unit axis moved between legs")
            d = a["min_gen"].astype(np.float64) - b["min_gen"].astype(np.float64)
            touched = np.abs(d) > 1e-9
            rows = np.flatnonzero(touched.any(axis=1))
            groups = np.asarray(a["plant_group"], dtype=str)
            codes = np.asarray(a["plant_code"], dtype=np.int64)
            frozen_on_touched = a["min_gen"].astype(np.float64)[touched]
            ratio = np.divide(
                d[touched],
                frozen_on_touched,
                out=np.zeros_like(frozen_on_touched),
                where=frozen_on_touched > 0,
            )
            rec["years"][str(year)] = {
                "delta_min_gen_twh": float(d.sum()) / 1e6,
                "frozen_min_gen_total_twh": float(a["min_gen"].sum()) / 1e6,
                "rebased_min_gen_total_twh": float(b["min_gen"].sum()) / 1e6,
                "rows_touched": int(rows.size),
                "rows_total": int(a["min_gen"].shape[0]),
                "hours_touched": int(touched.any(axis=0).sum()),
                "cells_touched": int(touched.sum()),
                "touched_groups": sorted({str(g) for g in groups[rows]}),
                "touched_plant_codes": sorted({int(c) for c in codes[rows]}),
                "ratio_min": float(ratio.min()) if ratio.size else 0.0,
                "ratio_max": float(ratio.max()) if ratio.size else 0.0,
                "expected_ratio": 1.0 - REBASED / FROZEN,
                "max_delta_mw": float(np.abs(d).max()),
                "mean_delta_mw_touched_hours": float(
                    d.sum(axis=0)[touched.any(axis=0)].mean()
                )
                if touched.any()
                else 0.0,
            }
            y = rec["years"][str(year)]
            print(
                f"{year}: delta {y['delta_min_gen_twh']:+.6f} TWh  rows {y['rows_touched']}"
                f"/{y['rows_total']}  hours {y['hours_touched']}  groups {y['touched_groups']}"
                f"  plants {y['touched_plant_codes']}"
                f"  ratio [{y['ratio_min']:.6f},{y['ratio_max']:.6f}]"
                f" vs expected {y['expected_ratio']:.6f}"
            )
    finally:
        COEFFS.write_bytes(original)
        print(f"\nrestored {COEFFS.relative_to(REPO_ROOT)} to its committed bytes")

    footprints = {y: abs(v["delta_min_gen_twh"]) for y, v in rec["years"].items()}
    screen_year = max(footprints, key=footprints.get)
    rec["screen_year"] = int(screen_year)
    rec["screen_year_basis"] = (
        "argmax over years of |delta min_gen TWh| — the mechanism's OWN measured "
        "LP-input footprint (rule 29 [R-SCREEN]); no residual, price or metric was read"
    )
    print(f"\nfootprints (|delta| TWh): {footprints}")
    print(f"SCREEN YEAR = {screen_year} (largest own footprint)")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=2, sort_keys=True))
    print(f"wrote {OUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
