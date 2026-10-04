"""Tests for the per-plant coal econ cliff split (closeout-ERCOT-w3).

``ScenarioConfig.coal_perplant_cliff_split`` splits a curve-registry coal
plant's econ tranche at the largest measured price step inside its capacity
window, so ``_coal_perplant_levels`` prices each side on its own side of the
step instead of one capacity-weighted mean across it. What must hold:

- the boundary is the largest priced step strictly inside the window, never a
  step out of the self-schedule floor, and ``None`` with no interior breakpoint;
- the split rows price at the two sides' own measured means, and the unsplit
  row at the straddling mean (the defect, executable);
- off is the single econ tranche; armed outside ERCOT or without the ERCOT-144
  level gate is a hard error; a split that would drop a sub-0.5 MW side is not
  taken.

Trivial fixtures: one plant, four or five tranches, 24 hours.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.fleet.assembly import _coal_cliff_split_frac
from market_sim.data.fleet.legacy_bins import (
    apply_coal_tranches,
    assemble_mc,
    coal_curve_cliff_boundary,
)

FLOOR = -200.0
PLANT = 6179
#: Cheap 600 MW, then a cliff to $100 (top 1000 MW) — the Fayette shape.
CLIFF_CURVE = ((300.0, 15.0), (600.0, 17.0), (1000.0, 100.0))


def _gen(unit_id: str, pmax: float) -> Generator:
    """One trivial CAMPD coal tranche generator."""
    return Generator(
        unit_id=unit_id,
        name="t",
        zone="N",
        fuel_type="coal",
        efficiency_bin="subcritical",
        pmax_mw=pmax,
        pmin_mw=0.0,
        heat_rate=10.0,
        vom=4.5,
        emission_rate_co2=0.0,
        nox_rate=0.0,
        eford=0.05,
        online_year=1980,
        is_campd_bin=True,
        plant_group="COAL_PRB",
        bin_label="X",
        plant_code=PLANT,
    )


def _levels(econ_rows: list[tuple[str, float]]) -> dict[str, float]:
    """mc (hour 0) per suffix for mustrun 300 / committed 200 / econ rows / peak 100."""
    rows = [("mustrun", 300.0), ("committed", 200.0), *econ_rows, ("peak", 100.0)]
    gens = [_gen(f"COAL_N_p{PLANT}_{s}", mw) for s, mw in rows]
    cfg = ScenarioConfig(
        hours=24,
        coal_perplant_offer_level=True,
        coal_perplant_offer_curves={PLANT: CLIFF_CURVE},
    )
    fa = generators_to_fleet_arrays(gens, ["N"], config=cfg, hours=24)
    fuel = np.full((len(gens), 24), 1.5)
    mc = assemble_mc(fa, fuel, 0.0, 0.0)
    apply_coal_tranches(mc, gens, fa, [1.0] * len(gens), fuel, cfg, year=2024)
    return {s: float(mc[i, 0]) for i, (s, _mw) in enumerate(rows)}


class CliffBoundary(unittest.TestCase):
    def test_largest_interior_step(self) -> None:
        self.assertAlmostEqual(
            coal_curve_cliff_boundary(CLIFF_CURVE, 0.5, 0.9, FLOOR), 0.6
        )

    def test_step_outside_window_is_ignored(self) -> None:
        # window [0.1, 0.55]: only the 300 MW breakpoint ($15 -> $17) is inside
        self.assertAlmostEqual(
            coal_curve_cliff_boundary(CLIFF_CURVE, 0.1, 0.55, FLOOR), 0.3
        )

    def test_no_interior_breakpoint(self) -> None:
        self.assertIsNone(coal_curve_cliff_boundary(CLIFF_CURVE, 0.65, 0.95, FLOOR))
        self.assertIsNone(coal_curve_cliff_boundary(((1000.0, 20.0),), 0.0, 1.0, FLOOR))

    def test_floor_block_never_starts_a_step(self) -> None:
        # San Miguel shape: a -$249 self-schedule block, then priced segments.
        curve = ((200.0, -249.0), (300.0, 42.0), (400.0, 45.0))
        self.assertAlmostEqual(coal_curve_cliff_boundary(curve, 0.1, 0.9, FLOOR), 0.75)


class CliffSplitPricing(unittest.TestCase):
    def test_unsplit_econ_straddles_the_cliff(self) -> None:
        # econ window 500..900 MW: 100 MW @ $17 + 300 MW @ $100
        lv = _levels([("econ", 400.0)])
        self.assertAlmostEqual(lv["econ"], (100 * 17.0 + 300 * 100.0) / 400, places=6)

    def test_split_rows_price_each_side(self) -> None:
        lv = _levels([("econlo", 100.0), ("econhi", 300.0)])
        self.assertAlmostEqual(lv["econlo"], 17.0, places=6)
        self.assertAlmostEqual(lv["econhi"], 100.0, places=6)
        # rows outside the econ window keep their owners' prices
        base = _levels([("econ", 400.0)])
        self.assertAlmostEqual(lv["committed"], base["committed"], places=9)
        self.assertAlmostEqual(lv["mustrun"], base["mustrun"], places=9)


class CliffSplitGate(unittest.TestCase):
    def _cfg(self, **kw) -> ScenarioConfig:
        base = dict(
            iso="ERCOT",
            coal_perplant_offer_level=True,
            coal_perplant_offer_curves={PLANT: CLIFF_CURVE},
            coal_perplant_cliff_split=True,
        )
        base.update(kw)
        return ScenarioConfig(**base)

    def test_off_is_single_tranche(self) -> None:
        cfg = self._cfg(coal_perplant_cliff_split=False)
        self.assertIsNone(
            _coal_cliff_split_frac("coal", PLANT, cfg, 500.0, 400.0, 100.0)
        )

    def test_split_fraction(self) -> None:
        frac = _coal_cliff_split_frac("coal", PLANT, self._cfg(), 500.0, 400.0, 100.0)
        self.assertAlmostEqual(frac, 0.25)

    def test_non_coal_and_unlisted_plant(self) -> None:
        cfg = self._cfg()
        self.assertIsNone(
            _coal_cliff_split_frac("gas", PLANT, cfg, 500.0, 400.0, 100.0)
        )
        self.assertIsNone(_coal_cliff_split_frac("coal", 1, cfg, 500.0, 400.0, 100.0))

    def test_outside_ercot_raises(self) -> None:
        with self.assertRaises(ValueError):
            _coal_cliff_split_frac(
                "coal", PLANT, self._cfg(iso="PJM"), 500.0, 400.0, 100.0
            )

    def test_without_level_gate_raises(self) -> None:
        with self.assertRaises(ValueError):
            _coal_cliff_split_frac(
                "coal",
                PLANT,
                self._cfg(coal_perplant_offer_level=False),
                500.0,
                400.0,
                100.0,
            )

    def test_sub_floor_side_is_not_split(self) -> None:
        # boundary 600 MW of a 1000 MW plant, econ window 599.7..999.7 -> 0.3 MW low side
        self.assertIsNone(
            _coal_cliff_split_frac("coal", PLANT, self._cfg(), 599.7, 400.0, 0.3)
        )


if __name__ == "__main__":
    unittest.main()
