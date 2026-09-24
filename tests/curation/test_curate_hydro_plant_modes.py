"""Tests for the hydro-plant-modes curation (caiso-126 RoR-split classifier).

Tiny synthetic EHA/HILARRI fixtures exercise every classification rule of
``scripts.data.curate_hydro_plant_modes`` (trivial case first per the repo
testing pattern), through the frozen ``clean_io`` seam into a redirected
``CLEAN_DIR``.
"""

from __future__ import annotations

import pandas as pd

from scripts.data.curate_hydro_plant_modes import curate
from scripts.lib import clean_io
from tests.helpers.base import RawFixtureTestCase


def _write_eha(path, rows: list[dict]) -> None:
    """Write a minimal EHA xlsx with only the columns the curator reads."""
    defaults = {
        "EHA_PtID": "hcX",
        "PtName": "Plant",
        "BACode": "CISO",
        "EIA_PtID": 1.0,
        "CH_MW": 10.0,
        "Mode": None,
        "FC_Dock": None,
        "Dam_Own": "Some Utility",
    }
    frame = pd.DataFrame([{**defaults, **r} for r in rows])
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path) as xl:
        frame.to_excel(xl, sheet_name="Operational", index=False)


def _write_hilarri(path, rows: list[dict]) -> None:
    """Write a minimal HILARRI csv with only the columns the curator reads."""
    defaults = {
        "eha_ptid": "hcX",
        "dataset": "Hydropower dam associated with power plant; no reservoir",
        "prjct_type": "Conventional hydropower",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{**defaults, **r} for r in rows]).to_csv(path, index=False)


