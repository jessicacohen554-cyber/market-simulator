"""Tests for ``ScenarioConfig.nwpp_path76_alturas_link`` (NWPP-NEXT-6).

The gated WECC Path 76 "Alturas Project" link, NWPP-NW <-> NWPP-SNV. Pins the
off-path identity (same object, same cache key), the armed topology (one
bidirectional 300 MW link, the catalogue rating) and the ISO scope.
"""

from __future__ import annotations

from market_sim.config.iso_configs import (
    NWPP_PATH76_ALTURAS_TTC_MW,
    get_iso_config,
    nwpp_path76_alturas_links,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.pipeline.ttc import apply_nwpp_path76_link


def test_off_returns_same_object():
    """Default off: the applier returns the identical ISOConfig."""
    ic = get_iso_config("NWPP")
    assert apply_nwpp_path76_link(ic, "NWPP", ScenarioConfig()) is ic


def test_other_iso_untouched_when_armed():
    """Armed on a non-NWPP ISO: no-op."""
    ic = get_iso_config("PJM")
    cfg = ScenarioConfig(nwpp_path76_alturas_link=True)
    assert apply_nwpp_path76_link(ic, "PJM", cfg) is ic


def test_armed_appends_one_nw_snv_link():
    """Armed: exactly one bidirectional NW<->SNV link at the catalogue rating."""
    ic = get_iso_config("NWPP")
    cfg = ScenarioConfig(nwpp_path76_alturas_link=True)
    out = apply_nwpp_path76_link(ic, "NWPP", cfg)
    assert len(out.links) == len(ic.links) + 1
    assert list(out.links[: len(ic.links)]) == list(ic.links)
    link = out.links[-1]
    assert (link.from_zone, link.to_zone) == ("NWPP-NW", "NWPP-SNV")
    assert link.is_bidirectional
    assert link.ttc_mw == NWPP_PATH76_ALTURAS_TTC_MW == 300.0
    assert link.flow_cost == 0.0
    # The static topology carries no NW<->SNV link of its own.
    pairs = {frozenset((l.from_zone, l.to_zone)) for l in ic.links}
    assert frozenset(("NWPP-NW", "NWPP-SNV")) not in pairs
    assert len(nwpp_path76_alturas_links()) == 1


def test_cache_key_default_dropped_and_armed_distinct():
    """Registered at its default: off keeps the key, armed earns a new one."""
    base = ScenarioConfig()
    assert (
        base.cache_key() == ScenarioConfig(nwpp_path76_alturas_link=False).cache_key()
    )
    assert base.cache_key() != ScenarioConfig(nwpp_path76_alturas_link=True).cache_key()
