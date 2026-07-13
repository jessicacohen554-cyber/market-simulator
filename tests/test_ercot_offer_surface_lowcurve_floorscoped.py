"""Validation of the ERCOT-64 FLOOR-SCOPED committed-LSL markdown.

Covers
:func:`market_sim.data.fleet.build_ercot_offer_surface_lowcurve_floorscoped_markdown`
— the measured committed-CC LSL bid applied to the gas ``_committed`` tranche
ONLY in the gas commitment bridge's own floored plant-hours — and the shared
prep pairing :func:`market_sim.pipeline.commitment.build_ercot_gas_bridge_p1_preps`
(one bridge-floor computation shared by the P1 fleet hook and the bid hook).
Contract:

* flag off / non-ERCOT / empty mask ⇒ ``None`` (byte-identical P1);
* ONLY committed rows move, ONLY in hours the plant is bridge-floored — econ
  rungs, peak rungs and other classes never (the v2 refutation's above-floor
  mid-merit repricing is exactly what this variant removes);
* the hour gate is the BRIDGE FLOOR MASK, never P0-online (charter wiring
  trap #1: P0-online is False in bridged gaps by construction);
* the detector runs ONCE per P0 result for both hooks (trap #2), and the
  fleet hook output is byte-identical to the pre-pairing
  ``build_ercot_gas_bridge_p1_prep``;
* the ratio is clamped <= 1 and the repriced energy part floored at $1/MWh;
* condition-responsive: the markdown deepens with the net-load bin;
* a config/JSON bin-edge disagreement fails loudly;
* ``floorscoped`` without the bridge, or stacked on the refuted tranche-wide
  v2, fails loudly (rule 19 / the requires-bridge contract).
"""

import json
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    build_ercot_offer_surface_lowcurve_floorscoped_markdown,
)


def _gen(uid: str, group: str):
    return types.SimpleNamespace(unit_id=uid, plant_group=group, efficiency_bin=group)


BASE_HR = 8.0
RESOLVED_COMMITTED = 1.0


def _surface_json(path: Path, edges=(0.8, 0.9, 0.97)) -> None:
    payload = {
        "_provenance": {
            "netload_pct_edges": list(edges),
            "rel_bands": [0.0, 0.22, 0.44, 0.67],
        },
        "CC_REGULAR": {
            "base_hr": BASE_HR,
            "binned_committed_p50": [0.55, 0.40, 0.25, 0.12],
            "binned_low_body": [[0.90, 1.10, 1.30]] * 4,
        },
        "ST_GAS": {
            "base_hr": 11.0,
            # measured LSL at/above the resolved band -> clamp to no-op
            "binned_committed_p50": [1.35, 1.35, 1.5, 1.4],
            "binned_low_body": [[1.0, 1.1, 1.2]] * 4,
        },
    }
    path.write_text(json.dumps(payload))


