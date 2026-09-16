"""Stage-6 fleet-unification parity tests (orchestrator-unification plan §6).

Pins the invariants of the Stage-6 migration, which pointed the backcast
orchestrator at the shared ``fleet.build_dispatch_fleet`` /
``fleet.build_base_fleet`` and extracted the netload-drag / NEISO-coldsnap
gate-and-log wrappers:

* the shared campd-branch fuel-frac machinery reproduces BOTH callers'
  pre-Stage-6 behaviour -- the runner's flat passthrough dict at the config
  defaults, and the backcast's per-supply routing (tiered PRB follower gate
  included) when the sigmoid fields are set;
* the backcast keyword seams (``imports_after_hydro``,
  ``drop_biomass_units``, ``apply_emission_overrides=False``) reproduce the
  backcast's historical fleet ordering and content;
* ``apply_neiso_coldsnap_derate`` reads the ScenarioConfig coefficient
  FIELDS (rule 24 -- no getattr fallback literals) and is a strict no-op off
  its gate; same for ``apply_netload_drag_floors`` with both drag flags off.

Trivial cases only (CLAUDE.md testing pattern): tiny fleets, no disk.
"""

import unittest
from unittest import mock

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import fleet as fleet_mod
from market_sim.data.fleet import (
    Generator,
    apply_neiso_coldsnap_derate,
    apply_netload_drag_floors,
    build_dispatch_fleet,
    campd_tranche_fuel_frac,
    generators_to_fleet_arrays,
)


def _gen(uid, fuel, zone="north", coal_supply="", plant_code=0, **kw):
    """One trivial-case generator."""
    return Generator(
        unit_id=uid,
        name=uid,
        zone=zone,
        fuel_type=fuel,
        pmax_mw=100.0,
        pmin_mw=0.0,
        heat_rate=9.0,
        eford=0.05,
        coal_supply=coal_supply,
        plant_code=plant_code,
        **kw,
    )


def _config(**overrides):
    """A small-hours config on a fake ISO (no on-disk data resolves)."""
    base = dict(iso="ERCOT", hours=24, use_campd_bins=False)
    base.update(overrides)
    return ScenarioConfig(**base)


class TestBuildDispatchFleetSeams(unittest.TestCase):
    """The Stage-6 keyword seams reproduce each orchestrator's behaviour."""

    def _small_fleet(self):
        return [
            _gen("COAL1", "coal", coal_supply="prb", plant_code=11),
            _gen("BIO1", "biomass", plant_code=12),
            _gen("NUKE1", "nuclear", plant_code=13),
        ]

    def _imports(self):
        imp = _gen("IMP1", "import", plant_code=99)
        return [imp]

    def test_runner_default_order_imports_inline(self):
        """Defaults (runner call shape): imports merge before the split."""
        fleet = self._small_fleet()
        out, fracs, hydro_idx, hydro_budget = build_dispatch_fleet(
            fleet,
            None,  # campd_bins: legacy split branch
            self._imports(),
            "ZZTEST",  # no hydro data resolves for a fake ISO
            2024,
            ["north"],
            _config(),
        )
        # Import unit present and positioned before any (absent) hydro.
        self.assertIn("IMP1", [g.unit_id for g in out])
        self.assertIsNone(hydro_idx)
        self.assertEqual(len(out), len(fracs))
        # Biomass kept at the default (runner never drops it).
        self.assertIn("BIO1", [g.unit_id for g in out])

    def test_backcast_seams_imports_after_hydro_and_biomass_drop(self):
        """Backcast call shape: biomass dropped, imports appended last."""
        fleet = self._small_fleet()
        out, fracs, hydro_idx, _ = build_dispatch_fleet(
            fleet,
            None,
            self._imports(),
            "ZZTEST",
            2024,
            ["north"],
            _config(),
            drop_biomass_units=True,
            imports_after_hydro=True,
            apply_emission_overrides=False,
        )
        ids = [g.unit_id for g in out]
        self.assertNotIn("BIO1", ids)
        # Imports are the LAST columns (after the -- here absent -- hydro).
        self.assertEqual(ids[-1], "IMP1")
        self.assertEqual(fracs[-1], 1.0)
        self.assertEqual(len(out), len(fracs))

    def test_emission_override_seam_off_never_touches_rates(self):
        """apply_emission_overrides=False must not call either override fn."""
        with (
            mock.patch.object(fleet_mod, "apply_plant_emission_rates_v2") as v2,
            mock.patch.object(fleet_mod, "apply_plant_emission_rates") as v1,
        ):
            build_dispatch_fleet(
                self._small_fleet(),
                None,
                [],
                "ZZTEST",
                2024,
                ["north"],
                _config(use_plant_emission_rates=True),
                apply_emission_overrides=False,
            )
            v1.assert_not_called()
            v2.assert_not_called()

    def test_campd_branch_flat_defaults_match_pre_stage6_runner_dict(self):
        """At the config defaults the campd branch's fuel fracs equal the
        pre-Stage-6 runner reference: campd_tranche_fuel_frac with the inline
        {"prb": p, "subbituminous": p} dict (p = 1.0 default)."""
        import pandas as pd

        cfg = _config()
        fleet = [
            _gen("COAL_prb", "coal", coal_supply="prb", plant_code=21),
            _gen("COAL_sub", "coal", coal_supply="subbituminous", plant_code=22),
            _gen("CC1", "gas_cc", plant_code=23),
        ]
        out, fracs, _, _ = build_dispatch_fleet(
            fleet,
            pd.DataFrame({"sentinel": [1]}),  # non-None selects campd branch
            [],
            "ZZTEST",
            2024,
            ["north"],
            cfg,
        )
        ref = [
            campd_tranche_fuel_frac(
                g,
                {
                    "prb": cfg.coal_prb_passthrough,
                    "subbituminous": cfg.coal_prb_passthrough,
                },
                None,
                econ_srmc_bound=False,
            )
            for g in fleet
        ]
        for got, want in zip(fracs[: len(ref)], ref):
            np.testing.assert_array_equal(got, want)

    def test_campd_branch_tiered_follower_routing_matches_backcast(self):
        """With sigmoid+tiered set (the backcast keepers' shape), a
        low-must-run prb plant routes to the follower curve exactly as the
        pre-Stage-6 backcast inline block did."""
        import pandas as pd

        from market_sim.data.fuel import (
            coal_passthrough_by_supply,
            prb_follower_passthrough_series,
        )

        cfg = _config(
            coal_prb_passthrough_sigmoid=True,
            coal_prb_passthrough_tiered=True,
        )
        low_pc, high_pc = 6180, 6181  # arbitrary; mustrun map patched below
        fleet = [
            _gen("PRB_low", "coal", coal_supply="prb", plant_code=low_pc),
            _gen("PRB_high", "coal", coal_supply="prb", plant_code=high_pc),
        ]
        mustrun = {
            low_pc: 0.0,  # <= follower threshold -> follower tier
            high_pc: 100.0,  # baseload tier
        }
        with mock.patch.object(fleet_mod, "COAL_MUSTRUN_BY_PLANT", mustrun):
            _, fracs, _, _ = build_dispatch_fleet(
                fleet,
                pd.DataFrame({"sentinel": [1]}),
                [],
                "ZZTEST",
                2024,
                ["north"],
                cfg,
            )
        pt = coal_passthrough_by_supply(cfg, 2024, cfg.hours)
        foll = {
            **pt,
            "prb": prb_follower_passthrough_series(cfg, 2024, cfg.hours),
        }
        ref_low = campd_tranche_fuel_frac(fleet[0], foll, None)
        ref_high = campd_tranche_fuel_frac(fleet[1], pt, None)
        np.testing.assert_array_equal(fracs[0], ref_low)
        np.testing.assert_array_equal(fracs[1], ref_high)


