"""Driver: PJM 89 — steam-gas overnight drag + CHP HR + outage-capture keeper candidate.

The pjm-83 keeper recipe VERBATIM (``run_pjm86_pjm83_head_baseline._solve``,
which is ``run_pjm80_srmc_reground_keeper`` re-solved at HEAD), re-solved on the
current data tree so it absorbs FOUR structural corrections landed on this
branch — all of which live in base config / base data, so the recipe itself is
byte-unchanged and every delta vs pjm-83 is one of these mechanisms:

1. **ST_GAS extreme-day overnight drag** (the headline). Within the
   ``reliability_floor`` engine (already ``reliability_floor=True`` here), PJM
   ST_GAS now carries overnight-windowed [0,6] tmax/tmin/netload limbs at its
   min-must-run level (``reliability_floor_coeffs_PJM.csv``,
   ``derive_pjm_st_gas_overnight_drag.py``): on an extreme-temperature or
   high-net-load day the boiler is held warm at min-stable overnight to ramp for
   the next peak instead of cycling off. 7 limbs enabled where the driver is
   real; forced-energy 3.4-6.1% of class energy (rule 20). Replaces the old
   all-day ST_GAS limbs (rule 14); ``gas_st_netload_drag`` stays OFF.

2. **CHP steam-credit power-only heat-rate correction** extended to PJM
   (``chp._correct_chp_steam_credit_hr``, ``CHP_STEAM_CREDIT_HR_CORRECTION_ISOS``
   now {CAISO, PJM}). PJM CC_CHP/CT_CHP reported physically-impossible
   steam-credited HRs (~4.95 / ~6.14 MMBtu/MWh) that let them clear as the
   cheapest thermal and over-deliver grid energy +52-67% vs EIA-923; the
   universal turbine-physics correction (topping factor + 6.3 floor) lifts them
   to their real power-only band.

3. **Outage capture**: FULL_STOP_OVERRIDE_DAYS 14->5 recovers the 5-13 day PRB
   dead stops (Kincaid/Powerton, ~3.7k COAL plant-days), and orphaned
   gross-blank ST_CHP steam-host boilers are now detected (Grays Ferry) so the
   flat ``chp_grid_pmin_mw`` floor no longer force-generates them through a real
   plant-wide stop. (Re-derived PJM outage CSVs, 2023-2025 only; holdouts
   preserved.)

4. **Coal-bituminous econ-high default** raised 0.8064->0.90 in the base
   ``_PJM_OFFER_CURVE``. NOTE: the keeper's ``OFFER_CURVE_OVERRIDES['COAL_BIT']``
   already sets econ_high=1.2664, which deep-merges OVER the default, so this
   base bump does not change THIS solve — coal-bit econ-high is held at the
   keeper's 1.2664 pending re-assessment against the post-fix 923 fuel-mix
   (the CHP HR fix and PRB outage capture both move coal-bit's dispatch, so the
   level is re-judged after this solve, not stacked blind).

Full span 2023-2025 in one bundle (rule 16), years sequential (rule 1/12).
A zero-forcing ablation twin + dashboard registration follow once this scores.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

from scripts.run_calibration_full import report_run  # noqa: E402
from scripts.run_pjm86_pjm83_head_baseline import _solve  # noqa: E402

NOTE = (
    "PJM 89 steam-gas overnight drag keeper candidate: pjm-83 recipe re-solved "
    "at HEAD, absorbing four base-config/base-data corrections vs pjm-83 - "
    "(1) ST_GAS extreme-day overnight [0,6] drag in the reliability_floor engine "
    "(tmax/tmin/netload, min-stable, 7 limbs enabled where the driver is real, "
    "forced-energy 3.4-6.1%), (2) CHP steam-credit power-only HR correction "
    "extended to PJM (CC_CHP/CT_CHP no longer clear on impossible ~5-6 MMBtu/MWh "
    "and over-deliver +52-67% vs 923), (3) PRB 5-13d dead-stop + orphaned ST_CHP "
    "steam-boiler outage capture, (4) coal-bit econ-high held at the keeper's "
    "1.2664 (base default 0.90 is deep-merged over). Recipe byte-unchanged; every "
    "delta vs pjm-83 is one of these four structural mechanisms."
)


def main() -> int:
    """Solve the PJM 89 steam-gas-drag keeper candidate over 2023-2025."""
    out_dir = Path("results/calibration/pjm89_steamgas_drag")
    run_dir = _solve(out_dir, note=NOTE)
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
