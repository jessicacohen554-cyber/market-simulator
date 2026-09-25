"""DAM-first / CAMPD-fallback outage-overlay wiring for CAISO/MISO/NEISO/PJM.

Guards the four-ISO DAM-outage wiring (infra/dam-outage-wiring-4iso, 2026-07-24):
each ISO's published availability instrument is applied IN PLACE OF the CAMPD
unit-outage derate for the scope it covers, at the instrument's native grain,
and is a pure no-op when its gate is off. Synthetic-fleet, no-LP array builds
(``generators_to_fleet_arrays`` only — no dispatch solve), scoped to the
in-sample year 2023.

Two invariants per ISO:
  * ON-fires: with the gate on, the covered scope's availability changes.
  * OFF/fallback-contained: the scope the instrument does NOT cover is
    byte-identical between the gate-off and gate-on builds (the CAMPD/statistical
    fallback is untouched — no leakage, no double-count outside covered scope).
"""

from __future__ import annotations

import dataclasses
import unittest

import numpy as np

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.outages import _hour_of_year

_ZONES = ["Z"]

# The four DAM-gate fields live in ``scenarios.py`` (8242 lines), which exceeds
# the API-only push path's single-call emission limit, so that change ships as
# ``docs/handoffs/patches/dam-outage-wiring-4iso-scenarios.patch``. These tests
# require the fields; skip until the patch is applied so main stays green in the
# interim, and activate automatically once the fields exist (``arrays.py`` guards
# the same fields with ``getattr(..., False)``, so the wiring is an inert no-op
# until then).
_DAM_GATES_PRESENT = "caiso_dam_outages" in {
    f.name for f in dataclasses.fields(ScenarioConfig)
}


def _gen(pc: int, grp: str, ft: str, i: int, mw: float) -> Generator:
    return Generator(
        unit_id=f"{pc}_{i}",
        name=f"{grp}{i}",
        zone="Z",
        fuel_type=ft,
        pmax_mw=mw,
        pmin_mw=0.0,
        heat_rate=7.5,
        vom=2.0,
        emission_rate_co2=0.4,
        nox_rate=0.0,
        eford=0.05,
        online_year=2005,
        plant_code=pc,
        is_campd_bin=True,
        plant_group=grp,
    )


def _build(gens, iso, **overrides):
    cfg = ScenarioConfig(
        weather_year=2023,
        iso=iso,
        mode="backcast",
        outage_source="historic",
        **overrides,
    )
    return generators_to_fleet_arrays(
        gens, _ZONES, hours=HOURS_PER_YEAR, iso=iso, config=cfg, year=2023
    ).availability


