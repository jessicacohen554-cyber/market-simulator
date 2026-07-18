"""ercot56 registration helpers for the one-shot CI workflow (relay fallback).

Three idempotent modes, mirroring ``_ercot55_ci_patch.py`` (the authoring
session's environment cannot push the ~600 KB calibration log or delete
registry files through the MCP relay, so these run on the CI runner):

* ``--write-attestations`` — derive the ercot56_nucwin main arm's
  ``calibration_attestation.json`` from the promoted ercot55-surface-ab
  keeper's (inherited DOF ledger, ZERO new tunables — the nuclear daily
  series is measured data, so per the ledger convention it extends the
  ``seeded`` note rather than adding an entry). The ablation twin carries no
  attestation (D-3 twins never do).
* ``--append-log`` — marker-guarded append of the ERCOT-56 session entry to
  ``docs/calibration-log.md``.
* ``--prune-registry --branch B`` — delete the 7 oldest / superseded ERCOT
  registrations' sidecar + runs files via the GitHub Data API (top-15
  retention, CLAUDE.md rule 15): the refuted temp-derate lineage
  (ercot48/49 pairs) and the superseded ercot46 clock trio. Bundle dirs under
  ``results/calibration/`` stay (archival record).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LOG = REPO / "docs" / "calibration-log.md"
KEEPER_ATT = (
    REPO / "results/calibration/ercot55_surface_ab/calibration_attestation.json"
)
MAIN_BUNDLE = REPO / "results/calibration/ercot56_nucwin"

OWNER = "jessicacohen554-cyber"
GH_REPO = "market-simulator"
API = "https://api.github.com"

PRUNE_IDS = (
    "2026-07-08-ercot46-clock-steamgas",
    "2026-07-08-ercot46-clock-steamgas-ablation",
    "2026-07-08-ercot46-statmode",
    "2026-07-08-ercot48-tempderate-full-probe",
    "2026-07-08-ercot48-tempderate-full-ablation",
    "2026-07-09-ercot49-offer-retune-tempderate",
    "2026-07-09-ercot49-retune-tempderate-ablation",
)

ENTRY_MARKER = "ERCOT-56: May-2024 outage-vs-heat collision forensics"

ENTRY = r"""
## 2026-07-10 — ERCOT-56: May-2024 outage-vs-heat collision forensics — outage-understatement hypothesis REFUTED at the event hours (thermal input faithful to ±0.3 GW on May 8); the ONE real defect found (nuclear refuel monthly smear) fixed as window-grain measured data; C3c-2024 stays the G-22 offer-formation residual (probe 27→27 h); ercot56 nucwin + twin registered, keeper stays ercot55-surface-ab

**Task (owner handoff).** Test the hypothesis that the May-2024 highs (May-8
deep event; recurring $200-1,500 DA evenings; May-27 Memorial-Day ~77 GW
record) were spring-maintenance outages colliding with unseasonable heat that
the model's outage inputs understate — leaving the model too much capacity to
form the observed depth/breadth (C3c-2024 27 h vs 68 DA, gate ≥34 h; May
monthly −34.7 % on the keeper).

**Forensics (diagnose-first; full detail in
docs/DIAGNOSIS-ercot-may2024-outage-forensics-2026-07.md).** (1) Actuals:
10 May event days; only May 8 is genuine reserve scarcity (PRC 4,778 MW,
RTORPA $179, λ $2,420). The seven DA-shoulder days (May 2/13/14/17/24/26/27,
16 of May's 22 DA>$200 h) cleared DA $266-1,518 while RT stayed ≤$180 and
measured RTORPA ≤$3 — offer/DA-expectation formation, not reserve physics.
May-27 peak 77.13 GW measured, model demand input 76.4 GW same day/hour;
2024 demand + HSL hygiene clean (no Dec-2025-style holes). (2) Outage
forensics — model derate vs 60-Day DAM Gen_Resource OUT (config-collapsed to
physical trains) and vs CEMS at the RT event hours: the measured overlay
tracks reality's return-from-maintenance ramp (≈23 GW out May 2 → ≈12 GW
May 27) within ±3.5 GW; at May-8 HE17-20 the model was NET −0.28 GW MORE
derated than CEMS reality (misses — the ST_GAS_PEAKER_PLANTS detector
exclusions [Stryker/Mountain Creek/Graham/Olinger], the CT-class exclusion,
Handley-5's one-day-late window — CANCEL against over-derates [Sam Seymour
back midday May 8, Tenaska Gateway, Sandy Creek, Wolf Hollow II one train]);
May 27 dead even (+0.1 GW). The hypothesis' load-bearing form is REFUTED —
the collision is IN the model at the right aggregate MW. (3) The one real
defect: NUCLEAR_MONTHLY_CF_BY_YEAR smears measured monthly energy uniformly
(May-2024 0.78 × all four reactors × all hours), but the disclosure shows
STP-2 OUT 2024-03-23→05-19 (spanning Apr-16, Apr-28, May-8) and CP-1 OUT
05-11→16, with ALL FOUR reactors back for May 20-31 (incl. the record
May-24..27 heat) — ±1.1-1.4 GW mis-timed within May; the fall refuels (STP-1
Oct 5–Nov 7, CP-2 Oct 21–Nov 17) smeared across Oct-Nov the same way.

