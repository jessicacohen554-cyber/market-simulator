"""``campd_dark_unit_year_windows``: a unit dark for a whole year (SOCO-61).

The per-unit CAMPD detector skips a unit that never produced in a year, and
the ``eia923_netzero`` hook works at PLANT grain, so a unit dark all year at a
running plant was modelled fully available (SOCO: Lindsay Hill CT3, 2024).
The gate is the REGISTERED channel that selects the ``-perunitdark-`` extract
(rule 24 ``[R-REGISTRY]``). Evidence: ``docs/handoffs/FINDING-soco-61-2026-09-24.md``.
"""

import importlib.util
from pathlib import Path

import pandas as pd

from market_sim.config.scenarios import ScenarioConfig, cache_key_drop_defaults

_ROOT = Path(__file__).resolve().parents[3]


def _deriver():
    spec = importlib.util.spec_from_file_location(
        "derive_campd_unit_outages", _ROOT / "scripts/data/derive_campd_unit_outages.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestRegistration:
    """Registered, default-off, key-stable at its default."""

    def test_defaults_off(self):
        assert ScenarioConfig().campd_dark_unit_year_windows is False

    def test_is_dropped_from_the_cache_key_at_its_frozen_default(self):
        drops = cache_key_drop_defaults()
        assert drops["campd_dark_unit_year_windows"] is False

    def test_arming_it_changes_the_cache_key(self):
        base = ScenarioConfig()
        armed = base.with_overrides(campd_dark_unit_year_windows=True)
        assert base.cache_key() != armed.cache_key()


class TestSelector:
    """A SEPARATE file, predicated on the per-unit flag, never under merit."""

    @staticmethod
    def _lay(tmp_path, monkeypatch, *names):
        import market_sim.data.outages as om

        monkeypatch.setattr(om, "UNIT_OUTAGE_CSV", tmp_path / "campd-unit-outages.csv")
        for n in names:
            (tmp_path / n).write_text("x\n")
        return om

    def test_selects_the_dark_companion(self, tmp_path, monkeypatch):
        om = self._lay(
            tmp_path,
            monkeypatch,
            "campd-unit-outages-perunit-SOCO.csv",
            "campd-unit-outages-perunitdark-SOCO.csv",
        )
        path = om.unit_outage_csv_for_iso(
            "SOCO", per_unit_crosswalk=True, dark_unit_years=True
        )
        assert path.name == "campd-unit-outages-perunitdark-SOCO.csv"

    def test_off_keeps_the_perunit_extract(self, tmp_path, monkeypatch):
        om = self._lay(
            tmp_path,
            monkeypatch,
            "campd-unit-outages-perunit-SOCO.csv",
            "campd-unit-outages-perunitdark-SOCO.csv",
        )
        path = om.unit_outage_csv_for_iso("SOCO", per_unit_crosswalk=True)
        assert path.name == "campd-unit-outages-perunit-SOCO.csv"

    def test_inert_without_the_per_unit_flag(self, tmp_path, monkeypatch):
        om = self._lay(tmp_path, monkeypatch, "campd-unit-outages-perunitdark-SOCO.csv")
        path = om.unit_outage_csv_for_iso("SOCO", dark_unit_years=True)
        assert path.name == "campd-unit-outages-SOCO.csv"

    def test_falls_back_when_not_derived(self, tmp_path, monkeypatch):
        om = self._lay(tmp_path, monkeypatch, "campd-unit-outages-perunit-NYISO.csv")
        path = om.unit_outage_csv_for_iso(
            "NYISO", per_unit_crosswalk=True, dark_unit_years=True
        )
        assert path.name == "campd-unit-outages-perunit-NYISO.csv"


class TestDarkPredicate:
    """Every admission condition is categorical and each one is necessary."""

    @staticmethod
    def _rows(n, op=0.0):
        return pd.DataFrame({"opTime": [op] * n})

    def test_admits_a_dark_unit_with_adjacent_same_id_output(self):
        d = _deriver()
        seen = {(55271, "CT3", 2023)}
        assert d._is_dark_unit_year(self._rows(24), 24, 55271, "CT3", 2024, seen, True)

    def test_refuses_without_adjacent_output(self):
        d = _deriver()
        assert not d._is_dark_unit_year(
            self._rows(24), 24, 55271, "CT3", 2024, set(), True
        )

    def test_refuses_when_the_unit_operated(self):
        d = _deriver()
        seen = {(55271, "CT3", 2025)}
        assert not d._is_dark_unit_year(
            self._rows(24, op=0.5), 24, 55271, "CT3", 2024, seen, True
        )

    def test_refuses_a_partial_year_record(self):
        d = _deriver()
        seen = {(55271, "CT3", 2025)}
        assert not d._is_dark_unit_year(
            self._rows(23), 24, 55271, "CT3", 2024, seen, True
        )

    def test_refuses_when_no_peer_ran(self):
        d = _deriver()
        seen = {(55271, "CT3", 2025)}
        assert not d._is_dark_unit_year(
            self._rows(24), 24, 55271, "CT3", 2024, seen, False
        )


def test_committed_soco_companion_is_perunit_plus_exactly_the_dark_rows():
    """The committed '-perunitdark-' SOCO extract adds only dark-unit-year rows."""
    raw = _ROOT / "data/raw"
    base = pd.read_csv(raw / "campd-unit-outages-perunit-SOCO.csv")
    dark = pd.read_csv(raw / "campd-unit-outages-perunitdark-SOCO.csv")
    added = dark.merge(base, how="left", indicator=True).query("_merge == 'left_only'")
    assert len(dark) == len(base) + len(added)
    assert set(added["capacity_source"]) == {"campd_dark_unit_year"}
    assert added[
        ["facility_id", "unit_id", "outage_start", "outage_end"]
    ].values.tolist() == [[55271, "CT3", "2024-01-01", "2024-12-31"]]
