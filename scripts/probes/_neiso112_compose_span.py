#!/usr/bin/env python3
"""Compose neiso-112's SIX YEAR-ISOLATED LEGS into ONE registrable NEISO span bundle.

Under CLAUDE.md rule 36 ``[R-YEAR-ISOLATION]`` a backcast year is solved alone,
in its own shard container, so a registrable NEISO run arrives as six per-year
bundles that the parent composes at ZERO LP (rule 32 ``[R-SHARD]`` (d)).

**NEISO has no partition, and that is the difference from the MISO analogue**
(``_miso260_compose_span.py``, whose ``PARTITIONED`` table encodes a data-forced
split at 2023). Every leg here was replayed from the SAME keeper ``meta.json``
through ``replay_keeper.py``, so the check is stronger and simpler: the legs'
``scenario_config`` blocks must be identical in EVERY field except the two that
are year-scoped by construction. Measured at composition time: 856 fields, of
which exactly ``gas_price_override`` and ``weather_year`` differ. Anything else
differing means the legs are not one run and the composite would be a fiction,
so this refuses to write one.

The composition itself is mechanical and lossless, on the MISO script's model:

* per-year files COPY (``dispatch/<y>_P1*.parquet``, ``floors/<y>_P1.npz``,
  ``hourly/*_<y>.parquet`` — all already year-stamped);
* bundle-root frames CONCATENATE (``system`` / ``btm`` / ``flows`` / ``storage``);
* each leg's ``run_config.json`` is kept as ``run_config_<y>.json``;
* **``legitimacy_diagnostics.json`` is REGENERATED over the composite**, never
  copied from a leg — copying one leg's is the trap that silently sends C8 to
  SKIPPED, an unscored PROTECTIVE criterion that downgrades the determination
  and reads exactly like a model regression.

Usage:
    python scripts/probes/_neiso112_compose_span.py \
        --leg 2020=neiso112_mer_2020 ... \
        --out results/calibration/neiso112_mer_span
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

#: The ONLY ``scenario_config`` fields allowed to differ between legs. Both are
#: year-scoped by construction: a backcast year carries its own weather year and
#: its own delivered gas price. Every other field must be byte-equal.
YEAR_SCOPED = ("gas_price_override", "weather_year")


def _leg_config(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text())


def check_recipes(legs: dict[str, list[int]]) -> None:
    """Verify every leg is the same recipe outside the year-scoped fields."""
    print(f"verifying {len(legs)} leg recipes (expect ONE recipe, no partition):")
    base_name = next(iter(legs))
    base = _leg_config(CAL / base_name)["scenario_config"]
    surfaces: set = set()
    for name, years in legs.items():
        cfg = _leg_config(CAL / name)
        sc = cfg["scenario_config"]
        surfaces.add((cfg.get("solve_surface") or {}).get("fingerprint"))
        offenders = [
            k
            for k in set(base) | set(sc)
            if k not in YEAR_SCOPED
            and json.dumps(base.get(k), sort_keys=True)
            != json.dumps(sc.get(k), sort_keys=True)
        ]
        if offenders:
            raise SystemExit(
                f"ABORT: {name} differs from {base_name} in {len(offenders)} "
                f"non-year-scoped field(s): {sorted(offenders)[:12]}. These legs "
                "are not one run."
            )
        recorded = sorted(cfg.get("calibration_flags", {}).get("years") or [])
        if recorded and recorded != sorted(years):
            raise SystemExit(
                f"ABORT: {name} records years {recorded}, the leg claims {sorted(years)}"
            )
        print(
            f"  {name:24s} years={years} "
            f"gas={sc.get('gas_price_override')} wy={sc.get('weather_year')} "
            f"surface={(cfg.get('solve_surface') or {}).get('fingerprint')}"
        )
    if len(surfaces) != 1:
        raise SystemExit(f"ABORT: legs disagree on the solve surface: {sorted(surfaces)}")
    print(
        f"  OK — {len(base)} scenario_config fields, only {list(YEAR_SCOPED)} vary, "
        f"one shared surface fingerprint {surfaces.pop()}."
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
                        f"ABORT: {path} has no `year` column and the leg spans {years}"
                    )
                df = df.assign(year=years[0])
            frames[fname].append(df)
        for y in years:
            per = src / f"run_config_{y}.json"
            shutil.copy2(per if per.is_file() else src / "run_config.json",
                         out / f"run_config_{y}.json")

    for fname, parts in frames.items():
        if parts:
            pd.concat(parts, ignore_index=True).to_parquet(out / fname, index=False)
            print(f"  {fname}: {len(parts)} leg(s) concatenated")

    all_years = sorted(set(all_years))
    base = next(iter(legs))
    # The composite's BASE run_config.json is the first leg's, so its
    # ``calibration_flags.years`` would claim the span is one year — which
    # ``audit_keepers`` E3 correctly reads as bundle metadata disagreeing with
    # ``meta.json``. Restamp it to the composed span; the per-year
    # ``run_config_<y>.json`` still carry each year's own truth.
    base_cfg = json.loads((CAL / base / "run_config.json").read_text())
    base_cfg.setdefault("calibration_flags", {})["years"] = all_years
    (out / "run_config.json").write_text(json.dumps(base_cfg, indent=2), encoding="utf-8")
    meta = json.loads((CAL / base / "meta.json").read_text())
    meta["years"] = all_years
    meta["composed_from"] = {n: sorted(y) for n, y in legs.items()}
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    n = sum(1 for p in out.rglob("*") if p.is_file())
    print(f"\ncomposed {out} — {n} files, years {all_years}")
    print(
        "  NOTE: run_config.json is the FIRST leg's, so its two year-scoped "
        "fields read 2020's. run_config_<y>.json carries each year's own; there "
        "is no partition to stamp, because there is only one recipe."
    )


def regenerate_diagnostics(out: Path, years: list[int]) -> int:
    """Rebuild ``legitimacy_diagnostics.json`` over the WHOLE composite (zero LP)."""
    cmd = [
        sys.executable,
        str(REPO / "scripts" / "legitimacy_diagnostics.py"),
        "--bundle", str(out),
        "--iso", "NEISO",
        "--years", *[str(y) for y in years],
        "--json-out", str(out / "legitimacy_diagnostics.json"),
    ]
    print("\nregenerating legitimacy_diagnostics.json over the composite:")
    print("  " + " ".join(cmd))
    rc = subprocess.run(cmd, cwd=REPO).returncode
    # A failing diagnostic GATE exits nonzero; that says nothing about whether
    # the artifact was written. What matters is that it exists and spans every
    # year — check that, not the status.
    art = out / "legitimacy_diagnostics.json"
    if not art.is_file():
        print(f"  NO ARTIFACT WRITTEN (exit {rc}) — C8 would score SKIPPED; do not register.")
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
    ap.add_argument("--leg", action="append", required=True,
                    help="YEARS=bundle_name, e.g. 2020=neiso112_mer_2020")
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip-diagnostics", action="store_true")
    args = ap.parse_args()

    legs: dict[str, list[int]] = {}
    for spec in args.leg:
        years, _, name = spec.partition("=")
        if not name:
            raise SystemExit(f"--leg expects YEARS=bundle, got {spec!r}")
        legs[name] = [int(y) for y in years.split(",")]

    out = Path(args.out)
    if not out.is_absolute():
        out = REPO / out
    compose(legs, out)
    if args.skip_diagnostics:
        return 0
    return regenerate_diagnostics(out, sorted({y for ys in legs.values() for y in ys}))


if __name__ == "__main__":
    raise SystemExit(main())
