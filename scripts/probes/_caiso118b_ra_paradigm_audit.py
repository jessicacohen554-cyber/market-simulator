"""caiso-118b AUDIT: the CAISO commitment paradigm + the import-mechanism stack.

Companion to `_caiso118_belly_price_derive.py`. Reproduces the three audit facts
behind the RA-commitment-paradigm diagnosis (NO LP):

  A. The published RA must-offer gas quantity (the measured commitment DRIVER,
     already in the codebase but wired only as a CAP) vs the model's committed
     belly gas.
  B. The CAISO flag stack: how many IMPORT mechanisms are ON vs how many
     OBLIGATION-based commitment mechanisms are ON, from the keeper run_config.
  C. The firm import self-schedule floor by hod vs actual net-import — showing
     the firm floor is belly-correct (~1 GW) and the model's belly OVER-import
     (~2-3 GW above it) is economic substitution for the gas it won't commit.

Run:  PYTHONPATH=<repo> python scripts/probes/_caiso118b_ra_paradigm_audit.py
"""

from __future__ import annotations

import json

import numpy as np

from market_sim.config.constants import CAISO_RA_MUSTOFFER_GAS_MW
from market_sim.config.interchange_config import IMPORT_TRANCHES
from market_sim.data.eia_loader import measured_firm_import_shape
from market_sim.model.interchange.caiso import CAISO_FIRM_IMPORT_TRANCHES

REPO = "/home/user/market-simulator"
KEEPER_CFG = f"{REPO}/results/calibration/caiso102_hourfix_B/run_config.json"
B, N, E = [10, 11, 12, 13, 14, 15], [0, 1, 2, 3, 4, 5], [17, 18, 19, 20, 21]
YEARS = (2023, 2024, 2025)
# measured, from _caiso118_belly_price_derive.py INV5 (EIA-930 CISO belly):
ACTUAL_BELLY_IMPORT = {2023: 651, 2024: 1341, 2025: 1766}
MODEL_BELLY_IMPORT = {2023: 3075, 2024: 3889, 2025: 3757}
MODEL_BELLY_GAS = {2023: 4260, 2024: 3721, 2025: 2947}
ACTUAL_BELLY_GAS = {2023: 8461, 2024: 9633, 2025: 10537}


def audit_a_ra_anchor() -> None:
    print("=== A. RA must-offer anchor (the measured commitment DRIVER) ===")
    print("CAISO_RA_MUSTOFFER_GAS_MW (DMM Annual Report, published, in codebase):")
    for y in YEARS:
        mw = CAISO_RA_MUSTOFFER_GAS_MW.get(y)
        at_minload = mw * 0.50  # ~physical CC min-load
        print(f"  {y}: obligated {mw:6.0f} MW  -> at min-load(0.50) ~{at_minload:5.0f} MW"
              f"   | model belly gas {MODEL_BELLY_GAS[y]:5.0f}  actual {ACTUAL_BELLY_GAS[y]:5.0f}")
    print("  READ: ~15.6 GW obligated x ~0.5 min-load ~= 8 GW ~= actual belly gas;"
          " the model commits ~1/3 of it.")


def audit_b_flag_stack() -> None:
    print("\n=== B. keeper flag stack: import ON vs obligation-commitment ON ===")
    sc = json.load(open(KEEPER_CFG))["scenario_config"]
    IMPORT = ["bidir_intertie", "corridor", "firm_import", "perhub", "per_hub",
              "import_hub", "import_node", "import_gas", "import_solar",
              "per_year_import", "dsw_", "intertie", "local_import",
              "reference_price_seam", "scarcity_import"]
    OBLIG = ["gas_commitment_floor", "ra_mustoffer_quantity_gate",
             "lcr_commitment_credit", "commitment_posture"]
    ECON = ["ra_mustoffer", "ra_startup", "ra_bridge", "ra_min_load"]

    def on(k):
        return sc.get(k) not in (False, None)

    imp_on = [k for k in sc if k.startswith("caiso_") and any(s in k for s in IMPORT) and on(k)]
    obl_on = [k for k in sc if any(k == f"caiso_{s}" or s in k for s in OBLIG)
              and k.startswith("caiso_") and on(k)]
    econ_on = [k for k in sc if k.startswith("caiso_") and any(s in k for s in ECON) and on(k)
               and "quantity_gate" not in k]
    print(f"  IMPORT mechanisms ON        : {len(imp_on)}")
    for k in sorted(imp_on):
        print(f"      {k.replace('caiso_', '')}")
    print(f"  OBLIGATION-commitment ON    : {len(obl_on)}  (the RA-quantity machinery)")
    for k in ("caiso_gas_commitment_floor", "caiso_ra_mustoffer_quantity_gate",
              "caiso_lcr_commitment_credit", "caiso_commitment_posture"):
        print(f"      {k.replace('caiso_', '')} = {sc.get(k)}  {'<- OFF' if not on(k) else ''}")
    print(f"  ECONOMIC-detection commit ON: {len(econ_on)}   min_load_frac ="
          f" {sc.get('caiso_ra_min_load_frac')}  (physical default 0.40; ERCOT-measured 0.574)")


def audit_c_firm_floor() -> None:
    print("\n=== C. firm import floor (self-schedule) vs actual net-import ===")
    firm_cap = sum(t[1] for t in IMPORT_TRANCHES["CAISO"] if t[0] in CAISO_FIRM_IMPORT_TRANCHES)
    print(f"  firm tranche nameplate = {firm_cap:.0f} MW (PNW_hydro_base + DSW_solar_PV)")
    for year in YEARS:
        w = measured_firm_import_shape("CAISO", year, 8760)
        if w is None:
            print(f"  {year}: no firm shape")
            continue
        w = np.asarray(w, float)
        hod = np.arange(8760) % 24
        fb = firm_cap * w
        floor_belly = fb[np.isin(hod, B)].mean()
        econ_over = MODEL_BELLY_IMPORT[year] - floor_belly
        print(f"  {year}: firm floor belly {floor_belly:5.0f} MW  (actual net-import"
              f" {ACTUAL_BELLY_IMPORT[year]:5.0f})  | model total import {MODEL_BELLY_IMPORT[year]:5.0f}"
              f"  -> ECONOMIC over-import ~{econ_over:5.0f} MW")
    print("  READ: firm floor ~= actual (~1 GW); the ~2-3 GW above it is economic import\n"
          "        substituting for the uncommitted gas (the dsw_*_clean depth supplies it).")


if __name__ == "__main__":
    print("=" * 78)
    print("caiso-118b RA-commitment-paradigm AUDIT (NO LP)")
    print("=" * 78)
    audit_a_ra_anchor()
    audit_b_flag_stack()
    audit_c_firm_floor()
    print("\n" + "=" * 78)
    print("READ: 9 import mechanisms ON, 0 obligation-commitment ON; the model commits")
    print("gas by ECONOMIC detection priced on its own (mis-cleared, over-imported) belly")
    print("LMP -> self-fulfilling under-commitment. Fix: wire CAISO_RA_MUSTOFFER_GAS_MW as")
    print("an obligation FLOOR (not a cap), restore physical min-load, retire the dsw stack.")
    print("=" * 78)
