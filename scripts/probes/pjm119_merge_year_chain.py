"""Merge a rule-12 per-year solve chain into one multi-year bundle.

A per-year `replay_keeper --years <Y> --out-dir <same dir>` chain (CLAUDE.md
rule 12: a single 3-year PJM per-plant process peaks ~16 GB and OOMs, so each
year runs in a fresh process) leaves every *per-year* artifact intact —
``dispatch/<year>_P1.parquet``, ``floors/<year>_P1.npz`` and the
``hourly/{system,class_hourly}_<year>.parquet`` sidecars — but each invocation
OVERWRITES the bundle-level aggregates with its own single year:
``meta.json["years"]``, ``system.parquet`` and ``btm.parquet``. Scoring the
bundle as-is silently grades one year.

This restores the aggregates without re-solving:

* ``meta.json["years"]`` -> every year present in ``hourly/``.
* ``system.parquet`` <- concat of the per-year ``hourly/system_<year>.parquet``
  sidecars (a superset of the overwritten frame's columns).
* ``btm.parquet`` <- recomputed for every year by
  ``run_calibration_full._btm_frame``, which is a PURE function of committed
  inputs (EIA-923 class totals x measured host shares, never this solve's
  dispatch — see its docstring), so the rebuild is byte-identical to what a
  single 3-year process would have written.
* ``run_config.json``'s ``calibration_flags["years"]`` -> the same full span (the
  invocation echo the chain also leaves single-year; keeper-audit E3).

Then run ``run_calibration_full.py --rebuild-benchmark <bundle>`` (which reads
``meta["years"]``, hence the ordering) so the shared EIA-923/930/CAMPD
benchmark frames cover all years, and ``dashboard_add_run.py`` to build the
payload.

Usage:
    python scripts/probes/pjm119_merge_year_chain.py results/calibration/<bundle>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import pandas as pd  # noqa: E402

import run_calibration_full as rcf  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402


def years_present(bundle: Path) -> list[int]:
    """Years with a per-year system sidecar, ascending."""
    return sorted(
        int(p.stem.rsplit("_", 1)[1])
        for p in (bundle / "hourly").glob("system_*.parquet")
    )


def merge(bundle: Path) -> list[int]:
    """Restore meta years + system.parquet + btm.parquet for the whole chain."""
    meta_path = bundle / "meta.json"
    meta = json.loads(meta_path.read_text())
    years = years_present(bundle)
    if not years:
        raise SystemExit(f"{bundle}: no hourly/system_<year>.parquet sidecars")
    iso = meta["iso"]
    hours = int(meta.get("hours", 8760))

    # 1. system.parquet from the per-year sidecars.
    sys_df = pd.concat(
        [pd.read_parquet(bundle / "hourly" / f"system_{y}.parquet") for y in years],
        ignore_index=True,
    )
    sys_df.to_parquet(bundle / "system.parquet", index=False)

    # 2. btm.parquet — pure function of committed inputs, per year x pass.
    generation = rcf.load_monthly_generation()
    parasitic_factors = rcf._parasitic_factor_map()
    iso_config = get_iso_config(iso)
    passes = sorted(sys_df["pass"].unique().tolist())
    frames = []
    for y in years:
        campd_year = rcf._campd_hourly_frame(y, iso, parasitic_factors, hours)
        campd_active = None
        if campd_year is not None:
            by_plant = campd_year.groupby("plant_id")["net_mw"].sum()
            campd_active = set(by_plant[by_plant > 0.0].index.astype(int))
        group_by_code = rcf._fleet_group_by_code(iso, iso_config, y)
        for label in passes:
            frames.append(
                rcf._btm_frame(
                    y,
                    label,
                    generation,
                    campd_active=campd_active,
                    iso=iso,
                    group_by_code=group_by_code,
                )
            )
    if frames:
        pd.concat(frames, ignore_index=True).to_parquet(
            bundle / "btm.parquet", index=False
        )

    # 3. run_config.json's calibration_flags["years"] — the invocation echo the
    # chain also leaves showing only its LAST year. audit_keepers E3 warns on the
    # meta/flags mismatch, and legitimacy_diagnostics merges these flags, so a
    # stale echo can misread a merged chain as single-year. indent=2 and no
    # trailing newline match what the solver writes.
    rc_path = bundle / "run_config.json"
    if rc_path.exists():
        rc = json.loads(rc_path.read_text())
        flags = rc.get("calibration_flags")
        if isinstance(flags, dict) and sorted(flags.get("years") or []) != years:
            flags["years"] = years
            rc_path.write_text(json.dumps(rc, indent=2))

    # 4. meta years last — --rebuild-benchmark reads them. indent=2 matches
    # what the solver writes, so a re-merge never churns formatting.
    meta["years"] = years
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    return years


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle")
    args = ap.parse_args()
    bundle = Path(args.bundle)
    years = merge(bundle)
    sys_df = pd.read_parquet(bundle / "system.parquet")
    btm = pd.read_parquet(bundle / "btm.parquet")
    print(f"merged {bundle}: years={years}")
    print(
        f"  system.parquet  {len(sys_df):,} rows, years {sorted(sys_df.year.unique())}"
    )
    print(f"  btm.parquet     {len(btm):,} rows, years {sorted(btm.year.unique())}")
    print(
        "next: run_calibration_full.py --rebuild-benchmark <bundle>, then dashboard_add_run.py"
    )


if __name__ == "__main__":
    main()
