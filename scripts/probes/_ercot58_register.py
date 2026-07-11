"""ercot58 registration helpers for the one-shot CI workflow (relay fallback).

Three idempotent modes, mirroring ``_ercot57_register.py`` (the authoring
session's environment cannot push the ~600 KB calibration log or the ~1 MB
run payloads through the MCP relay, so these run on the CI runner):

* ``--write-attestations`` — derive the ercot58_joint main arm's
  ``calibration_attestation.json`` from the PROMOTED ercot56-nucwin keeper's
  (inherited DOF ledger, ZERO new residual-fitted tunables — the joint round's
  deltas are a measured input, measured-MW-identified derived tables, and a
  fixed tie-break epsilon). The ablation twin carries no attestation (D-3
  twins never do).
* ``--append-log`` — marker-guarded append of the ERCOT-58 session entry to
  ``docs/calibration-log.md``.
* ``--prune-registry --branch B`` — delete the over-retention ERCOT
  registration's sidecar + runs files via the GitHub Data API (top-15
  retention, CLAUDE.md rule 15). Bundle dirs under ``results/calibration/``
  stay (archival record).
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
KEEPER_ATT = REPO / "results/calibration/ercot56_nucwin/calibration_attestation.json"
MAIN_BUNDLE = REPO / "results/calibration/ercot58_joint"

OWNER = "jessicacohen554-cyber"
GH_REPO = "market-simulator"
API = "https://api.github.com"

# Top-15 retention: with ercot58 + twin registered the ERCOT list stands at
# 16; drop the oldest superseded pair — the ercot51 coal net-summer-derate
# A/B, whose mechanism (coal_nameplate_summer_derate) was adopted into every
# keeper since ercot51 and is scored inside each of them. Bundle dirs stay.
PRUNE_IDS: tuple[str, ...] = (
    "2026-07-09-ercot51-coal-netsummer-derate",
    "2026-07-09-ercot51-coal-netsummer-ablation",
)

ENTRY_MARKER = "ERCOT-58: the ercot57 joint round executed"

ENTRY = r"""
## 2026-07-11 — ERCOT-58: the ercot57 joint round executed (owner-sanctioned) — measured availability + the envelope RE-IDENTIFIED on the measured-fleet basis + the ORDC-only product-ladder question ADJUDICATED across three probes; the market-faithful form (plan-only in-LP withholding + post-solve realized-room RTORPA) is LP-healthy and cures the phantom-scarcity channel, but its realized room measures a +2.4 GW binding-regime thermal-dispatch excess (storage under-discharge at evening peaks, the C5c/G-37 lane) — ercot58 joint + twin registered as the honest record, keeper stays ercot56-nucwin

**Task (owner sanction 2026-07-11, this session — the ERCOT-57 filed
completion, opening the rule-26 reserve-demand/product-ladder design round).**
Test the never-tested joint configuration: `ercot_thermal_dam_availability` +
an on-line-capacity envelope re-identified on the measured-fleet basis + the
per-product-VOLL-ramps vs ORDC-only scarcity-pricing design question. Full
three-probe adjudication: docs/DIAGNOSIS-ercot58-joint-round-2026-07.md.

**Leg B re-identification (measured-fleet basis, rules 13/14/23 — trigger:
the ercot-thermal-dam-availability.csv intake).** The ercot41/43 share tables
(committed on-line HSL / INSTALLED capacity) conflated commitment choice with
outage state. New `ercot_online_capacity_envelope_measured`: share =
committed HSL / MEASURED AVAILABLE capacity for the disclosure-covered
classes (CC_REGULAR, CT_PEAKER); basis = the fleet's finished availability
(measured rescale in backcast, statistical stack forward — the G4 seam); CHP
on the export basis (CAMPD gross is full cogen host+grid, the model's CHP is
grid-export — a ~2.5 GW room inflation otherwise). Identification gate
PASSED (`validate_ercot_online_capacity.py --measured`): binding regime
+3/+1/−3 %, pooled top-2 % extreme tail EXACT (−0.0 %), coverage 2.11×; the
per-year extreme-tail ledger tightens from ercot43's −23/−2/+18 % to
−13/−0/+9 % — the availability decomposition carries about half the
cross-year capability spread (the ERCOT-57 confound confirmed). A measured
check of the commitment share on the availability basis is FLAT
(~0.94-0.95) across years and across both a within-year-rank and an
absolute-net-load axis: availability, not commitment, was the cross-year
term.

