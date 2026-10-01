# FINDING — ercot-225 (the G-SPUR band-top blindness OWNER GATE REVISION, drafted as a decision card; NO LP, no solve, no gate change): the lidless re-reading of ALL 11 registered ERCOT runs changes ZERO standing verdicts, exonerates the one recorded artifact-leg FAIL (ercot-215's "2025 0→1"), strengthens both recorded FAILs a fortiori, and surfaces two hours the current gate structurally cannot see — the card is pushed AWAITING OWNER SIGN-OFF

**Session ercot-225, 2026-08-21, branch `claude/ercot-225-gspur-gate-z1q0f6`.**
Keeper resolved fresh at dispatch AND end:
**`2026-08-20-ercot223-arm-eventrelease`** — UNCHANGED (NOT-YET, fail set
{C3a-2023 −39.7 %, C3b-2023 0.729}, C3c ledgered CAVEAT ×3). Queue basis: the
R-A re-pointed queue's LAST standing item (item 8 was spent NEGATIVE at
ercot-224 and is not re-screened). **Phase-0 ordering honoured:** the revised
spec and the complete re-reading protocol were precommitted, pushed and
blob-verified (`docs/PRECOMMIT-ercot225-gspur-bandtop-gate-revision-2026-08-21.md`,
blob `9b55eac9`, commit `ff26017`) BEFORE any re-reading was computed.
Probe: `scripts/probes/ercot225_gspur_bandtop_reread.py` →
`results/calibration/ercot225_gspur_bandtop_reread.json` (committed).
Card: `results/calibration/DECISION-ercot225-gspur-bandtop-gate-2026-08-21.md`.
**The gate files are NOT edited; nothing changes without owner sign-off.**

## 0. VERDICT — the three dispatched questions, answered

**(a) The revised spec** (card §2): gate on
`S_nolid = #{model ≥ 150 & actual < 150}` (Option A, recommended), report
the `S_band`/`S_top` decomposition (`S_top = #{model > 500 & actual < 150}`
— the blind population); Option B = report-only side-by-side; Option C =
status quo. Bar semantics keep their shape; under Option A the baseline
constant re-reads **9/11/1 → 9/12/1** (the lidless re-read of the same
baseline bundle, `ercot215_decontam_B`).

**(b) The measured effect on every registered run** — all 11 ERCOT registry
entries re-read from committed sidecars only, both NaN conventions agreeing
on every count (probe JSON `runs`). Headline rows (2023 · 2024 · 2025,
banded → lidless):

* keeper `ercot223-arm-eventrelease`: 11·11·1 → **11·12·1** (S_top 0·1·0)
* `ercot213-arm-pubanchor` / `ercot215-ctl`: 17·13·0 → **24·14·1**
  (S_top **7**·1·**1**)
* `ercot219-arm-optionb`: 273·671·1239 → **2210·1330·2402** (S_top
  **1937**·659·1163 — the recorded 2023 count concealed ~8× its size)
* every 204/213-lineage control: 9·11·0 → 9·12·**1**

