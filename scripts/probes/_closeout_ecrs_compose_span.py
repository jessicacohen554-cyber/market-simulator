#!/usr/bin/env python3
"""Compose the closeout-ERCOT-ECRS span (R-42 + R-46) from the incumbent keeper.

Zero LP. The keeper bundle ``closeout_ercot_l1_span`` is the base. The 2024 and
2025 year files stay byte-identical: the keeper's own leg files are
sha-identical to the l1b-2024/2025 legs. The 2019–2023 year files are swapped
for the ×33-strip legs (``closeout_ercot_ecrs_<Y>``), each solved at its own
l1/l1b leg commit (code ``106d6bb7``) with only the 17
``offer_curve_by_group`` peak / phys_peak / peak_ladder keys returned to the
forward values.

Steps:
1. Copy the keeper bundle.
2. For each stripped year, copy the leg's hourly sidecars (the keeper's
   retained set only), ``dispatch/``, ``floors/`` and its ``run_config.json``
   as ``run_config_<Y>.json``.
3. Place the 2024/2025 leg ``dispatch/`` so diagnostics read real dispatch.
4. Re-stamp ``config_partition_overrides`` with ``stamp_config_partition.py``
   (derived from the run_configs, never hand-typed).
5. Regenerate ``legitimacy_diagnostics.json`` over all seven years.

Usage:
    python scripts/probes/_closeout_ecrs_compose_span.py \
        --out results/calibration/closeout_ercot_ecrs_span
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
CAL = REPO / "results" / "calibration"
KEEPER = CAL / "closeout_ercot_l1_span"
STRIP_YEARS = (2019, 2020, 2021, 2022, 2023)
KEPT_LEGS = {2024: "closeout_ercot_l1b_2024", 2025: "closeout_ercot_l1b_2025"}
BAND_KEYS = ("peak", "phys_peak", "peak_ladder")
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
    """K1 at compose time: the leg differs from the keeper only in band keys."""
    leg = CAL / f"closeout_ercot_ecrs_{year}"
    a = _flat(json.loads((leg / "run_config.json").read_text())["scenario_config"])
    k = _flat(
        json.loads((KEEPER / f"run_config_{year}.json").read_text())["scenario_config"]
    )
    diff = sorted(x for x in set(a) | set(k) if a.get(x) != k.get(x))
    bad = [
        x
        for x in diff
        if not (x.startswith("offer_curve_by_group.") and x.split(".")[-1] in BAND_KEYS)
    ]
    if bad or len(diff) != 17:
        raise SystemExit(f"ABORT K1 {year}: {len(diff)} diffs, non-band {bad}")
    if not (leg / "dispatch" / f"{year}_P1.parquet").is_file():
        raise SystemExit(f"ABORT: {leg}/dispatch/{year}_P1.parquet missing")
    return leg


def concat_root_frames(out: Path, legs: dict[int, Path]) -> None:
    """Concatenate the per-leg root frames (the registration renderer reads them).

    The slim keeper bundle no longer carries them, so every year comes from its
    leg: 2019–2023 from the strip legs, 2024/2025 from the l1b legs.
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
        **{f"closeout_ercot_ecrs_{y}": [y] for y in STRIP_YEARS},
        **{n: [y] for y, n in KEPT_LEGS.items()},
    }
    meta["run_note"] = (
        "closeout-ERCOT-ECRS (owner rulings R-42 2023, R-46 2019-22): the x33 "
        "peak / phys_peak / peak_ladder bands removed from every carve-out and "
        "validation year (forward values); 2023 ECRS carried only by the armed "
        "ercot_ecrs_conservative_deployment stack; 2024/2025 keeper legs byte-identical"
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
