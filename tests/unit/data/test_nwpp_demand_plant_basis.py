"""NWPP plant-basis demand anchor (session NWPP-NEXT-3, 2026-09-25).

Owner ruling on ``FINDING-nwpp-45`` §8 = framing 2: anchor NWPP's served
requirement to the plant basis C1 scores on — EIA-930 hourly shape, EIA-923
plant energy. ``ScenarioConfig.nwpp_demand_plant_basis`` (GATED default off)
adds :func:`envelopes.nwpp_plant_basis_correction` to the NWPP-20 served
schedule. This file pins: (1) the default is off and the off path is
byte-identical; (2) the correction moves each non-native family's annual energy
exactly onto its plant-basis total on the family's own non-negative EIA-930
shape; (3) wind / solar are never touched; (4) an armed run fails closed on a
missing year and refuses to run without the carried-wind leg served; (5) the
committed artifact conforms to its schema and year set, and its construction
(closeout-nwpp-anchor) maps plants by their own EIA-923 class inside the
EIA-860 footprint without ever reading the keeper's fleet roster.
"""

from __future__ import annotations

import unittest
from unittest import mock

import numpy as np
import pandas as pd

from market_sim.config.paths import EIA_HOURLY_DIR, RAW_DIR


def _frame(n: int = 6) -> pd.DataFrame:
    """A tiny pool frame with every family column the anchor reads."""
    return pd.DataFrame(
        {
            "NG: COL": [10.0, 20.0, 30.0, 40.0, 50.0, 50.0][:n],
            "NG: NG": [5.0, 5.0, 10.0, -100.0, 20.0, 60.0][:n],
            "NG: NUC": [1.0] * n,
            "NG: WAT": [2.0] * n,
            "NG: SUN": [0.0, 1e6, 0.0, 0.0, 0.0, 0.0][:n],
            "NG: WND": [3.0] * n,
            "NG: OTH": [1.0] * n,
            "NG: OIL": [0.5] * n,
        }
    )


class TestCorrection(unittest.TestCase):
    """Pure arithmetic on a synthetic frame (no data needed)."""

    def _run(self, energy, frame=None, grid_sw=None):
        from market_sim.data.eia930 import envelopes as E

        frame = _frame() if frame is None else frame
        grid_sw = np.zeros(len(frame)) if grid_sw is None else grid_sw
        with mock.patch.object(E, "_nwpp_plant_basis_energy", return_value=energy):
            return E.nwpp_plant_basis_correction(2023, frame, grid_sw)

    def test_family_energy_lands_on_plant_basis_with_930_shape(self):
        frame = _frame()
        coal = frame["NG: COL"].to_numpy()
        target = float(coal.sum()) * 1.5
        out = self._run({"COL": target}, frame)
        np.testing.assert_allclose(out.sum(), target - coal.sum())
        np.testing.assert_allclose(out, (target - coal.sum()) * coal / coal.sum())

    def test_negative_hours_take_no_share_and_grid_sw_is_netted_from_gas(self):
        frame = _frame()
        grid_sw = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 10.0])
        gas = frame["NG: NG"].to_numpy() - grid_sw
        out = self._run({"NG": 100.0}, frame, grid_sw)
        self.assertEqual(out[3], 0.0)  # the -100 MW unit-slip print
        np.testing.assert_allclose(out.sum(), 100.0 - gas.sum())

    def test_oth_family_is_oth_plus_oil(self):
        frame = _frame()
        base = (frame["NG: OTH"] + frame["NG: OIL"]).to_numpy()
        out = self._run({"OTH": float(base.sum())}, frame)
        np.testing.assert_allclose(out, 0.0, atol=1e-12)

    def test_wind_and_solar_are_never_touched(self):
        out = self._run({"SUN": 0.0, "WND": 1e9})
        np.testing.assert_array_equal(out, 0.0)

    def test_unknown_family_fails(self):
        from market_sim.data.eia930.envelopes import NwppPlantBasisUnavailableError

        with self.assertRaises(NwppPlantBasisUnavailableError):
            self._run({"XYZ": 1.0})


class TestGateAndArtifact(unittest.TestCase):
    """Default-off, fail-closed, and the committed artifact's integrity."""

    def test_default_off(self):
        from market_sim.config.scenarios import ScenarioConfig

        self.assertFalse(ScenarioConfig().nwpp_demand_plant_basis)

    def test_missing_year_fails_closed(self):
        from market_sim.data.eia930.envelopes import (
            NwppPlantBasisUnavailableError,
            _nwpp_plant_basis_energy,
        )

        with self.assertRaises(NwppPlantBasisUnavailableError):
            _nwpp_plant_basis_energy(1990)

    def test_artifact_conforms_to_its_schema_and_year_set(self):
        """The committed CSV validates and carries every keeper year once per family."""
        mod = _derive_module()
        from market_sim.data.eia930.envelopes import NWPP_PLANT_BASIS_ENERGY_PATH

        table = pd.read_csv(NWPP_PLANT_BASIS_ENERGY_PATH)
        mod.validate_rows(table.to_dict("records"))
        self.assertEqual(sorted(set(table["year"])), list(mod.YEARS))
        self.assertFalse(table.duplicated(["year", "family"]).any())
        for year, sub in table.groupby("year"):
            fams = set(sub["family"])
            if mod.is_preliminary(int(year)):
                self.assertEqual(fams, set(mod.PRELIMINARY_VINTAGE_FAMILIES))
            else:
                self.assertTrue({"COL", "NG", "NUC", "WAT", "OTH"} <= fams)


