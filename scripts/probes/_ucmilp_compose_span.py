#!/usr/bin/env python3
"""Compose per-year UC-2 shard legs into ONE registrable span bundle (any ISO).

The ISO-parameterized form of ``scripts/probes/_miso260_compose_span.py`` with
no data-forced partition: every leg is one year solved alone in its own shard
(rule 36 [R-YEAR-ISOLATION]) from the SAME recipe, so every recorded field
must agree across the legs (the only allowed per-year differences are the
fields the keeper itself records per year, ``config_partition`` aside).

What it adds for the MILP UC stage (``unit_commitment_milp``): each leg's
stage sidecars — ``hourly/uc_schedule_<y>.parquet``, ``hourly/uc_uplift_<y>.parquet``
and the bundle-root ``uc_solve_log_<y>.json`` the orchestrator's drain
writes — ride along (the hourly files with every other year-stamped sidecar,
the log copied explicitly); a leg that lacks the make-whole frame gets it
computed from the composite's own committed per-unit layer
(:func:`market_sim.model.uc.uplift.uplift_from_bundle`, zero LP). A leg whose
recipe arms the gate but carries no schedule is an ABORT: the schedule is the
evidence the A/B is scored against.

The composition itself is mechanical and lossless (per-year files copy,
bundle-root frames concatenate, ``run_config_<y>.json`` kept per year) and
``legitimacy_diagnostics.json`` is REGENERATED over the composite, never
copied from a leg (the C8-SKIPPED trap the MISO composer documents).

Usage:
    python scripts/probes/_ucmilp_compose_span.py --iso NEISO \\
        --leg 2023=ucmilp_neiso_2023 --leg 2024=ucmilp_neiso_2024 \\
        --out results/calibration/ucmilp_neiso_span
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
sys.path.insert(0, str(REPO / "src"))
CAL = REPO / "results" / "calibration"

ROOT_FRAMES = ("system.parquet", "btm.parquet", "flows.parquet", "storage.parquet")

#: Per-year fields a keeper records per year by design; everything else in
#: ``scenario_config`` must agree across the legs.
PER_YEAR_FIELDS = frozenset(
    {
        "weather_year",
        "start_year",
        "end_year",
        "gas_price",
        "gas_offer_margin_anchor",
        "hindcast_year",
    }
)


def _leg_config(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text())


def check_recipes(legs: dict[str, int], iso: str) -> bool:
    """Verify the legs are one recipe; return whether the UC gate is armed."""
    print("verifying the leg recipes:")
    seen: dict[str, set] = {}
    armed: set[bool] = set()
    for name, year in legs.items():
        cfg = _leg_config(CAL / name)
        sc = cfg["scenario_config"]
        if str(sc.get("iso", "")).upper() != iso.upper():
            raise SystemExit(f"ABORT: {name} is {sc.get('iso')!r}, not {iso}")
        armed.add(bool(sc.get("unit_commitment_milp", False)))
        for k, v in sc.items():
            if k in PER_YEAR_FIELDS:
                continue
            seen.setdefault(k, set()).add(json.dumps(v, sort_keys=True, default=str))
        recorded = sorted(cfg.get("calibration_flags", {}).get("years") or [])
        if recorded and recorded != [year]:
            raise SystemExit(
                f"ABORT: {name} records years {recorded}, the leg claims {year}"
            )
        print(
            f"  {name:28s} year={year} uc={sc.get('unit_commitment_milp')} "
            f"surface={(cfg.get('solve_surface') or {}).get('fingerprint')}"
        )
    bad = {k: v for k, v in seen.items() if len(v) != 1}
    if bad:
        for k, v in sorted(bad.items()):
            print(f"  DISAGREE {k}: {sorted(v)}")
        raise SystemExit(
            "ABORT: the legs disagree on fields outside the per-year set; not one run."
        )
    if len(armed) != 1:
        raise SystemExit("ABORT: the legs disagree on unit_commitment_milp.")
    gate = next(iter(armed))
    print(f"  OK — {len(seen)} shared fields agree; unit_commitment_milp={gate}")
    return gate


def _leg_has_uc_artifacts(leg: Path, year: int) -> bool:
    """Whether a leg carries the stage's bundle sidecars (hourly/uc_schedule + root log)."""
    return (leg / "hourly" / f"uc_schedule_{year}.parquet").is_file() and (
        leg / f"uc_solve_log_{year}.json"
    ).is_file()


