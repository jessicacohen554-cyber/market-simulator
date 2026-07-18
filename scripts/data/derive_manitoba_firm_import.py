#!/usr/bin/env python3
"""Derive MISO's per-year Manitoba firm-hydro delivery from EIA-930 interchange.

The backcast overlay for the Manitoba Hydro firm-import block: the flat
:data:`market_sim.config.constants.MISO_MANITOBA_FIRM_IMPORT_MW` (1400 MW,
~12.3 TWh/yr) is the forecast-native contract MIDPOINT, but a backcast year has
the measured firm delivery, which swings with Manitoba's hydro conditions (a
multi-year drought collapsed its southbound exports through 2024-2025). This
derives :data:`market_sim.config.constants.MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR`
straight from the measured directed-flow series.

The measured input is the EIA-930 BA-to-BA INTERCHANGE product for MISO
(``data/raw/eia-930-interchange/MISO interchange hourly.parquet``, the same
series the per-seam deliverability envelope uses), filtered to the MHEB
(Manitoba Hydro) DIBA. EIA sign is ``+ = MISO exports to MHEB``, so the firm
IMPORT is the negative-flow hours: ``import_mw = -min(mw, 0)``. The per-year
firm delivery is the GROSS directed import (the contract still delivers in
drought years; MISO's occasional surplus sell-back is a separate, seam-excluded
transaction), annualized to a flat MW at 8760 h.

This is NOT a fit to MISO's net-interchange residual (claude.md rules #11/#12):
it is the directed firm-delivery quantity computed before any LP runs,
regenerable for a forward year from Manitoba's hydro outlook + the contract, and
flow-responsive (the 2025 drought collapse is the input changing, not a tune).

    python scripts/data/derive_manitoba_firm_import.py --years 2023 2024 2025
    python scripts/data/derive_manitoba_firm_import.py --years 2023 2024 2025 --check
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.interchange_config import (  # noqa: E402
    MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR,
)

_PARQUET = REPO / "data/raw/eia-930-interchange/MISO interchange hourly.parquet"
_DIBA = "MHEB"
_HOURS = 8760


def derive_firm_import_mw(year: int) -> tuple[float, float]:
    """Return ``(gross_import_twh, flat_mw)`` for Manitoba into MISO in ``year``.

    ``flat_mw`` is the gross directed import annualized at 8760 h — the value
    that goes in :data:`MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR`.
    """
    df = pd.read_parquet(_PARQUET)
    df = df[(df["diba"] == _DIBA) & (df["local_time"].dt.year == year)]
    # EIA sign + = MISO exports to MHEB; firm import = negative-flow hours.
    import_mw = (-df["mw"]).clip(lower=0.0)
    gross_import_twh = float(import_mw.sum()) / 1e6
    flat_mw = gross_import_twh * 1e6 / _HOURS
    return gross_import_twh, flat_mw


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument(
        "--check",
        action="store_true",
        help="Assert the committed constants table matches the data (CI guard).",
    )
    args = ap.parse_args()

    mismatched = False
    for year in args.years:
        twh, mw = derive_firm_import_mw(year)
        committed = MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR.get(year)
        flag = ""
        if args.check and committed is not None and abs(committed - mw) > 1.0:
            flag = f"  MISMATCH (committed {committed:.0f})"
            mismatched = True
        print(f"{year}: gross_import={twh:6.3f} TWh -> {mw:6.1f} MW{flag}")

    if args.check and mismatched:
        print(
            "\nFAIL: committed MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR != data",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
