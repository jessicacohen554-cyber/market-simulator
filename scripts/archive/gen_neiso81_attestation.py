"""Write the calibration attestations for the neiso-81 ``measured_chp_heat_rates`` arms.

Both arms are ``replay_keeper`` re-solves of the
``2026-08-03-neiso-caiso156-meter-screen`` keeper's own ``meta.json`` at this
session's HEAD. Arm **A** is a ZERO-DELTA control; arm **B** carries exactly one
delta, ``measured_chp_heat_rates=true``. The governance posture, the standing
measured-input ledger entries (NEISO's single ledgered C3c caveat) and the DOF
ledger are therefore the keeper's — carried forward verbatim in *classification
and reason*, with each run's **own** measured magnitudes substituted from its own
scored verdict, so no number in an attestation describes a different run (the
miso-116 §7 basis discipline).

**BOTH arms need an attestation, and that is not cosmetic.** neiso-70 §4 measured
it: without one, a probe bundle reads ``NOT-YET / governance UNATTESTED`` and C3c
degrades from a ledgered CAVEAT to a raw FAIL, because a caveat can only be
*ledgered* by an attestation. That is a scoring artifact of probe bundles, and it
must apply identically to control and arm or the A/B comparison is not
like-for-like.

Arm B carries one new DOF entry, ``measured_chp_heat_rates``, adding **zero free
parameters**: it swaps eGRID's steam-credited ``PLHTRT`` for eGRID's own
published ``(PLHTIAN + CHPCHTI)/PLNGENAN`` on the same NET denominator. No
coefficient is chosen, fitted or swept.

Run AFTER each bundle is registered and its legitimacy diagnostics are written,
and BEFORE the final ``calibration_verdict.py --write-metrics`` pass, since C6
reads the attestation and the ledger entries reclassify C3c.

Usage::

    uv run python scripts/gen_neiso81_attestation.py --arm A
    uv run python scripts/gen_neiso81_attestation.py --arm B
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent

ISO = "NEISO"
KEEPER = REPO / "results/calibration/neiso_c156_meter_screen_B"
ARTIFACT = REPO / "data/raw/_processed-legacy/chp_power_only_heat_rates_NEISO.csv"
PHASE0_JSON = REPO / "results/calibration/_neiso81_chp_phase0.json"
AB_JSON = REPO / "results/calibration/_neiso81_chpheatrate_ab.json"

ARMS = {
    "A": {
        "bundle": REPO / "results/calibration/neiso81_control_A",
        "run_id_file": REPO / "results/calibration/_neiso81_run_id_A.txt",
        "armed": False,
    },
    "B": {
        "bundle": REPO / "results/calibration/neiso81_chpheatrate_B",
        "run_id_file": REPO / "results/calibration/_neiso81_run_id_B.txt",
        "armed": True,
    },
}

_COMMON = (
    "neiso-81, 2026-08-04. A replay_keeper re-solve of the "
    "2026-08-03-neiso-caiso156-meter-screen keeper's own meta.json at this "
    "session's HEAD, --years 2023 2024 2025 in ONE invocation (rules 12 / 16 "
    "[R-ALLYEARS]), years sequential inside the invocation. "
    "PRE-REGISTRATION: results/calibration/"
    "PREREG-neiso81-chp-heat-rate-readjudication-2026-08-04.md, pushed BEFORE "
    "either arm solved — every property, threshold, falsifier, verdict branch "
    "and the promotion standard itself was fixed in advance. "
)

_ATTEST_A = _COMMON + (
    "THIS IS THE ZERO-DELTA CONTROL (arm A). No --set; a programmatic diff of "
    "its scenario block against arm B's returns exactly one differing key. It "
    "exists because miso-124's DO-NOT-MISREAD is that price response is NOT "
    "stable across keepers, so every arm-B delta is quoted against THIS bundle "
    "and never against the committed keeper. It also discharges neiso-70 §4's "
    "own finding, that the destroyed keeper sha makes keeper-relative deltas "
    "charge unattributable code and environment drift to the mechanism. "
    "It arms NOTHING and claims NOTHING: it is scored, registered (rule 15 "
    "[R-DASHBOARD]) and attested only so the comparison is like-for-like."
)

_ATTEST_B = _COMMON + (
    "EXACTLY ONE DELTA against that keeper, measured_chp_heat_rates=true, "
    "applied through replay_keeper --set and recorded in run_config.json "
    "(rule 26 [R-REGISTRY]); it is scored against a SAME-HEAD ZERO-DELTA "
    "CONTROL (neiso81_control_A), never against the committed keeper. "
    "WHAT THE MECHANISM IS. eGRID's PLHTRT for a topping-cycle cogen is "
    "STEAM-CREDITED: the useful thermal output is netted out of the heat input, "
    "so the published rate understates the fuel the plant actually burns to "
    "make the electricity the LP dispatches. This replaces it with eGRID's own "
    "published (PLHTIAN + CHPCHTI)/PLNGENAN — the CHP useful-thermal heat-input "
    "allocation added back, on the SAME NET denominator, so no gross-to-net "
    "factor is involved (that is what blocked the CEMS route, FINDING-miso98 "
    "§6.1). It is a rule 14 [R-ACCURATE] input-accuracy swap and NOTHING ELSE: "
    "no floor, no adder, no override map, no new registry surface. "
    "WHY IT IS RE-ADJUDICATED. neiso-70 (2026-07-31) measured this arm LIVE "
    "with EVERY pre-registered gate PASSING — zero criterion regressions across "
    "all 70 scored records, C1 all 12/12 · free 8/8, C3c bit-identical — and "
    "stamped the cell 'O' rather than 'K' for exactly one reason: fit on the "
    "repriced class degrades. The owner's standing standard of 2026-08-04 ('if "
    "structural integrity improves but gates regress that may still be a "
    "keeper') is what authorises the re-adjudication, and the artifact has "
    "since been CORRECTED under the miso-122 dark-fuel scope gate at neiso-80 "
    "(19 -> 22 columns; (1595, CC_CHP) 9.5584 -> 9.4423). "
    "RE-MEASURED FROM SCRATCH: neiso-70's numbers are NOT reused as this arm's "
    "result — they were measured against a DIFFERENT keeper (the neiso-61 "
    "recipe) and a PRE-gate-3 artifact. "
    "WHAT THE SCOPE GATE DOES NOT DO. At the LP seam the corrected artifact "
    "gives +27.25 % against neiso-70's +27.96 % — a 0.71 pp walk-back, 2.54 % "
    "of the move that produced the overshoot (neiso-80 §1.1 measured 2.15 % on "
    "the artifact population). IT DOES NOT CLOSE THE OVERSHOOT and is not "
    "quoted as if it does. "
    "DO-NOT-REDO HONOURED (rule 28a): no CC_CHP host-steam floor was built and "
    "chp_steam_floor_p25 was NOT armed — neiso-71 closed that route, NEISO's "
    "merchant CC_CHP genuinely carries no host-steam obligation (the non-Kendall "
    "CC_CHP floor totals 15.0 MW across all seven plants) and a Kendall-based "
    "floor would be a FITTED parameter (rules 21 [R-DOF] / 24 [R-REGISTRY]). "
    "Kendall's capacity basis stays ADJUDICATED-ARTIFACT (neiso-73) and "
    "cc_steam_part_capacity NEISO stays 'I' (neiso-80), untested here."
)


def _run_id(arm: str) -> str:
    spec = ARMS[arm]
    path = spec["run_id_file"]
    if path.exists():
        return path.read_text().strip()
    raise SystemExit(
        f"missing {path} — write the registered run id there after dashboard_add_run.py"
    )


def _verdict(run_id: str) -> dict:
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
        for rec in crit.get("rows", []) + crit.get("records", []):
            year = rec.get("year")
            if year is None or rec.get("key") == "da_diagnostic":
                continue
            mag = rec.get("magnitude") or rec.get("detail")
            if mag:
                out[(name, int(year))] = str(mag)
    return out


def _artifact_md5() -> str:
    return hashlib.md5(ARTIFACT.read_bytes()).hexdigest()


def _phase0() -> dict:
    return json.loads(PHASE0_JSON.read_text()) if PHASE0_JSON.exists() else {}


def _ab() -> dict:
    return json.loads(AB_JSON.read_text()) if AB_JSON.exists() else {}


def _dof_entry() -> dict:
    """The ``measured_chp_heat_rates`` DOF entry — zero free parameters."""
    p0 = _phase0()
    wiring = p0.get("wiring", {})
    cc = (wiring.get("classes") or {}).get("CC_CHP", {})
    ct = (wiring.get("classes") or {}).get("CT_CHP", {})
    ab = _ab()
    live = ""
    p6 = ((ab.get("construction_properties") or {}).get("p6") or {}).get("per_year", {})
    if p6:
        live = (
            "Measured effect on THIS keeper, against a same-HEAD zero-delta "
            "control: CC_CHP energy delta "
            + " / ".join(f"{p6[y]['CC_CHP_energy_delta_twh']:+.4f}" for y in sorted(p6))
            + " TWh (2023/2024/2025). "
        )
    return {
        "name": "measured_chp_heat_rates",
        "identification": "measured",
        "classification": (
            "eGRID published CHP heat-input allocation, zero free parameters "
            "(rule 14 [R-ACCURATE] input-accuracy swap)"
        ),
        "value": True,
        "free_parameters_added": 0,
        "source": (
            "eGRID plant file: (PLHTIAN + CHPCHTI) / PLNGENAN, i.e. eGRID's own "
            "published CHP useful-thermal heat-input allocation added back on "
            "the SAME NET denominator as the credited rate it replaces. "
            "Deriver: scripts/data/derive_chp_power_only_heat_rates.py "
            "(--iso NEISO --vintage 2023), including miso-122 scope gate 3 "
            "(dark-fuel exclusion). Artifact: "
            f"{ARTIFACT.relative_to(REPO)} md5 {_artifact_md5()}, 40 rows x 22 "
            "columns, flag census not_unfired_topping 22 / ok 12 / no_egrid_row "
            "5 / basis_mismatch 1. Applied population: CC_CHP 3 rows / 378.2 MW "
            "(6.9636 -> 9.4576), CT_CHP 9 rows / 51.5 MW (8.7009 -> 11.5146). "
            "At the LP seam, at THIS keeper's own ScenarioConfig: "
            f"{wiring.get('generators_moved')} of "
            f"{wiring.get('generators_total')} generators, "
            f"{wiring.get('mw_moved')} MW; CC_CHP cap-weighted heat rate "
            f"{cc.get('capwt_hr_off')} -> {cc.get('capwt_hr_on')} "
            f"({cc.get('pct_dearer')} %), CT_CHP {ct.get('capwt_hr_off')} -> "
            f"{ct.get('capwt_hr_on')} ({ct.get('pct_dearer')} %). {live}"
            "Phase-0 identification record: "
            "results/calibration/_neiso81_chp_phase0.json + "
            "scripts/probes/_neiso81_chp_phase0.py."
        ),
        "why_zero": (
            "Nothing is chosen, tuned or swept. Both the incumbent and the "
            "replacement are PUBLISHED eGRID quantities on the same net "
            "denominator; the swap introduces no coefficient, no threshold and "
            "no percentile. The only screen is the 0.50 thermal-share ceiling, "
            "which is the EPA CHP Partnership unfired gas-turbine envelope, and "
            "the miso-122 dark-fuel scope gate, which is a measured per-unit "
            "CAMPD quantity (NEISO dark share 0.012142 / 0.009584 / 0.014798 "
            "for 2023/2024/2025; the committed artifact is the 2023 vintage, so "
            "9.4423 is the number of record and no vintage is mixed). "
            "VALIDATION: eGRID's (PLHTIAN + CHPCHTI) reproduces independently "
            "metered CAMPD heat input within 1 % on 4/4 covered NEISO plants, "
            "median ratio 1.00000, re-verified this session. "
            "Rule 13 [R-MEASURED]: a plant's heat rate is a physical INPUT that "
            "regenerates for any forward year and responds to changed "
            "conditions — not a measured outcome fed back to close a residual; "
            "no residual was consulted, in either direction. "
            "Rule 23 [R-FROZEN-DERIVE]: the artifact's last re-derive (neiso-80) "
            "cites the miso-122 gate-3 SCOPE CHANGE on measured grounds, never a "
            "residual. Rule 19 [R-ONE-MECH]: nothing is stacked on it — no "
            "host-steam floor is built (neiso-71 closed that route with "
            "evidence) and chp_steam_floor_p25 stays unarmed. Rule 25 "
            "[R-ISO-SCOPE]: MISO's, CAISO's, PJM's and NYISO's K on this "
            "mechanism transfer nothing; NEISO's parameters come from NEISO's "
            "own artifact on NEISO's own data, and no file outside the NEISO "
            "lane was re-derived. n_residual is unchanged."
        ),
    }


def _disclosures(arm: str) -> str:
    """Disclosures, with THIS run's own measured magnitudes substituted in."""
    p0 = _phase0()
    res = p0.get("resolvability", {})
    bnd = p0.get("boundary", {})
    sub = p0.get("substitution", {})
    parts = [
        f"neiso-81 arm {arm} disclosures, reported rather than patched. ",
        "(a) THE ATTRIBUTION-ARTIFACT READING WAS FALSIFIED PRE-SOLVE, AND THIS "
        "SESSION DOES NOT ARGUE IT. The prereg named as load-bearing the "
        "question whether the CC_CHP overshoot is a class-attribution artifact "
        "of the CC_CHP/CC_REGULAR boundary rather than a dispatch error. "
        "Measured at the keeper's own config before any solve: CC_CHP is "
        f"{(bnd.get('classes', {}).get('CC_CHP') or {}).get('n_units')} units / "
        f"{(bnd.get('classes', {}).get('CC_CHP') or {}).get('n_plants')} plants, "
        "CC_REGULAR is "
        f"{(bnd.get('classes', {}).get('CC_REGULAR') or {}).get('n_units')} / "
        f"{(bnd.get('classes', {}).get('CC_REGULAR') or {}).get('n_plants')}, "
        "the plant sets are DISJOINT, no artifact CC_CHP plant sits in the "
        "model's CC_REGULAR class, and the benchmark side "
        "(classFull = e923_bench - btm) buckets EIA-923 through the SAME "
        "plant_taxonomy.classify_plant registry the fleet uses. One registry "
        "applied twice, so a CC_CHP movement is a REAL per-class reallocation, "
        "not a bookkeeping seam. The promotion case does not rest on it. ",
        "(b) WHAT THE CASE DOES REST ON IS RESOLVABILITY, AND IT IS A NUMBER. "
        "C1's per-class volume band is min(2 % of ISO load, 8 TWh). CC_CHP's "
        "ENTIRE annual grid-delivered actual is "
        + " / ".join(f"{res[y]['actual_CC_CHP_twh']:.3f}" for y in sorted(res))
        + " TWh against bands of "
        + " / ".join(f"{res[y]['c1_vol_band_twh']:.3f}" for y in sorted(res))
        + " TWh — "
        + " / ".join(f"{res[y]['CC_CHP_actual_over_band']:.3f}x" for y in sorted(res))
        + ". A class whose whole annual output is roughly half its own "
        "tolerance cannot be discriminated by its C1 row in either direction. "
        "CC_CHP is additionally D-10 pinned / excluded_from_free, so the arm "
        "cannot move the free-class score by construction, and its 2025 row is "
        "SKIPPED on preliminary EIA-923 (3/7 plants missing, 57 % reporting). ",
        "(c) SUBSTITUTION HEADROOM IS AN UPPER BOUND, NEVER A MAGNITUDE "
        "(miso-119 / miso-121). "
        f"{sub.get('CC_REGULAR_cap_mw_cheaper_than_repriced_CHP')} MW of "
        f"CC_REGULAR ({sub.get('CC_REGULAR_cheaper_share_pct')} %) is cheaper "
        "than the repriced CC_CHP population and "
        f"{sub.get('CC_REGULAR_cap_mw_in_traversed_band')} MW sits inside the "
        "traversed heat-rate band. Marginal share, not headroom, is the "
        "predictive statistic and it is only observable post-solve. ",
        "(d) MAGNITUDE WAS NOT PREDICTED, AND THAT WAS STATED AGAINST INTEREST "
        "IN ADVANCE. The prereg recorded that this keeper's CC_REGULAR C1 error "
        "has ALREADY shrunk relative to neiso-70's control (-0.38 / -0.11 TWh "
        "vs -0.471 / -0.340), so the counterweight has LESS room and the "
        "combined-CC improvement neiso-70 reported might not replicate. Only "
        "the SIGN was predicted. ",
        "(e) CHP D-1 / D-2 NUMBERS ARE DIAGNOSTICS, NEVER A PASSED GATE. "
        "CC_CHP and CT_CHP are exempt from BOTH C7 (D1_GATED_CLASSES) and C8 "
        "(D2_EXEMPT_CLASSES) by EXPLICIT CLASS LIST for host-steam-pinned duty "
        "— not by the 2 % materiality floor — so a CHP class above 2 % of load "
        "is still ungated (the caiso-147 protective-framing correction). Any "
        "cv_ratio or profile_r movement on these classes is reported here and "
        "is not offered as evidence in either direction. ",
        "(f) THE CT_CHP LEG IS NOT IDENTIFIED. The artifact's CT_CHP half "
        "covers 19.3 % of class capacity and 0.0 % of the class's metered CAMPD "
        "energy — every covered CT_CHP plant sits below the Part-75 boundary, "
        "so none of them meters (neiso-70 §1). It is reported and must not be "
        "cited as evidence in either direction. ",
        "(g) THE FIRING PROOF IS AT TWO GRAINS, NOT ONE (miso-126(a)). Grain 1 "
        "is the pre-arm fleet-loader rebuild at the keeper's own config "
        "(never the loader defaults, which ship the flag False — the miso-116 "
        "trap); grain 2 is the post-arm per-class ENERGY delta. "
        "tests/unit/data/test_cc_steam_part_capacity.py::TestBackcastFleetSourcing, "
        "which generalises the forwarding guard to EVERY boolean "
        "ScenarioConfig-backed keyword of load_fleet_from_csv, was run this "
        "session and PASSES. Conservation is scored on the FULL identity across "
        "class_hourly + storage + system, not class_hourly alone (miso-126(b)). ",
    ]
    if arm == "A":
        parts.append(
            "(h) THIS BUNDLE ARMS NOTHING. It is the zero-delta control and "
            "makes no claim of its own; it exists so arm B's deltas are "
            "attributable to the mechanism rather than to code or environment "
            "drift, and it is attested only so both arms score on the same "
            "basis (neiso-70 §4: an unattested probe bundle reads NOT-YET / "
            "governance UNATTESTED and its C3c degrades from a ledgered CAVEAT "
            "to a raw FAIL — a scoring artifact of probe bundles that must "
            "apply identically to control and arm)."
        )
    return "".join(parts)


