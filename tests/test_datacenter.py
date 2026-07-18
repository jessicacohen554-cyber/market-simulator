"""Tests for the data-center load block + electrification adder (CX-4, G-34).

Trivial-first (CLAUDE.md testing pattern): 1-zone / small-horizon arithmetic
checks, scaled up to the full ERCOT zone set. The block is forecast-mode-only and
default-off, so the single most important test is the off-path byte-identity
(zero blast radius on every existing run) — memo §6.1/§8.
"""

import numpy as np
import pytest

from market_sim.config.constants import (
    DATACENTER_ADDITIONS_MW,
    DATACENTER_ZONE_SHARE,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.datacenter import (
    add_datacenter_block,
    datacenter_block_mw_by_zone,
    datacenter_zone_shares,
    electrification_shape,
    resolve_datacenter_mw,
    validate_datacenter_config,
)


# --------------------------------------------------------------------------
# 1. Off-path byte-identity — the zero-blast-radius guarantee.
# --------------------------------------------------------------------------
def test_default_path_is_off():
    """The block ships default-off so every current run is unchanged."""
    assert ScenarioConfig().datacenter_load_path == "off"
    assert ScenarioConfig().datacenter_load_factor == 0.85


def test_off_path_resolves_zero():
    cfg = ScenarioConfig(iso="ERCOT", datacenter_load_path="off")
    assert resolve_datacenter_mw(cfg, "ERCOT", 2035) == 0.0


def test_off_path_add_is_identity_same_object():
    """add_datacenter_block returns the SAME array object when off (byte-identical)."""
    cfg = ScenarioConfig(iso="ERCOT", datacenter_load_path="off")
    zones = get_iso_config("ERCOT").zone_names
    demand = np.random.default_rng(0).random((len(zones), 24)) * 5e4
    out = add_datacenter_block(demand, cfg, "ERCOT", 2035, zones)
    assert out is demand  # not merely equal — the identical object


def test_off_path_identity_even_with_percentile_moved():
    """percentile is inert while the path is 'off'."""
    cfg = ScenarioConfig(
        iso="ERCOT", datacenter_load_path="off", datacenter_percentile=1.0
    )
    assert resolve_datacenter_mw(cfg, "ERCOT", 2035) == 0.0


# --------------------------------------------------------------------------
# 2. On-path additivity — closed-form energy/peak deltas (analytic, no solve).
# --------------------------------------------------------------------------
def test_on_path_additivity_closed_form():
    cfg = ScenarioConfig(iso="ERCOT", datacenter_load_path="mid")
    zones = get_iso_config("ERCOT").zone_names
    t = 24
    demand = np.zeros((len(zones), t))
    out = add_datacenter_block(demand, cfg, "ERCOT", 2030, zones)

    dc_mw = resolve_datacenter_mw(cfg, "ERCOT", 2030)  # 37,000 MW mid @2030
    block_mw = dc_mw * cfg.datacenter_load_factor  # 37000 * 0.85
    assert block_mw == pytest.approx(37000.0 * 0.85)

    # Flat block: every hour of every zone gets the same per-zone MW.
    per_zone = out[:, 0]
    assert np.allclose(out, per_zone[:, None])  # no hourly shape
    # ERCOT load_shares sum to 1.0 -> total added system MW == block_mw.
    assert out.sum(axis=0)[0] == pytest.approx(block_mw)
    # Closed form: ΔEnergy = block_mw * T ; Δpeak = block_mw (flat).
    assert out.sum() == pytest.approx(block_mw * t)
    assert out.sum(axis=0).max() == pytest.approx(block_mw)


def test_block_not_netted_from_renewables_is_pure_load_add():
    """The block is added to demand (RHS), not subtracted — it only ever raises load."""
    cfg = ScenarioConfig(iso="ERCOT", datacenter_load_path="high")
    zones = get_iso_config("ERCOT").zone_names
    demand = np.full((len(zones), 12), 1000.0)
    out = add_datacenter_block(demand, cfg, "ERCOT", 2030, zones)
    assert np.all(out >= demand)
    assert out.sum() > demand.sum()


# --------------------------------------------------------------------------
# 3. Zone shares — sum to 1.0, default == load_share, import nodes get 0.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("iso", ["ERCOT", "PJM", "CAISO", "NYISO"])
def test_default_zone_shares_sum_to_one(iso):
    zones = get_iso_config(iso).zone_names
    shares = datacenter_zone_shares(iso, zones)
    assert shares.sum() == pytest.approx(1.0, abs=1e-6)


def test_default_zone_shares_equal_load_share():
    iso_cfg = get_iso_config("ERCOT")
    zones = iso_cfg.zone_names
    shares = datacenter_zone_shares("ERCOT", zones)
    expected = np.array([z.load_share for z in iso_cfg.zones])
    assert np.allclose(shares, expected)


def test_import_node_zone_gets_zero_block():
    """CAISO WECC_import has load_share 0, so it receives no DC block."""
    cfg = ScenarioConfig(iso="CAISO", datacenter_load_path="mid")
    zones = get_iso_config("CAISO").zone_names
    per_zone = datacenter_block_mw_by_zone(cfg, "CAISO", 2040, zones)
    idx = zones.index("WECC_import")
    assert per_zone[idx] == 0.0


def test_zone_share_default_table_is_empty():
    """No published siting override ships; every ISO uses its load_share default."""
    assert DATACENTER_ZONE_SHARE == {}


# --------------------------------------------------------------------------
# 4. resolve_datacenter_mw — year + percentile interpolation vs hand-computed.
# --------------------------------------------------------------------------
def test_resolve_at_anchor_years():
    cfg = ScenarioConfig(iso="ERCOT", datacenter_load_path="high")
    # high ERCOT: {2024:0, 2030:122000, 2035:158000}
    assert resolve_datacenter_mw(cfg, "ERCOT", 2024) == pytest.approx(0.0)
    assert resolve_datacenter_mw(cfg, "ERCOT", 2030) == pytest.approx(122000.0)
    assert resolve_datacenter_mw(cfg, "ERCOT", 2035) == pytest.approx(158000.0)


def test_resolve_between_anchors_linear():
    cfg = ScenarioConfig(iso="ERCOT", datacenter_load_path="high")
    # 2033 sits 3/5 of the way from 2030(122000) to 2035(158000).
    expected = 122000.0 + (158000.0 - 122000.0) * (3.0 / 5.0)
    assert resolve_datacenter_mw(cfg, "ERCOT", 2033) == pytest.approx(expected)


def test_resolve_flat_extrapolation_after_last_anchor():
    cfg = ScenarioConfig(iso="ERCOT", datacenter_load_path="mid")
    # mid ERCOT {2024:0, 2030:37000} -> flat 37000 past 2030.
    assert resolve_datacenter_mw(cfg, "ERCOT", 2045) == pytest.approx(37000.0)


def test_percentile_reproduces_low_mid_high():
    zones_year = 2030
    low_cfg = ScenarioConfig(
        iso="ERCOT", datacenter_load_path="mid", datacenter_percentile=0.0
    )
    mid_cfg = ScenarioConfig(
        iso="ERCOT", datacenter_load_path="mid", datacenter_percentile=0.5
    )
    high_cfg = ScenarioConfig(
        iso="ERCOT", datacenter_load_path="mid", datacenter_percentile=1.0
    )
    assert resolve_datacenter_mw(low_cfg, "ERCOT", zones_year) == pytest.approx(0.0)
    assert resolve_datacenter_mw(mid_cfg, "ERCOT", zones_year) == pytest.approx(37000.0)
    assert resolve_datacenter_mw(high_cfg, "ERCOT", zones_year) == pytest.approx(
        122000.0
    )


def test_percentile_midpoint_interpolation():
    """percentile 0.25 sits halfway between low(0) and mid(37000)."""
    cfg = ScenarioConfig(
        iso="ERCOT", datacenter_load_path="mid", datacenter_percentile=0.25
    )
    assert resolve_datacenter_mw(cfg, "ERCOT", 2030) == pytest.approx(18500.0)


def test_path_label_selects_case():
    """The discrete path label picks low/mid/high at the neutral 0.5 percentile."""
    y = 2030
    assert resolve_datacenter_mw(
        ScenarioConfig(iso="ERCOT", datacenter_load_path="low"), "ERCOT", y
    ) == pytest.approx(0.0)
    assert resolve_datacenter_mw(
        ScenarioConfig(iso="ERCOT", datacenter_load_path="high"), "ERCOT", y
    ) == pytest.approx(122000.0)


# --------------------------------------------------------------------------
# 5. Per-ISO parameterization — sourced ISOs vs the "no source => 0" rule.
# --------------------------------------------------------------------------
def test_caiso_iepr_anchors():
    cfg = ScenarioConfig(iso="CAISO", datacenter_load_path="mid")
    assert resolve_datacenter_mw(cfg, "CAISO", 2030) == pytest.approx(1800.0)
    assert resolve_datacenter_mw(cfg, "CAISO", 2040) == pytest.approx(4900.0)


def test_pjm_and_nyiso_have_sourced_blocks():
    assert resolve_datacenter_mw(
        ScenarioConfig(iso="PJM", datacenter_load_path="mid"), "PJM", 2030
    ) == pytest.approx(30000.0)
    assert resolve_datacenter_mw(
        ScenarioConfig(iso="NYISO", datacenter_load_path="high"), "NYISO", 2031
    ) == pytest.approx(10000.0)


def test_neiso_ships_zero():
    """NEISO's 2026-CELT large-load quantum (~110 MW) is immaterial -> ships {}
    (FF-1C / FF-0D §1.4): 0 MW on every path until the CELT table (M6) lands."""
    assert DATACENTER_ADDITIONS_MW["NEISO"] == {}
    for path in ("low", "mid", "high"):
        cfg = ScenarioConfig(iso="NEISO", datacenter_load_path=path)
        assert resolve_datacenter_mw(cfg, "NEISO", 2030) == 0.0


def test_miso_has_sourced_block():
    """MISO gained a sourced DC block (FF-1C) from its 2025 LTLF (8-14 GW in
    2026-2027; ~20% of energy by 2030). low = 0 floor; mid ~18 GW / high ~25 GW
    by 2030; the 2027 anchor is the 8-14 GW committed range."""
    assert DATACENTER_ADDITIONS_MW["MISO"] != {}
    assert resolve_datacenter_mw(
        ScenarioConfig(iso="MISO", datacenter_load_path="mid"), "MISO", 2030
    ) == pytest.approx(18000.0)
    assert resolve_datacenter_mw(
        ScenarioConfig(iso="MISO", datacenter_load_path="high"), "MISO", 2027
    ) == pytest.approx(14000.0)
    # low path is the honest 0 floor (no signed-IA subset published).
    assert (
        resolve_datacenter_mw(
            ScenarioConfig(iso="MISO", datacenter_load_path="low"), "MISO", 2030
        )
        == 0.0
    )
    # Default "off" is a no-op regardless of the sourced block.
    assert resolve_datacenter_mw(ScenarioConfig(iso="MISO"), "MISO", 2030) == 0.0


def test_unknown_iso_ships_zero():
    cfg = ScenarioConfig(iso="ERCOT", datacenter_load_path="mid")
    assert resolve_datacenter_mw(cfg, "NOT_AN_ISO", 2030) == 0.0


# --------------------------------------------------------------------------
# 6. Backcast guard — the block must never enter a scored backcast (rule 22).
# --------------------------------------------------------------------------
def test_backcast_with_nonoff_path_raises_at_construction():
    with pytest.raises(ValueError, match="forecast-only"):
        ScenarioConfig(iso="ERCOT", mode="backcast", datacenter_load_path="mid")


def test_backcast_with_off_path_is_fine():
    cfg = ScenarioConfig(iso="ERCOT", mode="backcast", datacenter_load_path="off")
    assert cfg.mode == "backcast"
    validate_datacenter_config(cfg)  # no raise


def test_validate_datacenter_config_rejects_backcast():
    cfg = ScenarioConfig(iso="ERCOT", mode="forecast", datacenter_load_path="mid")
    # Mutate past the constructor guard to exercise the standalone validator.
    object.__setattr__(cfg, "mode", "backcast")
    with pytest.raises(ValueError, match="forecast-only"):
        validate_datacenter_config(cfg)


def test_unknown_path_label_raises():
    with pytest.raises(ValueError, match="datacenter_load_path"):
        ScenarioConfig(iso="ERCOT", datacenter_load_path="bogus")


# --------------------------------------------------------------------------
# 7. Electrification adder — deferred interface returns a zero (no-op) profile.
# --------------------------------------------------------------------------
def test_electrification_shape_is_zero_stub():
    cfg = ScenarioConfig(iso="ERCOT")
    prof = electrification_shape(cfg, "ERCOT", 2035, 8760)
    assert prof.shape == (8760,)
    assert not prof.any()
