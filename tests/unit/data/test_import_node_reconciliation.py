"""Tests for the priced import-node monthly net-interchange reconciliation.

Covers:

* :func:`market_sim.model.dispatch._build_import_node_rows` — the per-month band
  constraint that pins the priced node's net throughput to a target schedule,
  forcing the modeled net import UP (under-importing economic node) and capping
  it DOWN (over-importing node) to the measured level.
* :func:`market_sim.model.dispatch.build_constraints` — byte-identical (no rows)
  when no node indices are supplied.
* :func:`market_sim.model.transmission.build_import_node_reconciliation` — the
  NYISO-gated helper that turns the measured EIA-930 export-positive schedule
  into the monthly net-import band (correct sign, aggregation and band width),
  and returns ``None`` for non-NYISO / no priced node.
"""

import unittest

import numpy as np

from market_sim.config.interchange_config import NYISO_IMPORT_RECON_BAND_FRAC
from market_sim.data.fleet import (
    Generator,
    generators_to_fleet_arrays,
)
from market_sim.model import transmission
from market_sim.model.dispatch import (
    VariableLayout,
    build_constraints,
    solve_dispatch,
)

T = 48  # two 24-hour "months" for the monthly-band tests


def _import_node_fleet():
    """In-state gas (zone Z) + an import tranche and export sink (zone EXT).

    Generator order: ``[gas, import, export_sink]``. The import tranche injects
    into the external zone (``pmax > 0``); the export sink withdraws
    (``pmax == 0``, ``pmin < 0``). EFORD is zeroed so availability is exactly
    1.0 and the throughput arithmetic is exact.
    """
    gens = [
        Generator(
            unit_id="Z_gas",
            name="Z_gas",
            zone="Z",
            fuel_type="gas_cc",
            pmax_mw=500.0,
            pmin_mw=0.0,
            eford=0.0,
        ),
        Generator(
            unit_id="EXT_import",
            name="import",
            zone="EXT",
            fuel_type="import",
            pmax_mw=400.0,
            pmin_mw=0.0,
            eford=0.0,
        ),
        Generator(
            unit_id="EXT_export",
            name="export",
            zone="EXT",
            fuel_type="import",
            pmax_mw=0.0,
            pmin_mw=-400.0,
            eford=0.0,
        ),
    ]
    return generators_to_fleet_arrays(gens, _ZONES)


# Zone order Z (load) then EXT (external, zero load); one link EXT -> Z.
_ZONES = ["Z", "EXT"]
_INCIDENCE = np.array([[1.0], [-1.0]])  # link 0: from EXT (-1) to Z (+1)
_TTC = np.array([400.0])


def _solve(mc_gas, mc_import, demand_mw, **kwargs):
    """Solve the 2-zone toy with the given gas/import offers and Z demand."""
    fa = _import_node_fleet()
    fa.availability = np.ones((3, T))  # trim default 8760-h availability to T
    demand = np.zeros((2, T))
    demand[0, :] = demand_mw  # all load in zone Z
    mc = np.zeros((3, T))
    mc[0, :] = mc_gas  # in-state gas
    mc[1, :] = mc_import  # import tranche
    mc[2, :] = 1.0  # export sink willingness-to-pay
    return solve_dispatch(
        fa,
        demand,
        np.zeros((2, T)),
        np.zeros(2),
        np.zeros((2, T)),
        np.zeros(2),
        mc=mc,
        voll=5000.0,
        incidence=_INCIDENCE,
        ttc=_TTC,
        **kwargs,
    )


def _net_import(res):
    """Net import per month = sum over import+export node rows, by 24-h month."""
    node = res.dispatch[1] + res.dispatch[2]  # import (+) minus export (-)
    return np.array([node[:24].sum(), node[24:].sum()])


