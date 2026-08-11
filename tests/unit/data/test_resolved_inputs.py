"""caiso-190: what the solve's disposable inputs RESOLVED to, persisted.

The defect this covers is not a wrong number — it is an *unanswerable
question*. Every CAISO bundle from caiso-175 onward recorded
``capacity_deliverability_limits: true`` while the LP solved on the baked
7,500 MW fitted scalar, and no committed artifact distinguished those runs
from ones that solved on the published MIC
(``FINDING-caiso188-import-tranche-dof-2026-08-09.md`` §4/§6b).

So the tests are organised around the three claims that close it:

1. The resolution is **correct** in all three states (flag off / armed and
   resolving / armed and degraded).
2. The recorded value is **the value the LP was handed** — enforced by having
   one derivation and statically pinning the topology step to it, because a
   second derivation done at record time is the very drift that produced the
   defect.
3. Behaviour with the partition **present is unchanged** — the seam cap the LP
   receives is byte-for-byte what it was before the resolver moved.
"""

from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import resolved_inputs as RI
from market_sim.model.interchange.spec import (
    apply_interchange_topology,
    get_interchange_spec,
)
from scripts.lib import clean_io
from tests.helpers import REPO_ROOT

_COLS = [
    "iso",
    "area",
    "area_type",
    "delivery_year",
    "season",
    "metric",
    "value_mw",
    "value_pu",
    "source_doc",
    "source_page",
]

#: The baked WECC_import_simultaneous scalar — the RESIDUAL-IDENTIFIED value
#: that governs whenever Part A does not resolve (caiso-188 §4).
BAKED_CAP_MW = 7500.0


def _mic_row(area: str, mw: float, delivery_year: str = "2025") -> dict:
    """One CAISO branch-group MIC row (an import limit into WECC_import)."""
    return {
        "iso": "CAISO",
        "area": area,
        "area_type": "branch_group",
        "delivery_year": delivery_year,
        "season": "annual",
        "metric": "import_limit",
        "value_mw": mw,
        "value_pu": None,
        "source_doc": "fixture",
        "source_page": "1",
    }


class _CleanTree:
    """Context manager pointing ``paths.CLEAN_DIR`` at an empty tmp tree."""

    def __enter__(self) -> Path:
        self._tmp = TemporaryDirectory()
        self._orig = clean_io.paths.CLEAN_DIR
        self.root = Path(self._tmp.name) / "clean"
        self.root.mkdir(parents=True)
        clean_io.paths.CLEAN_DIR = self.root
        RI.reset_recorded()
        return self.root

    def __exit__(self, *exc) -> None:
        clean_io.paths.CLEAN_DIR = self._orig
        self._tmp.cleanup()
        RI.reset_recorded()

    def write_mic(self, *rows: dict) -> None:
        """Write a capacity-deliverability partition from MIC rows."""
        df = pd.DataFrame(list(rows), columns=_COLS)
        df["value_mw"] = df["value_mw"].astype("float64")
        df["value_pu"] = df["value_pu"].astype("float64")
        clean_io.write_clean(df, "capacity-deliverability", iso="CAISO")

    def write_hydro_modes(self, shapeable: dict[int, bool]) -> None:
        """Write a hydro-plant-modes partition with a known plant count.

        Through ``write_clean``, not a bare ``to_parquet``: the reader
        validates the embedded datatype metadata, so a hand-rolled parquet
        raises ``SchemaError`` and the probe reports "no partition" for the
        wrong reason.
        """
        df = pd.DataFrame(
            [
                {
                    "iso": "CAISO",
                    "plant_id": pid,
                    "eha_ptid": str(pid),
                    "plant_name": f"fixture-{pid}",
                    "ch_mw": 10.0,
                    "mode": "Peaking" if sh else "Run-of-river",
                    "shapeable": sh,
                    "method": "eha_mode",
                }
                for pid, sh in shapeable.items()
            ]
        )
        df["plant_id"] = df["plant_id"].astype("int64")
        df["ch_mw"] = df["ch_mw"].astype("float64")
        df["shapeable"] = df["shapeable"].astype("bool")
        clean_io.write_clean(df, "hydro-plant-modes", iso="CAISO")


