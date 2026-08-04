"""Run-record provenance regression tests (FFR-3R).

A run record must describe the ``ScenarioConfig`` the solve ACTUALLY ran on.
Four lanes each found a record key that instead described the CLI request:

===========  ============================================================
FFR-1D       a meta entry sourced from a flag that armed nothing
FFR-3D       ``entry_lookahead_reprice`` / ``correlated_forced_outage``:
             once the flags became tri-state, ``bool(None)`` stamped
             ``false`` on every leg that ran the shipped ``True``
FFR-2E       ``capacity_market_clearing``: a flag-sourced value
             mis-classified every shipped-posture leg as curve-OFF
FFR-3L       ``retirement_rule``: missed by the FFR-3D sweep, so every
             shipped-default leg recorded ``null`` for the rule it solved
===========  ============================================================

These tests target the CLASS, not a fifth key. The property under test:

    every record key naming a ``ScenarioConfig`` field equals the solved
    config's value for it, with a declared, reasoned allowlist as the only
    exemption — and a key naming a config field that is in no spec is itself
    a violation.

:class:`TestHistoricalDefect` proves the check catches the real bug, by
rebuilding the FFR-3D/FFR-3L sourcing and showing it FAILS while the shipped
sourcing PASSES.

**Audit scope (no silent cap).** The static lint covers the record-writing
runners and registrars audited by FFR-3R:
``scripts/run_capacity_hindcast.py``, ``scripts/run_full_horizon.py``,
``scripts/register_forecast_baseline.py``, ``scripts/register_hindcast.py``,
``scripts/register_forecast_run.py``. ``scripts/run_calibration_full.py`` is
DELIBERATELY excluded: its ``meta.json`` is by design a record of the
``solve_and_persist`` KWARGS (``run_kwargs.build_kwargs`` reconstructs a replay
from it), not of the resolved config — the resolved config is recorded
separately in that bundle's ``run_config.json`` ``scenario_config`` block by
``pipeline.persist.write_run_config``, which is ``dataclasses.asdict(cfg)`` and
therefore solved-sourced by construction. Its own fidelity surface is covered
by ``tests/regression/test_recorded_cfg_fidelity.py`` and
``market_sim.pipeline.flags``. See
``docs/handoffs/ffr-3r-record-provenance-2026-08-04.md`` for the full census.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from market_sim.config.scenarios import ScenarioConfig
from scripts.lib.run_record import (
    Derived,
    FromArgs,
    FromConfig,
    RecordSpec,
    config_field_names,
)
from tests.helpers import REPO_ROOT

import scripts.register_forecast_baseline as RB
import scripts.run_capacity_hindcast as RH
import scripts.run_full_horizon as RF


#: Record-writing modules FFR-3R audited, and the record specs each declares.
AUDITED_SPECS = {
    "scripts/run_capacity_hindcast.py": RH.META_RECORD_SPEC,
    "scripts/run_full_horizon.py": RF.SUMMARY_RECORD_SPEC,
    "scripts/register_forecast_baseline.py": RB.SIDECAR_RECORD_SPEC,
}

#: Record-writing modules the static lint scans (a superset of the above: the
#: two registrars that copy a record forward carry no spec of their own but
#: must not introduce an args-sourced config-named key either).
LINTED_FILES = (
    *AUDITED_SPECS,
    "scripts/run_ces_leg.py",
    "scripts/register_hindcast.py",
    "scripts/register_forecast_run.py",
)


def _hindcast_meta(**build_kwargs) -> tuple[dict, ScenarioConfig, dict]:
    """Build a hindcast meta config-block the way ``main()`` does.

    Mirrors the runner's own assembly (spec ``build`` over the solved config)
    without solving, so the provenance contract is testable in the fast lane.

    Returns:
        ``(block, config, ctx)``.
    """
    iso = build_kwargs["iso"]
    force = build_kwargs.get("capacity_market_clearing", False)
    fixed = build_kwargs.get("fixed_net_cone", False)
    config = RH.build_config(**build_kwargs)
    _, posture = RH.resolve_capacity_clearing_posture(iso, force, fixed)
    ctx = {
        "iso": iso,
        "forward_from_base": build_kwargs.get("forward_from_base", False),
    }
    block = RH.META_RECORD_SPEC.build(
        config,
        ctx,
        args_values={
            "capacity_clearing_posture": posture,
            "capacity_market_clearing_forced": bool(force),
        },
    )
    return block, config, ctx


#: One leg per structurally distinct posture the harness can produce.
LEGS = {
    "plain_hindcast_ercot": dict(
        iso="ERCOT", start_year=2021, end_year=2025, variant="realized"
    ),
    "crossover_pjm": dict(
        iso="PJM",
        start_year=2023,
        end_year=2027,
        variant="realized",
        vintage=2023,
        crossover=True,
    ),
    "forced_curve_miso": dict(
        iso="MISO",
        start_year=2021,
        end_year=2025,
        variant="realized",
        capacity_market_clearing=True,
    ),
    "fixed_net_cone_caiso": dict(
        iso="CAISO",
        start_year=2021,
        end_year=2025,
        variant="realized",
        fixed_net_cone=True,
    ),
    "full_forward_ercot": dict(
        iso="ERCOT",
        start_year=2023,
        end_year=2025,
        variant="realized",
        vintage=2023,
        forward_from_base=True,
        arm="realized",
    ),
    "explicit_control_arms_nyiso": dict(
        iso="NYISO",
        start_year=2021,
        end_year=2025,
        variant="realized",
        retirement_rule="legacy",
        entry_lookahead_reprice=False,
        correlated_forced_outage=False,
        entry_rate_limits=False,
        limited_foresight_dispatch=True,
        entry_screen_diagnostics=True,
        energy_only_floor=True,
    ),
}


class TestSolvedSourced(unittest.TestCase):
    """Every audited record's config-describing block matches its solve."""

    def test_hindcast_meta_matches_solved_config(self):
        for name, kwargs in LEGS.items():
            with self.subTest(leg=name):
                block, config, ctx = _hindcast_meta(**kwargs)
                self.assertEqual(RH.META_RECORD_SPEC.check(block, config, ctx), [])

    def test_hindcast_posture_label_agrees_with_solved_config(self):
        # The one genuinely args-sourced config-ish key is checked for
        # CONSISTENCY instead of equality (it records which arm was chosen).
        for name, kwargs in LEGS.items():
            with self.subTest(leg=name):
                iso = kwargs["iso"]
                config = RH.build_config(**kwargs)
                _, posture = RH.resolve_capacity_clearing_posture(
                    iso,
                    kwargs.get("capacity_market_clearing", False),
                    kwargs.get("fixed_net_cone", False),
                )
                RH._assert_posture_consistent(posture, config, iso)

    def test_posture_label_contradicting_the_solve_is_refused(self):
        config = RH.build_config(
            iso="MISO", start_year=2021, end_year=2025, variant="realized"
        )  # shipped posture
        with self.assertRaises(SystemExit):
            RH._assert_posture_consistent("fixed_net_cone", config, "MISO")

    def test_full_horizon_summary_matches_solved_config(self):
        for iso in ("ERCOT", "PJM", "CAISO", "NYISO"):
            with self.subTest(iso=iso):
                config = ScenarioConfig(
                    iso=iso, mode="forecast", start_year=2026, end_year=2030
                )
                block = RF.SUMMARY_RECORD_SPEC.build(config, {"iso": iso})
                self.assertEqual(
                    RF.SUMMARY_RECORD_SPEC.check(block, config, {"iso": iso}), []
                )

    def test_every_declared_config_source_names_a_real_field(self):
        # A typo'd FromConfig key would silently record nothing checkable, so
        # every declared config source must resolve to an actual field.
        fields = config_field_names()
        for path, spec in AUDITED_SPECS.items():
            for key, src in spec.sources.items():
                if isinstance(src, FromConfig):
                    with self.subTest(spec=path, key=key):
                        self.assertIn(src.field or key, fields)

    def test_aliased_keys_state_why(self):
        # A key whose recorded name differs from its config field is the one
        # shape the "key names a field" rule cannot police on its own, so the
        # alias must say what it aliases and why.
        for path, spec in AUDITED_SPECS.items():
            for key, src in spec.sources.items():
                if isinstance(src, FromConfig) and src.field and src.field != key:
                    with self.subTest(spec=path, key=key):
                        self.assertTrue(str(src.why).strip(), key)
        for path, spec in AUDITED_SPECS.items():
            for key, src in spec.sources.items():
                if isinstance(src, Derived):
                    with self.subTest(spec=path, key=key):
                        self.assertTrue(str(src.why).strip(), key)

    def test_every_args_sourced_exemption_carries_a_reason(self):
        for path, spec in AUDITED_SPECS.items():
            for key, src in spec.sources.items():
                if isinstance(src, FromArgs):
                    with self.subTest(spec=path, key=key):
                        self.assertTrue(str(src.why).strip(), key)

    def test_fromargs_cannot_be_declared_without_a_reason(self):
        with self.assertRaises(ValueError):
            FromArgs("")


