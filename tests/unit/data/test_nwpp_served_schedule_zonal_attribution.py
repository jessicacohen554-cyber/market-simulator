"""NWPP served-schedule zonal attribution (session NWPP-NEXT-25, 2026-10-03).

``ScenarioConfig.nwpp_served_schedule_zonal_attribution`` (GATED default off)
places each measured leg of the NWPP served schedule at the zone of the member
BA that reports it (:func:`envelopes.nwpp_served_schedule_zone_interchange`)
instead of the load-share spread. This file pins: (1) the default is off;
(2) an out-of-footprint leg lands at its member's zone, and a member-to-member
leg or a priced seam's leg is never attributed (rule 19); (3) a Mountain
member's file is read on its own clock; (4) every column sums to the served
total, so the system balance is unchanged; (5) ``load_demand`` refuses the key
outside NWPP's priced-seam path.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR

_YEAR = 2021  # non-leap: the model clock and the local year align
_ZONES = ["NWPP-NW", "NWPP-OR", "NWPP-INLAND", "NWPP-EAST", "NWPP-SNV"]


def _utc_frame() -> pd.DataFrame:
    """Pool frame clock: Pacific local year, hour-ending, as UTC."""
    local = pd.date_range(f"{_YEAR}-01-01 01:00", periods=HOURS_PER_YEAR, freq="h")
    utc = local.tz_localize(
        "America/Los_Angeles", ambiguous=False, nonexistent="shift_forward"
    )
    return pd.DataFrame({"UTC time": utc.tz_convert("UTC").tz_localize(None)})


def _write(root: Path, ba: str, legs: dict[str, np.ndarray], shift_h: int) -> None:
    """Write a per-DIBA file whose local stamps sit ``shift_h`` ahead of PST."""
    local = pd.date_range(f"{_YEAR}-01-01 01:00", periods=HOURS_PER_YEAR, freq="h")
    rows = [
        pd.DataFrame(
            {
                "diba": diba,
                "mw": mw.astype("float32"),
                "local_time": (local + pd.Timedelta(hours=shift_h)).astype(
                    "datetime64[us]"
                ),
            }
        )
        for diba, mw in legs.items()
    ]
    out = root / "eia-930-interchange"
    out.mkdir(parents=True, exist_ok=True)
    pd.concat(rows).to_parquet(out / f"{ba} interchange hourly.parquet")


class TestDefault(unittest.TestCase):
    """The key ships off."""

    def test_default_off(self):
        from market_sim.config.scenarios import ScenarioConfig

        self.assertFalse(ScenarioConfig().nwpp_served_schedule_zonal_attribution)


class TestPlacement(unittest.TestCase):
    """Synthetic per-DIBA files under a patched RAW_DIR (no repo data read)."""

    def _place(self, residual: np.ndarray) -> np.ndarray:
        from market_sim.data.eia930 import envelopes as E

        tz_utc = pd.DatetimeIndex(_utc_frame()["UTC time"])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hours = np.arange(HOURS_PER_YEAR, dtype=float)
            # NEVP (Pacific): LDWP import -500 (attributed to SNV), CISO leg
            # (priced CAISO_NEVP seam: skipped), PACE leg (member: skipped).
            _write(
                root,
                "NEVP",
                {
                    "LDWP": np.full(HOURS_PER_YEAR, -500.0),
                    "CISO": np.full(HOURS_PER_YEAR, 9999.0),
                    "PACE": np.full(HOURS_PER_YEAR, 7777.0),
                },
                shift_h=0,
            )
            # PACE (Mountain, +1 h on its local stamps): WACM leg = hour index,
            # so a wrong clock shows up as a one-hour slip.
            _write(root, "PACE", {"WACM": -hours}, shift_h=1)
            frame = pd.DataFrame({"UTC time": tz_utc})
            with (
                mock.patch.object(E, "RAW_DIR", root),
                mock.patch.object(E, "_eia_hourly_frame_filled", return_value=frame),
                mock.patch(
                    "market_sim.data.zone_assignment._NWPP_BA_ZONES",
                    {"NEVP": "NWPP-SNV", "PACE": "NWPP-EAST", "BPAT": "NWPP-NW"},
                ),
            ):
                weights = np.full((len(_ZONES), HOURS_PER_YEAR), 1.0 / len(_ZONES))
                return E.nwpp_served_schedule_zone_interchange(
                    _YEAR, _ZONES, residual, weights
                ), hours

    def test_legs_land_at_member_zone_and_columns_conserve(self):
        residual = np.full(HOURS_PER_YEAR, -2000.0)
        out, hours = self._place(residual)
        np.testing.assert_allclose(out.sum(axis=0), residual, atol=1e-6)
        remainder = residual - (-500.0) - (-hours)
        share = remainder / len(_ZONES)
        snv, east = _ZONES.index("NWPP-SNV"), _ZONES.index("NWPP-EAST")
        # SNV carries only the LDWP leg (CISO priced, PACE a member), EAST
        # the WACM leg on the Mountain clock (no one-hour slip).
        np.testing.assert_allclose(
            out[snv, 100:200], -500.0 + share[100:200], atol=1e-3
        )
        np.testing.assert_allclose(
            out[east, 100:200], -hours[100:200] + share[100:200], atol=1e-3
        )
        nw = _ZONES.index("NWPP-NW")
        np.testing.assert_allclose(out[nw, 100:200], share[100:200], atol=1e-3)


class TestLoadDemandGate(unittest.TestCase):
    """The key is refused outside NWPP's priced-seam path."""

    def test_refused_for_other_iso(self):
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.data.eia930 import demand as D

        with (
            mock.patch.object(D, "_resolve_raw_demand", create=True),
            self.assertRaises(ValueError),
        ):
            try:
                D.load_demand(
                    "ERCOT",
                    2023,
                    get_iso_config("ERCOT"),
                    include_interchange=False,
                    nwpp_served_schedule_zonal_attribution=True,
                )
            except FileNotFoundError:
                self.skipTest("ERCOT demand data not present in this checkout")


if __name__ == "__main__":
    unittest.main()
