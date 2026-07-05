"""Stage-5 interchange-unification parity tests (builder-swap gate).

Freezes the OLD inline import-fleet construction + topology sequence that
``scripts/run_calibration.py::run_year`` carried before Stage 5 (verbatim
logic copy at origin/main ``85a0dd7``), and asserts the NEW shared path —
``get_interchange_spec`` → ``build_interchange_fleet`` →
``apply_interchange_topology`` — produces byte-identical ``Generator`` lists
(count, order, and every field) and an identical topology extension, for
every ISO with a priced interchange node and for all three CAISO seam modes
(reference-price seam, per-hub, bidirectional).

These are the fast CI-able half of the Stage-5 regression gate; the keeper
re-solve (``scripts/regression_gate.py --mode builder``) is the slow
authoritative half.
"""

from dataclasses import dataclass

import numpy as np
import pytest

from market_sim.config.interchange_config import (
    IMPORT_TRANCHES,
    IMPORT_TRANCHES_BY_YEAR,
    INTERFACE_NEIGHBORS,
    apply_interchange_topology,
    build_interchange_fleet,
    get_interchange_spec,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.model.transmission import (
    build_caiso_bidir_intertie,
    build_caiso_per_hub_intertie,
    build_export_sinks,
    build_import_generators,
    build_miso_firm_imports,
    build_reference_price_node,
    extend_with_import_node,
    split_caiso_import_node_per_hub,
)

# Every ISO whose backcast can serve interchange through the priced node.
PRICED_ISOS = ("CAISO", "PJM", "NYISO", "NEISO", "MISO")


@dataclass
class _FakeConfig:
    """Minimal ScenarioConfig stand-in carrying the interchange gates."""

    reference_price_interface: bool = False
    caiso_reference_price_seam: bool = False
    caiso_per_hub_intertie: bool = False
    caiso_bidir_intertie: bool = False
    caiso_perhub_firm_base: bool = False
    miso_firm_imports: bool = False
    nyiso_import_reconciliation: bool = False
    capacity_deliverability_limits: bool = False
    weather_year: int | None = None
    mode: str = "backcast"
    carbon_price: float = 0.0


# ---------------------------------------------------------------------------
# FROZEN pre-Stage-5 inline logic (labeled copy of run_calibration.py::run_year
# at origin/main 85a0dd7 — the builder ladder, the Manitoba firm append, and
# the extend → seam-limit → per-hub-split topology sequence). Do NOT "fix"
# this copy: it is the parity oracle.
# ---------------------------------------------------------------------------


def _old_inline_import_fleet(config, iso, year, border_carbon):
    """Frozen copy of the old inline builder ladder (returns gens, corridors)."""
    caiso_ref_seam = (
        getattr(config, "caiso_reference_price_seam", False) and iso == "CAISO"
    )
    caiso_per_hub = (not caiso_ref_seam) and (
        getattr(config, "caiso_per_hub_intertie", False) and iso == "CAISO"
    )
    caiso_corridors = caiso_per_hub or caiso_ref_seam
    if caiso_ref_seam:
        import_generators = build_reference_price_node(iso)
    elif caiso_per_hub:
        import_generators = build_caiso_per_hub_intertie(border_carbon)
    elif getattr(config, "caiso_bidir_intertie", False) and iso == "CAISO":
        import_generators = build_caiso_bidir_intertie(border_carbon)
    elif (
        getattr(config, "reference_price_interface", False)
        and iso in INTERFACE_NEIGHBORS
        and iso != "CAISO"
    ):
        import_generators = build_reference_price_node(iso)
    else:
        import_generators = build_import_generators(
            iso, border_carbon, year=year
        ) + build_export_sinks(iso)
    if getattr(config, "miso_firm_imports", False):
        import_generators = import_generators + build_miso_firm_imports(
            iso, year=year, mode=getattr(config, "mode", "forecast")
        )
    return import_generators, caiso_corridors


def _old_inline_topology(iso_config, iso, config, year, caiso_corridors):
    """Frozen copy of the old inline topology sequence."""
    iso_config = extend_with_import_node(iso_config)
    if getattr(config, "capacity_deliverability_limits", False):
        from market_sim.config.capacity_area_crosswalk import aggregate_by_zone
        from market_sim.config.interchange_config import IMPORT_ZONE
        from market_sim.data import capacity_deliverability as capdel
        from market_sim.model.transmission import apply_deliverability_seam_limit

        _dy = capdel.resolve_delivery_year(iso, year)
        _season = capdel.resolve_season(iso)
        _imp_area = capdel.import_limit_by_area(iso, _dy, _season)
        _imp_types = capdel.area_types_by_area(iso, _dy, _season, "import_limit")
        _imp_by_zone, _ = aggregate_by_zone(iso, _imp_area, _imp_types)
        _import_zone = IMPORT_ZONE.get(iso)
        _seam_mw = _imp_by_zone.get(_import_zone) if _import_zone else None
        if _seam_mw:
            iso_config = apply_deliverability_seam_limit(iso_config, iso, _seam_mw)
    if caiso_corridors:
        iso_config = split_caiso_import_node_per_hub(iso_config)
    return iso_config


# ---------------------------------------------------------------------------
# Comparison helpers
# ---------------------------------------------------------------------------

_GEN_FIELDS = ("unit_id", "name", "zone", "fuel_type")
_GEN_NUMERIC = ("pmax_mw", "pmin_mw", "heat_rate", "vom", "eford")


def _assert_gens_identical(old, new):
    assert len(old) == len(new), (
        f"generator count differs: old {len(old)} vs new {len(new)}"
    )
    for field_name in _GEN_FIELDS:
        old_v = [getattr(g, field_name) for g in old]
        new_v = [getattr(g, field_name) for g in new]
        assert old_v == new_v, f"{field_name} differs:\n{old_v}\nvs\n{new_v}"
    for field_name in _GEN_NUMERIC:
        old_v = np.array([getattr(g, field_name) for g in old], dtype=float)
        new_v = np.array([getattr(g, field_name) for g in new], dtype=float)
        assert np.array_equal(old_v, new_v), (
            f"{field_name} differs:\n{old_v}\nvs\n{new_v}"
        )


def _topology_signature(iso_config):
    return (
        tuple(iso_config.zone_names),
        tuple((ln.from_zone, ln.to_zone, float(ln.ttc_mw)) for ln in iso_config.links),
        tuple(
            (
                lim.name,
                tuple(tuple(pair) for pair in lim.links),
                float(lim.cap_mw),
                bool(getattr(lim, "bidirectional", False)),
            )
            for lim in iso_config.interface_limits
        ),
    )


def _new_path(config, iso, year, border_carbon):
    spec = get_interchange_spec(config, iso, year=year)
    gens = build_interchange_fleet(spec, border_carbon)
    return spec, gens


def _assert_parity(config, iso, year, border_carbon=0.0):
    old_gens, old_corridors = _old_inline_import_fleet(config, iso, year, border_carbon)
    spec, new_gens = _new_path(config, iso, year, border_carbon)
    _assert_gens_identical(old_gens, new_gens)
    assert spec.use_corridors == old_corridors
    old_topo = _old_inline_topology(
        get_iso_config(iso), iso, config, year, old_corridors
    )
    new_topo = apply_interchange_topology(
        get_iso_config(iso), spec, config, year=year, extend_node=True
    )
    assert _topology_signature(old_topo) == _topology_signature(new_topo)
    return spec, new_gens


# ---------------------------------------------------------------------------
# Static tranche ladder (the keeper path for NYISO/NEISO; default elsewhere)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("iso", PRICED_ISOS)
@pytest.mark.parametrize("year", [2023, 2024, 2025, 2030])
def test_static_ladder_parity(iso, year):
    """Static year-grounded tranche ladder: identical gens + topology."""
    config = _FakeConfig(weather_year=year)
    spec, gens = _assert_parity(config, iso, year)
    expected = IMPORT_TRANCHES_BY_YEAR.get(iso, {}).get(
        year, IMPORT_TRANCHES.get(iso, [])
    )
    n_exports = len(gens) - len(expected)
    assert len(gens) >= len(expected)
    assert [g.name for g in gens[: len(expected)]] == [n for n, _, _ in expected]
    assert n_exports >= 0


def test_static_ladder_year_resolution_nyiso():
    """NYISO's year-grounded ladders (2023-2025) differ from the static one
    and the spec path resolves the same ladder the old inline path did."""
    for year in (2023, 2024, 2025):
        config = _FakeConfig(weather_year=year)
        _, gens = _new_path(config, "NYISO", year, 0.0)
        expected = IMPORT_TRANCHES_BY_YEAR["NYISO"][year]
        got = [(g.name, g.pmax_mw, g.vom) for g in gens[: len(expected)]]
        assert got == [(n, c, m) for n, c, m in expected]


def test_static_ladder_explicit_year_overrides_weather_year():
    """run_year passes the solve year explicitly; it must win over
    config.weather_year if they ever diverge."""
    config = _FakeConfig(weather_year=2030)
    _, gens = _new_path(config, "NYISO", 2024, 0.0)
    expected = IMPORT_TRANCHES_BY_YEAR["NYISO"][2024]
    assert [(g.name, g.vom) for g in gens[: len(expected)]] == [
        (n, m) for n, c, m in expected
    ]


# ---------------------------------------------------------------------------
# Reference-price seams (PJM/MISO keepers; generic non-CAISO path)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("iso", ["PJM", "MISO"])
def test_reference_price_node_parity(iso):
    config = _FakeConfig(reference_price_interface=True, weather_year=2024)
    spec, gens = _assert_parity(config, iso, 2024)
    assert spec.use_reference_price
    assert not spec.use_corridors
    # one import + one export band per SEAM_FLOW_TRANCHES per neighbor
    assert len(gens) > 0 and all(g.fuel_type == "import" for g in gens)


def test_miso_reference_with_firm_imports_backcast_parity():
    """MISO keeper shape: reference seam + measured-year Manitoba firm block."""
    for year in (2023, 2024, 2025):
        config = _FakeConfig(
            reference_price_interface=True,
            miso_firm_imports=True,
            weather_year=year,
            mode="backcast",
        )
        spec, gens = _assert_parity(config, "MISO", year)
        firm = [g for g in gens if g.name == "Manitoba_firmhydro"]
        assert len(firm) == 1
        # the firm block is appended LAST (construction order preserved)
        assert gens[-1].name == "Manitoba_firmhydro"


def test_generic_reference_price_never_applies_to_caiso():
    """CAISO + reference_price_interface (without the dedicated seam flag)
    falls through to the static ladder — the old inline behaviour."""
    config = _FakeConfig(reference_price_interface=True, weather_year=2024)
    _assert_parity(config, "CAISO", 2024)
    spec = get_interchange_spec(config, "CAISO", year=2024)
    assert not spec.use_reference_price
    assert spec.caiso_mode is None


# ---------------------------------------------------------------------------
# CAISO — all three seam modes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("border_carbon", [0.0, 12.34])
def test_caiso_per_hub_parity(border_carbon):
    """Keeper caiso-51 shape: per-hub intertie (+ firm base is price-side only)."""
    config = _FakeConfig(
        caiso_per_hub_intertie=True,
        caiso_perhub_firm_base=True,
        weather_year=2024,
    )
    spec, gens = _assert_parity(config, "CAISO", 2024, border_carbon)
    assert spec.caiso_mode == "per_hub"
    assert spec.use_corridors
    zones = {g.zone for g in gens}
    assert zones == {"WECC_PNW", "WECC_DSW"}
    # two export legs, one per corridor, appended after the tranches
    assert [g.name for g in gens if g.pmin_mw < 0] == [
        "export_MALIN",
        "export_PALOVRDE",
    ]


@pytest.mark.parametrize("border_carbon", [0.0, 12.34])
def test_caiso_bidir_parity(border_carbon):
    config = _FakeConfig(caiso_bidir_intertie=True, weather_year=2024)
    spec, gens = _assert_parity(config, "CAISO", 2024, border_carbon)
    assert spec.caiso_mode == "bidir"
    assert not spec.use_corridors  # pooled WECC_import node, no per-hub split
    assert gens[-1].name == "export_bidir"
    assert all(g.zone == "WECC_import" for g in gens)


def test_caiso_reference_seam_parity():
    config = _FakeConfig(caiso_reference_price_seam=True, weather_year=2024)
    spec, gens = _assert_parity(config, "CAISO", 2024)
    assert spec.caiso_mode == "reference_seam"
    assert spec.use_reference_price and spec.use_corridors
    # corridor zones host the seam bands (per-hub split topology)
    assert {g.zone for g in gens} == {"WECC_PNW", "WECC_DSW"}


def test_caiso_mode_mutual_exclusion_ladder():
    """reference seam ≻ per-hub ≻ bidir — the frozen inline precedence."""
    config = _FakeConfig(
        caiso_reference_price_seam=True,
        caiso_per_hub_intertie=True,
        caiso_bidir_intertie=True,
        weather_year=2024,
    )
    spec, _ = _assert_parity(config, "CAISO", 2024)
    assert spec.caiso_mode == "reference_seam"

    config = _FakeConfig(
        caiso_per_hub_intertie=True, caiso_bidir_intertie=True, weather_year=2024
    )
    spec, _ = _assert_parity(config, "CAISO", 2024)
    assert spec.caiso_mode == "per_hub"


def test_caiso_static_pooled_parity():
    """CAISO with every seam flag off: pooled static ladder + export sinks."""
    config = _FakeConfig(weather_year=2024)
    spec, gens = _assert_parity(config, "CAISO", 2024, border_carbon=7.7)
    assert spec.caiso_mode is None
    assert all(g.zone == "WECC_import" for g in gens)


def test_caiso_per_hub_topology_split():
    """The split replaces WECC_import with the two corridor zones and re-homes
    the simultaneous-import limit onto the corridor links (both paths)."""
    config = _FakeConfig(caiso_per_hub_intertie=True, weather_year=2024)
    spec = get_interchange_spec(config, "CAISO", year=2024)
    topo = apply_interchange_topology(
        get_iso_config("CAISO"), spec, config, year=2024, extend_node=True
    )
    assert "WECC_import" not in topo.zone_names
    assert {"WECC_PNW", "WECC_DSW"} <= set(topo.zone_names)
    sim = [
        lim
        for lim in topo.interface_limits
        if all(pair[0] in ("WECC_PNW", "WECC_DSW") for pair in lim.links)
        and len(lim.links) == 2
    ]
    assert sim, "simultaneous-import limit not re-homed onto the corridor links"


# ---------------------------------------------------------------------------
# Cross-orchestrator: the spec resolved without an explicit year (the
# forecast runner's call) matches the explicit-year call when
# weather_year == solve year (the backcast invariant).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("iso", PRICED_ISOS)
def test_runner_and_calibration_spec_agree(iso):
    config = _FakeConfig(weather_year=2024)
    spec_runner = get_interchange_spec(config, iso)  # runner: no explicit year
    spec_cal = get_interchange_spec(config, iso, year=2024)
    assert spec_runner == spec_cal
    assert build_interchange_fleet(spec_runner, 0.0) == build_interchange_fleet(
        spec_cal, 0.0
    )
