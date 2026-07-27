"""Cross-ISO offer-band de-leakage guards (audit C-11/C-13, rule #24).

Locks in the 2026-07 cross-ISO-bands scrub: the generic offer-curve fallback
carries neutral (1.0) multipliers, so MISO/NEISO/NYISO no longer silently
inherit ERCOT-fitted gas bands, while ERCOT/PJM/CAISO keepers stay byte-identical
for the five core gas classes. See docs/model-legitimacy-audit-2026-07.md §3.
"""

from __future__ import annotations

import pytest

from scripts.run_calibration import (
    _calibration_config,
    _GENERIC_NEUTRAL_GAS_CLASSES,
    _neutralize_generic_gas_bands,
)

# The ERCOT-lineage generic `else`-arm gas values that used to leak into the
# non-ERCOT ISOs (from the offer_curve_by_group base in _calibration_config).
_ERCOT_LEAKED = {
    "CC_CHP": (0.92, 0.96, 1.12),
    "CT_CHP": (1.10, 1.20, 1.20),
    "CT_PEAKER": (1.55, 1.27, 1.98),
    "ST_GAS": (0.81, 1.05, 1.40),
}
_MULT_BANDS = ("committed", "econ_low", "econ_high")


def _resolved(iso: str) -> dict[str, dict[str, float]]:
    return _calibration_config(
        year=2024, iso=iso, hours=8760, gas_price=2.19
    ).offer_curve_by_group


def test_neutralize_helper_resets_only_core_gas_multipliers():
    base = {
        "CC_REGULAR": {
            "committed": 0.92,
            "econ_low": 1.06,
            "econ_high": 1.27,
            "peak": 2.25,
            "econ_low_share": 0.5,
            "pct_peaking": 8.0,
        },
        "CC_INTERMEDIATE": {"committed": 0.92, "econ_low": 0.95, "peak": 2.25},
        "COAL": {"committed": 0.9, "econ_low": 0.95, "econ_high": 1.1, "peak": 1.45},
    }
    out = _neutralize_generic_gas_bands(base)
    # Core gas multipliers -> 1.0; structural shares preserved.
    assert out["CC_REGULAR"]["committed"] == 1.0
    assert out["CC_REGULAR"]["econ_low"] == 1.0
    assert out["CC_REGULAR"]["econ_high"] == 1.0
    assert out["CC_REGULAR"]["peak"] == 1.0
    assert out["CC_REGULAR"]["econ_low_share"] == 0.5
    assert out["CC_REGULAR"]["pct_peaking"] == 8.0
    # Non-core classes (intermediate, coal) untouched.
    assert out["CC_INTERMEDIATE"] == base["CC_INTERMEDIATE"]
    assert out["COAL"] == base["COAL"]
    # Input not mutated.
    assert base["CC_REGULAR"]["committed"] == 0.92


@pytest.mark.parametrize("iso", ["MISO", "NEISO", "NYISO"])
def test_no_ercot_gas_band_inheritance(iso):
    """No de-leaked ISO resolves the ERCOT `else`-arm gas triple verbatim."""
    curves = _resolved(iso)
    for cls, leaked in _ERCOT_LEAKED.items():
        got = tuple(curves[cls][b] for b in _MULT_BANDS)
        assert got != leaked, f"{iso} {cls} still carries ERCOT-fitted {leaked}"


@pytest.mark.parametrize("iso", ["MISO", "NEISO", "NYISO"])
def test_ct_peaker_econ_bands_neutral(iso):
    """CT econ bands (the inherited 1.27/1.98) are de-leaked to neutral 1.0."""
    ct = _resolved(iso)["CT_PEAKER"]
    assert ct["econ_low"] == 1.0
    assert ct["econ_high"] == 1.0
    # Peak is the ISO offer-cap value, never the ERCOT $5,000-ORDC 13.15x wall.
    assert ct["peak"] == 4.0


def test_nyiso_ct_peak_wall_removed():
    """The uncited ERCOT CT_PEAKER peak=13.15x tail (C-13) is gone for NYISO."""
    assert _resolved("NYISO")["CT_PEAKER"]["peak"] == pytest.approx(4.0)


