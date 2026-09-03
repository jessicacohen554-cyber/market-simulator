"""Tests for CAISO's published NQC class-average VRE accreditation (FFR-3P).

Trivial-first (CLAUDE.md testing pattern): the gate's off-path byte-identity,
then the resolver ladder, then the reconciliation of every encoded literal
against the committed CPUC/CAISO source workbook (rule 13 — a published input,
never a fit target), then the rule-25 scope check that nothing leaked into
another ISO, then the ledger consumer.

The reconciliation deliberately re-derives from the RAW workbook rather than
from the derive script's own CSV, so a stale or hand-edited CSV cannot certify
the registry.
"""

import unittest
from pathlib import Path

from market_sim.config.constants import (
    RENEWABLE_CAPACITY_CREDIT,
    RENEWABLE_NQC_CURVES_BY_ISO,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator
from market_sim.model.capacity import (
    accredited_firm_capacity_mw,
    resolve_renewable_capacity_credit,
)
from tests.helpers.builders import no_hydro_accreditation

_WORKBOOK = Path(
    "data/raw/capacity-market/nqc/caiso/net-qualifying-capacity-report-cy2026.xlsx"
)
_YEAR = 2026
# The registry rounds the derived blend to 4 dp; nothing here may drift further.
_TOL = 5e-5


def _solar_gen(mw: float) -> Generator:
    return Generator(
        unit_id="S0",
        name="S0",
        zone="Z0",
        fuel_type="solar",
        pmax_mw=mw,
        heat_rate=0.0,
        vom=0.0,
        eford=0.0,
    )


class TestCaisoNqcGateOffPath(unittest.TestCase):
    """Unarmed, the registry is unreachable and nothing moves."""

    def test_field_defaults_off(self) -> None:
        self.assertFalse(ScenarioConfig().caiso_nqc_accreditation)

    def test_unarmed_caiso_keeps_the_generic_fallback(self) -> None:
        for fuel in ("solar", "wind"):
            self.assertAlmostEqual(
                resolve_renewable_capacity_credit(
                    fuel, "CAISO", installed_mw=22_000.0, peak_demand_mw=50_000.0
                ),
                RENEWABLE_CAPACITY_CREDIT[fuel],
            )

    def test_unarmed_default_cache_key_is_unmoved(self) -> None:
        # The field is registered in _CACHE_KEY_OPTIONAL_FIELDS at False, so the
        # pinned default key must not have moved when it was added.
        self.assertEqual(ScenarioConfig().cache_key(), "4c6b03ae098b6e3e")

    def test_armed_run_keys_distinctly(self) -> None:
        self.assertNotEqual(
            ScenarioConfig().cache_key(),
            ScenarioConfig(caiso_nqc_accreditation=True).cache_key(),
        )


class TestCaisoNqcResolution(unittest.TestCase):
    """Armed, rung 0 of the one ladder returns CAISO's published factor."""

    def test_armed_caiso_uses_the_published_class_factors(self) -> None:
        self.assertAlmostEqual(
            resolve_renewable_capacity_credit(
                "solar", "CAISO", curves_enabled=True, nqc_curves_enabled=True
            ),
            0.2096,
        )
        self.assertAlmostEqual(
            resolve_renewable_capacity_credit(
                "wind", "CAISO", curves_enabled=True, nqc_curves_enabled=True
            ),
            0.2202,
        )

    def test_published_factors_beat_the_generic_fallback_in_both_classes(self) -> None:
        # The direction FFR-3H left unresolved: CAISO's own accreditation is
        # HIGHER than the generic fallback in both classes, so the fallback
        # understates the ledger.
        for fuel in ("solar", "wind"):
            self.assertGreater(
                RENEWABLE_NQC_CURVES_BY_ISO["CAISO"][fuel].points[0][1],
                RENEWABLE_CAPACITY_CREDIT[fuel],
            )

    def test_curves_carry_no_fabricated_penetration_axis(self) -> None:
        # CPUC publishes an exceedance statistic, not a marginal-ELCC curve, so
        # the encoded curve must be a single-point constant (the NYISO shape).
        for curve in RENEWABLE_NQC_CURVES_BY_ISO["CAISO"].values():
            self.assertIsNone(curve.penetration_basis)
            self.assertEqual(len(curve.points), 1)

    def test_rule_25_scope_caiso_only(self) -> None:
        self.assertEqual(set(RENEWABLE_NQC_CURVES_BY_ISO), {"CAISO"})
        # Arming the gate cannot move any other ISO's credit.
        for iso in ("ERCOT", "PJM", "MISO", "NYISO", "NEISO"):
            for fuel in ("solar", "wind"):
                self.assertAlmostEqual(
                    resolve_renewable_capacity_credit(
                        fuel,
                        iso,
                        installed_mw=10_000.0,
                        peak_demand_mw=100_000.0,
                        curves_enabled=True,
                        nqc_curves_enabled=True,
                    ),
                    resolve_renewable_capacity_credit(
                        fuel,
                        iso,
                        installed_mw=10_000.0,
                        peak_demand_mw=100_000.0,
                        curves_enabled=True,
                    ),
                )


class TestCaisoNqcLedgerConsumer(unittest.TestCase):
    """The accredited-firm ledger moves by exactly nameplate x the credit."""

    def test_ledger_delta_is_the_published_credit_delta(self) -> None:
        fleet = [_solar_gen(10_000.0)]
        kwargs = dict(iso="CAISO", peak_demand_mw=50_000.0, elcc_curves_enabled=True)
        with no_hydro_accreditation():
            off = accredited_firm_capacity_mw(fleet, **kwargs)
            on = accredited_firm_capacity_mw(fleet, nqc_curves_enabled=True, **kwargs)
        self.assertAlmostEqual(on - off, 10_000.0 * (0.2096 - 0.18), places=4)


class TestCaisoNqcReconciliation(unittest.TestCase):
    """Every encoded literal re-derives from the committed source workbook."""

    def test_literals_match_the_published_workbook(self) -> None:
        if not _WORKBOOK.exists():  # pragma: no cover — raw intake absent
            self.skipTest(f"{_WORKBOOK} not present")
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "_derive_caiso_nqc",
            Path("scripts/data/derive_caiso_nqc_class_factors.py"),
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        table = module.derive(_WORKBOOK, _YEAR)
        for model_class, curve in RENEWABLE_NQC_CURVES_BY_ISO["CAISO"].items():
            sub = table[table["model_class"] == model_class].set_index("month")
            peak = sub.loc[list(module.PEAK_RISK_MONTHS), "class_average_factor"]
            self.assertAlmostEqual(
                curve.points[0][1],
                float(peak.min()),
                delta=_TOL,
                msg=(
                    f"{model_class}: registry {curve.points[0][1]} vs published "
                    f"peak-risk minimum {float(peak.min()):.6f} "
                    f"({peak.idxmin()}) — re-derive or fix the literal"
                ),
            )

    def test_source_string_names_the_committed_workbook(self) -> None:
        for curve in RENEWABLE_NQC_CURVES_BY_ISO["CAISO"].values():
            self.assertIn("net-qualifying-capacity-report-cy2026.xlsx", curve.source)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