class TestSeamResolution(unittest.TestCase):
    """The three states the seam cap can resolve into, each named explicitly."""

    def setUp(self) -> None:
        self.tree = _CleanTree()
        self.tree.__enter__()
        self.addCleanup(self.tree.__exit__, None, None, None)

    def _resolve(self, config):
        return RI.resolve_seam_import_cap(
            config, "CAISO", 2025, get_iso_config("CAISO")
        )

    def test_flag_off_records_the_baked_cap_as_the_declared_limit(self) -> None:
        """Flag off: the baked scalar IS the intended limit, not a degradation."""
        res = self._resolve(ScenarioConfig())
        self.assertFalse(res.flag_armed)
        self.assertEqual(res.source, "flag_off")
        self.assertEqual(res.cap_mw, BAKED_CAP_MW)

    def test_armed_without_partition_resolves_to_the_fitted_fallback(self) -> None:
        """THE caiso-188 defect state, now named in the record."""
        res = self._resolve(
            ScenarioConfig().with_overrides(capacity_deliverability_limits=True)
        )
        self.assertTrue(res.flag_armed)
        self.assertEqual(res.source, "baked_fallback")
        self.assertEqual(res.cap_mw, BAKED_CAP_MW)
        # The distinction the bundle could not previously make: armed-and-
        # degraded is NOT the same record as armed-and-applied.
        self.assertNotEqual(res.source, "mic_partition")

    def test_armed_with_partition_resolves_to_the_published_mic(self) -> None:
        """Part A resolving: the summed branch-group MIC, not the fitted cap."""
        self.tree.write_mic(_mic_row("COTP", 4000.0), _mic_row("PALO", 5000.0))
        res = self._resolve(
            ScenarioConfig().with_overrides(capacity_deliverability_limits=True)
        )
        self.assertEqual(res.source, "mic_partition")
        self.assertEqual(res.cap_mw, 9000.0)
        self.assertEqual(res.delivery_year, "2025")
        self.assertEqual(res.import_zone, "WECC_import")


class TestTopologyAppliesAndRecordsTheResolution(unittest.TestCase):
    """The LP-facing half: what gets applied, and that the record matches it."""

    def setUp(self) -> None:
        self.tree = _CleanTree()
        self.tree.__enter__()
        self.addCleanup(self.tree.__exit__, None, None, None)

    def _apply(self, config):
        return apply_interchange_topology(
            get_iso_config("CAISO"),
            get_interchange_spec(config, "CAISO", 2025),
            config,
            year=2025,
            extend_node=True,
        )

    def _seam_cap(self, iso_config) -> float | None:
        caps = {lim.name: lim.cap_mw for lim in iso_config.interface_limits}
        return caps.get("WECC_import_simultaneous")

    def test_partition_present_applies_the_mic_and_records_it(self) -> None:
        """Behaviour with the partition present — the cap the LP receives.

        This is the (c) leg: the resolver moving homes must not change the
        applied value. 9,000 MW of summed MIC replaces the 7,500 MW scalar,
        exactly as it did before caiso-190.
        """
        self.tree.write_mic(_mic_row("COTP", 4000.0), _mic_row("PALO", 5000.0))
        config = ScenarioConfig().with_overrides(capacity_deliverability_limits=True)
        updated = self._apply(config)
        self.assertEqual(self._seam_cap(updated), 9000.0)
        recorded = RI.recorded_seam_resolutions()[("CAISO", 2025)]
        self.assertEqual(recorded.source, "mic_partition")
        # The record and the LP agree — the whole point of one derivation.
        self.assertEqual(recorded.cap_mw, self._seam_cap(updated))

    def test_partition_absent_keeps_the_baked_cap_and_records_the_fallback(
        self,
    ) -> None:
        """The degraded state still solves, but is now self-identifying."""
        config = ScenarioConfig().with_overrides(capacity_deliverability_limits=True)
        with self.assertLogs("market_sim.model.interchange.spec", level="WARNING"):
            updated = self._apply(config)
        self.assertEqual(self._seam_cap(updated), BAKED_CAP_MW)
        recorded = RI.recorded_seam_resolutions()[("CAISO", 2025)]
        self.assertEqual(recorded.source, "baked_fallback")
        self.assertEqual(recorded.cap_mw, BAKED_CAP_MW)

    def test_flag_off_is_recorded_too(self) -> None:
        """Even an unarmed run records which cap governed it."""
        self._apply(ScenarioConfig())
        recorded = RI.recorded_seam_resolutions()[("CAISO", 2025)]
        self.assertEqual(recorded.source, "flag_off")
        self.assertEqual(recorded.cap_mw, BAKED_CAP_MW)


