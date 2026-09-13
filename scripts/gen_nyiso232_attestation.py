#!/usr/bin/env python3
"""Generate the nyiso-232 span attestation (rule 21 `[R-DOF]`, C6 governance).

The arm is the `2026-09-13-nyiso231-anchor-span` keeper recipe with ONE registered
field moved — `nyiso_st_gas_econ_bands_deleaked` False -> True — solved across
NYISO's full registered year set 2022-2025 in ONE invocation, ON the owner's
ruling "Arm it".

THE ONE THING THIS ATTESTATION MUST NOT FUDGE: **this run DOES move offer-curve
band multipliers** (`ST_GAS.econ_low` and `ST_GAS.econ_high`, both to 1.0), which
is otherwise the rules 1/13 authorized price-tuning channel. It is NOT that
channel, and the reason is nyiso-199's owner ruling of 2026-09-06 on the
structurally identical CT_PEAKER substitution, recorded verbatim in
`scenarios.py`: *"a band multiplier is otherwise the rule 1 carve-out channel; the
values remain MEASURED, so rule 20 [R-DOF] adds no ledger entry (R-AY applies to a
band identified by the PRICE RESIDUAL, which this is not)."* The carve-out governs
a band **identified by the price residual**. This band is identified by rules 24/25
— *"generic fallbacks carry neutral (1.0) bands"* — and it moves price the WRONG
way in every year, so it cannot be a price fit even in principle. Check (2) below
states the movement in full rather than asserting there is none.

Every claim that can be checked against the committed artifacts IS checked, and
the script ABORTS on a failed premise rather than emitting a false attestation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

CAL = Path("results/calibration")
ARM = CAL / "nyiso232_deleak_span"
KEEPER = CAL / "nyiso231_anchor_span"
YEARS = (2022, 2023, 2024, 2025)

#: Legitimately per-solve-YEAR, therefore not a per-year RECIPE (rule 1(b)).
PER_YEAR_RESOLVED = {"gas_price_override", "weather_year"}
#: The RESOLUTION of the moved field, not a second lever: `backcast_config`
#: rewrites these two bands FROM the gate, so they move because the gate moved.
#: Verified in check (2) against the declared target rather than waived.
RESOLVED_BY_THE_GATE = {"offer_curve_by_group"}
BAND_KEYS = (
    "committed",
    "econ_low",
    "econ_high",
    "peak",
    "econ_low_share",
    "pct_peaking",
)


def _p1(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    return df[df["pass"] == "P1"] if "pass" in df.columns else df


def main() -> None:
    from market_sim.config.scenarios import ScenarioConfig

    checks: dict[str, object] = {}
    a_sc = json.loads((ARM / "run_config.json").read_text())["scenario_config"]
    k_sc = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    live = ScenarioConfig()

    # (1) EXACTLY ONE registered field moves.
    differing = sorted(
        k
        for k in set(a_sc) | set(k_sc)
        if json.dumps(a_sc.get(k), sort_keys=True, default=str)
        != json.dumps(k_sc.get(k), sort_keys=True, default=str)
        and k not in PER_YEAR_RESOLVED
    )
    schema_drift = [
        k
        for k in differing
        if k not in k_sc and a_sc.get(k) == getattr(live, k, object())
    ]
    moved = [
        k for k in differing if k not in schema_drift and k not in RESOLVED_BY_THE_GATE
    ]
    assert moved == ["nyiso_st_gas_econ_bands_deleaked"], f"G-DELTA: {moved}"
    assert a_sc["nyiso_st_gas_econ_bands_deleaked"] is True
    checks["single_field_delta"] = {
        "fields_moved": moved,
        "from": k_sc.get("nyiso_st_gas_econ_bands_deleaked", False),
        "to": True,
        "per_year_resolved_excluded": sorted(PER_YEAR_RESOLVED),
        "resolved_by_the_gate_excluded": sorted(RESOLVED_BY_THE_GATE),
        "schema_drift_absent_in_keeper_and_at_live_default": {
            k: a_sc[k] for k in sorted(schema_drift)
        },
    }

    # (2) THE BAND MOVEMENT, STATED IN FULL. Exactly two bands move, both to the
    #     rule-24/25 NEUTRAL 1.0, and NOTHING else moves anywhere.
    a_oc, k_oc = (
        a_sc.get("offer_curve_by_group") or {},
        k_sc.get("offer_curve_by_group") or {},
    )
    band_moves = {
        f"{g}.{k}": [k_oc.get(g, {}).get(k), a_oc.get(g, {}).get(k)]
        for g in sorted(set(a_oc) | set(k_oc))
        for k in sorted(set(a_oc.get(g, {})) | set(k_oc.get(g, {})))
        if (k in BAND_KEYS or k.startswith("phys_"))
        and a_oc.get(g, {}).get(k) != k_oc.get(g, {}).get(k)
    }
    assert sorted(band_moves) == ["ST_GAS.econ_high", "ST_GAS.econ_low"], band_moves
    assert all(v[1] == 1.0 for v in band_moves.values()), band_moves
    phys_moved = [b for b in band_moves if ".phys_" in b]
    assert not phys_moved, f"measured basis moved: {phys_moved}"
    st_a = a_oc["ST_GAS"]
    assert st_a["committed"] == k_oc["ST_GAS"]["committed"] == 1.05
    assert st_a["peak"] == k_oc["ST_GAS"]["peak"] == 4.20
    checks["band_movement_stated_in_full"] = {
        "bands_moved": band_moves,
        "target_value": 1.0,
        "target_source": "rules 24/24 [R-REGISTRY] / 25 [R-ISO-SCOPE]: 'generic fallbacks carry neutral (1.0) bands'",
        "new_literals_introduced": 0,
        "phys_keys_moved": 0,
        "committed_and_peak_unchanged": {
            "committed": st_a["committed"],
            "peak": st_a["peak"],
        },
        "why_this_is_not_the_rules_1_13_carve_out": (
            "The carve-out governs a band multiplier IDENTIFIED BY THE PRICE RESIDUAL (rule 20 "
            "[R-DOF] cross-reference R-AY). This band is identified by the rule-24/25 neutral "
            "prescription, introduces zero new literals, and moves the mean LMP DOWN in every one "
            "of the four years (-1.42 / -0.60 / -0.68 / -1.36 $/MWh), against residuals that are "
            "already negative in 2022 and 2025 -- so it cannot be a price fit even in principle, "
            "and it was pre-registered as an expected C3a-2022 FAILURE before the solve. The "
            "governing precedent is nyiso-199's owner ruling of 2026-09-06 on the structurally "
            "identical CT_PEAKER band substitution, recorded in scenarios.py: 'a band multiplier "
            "is otherwise the rule 1 carve-out channel; the values remain MEASURED, so rule 20 "
            "adds no ledger entry (R-AY applies to a band identified by the PRICE RESIDUAL, which "
            "this is not).' This run's own owner ruling is 'Arm it' (2026-09-13), on "
            "PRECOMMIT-nyiso232-st-gas-deleak.md Addendum A."
        ),
    }

    # (3) WHAT IS BEING REMOVED IS A RULE-25 LEAK, verified arithmetically.
    cc = k_oc["CC_REGULAR"]
    leaked_reach = 1.21 / float(cc["phys_econ_high"])
    reg_lo = float(k_oc["ST_GAS"]["econ_low"])
    agree = {
        str(n): round(abs(n * leaked_reach - reg_lo) / reg_lo, 6)
        for n in (
            float(k_oc["ST_GAS"]["phys_econ_low"]),
            float(k_oc["ST_GAS"]["phys_econ_high"]),
            0.825,
        )
    }
    assert cc["econ_high"] == 1.0, "CC_REGULAR.econ_high is the de-leaked neutral band"
    assert max(agree.values()) < 0.01, agree
    checks["removed_value_is_a_rule_25_leak"] = {
        "cited_construction": "ST_GAS econ band = native steam marginal HR x (CC econ_high 1.21 / native CC marginal 0.925)",
        "leaked_reach": round(leaked_reach, 6),
        "registered_econ_low": reg_lo,
        "relative_agreement_by_native_triple": agree,
        "current_reach_cannot_reproduce_it": {
            "current_reach": round(
                float(cc["econ_high"]) / float(cc["phys_econ_high"]), 6
            ),
            "implied_band": round(
                float(k_oc["ST_GAS"]["phys_econ_low"])
                * float(cc["econ_high"])
                / float(cc["phys_econ_high"]),
                6,
            ),
            "relative_gap": round(
                abs(
                    float(k_oc["ST_GAS"]["phys_econ_low"])
                    * float(cc["econ_high"])
                    / float(cc["phys_econ_high"])
                    - reg_lo
                )
                / reg_lo,
                6,
            ),
        },
        "note": (
            "1.21 is an ERCOT KEEPER value the NYISO offer-curve file names as such and records as "
            "REMOVED under rule 25 (audit C-13, B-NYI-1). The registered ST_GAS econ band "
            "reproduces the CITED construction to under 1 % on every native-steam triple the file "
            "records, and is 16.9 % away from what the CURRENT reach gives -- i.e. it carries the "
            "removed value multiplicatively (rule 26 [R-DELETE], one derivation step removed)."
        ),
    }

    # (4) No pinning to actuals: served demand identical to the incumbent in every
    #     year, no firm load shed, nothing dumped.
    served = {}
    for y in YEARS:
        a = _p1(ARM / "hourly" / f"system_{y}.parquet")
        r = _p1(KEEPER / "hourly" / f"system_{y}.parquet")
        at, rt = float(a["demand"].sum() / 1e6), float(r["demand"].sum() / 1e6)
        assert round(at, 5) == round(rt, 5), f"{y}: served {at} vs {rt}"
        assert float(a["slack"].sum()) <= 1e-6 and float(a["dump"].sum()) <= 1e-6, y
        served[str(y)] = {
            "served_twh_arm": round(at, 5),
            "served_twh_incumbent": round(rt, 5),
            "slack_mwh": round(float(a["slack"].sum()), 6),
            "dump_mwh": round(float(a["dump"].sum()), 6),
        }
    checks["served_demand_identical_and_no_slack"] = served

    # (5) Solved ON-PIN.
    meta = json.loads((ARM / "meta.json").read_text())
    pkgs = (meta.get("environment") or {}).get("packages") or {}
    pins = {}
    for line in Path("requirements.txt").read_text().splitlines():
        if "==" in line and not line.strip().startswith("#"):
            n, _, v = line.strip().partition("==")
            pins[n.strip().lower().replace("_", "-")] = v.strip()
    offpin = {p: (pkgs[p], pins[p]) for p in pkgs if p in pins and pkgs[p] != pins[p]}
    assert not offpin, f"off-pin: {offpin}"
    assert meta.get("years") == list(YEARS), meta.get("years")
    checks["solved_on_pin_all_years_one_bundle"] = {
        "packages": pkgs,
        "matches_requirements_txt": True,
        "years": meta["years"],
        "one_invocation": True,
    }

    # (6) Zero new free parameters: the ledger is the incumbent's, byte-for-byte.
    keep_att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    ledger = keep_att["free_parameters"]
    checks["dof_ledger_carried_verbatim"] = {
        "source": "results/calibration/nyiso231_anchor_span/calibration_attestation.json",
        "n_entries": ledger["n_entries"],
        "n_residual": ledger["n_residual"],
        "new_entries_added_by_this_run": 0,
        "why_no_entry": (
            "The band's value is 1.0, the rule-24/25 neutral, not a number identified by any "
            "residual. Per nyiso-199's owner ruling, a band substitution whose value is not "
            "identified by the price residual adds no ledger entry."
        ),
    }

    att = {
        "schema": "calibration-attestation/v1",
        "governance": {
            "levers_trace_to_measured_input": True,
            "no_fit_to_price_residuals": True,
            "no_pinning_to_actuals": True,
            "outage_filter_exogenous_net_load": True,
            "attested_by": (
                "session nyiso-232 (2026-09-13), on the OWNER'S RULING 'Arm it'. Pre-registration: "
                "results/calibration/PRECOMMIT-nyiso232-st-gas-deleak.md + Addendum A (the ruling, "
                "the arming route, the span plan and the expected outcomes), pushed before the "
                "span solved. ONE registered field moves, nyiso_st_gas_econ_bands_deleaked False "
                "-> True. WHAT IT REMOVES: _NYISO_OFFER_CURVE's ST_GAS econ bands state their own "
                "basis as the measured native steam marginal HR x 'the CC class's own defensible "
                "reach ratio (CC econ_high 1.21 / native CC marginal 0.925 = 1.31x)', and 1.21 is "
                "an ERCOT KEEPER value the same file names as such and records as REMOVED under "
                "rule 25 [R-ISO-SCOPE] (audit C-13, B-NYI-1). The registered band therefore "
                "carries the removed value MULTIPLICATIVELY -- the de-leak took it out of the cell "
                "where it was WRITTEN and left it in the cell where it had been MULTIPLIED IN, "
                "which is rule 26 [R-DELETE]'s re-armable answer key one derivation step removed. "
                "Check (3) verifies this arithmetically: the registered 1.08 reproduces the CITED "
                "construction to under 1 % on every native-steam triple the file records, and is "
                "16.9 % away from what the CURRENT reach gives. NOT A RULE 23 [R-FROZEN-DERIVE] "
                "RE-DERIVATION: the ST_GAS source data (nyiso_campd_marginal_hr_summary.csv p50s, "
                "n=25) is untouched and the phys_* keys keep it verbatim (check 2, phys_keys_moved "
                "0); what moves is a borrowed multiplier on top of it, and rule 23's trigger "
                "('never because a residual moved') is not engaged -- no residual moved, and the "
                "change pushes price the WRONG way. THE BLOCK'S SECOND, OUTCOME-BASED "
                "IDENTIFICATION IS NOT LOAD-BEARING: it also claims the level 'reproduces measured "
                "steam volume', but calls that 'validating the level a priori, NOT residual-fitted' "
                "-- corroboration of a construction fixed beforehand, which cannot be promoted to "
                "THE identification once the construction fails without committing rule 13 "
                "[R-MEASURED]'s forbidden move (an OUTCOME fed back to select an input) and failing "
                "its forward test. ZERO free parameters and ZERO new literals: the target is 1.0, "
                "the rule-24/25 neutral, and it is the IDENTICAL remedy this file applied to "
                "CC_REGULAR.econ_high (1.21 -> 1.00) and to CT_PEAKER's econ bands in the SAME "
                "audit. committed (1.05) and peak (4.20) are EXCLUDED, as nyiso-199 excluded them: "
                "peak is the $1,000-offer-cap scarcity wall, and committed already sits BELOW its "
                "own phys_committed 1.104 so its markup clips to 0 in both legs -- moving it would "
                "price the steam min-load block 9.4 % below its own measured burn (measured "
                "-$4.09/MWh) and would turn a de-leak into a new fitted value. REPORTED AT FULL "
                "MAGNITUDE AND NOT ABSORBED: C3a-2022 goes -9.86 % -> -11.61 % and FAILS its "
                "+/-10 % band. That failure was PRE-REGISTERED as the expected outcome before the "
                "span solved, it is the accepted cost of the arming, and no gate was re-cut to "
                "accommodate it: the rule-29 screen STOPPED this arm on exactly that gate and the "
                "OWNER promoted it anyway, which is the division of authority rules 29/31 set up. "
                "The pre-registered at-risk year 2025 PASSES at -7.99 % (the addendum predicted "
                "'near -7 to -8 %'), 2024 IMPROVES (+1.05 -> -0.75 %) and 2023 stays in band "
                "(+0.59 -> -1.26 %). C1: ST_GAS moves toward its actual in 2022 (-1.148 -> -0.477 "
                "TWh), 2024 (-1.064 -> -0.462) and 2025 (-4.677 -> -4.006), and CC_REGULAR improves "
                "in every year; AGAINST IT, 2023 ST_GAS moves AWAY (+1.989 -> +3.326 TWh, in band) "
                "because ST_GAS over-runs there and the arm adds more -- pre-registered as the "
                "exception before the solve -- and CT_PEAKER worsens in all four years while "
                "staying well inside band. SEE ALSO the C8/D-2 disclosure in this run's RESULT "
                "doc: D-2's plant class is decided by a ROW-COUNT vote over LP tranches, which "
                "this mechanism's declared smoothing-ladder collapse (ST_GAS 88 -> 44 rows) flips "
                "for two mixed plants, one of them on an 8-7 margin "
                "(docs/FINDING-d2-plant-class-is-a-tranche-count-vote-2026-09-13.md). That is a "
                "shared-scorer defect this lane REPORTS and does not fix (rule 25), and any C8 "
                "result it produces is carried at full magnitude rather than re-scored here."
            ),
            "note": (
                "authorized_price_tuning is NONE. This run DOES move two offer-curve band "
                "multipliers -- ST_GAS.econ_low and ST_GAS.econ_high, both to 1.0 -- and check (2) "
                "states that movement in full rather than denying it. It is not the rules 1/13 "
                "carve-out because the carve-out governs a band IDENTIFIED BY THE PRICE RESIDUAL, "
                "and this band is identified by the rule-24/25 neutral prescription, introduces "
                "zero new literals, and moves price DOWN in all four years against residuals "
                "already negative in two of them."
            ),
            "computed_checks": checks,
        },
        "authorized_price_tuning": None,
        "free_parameters": ledger,
        "exceptions": [],
        "exceptions_note": keep_att.get("exceptions_note", ""),
    }
    (ARM / "calibration_attestation.json").write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {ARM / 'calibration_attestation.json'}")
    for k in checks:
        print(f"  check OK: {k}")


if __name__ == "__main__":
    main()
