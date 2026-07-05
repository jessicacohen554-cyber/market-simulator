"""Tests for run_calibration_full's D-3 zero-forcing ablation wiring (rule 21).

Exercises ``apply_zero_forcing_ablation`` (the args-forcing helper, mirror of
apply_statistical_mode) and the arg-alias reconciliation — no LP solve. The
module is heavy to import (pulls in the model); it is loaded by path once.
"""

import argparse
import importlib.util
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "run_calibration_full", str(_REPO / "scripts" / "run_calibration_full.py")
)
rcf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rcf)


def _armed_args(zero=True):
    return argparse.Namespace(
        zero_forcing_ablation=zero,
        reliability_floor=True,
        caiso_ra_mustoffer=True,
        caiso_ra_startup_bridge=True,
        caiso_ra_bridge_decommit=True,
        nyiso_local_selfsupply=True,
        ct_mustrun_per_plant=True,
        caiso_gas_commitment_floor=True,
        ct_deployment=True,  # aliases ct_deployment_overlay
        reliability_deployment=True,  # aliases reliability_deployment_overlay
        wefor_residual=0.06,
        wefor_relief_groups="ST_GAS",
    )


class ApplyAblationTest(unittest.TestCase):
    def test_forces_every_reachable_merchant_toggle_off(self):
        ns = _armed_args()
        rcf.apply_zero_forcing_ablation(ns)
        for f in (
            "reliability_floor",
            "caiso_ra_mustoffer",
            "caiso_ra_startup_bridge",
            "caiso_ra_bridge_decommit",
            "nyiso_local_selfsupply",
            "ct_mustrun_per_plant",
            "caiso_gas_commitment_floor",
            "ct_deployment",
            "reliability_deployment",
        ):
            self.assertFalse(getattr(ns, f), f)

    def test_wefor_neutralized(self):
        ns = _armed_args()
        rcf.apply_zero_forcing_ablation(ns)
        self.assertIsNone(ns.wefor_residual)
        self.assertIsNone(ns.wefor_relief_groups)

    def test_noop_when_flag_off(self):
        ns = _armed_args(zero=False)
        rcf.apply_zero_forcing_ablation(ns)
        self.assertTrue(ns.reliability_floor)  # untouched
        self.assertEqual(ns.wefor_residual, 0.06)

    def test_alias_map_covers_registry_name_mismatches(self):
        # Every merchant config field either has a same-named CLI arg or an
        # explicit alias — otherwise the ablation would silently miss it. The
        # net-load drags have no CLI arg here (default-off), so they are exempt.
        from market_sim.data.floor_mechanisms import merchant_ablation_fields

        no_cli = {"ct_netload_drag", "gas_st_netload_drag"}
        for field_name in merchant_ablation_fields():
            if field_name in no_cli:
                continue
            arg = rcf._ABLATION_ARG_ALIASES.get(field_name, field_name)
            self.assertTrue(
                hasattr(_armed_args(), arg),
                f"merchant field {field_name} maps to arg {arg} which is not "
                "settable — add an alias in _ABLATION_ARG_ALIASES",
            )


class OutDirNamingTest(unittest.TestCase):
    def test_twin_dir_and_ablation_of(self):
        # Mirrors main()'s redirect: <bundle> -> <bundle>-ablation, ablation_of
        # is the original basename.
        base = Path("results/calibration/caiso/keeperX")
        ablation_of = base.name
        twin = base.with_name(f"{base.name}-ablation")
        self.assertEqual(ablation_of, "keeperX")
        self.assertEqual(twin.name, "keeperX-ablation")


if __name__ == "__main__":
    unittest.main()
