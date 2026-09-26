"""SOCO-72: carry the keeper-only DOF entries forward and add this lane's one entry.

Runs LAST in the attestation chain (after ``build_dof_ledger.py``,
``gen_soco60b_attestation.py``, ``gen_rsoco_attestation.py`` and
``gen_rsocob_attestation.py``). Those builders regenerate the inherited ledger but
not the five entries the soco-67..71 lanes added by hand to their own bundles, so
this copies them verbatim from the incumbent keeper's attestation (by name,
failing loud if any is missing) and appends the soco-72 entry. Expected result:
26 + 1 = 27 entries, ``n_residual`` unchanged at 1.

Usage::

    python3 scripts/probes/soco72_attest_extras.py --bundle results/calibration/soco72_span
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KEEPER = ROOT / "results/calibration/soco71_span/calibration_attestation.json"

#: The keeper-only entries, carried by NAME PREFIX (the two artifact entries carry
#: their plant lists in the name).
CARRY = (
    "unit_outage_precod_clip",
    "summer_derate_basis_aware",
    "coal_mustrun_requires_measured_row",
    "thermal_tranches_SOCO.csv COAL coverage",
    "campd_coal_heat_rates_SOCO.csv window + population",
)

ENTRY = {
    "name": "GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR['SOCO'][2019..2022]",
    "value": {"2019": 0.27, "2020": 0.32, "2021": 0.30, "2022": 1.20},
    "identification": "measured-physical",
    "n_scalars": 4,
    "basis": (
        "soco-72 (rules 14 [R-ACCURATE] / 19 / 21 / 23). The K mechanism "
        "gas_basis_measured_by_year carried only SOCO-55's 2023-2025 rows, so the "
        "2019-2025 keeper's 2019-2022 gas fell through to the 2024 scalar 0.64 -- a "
        "fall-through the table reserves for years whose receipts are not filed. The "
        "SAME construction, unchanged (quantity-weighted EIA-923 delivered natural gas "
        "to BA=SOCO plants in data/raw/eia-860/eia860_plant.parquet, minus the Henry "
        "Hub annual mean; it reproduces the three committed rows byte-for-byte), on "
        "the committed 2019-2022 receipts: +0.2686 / +0.3209 / +0.3024 / +1.2023, "
        "registered at the family's 2dp. Four measured values, zero fitted: "
        "n_residual unchanged. Declared misalignment: the current plant file excludes "
        "the former Gulf plants the 2019-2022 runs carry; the run-fleet and vintage-BA "
        "variants agree in sign and to <= $0.07. "
        "docs/handoffs/r-soco/PRECOMMIT-soco-72-2026-09-26.md §2."
    ),
}


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", required=True)
    a = ap.parse_args()
    path = ROOT / a.bundle / "calibration_attestation.json"
    att = json.loads(path.read_text())
    fp = att["free_parameters"]
    keeper = json.loads(KEEPER.read_text())["free_parameters"]["entries"]
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
    fp["n_residual"] = sum(1 for e in fp["entries"] if e.get("identification") == "residual")
    att.setdefault("disclosures", {})["soco72_gas_basis_window"] = (
        "GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR['SOCO'] extended to 2019-2022 (0.27/0.32/0.30/1.20, "
        "was the 0.64 fall-through); pre-registered to deepen the 2019 COAL_BIT row. "
        "SOCO's key moves (lane-added-moved GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR)."
    )
    path.write_text(json.dumps(att, indent=2, sort_keys=True) + "\n")
    print(f"{path}: {fp['n_entries']} entries, n_residual {fp['n_residual']}")


if __name__ == "__main__":
    main()