class TestHistoricalDefect(unittest.TestCase):
    """The check FAILS against the historical sourcing and PASSES against the fix.

    The construction the prompt asks for: a leg where a tri-state flag is
    OMITTED and the shipped default is ``True``. That is the FFR-3D defect
    exactly — ``bool(args.entry_lookahead_reprice)`` is ``bool(None)`` is
    ``False`` — and the FFR-3L defect for the string-valued ``retirement_rule``,
    where the omitted flag recorded ``null``.
    """

    LEG = dict(iso="ERCOT", start_year=2021, end_year=2025, variant="realized")

    def _omitted_flags_config(self):
        config = RH.build_config(**self.LEG)
        # Precondition: the shipped defaults these legs inherit really are the
        # "on"/non-null values, otherwise the reproduction proves nothing.
        self.assertIs(config.entry_lookahead_reprice, True)
        self.assertIs(config.correlated_forced_outage, True)
        self.assertEqual(config.retirement_rule, "pipeline")
        self.assertIs(config.entry_rate_limits, True)
        return config

    def test_old_args_sourcing_is_caught(self):
        config = self._omitted_flags_config()
        ctx = {"iso": "ERCOT", "forward_from_base": False}
        # The pre-fix record, reconstructed: every one of these was written as
        # `bool(args.<flag>)` / `args.retirement_rule` with the flag omitted.
        omitted = None
        legacy_record = {
            "entry_lookahead_reprice": bool(omitted),
            "correlated_forced_outage": bool(omitted),
            "retirement_rule": omitted,
            "entry_rate_limits": bool(omitted),
        }
        violations = RH.META_RECORD_SPEC.check(legacy_record, config, ctx)
        caught = {v.split(":")[0] for v in violations}
        self.assertEqual(caught, set(legacy_record))
        with self.assertRaises(SystemExit):
            RH.META_RECORD_SPEC.assert_sourced(legacy_record, config, ctx)

    def test_shipped_sourcing_passes(self):
        block, config, ctx = _hindcast_meta(**self.LEG)
        self.assertEqual(RH.META_RECORD_SPEC.check(block, config, ctx), [])
        # And it records what the solve ran, not what the CLI omitted.
        self.assertEqual(block["retirement_rule"], "pipeline")
        self.assertTrue(block["entry_lookahead_reprice"])
        self.assertTrue(block["correlated_forced_outage"])
        self.assertTrue(block["entry_rate_limits"])

    def test_ffr2e_flag_sourced_clearing_gate_is_caught(self):
        # FFR-2E in the same frame: PJM ships curve-ON, so the harness's
        # shipped posture resolves the gate True while the raw force flag is
        # False. A flag-sourced record says curve-OFF; _curve_on reads it.
        config = RH.build_config(
            iso="PJM", start_year=2021, end_year=2025, variant="realized"
        )
        ctx = {"iso": "PJM", "forward_from_base": False}
        self.assertTrue(
            RH.META_RECORD_SPEC.check({"capacity_market_clearing": False}, config, ctx)
        )
        self.assertEqual(
            RH.META_RECORD_SPEC.check({"capacity_market_clearing": True}, config, ctx),
            [],
        )

    def test_instance_five_a_new_config_field_recorded_from_args(self):
        # The generalization: an UNDECLARED key naming a ScenarioConfig field
        # is a violation whatever its value happens to be, so the next lane's
        # new flag cannot enter a record without a deliberate declaration.
        config = RH.build_config(**self.LEG)
        ctx = {"iso": "ERCOT", "forward_from_base": False}
        field = "reserve_margin_build_enabled"
        self.assertIn(field, config_field_names())
        self.assertNotIn(field, RH.META_RECORD_SPEC.sources)
        violations = RH.META_RECORD_SPEC.check(
            {field: getattr(config, field)}, config, ctx
        )
        self.assertEqual(len(violations), 1, violations)
        self.assertIn("undeclared", violations[0])


