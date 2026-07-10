"""Tests for the NEISO condition-varying reserve-requirement channel (Limb A).

Covers the ``_neiso_design`` hourly-requirement path behind
``ScenarioConfig.neiso_dynamic_reserve_requirements`` (default-off
byte-identical, hard-error without the intake), and the rule-19
mutual-exclusion guard between the in-LP co-opt families and the post-solve
RCPF overlay (``neiso_rcpf_enabled``). The measured-series loader itself is
covered by ``tests/test_curate_reserve_requirements.py`` (the clean-datatype
round trip); here it is monkeypatched, mirroring
``tests/test_nyiso_dynamic_reserve_requirements.py``.
"""

from types import SimpleNamespace

import numpy as np
import pytest

from market_sim.config.reserve_config import NEISO_RCPF_PRODUCTS, _neiso_design
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays
from market_sim.data.neiso_reserve_requirements import FAMILY_BY_LOCATION_PRODUCT

T = 48
ZONES = ["North", "Central", "Boston", "Connecticut", "HQ_import"]


def _fa():
    """One reserve-eligible gas unit per zone, flat availability."""
    n = len(ZONES)
    return FleetArrays(
        pmax=np.full(n, 1000.0),
        pmin=np.zeros(n),
        heat_rate=np.full(n, 8.0),
        vom=np.zeros(n),
        emission_rate=np.zeros(n),
        nox_rate=np.zeros(n),
        so2_rate=np.zeros(n),
        zone_idx=np.arange(n),
        fuel_type_idx=np.full(n, FUEL_TYPE_MAP["gas_ct"]),
        availability=np.ones((n, T)),
        unit_ids=[f"g{i}" for i in range(n)],
        efficiency_bin=np.zeros(n, dtype=int),
        plant_code=np.zeros(n, dtype=int),
    )


def _config(**overrides):
    base = dict(
        iso="NEISO",
        weather_year=2024,
        neiso_rcpf_products=None,
        neiso_rcpf_enabled=False,
        neiso_dynamic_reserve_requirements=False,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_family_map_matches_design_names():
    design = _neiso_design(_config(), _fa(), T, ZONES)
    names = {f.name for f in design.families}
    assert set(FAMILY_BY_LOCATION_PRODUCT.values()) == names


def test_default_off_static_requirements():
    design = _neiso_design(_config(), _fa(), T, ZONES)
    static_by_name = {str(n): float(r) for n, r, _c, _p in NEISO_RCPF_PRODUCTS}
    for fam in design.families:
        assert fam.requirement.shape == (T,)
        np.testing.assert_allclose(fam.requirement, static_by_name[fam.name])


def test_flag_without_data_raises(tmp_path):
    import scripts.lib.clean_io as clean_io

    old = clean_io.paths.CLEAN_DIR
    clean_io.paths.CLEAN_DIR = tmp_path  # no clean partition here
    try:
        cfg = _config(neiso_dynamic_reserve_requirements=True)
        with pytest.raises(FileNotFoundError, match="static requirements"):
            _neiso_design(cfg, _fa(), T, ZONES)
    finally:
        clean_io.paths.CLEAN_DIR = old


def test_dynamic_series_replaces_family_requirement(monkeypatch):
    series = {"ne_30min_total": 2000.0 + np.arange(T, dtype=float)}
    monkeypatch.setattr(
        "market_sim.data.neiso_reserve_requirements.load_neiso_reserve_requirements",
        lambda year, hours: series,
    )
    cfg = _config(neiso_dynamic_reserve_requirements=True)
    design = _neiso_design(cfg, _fa(), T, ZONES)
    by_name = {f.name: f for f in design.families}
    np.testing.assert_allclose(
        by_name["ne_30min_total"].requirement, series["ne_30min_total"]
    )
    # Families without a measured series keep the static published value.
    static = by_name["ne_10min_spin"].requirement
    assert np.all(static == static[0])
    # ORDC step shape stays anchored to the published static anchors.
    base = _neiso_design(_config(), _fa(), T, ZONES)
    base_by_name = {f.name: f for f in base.families}
    np.testing.assert_allclose(
        by_name["ne_30min_total"].ordc_penalties,
        base_by_name["ne_30min_total"].ordc_penalties,
    )
    np.testing.assert_allclose(
        by_name["ne_30min_total"].ordc_step_widths,
        base_by_name["ne_30min_total"].ordc_step_widths,
    )


def test_overlay_plus_coopt_raises():
    cfg = _config(neiso_rcpf_enabled=True)
    with pytest.raises(ValueError, match="rule 19"):
        _neiso_design(cfg, _fa(), T, ZONES)
