"""Compose neiso-117's seven single-year legs into one 2019-2025 bundle (zero LP).

Copy of ``docs/handoffs/neiso114/compose_span.py`` with the arm selector removed:
neiso-117 has one arm (``coal_fuel_inventory_plant_grain``), checked by
``docs/handoffs/neiso117/shard_check.py``. Inherited header follows.

Rule 36 ``[R-YEAR-ISOLATION]`` solved each year in its own shard; composition is
the parent's zero-LP job (rule 32 ``[R-SHARD]`` (d)). The mechanics are
``scripts/probes/_hydro5_compose_span.py``'s (bundle-root frames concatenate,
year-stamped files copy, ``run_config_<y>.json`` per leg, ``meta.json`` years /
gas prices / ``composed_from`` re-spanned, the year-dependent shared benchmark
frames rebuilt over the span, ``legitimacy_diagnostics.json`` regenerated over
the composite) — imported, not re-derived. Only the recipe check differs: every
leg must pass ``docs/handoffs/neiso117/shard_check.py`` (keeper +
exactly the PRECOMMIT delta, std extract sha256, classifier hash) and all legs
must share one solve-surface fingerprint.

Usage::

    uv run python docs/handoffs/neiso117/compose_span.py \\
        --leg 2019=neiso117_2019 ... --leg 2025=neiso117_2025 --out results/calibration/neiso117_span
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
for p in (str(REPO), str(REPO / "src"), str(REPO / "scripts" / "probes")):
    if p not in sys.path:
        sys.path.insert(0, p)

from _hydro5_compose_span import compose, regenerate_diagnostics  # noqa: E402

CAL = REPO / "results" / "calibration"
CHECK = REPO / "docs" / "handoffs" / "neiso117" / "shard_check.py"


def check_legs(legs: dict[str, list[int]]) -> None:
    """Abort unless every leg passes shard_check and all share one surface."""
    surfaces = set()
    for name, years in legs.items():
        if len(years) != 1:
            raise SystemExit(
                f"ABORT: {name} claims {years}; rule 36 legs are single-year"
            )
        (year,) = years
        rc = subprocess.run(
            [
                sys.executable,
                str(CHECK),
                "--leg",
                f"results/calibration/{name}",
                "--year",
                str(year),
            ],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        tail = (
            rc.stdout.strip().splitlines()[-1]
            if rc.stdout.strip()
            else rc.stderr[-400:]
        )
        print(f"  {name:14s} {year}: {tail}")
        if rc.returncode:
            print(rc.stdout)
            raise SystemExit(f"ABORT: {name} fails shard_check")
        cfg = json.loads((CAL / name / "run_config.json").read_text())
        recorded = sorted(cfg.get("calibration_flags", {}).get("years") or [])
        if recorded != [year]:
            raise SystemExit(f"ABORT: {name} records years {recorded}, claims [{year}]")
        surfaces.add((cfg.get("solve_surface") or {}).get("fingerprint"))
    if len(surfaces) != 1:
        raise SystemExit(
            f"ABORT: legs disagree on the solve-surface fingerprint: {surfaces}"
        )
    print(f"  OK — every leg is keeper + the declared delta; surface {surfaces.pop()}")


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--leg", action="append", required=True, help="YEAR=bundle_name")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    legs: dict[str, list[int]] = {}
    for spec in args.leg:
        ys, _, name = spec.partition("=")
        legs[name] = sorted(int(y) for y in ys.split(","))
    out = Path(args.out)
    out = out if out.is_absolute() else REPO / out
    check_legs(legs)
    compose(legs, out)
    years = sorted({y for ys in legs.values() for y in ys})
    return regenerate_diagnostics(out, "NEISO", years)


if __name__ == "__main__":
    raise SystemExit(main())
