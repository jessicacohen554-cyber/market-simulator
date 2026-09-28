"""SOCO-83: carry the keeper-only DOF entries forward and ledger the ST_GAS out-of-merit level.

Runs LAST in the attestation chain, where ``soco82_attest_extras.py`` ran (after
``build_dof_ledger.py``, ``gen_soco60b_attestation.py``, ``gen_rsoco_attestation.py`` and
``gen_rsocob_attestation.py``). Carries soco-82's hand-added entries verbatim from the
incumbent keeper and adds ONE measured entry: ``thermal_tranches_oom_level_mw_SOCO.csv``
(3 per-plant levels, identified by Southern's FERC-714 lambda below the plant's measured
cost — zero fitted, so ``n_residual`` is unchanged).

Usage::

    python3 scripts/probes/soco83_attest_extras.py --bundle results/calibration/soco83_span
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Repointed soco-84 (2026-09-28): soco82_span was pruned at the soco-83 promotion (rule 35);
# read the incumbent keeper.
KEEPER = ROOT / "results/calibration/soco83_span/calibration_attestation.json"

#: Keeper-only entries, carried by NAME PREFIX (soco82_attest_extras.CARRY).
CARRY = (
    "unit_outage_precod_clip",
    "summer_derate_basis_aware",
    "coal_mustrun_requires_measured_row",
    "thermal_tranches_SOCO.csv COAL coverage",
    "campd_coal_heat_rates_SOCO.csv window + population",
    "GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR['SOCO'][2019..2022]",
    "egrid_identity_heat_rates_SOCO.csv",
    "coal_incremental_hr_ratio_SOCO.csv",
)

ENTRY = {
    "name": "thermal_tranches_oom_level_mw_SOCO.csv (ST_GAS out-of-merit must-run level: Gaston 26, Yates 728, Watson 2049)",
    "identification": "measured-conduct",
    "n_scalars": 3,
    "value": "179.0 / 120.0 / 190.0 MW (pooled 2019-2025)",
    "basis": (
        "soco-83 (owner rulings 2026-09-28 on the soco-83 decision cards: build the ST out-of-merit floor; "
        "partition by plant; condition on Southern lambda < plant cost). p25 of each plant's measured net "
        "output in its online hours when Southern Company's FERC-714 Part II Sch. 6 system lambda sat below "
        "the plant's own monthly cost (thermal_tranches_oom_cost_SOCO.csv), pooled 2019-2025 "
        "(derive_thermal_tranche_oom_level_mw.py --condition lambda; the frozen family's online mask, net, "
        "derate, percentile and clamp). Armed through st_gas_mustrun_per_plant + st_gas_mustrun_p25_level + "
        "st_gas_mustrun_oom_level; those plants leave soco_gas_st_campaign_commitment (rule 19 partition). "
        "Zero fitted: n_residual unchanged. docs/handoffs/r-soco/PRECOMMIT-soco-83-2026-09-28.md."
    ),
}

DISCLOSURE = (
    "SOCO ST_GAS out-of-merit must-run floor (soco-83): Gaston / Yates / Watson floored at their measured "
    "lambda-conditioned p25 level in the family's top-online_frac load-hour window; they leave the campaign "
    "floor, which keeps Greene County. Driver measured as non-economic (FINDING-soco-83 §2: ST boilers run "
    "while Southern's lambda is below their cost in 60-88 % of synced hours) but its cause is unidentified; "
    "about 21 % of floor energy falls in hours the plants' CEMS shows offline (reported, PRECOMMIT §3)."
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
    if ENTRY["name"] not in have:
        fp["entries"].append(ENTRY)
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )
    disc = att.setdefault("disclosures", {})
    for k in (
        "soco76_egrid_identity",
        "soco81_two_sided_incremental_hr",
        "soco82_perunitdark_regen",
    ):
        if k in kept.get("disclosures", {}):
            disc.setdefault(k, kept["disclosures"][k])
    disc["soco83_st_gas_oom_floor"] = DISCLOSURE
    path.write_text(json.dumps(att, indent=2, sort_keys=True) + "\n")
    print(f"{path}: {fp['n_entries']} entries, n_residual {fp['n_residual']}")


if __name__ == "__main__":
    main()
