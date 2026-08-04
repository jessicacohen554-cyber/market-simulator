"""Write the calibration attestations for the miso-121 A/B arms.

Both arms are ``replay_keeper`` re-solves of the ``2026-08-03-miso-117b-ct-heat``
keeper's own ``meta.json`` at this session's HEAD, so the governance posture,
the standing measured-input ledger entries and the DOF ledger are the keeper's
— carried forward verbatim in *classification and reason*, with each arm's
**own** measured magnitudes substituted from its own scored verdict so no
number in an attestation describes a different run (the miso-116 §7 basis
discipline, applied at miso-117/119 and again here).

Arm B additionally carries the one new DOF entry, ``dual_fuel_switching``
(MISO) — the EIA-860 Multifuel switch capability priced at MISO's own measured
F923 Petroleum receipt. It adds **zero free parameters**: both legs are
measured registries, neither is fitted, and rule 23 ``[R-FROZEN-DERIVE]``
re-derives them only on a source-data change.

Arm B is **NOT promoted** — the pre-registration's own K3 liveness rule
adjudicates the mechanism ``I`` (inert) at MISO. The attestation is written
anyway because both arms are registered runs (rule 15) and C6 reads it.

Run AFTER both bundles are registered and their legitimacy diagnostics are
written, and BEFORE the final ``calibration_verdict.py --write-metrics`` pass,
since C6 reads the attestation and the ledger entries reclassify C3a/C3c.

Usage::

    uv run python scripts/gen_miso121_attestation.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

KEEPER = REPO / "results/calibration/miso117_ctheatrate_B"
AB_JSON = REPO / "results/calibration/_miso121_dual_fuel_ab.json"
SV_JSON = REPO / "results/calibration/_miso121_switched_volume.json"

ARMS = {
    "A": (
        REPO / "results/calibration/miso121_control_A",
        "2026-08-03-miso-121a-control",
    ),
    "B": (
        REPO / "results/calibration/miso121_dualfuel_B",
        "2026-08-03-miso-121b-dual-fuel",
    ),
}

YEARS = ("2023", "2024", "2025")

_SHARED_ATTEST = (
    "miso-121, 2026-08-03. Both arms are replay_keeper re-solves of the "
    "2026-08-03-miso-117b-ct-heat keeper's own meta.json at this session's "
    "HEAD, --years 2023 2024 2025 in ONE invocation each, years sequential "
    "inside the invocation (rules 12 / 16), arms run one at a time. The "
    "pre-registration results/calibration/PREREG-miso121-dual-fuel-switching-"
    "2026-08-03.md was written, committed and PUSHED before any measurement, "
    "and its §8 amendment fixed the Phase-1 gates K1-K7 and the disposition "
    "rule BEFORE either arm solved. Its §3 Phase-0 screen (no LP) returned "
    "LIVE on all four legs — capability, switch price, binding arithmetic and "
    "event-window observability — which is what authorized these two solves at "
    "all. Rule 22 [R-HOLDOUT]: 2023-2025 only — MISO holds no "
    "calibration-complete marker, so no validation or locked-test year was "
    "solved, scored or read; Winter Storm Elliott (Dec 2022) was declared out "
    "of scope at §3 and never read. "
)

ATTEST_BY = {
    "A": _SHARED_ATTEST
    + "THIS ARM IS THE ZERO-DELTA CONTROL: no --set, no override, no mechanism "
    "armed or disarmed. It exists so the treatment arm is measured against a "
    "same-HEAD twin rather than against the committed keeper, which would "
    "confound the flag with whatever drifted on main since that keeper solved "
    "(the neiso-69 drift-control precedent). It REPRODUCES the committed "
    "miso-117b keeper on the STRICT BYTE basis — max |delta MW| = 0.000000 on "
    "every one of 148,920 class-hours in all three years — so the A/B is "
    "unconfounded. That zero also empirically confirms that main's move during "
    "this session (f0b8c02 -> 98ad9c1, which touched scripts/run_calibration.py) "
    "is a CAISO-gated no-op for MISO. It is NOT a candidate and must never be "
    "promoted.",
    "B": _SHARED_ATTEST
    + "THIS ARM IS THE TREATMENT: exactly ONE delta against the control, "
    "dual_fuel_switching=true, applied through replay_keeper --set and recorded "
    "in run_config.json (rule 26 [R-REGISTRY]). Nothing is stacked (rule 19 "
    "[R-ONE-MECH]): the two sibling cells that require this mechanism — "
    "dual_fuel_oil_reattribution (a reporting relabel) and "
    "dual_fuel_oil_daily_parity (a granularity re-grain of this cap) — are OFF "
    "in BOTH arms and neither is adjudicated here. CHARTER: a gas unit flagged "
    "oil/gas switch-capable on the EIA-860 Multifuel schedule burns whichever "
    "fuel is cheaper, so its delivered price is min(gas, oil) — an "
    "objective-only cap, no LP structural change, emissions and heat rate "
    "staying on the gas characterization. THE MECHANISM IS CONFIRMED ARMED AND "
    "FIRING, not silently inert: the solve logs the cap applied to 371 / 371 / "
    "369 gas tranches (15,827 / 15,827 / 15,825 MW) in 2023 / 2024 / 2025, "
    "matching the Phase-0 capability census exactly — the miso-113 'hook never "
    "wired into the calibration path' hazard was checked for in advance and is "
    "cleared BY MEASUREMENT. Rule 25 [R-ISO-SCOPE]: MISO's capability set from "
    "MISO's own EIA-860 rows and MISO's own F923 Petroleum receipts; the "
    "PJM / NYISO / NEISO keeper verdicts on this row transfer nothing and no "
    "parameter is imported from them. THIS ARM IS NOT PROMOTED: the "
    "pre-registration's own K3 liveness rule adjudicates the mechanism INERT at "
    "MISO on the price grain the rubric scores, and the keeper is unchanged.",
}

DISCLOSURES = {
    "A": (
        "miso-121 arm A disclosures. (a) This bundle is a CONTROL and carries "
        "no finding of its own. (b) IT REPRODUCES THE COMMITTED KEEPER "
        "EXACTLY. On the strict-byte basis — class-hour for class-hour, all "
        "three years — this same-HEAD zero-delta replay differs from the "
        "committed 2026-08-03-miso-117b-ct-heat sidecars by 0.000000 MW across "
        "148,920 cells per year. The prereg §8.3 K2 gate is the SCORECARD "
        "basis (same determination, same nine criterion statuses) and it also "
        "passes; the byte basis is reported because it is what surfaces drift, "
        "and here there is none. (c) PROVENANCE NOTE: an earlier per-year "
        "invocation chain for these arms was DISCARDED and both arms re-solved "
        "from scratch. replay_keeper sets kwargs['years'] = args.years, so a "
        "'--years <one>' invocation writes meta.json with only that year: the "
        "hourly sidecars accumulate across a chain but the bundle's own "
        "provenance does not, and the finished bundle would have claimed years "
        "[2025]. That would have mis-stated the K5 year-span gate and rule 16's "
        "one-bundle span, and the only remedy after the fact would have been "
        "hand-editing a provenance artifact. This bundle's meta records the "
        "TRUE span [2023, 2024, 2025] by construction."
    ),
    "B": (
        "miso-121 arm B disclosures, reported rather than patched. "
        "(a) THE MECHANISM IS PRICE-INERT AND BARELY DISPATCH-LIVE, AND THAT "
        "IS THE RESULT. K3's price leg FAILS in every year — max zonal |dLMP| "
        "0.0000 / 0.0003 / 0.0000 $/MWh against the 0.10 bar, system "
        "load-weighted dLMP +0.0000 / -0.0003 / +0.0000 — while its dispatch "
        "leg clears 50 MW in 2024 ALONE (max class-hour delta 0.0 / 912.5 / "
        "16.0 MW) and carries ~0.2 GWh of class energy. Under the prereg's "
        "pre-committed rule that is `I`, registered, keeper unchanged. "
        "(b) NONE OF THE PHASE-0 IDENTIFICATION IS RETRACTED, and that is what "
        "makes this verdict worth recording. All three legs the mechanism needs "
        "ARE identified from MISO's own data: capability (371 tranches, "
        "15,827 MW = 23.3 % of MISO gas, per-plant from the EIA-860 Multifuel "
        "switch flag), switch price (12/12 measured MISO F923 Petroleum months "
        "in every year, 20.36 / 18.22 / 17.21 $/MMBtu — the national fallback "
        "constant is never used), and event windows (90 / 459 / 452 "
        "gas-labelled CAMPD unit-hours across 25 / 43 / 40 distinct units "
        "lifting from a p50 of 53.91 kg CO2/MMBtu, pipeline gas, into the "
        "70-80 distillate band, validated against CAMPD's OWN diesel-labelled "
        "units at p50 73.65 / 73.46 / 73.65). The fuel deltas are enormous — "
        "max 197.8 / 107.9 / 45.9 $/MMBtu, delivered gas reaching 218.9 "
        "$/MMBtu against oil at 17.7. A well-identified, correctly-wired, "
        "genuinely-firing mechanism can still be inert. "
        "(c) THE SCREEN'S OWN LIVENESS STATISTIC FAILED, AND IT FAILED AGAINST "
        "INTEREST. PREREG §8.1 could not run L5 literally (the keeper bundle "
        "commits no generator-grain P1 dispatch) and substituted the p50 of "
        "|delta offer| over BINDING gen-hours: 64.30 / 93.93 / 108.23 $/MWh "
        "against a 0.10 bar. The realized price effect is 0.0003 $/MWh — the "
        "substitute over-predicted by roughly FIVE ORDERS OF MAGNITUDE. This is "
        "the miso-119 DO-NOT-REDO recurring one level deeper: that session "
        "established max |delta offer| is an upper bound only and named the "
        "capacity-weighted p50 as 'the predictive statistic'. The p50 over "
        "BINDING hours is NOT predictive either, because binding is not "
        "marginality. Measured here on the arms' own unit_hourly sidecars: the "
        "share of binding tranche-hours that are also PARTIALLY LOADED (i.e. "
        "genuinely price-setting, 0 < mw < cap_mw) is 0.00 % / 1.24 % / 0.54 % "
        "— 0 of 15,792, 225 of 18,192 and 63 of 11,568. In 2023 NO capable "
        "tranche is ever both binding and marginal, which is exactly why that "
        "year's price delta is an exact 0.0000. The literal L5 is a large "
        "improvement (it calls 2023 correctly, capw p50 undefined / 1.29 / "
        "18.74) but it would still NOT have prevented these solves, passing in "
        "2024 and 2025. The transferable statistic is the MARGINAL SHARE of "
        "binding hours, not any percentile of the offer delta. "
        "(d) THE PRE-REGISTERED OVER-SWITCHING RISK DID NOT MATERIALISE, and it "
        "is reported because it was named in advance as a possible black mark. "
        "K7 was written reported-only because Phase 0 could only set the "
        "model's binding TRANCHE-hours against CAMPD's observed UNIT-hours — "
        "different grains. The Phase-1 bundles carry unit_hourly sidecars the "
        "keeper lacks, so the comparison is now same-grain, in MWh: model "
        "switched generation 0.00013 / 0.03757 / 0.01096 TWh against CAMPD's "
        "own observed 0.00233 / 0.01133 / 0.01284 TWh — ratios 0.06x, 3.3x and "
        "0.85x, with the CAMPD figure a STATED LOWER BOUND (only 49 of the 89 "
        "capable plants report to CAMPD). The model does not systematically "
        "over-switch; in 2023 it under-switches. "
        "(e) MISO IS INERT FOR A DIFFERENT REASON THAN THE ZONAL ANCHOR WAS, "
        "AND THE TWO MUST NOT BE CONFLATED. gas_offer_margin_zonal_anchor "
        "(miso-119/120) is inert because a mean-zero perturbation never reaches "
        "the price-setting tranches. THIS mechanism is inert because THE "
        "UNDERLYING PHYSICAL PHENOMENON IS NEGLIGIBLE AT MISO'S SCALE: CAMPD's "
        "own meters put observed dual-fuel oil generation at 0.002-0.013 TWh a "
        "year, against ~17-23 TWh of capable-unit generation and a MISO load "
        "measured in hundreds of TWh — of order 0.002 % of ISO energy. The "
        "mechanism reproduces the real behaviour at the right order of "
        "magnitude and the real behaviour is simply too small to move an "
        "ISO-level annual price criterion. That is a statement about MISO, not "
        "about the mechanism's correctness. "
        "(f) NO CRITERION IS CLAIMED AND NOTHING IS BANKED. C7 COAL_PRB is "
        "untouched exactly as pre-declared at §6 P6: this lever was never "
        "offered as a C7 instrument and did not become one, and the C7 residual "
        "stays routed to the data-blocked miso-78/79 congestion + sub-hourly-RT "
        "lane. (g) P5 HOLDS: no parameter was moved to 'finish' this result. "
        "The capable set is EIA-860's own Multifuel switch flag and the parity "
        "price is MISO's own F923 Petroleum receipt; neither was swept, and "
        "neither is re-derived against this arm's inert outcome (rule 23 "
        "[R-FROZEN-DERIVE]). The flag stays default-off, one CLI switch away."
    ),
}


def _new_dof_entry(sv: dict | None) -> dict:
    """Arm B's single new DOF entry — zero free parameters added."""
    measured = (
        "Capability: 371 / 371 / 369 (plant, group) gas tranches, 15,827 / "
        "15,827 / 15,825 MW = 23.34 / 23.30 / 23.49 % of MISO gas capacity, "
        "from the EIA-860 Multifuel schedule ('Switch Between Oil and Natural "
        "Gas?' = Y on a gas-primary unit). Switch price: the volume-weighted "
        "EIA-923 Schedule 5 Petroleum receipt across MISO's plants, 12 of 12 "
        "months measured in every year (20.3584 / 18.2161 / 17.2050 $/MMBtu "
        "annual mean); the flat national OIL_PRICE_PER_MMBTU fallback is never "
        "reached."
    )
    if sv is not None:
        rows = sv.get("by_year") or {}
        mod = " / ".join(
            f"{(rows.get(y, {}).get('model_switched_arm_B') or {}).get('switched_twh', 0.0):.5f}"
            for y in YEARS
        )
        obs = " / ".join(
            f"{(rows.get(y, {}).get('campd_observed') or {}).get('observed_switched_twh', 0.0):.5f}"
            for y in YEARS
        )
        measured += (
            f" Measured A/B effect: switched generation {mod} TWh against "
            f"CAMPD's own observed {obs} TWh (same grain, CAMPD a lower bound); "
            "max zonal |dLMP| 0.0000 / 0.0003 / 0.0000 $/MWh against the 0.10 "
            "K3 bar — FAILS, hence the `I` verdict (committed "
            "results/calibration/_miso121_dual_fuel_ab.json and "
            "_miso121_switched_volume.json)."
        )
    return {
        "name": (
            "dual_fuel_switching (MISO) — oil/gas switch-capable gas units "
            "price their fuel at min(gas, oil) per hour, so a unit whose "
            "delivered gas spikes past oil parity bids its backup distillate "
            "cost instead of being priced out"
        ),
        "where": "run_config.scenario_config.dual_fuel_switching",
        "identification": "measured/published",
        "lineage_solves": (
            "1 (miso-121 arm B, against a same-HEAD zero-delta control; "
            "adjudicated INERT — the arm is NOT a keeper)"
        ),
        "value": True,
        "free_parameters_added": 0,
        "source": (
            "Capability: data.fleet.eia860.dual_fuel_plant_groups over the "
            "EIA-860 Multifuel schedule. Parity price: "
            "data.fuel.plant_prices.iso_monthly_oil_prices over EIA-923 "
            "Schedule 5 Petroleum receipts for MISO's own plants. "
            f"{measured} The Phase-0 identification record — the capability "
            "census, the F923 month coverage, the binding arithmetic and the "
            "CAMPD event-window observability test (including its internal "
            "diesel-labelled control) — is committed in "
            "results/calibration/PROBE-miso121-dual-fuel-screen-2026-08-03.txt "
            "and _miso121_dual_fuel_screen.json."
        ),
        "why_zero": (
            "Neither leg is chosen, tuned or swept. The capable set is a "
            "published EIA-860 boolean field and the parity price is a "
            "published EIA-923 receipt; the mechanism is the arithmetic "
            "min() of two measured series, with no coefficient between them. "
            "Rule 13 [R-MEASURED]: both regenerate for a forward year from "
            "forward drivers (a forward oil trajectory and the same capability "
            "roster) and respond to changed conditions, so this is an "
            "admissible input rather than a backcast overlay. Rule 23 "
            "[R-FROZEN-DERIVE]: re-derived only on a source-data change, never "
            "because a residual moved — and expressly NOT re-derived against "
            "this arm's inert outcome. Rule 19 [R-ONE-MECH]: the two sibling "
            "cells that consume this mechanism (dual_fuel_oil_reattribution, "
            "dual_fuel_oil_daily_parity) stay OFF in both arms, so nothing "
            "stacks. n_residual is unchanged."
        ),
    }


