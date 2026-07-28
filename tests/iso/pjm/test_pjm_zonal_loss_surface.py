"""Tests for the PJM zonal loss-surface LP mechanism (pjm-136 M2).

Mirrors the miso-76 test set on PJM's own topology and surface: off-state
byte-identity, a toy 2-zone separation by the loss factor, the loss-fraction
construction (formula, reverse-direction clamp, fail-loud on a signed lossy
link), and the composition properties PJM specifically needs — the external
star node must stay lossless and un-split, and the joint interface cuts must
still read net corridor flow after the split. Trivial cases first (2 zones /
24 hours), per the repo testing pattern.
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
    apply_pjm_zonal_loss_links,
    build_incidence_matrix,
    build_pjm_apsouth_interface_cut_groups,
    build_pjm_link_loss,
    extend_with_import_node,
    get_link_bidirectional_array,
    get_ttc_array,
    PJM_LOSS_LINK_TIEBREAK_EPS,
)

T = 24  # trivial horizon


def _fleet(specs, zone_names):
    """FleetArrays from ``(zone, pmax)`` specs (pmin 0, always available)."""
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


def _toy_links(eps: float):
    """A one-way lossy pair between two toy zones plus its loss matrix."""
    links = [
        TransferLink(
            from_zone="Z1", to_zone="Z2", ttc_mw=500.0, is_bidirectional=False
        ),
        TransferLink(
            from_zone="Z2", to_zone="Z1", ttc_mw=500.0, is_bidirectional=False
        ),
    ]
    loss = np.zeros((2, T))
    loss[0, :] = eps  # Z1 -> Z2 is the lossy direction
    return links, loss


def _solve_toy(links, loss, mc_cheap=30.0, mc_dear=80.0):
    """Cheap generation in Z1, dear in Z2, all load in Z2 — flow is Z1->Z2."""
    zone_names = ["Z1", "Z2"]
    fleet = _fleet([("Z1", 500.0), ("Z2", 500.0)], zone_names)
    mc = np.vstack([np.full(T, mc_cheap), np.full(T, mc_dear)])
    demand = np.vstack([np.zeros(T), np.full(T, 100.0)])
    return solve_dispatch(
        fleet,
        demand,
        mc=mc,
        T=T,
        incidence=build_incidence_matrix(links, zone_names),
        ttc=get_ttc_array(links),
        link_bidirectional=get_link_bidirectional_array(links),
        link_loss=loss,
        **_no_renewables(2),
    )


class TestToyTwoZoneSeparation(unittest.TestCase):
    """The receiving zone prices at sender / (1 - eps): losses, not an adder."""

    def test_receiving_zone_prices_at_sender_over_one_minus_eps(self):
        eps = 0.04
        links, loss = _toy_links(eps)
        res = _solve_toy(links, loss)
        # Losses consume MWh: Z1 must generate demand / (1 - eps).
        np.testing.assert_allclose(res.dispatch[0], 100.0 / (1.0 - eps), rtol=1e-6)
        np.testing.assert_allclose(res.prices[0], 30.0, rtol=1e-6)
        np.testing.assert_allclose(res.prices[1], 30.0 / (1.0 - eps), rtol=1e-6)

    def test_zero_loss_leaves_the_zones_at_one_dual(self):
        links, loss = _toy_links(0.0)
        res = _solve_toy(links, loss)
        np.testing.assert_allclose(res.prices[0], res.prices[1], atol=1e-9)


class TestApplyPjmZonalLossLinks(unittest.TestCase):
    """Topology transform: internal links split, external star untouched."""

    def test_splits_internal_bidirectional_links_only(self):
        cfg = get_iso_config("PJM")
        n_internal = len(cfg.links)
        out = apply_pjm_zonal_loss_links(cfg)
        self.assertEqual(len(out.links), 2 * n_internal)
        for ln in out.links:
            self.assertFalse(ln.is_bidirectional)
            self.assertAlmostEqual(ln.flow_cost, PJM_LOSS_LINK_TIEBREAK_EPS)

    def test_external_star_links_are_never_split_or_charged(self):
        cfg = extend_with_import_node(get_iso_config("PJM"))
        n_star = sum(
            1 for ln in cfg.links if "PJM_external" in (ln.from_zone, ln.to_zone)
        )
        self.assertEqual(n_star, 5)
        out = apply_pjm_zonal_loss_links(cfg)
        star = [ln for ln in out.links if "PJM_external" in (ln.from_zone, ln.to_zone)]
        self.assertEqual(len(star), n_star)
        self.assertEqual({ln.flow_cost for ln in star}, {0.0})

    def test_idempotent(self):
        cfg = get_iso_config("PJM")
        once = apply_pjm_zonal_loss_links(cfg)
        self.assertIs(apply_pjm_zonal_loss_links(once), once)

    def test_joint_interface_cut_reads_net_flow_after_the_split(self):
        """AP-South's joint cut must sum the pair to NET eastward flow."""
        cfg = apply_pjm_zonal_loss_links(get_iso_config("PJM"))
        limit = np.full(T, 3900.0)
        groups = build_pjm_apsouth_interface_cut_groups(cfg.links, limit)
        self.assertEqual(len(groups), 1)
        idx, _cap, bidir, _lower, signs = groups[0]
        # Two cut links x both orientations = four members, signed +1/-1.
        self.assertEqual(len(idx), 4)
        self.assertEqual(sorted(signs), [-1.0, -1.0, 1.0, 1.0])
        self.assertFalse(bidir)


