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
    invert_normalized_curve,
    invert_own_curve,
    is_locked,
    miso_seasonal_pass1,
    model_curve_price_kw_yr,
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


def test_invert_normalized_curve_round_trips():
    # Inverting the MISO summer curve at a fraction recovers a position whose
    # forward evaluation returns that fraction (clamped past both ends).
    from market_sim.config.constants import (
        MISO_SEASONAL_RBDC,
        evaluate_demand_curve,
    )

    summer = MISO_SEASONAL_RBDC.seasons[0].demand_curve
    for frac in (0.5, 1.0, 2.0, 4.0):
        pos = invert_normalized_curve(summer, frac)
        assert evaluate_demand_curve(summer, pos) == pytest.approx(frac, abs=1e-6)


def test_miso_seasonal_pass1_reproduces_net_cone_and_concentration():
    # RC-1C: the seasonal SUM (Σ cleared × days) lands on the published
    # North/Central net-CONE (~79,800), and the per-season implied positions
    # reproduce the summer-short / other-seasons-long concentration directionally.
    mp = miso_seasonal_pass1()
    assert not mp["locked"]  # PY2025-26 is in-train
    assert mp["published_net_cone_mw_yr"] == pytest.approx(79_800.0, abs=1.0)
    # Annual sum within a few percent of net-CONE (a real reproduction).
    assert abs(mp["pct_error"]) < 3.0
    by_season = {s["season"]: s for s in mp["seasons"]}
    assert by_season["summer"]["implied_reserve_position"] < 1.0  # short
    for season in ("fall", "winter", "spring"):
        assert by_season[season]["implied_reserve_position"] > 1.0  # long
    # Summer's gross-CONE cap fraction is ~6.3× the flat daily net-CONE.
    assert by_season["summer"]["model_cap_frac"] == pytest.approx(6.33, abs=0.05)


def test_nyiso_scored_per_vintage_and_sparse_years_excluded():
    # NYISO Pass 1B (RC-1C): 2023/24 & 2024/25 score on their OWN vintage anchor
    # (model net-CONE == published net-CONE per year, shape resid ~0); the sparse
    # 2021-22/2022-23 (no ARV/cap) are non-scoreable with no interpolation;
    # 2025/26 is locked.
    rows = {r.delivery_year: r for r in run_pass1("NYISO")}
    scored = ("2023/2024", "2024/2025")
    for y in scored:
        r = rows[y]
        assert not r.locked
        # per-vintage anchor: the model net-CONE tracks each year's published ARV
        assert r.model_net_cone_kw_yr == pytest.approx(r.pub_net_cone_kw_yr, abs=0.01)
        assert abs(r.shape_resid_pct) < 0.5  # instrument faithful per vintage
        assert abs(r.pct_error) < 1.0  # price reproduced at its own position
    # The 2024/25 and 2023/24 anchors DIFFER (no frozen single-vintage anchor).
    assert rows["2023/2024"].model_net_cone_kw_yr != pytest.approx(
        rows["2024/2025"].model_net_cone_kw_yr, abs=0.5
    )
    # Sparse pre-ARV years carry no curve params (explicit, not interpolated).
    for y in ("2021/2022", "2022/2023"):
        assert rows[y].pub_net_cone_kw_yr is None
        assert rows[y].reserve_position is None
    assert rows["2025/2026"].locked is True


def test_nyiso_flat_anchor_vintage_prices_flat():
    # A NYISO ()-shape flat-anchor vintage (2021-2022: reference price × 12, no
    # curve) prices its flat anchor independent of position through the shipped
    # vintage seam.
    flat = model_curve_price_kw_yr("NYISO", 0.8, year=2021)
    assert model_curve_price_kw_yr("NYISO", 1.3, year=2021) == pytest.approx(flat)
    assert flat == pytest.approx(7.81 * 12.0, abs=0.01)
