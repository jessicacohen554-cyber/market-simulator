"""``unit_outage_window_hour_grain``: the DETECTED-hour outage window (nyiso-229).

The CAMPD unit-outage detector has always worked in hours while the extract
stored dates, so :mod:`market_sim.data.outages` re-expanded every window to
``outage_start`` 00:00 -> ``outage_end`` 23:00 and asserted up to 23 h at each
edge the detector never detected. caiso-183 built the optional column carriage;
this gate is the REGISTERED channel that selects the ``-perunitmerithour-``
extract carrying it, so the grain appears in ``run_config.json`` and in
``cache_key()`` instead of being silently data-triggered (rule 24
``[R-REGISTRY]``).

Evidence: ``docs/FINDING-nyiso229-phase0-the-outage-window-grain-2026-09-12.md``.
"""

import pandas as pd
import pytest

from market_sim.config.scenarios import (
    ScenarioConfig,
    cache_key_drop_defaults,
)
from market_sim.data.outages import unit_outage_event_window


class TestRegistration:
    """The field is registered, default-off, and does not move any pinned key."""

    def test_defaults_off(self):
        assert ScenarioConfig().unit_outage_window_hour_grain is False

    def test_is_dropped_from_the_cache_key_at_its_frozen_default(self):
        """Registered WITH the field, so every pre-existing config keeps its key."""
        drops = cache_key_drop_defaults()
        assert "unit_outage_window_hour_grain" in drops
        assert drops["unit_outage_window_hour_grain"] is False

    def test_arming_it_changes_the_cache_key(self):
        """A registered channel: the grain is visible in the key when armed."""
        base = ScenarioConfig()
        armed = base.with_overrides(unit_outage_window_hour_grain=True)
        assert base.cache_key() != armed.cache_key()

    def test_off_reproduces_the_incumbent_key_exactly(self):
        base = ScenarioConfig()
        assert (
            base.with_overrides(unit_outage_window_hour_grain=False).cache_key()
            == base.cache_key()
        )


class TestSelector:
    """The gate selects a SEPARATE file and is predicated on both siblings."""

    @staticmethod
    def _lay(tmp_path, monkeypatch, *names):
        import market_sim.data.outages as om

        monkeypatch.setattr(om, "UNIT_OUTAGE_CSV", tmp_path / "campd-unit-outages.csv")
        for n in names:
            (tmp_path / n).write_text("x\n")
        return om

    def test_selects_the_hour_grain_companion(self, tmp_path, monkeypatch):
        om = self._lay(
            tmp_path,
            monkeypatch,
            "campd-unit-outages-perunit-NYISO.csv",
            "campd-unit-outages-perunitmerit-NYISO.csv",
            "campd-unit-outages-perunitmerithour-NYISO.csv",
        )
        assert (
            om.unit_outage_csv_for_iso(
                "NYISO",
                per_unit_crosswalk=True,
                merit_order_guard=True,
                hour_grain=True,
            ).name
            == "campd-unit-outages-perunitmerithour-NYISO.csv"
        )

    def test_off_keeps_the_day_grain_extract(self, tmp_path, monkeypatch):
        om = self._lay(
            tmp_path,
            monkeypatch,
            "campd-unit-outages-perunit-NYISO.csv",
            "campd-unit-outages-perunitmerit-NYISO.csv",
            "campd-unit-outages-perunitmerithour-NYISO.csv",
        )
        assert (
            om.unit_outage_csv_for_iso(
                "NYISO", per_unit_crosswalk=True, merit_order_guard=True
            ).name
            == "campd-unit-outages-perunitmerit-NYISO.csv"
        )

    def test_falls_through_when_the_companion_is_absent(self, tmp_path, monkeypatch):
        """An ISO adopts the grain by deriving its own file and nothing else."""
        om = self._lay(
            tmp_path,
            monkeypatch,
            "campd-unit-outages-perunit-MISO.csv",
            "campd-unit-outages-perunitmerit-MISO.csv",
        )
        assert (
            om.unit_outage_csv_for_iso(
                "MISO",
                per_unit_crosswalk=True,
                merit_order_guard=True,
                hour_grain=True,
            ).name
            == "campd-unit-outages-perunitmerit-MISO.csv"
        )

    @pytest.mark.parametrize(
        "kwargs,expected",
        [
            # No merit guard: the grain has no meaning and is ignored.
            (
                {"per_unit_crosswalk": True, "hour_grain": True},
                "campd-unit-outages-perunit-NYISO.csv",
            ),
            # No per-unit crosswalk: ignored again.
            ({"hour_grain": True}, "campd-unit-outages-NYISO.csv"),
        ],
    )
    def test_is_inert_without_both_siblings(
        self, tmp_path, monkeypatch, kwargs, expected
    ):
        om = self._lay(
            tmp_path,
            monkeypatch,
            "campd-unit-outages-NYISO.csv",
            "campd-unit-outages-perunit-NYISO.csv",
            "campd-unit-outages-perunitmerit-NYISO.csv",
            "campd-unit-outages-perunitmerithour-NYISO.csv",
        )
        assert om.unit_outage_csv_for_iso("NYISO", **kwargs).name == expected