class TestEverySolvePathIsGuarded(unittest.TestCase):
    """Static: a module that reaches the LP must also call the guard.

    THE caiso-190 invariant, and the mechanical form of the lesson that cost
    two sessions. caiso-157 wrote ``check_clean_partitions`` and wired it to
    ``pipeline/year.py::run_year_solve`` — a function with **no production
    caller** — so the guard passed CI (its unit tests call it directly) while
    being dead on every lane that actually solves. The defect it was built to
    prevent then recurred across every CAISO promotion from caiso-175 onward
    (caiso-188 §6).

    A unit test of the guard cannot catch that; only a test of the WIRING can.
    ``run_energy_solve`` is the single door to the LP, so the invariant is:
    every module that calls it also calls ``check_clean_partitions``.
    """

    #: Modules that reach the LP. Kept in sync by
    #: ``test_p1_prep_wiring.py::test_run_energy_solve_call_sites_are_the_known_three``,
    #: which fails if a fourth appears — so this list cannot silently go stale.
    SOLVE_PATHS = (
        "src/market_sim/pipeline/year.py",
        "src/market_sim/runner.py",
        "scripts/run_calibration.py",
    )

    def _calls(self, rel: str) -> set[str]:
        tree = ast.parse((REPO_ROOT / rel).read_text())
        return {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }

    def test_every_run_energy_solve_module_calls_the_guard(self) -> None:
        for rel in self.SOLVE_PATHS:
            with self.subTest(module=rel):
                calls = self._calls(rel)
                self.assertIn(
                    "run_energy_solve",
                    calls,
                    f"{rel} no longer reaches the LP — update SOLVE_PATHS.",
                )
                self.assertIn(
                    "check_clean_partitions",
                    calls,
                    f"{rel} reaches the LP through run_energy_solve but never "
                    "calls check_clean_partitions. That exact gap — a guard "
                    "with no call site on the lane being solved — let the "
                    "caiso-157 defect recur across every CAISO keeper "
                    "promotion from caiso-175 onward (caiso-188 §6).",
                )

    def test_the_calibration_lane_is_strict(self) -> None:
        """Keepers are promoted from this lane; a declared fallback is fatal."""
        source = (REPO_ROOT / "scripts" / "run_calibration.py").read_text()
        self.assertIn(
            "check_clean_partitions(config, iso, strict=True)",
            source,
            "the backcast/calibration lane must pass strict=True explicitly — "
            "it is the lane keepers are promoted from, so even a mechanism "
            "with a declared fallback must refuse rather than degrade.",
        )

    def test_the_forecast_lane_opts_out_deliberately(self) -> None:
        """The one non-strict caller states so at the call site."""
        source = (REPO_ROOT / "src" / "market_sim" / "runner.py").read_text()
        self.assertIn(
            "check_clean_partitions(config, iso, strict=False)",
            source,
            "the forecast orchestrator's non-strict posture must be explicit "
            "at the call site, not inherited from a default.",
        )


class TestSpecResolvesThroughHelper(unittest.TestCase):
    """Static: the topology step must resolve through the SHARED derivation.

    caiso-162's lesson was "check a call site exists on the lane being solved";
    caiso-188 §7 item 5 added "check the DATA the gate resolves through". This
    is both, made mechanical: if a future edit re-inlines the seam derivation
    into ``spec.py``, the recorded provenance could drift from the applied cap
    without any test noticing — which is precisely how the original defect
    survived five keeper promotions.
    """

    @classmethod
    def setUpClass(cls) -> None:
        path = REPO_ROOT / "src" / "market_sim" / "model" / "interchange" / "spec.py"
        cls.tree = ast.parse(path.read_text())

    def _called_names(self) -> set[str]:
        return {
            node.func.id
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }

    def test_spec_calls_the_shared_resolver(self) -> None:
        self.assertIn(
            "resolve_seam_import_cap",
            self._called_names(),
            "interchange/spec.py must resolve the seam cap through "
            "market_sim.data.resolved_inputs.resolve_seam_import_cap — a "
            "second in-line derivation can drift from the recorded value "
            "(caiso-188 §7 item 5).",
        )

    def test_spec_records_the_resolution(self) -> None:
        self.assertIn(
            "record_seam_resolution",
            self._called_names(),
            "interchange/spec.py must record what it resolved, or "
            "run_config.json's resolved_inputs falls back to 'unrecorded' and "
            "the bundle again cannot say which cap it solved against.",
        )

    def test_spec_no_longer_derives_the_seam_inline(self) -> None:
        """The old inline derivation must not come back alongside the helper."""
        self.assertNotIn(
            "import_limit_by_area",
            self._called_names(),
            "the per-area import-limit read belongs to the shared resolver "
            "only; a second call site here is a drift channel.",
        )


