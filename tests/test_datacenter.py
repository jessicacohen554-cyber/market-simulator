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
def test_default_path_is_mid_forecast_posture():
    """FF-1F (owner, 2026-07-18): the forecast-posture default is 'mid'.

    A bare forecast config models the published DC boom as a flat block; the
    axis is coerced back to 'off' in any non-forward run (see the backcast /
    hindcast coercion tests below), so keepers stay byte-identical.
    """
    assert ScenarioConfig().datacenter_load_path == "mid"
    assert ScenarioConfig().mode == "forecast"
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
# 2. On-path RELOCATION — energy-invariant double-count fix (FF-1C / CX-4 §3.5).
#    The near-era DEMAND_GROWTH_RATES are DC-inclusive, so the block relocates
#    (scale peaky demand down by its energy fraction, add back flat) rather than
#    naively adding — total energy invariant, peak flattens. Analytic, no solve.
# --------------------------------------------------------------------------
def test_on_path_relocation_energy_invariant_closed_form():
    cfg = ScenarioConfig(iso="ERCOT", datacenter_load_path="mid")
    zones = get_iso_config("ERCOT").zone_names
    t = 24
    # Peaky demand whose energy comfortably contains the block (relocate regime).
    rng = np.random.default_rng(1)
    demand = rng.random((len(zones), t)) * 6e4 + 2e4
    out = add_datacenter_block(demand, cfg, "ERCOT", 2030, zones)

    dc_mw = resolve_datacenter_mw(cfg, "ERCOT", 2030)  # 37,000 MW mid @2030
    block_mw = dc_mw * cfg.datacenter_load_factor  # 37000 * 0.85
    assert block_mw == pytest.approx(37000.0 * 0.85)

    dc_energy = block_mw * t
    total_energy = float(demand.sum())
    assert dc_energy < total_energy  # relocate regime, not tail-add
    scale = 1.0 - dc_energy / total_energy

    # Closed form: out = demand*scale + flat_block; energy is INVARIANT.
    per_zone = datacenter_block_mw_by_zone(cfg, "ERCOT", 2030, zones)
    assert np.allclose(out, demand * scale + per_zone[:, None])
    assert out.sum() == pytest.approx(total_energy)  # <-- double-count removed
    # Peak flattens: new peak == base_peak*scale + block_mw < base_peak + block_mw.
    base_peak = float(demand.sum(axis=0).max())
    assert out.sum(axis=0).max() == pytest.approx(base_peak * scale + block_mw)
    assert out.sum(axis=0).max() < base_peak + block_mw


def test_tail_regime_adds_when_block_exceeds_total():
    """When the block's energy exceeds the demand's, it is incremental load
    (added, not relocated) — the full-queue tail (FF-1C add_datacenter_block)."""
    cfg = ScenarioConfig(iso="ERCOT", datacenter_load_path="high")
    zones = get_iso_config("ERCOT").zone_names
    # A tiny demand the ERCOT-high 2035 block (158 GW * 0.85) dwarfs.
    demand = np.full((len(zones), 12), 100.0)
    out = add_datacenter_block(demand, cfg, "ERCOT", 2035, zones)
    block_mw = resolve_datacenter_mw(cfg, "ERCOT", 2035) * cfg.datacenter_load_factor
    assert out.sum() == pytest.approx(demand.sum() + block_mw * 12)  # added on top
    assert np.all(out >= demand)  # never subtracted from load


def test_block_is_load_side_not_netted_from_renewables():
    """The block acts on demand (RHS), never as a renewable credit. In the
    relocate regime total load is held (energy invariant); it is never negative."""
    cfg = ScenarioConfig(iso="ERCOT", datacenter_load_path="mid")
    zones = get_iso_config("ERCOT").zone_names
    demand = np.full((len(zones), 12), 5000.0)
    out = add_datacenter_block(demand, cfg, "ERCOT", 2030, zones)
    assert np.all(out >= 0.0)
    assert out.sum() == pytest.approx(demand.sum())  # relocation conserves energy