def build(arm: str) -> Path:
    """Write the arm's attestation; return its path."""
    spec = ARMS[arm]
    bundle: Path = spec["bundle"]
    base = json.loads((KEEPER / "calibration_attestation.json").read_text())
    mags = _magnitudes(_verdict(_run_id(arm)))

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
            "attested_by": _ATTEST_A if arm == "A" else _ATTEST_B,
        },
        "disclosures": {"note": _disclosures(arm)},
        "exceptions": [],
    }
    for exc in base["exceptions"]:
        new = dict(exc)
        # A yearless exception (a whole-run adjudication) carries no per-year
        # magnitude to substitute — it is carried forward verbatim.
        year = exc.get("year")
        key = (str(exc.get("criterion")), int(year)) if year is not None else None
        if key is not None and key in mags:
            new["magnitude"] = mags[key]
            new["magnitude_basis"] = (
                f"this run's own scored value (neiso-81 arm {arm}); the "
                "classification and reason are the standing NEISO adjudication "
                "carried forward"
            )
        att["exceptions"].append(new)

    path = bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1) + "\n")
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=sorted(ARMS), required=True)
    args = ap.parse_args()
    arm = args.arm
    spec = ARMS[arm]
    bundle: Path = spec["bundle"]

    path = build(arm)
    print(f"wrote {path.relative_to(REPO)}")

    out = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/build_dof_ledger.py"),
            str(bundle),
            "--iso",
            ISO,
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    print(f"  build_dof_ledger rc={out.returncode} {out.stdout.strip()[-300:]}")
    if out.returncode != 0:
        print(f"  stderr: {out.stderr[-500:]}")

    # build_dof_ledger replaces the whole section and regenerates only the
    # entries it can derive from run_config.json. The keeper carries five more
    # that earlier promoting sessions hand-attached (the RCPF/co-opt block, the
    # gas offer-margin anchor, the phys_* physical-basis keys,
    # measured_ct_heat_rates and nuclear_unit_availability). BOTH arms must
    # carry them or the ledger would silently shrink 12 -> 7 and read as though
    # this session retired five parameters it never touched. The armed arm adds
    # its own entry on top.
    att = json.loads(path.read_text())
    derived = att["free_parameters"].get("entries", [])
    derived_names = {e.get("name") for e in derived}
    carried = [
        e
        for e in json.loads((KEEPER / "calibration_attestation.json").read_text())[
            "free_parameters"
        ].get("entries", [])
        if e.get("name") not in derived_names
    ]
    entries = list(derived) + carried
    added = 0
    if spec["armed"]:
        new = _dof_entry()
        entries = [e for e in entries if e.get("name") != new["name"]]
        entries.append(new)
        added = 1
    att["free_parameters"]["entries"] = entries
    att["free_parameters"]["n_entries"] = len(entries)
    att["free_parameters"]["n_residual"] = sum(
        1 for e in entries if e.get("identification") == "residual"
    )
    path.write_text(json.dumps(att, indent=1) + "\n")
    print(
        f"  re-attached {len(carried)} carried + {added} new DOF entry "
        f"({len(entries)} total, n_residual "
        f"{att['free_parameters']['n_residual']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
