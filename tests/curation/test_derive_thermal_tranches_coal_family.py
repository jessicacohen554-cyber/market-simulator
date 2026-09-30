"""Tests for the NWPP-NEXT-13 coal repairs in ``derive_thermal_tranches``.

Two defects, both of which silently dropped COAL rows from a re-derive:

* ``_fleet_nameplate_and_group`` keyed on the generator's coal SUBCLASS (COAL-SUB,
  2026-09-25), so every coal bin failed the ``_THERMAL_GROUPS`` filter;
* ``_per_unit_group_resolver`` routed a coal boiler through the GAS-class
  crosswalk, which maps every boiler to ``ST_GAS`` — at a plant carrying both a
  ``COAL`` and an ``ST_GAS`` bin the coal gross landed on ``ST_GAS``.

Trivial synthetic fleets only (testing pattern): the fleet loader and the CHP
flags are stubbed.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace

from tests.helpers import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts" / "data"))

import derive_thermal_tranches as dtt  # noqa: E402


def _gen(code: int, group: str, mw: float) -> SimpleNamespace:
    return SimpleNamespace(plant_code=code, plant_group=group, pmax_mw=mw)


def test_coal_subclasses_collapse_to_the_family_token(monkeypatch):
    fleet = [
        _gen(1, "COAL_PRB", 400.0),
        _gen(1, "COAL_PRB", 300.0),
        _gen(2, "CC_REGULAR", 500.0),
    ]
    monkeypatch.setattr(dtt, "load_fleet_from_csv", lambda iso, cfg: fleet)
    monkeypatch.setattr(dtt, "get_iso_config", lambda iso: None)
    cap, primary = dtt._fleet_nameplate_and_group("TEST")
    assert cap == {(1, "COAL"): 700.0, (2, "CC_REGULAR"): 500.0}
    assert primary == {1: "COAL", 2: "CC_REGULAR"}


def _resolver(monkeypatch, cap, primary, fuel):
    import market_sim.data.chp as chp

    monkeypatch.setattr(chp, "_chp_by_plant", lambda *a, **k: {})
    return dtt._per_unit_group_resolver(cap, primary, "TEST", fuel)


BOILER = "Dry bottom wall-fired boiler"


def test_coal_boiler_routes_to_coal_at_a_mixed_coal_steam_plant(monkeypatch):
    cap = {(8, "COAL"): 1049.0, (8, "ST_GAS"): 1070.0}
    fuel = {(8, "1"): "GAS", (8, "3"): "COAL"}
    group_of = _resolver(monkeypatch, cap, {8: "ST_GAS"}, fuel)
    assert group_of(8, "3", BOILER) == "COAL"
    assert group_of(8, "1", BOILER) == "ST_GAS"


def test_guard_is_inert_where_the_plant_has_no_coal_bin(monkeypatch):
    cap = {(9, "ST_GAS"): 300.0}
    group_of = _resolver(monkeypatch, cap, {9: "ST_GAS"}, {(9, "1"): "COAL"})
    assert group_of(9, "1", BOILER) == "ST_GAS"


def test_no_fuel_map_keeps_the_crosswalk(monkeypatch):
    cap = {(8, "COAL"): 1049.0, (8, "ST_GAS"): 1070.0}
    group_of = _resolver(monkeypatch, cap, {8: "ST_GAS"}, None)
    assert group_of(8, "3", BOILER) == "ST_GAS"