@pytest.mark.parametrize(
    "iso,year",
    [("ERCOT", 2030), ("PJM", 2030), ("CAISO", 2040), ("NYISO", 2031), ("MISO", 2030)],
)
def test_mid_relocation_conserves_energy_all_isos(iso, year):
    """Every sourced ISO's MID block sits in the relocate regime, so folding it
    into a representative peaky demand holds total energy invariant (no
    growth x DC double-count) — the FF-1C continuity guarantee, per ISO."""
    cfg = ScenarioConfig(iso=iso, datacenter_load_path="mid")
    zones = get_iso_config(iso).zone_names
    n = len(zones)
    rng = np.random.default_rng(7)
    # Large peaky demand so every mid block is contained (relocate, not tail-add).
    demand = rng.random((n, 48)) * 3e5 + 1e5
    before = float(demand.sum())
    out = add_datacenter_block(demand, cfg, iso, year, zones)
    block_mw = resolve_datacenter_mw(cfg, iso, year) * cfg.datacenter_load_factor
    assert block_mw > 0.0  # each of these ISOs has a nonzero mid block
    assert float(out.sum()) == pytest.approx(before)  # energy invariant


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


def test_miso_block_sourced_from_ltlf():
    """FF-1C wired MISO's DC block from the Sept-2025 MISO LTLF (was {}):
    mid ~11 GW by 2027 growing to ~20 GW by 2030; low signed-subset -> 0."""
    mid = ScenarioConfig(iso="MISO", datacenter_load_path="mid")
    assert resolve_datacenter_mw(mid, "MISO", 2027) == pytest.approx(11000.0)
    assert resolve_datacenter_mw(mid, "MISO", 2030) == pytest.approx(20000.0)
    high = ScenarioConfig(iso="MISO", datacenter_load_path="high")
    assert resolve_datacenter_mw(high, "MISO", 2030) == pytest.approx(27000.0)
    low = ScenarioConfig(iso="MISO", datacenter_load_path="low")
    assert resolve_datacenter_mw(low, "MISO", 2030) == 0.0


def test_unsourced_isos_ship_zero():
    """NEISO's DC quantum is immaterial (~110 MW), so it still ships {} -> 0 MW
    on every path (FF-0D §1.4, documented deferral)."""
    assert DATACENTER_ADDITIONS_MW["NEISO"] == {}
    for path in ("low", "mid", "high"):
        cfg = ScenarioConfig(iso="NEISO", datacenter_load_path=path)
        assert resolve_datacenter_mw(cfg, "NEISO", 2030) == 0.0


def test_unknown_iso_ships_zero():
    cfg = ScenarioConfig(iso="ERCOT", datacenter_load_path="mid")
    assert resolve_datacenter_mw(cfg, "NOT_AN_ISO", 2030) == 0.0


# --------------------------------------------------------------------------
# 6. Backcast guard — the block must never enter a scored backcast (rule 22).
# --------------------------------------------------------------------------
def test_backcast_coerces_nonoff_path_to_off():
    # FF-1F: the field default is now the forecast posture "mid", so a backcast
    # that inherits it (or is handed any non-off path) is COERCED to "off" at
    # construction — a non-forward run pins measured load, so the DC block is
    # inert. This keeps every backcast byte-identical to the legacy "off"
    # default instead of raising on the new default.
    assert ScenarioConfig(iso="ERCOT", mode="backcast").datacenter_load_path == "off"
    assert (
        ScenarioConfig(
            iso="ERCOT", mode="backcast", datacenter_load_path="mid"
        ).datacenter_load_path
        == "off"
    )
    assert (
        ScenarioConfig(
            iso="ERCOT", mode="backcast", datacenter_load_path="high"
        ).datacenter_load_path
        == "off"
    )


def test_hindcast_coerces_path_to_off():
    # A capacity-hindcast (mode="forecast", hindcast=True) solves measured/pinned
    # load (runner.py uses year_base_demand), so the forecast-only DC axis must
    # stay inert there too — coerced to "off" and byte-identical to legacy.
    cfg = ScenarioConfig(iso="ERCOT", mode="forecast", hindcast=True)
    assert cfg.datacenter_load_path == "off"


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
