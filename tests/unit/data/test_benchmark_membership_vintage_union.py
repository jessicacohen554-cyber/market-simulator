"""Vintage-aware UNION of the benchmark's ISO plant membership (spp-49).

``ScenarioConfig.benchmark_membership_vintage_union`` widens the plant set the
benchmark's ``isin`` filter uses, at the single ``_iso_plant_ids`` seam, to
include the plants BA-coded to the ISO in the EIA-860 vintage covering the
scored year.

THE DEFECT it repairs, measured rather than asserted: the membership comes from
``zone_assignment.build_zone_lookup``, whose EIA-860 supplement reads a
module-level path bound at import to the CANONICAL directory. It therefore
never follows the solved year, so a plant that retired mid-window is absent
from the ACTUAL in the very years it ran — while the LP FLEET carries it
through a fallback-zone path that the benchmark's hard ``isin`` does not have.
A mid-window retiree is then IN the model and OUT of the actual at once.

These tests pin the properties the mechanism's admissibility rests on:

* **byte-identical off** — the default path is untouched, so every keeper
  replays unchanged (rule 24 ``[R-REGISTRY]``);
* **additive, never subtractive** — the union can only ADD plants, which is
  the whole rules 13/14 safety argument: it cannot delete real metered
  generation the way the REFUSED replace-variant does;
* **no double count with the CAMPD backfill** — the backfill's firing test
  skips a plant EIA-923 already reports at or above
  ``_CAMPD_BACKFILL_MIN_MWH``, so the two membership gates compose rather than
  stack (rule 19 ``[R-ONE-MECH]``); and
* **bench and injection move in lockstep** — both reach the same seam, so the
  widening cannot manufacture a benchmark miss.
"""

import importlib.util
import unittest

import numpy as np
import pandas as pd

from tests.helpers import REPO_ROOT

REPO = REPO_ROOT
_spec = importlib.util.spec_from_file_location(
    "rcf_membership", str(REPO / "scripts" / "run_calibration_full.py")
)
rcf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rcf)

_MONTHS = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]

# Plant ids used below:
#   1  wind, the ISO's bulk energy (keeps the vintage reading complete)
#   2  coal, in the CANONICAL lookup — always present
#   127 coal, the MID-WINDOW RETIREE: absent from the canonical lookup,
#      present in the scored year's own vintage. This IS Oklaunion, and the
#      real ORIS code matters: the CAMPD-backfill skip below turns on
#      ``_coal_supply_class`` agreeing with ``_classify_f923``, which holds
#      for a plant in the coal-supply registry and not for a synthetic id.
_RETIREE = 127
_CANONICAL = frozenset({1, 2})
_VINTAGE_EXTRA = frozenset({_RETIREE})


def _gen_row(year, plant_id, prime_mover, fuel_code, annual, chp="N"):
    """One EIA-923 ``generation`` row (flat monthly shape)."""
    r = {
        "year": np.int16(year),
        "plant_id": plant_id,
        "prime_mover": prime_mover,
        "fuel_type": fuel_code,
        "chp": chp,
        "netgen_annual_mwh": float(annual),
    }
    r.update({f"netgen_{m}_mwh": annual / 12.0 for m in _MONTHS})
    return r


def _fixture(year, *, retiree_mwh=1.2e6, bulk=196.0e6):
    """Two vintages, so any prior-year carry has a source."""
    frames = []
    for y in (year - 1, year):
        frames += [
            _gen_row(y, 1, "WT", "WND", bulk),
            _gen_row(y, 2, "ST", "SUB", 5.0e6),
            _gen_row(y, _RETIREE, "ST", "SUB", retiree_mwh),
        ]
    return pd.DataFrame(frames)


class _MembershipPatch(unittest.TestCase):
    """Patch the seam so the union's effect is exercised without touching disk.

    The real ``_iso_plant_ids`` reads eGRID and the committed EIA-860 vintage
    parquets; here the canonical set and the vintage extra are stated outright
    so the tests pin the SEAM'S CONTRACT rather than the data.
    """

    def setUp(self):
        self._orig = rcf._iso_plant_ids

        def _fake(iso, year=None, vintage_union=False):
            if vintage_union and year is not None:
                return _CANONICAL | _VINTAGE_EXTRA
            return _CANONICAL

        rcf._iso_plant_ids = _fake

    def tearDown(self):
        rcf._iso_plant_ids = self._orig


