"""``unit_outage_membership_repair``: windows for never-scanned facilities (PJM-NEXT-2).

The committed standard CAMPD outage extract was derived against one fleet
membership, so a facility outside it carries no window in any year (PJM: the
pre-exit coal and the partial-plant coal exits keyed on their surviving CT
class). The gate selects the ``-memberrepair-`` companion: the committed rows
unchanged plus the re-derived rows of exactly the never-scanned facilities.
Also pinned: the deriver's COAL-SUB artifact-token membership fix.
"""

import importlib.util
from pathlib import Path

import pandas as pd

from market_sim.config.scenarios import ScenarioConfig, cache_key_drop_defaults

_ROOT = Path(__file__).resolve().parents[3]


def _load(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, _ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestRegistration:
    """Registered, default-off, key-stable at its default."""

    def test_defaults_off(self):
        assert ScenarioConfig().unit_outage_membership_repair is False

    def test_dropped_from_the_cache_key_at_its_default(self):
        assert cache_key_drop_defaults()["unit_outage_membership_repair"] is False

    def test_arming_it_changes_the_cache_key(self):
        base = ScenarioConfig()
        armed = base.with_overrides(unit_outage_membership_repair=True)
        assert base.cache_key() != armed.cache_key()


class TestSelector:
    """A SEPARATE file on the standard path only, falling back when absent."""

    @staticmethod
    def _lay(tmp_path, monkeypatch, *names):
        import market_sim.data.outages as om

        monkeypatch.setattr(om, "UNIT_OUTAGE_CSV", tmp_path / "campd-unit-outages.csv")
        for n in names:
            (tmp_path / n).write_text("x\n")
        return om

    def test_selects_the_companion(self, tmp_path, monkeypatch):
        om = self._lay(tmp_path, monkeypatch, "campd-unit-outages-memberrepair-PJM.csv")
        path = om.unit_outage_csv_for_iso("PJM", membership_repair=True)
        assert path.name == "campd-unit-outages-memberrepair-PJM.csv"

    def test_off_keeps_the_standard_extract(self, tmp_path, monkeypatch):
        om = self._lay(tmp_path, monkeypatch, "campd-unit-outages-memberrepair-PJM.csv")
        assert om.unit_outage_csv_for_iso("PJM").name == "campd-unit-outages-PJM.csv"

    def test_falls_back_when_not_derived(self, tmp_path, monkeypatch):
        om = self._lay(tmp_path, monkeypatch)
        path = om.unit_outage_csv_for_iso("NYISO", membership_repair=True)
        assert path.name == "campd-unit-outages-NYISO.csv"

    def test_ignored_under_the_per_unit_family(self, tmp_path, monkeypatch):
        om = self._lay(
            tmp_path,
            monkeypatch,
            "campd-unit-outages-memberrepair-PJM.csv",
        )
        path = om.unit_outage_csv_for_iso(
            "PJM", per_unit_crosswalk=True, membership_repair=True
        )
        assert path.name == "campd-unit-outages-PJM.csv"


class TestCompanionBuilder:
    """Committed rows untouched; only never-scanned facilities are added."""

    def test_adds_only_never_scanned_facilities(self):
        mod = _load(
            "scripts/data/build_outage_membership_repair.py", "build_outage_membership"
        )
        cols = ["facility_id", "unit_id", "outage_start"]
        base = pd.DataFrame([[1, "a", "2019-01-01"]], columns=cols)
        rederive = pd.DataFrame(
            [[1, "a", "2019-02-01"], [2, "b", "2019-03-01"]], columns=cols
        )
        comp = mod.build_companion(base, rederive)
        assert comp.iloc[:1].equals(base)
        assert comp.iloc[1:]["facility_id"].tolist() == [2]

    def test_committed_pjm_companion_preserves_every_committed_row(self):
        base = pd.read_csv(_ROOT / "data/raw/campd-unit-outages-PJM.csv")
        comp = pd.read_csv(_ROOT / "data/raw/campd-unit-outages-memberrepair-PJM.csv")
        assert comp.iloc[: len(base)].equals(base)
        added = comp.iloc[len(base) :]
        assert not set(added["facility_id"]) & set(base["facility_id"])


def test_deriver_membership_speaks_the_artifact_coal_token():
    """COAL-SUB: a coal-SUBCLASS fleet row must qualify as the COAL family."""
    from market_sim.config.plant_taxonomy import artifact_class
    from market_sim.data.outages import QUALIFYING_PLANT_GROUPS

    for sub in ("COAL_BIT", "COAL_PRB", "COAL_WC", "COAL_LIGNITE"):
        assert artifact_class(sub) in QUALIFYING_PLANT_GROUPS
    src = (_ROOT / "scripts/data/derive_campd_unit_outages.py").read_text()
    assert "= artifact_class(g.plant_group)" in src


class TestNuclearDormancyDefersToVintageExit:
    """PJM-NEXT-2 card 3: a mid-vintage-exit nuclear unit is not dormancy-zeroed."""

    @staticmethod
    def _run(flag: bool, mid: bool):
        import numpy as np

        from market_sim.data.fleet import Generator
        from market_sim.data.fleet.arrays import _nuclear_monthly

        g = Generator(
            unit_id="8011_1",
            name="TMI",
            zone="PJM_Central_PA",
            fuel_type="nuclear",
            pmax_mw=802.8,
            plant_code=8011,
        )
        g.mid_vintage_exit_unit = mid
        av = np.ones((1, 48))
        cfg = ScenarioConfig(
            iso="PJM",
            mode="backcast",
            nuclear_dormancy_defers_to_vintage_exit=flag,
        )
        _nuclear_monthly([g], av, 48, "PJM", 2019, cfg)
        return av

    def test_registered_default_off(self):
        assert ScenarioConfig().nuclear_dormancy_defers_to_vintage_exit is False
        assert (
            cache_key_drop_defaults()["nuclear_dormancy_defers_to_vintage_exit"]
            is False
        )

    def test_off_keeps_the_dormancy_zeroing(self):
        assert self._run(False, True).max() == 0.0

    def test_armed_exempts_only_the_vintage_exit_unit(self):
        assert self._run(True, True).max() > 0.0
        assert self._run(True, False).max() == 0.0
