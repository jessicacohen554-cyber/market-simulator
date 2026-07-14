"""Tests for the CR-2 capacity-price validation tool (scripts/validate_capacity_prices).

Trivial-first (rule: test trivial cases first): unit conversions, curve inversion,
locked-window governance, and the two structural invariants the tool must never
silently break — the normalized SHAPE is reproduced exactly at a published cap
point, and locked (H1-2026 forward-edge) rows are excluded from verdicts.
"""

from __future__ import annotations


import pytest

from scripts.validate_capacity_prices import (
    YearParams,
    canon_year,
    delivery_start_year,
    invert_own_curve,
    is_locked,
    run_pass1,
    run_pass2,
    to_kw_yr,
)


def test_unit_conversions():
    assert to_kw_yr(365.0, "usd_per_mw_day") == pytest.approx(133.225)
    assert to_kw_yr(1.0, "usd_per_kw_month") == pytest.approx(12.0)
    assert to_kw_yr(50.55, "usd_per_kw_yr") == pytest.approx(50.55)
    assert to_kw_yr(60396.0, "usd_per_mw_yr") == pytest.approx(60.396)
    with pytest.raises(ValueError):
        to_kw_yr(1.0, "bogus_unit")


def test_delivery_year_parsing_and_canon():
    assert delivery_start_year("2025/2026") == 2025
    assert delivery_start_year("2020/21") == 2020
    assert delivery_start_year("2025-2026") == 2025
    # '2025/26', '2025-2026', '2025/2026' must all collapse to one key.
    assert canon_year("2025/26") == canon_year("2025-2026") == "2025/2026"


def test_locked_window_governance():
    # Forward-edge delivery years (2026+) are locked (rule 22).
    assert is_locked("PJM", "2026/2027", "any") is True
    assert is_locked("NEISO", "2026-2027", "any") is True
    # In-train delivery years are scored.
    assert is_locked("PJM", "2025/2026", "BRA report 2024-07-30") is False
    # NYISO 2025/26 spot is a 2026-published SOM observation -> locked.
    assert is_locked("NYISO", "2025/26", "2025 SOM Report, pub. 2026-05-19") is True
    assert is_locked("NYISO", "2024/25", "2024 SOM Report, pub. 2025-05-14") is False


def test_invert_own_curve_monotone_and_anchored():
    # A simple curve: cap 1.5x net-CONE at pos 0.99, net-CONE at 1.015, zero at 1.045.
    p = YearParams(
        net_cone_kw_yr=100.0,
        net_cone_ucap_kw_yr=100.0,
        price_cap_kw_yr=150.0,
        ref_x=1.015,
        cap_x=0.99,
        zero_x=1.045,
        cap_frac_source="published",
    )
    # At net-CONE the position is the reference; at/above cap it clamps to cap_x;
    # at/below zero it clamps to zero_x.
    assert invert_own_curve(p, 100.0) == pytest.approx(1.015)
    assert invert_own_curve(p, 200.0) == pytest.approx(0.99)  # above cap -> plateau
    assert invert_own_curve(p, 0.0) == pytest.approx(1.045)  # zero -> zero-cross
    # Monotone: a higher price maps to a tighter (smaller) reserve position.
    assert invert_own_curve(p, 130.0) < invert_own_curve(p, 110.0)


def test_neiso_shape_reproduced_exactly():
    # ISO-NE's published starting-price/net-CONE ratio is a constant 1.600 for
    # 2020/21-2024/25, which the implemented curve's cap fraction must reproduce
    # with ~zero shape residual; 2025/26 legitimately publishes 1.660 (a ~3.6%
    # data deviation, not a tool bug), so the general bound is a loose one.
    scored = [r for r in run_pass1("NEISO") if not r.locked and r.pub_cap_frac]
    assert scored, "expected scored NEISO years"
    for r in scored:
        assert abs(r.shape_resid_pct) < 5.0, (r.delivery_year, r.shape_resid_pct)
    exact = [r for r in scored if delivery_start_year(r.delivery_year) <= 2024]
    assert exact, "expected constant-ratio NEISO years"
    for r in exact:
        assert abs(r.shape_resid_pct) < 0.5, (r.delivery_year, r.shape_resid_pct)


def test_pjm_pass2_position_is_long_and_pays_zero():
    # Post-P-2B-migration (R1-R4): the PJM accredited position collapsed from
    # 1.29-1.36 to ~1.06-1.15 as the supply ledger re-bases onto the published
    # ELCC class ratings (R3) and the requirement onto the published FPR (R2),
    # but it still sits PAST the curve's ~1.045 zero-cross, so CR-1 ON still
    # pays $0 — the remaining excess is the retirement miss (G-30/G-31 lane),
    # NOT the accreditation basis. The curve stays gated off.
    rows = run_pass2("PJM")
    assert rows, "expected a PJM hindcast"
    for r in rows:
        assert 1.045 < r.reserve_position < 1.2  # still long, but no longer 1.3+
        assert r.model_price_kw_yr == pytest.approx(0.0, abs=1e-6)


def test_no_locked_row_is_ever_scored_without_flag():
    # Every locked row must carry the locked flag so rendering greys/excludes it.
    for iso in ("PJM", "NYISO", "NEISO", "MISO"):
        for r in run_pass1(iso):
            if delivery_start_year(r.delivery_year) >= 2026:
                assert r.locked is True