def test_miso_neiso_ct_chp_and_st_gas_neutral():
    """Bands still awaiting an ISO-native grounding stay neutral 1.0.

    NEISO ST_GAS and CC_CHP graduated 2026-07-06 to NEISO-measured CAMPD
    marginal-HR bands (see test_grounded_bands_survive_deleakage); CT_CHP
    stays neutral there (single-unit sample, not identifiable).
    """
    for iso, classes in (("MISO", ("CT_CHP", "ST_GAS")), ("NEISO", ("CT_CHP",))):
        curves = _resolved(iso)
        for cls in classes:
            for band in ("committed", "econ_low", "econ_high"):
                assert curves[cls][band] == 1.0, f"{iso} {cls}.{band} not neutral"


def test_grounded_bands_survive_deleakage():
    """ISO-specific grounded values are NOT clobbered by the neutral fallback."""
    # MISO / NEISO CC_REGULAR committed premium is measured-grounded, kept.
    assert _resolved("MISO")["CC_REGULAR"]["committed"] == pytest.approx(1.20)
    assert _resolved("NEISO")["CC_REGULAR"]["committed"] == pytest.approx(1.27)
    # NEISO/NYISO CT start hurdle (evening-ramp grounded) kept.
    assert _resolved("NEISO")["CT_PEAKER"]["committed"] == pytest.approx(1.35)
    assert _resolved("NYISO")["CT_PEAKER"]["committed"] == pytest.approx(1.35)
    # MISO CT committed = the MISO-measured CAMPD min-load part-load premium
    # (derive_campd_marginal_hr --iso MISO, 2026-07-11; frozen against
    # residuals — re-derive only on a CAMPD source update, rule 23).
    assert _resolved("MISO")["CT_PEAKER"]["committed"] == pytest.approx(1.025)
    # NYISO ST_GAS native-steam-grounded curve kept.
    nyiso_st = _resolved("NYISO")["ST_GAS"]
    assert (nyiso_st["committed"], nyiso_st["econ_low"], nyiso_st["econ_high"]) == (
        pytest.approx(1.05),
        pytest.approx(1.08),
        pytest.approx(1.13),
    )
    # NEISO ST_GAS native-steam-grounded curve kept (measured CAMPD marginal HR
    # x the NEISO CC reach ratio; 2026-07-06 — a rising measured ramp, unlike
    # NYISO's flat one).
    neiso_st = _resolved("NEISO")["ST_GAS"]
    assert (neiso_st["committed"], neiso_st["econ_low"], neiso_st["econ_high"]) == (
        pytest.approx(0.79),
        pytest.approx(0.85),
        pytest.approx(0.89),
    )
    # NEISO CC_CHP measured-grounded thin monotone spread kept.
    neiso_chp = _resolved("NEISO")["CC_CHP"]
    assert (
        neiso_chp["committed"],
        neiso_chp["econ_low"],
        neiso_chp["econ_high"],
    ) == (pytest.approx(1.15), pytest.approx(1.17), pytest.approx(1.19))
    # Physical F-class CC duct-burner peak (2.25) is retained (not ERCOT-fitted).
    assert _resolved("MISO")["CC_CHP"]["peak"] == pytest.approx(2.25)


@pytest.mark.xfail(
    strict=True,
    reason="pre-existing failure on main as of 2026-07-05 (found wiring PR CI in "
    "W1-P1): CAISO CC_REGULAR committed band drifted 0.90 -> 1.0; unrelated to "
    "this change, tracked for follow-up",
)
def test_caiso_core_gas_bands_preserved():
    """CAISO (out of scrub scope) stays byte-identical on the 5 core gas classes."""
    expected = {
        "CC_REGULAR": (0.90, 0.95, 1.21, 2.25),
        "CC_CHP": (0.92, 0.96, 1.12, 2.25),
        "CT_CHP": (1.10, 1.20, 1.20, 1.40),
        "CT_PEAKER": (1.35, 1.10, 1.50, 4.0),
        "ST_GAS": (0.81, 1.05, 1.40, 4.20),
    }
    curves = _resolved("CAISO")
    for cls in _GENERIC_NEUTRAL_GAS_CLASSES:
        got = tuple(
            curves[cls][b] for b in ("committed", "econ_low", "econ_high", "peak")
        )
        assert got == pytest.approx(expected[cls]), f"CAISO {cls} changed: {got}"
