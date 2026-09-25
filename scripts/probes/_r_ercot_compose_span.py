#!/usr/bin/env python3
"""Compose R-ERCOT's per-year legs (ARM or CONTROL) into one ERCOT span bundle.

Rule 36 ``[R-YEAR-ISOLATION]``: every year solved in its own shard; the parent
composes at zero LP. The mechanical half is ``_spp78_compose_span.py``'s
verbatim (bundle-root frames concatenate, year-stamped files copy,
``legitimacy_diagnostics.json`` REGENERATED over the composite). What is
ERCOT's own:

* the base ``run_config.json`` / ``meta.json`` come from the FORWARD leg (2024),
  as in the incumbent keeper — the carve-out legs are per-year overlays that
  ``scripts/stamp_config_partition.py`` derives and stamps afterwards;
* the SIGNATURE: every leg must carry the eight R-ERCOT flags (True on ``arm``,
  False on ``control``) and its own partition signature (PRECOMMIT §6).

Usage:
    python scripts/probes/_r_ercot_compose_span.py --side arm \
        --leg 2019=r_ercot_arm_2019 ... --leg 2025=r_ercot_arm_2025 \
        --out results/calibration/r_ercot_arm_span
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
CAL = REPO / "results" / "calibration"

ROOT_FRAMES = ("system.parquet", "btm.parquet", "flows.parquet", "storage.parquet")

#: The eight R-ERCOT flags (PRECOMMIT §3).
FIELDS = (
    "eia860_vintage_tracks_solve_year",
    "measured_ct_heat_rates",
    "measured_coal_heat_rates",
    "measured_st_heat_rates",
    "measured_cc_heat_rates",
    "measured_chp_heat_rates",
    "unit_outage_short_windows",
    "unit_outage_short_windows_gas",
)
#: Fields every year must agree on (the recipe's shared spine).
MUST_AGREE = (
    "mode",
    "use_campd_bins",
    "ercot_ep_gas_basis_receipts_fallback",
    "ercot_noncampd_plant_availability",
    "ercot_thermal_dam_availability",
    "ercot_partial_outage_shaped_derate",
    "outage_source",
) + FIELDS


def _partition_signature(year: int) -> tuple:
    """(swcap_clip, zonal_spread_ep_referenced, CC_REGULAR.peak, CT_PEAKER.peak)."""
    if year <= 2022:
        return (True, True, 151.008, 433.95)
    if year == 2023:
        return (True, False, 151.008, 433.95)
    return (False, True, 4.576, 13.15)


SIDE: dict = {}


def _leg_config(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text())


def check_recipes(legs: dict[str, list[int]]) -> None:
    """Verify every leg is the requested side, on its own partition signature."""
    print(f"verifying {len(legs)} leg recipe(s):")
    agree: dict[str, set] = {k: set() for k in MUST_AGREE}
    for name, years in legs.items():
        sc = _leg_config(CAL / name)["scenario_config"]
        for f in FIELDS:
            want_f = SIDE["value"] and not (
                SIDE.get("chp_off") and f == "measured_chp_heat_rates"
            )
            if bool(sc.get(f)) != want_f:
                raise SystemExit(
                    f"ABORT: {name} {f}={sc.get(f)!r} — not the {SIDE['name']} side"
                )
        ocg = sc.get("offer_curve_by_group") or {}
        got = (
            bool(sc.get("ercot_offer_swcap_clip")),
            bool(sc.get("ercot_zonal_spread_ep_referenced")),
            float(ocg.get("CC_REGULAR", {}).get("peak", float("nan"))),
            float(ocg.get("CT_PEAKER", {}).get("peak", float("nan"))),
        )
        want = _partition_signature(years[0])
        if got != want:
            raise SystemExit(f"ABORT: {name} partition signature {got} != {want}")
        for k in MUST_AGREE:
            agree[k].add(json.dumps(sc.get(k)))
        recorded = sorted(
            _leg_config(CAL / name).get("calibration_flags", {}).get("years") or []
        )
        if recorded and recorded != sorted(years):
            raise SystemExit(
                f"ABORT: {name} records years {recorded}, leg claims {years}"
            )
        print(f"  {name:22s} years={years} sig={got}")
    for key, values in agree.items():
        if len(values) != 1:
            raise SystemExit(f"ABORT: legs disagree on {key!r}: {sorted(values)}")
    print(
        f"  OK — {SIDE['name']} signature on every leg; {len(MUST_AGREE)} shared fields agree."
    )


def compose(legs: dict[str, list[int]], out: Path) -> None:
    check_recipes(legs)
    if out.exists():
        shutil.rmtree(out)
    for sub in ("dispatch", "floors", "hourly"):
        (out / sub).mkdir(parents=True)

    frames: dict[str, list[pd.DataFrame]] = {n: [] for n in ROOT_FRAMES}
    all_years: list[int] = []
    for name, years in legs.items():
        src = CAL / name
        all_years.extend(years)
        for sub in ("dispatch", "floors", "hourly"):
            if not (src / sub).is_dir():
                continue
            for path in sorted((src / sub).glob("*")):
                if not any(str(y) in path.name for y in years):
                    raise SystemExit(f"ABORT: {path} carries no year of {years}")
                shutil.copy2(path, out / sub / path.name)
        for fname in ROOT_FRAMES:
            path = src / fname
            if not path.is_file():
                print(f"  {name}: {fname} absent, skipped")
                continue
            df = pd.read_parquet(path)
            if "year" not in df.columns:
                if len(years) != 1:
                    raise SystemExit(
                        f"ABORT: {path} has no `year` column and the leg spans "
                        f"{years} — the year cannot be inferred."
                    )
                df = df.assign(year=years[0])
            frames[fname].append(df)
        wrote_any = False
        for y in years:
            per = src / f"run_config_{y}.json"
            if per.is_file():
                shutil.copy2(per, out / f"run_config_{y}.json")
                wrote_any = True
        if not wrote_any:
            for y in years:
                shutil.copy2(src / "run_config.json", out / f"run_config_{y}.json")

    for fname, parts in frames.items():
        if parts:
            pd.concat(parts, ignore_index=True).to_parquet(out / fname, index=False)
            print(f"  {fname}: {len(parts)} leg(s) concatenated")

    # Span widening, gas re-span and shared-input re-span: ported verbatim from
    # _hydro5_compose_span.py (the keeper's own composer; the nwpp-42 stale-benchmark fix).
    all_years = sorted(set(all_years))
    # ERCOT: the FORWARD leg is the base recipe (meta.json records the forward
    # config; the carve-out legs are overlays stamped by stamp_config_partition).
    base = max(legs, key=lambda n: min(legs[n]))
    base_cfg = _leg_config(CAL / base)
    flags = base_cfg.setdefault("calibration_flags", {})
    flags["years"] = list(all_years)
    gas: dict[str, float] = {}
    for name in legs:
        gas.update(
            _leg_config(CAL / name).get("calibration_flags", {}).get("gas_prices") or {}
        )
    if gas:
        flags["gas_prices"] = {k: gas[k] for k in sorted(gas)}
    (out / "run_config.json").write_text(json.dumps(base_cfg, indent=2) + "\n")
    meta = json.loads((CAL / base / "meta.json").read_text())
    meta["years"] = all_years
    meta["composed_from"] = {n: sorted(y) for n, y in legs.items()}
    if gas:
        meta["gas_prices"] = {k: gas[k] for k in sorted(gas)}
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    _respan_shared_inputs(meta, out)
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    n = sum(1 for p in out.rglob("*") if p.is_file())
    print(f"\ncomposed {out} — {n} files, years {all_years}")


def _respan_shared_inputs(meta: dict, out: Path) -> None:
    """Re-point the year-dependent benchmark frames at the span (nwpp-42 fix)."""
    recorded = meta.get("shared_inputs")
    if not recorded:
        return
    from scripts.lib.bundle_io import SHARED_INPUT_NAMES
    from scripts.run_calibration_full import build_benchmark_frames, write_shared_input

    stale = [n for n in SHARED_INPUT_NAMES if n in recorded]
    if not stale:
        return
    iso, built = build_benchmark_frames(out)
    for name in sorted(stale):
        if name not in built:
            raise SystemExit(f"compose: span rebuild produced no {name!r} frame")
        was = recorded[name]
        recorded[name] = write_shared_input(built[name], name, iso, out)
        print(f"  shared {name:<7} {Path(was).name} -> {Path(recorded[name]).name}")
    meta["shared_inputs"] = recorded


def regenerate_diagnostics(out: Path, years: list[int]) -> int:
    """Rebuild ``legitimacy_diagnostics.json`` over the WHOLE composite (zero LP)."""
    cmd = [
        sys.executable,
        str(REPO / "scripts" / "legitimacy_diagnostics.py"),
        "--bundle",
        str(out),
        "--iso",
        "ERCOT",
        "--years",
        *[str(y) for y in years],
        "--json-out",
        str(out / "legitimacy_diagnostics.json"),
    ]
    print("\nregenerating legitimacy_diagnostics.json over the composite:")
    print("  " + " ".join(cmd))
    rc = subprocess.run(cmd, cwd=REPO).returncode
    art = out / "legitimacy_diagnostics.json"
    if not art.is_file():
        print(
            f"  NO ARTIFACT WRITTEN (exit {rc}) — C8 would score SKIPPED; do not register."
        )
        return 1
    if rc != 0:
        print(f"  (exit {rc} — a failing diagnostic gate, not a missing artifact)")
    d = json.loads(art.read_text())
    got = sorted(d.get("years") or [])
    print(f"  years in the regenerated artifact: {got}")
    if got != sorted(years):
        print(f"  MISMATCH: expected {sorted(years)} — do not register.")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--leg", action="append", required=True, help="YEARS=bundle_name")
    ap.add_argument("--out", required=True)
    ap.add_argument("--side", choices=("arm", "control"), required=True)
    ap.add_argument("--skip-diagnostics", action="store_true")
    ap.add_argument(
        "--chp-off",
        action="store_true",
        help="R-ERCOT-2: the arm side with measured_chp_heat_rates=False on every leg",
    )
    args = ap.parse_args()
    SIDE.update(name=args.side, value=args.side == "arm", chp_off=args.chp_off)
    legs: dict[str, list[int]] = {}
    for spec in args.leg:
        ys, _, name = spec.partition("=")
        legs[name] = sorted(int(y) for y in ys.split(","))
    out = Path(args.out)
    if not out.is_absolute():
        out = REPO / out
    compose(legs, out)
    if args.skip_diagnostics:
        return 0
    return regenerate_diagnostics(out, sorted({y for ys in legs.values() for y in ys}))


if __name__ == "__main__":
    raise SystemExit(main())
