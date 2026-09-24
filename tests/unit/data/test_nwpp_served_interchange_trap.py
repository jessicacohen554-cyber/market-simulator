"""The BPAT identity trap on the NWPP served schedule (lane NWPP-34, 2026-09-14).

``tests/unit/data/test_nwpp_pool_frame.py`` pins what the served schedule IS.
This file pins what it must never become: the naive derive.

``Demand = Net generation − Total interchange`` closes to 0.000 MW for
fourteen of the seventeen NWPP members and is broken at BPAT — 20.3 % of
footprint load — by a reporting convention BPA's own feed header describes
(its balancing area "includes some that are not BPA's" and excludes loads
"served by transfer, scheduled out of region, or scheduled to customers with
their own BAs such as Seattle and Tacoma"). Summing the members' ``Total
interchange`` therefore reads the footprint as a 29-33 TWh/yr net EXPORTER
where its energy balance makes it a 13-14 TWh/yr net IMPORTER, and disagrees
with the served schedule about the DIRECTION of flow in 70 % of hours.

The measured adjudication, its natural experiment and the CAISO-facing
magnitude are ``docs/handoffs/FINDING-nwpp-34-2026-09-14.md``. Rules 13
[R-MEASURED] / 14 [R-ACCURATE]: the divergence is reported at full magnitude
and corrected away nowhere. Reads the committed extracts NWPP-11 landed;
skipped when they are not hydrated.
"""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from market_sim.config.paths import EIA_HOURLY_DIR, RAW_DIR
from market_sim.data.fleet.models import NWPP_BAS

# The hour BPAT's ``Total interchange`` steps onto the repaired convention:
# hour-ending 2025-06-01 00:00 on BPAT's Pacific clock, the first hour of its
# local June. TI falls 7,045 -> 2,217 MW while Demand (6,303 -> 6,011) and Net
# generation (8,815 -> 8,228) stay continuous, and the identity closes from
# that hour on. FINDING-nwpp-34 §2.2.
_BPAT_CONVENTION_STEP = pd.Timestamp("2025-06-01 07:00")

_INTERCHANGE_DIR = RAW_DIR / "eia-930-interchange"


def _hydrated() -> bool:
    return (EIA_HOURLY_DIR / "BPAT hourly.parquet").exists() and (
        EIA_HOURLY_DIR / "PACW hourly.parquet"
    ).exists()


def _bpat_2025() -> pd.DataFrame:
    frame = pd.read_parquet(EIA_HOURLY_DIR / "BPAT hourly.parquet")
    frame["UTC time"] = pd.to_datetime(frame["UTC time"])
    frame = frame[
        (frame["UTC time"] >= "2025-01-01") & (frame["UTC time"] < "2026-01-01")
    ]
    return frame.drop_duplicates("UTC time").sort_values("UTC time")


