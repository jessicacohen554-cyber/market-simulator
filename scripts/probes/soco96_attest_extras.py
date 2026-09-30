"""SOCO-96: carry the keeper-only DOF entries forward; disclose the measured oil-burn fuel mix.

Runs LAST in the attestation chain, where ``soco93_attest_extras.py`` ran (after
``build_dof_ledger.py``, ``gen_soco60b_attestation.py``, ``gen_rsoco_attestation.py`` and
``gen_rsocob_attestation.py``). Carries soco-83's hand-added entries verbatim from the
incumbent keeper (soco93_span). ``dual_fuel_measured_oil_burn`` adds NO free parameter (the
two CO2 signatures are 40 CFR Part 75 App. G Eq. G-4 constants, no threshold, no scaling),
so ``n_entries`` and ``n_residual`` are unchanged; it is recorded as a disclosure only, with
its rule-13 standing stated, beside the carried soco-85/87/92/93 disclosures.

Usage::

    python3 scripts/probes/soco96_attest_extras.py --bundle results/calibration/soco96_span
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# The incumbent keeper at soco-96.
KEEPER = ROOT / "results/calibration/soco93_span/calibration_attestation.json"

#: Keeper-only entries, carried by NAME PREFIX (soco83_attest_extras.CARRY + its ENTRY).
CARRY = (
    "unit_outage_precod_clip",
    "summer_derate_basis_aware",
    "coal_mustrun_requires_measured_row",
    "thermal_tranches_SOCO.csv COAL coverage",
    "campd_coal_heat_rates_SOCO.csv window + population",
    "GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR['SOCO'][2019..2022]",
    "egrid_identity_heat_rates_SOCO.csv",
    "coal_incremental_hr_ratio_SOCO.csv",
    "thermal_tranches_oom_level_mw_SOCO.csv",
)

DISCLOSURE = (
    "dual_fuel_measured_oil_burn (soco-96, owner ruling 2026-09-30 'Oil price at measured burn'): each gas "
    "generator at a plant with a measured row is priced per covered day at f*oil + (1-f)*gas, oil = EIA-923 "
    "monthly delivered petroleum, gas = the cell's final delivered gas price. f = the plant-day oil share of "
    "heat input from the CAMPD CO2/heat-input mixing identity over gas-primary, non-coal-capable units, at the "
    "40 CFR Part 75 App. G Eq. G-4 signatures CAMPD books co2Mass on "
    "(data/raw/_processed-legacy/campd_measured_oil_burn_days_SOCO.csv). Zero DOF. RULE 13 STANDING: the trigger "
    "is measured unit fuel conduct in the solve year, admitted by owner ruling as a backcast-only measured "
    "physical input (analogous to CAMPD outage windows); forward substitute dual_fuel_switching's parity switch "
    "(PRECOMMIT-soco-96 sections 1 and 7)."
)


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", required=True)
    a = ap.parse_args()
    path = ROOT / a.bundle / "calibration_attestation.json"
    att = json.loads(path.read_text())
    fp = att["free_parameters"]
    kept = json.loads(KEEPER.read_text())
    keeper = kept["free_parameters"]["entries"]
    have = {e["name"] for e in fp["entries"]}
    for prefix in CARRY:
        src = [e for e in keeper if e["name"].startswith(prefix)]
        if len(src) != 1:
            raise SystemExit(f"keeper entry {prefix!r}: found {len(src)}")
        if src[0]["name"] not in have:
            fp["entries"].append(src[0])
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )
    disc = att.setdefault("disclosures", {})
    for k in (
        "soco76_egrid_identity",
        "soco81_two_sided_incremental_hr",
        "soco82_perunitdark_regen",
        "soco83_st_gas_oom_floor",
        "soco85_gas_daily_shape",
        "soco87_gas_hh_monthly_shape",
        "soco92_hydro_min_flow_floor",
        "soco93_hydro_pondage_bound",
    ):
        if k in kept.get("disclosures", {}):
            disc.setdefault(k, kept["disclosures"][k])
    disc["soco96_dual_fuel_measured_oil_burn"] = DISCLOSURE
    path.write_text(json.dumps(att, indent=2, sort_keys=True) + "\n")
    print(f"{path}: {fp['n_entries']} entries, n_residual {fp['n_residual']}")


if __name__ == "__main__":
    main()
