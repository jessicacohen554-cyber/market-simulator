"""Generate the miso-72 (KEEPER CANDIDATE) calibration_attestation.json pair.

Carries forward the miso-71 keeper attestation (governance clauses + the
hand-curated measured-physical rows build_dof_ledger does not enumerate) and
writes the run-specific text for the winter fuel-security Chicago Citygate
daily gas overlay (the fuel-security / gas_daily_shape lane) and its same-box
base replica.

Sequence (matches the miso-68/69/70/71 chain):

1. seed both bundles' ``calibration_attestation.json`` from the miso-71
   keeper attestation (``--seed``),
2. ``python scripts/build_dof_ledger.py <bundle> --iso MISO`` on BOTH bundles
   (rebuilds ``free_parameters`` from each bundle's own run_config — the main
   arm picks up the miso_winter_citygate_daily measured-physical entry
   -> 26 measured / 2 residual after the carried-row merge; the base arm stays
   25/2),
3. this script (merges back the carried rows + writes the texts).

Adjudication recorded here (2026-07-18 probe reads, main − same-box base; the
base reproduces the registered miso-71 keeper EXACTLY on every gated criterion
— zero box drift). Every pre-registered band of the frozen design
(docs/handoffs/miso-winter-fuel-security-design-2026-07.md §3.5/§3.6) HELD:
C3b 0.080/0.129/0.183 (mechanism-only Δ +0.001/+0.005/−0.001, at/inside the
≤ +0.005 band; all ≤ 0.20 veto — R1 held); C3c 1/7/1 IDENTICAL to base
(2024 inside the pre-declared [7,9]; the Heather event is off the Indiana
scoring hub exactly as pre-read); C3a-2024 −6.9 → −7.3 % (Δ −0.4, inside the
±0.5 watch); C1 CC_REGULAR-2023 −8.33 vs base −8.29 (0.04 TWh, noise);
C2/C4/C5a/C6/C7/C8 PASS both arms with the same ST_GAS grounded-above-budget
notes. R2 HELD: Heather-window max LMP $87.94, no $1000+ SETEX fabrication.
R4 HELD (not inert): the flow-date staircase places Jan-12's $25.82 print on
Jan-13-16 at 4.67×; Chicago-zone LMP lifts Jan-14/15/16 from ~$35-48 to
$50-65 against actuals $50-100. R5 HELD: C3c unchanged — no spurious gain.
THE DELIVERABLE (per-zone Heather-window |model − actual| mean LMP): improves
in EVERY zone with actuals — Illinois 12.75 → 0.89 $/MWh, East 28.13 → 14.49,
Indiana 45.33 → 31.68, West 45.33 → 31.69, South 42.53 → 36.91. Disclosed:
full-January MAE broadens ~+$2 in Indiana/East/West (the flat North/Central
zonal pool moves together under the redistribution days) while Illinois
improves 1.69 → 0.34 and South improves — the gated C3b shape metric moved
only +0.005/−0.001, inside its pre-registered band. KEEPER CANDIDATE — same
fail set as the keeper {C1 CC_REGULAR-2023, C3a-2025, C3c×3} with no gated
regression and one additional measured structure at zero fitted scalars
(rule 1). Keeper swap is owner-only.

Usage: python scripts/gen_miso72_attestation.py [--seed]  (after build_dof_ledger)
"""

import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC71 = REPO / "results/calibration/miso71_midwest/calibration_attestation.json"
MAIN = REPO / "results/calibration/miso72_winter_citygate"
BASE = REPO / "results/calibration/miso72_winter_citygate-base"

# Hand-curated measured-physical rows carried across the lineage (not
# enumerated by build_dof_ledger from config).
CARRIED = {
    "MISO COAL SOM near-cost offer floor",
    "COAL_SIGMOID_DEFAULTS[MISO]",
    "gas_daily_shape[MISO]",
    "hydro 2025 completeness (backfill 2024 + EIA-930 monthly repin)",
}

