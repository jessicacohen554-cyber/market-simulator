"""Zero-LP probe: rule-22 lone-C3c test ordered after the R-6/R-8/R-40 routes.

PRECOMMIT evidence for the rule-37 amendment proposed in
``docs/records/governance/closeout-2026-10/PRECOMMIT-rubric-c3c-order-2026-10-03.md``
(owner ruling R-57, 2026-10-03: "Open the amendment lane").

``determine_from_artifacts`` applies ``_apply_c3c_standing_rule`` BEFORE
``_apply_scoped_ledger`` / ``_apply_config_exceptions`` /
``_apply_reference_coverage``, so a FAIL those routes later excuse still makes a
C3c miss "not lone". The AFTER state (``--after``) runs the standing rule
LAST, by patching the module in memory only: the standing rule is no-op'd at
its current call site and re-invoked, unchanged, right after the
reference-coverage route. Every guard of the rule is its own code, untouched.
``scripts/calibration_verdict.py`` is never modified.

Scores every ISO's keeper through ``iso_determination`` (partition scopes plus
every folded run), BEFORE and AFTER, over the committed bundles; never runs an
LP. Usage::

    uv run python scripts/probes/rubric_c3c_order_probe.py [--json OUT]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import calibration_verdict as cv  # noqa: E402

ISOS = ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "NWPP", "SOCO"]
KEEPERS = REPO / "frontend" / "data" / "backcast" / "keepers"

_ORIG_C3C = cv._apply_c3c_standing_rule
_ORIG_REFCOV = cv._apply_reference_coverage
_ORIG_DETERMINE = cv.determine


def _set_order(after: bool) -> None:
    """Install the BEFORE (as committed) or AFTER (standing rule last) order."""
    if not after:
        cv._apply_c3c_standing_rule = _ORIG_C3C
        cv._apply_reference_coverage = _ORIG_REFCOV
        return

    def _refcov_then_c3c(records, iso, gov, bench, exceptions):
        _ORIG_REFCOV(records, iso, gov, bench, exceptions)
        _ORIG_C3C(records, gov)

    cv._apply_c3c_standing_rule = lambda records, gov: None
    cv._apply_reference_coverage = _refcov_then_c3c


def _capture() -> tuple[dict, callable]:
    """Wrap ``cv.determine`` to keep each scope's full verdict."""
    seen: dict = {}

    def _det(run_id, years=None):
        v = _ORIG_DETERMINE(run_id, years=years)
        seen[(run_id, tuple(years) if years else None)] = v
        return v

    return seen, _det


def _records(v: dict) -> dict:
    """``{(criterion, year, key, n): (status, classification, standing_rule)}``.

    ``n`` numbers a criterion-year's records in scoring order (C3c carries the
    gated RT row beside its report-only DA diagnostic row).
    """
    out = {}
    for cid, crit in (v.get("criteria") or {}).items():
        for r in crit.get("records") or []:
            n = sum(1 for k in out if k[:3] == (cid, r.get("year"), r.get("key")))
            out[(cid, r.get("year"), r.get("key"), n)] = (
                r.get("status"),
                r.get("classification"),
                r.get("standing_rule"),
            )
    return out


def _budget(v: dict) -> dict:
    """Caveat-budget use of one scope verdict, per criterion caveat kind."""
    kinds: dict = {}
    for cid, crit in (v.get("criteria") or {}).items():
        if crit.get("status") == cv.CAVEAT:
            kinds[cid] = crit.get("caveat_kind")
    gs = v.get("grade_summary") or {}
    return {
        "caveat_kinds": kinds,
        "grade_summary": {k: gs.get(k) for k in
                          ("scored", "target_grade", "commercial_grade",
                           "ledgered", "fails")},
    }


def score(after: bool) -> dict:
    """Score all nine keepers' ISO determinations under one ordering."""
    _set_order(after)
    out = {}
    for iso in ISOS:
        shard = json.loads((KEEPERS / f"{iso}.json").read_text())
        seen, det = _capture()
        cv.determine = det
        try:
            iso_v = cv.iso_determination(iso, shard["keeper"],
                                         shard.get("config_partition"))
        finally:
            cv.determine = _ORIG_DETERMINE
        scopes = []
        for s in iso_v["scopes"]:
            key = next(k for k in seen if k[0] == s["run_id"]
                       and (k[1] is None or sorted(k[1]) == s["years"]
                            or set(s["years"]) <= set(k[1])))
            v = seen[key]
            scopes.append({
                "kind": s["kind"], "role": s["role"], "run_id": s["run_id"],
                "years": s["years"], "determination": s["determination"],
                "failing": s["failing"], "records": _records(v),
                "budget": _budget(v), "reasons": s["reasons"],
            })
        out[iso] = {"keeper": shard["keeper"],
                    "determination": iso_v["determination"], "scopes": scopes}
    _set_order(False)
    return out


# The R-51 case that surfaced the defect: the ERCOT x33-strip probe's 2023 leg
# read C3c 44 h vs 181 h actual (FAIL) beside R-6-excused C3a/C3b
# (docs/records/ercot/closeout/RESULT-closeout-ercot-ecrs-x33-strip-2026-10-03.md
# §3). That composite is kept off main, so the sensitivity case is the ERCOT
# keeper's carve-out 2023 scope with ONLY the 2023 scored tail count replaced by
# the strip's measured 44 h; every other 2023 input is the keeper's.
STRIP_2023_TAIL_H = 44.0


