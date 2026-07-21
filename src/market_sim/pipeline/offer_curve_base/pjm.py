"""PJM base offer-curve band deltas (byte-for-byte from the former
``if iso == "PJM"`` ternary branches in ``backcast_config``).

NOTE: these branch values are SUPERSEDED for PJM in practice — immediately
after the base curve is built, ``backcast_config`` replaces the whole dict
with the calibrated ``_PJM_OFFER_CURVE`` ("Replacing the whole dict keeps
the calibrated PJM curve in one place ... and out of the per-band
``if iso == 'PJM'`` ternaries"). They are preserved here byte-for-byte so
the ternary→registry conversion is exact code motion (rule 23) — deleting
them would be a behavior change for any path reading the base curve before
the replacement, however hypothetical.

Provenance (from the former inline comments): PJM CC econ raised moderately
(econ_low 1.06->1.20, econ_high 1.27->1.49) to trim a residual CC_REGULAR
overrun — the bulk of the gas-level correction is the EIA-923-derived gas
basis (+0.67, constants.GAS_BASIS_DIFFERENTIAL) + per-plant gas pricing,
not the offer curve. PJM keeps its own validated CT curve (committed 1.10,
econ_low 1.20, peak 13.0).
"""

from __future__ import annotations

PJM_BASE_OFFER_CURVE_DELTAS: dict[str, dict[str, float]] = {
    "CC_REGULAR": {"econ_low": 1.20, "econ_high": 1.49},
    "CC_CHP": {"econ_low": 0.95, "econ_high": 1.14},
    "CT_CHP": {"committed": 1.20},
    "CT_PEAKER": {"committed": 1.10, "econ_low": 1.20, "peak": 13.0},
}
