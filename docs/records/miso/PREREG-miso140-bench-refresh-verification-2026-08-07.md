# PREREG — miso-140: the MISO bench `*_lw` refresh — verify it, re-verify every C3a on it, and say whether the keeper's determination moves

**Session:** miso-140, 2026-08-07, branch `claude/miso-140-calibration-rfb4o0`.
**Charter:** §5.4 **QUEUE ITEM 1** (owner-selected 2026-08-06) — *refresh the MISO
bench, then re-verify every MISO C3a from committed artifacts, no re-solve, and
state explicitly whether the keeper's determination changes.*

**THIS IS BENCH HYGIENE. IT IS NOT A LEVER.** It cannot close a −14 % gap and
nothing in this session may be reported as progress against the 2024/2025
mean-LMP level miss. **Owner directive honoured:** no C7 lane, no C7 ledger.

**Pushed BEFORE any adjudicating statistic.** Everything in §0 below was read
from committed artifacts before this file was written and is disclosed here in
full; every number in §2 is a *prediction* made before the measurement that
tests it. No `calibration_verdict.py` run, no recomputation of `rt_lw` from the
parquet, and no read of the cached scorecard in `frontend/data/backcast/status/MISO.js`
has been performed at the time of this commit.

---

## 0. §0, re-verified from committed artifacts — AND IT HAS ALREADY MOVED

Re-verification found a fact the charter could not have carried, because it
landed after the charter was written.

**THE REFRESH IS ALREADY COMMITTED AT HEAD.** Session **pjm-160** performed a
cross-ISO `*_lw` refresh on **2026-08-07**, MISO included:

| commit | date (UTC) | what |
|---|---|---|
| `908f27c9` | 2026-08-06 16:30 | `curate_demand_profile` gains `PRE_WINDOW_YEARS`/`curate_pre_window` — claims *"the 2021–2025 legacy pass is untouched and byte-identical"* |
| `1d63141c` | 2026-08-07 06:14:50 | B5 reference refresh — rewrites `data/raw/_validation-source/actual_lmp.json` |
| `056eb164` | 2026-08-07 06:14:59 | **B5 bench lw refresh — MISO**: `frontend/data/backcast/bench/MISO/{2023,2024,2025}.json.gz` + `status/MISO.js` |

Both are on `origin/main` (`638cd378`) and in this branch's history. The
committed MISO bench `avgLMP` scalars moved exactly as miso-137 §5 predicted:

| year | field | before `056eb164` | at HEAD | Δ | miso-137 §5 predicted Δ |
|---|---|---:|---:|---:|---:|
| 2023 | `rt_lw` | 32.87 | **32.85** | −0.02 | −$0.023 |
| 2024 | `rt_lw` | 32.27 | **32.30** | +0.03 | +$0.031 |
| 2025 | `rt_lw` | 45.39 | **45.46** | +0.07 | +$0.066 |
| 2025 | `da_lw` | 46.29 | **46.35** | +0.06 | +$0.064 |
| 2023 / 2024 | `da_lw` | 34.24 / 33.13 | **34.23 / 33.14** | −0.01 / +0.01 | — |

Only `da_lw`, `rt_lw`, `da_lw_mon`, `rt_lw_mon` changed in each file; the legacy
equal-hour `rt`/`da` fields (31.79 / 30.80 / 42.85) and every other bench block
(`plants`, `e930`, `classFull`, `ctOnly`, `storage`, `co2`) are byte-identical —
consistent with miso-137's diagnosis that **this was never a price-series
defect**.

**What that does to this session's charter.** The *refresh* half is discharged
by another session's ride-along. **The verification half is not**, and it is the
whole reason miso-138 §8 declined this as a ride-along in the first place: the
`*_lw` scalars are the **C3a comparator for every MISO run**. A commit with the
right title is not a verified comparator. So this session's chartered question
becomes the one that is actually still open:

> **Is the committed refresh correct, complete, and consistent with the model
> side it is compared against — and what does the keeper's scorecard read on it?**

**Keeper** (unchanged, and this session will not move it):
`2026-08-05-miso-132b-cc-committed`, bundle `results/calibration/miso132_ccmin_B`.

**Determination at HEAD, as carried by miso-139 §3** (itself re-verified from
`calibration_verdict.py --run-id` against the *pre-refresh* bench): **NOT-YET**,
8 criteria under rubric v3.1, **sole FAIL C3a `price_mean`**, **sole ledgered
caveat C3c** (budget 1 of 1). C7 is **not** a scored criterion under v3.1.
C3a then read **−0.5 / −5.9 / −14.0 %** (DA companions −4.4 / −8.3 / −15.6).
`PRICE_MEAN_TOL = 0.10` (`calibration_verdict.py:376`).

**Rule 22:** MISO is in neither the `complete` nor the `final` block of
`calibration-complete.json`. **2023–2025 only.** No out-of-training year will be
read, solved, scored or registered.

---

## 1. What a refresh MAY and MAY NOT change — fixed in advance

**MAY change** — and if it does, that is the correction working:
* the **actual-side** comparator scalars `rt_lw`/`da_lw`/`rt_lw_mon`/`da_lw_mon`
  for MISO 2023–2025;
