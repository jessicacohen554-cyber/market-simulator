"""FFR-4F — CAISO RA-MPB capacity-price anchor (gated default-OFF).

Pins the four properties the mechanism's charter rests on:

* the gate is **byte-inert off** — CAISO still prices the shipped CPM
  soft-offer-cap anchor, so no keeper can move (the keeper guard, held by
  construction rather than by measurement);
* armed, CAISO prices the CPUC unified RA Market Price Benchmark;
* armed, **no other ISO moves** (rule 25 ``[R-ISO-SCOPE]``);
* the constant cannot drift from its committed published source (rule 23
  ``[R-FROZEN-DERIVE]``: the re-derivation licence is the CPUC's own
  re-publication, never a residual).

This is NOT a row-4 fix and nothing here scores FC-2; see
``docs/handoffs/ffr-4f-caiso-anchor-merits-2026-08-09.md``.
"""

from __future__ import annotations

import csv

import pytest

from market_sim.config.capacity_market import (
    CAISO_RA_MPB_ANCHOR_PER_KW_YR,
    DEFAULT_MARKET_DESIGN,
    MARKET_DESIGN,
    resolve_caiso_ra_mpb_anchor,
)
from market_sim.config.paths import RAW_DIR
from market_sim.config.scenarios import ScenarioConfig

_CAISO_SOFT_OFFER_CAP_ANCHOR_PER_KW_YR = 88.08  # the shipped (mis-specified) anchor
_SOURCE_CSV = RAW_DIR / "capacity-market" / "demand-curve" / "caiso" / "caiso.csv"


def _price(iso: str, config: ScenarioConfig) -> float:
    """Price one ISO's firm MW through the ONE shared seam (rule 19)."""
    design = MARKET_DESIGN.get(iso, DEFAULT_MARKET_DESIGN)
    return design.capacity_price_per_firm_mw_yr(config, None, iso=iso)


def test_gate_off_is_byte_identical_caiso_keeper_guard() -> None:
    """Unarmed CAISO prices the shipped anchor exactly — the keeper guard."""
    assert _price("CAISO", ScenarioConfig()) == pytest.approx(
        _CAISO_SOFT_OFFER_CAP_ANCHOR_PER_KW_YR * 1000.0
    )


def test_gate_on_prices_the_published_ra_mpb() -> None:
    config = ScenarioConfig(caiso_ra_mpb_capacity_anchor=True)
    assert _price("CAISO", config) == pytest.approx(
        CAISO_RA_MPB_ANCHOR_PER_KW_YR * 1000.0
    )


@pytest.mark.parametrize("iso", ["ERCOT", "PJM", "NYISO", "NEISO", "MISO"])
def test_arming_caiso_moves_no_other_iso(iso: str) -> None:
    """Rule 25 [R-ISO-SCOPE]: the anchor is CAISO's and crosses no boundary."""
    off = _price(iso, ScenarioConfig())
    on = _price(iso, ScenarioConfig(caiso_ra_mpb_capacity_anchor=True))
    assert on == pytest.approx(off)


def test_resolver_is_caiso_only_and_unarmed_by_default() -> None:
    armed = ScenarioConfig(caiso_ra_mpb_capacity_anchor=True)
    assert resolve_caiso_ra_mpb_anchor(ScenarioConfig(), "CAISO") is None
    assert resolve_caiso_ra_mpb_anchor(armed, "CAISO") == CAISO_RA_MPB_ANCHOR_PER_KW_YR
    for iso in ("ERCOT", "PJM", "NYISO", "NEISO", "MISO", None):
        assert resolve_caiso_ra_mpb_anchor(armed, iso) is None
    # A None config (and a config predating the field) resolves unarmed.
    assert resolve_caiso_ra_mpb_anchor(None, "CAISO") is None
    assert resolve_caiso_ra_mpb_anchor(object(), "CAISO") is None


def test_anchor_matches_committed_published_source() -> None:
    """Rule 23: the constant is its published source x 12, or the test fails.

    Guards against the constant and the intaken CSV drifting apart silently —
    the failure mode that let a going-forward-cost ceiling sit in the
    new-entry-price slot unnoticed in the first place.
    """
    with _SOURCE_CSV.open(newline="", encoding="utf-8") as fh:
        rows = [
            r
            for r in csv.DictReader(fh)
            if r["metric"] == "ra_mpb" and r["delivery_year"] == "2026"
        ]
    assert len(rows) == 1, "expected exactly one 2026 unified RA MPB row"
    (row,) = rows
    assert row["area"] == "unified"
    assert row["y_unit"] == "usd_per_kw_month"
    assert CAISO_RA_MPB_ANCHOR_PER_KW_YR == pytest.approx(float(row["y_value"]) * 12.0)


def test_gate_reaches_the_thermal_screens_on_the_shared_seam() -> None:
    """Rule 19: the screens price through the seam, so they move WITH the gate.

    The unarmed CAISO ``gas_ct`` value also reproduces FFR-3W §1.2's measured
    capacity column ($82,795/MW-yr) to the dollar, which is what identifies
    this seam as the one that lane decomposed.
    """
    from market_sim.config.constants import EFORD
    from market_sim.model.capacity_evolution.retirements import (
        capacity_revenue_per_mw_yr,
    )

    def _rev(iso: str, config: ScenarioConfig) -> float:
        return capacity_revenue_per_mw_yr(iso, "gas_ct", EFORD["gas_ct"], config, None)

    off = _rev("CAISO", ScenarioConfig())
    on = _rev("CAISO", ScenarioConfig(caiso_ra_mpb_capacity_anchor=True))
    assert off == pytest.approx(
        _CAISO_SOFT_OFFER_CAP_ANCHOR_PER_KW_YR * 1000.0 * (1.0 - EFORD["gas_ct"])
    )
    assert off == pytest.approx(82_795.2, abs=0.1)  # FFR-3W §1.2, to the dollar
    assert on == pytest.approx(
        CAISO_RA_MPB_ANCHOR_PER_KW_YR * 1000.0 * (1.0 - EFORD["gas_ct"])
    )
    # ...and no other capacity-market ISO's screen moves (rule 25).
    for iso in ("PJM", "NYISO", "NEISO", "MISO", "ERCOT"):
        assert _rev(iso, ScenarioConfig(caiso_ra_mpb_capacity_anchor=True)) == (
            pytest.approx(_rev(iso, ScenarioConfig()))
        )


def test_armed_run_keys_distinctly_and_default_key_is_unmoved() -> None:
    """Registered at False: the pinned default key holds; armed hashes apart."""
    default = ScenarioConfig()
    armed = ScenarioConfig(caiso_ra_mpb_capacity_anchor=True)
    assert default.cache_key() == "4c6b03ae098b6e3e"
    assert armed.cache_key() != default.cache_key()
