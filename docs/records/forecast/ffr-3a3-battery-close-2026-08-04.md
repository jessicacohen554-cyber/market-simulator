# FFR-3A-3 — the T1-H / T1-X halves re-measured at the post-FFR-3F HEAD

**Session.** FFR Wave 3, battery-close lane, third pass. This document is an
**addendum** to `docs/handoffs/ffr-3a2-battery-close-2026-08-03.md`. That
document's sections stand as written; nothing in it is deleted or rewritten
here. Where a number moved, the correction is stated in §5 below and a forward
pointer is left at the affected section.

**Nothing is promoted. Nothing is tuned.** No `ScenarioConfig` default moved, no
band widened, no damper unarmed, no parameter adjusted in response to any score.
Owner decision Addendum D.1 (*HOLD PROMOTION, FIND ROOT CAUSE*, both mechanisms
stay armed) and Addendum G.1 (the D-8 mechanisms ship default-OFF) are honoured
throughout — verified in the **resolved** config, not just the request (§1.3).

---

## 0. Why this session exists — the dispatch premise was stale

The dispatching prompt directed this session to fill five `(pending)` sections in
FFR-3A-2's handoff and to do "the whole registration duty", stating that FFR-3A-2
had registered nothing.

**Both halves of that premise were false, and were checked before any compute was
spent.** FFR-3A-2's final commit `48b834c3` contains **zero** `(pending)` markers —
it completed all five sections — and it *did* register, in commits `720a0c01`,
`6d6b2ab4` and `6057347d`.

What FFR-3A-2 actually left open is named in its own **provenance ceiling** banner:
its battery measured a **superseded configuration**. The rebase brought in FFR-3F's
G3 cap-grain fix (`2adfb49`), which is **unconditional** and changes the admitted
exit set — the same economic-retirement screen every T1-H finding rests on. Its
banner says §3.7 (NYISO), §3.8 (PJM) and §3.9 (MISO) *"should be re-measured at the
post-FFR-3F HEAD before being relied on."*

This session does that, on owner instruction after the discrepancy was surfaced.

---

## 1. Scope and posture

### 1.1 What was re-solved

Seven legs were in scope: four T1-H curve legs and three T1-X crossover legs.
**Six completed.** MISO T1-X did not (§6.1).

| leg | bundle | status |
|---|---|---|
| NEISO T1-H | `neiso-2021-2025-realized-ffr3a3` | measured |
| NYISO T1-H | `nyiso-2021-2025-realized-ffr3a3` | measured |
| PJM T1-H | `pjm-2021-2025-realized-ffr3a3` | measured |
| MISO T1-H | `miso-2021-2025-realized-ffr3a3` | measured |
| ERCOT T1-X | `ercot-2023-2027-crossover-ffr3a3` | measured |
| PJM T1-X | `pjm-2023-2027-crossover-ffr3a3` | measured |
| **MISO T1-X** | — | **NOT MEASURED** (§6.1) |

**T1-F was deliberately NOT re-run.** It does not turn on the exit screen's grain,
so the extra cost buys nothing. That makes the scorecard **mixed-provenance**, which
is handled explicitly rather than hidden (§4).

### 1.2 Base

Solved at **`941f4983`**, which carries `2adfb49` and `87659ae4` as ancestors
(both verified, not assumed). Scored and registered at `e2a422c1`.

### 1.3 Posture — verified in the resolved config

All six solve-affecting flags were **omitted** from every invocation so each
inherits the shipped default. Confirmed by reading the *resolved* config out of the
run log, not the request:

```
retirement_rule = pipeline    entry_rate_limits = True
correlated_forced_outage = True    entry_commissioning_lag = True
entry_lookahead_reprice = True     exit_rate_limits = False
```

`exit_rate_limits=False` is Addendum G.1 honoured: FFR-3F's D-8 mechanism is
present in the code but unarmed.

### 1.4 Rule 22 — re-verified at this HEAD, not inherited

`scripts/lib/holdout_policy.py` was read at this HEAD rather than trusting
FFR-3A-2 §3.3: `HINDCAST_SOLVE_YEARS = {2021, 2023, 2024, 2025}`,
`HINDCAST_BRIDGE_YEARS = {2022, 2026}`, scoring bounded to 2023–2025. The runner
printed its governance line on every leg. The **holdout spend freeze is ACTIVE**
and was neither spent nor worked around. Every T1-X leg's scorer emitted
`read_ge_2026: false`. No marker was spent; no out-of-training year was solved,
scored or registered.

---

## 2. T1-H results — the four curve legs