**Rule-16 throwaway probe (2024-only, never registered): window-grain nuclear
moves the tail 27 → 27** — the C3c-2024 gate is availability-closed, exactly
as the RTORPA≈0 evidence predicted — while deepening May-8 HE18/19
$925/$1,405 → $1,371/$1,907 (measured λ $2,420/$2,368), fixing Nov
(−14.1 → −3.9 %), sign-flipping Jan (+4.9 → −5.1 %), and collapsing a
spurious May-26 $491 hour (model-tight on a day reality had all reactors
back — a smear artifact). C3c-2024 therefore STAYS LEDGERED as the filed
G-22 offer-formation residual (rules 1/13; no retune; ORDC frozen, rule 26).

**Fix landed as measured data (rules 14/15).**
`scripts/data/derive_ercot_nuclear_availability.py` →
`data/raw/ercot-nuclear-availability.csv`: per-reactor DAILY availability
from the 60-Day DAM disclosure NUC Resource Status (2023-2025 delivery
dates), monthly energy reconciled to the standing EIA-923 anchor — event
days (raw < 0.90: windows, trips, ramps, deep derates) kept exactly as
measured, the ≥0.90 pool scaled per month to the anchor (per-day cap 1.0;
pool scales 0.96-1.25, month energy on-anchor to <0.01 % everywhere except
the two winter months where the anchor's own 1.0-cap binds, ≤1.2 %). The
June-2023 heat-dome structure is cross-validated against the EIA-930 nuclear
hourly (CP-1 trip Jun 16-18 −1.23 GW, then a real ~0.73 CP-1 derate through
month-end); the Aug-2023 raw HSL low-read (~0.980 vs 930's 0.992) is
anchored out. Applied under new `ScenarioConfig.ercot_nuclear_unit_
availability` (default off; ERCOT backcast; both CLIs; meta/run_config
recorded; loader `outages.ercot_nuclear_unit_availability_series`; the
nuclear flat must-run floor tracks automatically; uncovered dates — the
Oct-2023 disclosure hole, Nov-Dec 2025 until the 2026 publications land —
keep the smear). Zero new tunables (DOF ledger seeded-note extension,
ercot53 precedent).

**Runs (full 2023-2025 + zero-forcing twin, solved and registered via the
`ercot56-solve-register` workflow).** Recipe = the PROMOTED keeper
(ercot55-surface-ab) reconstructed via `_ercot55_ab.py --surface` + the flag
(`--set ercot_nuclear_unit_availability=true`); local solves reproduced the
CI keeper byte-parity first (ercot54 precedent):

| run | C3a (23/24/25) | C3b | C3c h vs DA 311/68/23 | May-24 | caveats |
|---|---|---|---|---|---|
| ercot55 surface-ab (keeper) | +2.0/−4.7/−1.1 % | .106/.196/.094 | 166/27/24 | −34.7 % | 2 (C3c-2024, C5c) |
| ercot56 nucwin | +3.9/−4.5/−1.1 % | .133/.183/.094 | **171**/27/**25** | −33.2 % | (see run metrics) |

2024 improves across C3a/C3b/Nov/Jan/May-8-depth; 2025 ~unchanged (tail
25 vs 23 DA, 1.09×); C3c-2023 171 h ≥ the 162 h owner gate. **The honest
2023 movement (C3a +2.0→+3.9 %, C3b 0.106→0.133, both PASS) is the real
June/Sep heat-dome nuclear structure the smear was hiding: with CP-1's
measured trip + ~0.73 late-June derate in place of phantom flat nuclear,
June-2023 overshoots +22 % (was +7 %) — a DISCOVERED COMPENSATION (rule 15:
the accurate input stays; June scarcity formation was leaning on smeared
nuclear and is now an open root-cause lane), not a reason to revert.**
LOYO basis (rule 22): zero fitted parameters — the delta is measured window
data reconciled to the already-committed measured energy anchor (the
ercot53/ercot55 "zero-parameter clean basis"); 2023/2025 tail exposure
pre-checked (2023's DA tail is 93 % Jun-Sep; 2025's 24 h scattered). Keeper
promotion is the owner's call — keeper stays ercot55-surface-ab; the
recommendation (adopt: strictly better 2024, honest 2023 exposure, C3c-2025
still passing) is recorded on the run.

**Registry retention (rule 15).** ERCOT pruned 19 → 14 registrations: the
superseded ercot46 clock trio + the refuted temp-derate ercot48/49 pairs
dropped (sidecars + run payloads; bundle dirs kept as the archival record).

**Holdouts.** No solve, score, or intake outside 2023-2025 (rule 22); the
disclosure intake reads 2023-2025 delivery dates only; ORDC tariff
parameters untouched (rule 26); no offer-curve, sigmoid, floor, or
derive-script value changed (rules 13/21/23) — the new deriver is a new
measured input with a frozen formula (re-runs only on a disclosure-data
update), and the June-2023 overshoot is explicitly NOT retuned against.
"""


def write_attestations() -> None:
    """Write the ercot56_nucwin main-arm attestation (idempotent)."""
    src = json.loads(KEEPER_ATT.read_text())
    out = {
        "schema": src["schema"],
        "governance": dict(src["governance"]),
        "exceptions": [],
        "free_parameters": dict(src["free_parameters"]),
    }
    out["governance"]["attested_by"] = (
        "ercot56 nucwin keeper-track candidate gate, session 2026-07-10 "
        "(May-2024 outage-vs-heat collision forensics; full scored 2023-2025 "
        "bundle + zero-forcing ablation twin ercot56_nucwin_ablation; owner "
        "promotion PENDING — keeper stays ercot55-surface-ab)"
    )
    out["governance"]["note"] = (
        "Keeper-track arm on the PROMOTED ercot55-surface-ab recipe, ONE "
        "measured-input delta, ZERO new free parameters: "
        "ercot_nuclear_unit_availability=True — the four ERCOT reactors' "
        "availability moves from the NUCLEAR_MONTHLY_CF_BY_YEAR fleet-month "
        "smear (right monthly energy, refuel windows mis-timed within the "
        "month by up to ±1.4 GW) to the measured per-reactor DAILY series "
        "from the 60-Day DAM disclosure NUC Resource Status "
        "(data/raw/ercot-nuclear-availability.csv, "
        "scripts/data/derive_ercot_nuclear_availability.py), monthly energy "
        "reconciled to the SAME EIA-923 anchor (event days raw<0.90 kept as "
        "measured, cross-validated vs the EIA-930 nuclear hourly; the >=0.90 "
        "pool anchored per month, on-anchor to <0.01% except two winter "
        "months where the anchor's own 1.0-cap binds <=1.2%); uncovered "
        "dates (Oct-2023 hole, Nov-Dec 2025) keep "
        "the smear. A refuel window is a physical availability event — the "
        "nuclear analogue of the CAMPD fossil outage windows (rule 14); "
        "found and validated by the May-2024 outage-vs-heat collision "
        "forensics (docs/DIAGNOSIS-ercot-may2024-outage-forensics-2026-07.md: "
        "2024 type case STP-2 out 3/23-5/19 spanning the Apr-16/Apr-28/May-8 "
        "events and back for the May-24..27 record heat; CP-1 out 5/11-5/16). "
        "No offer curve, sigmoid, floor, or ORDC parameter touched."
    )
    fp = out["free_parameters"]
    fp["seeded"] = fp["seeded"] + (
        "; ercot56 delta appended 2026-07-10 (this round): "
        "ercot_nuclear_unit_availability window-grain measured nuclear refuel "
        "series (measured-input grain fix, no parameter) - no entry added "
        "because it introduces no tunable; no inherited scalar re-tuned"
    )
    for e in src["exceptions"]:
        e = dict(e)
        key = (e.get("criterion"), e.get("year"))
        if key == ("price_tail", 2024):
            e["magnitude"] = "27h vs DA actual 68h (0.40x, FAIL)"
            e["reason"] = (
                "Inherited by ercot56 and now FORENSICALLY ADJUDICATED as "
                "offer-formation, not availability: the May-2024 "
                "outage-vs-heat collision forensics (docs/DIAGNOSIS-ercot-"
                "may2024-outage-forensics-2026-07.md) shows the thermal "
                "outage input reproduces reality day-by-day (net -0.3 GW at "
                "the May-8 event hours, +0.1 GW on the May-27 record peak), "
                "demand/renewables inputs are clean, and measured RTORPA was "
                "<= $3 on every missed DA-shoulder day ($179 of the $2,420 "
                "lambda on May 8) — the missing 41 DA hours were formed by "
                "offers/DA expectations at reserve levels the ORDC (real and "
                "modeled) prices near zero. The window-grain nuclear fix "
                "moved the tail 27 -> 27 h (unchanged) while deepening "
                "May-8 HE18/19 $925/$1,405 -> $1,371/$1,907 (measured lambda $2,420/$2,368). "
            ) + e["reason"]
        elif key == ("storage_shape", 2024):
            e["reason"] = "Inherited unchanged by ercot56. " + e["reason"]
        else:
            e["reason"] = "Inherited by ercot56. " + e["reason"]
        out["exceptions"].append(e)
    dst = MAIN_BUNDLE / "calibration_attestation.json"
    dst.write_text(json.dumps(out, indent=1))
    print(f"wrote {dst}")


def append_log() -> None:
    """Append the ERCOT-56 calibration-log entry (marker-guarded)."""
    text = LOG.read_text()
    if ENTRY_MARKER in text:
        print("append-log: entry already present — no-op")
        return
    if not text.endswith("\n"):
        text += "\n"
    LOG.write_text(text + ENTRY.lstrip("\n"))
    print("append-log: appended")


def _req(method: str, path: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method)
    r.add_header("Authorization", "Bearer " + os.environ["GH_TOKEN"])
    r.add_header("Accept", "application/vnd.github+json")
    if data:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        sys.stderr.write(
            "%s %s -> %s: %s\n" % (method, path, e.code, e.read().decode())
        )
        raise


def prune_registry(branch: str) -> None:
    """Delete the pruned ids' sidecar + runs files via the Data API."""
    paths = []
    for rid in PRUNE_IDS:
        paths.append(f"frontend/data/backcast/registry/{rid}.json")
        paths.append(f"frontend/data/backcast/runs/{rid}.js")
    base = _req("GET", f"/repos/{OWNER}/{GH_REPO}/git/ref/heads/{branch}")["object"][
        "sha"
    ]
    base_commit = _req("GET", f"/repos/{OWNER}/{GH_REPO}/git/commits/{base}")
    # A tree entry with sha=None deletes the path. Only include paths that
    # exist at the tip (idempotent re-runs).
    tree = []
    for p in paths:
        try:
            _req(
                "GET",
                f"/repos/{OWNER}/{GH_REPO}/contents/{p}?ref={branch}",
            )
        except urllib.error.HTTPError:
            print(f"prune: {p} absent — skipped")
            continue
        tree.append({"path": p, "mode": "100644", "type": "blob", "sha": None})
    if not tree:
        print("prune: nothing to delete — no-op")
        return
    new_tree = _req(
        "POST",
        f"/repos/{OWNER}/{GH_REPO}/git/trees",
        {"base_tree": base_commit["tree"]["sha"], "tree": tree},
    )["sha"]
    commit = _req(
        "POST",
        f"/repos/{OWNER}/{GH_REPO}/git/commits",
        {
            "message": (
                "results: prune ERCOT registry to top-15 retention "
                "(ercot46 clock trio + refuted temp-derate ercot48/49 pairs; "
                "bundle dirs stay) [skip ci]"
            ),
            "tree": new_tree,
            "parents": [base],
        },
    )["sha"]
    _req(
        "PATCH",
        f"/repos/{OWNER}/{GH_REPO}/git/refs/heads/{branch}",
        {"sha": commit, "force": False},
    )
    print(f"prune: deleted {len(tree)} files in {commit[:8]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write-attestations", action="store_true")
    ap.add_argument("--append-log", action="store_true")
    ap.add_argument("--prune-registry", action="store_true")
    ap.add_argument("--branch", default=None)
    args = ap.parse_args()
    if args.write_attestations:
        write_attestations()
    if args.append_log:
        append_log()
    if args.prune_registry:
        if not args.branch:
            raise SystemExit("--prune-registry requires --branch")
        prune_registry(args.branch)


if __name__ == "__main__":
    main()
