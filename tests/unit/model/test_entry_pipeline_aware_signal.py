"""FFR-5C ``entry_pipeline_aware_signal``: the entry anti-cobweb guard relocation.

The gate does two things as ONE mechanism (rule 19 ``[R-ONE-MECH]`` -- the guard
RELOCATES, it neither vanishes nor duplicates):

* **E-1** removes the pending-pipeline STOCK netting from the two annual FLOW
  caps in ``capacity_evolution/new_entry.py`` (the growth ladder and the static
  per-tech queue cap), so each binds as the GW/yr rate its own citation defines;
* **E-2** puts the pending ``entry_pipeline`` rows into the merit stack the
  capacity screens' look-ahead pro-forma prices against
  (``runner._lookahead_reprice_signal``), which is where the cobweb the netting
  was aimed at actually lives.

Default OFF, and the OFF path must be byte-identical -- the first test class is
the regression that proves it against FFR-4A §5.2's measured Arm-0 series.

Measured reference: ``docs/handoffs/ffr-4a-entry-ladder-2026-08-04.md`` §5.2,
reproduced here through the same shipped code path.
"""

import unittest

import numpy as np

from market_sim.config.entry_config import (
    ENTRY_COD_LAG_DEFAULT_YEARS,
    ENTRY_COD_LAG_YEARS,
    ENTRY_GROWTH_LIMIT_MULTIPLE,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.capacity import (
    apply_economic_new_entry,
    pipeline_lookahead_units,
)
from market_sim.runner import _lookahead_reprice_signal, _pipeline_lookahead_terms

# Measured EIA-860 vintage_2020 ladder seeds (data.build_throughput), FFR-4A §2.
# MISO solar 0.618 GW ⇒ ladder 1,236 MW/yr, BELOW the 6,000 MW/yr static cap
# (ladder-first cell); MISO wind 4.367 GW ⇒ ladder 8,734 MW/yr, ABOVE the
# 4,000 MW/yr static cap (static-cap-first cell). One cell of each signature.
SEED_GW = {"solar": 0.618, "wind": 4.367}


def _entry_config(armed: bool) -> ScenarioConfig:
    """MISO entry config with emerging techs pushed past the horizon."""
    return ScenarioConfig(
        iso="MISO",
        entry_commissioning_lag=True,
        entry_pipeline_aware_signal=armed,
        h2_available_year=2099,
        ccs_available_year=2099,
        egs_available_year=2099,
        offshore_wind_available_year=2099,
    )


def _decision_series(tech: str, armed: bool, years=range(2022, 2034)) -> list[float]:
    """Drive the REAL entry screen over a multi-year path; return decided MW/yr.

    Reproduces the runner's year loop for the entry screen alone: the real
    ladder cap, the real step-4.5 pipeline commissioning (``evolve.py``) and the
    real prior-max ladder update (``runner.py``). Other techs carry a zero
    ladder row so MISO's shared 10 GW/yr ISO budget cannot mask the cell.
    Every tech is forced profitable with a flat high price -- the caps are the
    subject, so these are cap CEILINGS, never builds.
    """
    config = _entry_config(armed)
    prices = np.full(8760, 250.0)
    prior_max_gw = SEED_GW[tech]
    pipeline: list[dict] = []
    decided_by_year: list[float] = []
    for year in years:
        for row in [r for r in pipeline if int(r["cod_year"]) <= year]:
            pipeline.remove(row)
        caps = {t: 0.0 for t in ("wind", "solar", "gas_cc", "gas_ct")}
        caps[tech] = ENTRY_GROWTH_LIMIT_MULTIPLE * prior_max_gw * 1000.0
        before = {id(r) for r in pipeline}
        apply_economic_new_entry(
            [],
            prices,
            year,
            config,
            "MISO",
            entry_rate_caps_mw=caps,
            entry_pipeline=pipeline,
        )
        decided = sum(
            float(r["mw"])
            for r in pipeline
            if id(r) not in before and r["tech"] == tech
        )
        decided_by_year.append(decided)
        prior_max_gw = max(prior_max_gw, decided / 1000.0)
    return decided_by_year


class TestShippedPathUnchanged(unittest.TestCase):
    """OFF ⇒ byte-identical: the FFR-4A Arm-0 series, to the MW."""

    def test_field_defaults_off(self):
        self.assertFalse(ScenarioConfig().entry_pipeline_aware_signal)

    def test_miso_solar_frozen_at_the_ladder_seed(self):
        # FFR-4A §5.2 Arm 0: frozen at 1,236 MW every year, forever. The
        # signature of K - L + 1 == 1 -- the ratchet cannot rise.
        series = _decision_series("solar", armed=False)
        self.assertEqual(series, [1236.0] * 12)

    def test_miso_wind_alternates_at_the_static_cap(self):
        # FFR-4A §5.2 / §3.3: the OTHER signature -- against the 4,000 MW/yr
        # static per-tech cap the netting produces C, 0, C, 0 with mean C / L.
        series = _decision_series("wind", armed=False)
        self.assertEqual(series, [4000.0, 0.0] * 6)
        self.assertAlmostEqual(sum(series) / len(series), 4000.0 / 2)

    def test_lookahead_signal_identical_without_pipeline_terms(self):
        # The E-2 half's three parameters default to None, and None must
        # reproduce the pre-FFR-5C array exactly (not approximately).
        config, base_demand, fleet_arrays, mc_cost, result = _signal_fixture()
        base = _lookahead_reprice_signal(
            config, 2031, base_demand, fleet_arrays, mc_cost, result, 1
        )
        explicit_none = _lookahead_reprice_signal(
            config,
            2031,
            base_demand,
            fleet_arrays,
            mc_cost,
            result,
            1,
            pipeline_mc=None,
            pipeline_arrays=None,
            pipeline_vre=None,
        )
        np.testing.assert_array_equal(base, explicit_none)


class TestArmedRestoresTheFlowCaps(unittest.TestCase):
    """E-1: armed, both caps bind as annual flows (FFR-4A §5.2 Arm B)."""

    def test_miso_solar_ratchet_restored(self):
        # 1,236 → 2,472 → 4,944 → 6,000, then the static per-tech cap as the
        # TRUE binder. The ladder doubles each year exactly as ReEDS's 200 %
        # growth bound specifies once the stock is no longer subtracted.
        series = _decision_series("solar", armed=True)
        self.assertEqual(series[:5], [1236.0, 2472.0, 4944.0, 6000.0, 6000.0])
        self.assertEqual(series[4:], [6000.0] * 8)

    def test_miso_wind_alternation_killed(self):
        # The static cap becomes what it is documented to be: 4.0 GW PER YEAR,
        # not 4.0 GW every other year.
        series = _decision_series("wind", armed=True)
        self.assertEqual(series, [4000.0] * 12)

    def test_neither_k_nor_l_moves(self):
        # Rule 23 [R-FROZEN-DERIVE]: the fix deletes an uncited term; it does
        # not re-tune the two cited parameters (ReEDS 200 %, LBNL median lag).
        self.assertEqual(ENTRY_GROWTH_LIMIT_MULTIPLE, 2.0)
        self.assertEqual(ENTRY_COD_LAG_DEFAULT_YEARS, 2)
        self.assertEqual(set(ENTRY_COD_LAG_YEARS.values()), {2})


class TestPipelineLookaheadUnits(unittest.TestCase):
    """E-2 plumbing: the COD filter and the thermal/VRE split."""

    @staticmethod
    def _rows():
        return [
            {
                "tech": "gas_cc",
                "mw": 500.0,
                "zone": "Z0",
                "decision_year": 2030,
                "cod_year": 2031,
                "seq": 0,
                "kind": "thermal",
            },
            {
                "tech": "gas_cc",
                "mw": 800.0,
                "zone": "Z0",
                "decision_year": 2031,
                "cod_year": 2032,
                "seq": 0,
                "kind": "thermal",
            },
            {
                "tech": "solar",
                "mw": 1200.0,
                "zone": "Z0",
                "decision_year": 2030,
                "cod_year": 2031,
                "seq": 1,
                "kind": "vre",
            },
        ]

    def test_only_rows_online_in_the_priced_year_count(self):
        rows = self._rows()
        units, vre = pipeline_lookahead_units(rows, 2031, _entry_config(True), "MISO")
        self.assertEqual([u.pmax_mw for u in units], [500.0])
        self.assertEqual(vre, {("Z0", "solar"): 1200.0})
        # A year later the second CC is online too.
        units, vre = pipeline_lookahead_units(rows, 2032, _entry_config(True), "MISO")
        self.assertEqual(sorted(u.pmax_mw for u in units), [500.0, 800.0])

    def test_pipeline_is_not_mutated(self):
        rows = self._rows()
        pipeline_lookahead_units(rows, 2032, _entry_config(True), "MISO")
        self.assertEqual(len(rows), 3)

    def test_empty_pipeline_contributes_nothing(self):
        for pipeline in (None, []):
            units, vre = pipeline_lookahead_units(
                pipeline, 2031, _entry_config(True), "MISO"
            )
            self.assertEqual(units, [])
            self.assertEqual(vre, {})

    def test_thermal_unit_carries_its_commissioning_identity(self):
        units, _ = pipeline_lookahead_units(
            self._rows(), 2031, _entry_config(True), "MISO"
        )
        # Same id convention evolve.py's step-4.5 commissioning writes, so the
        # pro-forma unit and the unit it anticipates trace to one cohort.
        self.assertEqual(units[0].unit_id, "gas_cc_new_2030c2031_0")
        self.assertGreater(units[0].heat_rate, 0.0)


class TestPipelineDepressesTheProForma(unittest.TestCase):
    """E-2 effect: committed capacity lowers the price the screen sees."""

    def test_pending_thermal_pushes_the_stack_down(self):
        config, base_demand, fleet_arrays, mc_cost, result = _signal_fixture()
        base = _lookahead_reprice_signal(
            config, 2031, base_demand, fleet_arrays, mc_cost, result, 1
        )
        # 400 MW of committed $20/MWh capacity ahead of the $90 peaker.
        pipe = _FakeArrays(pmax=np.array([400.0]), availability=np.ones((1, 24)))
        with_pipe = _lookahead_reprice_signal(
            config,
            2031,
            base_demand,
            fleet_arrays,
            mc_cost,
            result,
            1,
            pipeline_mc=np.full((1, 24), 20.0),
            pipeline_arrays=pipe,
        )
        self.assertLess(float(with_pipe.mean()), float(base.mean()))

    def test_pending_vre_reduces_net_load(self):
        config, base_demand, fleet_arrays, mc_cost, result = _signal_fixture()
        base = _lookahead_reprice_signal(
            config, 2031, base_demand, fleet_arrays, mc_cost, result, 1
        )
        with_vre = _lookahead_reprice_signal(
            config,
            2031,
            base_demand,
            fleet_arrays,
            mc_cost,
            result,
            1,
            pipeline_vre=np.full(24, 300.0),
        )
        self.assertLess(float(with_vre.mean()), float(base.mean()))


class TestPipelineLookaheadTerms(unittest.TestCase):
    """E-2 glue: the runner helper that values the pipeline for the pro-forma."""

    ZONES = ["Z0", "Z1"]

    def _terms(self, pipeline, through_year=2031):
        config = _entry_config(True).with_overrides(hours=24)
        wind_cf = np.tile(np.linspace(0.1, 0.5, 24), (2, 1))
        solar_cf = np.tile(np.linspace(0.0, 0.8, 24), (2, 1))
        arrays, mc, vre = _pipeline_lookahead_terms(
            config,
            config,
            "MISO",
            pipeline,
            through_year,
            through_year,
            self.ZONES,
            wind_cf,
            solar_cf,
            np.full(24, 1000.0),
            0.0,
        )
        return arrays, mc, vre, solar_cf

    def test_thermal_priced_through_the_shipped_cost_seam(self):
        arrays, mc, _, _ = self._terms(
            [
                {
                    "tech": "gas_cc",
                    "mw": 600.0,
                    "zone": "Z0",
                    "decision_year": 2030,
                    "cod_year": 2031,
                    "seq": 0,
                    "kind": "thermal",
                },
                {
                    "tech": "gas_ct",
                    "mw": 200.0,
                    "zone": "Z1",
                    "decision_year": 2031,
                    "cod_year": 2033,
                    "seq": 0,
                    "kind": "thermal",
                },
            ]
        )
        # Only the row online in the priced year, at a plausible new-CC cost.
        np.testing.assert_array_equal(arrays.pmax, np.array([600.0]))
        self.assertEqual(mc.shape, (1, 24))
        self.assertTrue(10.0 < float(mc.mean()) < 200.0)

    def test_vre_valued_at_its_own_zone_capacity_factor(self):
        _, _, vre, solar_cf = self._terms(
            [
                {
                    "tech": "solar",
                    "mw": 1000.0,
                    "zone": "Z1",
                    "decision_year": 2030,
                    "cod_year": 2031,
                    "seq": 1,
                    "kind": "vre",
                }
            ]
        )
        np.testing.assert_allclose(vre, 1000.0 * solar_cf[1])

    def test_row_in_an_unknown_zone_is_skipped_not_misassigned(self):
        _, _, vre, _ = self._terms(
            [
                {
                    "tech": "wind",
                    "mw": 500.0,
                    "zone": "NOT_A_ZONE",
                    "decision_year": 2030,
                    "cod_year": 2031,
                    "seq": 2,
                    "kind": "vre",
                }
            ]
        )
        np.testing.assert_array_equal(vre, np.zeros(24))

    def test_empty_pipeline_yields_all_none(self):
        self.assertEqual(self._terms([])[:3], (None, None, None))


class _FakeArrays:
    """Minimal stand-in exposing the two fields the signal reads."""

    def __init__(self, pmax, availability):
        self.pmax = pmax
        self.availability = availability


class _FakeResult:
    """Minimal stand-in exposing the two dispatch arrays the signal reads."""

    def __init__(self, hours):
        self.wind_dispatched = np.zeros((1, hours))
        self.solar_dispatched = np.zeros((1, hours))


def _signal_fixture(hours: int = 24):
    """A 1-zone, 3-unit stack with demand landing on the dearest unit."""
    config = ScenarioConfig(
        iso="MISO",
        hours=hours,
        scarcity_pricing_enabled=False,
        entry_pipeline_aware_signal=True,
    )
    base_demand = np.full((1, hours), 900.0)
    fleet = _FakeArrays(
        pmax=np.array([500.0, 400.0, 500.0]), availability=np.ones((3, hours))
    )
    mc_cost = np.vstack(
        [np.full(hours, 15.0), np.full(hours, 40.0), np.full(hours, 90.0)]
    )
    return config, base_demand, fleet, mc_cost, _FakeResult(hours)


if __name__ == "__main__":
    unittest.main()
