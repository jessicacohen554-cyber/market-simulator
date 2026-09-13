"""The recorded-config gas-anchor MIRROR must not drift from the solve.

nyiso-231. ``run_config.json`` records the config the LP solved with, and for the
two gas-offer-margin **vintage** gates that value is not a lookup — it is
*resolved* from the run's own delivered-gas series. That makes it the one field
in the record computed twice: once inside ``run_calibration.run_year`` (which the
LP then prices against) and once inside ``run_calibration_full._recorded_config``
(which is written to the bundle).

**The two halves disagreed, and it cost a screen.** nyiso-230's 2022 NYISO arm
recorded ``Capital_Hudson 7.0563 $/MMBtu`` while the LP priced against
``8.4431`` — a uniform ``-1.3868`` in every zone — because the recorded mirror
was inlined ~144 lines ABOVE the block that puts ``gas_hub_basis_overlay`` on the
recorded config, while ``run_year`` sets the overlay *before* it resolves. The
bundle was internally inconsistent: ``gas_hub_basis_overlay: true`` beside
anchors that only reproduce at ``overlay=False``. Two of that screen's four
pre-registered gates failed on that single line, and NEITHER measured the
mechanism (``docs/RESULT-nyiso231-the-mirror-and-the-2022-rescreen-2026-09-13.md``).

The repair makes the resolution **structural rather than positional**: one shared
helper, ``run_calibration_full.mirror_solve_year_gas_anchors``, fused to
``_recorded_config``'s ``return``. These tests pin the three properties that keep
it that way — it is fused to the return, it is self-consistent on its own output,
and both runners gate it on the config FIELD as well as the solve kwarg.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from market_sim.config.constants import HOURS_PER_YEAR  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fuel.zonal_anchor import (  # noqa: E402
    zonal_gas_anchors_for_year,
)

FULL = ROOT / "scripts" / "run_calibration_full.py"
YEAR = ROOT / "scripts" / "run_calibration.py"

#: nyiso-230's 2022 arm, the bundle the defect was measured on. Its recorded
#: config is the only committed artifact carrying a vintage flag armed.
ARM = ROOT / "results" / "calibration" / "nyiso230_arm_y2022" / "run_config.json"

#: The anchors the repaired mirror must return for that config — which are the
#: PRECOMMIT's prediction and the values the LP actually priced against. The
#: defect recorded each of these 1.3868 $/MMBtu lower.
SOLVED_2022_ANCHORS = {
    "Upstate_West": 5.3731,
    "Capital_Hudson": 8.4431,
    "Lower_Hudson": 8.4431,
    "NYC": 6.6631,
    "Long_Island": 8.4431,
}
MIRROR_DEFECT_OFFSET = -1.3868


def _full_module():
    spec = importlib.util.spec_from_file_location("rcf_mirror_test", FULL)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["rcf_mirror_test"] = mod
    spec.loader.exec_module(mod)
    return mod


def _arm_config() -> ScenarioConfig:
    if not ARM.exists():
        pytest.skip("nyiso230_arm_y2022 bundle not on disk")
    sc = json.loads(ARM.read_text())
    sc = sc.get("scenario_config", sc)
    names = {f.name for f in dataclasses.fields(ScenarioConfig)}
    return ScenarioConfig(**{k: v for k, v in sc.items() if k in names})


# --------------------------------------------------------------------------
# 1. The ordering is structural: the mirror is fused to the return.
# --------------------------------------------------------------------------


def test_the_mirror_is_called_exactly_once_and_only_in_a_return():
    """A mid-function call is the defect. Fused to ``return``, it cannot be."""
    tree = ast.parse(FULL.read_text())
    in_return, total = 0, 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == (
            "mirror_solve_year_gas_anchors"
        ):
            total += 1
    for node in ast.walk(tree):
        if isinstance(node, ast.Return) and node.value is not None:
            for sub in ast.walk(node.value):
                if isinstance(sub, ast.Call) and getattr(sub.func, "id", None) == (
                    "mirror_solve_year_gas_anchors"
                ):
                    in_return += 1
    assert total == 1, f"expected one mirror call site, found {total}"
    assert in_return == 1, (
        "the mirror is not fused to a `return` — a config-mutating block can "
        "then land in front of it and record an anchor the LP never priced "
        "(rule 24 [R-REGISTRY]; the nyiso-230 defect)"
    )


def test_no_inline_mirror_survives_in_recorded_config():
    """The two removed inline blocks must not come back as a 'restore'."""
    src = FULL.read_text()
    for dead in ("_f4_gs", "_f5_zonal"):
        assert dead not in src, (
            f"{dead} is the alias of an inline mirror that resolved the anchor "
            "mid-function, before the gas posture was complete. Deleted, not "
            "zeroed (rule 26 [R-DELETE]) — do not restore it."
        )


def test_the_mirror_return_is_the_last_statement_of_recorded_config():
    """This is what makes the ordering structural rather than positional.

    ``_recorded_config`` must have exactly ONE ``return``, it must be the LAST
    statement of the function body, and it must be the mirror call. Given that,
    a future ``if flag: recorded_cfg = ...`` block can only land ABOVE it — so
    the new field is on the config before the anchors are resolved, and the
    nyiso-230 seam cannot re-open by appending. A second return, or a return
    that is not last, would let one path skip the resolution.
    """
    tree = ast.parse(FULL.read_text())
    fn = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_recorded_config"
    )
    returns = [n for n in ast.walk(fn) if isinstance(n, ast.Return)]
    assert len(returns) == 1, (
        f"_recorded_config has {len(returns)} returns; a path that skips the "
        "mirror records an anchor the LP never priced (rule 24 [R-REGISTRY])"
    )
    last = fn.body[-1]
    assert isinstance(last, ast.Return), (
        "the mirror return is not the last statement of _recorded_config"
    )
    assert isinstance(last.value, ast.Call)
    assert getattr(last.value.func, "id", None) == "mirror_solve_year_gas_anchors"


# --------------------------------------------------------------------------
# 2. The resolution itself: correct, self-consistent, and refusing to stack.
# --------------------------------------------------------------------------


def test_the_mirror_reproduces_the_anchors_the_lp_priced_against():
    """The repair's whole point, measured on the bundle that exposed it."""
    mod = _full_module()
    cfg = _arm_config()
    out = mod.mirror_solve_year_gas_anchors(cfg, 2022, HOURS_PER_YEAR)
    got = out.gas_offer_margin_anchor_by_zone
    for zone, want in SOLVED_2022_ANCHORS.items():
        assert abs(got[zone] - want) < 5e-4, f"{zone}: {got[zone]} != {want}"
        recorded = cfg.gas_offer_margin_anchor_by_zone[zone]
        assert abs((recorded - want) - MIRROR_DEFECT_OFFSET) < 5e-4, (
            "the bundle's recorded anchor is no longer the pre-overlay value — "
            "this test's premise has changed, re-read the RESULT doc"
        )