@unittest.skipUnless(
    _DAM_GATES_PRESENT,
    "DAM gate fields not yet in ScenarioConfig — apply "
    "docs/handoffs/patches/dam-outage-wiring-4iso-scenarios.patch",
)
class DamOutageWiringTest(unittest.TestCase):
    def test_caiso_per_plant_precedence_and_fallback(self):
        """Per-plant grain: a DAM-covered plant moves; an uncovered plant keeps
        its CAMPD/statistical availability byte-for-byte."""
        from market_sim.data.caiso_outages import (
            caiso_dam_outage_derate_factors,
            has_dam_coverage,
        )

        covered = caiso_dam_outage_derate_factors(2023, iso="CAISO")
        if not covered:
            self.skipTest("CAISO DAM curtailment data not present in this checkout")
        (pc, grp) = next(iter(covered))  # a real DAM-covered (plant_code, group)
        gens = [
            _gen(pc, grp, "gas_cc", 1, 300.0),
            _gen(999_999, grp, "gas_cc", 1, 300.0),
        ]
        off = _build(gens, "CAISO")
        on = _build(gens, "CAISO", caiso_dam_outages=True)
        self.assertFalse(np.array_equal(off[0], on[0]), "covered plant must change")
        np.testing.assert_array_equal(off[1], on[1])  # uncovered plant unchanged
        # Coverage gate: pre-series years fall back (loader empty).
        self.assertFalse(has_dam_coverage(2020))

    def test_miso_envelope_replaces_and_year_fallback(self):
        """Aggregate grain: the envelope replaces CAMPD on a covered thermal bin;
        a year the record does not cover returns empty (CAMPD fallback)."""
        from market_sim.data.miso_outages import miso_native_outage_derate_factors

        env = miso_native_outage_derate_factors(2023, iso="MISO")
        if not env:
            self.skipTest("MISO outage-envelope data not present in this checkout")
        (pc, grp) = next(iter(env))
        gens = [_gen(pc, grp, "gas_st", 1, 300.0)]
        off = _build(gens, "MISO")
        on = _build(gens, "MISO", miso_native_outage_source=True)
        self.assertFalse(np.array_equal(off[0], on[0]), "covered bin must change")
        # Pre-2023: MISO publishes nothing -> empty -> the `if _dam:` guard keeps
        # CAMPD (loader-level check; no out-of-training solve or fleet build).
        self.assertEqual(miso_native_outage_derate_factors(2019, iso="MISO"), {})

    def test_neiso_pooled_fleet_fraction(self):
        """Fleet grain: pooled thermal availability moves on a covered day and is
        identical on an uncovered hour."""
        from market_sim.data.neiso_operable_capacity import (
            neiso_thermal_availability_series,
        )

        if not np.isfinite(neiso_thermal_availability_series(2023)).any():
            self.skipTest("NEISO operable-capacity data not present in this checkout")
        gens = [
            _gen(60001, "CC_REGULAR", "gas_cc", 1, 300.0),
            _gen(60002, "ST_GAS", "gas_st", 1, 200.0),
        ]
        off = _build(gens, "NEISO")
        on = _build(gens, "NEISO", neiso_operable_capacity_availability=True)
        d0 = _hour_of_year(2, 1, 0)
        self.assertFalse(np.array_equal(off[:, d0 : d0 + 24], on[:, d0 : d0 + 24]))
        unc = np.where(~np.isfinite(neiso_thermal_availability_series(2023)))[0]
        if unc.size:
            np.testing.assert_array_equal(off[:, unc[0]], on[:, unc[0]])

    def test_pjm_per_class_uniform_fraction(self):
        """Per-class grain: each covered fossil-thermal class moves on a covered
        day; an uncovered hour is identical."""
        from market_sim.data.pjm_outages import pjm_dam_availability_series

        pjm_series = pjm_dam_availability_series(2023)
        if not pjm_series:
            # PJM by-year CSVs are the fetched intake; they regenerate via
            # scripts/data/fetch_pjm_outages.py + derive_pjm_dam_availability.py
            # and are not committed, so a fresh checkout has no PJM outage data.
            self.skipTest("PJM outage data not present in this checkout")
        gens = [
            _gen(70001, "CC_REGULAR", "gas_cc", 1, 300.0),
            _gen(70002, "COAL_BIT", "coal", 1, 400.0),
        ]
        off = _build(gens, "PJM")
        on = _build(gens, "PJM", pjm_dam_availability=True)
        d0 = _hour_of_year(3, 15, 0)
        self.assertFalse(np.array_equal(off[:, d0 : d0 + 24], on[:, d0 : d0 + 24]))
        pser = next(iter(pjm_series.values()))
        unc = np.where(~np.isfinite(pser))[0]
        if unc.size:
            np.testing.assert_array_equal(off[:, unc[0]], on[:, unc[0]])

    def test_default_off_is_noop(self):
        """All four gates default False and leave availability at the pre-DAM
        (statistical/CAMPD) build — the wiring is inert unless armed."""
        cfg = ScenarioConfig(weather_year=2023, iso="PJM", mode="backcast")
        for f in (
            "caiso_dam_outages",
            "miso_native_outage_source",
            "neiso_operable_capacity_availability",
            "pjm_dam_availability",
        ):
            self.assertIs(getattr(cfg, f), False)
        gens = [_gen(70001, "CC_REGULAR", "gas_cc", 1, 300.0)]
        a = _build(gens, "PJM")
        b = generators_to_fleet_arrays(
            gens,
            _ZONES,
            hours=HOURS_PER_YEAR,
            iso="PJM",
            config=ScenarioConfig(
                weather_year=2023,
                iso="PJM",
                mode="backcast",
                outage_source="historic",
                pjm_dam_availability=False,
            ),
            year=2023,
        ).availability
        np.testing.assert_array_equal(a, b)


if __name__ == "__main__":
    unittest.main()
