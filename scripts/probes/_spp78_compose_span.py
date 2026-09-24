#!/usr/bin/env python3
"""Compose SPP-78's per-year legs (control OR measured-HR arm) into SPP span/rung bundles.

Rule 36 ``[R-YEAR-ISOLATION]``: every backcast year was solved in its OWN shard; the
PARENT composes at zero LP. ADAPTED FROM ``_spp71_compose_span.py`` — the mechanical
half is unchanged (bundle-root frames concatenate, year-stamped files copy,
``legitimacy_diagnostics.json`` is REGENERATED over the composite).

**What differs is the signature.** ``--side arm`` requires the three SPP-78 fields
(``measured_{cc,st,coal}_heat_rates``) True on every leg; ``--side control`` requires
all three False — so a control leg can never be composed into an arm bundle or vice
versa. ``spp_curtailment_ceiling`` stays in ``MUST_AGREE`` (keeper 14's posture: False).

SPP's two sides are composed SEPARATELY (``mid_vintage_exit_carry`` is True on the rung,
False on the keeper span), exactly as SPP-51/71 did.

Usage:
    python scripts/probes/_spp78_compose_span.py --side arm \
        --leg 2023=spp78_hr_2023 --leg 2024=spp78_hr_2024 --leg 2025=spp78_hr_2025 \
        --out results/calibration/spp78_hr_span
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

#: Fields every year of a composite must agree on. A disagreement means the legs
#: are not one run and the composite would be a fiction. Includes BOTH gates this
#: lane armed, so a leg that silently solved the control can never be composed in.
MUST_AGREE = (
    "mode",
    "use_campd_bins",
    "coal_mustrun_online_pmin",
    "coal_sync_srmc_tranche",
    "vre_curtailment_oversupply_allocation",
    "mid_vintage_exit_carry",
    "benchmark_membership_vintage_union",
    "coal_mustrun_per_plant",
    "ira_ptc_wind",
    "spp_curtailment_ceiling",
    "spp_curtail_depth_wind",
    "vre_reference_rate_year_own",
    "coal_sync_ensemble_level",
    "measured_cc_heat_rates",
    "measured_st_heat_rates",
    "measured_coal_heat_rates",
)

FIELDS = ("measured_cc_heat_rates", "measured_st_heat_rates", "measured_coal_heat_rates")

#: Keeper 14 / hydro-5 recipe asserted so a leg built off the wrong base cannot compose.
BASE_REQUIRED = {
    "coal_sync_ensemble_level": True,
    "coal_mustrun_online_pmin": True,
    "coal_sync_srmc_tranche": True,
    "vre_reference_rate_year_own": True,
}
REQUIRED: dict = {}


def _leg_config(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text())


def check_recipes(legs: dict[str, list[int]]) -> None:
    """Verify every leg is the ARM and that the legs agree where they must."""
    print(f"verifying {len(legs)} leg recipe(s):")
    agree: dict[str, set] = {k: set() for k in MUST_AGREE}
    agree["_surface"] = set()  # measured-HR artifacts are not SURFACE_MODULES; sha checked by the shard
    for name, years in legs.items():
        cfg = _leg_config(CAL / name)
        sc = cfg["scenario_config"]
        for field, want in REQUIRED.items():
            got = sc.get(field)
            if got != want:
                raise SystemExit(
                    f"ABORT: {name} has {field}={got!r}, expected {want!r}. "
                    "This leg is not the requested side — refusing to compose it."
                )
        for k in MUST_AGREE:
            agree[k].add(json.dumps(sc.get(k)))
        agree["_surface"].add((cfg.get("solve_surface") or {}).get("fingerprint"))
        print(
            f"  {name:24s} years={years} "
            f"hr={[sc.get(f) for f in FIELDS]} gas={sc.get('gas_price_override')} "
            f"wy={sc.get('weather_year')} "
            f"midvint={sc.get('mid_vintage_exit_carry')} mode={sc.get('mode')}"
        )
        recorded = sorted(cfg.get("calibration_flags", {}).get("years") or [])
        if recorded and recorded != sorted(years):
            raise SystemExit(
                f"ABORT: {name} records years {recorded}, the leg claims {sorted(years)}"
            )
    for key, values in agree.items():
        if len(values) != 1:
            raise SystemExit(
                f"ABORT: the legs disagree on {key!r}: {sorted(map(str, values))}. "
                "Every year of one composite must carry one config — compose the "
                "keeper side and the rung side separately."
            )
    print(
        f"  OK — arm signature present on every leg; {len(MUST_AGREE)} shared "
        "fields agree; surface fingerprint shared."
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

    all_years = sorted(set(all_years))
    base = min(legs, key=lambda n: min(legs[n]))
    shutil.copy2(CAL / base / "run_config.json", out / "run_config.json")
    meta = json.loads((CAL / base / "meta.json").read_text())
    meta["years"] = all_years
    meta["composed_from"] = {n: sorted(y) for n, y in legs.items()}
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    n = sum(1 for p in out.rglob("*") if p.is_file())
    print(f"\ncomposed {out} — {n} files, years {all_years}")


def regenerate_diagnostics(out: Path, years: list[int]) -> int:
    """Rebuild ``legitimacy_diagnostics.json`` over the WHOLE composite (zero LP)."""
    cmd = [
        sys.executable,
        str(REPO / "scripts" / "legitimacy_diagnostics.py"),
        "--bundle",
        str(out),
        "--iso",
        "SPP",
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
    ap.add_argument(
        "--leg",
        action="append",
        required=True,
        help="YEARS=bundle_name, e.g. 2023=spp51_arm_2023",
    )
    ap.add_argument("--out", required=True)
    ap.add_argument("--side", choices=("arm", "control"), required=True)
    ap.add_argument("--skip-diagnostics", action="store_true")
    args = ap.parse_args()

    REQUIRED.clear()
    REQUIRED.update(BASE_REQUIRED)
    REQUIRED.update({f: args.side == "arm" for f in FIELDS})
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
