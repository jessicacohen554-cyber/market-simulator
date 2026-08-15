"""Write ``calibration_attestation.json`` for the ercot-159 A/B arms.

The arm is the single delta ``ercot_energy_online_capability_cap=true`` on the
ercot158 keeper — the ERCOT-155 named successor (queue item 9), the measured
online-capability ceiling on the slow-start energy stack
(``docs/PRECOMMIT-ercot159-energy-online-capability-cap-2026-08-04.md``).
This script builds the C6 attestation both bundles need (rule 21 ``[R-DOF]``),
inheriting the ercot158 keeper's ledger and adding ONE entry for the delta on
the arm.

**The delta adds ZERO free parameters.** The ceiling is the per-cell MAX of
the measured fast-tier online capability (slow-fossil + nuclear online HSL +
quick-start online headroom) over (season × hour-block × net-load bin) cells,
derived from the full-year delivery-2023 60-Day SCED corpus. The statistic
and grain were fixed a priori in the pushed precommit BEFORE either arm
solved; there is no deliverability coefficient, no margin, no offset
(rule 20), and the artifact freezes against residuals (rule 23).

The **control** arm (Run A) inherits the keeper's attestation verbatim except
for its own ``attested_by`` line.

Every quantitative claim in the generated prose is READ FROM the committed
JSONs (the envelope artifact always; ``_ercot159_cap_ab.json`` when it exists
— rerun this script after the scorer to enrich the prose), never
hand-transcribed.

Usage:
    PYTHONPATH=.:src .venv/bin/python scripts/gen_ercot159_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
PRIOR_KEEPER = (
    REPO / "results/calibration/ercot158_poolarm_B/calibration_attestation.json"
)
CAP_ARTIFACT = (
    REPO / "data/raw/_validation-source/ercot_energy_online_capability_condbinned.json"
)
AB_JSON = REPO / "results/calibration/_ercot159_cap_ab.json"
ARM_DEST = REPO / "results/calibration/ercot159_cap_B/calibration_attestation.json"
CONTROL_DEST = (
    REPO / "results/calibration/ercot159_control_A/calibration_attestation.json"
)

YEARS = ("2023", "2024", "2025")

NEW_ENTRY_NAME = (
    "ercot_energy_online_capability_cap (ERCOT-159, queue item 9 / ERCOT-155 "
    "named successor) — the measured conditional online-capability ENVELOPE "
    "on the fast tier: Σ P(gas_cc/gas_st/coal/nuclear) + Σ R(RegUp/RRS/ECRS) "
    "≤ per-cell MAX of slow-fossil + nuclear online HSL + quick-start online "
    "headroom, (season × hour-block × net-load-percentile bin) grain, on the "
    "EXISTING ReserveDesign.online_capacity_cap row block"
)


def _build_entry(art: dict, ab: dict | None) -> dict:
    """Assemble the DOF entry, reading every number from the committed JSONs."""
    blk = art["2023"]
    prov = art["_provenance"]
    val = prov["validation"]
    measured_effect = (
        f"Envelope artifact (frozen, year-scoped): {blk['n_cells']} cells over "
        f"{blk['n_hours_covered']} measured 2023 hours; evening OLC mean "
        f"{blk['olc_gw_evening_mean']} GW. Cross-year sample-day validation "
        f"(never gating): 2024 p50 OLC/envelope "
        f"{val['sample_day_check_2024']['olc_over_2023_envelope_p50']}, 2025 "
        f"{val['sample_day_check_2025']['olc_over_2023_envelope_p50']}; "
        f"rtolhsl system closure residue "
        f"{val['rtolhsl_closure_2023']['residue_gw_mean']} GW mean (hydro/PUN/"
        "other, the components the object correctly excludes)."
    )
    if ab is not None:
        g = ab["e89_gates"]
        c3a = [
            f"{g[y]['base']['resid_pct']:+.1f}%→{g[y]['probe']['resid_pct']:+.1f}%"
            for y in YEARS
        ]
        a23 = ab["c3c_anatomy"]["2023"].get("phase0_rederived", {})
        bit = ab.get("bit_identity_2024_2025", {})
        measured_effect += (
            f" Measured A/B effect (committed _ercot159_cap_ab.json): C3a "
            f"{' / '.join(c3a)} (2023/24/25); matched-hour 2023 missed-set "
            f"model mean ${a23.get('missed_model_mean_A', float('nan')):.0f}→"
            f"${a23.get('missed_model_mean_B', float('nan')):.0f} vs actual "
            f"${a23.get('missed_actual_mean', float('nan')):.0f}, "
            f"{a23.get('missed_flipped_to_tail_B', 0)} of "
            f"{a23.get('missed_A', 0)} missed hours flipped to tail; 2024/2025 "
            f"bit-identity {'CONFIRMED' if all(b.get('bit_identical') for b in bit.values()) else 'BROKEN'}; "
            f"kills fired: {ab.get('kills_fired') or 'none'}."
        )
    return {
        "name": NEW_ENTRY_NAME,
        "where": (
            "run_config.scenario_config.ercot_energy_online_capability_cap "
            "(+ ercot_energy_online_capability_cap_path default "
            "data/raw/_validation-source/ercot_energy_online_capability_condbinned.json)"
        ),
        "identification": "measured/published",
        "lineage_solves": "1 (ercot-159 arm B, against the same-HEAD zero-delta control A)",
        "value": {
            "n_cells_2023": blk["n_cells"],
            "n_hours_covered_2023": blk["n_hours_covered"],
            "olc_gw_evening_mean_2023": blk["olc_gw_evening_mean"],
            "grain": prov["grain"],
        },
        "source": (
            "scripts/data/derive_ercot_energy_online_capability.py over the "
            "full-year delivery-2023 NP3-965 60-Day SCED Gen Resource corpus "
            "(data/raw/ercot/SCED, 315 shards, all 365 delivery days — "
            "ERCOT-157), ERCOT-155 census taxonomy verbatim (online states, "
            "thermal types, CPT→CST clock); driver = EIA-930 net-load "
            "percentile rank (the standing wall driver). The per-hour "
            "telemetered online series BUILDS and VALIDATES the conditional "
            "object and never ships raw (rule 13, ERCOT-89 §6 bright line); "
            "2024/2025 sample-day extracts and the committed rtolhsl series "
            "are validators only."
        ),
        "free_parameters_added": 0,
        "why_zero": (
            "The statistic (per-cell MAX — envelope semantics: 'more than "
            "this was never mustered at these conditions') and the grain "
            "(4 seasons × 6 hour-blocks × 14 net-load bins, the ercot43 "
            "extreme-tail resolution) were fixed a priori in the pushed "
            "precommit BEFORE either arm solved, with the Phase-0 variant "
            "table disclosed in full (precommit §5). No deliverability "
            "coefficient, no margin, no offset exists between the corpus "
            "and the LP row (the rejected ercot41/43 envelope family's "
            "fitted deliv coefficient is exactly what this construction "
            "does not have). Year-scoped by full-corpus coverage (2023 "
            "block only; 2024/2025 byte-inert — the shoulder-span "
            "precedent), so no pooled fallback and no cross-year fit. "
            "Rule 23: re-derives only on SCED/EIA-930/HSL/storage source "
            "updates."
        ),
        "rule_19_reconciliation": (
            "Enumerated in precommit §3 BEFORE the seam was written: the DAM "
            "availability lane owns OUTAGES (per-unit bounds; the envelope "
            "never tightens on outage days — cell max is the best-attained "
            "state); the commitment bridges own the LOWER bound (min-gen from "
            "capped P0 — composition through the existing P0→P1 seam); the "
            "reserve supply cap owns the RESERVE side (R ≤ RTOLCAP — the "
            "physically nested pair, tightest binds); the fast-start pool "
            "owns the offline-quick PRICE route (quick types excluded from "
            "this cap's LHS, netted on its RHS — the cap closes the phantom "
            "slow-online QUANTITY route the pool's inertness at ERCOT-158 "
            "exposed); NonSpin/all-tier stays sentinel so the ORDC total "
            "family's escape valve prevents the ercot41/43 span-inside-the-"
            "cap arithmetic. One writer per ReserveDesign field, enforced by "
            "ScenarioConfig.__post_init__ hard errors (envelope family + "
            "ercot_ordc_only_scarcity exclusions)."
        ),
        "rule_25_scope": (
            "ERCOT-only by construction: the provider reads an ERCOT-derived "
            "artifact behind an ercot_* flag consumed inside the ERCOT "
            "multiproduct reserve-spec builder; no other ISO's cell is "
            "touched (matrix row energy_online_capability_cap, other ISOs "
            "'.')."
        ),
        "measured_effect": measured_effect,
    }


def _attested_by(ab: dict | None, arm: bool) -> str:
    """The C6 attestation prose for one arm, from the committed JSONs."""
    if ab is None:
        ab_line = (
            "The A/B scorer has not yet run; this attestation precedes the "
            "verdict so C6 can score, and is regenerated with the measured "
            "gate numbers once results/calibration/_ercot159_cap_ab.json is "
            "committed."
        )
    else:
        g = ab["e89_gates"]
        c3a = " / ".join(
            f"{g[y]['base']['resid_pct']:+.1f}%->{g[y]['probe']['resid_pct']:+.1f}%"
            for y in YEARS
        )
        ab_line = (
            f"Measured A/B (committed _ercot159_cap_ab.json): C3a {c3a} "
            f"(2023/24/25); kills fired: {ab.get('kills_fired') or 'none'}; "
            f"all pre-registered gates "
            f"{'HELD' if ab.get('all_gates_held') else 'NOT held'}."
        )
    if not arm:
        return (
            "ercot-159 2026-08-04 Run A — ZERO-DELTA CONTROL replay of the "
            "2026-08-03-ercot158-pool-arm keeper recipe (config UNCHANGED, "
            "meta.json kwargs replay, fresh out-dir, same HEAD — the ercot98 "
            "honest-inputs / ercot150-K2 drift-control pattern). This bundle "
            "carries the keeper's own recipe and therefore its DOF ledger "
            "unchanged; it is registered as the A/B base (rule 15), and any "
            "keeper-candidate standing is scored on its own rubric numbers, "
            "never assumed. " + ab_line
        )
    return (
        "ercot-159 2026-08-04 Run B — the 2026-08-03-ercot158-pool-arm recipe "
        "with ONE delta: ercot_energy_online_capability_cap=true (queue item "
        "9, the ERCOT-155 named successor; owner-authorized charter "
        "docs/PRECOMMIT-ercot159-energy-online-capability-cap-2026-08-04.md, "
        "pushed with the Phase-0 census and the A/B scorer BEFORE either arm "
        "solved). The mechanism installs the measured conditional envelope on "
        "the fast tier of the EXISTING online_capacity_cap row block; the "
        "REJECTED ercot41/43/106/108 envelope family is NOT re-opened "
        "(precommit §0 enumerates the four distinctions: direct measured "
        "identification with zero fitted scalars, fast-tier-only scope with "
        "the NonSpin/quick escape valves, the ex-ante Phase-0 bistability "
        "census, and the owner's conscious supersession of the ERCOT-89 "
        "§3(ii) no-cap line for this one mechanism). Zero fitted parameters "
        "added; n_residual unchanged. " + ab_line
    )


def main() -> int:
    """Write both arms' attestations from the keeper's + the committed JSONs."""
    keeper = json.loads(PRIOR_KEEPER.read_text())
    art = json.loads(CAP_ARTIFACT.read_text())
    ab = json.loads(AB_JSON.read_text()) if AB_JSON.exists() else None

    for dest, arm in ((CONTROL_DEST, False), (ARM_DEST, True)):
        if not dest.parent.exists():
            print(f"skip {dest.parent.name}: bundle not solved yet")
            continue
        att = json.loads(json.dumps(keeper))  # deep copy
        gov = att["governance"]
        for key in (
            "levers_trace_to_measured_input",
            "no_fit_to_price_residuals",
            "no_pinning_to_actuals",
            "outage_filter_exogenous_net_load",
        ):
            if gov.get(key) is not True:
                raise SystemExit(
                    f"keeper attestation assertion {key} is not true — refusing "
                    "to inherit a broken attestation"
                )
        gov["attested_by"] = _attested_by(ab, arm)
        if arm:
            fp = att["free_parameters"]
            fp["entries"] = list(fp["entries"]) + [_build_entry(art, ab)]
            fp["n_entries"] = int(fp["n_entries"]) + 1
            # n_residual unchanged: the added entry is measured/published.
        dest.write_text(json.dumps(att, indent=1) + "\n")
        led = json.loads(dest.read_text())["free_parameters"]
        print(
            f"wrote {dest.relative_to(REPO)} "
            f"(n_entries {led['n_entries']}, n_residual {led['n_residual']}, "
            f"ab_numbers={'yes' if ab is not None else 'PRELIMINARY'})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
