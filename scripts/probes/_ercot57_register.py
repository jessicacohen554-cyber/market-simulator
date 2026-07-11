"""ercot57 registration helpers for the one-shot CI workflow (relay fallback).

Three idempotent modes, mirroring ``_ercot56_register.py`` (the authoring
session's environment cannot push the ~600 KB calibration log or the ~1 MB
run payloads through the MCP relay, so these run on the CI runner):

* ``--write-attestations`` — derive the ercot57_thermavail main arm's
  ``calibration_attestation.json`` from the PROMOTED ercot56-nucwin keeper's
  (inherited DOF ledger, ZERO new tunables — the class-day thermal series is
  measured disclosure data, so per the ledger convention it extends the
  ``seeded`` note rather than adding an entry). The ablation twin carries no
  attestation (D-3 twins never do).
* ``--append-log`` — marker-guarded append of the ERCOT-57 session entry to
  ``docs/calibration-log.md``.
* ``--prune-registry --branch B`` — delete the over-retention ERCOT
  registration's sidecar + runs files via the GitHub Data API (top-15
  retention, twins exempt, CLAUDE.md rule 15). Bundle dirs under
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
KEEPER_ATT = REPO / "results/calibration/ercot56_nucwin/calibration_attestation.json"
MAIN_BUNDLE = REPO / "results/calibration/ercot57_thermavail"

OWNER = "jessicacohen554-cyber"
GH_REPO = "market-simulator"
API = "https://api.github.com"

# Top-15 retention: with ercot57 + twin registered the ERCOT list stands at
# 16; drop the oldest superseded pair — ercot50's origin surface probe + its
# control, whose mechanism lives on in the ercot55-surface-ab full-span A/B
# (scored under v2.4 + cap-dual) and in every keeper since. Bundle dirs stay.
PRUNE_IDS: tuple[str, ...] = (
    "2026-07-09-ercot50-offer-surface-conditional",
    "2026-07-09-ercot50-surface-control-ablation",
)

ENTRY_MARKER = "ERCOT-57: June/Sep-2023 scarcity-formation forensics"

ENTRY = r"""
## 2026-07-11 — ERCOT-57: June/Sep-2023 scarcity-formation forensics — the +22 % June overshoot root-caused to PHANTOM reserve-shortfall pricing (statistical gas availability 13-22 % derated at the summer reserve margin vs the measured disclosure fleet; per-product VOLL-ramp ladders print it into the energy duals); fixed as measured data (`ercot_thermal_dam_availability`), which ALSO exposes the July-Sep scarcity formation as leaning on the same phantom tightness — ercot57 thermavail + twin registered as the honest record, keeper stays ercot56-nucwin

**Task (owner lane, opened at the ercot56 promotion).** With the measured
nuclear structure in place, June-2023 overshoots +22 % (was +7 %) — find the
real owner of June scarcity over-formation; measured-comparison first, no
retune of the nuclear input / offer curves / sigmoids / ORDC (rules
1/13/15/26).

**Forensics (diagnose-first; full detail in
docs/DIAGNOSIS-ercot-june2023-scarcity-formation-2026-07.md).** (1) The June
overshoot lives on FIVE days (Jun 14/16/18/19/26 carry ~127 % of the net gap;
the one real scarcity day, Jun 20, is UNDER-priced −$153/h) — at QUANTIZED
prices ~$470/~$900/~$1,350 = the co-opt product-family shortfall steps
k×VOLL/12 + marginal fuel. On every over-formed day measured RTORPA ≤ $15 and
PRC ≥ 4,880 — reality priced no reserve scarcity there. Sep-2023 (+19 %
equal-hour) is the same signature (Sep 20/22/23/24/26; RTORPA ≤ $7).
(2) Suspects tested against measured series: AS-plan requirement + LR/storage
credits FAITHFUL (zero June hours with fast-req > measured RTOLCAP); the WS-A
forward reserve-supply cap SLACK (10.3-10.7 GW vs 4.2-6.6 GW headroom, dual
0.0 — REFUTED as driver); the conditional offer surface NOT the price-setter
(rungs are reserve-step penalties). (3) The defect: at every over-form hour
the model's entire spare responsive capacity is already holding reserve
(headroom == cleared, 4.2-6.6 GW) vs measured RTOLCAP+RTOFFCAP 6.3-12.4 GW —
a 2.6-4.1 GW phantom headroom deficit with the energy side faithful (model
thermal dispatch −0.2..−1.2 GW vs EIA-930). Class forensics (60-Day DAM
Gen_Resource, config-collapsed; the May-2024 method): June-evening model
derates CC_REGULAR 23.8 % / CT_PEAKER 23.9 % vs measured class-day fractions
0.79-0.87 — the statistical WEFOR/EFOR stack (relief configured only for
ST_CHP/ST_GAS) runs 7-10 pp tighter than the measured realization exactly at
the margin; window-edge errors are secondary (~1-1.5 GW: Bastrop 2-days-early,
Tenaska non-out zeroing, Wharton idle-vs-out). The product families short
0.3-2.6 GW and their NYISO-imported VOLL-ramp ladders (no pre-RTC+B ERCOT
analogue — RT reserve scarcity prices ONLY via the ORDC total curve, which the
model's fifth family carries CORRECTLY, $15-43 ≈ measured RTORPA at matching
levels) print $417-1,250 into the energy duals. ercot55 cross-check: Jun 14/16
over-formed pre-nuclear too (day-means $213/$211 vs actual $54/$95) — the
defect PRE-DATES ercot56; the honest nuclear input moved more days over the
same cliff.

