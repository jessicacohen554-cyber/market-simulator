"""closeout-PJM-lossdemand, zero LP: compose the seven year-isolated legs into ONE span bundle.

The keeper's own composer (:mod:`scripts.probes._pjmnext26_compose_span`) with exactly one declared
delta added to its required posture: every leg must record ``zonal_loss_demand_reconciliation=True``
(PRECOMMIT-closeout-pjm-lossdemand-2026-10-03 §1, the probe's single config delta). Every other
check — the recipe equals the keeper's on every other field, one surface fingerprint, the pinned
sha, a complete bundle per leg — is the keeper composer's, unchanged.

Usage::

    python scripts/probes/_closeoutpjm_lossdemand_compose_span.py --iso PJM \\
        --keeper results/calibration/closeout_pjm_nuc_full_span \\
        --leg 2019=results/calibration/closeout_pjm_lossdemand_2019 ... \\
        --pinned-sha <40-char sha> --out results/calibration/closeout_pjm_lossdemand_span
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

DELTA = "zonal_loss_demand_reconciliation"

_path = Path(__file__).resolve().parent / "_pjmnext26_compose_span.py"
_spec = importlib.util.spec_from_file_location("_pjmnext26_compose_span", _path)
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)
_w0 = base._w0_fields
base._w0_fields = lambda: (*_w0(), DELTA)

if __name__ == "__main__":
    base.main()
