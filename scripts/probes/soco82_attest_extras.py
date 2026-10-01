"""SOCO-82: carry the keeper-only DOF entries forward; disclose the regenerated outage extract.

Runs LAST in the attestation chain, exactly where ``soco81_attest_extras.py`` ran:
after ``build_dof_ledger.py``, ``gen_soco60b_attestation.py``,
``gen_rsoco_attestation.py`` and ``gen_rsocob_attestation.py``. Those builders do not
regenerate the entries the soco-67..81 lanes added by hand, so this copies them
verbatim from the incumbent keeper's attestation (by name prefix, failing loud if any
is missing). soco-82 adds NO free parameter — it re-derives one measured input with
its own frozen deriver — so the expected count stays 29 and ``n_residual`` stays 1.

Usage::

    python3 scripts/probes/soco82_attest_extras.py --bundle results/calibration/soco82_span
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Repointed soco-83 (2026-09-28): soco81_span was pruned (rule 35); read the incumbent keeper.
KEEPER = ROOT / "results/calibration/soco82_span/calibration_attestation.json"

#: Keeper-only entries, carried by NAME PREFIX.
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

DISCLOSURE = (
    "campd-unit-outages-perunitdark-SOCO.csv re-derived at HEAD with its own recorded invocation "
    "(rule 23 data change: F1 31e54d8a5 appended the SOCO retirees to "
    "eia860_generator_retired_within_window.parquet 37 min after F2 5ff0cb9cb derived the file). "
    "+44 coal windows (Wansley 6052: 37; Gorgas 8: 4; Hammond 708: 3 -- the latter two in no SOCO "
    "LP fleet); Wansley availability 0.914 -> 0.233 / 0.020 / 0.118 in 2019 / 2020 / 2021, nothing "
    "else moves. Zero scalars. docs/records/soco/r-soco/PRECOMMIT-soco-82-2026-09-27.md."
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
    for k in ("soco76_egrid_identity", "soco81_two_sided_incremental_hr"):
        if k in kept.get("disclosures", {}):
            disc.setdefault(k, kept["disclosures"][k])
    disc["soco82_perunitdark_regen"] = DISCLOSURE
    path.write_text(json.dumps(att, indent=2, sort_keys=True) + "\n")
    print(f"{path}: {fp['n_entries']} entries, n_residual {fp['n_residual']}")


if __name__ == "__main__":
    main()
