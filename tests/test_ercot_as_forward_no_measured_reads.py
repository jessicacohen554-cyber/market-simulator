"""Audit: the ERCOT forward AS path reads ZERO measured AS series.

Stage 5 of ``docs/handoffs/ercot-as-coopt-prompts-2026-07.md`` — the CLAUDE.md
#10 admissibility proof that every ancillary-service quantity on the *forecast*
path regenerates from forward drivers and is never a measured overlay/series read
from disk. This is the guard that keeps the forward path clean as the code evolves
(rules 1, 12, 13, 16): if anyone re-introduces a measured AS read on the forecast
path, one of these tests fails.

The four measured AS series named in the plan — and their loaders — are:

* **ASPLANNP433** (published AS Plan requirement) — ``ercot_as_plan_requirement_mw``
  reads ``ASPLANNP433_<year>.parquet``.
* **NP3-911** (load-resource cleared RRS-UFR) — ``ercot_load_resource_reserve_mw``
  reads ``ercot_<year>_as_up_mw.parquet``.
* **60-Day DAM** (storage AS award + binding MCPC) —
  ``ercot_storage_as_reserve_mw`` reads ``ercot_<year>_as_by_restype_hourly.parquet``
  and the DAM-AS overlay reads ``ercot_<year>_dam_as_mcpc_hourly.parquet``.
* **ordc_reserves** (RTOLCAP/RTOFFCAP supply + RTORDPA) — the measured branch of
  ``ercot_rtolcap_supply_cap_mw`` and the RTORDPA overlay read
  ``ercot_<year>_ordc_reserves_hourly.parquet``.

The guard installs two independent traps and drives the *real* forward
AS-construction path (``config.reserve_config.get_reserve_design``, exactly as
``runner.run_scenario_iso`` calls it):

1. every measured-AS loader is patched to RAISE, and
2. ``pandas.read_parquet`` is wrapped to RAISE on any measured-AS filename (the
   strace-style probe that also catches the inline reads).

The backcast companion (``test_mode_branch_is_not_vacuous``) proves the traps are
live — the measured path IS reachable in backcast — so the forecast passes are
not vacuous green.
"""

import unittest
from types import SimpleNamespace
from unittest import mock

import numpy as np

from market_sim.config.reserve_config import get_reserve_design
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays
from market_sim.results import scarcity

# Substrings that uniquely identify a MEASURED ERCOT AS parquet. If any of these
# is opened on the forecast path the run is inadmissible (CLAUDE.md #10).
_MEASURED_AS_MARKERS = (
    "ASPLANNP433",
    "_as_up_mw",
    "_as_by_restype",
    "_ordc_reserves_hourly",
    "_dam_as_mcpc",
)

# The named measured-AS loaders that live on the reserve-design path. Patched to
# raise so a measured read fails loudly with the offending loader's name.
_MEASURED_LOADERS = (
    "ercot_as_plan_requirement_mw",  # ASPLANNP433
    "ercot_load_resource_reserve_mw",  # NP3-911 (as_up_mw)
    "ercot_storage_as_reserve_mw",  # 60-Day DAM (as_by_restype)
)

T = 24


def _forecast_cfg(**kw) -> ScenarioConfig:
    """The Stage-4 forward AS stack in forecast mode (the ercot41 stack, forward).

    RTC+B regime, endogenous multi-product co-opt with the three forward branches
    on: forward AS requirement (G3), forward RTOLCAP supply cap (WS-A), endogenous
    duration-gated storage AS (G5/WS-B). Overlays are regime-gated inert at
    year >= 2026.
    """
    defaults = dict(
        iso="ERCOT",
        mode="forecast",
        ercot_market_design="rtcb",
        hours=T,
        weather_year=2024,
        energy_reserve_coopt=True,
        ercot_multiproduct_as_coopt=True,
        ercot_as_forward_requirement=True,
        ercot_reserve_supply_cap=True,
        ercot_reserve_supply_forward=True,
        ercot_storage_as_endogenous=True,
        ercot_storage_as_duration_gate=True,
        ercot_ecrs_conservative_deployment=True,
    )
    defaults.update(kw)
    return ScenarioConfig(**defaults)