**(c) Which historical verdicts flip:** exactly ONE, and it is the
exonerating one. **ercot-215's recorded strict-leg G-SPUR FAIL (2025 0→1,
`ercot215_ab.json`) flips to PASS on both its rules** — lidless the
decontamination reads 24→9 / 14→12 / 1→1, strictly non-increasing in every
year; the recorded "regression" was the blindness artifact itself (the
control's h3355 hidden at $1,411). **Nothing else flips:** ercot-204 PASS
stays; ercot-213's REJECTED-AS-ARMED G-SPUR FAIL stays and STRENGTHENS
(2023 9→17 banded was really 9→**24**, +15 against the +5 bar; the strict
leg now also fails 2024, 12→14); ercot-219 FAIL stays a fortiori; ercot-221
and the current keeper ercot-223 keep PASS with margin (11·11·1 and 11·12·1
vs revised bars 14/17/6). **No historical promotion or standing
determination would have differed** — ercot-213 was owner-promoted over its
FAIL (stands, stronger), ercot-215's operative session verdict was already
PASS (+5 bar; its rejection was G-C3c, untouched here).

## 1. New objects the lidless count surfaces (named, not chartered)

* **h3068-2024 (May 8, 20:00 CST) is band-top-blind in EVERY registered run
  of every lineage** — model $676.80–$798.20 (keeper $798.20) against actual
  **$110.41**: the hour after the May-8 evening event, where the model holds
  a deep price after reality came off the peak. It has never been counted by
  any G-SPUR reading. Under Option A it enters arm and baseline alike
  (hence 9/12/1) so it flips nothing, but it becomes permanently visible —
  a candidate object for a future lane (it is the same May-8 evening whose
  shed the ercot-223 event-release guard repaired; the price-side residual
  at the following hour remains).
* **h3355-2025 predates ercot-213**: above the top in the ercot-204-era
  keeper too ($630.98 vs actual $134.84) — every recorded "2025: 0" in the
  204/213 lineage was blindness, never a clean zero. (FINDING-214 fn¹
  attributed the overshoot to the 213-arm phantom adder; the re-reading
  shows the hour was already out the top under the prior two-tier form.)
* **The ercot-213-arm 2023 overshoot family is seven hours, not one**:
  h3954 $1,298 / h4051 $903 / h4069 $897 / h4070 $1,310 / h4071 $898 /
  h4117 $885 (June adder-made afternoons, actuals $83–138) + h5822 $583 —
  the FINDING-214 §2 phantom-deep population's actual<$150 members, exactly
  as the precommit prior P2 expected.

## 2. Hygiene defect CONFIRMED (report-only; card §7 step 2 carries the repair)

`ercot221_gates.py::SPUR_BASELINE`'s 2023/2024 baseline hour LISTS
([4283, 4404, …] / [4749, 4750, …]) do **not** match the baseline bundle's
own banded hours on the file's own construction — the true identities are
[5438, 5439, 5443, 5660, 5684, 5731, 5804, 5821, 5822] (2023) and
[336–349 block, 2540, 2829] (2024); 2025 [3355] is correct. Counts agree
(9/11/1), the gate compares counts only, so **no recorded verdict is
affected** — but the lists should be repaired in the same commit that
executes Option A (or independently if the owner declines).

## 3. Precommit priors — all five resolved, each in its declared expected branch

P1 (V3 flips iff ctl-2025 counts h3355 and 2023/24 stay non-increasing):
CONFIRMED, expected branch. P2 (V2 a-fortiori): CONFIRMED (+15). P3 (V4
stays FAIL): CONFIRMED. P4 (keeper stays PASS unless adaptive floors put
>bar hours over the top on actual<$150 hours): CONFIRMED PASS — the
adaptive keepers add ZERO S_top hours in 2023/2025; the only S_top hour is
the universal h3068-2024. P5 (V1 by construction): CONFIRMED.

## 4. Disposition

The card is pushed and AWAITS OWNER SIGN-OFF; the owner was not in-session,
so per dispatch the gate is NOT changed. **The R-A re-pointed queue is now
EMPTY**: item 8 closed effectively-unconditional (ercot-224), the band-top
item is card-drafted pending the owner. Whichever option the owner takes,
the measurement is complete and does not need repeating — the executing
session's checklist is card §7. Door D (2026 SOM anchors, ~mid-2027)
remains the recorded floor for the 2023 depth/count object.

## 5. Governance

Rule 22: years {2023, 2024, 2025} only; committed artifacts only
(data-not-score; the actuals parquet is the standing committed validation
source; no out-of-training year touched). Rule 25: ERCOT only. Rule 1/Q-B
FINAL/R-A: no residual direction weighed anywhere — the revision is
adjudicated on gate-integrity grounds (an escape hatch that inverts the
gate's purpose), and every C3-adjacent number in the card is decomposition
reporting, not a basis. Rule 27: local edits, exact on-disk bytes pushed,
≥300-line pushed files blob-verified; the precommit itself blob-verified
BEFORE any reading. Rule 28: no mechanism tested ⇒ no cell verdict minted;
the §5.1 queue re-stamp is the same-session evidence duty (the ercot-224
pattern). No LP, no solve, no re-bundle, no registration, no new workflows,
no cron, no PR — push-and-stop on the designated branch. DO-NOT-REDO
honoured in full: item 8 not re-screened, the adaptive family untouched,
Door A/item 11/mid-band/regime/ercot-219-aggregate/B-2/M-2 untouched,
Door D not re-entered.

**Session consumed the ercot-225 shorthand. Next shorthand: ercot-226**
(ercot-199 remains unclaimed).
