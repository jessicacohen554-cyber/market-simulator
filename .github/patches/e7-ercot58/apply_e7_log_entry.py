#!/usr/bin/env python3
"""Append the 2026-07-12 E7 adjudication entry to docs/calibration-log.md.

Script transport (g61b/ercot57/pjm97/caiso7475 precedent): calibration-log.md
is too large to relay whole through the MCP push_files call, so the small
entry travels here and an Actions job appends it server-side. Idempotent —
guarded on the entry header, safe to re-run.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
LOG = REPO / "docs" / "calibration-log.md"
AUDIT = REPO / "scripts" / "audit_keepers.py"

# Inserted at the head of E7_STALENESS_ADJUDICATED (scripts/audit_keepers.py).
AUDIT_ANCHOR = "E7_STALENESS_ADJUDICATED: dict[tuple[str, str], str] = {\n"
AUDIT_GUARD = '"2026-07-11-ercot58-joint-ordc-only",'
AUDIT_INSERT = """\
    # 2026-07-12 KEEP: ercot58-joint-ordc-only is the registered honest record
    # of the owner-sanctioned ERCOT-58 joint probe round (rules 1/15/16), not a
    # keeper candidate — its v3 realized-room RTORPA converts the ledgered
    # C5c/G-37 storage-dispatch-shape error into price errors (C3a
    # +324/+71/+206 %), and the round's own log entry disposes "keeper stays
    # ercot56-nucwin" three times. Re-probe v3 only after the storage-cycling
    # lane (measured-award energy co-participation) closes. See
    # calibration-log "2026-07-12 — E7 adjudication".
    (
        "2026-07-10-ercot56-nucwin",
        "2026-07-11-ercot58-joint-ordc-only",
    ): "2026-07-12",
"""

HEADER = (
    "## 2026-07-12 — E7 adjudication: ERCOT keeper/newer-run pair "
    "(ercot56-nucwin vs ercot58-joint-ordc-only) adjudicated KEEP"
)

ENTRY = """
## 2026-07-12 — E7 adjudication: ERCOT keeper/newer-run pair (ercot56-nucwin vs ercot58-joint-ordc-only) adjudicated KEEP — ercot58 is the honest record of a probe round, not a keeper candidate; keeper stays ercot56-nucwin

**Task (owner delegation, this session).** Adjudicate the open E7 staleness
WARN on ERCOT: `2026-07-11-ercot58-joint-ordc-only` is newer than the keeper
`2026-07-10-ercot56-nucwin`. Compared verdicts and structural fidelity per
rule 1 (keeper = most structurally faithful, never lowest MAE — and never
highest, either: the test is whether the run is the most faithful COMPLETE
model).

**Adjudication: KEEP ercot56-nucwin.** ercot58 was registered under rules
1/15/16 as the honest record of the owner-sanctioned ERCOT-58 joint round
(measured DAM availability + measured-basis envelope + ORDC-only v3), and its
own log entry disposes "keeper stays ercot56-nucwin" — it was never promoted
nor recommended. On the merits: ercot58's components are individually
measured-anchored, but the v3 realized-room RTORPA construction converts the
keeper's ledgered C5c/G-37 storage-dispatch-shape error (plus the
binding-regime class-mix gap) into a +2.4 GW phantom room deficit, printing
C3a +324/+71/+206 % and a 3.3–19.9× C3c tail — verdict NOT-YET with all three
price criteria at MODEL-MISS FAIL. A mechanism that faithfully AMPLIFIES a
known upstream dispatch error into the price stack is doing its structural
job as a diagnostic (rule 14), but a keeper must be the most faithful
complete model, and ercot56 carries the same measured nuclear/outage/offer
structure without routing the open storage lane through the price formation.
The filed forward path stands: close the storage-cycling lane (measured-award
energy co-participation, DIAGNOSIS-ercot-storage-cycling-lane-2026-07.md),
then re-probe v3.

**Executed.** Pair recorded in `E7_STALENESS_ADJUDICATED`
(`scripts/audit_keepers.py`) dated 2026-07-12 (annotation only — the WARN
stays visible per G-04 convention); `status.js` rebuilt (`build_status.py`,
S1 was stale); audit_keepers green (0 FAIL; the MISO E7 WARN on
miso-56-vs-miso-57 stays UNADJUDICATED — that pair is a live
PROMOTE-recommendation awaiting the owner, not a KEEP). No solve, no bundle,
no registry change.
"""


def main() -> None:
    audit = AUDIT.read_text()
    if AUDIT_GUARD in audit:
        print("already applied - audit_keepers.py unchanged")
    else:
        assert AUDIT_ANCHOR in audit, "E7_STALENESS_ADJUDICATED anchor not found"
        AUDIT.write_text(audit.replace(AUDIT_ANCHOR, AUDIT_ANCHOR + AUDIT_INSERT, 1))
        print("inserted E7 adjudication pair into %s" % AUDIT)

    text = LOG.read_text()
    if HEADER in text:
        print("already applied - calibration-log.md unchanged")
        return
    if not text.endswith("\n"):
        text += "\n"
    LOG.write_text(text + ENTRY)
    print("appended E7 adjudication entry to %s" % LOG)


if __name__ == "__main__":
    main()
