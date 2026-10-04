"""NWPP Path 76 served schedule (session NWPP-NEXT-27, 2026-10-03).

``ScenarioConfig.nwpp_path76_served_schedule`` (GATED default off) replaces the
priced WECC Path 76 link (NW<->SNV) with the measured NEVP<->BPAT EIA-930 leg,
served at both ends through the zonal served schedule. This file pins: (1) the
default is off; (2) the leg lands at SNV (+) and NW (-), every column still sums
to the served total, and off is byte-identical; (3) arming it with the priced
link is refused (rule 19); (4) ``load_demand`` refuses it without the zonal
attribution, and the forecast runner refuses it.
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

        self.assertFalse(ScenarioConfig().nwpp_path76_served_schedule)


class TestServedLeg(unittest.TestCase):
    """The measured leg is placed at both ends and conserves every column."""

    def test_leg_at_snv_and_nw(self):
        from market_sim.data.eia930 import envelopes as E

        year = 2024
        utc = _utc(year)
        local = pd.date_range(f"{year}-01-01 01:00", periods=HOURS_PER_YEAR, freq="h")
        leg = np.full(HOURS_PER_YEAR, -120.0)  # a net import into NEVP
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "eia-930-interchange"
            out_dir.mkdir(parents=True)
            pd.DataFrame(
                {
                    "diba": "BPAT",
                    "mw": leg.astype("float32"),
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
                    {"NEVP": "NWPP-SNV", "BPAT": "NWPP-NW"},
                ),
            ):
                on = E.nwpp_served_schedule_zone_interchange(
                    year, _ZONES, residual, weights, path76_served=True
                )
                off = E.nwpp_served_schedule_zone_interchange(
                    year, _ZONES, residual, weights
                )
        np.testing.assert_allclose(on.sum(axis=0), residual, atol=1e-6)
        np.testing.assert_allclose(off.sum(axis=0), residual, atol=1e-6)
        snv, nw = _ZONES.index("NWPP-SNV"), _ZONES.index("NWPP-NW")
        diff = on - off
        # The BPAT leg is internal (both members in the footprint): off never
        # places it; armed it is +leg at SNV and -leg at NW, nothing elsewhere.
        np.testing.assert_allclose(diff[snv], leg, atol=1e-3)
        np.testing.assert_allclose(diff[nw], -leg, atol=1e-3)
        others = [i for i in range(len(_ZONES)) if i not in (snv, nw)]
        np.testing.assert_allclose(diff[others], 0.0, atol=1e-9)


class TestRule19Gate(unittest.TestCase):
    """Priced link and served leg are never armed together."""

    def test_refused_with_priced_link(self):
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.pipeline.ttc import apply_nwpp_path76_link

        cfg = ScenarioConfig().with_overrides(
            nwpp_path76_alturas_link=True, nwpp_path76_served_schedule=True
        )
        with self.assertRaises(ValueError):
            apply_nwpp_path76_link(get_iso_config("NWPP"), "NWPP", cfg)

    def test_served_alone_drops_link(self):
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.pipeline.ttc import apply_nwpp_path76_link

        base = get_iso_config("NWPP")
        cfg = ScenarioConfig().with_overrides(nwpp_path76_served_schedule=True)
        self.assertIs(apply_nwpp_path76_link(base, "NWPP", cfg), base)


class TestLoadDemandGate(unittest.TestCase):
    """The key is refused without the zonal served schedule and in the runner."""

    def test_refused_without_zonal_attribution(self):
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.data.eia930 import demand as D

        with self.assertRaises(ValueError):
            try:
                D.load_demand(
                    "NWPP",
                    2021,
                    get_iso_config("NWPP"),
                    include_interchange=False,
                    nwpp_path76_served_schedule=True,
                )
            except FileNotFoundError:
                self.skipTest("NWPP demand data not present in this checkout")

    def test_runner_refuses(self):
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.runner import _hindcast_measured_demand

        cfg = ScenarioConfig().with_overrides(nwpp_path76_served_schedule=True)
        with self.assertRaises(ValueError):
            _hindcast_measured_demand(cfg, "NWPP", None, 2021, [])


if __name__ == "__main__":
    unittest.main()
