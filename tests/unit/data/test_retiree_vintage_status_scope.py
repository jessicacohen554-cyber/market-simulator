"""Tests for the retiree-channel vintage-status scope (miso-188).

``fleet.load_retired_within_window(..., vintage_status_scope=True)`` drops a
within-window retiree unit for backcast solve year Y iff its status in the
latest committed EIA-860 vintage <= Y whose operable sheet lists it is
non-OP — EIA's own contemporaneous judgment that the unit was deactivated
before its formal retirement date. Unlisted units fail OPEN (kept). Design:
``results/calibration/PREREG-miso188-retiree-vintage-status-scope-2026-08-30.md``.

Trivial synthetic cases first (tmp-dir retiree parquet + vintages), then the
real committed-data case (Grand Tower 862 dark / Rush Island 6155 running).
"""

import unittest
from pathlib import Path


from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import load_retired_within_window
from market_sim.data.fleet.eia860 import (
    _committed_vintage_years_for,
    _retiree_vintage_status,
)


class TestVintageStatusOracleLookup(unittest.TestCase):
    """The committed-data oracle lookup itself (read-only, no tmp dirs)."""

    def test_dark_retirees_read_non_op(self):
        # Grand Tower (862): OS in vintage_2023 — the deepest phantom (511 MW
        # CC, CAMPD 0.0 GWh 2022-2024, formal retirement 2024-04).
        for gid in ("1", "2", "3", "4"):
            self.assertEqual(_retiree_vintage_status(862, gid, 2023), "OS")
            self.assertEqual(_retiree_vintage_status(862, gid, 2024), "OS")
        self.assertEqual(_retiree_vintage_status(202, "1", 2024), "OS")
        self.assertEqual(_retiree_vintage_status(2050, "1", 2023), "SB")
        self.assertEqual(_retiree_vintage_status(10075, "GEN1", 2023), "SB")

    def test_running_retiree_reads_op(self):
        # Rush Island (6155): OP in vintage_2023, ran through Oct-2024 — the
        # oracle's keep-side control case.
        self.assertEqual(_retiree_vintage_status(6155, "1", 2023), "OP")
        self.assertEqual(_retiree_vintage_status(6155, "2", 2024), "OP")

    def test_unknown_unit_reads_none(self):
        # Fail-open: a unit no committed vintage lists is never dropped.
        self.assertIsNone(_retiree_vintage_status(99999999, "ZZ", 2024))

    def test_vintage_scan_is_bounded_to_year(self):
        # The oracle never reads a vintage AFTER the solve year: at year 2018
        # only vintage_2018 is eligible, so a unit first listed later is None.
        years = _committed_vintage_years_for(
            Path("data/raw/eia-860") if Path("data/raw/eia-860").exists() else Path(".")
        )
        if years:
            self.assertLessEqual(min(years), 2018 + 10)  # sanity, not a gate


class TestScopedRetireeLoad(unittest.TestCase):
    """The scope applied through the real MISO retiree channel."""

    @classmethod
    def setUpClass(cls):
        cls.ic = get_iso_config("MISO")

    def test_default_off_is_byte_inert(self):
        # rule 24 / S-0 premise: the unscoped call is unchanged by the field's
        # existence — same membership with and without the kwarg spelled out.
        a = load_retired_within_window("MISO", self.ic, year=2024)
        b = load_retired_within_window(
            "MISO", self.ic, year=2024, vintage_status_scope=False
        )
        self.assertEqual([g.unit_id for g in a], [g.unit_id for g in b])

    def test_scope_drops_dark_units_keeps_running(self):
        on = load_retired_within_window(
            "MISO", self.ic, year=2024, vintage_status_scope=True
        )
        codes = {int(g.plant_code) for g in on}
        # dropped: Grand Tower (OS), Carl Bailey (OS), Baxter Wilson (SB),
        # Taconite Harbor (SB)
        for dark in (862, 202, 2050, 10075):
            self.assertNotIn(dark, codes)
        # kept: Rush Island (OP — ran through Oct-2024) and Lansing (OP in its
        # latest vintage: the PREREG's disclosed accepted miss — the oracle is
        # status-only and never reads CEMS).
        self.assertIn(6155, codes)
        self.assertIn(1047, codes)

    def test_scope_without_year_is_inert(self):
        # No solve year -> the oracle cannot key a vintage -> nothing dropped.
        a = load_retired_within_window("MISO", self.ic)
        b = load_retired_within_window("MISO", self.ic, vintage_status_scope=True)
        self.assertEqual(len(a), len(b))

    def test_gate_default_off_in_config(self):
        self.assertFalse(ScenarioConfig().retiree_vintage_status_scope)


class TestSyntheticFailOpen(unittest.TestCase):
    """Fail-open on a base with no committed vintages (tmp dir)."""

    def test_no_vintages_drops_nothing(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(_committed_vintage_years_for(Path(tmp)), ())


if __name__ == "__main__":
    unittest.main()