class TestImportNodeBandLP(unittest.TestCase):
    def test_band_forces_net_import_up(self):
        # Gas ($20) cheaper than imports ($30): the economic node under-imports
        # (serves load from in-state gas). The band forces net import UP to the
        # monthly target.
        target = np.array([24 * 200.0, 24 * 150.0])  # MWh per month
        half = 0.0  # hard equality
        res = _solve(
            mc_gas=20.0,
            mc_import=30.0,
            demand_mw=300.0,
            import_node_gen_idx=np.array([1, 2]),
            import_node_monthly_lo=target - half,
            import_node_monthly_hi=target + half,
            import_node_month_index=np.repeat([0, 1], 24),
        )
        net = _net_import(res)
        self.assertTrue(np.allclose(net, target, atol=1e-3), net)

    def test_unconstrained_node_under_imports(self):
        # Same offers, NO band: confirm the economic node really does under-import
        # (so the band test above is forcing the level, not a no-op).
        res = _solve(mc_gas=20.0, mc_import=30.0, demand_mw=300.0)
        net = _net_import(res)
        self.assertTrue(np.all(net < 1.0), net)  # ~zero economic imports

    def test_band_caps_over_import(self):
        # Imports ($10) cheaper than gas ($40): the economic node imports the full
        # link rating every hour. The band's UPPER bound caps net import DOWN.
        cap = np.array([24 * 100.0, 24 * 100.0])  # MWh per month ceiling
        res = _solve(
            mc_gas=40.0,
            mc_import=10.0,
            demand_mw=300.0,
            import_node_gen_idx=np.array([1, 2]),
            import_node_monthly_lo=np.array([0.0, 0.0]),
            import_node_monthly_hi=cap,
            import_node_month_index=np.repeat([0, 1], 24),
        )
        net = _net_import(res)
        self.assertTrue(np.all(net <= cap + 1e-3), net)
        self.assertTrue(np.all(net >= cap - 1e-3), net)  # binds at the cap

    def test_within_band_price_freedom(self):
        # A wide band that already contains the economic optimum must not move the
        # dispatch: the constraint only pins the LEVEL, it does not distort an
        # already-compliant solution.
        base = _solve(mc_gas=20.0, mc_import=30.0, demand_mw=300.0)
        banded = _solve(
            mc_gas=20.0,
            mc_import=30.0,
            demand_mw=300.0,
            import_node_gen_idx=np.array([1, 2]),
            import_node_monthly_lo=np.array([-1e9, -1e9]),
            import_node_monthly_hi=np.array([1e9, 1e9]),
            import_node_month_index=np.repeat([0, 1], 24),
        )
        self.assertTrue(np.allclose(base.dispatch, banded.dispatch, atol=1e-6))


class TestBuildConstraintsIdentical(unittest.TestCase):
    def test_no_rows_when_node_idx_none(self):
        fa = _import_node_fleet()
        demand = np.zeros((2, T))
        layout = VariableLayout(n_gen=3, n_zones=2, n_storage=0, n_links=1, T=T)
        base_A, base_lo, base_hi, *_ = build_constraints(
            layout, fa, demand, incidence=_INCIDENCE
        )
        node_A, node_lo, node_hi, *_ = build_constraints(
            layout,
            fa,
            demand,
            incidence=_INCIDENCE,
            import_node_gen_idx=np.array([], dtype=int),
            import_node_monthly_lo=np.zeros(0),
            import_node_monthly_hi=np.zeros(0),
        )
        # Empty node index -> identical row count.
        self.assertEqual(base_A.shape, node_A.shape)
        self.assertEqual(base_lo.shape, node_lo.shape)


class TestReconciliationHelper(unittest.TestCase):
    def test_non_nyiso_returns_none(self):
        fa = _import_node_fleet()
        self.assertIsNone(
            transmission.build_import_node_reconciliation(fa, "PJM", 2023)
        )

    def test_sign_aggregation_and_band(self):
        # Patch the measured loader: a constant -250 MW (export-positive) =>
        # net IMPORT of +250 MW every hour. Monthly target = 250 * hours_in_month.
        import market_sim.data.eia_loader as eia

        orig = eia.nyiso_net_interchange
        try:
            eia.nyiso_net_interchange = lambda year: np.full(8760, -250.0)
            fa = _import_node_fleet()
            # Trim the toy fleet's availability to 8760 to match the schedule.
            T8760 = 8760
            fa.availability = np.ones((3, T8760))
            out = transmission.build_import_node_reconciliation(fa, "NYISO", 2023)
            self.assertIsNotNone(out)
            node_idx, lo, hi = out
            # Both import rows (idx 1, 2) are the node.
            self.assertEqual(sorted(node_idx.tolist()), [1, 2])
            # 12 monthly targets, each = 250 * (hours in that month).
            self.assertEqual(lo.shape, (12,))
            target = (hi + lo) / 2.0
            self.assertAlmostEqual(target.sum(), 250.0 * T8760, places=3)
            # Band half-width is the configured fraction of the target.
            self.assertTrue(
                np.allclose(hi - target, NYISO_IMPORT_RECON_BAND_FRAC * target)
            )
        finally:
            eia.nyiso_net_interchange = orig


