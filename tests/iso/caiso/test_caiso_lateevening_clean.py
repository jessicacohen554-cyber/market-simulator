"""caiso-269 LATE-EVENING (hod 22-23) DSW clean-depth window-gap tranche.

Guards the four properties the arm rests on:

* **Builder gate** — the row exists only when the flag is on, so the arm is
  byte-identical off (the LP column set is unchanged).
* **Registry** — EF 0 and the no-wheel WEIM delivery basis, both measured for
  these two hours by caiso-253's G-WEDGE and raw-hub legs rather than
  inherited from the neighbouring windows.
* **Footprint** — the armed capability is EXACTLY zero outside hod 22-23, so
  the mechanism cannot reach any hour the sibling constructions own
  (rule 19 ``[R-ONE-MECH]``).
* **Admissibility gate** — the arm honours caiso-253's refusal: a
  (month x hod) bucket whose measured DA CAISO-PaloVerde median spread falls
  outside the pre-registered band never arms, which is why 2023 stays largely
  dark while 2024/2025 arm.
"""

import unittest

import numpy as np

from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.model.interchange.spec import (
    CAISO_DSW_LATEEVENING_CLEAN_DEPTH_BY_YEAR,
    CAISO_DSW_LATEEVENING_CLEAN_NAME,
    CAISO_IMPORT_DELIVERY_BASIS,
    CAISO_LATEEVENING_CLEAN_HOD_MAX,
    CAISO_LATEEVENING_CLEAN_HOD_MIN,
    CAISO_LATEEVENING_SPREAD_BAND,
    CAISO_PER_HUB_IMPORT_ZONES,
    IMPORT_TRANCHE_EF,
)
from market_sim.model.transmission import (
    build_caiso_per_hub_intertie,
    inject_caiso_dsw_daytime_clean,
    inject_caiso_dsw_lateevening_clean,
    inject_caiso_dsw_overnight_clean,
    inject_caiso_dsw_surplus_clean,
    inject_caiso_firm_import_shape,
)

HOURS = 8760
ZONE = CAISO_PER_HUB_IMPORT_ZONES["PALOVRDE"]
UID = f"{ZONE}_{CAISO_DSW_LATEEVENING_CLEAN_NAME}"


def _armed_fleet(year):
    gens = build_caiso_per_hub_intertie(
        surplus_clean=True,
        overnight_clean=True,
        daytime_clean=True,
        lateevening_clean=True,
    )
    zones = sorted({g.zone for g in gens})
    fleet = generators_to_fleet_arrays(gens, zones, hours=HOURS)
    inject_caiso_firm_import_shape(fleet, "CAISO", year, envelope_clip=True)
    inject_caiso_dsw_surplus_clean(fleet, "CAISO", year)
    inject_caiso_dsw_overnight_clean(fleet, "CAISO", year)
    inject_caiso_dsw_daytime_clean(fleet, "CAISO", year)
    armed = inject_caiso_dsw_lateevening_clean(fleet, "CAISO", year)
    row = list(fleet.unit_ids).index(UID)
    return fleet, row, armed


class TestBuilderGate(unittest.TestCase):
    def test_off_has_no_lateevening_row(self):
        gens = build_caiso_per_hub_intertie(
            surplus_clean=True, overnight_clean=True, daytime_clean=True
        )
        self.assertNotIn(UID, [g.unit_id for g in gens])

    def test_on_adds_only_that_row_at_zero_capacity(self):
        off = build_caiso_per_hub_intertie(
            surplus_clean=True, overnight_clean=True, daytime_clean=True
        )
        on = build_caiso_per_hub_intertie(
            surplus_clean=True,
            overnight_clean=True,
            daytime_clean=True,
            lateevening_clean=True,
        )
        self.assertEqual(
            [g.unit_id for g in off],
            [g.unit_id for g in on if g.unit_id != UID],
        )
        row = next(g for g in on if g.unit_id == UID)
        self.assertEqual(row.pmax_mw, 0.0)
        self.assertEqual(row.zone, ZONE)


class TestRegistry(unittest.TestCase):
    def test_clean_ef_and_no_wheel_basis(self):
        self.assertEqual(
            IMPORT_TRANCHE_EF["CAISO"][CAISO_DSW_LATEEVENING_CLEAN_NAME], 0.0
        )
        self.assertEqual(
            CAISO_IMPORT_DELIVERY_BASIS[CAISO_DSW_LATEEVENING_CLEAN_NAME], (0.0, 0.0)
        )

    def test_window_is_the_gap_the_siblings_leave(self):
        self.assertEqual(CAISO_LATEEVENING_CLEAN_HOD_MIN, 22)
        self.assertEqual(CAISO_LATEEVENING_CLEAN_HOD_MAX, 23)

    def test_band_is_caiso253s_pre_registered_one(self):
        self.assertEqual(CAISO_LATEEVENING_SPREAD_BAND, (-2.0, 4.0))


class TestFootprint(unittest.TestCase):
    def test_capability_is_zero_outside_hod_22_23(self):
        hod = np.arange(HOURS) % 24
        for year in (2023, 2024, 2025):
            with self.subTest(year=year):
                fleet, row, armed = _armed_fleet(year)
                self.assertTrue(armed)
                cap = fleet.pmax[row] * fleet.availability[row, :]
                outside = (hod < CAISO_LATEEVENING_CLEAN_HOD_MIN) | (
                    hod > CAISO_LATEEVENING_CLEAN_HOD_MAX
                )
                self.assertEqual(float(cap[outside].max()), 0.0)
                self.assertGreater(float(cap.max()), 0.0)
                self.assertEqual(
                    float(fleet.pmax[row]),
                    CAISO_DSW_LATEEVENING_CLEAN_DEPTH_BY_YEAR[year],
                )


class TestAdmissibilityGate(unittest.TestCase):
    def test_2023_is_kept_dark_relative_to_2024_and_2025(self):
        """caiso-253 refused hod 22-23 raw-hub pricing on 2023's discriminator.

        The gate is that refusal, so 2023 must arm in far fewer hours than the
        years whose block medians cleared the band (-0.36 / -0.03 against
        2023's -3.21).
        """
        armed_hours = {}
        for year in (2023, 2024, 2025):
            fleet, row, _ = _armed_fleet(year)
            cap = fleet.pmax[row] * fleet.availability[row, :]
            armed_hours[year] = int((cap > 0.0).sum())
        self.assertLess(armed_hours[2023], armed_hours[2024])
        self.assertLess(armed_hours[2023], armed_hours[2025])
        self.assertLess(armed_hours[2023], 0.5 * armed_hours[2024])


if __name__ == "__main__":
    unittest.main()
