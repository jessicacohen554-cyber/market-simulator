"""Guards on ``BIN_FORCED_DERATE_BY_YEAR`` (rule 24 ``[R-REGISTRY]``).

The dict is an off-registry per-plant availability tuning channel being retired
entry by entry as each event finds its proper measured or registry home. Two
tests, pinning the two OPPOSITE outcomes of the 2026-07-28 audit so neither is
undone by a blanket edit in either direction:

* **Sandy Creek must stay OUT.** ``SC_COAL3: {2025: 0.0}`` zeroed the plant for
  all 8,760 hours of 2025 while its own comment cited EIA-923 showing 0.72 TWh
  generated. It was the sole cause of the ERCOT-130 §6 finding (model 0.000 TWh
  vs CAMPD 1,300 running hours / 0.697 TWh). The measured outage overlay
  already carries the event, so the hardcode was both wrong and redundant.
* **Martin Lake must stay IN.** ``N_COAL4: {2025: 0.67}`` encodes a unit-1
  turbine fire the measured overlay does NOT carry — ``campd-unit-outages.csv``
  has 2025 rows for units 2 and 3 only, because a unit destroyed before the
  vintage starts never produces the run/stop transition the outage derive
  detects. Deleting it would hand 2025 back ~793 MW that did not exist.
"""

import csv
import unittest

from market_sim.config.paths import RAW_DIR
from market_sim.data.fleet.eia860 import BIN_FORCED_DERATE_BY_YEAR

SANDY_CREEK_PLANT = 56611
MARTIN_LAKE_PLANT = 6146


def _outage_rows(plant_id: int, year: int) -> list[dict]:
    """Measured CAMPD unit-outage rows touching ``year`` for one plant."""
    path = RAW_DIR / "campd-unit-outages.csv"
    with path.open() as fh:
        return [
            r
            for r in csv.DictReader(fh)
            if r["facility_id"].strip() == str(plant_id)
            and (
                r["outage_start"].startswith(str(year))
                or r["outage_end"].startswith(str(year))
            )
        ]


class TestSandyCreekHardcodeRemoved(unittest.TestCase):
    """The self-refuting 2025 zeroing must not come back."""

    def test_sc_coal3_is_absent(self):
        self.assertNotIn(
            "SC_COAL3",
            BIN_FORCED_DERATE_BY_YEAR,
            "SC_COAL3 zeroed Sandy Creek for all of 2025 while CAMPD shows it "
            "running 1,300 hours; the measured outage overlay carries the "
            "event correctly (ERCOT-130 §6, removed 2026-07-28)",
        )

    def test_measured_overlay_covers_sandy_creek_2025(self):
        # The reason the hardcode is unnecessary: the measured path has it.
        rows = _outage_rows(SANDY_CREEK_PLANT, 2025)
        self.assertTrue(rows, "no measured 2025 outage for Sandy Creek")
        self.assertTrue(
            any(float(r["duration_days"]) > 300 for r in rows),
            "expected the long 2025-02-28..12-31 Sandy Creek outage",
        )


class TestMartinLakeHardcodeRetained(unittest.TestCase):
    """The unit-1 loss has no measured equivalent — it must NOT be deleted."""

    def test_n_coal4_is_present(self):
        self.assertEqual(
            BIN_FORCED_DERATE_BY_YEAR.get("N_COAL4", {}).get(2025),
            0.67,
            "N_COAL4 encodes a 2025 unit-1 turbine fire the measured outage "
            "overlay does not carry; deleting it restores ~793 MW that did "
            "not exist",
        )

    def test_measured_overlay_lacks_martin_lake_unit_1_in_2025(self):
        # The justification for retaining it, asserted rather than assumed.
        units = {r["unit_id"].strip() for r in _outage_rows(MARTIN_LAKE_PLANT, 2025)}
        self.assertNotIn(
            "1",
            units,
            "a measured 2025 unit-1 outage now exists — retire the N_COAL4 "
            "hardcode instead of keeping both (rule 19, one mechanism)",
        )


class TestRegistryChannelNotGrowing(unittest.TestCase):
    """Rule 24: the dict is being retired, never extended."""

    def test_no_new_entries(self):
        self.assertEqual(
            set(BIN_FORCED_DERATE_BY_YEAR),
            {"N_COAL4"},
            "BIN_FORCED_DERATE_BY_YEAR is an off-registry tuning channel "
            "(rule 24) being retired entry by entry — route new events to the "
            "measured outage overlay or the confirmed-retirement registry",
        )


if __name__ == "__main__":
    unittest.main()
