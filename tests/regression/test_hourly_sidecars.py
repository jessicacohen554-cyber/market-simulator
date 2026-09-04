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
