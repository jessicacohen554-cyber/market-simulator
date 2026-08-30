"""Tests for the NYISO zonal loss-surface LP mechanism (nyiso-159).

Mirrors the miso-76 / pjm-136 test set on NYISO's own topology and surface:
off-state byte-identity, a toy 2-zone separation by the loss factor, the
loss-fraction construction (formula, reverse-direction clamp, year-vs-pooled
selection, fail-loud on a signed lossy link), and the composition property
NYISO specifically needs — a non-internal zone must stay lossless and
un-split (the fail-closed posture PJM's star node and CAISO's WECC nodes
carry). Trivial cases first (2 zones / 24 hours), per the repo testing
pattern.
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
    NYISO_LOSS_LINK_TIEBREAK_EPS,
    apply_nyiso_zonal_loss_links,
    build_incidence_matrix,
    build_nyiso_link_loss,
    get_link_bidirectional_array,
    get_ttc_array,
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


class TestApplyNyisoZonalLossLinks(unittest.TestCase):
    """Topology transform: the four chain links split, non-internal untouched."""

    def test_splits_the_four_internal_chain_links(self):
        cfg = get_iso_config("NYISO")
        self.assertEqual(len(cfg.links), 4)
        out = apply_nyiso_zonal_loss_links(cfg)
        self.assertEqual(len(out.links), 8)
        for ln in out.links:
            self.assertFalse(ln.is_bidirectional)
            self.assertAlmostEqual(ln.flow_cost, NYISO_LOSS_LINK_TIEBREAK_EPS)
        # TTC transplants to both directions of each pair.
        by_pair = {(ln.from_zone, ln.to_zone): ln.ttc_mw for ln in out.links}
        for ln in cfg.links:
            self.assertEqual(by_pair[(ln.from_zone, ln.to_zone)], ln.ttc_mw)
            self.assertEqual(by_pair[(ln.to_zone, ln.from_zone)], ln.ttc_mw)

    def test_non_internal_zone_is_never_split_or_charged(self):
        # NYISO's real topology has no external zones (imports are priced
        # generators), so the exclusion is exercised synthetically — the
        # fail-closed posture for any future external node.
        from market_sim.config.iso_configs import Zone

        cfg = get_iso_config("NYISO")
        cfg = cfg.model_copy(
            update={
                "zones": [
                    *cfg.zones,
                    Zone(name="External_X", iso="NYISO", load_share=0.0),
                ],
                "links": [
                    *cfg.links,
                    TransferLink(from_zone="NYC", to_zone="External_X", ttc_mw=1000.0),
                ],
            }
        )
        out = apply_nyiso_zonal_loss_links(cfg)
        ext = [ln for ln in out.links if "External_X" in (ln.from_zone, ln.to_zone)]
        self.assertEqual(len(ext), 1)
        self.assertTrue(ext[0].is_bidirectional)
        self.assertEqual(ext[0].flow_cost, 0.0)

    def test_idempotent(self):
        cfg = get_iso_config("NYISO")
        once = apply_nyiso_zonal_loss_links(cfg)
        self.assertIs(apply_nyiso_zonal_loss_links(once), once)


class TestBuildNyisoLinkLoss(unittest.TestCase):
    """Loss-fraction construction from the surface (formula + clamps)."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        surface = Path(self._tmp.name) / "NYISO_loss_surface.csv"
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
                # Constant devs: UW -0.01, CH +0.05 (year rows); pooled rows
                # carry DIFFERENT values to prove year selection.
                w.writerow(["NYISO", "Upstate_West", 2023, month, -0.01, 744, False])
                w.writerow(["NYISO", "Capital_Hudson", 2023, month, 0.05, 744, False])
                w.writerow(["NYISO", "Upstate_West", 0, month, -0.005, 744, False])
                w.writerow(["NYISO", "Capital_Hudson", 0, month, 0.005, 744, False])
        # surface_path resolves NYISO through ISO_TRANSMISSION_DIR generically,
        # so the directory constant is what a hermetic test patches.
        self._orig = loss_surface.ISO_TRANSMISSION_DIR
        loss_surface.ISO_TRANSMISSION_DIR = Path(self._tmp.name)
        loss_surface.load_zone_month_deviation.cache_clear()

    def tearDown(self) -> None:
        loss_surface.ISO_TRANSMISSION_DIR = self._orig
        loss_surface.load_zone_month_deviation.cache_clear()
        self._tmp.cleanup()

    def _pair(self):
        return [
            TransferLink(
                from_zone="Upstate_West",
                to_zone="Capital_Hudson",
                ttc_mw=2850.0,
                is_bidirectional=False,
            ),
            TransferLink(
                from_zone="Capital_Hudson",
                to_zone="Upstate_West",
                ttc_mw=2850.0,
                is_bidirectional=False,
            ),
        ]

    def test_formula_and_reverse_clamp(self):
        loss = build_nyiso_link_loss(self._pair(), "NYISO", 2023, 48)
        self.assertEqual(loss.shape, (2, 48))
        # eps(UW->CH) = (dev_CH - dev_UW) / (1 + dev_CH) = 0.06 / 1.05.
        np.testing.assert_allclose(loss[0], 0.06 / 1.05, rtol=1e-12)
        # Reverse direction clamps to 0 (no fabricated inverted separation).
        np.testing.assert_allclose(loss[1], 0.0)

    def test_year_rows_selected_then_pooled_fallback(self):
        y2023 = build_nyiso_link_loss(self._pair(), "NYISO", 2023, 24)
        y2030 = build_nyiso_link_loss(self._pair(), "NYISO", 2030, 24)
        np.testing.assert_allclose(y2023[0], 0.06 / 1.05, rtol=1e-12)
        np.testing.assert_allclose(y2030[0], 0.01 / 1.005, rtol=1e-12)

    def test_non_internal_link_carries_no_loss(self):
        links = [
            *self._pair(),
            TransferLink(
                from_zone="NYC",
                to_zone="External_X",
                ttc_mw=1000.0,
                is_bidirectional=True,
            ),
        ]
        loss = build_nyiso_link_loss(links, "NYISO", 2023, 24)
        np.testing.assert_allclose(loss[2], 0.0)

    def test_bidirectional_lossy_link_fails_loud(self):
        links = [
            TransferLink(
                from_zone="Upstate_West", to_zone="Capital_Hudson", ttc_mw=2850.0
            )
        ]
        with self.assertRaises(ValueError):
            build_nyiso_link_loss(links, "NYISO", 2023, 24)

    def test_non_nyiso_returns_none(self):
        self.assertIsNone(build_nyiso_link_loss(self._pair(), "PJM", 2023, 24))


class TestOffStateByteIdentity(unittest.TestCase):
    """The flag off must leave the NYISO topology and the LP untouched."""

    def test_topology_unchanged_when_flag_off(self):
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.model.interchange.spec import (
            apply_interchange_topology,
            get_interchange_spec,
        )

        cfg = get_iso_config("NYISO")
        config = ScenarioConfig()
        self.assertFalse(config.nyiso_zonal_loss_surface)
        spec = get_interchange_spec(config, "NYISO", year=2025)
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

    def test_flag_on_splits_through_the_ladder(self):
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.model.interchange.spec import (
            apply_interchange_topology,
            get_interchange_spec,
        )

        cfg = get_iso_config("NYISO")
        config = ScenarioConfig().with_overrides(nyiso_zonal_loss_surface=True)
        spec = get_interchange_spec(config, "NYISO", year=2025)
        out = apply_interchange_topology(
            cfg, spec, config, year=2025, extend_node=False
        )
        self.assertEqual(len(out.links), 8)
        self.assertTrue(all(not ln.is_bidirectional for ln in out.links))


if __name__ == "__main__":
    unittest.main()
