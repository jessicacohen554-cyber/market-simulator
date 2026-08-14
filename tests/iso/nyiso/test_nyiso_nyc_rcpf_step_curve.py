"""Tests for ``nyiso_nyc_rcpf_step_curve`` — the NYC RCPF demand-curve SHAPE fix.

nyiso-115, a rule 14 ``[R-ACCURATE]`` correction to an already-correct LEVEL.
The model builds the published NYC locational reserve demand curves with
``critical_mw = 0``, which
:func:`market_sim.results.scarcity.nyiso_rcpf_product_shortfall_steps`
discretizes into an ``n_ramp=8`` LINEAR RAMP from $3.125 up to the $25/MW RCPF
over the whole requirement. NYISO's own posted zonal Day-Ahead ancillary-service
prices say the curve is a single STEP: the NYC-only locational adder (zone J
differenced against a zone sharing every nested region except NYC) shows one
atom exactly at $25.00 and essentially no mass at the ramp's interior rungs.
See ``scripts/probes/_nyiso115_nyc_rcpf_curve_screen.py``.

What these tests pin:

* the flag is byte-inert when off (every existing bundle is unaffected);
* on, it collapses the NYC pair's ramp to ONE band at the published RCPF whose
  width is the full requirement — so the curve saturates at the RCPF for ANY
  shortfall, which is the whole behavioural claim;
* the $25/MW LEVEL is untouched in both arms — this changes the depth at which
  the published penalty applies, never the penalty (rule 5 [R-NO-MAGIC]: no new
  number is introduced);
* the scope is exactly the two measured NYC families — East / SENY / LI keep
  their ramp, because the measurement does not identify their shape (their
  published RCPFs are never reached in the posted prices).
"""

from types import SimpleNamespace

import numpy as np

from market_sim.config.reserve_config import _nyiso_design
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays
from market_sim.model.reserves import NYISO_RCPF_STEP_CURVE_FAMILIES

T = 48
ZONES = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]

# The published NYC cells (reserves/spec.py NYISO_RCPF_LOCATIONAL["NYC"]).
NYC_PUBLISHED = {"nyc_10min_total": (500.0, 25.0), "nyc_30min_total": (1000.0, 25.0)}


def _fa():
    """One quick-start gas_ct per zone — enough to build a design."""
    n = len(ZONES)
    return FleetArrays(
        pmax=np.full(n, 1000.0),
        pmin=np.full(n, 250.0),
        heat_rate=np.full(n, 8.0),
        vom=np.zeros(n),
        emission_rate=np.zeros(n),
        nox_rate=np.zeros(n),
        so2_rate=np.zeros(n),
        zone_idx=np.arange(n, dtype=int),
        fuel_type_idx=np.array([FUEL_TYPE_MAP["gas_ct"]] * n, dtype=int),
        availability=np.ones((n, T)),
        unit_ids=[f"g{i}" for i in range(n)],
        efficiency_bin=np.zeros(n, dtype=int),
        plant_code=np.zeros(n, dtype=int),
    )


