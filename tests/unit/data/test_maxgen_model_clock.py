"""The max-gen registry lands on the MODEL clock, not on MISO market time (miso-210).

MISO declares its capacity-emergency windows in EST (the registry's
``start_local``/``end_local``; ``data/raw/maxgen-events/README.md``), but the
model's hour index is CST hour-beginning — measured by miso-208 with two
r = 1.000 witnesses (the keeper's demand vs EIA-930 D; the INDIANA.HUB LMP
hour-ending file vs the committed zonal ``rt``). Until 2026-09-04 both armed
consumers (``maxgen_emergency_tier_pricing`` and the M-2 deriver behind
``unit_outage_maxgen_events``) converted the registry's UTC endpoints to EST
and so fired ONE HOUR LATE on the model clock. These tests pin the repair:

* a window declared 13:00-20:00 EST lands on model hours 12..18 (CST);
* the M-2 deriver shares the SAME clock constant (asserted, not assumed);
* the deriver's DA hub certificate record (``he01``-``he24``, hour-ending
  EST) is shifted onto the model clock by the same hour, so guard 2 compares
  the same physical hours it always did.
"""

from __future__ import annotations

import unittest

import pandas as pd

from market_sim.data import maxgen_events as mge
from scripts.data import derive_campd_maxgen_outages as drv


def _utc_registry(rows):
    """Synthetic curated frame: (level, region, start_local_est, end_local_est)."""
    recs = []
    for level, region, start, end in rows:
        s = pd.Timestamp(start).tz_localize("Etc/GMT+5").tz_convert("UTC")
        e = pd.Timestamp(end).tz_localize("Etc/GMT+5").tz_convert("UTC")
        recs.append({"level": level, "region": region, "start_utc": s, "end_utc": e})
    return pd.DataFrame(recs)


class ModelClockTest(unittest.TestCase):
    def test_miso_model_clock_is_cst(self):
        # UTC-6, fixed (no DST): the model's 8760 index is standard time.
        self.assertEqual(mge.MODEL_TZ_BY_ISO["MISO"], "Etc/GMT+6")

    def test_deriver_shares_the_clock_constant(self):
        # "Clock and scoping conventions are IDENTICAL to the M-2 deriver" —
        # previously a docstring claim; now an invariant.
        self.assertEqual(drv.MODEL_TZ, mge.MODEL_TZ_BY_ISO["MISO"])

    def test_est_declared_window_lands_one_hour_earlier_on_model_clock(self):
        # The Aug-26-2024 Max Gen Warning: 13:00-20:00 EST (2024 SOM p.15).
        ev = mge.registry_to_model_clock(
            _utc_registry(
                [
                    (
                        "maxgen_warning",
                        "footprint",
                        "2024-08-26 13:00",
                        "2024-08-26 20:00",
                    )
                ]
            ),
            "MISO",
        )
        self.assertEqual(ev.loc[0, "start_model"], pd.Timestamp("2024-08-26 12:00"))
        self.assertEqual(ev.loc[0, "end_model_excl"], pd.Timestamp("2024-08-26 19:00"))

    def test_day_precision_end_ceils_to_model_midnight(self):
        # A declared 23:59 EST end-of-day becomes 23:00 CST -> ceil to the
        # next model hour, i.e. the window closes at 23:00 CST (= 00:00 EST).
        ev = mge.registry_to_model_clock(
            _utc_registry(
                [
                    (
                        "maxgen_event_step1",
                        "midwest",
                        "2025-06-23 00:00",
                        "2025-06-23 23:59",
                    )
                ]
            ),
            "MISO",
        )
        self.assertEqual(ev.loc[0, "start_model"], pd.Timestamp("2025-06-22 23:00"))
        self.assertEqual(ev.loc[0, "end_model_excl"], pd.Timestamp("2025-06-23 23:00"))
        self.assertEqual(
            int(
                (ev.loc[0, "end_model_excl"] - ev.loc[0, "start_model"]).total_seconds()
                // 3600
            ),
            24,
        )

    def test_unregistered_iso_raises(self):
        with self.assertRaises(ValueError):
            mge.registry_to_model_clock(_utc_registry([]), "ERCOT")


class DaHubCertificateClockTest(unittest.TestCase):
    def test_he_labels_shift_onto_model_clock(self):
        # he13 on 2024-08-26 is the EST hour-beginning 12:00 interval; on the
        # CST model clock that is 11:00. The shift constant is the same -1 h
        # the registry conversion applies (EST -> CST), so the certificate
        # compares the same physical hours as before the repair.
        self.assertEqual(drv.DA_HUB_EST_TO_MODEL_HOURS, -1)
        row = {
            "date": "2024-08-26",
            "node": "INDIANA.HUB",
            "type": "Hub",
            "value": "LMP",
        }
        row.update({f"he{h:02d}": float(h) for h in range(1, 25)})
        wide = drv.da_hub_long_to_wide(pd.DataFrame([row]))
        self.assertEqual(
            float(wide.loc[pd.Timestamp("2024-08-26 11:00"), "INDIANA.HUB"]), 13.0
        )
        self.assertEqual(
            float(wide.loc[pd.Timestamp("2024-08-25 23:00"), "INDIANA.HUB"]), 1.0
        )
        self.assertNotIn(pd.Timestamp("2024-08-26 23:00"), wide.index)

    def test_certificate_is_invariant_to_the_shift(self):
        # Registry window and hub record moved together: the hour count
        # above the threshold inside the window is unchanged.
        row = {
            "date": "2024-08-26",
            "node": "INDIANA.HUB",
            "type": "Hub",
            "value": "LMP",
        }
        row.update(
            {f"he{h:02d}": (200.0 if 14 <= h <= 17 else 30.0) for h in range(1, 25)}
        )
        wide = drv.da_hub_long_to_wide(pd.DataFrame([row]))
        ev = mge.registry_to_model_clock(
            _utc_registry(
                [("maxgen_warning", "midwest", "2024-08-26 13:00", "2024-08-26 20:00")]
            ),
            "MISO",
        )
        n = drv.certificate_hours(
            wide, "midwest", ev.loc[0, "start_model"], ev.loc[0, "end_model_excl"]
        )
        self.assertEqual(n, 4)


if __name__ == "__main__":
    unittest.main()
