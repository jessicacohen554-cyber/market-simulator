#!/usr/bin/env python3
"""Derive the CAISO LATE-EVENING (hod 22-23) south-corridor clean depth — gate check.

The fourth and last member of the caiso-87 / caiso-93 / caiso-94 DSW
clean-depth family, and the one that closes the family's WINDOW GAP. Its two
committed siblings are ``derive_caiso_overnight_clean_depth.py`` (hod 0-5) and
``derive_caiso_daytime_clean_depth.py`` (hod 6-21); this script produces
``interchange_config.CAISO_DSW_LATEEVENING_CLEAN_DEPTH_BY_YEAR`` /
``..._STATIC`` for hod 22-23, which those two windows leave uncovered and
which caiso-87's surplus trigger cannot reach (measured ON in 0.3/0.8 % of
2024 and 1.6/1.9 % of 2025 hod 22/23 — caiso-253's G-WINDOW leg).

Derived quantity — the sibling construction, unchanged:

  depth[y] = p95 of measured WECC_DSW corridor net import over ALL hod 22-23
             hours of year y (EIA-930 CISO DIBAs on the model clock, via
             ``corridor_net_import``).

Same series, same p95 statistic, same window-match rule (the depth is taken
over exactly the window the capability arms). Nothing here is a new statistic,
a new percentile or a new threshold.

Estimation-stage honesty gates (the FROZEN caiso-81/86/87/88 thresholds — a
FAIL files a FINDING and the lane stops; the gates are never iterated
against): CV <= 0.20 and LOYO (mean-of-other-two) <= 25 % over the 2023-2025
training years.

WINDOW PROVENANCE (rule 17 ``[R-FLOOR-WINDOW]``): the window is not this
script's choice. It is the complement caiso-93 (0-5) and caiso-94 (6-21)
leave, and caiso-253 already closed the question of which construction hod
22-23 belong to — "22-23 are OVERNIGHT-construction hours and no future
session need re-measure it". Driver = the WEIM/EDAM clean-transfer capability
the caiso-87/93/94 family already carries. Forward story (rule 13
``[R-MEASURED]``) = a forecast year carries the pooled static entry exactly as
``CAISO_DSW_OVERNIGHT_CLEAN_DEPTH_STATIC`` does, and the quantity regenerates
from any future year's measured corridor flows.

Rule 23 ``[R-FROZEN-DERIVE]``: re-run ONLY when the EIA-930 interchange
extract extends — never because a backcast residual moved.

Usage:
    python3 scripts/data/derive_caiso_lateevening_clean_depth.py
    python3 scripts/data/derive_caiso_lateevening_clean_depth.py --extra-years 2022
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.data.derive_caiso_import_tranches import (  # noqa: E402
    YEARS,
    corridor_net_import,
)

HOURS = 8760
#: The window this depth prices, and the window the capability arms.
HOD_MIN = 22
HOD_MAX = 23
#: The caiso-87 depth statistic, unchanged.
DEPTH_PCTL = 95.0
#: FROZEN estimation-stage gates (caiso-81/86/87/88).
CV_MAX = 0.20
LOYO_MAX = 0.25


def late_evening_depth(year: int, frame) -> float:
    """p95 of measured WECC_DSW corridor net import over hod 22-23 of ``year``."""
    series = frame.loc[year]["WECC_DSW"].to_numpy(dtype=float)
    hod = np.arange(HOURS) % 24
    window = (hod >= HOD_MIN) & (hod <= HOD_MAX)
    return float(np.nanpercentile(series[window], DEPTH_PCTL))


def main(argv: list[str] | None = None) -> int:
    """Print the per-year depths, the pooled static entry and the gate verdicts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--extra-years",
        type=int,
        nargs="*",
        default=[],
        help="Additional years to REPORT (never part of the gates or the "
        "pooled static entry, which stay on the 2023-2025 training window).",
    )
    args = parser.parse_args(argv)

    years = list(YEARS) + [y for y in args.extra_years if y not in YEARS]
    frame = corridor_net_import(sorted(years))
    depths = {y: late_evening_depth(y, frame) for y in sorted(years)}

    train = [depths[y] for y in YEARS]
    cv = float(np.std(train, ddof=0) / np.mean(train))
    loyo = 0.0
    for i in range(len(train)):
        others = [train[j] for j in range(len(train)) if j != i]
        loyo = max(loyo, abs(train[i] - np.mean(others)) / np.mean(others))

    print(
        f"CAISO DSW LATE-EVENING clean depth (hod {HOD_MIN}-{HOD_MAX}, "
        f"p{DEPTH_PCTL:.0f} corridor net import)"
    )
    for y in sorted(depths):
        tag = "" if y in YEARS else "   (reported only)"
        print(f"  {y}: {depths[y]:8.1f} MW{tag}")
    print(f"  pooled static (2023-2025 mean): {np.mean(train):.1f} MW")
    print(
        f"  GATE CV   {cv:.3f}  (<= {CV_MAX:.2f}) {'PASS' if cv <= CV_MAX else 'FAIL'}"
    )
    print(
        f"  GATE LOYO {loyo * 100:.1f}% (<= {LOYO_MAX * 100:.0f}%) "
        f"{'PASS' if loyo <= LOYO_MAX else 'FAIL'}"
    )
    return 0 if (cv <= CV_MAX and loyo <= LOYO_MAX) else 1


if __name__ == "__main__":
    raise SystemExit(main())
