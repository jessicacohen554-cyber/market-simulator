"""ercot56 keeper-promotion helpers for the one-shot CI workflow.

Companion to ``_ercot56_register.py`` (imports its paths), carrying the two
owner-approval actions the promotion workflow runs on the CI runner — the
authoring session's MCP relay cannot push the ~600 KB calibration log or the
~220 KB status.js, and re-emitting the 24 KB register helper whole risks
byte drift, so the promotion logic ships as this small fresh module
(ercot55-promote precedent).

* ``--approve-attestation`` — stamp the owner promotion approval on the
  ercot56_nucwin attestation's ``attested_by`` (same string replacement the
  authoring session applied locally, so the runner file is byte-identical to
  the session's working tree). Idempotent.
* ``--append-promotion-log`` — marker-guarded append of the keeper-promotion
  entry to ``docs/calibration-log.md``.
"""

from __future__ import annotations

import argparse
import json

from _ercot56_register import LOG, MAIN_BUNDLE

PROMOTION_MARKER = "ERCOT keeper PROMOTED: `ercot56 nucwin`"

PROMOTION_ENTRY = r"""
## 2026-07-10 — ERCOT keeper PROMOTED: `ercot56 nucwin` (CALIBRATED-WITH-CAVEATS, rubric v2.4) — owner sign-off; supersedes ercot55-surface-ab

**Owner decision (2026-07-10, May-2024 outage-forensics session, interactive
sign-off): ercot56 nucwin promoted.** The run is the promoted
ercot55-surface-ab recipe + ONE measured-input delta —
`ercot_nuclear_unit_availability`, the four ERCOT reactors moving from the
NUCLEAR_MONTHLY_CF_BY_YEAR fleet-month smear to the measured per-reactor
DAILY refuel availability (60-Day DAM disclosure NUC status, EIA-923
energy-anchored; found and validated by the May-2024 outage-vs-heat
collision forensics, ERCOT-56 entry above). Zero new free parameters.

**Scores (2023/2024/2025).** C3a +3.9/−4.5/−1.1 %, C3b 0.133/0.183/0.094,
C3c 171/27/25 h vs DA 311/68/23 (C3c-2023 ≥ the 162 h owner gate; C3c-2025
1.09× PASS), May-2024 −33.2 %, May-8 depth $1,371/$1,907 vs measured
$2,420/$2,368, Nov-2024 −3.9 %. Determination CALIBRATED-WITH-CAVEATS with
the SAME 2 ledgered caveats as the prior keeper (C3c-2024 27 h vs 68 DA —
the G-22 offer-formation residual, now forensically adjudicated as NOT
availability; C5c-2024 storage shape), zero fails, C8 ST_GAS grounded both
years.

**Adopted knowingly:** the honest 2023 movement (C3a +2.0→+3.9 %, C3b
0.106→0.133, both PASS) is the real June-2023 heat-dome nuclear structure
(CP-1 trip + measured ~0.73 late-June derate, EIA-930-confirmed) exposing a
June scarcity-formation compensation (+7 %→+22 % June overshoot) — an open
root-cause lane, deliberately NOT retuned (rule 15).

**LOYO basis (rule 22).** Zero residual-fitted parameters: the delta is
measured window data reconciled to the already-committed measured energy
anchor — the ercot53/ercot55 "zero-parameter" clean basis. DOF ledger
inherited verbatim (seeded-note extension only).

**Bookkeeping.** `keepers.json` ERCOT → `2026-07-10-ercot56-nucwin` (prior
keeper ercot55-surface-ab stays registered as the prior-keeper reference);
`status.js` rebuilt (ERCOT line CALIBRATED-WITH-CAVEATS); nucwin sidecar
carries the promotion note, ercot55 sidecar re-worded superseded; the
attestation `attested_by` records the owner approval; zero-forcing twin
`2026-07-10-ercot56-nucwin-ablation` registered alongside (rule 20).
Publication via the `ercot56-promote` workflow (session relay-ceiling
fallback; ercot55-promote precedent).

**Holdouts.** No solve, score, or intake outside 2023-2025 (rule 22); ORDC
tariff parameters untouched (rule 26); promotion changes no model code or
tunable (rules 13/21/23) — governance files only.
"""


def approve_attestation() -> None:
    """Record the owner promotion approval on the main arm's attestation.

    Applies the same string replacement the authoring session applied
    locally, so the runner-stamped attestation is byte-identical to the
    session's working tree. Idempotent (no-op once APPROVED is present).
    """
    dst = MAIN_BUNDLE / "calibration_attestation.json"
    a = json.loads(dst.read_text())
    if "APPROVED" in a["governance"]["attested_by"]:
        print("approve-attestation: already approved — no-op")
        return
    a["governance"]["attested_by"] = a["governance"]["attested_by"].replace(
        "owner promotion PENDING — keeper stays ercot55-surface-ab",
        "owner promotion APPROVED 2026-07-10 (May-2024 outage-forensics "
        "session, interactive sign-off) — supersedes ercot55-surface-ab",
    )
    assert "APPROVED" in a["governance"]["attested_by"]
    dst.write_text(json.dumps(a, indent=1))
    print("approve-attestation: stamped")


def append_promotion_log() -> None:
    """Append the keeper-promotion calibration-log entry (marker-guarded)."""
    text = LOG.read_text()
    if PROMOTION_MARKER in text:
        print("append-promotion-log: already present — no-op")
        return
    if not text.endswith("\n"):
        text += "\n"
    LOG.write_text(text + PROMOTION_ENTRY.lstrip("\n"))
    print("append-promotion-log: appended")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--approve-attestation", action="store_true")
    ap.add_argument("--append-promotion-log", action="store_true")
    args = ap.parse_args()
    if args.approve_attestation:
        approve_attestation()
    if args.append_promotion_log:
        append_promotion_log()


if __name__ == "__main__":
    main()
