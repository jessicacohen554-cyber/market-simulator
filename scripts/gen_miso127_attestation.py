"""Write the calibration attestation for the miso-127 ``coal_mustrun_online_pmin`` arm.

The arm is a ``replay_keeper`` re-solve of the ``2026-08-04-miso-126-steampart-b``
keeper's own ``meta.json`` at this session's HEAD with exactly one delta,
``coal_mustrun_online_pmin=true``. The governance posture, the standing
measured-input ledger entries and the DOF ledger are therefore the keeper's —
carried forward verbatim in *classification and reason*, with this run's **own**
measured magnitudes substituted from its own scored verdict so no number in the
attestation describes a different run (the miso-116 §7 basis discipline, applied
at miso-117 / 119 / 121 / 124 / 126 and again here).

It carries one new DOF entry, ``coal_mustrun_online_pmin``, which adds **zero
free parameters**: the flag selects one already-committed measured column of
``thermal_tranches_MISO.csv`` (``mustrun_online_pct``) in place of another
(``mustrun_pct``). No coefficient, threshold or percentile is introduced by this
session, and no value is swept.

Run AFTER the bundle is registered and its legitimacy diagnostics are written,
and BEFORE the final ``calibration_verdict.py --write-metrics`` pass, since C6
reads the attestation and the ledger entries reclassify C3a / C3c.

Usage::

    uv run python scripts/gen_miso127_attestation.py [--bundle DIR --run-id ID]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

KEEPER = REPO / "results/calibration/miso126_steampart_B"
AB_JSON = REPO / "results/calibration/_miso127_online_pmin_ab.json"

_ATTEST = (
    "miso-127, 2026-08-04. This arm is a replay_keeper re-solve of the "
    "2026-08-04-miso-126-steampart-b keeper's own meta.json at this session's "
    "HEAD, --years 2023 2024 2025 in ONE invocation (rules 12 / 16), years "
    "sequential inside the invocation. EXACTLY ONE DELTA against that keeper, "
    "coal_mustrun_online_pmin=true, applied through replay_keeper --set and "
    "recorded in run_config.json (rule 26 [R-REGISTRY]); a programmatic diff of "
    "the two scenario blocks returns exactly one differing key, and it is scored "
    "against a SAME-HEAD ZERO-DELTA CONTROL (miso127_onlinepmin_A), never "
    "against the committed keeper — miso-124's DO-NOT-MISREAD is that the price "
    "response is not stable across keepers. "
    "WHAT THE MECHANISM IS. The coal must-run (cheap, fuel-sunk) tranche is "
    "sized from the MEASURED online minimum stable load — the net MW a unit "
    "holds 95 % of its ONLINE time (thermal_tranches_MISO.csv "
    "mustrun_online_pct) — instead of the all-hours available-CF P5 "
    "(mustrun_pct), which is a biased proxy for it because an always-online "
    "unit's all-hours P5 sits inside its normal operating band and the "
    "outage-derate denominator inflates the available CF. In the energy-only LP "
    "that tranche has Pmin = 0, so this changes the SIZE OF THE CHEAP BID BAND "
    "and is NOT a forced floor: capacity leaving the band enters the "
    "full-delivered-cost rising tranches, where it price-follows. It is a "
    "rule 14 [R-ACCURATE] measured-input swap — a proxy replaced by the "
    "quantity it estimates — and NOTHING IS STACKED on the take-or-pay "
    "committed-band discount whose residual owns C7 (rule 19 [R-ONE-MECH]): no "
    "floor is added, and the discount itself is untouched. "
    "THE EXPECTED-INERT PRIOR WAS REFUTED EX ANTE, AND THAT IS WHY THIS WAS "
    "SOLVED. The field's own docstring predicts the all-hours figure 'reads ~2x "
    "high'; that was measured on ERCOT and is FALSE at MISO, where the "
    "capacity-weighted ratio is 0.956 (28.886 % -> 27.609 % over 44 coal plants "
    "/ 41,770.8 MW). But the -533.1 MW NET hides 7,528.1 MW GROSS — 18 % of the "
    "coal fleet — reallocating on 39 of 44 plants in OPPOSITE directions "
    "(20 grow, 19 shrink, per-plant delta -43.2 to +60.0 pp), and the p50 moves "
    "the other way (25.20 -> 28.00). A zero-solve inert declaration built on the "
    "net would have been exactly the cancelling-aggregate error the "
    "miso-119 / 122 / 125 DO-NOT-MISREADs warn against, so the pre-registration "
    "recorded the prior as wrong and chartered the A/B. "
    "FIRING IS PROVEN AT TWO GRAINS (the miso-126 §4 rule). Grain 1, pre-arm: "
    "calling fleet_to_bins directly with the flag off vs on over the MISO 2023 "
    "fleet moves pct_mr on 42 coal bins and pct_econ on 39 (gross 867.8 pp). "
    "Grain 2, post-arm: the per-class ENERGY delta against the control "
    "(miso-122's DO-NOT-MISREAD — max_abs_class_hour_mw is NOT a mechanism "
    "magnitude at MISO). The flag is config-borne, not a load_fleet_from_csv "
    "keyword, so it does not pass through the seam that silently dropped "
    "miso-126's first arm; that was verified in source and then measured. "
    "RULE 22 [R-HOLDOUT]: 2023-2025 only. MISO holds no calibration-complete "
    "marker, so no holdout year was solved, scored or read. "
    "RULE 23 [R-FROZEN-DERIVE]: NO re-derive was performed — the committed MISO "
    "artifact already carries mustrun_online_pct, so the data gate the field's "
    "docstring names was already satisfied and only the solve was missing. "
    "RULE 24 [R-REGISTRY]: no new field, no fitted value, nothing swept; the "
    "flag is an already-registered ScenarioConfig boolean and every number it "
    "selects is read from a committed artifact. "
    "RULE 25 [R-ISO-SCOPE]: the flag is K on the PJM keeper, but that verdict "
    "does NOT transfer — it entered MISO as U and MISO's band is derived from "
    "MISO's own CAMPD conduct via its own thermal_tranches_MISO.csv."
)


def _ab() -> dict:
    return json.loads(AB_JSON.read_text()) if AB_JSON.exists() else {}


def _disclosures() -> str:
    base = json.loads((KEEPER / "calibration_attestation.json").read_text())
    return str((base.get("disclosures") or {}).get("note") or "")


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
        for rec in crit.get("records", []):
            year = rec.get("year")
            if year is None or rec.get("key") == "da_diagnostic":
                continue
            mag = rec.get("magnitude") or rec.get("detail")
            if mag:
                out[(name, int(year))] = str(mag)
    return out


def _dof_entry() -> dict:
    """The ``coal_mustrun_online_pmin`` DOF entry.

    Zero free parameters: the flag is a SELECTOR between two measured columns
    of an already-committed artifact. This session introduces no coefficient,
    threshold or percentile, and sweeps nothing.
    """
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
        "name": "coal_mustrun_online_pmin",
        "identification": "measured",
        "classification": (
            "measured CAMPD unit conduct, zero free parameters added "
            "(rule 14 [R-ACCURATE] proxy-for-measurand swap)"
        ),
        "value": True,
        "free_parameters_added": 0,
        "source": (
            "data/raw/_processed-legacy/thermal_tranches_MISO.csv, column "
            "mustrun_online_pct — the net MW a unit holds 95 % of its ONLINE "
            "time, as a fraction of nameplate, derived from CAMPD unit-level "
            "hourly gross load by scripts/data/derive_thermal_tranches.py. "
            "Consumed by data/fleet/campd_bins.py (:1645) via the config, and "
            "applied in the bin synthesis both orchestrators run. MISO values: "
            "capacity-weighted 27.609 % against the incumbent mustrun_pct's "
            f"28.886 % over 44 coal plants / 41,770.8 MW. {measured}"
            "The Phase-0 identification record — the artifact statistics, the "
            "net-vs-gross decomposition and the pre-arm grain-1 firing check — "
            "is committed in results/calibration/"
            "PREREG-miso127-takeorpay-period-budget-2026-08-04.md §2 and "
            "scripts/probes/_miso127_budget_reshape_precheck.py."
        ),
        "why_zero": (
            "Nothing is chosen, tuned or swept by this session. The flag is a "
            "BOOLEAN SELECTOR between two columns that both already exist in a "
            "committed artifact, and it selects the one that measures the "
            "quantity the model means: the incumbent mustrun_pct is an "
            "all-hours available-CF P5, a BIASED PROXY for the online minimum "
            "stable load, while mustrun_online_pct measures that load directly "
            "on the hours the unit is actually synchronized. Rule 13 "
            "[R-MEASURED]: a unit's online minimum stable load is a physical "
            "operating characteristic that regenerates for any forward year "
            "from the same CEMS input-output record and responds to changed "
            "conditions (a re-rate, a retrofit or a retirement moves it) — it "
            "is not a measured OUTCOME fed back to close a residual, and it is "
            "not sized against any price or volume gap. Rule 23 "
            "[R-FROZEN-DERIVE]: no re-derive was performed in this session; the "
            "column was already committed. The 95 % online-time percentile "
            "lives in the frozen derive script and is the incumbent's own "
            "convention, not a knob introduced here. Rule 19 [R-ONE-MECH]: this "
            "REPLACES a proxy inside the existing coal must-run sizing rather "
            "than stacking a new mechanism on the take-or-pay discount's "
            "residual; no floor is added and the discount is untouched. "
            "n_residual is unchanged."
        ),
    }


def build(bundle: Path, run_id: str) -> Path:
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
            "attested_by": _ATTEST,
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
                "this run's own scored value (miso-127); the classification and "
                "reason are the standing MISO adjudication carried forward"
            )
        att["exceptions"].append(new)

    path = bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1) + "\n")
    return path


def main() -> int:
    """Write the attestation, re-seed the DOF ledger, re-attach the entries."""
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--bundle",
        default="results/calibration/miso127_onlinepmin_B",
        help="bundle dir to write the attestation into",
    )
    ap.add_argument(
        "--run-id", default="", help="dashboard run id for calibration_verdict"
    )
    ap.add_argument(
        "--control",
        action="store_true",
        help="this is the zero-delta control arm: carry the keeper's DOF ledger "
        "forward WITHOUT the coal_mustrun_online_pmin entry",
    )
    args = ap.parse_args()
    bundle = REPO / args.bundle
    run_id = args.run_id or json.loads((bundle / "meta.json").read_text()).get(
        "run_id", ""
    )
    if not run_id:
        raise SystemExit("--run-id is required (meta.json carries none)")

    path = build(bundle, run_id)
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
    # cannot know: the keeper's carried-forward entries and (arm B only) this
    # session's own coal_mustrun_online_pmin entry.
    att = json.loads(path.read_text())
    keeper_entries = json.loads((KEEPER / "calibration_attestation.json").read_text())[
        "free_parameters"
    ].get("entries", [])
    carried = [
        e
        for e in keeper_entries
        if e.get("name") in ("dual_fuel_switching", "cc_steam_part_capacity")
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