**Fix landed as measured data (rules 13/14/15).**
`scripts/derive_ercot_thermal_dam_availability.py` →
`data/raw/ercot-thermal-dam-availability.csv`: measured CLASS-day thermal
availability from the 60-Day DAM disclosure (config-collapsed live Gen_Resource
HSL / site p98 ratings; OUT counts zero, OFF counts its reported HSL —
commitment state is not an availability event; 2023-2025 delivery years;
Oct-2023 hole + Nov-Dec 2025 uncovered → statistical kept). Applied under new
`ScenarioConfig.ercot_thermal_dam_availability` (default off; ERCOT
backcast-gated; both CLIs; meta/run_config recorded; loader
`outages.ercot_thermal_dam_availability_series`) as a class-day RESCALE of the
finished availability (CC_REGULAR + CT_PEAKER scope) — the measured fraction
and the statistical stack estimate the SAME quantity, so the class-day total
is set to the measured value while the model's own outage windows stay the
within-class distribution (no stacking, no double-count; cap-1.0 water-fill;
floors clamp automatically; forecast keeps the statistical stack — the G4
mode-aware seam). Zero new tunables (DOF ledger seeded-note extension).

**Rule-16 throwaway probe (2023-only, never registered): the phantom days are
CURED and a SECOND compensation is exposed.** Jun 14: $194.9 → $30.7 day-mean
(actual $53.6); Jun 16: $175.8 → $30.2 ($95.0); Jun 19: $212.2 → $31.4
($48.4); Jun 26: $103.6 → $31.0 ($35.8); Sep 20/23/24 → $34-36 (actuals
$43-91). June monthly +26.7 % → −41.9 %; Sep +19.3 % → −59.7 %; Aug +0.9 % →
−65.1 %; 2023 tail 171 → 33 h. The measured RTORPA series discriminates the
collapse day-by-day: reality's TRUE reserve-scarcity days survive the measured
fleet (Aug 17/24/25/30 — PRC 3.3-4.7 GW, RTORPA $205-651 — still form
$1,216-5,000 max), while the offer-carried days collapse (Aug 10/28 — PRC ≥
5.2 GW, RTORPA ≤ $19.5 — to $103/$54), exactly like June 14/16. **The keeper's
July-Sep 2023 fit was riding the same phantom tightness: a rule-15 DISCOVERED
COMPENSATION one layer deeper** — the statistical availability stack was
standing in for BOTH real derates AND the missing commitment-thinness
structure (the LP's full-fleet headroom vs reality's ~RTOLCAP online room) AND
part of the G-22 offer-formation residual (whose true size was masked).

**Confound discovered in the ercot41 envelope rejection (documented, not
actioned — rejected-family, owner lane).** The G-22 on-line-capacity envelope
was identified (deliv_env) and A/B'd ON the phantom-tight fleet:
envelope-on-phantom-fleet double-tightens (the recorded over-fire),
measured-fleet-no-envelope double-loosens (this probe). The joint
configuration — measured availability + an envelope re-identified on the
measured-fleet basis — was NEVER TESTED and is the structurally-indicated
completion of this lane (its re-derivation trigger is this data change, rule
23), together with the product-ladder design question (per-product VOLL ramps
vs ORDC-only scarcity pricing). Both need owner sanction (rules 1/22: LOYO
before promotion).

**Runs (full 2023-2025 + zero-forcing twin, solved locally then re-solved and
registered via the `ercot57-solve-register` workflow).** Recipe = the PROMOTED
keeper (ercot56-nucwin) reconstructed from its meta.json via `_ercot57_ab.py`
+ the flag — ONE measured-input delta, zero new free parameters:

| run | C3a (23/24/25) | C3b | C3c h vs DA 311/68/23 | Jun-23 | Aug-23 | May-24 |
|---|---|---|---|---|---|---|
| ercot56 nucwin (keeper) | +3.9/−4.5/−1.1 % | .133/.183/.094 | 171/27/25 | +22 % | +1 % | −33.2 % |
| ercot57 thermavail | −45.4/−14.1/−8.7 % | .845/.188/.106 | 33/14/2 | −41.9 % | −65.1 % | **−1.6 %** |

