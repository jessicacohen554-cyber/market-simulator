"""capx D41 source-consistency: the CCS-retrofit fixed-cost legs vs their ATB basis.

Pins ``ScenarioConfig.fixed_om_gas_cc_ccs`` and
``ScenarioConfig.ccs_retrofit_capex_kw`` to the NREL ATB 2024 (2026$)
derivation they are cited to, so neither can silently drift back off its
source (CLAUDE.md rule 23 ``[R-ACCURATE]`` / rule 24 ``[R-REGISTRY]``). Reads
only the committed raw ATB extract and the committed cost-benchmark CSV, so it
runs in CI with no clean-build step and no solve.

**The defect these pin against** (``docs/handoffs/FINDING-capx-d30-45q-pace-
2026-09-02.md`` §5 rows 6-7, repaired by ``FINDING-capx-d41-ccs-fixedcost-
2026-09-02.md``):

* ``fixed_om_gas_cc_ccs`` = 25.0 sat BELOW its own host ``fixed_om_gas_cc`` =
  30.0 — a "host CC + capture island" figure cannot be less than the host. The
  G-32 ATB flip raised the host 12 -> 30 and left this field at its pre-flip
  value, so the retrofit screen's ``delta_fom`` was **-$5,000/MW-yr**: it PAID
  every retrofit a fixed-cost saving instead of charging the capture island's
  O&M.
* ``ccs_retrofit_capex_kw`` = 900.0 was ``needs-citation``, stated no
  dollar-year, and was 59 % of the capture-island increment the model's own
  new-build CCS carries — the "~$900/kW makes the capture island look nearly
  free" defect FF-1E repaired for new-build and left standing here.

The direction tests below are the ones that would have caught both at the G-32
commit, and they are deliberately stated as INEQUALITIES on physics ("an added
plant costs money", "a brownfield tie-in is not cheaper than the greenfield
increment") rather than as value pins, so they keep biting under a future ATB
edition that moves the numbers.
"""

import unittest

from market_sim.config.scenarios import ScenarioConfig
from scripts.data import derive_cost_benchmark_envelope as bench
from scripts.data import derive_entry_costs_from_atb as derive

# Cross-source rows carry their own dollar-year; each source's capture-island
# increment is taken MATCHED-CONFIGURATION (the CCS row against the same
# source's like-sized unabated CC), then deflated to the model's 2026$ basis.
_MATCHED_CC = {
    "sl2024_gas_cc_ccs": "sl2024_gas_cc_1x1",  # both 1x1x1 single-shaft
    "aeo2026_gas_cc_ccs": "aeo2026_gas_cc_ss",  # both single-shaft 627 MW
}


def _atb_increment(param: str) -> float:
    """ATB 2024 capture-island increment for ``param``, in 2026$."""
    derived = derive.derive_new_entry_costs()
    return derived["gas_cc_ccs"][param] - derived["gas_cc"][param]


def _benchmark_increments(param: str) -> dict[str, float]:
    """Matched-configuration capture-island increments per source, in 2026$."""
    rows = {r["source_id"]: r for r in bench.load_benchmarks()}
    out: dict[str, float] = {}
    for ccs_id, cc_id in _MATCHED_CC.items():
        ccs, cc = rows[ccs_id], rows[cc_id]
        # Both rows of a pair share a dollar-year, so one deflator serves both.
        factor = (1.0 + bench.INFLATION_RATE) ** (
            bench.REAL_DOLLAR_BASE_YEAR - ccs["dollar_year"]
        )
        out[ccs_id] = (float(ccs[param]) - float(cc[param])) * factor
    return out


