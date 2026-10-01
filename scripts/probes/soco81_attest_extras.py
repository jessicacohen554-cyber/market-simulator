"""SOCO-81: carry the keeper-only DOF entries forward and add this lane's one entry.

Runs LAST in the attestation chain, exactly where ``soco76_attest_extras.py`` ran:
after ``build_dof_ledger.py``, ``gen_soco60b_attestation.py``,
``gen_rsoco_attestation.py`` and ``gen_rsocob_attestation.py``. Those builders do
not regenerate the entries the soco-67..76 lanes added by hand, so this copies them
verbatim from the incumbent keeper's attestation (by name prefix, failing loud if
any is missing) and appends the soco-81 entry. Expected: 28 + 1 = 29 entries,
``n_residual`` unchanged.

Usage::

    python3 scripts/probes/soco81_attest_extras.py --bundle results/calibration/soco81_span
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KEEPER = ROOT / "results/calibration/soco76_span/calibration_attestation.json"

#: Keeper-only entries, carried by NAME PREFIX.
CARRY = (
    "unit_outage_precod_clip",
    "summer_derate_basis_aware",
    "coal_mustrun_requires_measured_row",
    "thermal_tranches_SOCO.csv COAL coverage",
    "campd_coal_heat_rates_SOCO.csv window + population",
    "GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR['SOCO'][2019..2022]",
    "egrid_identity_heat_rates_SOCO.csv",
)

ENTRY = {
    "name": "coal_incremental_hr_ratio_SOCO.csv (must-run-floored coal: Bowen, Miller, Scherer, Daniel, Gaston)",
    "value": "per plant-year ratio_econ_low / ratio_econ_high, 0.767-1.077 (2019-2025); pooled row for forward years",
    "identification": "measured-physical",
    "n_scalars": 70,
    "basis": (
        "soco-81 (owner ruling 2026-09-27 on FINDING-soco-75 §6; rules 13 / 14 / 18 / 19 / 21 / 23 / 25). "
        "Each plant's CEMS incremental heat rate (the frozen derive_campd_marginal_hr I/O slope at "
        "econ_low x = 0.5 / econ_high x = 0.9, over the same steady-state hours the average-HR artifact "
        "averages) divided by its average HR, same plant-year "
        "(scripts/data/derive_coal_incremental_hr_ratio.py). Applied by "
        "coal_econ_marginal_hr_two_sided only above a measured min-load floor (_committed/_econ*, a unit "
        "parameter), replacing the 1.0 band there; cyclers keep the average (SOCO-63 §5). 5 plants x 7 "
        "years x 2 points = 70 measured values, zero fitted: n_residual unchanged. "
        "docs/records/soco/r-soco/PRECOMMIT-soco-81-2026-09-27.md §1-§3."
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
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )
    disc = att.setdefault("disclosures", {})
    keeper_disc = json.loads(KEEPER.read_text()).get("disclosures", {})
    if "soco76_egrid_identity" in keeper_disc:
        disc.setdefault("soco76_egrid_identity", keeper_disc["soco76_egrid_identity"])
    disc["soco81_two_sided_incremental_hr"] = (
        "coal_econ_marginal_hr_two_sided armed for SOCO on its own artifact: the committed + econ "
        "tranches of the five must-run-floored coal plants price at their measured incremental HR "
        "(ratios 0.77-1.08 of average); pre-registered to close 2020 C4 coal and NOT 2019 COAL_BIT."
    )
    path.write_text(json.dumps(att, indent=2, sort_keys=True) + "\n")
    print(f"{path}: {fp['n_entries']} entries, n_residual {fp['n_residual']}")


if __name__ == "__main__":
    main()