class TestForwardBandSource(unittest.TestCase):
    """The forecast band target = the neighbor's forecast net position.

    Covers :func:`market_sim.data.eia_loader.nyiso_forward_net_import_monthly`
    and the ``mode="forecast"`` path of
    :func:`market_sim.model.transmission.build_import_node_reconciliation`:
    backcast is byte-identical to the default; forecast targets the supplied
    forecast (never the measured schedule); and the band relaxes to ``None``
    when no forecast is supplied.
    """

    def test_forward_monthly_conserves_annual_and_is_load_weighted(self):
        from market_sim.data.eia_loader import nyiso_forward_net_import_monthly

        # Flat split conserves the annual total across 12 months.
        flat = nyiso_forward_net_import_monthly(2030, {2030: 18.0})
        self.assertEqual(flat.shape, (12,))
        self.assertAlmostEqual(flat.sum() / 1e6, 18.0, places=6)

        # A bare float applies to any year.
        self.assertAlmostEqual(
            nyiso_forward_net_import_monthly(2031, 18.0).sum() / 1e6, 18.0, places=6
        )

        # Load weighting puts more imports in the heavier-load half of the year
        # (imports track load) while still conserving the annual total.
        demand = np.r_[np.full(4380, 20000.0), np.full(4380, 30000.0)]
        weighted = nyiso_forward_net_import_monthly(2030, 18.0, system_demand=demand)
        self.assertAlmostEqual(weighted.sum() / 1e6, 18.0, places=6)
        self.assertGreater(weighted[6:].sum(), weighted[:6].sum())

    def test_forward_relaxes_when_no_forecast(self):
        from market_sim.data.eia_loader import nyiso_forward_net_import_monthly

        self.assertIsNone(nyiso_forward_net_import_monthly(2030, None))
        # Year absent from the per-year mapping also relaxes.
        self.assertIsNone(nyiso_forward_net_import_monthly(2031, {2030: 18.0}))

    def test_build_forecast_targets_forecast_not_measured(self):
        # In forecast mode the band must come from the supplied neighbor forecast,
        # NOT the measured schedule — patch the measured loader to a value that
        # would be obviously wrong if it leaked into the forecast target.
        import market_sim.data.eia_loader as eia

        orig = eia.nyiso_net_interchange
        try:
            eia.nyiso_net_interchange = lambda year: np.full(8760, -9999.0)
            fa = _import_node_fleet()
            fa.availability = np.ones((3, 8760))
            out = transmission.build_import_node_reconciliation(
                fa,
                "NYISO",
                2030,
                mode="forecast",
                forward_net_import_twh={2030: 18.0},
            )
            self.assertIsNotNone(out)
            _node_idx, lo, hi = out
            target = (lo + hi) / 2.0
            # Annual band total = the FORECAST 18 TWh, not the measured leak.
            self.assertAlmostEqual(target.sum() / 1e6, 18.0, places=3)
        finally:
            eia.nyiso_net_interchange = orig

    def test_build_forecast_relaxes_without_forecast(self):
        # Forecast mode with no supplied trajectory -> no band (relax to the
        # priced-seam economics), even though a measured schedule "exists".
        import market_sim.data.eia_loader as eia

        orig = eia.nyiso_net_interchange
        try:
            eia.nyiso_net_interchange = lambda year: np.full(8760, -250.0)
            fa = _import_node_fleet()
            fa.availability = np.ones((3, 8760))
            self.assertIsNone(
                transmission.build_import_node_reconciliation(
                    fa, "NYISO", 2030, mode="forecast", forward_net_import_twh=None
                )
            )
        finally:
            eia.nyiso_net_interchange = orig

    def test_build_backcast_mode_matches_default(self):
        # Passing mode="backcast" explicitly is byte-identical to the default
        # (the calibration path is unchanged).
        import market_sim.data.eia_loader as eia

        orig = eia.nyiso_net_interchange
        try:
            eia.nyiso_net_interchange = lambda year: np.full(8760, -250.0)
            fa = _import_node_fleet()
            fa.availability = np.ones((3, 8760))
            default = transmission.build_import_node_reconciliation(fa, "NYISO", 2023)
            explicit = transmission.build_import_node_reconciliation(
                fa, "NYISO", 2023, mode="backcast"
            )
            self.assertTrue(np.allclose(default[1], explicit[1]))
            self.assertTrue(np.allclose(default[2], explicit[2]))
        finally:
            eia.nyiso_net_interchange = orig


if __name__ == "__main__":
    unittest.main()
