"""Tests for the MISO zonal loss-surface LP mechanism (miso-76 M3).

Charter-mandated unit tests (docs/handoffs/miso-nc-price-separation-design-
2026-07.md §4): off-state byte-identity, toy 2-zone separation by the loss
factor, and the loss-fraction construction (formula, reverse-direction
clamp, fail-loud on a signed lossy link). Trivial cases first (2 zones /
24 hours), per the repo testing pattern; derive determinism is covered in
tests/test_derive_miso_loss_surface.py.
"""

import csv
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from market_sim.config.iso_configs import TransferLink, get_iso_config
from market_sim.data import loss_surface
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import solve_dispatch
from market_sim.model.transmission import (
    MISO_LOSS_LINK_TIEBREAK_EPS,
    apply_miso_zonal_loss_links,
    build_incidence_matrix,
    build_interface_groups,
    build_miso_link_loss,
    get_link_bidirectional_array,
    get_ttc_array,
)

T = 24  # trivial horizon


def _fleet(specs, zone_names):
    """FleetArrays from ``(zone, pmax)`` specs (lossless, pmin 0)."""
    generators = [
        Generator(
            unit_id=f"G{i}",
            name=f"G{i}",
            zone=zone,
            fuel_type="gas_cc",
            pmax_mw=pmax,
            pmin_mw=0.0,
            eford=0.0,
        )
        for i, (zone, pmax) in enumerate(specs)
    ]
    return generators_to_fleet_arrays(generators, zone_names, hours=T)


def _no_renewables(n_zones):
    """Zero-capacity wind/solar kwargs."""
    return dict(
        wind_cf=np.zeros((n_zones, T)),
        wind_cap=np.zeros(n_zones),
        solar_cf=np.zeros((n_zones, T)),
        solar_cap=np.zeros(n_zones),
    )


def _one_way_pair(ttc=1000.0):
    """A->B / B->A one-way pair (the loss-pair topology)."""
    return [
        TransferLink(from_zone="A", to_zone="B", ttc_mw=ttc, is_bidirectional=False),
        TransferLink(from_zone="B", to_zone="A", ttc_mw=ttc, is_bidirectional=False),
    ]


