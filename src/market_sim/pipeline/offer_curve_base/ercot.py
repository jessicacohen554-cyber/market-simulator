"""ERCOT-fitted base offer-curve band deltas (byte-for-byte from the former
``if iso == "ERCOT"`` ternary branches in ``backcast_config``; rule 25 —
these fitted values are ERCOT's and never merge into the generic defaults).

ERCOT bands fold in the run57 baseline so a no-tweak ERCOT run reproduces
run57 and workflow tweaks are +/- relative to it:

* CC_REGULAR econ (econ_low 1.06->1.16, econ_high 1.27->1.41);
* CT_PEAKER committed (1.55 -> 1.48);
* ST_GAS (committed 0.81->0.91, econ_low 1.05->1.15, econ_high 1.40->1.55);
* COAL_PRB econ (econ_low 0.77->0.70, econ_high 1.19->0.94).
"""

from __future__ import annotations

ERCOT_BASE_OFFER_CURVE_DELTAS: dict[str, dict[str, float]] = {
    "CC_REGULAR": {"econ_low": 1.16, "econ_high": 1.41},
    "CT_PEAKER": {"committed": 1.48},
    "ST_GAS": {"committed": 0.91, "econ_low": 1.15, "econ_high": 1.55},
    "COAL_PRB": {"econ_low": 0.70, "econ_high": 0.94},
}