Determination NOT-YET (C3a 2023/2024, C3b-2023, C3c all years — the honest
residual). Inside the losses, two measured-input WINS that validate the series
independently of 2023: **May-2024 −33.2 % → −1.6 %** (the spring-2024
"+1.5-4.1 GW excess-available May 2-16" input fatness the May forensics
documented is CURED by the same measured series — the statistical stack was
too tight in summer-2023 AND too loose in spring-2024, and the measurement
fixes both in the measurement's direction), 2024 C3b 0.183→0.188 ≈ flat and
2025 near-keeper (C3b 0.106, C3a −8.7 % PASS). C1 16/16 (free 12/12) and
C2/C4/C5a PASS on the measured fleet — the volumes never depended on the
phantom derate.

**Why this registers with a WORSE fit (rules 1/14/15 verbatim).** The measured
input is rule-14 accurate data replacing a statistical estimate; the fit
collapse is the discovered-bug signal, not a reason to revert: "if swapping a
hand estimate for real data makes the backcast worse, that is a signal that
something else in the model is miscalibrated and the estimate was silently
compensating — keep the accurate input, find and fix the real root cause."
The real root causes now have honest sizes: (a) commitment thinness (the
envelope lane, confound documented above), (b) the G-22 offer/DA-expectation
formation (the already-filed residual, true size now visible). Keeper stays
ercot56-nucwin (owner's call, rule 1: the keeper is the most structurally
faithful COMPLETE model; ercot57 is more faithful on inputs but missing the
real structure those inputs expose — the owner decides which side of that
trade the keeper sits on, with the joint envelope round as the filed path
out).

**Registry retention (rule 15).** ERCOT pruned 16 → 14: the superseded
ercot50 origin-surface pair dropped (sidecars + run payloads; bundle dirs
kept as the archival record).

**Holdouts.** No solve, score, or intake outside 2023-2025 (rule 22); the
disclosure intake reads 2023-2025 delivery dates only; ORDC tariff parameters
untouched (rule 26); no offer-curve, sigmoid, floor, or derive-script value
changed (rules 13/21/23) — the new deriver is a new measured input with a
frozen formula (re-runs only on a disclosure-data update), and no residual
was retuned against (the June overshoot is fixed by the input's ACCURACY, not
by fitting it).
"""


def write_attestations() -> None:
    """Write the ercot57_thermavail main-arm attestation (idempotent)."""
    src = json.loads(KEEPER_ATT.read_text())
    out = {
        "schema": src["schema"],
        "governance": dict(src["governance"]),
        "exceptions": [],
        "free_parameters": dict(src["free_parameters"]),
    }
    out["governance"]["attested_by"] = (
        "ercot57 thermavail keeper-track candidate gate, session 2026-07-11 "
        "(June/Sep-2023 scarcity-formation forensics; full scored 2023-2025 "
        "bundle + zero-forcing ablation twin ercot57_thermavail_ablation; "
        "owner promotion PENDING — keeper stays ercot56-nucwin)"
    )
    out["governance"]["note"] = (
        "Keeper-track arm on the PROMOTED ercot56-nucwin recipe, ONE "
        "measured-input delta, ZERO new free parameters: "
        "ercot_thermal_dam_availability=True — the CC_REGULAR/CT_PEAKER "
        "classes' availability rescaled so each class-day mean equals the "
        "measured 60-Day DAM disclosure fraction (config-collapsed live "
        "Gen_Resource HSL / site ratings; OUT counts zero, OFF counts its "
        "reported HSL — commitment state is not an availability event; "
        "data/raw/ercot-thermal-dam-availability.csv, "
        "scripts/derive_ercot_thermal_dam_availability.py). Replaces the "
        "statistical WEFOR/EFOR ESTIMATE of the same quantity with its "
        "measured realization — the model's own discrete outage windows stay "
        "as the within-class distribution (rescale, not stacking); uncovered "
        "dates (Oct-2023 publication hole, Nov-Dec 2025) keep the "
        "statistical model; forecast mode untouched (the statistical stack "
        "is the forward analogue — G4 mode-aware seam). Root cause fixed: "
        "the June/Sep-2023 phantom reserve-shortfall pricing (statistical "
        "stack 13-22% derated at the summer-evening reserve margin vs the "
        "disclosure's ~97%-of-ratings live fleet -> 2.6-4.1 GW phantom "
        "headroom deficit vs measured RTOLCAP+RTOFFCAP -> the co-opt's "
        "per-product shortfall ladders printed $417-1,250 into energy duals "
        "on days measured RTORPA was <= $15; "
        "docs/DIAGNOSIS-ercot-june2023-scarcity-formation-2026-07.md). "
        "No offer curve, sigmoid, floor, or ORDC parameter touched."
    )
    fp = out["free_parameters"]
    fp["seeded"] = fp["seeded"] + (
        "; ercot57 delta appended 2026-07-11 (this round): "
        "ercot_thermal_dam_availability measured class-day thermal "
        "availability rescale (measured-input grain fix, no parameter) - no "
        "entry added because it introduces no tunable; no inherited scalar "
        "re-tuned"
    )
    for e in src["exceptions"]:
        e = dict(e)
        e["reason"] = "Inherited by ercot57. " + e["reason"]
        out["exceptions"].append(e)
    dst = MAIN_BUNDLE / "calibration_attestation.json"
    dst.write_text(json.dumps(out, indent=1))
    print(f"wrote {dst}")


def append_log() -> None:
    """Append the ERCOT-57 calibration-log entry (marker-guarded)."""
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