### 2.1 The pattern

**The G3 fix moves a leg exactly in proportion to how hard its economic-retirement
screen fires.** That is the correct signature for a change to the *admitted exit
set*, and two of the four legs act as negative controls on the re-measurement
itself.

| leg | economic exits | what moved |
|---|---|---|
| **NYISO** | **none** | **nothing**, to three decimals |
| **NEISO** | small | retirement level only |
| **PJM** | coal 14.756 GW | depth improved 3.55 GW |
| **MISO** | coal 11.932 GW | depth worsened; **one band flipped** |

### 2.2 NEISO — retirement level only

| metric | actual | pre-3F (§3.6) | **post-3F** | |
|---|---|---|---|---|
| `retire.total_gw` | 0.951 | 8.221 FAIL | **7.585** FAIL | closer, still ~8× |
| `retire.unit_recall_gt300` | — | FAIL | FAIL | unchanged |
| `retire.false_retire` | — | FAIL | FAIL | unchanged |
| `add.by_tech.wind` | 0.225 | 1.0 FAIL | **1.0** FAIL | **identical** |
| `add.by_tech.solar` | 1.947 | 1.028 FAIL | **1.028** FAIL | **identical** |
| `add.by_tech.gas_ct` | 0.163 | 0.0 FAIL | **0.0** FAIL | identical |
| `add.by_tech.storage` | 0.642 | 0.0 FAIL | **0.0** FAIL | identical |

**Every additions band is byte-identical while the retirement level moves.** That
is a useful internal check: an exit-screen-only change should touch exits and
nothing else, and here it demonstrably does.

### 2.3 NYISO — §3.7 CONFIRMED, and this is the strongest form of the claim

| metric | actual | pre-3F (§3.7) | **post-3F** |
|---|---|---|---|
| `retire.total_gw` | 1.488 | 1.036 FAIL | **1.036** FAIL |
| `retire.unit_recall_gt300` | — | PASS | **PASS** |
| `retire.false_retire` | — | PASS | **PASS** |
| `add.by_tech.wind` | 0.890 | 0.951 PASS | **0.951 PASS** |
| `add.by_tech.solar` | 2.197 | 0.891 FAIL | **0.891** FAIL |

**Every band identical.** The evolution ledgers book exactly **one** retirement
event across all five years — 2022, reason `announced` — and **zero economic
retirements**.

FFR-3A-2 §3.7 concluded D-1 is *provably inert* in NYISO's T1-H window. A fix to
the admission-cap grain of the economic screen is precisely the experiment that
claim predicts must do nothing, and it does nothing. §3.7 is not merely
un-invalidated by the ceiling; it is **independently confirmed post-fix**.

### 2.4 PJM — the depth residual was partly a grain artifact

| metric | actual | FF-2C | pre-3F (§3.8) | **post-3F** |
|---|---|---|---|---|
| `retire.total_gw` | 11.121 | 18.157 | 22.415 FAIL | **18.862** FAIL |
| `retire.unit_recall_gt300` | — | FAIL | PASS | **PASS** (13/17) |
| `retire.false_retire` | — | FAIL | FAIL | **FAIL** |

Per-fuel, the movement is confined to one channel:

| fuel | pre-3F | **post-3F** |
|---|---|---|
| **coal (economic)** | 18.309 | **14.756** |
| gas_st / gas_ct | 0.0 / 0.0 | 0.0 / 0.0 |
| nuclear / biomass (announced) | 4.097 / 0.009 | 4.097 / 0.009 |

**FFR-3C's membership-vs-calendar split SURVIVES** — membership still right
(recall PASS), depth still wrong (1.70× actual) — and the depth residual moved
3.55 GW in exactly the direction the split calls a grain artifact. The remaining
gap stays the chartered G-31 lane's business (Addendum F.1); no throughput
mechanism was armed, proposed or parameterized here.

### 2.5 MISO — the 3/3 retirement sweep does NOT survive

| metric | actual | pre-3F (§3.9) | **post-3F** | |
|---|---|---|---|---|
| `retire.total_gw` | 15.227 | 13.734 **PASS** | **12.716 FAIL** (−16.5%) | **FLIPPED BACK** |
| `retire.unit_recall_gt300` | — | PASS | **PASS** (13/17) | unchanged |
| `retire.false_retire` | — | PASS | **PASS** (0.997 GW) | unchanged |

Per-fuel: **coal (economic) 12.95 → 11.932 GW**; nuclear 0.768 and biomass 0.016
announced and unmoved.