class TestRetrofitFomBasis(unittest.TestCase):
    """``fixed_om_gas_cc_ccs`` = host FOM + the ATB capture-island increment."""

    def test_equals_host_plus_atb_island_increment(self) -> None:
        config = ScenarioConfig()
        expected = config.fixed_om_gas_cc + _atb_increment("fom_per_kw_yr")
        self.assertAlmostEqual(
            config.fixed_om_gas_cc_ccs,
            expected,
            places=6,
            msg=(
                "fixed_om_gas_cc_ccs drifted off its cited basis: it is "
                "fixed_om_gas_cc + (ATB 2024 gas_cc_ccs FOM - ATB 2024 gas_cc "
                "FOM), all in 2026$. Re-derive with "
                "scripts/data/derive_entry_costs_from_atb.py; a change to this "
                "value must cite the DATA change that moved it (rule 23), "
                "never a residual."
            ),
        )

    def test_island_increment_is_additive_not_ratio_scaled(self) -> None:
        # The capture island is separate plant with its own ABSOLUTE O&M, and it
        # is NEW plant at retrofit time, so it carries a full new-build fixed
        # cost rather than a paid-off host's going-forward discount. The
        # retrofit screen's delta_fom must therefore equal the ATB increment
        # exactly, independent of the host field's own rounding.
        config = ScenarioConfig()
        delta_fom = config.fixed_om_gas_cc_ccs - config.fixed_om_gas_cc
        self.assertAlmostEqual(delta_fom, _atb_increment("fom_per_kw_yr"), places=6)

    def test_host_plus_island_can_never_sit_below_the_host(self) -> None:
        # THE G-32 DEFECT, as a standing invariant. A "host CC + capture island"
        # going-forward fixed cost is the host's cost plus a strictly positive
        # amount; anything else makes the retrofit screen pay for retrofitting.
        config = ScenarioConfig()
        self.assertGreater(
            config.fixed_om_gas_cc_ccs,
            config.fixed_om_gas_cc,
            "fixed_om_gas_cc_ccs is 'host CC O&M + capture island O&M' and so "
            "must exceed fixed_om_gas_cc. Below it, the CCS retrofit screen's "
            "delta_fom is a SAVING and the retirement screen prices a "
            "retrofitted unit's going-forward bar below its unabated self.",
        )

    def test_every_published_basis_makes_the_island_an_added_cost(self) -> None:
        # ATB's FOM basis runs ~2.2x the EIA/S&L line for the same technology,
        # which is why host and island must be read off ONE basis. The sign,
        # though, is unanimous across all three published sources — so the
        # shipped -5.0 delta was outside every one of them.
        increments = _benchmark_increments("fom_per_kw_yr_mid")
        increments["atb2024"] = _atb_increment("fom_per_kw_yr")
        for source, value in increments.items():
            self.assertGreater(value, 0.0, f"{source} capture-island FOM increment")


class TestRetrofitCapexBasis(unittest.TestCase):
    """``ccs_retrofit_capex_kw`` = the ATB capture-island capex increment, 2026$."""

    def test_equals_atb_capture_island_increment(self) -> None:
        expected = _atb_increment("capex_per_kw")
        self.assertAlmostEqual(
            ScenarioConfig().ccs_retrofit_capex_kw,
            expected,
            places=6,
            msg=(
                "ccs_retrofit_capex_kw drifted off its cited basis: NREL ATB "
                "2024 Moderate NG CC 95 % CCS @2026 minus NG 2-on-1 CC "
                "(F-Frame) @2026, both 2026$ (derive_entry_costs_from_atb.py). "
                "The value carries a STATED dollar-year; any replacement must "
                "too."
            ),
        )

    def test_is_a_floor_not_a_ceiling(self) -> None:
        # A retrofit capture island costs MORE per kW than the greenfield
        # increment (congested brownfield site, steam and flue-gas tie-ins,
        # outage tie-in risk) — the inverse of the rationale the shipped 900.0
        # carried. Every published basis here is a GREENFIELD increment, so the
        # cited value is a floor and the screen stays biased TOWARD retrofitting.
        # A retrofit-specific TPC may only raise it.
        self.assertGreaterEqual(
            ScenarioConfig().ccs_retrofit_capex_kw, _atb_increment("capex_per_kw")
        )

    def test_atb_is_the_lowest_of_the_three_published_increments(self) -> None:
        # Why ATB is the floor: matched-configuration cross-check against the
        # committed benchmark rows the entry-cost envelope already reads.
        atb = _atb_increment("capex_per_kw")
        others = _benchmark_increments("capex_per_kw_mid")
        self.assertTrue(others, "benchmark CSV lost its matched CCS/CC pairs")
        for source, value in others.items():
            self.assertGreater(value, atb, f"{source} vs the ATB increment")

    def test_not_the_pre_repair_value(self) -> None:
        # The shipped 900.0 was 59 % of the increment the model's own new-build
        # CCS charges — the two-cost-basis arbitrage D30 §4 measured in the
        # NEISO golden (a 2031 new-build CC whose own CCS variant the entry
        # screen REJECTED at the 1521.4 increment, retrofitted in 2032 at a
        # learning-adjusted 621). Same base basis now, so the arbitrage closes.
        self.assertNotEqual(ScenarioConfig().ccs_retrofit_capex_kw, 900.0)


