"""Demand-affecting ScenarioConfig fields must survive the demand-threading seam.

``solve_and_persist`` loads demand ONCE per year and threads it into
``run_year`` (which skips its own ``load_demand`` when handed an array). That
optimization introduced a seam with a nasty property: the threading site builds
a PRISTINE ``backcast_config`` and reads the field off it, while the generic
``prb_overrides`` ScenarioConfig channel — the only route a
``replay_keeper.py --set`` probe has for a field that is not a
``solve_and_persist`` kwarg — is applied later, inside ``run_year``.

So a probe arming a demand-affecting field through ``--set`` gets:

* the LP solved on RAW demand (the threading site never saw the override), and
* ``run_config.json`` recording the ARMED value (``run_year``'s config did see
  it),

i.e. silently inert AND misreported — the worst combination, because the run
looks like evidence that the field does nothing.

caiso-80 fixed this for two CAISO demand flags with ``_caiso_demand_flag``.
nyiso-87 found ``td_loss_factor`` had the same defect, discovered only because
an arm-D probe came back byte-identical to its control (147.049 TWh demand
either way) while its ``scenario_config.td_loss_factor`` read 0.0251.

These tests pin the invariant for every demand-affecting field so the next one
added is caught at the seam rather than by a wasted 30-minute solve.
"""

import ast
import unittest
from pathlib import Path

from tests.helpers import REPO_ROOT

# ScenarioConfig fields that change the demand array `load_demand` returns.
# Every one must be read through the prb_overrides-aware resolution at the
# threading site, never straight off the pristine `cfg`.
_DEMAND_AFFECTING_FIELDS: tuple[str, ...] = (
    "td_loss_factor",
    "caiso_supply_consistent_demand",
    "caiso_demand_clock_realign",
    "nwpp_grid_carried_wind_served",
    "nwpp_demand_plant_basis",
    "demand_balance_screen",
)

_THREADING_SITE = "scripts/run_calibration_full.py"


def _load_demand_call(tree: ast.AST) -> ast.Call:
    """Return the threading site's ``load_demand(...)`` call with kwargs."""
    calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "load_demand"
        and any(kw.arg == "strict_demand_profile" for kw in n.keywords)
    ]
    assert len(calls) == 1, f"expected one threading-site load_demand, got {len(calls)}"
    return calls[0]


class TestThreadedDemandOverrides(unittest.TestCase):
    """The threading site must not read demand fields off the pristine cfg."""

    def setUp(self):
        self.src = (Path(REPO_ROOT) / _THREADING_SITE).read_text()
        self.tree = ast.parse(self.src)

    def test_no_demand_field_is_read_straight_off_cfg(self):
        """No BARE ``cfg.<field>`` read outside the documented fallback.

        A read is allowed only as the ``else`` branch of a prb_overrides
        lookup (the resolution itself has to bottom out somewhere). Anything
        else — and in particular the run_config recording — must use the
        resolved value, or the bundle disagrees with itself about what solved.
        """
        for field in _DEMAND_AFFECTING_FIELDS:
            offenders = []
            for n, line in enumerate(self.src.splitlines(), 1):
                code = line.split("#", 1)[0]
                if f"cfg.{field}" not in code:
                    continue
                if "else" in code:  # the documented resolution fallback
                    continue
                offenders.append(f"  line {n}: {line.strip()[:100]}")
            self.assertFalse(
                offenders,
                msg=(
                    f"\n{_THREADING_SITE} reads cfg.{field} directly at:\n"
                    + "\n".join(offenders)
                    + "\nThe pristine cfg does not carry prb_overrides, so a "
                    "--set probe of this field solves on raw demand while "
                    "run_config records it armed — silently inert AND "
                    "misreported (nyiso-87)."
                ),
            )

    def test_threading_site_consults_prb_overrides_for_every_demand_field(self):
        for field in _DEMAND_AFFECTING_FIELDS:
            self.assertIn(
                f'"{field}"',
                self.src,
                msg=(
                    f"{_THREADING_SITE} never mentions {field!r} as a "
                    "prb_overrides lookup key — it cannot be honoring a --set "
                    "override of it at the threading seam."
                ),
            )

    def test_td_loss_factor_reaches_load_demand_through_the_resolved_value(self):
        call = _load_demand_call(self.tree)
        kw = {k.arg: ast.unparse(k.value) for k in call.keywords}
        self.assertIn("td_loss_factor", kw)
        self.assertNotEqual(
            kw["td_loss_factor"],
            "cfg.td_loss_factor",
            msg="td_loss_factor must come from the prb_overrides-aware value",
        )
        self.assertEqual(kw["td_loss_factor"], "_td_loss")

    def test_every_demand_field_is_a_real_scenario_config_field(self):
        """Guards the list itself against drift (a renamed field silently passes)."""
        import dataclasses

        from market_sim.config.scenarios import ScenarioConfig

        names = {f.name for f in dataclasses.fields(ScenarioConfig)}
        for field in _DEMAND_AFFECTING_FIELDS:
            self.assertIn(
                field, names, msg=f"{field} is no longer a ScenarioConfig field"
            )


if __name__ == "__main__":
    unittest.main()
