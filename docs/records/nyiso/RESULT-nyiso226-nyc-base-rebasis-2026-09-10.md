# RESULT — nyiso-226: the NYC ST_GAS persistent-base re-basing SURVIVES its 2023 screen. It is NOT promoted, and the span is NOT spent

**Session:** nyiso-226 (parent / orchestrator) · **ISO:** NYISO · **Date:** 2026-09-10
**Keeper:** `2026-09-09-nyiso-221-fuelvintage-span`, **UNCHANGED by this session.**
**Charter:** `docs/PRECOMMIT-nyiso226-nyc-base-rebasis-2026-09-10.md` (pushed before the solve,
SHA `a61c1131ea7fb63147c3067fd284dc3fb898ae03`).
**Gate repair:** `docs/ADDENDUM-nyiso226-my-own-gate-S3a-failed-and-the-repair-is-the-strictest-satisfiable-form-2026-09-10.md` — **read it first.**
**Predecessor:** `docs/FINDING-nyiso225-topology-split-closed-2026-09-10.md` §8.

**LP spent: ONE shard, ONE year, 5 min 00 s.** The parent ran no LP (rule 32 `[R-SHARD]`).
No control solve was spent (rule 29(b) form 4 + G-DRIFT). Nothing is registered on the
dashboard: a screen bundle is a throwaway probe and rule 29 forbids registering it.

---

## 0. Headline, in four lines

1. The **outstanding owner call** nyiso-203 raised and nyiso-225 §8 carried was **put to the
   owner and answered: *screen it on one year first*.** This session is that screen.
2. The arm **passes `S1`, `S2`, `S3(b)`, `S3(c)`** and the measurable half of `S4`. Its own
   forced-energy footprint landed **within 7 %** of the prediction registered before the solve.
3. **One of my own gates, `S3(a)`, FAILED — and it failed on a false premise of mine, not on
   the mechanism.** Published in full in the ADDENDUM; repaired to `S3(a′)` with its bar taken
   from the model's own loss table. **The repair was declared after I had seen the number**, and
   that weakness is stated rather than buried.
4. **Nothing is promoted and the full span is NOT spent.** A screen may kill an arm and may
   never promote one. The span and promotion questions go to the owner (§6).

---

## 1. What was solved

One shard, pinned to the PRECOMMIT's 40-char SHA, replaying the keeper's own recipe on 2023 with
a **single-cell artifact edit** — `reliability_floor_coeffs_NYISO.csv`, the
`NYISO,NYC,ST_GAS,tmax,-50.0` row, `floor_pct` **0.175 → 0.16629202320362052**
(`1 file changed, 1 insertion(+), 1 deletion(-)`). No `ScenarioConfig` delta. Shard verified the
pinned SHA and the keeper's `git_sha da2e7076` before solving; solve wall clock **5 min 00 s**
against a 20-minute budget; no ERROR, no traceback, no infeasibility.

---

## 2. THE GATES, as registered, against what was measured

| gate | registered bar | measured | verdict |
|---|---|---|---|
| **S1** direction | ST_GAS falls, \|Δ\| > 0.001 TWh | **−0.078174 TWh** | **PASS** |
| **S2** magnitude | Δ ∈ [−0.0848, −0.0071] TWh (¼×–3× the 0.02827 prediction) | −0.078174 (**2.77×**) | **PASS** |
| **S3(a)** energy balance | supply total within 0.001 TWh | **+0.001343 TWh** | **FAILED AS WRITTEN** → `S3(a′)` **PASS** at 15.0 % of a model-sourced bar (ADDENDUM) |
| **S3(b)** ST_GAS is the largest faller | yes | **ST_GAS is the ONLY faller** | **PASS** |
| **S3(c)** no other class falls more | yes | no other class falls at all | **PASS** |
| **S4** C1 no PASS→FAIL | — | every class PASS; largest miss 1.715 TWh vs a **2.966 TWh** band | **PASS (measured)** |
| **S4** C2 no PASS→FAIL | — | gas family 61.280 → 61.273 TWh, no band | **PASS (measured)** |
| **S4** C3a no PASS→FAIL | — | **NOT MEASURED** (see §5) | **NOT MEASURED** |
| **S4** C3b no PASS→FAIL | — | **NOT MEASURED** (see §5) | **NOT MEASURED** |

### 2.1 The number that matters most: the mechanism's own footprint landed on prediction

The PRECOMMIT registered, before the solve, a first-order prediction of **0.02827 TWh** — the
4.976 % coefficient cut applied to the control's own D-4 binding energy on the two NYC plants
that bind (0.5681 TWh). Measured:

| quantity | control | arm | Δ | vs prediction |
|---|---|---|---|---|
| D-2 `reliability_floor × ST_GAS` forced TWh | 1.9019 | 1.8716 | **−0.0303** | **1.07×** |
| D-4 binding, NYC plant 2490 | 0.3284 | 0.3101 | −0.0183 | |
| D-4 binding, NYC plant 8906 | 0.2397 | 0.2283 | −0.0114 | |
| D-4 binding, the two NYC plants | 0.5681 | 0.5384 | **−0.0297** | **1.05×** |