So §3.9's headline — *"every retirement band now PASSES"* — is **2/3 post-fix**,
not 3/3.

**Direction matters and is not shared with PJM.** MISO **under**-retires (12.716
vs 15.227 actual) where PJM **over**-retires (18.862 vs 11.121). These are not the
same depth error with a common sign, and a single throughput story will not
explain both.

---

## 3. The load-bearing finding — both legs land on FFR-2B's controlled values

This is the strongest evidence in the session, and it is what makes §2.5's
correction a *vindication of the fix* rather than a regression.

FFR-2B measured the legacy→pipeline flip **against a paired control**. Post-G3-fix,
this session's independent, uncontrolled re-solves reproduce those controlled
numbers exactly:

| quantity | FFR-2B (paired control) | pre-3F (FFR-3A-2) | **post-3F (here)** |
|---|---|---|---|
| PJM coal economic exits | **14.756 GW** | 18.309 | **14.756** |
| MISO coal economic exits | **11.932 GW** | 12.95 | **11.932** |
| MISO false-retire | **0.997 GW** | 0.997 | **0.997** |
| MISO recall | **13/17** | 13/17 | **13/17** |

**Two ISOs converging independently on values measured under a control** is much
stronger than either leg alone. The reading: FFR-3A-2's pre-fix figures carried the
cap-grain bug, `2adfb49` removes it, and in MISO's case the bug happened to
*flatter* the level band into a PASS.

**Stated as convergence, not attribution.** No paired control was run in this
session. What is claimed is that two post-fix values coincide with two
independently controlled values — which is evidence about the fix, not a controlled
experiment of this session's own.

---

## 4. T1-X results

Both measured legs are **completely unmoved** — every metric identical to
FFR-3A-2.

### 4.1 ERCOT — the price-2025 regression is REAL, not a pre-3F artifact

| metric | 2023 | 2024 | 2025 | keeper 2025 |
|---|---|---|---|---|
| price | 68.7% | 41.2% | **22.5%** | 8.1% |
| co2 | 49.2% | 42.7% | 50.6% | — |
| coal_twh | 35.0% | 44.1% | 37.2% | 3.8% |
| gas_twh | 19.6% | 10.0% | uncovered | — |

FFR-3A-2 §9 blocker 7 recorded that FF-2D's headline convergence
(price 2025 `8.6% PASS → 22.5% FAIL`) had been lost, but could not say whether that
was an artifact of the superseded configuration. **It is not.** The regression
reproduces unchanged at the shipped configuration, so the blocker stands on its own
evidence rather than pending a re-measurement. Still **not attributed** — no T1-X
control arm was run here either.

### 4.2 PJM — unchanged

price `3.6 / 6.6 / 15.7 %`, co2 `45.1 / 40.4 / 54.2 %`,
coal_twh `13.0 / 23.9 / uncovered`, gas_twh `0.4 / 6.7 / uncovered`.

**PJM's T1-X is unmoved while PJM's T1-H moved 3.55 GW under the same fix.** That
is consistent, not contradictory: T1-X seeds from the 2023 vintage over 2023–2027
while T1-H seeds from 2020 over 2021–2025, so the admission cap re-grains a
different decision set on a different fleet.

---

## 5. Corrections to FFR-3A-2 — stated, not overwritten

Per the Addenda A–G convention, the predecessor's text stands and is corrected
here.

| FFR-3A-2 claim | status | correction |
|---|---|---|
| §3.9 *"MISO: every retirement band now PASSES"* (3/3) | **SUPERSEDED** | 2/3 post-fix; `retire.total_gw` 13.734 PASS → **12.716 FAIL** (§2.5) |
| §3.8 PJM `retire.total_gw` 22.415 | **SUPERSEDED** | **18.862** post-fix (§2.4) |
| §3.8 PJM coal 18.309 GW | **SUPERSEDED** | **14.756** post-fix, = FFR-2B's controlled value (§3) |
| §3.6 NEISO `retire.total_gw` 8.221 | **SUPERSEDED** | **7.585** post-fix (§2.2) |
| §3.7 NYISO — D-1 provably inert | **CONFIRMED** | every band identical post-fix (§2.3) |
| §3.10 *"all four FC-3 FAIL"* | **STANDS** | all four still FC-3 FAIL |
| §4.2–4.4 T1-X ERCOT / PJM numbers | **STAND** | reproduce exactly (§4) |
| §9 blocker 7 (ERCOT price-2025 regression) | **STANDS, now settled as real** | reproduces post-fix (§4.1) |
| §3.8 membership-vs-calendar split | **STANDS** | reproduced post-fix (§2.4) |

