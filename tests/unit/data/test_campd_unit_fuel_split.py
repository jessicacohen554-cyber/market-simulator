"""Tests for the miso-278 unit-fuel split of the thermal-tranche family.

``ScenarioConfig.campd_unit_fuel_split`` selects the four ``-fuelsplit-``
companions written by ``derive_thermal_tranches.py --unit-fuel-split``. Trivial
cases first (the fuel classifier, the byte-safe line replacer, the path
resolver), then the committed MISO companions against their incumbents: every
line of a plant outside the mixed-fuel set, and every CHP line, must be
byte-identical, which is what makes the gate a clean single delta.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import market_sim.data.fleet.campd_bins as cb
from market_sim.config.scenarios import ScenarioConfig
from scripts.data import derive_thermal_tranches as dtt
from tests.helpers import REPO_ROOT

PROC = REPO_ROOT / "data" / "raw" / "_processed-legacy"
FAMILY = (
    "thermal_tranches_MISO.csv",
    "thermal_tranches_online_frac_by_year_MISO.csv",
    "thermal_tranches_p25_level_mw_MISO.csv",
    "thermal_tranches_oom_level_mw_MISO.csv",
)


@pytest.mark.parametrize(
    ("label", "klass"),
    [
        ("Coal", "COAL"),
        ("Coal Refuse", "COAL"),
        ("Coal, Pipeline Natural Gas", "COAL"),
        ("Pipeline Natural Gas", "GAS"),
        ("Natural Gas", "GAS"),
        ("Other Gas", "GAS"),
        ("Process Gas", "GAS"),
        ("Petroleum Coke", "OTHER"),
        ("Diesel Oil", "OTHER"),
        ("Wood", "OTHER"),
        (None, "OTHER"),
    ],
)
def test_unit_fuel_class(label, klass):
    """CAMPD's own primaryFuelInfo label decides the class; pet-coke is not coal."""
    assert dtt._unit_fuel_class(label) == klass


def test_companion_path_names():
    """The ISO suffix stays last so the companion sorts beside its incumbent."""
    base = PROC / "thermal_tranches_p25_level_mw_MISO.csv"
    got = dtt.fuel_split_companion_path(base)
    assert got.name == "thermal_tranches_p25_level_mw-fuelsplit-MISO.csv"
    assert cb._fuel_split_companion(base) == got


def test_replace_plant_rows_is_byte_safe(tmp_path):
    """Other plants' lines and kept groups are copied verbatim; rows append."""
    src = tmp_path / "a.csv"
    src.write_text(
        "plant_code,plant_group,x\n1,COAL,1.10\n2,COAL,2.2000\n2,ST_CHP,9\n3,ST_GAS,3\n"
    )
    dst = tmp_path / "b.csv"
    removed = dtt._replace_plant_rows(
        src,
        dst,
        {2},
        [{"plant_code": 2, "plant_group": "ST_GAS", "x": 7.5}],
        frozenset({"ST_CHP"}),
    )
    assert removed == 1
    assert dst.read_text() == (
        "plant_code,plant_group,x\n1,COAL,1.10\n2,ST_CHP,9\n3,ST_GAS,3\n2,ST_GAS,7.5\n"
    )


def test_selector_default_off_and_per_unit_composition():
    """Off by default; under per-unit attribution it selects the per-unit
    family's own fuel-split companion (NWPP-NEXT-14), and refuses the merit
    guard beside it (no such companion)."""
    assert cb.campd_fuel_split_selector(ScenarioConfig()) is False
    assert cb.campd_fuel_split_selector(ScenarioConfig(campd_unit_fuel_split=True))
    assert (
        cb.campd_fuel_split_selector(
            ScenarioConfig(campd_unit_fuel_split=True, campd_per_unit_attribution=True)
        )
        == cb.PER_UNIT_FUEL_SPLIT_TAG
    )
    with pytest.raises(ValueError):
        cb.campd_fuel_split_selector(
            ScenarioConfig(
                campd_unit_fuel_split=True,
                campd_per_unit_attribution=True,
                campd_outage_merit_order_guard=True,
            )
        )


def test_per_unit_fuel_split_resolves_its_own_companion():
    """The pooled read takes '-perunit-fuelsplit-' where derived (NWPP), else
    the per-unit artifact (NYISO); a level artifact never takes a plain
    '-fuelsplit-' file under the per-unit tag."""
    tag = cb.PER_UNIT_FUEL_SPLIT_TAG
    assert cb.thermal_tranche_csv_for_iso("NWPP", True, False, tag).name == (
        "thermal_tranches-perunit-fuelsplit-NWPP.csv"
    )
    assert cb.thermal_tranche_csv_for_iso("NYISO", True, False, tag).name == (
        "thermal_tranches-perunit-NYISO.csv"
    )
    lvl = cb._fuel_split_companion(
        Path("thermal_tranches_online_frac_by_year_MISO.csv"), tag
    )
    assert lvl.name == "thermal_tranches_online_frac_by_year-perunit-fuelsplit-MISO.csv"


