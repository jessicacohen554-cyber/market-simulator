"""closeout-SOCO-w3, zero LP: compose the seven DIAGNOSTIC legs (holdout + metered coal online floor; never promotable) into one span bundle.

Thin wrapper over ``_w0_compose_span.py``. The keeper (``closeout_soco_3_span``)
already records every W0 field and the R-49 coal-pile arm ``True``, so the only
recipe delta a leg may carry is ``mustrun_chp_btm_holdout``. Every other field
must equal the keeper's, so the composer's recipe check enforces kill K3 of
``docs/records/soco/closeout-soco-w3/PRECOMMIT-solve-closeout-soco-w3-2026-10-04.md``.

Usage::

    python scripts/probes/_closeout_socow3_compose.py --iso SOCO \\
        --keeper results/calibration/closeout_soco_3_span \\
        --leg 2019=results/calibration/closeout_soco_w3d_2019 ... \\
        --pinned-sha 6cfad57bbf1ce96571989633e2cc8e47d4b0032a \\
        --out results/calibration/closeout_soco_w3d_span
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
import _w0_compose_span as base  # noqa: E402

ARM = ("mustrun_chp_btm_holdout", "diagnostic_coal_metered_online_floor")
_W0 = base._w0_fields


def _fields() -> tuple[str, ...]:
    """The W0 fields plus the w3 arm: each must read True on every leg."""
    return tuple(_W0()) + ARM


base._w0_fields = _fields

if __name__ == "__main__":
    sys.exit(base.main())