class TestToyTwoZoneSeparation(unittest.TestCase):
    """The loss factor separates the two zonal duals by the DF ratio."""

    def test_receiving_zone_prices_at_sender_over_one_minus_eps(self):
        eps = 0.02
        zone_names = ["A", "B"]
        fleet = _fleet([("A", 500.0), ("B", 500.0)], zone_names)
        mc = np.vstack([np.full(T, 30.0), np.full(T, 80.0)])
        demand = np.vstack([np.zeros(T), np.full(T, 100.0)])  # load in B only
        links = _one_way_pair()
        link_loss = np.zeros((2, T))
        link_loss[0, :] = eps  # A->B lossy; B->A lossless (clamped direction)

        result = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=T,
            incidence=build_incidence_matrix(links, zone_names),
            ttc=get_ttc_array(links),
            link_bidirectional=get_link_bidirectional_array(links),
            link_loss=link_loss,
            **_no_renewables(2),
        )
        # Interior flow on the lossy leg: cheap A serves B through the loss.
        self.assertTrue(np.all(result.flows[0] > 0.0))
        # Losses consume MWh: A must generate demand/(1-eps).
        np.testing.assert_allclose(result.dispatch[0], 100.0 / (1.0 - eps), rtol=1e-6)
        # Duals separate by exactly the delivery-factor ratio (rule #4:
        # prices stay LP duals).
        np.testing.assert_allclose(result.prices[0], 30.0, rtol=1e-6)
        np.testing.assert_allclose(result.prices[1], 30.0 / (1.0 - eps), rtol=1e-6)

    def test_reverse_leg_lossless_equalizes_and_no_circulation(self):
        eps = 0.02
        zone_names = ["A", "B"]
        fleet = _fleet([("A", 500.0), ("B", 500.0)], zone_names)
        mc = np.vstack([np.full(T, 80.0), np.full(T, 30.0)])  # B cheap now
        demand = np.vstack([np.full(T, 100.0), np.zeros(T)])  # load in A
        links = _one_way_pair()
        link_loss = np.zeros((2, T))
        link_loss[0, :] = eps  # only the A->B direction carries loss
        flow_cost = np.full(2, MISO_LOSS_LINK_TIEBREAK_EPS)

        result = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=T,
            incidence=build_incidence_matrix(links, zone_names),
            ttc=get_ttc_array(links),
            link_bidirectional=get_link_bidirectional_array(links),
            link_flow_cost=flow_cost,
            link_loss=link_loss,
            **_no_renewables(2),
        )
        # Flow rides the lossless B->A leg; prices equalize (up to the
        # tiebreak ε) — the clamp means atypical-direction hours carry no
        # separation rather than an inverted one.
        self.assertTrue(np.all(result.flows[1] > 0.0))
        np.testing.assert_allclose(result.prices[0], 30.0, atol=0.01)
        np.testing.assert_allclose(result.prices[1], 30.0, atol=0.01)
        # No circulation: the lossy leg stays at zero (the tiebreak makes a
        # simultaneous counterflow strictly cost-positive).
        np.testing.assert_allclose(result.flows[0], 0.0, atol=1e-6)

    def test_all_zero_loss_is_byte_identical_to_none(self):
        zone_names = ["A", "B"]
        fleet = _fleet([("A", 500.0), ("B", 500.0)], zone_names)
        mc = np.vstack([np.full(T, 30.0), np.full(T, 80.0)])
        demand = np.vstack([np.full(T, 100.0), np.full(T, 100.0)])
        links = _one_way_pair()
        common = dict(
            mc=mc,
            T=T,
            incidence=build_incidence_matrix(links, zone_names),
            ttc=get_ttc_array(links),
            link_bidirectional=get_link_bidirectional_array(links),
            **_no_renewables(2),
        )
        r_none = solve_dispatch(fleet, demand, link_loss=None, **common)
        r_zero = solve_dispatch(fleet, demand, link_loss=np.zeros((2, T)), **common)
        np.testing.assert_array_equal(r_none.prices, r_zero.prices)
        np.testing.assert_array_equal(r_none.dispatch, r_zero.dispatch)
        np.testing.assert_array_equal(r_none.flows, r_zero.flows)


class TestApplyMisoZonalLossLinks(unittest.TestCase):
    """Topology transform: L1-L6 split, RDT/seams untouched, idempotent."""

    def test_splits_midwest_bidirectional_links_only(self):
        cfg = get_iso_config("MISO")
        n_bidir = sum(1 for ln in cfg.links if ln.is_bidirectional)
        self.assertEqual(n_bidir, 6)  # L1-L6
        out = apply_miso_zonal_loss_links(cfg)
        self.assertEqual(len(out.links), len(cfg.links) + 6)  # pairs
        midwest = [
            ln
            for ln in out.links
            if ln.from_zone.startswith("MISO-")
            and ln.to_zone.startswith("MISO-")
            and "MISO-South" not in (ln.from_zone, ln.to_zone)
        ]
        self.assertEqual(len(midwest), 12)
        for ln in midwest:
            self.assertFalse(ln.is_bidirectional)
            self.assertAlmostEqual(ln.flow_cost, MISO_LOSS_LINK_TIEBREAK_EPS)
        # RDT pair unchanged (South separation stays RDT-owned, rule 19).
        rdt = [ln for ln in out.links if "MISO-South" in (ln.from_zone, ln.to_zone)]
        self.assertEqual(len(rdt), 2)
        self.assertEqual({ln.flow_cost for ln in rdt}, {0.0})

    def test_idempotent_and_interface_groups_read_net_flow(self):
        cfg = get_iso_config("MISO")
        once = apply_miso_zonal_loss_links(cfg)
        twice = apply_miso_zonal_loss_links(once)
        self.assertIs(twice, once)  # no bidirectional Midwest links remain
        groups = build_interface_groups(once.links, once.interface_limits)
        self.assertEqual(len(groups), len(cfg.interface_limits))
        # The West CIL group now spans both directions of each member pair
        # with opposite signs (net corridor flow), like the RDT pair.
        idx, _cap, _bidir, _lower, signs = groups[0]
        self.assertEqual(len(idx), 2 * len(cfg.interface_limits[0].links))
        self.assertEqual(set(signs), {1.0, -1.0})


