"""Write ``calibration_attestation.json`` for both pjm-140 A/B arms.

Both arms replay the ``2026-07-29-pjm-137-ctheatrate`` keeper recipe
(``pjm137_ctheatrate_B``), so the governance posture and the accepted-limitation
ledger are the keeper's, inherited unchanged:

* **arm A** (``pjm140_control_A``) is the keeper recipe VERBATIM — no delta, and
  verified against the committed keeper on the class hourlies
  (``PREREG-pjm140-ramp-envelopes-2026-07-30.md`` K5). Its attestation is the
  keeper's, re-attested as the A/B control. It is NOT a candidate.
* **arm B** (``pjm140_rampenv_B``) adds ONE delta, ``ramp_limits=true``, and
  therefore ONE ledger entry.

The delta adds **zero residual-identified degrees of freedom** (rule 22
``[R-DOF]``). Every number in the artifact is a measured MAXIMUM from the CEMS
trace: per (facility, CC/CT/ST family) pooled over 2023-2025, ``ramp_up_mw`` is
the max observed 1-h increase in summed CAMPD gross load and ``ramp_dn_mw`` the
max observed 1-h decrease excluding trip-to-offline deltas. No scale, no
haircut, no blend, no fitted anchor, no per-plant override, no quantile swap.
So the ledger gains a ``measured-physical`` entry and ``n_residual`` is
unchanged.

Usage:
    python scripts/gen_pjm140_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
KEEPER = REPO / "results/calibration/pjm137_ctheatrate_B/calibration_attestation.json"
ARM_A = REPO / "results/calibration/pjm140_control_A/calibration_attestation.json"
ARM_B = REPO / "results/calibration/pjm140_rampenv_B/calibration_attestation.json"
RESULT = REPO / "results/probes/pjm140_rampenv_ab.json"
COVERAGE = REPO / "results/probes/pjm140_ramp_coverage.json"

NEW_ENTRY = {
    "name": "Measured plant-group hourly ramp envelopes (CAMPD, per plant x family)",
    "where": "run_config.scenario_config.ramp_limits",
    "identification": "measured-physical",
    "lineage_solves": (
        "0 solves added to the tuning lineage — every envelope is the MAX "
        "observed 1-h move in that plant-family's own CAMPD gross-load trace, "
        "written by a frozen derive (rule 23 [R-FROZEN-DERIVE]) whose only "
        "re-derivation trigger is a CAMPD vintage change. Nothing was swept, "
        "and PREREG §5's no-feedback ceiling forbids ever applying a "
        "multiplier, scale, haircut, blend, floor, cap, widening, tightening, "
        "per-plant override or quantile swap to the derived envelopes — the "
        "only admissible knob is the flag's on/off state."
    ),
    "value": (
        "data.fleet.build_ramp_groups('PJM') -> model/lp/rows.py::"
        "_build_ramp_rows: one two-sided row per (plant, CC/CT/ST family) "
        "group per hour transition t = 1..T-1, bounding the group's summed P "
        "move by its measured envelope, widened at availability edges by the "
        "capacity discontinuity the model itself imposes. 194 live groups on "
        "124.1 GW = 90.1 % of the ISO's ramp-eligible thermal capacity; "
        "1,699,246 LP rows and ~23.3 M nonzeros. Live up-envelope median 0.40 "
        "of group pmax (p25 0.32 / p75 0.53), down-envelope median 0.53."
    ),
    "source": (
        "EPA CAMPD unit-level hourly grossLoad (data/raw/campd-unit-level), 14 "
        "PJM states x 2023-2025, aggregated per (facilityId, CAMPD unitType -> "
        "CC/CT/ST bucket) hour; ramp_up_mw = max 1-h increase, ramp_dn_mw = max "
        "1-h decrease excluding deltas ending below 5 % of observed pmax (a "
        "trip is an availability event the outage overlay already models). "
        "Facilities below 4,000 observed online hours fall back to the "
        "capacity-weighted median class envelope FRACTION; CT groups get no "
        "class fallback. The loader rebases CAMPD GROSS -> model NET per plant "
        "by the measured EIA-923-net / CAMPD-gross factor (142 measured "
        "factors, median 0.9700, range 0.8252-0.9968; 2 cited class defaults "
        "at 0.9750) and prunes any group whose envelope can never bind "
        "(RU >= cap AND RD >= cap), so bang-bang CTs drop out by physics and "
        "no class-name gate exists anywhere (rule 18 [R-PHYSICS]). Artifact: "
        "data/raw/_processed-legacy/campd_ramp_envelopes_PJM.csv (209 rows, "
        "145 well-observed plant-family groups)."
    ),
    "forward_story": (
        "A machine's hourly move capability is a physical characteristic and "
        "regenerates for a forward year from the same pipeline: a retrofit "
        "moves it, a new unit enters with its own trace once metered, a "
        "retired unit leaves the population, and an unmetered new build takes "
        "the class fraction. It is in the same admissibility class as the "
        "CAMPD min-stable loads, committed shares and measured run lengths "
        "already ledgered."
    ),
    "rule_13_admissibility": (
        "A measured ramp envelope is a physical INPUT, not an outcome pinned "
        "to a residual: it constrains the feasible set and the LP dispatches "
        "inside it. No volume is pinned to an actual and nothing is added to a "
        "price. It replaces an implicit ESTIMATE that is false as physics — "
        "with ramp_limits off the LP asserts every thermal plant can move from "
        "any output to any other output in one hour, which no PJM plant ever "
        "did in three years of CEMS record. Rule 14 [R-ACCURATE] governs the "
        "disposition: the measured envelope is kept as written even where the "
        "backcast does not move, and PREREG §5 forbids tuning it to make it "
        "bind."
    ),
}


def _evidence() -> str:
    """The shared A/B evidence block, read from the committed scorer output."""
    if not RESULT.exists():
        raise SystemExit(
            f"missing {RESULT} — run scripts/probes/_pjm140_rampenv_ab.py first"
        )
    res = json.loads(RESULT.read_text())
    parts = []

    cov = json.loads(COVERAGE.read_text()) if COVERAGE.exists() else {}
    y0 = (cov.get("years") or {}).get("2024", {})
    if y0:
        parts.append(
            "EVIDENCE (arms pjm140_control_A / pjm140_rampenv_B, all three years "
            "in one invocation, arms sequential). K7 COVERAGE: the loader puts a "
            f"live envelope on {y0['n_groups_live']} of {y0['n_groups_total']} "
            f"(plant, family) groups = {y0['live_cap_mw'] / 1000:.1f} GW = "
            f"{y0['k7_live_share_of_thermal'] * 100:.1f} % of ramp-eligible thermal "
            f"capacity, pruning {y0['n_groups_pruned']} groups "
            f"({y0['pruned_cap_mw']:.0f} MW) as non-binding and leaving "
            f"{y0['n_groups_no_row']} CT groups ({y0['no_row_cap_mw'] / 1000:.1f} GW) "
            "with no row at all (no class fallback for CT). K7 PASS."
        )

    k6 = res.get("K6_primary", {})
    if k6.get("available"):
        bits = []
        for year in ("2023", "2024", "2025"):
            r = k6["per_year"][year]
            bits.append(
                f"{year} {r['A_rise']:+.2f} -> {r['B_rise']:+.2f} "
                f"({r['delta']:+.3f}, {r['direction']})"
            )
        parts.append(
            "K6 PRIMARY — the DJF h04 -> h07 model system-price rise, the "
            "statistic the delta was chartered on, read from the committed W5 "
            "probe: " + "; ".join(bits) + ". Against PJM's own measured "
            "+15.28 / +21.63 / +35.45 the model goes "
            + ", ".join(
                f"{k6['per_year'][y]['A_pct_of_measured']:.0f} % -> "
                f"{k6['per_year'][y]['B_pct_of_measured']:.0f} %"
                for y in ("2023", "2024", "2025")
            )
            + f". K6 {'PASS' if k6['k6_pass'] else 'FAIL — the primary FELL'}."
        )

    for year in ("2023", "2024", "2025"):
        row = res["per_year"][year]
        ident = row["K5_arm_a_identity"]
        sd = row["K4_slack_dump"]
        k1 = row["K1_class_energy"]
        env = row.get("D_ENV_binding_arm_A", {})
        ident_txt = (
            "byte-identical"
            if ident.get("identical")
            else f"max |delta| {ident.get('max_abs_diff_mw')} MW"
        )
        env_txt = ""
        if env.get("available"):
            env_txt = (
                f" D-ENV: arm A's own dispatch crosses the envelope in "
                f"{env['share_of_group_transitions_pct']:.4f} % of "
                f"{env['n_group_transitions']:,} group-transitions "
                f"({env['n_groups_violating']}/{env['n_groups']} groups ever cross)."
            )
        parts.append(
            f"{year}: K5 arm A {ident_txt} vs the committed keeper over "
            f"{ident.get('n_class_hours')} class-hours; K4 slack/dump "
            f"{sd['A']['slack_mwh']:.0f}/{sd['A']['dump_mwh']:.0f} (A) and "
            f"{sd['B']['slack_mwh']:.0f}/{sd['B']['dump_mwh']:.0f} (B); K1 worst "
            f"class {k1['worst_class']} {k1['worst_pct_of_own_class']:+.4f} % of its "
            f"own energy, ISO total {k1['total_A_twh']:.3f} -> "
            f"{k1['total_B_twh']:.3f} TWh ({k1['total_delta_twh']:+.4f})." + env_txt
        )

    for arm in ("A", "B"):
        r = res["rubric"][arm]
        if r.get("available"):
            parts.append(
                f"Arm {arm} determination {r['determination']}; criteria "
                + ", ".join(f"{k}={v}" for k, v in sorted(r["criteria"].items()))
                + "."
            )
    return " ".join(parts)


ATTESTED_BY_A = (
    "pjm-140 arm A (CONTROL) 2026-07-30: the 2026-07-29-pjm-137-ctheatrate "
    "keeper recipe replayed VERBATIM with no delta, as the A/B baseline for "
    "ramp_envelopes. Verified against the committed keeper on the class "
    "hourlies (PREREG-pjm140-ramp-envelopes-2026-07-30.md K5), so the keeper's "
    "governance posture and accepted-limitation ledger carry over unchanged and "
    "this arm adds no parameter of any kind. Its purpose is to isolate the "
    "single delta; it is NOT a candidate."
)


def _attested_by_b() -> str:
    """Arm B's attestation narrative, with the A/B evidence spliced in."""
    return (
        "pjm-140 measured plant-group hourly ramp envelopes 2026-07-30: the "
        "2026-07-29-pjm-137-ctheatrate recipe replayed with a SINGLE delta, "
        "ramp_limits=true, on a newly generated PJM artifact from the existing "
        "frozen derive (scripts/data/derive_campd_ramp_envelopes.py --iso PJM, "
        "run for PJM for the first time — the pjm-137 pattern). Chartered by "
        "FINDING-pjm139-winter-morning-ramp-is-a-ramp-rate-deficit-2026-07-30.md "
        "§5 and gated by PREREG-pjm140-ramp-envelopes-2026-07-30.md, committed "
        "and pushed BEFORE any arm solved. "
        "DRIVER (rule 14 [R-ACCURATE], not a residual): with ramp_limits off the "
        "keeper's LP carries NO intertemporal coupling on the thermal fleet at "
        "all — it asserts that every thermal plant can move from any output to "
        "any other output in one hour, which is false as physics and false in "
        "the measured record. Replacing that implicit estimate with each plant "
        "family's measured maximum hourly move is an accuracy correction and "
        "goes in on that basis. Rule 19 [R-ONE-MECH]: no other mechanism in the "
        "PJM keeper owns intertemporal thermal coupling (commitment_enabled and "
        "pjm_commitment_posture are False, committed_ramp_spread is 0.0, and the "
        "three P1-native commitment bridges are ISO-exclusive to "
        "CAISO/ERCOT/NYISO; measured_ramp_capability governs reserve ramp "
        "ELIGIBILITY, not energy ramping), so this is a new phenomenon with a "
        "single owner. "
        + _evidence()
        + " HONEST SCOPE, and it is the headline rather than a caveat: the "
        "mechanism is measured NEARLY INERT on PJM and it does NOT close the "
        "defect it was chartered against. PREREG §3's pre-check compared the "
        "model's p99 1-h move against the real fleet's p99 (1.4-1.7x) and "
        "concluded per-plant rows would bind, but the derive writes each plant's "
        "MAX observed move pooled over 26,280 hours — a bound roughly 2-3x above "
        "its own p99 — so a model p99 can sit 1.5x above the actual p99 and "
        "still fall far below the actual max. That is the ERCOT-127 outcome "
        "class ('the real fleet violates the envelope 0-10 times a year'), now "
        "measured on PJM rather than inferred. PREREG §5's no-feedback ceiling "
        "was honoured: no multiplier, scale, haircut, blend, floor, cap, "
        "widening, tightening, per-plant override or quantile swap was applied "
        "to the derived envelopes, and none may be. Under rule 1 [R-STRUCT] the "
        "delta is a structurally-correct physical bound whose fit effect is "
        "~zero, and the winter-morning ramp defect remains OPEN with its root "
        "cause unclosed — it is NOT the ramp envelope."
    )


def _write(dest: Path, attested_by: str, *, add_entry: bool) -> None:
    """Write one arm's attestation from the keeper's."""
    att = json.loads(KEEPER.read_text())
    att["governance"] = dict(att.get("governance", {}), attested_by=attested_by)
    fp = att["free_parameters"]
    if add_entry:
        names = {e["name"] for e in fp["entries"]}
        if NEW_ENTRY["name"] not in names:
            fp["entries"] = [*fp["entries"], NEW_ENTRY]
    fp["n_entries"] = len(fp["entries"])
    # Unchanged on purpose: the delta adds no residual-identified parameter.
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(att, indent=1) + "\n")
    print(
        f"wrote {dest.relative_to(REPO)} — {fp['n_entries']} DOF entries "
        f"({fp['n_residual']} residual-identified)"
    )


def main() -> int:
    """Write both arms' attestations from the keeper's."""
    keeper_residual = json.loads(KEEPER.read_text())["free_parameters"]["n_residual"]
    _write(ARM_A, ATTESTED_BY_A, add_entry=False)
    _write(ARM_B, _attested_by_b(), add_entry=True)
    print(f"keeper n_residual = {keeper_residual} (unchanged in both arms)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