ATTESTED_MAIN = (
    "miso-72 winter fuel-security Chicago Citygate daily gas overlay "
    "2026-07-18 (KEEPER CANDIDATE, swap owner-only): the PROMOTED miso-71 "
    "keeper recipe (scripts/run_miso72_winter_probe.py — the miso71_midwest "
    "meta.json strict replay via replay_keeper.build_kwargs) plus ONE new "
    "mechanism through the generic prb_overrides channel: "
    "miso_winter_citygate_daily = True. In the winter months {Dec, Jan, Feb} "
    "only, the MISO gas units in the Chicago-hub zones only (MISO-Illinois/"
    "Indiana/East — READ from the published miso_zonal_gas_hub.csv, hub == "
    "'Chicago Citygate (IL)', the same file apply_miso_zonal_gas_basis reads) "
    "are repriced at the MEASURED Chicago Citygate daily shape "
    "(data/raw/gas-prices/miso_citygate_daily.csv — 680 weekday prints "
    "2023-2025 from the EIA Natural Gas Weekly Update spot table), placed on "
    "gas FLOW days (trade+1, weekend/holiday forward-fill — Friday Jan-12-2024 "
    "$25.82 prices the whole MLK storm package Jan-13-16) and renormalized to "
    "mean 1.0 within each month, SUPERSEDING the national-HH gas_daily_shape "
    "in exactly those cells (divide-out/multiply-in — replace, never stack, "
    "rule 19). The monthly gas level (measured EIA-923, already correct) and "
    "the additive annual miso_zonal_gas_basis spread are UNCHANGED by "
    "construction (mean-preserving within month; overlay runs BEFORE the "
    "zonal basis). Closes the Winter Storm Heather (Jan-14-17-2024) "
    "delivered-gas tail the national shape structurally misses: HH's even-"
    "spread interp mislocates the Jan-12 spike to Jan-13 and the Chicago "
    "citygate basis blowout (+$12.74 over HH on the Friday print) never "
    "appears in a national series. ZERO fitted scalars: the series is "
    "measured, the zone set is the published hub assignment, the winter "
    "window and flow-date convention are market structure. Design FROZEN "
    "before the build: docs/handoffs/miso-winter-fuel-security-design-"
    "2026-07.md (diagnosis, mechanism, bands §3.5, R1-R5 §3.6 all "
    "pre-registered; reserve-scarcity and cold-snap-derate routes "
    "pre-adjudicated REFUTED by the 2024 SOM record and NOT built)."
)

