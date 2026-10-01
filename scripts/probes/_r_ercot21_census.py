"""R-ERCOT-21 (zero LP): per-unit fleet census on keeper r-20 (Lost Pines + CC identity heat rates).

Rebuilds the keeper recipe's LP fleet (``run_year(fleet_only=True)``, bundle
``r_ercot20_span``) for each year and writes one row per LP unit: plant code,
group, pmax, mean availability, available energy (TWh), must-run floor energy
and mean mc. Run on the arm inputs and diff against the keeper's own legs
(``unit_hourly`` cap_mw / mc): Lost Pines 55154 should gain its 365 MW
non-CHP share, the identity-priced CC rows should move mc only, and any
fleet-wide construct defined over class capacity may move slightly
(R-ERCOT-11 §3).

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python \
        scripts/probes/_r_ercot21_census.py --years 2022 2024 --out <csv>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts/probes"):
    sys.path.insert(0, str(p))

import _r_ercot3_coal_census as c3  # noqa: E402
import _r_ercot11_parish_split_census as c11  # noqa: E402

c3.BUNDLE = REPO / "results/calibration/r_ercot20_span"


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs=2, default=[2019, 2025])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    frames = [c11.census(y) for y in range(a.years[0], a.years[1] + 1)]
    pd.concat(frames).to_csv(a.out, index=False)


if __name__ == "__main__":
    main()
