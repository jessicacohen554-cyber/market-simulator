"""Generate the miso-69 (REJECTED PROBE) calibration_attestation.json pair.

Carries forward the miso-68 keeper attestation (governance clauses + the
hand-curated measured-physical rows build_dof_ledger does not enumerate) and
rewrites the run-specific text for the M-2 declared-event-window revealed
derates probe and its same-box base replica.

Sequence (matches the miso-68 chain):

1. seed both bundles' ``calibration_attestation.json`` from the miso-68
   keeper attestation (this script does the copy),
2. ``python scripts/build_dof_ledger.py <bundle> --iso MISO`` on BOTH bundles
   (rebuilds ``free_parameters`` from each bundle's own run_config — the main
   arm picks up the two new measured-physical maxgen entries -> 23 measured /
   2 residual on the miso-68 21/2 base; the base arm stays 21/2),
3. this script (merges back the carried rows + writes the texts).

Adjudication recorded here (2026-07-16 probe reads, main − same-box base):
REJECTED PROBE — C3b-2024 NRMSE 0.124 -> 0.203 breaches the 0.20 shape veto
(a 6-hour ~$1,841-1,985/MWh block inside the declared Aug-26-2024 Warning
window vs actual DA peak $169), C3a-2025 −14.3% -> −13.7% (target band
−6..−9% missed), C3c-2025 0h -> 1h (band [19,76] missed — F5 trigger). The
mechanism (measured availability truth) stays built and gated default-off;
what the probe refutes is the model's price-formation DEPTH response, not
the measurement.

Usage: python scripts/archive/gen_miso69_attestation.py   (after build_dof_ledger)
"""

import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC68 = (
    REPO
    / "results/calibration/miso68_cottonwood_mothballs/calibration_attestation.json"
)
MAIN = REPO / "results/calibration/miso69_maxgen_derates"
BASE = REPO / "results/calibration/miso69_maxgen_derates-base"

# Hand-curated measured-physical rows carried across the lineage (not
# enumerated by build_dof_ledger from config).
CARRIED = {
    "MISO COAL SOM near-cost offer floor",
    "COAL_SIGMOID_DEFAULTS[MISO]",
    "gas_daily_shape[MISO]",
    "hydro 2025 completeness (backfill 2024 + EIA-930 monthly repin)",
}

ATTESTED_MAIN = (
    "miso-69 declared-event-window revealed derates 2026-07-16 (REJECTED "
    "PROBE): the miso-68 keeper recipe (scripts/probes/_miso69_maxgen_"
    "derates.py — the miso68_cottonwood_mothballs meta.json strict replay "
    "via replay_keeper.build_kwargs) with ONE single-delta override through "
    "the generic prb_overrides channel: unit_outage_maxgen_events = True. "
    "The gate applies CAMPD revealed unit derates INSIDE the ISO's declared "
    "capacity-emergency windows only (maxgen-events registry, 8 qualifying "
    "windows -> 5 event blocks 2023-2025), under the frozen M-2 guards "
    "(declared-window scope clipped to the declared start/end; $150 DA "
    "in-merit certificate, region-scoped hubs; ±45-day capability basis "
    "with best-event-hour credit; disjointness vs the std/short extracts "
    "asserted; no control-day screen). Class-agnostic — the only channel "
    "that can carry the measured CT/CC event-window leg. ZERO fitted "
    "scalars: every number is a declared instrument, a measured price "
    "certificate, or a measured CAMPD capability. Design: docs/handoffs/"
    "miso-price-formation-design-2026-07.md §3/M-2 + docs/handoffs/"
    "miso-maxgen-registry-findings-2026-07.md."
)