class TestResolvedInputsBlock(unittest.TestCase):
    """The payload persisted into run_config.json."""

    def setUp(self) -> None:
        self.tree = _CleanTree()
        self.tree.__enter__()
        self.addCleanup(self.tree.__exit__, None, None, None)

    def test_unrecorded_when_no_solve_resolved_a_seam(self) -> None:
        """Honest 'unrecorded' beats a back-filled re-derivation."""
        block = RI.resolved_inputs_block(ScenarioConfig(), "CAISO")
        self.assertEqual(block["seam_import_cap"]["status"], "unrecorded")
        self.assertEqual(block["seam_import_cap"]["by_year"], {})

    def test_records_every_year_of_a_multi_year_bundle(self) -> None:
        config = ScenarioConfig().with_overrides(capacity_deliverability_limits=True)
        for year in (2023, 2024, 2025):
            apply_interchange_topology(
                get_iso_config("CAISO"),
                get_interchange_spec(config, "CAISO", year),
                config,
                year=year,
                extend_node=True,
            )
        block = RI.resolved_inputs_block(config, "CAISO")
        self.assertEqual(block["seam_import_cap"]["status"], "recorded")
        self.assertEqual(
            sorted(block["seam_import_cap"]["by_year"]), ["2023", "2024", "2025"]
        )
        for row in block["seam_import_cap"]["by_year"].values():
            self.assertEqual(row["source"], "baked_fallback")
            self.assertEqual(row["cap_mw"], BAKED_CAP_MW)

    def test_hydro_plant_modes_presence_and_count(self) -> None:
        """caiso-188 §6c: make hydro_ror_split's engagement checkable."""
        config = ScenarioConfig().with_overrides(hydro_ror_split=True)
        absent = RI.resolved_inputs_block(config, "CAISO")["hydro_plant_modes"]
        self.assertTrue(absent["flag_armed"])
        self.assertFalse(absent["partition_present"])
        self.assertIsNone(absent["classified_plants"])

        self.tree.write_hydro_modes({1: True, 2: False, 3: True})
        present = RI.resolved_inputs_block(config, "CAISO")["hydro_plant_modes"]
        self.assertTrue(present["partition_present"])
        self.assertEqual(present["classified_plants"], 3)
        self.assertEqual(present["shapeable_plants"], 2)

    def test_campd_extract_identity(self) -> None:
        """The measured overlay's bytes are nameable from the bundle alone.

        ``outage_source="historic"`` is a backcast-only measured overlay
        (rule 13 ``[R-MEASURED]``), so the config must be in backcast mode for
        it to be armable at all.
        """
        config = ScenarioConfig().with_overrides(
            mode="backcast", outage_source="historic"
        )
        block = RI.resolved_inputs_block(config, "CAISO")["campd_unit_outages"]
        self.assertTrue(block["armed"])
        self.assertEqual(block["path"], "data/raw/campd-unit-outages-CAISO.csv")
        if block["present"]:
            self.assertEqual(len(block["sha256"]), 64)
            self.assertGreater(block["bytes"], 0)


class TestRunConfigCarriesResolvedInputs(unittest.TestCase):
    """End-to-end: the block lands in run_config.json, additively."""

    def setUp(self) -> None:
        self.tree = _CleanTree()
        self.tree.__enter__()
        self.addCleanup(self.tree.__exit__, None, None, None)

    def test_written_run_config_has_the_resolved_seam_cap(self) -> None:
        from market_sim.pipeline.persist import write_run_config

        config = ScenarioConfig().with_overrides(capacity_deliverability_limits=True)
        self.tree.write_mic(_mic_row("COTP", 4200.0))
        apply_interchange_topology(
            get_iso_config("CAISO"),
            get_interchange_spec(config, "CAISO", 2025),
            config,
            year=2025,
            extend_node=True,
        )
        with TemporaryDirectory() as out:
            run_dir = Path(out)
            write_run_config(
                run_dir, config, {"iso": "CAISO", "years": [2025], "hours": 8760}
            )
            payload = json.loads((run_dir / "run_config.json").read_text())

        self.assertIn("resolved_inputs", payload)
        block = payload["resolved_inputs"]
        self.assertEqual(block["iso"], "CAISO")
        row = block["seam_import_cap"]["by_year"]["2025"]
        self.assertEqual(row["source"], "mic_partition")
        self.assertEqual(row["cap_mw"], 4200.0)

        # ADDITIVE: scenario_config is what --reuse-solved diffs, and it must
        # not have gained a key (the block is deliberately top-level).
        self.assertNotIn("resolved_inputs", payload["scenario_config"])
        self.assertIn("scenario_config", payload)
        self.assertIn("environment", payload)


if __name__ == "__main__":
    unittest.main()