* the derived **C3a percentage** (both bases) and, through the monthly vectors,
  **C3b**;
* committed dashboard/status text that quotes those numbers.

**MAY NOT change**, and any of these moving is a stop-the-line event:
* **any model output.** No LP is solved, no bundle is regenerated, no sidecar is
  rewritten. The model price scalar must be **identical** before and after.
* the legacy equal-hour `rt`/`da` fields, or any non-price bench block;
* any `ScenarioConfig` field, mechanism, offer curve or parameter — none is
  touched;
* the **keeper designation**;
* any other ISO's artifacts (rule 25);
* any criterion other than C3a/C3b — C1, C2, C4, C6, C8 and every legitimacy
  diagnostic must be bit-identical, because none of them reads `*_lw`.

**STOP RULE.** If the keeper's **determination** moves (NOT-YET → anything), or
the fail set gains or loses a criterion, I **stop and escalate** rather than
promoting, re-keying or repairing anything. A comparator correction that flips a
verdict is an owner decision, not a hygiene commit.

---

## 2. Gates, with the prediction made before the measurement

### G-1 — is the committed refresh CORRECT? *(gating)*

Independently recompute `rt_lw`, `da_lw` and both 12-month vectors for MISO
2023/2024/2025 from the committed `actual_lmp_hourly_MISO.parquet` × the
model's own `eia_loader.load_demand`, through the deriver's own
`_lw_fields`/`_lw_stats` path at HEAD.

**PASS** iff every recomputed scalar reproduces the committed value to the
deriver's own 2-dp rounding (|Δ| ≤ $0.005 on the rounded comparison) in **all**
3 years × 2 bases, and all 72 monthly entries match.

> **Prediction (conf. 0.90):** PASS 3/3 × 2/2. Specifically 2025 `rt_lw` raw
> **45.4555 → 45.46**, 2025 `da_lw` raw ≈ 46.35, 2023 `rt_lw` 32.85,
> 2024 `rt_lw` 32.30. *Two-sided:* if pjm-160 refreshed the **reference**
> (`actual_lmp.json`) but propagated a **stale or partially-rounded** copy into
> the gz bench parts, or refreshed only the annual scalars and not the monthly
> vectors, G-1 fails on the monthlies while passing on the annuals — the failure
> mode I consider most likely if it fails at all (conf. 0.07 of the 0.10).

### G-2 — is the refresh CONSISTENT with the model side? *(gating — the real question)*

The diagnosed defect was **a vintage mismatch**: the scorer compared a model
dispatched on today's demand against an actual weighted on a stale one.
Refreshing the actual side only closes that if the model side is on **today's**
vintage too. Measure it: compare the keeper's committed `hourly/system_<year>.parquet`
demand against `load_demand('MISO', y, cfg)` at HEAD.

**PASS** iff annual energy agrees to ≤ 0.01 % and the hourly max |Δ| is within
float noise, in all three years.

> **Prediction (conf. 0.75):** PASS — `908f27c9` asserts the 2021–2025 pass is
> byte-identical, and the keeper solved 2026-08-05, after the last demand-input
> change I can find. *Two-sided, and this is the branch I actually care about:*
> if it FAILS, the bench refresh has closed only half the mismatch, the keeper's
> own model scalar is itself on a stale vintage, and **the honest answer is that
> queue item 1 is not dischargeable without a re-solve** — which is out of this
> session's scope. In that branch I report the measured mismatch and **escalate**;
> I do not paper over it, and I do not re-solve.

### G-3 — is the refresh COMPLETE? *(gating)*

Enumerate every committed **MISO comparator** artifact whose value resolves
through `eia_loader.load_demand`, and confirm the refresh covered all of them.
Candidate set from a source sweep: `derive_actual_lmp.py` (→ `actual_lmp.json`
→ bench `avgLMP`), `derive_actual_tail.py` (→ `tail/actual_tail.json`, C3c),
`build_calibration_reference.py`, `derive_import_tranches.py`,
`curate_zonal_shares.py`, `curate_demand_profile.py`.

**PASS** iff the set of demand-weighted **comparators** is exactly
{`actual_lmp.json` `*_lw` → bench `avgLMP`} — i.e. every other hit is an *input*
to the model, not a *comparator* the model is scored against.

> **Prediction (conf. 0.80):** PASS, singleton. C3c's tail is an unweighted
> hourly **count**, so it should carry no demand vintage at all. *Two-sided:* if
> a second demand-weighted comparator exists and was not refreshed, the lane is
> not discharged and I say so rather than declaring victory on the price scalar.

### G-4 — the adjudication: re-verify EVERY C3a on the refreshed bench

`scripts/calibration_verdict.py --run-id 2026-08-05-miso-132b-cc-committed --json`
at HEAD. **Committed artifacts only. NO RE-SOLVE.** Report the signed C3a per
year on **each basis separately** — never blended (miso-133 ONE-BASIS bar).

