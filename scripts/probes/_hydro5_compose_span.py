#!/usr/bin/env python3
"""Compose hydro-5's per-year arm legs into registrable keeper-shaped span bundles.

Rule 36 ``[R-YEAR-ISOLATION]`` solved every year in its own shard; composition is
the parent's zero-LP job (rule 32 ``[R-SHARD]`` (d)). The mechanical half is
``_nwpp42_compose_span.py``'s, unchanged and deliberately not re-derived:
bundle-root frames concatenate, year-stamped files copy, the base
``run_config.json`` echo is widened to the span, ``meta.json`` ``gas_prices`` and
the year-dependent ``shared_inputs`` frames are re-spanned (the stale-benchmark
fix of 39c79724), and ``legitimacy_diagnostics.json`` is REGENERATED over the
composite rather than copied from a leg.

**The recipe check is the stronger one this lane can make**: every leg must be
its keeper's OWN per-year recipe plus exactly ``<flag>: False -> True`` — the
same comparison ``_hydro5_shard_check.py`` ran on each shard, repeated here so
a control leg or a wrong-arm leg can never compose in. Fields added to
``ScenarioConfig`` after the keeper solved are allowed only at their default.
Legs must also share one solve-surface fingerprint.

For a keeper that carries a per-year recipe partition (MISO), the composite's
``config_partition_overrides`` is then DERIVED from its own per-year
``run_config_<y>.json`` by ``scripts/stamp_config_partition.py`` — never copied
by hand — so a replay of the composite reproduces each year's own recipe.

Usage::

    python scripts/probes/_hydro5_compose_span.py --iso NEISO \\
        --flag hydro_ror_split --keeper neiso112_mer_span \\
        --leg 2020=hydro5_neiso_ror_2020 ... --out results/calibration/hydro5_neiso_ror_span
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)
CAL = REPO / "results" / "calibration"

ROOT_FRAMES = ("system.parquet", "btm.parquet", "flows.parquet", "storage.parquet")


def _cfg(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text())


def _keeper_sc(keeper: Path, year: int) -> dict:
    per = keeper / f"run_config_{year}.json"
    rc = per if per.exists() else keeper / "run_config.json"
    return json.loads(rc.read_text())["scenario_config"]


def check_recipes(legs: dict[str, list[int]], keeper: Path, flag: str) -> None:
    """Abort unless every leg is its keeper's year recipe plus exactly ``flag``."""
    from market_sim.config.scenarios import ScenarioConfig

    defaults = {
        f.name: f.default
        for f in dataclasses.fields(ScenarioConfig)
        if f.default is not dataclasses.MISSING
    }
    print(f"verifying {len(legs)} leg(s) against keeper {keeper.name}, arm {flag}:")
    surfaces: set = set()
    for name, years in legs.items():
        if len(years) != 1:
            raise SystemExit(
                f"ABORT: {name} claims {years}; rule 36 legs are single-year"
            )
        (year,) = years
        cfg = _cfg(CAL / name)
        a, k = cfg["scenario_config"], _keeper_sc(keeper, year)
        diff = {x: (k[x], a[x]) for x in set(a) & set(k) if a[x] != k[x]}
        bad_new = {
            x: a[x]
            for x in set(a) - set(k)
            if x in defaults
            and json.dumps(a[x]) != json.dumps(defaults[x], default=str)
        }
        if diff != {flag: (False, True)} or bad_new:
            raise SystemExit(
                f"ABORT: {name} is not keeper+{flag}: diff={diff} non-default new={bad_new}"
            )
        recorded = sorted(cfg.get("calibration_flags", {}).get("years") or [])
        if recorded != [year]:
            raise SystemExit(f"ABORT: {name} records years {recorded}, claims [{year}]")
        surfaces.add((cfg.get("solve_surface") or {}).get("fingerprint"))
        print(f"  {name:26s} year={year} diff={diff}")
    if len(surfaces) != 1:
        raise SystemExit(
            f"ABORT: legs disagree on the solve-surface fingerprint: {surfaces}"
        )
    print("  OK — every leg is keeper + exactly one flag; surface fingerprint shared.")