class TestPersistedConfigDumps(unittest.TestCase):
    """A spec checks a persisted config dump as readily as a live object.

    Registrars and audits see the solved config only as its ``run_config.json``
    ``scenario_config`` block (or ``config.yaml``); the contract has to hold
    there too, or committed artifacts stay unverifiable.
    """

    def test_spec_checks_a_dumped_config(self):
        import dataclasses

        config = ScenarioConfig(
            iso="PJM", mode="forecast", start_year=2026, end_year=2030
        )
        dump = dataclasses.asdict(config)
        block = RB.SIDECAR_RECORD_SPEC.build(dump, {"iso": "PJM"})
        self.assertEqual(RB.SIDECAR_RECORD_SPEC.check(block, dump, {"iso": "PJM"}), [])
        self.assertEqual(block["mode"], "forecast")
        self.assertTrue(block["capacity_market_clearing"])  # PJM ships curve-ON

    def test_literal_mirrored_default_is_caught(self):
        # register_forecast_baseline recorded `correlated_forced_outage: True`
        # and `datacenter_load_path: "mid"` as LITERALS mirroring the shipped
        # forecast defaults. A control-arm leg makes that record false.
        import dataclasses

        config = ScenarioConfig(
            iso="PJM",
            mode="forecast",
            start_year=2026,
            end_year=2030,
            correlated_forced_outage=False,
            datacenter_load_path="off",
        )
        dump = dataclasses.asdict(config)
        mirrored = {"correlated_forced_outage": True, "datacenter_load_path": "mid"}
        violations = RB.SIDECAR_RECORD_SPEC.check(mirrored, dump, {"iso": "PJM"})
        self.assertEqual(len(violations), 2, violations)


