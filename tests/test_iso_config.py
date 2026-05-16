"""Tests for ISO topology configurations."""

import pytest

from market_sim.config.iso_configs import get_iso_config


def test_ercot_has_four_zones():
    """ERCOT defines exactly four load zones."""
    ercot = get_iso_config("ERCOT")
    assert ercot.n_zones == 4


def test_ercot_load_shares_sum_to_one():
    """ERCOT zone load shares sum to 1.0."""
    ercot = get_iso_config("ERCOT")
    total = sum(zone.load_share for zone in ercot.zones)
    assert total == pytest.approx(1.0)


def test_caiso_has_two_zones():
    """CAISO defines one real load zone plus one import node."""
    caiso = get_iso_config("CAISO")
    assert caiso.n_zones == 2


def test_all_links_reference_valid_zones():
    """Every link endpoint references a defined zone in each ISO."""
    for iso_name in ("ERCOT", "CAISO"):
        config = get_iso_config(iso_name)
        valid = set(config.zone_names)
        for link in config.links:
            assert link.from_zone in valid
            assert link.to_zone in valid


def test_unknown_iso_raises_value_error():
    """Requesting an unsupported ISO raises ValueError."""
    with pytest.raises(ValueError):
        get_iso_config("PJM")


def test_caiso_voll_is_2000():
    """CAISO uses a VOLL of $2,000/MWh."""
    caiso = get_iso_config("CAISO")
    assert caiso.voll == 2000.0
