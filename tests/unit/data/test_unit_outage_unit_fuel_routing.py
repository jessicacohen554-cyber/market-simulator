"""``unit_outage_unit_fuel_routing``: per-unit fuel routing of the membership-repaired extract (PJM-NEXT-3).

The standard deriver tags every window at a facility with ONE class per year, so
at a plant mid-conversion (one steam generator coal, one gas) every unit's window
lands on one fuel slice. The gate selects the ``-memberrepair-unitfuel-``
companion, whose rows are the membership-repaired rows with only a mixed-plant
steam row re-tagged to its own generator's class.
"""

import importlib.util
from pathlib import Path

import pandas as pd

from market_sim.config.scenarios import ScenarioConfig, cache_key_drop_defaults

_ROOT = Path(__file__).resolve().parents[3]


def _builder():
    spec = importlib.util.spec_from_file_location(
        "build_outage_unit_fuel_routing",
        _ROOT / "scripts/data/build_outage_unit_fuel_routing.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestRegistration:
    """Registered, default-off, key-stable at its default."""

    def test_defaults_off(self):
        assert ScenarioConfig().unit_outage_unit_fuel_routing is False

    def test_dropped_from_the_cache_key_at_its_default(self):
        assert cache_key_drop_defaults()["unit_outage_unit_fuel_routing"] is False

    def test_arming_it_changes_the_cache_key(self):
        base = ScenarioConfig()
        armed = base.with_overrides(unit_outage_unit_fuel_routing=True)
        assert base.cache_key() != armed.cache_key()


class TestSelector:
    """A companion OF '-memberrepair-', falling back when absent."""

    @staticmethod
    def _lay(tmp_path, monkeypatch, *names):
        import market_sim.data.outages as om

        monkeypatch.setattr(om, "UNIT_OUTAGE_CSV", tmp_path / "campd-unit-outages.csv")
        for n in names:
            (tmp_path / n).write_text("x\n")
        return om

    def test_selects_the_companion(self, tmp_path, monkeypatch):
        om = self._lay(
            tmp_path,
            monkeypatch,
            "campd-unit-outages-memberrepair-PJM.csv",
            "campd-unit-outages-memberrepair-unitfuel-PJM.csv",
        )
        path = om.unit_outage_csv_for_iso(
            "PJM", membership_repair=True, unit_fuel_routing=True
        )
        assert path.name == "campd-unit-outages-memberrepair-unitfuel-PJM.csv"

    def test_needs_membership_repair(self, tmp_path, monkeypatch):
        om = self._lay(
            tmp_path, monkeypatch, "campd-unit-outages-memberrepair-unitfuel-PJM.csv"
        )
        path = om.unit_outage_csv_for_iso("PJM", unit_fuel_routing=True)
        assert path.name == "campd-unit-outages-PJM.csv"

    def test_off_keeps_the_memberrepair_extract(self, tmp_path, monkeypatch):
        om = self._lay(
            tmp_path,
            monkeypatch,
            "campd-unit-outages-memberrepair-PJM.csv",
            "campd-unit-outages-memberrepair-unitfuel-PJM.csv",
        )
        path = om.unit_outage_csv_for_iso("PJM", membership_repair=True)
        assert path.name == "campd-unit-outages-memberrepair-PJM.csv"

    def test_falls_back_when_not_derived(self, tmp_path, monkeypatch):
        om = self._lay(tmp_path, monkeypatch, "campd-unit-outages-memberrepair-PJM.csv")
        path = om.unit_outage_csv_for_iso(
            "PJM", membership_repair=True, unit_fuel_routing=True
        )
        assert path.name == "campd-unit-outages-memberrepair-PJM.csv"


class TestCompanionBuilder:
    """Only a mixed-plant steam row moves, and only its tag."""

    def test_retags_to_the_units_own_class(self, monkeypatch):
        mod = _builder()
        monkeypatch.setattr(
            mod,
            "steam_unit_classes",
            lambda year: {9: {"1": "COAL", "2": "ST_GAS"}} if year == 2024 else {},
        )
        cols = ["facility_id", "unit_id", "plant_group", "outage_start", "outage_end"]
        base = pd.DataFrame(
            [
                [9, "1", "ST_GAS", "2024-01-01", "2024-02-01"],  # coal unit, gas tag
                [9, "2", "ST_GAS", "2024-03-01", "2024-04-01"],  # already right
                [9, "1", "COAL", "2023-01-01", "2023-02-01"],  # not a mixed year
                [9, "3", "ST_GAS", "2024-05-01", "2024-06-01"],  # unmatched unit
                [8, "1", "ST_GAS", "2024-01-01", "2024-02-01"],  # not a mixed plant
                [9, "1", "CC_REGULAR", "2024-01-01", "2024-02-01"],  # not steam
            ],
            columns=cols,
        )
        comp, log = mod.build_companion(base)
        assert comp["plant_group"].tolist() == [
            "COAL",
            "ST_GAS",
            "COAL",
            "ST_GAS",
            "ST_GAS",
            "CC_REGULAR",
        ]
        assert comp.drop(columns="plant_group").equals(base.drop(columns="plant_group"))
        assert (log["to_tag"] == "UNMATCHED").sum() == 1

    def test_committed_pjm_companion_only_retags(self):
        base = pd.read_csv(
            _ROOT / "data/raw/campd-unit-outages-memberrepair-PJM.csv",
            dtype={"unit_id": str},
        )
        comp = pd.read_csv(
            _ROOT / "data/raw/campd-unit-outages-memberrepair-unitfuel-PJM.csv",
            dtype={"unit_id": str},
        )
        assert comp.drop(columns="plant_group").equals(base.drop(columns="plant_group"))
        moved = comp["plant_group"] != base["plant_group"]
        assert set(comp.loc[moved, "facility_id"]) == {3140, 3149}
