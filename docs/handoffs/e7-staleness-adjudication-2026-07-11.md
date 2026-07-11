# E7 staleness adjudication — ERCOT (ercot58) & PJM (pjm-98), 2026-07-11

The keeper-auditor's E7 warning flagged both ISOs' designated keepers as one run
behind the newest registered run. E7 is warn-only by design ("changing the
designated keeper is the user's decision" — `.claude/agents/calibration-keeper-auditor.md`
§4); this brief records the adjudication per CLAUDE.md rules 1/15 (keeper = most
structurally faithful, never lowest error). **No keeper was changed.**
`keepers.json` stays: ERCOT → `2026-07-10-ercot56-nucwin`,
PJM → `2026-07-10-pjm-97-measured-interfaces`.

## ERCOT — RESOLVED, no owner decision needed: keeper correctly stays ercot56-nucwin

`2026-07-11-ercot58-joint-ordc-only` is not a pending candidate — it was
**adjudicated the day it was registered** (calibration-log 2026-07-11, "ercot58
joint + twin registered as the honest record, keeper stays ercot56-nucwin";
determination **NOT-YET**, confirmed against the live verdict:
C3a +308.7 / +58.8 / +183.9 %, C3b NRMSE 4.7/2.0/6.5, C3c 1022/256/457 h >$200
vs DA-actual 311/68/23 — against the keeper's C3a +3.9/−4.5/−1.1 %). It was
registered under rules 1/15/16 as the honest record of an owner-sanctioned
structural round (three measured deltas, zero new fitted parameters — DOF
ledger in `results/calibration/ercot58_joint/calibration_attestation.json`),
whose real yield was a root cause: the realized-room RTORPA converts the known
binding-regime storage under-discharge (+2.4 GW thermal excess; the ledgered
C5c/G-37 lane) into a price error. The filed forward path is to close the
storage lane first and re-probe the v3 mechanism afterwards. The E7 warning is
therefore expected steady-state — an honest-record registration newer than the
keeper — not staleness. No action.

## PJM — OWNER DECISION PENDING (this brief): keeper stays pjm-97 until then

`2026-07-11-pjm-98-cc-mustrun` is a **candidate explicitly awaiting owner
sign-off**, not an overlooked promotion:

- Its registry sidecar states "NOT a keeper; owner sign-off pending on the
  G-20 §5 over-forcing flag."
- The G-21 diagnosis (calibration-log 2026-07-11;
  `docs/handoffs/pjm-cc-overrun-benchmark-basis-g21-2026-07.md`) root-caused
  most of pjm-98's scored C1 cost to two scorer-layer benchmark defects and
  **re-flagged the promotion decision to the owner together with the proposed
  benchmark repairs** — on the measured basis pjm-98's 2024 CC over-run is
  +11.0 TWh (vs keeper +8.8), its "2023 CC flip" is in band, and the eastern
  CT under-run cells were largely a plant-bucketing artifact.
- The combined gas+coal reconcile scorer fix has since landed, but the
  committed bundles were **not re-rendered** (original `_shared` parquets
  overwritten; a reconcile-only re-render is impossible without confounding
  data drift). pjm-98's live verdict (NOT-YET; C1 2024 CC_REGULAR +23.29 TWh,
  C3a −11.6/−17.1 %) is still scored on the old, defective benchmark basis.

**Recommendation: HOLD** — defer pjm-98 promotion until the G-21 owner items
land (unit-class bucketing for the CAMPD backfill, then a controlled re-solve /
re-render of both pjm-97 and pjm-98 on the repaired scorer), and adjudicate the
G-20 §5 over-forcing flag against the corrected numbers. Promoting now would
swap keepers on scored numbers both sides agree are benchmark artifacts;
rejecting now would discard a measured, zero-fitted-scalar mechanism (CEMS
committed-tranche floor in its measured window) whose corrected cost is not yet
known. The E7 warning for PJM stays open by design until the owner decides.

*Authorization: session task 2026-07-11 (E7 staleness adjudication, judgment-laden
path — owner brief in lieu of promotion, keepers untouched).*
