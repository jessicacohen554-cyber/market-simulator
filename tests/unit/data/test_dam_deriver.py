"""Unit tests for the ERCOT DAM availability deriver repairs (ercot-191).

Covers the three signature-A1 rulings
(docs/PRECOMMIT-ercot191-a1-dam-deriver-2026-08-12.md):

* #9 — ``_site()`` collapses a CC config resource name to its PHYSICAL TRAIN
  (``GUADG_CC1``), never the bare mnemonic, so multi-train families sum
  per-train maxes instead of taking a cross-train max.
* #8 — an all-year-OUT site takes its rating from the nearest other derived
  year and enters both sides of every grain with live 0.
* #10 — the plant pin's REMOVE direction is diluted to the plant's measured
  DAM coverage so an accepted-subset outage cannot drag the unmeasured
  remainder.

Synthetic frames only (no disclosure read): ``_load_prep`` is monkeypatched
for the deriver tests, and the pin test drives
``_ercot_dam_plant_hourly_apply`` directly.
"""

from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts" / "data"))

import derive_ercot_thermal_dam_availability as deriver  # noqa: E402

from market_sim.data.fleet.withholding import (  # noqa: E402
    _ercot_dam_plant_hourly_apply,
)


def _rows(
    site_cfgs: dict[str, list[str]],
    dates: list[str],
    hsl: float,
    status: str,
    rtype: str = "CCGT90",
) -> pd.DataFrame:
    """One row per (config, date, HE 1..24) at a flat HSL/status."""
    rec = []
    for _site_key, cfgs in site_cfgs.items():
        for name in cfgs:
            for d in dates:
                for he in range(1, 25):
                    rec.append(
                        {
                            "Delivery Date": d,
                            "Hour Ending": he,
                            "Resource Name": name,
                            "Resource Type": rtype,
                            "HSL": hsl,
                            "Resource Status": status,
                        }
                    )
    return pd.DataFrame(rec)


def _prep(df: pd.DataFrame) -> pd.DataFrame:
    """Mirror ``_load_prep``'s derived columns on a synthetic frame."""
    df = df.copy()
    df["cls"] = df["Resource Type"].map(deriver.RESTYPE_TO_CLASS)
    df["site"] = [
        deriver._site(n, t) for n, t in zip(df["Resource Name"], df["Resource Type"])
    ]
    df["date"] = pd.to_datetime(df["Delivery Date"]).dt.normalize()
    df["out"] = df["Resource Status"].eq("OUT")
    return df


class SiteTrainGrainTest(unittest.TestCase):
    """Ruling #9: the site key is the physical train."""

    def test_cc_config_collapses_to_train(self):
        self.assertEqual(deriver._site("GUADG_CC1_1", "CCGT90"), "GUADG_CC1")
        self.assertEqual(deriver._site("GUADG_CC2_4", "CCGT90"), "GUADG_CC2")
        self.assertEqual(deriver._site("KMCHI_CC2_9", "CCLE90"), "KMCHI_CC2")
        self.assertEqual(deriver._site("JCKCNTY2_CC1_3", "CCGT90"), "JCKCNTY2_CC1")
        self.assertEqual(deriver._site("WHCCS2_CC2_1", "CCGT90"), "WHCCS2_CC2")

    def test_non_cc_names_unchanged(self):
        self.assertEqual(deriver._site("BRAUNIG_VHB3", "GSSUP"), "BRAUNIG_VHB3")
        self.assertEqual(deriver._site("SCES_UNIT1_J01", "CLLIG"), "SCES_UNIT1_J01")
        self.assertEqual(deriver._site("OLINGR_OLING_4", "SCGT90"), "OLINGR_OLING_4")

    def test_single_train_outage_visible_at_multi_train_family(self):
        """The GUADG aliasing case: CC1 OUT while CC2 runs must read ~0.5.

        Under the pre-#9 mnemonic collapse both trains aliased onto one site
        whose max() made the outage invisible (class fraction ~1.0).
        """
        dates = ["2024-10-20"]
        run = _rows({"GUADG_CC1": ["GUADG_CC1_1", "GUADG_CC1_2"]}, dates, 500.0, "ON")
        out = _rows({"GUADG_CC2": ["GUADG_CC2_1", "GUADG_CC2_2"]}, dates, 500.0, "OUT")
        df = _prep(pd.concat([run, out], ignore_index=True))
        # Both trains need a rating: give CC2 one operating day too.
        warm = _prep(
            _rows(
                {
                    "GUADG_CC1": ["GUADG_CC1_1"],
                    "GUADG_CC2": ["GUADG_CC2_1"],
                },
                ["2024-06-01"],
                500.0,
                "ON",
            )
        )
        full = pd.concat([warm, df], ignore_index=True)
        rating = deriver._inyear_rating(full)
        self.assertEqual(
            set(rating.index.get_level_values("site")), {"GUADG_CC1", "GUADG_CC2"}
        )
        live = full.copy()
        live["hsl_live"] = np.where(live["out"], 0.0, live["HSL"])
        live_sh = live.groupby(["cls", "site", "date", "Hour Ending"])["hsl_live"].max()
        day = live_sh.groupby(["cls", "site", "date"]).mean()
        oct20 = day.xs("2024-10-20", level="date")
        # Train grain: CC1 live 500, CC2 live 0 -> family fraction 0.5.
        self.assertAlmostEqual(float(oct20.sum()) / float(rating.sum()), 0.5, places=6)