**No determination moved.** All six measured legs are **HOLD**, with the same
category pattern FFR-3A-2 recorded (FC-3/FC-4 FAIL, FC-7 FAIL). The §2.1b gate is
unchanged and remains closed for all six ISOs.

---

## 6. What was NOT measured — stated explicitly

### 6.1 MISO T1-X — launched twice, killed twice, NOT measured

It is not reported, not estimated and not carried forward from FFR-3A-2. Its board
cell is **null**, not a stale value.

* **First kill.** OOM during year 2024 while nominally running solo on a 15 GB box.
* **Second kill.** OOM during year 2023 — **caused by this session**: a
  `git fetch` pulling 131 commits plus three push attempts ran while the leg sat at
  its memory peak. This is the same contention that killed the first PJM T1-X
  attempt, after that cause had already been identified. It was an avoidable error.
* **Both partial bundles were DELETED, not resumed**, because FFR-3A-2 §6.4 /
  blocker 3 measured kill-resume as not bit-reproducible; a resumed leg would have
  inherited that defect and been unreportable.

**What it would have tested.** Both other T1-X legs were completely unmoved, so the
prediction is that MISO T1-X is unmoved too. That prediction is **untested**. MISO
is also the ISO whose T1-H moved most, so it is not a free assumption.

### 6.2 Also not measured

1. **No control arm on any leg.** Every attribution here rests on structural
   inertness (NYISO), external corroboration (§3), or is withheld.
2. **T1-F was not re-run** (§1.1), so all T1-F determinations on the scorecard are
   carried forward at their own sha and marked `^`.
3. **FF-3E was not re-run.** Criterion (c)'s wall/RSS projection is carried from
   FFR-3A-2's committed scorecard and marked `^`.
4. **CAISO was not measured at all** — it has no T1-H or T1-X leg in this battery.
5. **FC-6 driver response was not run.** FFR-3A-2's bounded ERCOT result stands.
6. **The FH block is not lifted** and nothing here bears on it.
7. **G-31 exit throughput was not re-opened.** PJM's and MISO's remaining depth
   residuals are the chartered lane's business (Addendum F.1).

### 6.3 One scoring choice, disclosed

FC-7 scores **FAIL** on all six legs here, matching FFR-3A-2. Passing
`--run-config <bundle>/run_config.yaml` to the scorer instead lifts it to
**CAVEAT**, because the scorer accepts the hindcast runner's YAML.

**The like-for-like invocation was chosen deliberately.** FFR-3A-2 did not pass
that flag, and adopting it here would have shown FC-7 improving on every leg for
reasons having nothing to do with leg quality — a false gain in the regression
table. The CAVEAT result is recorded here as an instrument observation and is the
fix FFR-3A-2's blocker 5 asks for; it is **not** claimed as a result.

---

## 7. Scorecard, registration and the board

* **Scorecard.** `results/ffr3a3/scorecard/` via `scripts/build_ffr3a3_scorecard.py`,
  a thin successor that **imports** the predecessor's criterion functions rather
  than forking them. It was **authored before any leg finished solving** (rubric §4)
  and adds only two carry-forward channels, each tagged with `carried_from_sha` and
  rendered with `^`.
* **Registered** (rule 15, forecast namespace only — never the backcast registry):
  six sidecars under `frontend/data/hindcast/`, each with its own verdict key in
  `ff-verdicts.json` (32 → 38 entries) and its own `VERDICT_MAP` entry, because
  *a run must never render a verdict its own score contradicts*.
* **`program-status.json` refreshed.** The seed was dated **2026-07-20** and had
  gone materially stale — it recorded PJM as having no `calibration-complete`
  marker, which is false. Criterion (a) is now read **live**; what was carried
  rather than re-measured is enumerated in the file's own `refresh` block.

### 7.1 The §2.1b gate scorecard

`scored_at_sha e2a422c1` · holdout freeze **ACTIVE** · `^` = carried forward

| ISO | (a) backcast | mk | t1f | t1h | t1x | (c) proj h | solo |
|---|---|---|---|---|---|---|---|
| PJM | CALIBRATED | `C-` | HOLD^ | **HOLD** | **HOLD** | 7.34^ | yes |
| NEISO | CALIBRATED-WITH-CAVEATS | `C-` | HOLD^ | **HOLD** | — | 0.95^ | no |
| NYISO | NOT-YET | `C-` | HOLD^ | **HOLD** | — | 1.09^ | no |
| MISO | *(none parseable)* | `--` | HOLD^ | **HOLD** | — | 10.12^ | yes |
| ERCOT | NOT-YET | `--` | HOLD^ | — | **HOLD** | 2.0^ | no |
| CAISO | CALIBRATED-WITH-CAVEATS | `--` | HOLD^ | — | — | 2.78^ | no |

