"""Rule-29 screen collateral gate (G-4) for an UNREGISTERED bundle.

The problem this closes (miso-231, ``FINDING-miso231-hourly-seam-screen-2026-09-06.md``
§3): a rule-29 ``[R-SCREEN]`` screen's "no collateral flip" gate asks whether any
non-target load-bearing criterion flips PASS→FAIL against the keeper — but
``scripts/calibration_verdict.py`` scores only a REGISTERED run (it resolves a
registry sidecar + ``runs/<id>.js``), and rule 29(2) forbids registering a screen
bundle. So G-4 was unscorable at the miso-231 screen and only three of five gates
were live. That is a hole in every future screen, for every ISO, not a miso-231
accident.

This tool runs THE SAME scorer, in memory, on the screen bundle's own solve
outputs — the payload is assembled exactly as ``dashboard_add_run.py`` /
``render_backcast.generate`` would assemble it at registration, then round-tripped
through the ``runs/<id>.js`` codec so the scorer reads byte-equivalent input —
and never writes a sidecar, a payload, a bench part or a manifest. The keeper is
scored from its committed artifacts (``calibration_verdict.determine``), and the
two verdicts are compared record-by-record.

The bench (actuals) side is HELD FIXED between the two: the arm is scored against
the COMMITTED per-(ISO, year) bench parts the keeper's verdict reads, never a
bench rebuilt from the arm bundle, so the comparison measures the mechanism and
not a benchmark refresh.

What it is and is not (rule 29 ``[R-SCREEN]``): G-4 is STRUCTURAL and STOP-ONLY.
It may kill an arm; it may never promote one, and nothing it prints is a
determination. A flip is PASS→FAIL on a criterion in ``G4_CRITERIA`` for a
(year, class) cell the keeper carries. C3c is excluded by construction (the
ledgered caveat, rubric v3.3); every other status move — toward or away, PASS to
CAVEAT, SKIPPED either way — is REPORTED at full magnitude and never gated. A
screen bundle normally carries no ``calibration_attestation.json``, so its C6
reads UNATTESTED: that is reported as "not scorable at a screen", not as a flip.

Usage::

    python3 scripts/screen_collateral_gate.py \\
        --bundle results/calibration/<screen_bundle> \\
        --keeper-run-id <registered keeper id> \\
        [--years 2024] [--out results/calibration/_<lane>_g4.json]

Exit status 1 on a flip (the gate FAILS), 0 otherwise. The bundle is never
registered: rule 29(c) still applies and it is deleted before its PR merges.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts import calibration_verdict as cv  # noqa: E402
from scripts.lib import backcast_artifacts as ba  # noqa: E402
from scripts.lib.bundle_io import bundle_meta  # noqa: E402

# The non-target load-bearing / protective criteria a screen's G-4 watches.
# C3c (price_tail) is excluded: the ledgered, non-downgrading caveat (rubric
# v3.3) is never a screen gate. C4 (dispatch_corr) and C8 (forced_share) are
# supporting/protective and reported, not gated, exactly as the miso-231
# PRECOMMIT §4d wrote the bar.
G4_CRITERIA = ("fuelmix", "sysvol", "price_mean", "price_shape", "governance")
REPORTED_CRITERIA = ("dispatch_corr", "forced_share")


def _load_committed_bench(iso: str) -> dict[int, dict]:
    """The committed per-(ISO, year) bench parts, exactly as the scorer reads them."""
    bench: dict[int, dict] = {}
    for part in sorted((cv.BENCH_DIR / iso).glob("*.json.gz")):
        obj = ba.load_bench_part(part)
        for y in obj.get("meta", {}).get("years", []):
            bench[int(y)] = obj.get("bench", {})
    return bench


def screen_artifacts(
    bundle: Path, label: str, years: set[int] | None
) -> tuple[str, dict]:
    """Assemble the scorer's artifact dict for an UNREGISTERED bundle, in memory.

    Mirrors ``calibration_verdict.load_artifacts`` field-for-field, with the
    sidecar and payload derived from the bundle the way registration derives
    them, and nothing written under ``frontend/``.
    """
    from scripts import render_backcast as rb
    from scripts import render_calibration_html as rch

    entry = rb.manifest_entry(label, bundle)
    if years is not None:
        entry["years"] = [y for y in entry["years"] if int(y) in years]
    rid, iso = entry["id"], entry["iso"]
    try:
        entry["bundle"] = str(bundle.resolve().relative_to(REPO))
    except ValueError:
        entry["bundle"] = str(bundle)

    built = rch.build_payload([(label, bundle)], years=years)
    model = built["model"][0]
    model["label"] = entry["label"]
    # Round-trip through the runs/<id>.js codec so the scorer reads exactly
    # what a registered payload would decode to (float/int/key normalisation).
    payload = ba.decode_run_js(ba.encode_run_js(rid, model))

    rc = bundle / "run_config.json"
    config = {
        "scenario_config": (
            json.loads(rc.read_text()).get("scenario_config", {}) if rc.exists() else {}
        ),
        "meta": bundle_meta(bundle),
    }
    att = bundle / "calibration_attestation.json"
    legit = bundle / "legitimacy_diagnostics.json"
    return rid, {
        "sidecar": entry,
        "payload": payload,
        "bench": _load_committed_bench(iso),
        "config": config,
        "attestation": json.loads(att.read_text()) if att.exists() else None,
        "legitimacy": json.loads(legit.read_text()) if legit.exists() else None,
    }


def _cell_key(rec: dict) -> tuple:
    return (rec.get("year"), rec.get("key"))


def _gap(rec: dict) -> float | None:
    m, a = rec.get("model"), rec.get("actual")
    if isinstance(m, (int, float)) and isinstance(a, (int, float)):
        return float(m) - float(a)
    return None


def compare_verdicts(
    keeper_v: dict, arm_v: dict, years: set[int] | None = None
) -> dict:
    """Record-by-record G-4 comparison of two verdict dicts (pure; testable).

    Returns ``{"flips": [...], "moves": [...], "unscorable": [...], "verdict"}``.
    A flip is keeper PASS → arm FAIL on a ``G4_CRITERIA`` cell. Every status or
    magnitude change on a gated or reported criterion is a move (reported, not
    gated). A criterion the arm cannot score (no attestation ⇒ C6 UNATTESTED;
    SKIPPED on both sides) is listed as unscorable.
    """
    flips: list[dict] = []
    moves: list[dict] = []
    unscorable: list[dict] = []

    for cid in G4_CRITERIA + REPORTED_CRITERIA:
        gated = cid in G4_CRITERIA
        k_recs = {
            _cell_key(r): r
            for r in keeper_v["criteria"].get(cid, {}).get("records", [])
        }
        a_recs = {
            _cell_key(r): r for r in arm_v["criteria"].get(cid, {}).get("records", [])
        }
        for cell, a in a_recs.items():
            year = cell[0]
            if years is not None and year is not None and int(year) not in years:
                continue
            k = k_recs.get(cell)
            if k is None:
                continue
            ks, as_ = k["status"], a["status"]
            row = {
                "criterion": cid,
                "year": year,
                "key": cell[1],
                "keeper_status": ks,
                "arm_status": as_,
                "keeper_magnitude": k.get("magnitude"),
                "arm_magnitude": a.get("magnitude"),
            }
            kg, ag = _gap(k), _gap(a)
            if kg is not None and ag is not None:
                row["keeper_gap"] = round(kg, 3)
                row["arm_gap"] = round(ag, 3)
                row["direction"] = (
                    "toward"
                    if abs(ag) < abs(kg) - 1e-9
                    else ("away" if abs(ag) > abs(kg) + 1e-9 else "flat")
                )
            if as_ == "UNATTESTED" or (ks == cv.SKIPPED and as_ == cv.SKIPPED):
                row["note"] = (
                    "not scorable at a screen (no attestation)"
                    if as_ == "UNATTESTED"
                    else "SKIPPED on both sides"
                )
                unscorable.append(row)
                continue
            if gated and ks == cv.PASS and as_ == cv.FAIL:
                row["gated"] = True
                flips.append(row)
            if ks != as_ or row.get("direction") not in (None, "flat"):
                row["gated"] = gated
                moves.append(row)

    return {
        "flips": flips,
        "moves": moves,
        "unscorable": unscorable,
        "verdict": "FAIL" if flips else "PASS",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument(
        "--bundle", required=True, help="the UNREGISTERED screen bundle dir"
    )
    ap.add_argument(
        "--keeper-run-id", required=True, help="the registered keeper's run id"
    )
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=None,
        help="screen years to compare (default: every year the bundle solved)",
    )
    ap.add_argument(
        "--label", default=None, help="payload label (default: bundle name)"
    )
    ap.add_argument("--out", default=None, help="write the JSON record here")
    args = ap.parse_args()

    bundle = Path(args.bundle)
    if not bundle.is_absolute():
        bundle = REPO / bundle
    if not (bundle / "meta.json").exists():
        sys.exit(f"{bundle} has no meta.json — not a solved bundle")
    years = set(args.years) if args.years else None

    rid, art = screen_artifacts(bundle, args.label or bundle.name, years)
    arm_v = cv.determine_from_artifacts(
        rid, art, years=sorted(years) if years else None
    )
    keeper_v = cv.determine(args.keeper_run_id)
    cmp = compare_verdicts(keeper_v, arm_v, years)

    out = {
        "gate": "G-4 no collateral flip (rule 29 screen; STOP-only, never promotes)",
        "bar": (
            "no non-target load-bearing criterion "
            f"({', '.join(G4_CRITERIA)}) flips PASS->FAIL vs the keeper's committed "
            "scores; C3c excluded (ledgered caveat, rubric v3.3); every other move "
            "reported, not gated"
        ),
        "keeper": args.keeper_run_id,
        "arm_bundle": bundle.name,
        "arm_scored_as": rid,
        "years": sorted(years) if years else arm_v.get("scorable_years"),
        "bench": "committed frontend/data/backcast/bench parts (held fixed)",
        "arm_determination_NOT_A_RESULT": arm_v["determination"],
        **cmp,
    }
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
        print(f"wrote {args.out}")

    print(
        f"[{cmp['verdict']:>4}] G-4 no collateral flip  ({len(cmp['flips'])} flip(s))"
    )
    for f in cmp["flips"]:
        print(
            f"   FLIP {f['criterion']} {f['year']} {f['key']}: {f['keeper_status']} -> {f['arm_status']}  {f.get('keeper_magnitude')} -> {f.get('arm_magnitude')}"
        )
    print("--- moves (reported, not gated) ---")
    for m in cmp["moves"]:
        d = m.get("direction", "")
        print(
            f"   {m['criterion']:<13} {m['year']} {str(m['key']):<14} "
            f"{m['keeper_status']:>7} -> {m['arm_status']:<7} {d:<6} "
            f"{m.get('keeper_gap', '')} -> {m.get('arm_gap', '')}"
        )
    for u in cmp["unscorable"]:
        print(f"   unscorable: {u['criterion']} {u['year']} {u['key']}: {u['note']}")
    return 1 if cmp["flips"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
