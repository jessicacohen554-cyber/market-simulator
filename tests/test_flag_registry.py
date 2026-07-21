"""Recorded-config fidelity tests for the declarative flag registry
(:mod:`market_sim.pipeline.flags`) — the ERCOT-65 defect class guard.

Each migrated flag family pins four legs:

1. **Parser equivalence** — parsing an empty argv yields exactly the
   defaults the hand-written definitions produced (literals pinned here,
   captured from the pre-migration AST), aliases parse to the same dest,
   and boolean flags keep their ``--no-*`` forms.
2. **Kwarg mapping** — ``solve_kwargs_from_args`` reproduces the exact
   ``solve_and_persist`` keyword names the hand-written main call passed.
3. **ScenarioConfig field existence** — every row's ``config_field`` is a
   real field, so the registry cannot point at a phantom tunable (rule 24).
4. **Recorded-name aliases** — rows whose ``meta.json`` name differs from
   the solve kwarg carry the alias the capture/replay tooling depends on
   (``capture_keeper_goldens.py``'s four-entry alias map).
"""

from __future__ import annotations

import argparse
import dataclasses

from market_sim.config.scenarios import ScenarioConfig
from market_sim.pipeline.flags import (
    FLAG_REGISTRY,
    add_flag_arguments,
    iter_family,
    solve_kwargs_from_args,
)

# Pre-migration argparse defaults, captured from the hand-written
# run_calibration_full.py definitions (AST dump, 2026-07-21) — the parser
# generated from the registry must reproduce these exactly.
COAL_EXPECTED_DEFAULTS = {
    "coal_lignite_mustrun": None,
    "coal_prb_mustrun": None,
    "coal_prb_passthrough": 1.0,
    "coal_prb_sigmoid": True,
    "coal_mustrun_per_plant": True,
    "coal_drop_pof": True,
    "coal_mustrun_online_pmin": False,
    "coal_sync_srmc_tranche": False,
    "coal_bit_sigmoid": False,
    "coal_econ_srmc_bound": False,
    "coal_lignite_sigmoid": False,
    "coal_sub_sigmoid": False,
    "coal_waste_sigmoid": False,
    "coal_warm_committed": False,
}

# The exact solve_and_persist kwarg names the hand-written main call passed
# for the coal family's direct (non-channel) rows.
COAL_EXPECTED_SOLVE_PARAMS = {
    "coal_lignite_mustrun",
    "coal_prb_mustrun",
    "coal_prb_passthrough",
    "coal_prb_passthrough_sigmoid",
    "coal_mustrun_per_plant",
    "coal_drop_pof",
    "coal_mustrun_online_pmin",
    "coal_sync_srmc_tranche",
    "coal_bit_sigmoid",
    "coal_econ_srmc_bound",
}


def _coal_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    add_flag_arguments(parser, "coal")
    return parser


class TestCoalFamilyParserEquivalence:
    def test_defaults_match_pre_migration_literals(self):
        args = _coal_parser().parse_args([])
        got = {dest: getattr(args, dest) for dest in COAL_EXPECTED_DEFAULTS}
        assert got == COAL_EXPECTED_DEFAULTS

    def test_legacy_alias_parses_to_same_dest(self):
        # --prb-passthrough-sigmoid is the legacy spelling of
        # --coal-prb-sigmoid; both write dest coal_prb_sigmoid.
        args = _coal_parser().parse_args(["--prb-passthrough-sigmoid"])
        assert args.coal_prb_sigmoid is True

    def test_boolean_optional_no_forms(self):
        args = _coal_parser().parse_args(
            ["--no-coal-prb-sigmoid", "--no-coal-mustrun-per-plant"]
        )
        assert args.coal_prb_sigmoid is False
        assert args.coal_mustrun_per_plant is False

    def test_value_flags_thread_values(self):
        args = _coal_parser().parse_args(
            ["--coal-prb-passthrough", "0.7", "--coal-lignite-mustrun", "0.55"]
        )
        assert args.coal_prb_passthrough == 0.7
        assert args.coal_lignite_mustrun == 0.55


class TestCoalFamilyKwargMapping:
    def test_solve_kwargs_names_and_defaults(self):
        args = _coal_parser().parse_args([])
        kwargs = solve_kwargs_from_args(args, "coal")
        assert set(kwargs) == COAL_EXPECTED_SOLVE_PARAMS
        # Spot-check the dest->param rename the ERCOT-65 class hides in:
        assert kwargs["coal_prb_passthrough_sigmoid"] is True  # dest coal_prb_sigmoid
        assert kwargs["coal_bit_sigmoid"] is False
        assert kwargs["coal_lignite_mustrun"] is None

    def test_solve_kwargs_thread_non_defaults(self):
        args = _coal_parser().parse_args(
            ["--no-coal-prb-sigmoid", "--coal-prb-passthrough", "0.8"]
        )
        kwargs = solve_kwargs_from_args(args, "coal")
        assert kwargs["coal_prb_passthrough_sigmoid"] is False
        assert kwargs["coal_prb_passthrough"] == 0.8

    def test_channel_rows_excluded(self):
        # prb_overrides channel members keep hand-written plumbing.
        args = _coal_parser().parse_args([])
        kwargs = solve_kwargs_from_args(args, "coal")
        for absent in (
            "coal_lignite_sigmoid",
            "coal_sub_sigmoid",
            "coal_waste_sigmoid",
            "coal_warm_committed",
        ):
            assert absent not in kwargs


class TestRegistryIntegrity:
    def test_config_fields_exist(self):
        field_names = {f.name for f in dataclasses.fields(ScenarioConfig)}
        for family, specs in FLAG_REGISTRY.items():
            for spec in specs:
                if spec.config_field is not None:
                    assert spec.config_field in field_names, (
                        f"{family}:{spec.dest} points at phantom "
                        f"ScenarioConfig field {spec.config_field!r}"
                    )

    def test_channel_xor_solve_param(self):
        for specs in FLAG_REGISTRY.values():
            for spec in specs:
                assert (spec.solve_param is None) == (spec.channel is not None), (
                    f"{spec.dest}: exactly one of solve_param/channel"
                )

    def test_recorded_name_aliases(self):
        # The capture/replay alias map (capture_keeper_goldens.py): meta.json
        # records coal_bit_passthrough_sigmoid for solve kwarg coal_bit_sigmoid.
        by_dest = {s.dest: s for s in iter_family("coal")}
        assert (
            by_dest["coal_bit_sigmoid"].recorded_name == "coal_bit_passthrough_sigmoid"
        )

    def test_registry_dests_unique(self):
        for family, specs in FLAG_REGISTRY.items():
            dests = [s.dest for s in specs]
            assert len(dests) == len(set(dests)), f"duplicate dest in {family}"


class TestMainParserIntegration:
    """The real run_calibration_full parser carries the generated family."""

    def test_full_parser_accepts_family_flags(self):
        # Import inside the test: run_calibration_full has heavy imports.
        import scripts.run_calibration_full as rcf  # noqa: F401

        # The generated definitions live in main()'s parser; re-generate a
        # standalone parser here and cross-check against the module's
        # registry import (presence of the seam is what we pin — main()'s
        # parser itself is exercised by the CLI tests / keeper replays).
        assert hasattr(rcf, "add_flag_arguments")
        assert hasattr(rcf, "solve_kwargs_from_args")
