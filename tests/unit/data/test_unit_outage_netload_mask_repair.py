"""``unit_outage_netload_mask_repair``: the deriver's net-load mask made live for SPP (SPP-85).

``scripts/lib/outage_detect._ISO_TO_BA`` had no SPP key, so ``high_load_mask("SPP")``
returned ``None`` and ``filter_revealed_outages`` kept every detected span: the committed
SPP extracts' recorded ``min_inmerit_hours`` was never in effect. The gate selects the
``-netloadmask-`` companions of the standard, short and partial extracts -- the same
deriver at the same recorded invocation with the mask live -- and each committed
companion is a strict full-row subset of its incumbent.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from market_sim.config.scenarios import ScenarioConfig, cache_key_drop_defaults

_ROOT = Path(__file__).resolve().parents[3]
_RAW = _ROOT / "data" / "raw"


class TestRegistration:
    """Registered, default-off, key-stable at its default."""

    def test_defaults_off(self):
        assert ScenarioConfig().unit_outage_netload_mask_repair is False

    def test_dropped_from_the_cache_key_at_its_default(self):
        assert cache_key_drop_defaults()["unit_outage_netload_mask_repair"] is False

    def test_arming_it_changes_the_cache_key(self):
        base = ScenarioConfig()
        armed = base.with_overrides(unit_outage_netload_mask_repair=True)
        assert base.cache_key() != armed.cache_key()


class TestSelector:
    """SEPARATE files for all three layers, falling back when absent."""

    @staticmethod
    def _lay(tmp_path, monkeypatch, *names):
        import market_sim.data.outages as om

        monkeypatch.setattr(om, "UNIT_OUTAGE_CSV", tmp_path / "campd-unit-outages.csv")
        for n in names:
            (tmp_path / n).write_text("x\n")
        return om

    def test_selects_all_three_companions(self, tmp_path, monkeypatch):
        om = self._lay(
            tmp_path,
            monkeypatch,
            "campd-unit-outages-netloadmask-SPP.csv",
            "campd-unit-outages-short-netloadmask-SPP.csv",
            "campd-partial-outages-netloadmask-SPP.csv",
        )
        assert (
            om.unit_outage_csv_for_iso("SPP", netload_mask_repair=True).name
            == "campd-unit-outages-netloadmask-SPP.csv"
        )
        assert (
            om.unit_outage_short_csv_for_iso("SPP", netload_mask_repair=True).name
            == "campd-unit-outages-short-netloadmask-SPP.csv"
        )
        assert (
            om.unit_partial_outage_csv_for_iso("SPP", netload_mask_repair=True).name
            == "campd-partial-outages-netloadmask-SPP.csv"
        )

    def test_off_keeps_the_incumbents(self, tmp_path, monkeypatch):
        om = self._lay(
            tmp_path,
            monkeypatch,
            "campd-unit-outages-netloadmask-SPP.csv",
            "campd-unit-outages-short-netloadmask-SPP.csv",
            "campd-partial-outages-netloadmask-SPP.csv",
        )
        assert om.unit_outage_csv_for_iso("SPP").name == "campd-unit-outages-SPP.csv"
        assert (
            om.unit_outage_short_csv_for_iso("SPP").name
            == "campd-unit-outages-short-SPP.csv"
        )
        assert (
            om.unit_partial_outage_csv_for_iso("SPP").name
            == "campd-partial-outages-SPP.csv"
        )

    def test_falls_back_when_not_derived(self, tmp_path, monkeypatch):
        om = self._lay(tmp_path, monkeypatch)
        assert (
            om.unit_outage_csv_for_iso("MISO", netload_mask_repair=True).name
            == "campd-unit-outages-MISO.csv"
        )
        assert (
            om.unit_outage_short_csv_for_iso("MISO", netload_mask_repair=True).name
            == "campd-unit-outages-short-MISO.csv"
        )
        assert (
            om.unit_partial_outage_csv_for_iso("MISO", netload_mask_repair=True).name
            == "campd-partial-outages-MISO.csv"
        )

    def test_ignored_under_the_per_unit_family(self, tmp_path, monkeypatch):
        om = self._lay(tmp_path, monkeypatch, "campd-unit-outages-netloadmask-SPP.csv")
        path = om.unit_outage_csv_for_iso(
            "SPP", per_unit_crosswalk=True, netload_mask_repair=True
        )
        assert path.name == "campd-unit-outages-SPP.csv"


class TestDeriverKey:
    """The repair's code half: the SPP net-load mask now resolves."""

    def test_spp_maps_to_the_swpp_balancing_authority(self):
        from scripts.lib.outage_detect import _ISO_TO_BA

        assert _ISO_TO_BA["SPP"] == "SWPP"


_PAIRS = [
    ("campd-unit-outages-SPP.csv", "campd-unit-outages-netloadmask-SPP.csv"),
    (
        "campd-unit-outages-short-SPP.csv",
        "campd-unit-outages-short-netloadmask-SPP.csv",
    ),
    ("campd-partial-outages-SPP.csv", "campd-partial-outages-netloadmask-SPP.csv"),
]


@pytest.mark.parametrize("incumbent,companion", _PAIRS)
def test_committed_companion_is_a_full_row_subset(incumbent, companion):
    """The filter only DROPS spans: every companion row is an incumbent row, byte for byte."""
    a, b = _RAW / incumbent, _RAW / companion
    if not (a.exists() and b.exists()):
        pytest.skip("SPP data profile not hydrated")
    A = pd.read_csv(a).astype(str)
    B = pd.read_csv(b).astype(str)
    assert list(A.columns) == list(B.columns)
    assert len(A.merge(B, how="inner")) == len(B)
    assert np.all(B.plant_group.isin(A.plant_group.unique()))
