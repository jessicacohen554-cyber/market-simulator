# FINDING — capx D78-ARM completion: the armed PJM `pjm-t1h` is solved at the declared key and **independently REPRODUCES D75-R-ARM steps 3–4 byte-for-byte**; **Q56 is discharged by that lane's registration**, this lane's duplicate bundle is deleted, and the one band that crossed FAIL → PASS is the one neither lane argues from

**Lane:** capx **D78-ARM completion**. **Branch:** `claude/pjm-retirement-sector-gate-at0cao-lsffr8`,
fast-forwarded onto `origin/main` **`9518fe0b`**. **Date:** 2026-09-07. **Model:** Opus.
**DATA PROFILE:** `pjm`.

**Charter:** finish, do not re-derive. The arming act (`a154222c`, salvaged and corrected by
`fd2a0d18`, PR #5373) is on `main` and was not re-argued, re-probed or re-opened here.
Owner ruling **Q56** reads *ARM, **REGISTRATION REQUIRED***; the registration is part of the
ruling, not a note on it, so arming without registering does not discharge it. This document is
the back half.

**Predecessors:** `PRECOMMIT-capx-d78arm-2026-09-06.md` (every key, STOP and expectation, pushed
before the edit), `FINDING-capx-d78r3-2026-09-06.md` §5 (the serving recommendation),
`FINDING-capx-d78r2-2026-09-06.md` §§3–8 (limbs (b)/(c)/(d), **carried**),
`FINDING-pr5319-d78arm-salvage-2026-09-07.md` (what `main` restaled and what was held).

---

## 0. Result in one paragraph

The armed PJM T1-H solved at **`fb16fda2ddb0a94a`** — the key the PRECOMMIT declared at `8875af59`,
reproduced exactly ~200 commits later — with the HEAD guard holding. **While it was solving, capx
D75-R-ARM steps 3–4 merged to `main` carrying the SAME key**, because at this head the bare `pjm-t1h`
recipe is one recipe carrying both arms. The charter anticipated exactly this and instructed
*"rebase and re-declare rather than assume"*, so this lane does: **D75-R-ARM steps 3–4 landed first
and holds the bare `pjm-t1h`**, its `pjm-t1h-pre-d75rarm` naming is adopted on the merits over this
lane's held `-pre-d78arm`, and **Q56's registration condition is discharged by that registration** —
one solve, one bundle, one row (rule 19 `[R-ONE-MECH]` in its registration form). This lane's own
bundle is a **duplicate and is deleted before merge**, not registered.

**What the collision bought, and it is not nothing:** two lanes solved the same recipe independently,
on two different HEADs, nineteen seconds apart — and the output is **byte-identical**. All five
`evolution_<year>.json`, `score.json` and every `year_*_floor_retentions.json` match to the sha256;
the *only* differing leaves in either bundle are `solve_surface.json`'s recorded `git_sha`
(`10cda1fa` vs `04222503`) and a timestamp. That is an **independent reproduction** of the joint
Q55+Q56 posture and an empirical confirmation that capx D79's solve-surface fingerprint means what it
claims. §4's numbers therefore describe the row `main` now carries, measured twice.

**14 of 14 forecast invariants PASS.** Of **26 scored bands, exactly two flip**, the same quantity
twice: `retire.total_gw` raw and IS-2020, **FAIL → PASS**, 18.058 → **15.292 GW** against 15.062
actual. **That crossing is not an argument for arming and is not cited as one** (rule 14; D78-R3
§5.2 item 2 said so before any of this was solved, and a worse band would not have been an argument
against). Against it, at equal weight: `unit_recall_gt300` **FALLS** 0.650 → 0.550 exactly as
pre-declared, coal exits move **away** from actual, `false_retire` stays FAIL, and the DY2026/27
clearing price moves 358.267 → **213.056 $/MW-day**. Limb (d) still cannot discriminate on recall.
Q56 is discharged; the model is not thereby better.

---

## 1. Reconciliation the charter asked for first: what `d41ac928` did to owed item (1)

**Answer: `d41ac928` did item (1) for the UNARMED tree, and the salvage `fd2a0d18` then completed it
for the ARMED tree. At my HEAD the file is correct and the test is GREEN — 12/12. I edited nothing.**

The WIP handoff (`3b369f26`) recorded `TestQ52ArmingKeys` as red on `main` since `6164231e` and owed
`BARE_PJM_ARMED` `a9c66d8ea25acb9d` → `fb16fda2ddb0a94a` plus `retirement_sector_gate=False` on the
inverse leg. Three separate acts touched it, in this order:

| act | what it did | value it left |
|---|---|---|
| `6164231e` (Q55 / D75-R-ARM) | armed `pjm_vre_accreditation_vintage` and **did not re-pin this file** — the defect | `a9c66d8ea25acb9d` (stale) |
| **`d41ac928`** | repaired the red **for unarmed `main`**, deriving the value rather than carrying PR #5319's: re-pinned `BARE_PJM_ARMED` → `b518f5fe7d02f961`, and — the load-bearing half — **completed the inverse** by adding `pjm_vre_accreditation_vintage=False` beside `capacity_adequacy_requirement_published=False`, restoring `BARE_PJM_PRE_ARM` `15a723ba3b6dc856` instead of re-pinning that constant, which would have discarded the (b′-1) invertibility the test exists to hold. It deliberately left the D78 arm alone and left a note telling the arming lane what to re-measure. | `b518f5fe7d02f961` |
| `fd2a0d18` (salvage) | the arm landed, restaling the constant exactly as `d41ac928`'s note predicted: `BARE_PJM_ARMED` → `fb16fda2ddb0a94a`, `retirement_sector_gate=False` added to the inverse leg | **`fb16fda2ddb0a94a`** ✓ |

So the honest statement is **"partly, and then finished by another commit"** — not "already done" and
not "did something else". Verified at my HEAD, not assumed:
`tests/unit/config/test_d67arm_pjm_requirement.py` → **12 passed**.

---

## 2. The key, realized vs declared — and **which lane's row carries it**

The charter required this lane to name its key, because the bare `pjm-t1h` recipe has **three
vintages** in play and two PJM registration lanes were chartered against different ones. It also gave
the tie-break in advance: *"if D75-R-ARM steps 3-4 has landed before you, rebase and re-declare rather
than assume."* **It landed.** `git log origin/main --grep="D75-R-ARM"` at `1ee2efba` carries
`FINDING-capx-d75rarm-steps34-2026-09-07.md` and the registered bundle
`results/capacity-hindcast/pjm-2021-2025-realized-t1h-d75rarm`.

| vintage | key | status after the re-declaration |
|---|---|---|
| pre-Q55 | `a9c66d8ea25acb9d` | the committed D67-ARM bundle, the graded control — **preserved as `pjm-t1h-pre-d75rarm`** |
| post-Q55, pre-Q56 | `b518f5fe7d02f961` | **no bundle exists at this key**; D76-P3B solved it as its own control and deleted it under rule 29(c) |
| **post-Q56 = the joint Q55+Q56 posture** | **`fb16fda2ddb0a94a`** | **registered on `main` as the bare `pjm-t1h` by D75-R-ARM steps 3–4**, id `pjm-2021-2025-realized-t1h-d75rarm` |

**Realized == declared** on both sides: this lane's runner logged
`run_scenario_iso start: iso=PJM cache_key=fb16fda2ddb0a94a` and finished on it, and D75-R-ARM's
ADDENDUM B declared the same key before its LP ran.

### 2.0 Why this lane adopts `-pre-d75rarm` and drops its own held `-pre-d78arm`

**On the merits, not merely because that lane merged first.** The preserved object is the D67-ARM
bundle, whose key is `a9c66d8ea25acb9d` — which is the posture immediately before **D75-R-ARM**. The
posture immediately before **D78-ARM** is `b518f5fe7d02f961`, and *no bundle at that key exists to
preserve*. Naming an `a9c66d8ea25acb9d` bundle `-pre-d78arm` would therefore label it with a
different posture's name. D75-R-ARM's own `VERDICT_MAP` comment makes that argument and invites this
lane to adopt its id "rather than create a second alias for one object"; the argument is correct, and
a second alias for one object is precisely what rule 19 `[R-ONE-MECH]` refuses in its registration
form. **The held hunk from PR #5319 is therefore superseded, not applied.**

### 2.0b The reproduction — the one thing the collision produced that neither lane could have alone

Both lanes solved the same recipe at the same key, independently, on different HEADs, **nineteen
seconds apart**. Differenced file by file:

| artifact | result |
|---|---|
| `evolution_2021.json` … `evolution_2025.json` | **byte-identical**, sha256 `b23c54a3176d6010` · `a4a77735463552a4` · `2ef88bc80966293b` · `8f774e463a8c6b18` · `cab2aae339d5bca9` |
| `score.json` (incl. `--flip-gate-extras`) | **identical on every leaf** but `flip_gate_extras.utc` (03:00:16Z vs 03:00:35Z) |
| `year_*_floor_retentions.json` | **byte-identical** |
| `solve_surface.json` | **one** differing leaf: `git_sha` `10cda1fa` (theirs) vs `04222503` (mine) |

Two independent solves of one cache key on two different code states produced the same numbers to the
byte. That is a real result: it is an **independent reproduction** of the joint Q55+Q56 posture, and
an empirical confirmation from a second direction that capx D79's solve-surface fingerprint keys what
it claims to key — the two HEADs differ, the fingerprint says PJM's surface does not, and the output
agrees with the fingerprint. It is recorded here because a duplicated effort that agrees is evidence,
and deleting the bundle should not delete the finding.

### 2.1 G-DRIFT increment, written before the solve

The PRECOMMIT declared its keys at `8875af59`; this lane solves 49 merges later. The increment audit —
`docs/handoffs/d78arm/gdrift-increment-8875af59-to-9518fe0b.md`, **committed at `04222503` before
`run_arm.sh` was invoked** — classifies all 40 changed files and reads **ALL HUNKS INERT**: in
substance one new ISO (SPP, lanes SPP-14/-20), one ERCOT price-formation vintaging (ercot-253), and
two default-off `ScenarioConfig` fields dropped from the hash at their declared `False`. G-DRIFT
form 4 is therefore valid and **no control solve is earned**. Stated there against interest: an
unmoved key evidences an unmoved *declared* surface, not that no code path changed — which is why
§1 of that doc audits the uncovered hunks by hand instead of resting on the key.

---

## 3. The STOPs

| # | STOP | reading |
|---|---|---|
| **S1** | key table / no-op sweep departs from §2 | **PASS** — every PJM leg byte-identical at HEAD; no non-PJM or backcast PJM move |
| **S2** | realized key ≠ `fb16fda2ddb0a94a`, or the HEAD guard trips | **PASS** — key exact, guard OK at `04222503` |
| **S3** | any of the 14 forecast invariants non-PASS | **PASS** — **14 PASS / 0 FAIL / 0 WARN**, the D67-ARM / D75-R-ARM bar |
| **S4** | the identity the mechanism asserts | **see §3.1 — reported both ways** |
| **S5** | a re-key outside the declared set, or any edit to `retirements.py` | **PASS** — `retirements.py` untouched; the only solve-path file this lane edits is `register_forecast_run.py`'s `VERDICT_MAP`, which the PRECOMMIT §2.2 declared would land here |

### 3.1 S4 — FIRED on exactly one row, and the row is the seed year

The instrument is `docs/handoffs/d78arm/s4_identity_check.py`, **written and committed
(`def45e01`) while the arm was still solving, before its bundle existed**, so it could not be shaped
to its own result — and it was **not edited afterwards**. It reuses `docs/handoffs/d78/screen_compare.py`'s
`sectors` / `sector_of` readers rather than re-implementing "what sector-1 means".

**Known-answer first** (`s4_control_known_answer.json`): run against the committed D67-ARM control —
the same bundle, no gate — it reads **FIRED on 126 sector-1 rows** (2022: 38 `pipeline_events` + 12
economic exits; 2023: 20 + 3; 2024: 34 + 14). So it demonstrably **detects** what it is asked to
report zero of.

**On the arm** (`s4_arm_measured.json`), the two clauses of S4 read differently and both are reported:

| clause | reading |
|---|---|
| **substantive** — no sector-1 row in `decided` / `entry_capped` / `floor_retained` / `throughput_deferred` / `pipeline_events` / `retirements[reason=economic]` | **ZERO**, in all five years and all six surfaces (against the control's 126). 0 unknown-sector rows. |
| **block presence** — every year carries a `sector_gated` block | **2022–2025 present; 2021 absent → S4 FIRES literally, 1 row** |

**The fired row is the seed year, and the same PRECOMMIT predicts it.** §5.3 **P-B**: *"2021 runs no
screen (no `prior_results`), so its ledger is byte-identical in the two mechanisms' presence or
absence."* No screen ⇒ no gate ⇒ no block. **Confirmed, not asserted:** `evolution_2021.json` is
**byte-identical across the two legs**, sha256
`b23c54a3176d6010ef749423f97b9bd9dc3f63f059a654629027cb2df04c1306` on both sides — **P-B is a HIT**.

**Adjudication, stated rather than performed by editing the instrument:** S4's block-presence clause,
read literally over all five years, over-reaches relative to §5.3 P-B in the *same document*; scoped
to the years that actually run a screen, it PASSES. The literal `FIRED` verdict stays in the
committed JSON exactly as measured. A reader who prefers the literal reading has the number.

**P-A also HIT:** the `sector_gated` block is present in every screen-running year and is drawn from
the 2020-vintage plant table — 2023 partitions **38,619.729 MW / 191 units, `mw_by_sector` `{"1": …}`
only**, coal 17,004.596 · gas_cc 8,435.400 · gas_ct 6,663.533 · gas_st 771.200 · nuclear 5,745.000,
with `unknown_sector_mw` reported separately (8,876.3 in 2023, 10,090.3 in 2025) and **failing open to
the screen** by design (D32 C5/R3).

**P-C:** D78-R2 measured economic exits executed 2024/2025 at **0** under the gate alone; the armed
run (gate **+** Q55) reads **0** in 2024 and 2025 as well. Reported, and it was never a STOP.

---

## 4. §5.2 at full magnitude — the disclosures the charter requires in this document's head

Every row here is **reported and gated on nothing** (rule 14). Control = the committed D67-ARM bundle
`a9c66d8ea25acb9d`; "gate only" is D78-R2's **document** figure (that bundle was never registered —
§6 item 1), and the armed run is **gate + Q55**, so it is not expected to equal it.

**These are the numbers of the row `main` now carries** (`pjm-2021-2025-realized-t1h-d75rarm`,
key `fb16fda2ddb0a94a`) — measured independently by both lanes and byte-identical (§2.0b), so nothing
here is lost by deleting this lane's duplicate bundle.

| quantity | control (D67-ARM) | Q55 only (doc) | gate only (doc) | **armed run** |
|---|---:|---:|---:|---:|
| `retire.total_gw` (actual 15.062) | 18.058 · FAIL | 17.294 · FAIL | 15.937 · PASS | **15.292 · PASS** (err 0.199 → **0.015**) |
| `retirements_is.total_gw` | 18.058 · FAIL | — | — | **15.292 · PASS** |
| `unit_recall_gt300` | 0.650 (13/20) · FAIL | 0.650 | 0.550 (11/20) | **0.550 (11/20) · FAIL** |
| `false_retire` GW · frac | 8.065 · 0.447 · FAIL | 7.596 | 7.166 · 0.450 | **6.825 · 0.446 · FAIL** |
| window `economic` precision | 0.122 | 0.129 | 0.146 | **0.155** |
| DY2026/27 clearing $/MW-day | 358.267 | — | 236.945 | **213.056** |
| DY2026/27 cleared position | 0.998023 | — | 1.009595 | **1.011874** |

1. **`retire.total_gw`'s FAIL → PASS is EXPLICITLY NOT an argument for arming**, and this document
   does not cite it as one. It is a consequence of removing candidates from a control that
   over-retires. D78-R3 §5.2 item 2 wrote that before the arm was solved precisely so it could not
   become an argument after; the PRECOMMIT §5.2 pre-declared the direction (**≤ 17.294**) and the
   measured 15.292 sits inside it. A worse band would not have been an argument against.
2. **`unit_recall_gt300` FALLS** 0.650 → **0.550**, matched 13/20 → 11/20 — exactly the pre-declared
   value. A partition that removes **matched** sector-1 exits must lose recall. Not a criterion; not
   hidden.
3. **The DY2026/27 clearing price moves a long way**, 358.267 → **213.056 $/MW-day**: the arm's extra
   **2,000.777 MW** of census (144,164.350 → 146,165.127 MW against a published requirement of
   144,450.0) carries the cleared position 0.998023 → **1.011874** across the requirement and down
   the steep VRR limb. It differs from D78-R2's documented 236.945 because that leg was the gate
   **without** Q55; the direction and mechanism are the same.
4. **Limb (d) cannot discriminate on recall** in either leg. Measured here: LOYO recall holds on
   **0 of 3** folds (−2023 6/12, −2024 11/19, −2025 11/19, all FAIL), while `tr10a`/`tr10b` PASS on
   all three in both legs and **do** discriminate. Read as **no evidence either way**, never as
   support.
5. **Limbs (b), (c) and (d) were CARRIED from D78-R2, not re-measured** — that was D78-R3's charter,
   and D78-R3 §5.2 item 1 recorded that they rest on an arm bundle committed nowhere. **This
   registration is what closes that gap**: the armed posture now has a committed bundle, a committed
   `score.json`, and a registered sidecar. What it does *not* do is retroactively re-measure those
   limbs on D78-R2's own configuration.
6. **W5″'s PASS came from a corrected DECLARATION, not a new measurement.** D78-R3 re-graded (a) at
   **zero LP**: the per-fuel mover counts are identical in both grades, and what changed is which
   sentence of D57 the gate was built from — its §4 per-delivery-year table rather than its §0/§8.1
   headline. Its supporting structural derivation is **one-sided and silent on `gas_ct` and
   `gas_st`**, the two classes that actually decide DY2022/23 and DY2023/24, and it carries a
   false-positive class ($0 price takers, `nuclear`). It corroborates the declaration; it does not
   replace it.

**Also moved, and reported because it is the row that got worse:** coal exits fall 6.797 → **5.575 GW**
against 10.299 actual, so `err_frac` moves −0.340 → **−0.459** — *further* from the actual. `gas_cc`
0.903 → 0.130 (err 1.081 → −0.700), `gas_st` 10.297 → 9.526 (err 2.811 → 2.526), `gas_ct` 0.000 and
`oil` 0.051 unchanged. **Every additions figure is byte-identical** between the two legs (wind 3.000,
solar 9.762, gas_cc 8.118, gas_ct 0.000, storage 0.000 GW), and all 20 additions bands are unmoved —
so all band movement in this run is inside the retirement screen, which is where the mechanism lives.

---

## 5. The board — **registered by D75-R-ARM steps 3–4, not by this lane**

Q56 reads *ARM, **REGISTRATION REQUIRED***, and the requirement is met: the armed posture
`fb16fda2ddb0a94a` **is** registered on the forecast namespace, as the bare **`pjm-t1h`**, under
`pjm-2021-2025-realized-t1h-d75rarm`, with the D67-ARM record preserved at `pjm-t1h-pre-d75rarm`.
That lane's own `VERDICT_MAP` comment states the reasoning this lane accepts: *"registering it once
discharges both lanes and no second `pjm-t1h` is solved."* **Q56 is discharged.**

**What this lane consequently DELETES rather than registers.** Its own bundle, sidecar and hindcast
report are a duplicate of a registered object at the same key:

- `results/capacity-hindcast/pjm-2021-2025-realized-t1h-d78arm/` (14 slim files)
- `frontend/data/hindcast/pjm-2021-2025-realized-t1h-d78arm.json`
- `docs/hindcast-reports/pjm-2021-2025-realized-t1h-d78arm-2026-09-07.md`

This is required, not tidying: `check_registry_payload_parity.py`'s bundle-retention sweep makes an
**unregistered bundle dir a gate RED**, and rule 29(c)'s "delete before merge" says git history is the
record for the bytes. Every number this lane will ever cite is in *this document*. Re-run after the
deletion: **registry/payload parity OK (16 runs checked, 49 bundle dirs swept, 0 tolerated)**.

**The held `VERDICT_MAP` re-key is SUPERSEDED, not applied** (§2.0). `main`'s rows stand unchanged;
this branch contributes no `VERDICT_MAP` edit at all after the merge resolution.

## 6. What this lane does NOT claim

1. **It does not claim the model got better.** Two bands crossed, both the same quantity, and this
   document refuses to argue from them (§4 item 1). Recall got *worse*, coal exits got *worse*,
   `false_retire` is still FAIL, and `unit_recall_gt300`'s band did not move.
2. **It does not re-measure limbs (b), (c) or (d)**, nor re-open Q56, nor re-argue the arm.
3. **It adjudicates nothing about D57 §4's zero-E&AS operand** — the CT / ST / oil E&AS operand
   remains zero in the hindcast prices and is the **named successor** for the retirement bands and
   for the clearing-price level.
4. **It does not re-score the FF-2D rubric verdict at `pjm-t1h`.** `rescore_forecast_verdicts.py`
   scans `results/hindcast/` only, and this bundle lives in `results/capacity-hindcast/` — the
   retention class D67-ARM established — so the key reads "no tracked artifact" there exactly as it
   did for D67-ARM. Changing that scan is outside S5's declared set.
5. **The board snapshot stays HELD** (the D65-B-R lock), per the lane's charter. Nothing in
   `program-status.json` was touched.
6. **It does not claim the registration as its own.** D75-R-ARM steps 3–4 registered the armed
   posture; this lane confirms it, re-declares against it, and deletes its duplicate. What this lane
   contributes to the record is the reconciliation (§1), the pre-solve G-DRIFT increment audit
   (§2.1), the S4 identity grading with its known-answer (§3.1), the independent reproduction
   (§2.0b), and this document.
7. **It takes no position on which lane *should* have been dispatched.** Two lanes were chartered
   against the same object and both solved it; that is a coordination fact for the director's ledger,
   not a finding about the model. It is recorded in §7.1 item 3 rather than argued here.

---

## 7. Governance attestation

**Rule 12 `[R-PARALLEL]`** — one invocation, PJM solo, years sequential. **Rule 14 `[R-ACCURATE]` /
rule 1 `[R-STRUCT]`** — the decision was the owner's on structural limbs; no band was used to select
anything, and the one favourable crossing is explicitly disclaimed. **Rule 19 `[R-ONE-MECH]`** — one
seam (`exit_exempt_unit_ids`); no unit's exit decided twice. **Rules 21/24 `[R-DOF]`/`[R-REGISTRY]`** —
zero free parameters; a partition on one published per-plant boolean, and the resolved posture is
written into the committed `run_config.json` `scenario_config`. **Rule 25 `[R-ISO-SCOPE]`** — PJM only;
25 of 173 committed configs move, all PJM/forecast, every other ISO and every backcast key
byte-identical. **Rule 27 `[R-PUSH]`** — every pushed file ≥300 lines blob-verified against the remote:
**10 of 10 byte-identical** (`register_forecast_run.py` 1,334 lines, the five `evolution_*.json`, the
sidecar, `score.json`, `run_config.json`, `run_config.yaml`). No `push_files` fallback; exact on-disk
bytes over `git push`. **Rule 28 `[R-MECH-MATRIX]`** — PJM's shard only; the cell was already `K` and
is **not duplicated**, only its "still owed" clause discharged. **Rule 29 `[R-SCREEN]`** — 29(a) does
not apply (a ruled arming, nothing to select); 29(b) form 4 validated by the G-DRIFT increment audit
committed before the solve; no screen or control bundle exists, so 29(c) has no object.

### 7.1 Three things recorded against interest

1. **I moved HEAD while the HEAD-guarded solve was running.** Two docs-only commits (`04222503`,
   `def45e01`) landed after `run_arm.sh` captured its baseline. I noticed before the guard evaluated,
   **restored HEAD to the baseline `04222503`** for the remainder of the solve, and re-applied the two
   commits after it exited — so the guard's report (`HEAD guard OK (04222503…)`) is **true of the code
   state the LP actually ran on**, and no commit in that window touched a solve-path file. Disclosed
   because the guard cannot see the difference between a docs commit and a code one, and a reader
   should not have to take my word for which it was.
2. **`run_config.yaml` reads `retirement_sector_gate: false`** while `run_config.json`'s
   `scenario_config` reads `True`. This is the **pre-** vs **post-**`apply_iso_scenario_defaults` dump
   and is a pre-existing convention, not a defect of this run: the merged D67-ARM record shows the
   identical pattern (`capacity_adequacy_requirement_published_by_iso: null` in its yaml, `{"PJM":
   true}` in its json). Flagged because the yaml alone would mislead a reader into thinking the arm
   was off; not changed, because that is outside S5's declared set.
3. **I spent an LP that turned out to be a duplicate.** D75-R-ARM steps 3–4 was solving the identical
   recipe at the identical key in the same minutes, and neither lane knew. I did not discover it
   until `main` moved under the PR and the merge conflicted. Nothing hid it — the charter named the
   collision risk explicitly and gave the tie-break, and I checked `git log --grep="D75-R-ARM"` at
   session start, when steps 3–4 had **not** yet landed. It is recorded because the honest reading is
   that the cost was real (one full 2021–2025 PJM window) and the mitigation is a coordination one,
   not a technical one. What the spend bought back is §2.0b's reproduction.

### 7.2 Environment notes

`data/clean` was rebuilt from empty (`scripts/regenerate_clean.py`), 60 datatypes. **One datatype
fails and it is not PJM's:** `load-forecast` raises `basis(es) not in vocab: ['coincident']` on
**SPP**, the ISO registered on 2026-09-06; PJM's `load-forecast.parquet` (1,533 rows, 2026–2046,
edition "2026 LTLF") writes cleanly, as do the other five ISOs'. Reported for the SPP lane; untouched
here. `emissions-unit-annual` was OOM-killed once in a batch and completed on a solo re-run.

