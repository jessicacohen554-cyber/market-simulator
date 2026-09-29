"""SOCO-85: carry the keeper-only DOF entries forward; disclose the Henry Hub daily gas shape.

Runs LAST in the attestation chain, where ``soco83_attest_extras.py`` ran (after
``build_dof_ledger.py``, ``gen_soco60b_attestation.py``, ``gen_rsoco_attestation.py`` and
``gen_rsocob_attestation.py``). Carries soco-83's hand-added entries verbatim from the
incumbent keeper, including soco-83's own ST_GAS out-of-merit level entry. ``gas_daily_shape``
adds NO free parameter (a measured national daily series, mean-preserving per month), so
``n_entries`` and ``n_residual`` are unchanged; it is recorded as a disclosure only.

Usage::

    python3 scripts/probes/soco85_attest_extras.py --bundle results/calibration/soco87_span
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Repointed soco-85 (2026-09-28): soco83_span was pruned at the soco-85 promotion (rule 35);
# the incumbent keeper is soco85_span (the soco-83 recipe + gas_daily_shape).
# Repointed soco-87 (2026-09-29): soco85_span was pruned at the soco-87 promotion (rule 35);
# the incumbent keeper is soco87_span (the soco-85 recipe + gas_hh_monthly_shape).
KEEPER = ROOT / "results/calibration/soco87_span/calibration_attestation.json"

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
    "gas_daily_shape (soco-85, owner ruling 2026-09-28 'Arm + solve 7 shards'): every gas plant-month's "
    "measured F923 delivered level carries the measured Henry Hub daily staircase / its own month's "
    "calendar-day mean (fuel.hubs.gas_daily_shape_factors), mean-preserving per month. Zero DOF. It does "
    "NOT carry the Southeast basis: no free daily SE hub exists 2019-2025 (FINDING-soco-85 section 4), so the "
    "cold-snap peak gap (Elliott lambda 407 vs model ~93 $/MWh) is a stated data limitation."
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
    ):
        if k in kept.get("disclosures", {}):
            disc.setdefault(k, kept["disclosures"][k])
    disc["soco85_gas_daily_shape"] = DISCLOSURE
    path.write_text(json.dumps(att, indent=2, sort_keys=True) + "\n")
    print(f"{path}: {fp['n_entries']} entries, n_residual {fp['n_residual']}")


if __name__ == "__main__":
    main()