NOTE_MAIN = (
    "Winter fuel-security Chicago Citygate daily overlay — KEEPER CANDIDATE "
    "(mechanism-only read = main minus a same-box unchanged-keeper-recipe "
    "base replica; the base reproduces the registered miso-71 keeper EXACTLY "
    "on every gated criterion — zero box drift). EVERY pre-registered band "
    "of the frozen design HELD. R1 (C3b veto) HELD: C3b 0.080/0.129/0.183 "
    "(mechanism-only Δ +0.001/+0.005/−0.001 — at/inside the ≤ +0.005 band; "
    "all years ≤ 0.20). C3c 1/7/1 IDENTICAL to base (2024 inside the "
    "pre-declared [7,9] band): the Heather event is off the Indiana scoring "
    "hub exactly as pre-read (~1 in-window tail hour; 2 of 37 annual 2024 "
    "tail hours are in January) — the design pre-declared C3c must NOT be "
    "the validation and it was not. THE DELIVERABLE — per-zone Heather-"
    "window (Jan-14-17-2024) mean-LMP fidelity — IMPROVES IN EVERY ZONE "
    "with actuals: Illinois |model−actual| 12.75 → 0.89 $/MWh, East 28.13 → "
    "14.49, Indiana 45.33 → 31.68, West 45.33 → 31.69, South 42.53 → 36.91. "
    "R2 (SETEX fabrication) HELD: Heather-window max LMP $87.94 across all "
    "zones — nowhere near the out-of-representation TEXAS.HUB $1070 print "
    "(never chased, rule 13). R3 (no double-count) HELD: off-state LP byte "
    "identity unit-tested; the covered-cell supersession of gas_daily_shape "
    "and non-perturbation of miso_zonal_gas_basis are construction "
    "properties with dedicated tests. R4 (inertness) HELD — NOT inert: the "
    "flow-date staircase places the Jan-12 $25.82 Friday print on flow days "
    "Jan-13-16 at 4.67×; Chicago-zone daily LMP lifts Jan-14/15/16 from "
    "$47.9/39.5/35.1 to $64.9/64.1/50.6 against actuals (Indiana "
    "$78.7/100.0/84.5). R5 (honesty) HELD: C3c unchanged — no spurious "
    "scored gain; the per-zone read IS the validation. C3a-2024 −6.9 → "
    "−7.3 % (Δ −0.4, inside the ±0.5 watch band; still PASS); C3a-2025 "
    "−13.7 % IDENTICAL (not this lane's lever); C1 CC_REGULAR-2023 −8.33 vs "
    "base −8.29 TWh (0.04 TWh, noise; unchanged watch); C2/C4/C5a PASS both "
    "arms; C6/C7/C8 PASS with the same ST_GAS grounded-above-budget notes "
    "(NO new floors — a fuel-price shape carries no floor-mechanism id; "
    "D-2/D-4 regen adds no row and the fail set is byte-identical to the "
    "keeper's). DISCLOSED (sub-band, non-gated): full-January MAE broadens "
    "~+$2 in Indiana/East/West — the reduced network's North/Central zones "
    "are price-uniform, so the Chicago shape moves the whole pool on "
    "redistribution days — while Illinois improves 1.69 → 0.34 and South "
    "improves; the gated C3b shape deltas stayed inside their pre-registered "
    "band, and resolving per-zone winter gas within North/Central needs the "
    "West/Panhandle-style topology split (its own charter, not this lane). "
    "DOF main 26/2, base 25/2 (+1 measured-physical: the Chicago Citygate "
    "daily series — zero new fitted scalars). KEEPER CASE (rule 1): the fail "
    "set is EXACTLY the keeper's {C1 CC_REGULAR-2023, C3a-2025, C3c×3} with "
    "no gated regression, and ONE additional real structure at zero fitted "
    "scalars — the measured regional delivered-gas winter shape the national "
    "series cannot represent. A more structurally faithful run with no "
    "criterion regression is the keeper definition — recommendation to the "
    "owner; swap is owner-only. No zero-forcing ablation twin (rule 20 as "
    "amended 2026-07-14)."
)

ATTESTED_BASE = (
    "miso-72 base 2026-07-18 (PROBE drift control): unchanged miso-71 keeper "
    "recipe (miso71_midwest meta.json strict replay via "
    "replay_keeper.build_kwargs, NO override), solved same-box so the "
    "mechanism-only footprint of the paired main run is main - base, never "
    "main - the registered bundle. Reproduces the registered miso-71 keeper "
    "EXACTLY on every gated criterion (C1 CC_REGULAR-2023 −8.29, C3a-2025 "
    "−13.7%, C3b 0.079/0.124/0.184 PASS, C3c 1/7/1 vs RT 30/37/88) — zero "
    "box drift, which certifies the paired mechanism-only read."
)

NOTE_BASE = (
    "Same-box unchanged-recipe drift control for the miso-72 winter "
    "fuel-security Chicago Citygate daily overlay probe (the miso-66 drift "
    "lesson: mechanism-only = probe - base, never probe - registered). Not a "
    "keeper candidate; registered per rule 15 so the paired read is "
    "reproducible from the dashboard."
)


def _finish(dst_dir: Path, attested_by: str, note: str) -> None:
    """Merge carried rows into the ledger-rebuilt attestation + write texts."""
    dst = dst_dir / "calibration_attestation.json"
    att = json.loads(dst.read_text())
    src = json.loads(SRC71.read_text())
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
    """Copy the miso-71 keeper attestation into both bundles (step 1)."""
    for d in (MAIN, BASE):
        shutil.copy(SRC71, d / "calibration_attestation.json")
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