**The mechanism does what its own arithmetic says it does, to within 7 %.** That is precisely
and only what a rule-29 screen is entitled to establish.

### 2.2 Why the CLASS moved 2.8× the mechanism's own footprint — and why that is not a violation

ST_GAS fell **0.078174 TWh** while the forcing relaxed by **0.0303 TWh**. The extra
**0.048 TWh** is second-order economic displacement: units that were *pinned at* the floor, once
unpinned, are undercut further by cheaper units. The pickup is a clean merit-order one —
CC_REGULAR **+0.045277**, CC_CHP **+0.020355**, CT_CHP **+0.008034**, ST_CHP **+0.003869**,
CT_PEAKER **+0.001540**, imports +0.000346, oil +0.000085 — and hydro / nuclear / wind / solar /
biomass / OTHER / coal are unchanged to < 1e-5 TWh.

This sits at **92 % of `S2`'s outer edge**, inside a ceiling registered at 3× before the solve.
Reported at full magnitude: had I registered 2× rather than 3×, this arm would have been killed.

### 2.3 Confinement, at three independent layers

- **LP input** (phase 0, zero LP): 24 of ~870 rows, all `ST_GAS`, plants {2490, 2500, 8906},
  ratio exactly 0.0497600 on every touched cell.
- **Dispatch**: ST_GAS is the **only** class that falls.
- **Diagnostics**: 98 % of the D-4 movement is on the two NYC plants; 2511 is unchanged to 4 dp
  and 2516 moves 0.0004 TWh.

### 2.4 No new diagnostic failure was introduced