---

## 8. Matrix (rule 28) and what is routed on

PJM's `retirement_sector_gate` cell is **already `fc: "K"`** (set by the salvage) and is **verified,
not duplicated**. Its evidence string's clause *"STILL OWED by the arming lane and NOT claimed here:
the armed pjm-t1h re-solve, its scoring and its registration"* is now **discharged** and replaced with
this document's citation and the registered key.

**Routed on, not absorbed:**
- the **CT / ST / oil E&AS operand is zero** in the hindcast prices (D57 §4) — the named successor for
  both the retirement bands and the clearing-price level;
- **`false_retire` remains FAIL** (6.825 GW, 0.446 of model);
- **coal exits move away from actual** under the partition (err −0.340 → −0.459) — the gate removes
  *false* exits without finding missing *true* ones, the same shape D75-R §5.4 recorded;
- **the Q55-only posture `b518f5fe7d02f961` is registered nowhere and no bundle exists at that key**
  (D76-P3B deleted its control under rule 29(c)), so Q55's isolated attribution stays document-only in
  `FINDING-capx-d75r` §5.2 — the registered row is the JOINT Q55+Q56 posture and **no number in it may
  be attributed to either arm alone**;
- **two lanes were chartered against one object and both solved it** — a coordination item for the
  director's ledger, not a model finding (§7.1 item 3).

