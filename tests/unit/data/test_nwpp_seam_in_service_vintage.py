"""NWPP seam in-service vintage (session NWPP-NEXT-26, 2026-10-03).

``ScenarioConfig.nwpp_seam_in_service_vintage`` (GATED default off) prices a
seam listed in ``constants.NWPP_SEAM_IN_SERVICE_UTC`` only in the hours after
its physical path entered service (CAISO_NEVP: the Harry Allen-Eldorado
intertie, 2020-08-12). This file pins: (1) the default is off; (2) the priced
mask is all-true off, and splits at the in-service instant armed; (3) a seam
not priced in the year is unpriced in every hour either way; (4) the zonal
attribution serves a partly priced pair's leg exactly in its unpriced hours,
so served + priced partition the leg (rule 19) and columns still conserve;
(5) ``load_demand`` refuses the key outside NWPP's priced-seam path.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR

_ZONES = ["NWPP-NW", "NWPP-OR", "NWPP-INLAND", "NWPP-EAST", "NWPP-SNV"]


def _utc(year: int) -> pd.DatetimeIndex:
    """Pool frame clock: Pacific local year, hour-ending, as naive UTC."""
    local = pd.date_range(f"{year}-01-01 01:00", periods=HOURS_PER_YEAR, freq="h")
    utc = local.tz_localize(
        "America/Los_Angeles", ambiguous=False, nonexistent="shift_forward"
    )
    return utc.tz_convert("UTC").tz_localize(None)


class TestDefault(unittest.TestCase):
    """The key ships off."""

    def test_default_off(self):
        from market_sim.config.scenarios import ScenarioConfig

        self.assertFalse(ScenarioConfig().nwpp_seam_in_service_vintage)


class TestPricedHours(unittest.TestCase):
    """The mask splits exactly at the registered in-service instant."""

    def test_off_prices_every_hour(self):
        from market_sim.data.eia930.envelopes import nwpp_seam_priced_hours

        mask = nwpp_seam_priced_hours("CAISO_NEVP", 2019, _utc(2019))
        self.assertTrue(mask.all())

    def test_armed_splits_at_in_service(self):
        from market_sim.config.constants import NWPP_SEAM_IN_SERVICE_UTC
        from market_sim.data.eia930.envelopes import nwpp_seam_priced_hours

        start = pd.Timestamp(NWPP_SEAM_IN_SERVICE_UTC["CAISO_NEVP"])
        for year in (2019, 2020, 2021):
            utc = _utc(year)
            mask = nwpp_seam_priced_hours(
                "CAISO_NEVP", year, utc, in_service_vintage=True
            )
            np.testing.assert_array_equal(mask, np.asarray(utc > start))
        self.assertFalse(
            nwpp_seam_priced_hours(
                "CAISO_NEVP", 2019, _utc(2019), in_service_vintage=True
            ).any()
        )
        self.assertTrue(
            nwpp_seam_priced_hours(
                "CAISO_NEVP", 2021, _utc(2021), in_service_vintage=True
            ).all()
        )

    def test_ungated_seam_unchanged(self):
        from market_sim.data.eia930.envelopes import nwpp_seam_priced_hours

        # CAISO_COI has no in-service entry: priced in every hour armed or not.
        self.assertTrue(
            nwpp_seam_priced_hours(
                "CAISO_COI", 2019, _utc(2019), in_service_vintage=True
            ).all()
        )
        # WECC_CAN is unpriced before its 2023 anchor whatever the flag.
        for flag in (False, True):
            self.assertFalse(
                nwpp_seam_priced_hours(
                    "WECC_CAN", 2020, _utc(2020), in_service_vintage=flag
                ).any()
            )


class TestPartlyPricedAttribution(unittest.TestCase):
    """A partly priced pair is served in its unpriced hours, never both."""

    def test_nevp_ciso_leg_served_before_in_service(self):
        from market_sim.data.eia930 import envelopes as E

        year = 2020
        utc = _utc(year)
        start = pd.Timestamp("2020-08-12 07:00:00")
        priced = np.asarray(utc > start)
        local = pd.date_range(f"{year}-01-01 01:00", periods=HOURS_PER_YEAR, freq="h")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "eia-930-interchange"
            out_dir.mkdir(parents=True)
            pd.DataFrame(
                {
                    "diba": "CISO",
                    "mw": np.full(HOURS_PER_YEAR, 300.0, dtype="float32"),
                    "local_time": local.astype("datetime64[us]"),
                }
            ).to_parquet(out_dir / "NEVP interchange hourly.parquet")
            frame = pd.DataFrame({"UTC time": utc})
            residual = np.full(HOURS_PER_YEAR, 1000.0)
            weights = np.full((len(_ZONES), HOURS_PER_YEAR), 1.0 / len(_ZONES))
            with (
                mock.patch.object(E, "RAW_DIR", root),
                mock.patch.object(E, "_eia_hourly_frame_filled", return_value=frame),
                mock.patch(
                    "market_sim.data.zone_assignment._NWPP_BA_ZONES",
                    {"NEVP": "NWPP-SNV"},
                ),
            ):
                on = E.nwpp_served_schedule_zone_interchange(
                    year, _ZONES, residual, weights, seam_in_service_vintage=True
                )
                off = E.nwpp_served_schedule_zone_interchange(
                    year, _ZONES, residual, weights
                )
        np.testing.assert_allclose(on.sum(axis=0), residual, atol=1e-6)
        snv = _ZONES.index("NWPP-SNV")
        share = residual / len(_ZONES)
        # Off: the CISO leg is priced every hour, never attributed.
        np.testing.assert_allclose(off[snv], share, atol=1e-6)
        # Armed: attributed (300 at SNV, remainder spread) only before the date.
        served = ~priced
        expect = share + np.where(served, 300.0 - 300.0 / len(_ZONES), 0.0)
        np.testing.assert_allclose(on[snv], expect, atol=1e-3)
        self.assertGreater(served.sum(), 5000)
        self.assertGreater(priced.sum(), 3000)


class TestLoadDemandGate(unittest.TestCase):
    """The key is refused outside NWPP's priced-seam path."""

    def test_refused_with_measured_interchange(self):
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.data.eia930 import demand as D

        with self.assertRaises(ValueError):
            try:
                D.load_demand(
                    "NWPP",
                    2021,
                    get_iso_config("NWPP"),
                    include_interchange=True,
                    nwpp_seam_in_service_vintage=True,
                )
            except FileNotFoundError:
                self.skipTest("NWPP demand data not present in this checkout")

    def test_runner_refuses(self):
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.runner import _hindcast_measured_demand

        cfg = ScenarioConfig().with_overrides(nwpp_seam_in_service_vintage=True)
        with self.assertRaises(ValueError):
            _hindcast_measured_demand(cfg, "NWPP", None, 2021, [])


if __name__ == "__main__":
    unittest.main()