@unittest.skipUnless(_hydrated(), "NWPP member extracts not hydrated")
class TestBpatIdentity(unittest.TestCase):
    """The identity is broken at BPAT alone, and ``Total interchange`` is why."""

    def test_the_identity_holds_for_the_members_that_are_not_bpat(self):
        """PACW / PSEI / TPWR close to 0.000 MW in every hour of 2023-2025."""
        for ba in ("PACW", "PSEI", "TPWR"):
            frame = pd.read_parquet(EIA_HOURLY_DIR / f"{ba} hourly.parquet")
            # The claim is scoped to 2023-2025; the extracts carry 2019-2022
            # too since R-NWPP (2026-09-24), where EIA's TPWR triple does not
            # close exactly (max 281 MW).
            year = pd.to_datetime(frame["Local date"]).dt.year
            frame = frame[year.between(2023, 2025)]
            residual = (
                frame["Net generation (Adjusted)"]
                - frame["Demand (Adjusted)"]
                - frame["Total interchange (Adjusted)"]
            ).dropna()
            self.assertEqual(float(residual.abs().max()), 0.0, ba)

    def test_bpat_misses_in_essentially_every_pre_step_hour(self):
        """Mean residual ~ -3.6 GW and > 99 % of hours before the step."""
        frame = _bpat_2025()
        pre = frame[frame["UTC time"] < _BPAT_CONVENTION_STEP]
        residual = (
            pre["Net generation (Adjusted)"]
            - pre["Demand (Adjusted)"]
            - pre["Total interchange (Adjusted)"]
        )
        self.assertGreater((residual.abs() > 1.0).mean(), 0.99)
        self.assertLess(residual.mean(), -3_000.0)

    def test_the_step_is_in_total_interchange_and_nowhere_else(self):
        """At the step TI takes its single largest hourly move of the year.

        Demand and Net generation move at ordinary magnitudes in the same
        hour, so the discontinuity identifies TI as the defective series — the
        measurement the served construction rests on, rather than an
        assumption about which column to trust.
        """
        frame = _bpat_2025()
        at_step = frame["UTC time"] == _BPAT_CONVENTION_STEP
        self.assertEqual(int(at_step.sum()), 1)
        moves = {
            key: frame[col].diff()
            for key, col in (
                ("demand", "Demand (Adjusted)"),
                ("net_gen", "Net generation (Adjusted)"),
                ("interchange", "Total interchange (Adjusted)"),
            )
        }
        step = abs(float(moves["interchange"][at_step].iloc[0]))
        self.assertAlmostEqual(step, 4828.0, places=3)
        self.assertEqual(step, float(moves["interchange"].abs().max()))
        for key in ("demand", "net_gen"):
            ordinary = moves[key].abs().dropna()
            at = abs(float(moves[key][at_step].iloc[0]))
            self.assertLess((ordinary <= at).mean(), 0.95, key)

    def test_the_identity_closes_after_the_step(self):
        """Post-step BPAT is an ordinary member: |residual| <= 1 MW in 94 %+."""
        frame = _bpat_2025()
        post = frame[frame["UTC time"] >= _BPAT_CONVENTION_STEP]
        residual = (
            post["Net generation (Adjusted)"]
            - post["Demand (Adjusted)"]
            - post["Total interchange (Adjusted)"]
        )
        self.assertGreater(len(post), 5_000)
        self.assertGreater((residual.abs() <= 1.0).mean(), 0.94)


@unittest.skipUnless(_hydrated(), "NWPP member extracts not hydrated")
class TestNaiveDeriveIsRefused(unittest.TestCase):
    """Summing the members' ``Total interchange`` is the derive that is wrong."""

    YEAR = 2024

    @classmethod
    def setUpClass(cls):
        from market_sim.data.eia930.envelopes import nwpp_net_interchange
        from market_sim.data.eia930.frames import _pool_member_frames

        cls.served = nwpp_net_interchange(cls.YEAR)
        members = _pool_member_frames("NWPP", cls.YEAR)
        cls.summed_ti = np.zeros(len(cls.served), dtype=float)
        for frame in members.values():
            leg = pd.Series(frame["Total interchange (Adjusted)"].to_numpy(dtype=float))
            cls.summed_ti += (
                leg.interpolate().bfill().ffill().fillna(0.0).to_numpy(dtype=float)
            )

    def test_the_two_derives_disagree_about_the_annual_direction(self):
        """Sum-TI reads a +32 TWh exporter; the served schedule a -13 TWh importer."""
        self.assertGreater(self.summed_ti.sum() / 1e6, 25.0)
        self.assertLess(self.served.sum() / 1e6, -10.0)

    def test_the_two_derives_disagree_hour_by_hour_in_most_hours(self):
        """Sign disagreement in ~69 % of 2024 hours — not a level offset."""
        disagree = ((self.summed_ti > 0) & (self.served < 0)) | (
            (self.summed_ti < 0) & (self.served > 0)
        )
        self.assertGreater(disagree.mean(), 0.60)
        self.assertGreater((self.summed_ti - self.served).mean(), 4_000.0)


@unittest.skipUnless(
    _hydrated() and (_INTERCHANGE_DIR / "GRID interchange hourly.parquet").exists(),
    "NWPP interchange extracts not hydrated",
)
class TestGridSouthwestLegs(unittest.TestCase):
    """The set the served schedule removes is GRID's whole external book."""

    def test_grids_external_counterparties_are_the_three_desert_southwest_bas(self):
        frame = pd.read_parquet(_INTERCHANGE_DIR / "GRID interchange hourly.parquet")
        external = set(frame.loc[~frame["diba"].isin(NWPP_BAS), "diba"].unique())
        self.assertEqual(external, {"PNM", "SRP", "WALC"})


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
