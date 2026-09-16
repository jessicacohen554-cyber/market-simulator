#!/usr/bin/env python3
"""Compose the miso-259 per-year arm bundles into ONE registrable span bundle.

Each year was solved by its own shard and pushed as a WHOLE bundle (17 files
including ``dispatch/``, ``system.parquet``, ``btm.parquet`` and ``floors/``) —
which is what makes per-year fan-out composable at all, and what the slim-shard
ban in CLAUDE.md rule 32 ``[R-SHARD]`` (b) was actually written against.

The composition is mechanical and lossless:

* **per-year files are copied** — ``dispatch/<y>_P1.parquet``,
  ``dispatch/<y>_P1_fleet.parquet``, ``floors/<y>_P1.npz`` and every
  ``hourly/*_<y>.parquet`` already carry the year in their name, so they simply
  land side by side;
* **bundle-root frames are CONCATENATED** — ``system.parquet``,
  ``btm.parquet``, ``flows.parquet`` and ``storage.parquet`` are per-year in a
  single-year bundle and must become the six-year frame a composite carries. A
  ``year`` column is added where the frame does not already have one, so the
  concat is inspectable rather than an anonymous stack;
* **``run_config.json`` is kept per year** as ``run_config_<y>.json`` (the shape
  the keeper bundle itself uses) with the first year's also written as the base
  ``run_config.json``, and ``legitimacy_diagnostics.json`` likewise;
* **``meta.json``** is the first year's with ``years`` widened to the full span.

Every source year's config is CHECKED before anything is written: same
``coal_fuel_inventory``, same ``mode``, same ``solve_surface`` fingerprint. A
mismatch aborts rather than composing a bundle whose years did not solve the
same recipe.

Usage:
    python scripts/probes/_miso259_compose_span.py \
        --out results/calibration/miso259_coalinv_span
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

CAL = REPO / "results" / "calibration"

#: year -> source bundle. 2022 is the screen ARM, already solved and verified;
#: re-solving it would have been pure waste.
SOURCES: dict[int, str] = {
    2020: "miso259_coalinv_2020",
    2021: "miso259_coalinv_2021",
    2022: "miso259_screen_arm",
    2023: "miso259_coalinv_2023",
    2024: "miso259_coalinv_2024",
    2025: "miso259_coalinv_2025",
}

#: Bundle-root frames that are per-year in a single-year bundle and must be
#: concatenated into the composite's six-year frame.
ROOT_FRAMES = ("system.parquet", "btm.parquet", "flows.parquet", "storage.parquet")


def _check_recipes() -> dict:
    """Verify every source year solved the SAME recipe; return the shared config."""
    seen: dict[str, set] = {"coal_fuel_inventory": set(), "mode": set(), "fp": set()}
    first = None
    for year, name in sorted(SOURCES.items()):
        cfg = json.loads((CAL / name / "run_config.json").read_text())
        sc = cfg["scenario_config"]
        seen["coal_fuel_inventory"].add(sc.get("coal_fuel_inventory"))
        seen["mode"].add(sc.get("mode"))
        seen["fp"].add((cfg.get("solve_surface") or {}).get("fingerprint"))
        if first is None:
            first = cfg
        print(
            f"  {year} {name:26s} armed={sc.get('coal_fuel_inventory')} "
            f"mode={sc.get('mode')} surface={(cfg.get('solve_surface') or {}).get('fingerprint')}"
        )
    for key, values in seen.items():
        if len(values) != 1:
            raise SystemExit(
                f"ABORT: source years disagree on {key!r}: {sorted(map(str, values))}. "
                "A composite whose years solved different recipes is not one run."
            )
    if seen["coal_fuel_inventory"] != {True}:
        raise SystemExit("ABORT: not every source year is ARMED.")
    if seen["mode"] != {"backcast"}:
        raise SystemExit("ABORT: not every source year is mode=backcast.")
    return first


def compose(out: Path) -> None:
    print("verifying the six source recipes agree:")
    first_cfg = _check_recipes()

    if out.exists():
        shutil.rmtree(out)
    (out / "dispatch").mkdir(parents=True)
    (out / "floors").mkdir(parents=True)
    (out / "hourly").mkdir(parents=True)

    frames: dict[str, list[pd.DataFrame]] = {n: [] for n in ROOT_FRAMES}
    for year, name in sorted(SOURCES.items()):
        src = CAL / name
        for sub in ("dispatch", "floors", "hourly"):
            for path in sorted((src / sub).glob("*")):
                if str(year) not in path.name:
                    raise SystemExit(f"ABORT: {path} is not stamped with {year}")
                shutil.copy2(path, out / sub / path.name)
        for fname in ROOT_FRAMES:
            path = src / fname
            if not path.is_file():
                print(f"  {year}: {fname} absent, skipped")
                continue
            df = pd.read_parquet(path)
            if "year" not in df.columns:
                df.insert(0, "year", year)
            frames[fname].append(df)
        shutil.copy2(src / "run_config.json", out / f"run_config_{year}.json")
        diag = src / "legitimacy_diagnostics.json"
        if diag.is_file():
            shutil.copy2(diag, out / f"legitimacy_diagnostics_{year}.json")

    for fname, parts in frames.items():
        if parts:
            pd.concat(parts, ignore_index=True).to_parquet(out / fname, index=False)
            print(f"  {fname}: {len(parts)} year(s) concatenated")

    shutil.copy2(CAL / SOURCES[2020] / "run_config.json", out / "run_config.json")
    shutil.copy2(
        CAL / SOURCES[2020] / "legitimacy_diagnostics.json",
        out / "legitimacy_diagnostics.json",
    )
    meta = json.loads((CAL / SOURCES[2020] / "meta.json").read_text())
    meta["years"] = sorted(SOURCES)
    meta["composed_from"] = {str(y): n for y, n in sorted(SOURCES.items())}
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    n = sum(1 for _ in out.rglob("*") if _.is_file())
    print(f"\ncomposed {out} — {n} files, years {sorted(SOURCES)}")
    for sub in ("dispatch", "floors", "hourly"):
        print(f"  {sub}/: {len(list((out / sub).glob('*')))} files")
    _ = first_cfg


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=CAL / "miso259_coalinv_span")
    compose(ap.parse_args().out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
