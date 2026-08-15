"""Write the calibration attestations for the miso-117 A/B arms.

Both arms replay the `2026-07-31-miso-109b-hy-level` keeper's recipe, so the
governance posture, the standing measured-input ledger entries and the DOF
ledger are the keeper's — carried forward verbatim in *classification and
reason*, with each arm's **own** measured magnitudes substituted from its own
scored verdict so no number in an attestation describes a different run
(the miso-116 §7 basis discipline, applied to the attestation this time).

Arm B additionally carries the one new DOF entry, `measured_ct_heat_rates`,
identified `measured-physical` under rule 14 `[R-ACCURATE]`.

Run AFTER both bundles are registered (the magnitudes come from
``scripts/calibration_verdict.py --json``) and BEFORE the final scoring pass,
since C6 reads the attestation and the ledger entries reclassify C3a/C3c.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/gen_miso117_attestation.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent

KEEPER = REPO / "results/calibration/miso109_hy_level_B"
ARMS = {
    "A": (
        REPO / "results/calibration/miso117_control_A",
        "2026-08-03-miso-117a-control",
    ),
    "B": (
        REPO / "results/calibration/miso117_ctheatrate_B",
        "2026-08-03-miso-117b-ct-heat",
    ),
}

#: The measured artifact arm B arms. Rule 23 [R-FROZEN-DERIVE]: re-derived only
#: on a CAMPD vintage change, never because a residual moved.
ARTIFACT = "data/raw/_processed-legacy/campd_ct_heat_rates_MISO.csv"

_SHARED_ATTEST = (
    "miso-117, 2026-08-03. Both arms are replay_keeper re-solves of the "
    "2026-07-31-miso-109b-hy-level keeper's own meta.json at this session's "
    "HEAD, --year 2023 2024 2025 in ONE invocation each, years sequential "
    "inside the invocation (rules 12 / 16), chains run one at a time. The "
    "pre-registration results/calibration/PREREG-miso117-ct-heat-rates-"
    "2026-08-03.md was written, committed and PUSHED before either arm "
    "solved; every gate, kill, predicted direction and disposition rule "
    "below was fixed there. Rule 22 [R-HOLDOUT]: 2023-2025 only — MISO holds "
    "no calibration-complete marker, so no validation or locked-test year was "
    "solved, scored or read. "
)

ATTEST_BY = {
    "A": _SHARED_ATTEST
    + "THIS ARM IS THE ZERO-DELTA CONTROL: no --set, no override, no "
    "mechanism armed or disarmed. It exists so the treatment arm is measured "
    "against a same-HEAD twin rather than against the committed keeper, which "
    "would confound the flag with whatever drifted on main since the keeper "
    "solved (the neiso-69 drift-control precedent). It is NOT a candidate and "
    "must never be promoted.",
    "B": _SHARED_ATTEST
    + "THIS ARM IS THE TREATMENT: exactly ONE delta against the control, "
    "measured_ct_heat_rates=true, applied through replay_keeper --set and "
    "recorded in run_config.json in BOTH channels (scenario_config and "
    "calibration_flags.coal_prb_sigmoid_overrides) so the arming is visible "
    "in the reproducibility record (rule 26 [R-REGISTRY]). Nothing is "
    "stacked (rule 19 [R-ONE-MECH]). CHARTER: rule 14 [R-ACCURATE] — it "
    "replaces eGRID's plant-average ANNUAL heat rate with MISO's own measured "
    "per-plant CAMPD loaded heat rate on 86 plants / 19,120.7 MW of CT_PEAKER "
    "capacity (85.8 % of the class), admissible on input accuracy REGARDLESS "
    "of what it does to any residual, and it is NOT offered as an instrument "
    "for C7 COAL_PRB or for the overnight level offset. Rule 25 "
    "[R-ISO-SCOPE]: MISO's own artifact from MISO's own CAMPD data; the "
    "NYISO / PJM / CAISO / NEISO verdicts on this mechanism transfer nothing "
    "to it, and no parameter is imported from them.",
}

DISCLOSURES = {
    "A": (
        "miso-117 arm A disclosures. (a) This bundle is a CONTROL and carries "
        "no finding of its own. (b) STRICT-BYTE DRIFT AGAINST THE COMMITTED "
        "KEEPER IS REAL AND IS REPORTED, NOT HIDDEN: class-hour for "
        "class-hour, this same-HEAD zero-delta replay differs from the "
        "committed 2026-07-31-miso-109b-hy-level sidecars by up to 3,728.5 MW. "
        "The prereg §4 K2 gate is the SCORECARD basis, which reproduces "
        "(same determination, same nine criterion statuses); the byte basis is "
        "reported because it is what surfaces drift. It does not confound the "
        "A/B: both arms sit at the same HEAD with one flag between them, which "
        "is precisely why a same-HEAD control was solved. (c) The cause is "
        "not identified here and is not guessed at; bisecting it needs full "
        "solves. It is filed, not explained."
    ),
    "B": (
        "miso-117 arm B disclosures, reported rather than patched. "
        "(a) THE PREREG'S HEADLINE PREDICTION IS REFUTED, AND THAT IS THE "
        "RESULT. §5 prediction 1 said CT_PEAKER energy would RISE +0.2 to "
        "+1.5 TWh in all three years because the class average gets cheaper. "
        "It FALLS 1.234 / 1.010 / 1.226 TWh. The measurement that explains it "
        "is in the artifact itself and was in front of me at Phase 0 without "
        "my reading it correctly: the re-price is CAPACITY-weighted cheaper "
        "(-0.393 MMBtu/MWh) but GENERATION-weighted essentially neutral and "
        "very slightly DEARER (+0.003). The 13,801 MW that got cheaper barely "
        "runs; the 5,320 MW that got dearer is the part of the class that "
        "actually clears. A class-average heat rate is the wrong statistic "
        "for a dispatch prediction, and the Phase 0 write-up quoted it as if "
        "it were the right one. (b) PREDICTION 2 IS ALSO WRONG, IN BOTH "
        "DIRECTIONS: it said C1 CT_PEAKER improves in 2023 and worsens in "
        "2024. 2023 was 1.57 TWh UNDER actual and gets worse; 2024 was +0.61 "
        "TWh OVER and improves to -0.40 under. (c) PREDICTION 4 IS WRONG IN "
        "SIGN: lambda was predicted DOWN and moves UP (+0.065 / +0.059 / "
        "+0.020 $/MWh), consistent with (a). It is a ~0.2 % move and is not "
        "offered as a C3a improvement. (d) PREDICTION 5 IS CONFIRMED AND "
        "REPRODUCES miso-107's INDEPENDENT MEASUREMENT: the h14-21 "
        "reliability_floor x CT_PEAKER limb's forced energy rises 1.1819 -> "
        "1.7361 TWh (+46.9 %), against miso-107's +47 % measured on miso-106's "
        "arm. The D-2 share rises 0.1157/0.0821/0.0867 -> 0.1407/0.0999/0.1043 "
        "and stays UNDER the 0.15 peaker cap in all three years, so C8 PASSES "
        "outright and the rule-20 conditional-pass route was NOT needed. The "
        "limb was not touched, and per the miso-106 keeper note it must not "
        "be. (e) THE KEEPER'S ONE FAILING CRITERION GETS MARGINALLY WORSE. C7 "
        "COAL_PRB off-peak CV ratio moves 0.466 -> 0.462, 0.475 -> 0.474, "
        "0.314 -> 0.309 against a 0.50 bound. It FAILs in both arms and in "
        "every year; the movement is small but adverse, and the prereg §7 "
        "makes exactly this a PROMOTION BLOCKER. This arm is therefore NOT "
        "promoted. Per rules 1 [R-STRUCT] / 14 [R-ACCURATE] the measured "
        "input is NOT reverted for it: a worse residual on an accurate input "
        "is a discovered bug, not a reason to restore an estimate. (f) WHAT "
        "IMPROVES IS REPORTED BUT IS NOT THE JUSTIFICATION: C7 CT_PEAKER "
        "off-peak CV ratio 0.981/0.836/0.799 -> 1.219/0.917/1.042, i.e. the "
        "repriced class's own diurnal amplitude moves toward the actual in "
        "all three years, and 2025 clears the 0.50 bound by a wider margin. "
        "No criterion verdict changes in either direction. (g) BASIS NOTE, so "
        "no successor reads two incomparable numbers as a contradiction: D-2's "
        "class_total_twh denominator is summed over the ALIGNED plant subset "
        "the floor reconstruction covers, not the whole class, so it moves "
        "10.2164 -> 12.3420 TWh for CT_PEAKER while the SOLVED class dispatch "
        "moves 15.4683 -> 14.2348 TWh in the opposite direction. Both are "
        "correct on their own basis. On the solved-dispatch denominator the "
        "forced shares would be 0.122 / 0.090 / 0.093, i.e. the gate as "
        "scored is the CONSERVATIVE reading."
    ),
}

NEW_DOF = {
    "name": "measured_ct_heat_rates",
    "where": "run_config.scenario_config.measured_ct_heat_rates",
    "identification": "measured-physical",
    "lineage_solves": "1 (miso-117 A/B, 2026-08-03)",
    "value": True,
    "source": (
        f"{ARTIFACT} (86 plant rows, ALL flag=='ok' — zero excluded by the "
        "physical band), written by scripts/data/derive_campd_ct_heat_rates.py "
        "--iso MISO --years 2023 2024 2025 and landed on main under PR #3217. "
        "Consumed by fleet.campd_bins.measured_ct_heat_rates('MISO') -> "
        "eia860._rows_to_generators, class-scoped to CT_PEAKER rows only "
        "(verified empirically at the fleet seam: classes touched == "
        "['CT_PEAKER'], scripts/probes/_miso117_flag_fidelity.py)."
    ),
    "note": (
        "NOT a fitted parameter and not a tunable: it is a boolean that "
        "selects MEASURED per-plant loaded heat rates over eGRID's "
        "plant-average ANNUAL rate (rule 14 [R-ACCURATE]). It carries no "
        "threshold or scalar of its own — every number it applies is a CAMPD "
        "measurement of a specific machine, converted to the NET basis by the "
        "same committed parasitic-factor map the benchmark's net actual uses. "
        "Rule 23 [R-FROZEN-DERIVE]: the artifact re-derives ONLY when CAMPD "
        "publishes new or revised vintages, never because a residual moved, "
        "and any re-derivation commit must cite the data change. Rule 25 "
        "[R-ISO-SCOPE]: MISO's own artifact from MISO's own data."
    ),
    "known_limitation": (
        "The SHARED derive admits some sub-6.0 MMBtu/MWh loaded METER hours, "
        "which biases every measured ISO's CT artifact low. MISO is the LEAST "
        "exposed of the four measured ISOs: 0.30 % of loaded hours, worth "
        "+0.014 MMBtu/MWh energy-weighted, against CAISO 3.46 % / +0.114 and "
        "NYISO 2.45 % / +0.122 (scripts/probes/_caiso146_hourly_hr_integrity.py). "
        "An hour-grain screen would move several committed keepers' inputs and "
        "is a cross-cutting audit item, not a MISO session's call — it is "
        "filed, and at +0.014 MMBtu/MWh it cannot account for this arm's "
        "dispatch result either way."
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


def build(arm: str) -> Path:
    """Write one arm's attestation; return its path."""
    bundle, run_id = ARMS[arm]
    base = json.loads((KEEPER / "calibration_attestation.json").read_text())
    mags = _magnitudes(_verdict(run_id))

    att = {
        "schema": base["schema"],
        # free_parameters is re-seeded from THIS bundle's run_config by
        # scripts/build_dof_ledger.py immediately after this write; the keeper's
        # section is carried only as the starting shape.
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
                "this run's own scored value (miso-117); the classification and "
                "reason are the standing MISO adjudication carried forward"
            )
        att["exceptions"].append(new)

    if arm == "B":
        entries = att["free_parameters"].setdefault("entries", [])
        entries = [e for e in entries if e.get("name") != NEW_DOF["name"]]
        entries.append(dict(NEW_DOF))
        att["free_parameters"]["entries"] = entries

    path = bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1) + "\n")
    return path


def main() -> int:
    """Write both arms' attestations and re-seed each DOF ledger."""
    for arm in ("A", "B"):
        path = build(arm)
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
            entries = [
                e
                for e in att["free_parameters"].get("entries", [])
                if e.get("name") != NEW_DOF["name"]
            ]
            entries.append(dict(NEW_DOF))
            att["free_parameters"]["entries"] = entries
            att["free_parameters"]["n_entries"] = len(entries)
            att["free_parameters"]["n_residual"] = sum(
                1 for e in entries if e.get("identification") == "residual"
            )
            att_path.write_text(json.dumps(att, indent=1) + "\n")
            print(f"  re-attached {NEW_DOF['name']} DOF entry ({len(entries)} total)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
