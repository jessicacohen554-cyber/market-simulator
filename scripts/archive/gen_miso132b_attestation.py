"""Write the calibration attestation for the miso-132(b) CC committed-band arm.

The arm is a ``replay_keeper`` re-solve of the ``2026-08-04-miso-127-onlinepmin``
keeper's own ``meta.json`` at this session's HEAD with exactly one mechanism
changed: both CC ``committed`` (min-stable-load) offer bands take the fleet's own
MEASURED min-load block-average burn. The governance posture, the standing
measured-input ledger entries and the DOF ledger are therefore the keeper's —
carried forward verbatim in *classification and reason*, with this run's **own**
measured magnitudes substituted from its own scored verdict so no number in the
attestation describes a different run (the miso-116 §7 basis discipline, applied
at miso-117 / 119 / 121 / 124 / 126 / 127 and again here).

It carries one new DOF entry, ``cc_committed_band_measured``, which adds **zero
free parameters**: the two registered multipliers are replaced by a value read
off an already-committed measured artifact. Nothing is chosen, tuned or swept.

Run AFTER the bundle is registered and its legitimacy diagnostics are written,
and BEFORE the final ``calibration_verdict.py --write-metrics`` pass, since C6
reads the attestation and the ledger entries reclassify C3a / C3c.

Usage::

    uv run python scripts/gen_miso132b_attestation.py --bundle DIR --run-id ID
                                                      [--control]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent

KEEPER = REPO / "results/calibration/miso127_onlinepmin_B"
AB_JSON = REPO / "results/calibration/_miso132b_cc_committed_ab.json"

MEASURED_COMMITTED = 1.005
REGISTERED_BEFORE = {"CC_REGULAR": 1.20, "CC_INTERMEDIATE": 0.92}

_ATTEST = (
    "miso-132(b), 2026-08-05. This arm is a replay_keeper re-solve of the "
    "2026-08-04-miso-127-onlinepmin keeper's own meta.json at this session's "
    "HEAD, --years 2023 2024 2025 in ONE invocation (rules 12 / 16), years "
    "sequential inside the invocation. EXACTLY ONE MECHANISM CHANGES against "
    "that keeper — the CC min-stable-load (committed) offer band — applied "
    "through replay_keeper --set offer_curve_by_group and recorded verbatim in "
    "run_config.json (rule 26 [R-REGISTRY]); a programmatic diff of the two "
    "scenario blocks returns exactly one differing key and, inside it, exactly "
    "the two committed entries. It is scored against a SAME-HEAD ZERO-DELTA "
    "CONTROL (miso132_ccmin_A), never against the committed keeper — miso-124's "
    "DO-NOT-MISREAD is that the price response is not stable across keepers. "
    "WHAT THE MECHANISM IS. Both CC committed bands take the fleet's OWN "
    "measured min-load block-average burn, avg_committed_p50 = 1.005 (n = 103 "
    "CC units, capacity-weighted, 2023-2025 pooled, "
    "data/raw/reference/miso_campd_marginal_hr_summary.csv), replacing "
    "CC_REGULAR's 1.20 — a generic 'a CC's part-load $/MWh is ~30-40 % above "
    "its full-load SRMC' claim that PREDATES that artifact — and "
    "CC_INTERMEDIATE's 0.92, the generic default that backcast_config.py's own "
    "comment calls 'an unphysical, artificially-cheap min-load block'. Both are "
    "the SAME physical quantity on the SAME 103 measured units: "
    "cc_intermediate_split is a duty-cycle ROUTING, not a different measurand. "
    "It is a rule 14 [R-ACCURATE] proxy-for-measurand swap, and the "
    "CC_REGULAR dict ALREADY CARRIED the measured value as phys_committed "
    "1.005 — used only as the gas_offer_margin markup basis (markup "
    "max(0, 1.20 - 1.005) = 0.195, about $4.4/MWh at the ISO anchor), never as "
    "the band itself. CT_PEAKER's committed band is already grounded on its own "
    "measured value (1.025 = registered = phys, markup 0); CC's was not. "
    "BOTH COHORTS MOVE TOGETHER, AND THAT IS THE POINT. Moving only CC_REGULAR "
    "(cheaper) or only CC_INTERMEDIATE (dearer) would be CHOOSING THE "
    "DIRECTION — the forbidden path (rules 1 / 24). The pre-registration "
    "declared the two-sided prior in advance and PRE-ACCEPTED the adverse case: "
    "because cc_intermediate_split routes the bulk of MISO's baseload CC fleet "
    "to the 0.92 cohort, the NET expected direction on the July night clearing "
    "was UP, which would move the C7 target the WRONG way (miso-130 §3: a "
    "higher overnight floor freezes MORE of the cheap PRB econ ladder out of "
    "the diurnal wave). Under rules 1 [R-STRUCT] and 14 the accurate input "
    "stays in and a worsened fit is a DISCOVERED BUG pointing at the real root "
    "cause, never grounds to revert to 0.92 / 1.20 — and equally, a C7 gain is "
    "not by itself grounds to promote. "
    "ZERO FREE PARAMETERS. No value is chosen, swept or fitted: 1.005 is read "
    "off a committed artifact that re-derives only when its source data changes "
    "(rule 23 [R-FROZEN-DERIVE]; no derive was run in this session). "
    "phys_committed is untouched, so under the keeper's armed gas_offer_margin "
    "both bands land at markup 0 — the measured block-average burn with no "
    "adder. Rule 19 [R-ONE-MECH]: this REPLACES an ungrounded multiplier inside "
    "the existing CC offer surface rather than stacking a new mechanism on any "
    "residual; no floor is added, no forced energy is created, and the coal "
    "take-or-pay discount that owns C7 is untouched. n_residual is unchanged. "
    "ARMING CHANNEL, disclosed. The pre-registration named --offer-curve-json; "
    "that channel CANNOT express this mechanism, because "
    "pipeline/persist.py::parse_offer_curve_json validates class keys against "
    "plant_taxonomy.fossil_classes() and CC_INTERMEDIATE is an offer-curve "
    "ROUTING key, not a taxonomy class. This was found by reading the validator "
    "BEFORE any arm was solved and before any lane-(b) number existed, and the "
    "response was to change the TRANSPORT (--set offer_curve_by_group, which "
    "routes through prb_overrides and is applied last in run_year), NOT the "
    "scope: narrowing to CC_REGULAR alone was considered and REFUSED because it "
    "is the direction-flattering half. The arm-B JSON is generated "
    "programmatically from arm A's own committed run_config.json with only the "
    "two committed entries changed, so the band diff is byte-exact by "
    "construction. Still no code edit (the miso-122 reproducibility seam). "
    "HOLDOUT. Rule 22 [R-HOLDOUT]: MISO holds NO calibration-complete marker. "
    "Both arms solve and score 2023-2025 ONLY; no out-of-training year was "
    "solved, scored or read in this session."
)

_CONTROL_ATTEST = (
    "miso-132(b) ARM A, 2026-08-05. SAME-HEAD ZERO-DELTA CONTROL: a "
    "replay_keeper re-solve of the 2026-08-04-miso-127-onlinepmin keeper's own "
    "meta.json at this session's HEAD with NO delta of any kind, --years 2023 "
    "2024 2025 in ONE invocation (rules 12 / 16). Its only purpose is to be the "
    "baseline every miso-132(b) delta is quoted against, because the price "
    "response is not stable across keepers (miso-124) and a zero-delta control "
    "has been observed to diverge from its own incumbent at GW scale "
    "(caiso-146). It introduces NO mechanism and NO free parameter, and it is "
    "NOT a promotion candidate. Rule 22: 2023-2025 only."
)


def _disclosures() -> str:
    base = json.loads((KEEPER / "calibration_attestation.json").read_text())
    return (base.get("disclosures") or {}).get("note", "")


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
    # rc 1 is a NOT-YET determination, not a failure (gen_miso127 pattern).
    if out.returncode not in (0, 1) or not out.stdout.strip():
        raise SystemExit(f"calibration_verdict failed:\n{out.stderr[-2000:]}")
    return json.loads(out.stdout)


def _magnitudes(verdict: dict) -> dict:
    out: dict = {}
    for name, crit in verdict["criteria"].items():
        for rec in crit.get("records", []):
            year = rec.get("year")
            if year is None or rec.get("key") == "da_diagnostic":
                continue
            mag = rec.get("magnitude") or rec.get("detail")
            if mag:
                out[(name, int(year))] = str(mag)
    return out


def _ab() -> dict:
    return json.loads(AB_JSON.read_text()) if AB_JSON.exists() else {}


def _dof_entry() -> dict:
    """The ``cc_committed_band_measured`` DOF entry — zero free parameters."""
    ab = _ab()
    dl = ab.get("max_zonal_abs_dlmp", {})
    measured = ""
    if dl:
        measured = (
            "Measured effect on THIS keeper, against a same-HEAD zero-delta "
            "control: max zonal |dLMP| "
            + " / ".join(f"{dl[y]:.6f}" for y in sorted(dl))
            + " $/MWh. "
        )
    return {
        "name": "cc_committed_band_measured",
        "identification": "measured",
        "classification": (
            "measured CAMPD unit conduct, zero free parameters added "
            "(rule 14 [R-ACCURATE] proxy-for-measurand swap)"
        ),
        "value": MEASURED_COMMITTED,
        "free_parameters_added": 0,
        "source": (
            "data/raw/reference/miso_campd_marginal_hr_summary.csv, row "
            "CC_REGULAR, column avg_committed_p50 = 1.005 (n = 103 CC units, "
            "capacity-weighted, 2023-2025 pooled; base_hr 7.436) — the min-load "
            "block's AVERAGE burn relative to the plant's own base heat rate, "
            "derived from CAMPD unit-level hourly load by "
            "scripts/data/derive_campd_marginal_hr.py --iso MISO. It replaces "
            "the registered CC_REGULAR committed 1.20 and CC_INTERMEDIATE "
            "committed 0.92. The measured value was ALREADY committed in the "
            "same offer-curve dict as phys_committed, used only as the "
            f"gas_offer_margin markup basis. {measured}"
            "The pre-registration and its pre-check record are committed in "
            "results/calibration/"
            "PREREG-miso132b-cc-committed-band-regrounding-2026-08-05.md and "
            "scripts/probes/_miso132b_cc_committed_precheck.py."
        ),
        "why_zero": (
            "Nothing is chosen, tuned or swept by this session. Two registered "
            "multipliers are replaced by ONE value read off an artifact that "
            "was already committed and that re-derives only when its source "
            "data changes (rule 23 [R-FROZEN-DERIVE]; no derive was run here). "
            "Rule 13 [R-MEASURED]: a CC's min-load block-average burn is a "
            "physical operating characteristic that regenerates for any forward "
            "year from the same CEMS input-output record and responds to "
            "changed conditions (a re-rate, a retrofit or a retirement moves "
            "it) — it is not a measured OUTCOME fed back to close a residual, "
            "and it is sized against no price or volume gap. Both cohorts move "
            "TOGETHER precisely so the DIRECTION is not chosen: CC_REGULAR "
            "alone would be cheaper (the C7-flattering half) and "
            "CC_INTERMEDIATE alone dearer, and the pre-registration declared "
            "the net expected direction (UP, the ADVERSE one) in advance and "
            "pre-accepted it. Rule 19 [R-ONE-MECH]: this REPLACES an ungrounded "
            "multiplier inside the existing CC offer surface rather than "
            "stacking a mechanism on a residual; no floor is added and the "
            "coal take-or-pay discount that owns C7 is untouched. n_residual is "
            "unchanged."
        ),
    }


def build(bundle: Path, run_id: str, control: bool) -> Path:
    """Write the arm's attestation; return its path."""
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
            "attested_by": _CONTROL_ATTEST if control else _ATTEST,
        },
        "disclosures": {"note": _disclosures()},
        "exceptions": [],
    }
    for exc in base["exceptions"]:
        new = dict(exc)
        key = (str(exc.get("criterion")), int(exc.get("year")))
        if key in mags:
            new["magnitude"] = mags[key]
            new["magnitude_basis"] = (
                "this run's own scored value (miso-132(b)); the classification "
                "and reason are the standing MISO adjudication carried forward"
            )
        att["exceptions"].append(new)

    path = bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1) + "\n")
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", required=True, help="bundle dir")
    ap.add_argument("--run-id", default="", help="dashboard run id")
    ap.add_argument(
        "--control",
        action="store_true",
        help="this is the zero-delta control arm: carry the keeper's DOF ledger "
        "forward WITHOUT the cc_committed_band_measured entry",
    )
    args = ap.parse_args()
    bundle = (
        REPO / args.bundle if not Path(args.bundle).is_absolute() else Path(args.bundle)
    )
    run_id = args.run_id or json.loads((bundle / "meta.json").read_text()).get(
        "run_id", ""
    )
    if not run_id:
        raise SystemExit("--run-id is required (meta.json carries none)")

    path = build(bundle, run_id, args.control)
    print(f"wrote {path.relative_to(REPO)}")
    out = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/build_dof_ledger.py"),
            str(bundle),
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
    # build_dof_ledger replaces the whole section, so re-attach the entries it
    # cannot know: the keeper's carried-forward entries (this arm replays the
    # keeper, so they are all still armed) and, on arm B only, this session's
    # own cc_committed_band_measured entry.
    att = json.loads(path.read_text())
    keeper_entries = json.loads((KEEPER / "calibration_attestation.json").read_text())[
        "free_parameters"
    ].get("entries", [])
    carried = [
        e
        for e in keeper_entries
        if e.get("name")
        in ("dual_fuel_switching", "cc_steam_part_capacity", "coal_mustrun_online_pmin")
    ]
    new = None if args.control else _dof_entry()
    keep_names = {e["name"] for e in carried} | ({new["name"]} if new else set())
    entries = [
        e
        for e in att["free_parameters"].get("entries", [])
        if e.get("name") not in keep_names
    ]
    entries.extend(carried)
    if new:
        entries.append(new)
    att["free_parameters"]["entries"] = entries
    att["free_parameters"]["n_entries"] = len(entries)
    att["free_parameters"]["n_residual"] = sum(
        1 for e in entries if e.get("identification") == "residual"
    )
    path.write_text(json.dumps(att, indent=1) + "\n")
    print(
        f"  re-attached {len(carried)} carried + {1 if new else 0} new DOF entry "
        f"({len(entries)} total, n_residual "
        f"{att['free_parameters']['n_residual']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
