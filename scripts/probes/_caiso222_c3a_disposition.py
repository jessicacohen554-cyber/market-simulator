"""caiso-222 owner-sitting instrument: the C3a disposition re-measurement.

Re-measures the caiso-186 §b.2 six-keeper table on TODAY's designated keepers
(the ERCOT two-config structure included) and computes, mechanically, what a
model-class-style C3a ledger disposition would change per ISO under the guard
variants — from committed artifacts ONLY, via ``scripts/calibration_verdict``.
NO LP, NO SOLVE, no scorer constant is modified: the counterfactuals are
post-processing over each run's scored per-criterion table, applying the
aggregation semantics ``calibration_verdict.determine`` documents (explicit
ledger → C3c standing rule → budgets → the v3.3 non-downgrading branch), with
the single hypothetical change that a C3a (``price_mean``) FAIL is admitted to
reclassify as a ledgered model-class CAVEAT. Decision-support arithmetic for
``ASSESSMENT-caiso222-owner-sitting-2026-08-30.md`` — it arms nothing,
proposes nothing, and changes no rubric constant.

Variants (each computed at ledgered-caveat budget 1 AND 2):
  * ``E``  — explicit-entry form: every C3a FAIL reclassifies (an owner-signed
    exhaustion-cited entry is assumed WHEREVER a lane would write one).
  * ``S``  — standing-rule form (the C3c rule's guards (a)-(d) transposed):
    C3a reclassifies only where it is the LONE failing criterion over
    CRITERIA membership and governance PASSes.
After the C3a reclassification the EXISTING C3c standing rule is re-evaluated
exactly as ``_apply_c3c_standing_rule`` would see the table (lone remaining
C3c FAIL + governance PASS → ledgered CAVEAT), because in the real scorer the
explicit ledger runs first and the standing rule second.

Record: ``results/calibration/_caiso222_c3a_disposition.json`` (deterministic:
sorted keys, no timestamps).

Usage: ``PYTHONPATH=.:src python3 scripts/probes/_caiso222_c3a_disposition.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import calibration_verdict as cv  # noqa: E402

OUT = REPO / "results" / "calibration" / "_caiso222_c3a_disposition.json"

# The seven designated configs (six keeper shards; ERCOT contributes its
# two-config partition — owner ruling 2026-08-26, keepers/ERCOT.json — so its
# forward keeper's registered 3-year record, its designated 2024-2025 span
# read, and the 2023 carve-out are each scored).
CONFIGS = [
    ("CAISO", "2026-08-26-caiso-220-c1-crosswalk", None),
    ("ERCOT", "2026-08-25-234-eastex-identity", None),
    ("ERCOT", "2026-08-25-234-eastex-identity", [2024, 2025]),
    ("ERCOT", "2026-08-25-236-swcap-clip-k33", None),
    ("MISO", "2026-08-30-miso-188-rvsscope", None),
    ("NEISO", "2026-08-17-neiso-99-joint-p1", None),
    ("NYISO", "2026-08-25-nyiso-155-hydro-repair", None),
    ("PJM", "2026-08-15-pjm-162-inputclock", None),
]


def _crit_table(verdict: dict) -> dict[str, dict]:
    """Reduce a verdict to {criterion: {status, tier, caveat_kind}} over CRITERIA."""
    out: dict[str, dict] = {}
    for cid, c in verdict["criteria"].items():
        if cid not in cv.CRITERIA:
            continue
        out[cid] = {
            "status": c["status"],
            "tier": c["tier"],
            "caveat_kind": c.get("caveat_kind"),
        }
    return out


def _aggregate(table: dict[str, dict], *, max_ledgered: int, data_blocked: bool) -> str:
    """Reproduce determine()'s aggregation (v3.5 semantics) over a criterion table.

    Mirrors scripts/calibration_verdict.py lines ~2869-2973: governance gate,
    FAILs, caveat budgets (protective then ledgered), then the v3.3 branch in
    which only protective/band caveats, skips and data-blocked years downgrade.
    """
    gov = table.get("governance", {}).get("status")
    if gov != cv.PASS:
        return cv.NOT_YET
    fails = [c for c, r in table.items() if r["status"] == cv.FAIL]
    if fails:
        return cv.NOT_YET
    protective = [
        r
        for c, r in table.items()
        if r["tier"] == cv.TIER_PROTECT and c != "governance" and r["status"] == cv.CAVEAT
    ]
    ledgered = [
        r
        for r in table.values()
        if r["tier"] != cv.TIER_PROTECT
        and r["status"] == cv.CAVEAT
        and r["caveat_kind"] == "ledgered"
    ]
    band = [
        r
        for r in table.values()
        if r["tier"] != cv.TIER_PROTECT
        and r["status"] == cv.CAVEAT
        and r["caveat_kind"] == "commercial-band"
    ]
    skipped = [
        c for c, r in table.items() if c != "governance" and r["status"] == cv.SKIPPED
    ]
    if len(protective) > cv.MAX_PROTECTIVE_CAVEATS or len(ledgered) > max_ledgered:
        return cv.NOT_YET
    if len(protective) + len(band) == 0 and not skipped and not data_blocked:
        return cv.CALIBRATED
    return cv.CALIBRATED_CAVEATS


def _apply_disposition(table: dict[str, dict], *, lone_only: bool) -> dict[str, dict]:
    """Return the table with the hypothetical C3a ledger disposition applied.

    ``lone_only=False`` is variant E (explicit entry: any price_mean FAIL
    reclassifies); ``True`` is variant S (the standing-rule transposition:
    only a LONE price_mean FAIL reclassifies). Governance must PASS for
    either (guard (b)). Afterwards the EXISTING C3c standing rule is
    re-evaluated on the modified table (explicit ledger runs before the
    standing rule in determine(), so a reclassified C3a exposes a lone C3c).
    """
    t = {c: dict(r) for c, r in table.items()}
    gov_pass = t.get("governance", {}).get("status") == cv.PASS
    fails = [c for c, r in t.items() if r["status"] == cv.FAIL]
    if "price_mean" in fails and gov_pass:
        if not lone_only or fails == ["price_mean"]:
            t["price_mean"] = {
                "status": cv.CAVEAT,
                "tier": t["price_mean"]["tier"],
                "caveat_kind": "ledgered",
            }
    # The existing C3c standing rule, as _apply_c3c_standing_rule would now
    # see the table: lone remaining price_tail FAIL + governance PASS.
    fails2 = [c for c, r in t.items() if r["status"] == cv.FAIL]
    if fails2 == ["price_tail"] and gov_pass:
        t["price_tail"] = {
            "status": cv.CAVEAT,
            "tier": t["price_tail"]["tier"],
            "caveat_kind": "ledgered",
        }
    return t


def main() -> None:
    """Score the designated configs and write the disposition record."""
    record: dict = {
        "rubric_version": cv.RUBRIC_VERSION,
        "constants": {
            "LEDGERABLE_CRITERIA": sorted(cv.LEDGERABLE_CRITERIA),
            "MAX_LEDGERED_CAVEATS": cv.MAX_LEDGERED_CAVEATS,
            "MAX_PROTECTIVE_CAVEATS": cv.MAX_PROTECTIVE_CAVEATS,
            "price_mean_tier": cv.CRITERIA["price_mean"][1],
            "price_tail_tier": cv.CRITERIA["price_tail"][1],
        },
        "configs": {},
    }
    for iso, run_id, years in CONFIGS:
        verdict = cv.determine(run_id, years=years)
        key = run_id + (f"@{'-'.join(map(str, years))}" if years else "")
        table = _crit_table(verdict)
        c3a = [
            {"year": r["year"], "status": r["status"], "magnitude": r["magnitude"]}
            for r in verdict["criteria"]["price_mean"]["records"]
            if r["status"] != cv.SKIPPED  # drop the DA diagnostic companions
        ]
        entry = {
            "iso": iso,
            "span_restricted": bool(years),
            "determination": verdict["determination"],
            "reasons": verdict["reasons"],
            "grade_summary": verdict["grade_summary"],
            "data_blocked_years": verdict["data_blocked_years"],
            "c3a_records": c3a,
            "fails": sorted(
                c for c, r in table.items() if r["status"] == cv.FAIL
            ),
            "criterion_table": table,
        }
        blocked = bool(verdict["data_blocked_years"])
        variants: dict[str, str] = {}
        for name, lone in (("E", False), ("S", True)):
            vt = _apply_disposition(table, lone_only=lone)
            for budget in (1, 2):
                variants[f"{name}_budget{budget}"] = _aggregate(
                    vt, max_ledgered=budget, data_blocked=blocked
                )
        entry["disposition_variants"] = variants
        record["configs"][key] = entry
    OUT.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    for key, e in record["configs"].items():
        print(
            f"{e['iso']:6s} {key}: {e['determination']:24s} "
            f"E1={e['disposition_variants']['E_budget1']:24s} "
            f"E2={e['disposition_variants']['E_budget2']:24s} "
            f"S2={e['disposition_variants']['S_budget2']}"
        )


if __name__ == "__main__":
    main()