class TestFrameMembership(_MembershipPatch):
    """The seam itself: which plants the union admits, and which it never drops."""

    def test_off_is_byte_identical(self):
        gen = _fixture(2020)
        a = rcf._eia923_frame(2020, gen, "SPP")
        b = rcf._eia923_frame(2020, gen, "SPP", False, False)
        pd.testing.assert_frame_equal(a, b)

    def test_off_excludes_the_mid_window_retiree(self):
        """The defect, reproduced: real metered generation is simply absent."""
        df = rcf._eia923_frame(2020, _fixture(2020), "SPP", False, False)
        self.assertNotIn(_RETIREE, set(df["plant_id"]))

    def test_on_admits_the_mid_window_retiree_at_its_metered_value(self):
        df = rcf._eia923_frame(2020, _fixture(2020), "SPP", False, True)
        row = df[df["plant_id"] == _RETIREE]
        self.assertEqual(len(row), 1)
        self.assertAlmostEqual(float(row["annual_mwh"].iloc[0]), 1.2e6, places=3)

    def test_union_is_additive_never_subtractive(self):
        """Rules 13/14: the union may only ADD. Every off-row survives on, at
        an unchanged value — the property that makes this safe where the
        REFUSED replace-variant (measured to delete real generation in 7 of 9
        registered regions) is not."""
        gen = _fixture(2020)
        off = rcf._eia923_frame(2020, gen, "SPP", False, False)
        on = rcf._eia923_frame(2020, gen, "SPP", False, True)
        key = ["plant_id", "klass"]
        off_i = off.set_index(key)["annual_mwh"]
        on_i = on.set_index(key)["annual_mwh"]
        self.assertTrue(set(off_i.index).issubset(set(on_i.index)))
        for k, v in off_i.items():
            self.assertAlmostEqual(float(on_i.loc[k]), float(v), places=6)
        self.assertGreater(
            float(on["annual_mwh"].sum()), float(off["annual_mwh"].sum())
        )

    def test_admitted_plant_contributes_only_what_eia923_reports(self):
        """It cannot inject generation that did not happen: a retiree with no
        rows in the scored year adds nothing, even though the union admits it."""
        gen = _fixture(2020)
        gen = gen[~((gen["plant_id"] == _RETIREE) & (gen["year"] == 2020))]
        off = rcf._eia923_frame(2020, gen, "SPP", False, False)
        on = rcf._eia923_frame(2020, gen, "SPP", False, True)
        pd.testing.assert_frame_equal(
            off.sort_values(["plant_id", "klass"]).reset_index(drop=True),
            on.sort_values(["plant_id", "klass"]).reset_index(drop=True),
        )


class TestNoDoubleCountWithCampdBackfill(_MembershipPatch):
    """Rule 19: the membership gate and the fleet-keyed backfill gate COMPOSE.

    A plant the union admits is also a plant the CAMPD backfill can see (it is
    in the model fleet — that is the whole asymmetry this repair closes). The
    backfill must therefore leave it alone rather than book its CAMPD net on
    top of the EIA-923 row now present.
    """

    def test_backfill_skips_a_plant_eia923_now_reports(self):
        year = 2020
        gen = _fixture(year)
        e923 = rcf._eia923_frame(year, gen, "SPP", False, True)
        before = float(e923[e923["plant_id"] == _RETIREE]["annual_mwh"].sum())
        self.assertGreaterEqual(before, rcf._CAMPD_BACKFILL_MIN_MWH)

        # CAMPD carries the same plant at a DIFFERENT (CEMS) level; if the
        # backfill fired it would overwrite the survey value.
        hours = 8760
        campd = pd.DataFrame(
            {
                "plant_id": np.full(hours, _RETIREE, dtype=int),
                "hour": np.arange(hours),
                "net_mw": np.full(hours, 150.0),
            }
        )
        out = rcf._backfill_eia923_with_campd(
            e923, campd, {_RETIREE: "COAL"}, year, class_shares=None
        )
        after = float(out[out["plant_id"] == _RETIREE]["annual_mwh"].sum())
        self.assertAlmostEqual(after, before, places=3)

    def test_backfill_still_fires_for_a_genuinely_under_reported_plant(self):
        """The guard above must not disarm the backfill itself."""
        year = 2020
        gen = _fixture(year, retiree_mwh=10.0)  # far below the threshold
        e923 = rcf._eia923_frame(year, gen, "SPP", False, True)
        hours = 8760
        campd = pd.DataFrame(
            {
                "plant_id": np.full(hours, _RETIREE, dtype=int),
                "hour": np.arange(hours),
                "net_mw": np.full(hours, 150.0),
            }
        )
        out = rcf._backfill_eia923_with_campd(
            e923, campd, {_RETIREE: "COAL"}, year, class_shares=None
        )
        after = float(out[out["plant_id"] == _RETIREE]["annual_mwh"].sum())
        self.assertGreater(after, rcf._CAMPD_BACKFILL_MIN_MWH)


class TestVintageResolver(unittest.TestCase):
    """:func:`_eia860_vintage_ba_plants` against the COMMITTED parquets.

    This is the half that reads real data, so it states the measured facts the
    repair rests on rather than a fixture's.
    """

    def test_spp_vintages_carry_oklaunion_and_canonical_does_not(self):
        # EIA retirement 9/2020: on file as SWPP in its own vintages, gone
        # from the 2021+ releases and from the canonical 2025 Early Release.
        for year in (2019, 2020):
            self.assertIn(127, rcf._eia860_vintage_ba_plants("SPP", year))
        for year in (2021, 2022):
            self.assertNotIn(127, rcf._eia860_vintage_ba_plants("SPP", year))

    def test_union_leaves_spp_keeper_years_inert(self):
        """Rule 25: arming SPP cannot move its 2023-2025 keeper.

        Measured at ROW grain, not MWh — a zero-MWh row would still change the
        frame's bytes.
        """
        from market_sim.data.eia923 import load_monthly_generation

        gen = load_monthly_generation()
        pid = pd.to_numeric(gen["plant_id"], errors="coerce")
        for year in (2023, 2024, 2025):
            off = rcf._iso_plant_ids("SPP", year, False)
            on = rcf._iso_plant_ids("SPP", year, True)
            added = on - off
            rows = gen[(gen["year"] == year) & (pid.isin(list(added)))]
            self.assertEqual(
                len(rows),
                0,
                f"SPP {year} gained {len(rows)} EIA-923 row(s) from the union; "
                "the keeper is no longer inert and this is a stop-the-line "
                "event (rule 25 [R-ISO-SCOPE]).",
            )


if __name__ == "__main__":
    unittest.main()
