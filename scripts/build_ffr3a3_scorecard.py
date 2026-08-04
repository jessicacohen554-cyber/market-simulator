#!/usr/bin/env python
"""Assemble the §2.1b gate scorecard for a PARTIAL re-measurement (FFR-3A-3).

FFR-3A-2 measured all 14 legs and built the scorecard with
:mod:`scripts.build_ffr3a2_scorecard`. Its own provenance banner then recorded
that the battery had measured a **superseded configuration**: the rebase
brought in FFR-3F's G3 cap-grain fix (``2adfb49``), which is UNCONDITIONAL and
changes the admitted exit set — the same economic-retirement screen every T1-H
finding rests on.

FFR-3A-3 re-measures the exposed halves (**T1-H** ×4 and **T1-X** ×3) at the
post-FFR-3F HEAD and deliberately does NOT re-run T1-F, which does not turn on
the exit screen's grain. That leaves the scorecard with **mixed provenance**,
and the only dishonest way to present it would be to let a carried-forward
column read as freshly measured.

So this successor adds exactly two carry-forward channels to the predecessor's
instrument — and **nothing else**. It re-uses the predecessor's criterion
functions verbatim by import; it does not fork, re-implement or re-grade them:

* ``--t1f-from-snapshot`` — carry the T1-F determinations from the committed
  ``ff-verdicts.json`` snapshot, each tagged ``provenance="carried-forward"``
  with the ``scored_at_sha`` the snapshot itself recorded.
* ``--ff3e-from-scorecard`` — carry criterion (c)'s projected wall/RSS from a
  prior committed ``scorecard.json`` when this session did not re-run the
  FF-3E battery (its bundle is gitignored and dies with the container).

Every carried value is marked in both the JSON and the printed table (a ``^``
suffix), so a reader can never mistake a prior-sha number for a fresh one.

Rule 1 / rule 14: nothing here widens a band, re-grades a miss, or chooses a
value to clear one. Rubric §4: this script was authored **before** any
FFR-3A-3 leg finished solving, precisely so it cannot be shaped by its own
results.

Usage::

    python scripts/build_ffr3a3_scorecard.py \\
        --t1h-dir results/ffr3a3/t1h --t1x-dir results/ffr3a3/t1x \\
        --t1f-from-snapshot \\
        --ff3e-from-scorecard results/ffr3a2/scorecard/scorecard.json \\
        --out results/ffr3a3/scorecard
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_ffr3a2_scorecard import (
    FF_VERDICTS,
    FREEZE,
    ISOS,
    REPO,
    _load,
    cache_epoch,
    criterion_a,
    criterion_b,
    criterion_c,
    regression_vs_ff2d,
    scored_at_sha,
)

# The tiers this session actually re-solved. Anything outside it is carried
# forward and labelled, never silently presented as measured.
REMEASURED_TIERS = ("t1h", "t1x")


def t1f_from_snapshot() -> dict:
    """Per-ISO T1-F determinations carried from the committed FF verdicts.

    Returns a mapping ``{ISO: row-or-None}`` shaped like
    :func:`build_ffr3a2_scorecard.criterion_b`'s per-tier rows, with each row
    tagged by the sha the snapshot recorded so the carry-forward is legible.
    Entries whose id ends ``-ff2d`` are the FF-2D baselines rather than the
    most recent measurement; the newest non-baseline entry per ISO wins.
    """
    snap = _load(FF_VERDICTS) or {}
    best: dict[str, tuple[str, dict]] = {}
    for run_id, v in snap.items():
        if (v.get("tier") or "").lower() != "t1f":
            continue
        iso = (v.get("iso") or "").upper()
        if not iso:
            continue
        # Prefer a non-baseline entry; among those prefer the shortest id,
        # which is the session's own leg (`ercot-t1f`) over its control arms.
        is_baseline = run_id.endswith("-ff2d")
        rank = (is_baseline, len(run_id))
        if iso not in best or rank < best[iso][0]:  # type: ignore[operator]
            best[iso] = (rank, {"id": run_id, **v})  # type: ignore[assignment]

    out: dict[str, dict | None] = {}
    for iso in ISOS:
        got = best.get(iso)
        if not got:
            out[iso] = None
            continue
        _, v = got
        prov = v.get("provenance") or {}
        out[iso] = {
            "determination": v.get("determination"),
            "categories": {
                c: d.get("status") for c, d in (v.get("categories") or {}).items()
            },
            "reasons": v.get("reasons"),
            "provenance": "carried-forward",
            "carried_from_id": v.get("id"),
            "carried_from_sha": prov.get("scored_at_sha"),
            "carried_from_session": prov.get("session"),
        }
    return out


def ff3e_from_scorecard(path: Path) -> dict:
    """Carry criterion (c)'s wall/RSS projection from a prior scorecard.json."""
    prior = _load(path) or {}
    src = prior.get("criterion_c_worth_the_compute") or {}
    out = {}
    for iso in ISOS:
        row = dict(src.get(iso) or {})
        row.pop("crossover_score", None)  # this session measures its own
        if row:
            row["provenance"] = "carried-forward"
            row["carried_from_sha"] = prior.get("scored_at_sha")
            row["carried_from"] = str(path)
        out[iso] = row
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--t1f-dir", type=Path, default=REPO / "results/ffr3a3/t1f")
    ap.add_argument("--t1h-dir", type=Path, default=REPO / "results/ffr3a3/t1h")
    ap.add_argument("--t1x-dir", type=Path, default=REPO / "results/ffr3a3/t1x")
    ap.add_argument(
        "--t1f-from-snapshot",
        action="store_true",
        help="Carry T1-F determinations from the committed ff-verdicts.json "
        "snapshot (this session did not re-run T1-F). Each is tagged with the "
        "sha it was originally scored at.",
    )
    ap.add_argument(
        "--ff3e",
        type=Path,
        default=REPO / "results/ffr3a3/ff3e/ff3e_readiness_bundle.json",
    )
    ap.add_argument(
        "--ff3e-from-scorecard",
        type=Path,
        default=None,
        help="Carry criterion (c)'s projected wall/RSS from a prior committed "
        "scorecard.json when this session did not re-run FF-3E.",
    )
    ap.add_argument("--out", type=Path, default=REPO / "results/ffr3a3/scorecard")
    args = ap.parse_args(argv)

    a = criterion_a()
    b = criterion_b(args.t1f_dir, args.t1h_dir, args.t1x_dir)

    carried_tiers = []
    if args.t1f_from_snapshot:
        carried = t1f_from_snapshot()
        for iso in ISOS:
            # Never overwrite a leg this session actually solved.
            if not (b[iso].get("t1f")):
                b[iso]["t1f"] = carried[iso]
        carried_tiers.append("t1f")

    if args.ff3e_from_scorecard:
        c = ff3e_from_scorecard(args.ff3e_from_scorecard)
        # This session's own crossover scores still attach.
        fresh = criterion_c(args.ff3e, args.t1x_dir)
        for iso in ISOS:
            if fresh[iso].get("crossover_score"):
                c[iso]["crossover_score"] = fresh[iso]["crossover_score"]
        carried_tiers.append("ff3e/criterion-c")
    else:
        c = criterion_c(args.ff3e, args.t1x_dir)

    freeze = _load(FREEZE) or {}
    sha = scored_at_sha()

    payload = {
        "scored_at_sha": sha,
        "cache_epoch": cache_epoch(),
        "holdout_freeze_active": bool(freeze.get("active")),
        "session": "FFR-3A-3",
        "remeasured_tiers": list(REMEASURED_TIERS),
        "carried_forward": carried_tiers,
        "provenance_note": (
            "MIXED PROVENANCE. Tiers "
            f"{', '.join(REMEASURED_TIERS)} were re-solved at {sha} (post-FFR-3F, "
            "so the G3 cap-grain fix 2adfb49 is in force). Anything listed in "
            "`carried_forward` retains the sha recorded on its own artifact and "
            "was NOT re-measured here — see each row's `carried_from_sha`."
        ),
        "criterion_a_backcast_calibration": a,
        "criterion_b_t1_gates": b,
        "criterion_c_worth_the_compute": c,
        "criterion_d_owner_authorization": (
            "NOT MEASURED HERE — an explicit, per-campaign owner decision. "
            "No ISO carries one; `final` is empty by design."
        ),
        "regression_vs_ff2d": regression_vs_ff2d(b),
    }

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "scorecard.json").write_text(json.dumps(payload, indent=1))

    def _mark(row: dict | None) -> str:
        """Render a determination, suffixing ``^`` when it was carried forward."""
        if not row:
            return "—"
        det = row.get("determination") or "—"
        return det + ("^" if row.get("provenance") == "carried-forward" else "")

    lines = [
        f"§2.1b GATE SCORECARD (FFR-3A-3) — scored_at_sha={sha} "
        f"cache_epoch={payload['cache_epoch']} "
        f"holdout_freeze_active={payload['holdout_freeze_active']}",
        "re-measured at this sha: "
        + ", ".join(REMEASURED_TIERS)
        + ("   ^ = carried forward, see carried_from_sha" if carried_tiers else ""),
        "",
        f"{'ISO':6s} {'(a) backcast':34s} {'mk':4s} {'(b) t1f':9s} {'t1h':9s} "
        f"{'t1x':9s} {'(c) proj h':10s} solo",
    ]
    for iso in ISOS:
        ra, rb, rc = a[iso], b[iso], c[iso]
        det = (ra["determination"] or "—")[:33]
        mk = ("C" if ra["marker_complete"] else "-") + (
            "F" if ra["marker_final"] else "-"
        )
        ph = rc.get("projected_hours")
        ph_s = (str(ph) if ph is not None else "—") + (
            "^" if rc.get("provenance") == "carried-forward" else ""
        )
        lines.append(
            f"{iso:6s} {det:34s} {mk:4s} {_mark(rb['t1f']):9s} "
            f"{_mark(rb['t1h']):9s} {_mark(rb['t1x']):9s} {ph_s:10s} "
            f"{rc.get('must_run_solo')}"
        )
    txt = "\n".join(lines)
    (args.out / "scorecard.txt").write_text(txt + "\n")
    print(txt)
    print(f"\nwrote {args.out}/scorecard.json + scorecard.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
