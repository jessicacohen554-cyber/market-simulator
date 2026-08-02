"""xiso-3 — cross-ISO forced-share / D-4 window census on all six current keepers.

Rule 20 ``[R-FORCED-BUDGET]`` compliance census, all six ISOs. Mechanical,
**zero LP**: the C8 gate is scorer-only, so everything here is read from each
keeper bundle's COMMITTED ``legitimacy_diagnostics.json`` (plus the committed
run payload / bench parts the rubric's materiality lookup uses) through the
PRODUCTION scorer itself — ``scripts/calibration_verdict.py`` — never a
re-implementation.

THE QUESTION
------------
Per ISO, on the current keeper:

1. Which MATERIAL classes (annual energy >= 2 % of ISO load, max(model, actual)
   — ``calibration_verdict._class_load_share``) sit ABOVE their rule-20
   forced-energy budget (30 % merchant / 15 % CT_PEAKER)?
2. For each over-budget class, does EVERY binding non-exempt mechanism carry a
   declared D-4 window (a committed D-4 row — generated iff the mechanism has a
   cited ``D4_WINDOWS`` entry in ``scripts/legitimacy_diagnostics.py``) and
   clear D-4 off-window binding (<= 5 % of floored MWh outside the window)?
3. Does the class's D-1 hour-of-day profile clear the artifact's own gates
   (``profile_r`` >= 0.8, ``cv_ratio`` >= 0.5)?

Rule 20's conditional-pass path makes an over-budget class NOT an automatic
fail: (2) + (3) both clear -> CLEAN PASS classified GROUNDED-ABOVE-BUDGET
(a report note, never a caveat); either misses -> FAIL (forcing
shape/provenance mismatch). The census verdict per class IS the production
``score_forced_share`` record — this probe adds the underlying D-2/D-4/D-1
detail rows, the HEAD ``D4_WINDOWS`` registry cross-check, and a latent
coverage sweep the gate does not reach (below-budget classes, informational).

ADMISSIBILITY (stated up front, per the arm's method note)
-----------------------------------------------------------
This is an AUDIT, not a mechanism. It solves nothing, arms nothing, changes no
ScenarioConfig field, and registers nothing (rule 15's zero-LP disposition —
the neiso-71/73/74 + xiso-1 + xiso-2 precedent). Every input is a committed
byte: the six keeper bundles' ``legitimacy_diagnostics.json``, their registry
sidecars / run payloads / bench parts, and the HEAD scorer sources. All scored
years are inside the 2023-2025 training window (the sidecar year spans are
asserted below); no holdout year is read, so the active holdout spend freeze
is untouched. Verdicts are strictly per ISO (rule 25) — a grounded pass in one
ISO transfers nothing to another.

Reporting against interest is the point: finding every keeper compliant is a
full deliverable, and a latent gap in a class the gate never reaches is
reported as prominently as a live one.

WHAT IT DOES
------------
For each ISO's keeper (read live from ``frontend/data/backcast/keepers/<ISO>``
``.json`` so re-runs track keeper swaps):

* run the PRODUCTION verdict (``determine_from_artifacts``) and extract the C8
  criterion status + any grounded-above-budget notes + the determination;
* re-run ``score_forced_share`` per year (pre-ledger) and diff against the
  verdict's post-ledger records — a status flip means an attestation
  exceptions-ledger entry touched C8 and is surfaced;
* census table per year x class: forced share vs cap, rubric materiality
  (max(model, actual) / load), the artifact's own baked ``load_share`` /
  ``immaterial`` / ``lower_bound`` flags, and the production status;
* for every over-budget MATERIAL class: the binding merchant mechanism set
  (``_binding_merchant_mechs``), each mechanism's committed D-4 row(s) +
  off-window share, whether the mechanism holds a ``D4_WINDOWS`` entry at HEAD
  (committed-row-missing vs HEAD-entry-missing are different defects: the
  first needs a bundle regen, the second a registry citation), and the D-1
  profile_r / cv_ratio detail;
* LATENT sweep (informational, never gated): the same D-4 coverage check for
  every material class BELOW its cap — a mechanism that would have no declared
  window if its class ever escalated;
* WINDOW-DRIFT check: every committed D-4 row's baked window vs the HEAD
  ``D4_WINDOWS`` registry — a drift means the artifact predates a registry
  change and the bundle needs re-generation before its D-4 evidence is quoted
  (rule 20's "that bundle re-generated so the D-4 row exists" clause).

Run::

    python scripts/probes/_xiso3_forced_share_d4_census.py \
        | tee results/calibration/PROBE-xiso3-forced-share-d4-census-2026-08-02.txt
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.calibration_verdict import (  # noqa: E402
    FAIL,
    FORCED_EXEMPT_MECH_NAMES,
    FORCED_SHARE_MERCHANT_MAX,
    FORCED_SHARE_PEAKER_CLASSES,
    FORCED_SHARE_PEAKER_MAX,
    GROUNDED_ABOVE_BUDGET,
    PROTECTIVE_MIN_LOAD_FRAC,
    SKIPPED,
    _binding_merchant_mechs,
    _class_load_share,
    _d1_shape,
    _d4_provenance,
    determine_from_artifacts,
    load_artifacts,
    score_forced_share,
)
from scripts.legitimacy_diagnostics import (  # noqa: E402
    D4_MAX_OFFWINDOW_SHARE,
    D4_WINDOWS,
)
from market_sim.data.floor_mechanisms import MECH_NAMES  # noqa: E402

ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")
KEEPER_DIR = REPO / "frontend" / "data" / "backcast" / "keepers"
TRAINING_YEARS = {2023, 2024, 2025}

# name -> mechanism id, for the HEAD D4_WINDOWS registry cross-check.
MECH_IDS = {name: mid for mid, name in MECH_NAMES.items()}


def head_window(mech_name: str, klass: str) -> str:
    """Describe the HEAD D4_WINDOWS entry applying to (mechanism, class).

    Returns ``"h<start>-<end-1>"`` for the most specific registry key —
    ``(id, class)`` beats ``(id, None)`` — or ``"NONE"`` when the mechanism has
    no entry at HEAD (a rule-17 missing declaration if the class escalates), or
    ``"UNMAPPED"`` when the committed name is not in ``MECH_NAMES`` at all.
    """
    mid = MECH_IDS.get(mech_name)
    if mid is None:
        return "UNMAPPED"
    for key in ((mid, klass), (mid, None)):
        if key in D4_WINDOWS:
            start, end = D4_WINDOWS[key]
            return f"h{start}-{end - 1}"
    return "NONE"


def window_drift(legit: dict) -> list[str]:
    """Committed D-4 rows whose baked window differs from the HEAD registry.

    The committed ``floor`` label is ``"<mech>"`` (class filter None) or
    ``"<mech> × <class>"``; the committed ``window`` string (``"h<a>-<b>"``)
    is compared against the HEAD ``D4_WINDOWS`` entry for the same key. A
    mismatch — including a row whose mechanism/class no longer holds any HEAD
    entry — means the artifact predates a registry change.
    """
    out = []
    for r in legit.get("diagnostics", {}).get("D4", {}).get("rows", []):
        label = str(r.get("floor", ""))
        mech, _, klass = (p.strip() for p in label.partition(" × "))
        mid = MECH_IDS.get(mech)
        if mid is None:
            out.append(f"{r.get('year')} {label}: mechanism not in MECH_NAMES at HEAD")
            continue
        key = (mid, klass) if klass and (mid, klass) in D4_WINDOWS else (mid, None)
        if key not in D4_WINDOWS:
            out.append(
                f"{r.get('year')} {label}: no HEAD D4_WINDOWS entry (row is orphaned)"
            )
            continue
        start, end = D4_WINDOWS[key]
        head = f"h{start}-{end - 1}"
        if str(r.get("window")) != head:
            out.append(
                f"{r.get('year')} {label}: committed window {r.get('window')} "
                f"!= HEAD {head} — bundle predates the registry change"
            )
    return out


def committed_d4_rows(legit: dict, year: int, klass: str, mech: str) -> list[dict]:
    """The committed D-4 rows applicable to (year, class, mechanism).

    Same match rule as ``calibration_verdict._d4_provenance``: the ``floor``
    label is the mechanism name alone or ``"<mech> × <class>"``.
    """
    return [
        r
        for r in legit.get("diagnostics", {}).get("D4", {}).get("rows", [])
        if int(r.get("year", -1)) == int(year)
        and str(r.get("floor", "")) in (mech, f"{mech} × {klass}")
    ]


def census_iso(iso: str) -> dict:
    """Run the census for one ISO's keeper; return the summary row."""
    keeper = json.loads((KEEPER_DIR / f"{iso}.json").read_text())["keeper"]
    art = load_artifacts(keeper)
    legit = art["legitimacy"]
    sidecar, payload, bench = art["sidecar"], art["payload"], art["bench"]
    bundle = sidecar.get("bundle", "?")
    print(f"\n{'=' * 78}\n{iso} — keeper {keeper}\n  bundle {bundle}")

    years = sorted(int(y) for y in (payload or {}).get("years", {}))
    assert set(years) <= TRAINING_YEARS, (
        f"{iso}: payload years {years} outside the 2023-2025 training window"
    )
    if legit is None:
        print("  !! NO legitimacy_diagnostics.json in bundle — C8 SKIPPED")
        return {"iso": iso, "keeper": keeper, "verdict": "NO-ARTIFACT"}

    # Production verdict (post-ledger) for the headline + notes.
    v = determine_from_artifacts(keeper, art)
    c8 = v["criteria"]["forced_share"]
    grounded_notes = [n for n in v.get("notes", []) if n.startswith("C8")]
    print(
        f"  determination {v['determination']} (rubric v{v['rubric_version']}) · "
        f"C8 criterion: {c8['status']}"
    )
    post = {(r["year"], r.get("key")): r for r in c8["records"]}

    over_rows: list[str] = []
    latent_rows: list[str] = []
    ledger_flips: list[str] = []
    immaterial: list[str] = []
    statuses: list[str] = []
    print(
        f"  C8 census (caps {FORCED_SHARE_MERCHANT_MAX:.0%} merchant / "
        f"{FORCED_SHARE_PEAKER_MAX:.0%} {'/'.join(FORCED_SHARE_PEAKER_CLASSES)}; "
        f"materiality >= {PROTECTIVE_MIN_LOAD_FRAC:.0%} of load, max(model, actual)):"
    )
    print(
        f"    {'year':<5} {'class':<14} {'forced%':>8} {'cap%':>5} {'load%':>6} "
        f"{'baked':>6} {'lb':>3}  status"
    )
    for year in years:
        ypay = payload["years"][str(year)]
        ybench = bench.get(year, {})
        raw = {
            (r["year"], r.get("key")): r
            for r in score_forced_share(year, legit, ypay, ybench)
        }
        d2 = [
            r
            for r in legit.get("diagnostics", {}).get("D2", {}).get("summary", [])
            if int(r.get("year", -1)) == int(year)
        ]
        for r in sorted(d2, key=lambda x: -float(x.get("forced_share", 0) or 0)):
            klass = str(r.get("class"))
            fs = float(r.get("forced_share", 0) or 0.0)
            cap = (
                FORCED_SHARE_PEAKER_MAX
                if klass in FORCED_SHARE_PEAKER_CLASSES
                else FORCED_SHARE_MERCHANT_MAX
            )
            share = _class_load_share(klass, ypay, ybench)
            rec = raw.get((year, klass))
            prec = post.get((year, klass))
            status = rec["status"] if rec else "?"
            tag = status
            if rec and rec.get("classification") == GROUNDED_ABOVE_BUDGET:
                tag = "PASS (GROUNDED ABOVE BUDGET)"
            elif status == SKIPPED:
                tag = "SKIPPED-immaterial"
                immaterial.append(f"{year} {klass} ({fs:.1%} forced)")
            if rec and prec and prec["status"] != status:
                tag += f" -> {prec['status']} (LEDGERED)"
                ledger_flips.append(
                    f"{year} {klass}: {status} -> {prec['status']} via exceptions ledger"
                )
            baked = r.get("load_share")
            print(
                f"    {year:<5} {klass:<14} {fs * 100:>7.1f} {cap * 100:>5.0f} "
                f"{'n/a' if share is None else f'{share * 100:.1f}':>6} "
                f"{'n/a' if baked is None else f'{baked * 100:.1f}':>6} "
                f"{'LB' if r.get('lower_bound') else '':>3}  {tag}"
            )
            statuses.append(status)

            material = share is not None and share >= PROTECTIVE_MIN_LOAD_FRAC
            mechs = _binding_merchant_mechs(legit, year, klass)
            if material and fs > cap:
                # The escalation detail behind the production record.
                prov_ok, prov_detail = _d4_provenance(legit, year, klass, mechs)
                shape_ok, shape_detail = _d1_shape(legit, year, klass)
                over_rows.append(
                    f"{year} {klass} {fs:.1%} > {cap:.0%} -> "
                    f"D-4 {'CLEAR' if prov_ok else 'MISS'} ({prov_detail}); "
                    f"D-1 {'CLEAR' if shape_ok else 'MISS'} ({shape_detail})"
                )
                for mech in mechs:
                    rows = committed_d4_rows(legit, year, klass, mech)
                    hw = head_window(mech, klass)
                    if not rows:
                        over_rows.append(
                            f"      {mech}: NO committed D-4 row · HEAD registry {hw}"
                        )
                    for row in rows:
                        over_rows.append(
                            f"      {mech}: window {row.get('window')} · "
                            f"floored {row.get('floored_twh')} TWh · off-window "
                            f"{float(row.get('offwindow_share', 0)):.1%} "
                            f"(<= {D4_MAX_OFFWINDOW_SHARE:.0%}) {row.get('verdict')} · "
                            f"HEAD registry {hw}"
                        )
            elif material and mechs:
                # Latent: below budget today, so the gate never reads these —
                # reported so a future escalation has no surprise missing window.
                for mech in mechs:
                    rows = committed_d4_rows(legit, year, klass, mech)
                    hw = head_window(mech, klass)
                    if not rows or hw == "NONE":
                        latent_rows.append(
                            f"{year} {klass} ({fs:.1%} <= {cap:.0%}) {mech}: "
                            f"{'no committed D-4 row' if not rows else 'committed row present'}"
                            f" · HEAD registry {hw}"
                        )

    if over_rows:
        print("  over-budget material classes (rule-20 escalation detail):")
        for line in over_rows:
            print(f"    {line}")
    else:
        print(
            "  over-budget material classes: NONE — every material class within its cap"
        )
    if grounded_notes:
        print("  grounded-above-budget notes (production verdict):")
        for n in grounded_notes:
            print(f"    {n}")
    if ledger_flips:
        print("  C8 exceptions-ledger flips (post-ledger differs from raw):")
        for line in ledger_flips:
            print(f"    {line}")
    if immaterial:
        print(f"  immaterial (reported, never gated): {', '.join(immaterial)}")
    if latent_rows:
        print(
            "  LATENT D-4 coverage gaps (below-budget classes — informational, not gated):"
        )
        for line in latent_rows:
            print(f"    {line}")
    else:
        print(
            "  latent D-4 coverage gaps: none — every binding mechanism on a material class is windowed"
        )
    drift = window_drift(legit)
    if drift:
        print(
            "  D-4 WINDOW DRIFT vs HEAD registry (bundle predates a registry change):"
        )
        for line in drift:
            print(f"    {line}")
    else:
        print(
            "  D-4 window drift vs HEAD registry: none — every committed row matches HEAD"
        )

    n_fail = sum(1 for s in statuses if s == FAIL)
    n_grounded = len(grounded_notes)
    verdict = "FAIL" if n_fail else ("GROUNDED-PASS" if n_grounded else "PASS")
    return {
        "iso": iso,
        "keeper": keeper,
        "c8_status": c8["status"],
        "n_fail": n_fail,
        "n_grounded": n_grounded,
        "n_ledgered": len(ledger_flips),
        "n_latent": len(latent_rows),
        "n_drift": len(drift),
        "verdict": verdict,
    }


def main(argv: list[str] | None = None) -> int:
    """Run the six-ISO census and print the cross-ISO summary table."""
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    print("xiso-3 forced-share / D-4 window census — six current keepers, zero LP")
    print(
        f"exempt mechanism names (never count toward the budget): "
        f"{', '.join(sorted(FORCED_EXEMPT_MECH_NAMES))}"
    )
    rows = [census_iso(iso) for iso in ISOS]
    print(f"\n{'=' * 78}\nCROSS-ISO SUMMARY")
    print(
        f"  {'ISO':<7} {'C8':<8} {'fails':>5} {'grounded':>8} {'ledgered':>8} "
        f"{'latent':>6} {'drift':>5}  verdict"
    )
    for r in rows:
        print(
            f"  {r['iso']:<7} {r.get('c8_status', '?'):<8} {r.get('n_fail', '?'):>5} "
            f"{r.get('n_grounded', '?'):>8} {r.get('n_ledgered', '?'):>8} "
            f"{r.get('n_latent', '?'):>6} {r.get('n_drift', '?'):>5}  {r['verdict']}"
        )
    print(
        "\nCensus is report-only (rule-20 authority stays with "
        "calibration_verdict); exit 0 regardless of verdicts."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
