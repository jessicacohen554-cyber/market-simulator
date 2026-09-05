"""Committable ``hourly/`` bundle sidecars (run_calibration_full).

The slim-bundle gitignore rules drop every heavy solve output
(``dispatch/``, ``system.parquet``), so before these sidecars every
diagnostic session replayed the keeper to read its own hourlies. The
sidecar writers must (a) reconcile exactly with the unit-hour dispatch
frames they summarize, (b) cover every pass label written for the year,
and (c) write per-year system slices identical to the year's rows of the
full frame.
"""

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from scripts import run_calibration_full as rcf


def _unit_frame(year: int, pass_label: str, n_units: int = 3, T: int = 4):
    """Tiny synthetic unit-hour dispatch frame in the bundle schema."""
    rows = []
    for g in range(n_units):
        for t in range(T):
            rows.append(
                {
                    "year": year,
                    "pass": pass_label,
                    "unit_id": f"u{g}",
                    "klass": "CC_REGULAR" if g % 2 == 0 else "CT_PEAKER",
                    "hour": t,
                    "mw": float(10 * g + t),
                }
            )
    return pd.DataFrame(rows)


class ClassHourlySidecarTest(unittest.TestCase):
    def test_reconciles_with_unit_frames_across_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "dispatch").mkdir()
            for label in ("P0", "P1"):
                _unit_frame(2024, label).to_parquet(
                    run_dir / "dispatch" / f"2024_{label}.parquet", index=False
                )
            out = rcf._write_class_hourly_sidecar(run_dir, 2024, ["P0", "P1"])
            self.assertEqual(out, run_dir / "hourly" / "class_hourly_2024.parquet")
            ch = pd.read_parquet(out)
            self.assertEqual(
                sorted(ch.columns), ["hour", "klass", "mw", "pass", "year"]
            )
            self.assertEqual(set(ch["pass"]), {"P0", "P1"})
            # Class-hour totals reconcile with the unit frame they summarize.
            unit = pd.read_parquet(run_dir / "dispatch" / "2024_P1.parquet")
            want = unit.groupby(["klass", "hour"])["mw"].sum()
            got = (
                ch[ch["pass"] == "P1"]
                .groupby(["klass", "hour"])["mw"]
                .sum()
                .reindex(want.index)
            )
            np.testing.assert_allclose(got.to_numpy(), want.to_numpy())