class TestSharedAvailabilityWrappers(unittest.TestCase):
    """Gate-and-log wrappers: strict no-ops off their gates; field threading."""

    def _arrays(self, cfg):
        gens = [_gen("G1", "gas_cc", plant_code=31)]
        return (
            gens,
            generators_to_fleet_arrays(
                gens, ["north"], hours=cfg.hours, iso="ZZTEST", config=cfg
            ),
        )

    def test_drag_wrapper_noop_with_flags_off(self):
        cfg = _config()
        gens, fa = self._arrays(cfg)
        before = np.array(fa.min_gen, copy=True)
        demand = np.full((1, cfg.hours), 50.0)
        zero_cf = np.zeros((1, cfg.hours))
        zero_cap = np.zeros(1)
        apply_netload_drag_floors(
            fa, gens, demand, zero_cf, zero_cap, zero_cf, zero_cap, cfg, "ZZTEST", 2024
        )
        np.testing.assert_array_equal(np.asarray(fa.min_gen), before)

    def test_coldsnap_wrapper_noop_off_gate(self):
        cfg = _config()
        gens, fa = self._arrays(cfg)
        with mock.patch(
            "market_sim.model.transmission.inject_neiso_gas_coldsnap_derate"
        ) as inj:
            apply_neiso_coldsnap_derate(fa, cfg, "NEISO", 2024)
            inj.assert_not_called()

    def test_coldsnap_wrapper_threads_config_fields(self):
        """Rule 24: the wrapper passes the ScenarioConfig FIELD values (no
        fallback literals), including non-default overrides."""
        cfg = _config(
            neiso_gas_coldsnap_derate=True,
            neiso_gas_derate_t0_c=-5.5,
            neiso_gas_derate_slope_per_c=0.02,
            neiso_gas_derate_cap=0.25,
        )
        gens, fa = self._arrays(cfg)
        with mock.patch(
            "market_sim.model.transmission.inject_neiso_gas_coldsnap_derate",
            return_value=False,
        ) as inj:
            apply_neiso_coldsnap_derate(fa, cfg, "NEISO", 2024)
            # dual_switch_active=None is the LEGACY exemption (neiso-110): the
            # conditional dual-fuel scope correction is gated default-off, so an
            # unarmed config threads None and the call is behaviourally unchanged.
            inj.assert_called_once_with(
                fa, "NEISO", 2024, -5.5, 0.02, 0.25, dual_switch_active=None
            )

    def test_coldsnap_coefficient_fields_default_to_cited_values(self):
        """The former getattr literals are now the field defaults."""
        cfg = ScenarioConfig(iso="NEISO")
        self.assertEqual(cfg.neiso_gas_derate_t0_c, -7.0)
        self.assertEqual(cfg.neiso_gas_derate_slope_per_c, 0.018)
        self.assertEqual(cfg.neiso_gas_derate_cap, 0.20)


if __name__ == "__main__":
    unittest.main()