> **Predictions (conf. 0.85), from the model scalars miso-137 §5 verified to the
> penny (32.7156 / 30.3676 / 39.0472) divided by the refreshed comparators:**
>
> | year | RT C3a (predicted) | was | Δ pp | DA C3a (predicted) | was | Δ pp |
> |---|---:|---:|---:|---:|---:|---:|
> | 2023 | **−0.4 %** | −0.5 | **+0.1** | **−4.4 %** | −4.4 | 0.0 |
> | 2024 | **−6.0 %** | −5.9 | **−0.1** | **−8.4 %** | −8.3 | **−0.1** |
> | 2025 | **−14.1 %** | −14.0 | **−0.1** | **−15.8 %** | −15.6 | **−0.2** |
>
> **Determination: NOT-YET, unchanged.** Fail set unchanged = {C3a `price_mean`},
> failing on 2025 only (2023 and 2024 stay inside ±10 %). Ledger unchanged at
> C3c, 1 of 1. Every non-price criterion identical.
>
> *Two-sided:* the prediction that could break is **C3b** — the monthly vectors
> moved too, and C3b is an NRMSE against `rt_lw_mon`. I predict no C3b status
> flip (conf. 0.80) but I do **not** predict its value is unchanged, and if C3b
> flips, §1's stop rule binds.

### G-5 — drift *(reporting, not gating)*

Does the committed dashboard text — `status/MISO.js`, the keeper shard
`keepers/MISO.json`, the run report — still state the truth against the
re-verified scorecard? Any stale C3a figure or stale caveat count found is
reported; repair is confined to text that is *false at HEAD* and never extends
to re-writing history in a promotion note.

> **Prediction (conf. 0.50):** at least one committed artifact still quotes a
> pre-v3.1 caveat count ({C3a, C3c}, "2/3") that miso-139 §3 already showed is
> inadmissible. I expect to find drift and to report it; whether it is mine to
> repair depends on whether it is a live claim or a historical note.

---

## 3. THE LOOK-ALIKE TRAP, named in advance with its counter-measurement

**TRAP 1 — "the comparator moved in our favour."** 2023's C3a is predicted to
*improve* from −0.5 % to −0.4 %. **A comparator that moves in the model's favour
is not an improvement in the model.** Nothing about the model changed; only the
number it is measured against did.

*Pre-committed counter-measurement:* I will report the **model scalar** for each
year alongside each C3a and demonstrate it is **unchanged** across the refresh
(it is read from the keeper's committed sidecars, which pjm-160 did not touch —
verifiable by `git log` on the bundle). Any C3a movement is therefore **100 %
comparator-side**. I will report all three years signed, on both bases,
**never a net or averaged "improvement"**, and the session's headline will state
in terms that the gap did not close.

**TRAP 2 — accepting pjm-160's own attestation as the verification.** Its commit
message asserts *"Keeper re-scored: no determination flip, no C3a criterion
flip."* That claim is **the hypothesis under test, not evidence for it**.
*Counter-measurement:* G-1 recomputes the scalars independently from the parquet,
and G-4 re-runs the scorer at HEAD; neither reads pjm-160's assertion as input.
I have deliberately not opened the cached scorecard in `status/MISO.js` before
this file is pushed.

**TRAP 3 — declaring the lane discharged because a correctly-titled commit
exists.** *Counter-measurement:* G-2 (vintage consistency on the **model** side)
and G-3 (scope completeness) are the two ways a titled refresh can still leave
the defect open, and both are gating.

**TRAP 4 — scope creep into a lever.** The measurements here touch the number the
−14 % gap is measured against. It would be easy to slide from "the comparator is
now right" into "and here is what would close it".
*Counter-measurement:* no mechanism, no `ScenarioConfig` field, no arm, no solve
is in scope, and **no C3a claim of progress may be attached to anything measured
here** (rules 1/19/21/24). Queue item 2 (the flat `SUMMER_CLASS_DERATE` vs the
net-summer `pmax` basis) is explicitly **NOT** folded in — one question per
session.

---

## 4. Prior, stated against interest

I expect the boring outcome: the refresh is right, the model side matches, the
scope is a singleton, C3a reads −0.4 / −6.0 / −14.1, and the determination does
not move. **P(all four gating gates pass and determination unchanged) = 0.65.**
The single most likely way I am wrong is **G-2** — that the model side is *also*
on a stale demand vintage, in which case the correct output of this session is an
**escalation**, not a discharge, and I will say so plainly rather than reporting a
half-fix as done.

I also record now, before measuring, that **nothing this session can produce is
progress against the miso-137 object.** The largest possible C3a movement here is
**0.2 pp** against a **14 pp** gap.

---

## 5. Duties

**Rule 15** — if no LP is solved there is no run to register (the miso-131…139
precedent). No solve is planned. **Rule 28(b)** — no mechanism is tested, so no
cell verdict is minted; a §5.4 queue stamp is written this session either way.
**Rule 22** — 2023–2025 only. **Rules 13/19/21/24/25** — no measured outcome fed
back, one question, nothing sized to a residual, no tuning channel, no other
ISO's artifact touched. **Rule 27** — any pushed file ≥300 lines is blob-verified
after push.
