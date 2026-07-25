#!/usr/bin/env python3
"""Repair the NYISO bench parts' EIA-930 ``nuclear`` cell (no LP solve).

Rule-14 follow-through for the zero-coded-gap fix in
``data/eia930/actuals.py`` (``_ZERO_CODED_GAP_SERIES``, 2026-07-24, see
``docs/FINDING-nyiso-import-hour-assignment-and-nuclear-benchmark-2026-07-24.md``
§4). The NYIS EIA-930 extract codes ``NG: NUC`` filing gaps as an exact ``0.0``
— 1,275 h in 2023, 390 h in 2024, 118 h in 2025 — so the committed bench parts
carry a nuclear actual understated by 3.46 / 1.12 / 0.37 TWh. The loader now
masks those zeros to NaN and bridges them, but the bench parts were rendered
BEFORE the fix and still show the artifact on the run explorer.

Scope — deliberately one field:

* ``bench.e930.nuclear`` only, for NYISO 2023-2025.
* Every other bench field (``plants``, ``classFull``, ``avgLMP``, ``storage``,
  ``co2``, and the other ``e930`` cells) is left byte-for-byte.

This is provably equivalent to a full re-render of that cell.
``render_calibration_html.build_payload`` computes each raw ``e930`` cell as
``sum(series)/1e6`` over the bundle's EIA-930 extract, and that extract is
``load_eia_hourly_benchmark`` output; the guard below asserts that EVERY other
raw cell the loader produces already reproduces the committed value exactly, so
``nuclear`` is the sole cell the fix moves. ``solar`` is excluded from the guard
and never written: the render deliberately MIRRORS the utility-scale EIA-923
solar into the ``e930`` slot (build_payload's ``_vre`` block), so its committed
value is not a raw 930 sum and must not be recomputed here.

The write uses the same deterministic gzip as
``render_backcast._write_bench_part`` (``backcast_artifacts.write_bench_part``,
compresslevel=9, mtime=0), so re-running is idempotent and the diff shows only
the years whose value genuinely changed.

SCORING IMPACT: none, and structurally none. ``calibration_verdict`` reads
``bench.e930`` only for ``coal_cems`` / ``gas`` / ``coal`` /
``gas_cems_grid`` / ``gas_cogen_grid``; C1 takes nuclear from ``classFull``
(EIA-923 basis) and C4 scores only the gas and coal families. This repairs the
DISPLAYED benchmark, not any gate. ``--check`` re-runs the guards and reports
the drift without writing.

Usage:
    python scripts/regen_nyiso_bench_nuclear.py [--check]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
for _p in (str(_REPO / "src"), str(_REPO)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from market_sim.data.eia930.actuals import (  # noqa: E402
    load_eia_hourly_benchmark,
)
from scripts.lib import backcast_artifacts as ba  # noqa: E402

ISO = "NYISO"
YEARS = (2023, 2024, 2025)
BENCH_DIR = _REPO / "frontend" / "data" / "backcast" / "bench"

# Raw 930 cells the render sums straight from the loader's series. ``solar`` is
# excluded on purpose (mirrored from EIA-923 by the render — see module
# docstring); ``coal_cems`` / ``gas_cems_grid`` / ``gas_cogen_grid`` are CAMPD /
# EIA-923 derived and are not loader sums either.
_RAW_CELLS = ("gas", "coal", "wind", "other")

# The cell this script repairs.
_TARGET = "nuclear"


def _loader_twh(year: int) -> dict[str, float]:
    """Return the loader's per-fuel annual net generation (TWh) for ``year``."""
    series = load_eia_hourly_benchmark(ISO, year)
    if series is None:
        raise SystemExit(f"no EIA-930 hourly benchmark for {ISO} {year}")
    return {k: round(float(np.nansum(v)) / 1e6, 3) for k, v in series.items()}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--check",
        action="store_true",
        help="report drift and run the guards without writing the parts",
    )
    args = ap.parse_args()

    changed: list[str] = []
    for year in YEARS:
        path = BENCH_DIR / ISO / f"{year}.json.gz"
        if not path.exists():
            raise SystemExit(f"missing bench part {path}")
        part = ba.load_bench_part(path)
        e930 = part["bench"]["e930"]
        fresh = _loader_twh(year)

        # GUARD (input parity): every OTHER raw cell must already reproduce
        # exactly. If one drifts, the committed part was not built from this
        # loader's basis and a one-field patch would silently mix bases.
        for cell in _RAW_CELLS:
            if cell not in e930:
                continue
            committed, recomputed = float(e930[cell]), float(fresh.get(cell, 0.0))
            if abs(committed - recomputed) > 5e-4:
                raise SystemExit(
                    f"{ISO} {year}: raw cell {cell!r} does not reproduce "
                    f"(committed {committed}, loader {recomputed}) — refusing "
                    "to patch a part built on a different basis."
                )

        old = float(e930.get(_TARGET, 0.0))
        new = float(fresh[_TARGET])
        # GUARD (direction): bridging filing gaps can only ADD energy.
        if new < old - 5e-4:
            raise SystemExit(
                f"{ISO} {year}: repaired {_TARGET} {new} < committed {old}; "
                "gap-bridging must not remove energy."
            )
        delta = new - old
        print(f"{ISO} {year}: e930.{_TARGET} {old:.3f} -> {new:.3f} TWh ({delta:+.3f})")
        if abs(delta) <= 5e-4:
            continue
        changed.append(f"{year}")
        if args.check:
            continue
        e930[_TARGET] = new
        ba.write_bench_part(BENCH_DIR, ISO, year, part["meta"], part["bench"])

    if args.check:
        print(f"[check] would rewrite: {changed or 'nothing'}")
    else:
        print(f"rewrote bench parts: {changed or 'nothing'}")


if __name__ == "__main__":
    main()
