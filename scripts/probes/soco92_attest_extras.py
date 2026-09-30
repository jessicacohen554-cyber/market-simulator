"""SOCO-92: carry the keeper-only DOF entries forward; disclose the reconciled reservoir min-flow floor.

Runs LAST in the attestation chain, where ``soco87_attest_extras.py`` ran (after
``build_dof_ledger.py``, ``gen_soco60b_attestation.py``, ``gen_rsoco_attestation.py`` and
``gen_rsocob_attestation.py``). Carries soco-83's hand-added entries verbatim from the
incumbent keeper (soco92_span). ``hydro_min_flow_floor`` (reconciled under
``hydro_ror_split``) adds NO free parameter (the percentile is the ceiling's mirror, the
allocation is by measured budget), so ``n_entries`` and ``n_residual`` are unchanged; it is
recorded as a disclosure only, beside the carried soco-85/87 disclosures.

Usage::

    python3 scripts/probes/soco92_attest_extras.py --bundle results/calibration/soco92_span
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# The incumbent keeper at soco-92.
KEEPER = (
    ROOT / "results/calibration/soco93_span/calibration_attestation.json"
)  # repointed soco-93 (rule 35 prune of soco92_span)

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
    "hydro_min_flow_floor reconciled under hydro_ror_split (soco-92, owner ruling 2026-09-29 'Queue as "
    "next SOCO lane'): the fleet's measured monthly Q95 low-flow level (EIA-930 NG: WAT, "
    "measured_hydro_min_flow_level) less the RoR class's stamped flat base, allocated over the RESERVOIR "
    "class pro rata by budget (data.hydro.build_hydro_fleet). Zero DOF. Pre-2024-07-15 NG: WAT folds PS "
    "discharge (<= +12 MW on the 2025 Q05, rule 14 bounded) and Dec-2024 carries no floor (EIA-930 gap). "
    "Built for structure, not C3a (PRECOMMIT-soco-92 section 1)."
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
    ):
        if k in kept.get("disclosures", {}):
            disc.setdefault(k, kept["disclosures"][k])
    disc["soco92_hydro_min_flow_floor"] = DISCLOSURE
    path.write_text(json.dumps(att, indent=2, sort_keys=True) + "\n")
    print(f"{path}: {fp['n_entries']} entries, n_residual {fp['n_residual']}")


if __name__ == "__main__":
    main()