**No ISO clears the gate; criterion (b) closes it for all six.** Criterion (d) is
not evaluated — it is the owner's, and `final` is empty by design.

Two criterion-(a) cells moved during this session and are **backcast-lane facts,
not findings of this session**: NYISO now reads `NOT-YET`, and MISO's determination
is **not parseable** (its promotion note carries no determination string and it
holds no `complete` marker). Keepers moved at least four times while this session
ran; the scorecard reads them live.

---

## 8. Open blockers found here

1. **`ScenarioConfig.from_yaml` is strict, so a rule-26 field deletion makes every
   previously-written bundle unloadable.** `from_yaml` does a bare `cls(**data)`.
   When `pjm_seam_envelope_by_neighbor` was collapsed at `2ca08ed9` under rule 26
   `[R-DELETE]`, every bundle written before it — including all six here — became
   unregisterable with `TypeError: unexpected keyword argument`. This will recur on
   **every** future field deletion and silently strands any bundle older than it.
   A tolerant loader that drops unknown keys with a warning would close it.
   *Worked around here by stripping that one key from the 12 bundle configs. It was
   at its default (`false`) in a `to_yaml_full` dump — a defaulted key the codebase
   had deleted — so no solve semantics changed. Disclosed rather than silent.*
2. **FFR-3A-2 blocker 9 REPRODUCED and is still unguarded.** `--bundle` derives the
   run id from the directory basename, so out-dirs named `pjm` under `t1h/` and
   `t1x/` collided: the T1-X registration **silently overwrote** the T1-H one, and
   six registrations produced five sidecars. Caught by counting outputs, not by any
   error. Fixed here by renaming bundles to the `<iso>-<start>-<end>-<label>`
   convention, but the collision remains unguarded in the tool.
3. **`git push` cannot create a deleted branch through this remote.** After the
   session's branch was merged and deleted, re-creating it returned **HTTP 413 on a
   15,680-byte, 5-object pack**. Neither documented cause applied (`remote prune` +
   `fetch main` were done; it is not pack size), and `http.version=HTTP/1.1` and a
   large `postBuffer` both failed. **Workaround: `mcp__github__create_branch` +
   `push_files`**, which succeeded, with the blob verified byte-identical.
4. **Heavy crossover legs OOM on a 15 GB box under concurrent bookkeeping.** PJM
   T1-X peaks ~6.5 GB and completes when the box is clear, but dies in year 2024 if
   a scorer or a git fetch runs alongside it. This killed three legs across the
   session (one PJM, two MISO). For T2/T3, where resume is not optional, this needs
   either a real memory budget per leg or a scheduler that refuses to co-run.
5. **FC-7 fails on every leg by construction** — FFR-3A-2 blocker 5, unchanged.
   §6.3 records that passing the YAML lifts it to CAVEAT, which is the shape of the
   fix.

---

## 9. Standing disclosure list

Carried verbatim from `docs/forecast-readiness-peer-review-2026-07.md` §4 (the
single wording authority):

> This forecast is produced by a chronological full-8760 LP dispatch model with a
> one-pass annual capacity-evolution loop. It does not include: MIP unit commitment;
> intertemporal capacity optimization or within-year entry/exit convergence;
> inter-hour ramp constraints; intra-ISO hurdle rates; demand-responsive fuel
> pricing. Unless produced by the weather ensemble, results are conditional on a
> single pinned weather year (stated in the run config). Uncertainty bands are
> dispatch-conditional: the fleet-path (capacity-expansion) component of structural
> error is unmeasured and excluded. Deterministic scenario cases are a range, not a
> probability distribution.

---

## 10. For the successor

1. **Run MISO T1-X** (§6.1) — the one unmeasured leg. Give it a clear box.
2. **Do not re-run the other six.** Main moved 131 commits during this session and
   **zero** carried a default-ON `ScenarioConfig` addition, so the shipped posture
   is unchanged and these measurements stand at `941f4983`. Verify that claim again
   before relying on it — it is a property of those 131 commits, not a standing one.
3. **Blocker 1 is the highest-value fix** — it will strand bundles on every future
   rule-26 deletion, and it is a few lines.
4. **The depth residuals are G-31's**, not a tuning target. PJM over-retires and
   MISO under-retires; they need separate explanations (§2.5).