def test_the_mirror_is_self_consistent_on_its_own_output():
    """Re-resolving on the returned config must be a no-op.

    This is the invariant the defect violated: the recorded config claimed
    ``gas_hub_basis_overlay: true`` beside anchors that only reproduce at
    ``overlay=False``. Idempotence is the cheapest statement of "the anchors
    belong to the config they are recorded on".
    """
    mod = _full_module()
    once = mod.mirror_solve_year_gas_anchors(_arm_config(), 2022, HOURS_PER_YEAR)
    again = zonal_gas_anchors_for_year(once, 2022, HOURS_PER_YEAR)
    for zone, v in once.gas_offer_margin_anchor_by_zone.items():
        assert abs(again[zone] - v) < 1e-9, f"{zone} drifts on re-resolution"


def test_the_two_vintage_gates_are_never_stacked():
    """Rule 19 [R-ONE-MECH]: alternatives, and ``run_year`` raises on both."""
    mod = _full_module()
    cfg = _arm_config().with_overrides(gas_offer_margin_anchor_vintage=True)
    with pytest.raises(SystemExit):
        mod.mirror_solve_year_gas_anchors(cfg, 2022, HOURS_PER_YEAR)


def test_the_off_path_returns_the_config_untouched():
    """Every run with neither gate armed must be byte-identical."""
    mod = _full_module()
    cfg = ScenarioConfig(iso="NYISO", mode="backcast", hours=HOURS_PER_YEAR)
    assert mod.mirror_solve_year_gas_anchors(cfg, 2023, HOURS_PER_YEAR) is cfg


# --------------------------------------------------------------------------
# 3. Kwarg-or-field parity, on BOTH gates and in BOTH runners.
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field",
    ["gas_offer_margin_anchor_vintage", "gas_offer_margin_zonal_anchor_vintage"],
)
def test_run_year_gates_on_the_config_field_as_well_as_the_kwarg(field):
    """``replay_keeper.py --set`` writes the FIELD, never the solve kwarg.

    A kwarg-only gate lets a ``--set`` A/B silently solve the CONTROL while the
    mirror — which gates on kwarg-or-field — records an armed config. The ISO
    level sibling was kwarg-only until nyiso-231; that asymmetry was itself a
    latent recording defect, so both gates are fixed together.
    """
    src = " ".join(YEAR.read_text().split())
    assert f'if {field} or getattr( config, "{field}", False )' in src, (
        f"run_year gates {field} on the kwarg alone"
    )


@pytest.mark.parametrize(
    "field",
    ["gas_offer_margin_anchor_vintage", "gas_offer_margin_zonal_anchor_vintage"],
)
def test_the_mirror_gates_on_the_config_field_as_well_as_the_kwarg(field):
    mod = _full_module()
    cfg = _arm_config().with_overrides(
        gas_offer_margin_zonal_anchor_vintage=False,
        gas_offer_margin_anchor_vintage=False,
    )
    armed = cfg.with_overrides(**{field: True})
    out = mod.mirror_solve_year_gas_anchors(armed, 2022, HOURS_PER_YEAR)
    assert getattr(out, field) is True
    if field.startswith("gas_offer_margin_zonal"):
        assert out.gas_offer_margin_anchor_by_zone != (
            cfg.gas_offer_margin_anchor_by_zone
        )
    else:
        assert out.gas_offer_margin_anchor != cfg.gas_offer_margin_anchor


def test_run_year_stamps_the_iso_level_field_on_the_solved_config():
    """Otherwise a kwarg-armed solve records ``vintage: false`` beside a moved
    anchor, and the bundle cannot be told apart from an unarmed one."""
    src = " ".join(YEAR.read_text().split())
    assert (
        "gas_offer_margin_anchor_vintage=True, gas_offer_margin_anchor=_f4_anchor"
        in src
    )