def _fleet(n_zones: int = 1) -> FleetArrays:
    """Minimal 2-gen ERCOT fleet (gas_cc + wind), 24 h, carrying ``plant_group``.

    ``plant_group`` is required for the WS-A forward supply cap to build (the
    forward base is per-class installed capacity); without it the cap early-returns
    ``None`` (uncapped) — see ``ercot_rtolcap_forward_supply_cap_mw``.
    """
    cc_idx = FUEL_TYPE_NAMES.index("gas_cc")
    wind_idx = FUEL_TYPE_NAMES.index("wind")
    n = 2
    fleet = FleetArrays(
        pmax=np.array([1000.0, 500.0]),
        pmin=np.array([200.0, 0.0]),
        heat_rate=np.array([7.0, 0.0]),
        vom=np.zeros(n),
        emission_rate=np.zeros(n),
        nox_rate=np.zeros(n),
        so2_rate=np.zeros(n),
        zone_idx=np.array([0, min(n_zones - 1, 0)]),
        fuel_type_idx=np.array([cc_idx, wind_idx]),
        availability=np.ones((n, T)),
        unit_ids=["cc0", "wind0"],
        efficiency_bin=np.zeros(n),
        plant_code=np.array([100, 200]),
    )
    fleet.plant_group = np.array(["gas_cc", "wind"])
    return fleet


def _profiles():
    """(system_load, wind_gen, solar_gen) forecast profiles for the co-opt build."""
    return (
        np.ones(T) * 50000.0,
        np.ones(T) * 10000.0,
        np.ones(T) * 5000.0,
    )


class _MeasuredReadTraps:
    """Context manager: every measured-AS read (loader or raw parquet) raises."""

    def __init__(self):
        self._patchers = []

    def __enter__(self):
        def _forbidden(name):
            def _raise(*_a, **_k):
                raise AssertionError(
                    f"measured-AS loader {name!r} was called on the forecast path"
                )

            return _raise

        for name in _MEASURED_LOADERS:
            p = mock.patch.object(scarcity, name, _forbidden(name))
            p.start()
            self._patchers.append(p)

        import pandas

        real_read_parquet = pandas.read_parquet

        def _guarded_read_parquet(path, *a, **k):
            s = str(path)
            for marker in _MEASURED_AS_MARKERS:
                if marker in s:
                    raise AssertionError(
                        f"measured-AS parquet {s!r} was opened on the forecast path"
                    )
            return real_read_parquet(path, *a, **k)

        # Every scarcity/fleet/storage loader resolves ``read_parquet`` from the
        # pandas module (module-level ``import pandas as pd`` or a function-local
        # ``import pandas as pd``), so patching ``pandas.read_parquet`` covers them
        # all — including the dam-AS overlay's local import.
        p = mock.patch.object(pandas, "read_parquet", _guarded_read_parquet)
        p.start()
        self._patchers.append(p)
        return self

    def __exit__(self, *exc):
        for p in reversed(self._patchers):
            p.stop()
        return False