def _config(**overrides):
    base = dict(
        iso="NYISO",
        weather_year=2024,
        nyiso_rcpf_products=None,
        nyiso_rcpf_locational=None,
        nyiso_synchronised_reserve=False,
        nyiso_rcpf_enabled=False,
        nyiso_dynamic_reserve_requirements=False,
        nyiso_hydro_reserve_eligible=False,
        nyiso_scr_edrp_reserve_eligible=False,
        nyiso_li_locational_reserve=False,
        nyiso_incity_commitment_obligation=False,
        nyiso_east_reserve_families=False,
        nyiso_spin_reserve_online=False,
        nyiso_ordc_measured_step_span=False,
        nyiso_nyc_rcpf_step_curve=False,
        commitment_enabled=False,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _family(design, name):
    for fam in design.families:
        if fam.name == name:
            return fam
    return None


class TestScope:
    """The measurement's own boundary, pinned so it cannot silently widen."""

    def test_scope_is_exactly_the_two_measured_nyc_families(self):
        # NYC is the ONLY locational region whose published RCPF the measured
        # market ever reaches: East's $775 is never approached, LI shows no
        # material adder in any hour, and SENY caps at $40 rather than its
        # modelled $500 (the #1344 increment — a different mechanism, rule 19).
        assert NYISO_RCPF_STEP_CURVE_FAMILIES == ("nyc_10min_total", "nyc_30min_total")


class TestFlagOffIsInert:
    """Default off must leave every existing bundle byte-identical."""

    def test_flag_off_keeps_the_eight_step_ramp(self):
        design = _nyiso_design(_config(), _fa(), T, ZONES)
        for name, (req, pen) in NYC_PUBLISHED.items():
            fam = _family(design, name)
            assert fam is not None
            assert fam.ordc_penalties.shape == (8,)
            expected = np.array([pen * (k + 1) / 8 for k in range(8)])
            np.testing.assert_allclose(fam.ordc_penalties, expected)
            np.testing.assert_allclose(fam.ordc_step_widths, np.full(8, req / 8))

    def test_flag_off_and_on_agree_on_every_non_nyc_family(self):
        off = _nyiso_design(_config(), _fa(), T, ZONES)
        on = _nyiso_design(_config(nyiso_nyc_rcpf_step_curve=True), _fa(), T, ZONES)
        names = {f.name for f in off.families}
        assert names == {f.name for f in on.families}
        for name in names - set(NYISO_RCPF_STEP_CURVE_FAMILIES):
            a, b = _family(off, name), _family(on, name)
            np.testing.assert_allclose(a.ordc_penalties, b.ordc_penalties)
            np.testing.assert_allclose(a.ordc_step_widths, b.ordc_step_widths)
            np.testing.assert_allclose(a.requirement, b.requirement)


class TestStepCurve:
    """Flag on: one band at the published RCPF spanning the whole requirement."""

    def test_nyc_families_collapse_to_a_single_published_step(self):
        design = _nyiso_design(_config(nyiso_nyc_rcpf_step_curve=True), _fa(), T, ZONES)
        for name, (req, pen) in NYC_PUBLISHED.items():
            fam = _family(design, name)
            assert fam is not None
            # ONE band, priced at the published RCPF, spanning the full
            # requirement: any shortfall at all clears at $25/MW.
            np.testing.assert_allclose(fam.ordc_penalties, [pen])
            np.testing.assert_allclose(fam.ordc_step_widths, [req])

    def test_level_is_unchanged_only_the_depth_moves(self):
        # rule 5 [R-NO-MAGIC]: the correction introduces NO new number. The max
        # penalty is the same published $25/MW in both arms; what changes is
        # that the ramp never reached it except at zero reserve.
        off = _nyiso_design(_config(), _fa(), T, ZONES)
        on = _nyiso_design(_config(nyiso_nyc_rcpf_step_curve=True), _fa(), T, ZONES)
        for name, (_req, pen) in NYC_PUBLISHED.items():
            assert _family(off, name).ordc_penalties.max() == pen
            assert _family(on, name).ordc_penalties.max() == pen

    def test_total_step_width_is_conserved_so_the_balance_row_stays_feasible(self):
        # The shortfall variable must still span the whole requirement, or the
        # reserve balance row becomes infeasible at zero reserve.
        off = _nyiso_design(_config(), _fa(), T, ZONES)
        on = _nyiso_design(_config(nyiso_nyc_rcpf_step_curve=True), _fa(), T, ZONES)
        for name in NYISO_RCPF_STEP_CURVE_FAMILIES:
            assert np.isclose(
                _family(off, name).ordc_step_widths.sum(),
                _family(on, name).ordc_step_widths.sum(),
            )

    def test_step_prices_a_shallow_shortfall_at_the_full_rcpf(self):
        # The behavioural claim, stated as the arithmetic the LP will see: at a
        # ~310 MW shortfall of the 500 MW 10-minute requirement the ramp charges
        # its 5th rung ($15.625) while the published step charges $25.00.
        off = _family(_nyiso_design(_config(), _fa(), T, ZONES), "nyc_10min_total")
        on = _family(
            _nyiso_design(_config(nyiso_nyc_rcpf_step_curve=True), _fa(), T, ZONES),
            "nyc_10min_total",
        )
        shortfall = 310.0
        # Marginal price of the band the shortfall lands in, each arm.
        edges_off = np.cumsum(off.ordc_step_widths)
        assert off.ordc_penalties[int(np.searchsorted(edges_off, shortfall))] == 15.625
        edges_on = np.cumsum(on.ordc_step_widths)
        assert on.ordc_penalties[int(np.searchsorted(edges_on, shortfall))] == 25.0