**Leg C adjudication (rule-16 2023-only throwaways, never registered).**
* **v1 — in-LP ORDC total family + envelope LP row: REJECTED.** C3a +55 %,
  62 GWh shed, 12.8 GW of coal parked at the Aug-25 peak: the total curve's
  VOLL-floored sub-MCL steps (OBDRR048) make reserve-holding and load-shed
  exactly degenerate, so the LP withholds up the full span inside the
  envelope — the ercot43 §7.4 defect reproduced with the availability
  confound removed. The in-LP span demand is the defect, not the fleet.
* **v2 — plan-only withholding + envelope as a HARD LP row: REJECTED.**
  833 GWh shed across 476 summer hours (C3a +707 %): an LP cap anchored to
  reality's committed capability converts every model-vs-reality supply-mix
  difference at tight hours into VOLL shed. Pre-RTC+B SCED carries no
  committed-capability dispatch constraint at all.
* **v3 — the market-faithful form (registered):** ε-held product plans (the
  DAM award's physical withholding; `ERCOT_AS_PLAN_HOLD_EPS` = 0.001, a
  fixed tie-break, not a fit) + the rigid pre-reform ECRS_withheld + NO
  envelope LP row + NO in-LP total family; RTORPA computed POST-SOLVE on the
  realized room (`scarcity.ercot_ordc_realized_adder`: online = env_all − ΣP
  + measured storage-AS + LR credit; offline = forward RTOFFCAP; the
  published two-half-hour LOLP construction with the OBDRR048 floor mask —
  RTSPP = SPP + RTORPA, Nodal Protocols §6.5.7.5). LP-healthy (shed
  0.2 GWh); the June/Sep-2023 phantom channel stays cured; rule 19 enforced
  (`ercot_ordc_only_scarcity` FORBIDS `ercot_ordc_total_reserve` and the
  cap-dual adder path).

**Runs (full 2023-2025 + zero-forcing twin, solved locally then re-solved
and registered via the `ercot58-solve-register` workflow).** Recipe = the
PROMOTED keeper (ercot56-nucwin) reconstructed from its meta.json via
`_ercot58_ab.py` + the three deltas; zero new residual-fitted parameters.
Session-computed scores (official rubric lands with the registered sidecar):

| run | C3a lw (23/24/25) | monthly NRMSE | h>$200 vs DA 310/68/24 |
|---|---|---|---|
| ercot56 nucwin (keeper) | +3.9/−4.5/−1.1 % | .133/.183/.094 (C3b) | 171/27/25 |
| ercot57 thermavail | −45.4/−14.1/−8.7 % | .845/.188/.106 (C3b) | 33/14/2 |
| ercot58 joint (v3) | **+324/+71/+206 %** | 4.78/2.18/7.20 | 1022/255/457 |

Determination NOT-YET — registered as the honest record (rules 1/15/16);
**keeper stays ercot56-nucwin.**

