"""Emit the nyiso-142 arm's ``calibration_attestation.json`` (C6 governance gate).

The nyiso-142 arm is the incumbent keeper's recipe re-solved on the CORRECTED
Astoria intake (``campd.CAMPD_STACK_DUPLICATE_UNITS`` live + the 18 repaired
``plant_emission_rates_v2`` rows). It adds **no mechanism and no free
parameter**, so its attestation is the incumbent's — lineage, DOF ledger and
C3c ledger entries all carried forward — with three things updated:

1. ``governance.attested_by`` / ``note`` / ``residuals_note`` — what this run is
   and why the correction stands independently of its effect on the residual;
2. the three ``price_tail`` exception ``magnitude`` strings, RE-MEASURED on this
   bundle (the C3c model/actual hour counts, passed in from
   ``scripts/calibration_verdict.py``'s own output so the two can never drift);
3. ``config_drift_vs_incumbent`` — which for this run records that the drift is
   **ZERO** scenario_config fields, because the delta is a data correction.

THE GENERATOR IS THE SOURCE OF TRUTH (the convention the incumbent's own
attestation states): editing the emitted JSON by hand is reverted by the next
run of this script.

Usage:
    python scripts/gen_nyiso142_attestation.py \\
        --bundle results/calibration/nyiso142_stackdup \\
        --c3c 2023=21/10 2024=3/13 2025=24/42
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
INCUMBENT = REPO / "results" / "calibration" / "nyiso140_exclusion_arm"

_ATTESTED_BY = "nyiso-142 arm (Astoria CAMPD stack-duplication data correction)"

_NOTE = (
    "DATA CORRECTION, ZERO NEW DEGREES OF FREEDOM (rule 21 [R-DOF]) AND ZERO "
    "CONFIG DRIFT. This run is the incumbent keeper's own recipe re-solved on a "
    "corrected CAMPD intake; no ScenarioConfig field moved, no mechanism was "
    "added, no coefficient was fitted. Astoria Generating Station (ORIS 8906, "
    "NYC) files units 30 and 50 as reheat/superheat pairs (31RH/32SH, "
    "51RH/52SH): one generating unit each, monitored on two flue paths, whose "
    "FULL grossLoad CAMPD repeats on both rows while SPLITTING heat input and "
    "the emission masses. Identified at nyiso-141 on THREE INDEPENDENT CHANNELS, "
    "none of them a residual — INTERNAL (51RH/52SH grossLoad byte-identical in "
    "100.00 % of their 4,327 fired hours of 2025, max |diff| exactly 0.000, "
    "while heat splits ~50/50; the fleet's genuine twin-unit peaker banks reach "
    "the same output identity but each carries its OWN full heat input), "
    "PHYSICAL (5,172-5,512 Btu/kWh counted alone is impossible for a fired "
    "boiler; 10,436-10,764 counted once, matching its NYISO gas-steam peers), "
    "and EXTERNAL (EIA-923 net over CAMPD gross = 0.472/0.471 against a "
    "0.88-0.96 peer band, landing inside the band at 0.935/0.937 once the "
    "duplicate is dropped). Rule 14 [R-ACCURATE]: the accurate measurement is "
    "adopted because it is accurate. Rule 13 [R-MEASURED]: both corrected "
    "quantities are INPUTS with forward analogues — a plant's CEMS emission "
    "rate and a class's metered generation — never an outcome fed back to move "
    "a score. Rule 25 [R-ISO-SCOPE]: the identification scanned state NY only "
    "and the correction table carries ONE facility; the committed diff is "
    "Astoria-only (17 lines changed, every one keyed NYISO,8906)."
)

_RESIDUALS_NOTE = (
    "REPORTED, NOT FITTED — and the direction of the fit is explicitly NOT the "
    "argument. PREREG-nyiso141-astoria-stack-duplication-2026-08-17.md was "
    "written and committed BEFORE any solve and pre-committed to the honest "
    "headline that most of the 2025 movement would come from the TARGET moving "
    "rather than the model improving. THE BENCHMARK ITSELF CHANGES in this run: "
    "run_calibration_full._backfill_eia923_with_campd fired for Astoria in 2025 "
    "only (EIA-923 had not published the plant), so the scored 2025 ST_GAS "
    "actual carried the doubled 2.672 TWh where the corrected series gives "
    "~1.359. 2023 and 2024 used metered EIA-923 and do not move. GOVERNANCE "
    "CONSEQUENCE, stated against our own result: every NYISO run ever scored on "
    "2025 — this run's own incumbent included — was scored against an inflated "
    "ST_GAS target, so post-correction 2025 figures are NOT comparable to the "
    "committed ones across this change. WHAT IS NOT CLOSED: the correction "
    "accounts for roughly 35 % of the 2025 ST_GAS under-production and NONE of "
    "2023 or 2024. The remaining ~-2.4 TWh in 2025, the +2.26 TWh 2023 "
    "over-production and the CC-for-steam substitution all stay OPEN and remain "
    "the successor object (results/calibration/"
    "FINDING-nyiso142-incity-cc-outage-substitution-2026-08-17.md)."
)

_DRIFT_NOTE = (
    "ZERO differing scenario_config fields between this arm and its paired "
    "control 2026-08-17-nyiso-142-control, by construction: the correction is a "
    "row-identity fix in the data layer (campd.CAMPD_STACK_DUPLICATE_UNITS plus "
    "the 18 repaired plant_emission_rates_v2 rows) and has no flag. K1 as "
    "normally written is therefore INAPPLICABLE and was replaced ex ante, in the "
    "pre-registration, by a DIFF-SCOPE check: the only source difference is the "
    "stack-duplicate table and its call sites, and the only artifact difference "
    "is 17 changed CSV lines, all keyed NYISO,8906."
)


def _parse_c3c(items: list[str]) -> dict[int, tuple[int, int]]:
    """Parse ``YEAR=MODEL/ACTUAL`` hour counts from the verdict's own output."""
    out: dict[int, tuple[int, int]] = {}
    for item in items:
        year, _, counts = item.partition("=")
        model, _, actual = counts.partition("/")
        out[int(year)] = (int(model), int(actual))
    return out


