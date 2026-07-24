"""Measured overlays must HARD FAIL, never silently degrade (pjm-119).

Guards the fix for the defect in
``docs/FINDING-pjm119-silent-overlay-degradation-2026-07.md``: three of the PJM
keeper's measured inputs read the CURATED ``data/clean`` tree, which is
gitignored and disposable, and each previously warned-and-fell-back when its
partition was absent. A fresh container therefore solved with those mechanisms
off while the run's recorded config — and the keeper attestation's DOF ledger —
still claimed them. That is how the pjm-118 keeper was scored with
``pjm_east_interface_cut`` (worth 17→40 C3c tail hours) never applied, and its
residual written up as a summer-scarcity structural miss.

The invariant, matching the ``pjm_da_virtual_bids`` precedent: a measured
mechanism whose input is missing raises. Silence is the bug. The guard lives in
the LOADER, not the call site, so it protects every present and future caller —
it must not depend on the analyst remembering.

The per-series / per-plant fallbacks INSIDE a present partition are deliberately
preserved and pinned here too, so the hard-fail cannot be over-read as "no
fallback anywhere".

No LP and no clean-tree dependency: each missing-input state is simulated.
"""

from __future__ import annotations

import unittest
from unittest import mock

import numpy as np

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays


class PjmEasternInterfaceGuardTest(unittest.TestCase):
    """``pjm_eastern_interface_hourly`` raises instead of returning ``None``."""

    def test_missing_partition_raises(self):
        from market_sim.data.transfer_interface_limits import (
            pjm_eastern_interface_hourly,
        )

        with mock.patch(
            "market_sim.data.transfer_interface_limits.load_interface_hourly",
            return_value=None,
        ):
            with self.assertRaises(FileNotFoundError) as ctx:
                pjm_eastern_interface_hourly(2025, HOURS_PER_YEAR)
        self.assertIn("never silently no-ops", str(ctx.exception))

    def test_present_partition_feeds_one_joint_two_link_group(self):
        """Positive control: with the real partition present the cut resolves to
        ONE one-sided group over BOTH EMAAC-import links."""
        from market_sim.data.transfer_interface_limits import (
            pjm_eastern_interface_hourly,
        )
        from market_sim.model.transmission import (
            build_pjm_east_interface_cut_groups,
        )

        try:
            limit = pjm_eastern_interface_hourly(2025, HOURS_PER_YEAR)
        except FileNotFoundError:
            self.skipTest(
                "transfer-interface-limits clean partition absent in this "
                "checkout (run scripts/regenerate_clean.py "
                "transfer-interface-limits)"
            )
        groups = build_pjm_east_interface_cut_groups(get_iso_config("PJM").links, limit)
        self.assertEqual(len(groups), 1)
        link_idx, cap, bidirectional, _, signs = groups[0]
        self.assertEqual(len(link_idx), 2)  # Central_PA→EMAAC + SWMAAC→EMAAC
        self.assertFalse(bidirectional)  # an import security limit is one-sided
        self.assertEqual(cap.shape, (HOURS_PER_YEAR,))
        self.assertTrue(np.all(np.abs(signs) == 1.0))


def _gen(plant_code: int) -> Generator:
    return Generator(
        unit_id=f"{plant_code}_1",
        name="cc1",
        zone="Z",
        fuel_type="gas_cc",
        pmax_mw=300.0,
        pmin_mw=0.0,
        heat_rate=7.5,
        vom=2.0,
        emission_rate_co2=0.4,
        nox_rate=0.0,
        eford=0.05,
        online_year=2005,
        plant_code=plant_code,
        is_campd_bin=True,
        plant_group="CC_REGULAR",
    )


class MeasuredRampCapabilityGuardTest(unittest.TestCase):
    """``load_measured_ramp_capability`` raises when the ISO has no rows."""

    def _build(self):
        cfg = ScenarioConfig(
            weather_year=2023,
            iso="PJM",
            mode="backcast",
            outage_source="historic",
            measured_ramp_capability=True,
        )
        return generators_to_fleet_arrays(
            [_gen(3149)],
            ["Z"],
            hours=HOURS_PER_YEAR,
            iso="PJM",
            config=cfg,
            year=2023,
        )

    def test_missing_partition_raises(self):
        from market_sim.data.ramp_capability import load_measured_ramp_capability

        with mock.patch(
            "scripts.lib.clean_io.read_clean", side_effect=FileNotFoundError("x")
        ):
            with self.assertRaises(FileNotFoundError) as ctx:
                load_measured_ramp_capability("PJM")
        self.assertIn("never silently no-ops", str(ctx.exception))

    def test_fleet_build_propagates_the_guard(self):
        """The gated consumer surfaces it — a solve stops rather than quietly
        reverting to class ramp fractions."""
        with mock.patch(
            "market_sim.data.ramp_capability.load_measured_ramp_capability",
            side_effect=FileNotFoundError("never silently no-ops"),
        ):
            with self.assertRaises(FileNotFoundError):
                self._build()

    def test_populated_partition_does_not_raise(self):
        """A non-empty measured mapping builds normally: the guard is scoped to
        an ISO with NO measured rows, and uncovered individual plants still fall
        back to the class ramp fraction (documented per-plant behaviour)."""
        from market_sim.data.ramp_capability import PlantRampCapability

        rows = {
            3149: PlantRampCapability(
                fast_start_mw=float("nan"),
                thermal_nameplate_mw=300.0,
                ramp_up_1h_mw=150.0,
                observed_pmax_mw=290.0,
                hours_observed=8000,
            )
        }
        with mock.patch(
            "market_sim.data.ramp_capability.load_measured_ramp_capability",
            return_value=rows,
        ):
            fa = self._build()
        self.assertEqual(fa.pmax.shape[0], 1)


if __name__ == "__main__":
    unittest.main()
