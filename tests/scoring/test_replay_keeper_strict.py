"""Strict meta.json replay mapping (the miso-50..53 regression-class closure).

``replay_keeper.build_kwargs`` is the single sanctioned recipe reconstruction
(driving both ``scripts/replay_keeper.py`` and ``run_calibration_full
--replay-bundle``). These tests pin its strict contract: a meta key that maps
to no ``solve_and_persist`` kwarg is a HARD ERROR, never a silent drop — the
miso-50..53 runs reconstructed a recipe from a lossy channel and silently
islanded MISO (see ``results/calibration/FINDING-miso-august-scarcity-2026-07.md``).
"""

import json
import unittest

from scripts.replay_keeper import build_kwargs
from tests.helpers import REPO_ROOT

REPO = REPO_ROOT

_BASE = {"iso": "MISO", "years": [2023], "commitment": False}


class TestStrictUnmappedKeys(unittest.TestCase):
    def test_unmapped_key_is_a_hard_error(self):
        meta = dict(_BASE, not_a_real_kwarg_xyz=True)
        with self.assertRaises(SystemExit) as ctx:
            build_kwargs(meta)
        self.assertIn("not_a_real_kwarg_xyz", str(ctx.exception))

    def test_lossy_channel_meta_is_rejected(self):
        # A run_config.json-shaped record (calibration_flags et al.) is not an
        # exhaustive solve_and_persist snapshot — exactly the trap format.
        meta = dict(_BASE, calibration_flags={"energy_reserve_coopt": True})
        with self.assertRaises(SystemExit) as ctx:
            build_kwargs(meta)
        self.assertIn("calibration_flags", str(ctx.exception))


class TestEnvGatedRecordedOnly(unittest.TestCase):
    def test_inert_env_gated_values_pass(self):
        meta = dict(
            _BASE,
            ercot_zonal_gas_basis=False,
            ercot_west_netload_gas_shape=False,
            ercot_west_gas_delivered_floor=None,
        )
        kwargs = build_kwargs(meta)
        self.assertNotIn("ercot_zonal_gas_basis", kwargs)

    def test_armed_env_gated_value_is_a_hard_error(self):
        meta = dict(_BASE, ercot_zonal_gas_basis=True)
        with self.assertRaises(SystemExit) as ctx:
            build_kwargs(meta)
        self.assertIn("ercot_zonal_gas_basis", str(ctx.exception))


class TestRule26DeletedRecordedOnly(unittest.TestCase):
    """rule-26-deleted fields recorded by bundles that solved while they lived.

    nyiso-136 deleted ``nyiso_solar_registry_cod_dates`` after making
    cod_basis=True unconditional (cache.py epoch 2026-08-15). Outside NYISO
    the flag was never reachable (rule 25), so a recorded default is inert
    provenance; an NYISO bundle recording False selected a basis that no
    longer exists and must hard-error — "read, never replayed".
    """

    def test_non_owning_iso_recorded_default_is_inert(self):
        meta = dict(_BASE, iso="PJM", nyiso_solar_registry_cod_dates=False)
        kwargs = build_kwargs(meta)
        self.assertNotIn("nyiso_solar_registry_cod_dates", kwargs)

    def test_owning_iso_unconditional_value_passes(self):
        meta = dict(_BASE, iso="NYISO", nyiso_solar_registry_cod_dates=True)
        kwargs = build_kwargs(meta)
        self.assertNotIn("nyiso_solar_registry_cod_dates", kwargs)

    def test_owning_iso_other_polarity_is_a_hard_error(self):
        meta = dict(_BASE, iso="NYISO", nyiso_solar_registry_cod_dates=False)
        with self.assertRaises(SystemExit) as ctx:
            build_kwargs(meta)
        self.assertIn("never replayed", str(ctx.exception))


class TestCurrentKeepersReplayCleanly(unittest.TestCase):
    """Every designated keeper's committed meta.json must build under strict
    mode — the CI --replay-bundle path depends on it."""

    def test_all_keeper_metas_build(self):
        from scripts.lib import keeper_store

        keepers = keeper_store.keeper_ids(REPO)
        checked = 0
        for iso in (
            "ERCOT",
            "CAISO",
            "PJM",
            "MISO",
            "NYISO",
            "NEISO",
            "SPP",
            "NWPP",
            "SOCO",
        ):
            rid = keepers.get(iso)
            if not rid:
                continue
            sidecar = REPO / f"frontend/data/backcast/registry/{rid}.json"
            if not sidecar.exists():
                continue
            bundle = json.loads(sidecar.read_text()).get("bundle")
            meta_path = REPO / bundle / "meta.json" if bundle else None
            if not meta_path or not meta_path.exists():
                continue
            kwargs = build_kwargs(json.loads(meta_path.read_text()))
            self.assertGreater(len(kwargs), 50, f"{iso} keeper meta too thin")
            checked += 1
        self.assertGreater(checked, 0, "no keeper meta.json found to check")


if __name__ == "__main__":
    unittest.main()