class AllYearOutRatingFallbackTest(unittest.TestCase):
    """Ruling #8: an all-year-OUT site enters the denominator with live 0."""

    def _patch(self, frames: dict[int, pd.DataFrame]):
        orig = deriver._load_prep
        deriver._load_prep = lambda y: frames.get(y, pd.DataFrame())
        self.addCleanup(lambda: setattr(deriver, "_load_prep", orig))

    def test_fallback_rating_from_nearest_year(self):
        # 2024: unit runs at 800 MW. 2025: OUT all year @ 800 (Martin Lake U1
        # pattern), plus a sibling running at 800 so the class has live MW.
        run24 = _rows({"MLSES1": ["MLSES1"]}, ["2024-06-01"], 800.0, "ON", "CLLIG")
        run25 = _rows({"MLSES2": ["MLSES2"]}, ["2025-06-01"], 800.0, "ON", "CLLIG")
        out25 = _rows({"MLSES1": ["MLSES1"]}, ["2025-06-01"], 800.0, "OUT", "CLLIG")
        self._patch(
            {
                2024: _prep(run24),
                2025: _prep(pd.concat([run25, out25], ignore_index=True)),
            }
        )
        triples = deriver.derive_years([2024, 2025])
        day25 = triples[1][0]
        row = day25[(day25["class"] == "COAL") & (day25["date"] == "2025-06-01")]
        self.assertEqual(len(row), 1)
        # Denominator carries BOTH sites (800 + 800); live only the runner.
        self.assertAlmostEqual(float(row["rating_mw"].iloc[0]), 1600.0, places=1)
        self.assertAlmostEqual(float(row["live_mw"].iloc[0]), 800.0, places=1)
        self.assertAlmostEqual(float(row["avail"].iloc[0]), 0.5, places=4)
        # Site-hour grain carries the dead site at live 0 / rating 800.
        sh25 = triples[1][2]
        dead = sh25[sh25["site"] == "MLSES1"]
        self.assertTrue((dead["live_mw"] == 0.0).all())
        self.assertTrue((dead["rating_mw"] == 800.0).all())

    def test_no_rating_anywhere_stays_absent(self):
        out_only = _rows({"GHOST1": ["GHOST1"]}, ["2024-06-01"], 500.0, "OUT", "CLLIG")
        run = _rows({"MLSES2": ["MLSES2"]}, ["2024-06-01"], 800.0, "ON", "CLLIG")
        self._patch({2024: _prep(pd.concat([out_only, run], ignore_index=True))})
        triples = deriver.derive_years([2024])
        row = triples[0][0]
        self.assertAlmostEqual(float(row["rating_mw"].iloc[0]), 800.0, places=1)
        # A site with no rating in ANY derived year stays UNRATED: its
        # site-hour rows are all-NaN (the pre-existing convention — consumers
        # sum with skipna, so it contributes to neither side).
        ghost = triples[0][2][triples[0][2]["site"] == "GHOST1"]
        self.assertTrue(ghost["live_mw"].isna().all())
        self.assertTrue(ghost["rating_mw"].isna().all())


class PinRemoveDirectionCoverageTest(unittest.TestCase):
    """Ruling #10: remove-direction dilution to measured coverage."""

    class _Gen:
        def __init__(self, plant_code: int, plant_group: str):
            self.plant_code = plant_code
            self.plant_group = plant_group

    def _apply(self, plant_rating):
        hours = 2
        gens = [self._Gen(3612, "ST_GAS")]
        pmax = np.array([1000.0])
        availability = np.ones((1, hours))
        meas_h = {"ST_GAS": np.full(hours, 0.075)}
        plant_series = {3612: np.full(hours, 0.075)}
        done = _ercot_dam_plant_hourly_apply(
            availability,
            gens,
            pmax,
            hours,
            2025,
            meas_h,
            plant_series,
            logging.getLogger("test"),
            plant_rating=plant_rating,
        )
        self.assertEqual(done, {"ST_GAS"})
        return availability

    def test_full_coverage_reproduces_prior_arithmetic(self):
        avail = self._apply({3612: np.full(2, 1000.0)})  # cov = 1
        np.testing.assert_allclose(avail[0], [0.075, 0.075], atol=1e-9)

    def test_partial_coverage_dilutes_removal(self):
        # VHB pattern: measured sites cover 400 of 1000 MW -> pf_eff =
        # 0.075*0.4 + 1.0*0.6 = 0.63, not 0.075.
        avail = self._apply({3612: np.full(2, 400.0)})
        np.testing.assert_allclose(avail[0], [0.63, 0.63], atol=1e-9)

    def test_no_rating_series_keeps_prior_behavior(self):
        avail = self._apply(None)
        np.testing.assert_allclose(avail[0], [0.075, 0.075], atol=1e-9)


if __name__ == "__main__":
    unittest.main()