class TestRetrofitVomBasis(unittest.TestCase):
    """``ccs_retrofit_vom_adder`` = the ATB capture-island VOM increment, 2026$.

    capx D65-B Act B. The pin this class puts on the field is the thing that was
    MISSING before D65-B: the extract carried no ``Variable O&M`` for
    ``NaturalGas_FE`` at all, so the shipped 8.0 $/MWh could not have been read
    off the pinned basis and was registered ``needs-citation``. D64 STOP 6 made
    the widened extract the precondition for changing the value, precisely so
    the new value arrives with an ASSERTED derivation rather than a better
    story — a value with no asserted derivation is the defect capx D41 removed
    from the two fixed-cost legs above (rule 23 ``[R-ACCURATE]``).
    """

    def test_equals_atb_capture_island_vom_increment(self) -> None:
        self.assertAlmostEqual(
            ScenarioConfig().ccs_retrofit_vom_adder,
            derive.derive_ccs_retrofit_vom_adder(),
            places=6,
            msg=(
                "ccs_retrofit_vom_adder drifted off its cited basis: it is "
                "(ATB 2024 v4.0.0 Moderate NG 2-on-1 CC (F-Frame) 95% CCS "
                "Variable O&M @2026 - the same class's unabated NG 2-on-1 CC "
                "(F-Frame) Variable O&M @2026) x inflation_factor(), i.e. "
                "(4.8 - 2.1) x 1.090947 = 2.95 $/MWh in 2026$. Re-derive with "
                "scripts/data/derive_entry_costs_from_atb.py; a change to this "
                "value must cite the DATA change that moved it (rule 23), "
                "never a residual and never a solve result."
            ),
        )

    def test_is_read_off_the_same_basis_as_the_other_two_legs(self) -> None:
        # capx D41 §2.3's rule: host and island on ONE basis. All three legs of
        # the retrofit screen's cost side — capex, ΔFOM, VOM — are ATB 2024
        # increments of the SAME matched pair of ATB classes. This asserts the
        # pair itself, so a future edition that renamed a class fails loudly
        # here instead of silently re-identifying one leg against another's host.
        df = derive.load_atb()
        for param in ("CAPEX", "Fixed O&M", "Variable O&M"):
            for tech_key in ("gas_cc", "gas_cc_ccs"):
                technology, detail, base_year = derive.ENTRY_TECH_MAP[tech_key]
                self.assertEqual(technology, "NaturalGas_FE", tech_key)
                # Raises if the row is absent or not unique.
                derive._value(df, technology, detail, param, "Moderate", base_year)

    def test_not_the_pre_repair_value(self) -> None:
        # The shipped 8.0 was needs-citation and 2.7x this basis (3.6x NETL's).
        # Under ccs_retrofit_fixed_cost_co2_scaling that error would have been
        # multiplied by k on exactly the high-emitting hosts the seam exists to
        # re-price, which is why D65 §8.1 refused to arm the shape alone.
        self.assertNotEqual(ScenarioConfig().ccs_retrofit_vom_adder, 8.0)

    def test_the_island_vom_is_an_added_cost(self) -> None:
        # Direction, as an invariant rather than a value pin (the convention
        # this module's other classes use): a capture island ADDS variable O&M
        # — solvent makeup, reclaimer waste, capture-cooling water, island
        # maintenance materials. A non-positive increment would mean capturing
        # CO2 lowers the host's variable cost.
        self.assertGreater(derive.derive_ccs_retrofit_vom_adder(), 0.0)
        self.assertGreater(ScenarioConfig().ccs_retrofit_vom_adder, 0.0)

    def test_atb_host_heat_rate_is_the_seam_reference_host(self) -> None:
        # The widening also lands ATB's Heat Rate for NaturalGas_FE, which
        # closes a cross-check that was previously a coincidence on paper: the
        # hr_ref inside ccs_retrofit_captured_ref_t_per_mwh (D50 seam 1) is
        # min(HEAT_RATE_BINS["gas_cc"]), and ATB's own unabated NG 2-on-1 CC
        # (F-Frame) heat rate at the same base year is the same number. So the
        # host the capex increment is charged against and the host the captured
        # -CO2 reference flow is computed from are ONE host, from the bytes.
        from market_sim.config.constants import HEAT_RATE_BINS

        self.assertAlmostEqual(
            derive.derive_gas_cc_heat_rate(),
            min(HEAT_RATE_BINS["gas_cc"].values()),
            places=6,
            msg=(
                "ATB's unabated gas-CC heat rate no longer equals the model's "
                "own hr_ref (min(HEAT_RATE_BINS['gas_cc'])), which "
                "ccs.ccs_retrofit_captured_ref_t_per_mwh uses to size the "
                "reference captured-CO2 flow. The D50 capex seam and the D65 "
                "fixed-cost seam both assume these are the same host."
            ),
        )


if __name__ == "__main__":
    unittest.main()