class TestCurateHydroPlantModes(RawFixtureTestCase):
    """Rule-by-rule classification through the clean_io contract."""

    def _curate(self, eha_rows, hilarri_rows, iso: str = "CAISO") -> pd.DataFrame:
        _write_eha(
            self.raw_dir / "ornl-eha" / "ORNL_EHAHydroPlant_PublicFY2024.xlsx",
            eha_rows,
        )
        _write_hilarri(self.raw_dir / "hilarri" / "HILARRI_v4.csv", hilarri_rows)
        paths = curate(raw_root=self.raw_dir, isos=[iso])
        self.assertEqual(len(paths), 1)
        clean_io.validate_clean(paths[0])
        return clean_io.read_clean("hydro-plant-modes", iso=iso)

    def test_single_labeled_plant(self) -> None:
        """Trivial case: one EHA-labeled peaking plant -> shapeable."""
        df = self._curate(
            [{"EHA_PtID": "hc1", "EIA_PtID": 100.0, "Mode": "Peaking"}],
            [{"eha_ptid": "hc1"}],
        )
        self.assertEqual(len(df), 1)
        row = df.iloc[0]
        self.assertEqual(row["plant_id"], 100)
        self.assertTrue(row["shapeable"])
        self.assertEqual(row["method"], "eha_mode")

    def test_completion_rules(self) -> None:
        """Each Mode-NaN completion rule fires in its documented order."""
        resv = "Hydropower dam associated with reservoir and power plant"
        df = self._curate(
            [
                # rule 1: labeled RoR stays RoR even with a reservoir linked.
                {"EHA_PtID": "hc1", "EIA_PtID": 1.0, "Mode": "Run-of-river"},
                # rule 2: canal project type wins over its reservoir.
                {"EHA_PtID": "hc2", "EIA_PtID": 2.0},
                # rule 3: Corps dam -> release-taker.
                {"EHA_PtID": "hc3", "EIA_PtID": 3.0, "Dam_Own": "CESPK"},
                # rule 4: no reservoir association anywhere.
                {"EHA_PtID": "hc4", "EIA_PtID": 4.0},
                # rule 5: reservoir-associated, operator-controlled.
                {"EHA_PtID": "hc5", "EIA_PtID": 5.0},
            ],
            [
                {"eha_ptid": "hc1", "dataset": resv},
                {"eha_ptid": "hc2", "dataset": resv, "prjct_type": "Canal/conduit"},
                {"eha_ptid": "hc3", "dataset": resv},
                {"eha_ptid": "hc4"},
                {"eha_ptid": "hc5", "dataset": resv},
            ],
        )
        by_id = df.set_index("plant_id")
        self.assertFalse(by_id.loc[1, "shapeable"])
        self.assertEqual(by_id.loc[1, "method"], "eha_mode")
        self.assertFalse(by_id.loc[2, "shapeable"])
        self.assertEqual(by_id.loc[2, "method"], "hilarri_canal")
        self.assertFalse(by_id.loc[3, "shapeable"])
        self.assertEqual(by_id.loc[3, "method"], "corps_dam")
        self.assertFalse(by_id.loc[4, "shapeable"])
        self.assertEqual(by_id.loc[4, "method"], "hilarri_no_reservoir")
        self.assertTrue(by_id.loc[5, "shapeable"])
        self.assertEqual(by_id.loc[5, "method"], "hilarri_reservoir")

    def test_eia_id_aggregation_any_shapeable(self) -> None:
        """Two EHA plants on one EIA id: shapeable = any, capacity sums."""
        df = self._curate(
            [
                {
                    "EHA_PtID": "hc1",
                    "EIA_PtID": 9.0,
                    "Mode": "Run-of-river",
                    "CH_MW": 5.0,
                },
                {"EHA_PtID": "hc2", "EIA_PtID": 9.0, "Mode": "Peaking", "CH_MW": 7.0},
            ],
            [{"eha_ptid": "hc1"}, {"eha_ptid": "hc2"}],
        )
        self.assertEqual(len(df), 1)
        row = df.iloc[0]
        self.assertTrue(row["shapeable"])
        self.assertAlmostEqual(row["ch_mw"], 12.0)
        self.assertEqual(row["eha_ptid"], "hc1|hc2")

    def test_pumped_storage_and_other_ba_excluded(self) -> None:
        """CH_MW NaN (pure PS) and non-CISO rows never reach the table."""
        df = self._curate(
            [
                {"EHA_PtID": "hc1", "EIA_PtID": 1.0, "Mode": "Peaking"},
                {"EHA_PtID": "hc2", "EIA_PtID": 2.0, "CH_MW": float("nan")},
                {"EHA_PtID": "hc3", "EIA_PtID": 3.0, "BACode": "ERCO"},
            ],
            [{"eha_ptid": "hc1"}],
        )
        self.assertEqual(df["plant_id"].tolist(), [1])

    def test_regulated_chain_overrides_ror_label(self) -> None:
        """Rule 0: a registered chain plant is shapeable despite an RoR label.

        An off-chain RoR plant in the same ISO stays flat, and an ISO with no
        chain registry is classified by rules 1-5 alone (the CAISO tests above).
        """
        chain = self.raw_dir / "nwpp-hydro" / "nwpp_hydro_chain.csv"
        chain.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"plant_id": [1], "plant_name": ["John Day"]}).to_csv(
            chain, index=False
        )
        df = self._curate(
            [
                {
                    "EHA_PtID": "hc1",
                    "EIA_PtID": 1.0,
                    "Mode": "Run-of-river",
                    "BACode": "BPAT",
                },
                {
                    "EHA_PtID": "hc2",
                    "EIA_PtID": 2.0,
                    "Mode": "Run-of-river",
                    "BACode": "BPAT",
                },
            ],
            [{"eha_ptid": "hc1"}, {"eha_ptid": "hc2"}],
            iso="NWPP",
        )
        by_id = df.set_index("plant_id")
        self.assertTrue(by_id.loc[1, "shapeable"])
        self.assertEqual(by_id.loc[1, "method"], "regulated_chain")
        self.assertFalse(by_id.loc[2, "shapeable"])
        self.assertEqual(by_id.loc[2, "method"], "eha_mode")
