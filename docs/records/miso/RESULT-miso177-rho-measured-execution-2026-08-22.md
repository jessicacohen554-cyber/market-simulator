# RESULT miso-177 — the measured-rho re-gate: floor refuted, owner-deleted, re-solved; KEEPER → `2026-08-22-miso-177-rho-measured`

**Session miso-177 (2026-08-22).** Charter: the standing owner escalation from
the miso-169 promotion and nyiso-144 — identify or refute the uncited
`RHO_CLIP` 0.5 floor, and A/B the MISO keeper at the measured coefficient.
Runs registered (rule 15, full span rule 16): control
`2026-08-22-miso-177-control` (`miso177_rho_A`), arm
`2026-08-22-miso-177-rho-measured` (`miso177_rho_B`). **Keeper →
`2026-08-22-miso-177-rho-measured`**, promoted under the owner's standing
same-session instruction, executing the owner's same-day band ruling.

---

## 1. The identification (charter steps 1–2): REFUTED, then RULED

`FINDING-miso177-rho-clip-floor-identification-2026-08-22.md`: the 0.5 floor
has no identification — negative on all three source classes. Repo record:
earliest appearance (PREREG-nyiso110 §2) asserts the band bare; the nyiso-145
card's genealogy stands (a min-load-estimand bracket `(1−f)/f`,
`f ∈ [0.2, 0.667]`, inherited across a change of estimand). Primary record
(read for this session, BPM-002-r25): per-resource reserve capability is
**ramp × deploy-time** (§4.2.1.46–47, `ContResRampMult = 1.0`,
`ContResDeployTime = 10 min` — the measured statistic's own construction);
the ONLY 0.5 in a capability role is the §4.2.1.37 **hard ceiling** on the
regulation range (wrong direction, wrong denominator, wrong product);
Schedule 28 / the reserve-demand-curve FERC record are requirement-side, and
§6.1.13 confirms the coded $98/$65/$0 curve from the primary source.

**Mid-session, the owner ruled** (session nyiso-151, rule 22 D-5(b), merged
to main while the control was solving): `RHO_CLIP (0.5, 4.0) → (0.0, 4.0)`,
decision-card option A, with the governance log handing MISO the re-gate.
The refutation and the ruling are independent and agree.

## 2. The A/B (PREREG-miso177, committed with the frozen instrument before any solve)

Same pre-ruling tree, single delta = the coefficient (0.5 → the measured
**0.17644175978069962** — byte-exactly the post-ruling seam default). Both
arms `--year 2023 2024 2025` sequential in one invocation each, on the 15 GB
container under the miso-169 memory recipe (year peak 13.30 GB).

* **R-0 CONTROL INERTNESS: PASS, perfect.** 12/12 scored sidecars
  value-identical to the committed keeper (max|diff| = 0.0, non-numeric
  equal); consumed 0.5000 per the solve log.
* **R-1 COEFFICIENT EXACTNESS: PASS.** Artifact sha256 matches the frozen
  digest; the arm's log reads `MEASURED online_rho=0.1764 (ceiling-only,
  floor refuted miso-177)` in all three years; run_configs record the
  polarity.
* **R-2 LIVENESS: LIVE, concentrated exactly as the frozen instrument
  predicted** (static aggregate surface 0/0/0 — pool-grain action only):
  244 differing P1 price cells; regspin binding hours **5→6 / 6→7 / 10→15**;
  duals now reach the **full $98 Schedule-28 step** (control maxed $84.31 /
  $84.47 in 2024/2025); bind-hour demand-weighted uplift **+$18.43 / −$0.00
  / +$11.91**; annual **+0.051 / −0.000 / +0.060 %**; the 2023 model tail
  gains one >$200 hour (3→4, vs actuals' 30).
* **R-3 CONDUCT: PASS.** ZERO D-4 conduct failures on both regenerated
  bundles, zero new — the miso-173/175 headline preserved.
* **R-6 AGAINST-INTEREST: PASS.** C3a-2023 +1.218 → +1.279 % (band ±3.0);
  C3a-2024 −4.056 → −4.056 % (adverse 0.00 pp).
* **R-7 OVER-REACH: PASS.** Worst annual 0.060 % vs the 2.0 % band.
* **R-4 / R-5 AS-WRITTEN FIRED — ON INSTRUMENT ARTIFACTS, RECORDED NOT
  REWRITTEN** (the miso-170 discipline; scorer
  `scripts/probes/_miso177_rho_ab.py`, record `_miso177_rho_ab.json`,
  committed before any result existed). R-4's `all(PASS)` coding counted the
  three `hydro SKIPPED` sub-materiality records — present identically in
  keeper, control and arm — as failures; **C8 is 12/12 scored-class PASS in
  every year on both arms.** R-5's single "flip" is the `governance`
  attestation-presence record (`PASS → UNATTESTED`), identical on the
  bit-identical control, cured by the promotion attestation itself; **zero
  flips across the 66 solve records.** The mechanical as-written verdict
  (REJECTED-AS-ARMED) is recorded in the gate JSON; the post-attestation arm
  reads the keeper's exact posture record-for-record.

## 3. Determination and promotion

With the promotion attestation (`calibration_attestation.json`, ledger 33
entries / 2 residual **unchanged** — zero new free parameters): **NOT-YET on
C3a-2025 ALONE (−11.791 → −11.747 %, disclosed never claimed — the miso-163
model-class lane), C3c the single ledgered caveat, C6 PASS, C8 PASS all
years.** Zero solve-record regressions against the predecessor.

Promoted BY THE OWNER'S STANDING SAME-SESSION INSTRUCTION ("Is this a
recommended keeper candidate? If so plz promote…"), applied to the owner's
own band ruling: the keeper now solves the armed mechanism on a
data-identified coefficient (rules 5/14/21), and is **the first
HEAD-consistent MISO keeper since the ruling** — a zero-delta replay at HEAD
reproduces it (the predecessor's 0.5 basis no longer exists in code; its
bundle is historical-record-only, like every pre-ruling MISO bundle, per the
ruling itself). `audit_keepers --iso MISO` PASS on every check, zero
repairs; `build_status --check --iso MISO` in sync.

## 4. The reconciliation (prereg §7 amendment, executed)

The transient delivery field `miso_online_rho_no_floor` was REMOVED in the
same-session merge of the ruling (rules 19/26 — it never reached main);
`replay_keeper._RULE26_DELETED_UNCONDITIONAL` carries `("MISO", True)` so
the keeper bundle replays at HEAD byte-equivalently and the control
hard-errors as historical-record-only. Validation at the merged tree: 67/67
cache-key pins (pinned default key unmoved), matrix guard exit 0,
seam/gated/NYISO-obligation suites green; the 5 forecast-lane scoring
failures at HEAD reproduce with this session's edits stashed (not ours).

## 5. Standing items after this session

1. **The RHO_CLIP escalation is CLOSED** — refuted (this session), deleted
   (the owner's ruling), re-solved and promoted (this keeper). The
   nyiso-145 decision card is executed; NYISO's gated flags are that lane's
   to re-adjudicate on the now-admissible coefficient.
2. **C3a-2025 (−11.75 %) remains the sole failing criterion** — the
   RT-only ORDC/RCPF model-class lane (miso-163 ruling; DA-foreseen half
   closed by FINDING-miso171 §6). This session's mechanism claims nothing
   against it; the reachable DA-foreseen surface is now fully priced (duals
   at the $98 step).
3. Two HEAD defects repaired in passing (both ercot-227 merge fallout):
   the `MECH_ERCOT_RUC_COMMITMENT` import drop (broke every ISO's
   diagnostics regeneration) and the matrix category `commitment`→`commit`
   (failed the CI matrix guard; independently fixed on main).