def _verdict(run_id: str) -> dict:
    """Score a registered run and return its JSON verdict."""
    out = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/calibration_verdict.py"),
            "--run-id",
            run_id,
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    if out.returncode not in (0, 1) or not out.stdout.strip():
        raise SystemExit(
            f"calibration_verdict failed for {run_id}: {out.stderr[-800:]}"
        )
    return json.loads(out.stdout)


def _magnitudes(verdict: dict) -> dict[tuple[str, int], str]:
    """(criterion, year) -> this run's OWN measured magnitude string."""
    out: dict[tuple[str, int], str] = {}
    for name, crit in verdict["criteria"].items():
        for rec in crit.get("records", []):
            year = rec.get("year")
            if year is None or rec.get("key") == "da_diagnostic":
                continue
            mag = rec.get("magnitude") or rec.get("detail")
            if mag:
                out[(name, int(year))] = str(mag)
    return out


def build(arm: str, sv: dict | None) -> Path:
    """Write one arm's attestation; return its path."""
    bundle, run_id = ARMS[arm]
    base = json.loads((KEEPER / "calibration_attestation.json").read_text())
    mags = _magnitudes(_verdict(run_id))

    att = {
        "schema": base["schema"],
        "free_parameters": base["free_parameters"],
        "governance": {
            **{
                k: base["governance"][k]
                for k in (
                    "levers_trace_to_measured_input",
                    "no_fit_to_price_residuals",
                    "no_pinning_to_actuals",
                    "outage_filter_exogenous_net_load",
                )
            },
            "attested_by": ATTEST_BY[arm],
        },
        "disclosures": {"note": DISCLOSURES[arm]},
        "exceptions": [],
    }
    for exc in base["exceptions"]:
        new = dict(exc)
        key = (str(exc.get("criterion")), int(exc.get("year")))
        if key in mags:
            new["magnitude"] = mags[key]
            new["magnitude_basis"] = (
                "this run's own scored value (miso-121); the classification "
                "and reason are the standing MISO adjudication carried forward"
            )
        att["exceptions"].append(new)

    if arm == "B":
        entry = _new_dof_entry(sv)
        entries = [
            e
            for e in att["free_parameters"].get("entries", [])
            if e.get("name") != entry["name"]
        ]
        entries.append(entry)
        att["free_parameters"]["entries"] = entries

    path = bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1) + "\n")
    return path


