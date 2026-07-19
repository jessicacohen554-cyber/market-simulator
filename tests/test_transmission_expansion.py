"""Tests for the forward transmission-expansion channel (FF-G1).

Covers the consumption seam (``data.transmission_expansion``): the loader's
superseded / base-static-vintage filters and fail-loud ``required=True``
contract; ``cumulative_deltas`` stacking; ``apply_transmission_expansion`` on a
trivial synthetic two-zone topology first (COD gating, same-object identity on
the no-op path, reversed-orientation match, exact-orientation preference on a
one-way pair, interface-cap uplift, unmatched-element skip) and then on the
real NEISO config; and the ScenarioConfig gate (backcast/hindcast coercion,
cache-key optional-field membership: default-off keys byte-stable, ON keys
distinct).
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.data import curate_transmission_expansion as curate_tx
from scripts.lib import clean_io

from market_sim.config.iso_configs import (
    InterfaceLimit,
    ISOConfig,
    TransferLink,
    Zone,
    get_iso_config,
)
from market_sim.config.scenarios import _CACHE_KEY_OPTIONAL_FIELDS, ScenarioConfig
from market_sim.data.transmission_expansion import (
    TransmissionExpansion,
    apply_transmission_expansion,
    cumulative_deltas,
    load_transmission_expansions,
)

from tests.test_curate_transmission_expansion import _NEISO_ROWS, _write_fixture


def _row(
    row_id: str,
    kind: str = "link",
    from_zone: str | None = "A",
    to_zone: str | None = "B",
    interface_name: str | None = None,
    year: int = 2027,
    delta: float = 500.0,
    delta_rev: float | None = None,
) -> TransmissionExpansion:
    return TransmissionExpansion(
        row_id=row_id,
        project_id=row_id.split("--")[0],
        project_name=row_id,
        status_tier="approved_funded",
        target_kind=kind,
        from_zone=from_zone,
        to_zone=to_zone,
        interface_name=interface_name,
        in_service_year=year,
        delta_mw=delta,
        delta_mw_reverse=delta_rev,
        mapping_confidence="exact",
    )


def _tiny_config() -> ISOConfig:
    """Trivial two-zone topology: one bidirectional link, one one-way pair,
    one interface group (the repo's trivial-case-first testing pattern)."""
    return ISOConfig(
        name="TINY",
        zones=[
            Zone(name="A", iso="TINY", load_share=1.0),
            Zone(name="B", iso="TINY", load_share=0.0),
            Zone(name="C", iso="TINY", load_share=0.0),
        ],
        links=[
            TransferLink(from_zone="A", to_zone="B", ttc_mw=1000.0),
            # One-way pair with asymmetric ratings (export vs import).
            TransferLink(
                from_zone="B", to_zone="C", ttc_mw=300.0, is_bidirectional=False
            ),
            TransferLink(
                from_zone="C", to_zone="B", ttc_mw=700.0, is_bidirectional=False
            ),
        ],
        voll=5000.0,
        interface_limits=[
            InterfaceLimit(name="AB_group", links=[("A", "B")], cap_mw=800.0)
        ],
    )


class TestApplyTinyTopology(unittest.TestCase):
    def test_pre_cod_year_is_same_object(self) -> None:
        cfg = _tiny_config()
        rows = [_row("p--ab", year=2028)]
        self.assertIs(apply_transmission_expansion(cfg, "TINY", 2027, rows), cfg)

    def test_no_rows_is_same_object(self) -> None:
        cfg = _tiny_config()
        self.assertIs(apply_transmission_expansion(cfg, "TINY", 2030, []), cfg)

    def test_link_delta_applies_from_cod_and_accumulates(self) -> None:
        cfg = _tiny_config()
        rows = [
            _row("p1--ab", year=2027, delta=500.0),
            _row("p2--ab", year=2029, delta=250.0),
        ]
        got_2027 = apply_transmission_expansion(cfg, "TINY", 2027, rows)
        self.assertEqual(got_2027.links[0].ttc_mw, 1500.0)
        got_2030 = apply_transmission_expansion(cfg, "TINY", 2030, rows)
        self.assertEqual(got_2030.links[0].ttc_mw, 1750.0)
        # The input config is never mutated.
        self.assertEqual(cfg.links[0].ttc_mw, 1000.0)

    def test_reversed_orientation_matches_bidirectional_link(self) -> None:
        cfg = _tiny_config()
        rows = [_row("p--ba", from_zone="B", to_zone="A", year=2027, delta=200.0)]
        got = apply_transmission_expansion(cfg, "TINY", 2027, rows)
        self.assertEqual(got.links[0].ttc_mw, 1200.0)

    def test_exact_orientation_targets_one_way_leg(self) -> None:
        cfg = _tiny_config()
        # (C, B) must hit the 700 MW import leg, not the 300 MW export leg.
        rows = [_row("p--cb", from_zone="C", to_zone="B", year=2027, delta=100.0)]
        got = apply_transmission_expansion(cfg, "TINY", 2027, rows)
        self.assertEqual(got.links[1].ttc_mw, 300.0)
        self.assertEqual(got.links[2].ttc_mw, 800.0)

    def test_interface_delta_raises_cap(self) -> None:
        cfg = _tiny_config()
        rows = [
            _row(
                "p--group",
                kind="interface",
                from_zone=None,
                to_zone=None,
                interface_name="AB_group",
                year=2027,
                delta=400.0,
            )
        ]
        got = apply_transmission_expansion(cfg, "TINY", 2027, rows)
        self.assertEqual(got.interface_limits[0].cap_mw, 1200.0)
        self.assertEqual(cfg.interface_limits[0].cap_mw, 800.0)

    def test_unmatched_elements_skip_without_change(self) -> None:
        cfg = _tiny_config()
        rows = [
            _row("p--xz", from_zone="X", to_zone="Z", year=2027),
            _row(
                "p--noiface",
                kind="interface",
                from_zone=None,
                to_zone=None,
                interface_name="NOPE",
                year=2027,
            ),
        ]
        with self.assertLogs(
            "market_sim.data.transmission_expansion", level="WARNING"
        ) as logs:
            got = apply_transmission_expansion(cfg, "TINY", 2027, rows)
        self.assertIs(got, cfg)
        self.assertEqual(len(logs.output), 2)

    def test_recorded_kinds_never_apply(self) -> None:
        cfg = _tiny_config()
        rows = [
            _row(
                "p--intra",
                kind="intra_zonal",
                from_zone="A",
                to_zone=None,
                year=2027,
                delta=0.0,
            ),
            _row(
                "p--tranche",
                kind="import_tranche",
                from_zone=None,
                to_zone="A",
                year=2027,
                delta=500.0,
            ),
        ]
        self.assertIs(apply_transmission_expansion(cfg, "TINY", 2030, rows), cfg)

    def test_cumulative_deltas_shapes(self) -> None:
        rows = [
            _row("p1--ab", year=2027, delta=500.0),
            _row(
                "p--group",
                kind="interface",
                from_zone=None,
                to_zone=None,
                interface_name="AB_group",
                year=2028,
                delta=400.0,
                delta_rev=100.0,
            ),
        ]
        links, ifaces = cumulative_deltas(rows, 2026)
        self.assertEqual((links, ifaces), ({}, {}))
        links, ifaces = cumulative_deltas(rows, 2028)
        self.assertEqual(links, {("A", "B"): 500.0})
        self.assertEqual(ifaces, {"AB_group": (400.0, 100.0)})


class TestLoaderRoundTrip(unittest.TestCase):
    """Loader semantics against a curated tmp CLEAN_DIR NEISO fixture."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        _write_fixture(self.raw_root, _NEISO_ROWS)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"
        curate_tx.curate(raw_root=self.raw_root, isos=["NEISO"])

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_superseded_dropped_all_kinds_loaded(self) -> None:
        rows = load_transmission_expansions("NEISO")
        # 5 fixture rows - 1 superseded (all post-2023-vintage) = 4.
        self.assertEqual(len(rows), 4)
        self.assertEqual(
            sorted(r.target_kind for r in rows),
            ["import_tranche", "interface", "intra_zonal", "link"],
        )

    def test_apply_on_real_neiso_config(self) -> None:
        cfg = get_iso_config("NEISO")
        rows = load_transmission_expansions("NEISO")
        pre = apply_transmission_expansion(cfg, "NEISO", 2025, rows)
        self.assertIs(pre, cfg)
        got = apply_transmission_expansion(cfg, "NEISO", 2026, rows)
        by_pair = {(ln.from_zone, ln.to_zone): ln.ttc_mw for ln in got.links}
        # NECEC fixture: HQ_import->North 900 + 1200; simultaneous 3850 + 1200.
        self.assertEqual(by_pair[("HQ_import", "North")], 2100.0)
        self.assertEqual(got.interface_limits[0].cap_mw, 5050.0)
        got.validate_topology()

    def test_absent_partition_returns_empty(self) -> None:
        self.assertEqual(load_transmission_expansions("MISO"), [])

    def test_required_raises_on_never_curated_root(self) -> None:
        with TemporaryDirectory() as other:
            orig = clean_io.paths.CLEAN_DIR
            clean_io.paths.CLEAN_DIR = Path(other) / "clean"
            try:
                with self.assertRaises(RuntimeError):
                    load_transmission_expansions("NEISO", required=True)
            finally:
                clean_io.paths.CLEAN_DIR = orig

    def test_required_degrades_on_curated_root_missing_iso(self) -> None:
        # Root exists (NEISO curated) but MISO has no partition: zero-row
        # registry, not a setup failure.
        self.assertEqual(load_transmission_expansions("MISO", required=True), [])


class TestScenarioGate(unittest.TestCase):
    def test_cache_key_membership_and_stability(self) -> None:
        self.assertIn("transmission_expansion_enabled", _CACHE_KEY_OPTIONAL_FIELDS)
        base = ScenarioConfig().cache_key()
        off = ScenarioConfig(transmission_expansion_enabled=False).cache_key()
        on = ScenarioConfig(transmission_expansion_enabled=True).cache_key()
        self.assertEqual(base, off)
        self.assertNotEqual(base, on)

    def test_backcast_coerces_off(self) -> None:
        cfg = ScenarioConfig(mode="backcast", transmission_expansion_enabled=True)
        self.assertFalse(cfg.transmission_expansion_enabled)

    def test_hindcast_coerces_off(self) -> None:
        cfg = ScenarioConfig(
            mode="forecast", hindcast=True, transmission_expansion_enabled=True
        )
        self.assertFalse(cfg.transmission_expansion_enabled)

    def test_forecast_keeps_flag(self) -> None:
        cfg = ScenarioConfig(mode="forecast", transmission_expansion_enabled=True)
        self.assertTrue(cfg.transmission_expansion_enabled)


if __name__ == "__main__":
    unittest.main()