**The uncovered root cause (the round's real yield).** The realized room runs
systematically tight because the model serves ~+2.4 GW MORE of the
binding-regime (top-30 % net-load) load with envelope-class thermal than the
CAMPD export-basis gross shows reality did — sitting exactly on the steep end
of the ORDC. Leading identified component: **model storage discharges 145 MW
mean at binding hours (net +108 MW) where the real 2023 battery fleet ran
~1-2 GW at evening peaks** — the batteries are AS-committed (measured award
reserved out of the power cap) and the perfect-foresight arbitrage does not
reproduce the real evening-peak discharge. This is the SAME open lane as the
keeper's ledgered C5c-2024 storage-shape caveat (r = 0.361) and the G-37
duration-gate finding; the realized-room construction converts that known
dispatch-shape error into a price error — exactly what a structurally honest
mechanism should do (rule 14: keep the accurate structure, fix the real root
cause). Secondary terms: ST_GAS +1.3 GW / CT_PEAKER −0.6 GW binding-regime
class-mix shifts, and the CAMPD-gross-vs-model-net metering wedge (which
biases the room LOOSE, i.e. the supply-mix gap is somewhat larger than
+2.4 GW).

**Filed forward path.** (a) The binding-regime supply mix, storage first
(evening-peak battery discharge — the C5c/G-37 lane: forward AS commitment
under uncertainty and/or measured-award energy co-participation), then the
ST_GAS/CT class-mix at the peak; (b) re-probe v3 when that lane closes — its
room is bounded by the same gap, and every other component (availability,
envelope identification, plan withholding, adder construction) is
measured-anchored and already gated. The G-22 DA-shoulder offer-formation
residual stays with its filed owner (the conditional-offer-distribution
lane), untouched by this round. LOYO (rule 22) not run — required only
before promotion, and nothing here is promotable.

**Holdouts / governance.** No solve, score, or intake outside 2023-2025
(rule 22); ORDC tariff parameters (VOLL, MCL, LOLP μ/σ, floor steps)
untouched at every step (rule 26) — the three probes changed only WHICH
mechanism carries them; no offer curve, sigmoid, floor, or derive-script
value changed (rules 13/21/23); the envelope constants re-derived under
their rule-23 trigger (the disclosure intake); registry pruned to top-15
(the ercot51 coal-net-summer pair — mechanism adopted into every keeper
since; bundle dirs stay).
"""


def write_attestations() -> None:
    """Write the ercot58_joint main-arm attestation (idempotent)."""
    src = json.loads(KEEPER_ATT.read_text())
    out = {
        "schema": src["schema"],
        "governance": dict(src["governance"]),
        "exceptions": [],
        "free_parameters": dict(src["free_parameters"]),
    }
    out["governance"]["attested_by"] = (
        "ercot58 joint-round registration gate, session 2026-07-11 "
        "(owner-sanctioned ercot57 filed completion; full scored 2023-2025 "
        "bundle + zero-forcing ablation twin ercot58_joint_ablation; "
        "determination NOT-YET — keeper stays ercot56-nucwin)"
    )
    out["governance"]["note"] = (
        "Honest-record arm on the PROMOTED ercot56-nucwin recipe, THREE "
        "deltas, ZERO new residual-fitted parameters: (1) "
        "ercot_thermal_dam_availability=True (the ercot57 measured 60-Day "
        "DAM class-day availability rescale); (2) "
        "ercot_online_capacity_envelope_measured=True — the G-22 envelope "
        "re-identified on the measured-fleet basis (share = committed HSL / "
        "measured AVAILABLE capacity for CC_REGULAR/CT_PEAKER; basis = the "
        "fleet's finished availability; CHP export basis; identification "
        "gate PASSED: binding +3/+1/-3%, pooled top-2% exact, coverage "
        "2.11x) — under the ORDC-only flag the envelope is a PRICING-ONLY "
        "basis, never an LP row; (3) ercot_ordc_only_scarcity=True — "
        "pre-RTC+B ORDC-only scarcity pricing: per-product VOLL ladders -> "
        "plan-hold epsilon (fixed 0.001 tie-break), in-LP ORDC total family "
        "and cap-dual adder REMOVED (rule 19), RTORPA computed post-solve "
        "on the realized room (scarcity.ercot_ordc_realized_adder; RTSPP = "
        "SPP + RTORPA, Nodal Protocols 6.5.7.5). The three-probe "
        "adjudication (in-LP span demand and the hard envelope row both "
        "REJECTED on the honest fleet) and the uncovered +2.4 GW "
        "binding-regime supply-mix gap (storage under-discharge at evening "
        "peaks, the C5c/G-37 lane) are in "
        "docs/DIAGNOSIS-ercot58-joint-round-2026-07.md. No offer curve, "
        "sigmoid, floor, or ORDC tariff parameter touched."
    )
    fp = out["free_parameters"]
    fp["seeded"] = fp["seeded"] + (
        "; ercot58 deltas appended 2026-07-11 (this round): "
        "ERCOT_ONLINE_CAP_SHARE_MEASURED / _DELIV_PROFILE_MEASURED "
        "(measured-MW-identified derived tables, rule-23 trigger = the "
        "disclosure/CAMPD/RTOLCAP source data — no residual-fitted tunable) "
        "and ERCOT_AS_PLAN_HOLD_EPS=0.001 (fixed degeneracy tie-break, the "
        "storage-epsilon magnitude class, not fitted) - no ledger entry "
        "added because none is a free parameter; no inherited scalar "
        "re-tuned"
    )
    for e in src["exceptions"]:
        e = dict(e)
        e["reason"] = "Inherited by ercot58. " + e["reason"]
        out["exceptions"].append(e)
    dst = MAIN_BUNDLE / "calibration_attestation.json"
    dst.write_text(json.dumps(out, indent=1))
    print(f"wrote {dst}")


def append_log() -> None:
    """Append the ERCOT-58 calibration-log entry (marker-guarded)."""
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
    if not PRUNE_IDS:
        print("prune: PRUNE_IDS empty — no-op")
        return
    paths = []
    for rid in PRUNE_IDS:
        paths.append(f"frontend/data/backcast/registry/{rid}.json")
        paths.append(f"frontend/data/backcast/runs/{rid}.js")
    base = _req("GET", f"/repos/{OWNER}/{GH_REPO}/git/ref/heads/{branch}")["object"][
        "sha"
    ]
    base_commit = _req("GET", f"/repos/{OWNER}/{GH_REPO}/git/commits/{base}")
    tree = []
    for p in paths:
        try:
            _req("GET", f"/repos/{OWNER}/{GH_REPO}/contents/{p}?ref={branch}")
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
                "(bundle dirs stay) [skip ci]"
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
