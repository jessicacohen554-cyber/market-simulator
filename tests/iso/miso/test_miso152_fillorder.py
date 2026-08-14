"""miso-152 G-3 — the tranche FILL-ORDER existence proof, on a real LP solve.

PREREG ``PREREG-miso152-tranche-fill-order-2026-08-11.md`` §2 G-3. The probe's
G-4 magnitude is measured on a price-taking merit RECONSTRUCTION; this file
proves the underlying claim against an actual ``solve_dispatch``, so the
reconstruction's central assumption is verified rather than assumed.

The claim: MISO registers ``econ_low`` (0.95) BELOW ``committed`` (1.005), the
LP carries no same-plant fill-order constraint, and MISO floors nothing on the
CC committed tranche (measured on the real 2025 fleet: ``pmin`` and ``min_gen``
are 0.0 on all 44 CC_REGULAR committed rows). A CC plant therefore produces its
INCREMENTAL bands while its MIN-LOAD block sits idle — an output the physical
unit cannot deliver.

Trap T-1 (the miso-151 ``SimpleNamespace(pmax=…)`` incident): every fixture row
is built through the production ``make_gen``/``generators_to_fleet_arrays`` path
on the real ``Generator`` type, so a wrong field name fails here instead of
silently encoding itself into the test.
"""

from __future__ import annotations

import numpy as np

from market_sim.data.fleet import generators_to_fleet_arrays
from tests.helpers.builders import make_gen
from tests.helpers.solve import solve_tiny

# The real MISO keeper tranche stack for CC_REGULAR plant p991
# (`results/calibration/miso148_basis_B`, 2025, measured by
# scripts/probes/_miso152_fillorder.py): one 515.97 MW min-load block and six
# 36.85 MW smoothed econ sub-tranches (offer_curve_smoothing_n = 6).
COMMITTED_MW = 515.97
ECON_MW = 36.85
COMMITTED_MC = 26.184
ECON_MC = (25.122, 25.643, 26.164, 26.686, 27.207, 27.729)

ZONES = ["Z0"]


def _plant(monotone: bool = False):
    """Build one CC plant's tranche rows through the production path.

    Args:
        monotone: When True the min-load block is priced BELOW every econ
            sub-tranche (a physically-ordered offer curve), the control for
            the non-monotone MISO case.
    """
    gens = [
        make_gen(
            unit_id="CC_REGULAR_Z0_p991_committed",
            zone="Z0",
            pmax_mw=COMMITTED_MW,
            pmin_mw=0.0,  # measured on the real fleet: tranches carry no pmin
            eford=0.0,
            plant_group="CC_REGULAR",
        )
    ]
    gens += [
        make_gen(
            unit_id=f"CC_REGULAR_Z0_p991_econc0{j}",
            zone="Z0",
            pmax_mw=ECON_MW,
            pmin_mw=0.0,
            eford=0.0,
            plant_group="CC_REGULAR",
        )
        for j in range(len(ECON_MC))
    ]
    fleet = generators_to_fleet_arrays(gens, ZONES, hours=24)
    committed_mc = min(ECON_MC) - 1.0 if monotone else COMMITTED_MC
    mc = np.array([committed_mc, *ECON_MC], dtype=float)
    return fleet, mc


def test_fixture_uses_production_fields():
    """T-1 guard: capacities must read back non-zero and distinct.

    A wrong capacity field name (the miso-151 ``pmax`` vs ``pmax_mw`` defect)
    collapses every row to 0.0 and makes the tests below vacuous.
    """
    fleet, _ = _plant()
    assert fleet.pmax[0] == COMMITTED_MW
    assert np.allclose(fleet.pmax[1:], ECON_MW)
    assert fleet.pmax[0] != fleet.pmax[1]


def test_lp_fills_econ_before_the_min_load_block():
    """The LP produces incremental MW with the min-load block idle."""
    fleet, mc = _plant()
    # 100 MW — far below the 515.97 MW the unit must reach to be at min load.
    res = solve_tiny(fleet, {"Z0": 100.0}, ZONES, hours=24, mc=mc)
    d = res.dispatch[:, 0]

    assert d[0] == 0.0, "min-load block should be idle (it is the dearer row)"
    assert d[1:].sum() > 0.0, "econ sub-tranches carry the whole output"
    # The physical impossibility, stated as the assertion: the plant delivers
    # output while sitting below its own minimum stable load.
    assert 0.0 < d.sum() < COMMITTED_MW


def test_out_of_order_energy_is_the_sub_tranches_under_committed_mc():
    """Exactly the econ sub-tranches priced below the min-load block fill."""
    fleet, mc = _plant()
    cheaper = [j for j, m in enumerate(ECON_MC) if m < COMMITTED_MC]
    # Demand equal to the cheaper sub-tranches' combined capacity.
    demand = len(cheaper) * ECON_MW
    res = solve_tiny(fleet, {"Z0": demand}, ZONES, hours=24, mc=mc)
    d = res.dispatch[:, 0]

    assert d[0] == 0.0
    assert np.isclose(d[1 : 1 + len(cheaper)].sum(), demand, atol=1e-6)
    assert len(cheaper) == 3, "3 of 6 econ subs sit below committed on MISO"


def test_monotone_curve_fills_the_min_load_block_first():
    """Control: the defect is caused by the PRICING, not by the LP.

    With a physically-ordered curve (min-load cheapest) the same LP fills the
    min-load block first, so nothing in the formulation needs changing — only
    the non-monotone band registration makes the fill order unphysical.
    """
    fleet, mc = _plant(monotone=True)
    res = solve_tiny(fleet, {"Z0": 100.0}, ZONES, hours=24, mc=mc)
    d = res.dispatch[:, 0]

    assert np.isclose(d[0], 100.0, atol=1e-6)
    assert np.isclose(d[1:].sum(), 0.0, atol=1e-6)