def test_per_unit_fuel_split_companion_moves_only_bridger_coal():
    """The committed NWPP companion differs from '-perunit-' in ONE line: Jim
    Bridger 8066's COAL row, now on each window year's own vintage bin."""
    from market_sim.config.paths import PROCESSED_DIR

    a = (PROCESSED_DIR / "thermal_tranches-perunit-NWPP.csv").read_text().splitlines()
    b = (
        (PROCESSED_DIR / "thermal_tranches-perunit-fuelsplit-NWPP.csv")
        .read_text()
        .splitlines()
    )
    assert a[0] == b[0]
    gone, new = set(a) - set(b), set(b) - set(a)
    assert len(gone) == len(new) == 1
    (row,) = new
    assert row.startswith("8066,COAL,Jim Bridger,ok,25211,2119.0,")


def test_resolver_falls_back_where_not_derived():
    """Only MISO carries the companion; every other ISO reads its incumbent."""
    assert cb.thermal_tranche_csv_for_iso("PJM", fuel_split=True).name == (
        "thermal_tranches_PJM.csv"
    )
    assert cb.thermal_tranche_csv_for_iso("MISO").name == "thermal_tranches_MISO.csv"
    assert cb.thermal_tranche_csv_for_iso("MISO", fuel_split=True).name == (
        "thermal_tranches-fuelsplit-MISO.csv"
    )


def _mixed_plants() -> set[int]:
    side = json.loads((PROC / "thermal_tranches-fuelsplit-MISO.meta.json").read_text())
    return set(side["derive_invocation"]["mixed_fuel_plants"])


@pytest.mark.parametrize("name", FAMILY)
def test_committed_companion_is_a_clean_single_delta(name):
    """Unaffected plants' lines and every CHP line are byte-identical."""
    inc = (PROC / name).read_text().splitlines()
    comp = (PROC / dtt.fuel_split_companion_path(PROC / name).name).read_text()
    comp_lines = comp.splitlines()
    assert comp_lines[0] == inc[0]
    mixed = _mixed_plants()
    gcol = inc[0].split(",").index("plant_group")

    def untouched(line: str) -> bool:
        cells = line.split(",")
        return int(cells[0]) not in mixed or cells[gcol] in dtt._CHP_GROUPS

    kept_inc = [ln for ln in inc[1:] if untouched(ln)]
    assert comp_lines[1 : 1 + len(kept_inc)] == kept_inc
    for ln in comp_lines[1 + len(kept_inc) :]:
        assert int(ln.split(",")[0]) in mixed


def _clear(fn) -> None:
    if hasattr(fn, "cache_clear"):
        fn.cache_clear()


def test_fuel_split_reaches_the_st_gas_floor_readers():
    """Armed, Brame 6190 and Big Cajun 2 6055 carry ST_GAS rows at every layer."""
    for fn in (cb.thermal_tranche_p25_level, cb.thermal_tranche_online_frac):
        _clear(fn)
        off = fn("MISO")
        on = fn("MISO", False, False, True)
        for key in ((6190, "ST_GAS"), (6055, "ST_GAS")):
            assert key not in off and key in on
    for fn in (cb.thermal_tranche_oom_level, cb.thermal_tranche_p25_measured_level):
        _clear(fn)
        assert (6190, "ST_GAS") not in fn("MISO")
        assert (6190, "ST_GAS") in fn("MISO", True)
    # Dan E Karn 1702: its ST_GAS row was the coal units' conduct; the gas
    # boilers alone never reach the online threshold, so the row is gone.
    _clear(cb.thermal_tranche_online_frac)
    assert (1702, "ST_GAS") in cb.thermal_tranche_online_frac("MISO")
    assert (1702, "ST_GAS") not in cb.thermal_tranche_online_frac(
        "MISO", False, False, True
    )


def test_per_unit_fuel_split_and_vintage_denominator_are_exclusive():
    """Rule 19: the two repairs of the per-unit head-vintage denominator never
    compose (NWPP-NEXT-14 reconciliation); arming both raises."""
    with pytest.raises(ValueError):
        cb.campd_fuel_split_selector(
            ScenarioConfig(
                campd_unit_fuel_split=True,
                campd_per_unit_attribution=True,
                campd_per_unit_vintage_denominator=True,
            )
        )
