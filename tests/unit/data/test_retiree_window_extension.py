"""Guards for the within-window retiree artifact when its window widens.

``RETIREMENT_WINDOW_START`` moved 2023 -> 2019 (session xiso-fuelvintage-1,
executing ``docs/handoffs/fleet-vintage-retiree-window-charter-2026-08.md``)
so that units which retired inside 2019-2022 are present in the 2019-2022
backcast fleets instead of silently absent. The widening must be strictly
ADDITIVE: EIA prunes older retirements from each release, so the release
vintages that supplied the shipped 2023/2024 rows are no longer on disk and a
bare rebuild would DROP 161 real units rather than add any. These tests pin
that property, the whole-plant invariant the injection relies on, and the COD
ramp's behaviour on both edges of a pre-2023 retirement.
"""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data.cod_ramp import monthly_online_mask
from scripts.data.process_eia860 import (
    RETIREMENT_WINDOW_START,
    RETIRED_WITHIN_WINDOW_PARQUET,
    build_within_window_retirees,
)

EIA_860 = Path("data/raw/eia-860")
WINDOW_PARQUET = EIA_860 / RETIRED_WITHIN_WINDOW_PARQUET
OPERABLE_PARQUET = EIA_860 / "eia860_generator_operable.parquet"
KEY = ["plant_id", "generator_id"]

# The artifact EXACTLY as shipped before the window widened: 477 units, all
# retiring 2023-2024, sha256 of its key-sorted CSV projection. Every one of
# these rows must survive the widening byte-identically -- if this hash moves,
# the rebuild MOVED existing rows instead of adding new ones, which would
# silently re-key every committed bundle. That is a STOP condition, never a
# hash to update.
_PRE_EXTENSION_ROWS = 477
# Hashed over ALPHABETICALLY-ORDERED columns: the shipped parquet predates
# ``planned_retirement_month`` joining EIA_860_CSV_COLUMNS, so its physical
# column order is stale while its CONTENT is canonical. Consumers read by
# name, so content is what this pins.
# F1 (2026-09-24): re-pinned from b1f1a953...0627 (which covered heat_rate) to
# the SAME rows' projection WITHOUT heat_rate, which F1 re-joins at each unit's
# own eGRID vintage. Verified at the re-pin: the pre-F1 artifact reproduces the
# old hash exactly, and its heat_rate-less projection equals the post-F1 one.
_PRE_EXTENSION_SHA256 = (
    "11ba7b7aa669fed22aecaf8499ce362b8f05e890023c5dfd2d42e221749b0d2d"
)
_PRE_EXTENSION_BY_YEAR = {2023: (325, 9474.5), 2024: (152, 5413.0)}


#: The balancing authorities F1 appended to the retiree artifact (NWPP's pool
#: members and SOCO), which the pre-extension build never admitted.
_F1_APPENDED_BAS = frozenset(
    {"BPAT", "GCPD", "IPCO", "NEVP", "PACE", "PACW", "PGE", "SOCO", "WAUW"}
)


def _frame_sha256(frame: pd.DataFrame) -> str:
    """Return the sha256 of a frame's column- and key-sorted CSV projection."""
    ordered = frame[sorted(frame.columns)].sort_values(KEY).reset_index(drop=True)
    return hashlib.sha256(ordered.to_csv(index=False).encode()).hexdigest()


class TestCodRampEdgesOnAPreWindowRetirement(unittest.TestCase):
    """The COD ramp masks a 2021 retiree correctly on BOTH edges (synthetic)."""

    def test_online_before_partial_during_absent_after(self):
        # A 1980-vintage unit retiring 2021-06: fully online in 2020, online
        # only through June in 2021, and gone for every month of 2022.
        args = (1980, 1, 2021, 6)
        np.testing.assert_array_equal(
            monthly_online_mask(*args, run_year=2020), np.ones(12, dtype=bool)
        )
        expected_2021 = np.array([m <= 6 for m in range(1, 13)])
        np.testing.assert_array_equal(
            monthly_online_mask(*args, run_year=2021), expected_2021
        )
        np.testing.assert_array_equal(
            monthly_online_mask(*args, run_year=2022), np.zeros(12, dtype=bool)
        )

    def test_pre_cod_edge_still_masks(self):
        # The build edge is untouched by the widening: a unit commissioned
        # 2021-09 is absent in 2020 and online from September in 2021.
        args = (2021, 9, None, None)
        np.testing.assert_array_equal(
            monthly_online_mask(*args, run_year=2020), np.zeros(12, dtype=bool)
        )
        np.testing.assert_array_equal(
            monthly_online_mask(*args, run_year=2021),
            np.array([m >= 9 for m in range(1, 13)]),
        )