class TestExtraBlockSeams(unittest.TestCase):
    """The two "merge a dict into someone else's record" seams stay checked.

    ``extra_summary`` (a leg driver adding to a full-horizon summary) and
    ``extra_meta`` (a hand-typed ``--extra-meta`` JSON blob on a registration
    command line) are the widest holes in the contract: both accept arbitrary
    keys. Neither is exempted — the first requires the caller to DECLARE its
    keys, the second auto-declares them as ``FromConfig`` so a hand-typed claim
    passes only when the solve agrees with it.
    """

    def _ces_config(self, **kw):
        return ScenarioConfig(
            iso="ERCOT", mode="forecast", start_year=2026, end_year=2030, **kw
        )

    def test_ces_leg_block_is_declared_and_verified(self):
        import scripts.run_ces_leg as CES

        config = self._ces_config(federal_ces_enabled=True)
        summary = {
            **RF.SUMMARY_RECORD_SPEC.build(config, {"iso": "ERCOT"}),
            **CES._leg_meta("CES-20", config, "poc"),
        }
        merged = RF.SUMMARY_RECORD_SPEC.merged(CES.CES_LEG_SPEC)
        self.assertEqual(merged.check(summary, config, {"iso": "ERCOT"}), [])
        # Undeclared, the same two config-named keys are violations — which is
        # why solve_and_summarize takes extra_spec rather than trusting the merge.
        self.assertEqual(
            len(RF.SUMMARY_RECORD_SPEC.check(summary, config, {"iso": "ERCOT"})), 2
        )

    def test_merged_refuses_two_declarations_of_one_key(self):
        a = RecordSpec({"mode": FromConfig()}, name="a")
        b = RecordSpec({"mode": FromArgs("because")}, name="b")
        with self.assertRaises(ValueError):
            a.merged(b)

    def _sidecar_fixture(self, tmp: Path, config: ScenarioConfig) -> Path:
        import dataclasses
        import json

        (tmp / "run_config.json").write_text(
            json.dumps({"scenario_config": dataclasses.asdict(config)}, default=str)
        )
        summary_path = tmp / "full_horizon_summary.json"
        summary_path.write_text(
            json.dumps(
                {
                    "iso": config.iso,
                    "start_year": config.start_year,
                    "end_year": config.end_year,
                    "cache_key": "k",
                    "run_dir": str(tmp),
                    "solved_years": [config.start_year],
                    "n_solved_years": 1,
                    "trajectory": [],
                    "invariants": [],
                }
            )
        )
        return summary_path

    def test_truthful_campaign_extra_meta_is_accepted(self):
        import tempfile

        config = self._ces_config(federal_ces_enabled=True)
        with tempfile.TemporaryDirectory() as tmp:
            path = self._sidecar_fixture(Path(tmp), config)
            sidecar = RB.build_sidecar(
                path,
                "ces-poc-bau",
                kind="ces-poc",
                extra_meta={
                    "case": "BAU",
                    "federal_ces_crediting": config.federal_ces_crediting,
                },
            )
        self.assertEqual(sidecar["meta"]["case"], "BAU")
        self.assertEqual(
            sidecar["meta"]["federal_ces_crediting"], config.federal_ces_crediting
        )
        # And the literals FFR-3R replaced now come off the run's own config.
        self.assertEqual(sidecar["meta"]["mode"], "forecast")
        self.assertIs(sidecar["meta"]["correlated_forced_outage"], True)

    def test_extra_meta_contradicting_the_solve_is_refused(self):
        import tempfile

        config = self._ces_config()
        with tempfile.TemporaryDirectory() as tmp:
            path = self._sidecar_fixture(Path(tmp), config)
            with self.assertRaises(SystemExit):
                RB.build_sidecar(
                    path, "x", extra_meta={"federal_ces_crediting": "cesa_ci"}
                )
            with self.assertRaises(SystemExit):
                RB.build_sidecar(
                    path, "x", extra_meta={"correlated_forced_outage": False}
                )

    def test_missing_resolved_config_records_null_not_a_default(self):
        # Rubric §4: an unrecoverable value is recorded as unknown, never
        # substituted from today's shipped default.
        import json
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "full_horizon_summary.json"
            path.write_text(
                json.dumps(
                    {
                        "iso": "ERCOT",
                        "start_year": 2026,
                        "end_year": 2030,
                        "run_dir": None,
                        "trajectory": [],
                        "invariants": [],
                    }
                )
            )
            meta = RB.build_sidecar(path, "orphan")["meta"]
        self.assertIsNone(meta["correlated_forced_outage"])
        self.assertIsNone(meta["datacenter_load_path"])
        self.assertIsNone(meta["mode"])
        self.assertEqual(meta["iso"], "ERCOT")


