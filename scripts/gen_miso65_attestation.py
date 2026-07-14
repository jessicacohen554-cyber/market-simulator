"""Generate the miso-65 candidate calibration_attestation.json.

Carries forward the miso-64 keeper attestation (governance clauses + the two
ledgered storage benchmark-basis exceptions, C5b throughput + C5c 2025 shape)
and rewrites the run-specific text for the miso-65 delta:

* ``attested_by`` — NOT a mechanism change: the miso-64 keeper recipe VERBATIM
  on the REGENERATED ``campd-unit-outages-MISO.csv`` (the committed >= 5-day
  extract was stale against its own frozen deriver + committed CAMPD; commit
  7b5c26fd, docs/FINDING-miso-lane3-north-supply-2026-07.md §3).
* ``note`` — the lane, the reproducibility evidence, and the LOYO argument
  (caiso-78 re-gate family: a year-invariant measured-input regeneration).
* ``free_parameters`` — rebuilt by build_dof_ledger.py (call FIRST); this
  merges back the hand-curated measured-physical rows. The change adds no
  parameter of any kind (same flags, same guards, same constants).

Usage: python scripts/gen_miso65_attestation.py {main|ablation}
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC64 = REPO / "results/calibration/miso64_classdonor/calibration_attestation.json"


def main(mode: str) -> None:
    ablate = mode == "ablation"
    out_dir = REPO / (
        "results/calibration/miso65_outage_regen" + ("-ablation" if ablate else "")
    )
    att = json.loads(SRC64.read_text())
    dst = out_dir / "calibration_attestation.json"

    carried = {
        "MISO COAL SOM near-cost offer floor",
        "COAL_SIGMOID_DEFAULTS[MISO]",
        "gas_daily_shape[MISO]",
        "hydro 2025 completeness (backfill 2024 + EIA-930 monthly repin)",
    }
    if dst.exists():
        cur = json.loads(dst.read_text())
        if "free_parameters" in cur:
            fp = cur["free_parameters"]
            have = {e["name"] for e in fp["entries"]}
            for e in att["free_parameters"]["entries"]:
                if e["name"] in carried and e["name"] not in have:
                    fp["entries"].append(e)
            fp["n_entries"] = len(fp["entries"])
            fp["n_residual"] = sum(
                1 for e in fp["entries"] if e["identification"] == "residual"
            )
            att["free_parameters"] = fp

    att["governance"]["attested_by"] = (
        "miso-65 outage-regen 2026-07-14: the miso-64 KEEPER recipe replayed "
        "VERBATIM (scripts/probes/_miso65_outage_regen.py — the miso-62 "
        "meta.json strict RENAME/SKIP replay + miso_rpe_pricing + "
        "unit_outage_short_windows + class_aware_fuel_price_fallback, all "
        "kept armed) with ZERO flag or parameter changes. The only delta is "
        "the regenerated measured input campd-unit-outages-MISO.csv (commit "
        "7b5c26fd): the committed >= 5-day unit-outage extract (PR #1820 "
        "vintage) did not reproduce from its own FROZEN deriver on the "
        "committed CAMPD unit-level parquets — re-running "
        "scripts/derive_campd_unit_outages.py --iso MISO --years 2023 2024 "
        "2025 (guards, constants and defaults untouched; the only deriver "
        "commit since #1820 is the purely-additive --short-windows mode) "
        "emits 1,655 windows the committed file lacked (2,924 -> 4,418 rows; "
        "+~1,550 GW-days in EACH of 2023/2024/2025), among them seven "
        ">= 5-day July-2025 North coal sustained full stops at span-CF < "
        "0.002 (Ottumwa 1, Gibson 3, Labadie 2, Baldwin 2, Cayuga 1/2, "
        "Sioux 1) that the full-stop override keeps unconditionally. July "
        "North-coal outage coverage rises 2.75 -> 4.00 GW mean (2023 5.32 -> "
        "7.03, 2024 4.63 -> 6.26); verified disjoint from the short-window "
        "companion file (0 same-unit overlaps). Lane 3 "
        "(docs/FINDING-miso-lane3-north-supply-2026-07.md): the stale "
        "extract left the model's July North coal shelf ~1.3-1.7 GW too "
        "deep in every backcast year — the phantom depth that kept the "
        "S->N corridor from separating."
    )
    att["governance"]["note"] = (
        "Lane 3 (North supply-curve depth / N-S separation). NOT a mechanism "
        "change and NOT a re-derivation of any measured-behaviour parameter "
        "(rule 23 untouched: no guard, constant, or detector default moved) "
        "— a reproducibility fix that makes a committed measured artifact "
        "byte-reproduce from its own frozen generator + committed source "
        "data, the caiso-78/nyiso-62/neiso-59 re-gate family (rule 14/15: "
        "the corrected extract is strictly more accurate measured "
        "availability truth; keeping the stale file would bury real outages "
        "inside phantom capacity). LOYO (rule 22): exempt by the same "
        "precedent — a year-invariant input regeneration with zero fitted "
        "parameters (the windows are each unit's own CEMS record; coverage "
        "rises comparably in all three years, not selectively in the "
        "studied one)."
    )
    if ablate:
        att["governance"]["note"] += (
            " ZERO-FORCING ABLATION TWIN of 2026-07-14-miso-65-outage-regen "
            "(rule 20): merchant floors off — including "
            "st_gas_mustrun_per_plant (MECH_ABLATION_FIELDS) — structural "
            "mechanisms kept: the topology split, RDT TCDC + RPE violation "
            "pricing, the committed take-or-pay / warm-boiler offer pricing, "
            "the outage overlays (incl. the short-window channel and the "
            "regenerated >= 5-day extract) and the class-aware fuel-price "
            "donor are offer structure / pricing / availability inputs, not "
            "floors, and stay armed."
        )

    att["disclosures"]["note"] = (
        "PENDING SCORE (filled by the registration step; see metrics.json "
        "determination + reasons)."
    )

    dst.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {dst}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
