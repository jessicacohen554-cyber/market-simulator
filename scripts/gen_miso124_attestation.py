"""Write the calibration attestation for the miso-124 dual-fuel re-arm.

The arm is a ``replay_keeper`` re-solve of the ``2026-08-04-miso-122b-scope-gate``
keeper's own ``meta.json`` at this session's HEAD with exactly one delta,
``dual_fuel_switching=true``. The governance posture, the standing
measured-input ledger entries and the DOF ledger are therefore the keeper's —
carried forward verbatim in *classification and reason*, with this run's **own**
measured magnitudes substituted from its own scored verdict so no number in the
attestation describes a different run (the miso-116 §7 basis discipline, applied
at miso-117 / 119 / 121 and again here).

It carries the ``dual_fuel_switching`` DOF entry miso-121 introduced. That entry
adds **zero free parameters**: both legs are measured registries, neither is
fitted, and rule 23 ``[R-FROZEN-DERIVE]`` re-derives them only on a source-data
change.

This session does **not** re-adjudicate the mechanism. miso-121 settled it
(`FINDING-miso121-dual-fuel-switching-2026-08-03.md`): fully identified,
price-inert in sample, cell `I` on the K3 liveness rule. What this session
restores is the **arming**, on the owner's rule 1 ``[R-STRUCT]`` call that a
keeper should carry structurally-faithful measured market structure even where
it is costless at the scored grain — the call miso-121's own matrix note flagged
as "an OWNER call, not a session call".

Run AFTER the bundle is registered and its legitimacy diagnostics are written,
and BEFORE the final ``calibration_verdict.py --write-metrics`` pass, since C6
reads the attestation and the ledger entries reclassify C3a / C3c.

Usage::

    uv run python scripts/gen_miso124_attestation.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

KEEPER = REPO / "results/calibration/miso122_scopegate_B"
BUNDLE = REPO / "results/calibration/miso124_dualfuel_B"
RUN_ID = "2026-08-04-miso-124-dualfuel-rearm"
AB_JSON = REPO / "results/calibration/_miso124_dualfuel_rearm_ab.json"

_ATTEST = (
    "miso-124, 2026-08-04. This arm is a replay_keeper re-solve of the "
    "2026-08-04-miso-122b-scope-gate keeper's own meta.json at this session's "
    "HEAD, --years 2023 2024 2025 in ONE invocation (rules 12 / 16), years "
    "sequential inside the invocation. EXACTLY ONE DELTA against that keeper, "
    "dual_fuel_switching=true, applied through replay_keeper --set and recorded "
    "in run_config.json (rule 26 [R-REGISTRY]); a programmatic diff of the two "
    "scenario blocks returns exactly one differing key. Nothing is stacked "
    "(rule 19 [R-ONE-MECH]): the two sibling cells that consume this mechanism "
    "— dual_fuel_oil_reattribution (a reporting relabel) and "
    "dual_fuel_oil_daily_parity (a granularity re-grain of this cap) — are OFF "
    "in both the keeper and this arm, and neither is adjudicated here. "
    "THE MECHANISM IS NOT RE-ADJUDICATED. miso-121 settled it against a "
    "pre-registration pushed before any measurement: fully identified, "
    "price-inert at the scored grain, cell I. This session restores only the "
    "ARMING, which was lost to a merge race — the miso-121 promotion and the "
    "miso-122 promotion were prepared in parallel off different parents, and "
    "miso-122b (branched from the older miso-117b keeper) landed carrying "
    "dual_fuel_switching=false. CHARTER FOR ARMING AN INERT MECHANISM: rule 1 "
    "[R-STRUCT] — a gas unit flagged oil/gas switch-capable on the EIA-860 "
    "Multifuel schedule burns whichever fuel is cheaper, so its delivered price "
    "is min(gas, oil). That is the market's actual structure; it is an "
    "objective-only cap with no LP structural change, emissions and heat rate "
    "staying on the gas characterization, it adds zero free parameters, and it "
    "is costless at every scored grain. Whether a keeper should carry it anyway "
    "is an owner call, and the owner made it. THE MECHANISM IS CONFIRMED ARMED "
    "AND FIRING, not silently inert: the solve logs the cap applied to "
    "371 / 371 / 369 gas tranches (15,827 / 15,827 / 15,825 MW) in "
    "2023 / 2024 / 2025, reproducing miso-121's capability census exactly — the "
    "miso-113 'hook never wired into the calibration path' hazard is cleared BY "
    "MEASUREMENT, not by assumption. Rule 25 [R-ISO-SCOPE]: MISO's capability "
    "set from MISO's own EIA-860 rows and MISO's own F923 Petroleum receipts; "
    "the PJM / NYISO / NEISO keeper verdicts on this row transfer nothing and "
    "no parameter is imported from them. Rule 22 [R-HOLDOUT]: 2023-2025 only — "
    "MISO holds no calibration-complete marker, so no validation or locked-test "
    "year was solved, scored or read, and no D-5(b) re-key duty arises."
)

DISCLOSURES = (
    "miso-124 disclosures, reported rather than patched. "
    "(a) THE PRE-DECLARED PRICE EXPECTATION WAS WRONG, AND IT IS RECORDED AS "
    "WRONG RATHER THAN RE-NARRATED. The session brief pre-declared 'max zonal "
    "|dLMP| well under 0.01 $/MWh', extrapolating miso-121's measured "
    "0.0000 / 0.0003 / 0.0000 on the miso-117b keeper. Measured here against "
    "miso-122b: 0.000000 / 1.382669 / 0.000000 $/MWh. The 2024 figure is ~4,600x "
    "miso-121's and ~138x the pre-declared bar. THIS IS A REAL INTERACTION WITH "
    "THE miso-122 SCOPE GATE and it is stated plainly: the dispatch response is "
    "essentially UNCHANGED from miso-121 (max class-hour delta "
    "0.0 / 912.5 / 16.0 MW there, 0.000 / 912.500 / 15.959 MW here — the same "
    "912.5 MW seam-band quantisation constant miso-122 identified, and the same "
    "~16 MW in 2025), so the mechanism does the same thing to dispatch; what "
    "changed is WHICH UNIT IS MARGINAL in those hours after the scope gate "
    "re-priced 55088 Dearborn's CC_CHP / CT_CHP tranches by -16.6 %. "
    "(b) THE INTERACTION IS SIX HOURS OF 8,760 AND ONE-SIDED. Every non-zero "
    "zonal price delta in 2024 falls in 6 hours, all in mid-January (model "
    "hours 62 and 344-355) — the SAME winter locus miso-121 measured ('the "
    "ENTIRE price effect sits in winter 2024'). Direction is as the arithmetic "
    "requires and is checked, not assumed: price FALLS in 23 zone-hours and "
    "rises in 6, and the system demand-weighted dLMP is -0.000159 $/MWh in "
    "2024 and exactly 0.000000 in 2023 and 2025 — a min(gas, oil) cap can only "
    "lower a delivered cost, so a net system-lambda increase would have been a "
    "red flag. There is none. "
    "(c) NO GATE REGRESSES, WHICH IS THE CONDITION THIS SESSION WAS REQUIRED TO "
    "TEST. All nine criterion statuses, the determination and the ledgered "
    "caveat budget are identical to the keeper's, and the legitimacy "
    "diagnostics carry ZERO verdict changes across D-1 / D-2 / D-4 / D-5 / "
    "D-9 / D-10 (4 of 30 D-1 rows, 6 of 27 D-2 rows and 1 of 3 D-4 rows move "
    "numerically, none across a threshold). C7 COAL_PRB remains the sole FAIL. "
    "(d) CLASS ENERGY IS THE MAGNITUDE, NOT THE MAX CLASS-HOUR (miso-122's "
    "DO-NOT-MISREAD, which applies with double force here because this arm's "
    "max class-hour delta lands on the import class where one 912.5 MW seam "
    "band flips). Signed 2024 class energy: CC_REGULAR -0.337 GWh, CT_PEAKER "
    "+0.318 GWh, ST_CHP +0.063 GWh, ST_GAS -0.026 GWh, CC_CHP -0.016 GWh, oil "
    "-0.002 GWh; 2023 is identically zero and 2025 moves ~0.02 GWh. That is of "
    "order 0.0003 TWh against a MISO load in the hundreds of TWh — the same "
    "~0.002 %-of-energy scale miso-121 measured, and the reason the mechanism "
    "is inert at every scored grain. "
    "(e) NOTHING IS CLAIMED FOR ANY CRITERION. C7 COAL_PRB is untouched and was "
    "never offered as a target; the C7 residual stays routed to the "
    "data-blocked miso-78/79 congestion + sub-hourly-RT lane, and the "
    "contract-period tonnage route stays refused (miso-103 / 104) pending the "
    "Form 580 count, which is a DATA ASK and not a solve. C3a and C3c remain "
    "ledgered at 2/3, unchanged."
)


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


def _dof_entry() -> dict:
    """The dual_fuel_switching DOF entry, carried forward from miso-121.

    Zero free parameters: both legs are published measured registries and the
    mechanism is the arithmetic ``min()`` of two of them, with no coefficient
    between. ``n_residual`` is unchanged.
    """
    measured = ""
    if AB_JSON.exists():
        ab = json.loads(AB_JSON.read_text())
        dl = ab.get("max_zonal_abs_dlmp", {})
        if dl:
            measured = (
                "Measured effect on THIS keeper: max zonal |dLMP| "
                + " / ".join(f"{dl[y]:.6f}" for y in sorted(dl))
                + " $/MWh. "
            )
    return {
        "name": "dual_fuel_switching",
        "identification": "measured",
        "classification": (
            "measured registry pair, zero free parameters (armed on rule 1 "
            "[R-STRUCT] grounds; miso-121 adjudicated the mechanism INERT at "
            "MISO's scored grain and that verdict stands)"
        ),
        "value": True,
        "free_parameters_added": 0,
        "source": (
            "Capability: data.fleet.eia860.dual_fuel_plant_groups over the "
            "EIA-860 Multifuel schedule. Parity price: "
            "data.fuel.plant_prices.iso_monthly_oil_prices over EIA-923 "
            f"Schedule 5 Petroleum receipts for MISO's own plants. {measured}"
            "The Phase-0 identification record — the capability census, the "
            "F923 month coverage, the binding arithmetic and the CAMPD "
            "event-window observability test (including its internal "
            "diesel-labelled control) — is committed in "
            "results/calibration/PROBE-miso121-dual-fuel-screen-2026-08-03.txt "
            "and _miso121_dual_fuel_screen.json."
        ),
        "why_zero": (
            "Neither leg is chosen, tuned or swept. The capable set is a "
            "published EIA-860 boolean field and the parity price is a "
            "published EIA-923 receipt; the mechanism is the arithmetic min() "
            "of two measured series, with no coefficient between them. Rule 13 "
            "[R-MEASURED]: both regenerate for a forward year from forward "
            "drivers (a forward oil trajectory and the same capability roster) "
            "and respond to changed conditions, so this is an admissible input "
            "rather than a backcast overlay. Rule 23 [R-FROZEN-DERIVE]: "
            "re-derived only on a source-data change, never because a residual "
            "moved — and expressly NOT re-derived for this re-arm. Rule 19 "
            "[R-ONE-MECH]: the two sibling cells that consume this mechanism "
            "(dual_fuel_oil_reattribution, dual_fuel_oil_daily_parity) stay OFF, "
            "so nothing stacks. n_residual is unchanged."
        ),
    }


def build() -> Path:
    """Write the arm's attestation; return its path."""
    base = json.loads((KEEPER / "calibration_attestation.json").read_text())
    mags = _magnitudes(_verdict(RUN_ID))

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
            "attested_by": _ATTEST,
        },
        "disclosures": {"note": DISCLOSURES},
        "exceptions": [],
    }
    for exc in base["exceptions"]:
        new = dict(exc)
        key = (str(exc.get("criterion")), int(exc.get("year")))
        if key in mags:
            new["magnitude"] = mags[key]
            new["magnitude_basis"] = (
                "this run's own scored value (miso-124); the classification and "
                "reason are the standing MISO adjudication carried forward"
            )
        att["exceptions"].append(new)

    path = BUNDLE / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1) + "\n")
    return path


def main() -> int:
    """Write the attestation, re-seed the DOF ledger, re-attach the entry."""
    path = build()
    print(f"wrote {path.relative_to(REPO)}")
    out = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/build_dof_ledger.py"),
            str(BUNDLE),
            "--iso",
            "MISO",
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    print(f"  build_dof_ledger rc={out.returncode} {out.stdout.strip()[-300:]}")
    if out.returncode != 0:
        print(f"  stderr: {out.stderr[-500:]}")
    # build_dof_ledger replaces the whole section, so re-attach the dual-fuel
    # entry afterwards (it only knows the curated per-ISO table).
    att = json.loads(path.read_text())
    entry = _dof_entry()
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
    path.write_text(json.dumps(att, indent=1) + "\n")
    print(f"  re-attached the dual-fuel DOF entry ({len(entries)} total)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