class TestWindowReconstruction:
    """The grain narrows a window and can never widen or move one."""

    @staticmethod
    def _row(**kw):
        base = dict(
            outage_start="2022-05-22",
            outage_end="2022-05-31",
            outage_start_hour=23,
            outage_end_hour=5,
        )
        base.update(kw)
        return pd.DataFrame([base]).itertuples(index=False).__next__()

    def test_day_grain_is_the_incumbent_reconstruction(self):
        start, stop = unit_outage_event_window(self._row(), False)
        assert start == pd.Timestamp("2022-05-22 00:00")
        assert stop == pd.Timestamp("2022-06-01 00:00")

    def test_hour_grain_uses_the_detected_boundaries(self):
        start, stop = unit_outage_event_window(self._row(), True)
        assert start == pd.Timestamp("2022-05-22 23:00")
        assert stop == pd.Timestamp("2022-05-31 06:00")

    def test_absent_grain_is_the_identity_not_an_approximation(self):
        """start_hour 0 / end_hour 23 must reproduce the day window exactly."""
        row = self._row(outage_start_hour=0, outage_end_hour=23)
        assert unit_outage_event_window(row, True) == unit_outage_event_window(
            row, False
        )

    def test_the_hour_window_is_a_subset_of_the_day_window(self):
        row = self._row()
        h0, h1 = unit_outage_event_window(row, True)
        d0, d1 = unit_outage_event_window(row, False)
        assert d0 <= h0 < h1 <= d1

    def test_a_null_hour_degrades_to_the_day_window_per_row(self):
        row = self._row(outage_start_hour=None)
        assert unit_outage_event_window(row, True) == unit_outage_event_window(
            row, False
        )

    def test_the_boundary_day_overlap_disappears(self):
        """The nyiso-229 defect: two windows sharing a boundary DATE.

        Under day grain both cover 2022-05-31 in full, so the accumulator
        subtracts the unit twice on a day it demonstrably ran (Bowline 2625 u1
        metered 7,249 MWh across hours 6-22). Under the detected grain they are
        disjoint and the running hours are available.
        """
        first = self._row(
            outage_start="2022-05-22",
            outage_end="2022-05-31",
            outage_start_hour=23,
            outage_end_hour=5,
        )
        second = self._row(
            outage_start="2022-05-31",
            outage_end="2022-06-15",
            outage_start_hour=23,
            outage_end_hour=6,
        )

        d1 = unit_outage_event_window(first, False)
        d2 = unit_outage_event_window(second, False)
        day_overlap = min(d1[1], d2[1]) - max(d1[0], d2[0])
        assert day_overlap == pd.Timedelta(hours=24)

        h1 = unit_outage_event_window(first, True)
        h2 = unit_outage_event_window(second, True)
        assert min(h1[1], h2[1]) - max(h1[0], h2[0]) <= pd.Timedelta(0)
        # ...and the metered peak hours sit in neither window.
        for hour in (16, 17):
            t = pd.Timestamp("2022-05-31") + pd.Timedelta(hours=hour)
            assert not (h1[0] <= t < h1[1])
            assert not (h2[0] <= t < h2[1])


