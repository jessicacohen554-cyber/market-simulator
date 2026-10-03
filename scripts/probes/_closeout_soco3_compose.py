"""closeout-SOCO-3, zero LP: compose the seven take-or-pay-pile legs into one span bundle.

Thin wrapper over ``_w0_compose_span.py``. The keeper (``closeout_soco_2_span``)
already records every W0 field ``True``, so the only recipe delta a leg may carry
is the R-49 arm. This wrapper adds the four arm fields to the composer's
required-``True`` set; every other field must equal the keeper's, so the
composer's recipe check enforces kill 4 of
``docs/records/soco/closeout-soco-3/PRECOMMIT-solve-closeout-soco-3-2026-10-03.md``.

Usage::

    python scripts/probes/_closeout_soco3_compose.py --iso SOCO \\
        --keeper results/calibration/closeout_soco_2_span \\
        --leg 2019=results/calibration/closeout_soco_3_2019 ... \\
        --pinned-sha 0629d7955843948313beaa5c5f1d7a48e52ef4ef \\
        --out results/calibration/closeout_soco_3_span
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
import _w0_compose_span as base  # noqa: E402

ARM = (
    "coal_fuel_inventory_plant_grain",
    "coal_fuel_inventory_take_floor",
    "coal_fuel_inventory_monthly_pile",
    "coal_monthly_pile_measured_receipts",
)
_W0 = base._w0_fields


def _fields() -> tuple[str, ...]:
    """The W0 fields plus the R-49 arm: each must read True on every leg."""
    return tuple(_W0()) + ARM


base._w0_fields = _fields

if __name__ == "__main__":
    sys.exit(base.main())