def sensitivity() -> dict:
    """Score the ERCOT carve-out 2023 scope with the R-51 strip tail count."""
    import copy

    shard = json.loads((KEEPERS / "ERCOT.json").read_text())
    cfg = next(c for c in shard["config_partition"]["configs"]
               if [int(y) for y in c["years"]] == [2023])
    art = copy.deepcopy(cv.load_artifacts(cfg["run_id"]))
    h = art["payload"]["years"]["2023"]["ordc"]["hoursGt200"]
    field = "overlay" if h.get("overlay") is not None else "model"
    h[field] = STRIP_2023_TAIL_H
    out = {"run_id": cfg["run_id"], "field": field}
    for after in (False, True):
        _set_order(after)
        v = cv.determine_from_artifacts(cfg["run_id"], art, years=[2023])
        out["after" if after else "before"] = {
            "determination": v["determination"],
            "records": {f"{k[0]} {k[1]} {k[2]} #{k[3]}": r for k, r in _records(v).items()
                        if k[0] in ("price_mean", "price_shape", "price_tail")},
            "budget": _budget(v),
        }
    _set_order(False)
    return out


def per_year_ladder() -> list:
    """Every scope re-scored one year at a time (the rule-30 per-year ladder).

    ``build_status`` scores each registered year alone for the Calibration
    Status ladder; there "lone" is measured inside that single year.
    Returns the (iso, run_id, year, before, after) rows that move.
    """
    moved, rows = [], 0
    for iso in ISOS:
        shard = json.loads((KEEPERS / f"{iso}.json").read_text())
        cfgs = (shard.get("config_partition") or {}).get("configs") or []
        runs = [(c["run_id"], [int(y) for y in c["years"]]) for c in cfgs] or [
            (shard["keeper"], None)]
        runs += [(r["id"], None) for r in cv.folded_touchpoints(iso, shard["keeper"])]
        for run_id, span in runs:
            art = cv.load_artifacts(run_id)
            years = span or [int(y) for y in art["sidecar"].get("years", [])]
            for y in years:
                got = []
                for after in (False, True):
                    _set_order(after)
                    v = cv.determine_from_artifacts(run_id, art, years=[y])
                    got.append((v["determination"], _records(v)))
                rows += 1
                if got[0] != got[1]:
                    moved.append((iso, run_id, y, got[0][0], got[1][0]))
    _set_order(False)
    print(f"\nper-year ladder: {rows} scope-years scored, {len(moved)} move")
    for m in moved:
        print("  ", m)
    return moved


def main() -> None:
    """Print the BEFORE/AFTER table and every criterion-year that moves."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", type=Path, help="write the full diff as JSON")
    a = ap.parse_args()
    before, after = score(False), score(True)
    print(f"rubric {cv.RUBRIC_VERSION} as committed vs AFTER (C3c standing rule last)\n")
    print(f"{'ISO':6} {'BEFORE':28} {'AFTER':28} keeper")
    moves = []
    for iso in ISOS:
        b, f = before[iso], after[iso]
        print(f"{iso:6} {b['determination']:28} {f['determination']:28} {b['keeper']}")
        for sb, sf in zip(b["scopes"], f["scopes"]):
            assert sb["run_id"] == sf["run_id"]
            for k in sorted(set(sb["records"]) | set(sf["records"]), key=str):
                rb, rf = sb["records"].get(k), sf["records"].get(k)
                if rb != rf:
                    moves.append((iso, sb["kind"], sb["role"], sb["run_id"],
                                  sb["years"], k, rb, rf))
            if sb["determination"] != sf["determination"] or sb["budget"] != sf["budget"]:
                moves.append((iso, sb["kind"], sb["role"], sb["run_id"], sb["years"],
                              ("SCOPE",), (sb["determination"], sb["budget"]),
                              (sf["determination"], sf["budget"])))
    print("\nscope rows (every scope, both orders):")
    for iso in ISOS:
        for sb, sf in zip(before[iso]["scopes"], after[iso]["scopes"]):
            print(f"  {iso:6} {sb['kind']:9} {str(sb['role'] or ''):10} "
                  f"{'/'.join(map(str, sb['years'])):30} {sb['determination']:26} -> "
                  f"{sf['determination']:26} fail-before={sb['failing']} "
                  f"fail-after={sf['failing']} kinds-after={sf['budget']['caveat_kinds']}")
    print(f"\n{len(moves)} moved rows:")
    for m in moves:
        print("  ", m)
    ladder = per_year_ladder()
    sens = sensitivity()
    print(f"\nsensitivity (R-51): ERCOT carve-out 2023, {sens['run_id']}, "
          f"hoursGt200.{sens['field']} := {STRIP_2023_TAIL_H:.0f}")
    for side in ("before", "after"):
        print(f"  {side.upper():6} {sens[side]['determination']}  "
              f"{sens[side]['records']}  {sens[side]['budget']}")
    if a.json:
        def _str_keys(o):
            if isinstance(o, dict):
                return {str(k): _str_keys(v) for k, v in o.items()}
            if isinstance(o, (list, tuple)):
                return [_str_keys(v) for v in o]
            return o
        a.json.write_text(json.dumps(_str_keys({"before": before, "after": after,
                                                "moves": moves,
                                                "per_year_ladder": ladder,
                                                "sensitivity": sens}),
                                     default=str, indent=1))


if __name__ == "__main__":
    main()