def _derive_module():
    """Import the derive script as a module."""
    import importlib.util

    from tests.helpers import REPO_ROOT

    spec = importlib.util.spec_from_file_location(
        "derive_nwpp_plant_basis_energy",
        REPO_ROOT / "scripts" / "data" / "derive_nwpp_plant_basis_energy.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _generation(rows) -> pd.DataFrame:
    """A tiny EIA-923 Page-1 frame: (year, plant_id, fuel, prime mover, chp, MWh)."""
    return pd.DataFrame(
        rows,
        columns=[
            "year",
            "plant_id",
            "fuel_type",
            "prime_mover",
            "chp",
            "netgen_annual_mwh",
        ],
    )


class TestRosterIndependentConstruction(unittest.TestCase):
    """closeout-nwpp-anchor: the anchor never reads the keeper's fleet roster."""

    def _class_map(self, generation, year, footprint):
        from scripts import run_calibration_full as rcf

        mod = _derive_module()
        boom = mock.Mock(side_effect=AssertionError("fleet roster read"))
        with (
            mock.patch.object(rcf, "_iso_plant_ids", return_value=frozenset(footprint)),
            mock.patch.object(rcf, "_fleet_group_by_code", boom),
            mock.patch("market_sim.data.fleet.load_fleet_from_csv", boom),
        ):
            return mod.plant_class_map(year, generation)

    def test_dominant_eia923_class_within_the_footprint(self):
        gen = _generation(
            [
                # A coal plant with a little gas co-firing: coal, whatever a
                # fleet's current gas-conversion designation says.
                (2019, 1, "SUB", "ST", "N", 2_800_000.0),
                (2019, 1, "NG", "ST", "N", 27_000.0),
                # A biomass host with a small gas turbine: biomass.
                (2019, 2, "WDS", "ST", "N", 300_000.0),
                (2019, 2, "NG", "GT", "N", 18_000.0),
                # Outside the footprint: never mapped.
                (2019, 9, "NG", "CT", "N", 1e6),
            ]
        )
        out = self._class_map(gen, 2019, {1, 2})
        self.assertEqual(set(out), {1, 2})
        self.assertTrue(out[1].startswith("COAL"))
        self.assertEqual(out[2], "biomass")

    def test_silent_year_takes_the_latest_prior_reporting_year(self):
        from scripts import run_calibration_full as rcf

        gen = _generation(
            [
                (2020, 1, "SUB", "ST", "N", 2_000_000.0),  # older year: coal
                (2021, 1, "SUB", "ST", "N", 10.0),
                (2021, 1, "WDS", "ST", "N", 900_000.0),  # latest reporting year
                (2023, 1, "WDS", "ST", "N", 0.0),  # silent in the solve year
            ]
        )
        self.assertEqual(self._class_map(gen, 2023, {1}), {1: "biomass"})
        old = 2023 - rcf._CLASS_SHARE_MAX_PRIOR_YEARS - 1
        gen_old = _generation([(old, 1, "NG", "CT", "N", 1.0)])
        self.assertEqual(self._class_map(gen_old, 2023, {1}), {})

    def test_family_sum_fails_on_an_unmapped_class(self):
        mod = _derive_module()
        with self.assertRaises(ValueError):
            mod.family_energy({"NOT_A_CLASS": 1.0}, 2019)

    def test_preliminary_vintage_keeps_only_the_repaired_fossil_families(self):
        mod = _derive_module()
        cls = {"COAL_PRB": 1.0, "CC_REGULAR": 2.0, "hydro": 3.0, "biomass": 0.5}
        with mock.patch.object(mod, "is_preliminary", return_value=True):
            self.assertEqual(mod.family_energy(cls, 2025), {"COL": 1.0, "NG": 2.0})
        with mock.patch.object(mod, "is_preliminary", return_value=False):
            self.assertEqual(
                mod.family_energy(cls, 2023),
                {"COL": 1.0, "NG": 2.0, "WAT": 3.0, "OTH": 0.5},
            )


def _hydrated() -> bool:
    return (EIA_HOURLY_DIR / "GRID hourly.parquet").exists() and (
        RAW_DIR / "eia-930-interchange" / "GRID interchange hourly.parquet"
    ).exists()


@unittest.skipUnless(_hydrated(), "NWPP member extracts not hydrated")
class TestOnCommittedData(unittest.TestCase):
    """The gate on the real pool frame."""

    def test_off_is_byte_identical_and_arm_requires_wind_served(self):
        from market_sim.data.eia930.envelopes import nwpp_net_interchange

        base = nwpp_net_interchange(2023, grid_carried_wind_served=True)
        off = nwpp_net_interchange(
            2023, grid_carried_wind_served=True, plant_basis=False
        )
        np.testing.assert_array_equal(base, off)
        with self.assertRaises(ValueError):
            nwpp_net_interchange(2023, plant_basis=True)

    def test_arm_adds_the_correction(self):
        from market_sim.data.eia930.envelopes import nwpp_net_interchange

        base = nwpp_net_interchange(2023, grid_carried_wind_served=True)
        armed = nwpp_net_interchange(
            2023, grid_carried_wind_served=True, plant_basis=True
        )
        delta = float((armed - base).sum()) / 1e6
        # PRECOMMIT-nwppnext3 §1: +7.726 TWh in 2023.
        self.assertGreater(delta, 7.5)
        self.assertLess(delta, 8.0)


if __name__ == "__main__":
    unittest.main()
