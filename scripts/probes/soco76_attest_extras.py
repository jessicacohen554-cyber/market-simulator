"""SOCO-76: carry the keeper-only DOF entries forward and add this lane's one entry.

Runs LAST in the attestation chain (after ``build_dof_ledger.py``,
``gen_soco60b_attestation.py``, ``gen_rsoco_attestation.py`` and
``gen_rsocob_attestation.py``). Those builders regenerate the inherited ledger but
not the six entries the soco-67..72 lanes added by hand to their own bundles, so
this copies them verbatim from the incumbent keeper's attestation (by name,
failing loud if any is missing) and appends the soco-76 entry. Expected result:
27 + 1 = 28 entries, ``n_residual`` unchanged at 1.

Usage::

    python3 scripts/probes/soco76_attest_extras.py --bundle results/calibration/soco76_span
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KEEPER = ROOT / "results/calibration/soco72_span/calibration_attestation.json"

#: The keeper-only entries, carried by NAME PREFIX (the two artifact entries carry
#: their plant lists in the name).
CARRY = (
    "unit_outage_precod_clip",
    "summer_derate_basis_aware",
    "coal_mustrun_requires_measured_row",
    "thermal_tranches_SOCO.csv COAL coverage",
    "campd_coal_heat_rates_SOCO.csv window + population",
    "GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR['SOCO'][2019..2022]",
)

ENTRY = {
    "name": "egrid_identity_heat_rates_SOCO.csv (Dahlberg 7709<->7765, Hartwell 54538<->70454)",
    "value": {"7709": 12.6212, "54538": 12.5649},
    "identification": "measured-physical",
    "n_scalars": 2,
    "basis": (
        "soco-76 (rules 14 [R-ACCURATE] / 19 / 21 / 23 / 25). EPA files Dahlberg (EIA 7709) and "
        "Hartwell (EIA 54538) under CAMD/eGRID ORIS 7765 / 70454 (the CAMD-EIA crosswalk's "
        "PLANT_ID_CHANGE_FLAG=1 pair), so neither reached a CAMPD or eGRID measured rate and both "
        "priced at the HEAT_RATE_BINS class default (10.5 / 11.5). The registered carrier "
        "egrid_identity_heat_rates (nyiso-151), its frozen threshold-free discovery rule run over "
        "SOCO's whole CAMPD-less fossil population (AL/FL/GA/MS; one ISO_SCOPE row), finds exactly "
        "these two plants at 7/7 eGRID vintages (PLNGENAN == EIA-923 netgen <0.5 MWh); rate = pooled "
        "eGRID PLHTIAN/PLNGENAN (LOYO 12.61-12.64 / 12.26-12.65). Two measured values, zero fitted: "
        "n_residual unchanged. docs/records/soco/r-soco/PRECOMMIT-soco-76-2026-09-27.md §2a."
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
    att.setdefault("disclosures", {})["soco76_egrid_identity"] = (
        "egrid_identity_heat_rates armed for SOCO on its own artifact (Dahlberg 10.5 -> 12.6212, "
        "Hartwell 11.5 -> 12.5649 MMBtu/MWh); pre-registered NOT to close 2019 COAL_BIT or 2020 C4."
    )
    path.write_text(json.dumps(att, indent=2, sort_keys=True) + "\n")
    print(f"{path}: {fp['n_entries']} entries, n_residual {fp['n_residual']}")


if __name__ == "__main__":
    main()