class TestErcotFamily:
    """R-ERCOT-5: the same field reaches ERCOT's own incumbent window family.

    ERCOT routes its windows through its bin sheet and arms neither per-unit
    flag, so the ``-perunitmerithour-`` branch never reaches it. For ERCOT the
    gate selects the ``-hourgrain`` companions of its three window families
    (standard, short coal, short gas); every other ISO's paths are unchanged.
    Evidence: ``docs/handoffs/FINDING-r-ercot-5-2019-scarcity-2026-09-25.md``.
    """

    NAMES = (
        "campd-unit-outages-hourgrain.csv",
        "campd-unit-outages-short.csv",
        "campd-unit-outages-short-hourgrain.csv",
        "campd-unit-outages-shortgas.csv",
        "campd-unit-outages-shortgas-hourgrain.csv",
        "campd-unit-outages-short-NYISO.csv",
        "campd-unit-outages-shortgas-NYISO.csv",
    )

    def _om(self, tmp_path, monkeypatch, names=NAMES):
        return TestSelector._lay(tmp_path, monkeypatch, *names)

    def test_standard_family_selects_the_companion(self, tmp_path, monkeypatch):
        om = self._om(tmp_path, monkeypatch)
        assert om.unit_outage_csv_for_iso("ERCOT", hour_grain=True).name == (
            "campd-unit-outages-hourgrain.csv"
        )
        assert om.unit_outage_csv_for_iso(None, hour_grain=True).name == (
            "campd-unit-outages-hourgrain.csv"
        )

    def test_off_keeps_every_incumbent(self, tmp_path, monkeypatch):
        om = self._om(tmp_path, monkeypatch)
        assert om.unit_outage_csv_for_iso("ERCOT").name == "campd-unit-outages.csv"
        assert om.unit_outage_short_csv_for_iso("ERCOT").name == (
            "campd-unit-outages-short.csv"
        )
        assert om.unit_outage_short_gas_csv_for_iso("ERCOT").name == (
            "campd-unit-outages-shortgas.csv"
        )

    def test_short_families_select_their_companions(self, tmp_path, monkeypatch):
        om = self._om(tmp_path, monkeypatch)
        assert om.unit_outage_short_csv_for_iso("ERCOT", True).name == (
            "campd-unit-outages-short-hourgrain.csv"
        )
        assert om.unit_outage_short_gas_csv_for_iso("ERCOT", True).name == (
            "campd-unit-outages-shortgas-hourgrain.csv"
        )

    def test_falls_through_when_a_companion_is_absent(self, tmp_path, monkeypatch):
        om = self._om(
            tmp_path,
            monkeypatch,
            ("campd-unit-outages-short.csv", "campd-unit-outages-shortgas.csv"),
        )
        assert om.unit_outage_csv_for_iso("ERCOT", hour_grain=True).name == (
            "campd-unit-outages.csv"
        )
        assert om.unit_outage_short_csv_for_iso("ERCOT", True).name == (
            "campd-unit-outages-short.csv"
        )
        assert om.unit_outage_short_gas_csv_for_iso("ERCOT", True).name == (
            "campd-unit-outages-shortgas.csv"
        )

    def test_other_isos_ignore_it(self, tmp_path, monkeypatch):
        om = self._om(tmp_path, monkeypatch)
        assert om.unit_outage_short_csv_for_iso("NYISO", True).name == (
            "campd-unit-outages-short-NYISO.csv"
        )
        assert om.unit_outage_short_gas_csv_for_iso("NYISO", True).name == (
            "campd-unit-outages-shortgas-NYISO.csv"
        )
        assert om.unit_outage_csv_for_iso("NYISO", hour_grain=True).name == (
            "campd-unit-outages-NYISO.csv"
        )


class TestErcotCommittedCompanions:
    """The committed ERCOT companions only ever NARROW the incumbent windows."""

    PAIRS = (
        ("campd-unit-outages.csv", "campd-unit-outages-hourgrain.csv"),
        ("campd-unit-outages-short.csv", "campd-unit-outages-short-hourgrain.csv"),
        (
            "campd-unit-outages-shortgas.csv",
            "campd-unit-outages-shortgas-hourgrain.csv",
        ),
    )

    @pytest.mark.parametrize("incumbent,companion", PAIRS)
    def test_base_projection_is_the_incumbent(self, incumbent, companion):
        from market_sim.config.paths import RAW_DATA_DIR

        a = RAW_DATA_DIR / incumbent
        b = RAW_DATA_DIR / companion
        if not (a.exists() and b.exists()):
            pytest.skip("ERCOT window extracts not hydrated")
        inc, hg = pd.read_csv(a), pd.read_csv(b)
        assert hg[list(inc.columns)].equals(inc)

    @pytest.mark.parametrize("incumbent,companion", PAIRS)
    def test_every_window_is_a_subset_of_its_day_window(self, incumbent, companion):
        from market_sim.config.paths import RAW_DATA_DIR

        b = RAW_DATA_DIR / companion
        if not b.exists():
            pytest.skip("ERCOT window extracts not hydrated")
        hg = pd.read_csv(b)
        has = hg["outage_start_hour"].notna() & hg["outage_end_hour"].notna()
        assert has.mean() > 0.8
        rows = hg[has]
        start = pd.to_datetime(rows["outage_start"]) + pd.to_timedelta(
            rows["outage_start_hour"].astype(int), unit="h"
        )
        stop = pd.to_datetime(rows["outage_end"]) + pd.to_timedelta(
            rows["outage_end_hour"].astype(int) + 1, unit="h"
        )
        assert (start >= pd.to_datetime(rows["outage_start"])).all()
        assert (stop <= pd.to_datetime(rows["outage_end"]) + pd.Timedelta(days=1)).all()
        assert (stop > start).all()
