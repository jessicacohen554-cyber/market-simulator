#!/usr/bin/env python3
"""Compose the closeout-ERCOT-w6 span (measured CHP BTM share) from the keeper.

Zero LP. Adapted from ``_closeout_ercot_w4_compose_span.py``. The keeper bundle
``closeout_ercot_l1_span`` is the base. ALL SEVEN year files are swapped for the
w6 legs (``closeout_ercot_w6_<Y>``), each solved at ``60e11319`` (keeper recipe
replayed per year, its own partition overlay included) with only
``ercot_chp_btm_measured=true`` set.

Steps:
1. Copy the keeper bundle.
2. For each armed year, copy the leg's hourly sidecars (the keeper's
   retained set only), ``dispatch/``, ``floors/`` and its ``run_config.json``
   as ``run_config_<Y>.json``.
3. Place the 2023 leg ``dispatch/`` and ``floors/`` so diagnostics read real dispatch.
4. Re-stamp ``config_partition_overrides`` with ``stamp_config_partition.py``
   (derived from the run_configs, never hand-typed).
5. Regenerate ``legitimacy_diagnostics.json`` over all seven years.

Usage:
    python scripts/probes/_closeout_ercot_w6_compose_span.py \
        --out results/calibration/closeout_ercot_w6_span
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "src"), str(REPO)]
CAL = REPO / "results" / "calibration"
KEEPER = CAL / "closeout_ercot_l1_span"
STRIP_YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
KEPT_LEGS: dict[int, str] = {}
ARM_KEYS = ("ercot_chp_btm_measured",)
ROOT_FRAMES = ("system.parquet", "btm.parquet", "flows.parquet", "storage.parquet")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _flat(d: dict, pre: str = "") -> dict:
    out: dict = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(_flat(v, pre + k + "."))
        else:
            out[pre + k] = v
    return out


def check_leg(year: int) -> Path:
    """K1 at compose time: the leg differs from the keeper only in the arm keys."""
    leg = CAL / f"closeout_ercot_w6_{year}"
    a = _flat(json.loads((leg / "run_config.json").read_text())["scenario_config"])
    k = _flat(
        json.loads((KEEPER / f"run_config_{year}.json").read_text())["scenario_config"]
    )
    # A field added after the keeper sha is absent from the keeper's record and
    # must sit at its shipped default in the leg; a field deleted since (rule 26)
    # is absent from the leg and must have been off/unset in the keeper.
    import dataclasses

    from market_sim.config.scenarios import ScenarioConfig

    defaults = {
        f.name: f.default
        for f in dataclasses.fields(ScenarioConfig)
        if f.default is not dataclasses.MISSING
    }

    def _differs(x: str) -> bool:
        if x in a and x in k:
            return a[x] != k[x]
        if x in a:  # added since the keeper
            return x in ARM_KEYS or a[x] != defaults.get(x, object())
        return k[x] not in (False, None)  # deleted since the keeper

    diff = sorted(x for x in set(a) | set(k) if _differs(x))
    if diff != sorted(ARM_KEYS) or any(a[k] is not True for k in ARM_KEYS):
        raise SystemExit(f"ABORT K1 {year}: diffs {diff}")
    if not (leg / "dispatch" / f"{year}_P1.parquet").is_file():
        raise SystemExit(f"ABORT: {leg}/dispatch/{year}_P1.parquet missing")
    return leg


def concat_root_frames(out: Path, legs: dict[int, Path]) -> None:
    """Concatenate the per-leg root frames (the registration renderer reads them).

    The slim keeper bundle no longer carries them, so every year comes from its
    leg: every year from its w6 leg.
    """
    import pandas as pd

    for fname in ROOT_FRAMES:
        parts = []
        for y, leg in sorted(legs.items()):
            path = leg / fname
            if not path.is_file():
                raise SystemExit(f"ABORT: {path} missing")
            df = pd.read_parquet(path)
            parts.append(df if "year" in df.columns else df.assign(year=y))
        pd.concat(parts, ignore_index=True).to_parquet(out / fname, index=False)


def compose(out: Path) -> None:
    """Build the composed bundle at ``out`` (see module docstring)."""
    legs = {y: check_leg(y) for y in STRIP_YEARS}
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(KEEPER, out)
    kept_hourly = sorted(p.name for p in (KEEPER / "hourly").glob("*_2023.parquet"))
    stems = [n[: -len("_2023.parquet")] for n in kept_hourly]
    # unit_marginal is the rule-15 slim layer every keeper carries; unit_hourly stays out.
    stems = [s for s in stems if s != "unit_hourly"]
    for y, leg in legs.items():
        for stem in stems:
            src = leg / "hourly" / f"{stem}_{y}.parquet"
            if not src.is_file():
                raise SystemExit(f"ABORT: {src} missing")
            shutil.copy2(src, out / "hourly" / src.name)
        for sub in ("dispatch", "floors"):
            if (leg / sub).is_dir():
                (out / sub).mkdir(exist_ok=True)
                for p in (leg / sub).glob(f"{y}_*"):
                    shutil.copy2(p, out / sub / p.name)
        shutil.copy2(leg / "run_config.json", out / f"run_config_{y}.json")
    for y, name in KEPT_LEGS.items():
        src = CAL / name
        for stem in stems:
            a, b = (
                src / "hourly" / f"{stem}_{y}.parquet",
                out / "hourly" / f"{stem}_{y}.parquet",
            )
            if a.is_file() and _sha(a) != _sha(b):
                raise SystemExit(f"ABORT: kept leg {y} {stem} differs from keeper")
        # dispatch AND floors: the diagnostics rebuild the bridge floors from
        # floors/<Y>_P1.npz, so a kept year without it reads 0 % forced.
        for sub in ("dispatch", "floors"):
            (out / sub).mkdir(exist_ok=True)
            for p in (src / sub).glob(f"{y}_*"):
                shutil.copy2(p, out / sub / p.name)
    concat_root_frames(out, {**legs, **{y: CAL / n for y, n in KEPT_LEGS.items()}})
    meta = json.loads((out / "meta.json").read_text())
    meta["composed_from"] = {
        **{f"closeout_ercot_w6_{y}": [y] for y in STRIP_YEARS},
        **{n: [y] for y, n in KEPT_LEGS.items()},
    }
    meta["run_note"] = (
        "closeout-ERCOT-w6: ercot_chp_btm_measured armed in every year "
        "(measured EIA-923 Schedules 6/7 CHP behind-the-meter share)"
    )
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    legspec = [f"--leg={y}=run_config_{y}.json" for y in range(2019, 2026)]
    subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "stamp_config_partition.py"),
            str(out),
            *legspec,
        ],
        cwd=REPO,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "stamp_config_partition.py"),
            str(out),
            *legspec,
            "--check",
        ],
        cwd=REPO,
        check=True,
    )


def regenerate_diagnostics(out: Path) -> int:
    """Rebuild ``legitimacy_diagnostics.json`` over all seven years (zero LP)."""
    years = [str(y) for y in range(2019, 2026)]
    rc = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "legitimacy_diagnostics.py"),
            "--bundle",
            str(out),
            "--iso",
            "ERCOT",
            "--years",
            *years,
            "--json-out",
            str(out / "legitimacy_diagnostics.json"),
        ],
        cwd=REPO,
    ).returncode
    got = json.loads((out / "legitimacy_diagnostics.json").read_text()).get("years")
    print(f"legitimacy_diagnostics exit {rc}; years {got}")
    return 0 if sorted(got or []) == list(range(2019, 2026)) else 1


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    if not out.is_absolute():
        out = REPO / out
    compose(out)
    return regenerate_diagnostics(out)


if __name__ == "__main__":
    raise SystemExit(main())