class TestFloorscopedMarkdown(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.jpath = Path(self.tmp.name) / "lowcurve.json"
        _surface_json(self.jpath)
        # Same fixture family as the v2 tests: one CC plant (committed + two
        # econ rungs + a peak rung), one ST_GAS plant (clamped no-op), one
        # unpriced class.
        self.gens = [
            _gen("CC_North_p1_committed", "CC_REGULAR"),  # row 0
            _gen("CC_North_p1_econc00", "CC_REGULAR"),  # row 1
            _gen("CC_North_p1_econc01", "CC_REGULAR"),  # row 2
            _gen("CC_North_p1_peak", "CC_REGULAR"),  # row 3
            _gen("ST_South_p2_committed", "ST_GAS"),  # row 4
            _gen("CT_West_p3_committed", "CT_CHP"),  # row 5
        ]
        self.T = 100
        self.fa = types.SimpleNamespace(
            heat_rate=np.array([8.0, 8.0 * 1.2, 8.0 * 1.4, 8.0 * 4.0, 11.0, 9.0]),
            pmax=np.full(6, 100.0),
        )
        self.fuel = np.full((6, self.T), 3.0)
        self.net = np.arange(self.T, dtype=float)  # rising -> hour 99 tightest
        self.cfg = ScenarioConfig(iso="ERCOT").with_overrides(
            ercot_gas_commitment_bridge=True,
            ercot_offer_surface_lowcurve_floorscoped=True,
            ercot_offer_surface_lowcurve_path=str(self.jpath),
            offer_curve_by_group={
                "CC_REGULAR": {"committed": RESOLVED_COMMITTED},
                "ST_GAS": {"committed": 1.0},
            },
        )
        # Bridge floors the CC plant (via its committed row) hours 20..39 and
        # the ST plant hours 50..59.
        self.mask = np.zeros((6, self.T), dtype=bool)
        self.mask[0, 20:40] = True
        self.mask[4, 50:60] = True

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _markdown(self, cfg=None, mask="default"):
        return build_ercot_offer_surface_lowcurve_floorscoped_markdown(
            self.fa,
            self.gens,
            self.fuel,
            self.net,
            cfg or self.cfg,
            self.mask if isinstance(mask, str) else mask,
        )

    def test_flag_off_returns_none(self) -> None:
        cfg = self.cfg.with_overrides(ercot_offer_surface_lowcurve_floorscoped=False)
        self.assertIsNone(self._markdown(cfg))

    def test_non_ercot_returns_none(self) -> None:
        cfg = self.cfg.with_overrides(iso="PJM")
        self.assertIsNone(self._markdown(cfg))

    def test_empty_or_none_mask_returns_none(self) -> None:
        self.assertIsNone(self._markdown(mask=None))
        self.assertIsNone(self._markdown(mask=np.zeros((6, self.T), dtype=bool)))

    def test_scope_committed_rows_in_floored_hours_only(self) -> None:
        md = self._markdown()
        self.assertIsNotNone(md)
        self.assertTrue(np.all(md <= 0.0))  # a markdown can only lower
        # CC committed moves ONLY in its plant's floored hours 20..39.
        self.assertTrue(np.all(md[0, 20:40] < 0.0))
        self.assertTrue(np.all(md[0, :20] == 0.0))
        self.assertTrue(np.all(md[0, 40:] == 0.0))
        # econ rungs and the peak rung NEVER move (the v2 defect removed).
        self.assertTrue(np.all(md[1] == 0.0))
        self.assertTrue(np.all(md[2] == 0.0))
        self.assertTrue(np.all(md[3] == 0.0))
        # ST committed: floored 50..59 but measured >= resolved -> clamp no-op.
        self.assertTrue(np.all(md[4] == 0.0))
        # unpriced class untouched.
        self.assertTrue(np.all(md[5] == 0.0))

    def test_plant_hours_aggregate_over_any_row(self) -> None:
        # Floor recorded on an ECON row of the plant: the committed row is
        # still marked down there (a plant-hour mask, any-row aggregation).
        mask = np.zeros((6, self.T), dtype=bool)
        mask[1, 30:35] = True  # econ row floored
        md = self._markdown(mask=mask)
        self.assertIsNotNone(md)
        self.assertTrue(np.all(md[0, 30:35] < 0.0))
        self.assertTrue(np.all(md[0, :30] == 0.0))
        self.assertTrue(np.all(md[0, 35:] == 0.0))
        self.assertTrue(np.all(md[1] == 0.0))  # the econ row itself never moves

    def test_condition_responsive_committed(self) -> None:
        # Floor the whole horizon so every bin is visible: markdown deepens
        # with tightness; hour 0 (bin 0) reprices at the p50 ratio exactly.
        mask = np.zeros((6, self.T), dtype=bool)
        mask[0, :] = True
        md = self._markdown(mask=mask)
        self.assertLess(md[0, 99], md[0, 0])
        self.assertLess(md[0, 0], 0.0)
        # hour 0: ratio .55 -> energy 8*3=24 -> adj = 24*(.55-1) = -10.8
        self.assertAlmostEqual(md[0, 0], 24.0 * (0.55 - 1.0), places=6)

    def test_energy_floor_one_dollar(self) -> None:
        md = self._markdown()
        energy = self.fa.heat_rate[:, None] * self.fuel
        repriced = energy + md
        self.assertTrue(np.all(repriced[md < 0.0] >= 1.0 - 1e-9))

    def test_edge_mismatch_raises(self) -> None:
        _surface_json(self.jpath, edges=(0.5, 0.9, 0.97))
        with self.assertRaises(ValueError):
            self._markdown()


class TestSharedBridgePreps(unittest.TestCase):
    """build_ercot_gas_bridge_p1_preps: one floor computation, two hooks."""

    def _setup(self, **overrides):
        from market_sim.data.fleet import Generator, generators_to_fleet_arrays

        gen = Generator(
            unit_id="CC",
            name="CC",
            zone="z",
            fuel_type="gas_cc",
            pmax_mw=300.0,
            pmin_mw=0.0,
            heat_rate=7.0,
            eford=0.0,
            plant_group="CC_REGULAR",
        )
        hours = 48
        fa = generators_to_fleet_arrays([gen], ["z"], hours=hours)
        cfg = ScenarioConfig(iso="ERCOT").with_overrides(
            ercot_gas_commitment_bridge=True, **overrides
        )
        disp = np.zeros(hours)
        disp[6:22] = 300.0
        disp[30:46] = 300.0  # 8 h overnight gap -> economic bridge
        p0 = disp.reshape(1, hours)
        mc = np.full((1, hours), 30.0)
        lmp = np.full((1, hours), 25.0)
        r0 = types.SimpleNamespace(dispatch=p0, prices=lmp)
        return cfg, [gen], fa, mc, r0

    def test_gate_off_returns_none_pair(self):
        from market_sim.pipeline.commitment import build_ercot_gas_bridge_p1_preps

        cfg, gens, fa, mc, _ = self._setup()
        off = cfg.with_overrides(ercot_gas_commitment_bridge=False)
        self.assertEqual(
            build_ercot_gas_bridge_p1_preps(off, "ERCOT", gens, fa, mc), (None, None)
        )
        self.assertEqual(
            build_ercot_gas_bridge_p1_preps(cfg, "CAISO", gens, fa, mc), (None, None)
        )

    def test_fleet_hook_matches_legacy_prep(self):
        from market_sim.pipeline.commitment import (
            build_ercot_gas_bridge_p1_prep,
            build_ercot_gas_bridge_p1_preps,
        )

        cfg, gens, fa, mc, r0 = self._setup()
        fleet_prep, bid_prep = build_ercot_gas_bridge_p1_preps(
            cfg, "ERCOT", gens, fa, mc
        )
        self.assertIsNone(bid_prep)  # floorscoped off -> no bid hook
        legacy = build_ercot_gas_bridge_p1_prep(cfg, "ERCOT", gens, fa, mc)
        out_new = fleet_prep(r0)
        out_legacy = legacy(
            types.SimpleNamespace(dispatch=r0.dispatch, prices=r0.prices)
        )
        np.testing.assert_array_equal(out_new.min_gen, out_legacy.min_gen)
        np.testing.assert_array_equal(
            out_new.min_gen_mechanism, out_legacy.min_gen_mechanism
        )
        np.testing.assert_array_equal(out_new.availability, out_legacy.availability)

    def test_detector_runs_once_and_mask_is_bridge_floor(self):
        from market_sim.pipeline import commitment as pc

        cfg, gens, fa, mc, r0 = self._setup(
            ercot_offer_surface_lowcurve_floorscoped=True
        )
        calls = {"n": 0}
        real = pc._ercot_gas_bridge_floor

        def _counting(*a, **kw):
            calls["n"] += 1
            return real(*a, **kw)

        received = {}

        def _md_fn(mask):
            received["mask"] = mask
            return None

        orig = pc._ercot_gas_bridge_floor
        pc._ercot_gas_bridge_floor = _counting
        try:
            fleet_prep, bid_prep = pc.build_ercot_gas_bridge_p1_preps(
                cfg, "ERCOT", gens, fa, mc, floorscoped_markdown_fn=_md_fn
            )
            self.assertIsNotNone(bid_prep)
            # run_energy_solve order: bid hook first, then fleet hook.
            bid_prep(r0)
            out = fleet_prep(r0)
        finally:
            pc._ercot_gas_bridge_floor = orig
        self.assertEqual(calls["n"], 1)  # ONE detector run for both hooks
        # The mask the markdown saw is exactly the fleet hook's floored hours.
        self.assertIsNotNone(out)
        np.testing.assert_array_equal(received["mask"], out.min_gen > 0.0)
        self.assertTrue(np.all(received["mask"][0, 22:30]))
        self.assertFalse(np.any(received["mask"][0, :22]))

    def test_floorscoped_without_bridge_raises(self):
        from market_sim.pipeline.commitment import build_ercot_gas_bridge_p1_preps

        cfg, gens, fa, mc, _ = self._setup(
            ercot_offer_surface_lowcurve_floorscoped=True
        )
        cfg = cfg.with_overrides(ercot_gas_commitment_bridge=False)
        with self.assertRaises(ValueError):
            build_ercot_gas_bridge_p1_preps(cfg, "ERCOT", gens, fa, mc)

    def test_floorscoped_with_tranchewide_v2_raises(self):
        from market_sim.pipeline.commitment import build_ercot_gas_bridge_p1_preps

        cfg, gens, fa, mc, _ = self._setup(
            ercot_offer_surface_lowcurve_floorscoped=True,
            ercot_offer_surface_lowcurve=True,
        )
        with self.assertRaises(ValueError):
            build_ercot_gas_bridge_p1_preps(cfg, "ERCOT", gens, fa, mc)


if __name__ == "__main__":
    unittest.main()