class TestPreserveIsStrictlyAdditive(unittest.TestCase):
    """``preserve`` rows win every shared key; only new keys are appended.

    Trivial synthetic case first (CLAUDE.md testing pattern): a two-unit
    vintage directory written to a tmp dir, read through the real builder.
    """

    @staticmethod
    def _sheet(rows: list[dict]) -> pd.DataFrame:
        """Return a minimal EIA-860 'Retired and Canceled' sheet."""
        return pd.DataFrame(
            [
                {
                    "Plant Code": r["plant"],
                    "Generator ID": r["gid"],
                    "Plant Name": f"P{r['plant']}",
                    "State": "XX",
                    "Technology": "Natural Gas Steam Turbine",
                    "Energy Source 1": "NG",
                    "Prime Mover": "ST",
                    "Nameplate Capacity (MW)": r["mw"],
                    "Summer Capacity (MW)": r["mw"],
                    "Operating Year": 1970,
                    "Operating Month": 1,
                    "Retirement Year": r["year"],
                    "Retirement Month": 12,
                    "Status": "RE",
                }
                for r in rows
            ]
        )

    def _vintage(self, tmp: Path, rows: list[dict]) -> Path:
        vdir = tmp / "vintage"
        vdir.mkdir(exist_ok=True)
        self._sheet(rows).to_parquet(
            vdir / "eia860_generator_retired_and_canceled.parquet", index=False
        )
        pd.DataFrame(
            [
                {"Plant Code": r["plant"], "Balancing Authority Code": "MISO"}
                for r in rows
            ]
        ).to_parquet(vdir / "eia860_plant.parquet", index=False)
        return vdir

    def test_shared_key_keeps_preserved_record_and_new_key_is_added(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            vdir = self._vintage(
                tmp,
                [
                    # Same key as the preserved row, but a DIFFERENT capacity.
                    {"plant": 1, "gid": "A", "year": 2023, "mw": 999.0},
                    # Genuinely new, inside the widened window.
                    {"plant": 2, "gid": "B", "year": 2021, "mw": 50.0},
                ],
            )
            preserve = build_within_window_retirees(
                [vdir], tmp / "absent-operable.parquet", cutoff_year=2023
            )
            self.assertEqual(len(preserve), 1)
            preserve = preserve.assign(nameplate_capacity_mw=100.0)

            out = build_within_window_retirees(
                [vdir],
                tmp / "absent-operable.parquet",
                cutoff_year=2019,
                preserve=preserve,
            )
        self.assertEqual(len(out), 2)
        a = out[out["generator_id"] == "A"]
        self.assertEqual(float(a["nameplate_capacity_mw"].iloc[0]), 100.0)
        b = out[out["generator_id"] == "B"]
        self.assertEqual(int(b["planned_retirement_year"].iloc[0]), 2021)

    def test_until_year_bounds_the_newly_read_rows(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            vdir = self._vintage(
                tmp,
                [
                    {"plant": 3, "gid": "C", "year": 2021, "mw": 10.0},
                    {"plant": 4, "gid": "D", "year": 2024, "mw": 20.0},
                ],
            )
            out = build_within_window_retirees(
                [vdir],
                tmp / "absent-operable.parquet",
                cutoff_year=2019,
                until_year=2023,
            )
        self.assertEqual(list(out["generator_id"]), ["C"])

    def test_builder_with_no_sources_returns_schema(self):
        out = build_within_window_retirees([], OPERABLE_PARQUET)
        self.assertTrue(out.empty)


@unittest.skipUnless(WINDOW_PARQUET.exists(), "EIA-860 data profile not hydrated")
class TestCommittedArtifactInvariants(unittest.TestCase):
    """The on-disk artifact after the widening."""

    @classmethod
    def setUpClass(cls):
        window = pd.read_parquet(WINDOW_PARQUET)
        # F1 (2026-09-24) appended the NWPP / SOCO balancing authorities the
        # artifact predated (``process_eia860.rescope_retired_window``, strictly
        # additive) and re-joined ``heat_rate`` at each unit's own eGRID vintage.
        # Neither moves a pre-extension row's identity, so these invariants are
        # asserted over the pre-F1 BA set, ex the re-joined column.
        cls.window = window[
            ~window["balancing_authority_code"].astype(str).isin(_F1_APPENDED_BAS)
        ].drop(columns=["heat_rate"])

    def test_pre_extension_rows_are_byte_identical(self):
        """The 2023+ subset still hashes to the pre-extension artifact.

        A failure here means the rebuild MOVED existing rows. Do not update
        the hash -- root-cause it (it would silently re-key every committed
        bundle whose fleet reads this artifact).
        """
        legacy = self.window[self.window["planned_retirement_year"] >= 2023]
        self.assertEqual(len(legacy), _PRE_EXTENSION_ROWS)
        for year, (units, mw) in _PRE_EXTENSION_BY_YEAR.items():
            rows = legacy[legacy["planned_retirement_year"] == year]
            self.assertEqual(len(rows), units, f"{year} unit count moved")
            self.assertAlmostEqual(
                float(rows["net_summer_capacity_mw"].sum()), mw, places=4
            )
        self.assertEqual(_frame_sha256(legacy), _PRE_EXTENSION_SHA256)

    def test_widening_added_nothing_inside_the_training_window(self):
        """No row was ADDED at retirement year >= 2023.

        The currently-committed release sheet carries 107 units / 497.7 MW of
        2023-2025 retirements the original build's (now-unavailable) vintages
        did not — a real, separate gap (see
        docs/FINDING-xiso-fuelvintage-retiree-window-2026-09-09.md §2). Adding
        them here would change every ISO's 2023-2025 TRAINING fleet and re-key
        every committed keeper bundle, so the widening is bounded above by
        ``--retired-until-year 2023``.
        """
        legacy = self.window[self.window["planned_retirement_year"] >= 2023]
        self.assertEqual(len(legacy), _PRE_EXTENSION_ROWS)

    def test_window_covers_the_declared_start_year(self):
        self.assertGreaterEqual(
            int(self.window["planned_retirement_year"].min()),
            RETIREMENT_WINDOW_START,
        )
        self.assertLess(
            int(self.window["planned_retirement_year"].min()),
            2023,
            "the widening added no pre-2023 rows",
        )

    def test_no_duplicate_unit_keys(self):
        self.assertFalse(self.window.duplicated(subset=KEY).any())

    @unittest.skipUnless(OPERABLE_PARQUET.exists(), "operable parquet absent")
    def test_no_plant_overlaps_the_operable_snapshot(self):
        """Whole-plant exits only: no injected plant is also dispatched.

        The injection is plant-keyed, so a plant present in BOTH sheets would
        be double-counted in every solve year (the COD map would hold the
        whole plant online).
        """
        op = pd.read_parquet(OPERABLE_PARQUET, columns=["Plant Code"])
        op_ids = set(
            pd.to_numeric(op["Plant Code"], errors="coerce").dropna().astype(int)
        )
        overlap = sorted(set(self.window["plant_id"].astype(int)) & op_ids)
        self.assertEqual(overlap, [], f"plants in both sheets: {overlap[:10]}")

    def test_multi_vintage_plants_age_out_PER_UNIT_not_plant_collapsed(self):
        """A plant whose units retired in DIFFERENT years ages out per unit.

        Widening the window to 2019 created injected plants whose units retire
        up to FOUR years apart (AES Redondo Beach 356: gen 7 in 2019-10, gens
        5/6/8 in 2023-12). ``_load_cod_map`` collapses a plant's heterogeneous
        retirements to the LATEST one, so a plant-keyed mask would hold gen 7's
        480 MW online for three extra years -- 31 units / 4,779.2 MW across the
        artifact if it did.

        It does not: ``cod_ramp.effective_cod`` prefers a generator's OWN
        retirement over the plant-collapsed date whenever the row carries one
        (the Homer City seam, plant 3122), and every retiree row carries one by
        construction. This test pins that, because it is the property a future
        change to the COD map would silently break, and because session
        caiso-fuelvintage-1 reported it as a defect on 2026-09-09 -- measured
        here as a NON-defect.
        """
        from market_sim.config.paths import EIA_860_DIR
        from market_sim.data.cod_ramp import _load_cod_map, effective_cod

        multi = self.window.groupby("plant_id")["planned_retirement_year"].nunique()
        multi_ids = set(multi[multi > 1].index)
        self.assertGreater(len(multi_ids), 0, "no multi-vintage plant to test")

        cod_map = _load_cod_map(EIA_860_DIR)
        for row in self.window[self.window["plant_id"].isin(multi_ids)].itertuples():
            _, _, ret_year, ret_month = effective_cod(
                int(row.plant_id),
                int(row.operating_year or 1970),
                int(row.operating_month or 1),
                int(row.planned_retirement_year),
                int(row.planned_retirement_month),
                cod_map,
            )
            self.assertEqual(
                (ret_year, ret_month),
                (int(row.planned_retirement_year), int(row.planned_retirement_month)),
                f"plant {row.plant_id} gen {row.generator_id} took the "
                f"plant-collapsed retirement instead of its own",
            )

    def test_a_units_own_retirement_wins_over_a_later_plant_date(self):
        """The synthetic form of the above: unit 2019-10, plant map 2023-12."""
        from market_sim.data.cod_ramp import effective_cod

        cod_map = {356: (1964, 7, 2023, 12)}
        _, _, ret_year, ret_month = effective_cod(356, 1967, 6, 2019, 10, cod_map)
        self.assertEqual((ret_year, ret_month), (2019, 10))
        np.testing.assert_array_equal(
            monthly_online_mask(1967, 6, ret_year, ret_month, run_year=2020),
            np.zeros(12, dtype=bool),
        )

    def test_every_row_carries_a_retirement_month(self):
        """The COD ramp needs a month to time a mid-year exit."""
        missing = self.window["planned_retirement_month"].isna().sum()
        self.assertEqual(int(missing), 0)


if __name__ == "__main__":
    unittest.main()
