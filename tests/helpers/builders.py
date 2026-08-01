"""Fleet / scenario builders for tests.

Consolidates the ~20 hand-rolled ``_gen()`` / ``_make_fleet()`` wrappers and
the 900+ inline ``ScenarioConfig(...)`` constructions into a few named
builders with sensible trivial-case defaults (the 1-gen/1-zone/24h pattern
CLAUDE.md's testing section prescribes). None of these solve — they only build
the objects a test then hands to the LP or a loader.

* :func:`make_gen` — one :class:`~market_sim.data.fleet.Generator`.
* :func:`make_fleet` — :class:`~market_sim.data.fleet.FleetArrays` with one gen
  per zone entry (the exact shape ``tests/unit/model/test_dispatch.py::_make_fleet`` used).
* :func:`base_scenario` — a forecast :class:`~market_sim.config.scenarios.ScenarioConfig`
  with ``**overrides``.
* :func:`backcast_scenario` — the calibration config via
  :func:`market_sim.pipeline.backcast_config.backcast_config`.
"""

from __future__ import annotations

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    FleetArrays,
    Generator,
    generators_to_fleet_arrays,
)
from market_sim.pipeline.backcast_config import backcast_config


def make_gen(
    unit_id: str = "G0",
    zone: str = "Z0",
    *,
    name: str | None = None,
    fuel_type: str = "gas_cc",
    pmax_mw: float = 100.0,
    pmin_mw: float = 10.0,
    eford: float = 0.05,
    **fields,
) -> Generator:
    """Build one :class:`Generator` with trivial-case defaults.

    Every keyword maps straight onto a ``Generator`` field; ``name`` defaults
    to ``unit_id``. Extra model fields (heat_rate, vom, plant_group, ...) pass
    through ``**fields`` unchanged so a test can set exactly what it exercises
    without restating the required attributes.
    """
    return Generator(
        unit_id=unit_id,
        name=unit_id if name is None else name,
        zone=zone,
        fuel_type=fuel_type,
        pmax_mw=pmax_mw,
        pmin_mw=pmin_mw,
        eford=eford,
        **fields,
    )


def make_fleet(
    zones_of_gens,
    zone_names,
    hours: int,
    *,
    pmax: float = 100.0,
    pmin: float = 10.0,
    eford: float = 0.05,
    fuel_type: str = "gas_cc",
    **fields,
) -> FleetArrays:
    """Build ``FleetArrays`` with one generator per entry of ``zones_of_gens``.

    Byte-compatible with ``tests/unit/model/test_dispatch.py::_make_fleet``: generator
    ``i`` is ``G{i}`` in zone ``zones_of_gens[i]``. ``**fields`` is applied to
    every generator (e.g. ``heat_rate=9.0``), so a caller keeps the one-liner
    shape while tuning the attribute under test.

    Args:
        zones_of_gens: One zone name per generator to create.
        zone_names: The ordered zone axis for the arrays.
        hours: Dispatch horizon T (24 for the trivial case).
    """
    generators = [
        make_gen(
            unit_id=f"G{i}",
            zone=z,
            fuel_type=fuel_type,
            pmax_mw=pmax,
            pmin_mw=pmin,
            eford=eford,
            **fields,
        )
        for i, z in enumerate(zones_of_gens)
    ]
    return generators_to_fleet_arrays(generators, zone_names, hours=hours)


def base_scenario(
    mode: str = "forecast",
    iso: str = "ERCOT",
    **overrides,
) -> ScenarioConfig:
    """Build a :class:`ScenarioConfig` with ``mode`` / ``iso`` and overrides.

    ``ScenarioConfig`` is a single flat dataclass with frozen field names
    (its ``cache_key`` hashes ``asdict(self)``), so every keyword here is a
    real field. This is the sanctioned replacement for the inline
    ``ScenarioConfig(iso=..., mode=..., ...)`` scattered across the suite.
    """
    return ScenarioConfig(mode=mode, iso=iso, **overrides)


def backcast_scenario(
    year: int = 2024,
    iso: str = "ERCOT",
    hours: int = 24,
    gas_price: float = 3.0,
    **overrides,
) -> ScenarioConfig:
    """Build a calibration (backcast) :class:`ScenarioConfig`.

    Thin wrapper over :func:`market_sim.pipeline.backcast_config.backcast_config`
    — the single source of truth for the backcast field wiring — with
    trivial-case defaults (2024, ERCOT, 24 h, $3/MMBtu gas). ``**overrides`` are
    the ``backcast_config`` flags (``coal_prb_passthrough``,
    ``offer_curve_overrides``, ...), not raw ScenarioConfig fields, so a test
    exercises the real flag→field mapping rather than a hand-built config.
    """
    return backcast_config(year, iso, hours, gas_price, **overrides)


def no_hydro_accreditation():
    """Zero the FFR-1C hydro pool for hand-computed adequacy-ledger tests.

    :func:`market_sim.model.capacity_evolution.adequacy.accredited_firm_capacity_mw`
    credits the ISO's own dispatched conventional-hydro fleet at its published
    accreditation (audit FR-3 / gap-register R5c). That term is real data — the
    ISO's EIA-860/EIA-923 hydro census — and has no place in a synthetic
    1-2-unit fixture whose point is the requirement/UCAP arithmetic. Use this
    context manager (or ``self.enterContext``/``addCleanup``) so those tests stay
    hermetic; tests that assert the LEDGER'S COMPOSITION should instead add the
    hydro term explicitly rather than zero it.
    """
    from unittest import mock

    return mock.patch(
        "market_sim.model.capacity_evolution.adequacy.modelled_hydro_nameplate_mw",
        lambda iso, year=None: 0.0,
    )