def compose(legs: dict[str, int], iso: str, out: Path) -> None:
    """Copy / concatenate the legs into ``out`` and fold the UC artifacts."""
    armed = check_recipes(legs, iso)
    if out.exists():
        shutil.rmtree(out)
    for sub in ("dispatch", "floors", "hourly"):
        (out / sub).mkdir(parents=True)
    frames: dict[str, list[pd.DataFrame]] = {n: [] for n in ROOT_FRAMES}
    years: list[int] = []
    for name, year in legs.items():
        src = CAL / name
        years.append(year)
        for sub in ("dispatch", "floors", "hourly"):
            if not (src / sub).is_dir():
                continue
            for path in sorted((src / sub).glob("*")):
                if str(year) not in path.name:
                    raise SystemExit(f"ABORT: {path} does not carry year {year}")
                shutil.copy2(path, out / sub / path.name)
        for fname in ROOT_FRAMES:
            path = src / fname
            if not path.is_file():
                print(f"  {name}: {fname} absent, skipped")
                continue
            df = pd.read_parquet(path)
            if "year" not in df.columns:
                df = df.assign(year=year)
            frames[fname].append(df)
        per = src / f"run_config_{year}.json"
        shutil.copy2(
            per if per.is_file() else src / "run_config.json",
            out / f"run_config_{year}.json",
        )
        if armed:
            if not _leg_has_uc_artifacts(src, year):
                raise SystemExit(
                    f"ABORT: {name} arms unit_commitment_milp but carries no "
                    f"hourly/uc_schedule_{year}.parquet + uc_solve_log_{year}.json "
                    "(the orchestrator's drain writes both into the bundle)"
                )
            shutil.copy2(
                src / f"uc_solve_log_{year}.json", out / f"uc_solve_log_{year}.json"
            )
            print(
                f"  {name}: UC artifacts present (schedule copied with hourly/, log copied)"
            )
    for fname, parts in frames.items():
        if parts:
            pd.concat(parts, ignore_index=True).to_parquet(out / fname, index=False)
            print(f"  {fname}: {len(parts)} leg(s) concatenated")
    years = sorted(years)
    base = next(iter(legs))
    shutil.copy2(CAL / base / "run_config.json", out / "run_config.json")
    meta = json.loads((CAL / base / "meta.json").read_text())
    meta["years"] = years
    meta["composed_from"] = {n: [y] for n, y in legs.items()}
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    if armed:
        write_uplift(out, years)
    n = sum(1 for p in out.rglob("*") if p.is_file())
    print(f"\ncomposed {out} — {n} files, years {years}")


def write_uplift(out: Path, years: list[int]) -> None:
    """``hourly/uc_uplift_<y>.parquet`` from the composite's own sidecars (zero LP)."""
    from market_sim.model.uc.uplift import uplift_from_bundle

    for y in years:
        um = out / "hourly" / f"unit_marginal_{y}.parquet"
        if (out / "hourly" / f"uc_uplift_{y}.parquet").is_file():
            print(f"  uplift {y}: carried by the leg")
            continue
        if not um.is_file() or not (out / f"uc_solve_log_{y}.json").is_file():
            print(f"  uplift {y}: unit_marginal or uc_solve_log absent — not written")
            continue
        frame = uplift_from_bundle(str(out), str(out), y)
        frame.to_parquet(out / "hourly" / f"uc_uplift_{y}.parquet", index=False)
        print(
            f"  uplift {y}: {len(frame)} cluster-days, total ${frame['uplift_usd'].sum():,.0f}"
        )


def regenerate_diagnostics(out: Path, iso: str, years: list[int]) -> int:
    """Rebuild ``legitimacy_diagnostics.json`` over the WHOLE composite (zero LP)."""
    cmd = [
        sys.executable,
        str(REPO / "scripts" / "legitimacy_diagnostics.py"),
        "--bundle",
        str(out),
        "--iso",
        iso,
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
    got = sorted(json.loads(art.read_text()).get("years") or [])
    print(f"  years in the regenerated artifact: {got}")
    if got != sorted(years):
        print(f"  MISMATCH: expected {sorted(years)} — do not register.")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--iso", required=True)
    ap.add_argument(
        "--leg", action="append", required=True, help="YEAR=bundle_name, one per shard"
    )
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--uc-root", default=None, help="UC artifact root (default results/uc)"
    )
    ap.add_argument("--skip-diagnostics", action="store_true")
    args = ap.parse_args(argv)
    legs: dict[str, int] = {}
    for spec in args.leg:
        y, _, name = spec.partition("=")
        legs[name] = int(y)
    out = Path(args.out)
    if not out.is_absolute():
        out = REPO / out
    compose(legs, args.iso, out)
    if args.skip_diagnostics:
        return 0
    return regenerate_diagnostics(out, args.iso, sorted(legs.values()))


if __name__ == "__main__":
    raise SystemExit(main())