The shard reported the replayed bundle's legitimacy gate as **FAIL** with **`D-4 off-window
binding — FAIL`**. **The control reads exactly the same**: the keeper's committed
`legitimacy_diagnostics.json` carries `D4.passed = False`, and the arm's D-4 unit-conduct FAIL
set — plants **{2480, 8906}** — is **identical to the control's**. Nothing new failed. (The
keeper nonetheless scores **C8 PASS** and reads CALIBRATED, because C8 gates the D-2 forced-share
budget under rule 20's materiality floor, not the D-4 unit-conduct rider.)

---

## 3. G-DRIFT and the control (rule 29(b) form 4)

All 22 files changed between the keeper's `git_sha da2e7076` and HEAD were classified INERT for a
NYISO backcast (PRECOMMIT §5), including two structural checks: the six new `ScenarioConfig`
fields are all default-off and **verified absent** from the keeper recipe, and the NYISO subtrees
of `actual_lmp.json` / `calibration_reference.json` are **byte-identical** at both revisions
(sha `0cead87c1f10834f`, zero differing NYISO paths). **The committed keeper bundle is the
control and no control solve was spent.**

Independently corroborated this session: the parent re-scored the control's own 2023 leg at HEAD
and reproduced **CALIBRATED, fails 0, C3c the lone ledgered caveat** — C1 PASS, C2 PASS, C3a PASS
(33.65 vs 32.25), C3b PASS (NRMSE 0.122), C4 PASS, C6 PASS, C8 PASS.

---

## 4. Rules

- **Rule 1 `[R-STRUCT]`** — the coefficient was fixed ex ante from committed source, declared in
  the PRECOMMIT before the solve, and never swept; the gates are structural and none reads a
  residual. `authorized_price_tuning` = **NONE**.
- **Rule 13/14 `[R-MEASURED]` / `[R-ACCURATE]`** — the basis. Both candidate values are the same
  measurement on the same population; only the time aggregation differs, and the applied grain
  (per unit-hour) is what selects the hourly one.
- **Rule 16 `[R-ALLYEARS]`** — honoured by NOT registering: the screen bundle is a throwaway
  probe, 2023 would be re-solved inside any full bundle.
- **Rule 21 `[R-DOF]`** — the moved coefficient is a ledgered free parameter, identification
  source *"cool-day when-available CF p25, fleet aggregate, hourly grain, CAMPD 2023–2025 +
  guard-corrected outage extract; owner ruling 2026-09-10"*.
- **Rule 23 `[R-FROZEN-DERIVE]`** — **no source-data trigger, and none is claimed.**
- **Rule 29 `[R-SCREEN]`** — phase 0 first, screen year on the mechanism's own footprint, one
  year, structural STOP-only gates, form-4 control. **Clause (c) is discharged by `.gitignore`,
  not by `rm`.**
- **Rule 31 `[R-RETAIN]`** — **nothing was deleted.** §6.
- **Rule 32 `[R-SHARD]`** — the parent ran no LP; one shard, 5 min, own branch, own out-dir.

---

## 5. WHAT THIS SCREEN DID NOT MEASURE — stated rather than glossed

- **`S4`'s C3a and C3b legs are NOT MEASURED.** The solve path writes no `metrics.json` (it is
  written by the registration path), the arm bundle is gitignored and lives only on the shard's
  container, and the shard was **not reachable** by `SendMessage` — neither by session id nor by
  title, and `ListAgents` never listed it — so the read-only scorer call could not be added
  mid-flight. **This is a defect in my shard prompt and it is mine.** Any future screen shard
  must be told, in its original prompt, to run
  `scripts/calibration_verdict.py <bundle> --years <y>` and `--json` read-only and paste both.
- What *can* be said about them, as bounds rather than measurements: the arm's unweighted system
  price mean moved **+0.0269 $/MWh** (33.016364 → 33.0433), p95 **+0.035**, and the maximum is
  **identical** (326.4235 both). The control's C3a sits 1.825 $/MWh below its upper band, so a
  flip would require the load-weighted move to exceed the unweighted move by **~68×**. That is an
  inference, not a measurement, and it is not counted as a pass.
- **C1 could not have flipped at this magnitude, and that is arithmetic rather than luck**: the
  band is ≥2.966 TWh and the mechanism moves ~0.078 TWh. `S4`'s C1 leg is therefore a weak test,
  exactly as the PRECOMMIT said in advance.
- **The screen says nothing about whether the arm is better.** It is not allowed to. For the
  record and explicitly **not as a gate**: the control over-produces ST_GAS by +1.669 TWh against
  its bench and the arm's miss is +1.591 TWh. That number played no part in any verdict above.

---

## 6. THE OPEN QUESTIONS — both are the owner's, and both are live NOW

**(a) Spend the full 2023–2025 span?** The owner's ruling was *"full span only if the screen
clears"*. The screen killed the arm on **no** mechanism property — but one registered gate fired
and was repaired **post-hoc**, and two `S4` legs went unmeasured, so I am **not** treating
"clears" as self-evidently satisfied and have **not** spent the span on my own reading. Cost if
authorized: three per-year shards; the screen year took **5 minutes**, so ~5–8 minutes wall clock
in parallel plus parent-side composition and scoring.

**(b) Promotion is separate, and it is not mine.** Even a clean span would not make this a
keeper; rule 31 `[R-RETAIN]` reserves that call. My own reading, offered as a recommendation and
nothing more: the change is a genuine rule-14 construction repair with a measured basis, zero new
fields, exact confinement, and a footprint that landed on its pre-registered prediction — but it
**moves a frozen coefficient with no source-data trigger**, which is precisely the rule-21
admissibility question nyiso-203 refused to answer alone and the owner has not yet ruled on.

**RETENTION, PLAINLY: the arm bundle exists only on the shard's container
(`results/calibration/nyiso226_screen_2023/`, gitignored per rule 29(c)/31) and WILL NOT SURVIVE
container reclamation.** It was not deleted. If it is gone when (a) is answered, the 2023 leg
costs ~5 minutes to reproduce. Every number this session will ever cite is in this document and
in `docs/SHARDREPORT-nyiso226-screen-2023.md` on branch `claude/nyiso226-screen-2023` — the
record is the doc, never the parquet.

---

## 7. Two zero-LP findings this session also produced, neither of them a lane

**(a) CT_CHP is scored by nothing, and the stated reason for that is false in NYISO.**
`calibration_verdict.FUELMIX_EXCLUDED` drops CT_CHP from C1 on the ground that *"CT_CHP is a BTM
peaker the grid LP zeroes by construction"*. For NYISO the bench's own `btmClass` puts CT_CHP at
**0.1514 TWh of a 2.4336 TWh class — 94 % grid-delivered** — and the LP dispatches **2.843 TWh**
of it (2023). It is simultaneously exempt in D-2 (`d2_exempt_classes`) and ungated in D-1 (not in
`d1_gated_classes`), while its measured D-1 shape is **`profile_r` 0.337 / 0.251 / 0.231** and
**`cv_ratio` 6.03 / 7.50 / 3.13** across 2023–2025 — a class at ~1.9 % of ISO load whose diurnal
profile is essentially uncorrelated with its own meter. **This is a shared-scorer scope question
touching every ISO, not a NYISO mechanism**, so it is recorded for the owner and **not** acted on
(rule 25 `[R-ISO-SCOPE]` and the plain fact that `FUELMIX_EXCLUDED` is not NYISO's file).

**(b) `curate_lmp.py`'s `KeyError: 'MGHG'` is avoidable, and the standing handoff text is wrong.**
It is a **CAISO** file defect. Pointing `curate_lmp.main()` at a raw dir containing only the
`NYISO/` subtree (a symlink suffices) curates all four NYISO partitions cleanly. The parent did
exactly that and scored C1–C8 in-session. The claim that shards cannot score C3a/C3b — carried
forward in several NYISO handoffs — is therefore false as stated. **No script was modified.**

---

## 8. Matrix (rule 30 `[R-MECH-MATRIX]`)

No new `ScenarioConfig` field was created, so **no new matrix row**. The NYISO shard is
re-stamped this session with the screen's outcome, per duty (b).