class TestStaticSourcingLint(unittest.TestCase):
    """No record literal in an audited writer sources a config-named key from ``args``.

    The runtime check catches a divergence when a run is made; this catches the
    authoring of one, in review, with no solve. It is deliberately narrow — it
    flags only ``args.<x>`` inside the value expression of a dict key that
    names a ``ScenarioConfig`` field — because that is precisely the shape all
    four historical instances had.
    """

    def _violations(self, path: Path) -> list[str]:
        fields = config_field_names()
        allowlisted = {
            key
            for spec in AUDITED_SPECS.values()
            for key, src in spec.sources.items()
            if isinstance(src, FromArgs)
        }
        tree = ast.parse(path.read_text())
        found: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            for key, value in zip(node.keys, node.values):
                if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
                    continue
                name = key.value
                if name not in fields or name in allowlisted:
                    continue
                for sub in ast.walk(value):
                    if (
                        isinstance(sub, ast.Attribute)
                        and isinstance(sub.value, ast.Name)
                        and sub.value.id == "args"
                    ):
                        found.append(
                            f"{path.name}:{key.lineno}: {name!r} sourced from "
                            f"args.{sub.attr}"
                        )
        return found

    def test_no_args_sourced_config_named_record_key(self):
        for rel in LINTED_FILES:
            with self.subTest(file=rel):
                self.assertEqual(self._violations(REPO_ROOT / rel), [])

    def test_lint_catches_a_planted_instance_five(self):
        # Negative control: the lint is only worth its green if it goes red on
        # the shape it claims to catch. This is instance one through four,
        # verbatim.
        import tempfile

        planted = (
            "meta = {\n"
            '    "kind": kind,\n'
            '    "retirement_rule": args.retirement_rule,\n'
            '    "correlated_forced_outage": bool(args.correlated_forced_outage),\n'
            "}\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "planted.py"
            path.write_text(planted)
            found = self._violations(path)
        self.assertEqual(len(found), 2, found)
        self.assertTrue(any("retirement_rule" in f for f in found), found)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