class TestErcotForwardASNoMeasuredReads(unittest.TestCase):
    """The forecast AS path regenerates every quantity from forward drivers."""

    def test_reserve_design_forecast_reads_no_measured_as(self):
        """The real reserve-design build opens no measured AS parquet in forecast."""
        cfg = _forecast_cfg()
        fleet = _fleet()
        load, wind, solar = _profiles()
        with _MeasuredReadTraps():
            design = get_reserve_design(
                cfg,
                fleet,
                T,
                ["ERCOT"],
                system_load=load,
                wind_gen=wind,
                solar_gen=solar,
                sim_year=2026,
            )
        # Four AS products still built — the co-opt is fully populated from the
        # forward formulas, not skipped.
        self.assertEqual(len(design.families), 4)
        for fam in design.families:
            self.assertEqual(fam.requirement.shape, (T,))

    def test_all_products_use_forward_requirement(self):
        """Every AS product resolves from the forward formula (no ASPLANNP433).

        ``ercot_as_forward_requirement_mw`` returns ``None`` for an unrecognized
        product, and the caller then falls back to the measured ASPLANNP433 read.
        A non-``None`` result for all four products is what keeps that fallback
        from ever firing in forecast.
        """
        cfg = _forecast_cfg()
        load, wind, solar = _profiles()
        drivers = scarcity.ercot_as_forward_drivers(load, wind, solar)
        for code in ("REGUP", "RRS", "ECRS", "NSPIN"):
            req = scarcity.ercot_as_forward_requirement_mw(cfg, code, T, drivers)
            self.assertIsNotNone(req, f"{code} fell back to the measured requirement")
            self.assertEqual(np.asarray(req).shape, (T,))
            self.assertTrue((np.asarray(req) > 0).all())

    def test_lr_credit_is_forward_in_forecast(self):
        """The load-resource RRS credit uses the forward enrollment formula."""
        cfg = _forecast_cfg()
        with _MeasuredReadTraps():
            lr = scarcity.ercot_load_resource_reserve_credit_mw(cfg, T, year=2026)
        self.assertEqual(np.asarray(lr).shape, (T,))
        self.assertTrue((np.asarray(lr) >= 0).all())

    def test_rtolcap_uses_forward_formula_not_measured(self):
        """WS-A: the forecast supply cap is the forward formula, not the parquet.

        With ``mode='forecast'`` the seam routes to
        ``ercot_rtolcap_forward_supply_cap_mw`` (built from the fleet + forecast
        net-load), never the measured ``ercot_<year>_ordc_reserves_hourly.parquet``.
        A finite, non-``None`` array under the read traps proves the forward branch
        is genuinely exercised. (The WS-A forward-response *direction* — deeper VRE
        troughs tightening the cap — is checked end-to-end on the real fleet in the
        forecast A/B, not on this toy fleet, whose class labels do not span the
        derived share tables.)
        """
        cfg = _forecast_cfg()
        fleet = _fleet()
        load, wind, solar = _profiles()
        with _MeasuredReadTraps():
            cap = scarcity.ercot_rtolcap_supply_cap_mw(
                cfg, T, fleet, system_load=load, wind_gen=wind, solar_gen=solar
            )
        self.assertIsNotNone(cap, "forward supply cap did not build")
        cap = np.asarray(cap)
        self.assertEqual(cap.shape[-1], T)
        self.assertTrue(np.all(np.isfinite(cap)))
        self.assertTrue(np.all(cap >= 0.0))

    def test_overlays_inert_and_readfree_in_rtcb(self):
        """DAM-AS and RTORDPA overlays are regime-gated inert (and read nothing)."""
        cfg = _forecast_cfg()
        with _MeasuredReadTraps():
            dam = scarcity.ercot_dam_as_overlay_series(
                2026, T, scarcity_threshold=150.0, from_year=2024, config=cfg
            )
            rtordpa = scarcity.ercot_rtordpa_overlay_series(2026, T, config=cfg)
        self.assertEqual(float(np.max(np.abs(dam))), 0.0)
        self.assertEqual(float(np.max(np.abs(rtordpa))), 0.0)

    def test_forward_stack_disables_measured_withholding(self):
        """The forecast stack enables no measured AS-withholding treatment.

        The fleet-level (``load_as_reserve_withholding_mw`` /
        ``load_as_thermal_withholding``) and storage (``ercot_storage_as_reserve_mw``)
        measured reads are reachable only when these flags are on. Locking them off
        in the documented forward stack keeps the whole fleet-build path read-free
        too — the reserve-design tests above cannot cover the fleet-build path.
        """
        cfg = _forecast_cfg()
        self.assertFalse(getattr(cfg, "as_reserve_withholding", False))
        self.assertFalse(getattr(cfg, "ercot_storage_as_reserve", False))
        self.assertFalse(getattr(cfg, "storage_as_commitment", False))
        self.assertFalse(getattr(cfg, "ercot_storage_as_product_credit", False))

    def test_mode_branch_is_not_vacuous(self):
        """Backcast DOES reach the measured loader — proves the traps are live.

        Without this, the forecast passes could be green simply because the
        measured reads are dead code. Here the measured NP3-911 loader is spied;
        it must be called in backcast and NOT in forecast.
        """
        forecast_cfg = _forecast_cfg()
        backcast_cfg = SimpleNamespace(mode="backcast", weather_year=2024)
        spy = mock.MagicMock(return_value=np.zeros(T))
        with mock.patch.object(scarcity, "ercot_load_resource_reserve_mw", spy):
            scarcity.ercot_load_resource_reserve_credit_mw(forecast_cfg, T, year=2026)
            self.assertEqual(
                spy.call_count, 0, "forecast must not read the measured NP3-911 series"
            )
            scarcity.ercot_load_resource_reserve_credit_mw(backcast_cfg, T, year=2024)
            self.assertEqual(
                spy.call_count, 1, "backcast must read the measured NP3-911 series"
            )


if __name__ == "__main__":
    unittest.main()
