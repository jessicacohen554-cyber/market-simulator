#!/usr/bin/env python3
"""Compose nwpp-42's THREE per-year legs into ONE registrable NWPP span bundle.

Rule 36 ``[R-YEAR-ISOLATION]`` (owner ruling 2026-09-19, miso-262) solves every
backcast year in its OWN shard container, so this lane's arm and its control each
arrive as three single-year bundles. Composition is the parent's job (rule 32
``[R-SHARD]`` (d)) and is a zero-LP file operation.

This is the NWPP sibling of ``_miso260_compose_span.py``. It differs in its
recipe check, and the difference is deliberate: MISO's legs carry a DATA-FORCED
partition (a measured reserve parquet that starts in 2023), so that script
enumerates the fields that may differ. **NWPP has no partition** — one config
across all three years — so the check here is the stronger, generic one: every
``scenario_config`` field must agree across the legs EXCEPT the two the
single-year invocation necessarily carries per year,

``gas_price_override``
    verified against each leg's own ``calibration_flags.gas_prices`` map, so a
    genuinely wrong fuel price is still caught rather than waved through.

``weather_year``
    must equal the leg's own year.

Anything else that differs means the legs are not one run and the composite
would be a fiction, so the script aborts rather than composing it.

``legitimacy_diagnostics.json`` is REGENERATED over the composite, never copied
from a leg — copying one leg's silently sends C8 (a PROTECTIVE criterion) to
SKIPPED, which downgrades the determination and reads like a model regression.

Usage:
    python scripts/probes/_nwpp42_compose_span.py \
        --leg 2023=nwpp42_coalhr_2023 \
        --leg 2024=nwpp42_coalhr_2024 \
        --leg 2025=nwpp42_coalhr_2025 \
        --out results/calibration/nwpp42_coalhr_span
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

#: The only fields a single-year leg may legitimately differ on (module docstring).
YEAR_CARRIED = ("gas_price_override", "weather_year")


def _cfg(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text())


def check_recipes(legs: dict[str, list[int]]) -> None:
    """Abort unless the legs are one recipe differing only where the year forces it."""
    print("verifying the leg recipes (NWPP carries no partition — one config):")
    shared: dict[str, set[str]] = {}
    surfaces: set = set()
    for name, years in legs.items():
        if len(years) != 1:
            raise SystemExit(
                f"ABORT: {name} claims years {years}. Rule 36 solves one year per "
                "leg; a multi-year leg is a span solve and is not composable here."
            )
        (year,) = years
        cfg = _cfg(CAL / name)
        sc = cfg["scenario_config"]
        flags = cfg.get("calibration_flags", {})

        recorded = sorted(flags.get("years") or [])
        if recorded != [year]:
            raise SystemExit(f"ABORT: {name} records years {recorded}, claims [{year}]")

        want_gas = (flags.get("gas_prices") or {}).get(str(year))
        got_gas = sc.get("gas_price_override")
        if want_gas is None or got_gas != want_gas:
            raise SystemExit(
                f"ABORT: {name} has gas_price_override={got_gas!r} but its own "
                f"calibration_flags.gas_prices[{year}]={want_gas!r}."
            )
        if sc.get("weather_year") != year:
            raise SystemExit(
                f"ABORT: {name} has weather_year={sc.get('weather_year')!r}, not {year}"
            )

        surfaces.add((cfg.get("solve_surface") or {}).get("fingerprint"))
        for key, value in sc.items():
            if key in YEAR_CARRIED:
                continue
            shared.setdefault(key, set()).add(json.dumps(value, sort_keys=True))
        print(
            f"  {name:24s} year={year} gas={got_gas} "
            f"measured_coal_heat_rates={sc.get('measured_coal_heat_rates')} "
            f"surface={(cfg.get('solve_surface') or {}).get('fingerprint')}"
        )

    if len(surfaces) != 1:
        raise SystemExit(f"ABORT: legs disagree on the solve-surface fingerprint: {surfaces}")
    disagree = {k: sorted(v) for k, v in shared.items() if len(v) != 1}
    if disagree:
        for key, values in disagree.items():
            print(f"  DISAGREE {key}: {values}")
        raise SystemExit(
            f"ABORT: {len(disagree)} non-year-carried field(s) differ across the legs. "
            "NWPP has no declared partition, so these are not one run."
        )
    print(
        f"  OK — {len(shared)} shared fields agree, surface fingerprint shared, "
        f"{len(YEAR_CARRIED)} year-carried fields verified against each leg's own flags."
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
                raise SystemExit(f"ABORT: {path} has no `year` column")
            frames[fname].append(df)
        for y in years:
            shutil.copy2(src / "run_config.json", out / f"run_config_{y}.json")

    for fname, parts in frames.items():
        if parts:
            pd.concat(parts, ignore_index=True).to_parquet(out / fname, index=False)
            print(f"  {fname}: {len(parts)} leg(s) concatenated")

    all_years = sorted(set(all_years))
    base = next(iter(legs))
    # The composite's base run_config is the FIRST leg's, so its invocation echo
    # (calibration_flags.years / gas_prices) would describe one year and trip
    # audit_keepers E3. Widen the echo to the span; the per-year truth stays in
    # run_config_<y>.json and scenario_config is untouched.
    base_cfg = json.loads((CAL / base / "run_config.json").read_text())
    flags = base_cfg.setdefault("calibration_flags", {})
    flags["years"] = list(all_years)
    gas: dict[str, float] = {}
    for name in legs:
        leg_flags = _cfg(CAL / name).get("calibration_flags", {})
        gas.update(leg_flags.get("gas_prices") or {})
    if gas:
        flags["gas_prices"] = {k: gas[k] for k in sorted(gas)}
    (out / "run_config.json").write_text(json.dumps(base_cfg, indent=2) + "\n")
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
        "--bundle", str(out),
        "--iso", "NWPP",
        "--years", *[str(y) for y in years],
        "--json-out", str(out / "legitimacy_diagnostics.json"),
    ]
    print("\nregenerating legitimacy_diagnostics.json over the composite:")
    print("  " + " ".join(cmd))
    rc = subprocess.run(cmd, cwd=REPO).returncode
    art = out / "legitimacy_diagnostics.json"
    if not art.is_file():
        print(f"  NO ARTIFACT WRITTEN (exit {rc}) — C8 would score SKIPPED; do not register.")
        return 1
    if rc != 0:
        print(f"  (exit {rc} — a failing diagnostic gate, not a missing artifact)")
    got = sorted(json.loads(art.read_text()).get("years") or [])
    print(f"  years in the regenerated artifact: {got}")
    if got != sorted(years):
        print(f"  MISMATCH: expected {sorted(years)} — do not register.")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--leg", action="append", required=True,
                    help="YEAR=bundle_name, e.g. 2023=nwpp42_coalhr_2023")
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip-diagnostics", action="store_true")
    args = ap.parse_args()

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
