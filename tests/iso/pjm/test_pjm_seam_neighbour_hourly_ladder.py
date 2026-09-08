"""Tests for PJM's HOURLY neighbour-anchored seam ladder (pjm-174).

``inject_pjm_seam_ladder_prices(..., neighbour_hourly=True)`` reads the covered
seams' bands from ``interchange_config.PJM_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR``
as per-band OFFSETS on the seam SPREAD and applies ``neighbour(t) + offset_k``
— an hourly vector rather than a scalar — so a band clears on the spread rather
than on PJM's absolute price level.  It is a SUB-GATE of the parent measured
ladder, DISPLACES the parent's scalar price on the seams it covers and DEGRADES
to that parent everywhere else (rule 19 ``[R-ONE-MECH]``: alternatives, never
stacked, and never a degrade to an unpriced seam).  Mirrors
``test_miso_seam_ladder.py``'s hourly-overlay coverage.
"""

import unittest
from unittest import mock

import numpy as np

from market_sim.config.interchange_config import (
    INTERFACE_NEIGHBORS,
    PJM_SEAM_LADDER_BY_YEAR,
    PJM_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR,
    PJM_SEAM_NEIGHBOUR_ANCHOR,
)
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
from market_sim.model.transmission import (
    _REF_EXPORT_MARK,
    _REF_IMPORT_MARK,
    build_reference_price_node,
    inject_pjm_seam_ladder_prices,
)

T = 48  # trivial clock first
_ANCHOR_PATH = "market_sim.data.eia930.envelopes.measured_pjm_neighbour_prices"


def _fleet_and_mc():
    node = build_reference_price_node("PJM")
    zone_names = sorted({g.zone for g in node})
    fleet = generators_to_fleet_arrays(node, zone_names, hours=T)
    return fleet, np.full((len(node), T), -123.0)


def _rows(fleet):
    """``{(seam, side, band): row}`` for every reference-price band row."""
    out = {}
    for row, uid in enumerate(fleet.unit_ids):
        if _REF_IMPORT_MARK in uid:
            tag, side = uid.rsplit(_REF_IMPORT_MARK, 1)[1], "import"
        elif _REF_EXPORT_MARK in uid:
            tag, side = uid.rsplit(_REF_EXPORT_MARK, 1)[1], "export"
        else:
            continue
        name, _, k = tag.partition("#")
        out[(name, side, int(k))] = row
    return out


class TestOffsetRegistry(unittest.TestCase):
    """The offset registry is well-formed and honours its declared boundaries."""

    def test_shapes_and_years(self):
        seams = {n.name for n in INTERFACE_NEIGHBORS["PJM"]}
        self.assertTrue(set(PJM_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR))
        for year, ladder in PJM_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR.items():
            self.assertIn(year, PJM_SEAM_LADDER_BY_YEAR, msg=f"{year} has no parent")
            self.assertTrue(set(ladder) <= seams, msg=f"{year} unknown seam")
            for seam, sides in ladder.items():
                for side in ("import", "export"):
                    self.assertEqual(
                        len(sides[side]),
                        SEAM_FLOW_TRANCHES,
                        msg=f"{year} {seam} {side}",
                    )

    def test_only_seams_with_a_measured_neighbour_series_appear(self):
        # SERC (Carolinas / TVA / LGEE) publishes no hub or nodal price, so
        # those seams can never carry an hourly row — they keep the parent.
        for year, ladder in PJM_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR.items():
            for seam in ladder:
                self.assertIn(seam, PJM_SEAM_NEIGHBOUR_ANCHOR, msg=f"{year} {seam}")

    def test_offsets_rise_for_import_and_fall_for_export(self):
        # The same duration-coupled supply-curve ordering the parent has, on
        # the spread: a deeper import band needs a wider spread, a deeper
        # export band accepts a narrower one.
        for year, ladder in PJM_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR.items():
            for seam, sides in ladder.items():
                self.assertEqual(
                    list(sides["import"]),
                    sorted(sides["import"]),
                    msg=f"{year} {seam} import offsets not rising",
                )
                self.assertEqual(
                    list(sides["export"]),
                    sorted(sides["export"], reverse=True),
                    msg=f"{year} {seam} export offsets not falling",
                )

    def test_same_seam_no_wash_ordering_on_the_offsets(self):
        for year, ladder in PJM_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR.items():
            for seam, sides in ladder.items():
                self.assertLess(
                    max(sides["export"]),
                    min(sides["import"]),
                    msg=f"{year} {seam} wash ordering violated",
                )


