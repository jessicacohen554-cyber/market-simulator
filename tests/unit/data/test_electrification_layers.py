"""Tests for the FF-G4 Option-B electrification end-use layers (FR-16).

Design: ``docs/handoffs/ff-g4-load-shape-design-memo-2026-07.md`` §4.2/§5.
Trivial-first (CLAUDE.md testing pattern): closed-form resolver/profile
arithmetic, then the fold-in algebra on synthetic zone demand. The axis is
forecast-only and DEFAULT OFF, so the load-bearing tests are the off-path
byte-identity family (zero blast radius on every existing run — including the
DC-only bit-identity of the :func:`add_load_layers` refactor, which the armed
``datacenter_load_path="mid"`` forecast default rides through) and the
backcast/hindcast coercion (keepers can never see the layers).
"""

import numpy as np
import pytest

from market_sim.config.constants import (
    ELECTRIFICATION_LAYERS,
    HEAT_PUMP_BALANCE_POINT_C,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.datacenter import (
    _LAYER_PROFILE_BUILDERS,
    add_datacenter_block,
    add_load_layers,
    electrification_layer_contributions,
    heat_pump_layer_profile,
    resolve_electrification_gwh,
    validate_electrification_config,
)

NEISO_ZONES = get_iso_config("NEISO").zone_names
ERCOT_ZONES = get_iso_config("ERCOT").zone_names


def _demand(n_zones: int, hours: int = 8760, seed: int = 0) -> np.ndarray:
    return np.random.default_rng(seed).uniform(500.0, 3000.0, size=(n_zones, hours))


# --------------------------------------------------------------------------
# 1. Default posture + off-path byte-identity — zero blast radius.
# --------------------------------------------------------------------------
def test_default_is_off_forecast_and_backcast():
    """FF-G4 ships DEFAULT OFF (owner box §8-D2 pending): no run moves."""
    assert ScenarioConfig().electrification_path == "off"
    assert ScenarioConfig().electrification_percentile == 0.5


def test_off_path_resolves_zero():
    cfg = ScenarioConfig(iso="NEISO", mode="forecast")
    assert resolve_electrification_gwh(cfg, "NEISO", "heat_pump", 2035) == 0.0
    assert (
        electrification_layer_contributions(cfg, "NEISO", 2035, NEISO_ZONES, 24) == []
    )


def test_all_off_add_is_identity_same_object():
    """Every layer off/unsourced => the SAME array object (byte-identical)."""
    cfg = ScenarioConfig(iso="NEISO", mode="forecast", datacenter_load_path="off")
    demand = _demand(len(NEISO_ZONES), 24)
    assert add_load_layers(demand, cfg, "NEISO", 2035, NEISO_ZONES) is demand


def test_unsourced_iso_armed_is_still_identity():
    """PJM ships {} layers (M11 blocked): armed == off, the honest no-op."""
    zones = get_iso_config("PJM").zone_names
    cfg = ScenarioConfig(
        iso="PJM",
        mode="forecast",
        datacenter_load_path="off",
        electrification_path="mid",
    )
    demand = _demand(len(zones), 24)
    assert add_load_layers(demand, cfg, "PJM", 2035, zones) is demand


def test_dc_only_path_bit_identical_to_add_datacenter_block():
    """The add_load_layers refactor reproduces the DC block BIT-EXACTLY.

    The forecast default (datacenter mid, electrification off) rides through
    this path, so bit-identity here is what keeps the Wave-3 forecast baseline
    valid through the seam swap (memo §5.3: "a refactor with a byte-identity
    test")."""
    cfg = ScenarioConfig(iso="ERCOT", mode="forecast")  # DC mid default
    demand = _demand(len(ERCOT_ZONES), 8760, seed=7)
    legacy = add_datacenter_block(demand, cfg, "ERCOT", 2030, ERCOT_ZONES)
    unified = add_load_layers(demand, cfg, "ERCOT", 2030, ERCOT_ZONES)
    assert legacy is not demand  # the block is genuinely armed here
    assert np.array_equal(legacy, unified)


# --------------------------------------------------------------------------
# 2. Backcast/hindcast coercion + validator — keepers can never see the layers.
# --------------------------------------------------------------------------
def test_backcast_coerces_off():
    cfg = ScenarioConfig(iso="NEISO", mode="backcast", electrification_path="mid")
    assert cfg.electrification_path == "off"


def test_hindcast_coerces_off():
    cfg = ScenarioConfig(
        iso="NEISO", mode="forecast", hindcast=True, electrification_path="high"
    )
    assert cfg.electrification_path == "off"


def test_validator_rejects_armed_backcast_bypass():
    """Defense in depth: a post-construction mutation still hard-errors."""
    cfg = ScenarioConfig(iso="NEISO", mode="backcast")
    cfg.electrification_path = "mid"  # simulate a bypass of __post_init__
    with pytest.raises(ValueError, match="forecast-only"):
        validate_electrification_config(cfg)


def test_unknown_path_label_raises():
    with pytest.raises(ValueError, match="electrification_path"):
        ScenarioConfig(iso="NEISO", electrification_path="bogus")


def test_cache_key_stable_at_default_and_distinct_armed():
    """Registered in _CACHE_KEY_OPTIONAL_FIELDS: off keeps the key, armed moves it."""
    from market_sim.config.scenarios import _CACHE_KEY_OPTIONAL_FIELDS

    base = ScenarioConfig(iso="NEISO", mode="forecast")
    armed = ScenarioConfig(iso="NEISO", mode="forecast", electrification_path="mid")
    assert base.cache_key() != armed.cache_key()
    # At their defaults the fields are dropped from the hash entirely, so every
    # pre-existing cached run keeps its key (check_cache_key_registration.py).
    assert "electrification_path" in _CACHE_KEY_OPTIONAL_FIELDS
    assert "electrification_percentile" in _CACHE_KEY_OPTIONAL_FIELDS


# --------------------------------------------------------------------------
# 3. Adoption-anchor resolver arithmetic (NEISO heat_pump, CELT-cited).
# --------------------------------------------------------------------------
def test_neiso_heat_pump_anchor_interpolation():
    """The CELT 2026 sheet-1.7 series, not the former two-anchor line.

    SCN-LOAD 2026-09-06 replaced ``{2026: 0.0, 2035: 7165.0}`` with ISO-NE's own
    published ten-year Heating series. The gated published facts are the
    endpoints and the CONVEXITY the two-anchor line could not carry: a straight
    line would put 2030 at 4/9 of 7,165 GWh (~3,184), and ISO-NE publishes
    2,464 -- a ~29% overstatement the intake removed.
    """
    cfg = ScenarioConfig(iso="NEISO", mode="forecast", electrification_path="mid")
    assert resolve_electrification_gwh(cfg, "NEISO", "heat_pump", 2026) == 198.0
    assert resolve_electrification_gwh(cfg, "NEISO", "heat_pump", 2030) == 2464.0
    assert resolve_electrification_gwh(cfg, "NEISO", "heat_pump", 2035) == 7165.0
    # Convex, i.e. materially below the straight line the former anchors implied.
    assert (
        resolve_electrification_gwh(cfg, "NEISO", "heat_pump", 2030)
        < 7165.0 * 4.0 / 9.0
    )
    # Published years interpolate piecewise-linearly between the anchors...
    assert resolve_electrification_gwh(
        cfg, "NEISO", "heat_pump", 2032
    ) == pytest.approx(4113.0)
    # ...and flat-hold after the last one (documented understatement).
    assert resolve_electrification_gwh(cfg, "NEISO", "heat_pump", 2050) == 7165.0


def test_low_high_collapse_onto_mid_when_unpublished():
    """NEISO ships mid-only: low/high must NOT invent a band."""
    for path in ("low", "high"):
        cfg = ScenarioConfig(iso="NEISO", mode="forecast", electrification_path=path)
        assert resolve_electrification_gwh(cfg, "NEISO", "heat_pump", 2035) == 7165.0


def test_ev_arms_only_where_a_published_hourly_profile_exists():
    """A shape we cannot cite is a blocker -- and ERCOT is the one that can.

    SCN-LOAD 2026-09-06: ERCOT's 2025 Adjusted LTLF workbook publishes an hourly
    per-weather-zone ``<zone>_ev`` component, curated to a normalized 8,760-hour
    profile, so the ERCOT ``ev`` layer arms. ISO-NE, NYISO and MISO all publish
    EV ADOPTION anchors (curated in the ``load-forecast`` datatype) but describe
    the charging SHAPE in charts or defer to third-party profiles, so their
    layers stay ``{}`` -- the blocker is the shape, not the numbers, and rule 25
    [R-ISO-SCOPE] forbids borrowing ERCOT's.
    """
    from market_sim.data.datacenter import _EV_PROFILE_SOURCES

    for iso, layers in ELECTRIFICATION_LAYERS.items():
        has_anchors = bool(layers.get("ev", {}))
        has_profile = iso in _EV_PROFILE_SOURCES
        assert has_anchors == has_profile, iso
    assert set(_EV_PROFILE_SOURCES) == {"ERCOT"}


def test_ercot_ev_profile_is_normalized_and_iso_scoped():
    """The published profile sums to 1 and is never another ISO's fallback."""
    from market_sim.data.datacenter import ev_layer_profile

    profile = ev_layer_profile("ERCOT", 2024, 8760)
    assert profile.shape == (8760,)
    assert profile.sum() == pytest.approx(1.0)
    assert (profile > 0.0).all()
    for iso in ("PJM", "NEISO", "NYISO", "MISO", "CAISO"):
        with pytest.raises(ValueError, match="no published hourly charging"):
            ev_layer_profile(iso, 2024, 8760)


def test_layer_with_anchors_but_no_profile_builder_fails_closed():
    """Anchors without a registered profile source refuse to arm (rule 5)."""
    cfg = ScenarioConfig(iso="NEISO", mode="forecast", electrification_path="mid")
    ELECTRIFICATION_LAYERS["NEISO"]["_test_layer"] = {"mid": {2026: 0.0, 2035: 1.0}}
    try:
        with pytest.raises(ValueError, match="no profile source"):
            electrification_layer_contributions(cfg, "NEISO", 2035, NEISO_ZONES, 24)
    finally:
        del ELECTRIFICATION_LAYERS["NEISO"]["_test_layer"]


def test_every_populated_layer_has_a_registered_profile_builder():
    """Standing guard: anchors and profile sources may never drift apart."""
    for iso, layers in ELECTRIFICATION_LAYERS.items():
        for layer, curves in layers.items():
            if curves:
                assert layer in _LAYER_PROFILE_BUILDERS, (iso, layer)


# --------------------------------------------------------------------------
# 4. Heat-pump profile physics (weather-year heating degrees).
# --------------------------------------------------------------------------
def test_heat_pump_profile_normalized_nonnegative():
    p = heat_pump_layer_profile("NEISO", 2024, 8760)
    assert p.shape == (8760,)
    assert float(p.sum()) == pytest.approx(1.0)
    assert float(p.min()) >= 0.0


def test_heat_pump_profile_is_winter_concentrated():
    """The shape follows heating degrees: January >> July (NEISO 2024)."""
    p = heat_pump_layer_profile("NEISO", 2024, 8760)
    jan = float(p[: 31 * 24].mean())
    jul_start = (31 + 28 + 31 + 30 + 31 + 30) * 24
    jul = float(p[jul_start : jul_start + 31 * 24].mean())
    assert jan > 10.0 * jul


def test_heat_pump_profile_missing_weather_raises():
    """An ARMED layer with no weather archive is a hard error, never silent."""
    with pytest.raises(ValueError, match="weather"):
        heat_pump_layer_profile("NEISO", 1901, 8760)


def test_balance_point_is_the_noaa_standard():
    assert HEAT_PUMP_BALANCE_POINT_C == 18.3  # 65 F NOAA/EIA degree-day base


# --------------------------------------------------------------------------
# 5. Fold-in algebra: energy invariance + shape direction (the winter flip).
# --------------------------------------------------------------------------
def test_relocation_is_energy_invariant():
    cfg = ScenarioConfig(
        iso="NEISO",
        mode="forecast",
        datacenter_load_path="off",
        electrification_path="mid",
    )
    demand = _demand(len(NEISO_ZONES), 8760, seed=3)
    out = add_load_layers(demand, cfg, "NEISO", 2035, NEISO_ZONES)
    assert out is not demand
    assert float(out.sum()) == pytest.approx(float(demand.sum()), rel=1e-9)


def test_relocation_moves_energy_into_winter():
    """The HP layer raises winter load and lowers summer load — the direction
    that makes the published ISO-NE winter-peaking flip EXPRESSIBLE (FR-16)."""
    cfg = ScenarioConfig(
        iso="NEISO",
        mode="forecast",
        datacenter_load_path="off",
        electrification_path="mid",
    )
    demand = _demand(len(NEISO_ZONES), 8760, seed=3)
    out = add_load_layers(demand, cfg, "NEISO", 2035, NEISO_ZONES)
    sys_b = demand.sum(axis=0)
    sys_o = out.sum(axis=0)
    janfeb = slice(0, (31 + 28) * 24)
    jul_start = (31 + 28 + 31 + 30 + 31 + 30) * 24
    jul = slice(jul_start, jul_start + 31 * 24)
    assert float(sys_o[janfeb].max()) > float(sys_b[janfeb].max())
    assert float(sys_o[jul].max()) < float(sys_b[jul].max())


def test_contribution_conserves_layer_energy():
    """shares (Σ=1) × profile (Σ=1) × MWh: contribution energy == layer energy."""
    cfg = ScenarioConfig(iso="NEISO", mode="forecast", electrification_path="mid")
    contribs = electrification_layer_contributions(
        cfg, "NEISO", 2035, NEISO_ZONES, 8760
    )
    assert [name for name, _, _ in contribs] == ["heat_pump"]
    _, energy_mwh, arr = contribs[0]
    assert energy_mwh == pytest.approx(7165.0 * 1000.0)
    assert float(arr.sum()) == pytest.approx(energy_mwh, rel=1e-9)
    assert arr.shape == (len(NEISO_ZONES), 8760)
    assert float(arr.min()) >= 0.0