NOTE_MAIN = (
    "M-2 declared-event-window revealed derates — REJECTED PROBE "
    "(mechanism-only read = main minus a same-box unchanged-recipe base "
    "replica; the base reproduces the registered miso-68 keeper EXACTLY on "
    "every gated criterion — zero box drift). THE BREACH: C3b-2024 price-"
    "duration NRMSE 0.124 -> 0.203 (> 0.20 veto) — the Aug-26-2024 Max Gen "
    "Warning block (10.67 GW derated, the largest of the five blocks "
    "because its declared window is only 7 hours, so best-event-hour credit "
    "has the least chance to engage) drives the model into the zonal-ORDC "
    "deep steps for 6 straight hours (~$1,841-1,985/MWh) where the actual "
    "DA record peaked $169 (Tier-0/1 emergency pricing ~+$60). The same "
    "overshoot 'improves' C3a-2024 (-8.0% -> -2.0%) — a wrong-shaped gain "
    "the shape veto correctly rejects (rule 1: never reach the right "
    "number through prices 10x the actual). MEANWHILE the deep 2025 events "
    "under-engage: Jun-23/24 (2.99 GW, Midwest-scoped) peaks $196.7, "
    "Jul-28/29 (7.41 GW) prints ONE hour $248, Jul-24 (10.59 GW) moves "
    "nothing — C3c-2025 0h -> 1h vs the [19,76] pre-registered band and RT "
    "actual 88h (F5 TRIGGERED: the phantom-headroom hypothesis is refuted "
    "at current depth). C3a-2025 -14.3% -> -13.7% (band -6..-9% missed). "
    "Every protective read held: C3b-2025 mechanism-only -0.009 (improved; "
    "the F2 2025-composition veto was NOT the breach), C3b-2023 0.081 -> "
    "0.079, C1 CC_REGULAR-2023 -8.28 -> -8.29 (watch unchanged), max class "
    "energy move 0.12 TWh (<= 0.5 watch), C2/C4/C5a PASS both arms, RDT "
    "S->N flows byte-identical, C7/C8 unchanged (no new floors — the "
    "channel is an availability derate with no floor-mechanism id; its "
    "rule-12 window declaration is the registry window set itself, "
    "off-window derates structurally impossible). THE STRUCTURAL FINDING "
    "the two-sided miss exposes: MISO's declared-window prices are formed "
    "by ELMP emergency-pricing TIERS (Alert = 4-h online resources "
    "price-set; Warning = Tier 1 $500/MWh offer floor; Step 2 = Tier 2 + "
    "LMRs — 2023 SOM p.10, 2025 SOM fn.17), i.e. bounded tier pricing, NOT "
    "pure headroom exhaustion — so removing measured headroom either does "
    "nothing (2025: slack elsewhere in the model stack) or explodes to the "
    "$1,100/$3,300 ORDC steps (2024: a shallow $169 warning priced at "
    "$1,900). That tier treatment is the F5 scarcity-depth charter's "
    "measured basis (registry-findings memo §5); it is NOT built in this "
    "lane (rule 19 — one mechanism per phenomenon, and rule 25 — never an "
    "ERCOT/NYISO analogue import). The maxgen extract and the gated "
    "default-off channel remain in the codebase as measured structure "
    "(rule 1); the keeper recipe does NOT arm it. No zero-forcing ablation "
    "twin (rule 20 as amended 2026-07-14)."
)

ATTESTED_BASE = (
    "miso-69 base 2026-07-16 (PROBE drift control): unchanged miso-68 "
    "keeper recipe (miso68_cottonwood_mothballs meta.json strict replay via "
    "replay_keeper.build_kwargs, NO override), solved same-box so the "
    "mechanism-only footprint of the paired main run is main - base, never "
    "main - the registered bundle. Reproduces the registered miso-68 keeper "
    "EXACTLY on every gated criterion (C1 CC_REGULAR-2023 -8.28, C3a-2025 "
    "-14.3%, C3b 0.081/0.124/0.193 PASS, C3c 0/4/0 vs RT 30/37/88) — zero "
    "box drift."
)

NOTE_BASE = (
    "Same-box unchanged-recipe drift control for the miso-69 M-2 probe "
    "(the miso-66 drift lesson: mechanism-only = probe - base, never "
    "probe - registered). Not a keeper candidate; registered per rule 15 "
    "so the paired read is reproducible from the dashboard."
)


def _finish(dst_dir: Path, attested_by: str, note: str) -> None:
    """Merge carried rows into the ledger-rebuilt attestation + write texts."""
    dst = dst_dir / "calibration_attestation.json"
    att = json.loads(dst.read_text())
    src = json.loads(SRC68.read_text())
    fp = att.get("free_parameters")
    if fp:
        have = {e["name"] for e in fp["entries"]}
        for e in src["free_parameters"]["entries"]:
            if e["name"] in CARRIED and e["name"] not in have:
                fp["entries"].append(e)
        fp["n_entries"] = len(fp["entries"])
        fp["n_residual"] = sum(
            1 for e in fp["entries"] if e["identification"] == "residual"
        )
        att["free_parameters"] = fp
    att["governance"]["attested_by"] = attested_by
    att["governance"]["note"] = note
    att["disclosures"]["note"] = (
        "PENDING SCORE (filled by the registration step; see metrics.json "
        "determination + reasons)."
    )
    dst.write_text(json.dumps(att, indent=1) + "\n")
    fpn = att.get("free_parameters", {})
    print(
        f"wrote {dst}  (ledger {fpn.get('n_entries', '?')} entries / "
        f"{fpn.get('n_residual', '?')} residual)"
    )


def seed() -> None:
    """Copy the miso-68 keeper attestation into both bundles (step 1)."""
    for d in (MAIN, BASE):
        shutil.copy(SRC68, d / "calibration_attestation.json")
        print(f"seeded {d / 'calibration_attestation.json'}")


def main() -> None:
    import sys

    if "--seed" in sys.argv:
        seed()
        return
    _finish(MAIN, ATTESTED_MAIN, NOTE_MAIN)
    _finish(BASE, ATTESTED_BASE, NOTE_BASE)


if __name__ == "__main__":
    main()
