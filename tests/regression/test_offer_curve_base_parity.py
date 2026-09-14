"""Byte-for-byte parity of the per-ISO base offer-curve constants
(:mod:`market_sim.pipeline.offer_curve_base`) against the frozen pre-Stage-E
inline ternary construction (rules 23/25: tuned values transplant
byte-for-byte; per-ISO fitted parameters never merge into generic defaults).

``_frozen_inline_curve`` is the exact ``offer_curve_by_group`` dict
``backcast_config`` built inline (per-band ``if iso == ...`` ternaries,
captured verbatim 2026-07-21 before the conversion). Any value drift in the
constant modules — or any change to the selection semantics (case-sensitive
raw-``iso`` comparison) — fails here.
"""

from __future__ import annotations

import pytest

from market_sim.pipeline.offer_curve_base import (
    BASE_OFFER_CURVE_DELTAS_BY_ISO,
    GENERIC_BASE_OFFER_CURVE,
    base_offer_curve_by_group,
)


def _frozen_inline_curve(iso: str) -> dict[str, dict[str, float]]:
    """The pre-conversion inline construction, frozen verbatim."""
    return {
        "CC_REGULAR": {
            "committed": 0.92,
            "econ_low": 1.20 if iso == "PJM" else (1.16 if iso == "ERCOT" else 1.06),
            "econ_high": 1.49 if iso == "PJM" else (1.41 if iso == "ERCOT" else 1.27),
            "peak": 2.25,
            "econ_low_share": 0.50,
            "pct_peaking": 8.0,
        },
        "CC_INTERMEDIATE": {
            "committed": 0.92,
            "econ_low": 0.95,
            "econ_high": 1.08,
            "peak": 2.25,
            "econ_low_share": 0.50,
            "pct_peaking": 8.0,
        },
        "CC_CHP": {
            "committed": 0.92,
            "econ_low": 0.95 if iso == "PJM" else 0.96,
            "econ_high": 1.14 if iso == "PJM" else 1.12,
            "peak": 2.25,
            "econ_low_share": 0.50,
            "pct_peaking": 8.0,
        },
        "CT_CHP": {
            "committed": 1.20 if iso == "PJM" else 1.10,
            "econ_low": 1.20,
            "econ_high": 1.20,
            "peak": 1.40,
            "econ_low_share": 0.50,
        },
        "CT_PEAKER": {
            "committed": 1.10 if iso == "PJM" else (1.48 if iso == "ERCOT" else 1.55),
            "econ_low": 1.20 if iso == "PJM" else 1.27,
            "econ_high": 1.98,
            "peak": 13.0 if iso == "PJM" else 13.15,
            "econ_low_share": 0.526,
            "pct_peaking": 7.0,
        },
        "CT_INTERMEDIATE": {
            "committed": 1.00,
            "econ_low": 1.00,
            "econ_high": 1.20,
            "peak": 3.00,
            "econ_low_share": 0.50,
            "pct_peaking": 5.0,
        },
        "ST_GAS": {
            "committed": 0.91 if iso == "ERCOT" else 0.81,
            "econ_low": 1.15 if iso == "ERCOT" else 1.05,
            "econ_high": 1.55 if iso == "ERCOT" else 1.40,
            "peak": 4.20,
            "econ_low_share": 0.500,
            "pct_peaking": 15.0,
        },
        "ST_GAS_INTERMEDIATE": {
            "committed": 1.00,
            "econ_low": 1.00,
            "econ_high": 1.15,
            "peak": 2.20,
            "econ_low_share": 0.500,
            "pct_peaking": 6.0,
        },
        "COAL_LIGNITE": {
            "committed": 0.95,
            "econ_low": 1.14,
            "econ_high": 1.15,
            "peak": 1.55,
            "econ_low_share": 0.556,
        },
        "COAL_PRB": {
            "committed": 0.95,
            "econ_low": 0.70 if iso == "ERCOT" else 0.77,
            "econ_high": 0.94 if iso == "ERCOT" else 1.19,
            "peak": 1.48,
            "econ_low_share": 0.556,
        },
        "COAL_BIT": {
            "committed": 0.90,
            "econ_low": 0.95,
            "econ_high": 1.10,
            "peak": 1.45,
            "econ_low_share": 0.55,
        },
        "COAL_WC": {
            "committed": 0.85,
            "econ_low": 0.90,
            "econ_high": 1.02,
            "peak": 1.20,
            "econ_low_share": 0.55,
        },
        "COAL": {
            "committed": 0.90,
            "econ_low": 0.95,
            "econ_high": 1.10,
            "peak": 1.45,
            "econ_low_share": 0.55,
        },
    }


# Case-sensitivity legs ("ercot", "Pjm") pin the ternaries' raw comparison:
# a differently-cased ISO got — and must keep getting — the generic curve.
@pytest.mark.parametrize(
    "iso",
    [
        "ERCOT",
        "PJM",
        "CAISO",
        "MISO",
        "NYISO",
        "NEISO",
        "SPP",
        "SOCO",
        "ercot",
        "Pjm",
        "",
    ],
)
def test_base_curve_matches_frozen_inline(iso: str) -> None:
    assert base_offer_curve_by_group(iso) == _frozen_inline_curve(iso)


def test_returns_fresh_copies() -> None:
    a = base_offer_curve_by_group("ERCOT")
    a["CC_REGULAR"]["econ_low"] = 999.0
    assert base_offer_curve_by_group("ERCOT")["CC_REGULAR"]["econ_low"] == 1.16
    assert GENERIC_BASE_OFFER_CURVE["CC_REGULAR"]["econ_low"] == 1.06


def test_no_per_iso_values_in_generic() -> None:
    """Rule 25: a fitted per-ISO value never appears in the generic table."""
    for iso, deltas in BASE_OFFER_CURVE_DELTAS_BY_ISO.items():
        for group, bands in deltas.items():
            for band, value in bands.items():
                assert GENERIC_BASE_OFFER_CURVE[group][band] != value, (
                    f"{iso} delta {group}.{band}={value} equals the generic "
                    "value — a redundant delta row (or a fitted value leaked "
                    "into the generic table)"
                )