class SystemYearSidecarTest(unittest.TestCase):
    def test_per_year_slices_match_full_frame(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            sysdf = pd.DataFrame(
                {
                    "year": [2024, 2024, 2025],
                    "pass": ["P1", "P1", "P1"],
                    "zone": ["North", "West", "North"],
                    "hour": [0, 0, 0],
                    "price": [30.0, 31.0, 45.0],
                    "demand": [100.0, 50.0, 110.0],
                }
            )
            rcf._write_system_year_sidecars(run_dir, sysdf)
            for year in (2024, 2025):
                got = pd.read_parquet(run_dir / "hourly" / f"system_{year}.parquet")
                want = sysdf[sysdf["year"] == year].reset_index(drop=True)
                pd.testing.assert_frame_equal(
                    got.reset_index(drop=True), want, check_dtype=False
                )


if __name__ == "__main__":
    unittest.main()


def _dual_fuel_unit_frame(year: int, pass_label: str, T: int = 4):
    """Unit-hour frame exercising the dual-fuel re-attribution.

    Two ``ST_GAS`` tranches of one bin. ``u_peak`` is oil-switched in the back
    half of the horizon, so its ``klass`` reads ``oil`` there while its
    ``klass_base`` stays ``ST_GAS`` — the exact shape that makes a ``klass``
    aggregate undercount the class (nyiso-179 §6.1 candidate (c)).
    """
    rows = []
    for unit, band in (
        ("ST_GAS_NYC_p1_committed", "committed"),
        ("ST_GAS_NYC_p1_peak", "peak"),
    ):
        for t in range(T):
            switched = band == "peak" and t >= T // 2
            rows.append(
                {
                    "year": year,
                    "pass": pass_label,
                    "unit_id": unit,
                    "klass": "oil" if switched else "ST_GAS",
                    "klass_base": "ST_GAS",
                    "hour": t,
                    "mw": float(10 + t),
                }
            )
    return pd.DataFrame(rows)


class TrancheBandTest(unittest.TestCase):
    """Only the closed LP tranche vocabulary counts as a band."""

    def test_real_tranche_suffixes_are_recognised(self):
        for uid, want in (
            ("ST_GAS_NYC_p1_committed", "committed"),
            ("CC_REGULAR_NYC_p2_econc03", "econc03"),
            ("COAL_West_p3_mustrun", "mustrun"),
            ("CC_CHP_NYC_p4_peak2", "peak2"),
            ("ST_GAS_NYC_p1_commitcyc", "commitcyc"),
        ):
            self.assertEqual(rcf._tranche_band(uid), want)

    def test_non_tranche_units_get_no_band(self):
        """Zone names, unit numbers and corridor labels are NOT bands."""
        for uid in (
            "WIND_Upstate_West",
            "SOLAR_NYC",
            "NYISO_external_HQ_tie",
            "hydro_Lower_Hudson",
            "import_scarcity",
            "PLANT_GEN1",
        ):
            self.assertEqual(rcf._tranche_band(uid), "")


class ClassBandHourlySidecarTest(unittest.TestCase):
    """``class_band_hourly`` — the per-offer-band dispatch sidecar."""

    def _write(self, tmp, labels=("P0", "P1")):
        run_dir = Path(tmp)
        (run_dir / "dispatch").mkdir()
        for label in labels:
            _dual_fuel_unit_frame(2024, label).to_parquet(
                run_dir / "dispatch" / f"2024_{label}.parquet", index=False
            )
        return run_dir, rcf._write_class_band_hourly_sidecar(
            run_dir, 2024, list(labels)
        )

    def test_schema_and_band_split(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, out = self._write(tmp)
            self.assertEqual(out, run_dir / "hourly" / "class_band_hourly_2024.parquet")
            cb = pd.read_parquet(out)
            self.assertEqual(
                sorted(cb.columns),
                ["band", "hour", "klass", "mw", "mw_oil", "pass", "year"],
            )
            # Band is the last underscore token of the unit id, and the two
            # tranches of one bin stay separate.
            self.assertEqual(set(cb["band"]), {"committed", "peak"})
            self.assertEqual(set(cb["pass"]), {"P0", "P1"})

    def test_klass_is_pre_reattribution_so_the_class_is_not_undercounted(self):
        """The whole point: ``klass`` here counts oil-switched hours too."""
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, out = self._write(tmp)
            cb = pd.read_parquet(out)
            cb = cb[cb["pass"] == "P1"]
            unit = pd.read_parquet(run_dir / "dispatch" / "2024_P1.parquet")
            # Every row is ST_GAS on the base key, including the switched ones.
            self.assertEqual(set(cb["klass"]), {"ST_GAS"})
            self.assertAlmostEqual(
                float(cb["mw"].sum()), float(unit["mw"].sum()), places=4
            )
            # ...whereas the klass key alone would have lost the switched MW.
            self.assertLess(
                float(unit[unit["klass"] == "ST_GAS"]["mw"].sum()),
                float(unit["mw"].sum()),
            )

    def test_mw_oil_reproduces_the_class_hourly_view(self):
        """``mw - mw_oil`` must equal what ``class_hourly`` reports per class."""
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, out = self._write(tmp)
            rcf._write_class_hourly_sidecar(run_dir, 2024, ["P0", "P1"])
            ch = pd.read_parquet(run_dir / "hourly" / "class_hourly_2024.parquet")
            cb = pd.read_parquet(out)
            for label in ("P0", "P1"):
                b = cb[cb["pass"] == label]
                h = ch[ch["pass"] == label]
                gas = (b[b["klass"] == "ST_GAS"]["mw"].sum()) - (
                    b[b["klass"] == "ST_GAS"]["mw_oil"].sum()
                )
                self.assertAlmostEqual(
                    float(gas),
                    float(h[h["klass"] == "ST_GAS"]["mw"].sum()),
                    places=4,
                )
                self.assertAlmostEqual(
                    float(b["mw_oil"].sum()),
                    float(h[h["klass"] == "oil"]["mw"].sum()),
                    places=4,
                )

    def test_returns_none_on_an_unreadable_placeholder_frame(self):
        """A reused-year bundle can carry a frame this process cannot read."""
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "dispatch").mkdir()
            (run_dir / "dispatch" / "2024_P1.parquet").write_text("x")
            self.assertIsNone(
                rcf._write_class_band_hourly_sidecar(run_dir, 2024, ["P1"])
            )

    def test_returns_none_on_a_frame_predating_klass_base(self):
        """Additive: an older bundle replays without the sidecar, never fails."""
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "dispatch").mkdir()
            _unit_frame(2024, "P1").to_parquet(
                run_dir / "dispatch" / "2024_P1.parquet", index=False
            )
            self.assertIsNone(
                rcf._write_class_band_hourly_sidecar(run_dir, 2024, ["P1"])
            )