class TestHourlyInjection(unittest.TestCase):
    """The applied cost is ``anchor(t) + offset_k`` on covered seams only."""

    def test_off_is_byte_identical_to_the_parent_ladder(self):
        fleet_a, mc_a = _fleet_and_mc()
        fleet_b, mc_b = _fleet_and_mc()
        self.assertTrue(inject_pjm_seam_ladder_prices(fleet_a, mc_a, "PJM", 2025))
        self.assertTrue(
            inject_pjm_seam_ladder_prices(
                fleet_b, mc_b, "PJM", 2025, neighbour_hourly=False
            )
        )
        np.testing.assert_array_equal(mc_a, mc_b)

    def test_covered_seam_takes_anchor_plus_offset(self):
        fleet, mc = _fleet_and_mc()
        anchor = np.linspace(10.0, 90.0, T)

        def fake(iso, seam, year, hours):
            return anchor.copy() if seam == "NYISO" else None

        with mock.patch(_ANCHOR_PATH, side_effect=fake):
            self.assertTrue(
                inject_pjm_seam_ladder_prices(
                    fleet, mc, "PJM", 2025, neighbour_hourly=True
                )
            )
        rows = _rows(fleet)
        offsets = PJM_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[2025]["NYISO"]
        for side in ("import", "export"):
            for k in range(1, SEAM_FLOW_TRANCHES + 1):
                np.testing.assert_allclose(
                    mc[rows[("NYISO", side, k)], :],
                    anchor + offsets[side][k - 1],
                    err_msg=f"NYISO {side} band {k}",
                )

    def test_uncovered_seam_degrades_to_the_parent_never_to_nothing(self):
        # MISO's anchor is unavailable in this scenario: its bands must keep
        # the parent's scalar ladder price, and the SERC seams always do.
        fleet, mc = _fleet_and_mc()

        def fake(iso, seam, year, hours):
            return np.full(hours, 25.0) if seam == "NYISO" else None

        with mock.patch(_ANCHOR_PATH, side_effect=fake):
            inject_pjm_seam_ladder_prices(fleet, mc, "PJM", 2025, neighbour_hourly=True)
        rows = _rows(fleet)
        parent = PJM_SEAM_LADDER_BY_YEAR[2025]
        for seam in ("MISO", "Carolinas", "TVA", "LGEE"):
            for side in ("import", "export"):
                for k in range(1, SEAM_FLOW_TRANCHES + 1):
                    np.testing.assert_allclose(
                        mc[rows[(seam, side, k)], :],
                        parent[seam][side][k - 1],
                        err_msg=f"{seam} {side} band {k} did not keep the parent",
                    )

    def test_year_without_offsets_is_byte_identical_armed_or_not(self):
        # A parent year absent from the hourly registry must be unchanged even
        # with the sub-gate armed (there is nothing to overlay).
        year = (
            next(
                y
                for y in PJM_SEAM_LADDER_BY_YEAR
                if y not in PJM_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR
            )
            if set(PJM_SEAM_LADDER_BY_YEAR)
            - set(PJM_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR)
            else None
        )
        if year is None:
            self.skipTest("every parent year carries hourly offsets")
        fleet_a, mc_a = _fleet_and_mc()
        fleet_b, mc_b = _fleet_and_mc()
        inject_pjm_seam_ladder_prices(fleet_a, mc_a, "PJM", year)
        with mock.patch(_ANCHOR_PATH, return_value=np.full(T, 30.0)):
            inject_pjm_seam_ladder_prices(
                fleet_b, mc_b, "PJM", year, neighbour_hourly=True
            )
        np.testing.assert_array_equal(mc_a, mc_b)

    def test_availability_untouched(self):
        fleet, mc = _fleet_and_mc()
        before = fleet.availability.copy()
        with mock.patch(_ANCHOR_PATH, return_value=np.full(T, 30.0)):
            inject_pjm_seam_ladder_prices(fleet, mc, "PJM", 2025, neighbour_hourly=True)
        np.testing.assert_array_equal(fleet.availability, before)

    def test_non_pjm_iso_is_a_noop_even_armed(self):
        fleet, mc = _fleet_and_mc()
        before = mc.copy()
        self.assertFalse(
            inject_pjm_seam_ladder_prices(
                fleet, mc, "MISO", 2025, neighbour_hourly=True
            )
        )
        np.testing.assert_array_equal(mc, before)


class TestAnchorLoader(unittest.TestCase):
    """The measured anchor is full-coverage-or-None, and PJM-only."""

    def test_non_pjm_and_unknown_seam_return_none(self):
        from market_sim.data.eia930.envelopes import measured_pjm_neighbour_prices

        self.assertIsNone(measured_pjm_neighbour_prices("MISO", "NYISO", 2025, 8760))
        self.assertIsNone(measured_pjm_neighbour_prices("PJM", "TVA", 2025, 8760))

    def test_registry_and_loader_agree_on_coverage(self):
        # A table row must be armable: every seam-year in the registry resolves
        # a fully-finite anchor, and the loader must not offer one where the
        # registry has no row (that would be a band with no offsets).
        from market_sim.data.eia930.envelopes import measured_pjm_neighbour_prices

        for year, ladder in PJM_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR.items():
            for seam in ladder:
                anchor = measured_pjm_neighbour_prices("PJM", seam, year, 8760)
                if anchor is None:
                    self.skipTest(f"{seam} {year} source parquet not hydrated")
                self.assertEqual(anchor.shape, (8760,), msg=f"{seam} {year}")
                self.assertTrue(np.all(np.isfinite(anchor)), msg=f"{seam} {year}")


if __name__ == "__main__":
    unittest.main()