class TestBuildPjmLinkLoss(unittest.TestCase):
    """Loss-fraction construction from the surface (formula + clamps)."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        surface = Path(self._tmp.name) / "PJM_loss_surface.csv"
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
                # Constant devs: AEP_Ohio -0.01, Dominion +0.03 (year rows);
                # pooled rows carry DIFFERENT values to prove year selection.
                w.writerow(["PJM", "PJM_AEP_Ohio", 2023, month, -0.01, 744, False])
                w.writerow(["PJM", "PJM_Dominion", 2023, month, 0.03, 744, False])
                w.writerow(["PJM", "PJM_AEP_Ohio", 0, month, -0.005, 744, False])
                w.writerow(["PJM", "PJM_Dominion", 0, month, 0.005, 744, False])
        self._orig = loss_surface.PJM_SURFACE_PATH
        loss_surface.PJM_SURFACE_PATH = surface
        loss_surface.load_zone_month_deviation.cache_clear()

    def tearDown(self) -> None:
        loss_surface.PJM_SURFACE_PATH = self._orig
        loss_surface.load_zone_month_deviation.cache_clear()
        self._tmp.cleanup()

    def _pair(self):
        return [
            TransferLink(
                from_zone="PJM_AEP_Ohio",
                to_zone="PJM_Dominion",
                ttc_mw=4069.0,
                is_bidirectional=False,
            ),
            TransferLink(
                from_zone="PJM_Dominion",
                to_zone="PJM_AEP_Ohio",
                ttc_mw=4069.0,
                is_bidirectional=False,
            ),
        ]

    def test_formula_and_reverse_clamp(self):
        loss = build_pjm_link_loss(self._pair(), "PJM", 2023, 48)
        self.assertEqual(loss.shape, (2, 48))
        # eps(AEP->DOM) = (dev_DOM - dev_AEP) / (1 + dev_DOM) = 0.04 / 1.03.
        np.testing.assert_allclose(loss[0], 0.04 / 1.03, rtol=1e-12)
        # Reverse direction clamps to 0 (no fabricated inverted separation).
        np.testing.assert_allclose(loss[1], 0.0)

    def test_year_rows_selected_then_pooled_fallback(self):
        y2023 = build_pjm_link_loss(self._pair(), "PJM", 2023, 24)
        y2030 = build_pjm_link_loss(self._pair(), "PJM", 2030, 24)
        np.testing.assert_allclose(y2023[0], 0.04 / 1.03, rtol=1e-12)
        np.testing.assert_allclose(y2030[0], 0.01 / 1.005, rtol=1e-12)

    def test_external_star_link_carries_no_loss(self):
        links = [
            *self._pair(),
            TransferLink(
                from_zone="PJM_external",
                to_zone="PJM_Dominion",
                ttc_mw=6300.0,
                is_bidirectional=True,
            ),
        ]
        loss = build_pjm_link_loss(links, "PJM", 2023, 24)
        np.testing.assert_allclose(loss[2], 0.0)

    def test_bidirectional_lossy_link_fails_loud(self):
        links = [
            TransferLink(
                from_zone="PJM_AEP_Ohio", to_zone="PJM_Dominion", ttc_mw=4069.0
            )
        ]
        with self.assertRaises(ValueError):
            build_pjm_link_loss(links, "PJM", 2023, 24)

    def test_non_pjm_returns_none(self):
        self.assertIsNone(build_pjm_link_loss(self._pair(), "MISO", 2023, 24))


class TestOffStateByteIdentity(unittest.TestCase):
    """The flag off must leave the PJM topology and the LP untouched."""

    def test_topology_unchanged_when_flag_off(self):
        from market_sim.model.interchange.spec import apply_interchange_topology
        from market_sim.model.interchange.spec import get_interchange_spec
        from market_sim.config.scenarios import ScenarioConfig

        cfg = get_iso_config("PJM")
        config = ScenarioConfig()
        self.assertFalse(config.pjm_zonal_loss_surface)
        spec = get_interchange_spec(config, "PJM", year=2025)
        out = apply_interchange_topology(
            cfg, spec, config, year=2025, extend_node=False
        )
        self.assertEqual(
            [
                (ln.from_zone, ln.to_zone, ln.is_bidirectional, ln.flow_cost)
                for ln in out.links
            ],
            [
                (ln.from_zone, ln.to_zone, ln.is_bidirectional, ln.flow_cost)
                for ln in cfg.links
            ],
        )


if __name__ == "__main__":
    unittest.main()