class BandCategoricalTest(unittest.TestCase):
    """``_band_categorical`` == the per-row ``pd.Categorical([...])`` it replaced.

    Wallclock A-3: the band is computed once per distinct ``unit_id`` and
    indexed by the categorical codes. The gate is element-wise AND
    category-wise identity with the per-row construction on a frame covering
    every ``_TRANCHE_BANDS_EXACT`` token, every ``_TRANCHE_BANDS_PREFIX``
    family (with the numbered / ``peak2`` variants) and non-tranche ids.
    """

    #: Every exact token, every prefix family, and ids that are NOT tranches.
    UNIT_IDS = (
        [f"COAL_West_p3_{tok}" for tok in sorted(rcf._TRANCHE_BANDS_EXACT)]
        + [
            "CC_REGULAR_NYC_p2_sync",
            "CC_REGULAR_NYC_p2_sync1",
            "CC_REGULAR_NYC_p2_econc00",
            "CC_REGULAR_NYC_p2_econc12",
            "CT_PEAKER_NYC_p5_peak",
            "CC_CHP_NYC_p4_peak2",
        ]
        + [
            "WIND_Upstate_West",
            "SOLAR_NYC",
            "NYISO_external_HQ_tie",
            "hydro_Lower_Hudson",
            "import_scarcity",
            "PLANT_GEN1",
            "WECC_WEST_NET_IMPORT",
        ]
    )

    @staticmethod
    def _per_row(unit_ids: pd.Series) -> pd.Categorical:
        """The exact pre-A-3 construction, kept verbatim as the oracle."""
        return pd.Categorical([rcf._tranche_band(u) for u in unit_ids.astype(str)])

    def _assert_identical(self, got: pd.Categorical, want: pd.Categorical):
        self.assertIsInstance(got, pd.Categorical)
        self.assertTrue(got.categories.equals(want.categories))
        self.assertEqual(got.categories.dtype, want.categories.dtype)
        self.assertEqual(got.ordered, want.ordered)
        np.testing.assert_array_equal(got.codes, want.codes)
        self.assertTrue(pd.Series(got).equals(pd.Series(want)))

    def _frame_ids(self, T: int = 3, repeat: int = 2) -> list:
        # Interleave and repeat so codes are non-monotone and every id recurs.
        ids = list(self.UNIT_IDS) * repeat
        return [u for u in ids for _ in range(T)][::-1]

    def test_covers_every_token_and_matches_per_row_on_categorical_input(self):
        ids = self._frame_ids()
        col = pd.Series(pd.Categorical(ids))
        got = rcf._band_categorical(col)
        want = self._per_row(col)
        self._assert_identical(got, want)
        # The frame really exercised the whole vocabulary: every exact token,
        # every prefix family, and the non-tranche "" bucket.
        bands = set(got.categories)
        self.assertTrue(rcf._TRANCHE_BANDS_EXACT <= bands)
        for prefix in rcf._TRANCHE_BANDS_PREFIX:
            self.assertTrue(any(b.startswith(prefix) for b in bands), prefix)
        self.assertIn("", bands)

    def test_matches_per_row_on_plain_string_input(self):
        col = pd.Series(self._frame_ids())
        self._assert_identical(rcf._band_categorical(col), self._per_row(col))

    def test_unused_unit_category_does_not_invent_a_band(self):
        """Categories are the bands the ROWS carry, exactly as before."""
        cats = list(self.UNIT_IDS) + ["GHOST_p9_mustrun"]
        rows = [u for u in self.UNIT_IDS if not u.endswith("mustrun")]
        col = pd.Series(pd.Categorical(rows, categories=cats))
        got = rcf._band_categorical(col)
        self._assert_identical(got, self._per_row(col))
        self.assertNotIn("mustrun", set(got.categories))

    def test_missing_id_maps_to_the_empty_band_like_str_nan_did(self):
        col = pd.Series(pd.Categorical(["COAL_West_p3_peak", None, "SOLAR_NYC"]))
        self._assert_identical(rcf._band_categorical(col), self._per_row(col))

    def test_sidecar_band_column_matches_per_row_end_to_end(self):
        """The sidecar written through the new path equals a per-row rebuild."""
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "dispatch").mkdir()
            rows = []
            for i, uid in enumerate(self._frame_ids(T=4, repeat=1)):
                rows.append(
                    {
                        "year": 2024,
                        "pass": "P1",
                        "unit_id": uid,
                        "klass": "oil" if i % 7 == 0 else "ST_GAS",
                        "klass_base": "ST_GAS" if i % 2 else "CC_REGULAR",
                        "hour": i % 4,
                        "mw": float(i),
                    }
                )
            d = pd.DataFrame(rows)
            d["unit_id"] = pd.Categorical(d["unit_id"])
            d.to_parquet(run_dir / "dispatch" / "2024_P1.parquet", index=False)
            out = rcf._write_class_band_hourly_sidecar(run_dir, 2024, ["P1"])
            got = pd.read_parquet(out)
            # Oracle: the same aggregation with the per-row band construction.
            d["band"] = self._per_row(d["unit_id"])
            d["mw_oil"] = np.where(d["klass"].astype(str) == "oil", d["mw"], 0.0)
            want = (
                d.groupby(
                    ["year", "pass", "klass_base", "band", "hour"], observed=True
                )[["mw", "mw_oil"]]
                .sum()
                .reset_index()
                .rename(columns={"klass_base": "klass"})
            )
            want["mw"] = want["mw"].astype(np.float32)
            want["mw_oil"] = want["mw_oil"].astype(np.float32)
            for c in ("pass", "klass", "band"):
                want[c] = want[c].astype(str)
                got[c] = got[c].astype(str)
            pd.testing.assert_frame_equal(
                got.reset_index(drop=True),
                want.reset_index(drop=True),
                check_dtype=False,
            )