def compose(legs: dict[str, list[int]], out: Path) -> None:
    """Copy / concatenate the legs into ``out`` (see module docstring)."""
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
                continue
            df = pd.read_parquet(path)
            if "year" not in df.columns:
                df = df.assign(year=years[0])
            frames[fname].append(df)
        for y in years:
            shutil.copy2(src / "run_config.json", out / f"run_config_{y}.json")
    for fname, parts in frames.items():
        if parts:
            pd.concat(parts, ignore_index=True).to_parquet(out / fname, index=False)
            print(f"  {fname}: {len(parts)} leg(s) concatenated")

    all_years = sorted(set(all_years))
    base = min(legs, key=lambda n: min(legs[n]))
    base_cfg = _cfg(CAL / base)
    flags = base_cfg.setdefault("calibration_flags", {})
    flags["years"] = list(all_years)
    gas: dict[str, float] = {}
    for name in legs:
        gas.update(
            _cfg(CAL / name).get("calibration_flags", {}).get("gas_prices") or {}
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
    print(f"composed {out.relative_to(REPO)} — {n} files, years {all_years}")


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


def stamp_partition(out: Path, years: list[int]) -> None:
    """Derive ``config_partition_overrides`` from the composite's own legs."""
    cmd = [
        sys.executable,
        str(REPO / "scripts" / "stamp_config_partition.py"),
        str(out),
    ]
    for y in years:
        cmd += ["--leg", f"{y}=run_config_{y}.json"]
    print("stamping the per-year recipe partition:\n  " + " ".join(cmd[1:]))
    rc = subprocess.run(cmd, cwd=REPO).returncode
    if rc:
        raise SystemExit(f"stamp_config_partition failed ({rc})")


def regenerate_diagnostics(out: Path, iso: str, years: list[int]) -> int:
    """Rebuild ``legitimacy_diagnostics.json`` over the WHOLE composite (zero LP)."""
    cmd = [
        sys.executable,
        str(REPO / "scripts" / "legitimacy_diagnostics.py"),
        "--bundle", str(out), "--iso", iso,
        "--years", *[str(y) for y in years],
        "--json-out", str(out / "legitimacy_diagnostics.json"),
    ]  # fmt: skip
    rc = subprocess.run(cmd, cwd=REPO).returncode
    art = out / "legitimacy_diagnostics.json"
    if not art.is_file():
        print(f"NO legitimacy_diagnostics.json (exit {rc}) — do not register")
        return 1
    got = sorted(json.loads(art.read_text()).get("years") or [])
    if got != sorted(years):
        print(
            f"legitimacy_diagnostics years {got} != {sorted(years)} — do not register"
        )
        return 1
    print(f"legitimacy_diagnostics.json regenerated over {got} (exit {rc})")
    return 0


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--iso", required=True)
    ap.add_argument("--flag", required=True)
    ap.add_argument("--keeper", required=True, help="keeper bundle dir name")
    ap.add_argument("--leg", action="append", required=True, help="YEAR=bundle_name")
    ap.add_argument("--out", required=True)
    ap.add_argument("--stamp-partition", action="store_true")
    args = ap.parse_args()
    legs: dict[str, list[int]] = {}
    for spec in args.leg:
        ys, _, name = spec.partition("=")
        legs[name] = sorted(int(y) for y in ys.split(","))
    out = Path(args.out)
    out = out if out.is_absolute() else REPO / out
    check_recipes(legs, CAL / args.keeper, args.flag)
    compose(legs, out)
    years = sorted({y for ys in legs.values() for y in ys})
    if args.stamp_partition:
        stamp_partition(out, years)
    return regenerate_diagnostics(out, args.iso, years)


if __name__ == "__main__":
    raise SystemExit(main())