def main() -> int:
    """Write both arms' attestations and re-seed each DOF ledger."""
    sv = json.loads(SV_JSON.read_text()) if SV_JSON.exists() else None
    if sv is None:
        print(
            "NOTE: switched-volume JSON absent — the DOF entry's measured-effect "
            "prose is omitted; re-run this script after that probe to enrich it."
        )
    for arm in ("A", "B"):
        path = build(arm, sv)
        print(f"wrote {path.relative_to(REPO)}")
        out = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts/build_dof_ledger.py"),
                str(ARMS[arm][0]),
                "--iso",
                "MISO",
            ],
            capture_output=True,
            text=True,
            cwd=REPO,
        )
        print(
            f"  build_dof_ledger[{arm}] rc={out.returncode} {out.stdout.strip()[-300:]}"
        )
        if out.returncode != 0:
            print(f"  stderr: {out.stderr[-500:]}")
        if arm == "B":
            # build_dof_ledger replaces the whole section, so re-attach the new
            # entry after it runs (it only knows the curated per-ISO table).
            att_path = ARMS[arm][0] / "calibration_attestation.json"
            att = json.loads(att_path.read_text())
            entry = _new_dof_entry(sv)
            entries = [
                e
                for e in att["free_parameters"].get("entries", [])
                if e.get("name") != entry["name"]
            ]
            entries.append(entry)
            att["free_parameters"]["entries"] = entries
            att["free_parameters"]["n_entries"] = len(entries)
            att["free_parameters"]["n_residual"] = sum(
                1 for e in entries if e.get("identification") == "residual"
            )
            att_path.write_text(json.dumps(att, indent=1) + "\n")
            print(f"  re-attached the dual-fuel DOF entry ({len(entries)} total)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