class TestBuildMisoLinkLoss(unittest.TestCase):
    """Loss-fraction construction from the surface (formula + clamps)."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        surface = Path(self._tmp.name) / "MISO_loss_surface.csv"
        with surface.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(
                [
                    "iso",
                    "zone",
                    "year",
                    "month",
                    "df_deviation",
                    "n_hours",
                    "interpolated",
                ]
            )
            for month in range(1, 13):
                # Constant devs: West -0.02, Indiana +0.03 (year rows), and
                # pooled rows with a DIFFERENT value to prove year selection.
                w.writerow(["MISO", "MISO-West", 2023, month, -0.02, 744, False])
                w.writerow(["MISO", "MISO-Indiana", 2023, month, 0.03, 744, False])
                w.writerow(["MISO", "MISO-West", 0, month, -0.01, 744, False])
                w.writerow(["MISO", "MISO-Indiana", 0, month, 0.01, 744, False])
        self._orig_path = loss_surface.SURFACE_PATH
        loss_surface.SURFACE_PATH = surface
        loss_surface.load_zone_month_deviation.cache_clear()

    def tearDown(self) -> None:
        loss_surface.SURFACE_PATH = self._orig_path
        loss_surface.load_zone_month_deviation.cache_clear()
        self._tmp.cleanup()

    def _pair(self):
        return [
            TransferLink(
                from_zone="MISO-West",
                to_zone="MISO-Indiana",
                ttc_mw=1000.0,
                is_bidirectional=False,
            ),
            TransferLink(
                from_zone="MISO-Indiana",
                to_zone="MISO-West",
                ttc_mw=1000.0,
                is_bidirectional=False,
            ),
        ]

    def test_formula_and_reverse_clamp(self):
        loss = build_miso_link_loss(self._pair(), "MISO", 2023, 48)
        self.assertEqual(loss.shape, (2, 48))
        # eps(West->Indiana) = (dev_I - dev_W) / (1 + dev_I) = 0.05/1.03.
        np.testing.assert_allclose(loss[0], 0.05 / 1.03, rtol=1e-12)
        # Reverse direction clamps to 0 (no fabricated inverted separation).
        np.testing.assert_allclose(loss[1], 0.0)

    def test_year_rows_selected_then_pooled_fallback(self):
        loss_2023 = build_miso_link_loss(self._pair(), "MISO", 2023, 24)
        loss_2030 = build_miso_link_loss(self._pair(), "MISO", 2030, 24)
        np.testing.assert_allclose(loss_2023[0], 0.05 / 1.03, rtol=1e-12)
        # 2030 has no rows -> pooled (0.02/1.01).
        np.testing.assert_allclose(loss_2030[0], 0.02 / 1.01, rtol=1e-12)

    def test_bidirectional_lossy_link_fails_loud(self):
        links = [
            TransferLink(from_zone="MISO-West", to_zone="MISO-Indiana", ttc_mw=1000.0)
        ]
        with self.assertRaises(ValueError):
            build_miso_link_loss(links, "MISO", 2023, 24)

    def test_non_miso_returns_none(self):
        self.assertIsNone(build_miso_link_loss(self._pair(), "ERCOT", 2023, 24))


if __name__ == "__main__":
    unittest.main()