---

## 9. Test posture, measured against a clean-`main` baseline rather than asserted

`tests/unit/config` **828 passed / 24 skipped / 0 failed**, including
`test_d67arm_pjm_requirement.py` **12/12** (owed item 1, §1).

`tests/unit/model/test_capacity.py` + `tests/scoring` read **13 failed / 1,845 passed** on this
branch. **Every one of the 13 is PRE-EXISTING**, established by re-running the identical selection on
a detached clean `origin/main` `9518fe0b`: **the same 13 names, and 1,841 passed** — so this branch
*adds* four passing tests and removes none. The three that could plausibly have been mine, checked by
their own assertion text:

| failure | why it is not this lane's |
|---|---|
| `test_forecast_parity::test_all_six_keepers_resolve` / `::test_check_exits_zero_on_the_current_keepers` | `MISO: ['miso_seam_neighbour_anchored_ladder', 'miso_seam_neighbour_hourly_ladder', 'miso_seam_neighbour_hourly_spp'] armed in the keeper with no … registry declaration` — the miso-233 / SPP-14 seam fields, MISO's keeper |
| `test_registration_marker_gate::…::test_all_committed_out_of_window_sidecars_pass` | `every registered holdout run must belong to a 'complete' ISO … Extra items: 'NYISO'` — the nyiso-193 marker withdrawal against a committed NYISO holdout sidecar. This lane's run is PJM 2021–2025 and registers **no** out-of-window year; the registration marker gate passed |
| `test_ff_readiness_battery::test_build_registration_scorecard_no_iso_gate_open` | expects NYISO's marker `withdrawn`, reads `complete` — the same NYISO marker lane |

The remainder (`TestGetRPSTarget::test_unregistered_iso_is_none`, the four
`test_collate_scenario_campaign*` and three `test_scenario_campaign_configs`) belong to the SPP
registration and SCN campaign lanes. **None is repaired here** — they are other lanes' objects, and
S5 scopes this PR.

`ruff check` and `ruff format --check` clean on both touched Python files.
`check_mechanism_matrix.py --base origin/main` exits **0**; its anchor warnings are all emitted with
the `(pre-existing, not this PR)` marker.