def build(bundle: Path, c3c: dict[int, tuple[int, int]]) -> dict:
    """Return the arm's attestation, derived from the incumbent's."""
    att = json.loads((INCUMBENT / "calibration_attestation.json").read_text())

    att["governance"]["attested_by"] = _ATTESTED_BY
    att["governance"]["note"] = _NOTE
    att["governance"]["residuals_note"] = _RESIDUALS_NOTE

    for exc in att.get("exceptions", []):
        year = int(exc.get("year", 0))
        if exc.get("criterion") != "price_tail" or year not in c3c:
            continue
        model, actual = c3c[year]
        ratio = (model / actual) if actual else float("nan")
        prior = str(exc.get("magnitude", ""))
        exc["magnitude"] = (
            f"RE-MEASURED on this bundle (nyiso-142 treatment): model {model} h "
            f"> $300/MWh against RT actual {actual} h ({ratio:.2f}x). "
            f"Prior keeper magnitude, lineage only: {prior}"
        )
        exc.setdefault(
            "carried_from",
            "2026-08-16-nyiso-140-layup-exclusion (NYISO ledger, nyiso-100 onward)",
        )
        exc["benchmark_basis_note"] = (
            "The RT ACTUAL side of this criterion is unaffected by the Astoria "
            "correction: C3c scores against the hub LMP series "
            "(actual_lmp_hourly_NYISO), not against the generation benchmark the "
            "correction moves. Any change in the model count is a dispatch "
            "change, not a target change."
        )

    att["config_drift_vs_incumbent"] = {
        "note": _DRIFT_NOTE,
        "differing_fields": [],
        "prior": att.get("config_drift_vs_incumbent", {}).get("prior", {}),
    }
    fp = att.get("free_parameters", {})
    fp["seeded"] = (
        "CARRIED UNCHANGED from 2026-08-16-nyiso-140-layup-exclusion. A data "
        "correction adds no free parameter: n_entries and n_residual are both "
        f"unchanged (n_entries {fp.get('n_entries')}, n_residual "
        f"{fp.get('n_residual')})."
    )
    att["free_parameters"] = fp
    att["_open_items"] = [
        "SUCCESSOR, still open: after this correction ~-2.4 TWh of 2025 downstate "
        "ST_GAS under-production and +2.26 TWh of 2023 over-production remain. "
        "nyiso-142 localises the 2025 half to New York City and refutes both the "
        "availability-plumbing and the Ravenswood-override readings; the "
        "discriminating measurement is the model's Zone-J energy balance. See "
        "FINDING-nyiso142-incity-cc-outage-substitution-2026-08-17.md.",
        "ARTIFACT-LIFECYCLE HAZARD, pre-existing and disclosed rather than fixed: "
        "plant_emission_rates_v2.parquet cannot be re-derived on the default path "
        "without destroying its 2018 rows (2018 is no longer built by "
        "regenerate_clean) and its 2022/2026 holdout-intake rows (unrepeatable by "
        "construction). This run used the surgical route "
        "(scripts/data/repair_v2_stack_duplicate_rows.py), validated MATCH against "
        "the freshly curated emissions-unit-annual for every year the clean tree "
        "can still build (2019/2020/2021/2023/2024/2025).",
        *att.get("_open_items", []),
    ]
    return att


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True, type=Path)
    ap.add_argument(
        "--c3c",
        nargs="+",
        required=True,
        metavar="YEAR=MODEL/ACTUAL",
        help="C3c hour counts as reported by scripts/calibration_verdict.py",
    )
    args = ap.parse_args(argv)

    att = build(args.bundle, _parse_c3c(args.c3c))
    out = args.bundle / "calibration_attestation.json"
    out.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
