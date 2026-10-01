# PRECOMMIT — capx D78-R2: the sector gate over the full 2021–2025 window, on the corrected W4 edge and a restated, TESTED W5

**Lane:** capx D78-R2 (director r#50, pack §D78-R2). **Branch:**
`claude/capx-d78r2-full-window-2zudj4`, FRESH off `origin/main` `e6a0402f`.
**Date:** 2026-09-06. **Model:** Opus. **DATA PROFILE:** `pjm`.
**Charter:** pack §D78-R2 + `FINDING-capx-d78r-2026-09-06.md` (§3 identities, §3.4 the
E&AS propagation, §4 the W4 construction error and the corrected edge, §6 the flip condition
and its three successor items) + `FINDING-capx-d81-2026-09-06.md` §8 item 2 +
D78 PRECOMMIT §7 / `FINDING-capx-d58-2026-09-06.md` §5.

**THIS DOCUMENT IS PUSHED BEFORE ANY LP.** Every gate, every edge, every declared
class and the whole-ledger classification rules below are fixed here. The one
quantity that cannot be written until the control leg exists — the W4′ band's two
numeric edges — is computed **on the control leg alone, after it solves and before
the arm is launched**, and pushed as **ADDENDUM 1** (D74 §9 item 3's procedure).
Its *definition* is fixed here and is not re-derivable afterwards.

**NOTHING ARMS FROM THIS LANE'S SOLVES.** No `ScenarioConfig` field is added or
changed, no default is flipped, no `_pjm_config` override is written, no keeper or
marker moves. `retirement_sector_gate` stays default-off and un-overridden for PJM.
The arm registers **SUFFIXED** as `pjm-t1h-d78r2-sectorgate`; the bare `pjm-t1h` key
is untouched; the control bundle is **deleted before merge** (rule 29(c)).

---

## 1. STEP 0 is already landed, and it is INERT for both legs

`bf97317f` (pushed, blobs verified against local per rule 27) deletes
`apply_economic_retirements`'s `exempt_unit_ids` parameter — the director's
decision (a) on `FINDING-capx-d81` §8 item 2 — and restates D78's T3 as the
negative test on the residual construction. It is on this branch, so **both legs
below run with it**, which is why its inertness matters and is established here
rather than asserted later:

| claim | how it is established |
|---|---|
| the deleted branch was unreachable | D81 routed all three declarations to `exit_exempt_unit_ids`; the parameter had no producer at any call site, and `evolve_fleet` passed a literal `frozenset()` |
| no cache key moves | `docs/handoffs/d78r2/keys_probe.py` run in this tree and on `origin/main` gives **byte-identical** JSON (`keys_probe.json` vs `keys_probe_origin_main.json`) |
| the bare `pjm-t1h` key is unmoved | control key resolves to `a9c66d8ea25acb9d` = the key the registered D67-ARM sidecar `frontend/data/hindcast/pjm-2021-2025-realized-t1h-d67arm.json` carries in `meta.cache_key` |
| the armed key is unmoved | arm key resolves to `bb6a60239d69508b` = D78-R's arm key (its §1 table) |
| every backcast key is unmoved | one backcast key per ISO in the same probe, identical on both trees |
| no test regresses | `tests/unit/model/`: **27 failed / 1420 passed** here vs **27 failed / 1419 passed** on `origin/main` — the same 27 pre-existing `test_d74_no_default_cap_convention` failures, plus the one new test |

Rules 21 / 24: zero DOF, no tunable added or changed, no field, no registry entry.

## 2. G-DRIFT — the code-level drift audit, before any LP (rule 29(b))

The question rule 29(b) puts is whether the incumbent's committed numbers can serve
as a control. Here the answer is settled twice over and in opposite directions, and
both are recorded before the solves:

**(a) From D78-R's close `f9b377a8` to this branch's base `e6a0402f`: ZERO HUNKS on
the solve path.**

```
git diff --stat f9b377a8..e6a0402f -- src/market_sim scripts/run_calibration.py \
    scripts/run_calibration_full.py scripts/run_capacity_hindcast.py scripts/lib \
    data/raw/_validation-source data/raw/reference
→ (empty)
```

`constants.py` first, as the charter directs: `git diff --stat f9b377a8..e6a0402f --
src/market_sim/config/constants.py` is **empty**. There is no hunk to classify LIVE
or INERT — the audit is complete because the surface is empty. The 25 commits in
that range touch `results/capacity-hindcast`, `docs/handoffs`,
`results/calibration`, `scripts/probes`, `docs/codebase-site`, `frontend/data`,
`scripts/register_forecast_run.py` and one `.gitignore` — no solve-path file.

**(b) But D78-R's LEGS are NOT at that state, so its bundles are still not a
control.** Its control-P guard was `cbf98979` and its arm `99245361`, both *before*
its branch took main's D67-ARM / D81 / D74 / D75-R:

```
git diff --stat 99245361 e6a0402f -- src/market_sim scripts/
→ 19 files, 2975 insertions, 54 deletions
  (incl. retirements.py +116/-…, runner.py +106/-…, scenarios.py +142,
   capacity_market.py +131, constants.py +1, adequacy.py +16, new_entry.py +6)
```

Those hunks are **LIVE for this ISO by inspection** — `retirements.py`,
`capacity_market.py` and `adequacy.py` are the clearing/screen path a PJM
forecast-mode hindcast runs through, and `constants.py` moved. Under rule 29(b)
that earns a control solve, and it is why **BOTH legs are re-solved at one HEAD**
rather than differenced against D78-R's committed arm. Two further reasons compound
it, either of which alone would be sufficient: D78-R's **control-P was deleted
before merge** (rule 29(c)), and its arm is registered **slim** (`meta.json`,
`run_config.json`, `forecast_verdict.json` only) — it carries no
`evolution_<year>.json`, so the whole-ledger diff §4 requires could not be taken
against it at any code state.

**Recorded consequence.** The two legs of this lane share one solve-code state by
construction (§5's HEAD guard proves it after the fact); nothing from D78-R's
measurement is reused as a control number, and its numbers appear in the FINDING
only as *history* — never differenced against this lane's.

## 3. What is being decided, and what is not

The mechanism is `retirement_sector_gate` (capx D53): armed, every thermal unit
whose plant's EIA-860 `Sector` is 1 (regulated electric utility) is exogenous to the
step-3 economic screen through `exit_exempt_unit_ids` — evaluated, **offered** into
the D57 clearing at its net-ACR cap, and partitioned out of `margins` before any
decision rule. It is PJM's must-offer requirement plus an ownership attribute, not a
tuned quantity. **Rule 1 `[R-STRUCT]`: every gate below is an identity or a
control-derived bracket; none is a residual, and none may be read as "did the fit
improve".**

**Rule 14, the sign line, stated before the solve.** A candidate-set gate can only
REMOVE candidates from a screen that produces exits, so the window's decided and
executed economic MW can only FALL or stay equal. `retire.total_gw`,
`unit_recall_gt300`, `plant_recall_frac` and `false_retire` will move as a
consequence and are **REPORTED AT FULL MAGNITUDE AND ARE NOT CRITERIA IN EITHER
DIRECTION** — an improvement is not evidence for the mechanism and a degradation is
not evidence against it. D58 PREDECL §3 P5 established that PJM's control
over-retires, so `retire.total_gw` improving is the expected arithmetic of removing
candidates, not skill.

## 4. The gates

W0 is **DROPPED, not restated.** D78-R's §2 W0′ closed the attribution of every
2022 quantity to D67-ARM and D81 exactly and to the MW, discharging the residual
known-answer content W0 carried; and both of this lane's legs solve at ONE code
state, so there is no cross-HEAD known answer left for it to check. Saying so here,
before the solve, is the point — a gate dropped after a result is a gate evaded.

### W1 / W2 / W3 — as D78-R, unchanged, on D78-R's own readers

Imported from `docs/handoffs/d78r/window_compare.py`, never re-implemented, so the
two lanes cannot drift on what a failing pool or a decided row is.

- **W1 (candidate identity).** In an *exact* year (identical fleets) the arm's
  failing pool is the control's minus rows that are **100 % sector-1**, the arm-only
  set is **EMPTY**, and every shared row's MW is identical to 1e-6. In a
  *fleet-delta* year every control-only row is sector-1 **or** already gone from the
  arm's fleet, and every arm-only row is one the control retired earlier.
- **W2 (decided-cohort composition).** **ZERO** sector-1 rows in the arm's
  `decided`, `entry_capped`, `floor_retained`, `throughput_deferred`, any
  `pipeline_events` row, or `retirements` with `reason == "economic"` — in every
  year. Zero unknown-sector pipeline rows.
- **W3 (decided-cohort provenance).** Every arm-only decided row and every arm-only
  executed row is explained by the control's `entry_capped` pool or by the fleet
  delta. An unexplained row is a STOP.

### W4′ — the band, with the LOWER EDGE REPAIRED

```
band = [ Σ_y decided_mw(ctl) − Σ_y sector1_decided_mw(ctl) ,
         Σ_y decided_mw(ctl) + Σ_y g_y ]
g_y  = max single-row MW in control-P's year-y failing pool (decided ∪ entry_capped),
       0 in a year where the admission cap does not bind
```

**Both edges are computed on the SAME-HEAD control leg, after it solves and before
the arm is launched**, and pushed as ADDENDUM 1.

The upper edge is D78-R's and is unchanged: `g_y` is the granularity of one
whole-unit admission at the budget boundary, which is the right bound on how far a
re-fill can overshoot. **The lower edge is the repair.** A candidate-set gate can
only remove candidates, so the most it can subtract from the window's decided total
is exactly the decided MW of the candidates it removes — the control's own sector-1
decided MW. D78-R bracketed the downside by `±Σg_y` instead, a quantity about the
cap's granularity rather than about the partition, and its arm landed 1,117.354 MW
below the resulting edge on a measurement that was otherwise the cleanest possible
confirmation of an exact partition (D78-R §4).

**`Σdecided_ctl − Σ(sector-1 decided_ctl)` is therefore also the POINT VALUE — the
exact-partition prediction.** An arm that removes exactly the sector-1 candidates
and re-fills nothing lands ON the lower edge. That is a stronger claim than "inside
a band", and it is pre-registered as such: the FINDING will report the arm's
distance from the point value, not merely its band membership.

### W5′ — purity, restated to admit the E&AS propagation and to TEST it

D78-R's W5 asserted "every unit present in both years' stacks carries an identical
offer and `A_g`" with no carve-out, and fired in 2024–2025 because the net-ACR
offer's E&AS margin reads the **prior year's** prices through `prior_results`: once
the arm retires less in 2022, the 2023 prices differ, so the 2024 offers differ.
That is a second-order propagation of the fleet delta, one year removed, and it is
unavoidable for *any* mechanism that changes *any* exit.

Let **D** = the **first divergent year**: the first solved year whose screen sees
different fleets in the two legs (computed from the ledgers, never hard-coded —
`first_divergent_year` compares the prior-exit sets). Per year, over units present
in **both** legs' offer stacks:

| limb | years | condition | why it is the right edge |
|---|---|---|---|
| **structural** | **every** | shared-stack `A_g` identical (≤1e-6) **and** `fuel` identical | neither can move through any channel this mechanism owns; a difference is a second seam by definition |
| **exactness** | **y ≤ D** | shared-stack **offers** identical (≤1e-9) **and** **cleared flags** identical | up to D the offers read a prior-year price vector the legs share, so they must agree; where offers agree the clearing must agree |
| **propagation (i)** | **y > D** | every shared unit whose fuel is in the declared **zero-E&AS class set** carries offer delta **EXACTLY 0** | a unit with `EAS_g ≤ 0` offers at its FULL net-ACR bar `GFC_g/(A_g×365)`, which reads no price vector at all — so it *cannot* move through the price channel |
| **propagation (ii)** | **y > D** | every shared unit whose offer DOES differ is **outside** that set | the movers are exactly the units with a live E&AS operand |

**The zero-E&AS class set is `{gas_ct, gas_st, oil}`, DECLARED EX ANTE FROM THE
RECORD, never selected on this lane's measurement**: `FINDING-capx-d57-2026-09-05.md`
§8.1 names the CT / ST / oil E&AS operand as zero in the hindcast prices (it is why
D57's measured price ran 1.5–5.7× the published), and `FINDING-capx-d81` §8 item 3
restates it as the successor question. That citation is what makes limbs (i)/(ii) a
**falsifiable prediction** of the propagation story rather than a restatement of it:
if the offer movers are *not* confined to the live-E&AS classes, the propagation
account is wrong and W5′ fails.

The stack's fuel vocabulary is checked against the seven keys of
`retirements._THERMAL_FOM`; **an unrecognised fuel string is a STOP**, never a
silent skip, because it would mean the zero-E&AS partition is grading a set whose
shape it does not know.

**A cleared-flag difference in a year after D is REPORTED, NOT GATED, and this is
declared before the solve rather than discovered after it.** The flag is a function
of the offer stack's ordering against the demand curve. Gating it while admitting
offer drift would gate the same propagation twice — the same class of mis-derived
edge that fired D78-R's W4 (a gate whose bound does not match the mechanism's own
arithmetic). It is differenced and printed in full so a reader can see it; it simply
does not decide anything. D78-R measured 5 such flags in 2024; whatever this lane
measures is reported the same way.

### LEDGER — the whole-ledger diff (`FINDING-capx-d81` §8 item 4)

D81's own lesson: three of six gates in that lane were mis-specified, and the
mechanism's real effect was found by differencing every committed block, not by the
gate table. **An assertion list is the floor, not the ceiling.** So every top-level
block of every year's `evolution_<year>.json` is differenced — the union of both
legs' keys, not an allowlist — and each difference classified:

- **R1 sector-1 partition** — the differing per-unit rows are all at sector-1 plants.
- **R2 fleet-delta** — the differing per-unit rows are units exactly one leg had
  already retired in an earlier year.
- **R3 E&AS propagation** — an `offer_stack` offer value differing in a year after
  **D**, on a unit outside the zero-E&AS set.
- **R4 aggregate** — a scalar or by-fuel/by-tech roll-up. Differenced and
  **REPORTED for narrative explanation in the FINDING**; never a STOP, because an
  aggregate cannot localise a seam.

**A per-unit row difference (in `retirements`, `pipeline_events`, `floor_retained`,
`confirmed_derates`, `announced_derates`, `ccs_retrofits`, `thermal_additions`,
`renewable_additions`) that classifies under none of R1–R3 is a STOP.** That is the
only place this diff refuses rather than reports, and it is where a second seam
would show. The FINDING carries the *whole* diff — every differing block with its
values — not just the gate verdicts.

Instrument: `docs/handoffs/d78r2/window_compare2.py`, **committed before the first
LP**.

## 5. The two legs

| leg | recipe | out-dir |
|---|---|---|
| **control-P** | bare `pjm-t1h` | `results/hindcast/pjm-2021-2025-realized-t1h-d78r2-control-P` |
| **arm** | `--retirement-sector-gate` | `results/hindcast/pjm-2021-2025-realized-t1h-d78r2-sectorgate` |

Both: `run_capacity_hindcast.py --iso PJM --start-year 2021 --end-year 2025
--vintage 2020 --fuel-variant realized --entry-screen-diagnostics`, through the
committed `docs/handoffs/d78r2/run_full.sh`, which **guards HEAD around each leg**
and exits 90 if it moves. PJM solo, legs sequential, years sequential (rule 12).
Declared keys, to be checked against the realized `run_config.json`: control
`a9c66d8ea25acb9d`, arm `bb6a60239d69508b` (§1).

**Rebase discipline (rule 29 / D78-R §1's STOP 9).** A rebase happens **BETWEEN**
legs, **never during one**. If `main` moves under the lane, the G-DRIFT audit of §2
is re-run over the new range and the W0′-style attribution restated **before**
anything is re-solved or graded; a LIVE hunk on this ISO's backcast path voids the
control and costs a re-solve, exactly as it cost D78-R one.

`data/clean` was absent at session start and is rebuilt in full
(`scripts/regenerate_clean.py`) before any leg; the rebuild's datatype count and
failure count are recorded in the FINDING.

**Rule 22.** Forecast-mode hindcast (`mode="forecast"`); the holdout freeze is
asserted ACTIVE on every leg; no backcast-mode run touches an out-of-training year,
and nothing outside 2023–2025 is solved, scored or registered in backcast mode.

## 6. STOPs — any one kills the arm; none is promoted past

1. A **HEAD guard** trip (`run_full.sh` exit 90).
2. A realized cache key ≠ its declared value in §1/§5.
3. **W1**, **W2** or **W3** failing.
4. **W5′** failing on any limb — including an unrecognised stack fuel.
5. A **LEDGER** per-unit STOP (a row difference no R1–R3 rule classifies).
6. **W4′** falling outside its ADDENDUM-1 band.
7. `main` moving **during** a leg (the leg is discarded, not graded).

A fired STOP is **honored however right the diagnosis** — the D62 / D78 / D78-R
precedent. A lane does not promote past its own pre-registration, and a corrected
gate is offered to the director as a *successor's* pre-registration, never as a
re-read of this one.

## 7. The flip condition — the arming recommendation, PRE-STATED

Restating D78 PRECOMMIT §7 / D58 §5 on the repaired W4 edge and the restated W5′.
Recommend **ARM for PJM** (`retirement_sector_gate: True` in
`iso_configs._pjm_config` `default_scenario_overrides` — **recommended, never
written by this lane**) **iff ALL FOUR of**:

- **(a) purity** — **W5′** holds on the full window (structural limbs every year;
  exactness through D; propagation (i)/(ii) after D);
- **(b) fidelity** — **W1 ∧ W2 ∧ W3** hold;
- **(c) composition** — window `economic` release precision does not fall below the
  **same-HEAD control's**, and every admitted / decided / executed row is at a
  non-sector-1 plant;
- **(d) LOYO** — `retire.unit_recall_gt300` LOYO loses no fold the same-HEAD control
  holds (`--flip-gate-extras` on both legs; an ABSENT `loyo` block reads **NOT
  ADJUDICABLE**, never a vacuous pass — D78-R §7 limitation 5).

**W4′ and the LEDGER diff are STOPs (§6), not limbs**: they can kill the
recommendation but cannot make it.

Recommend **HOLD-and-route** if (a) fails. Recommend **DECLINE** if (b) or (c)
fails. `retire.total_gw`, `false_retire`, recall and precision-as-a-number are
**explicitly NOT conditions in either direction** (rule 14, §3).

## 8. Registration, retention, board

- The **arm** registers **SUFFIXED** as
  `pjm-2021-2025-realized-t1h-d78r2-sectorgate` → **`pjm-t1h-d78r2-sectorgate`**,
  **AFTER D65-B-R's batch registers**, slim files only.
- The **control** bundle is **DELETED BEFORE MERGE** (rule 29(c)); every number this
  lane will ever cite lives in this PRECOMMIT with its addenda, the FINDING, and
  `docs/handoffs/d78r2/{keys_probe,control_band,window_compare2}.json`.
- **Rule 28(b):** PJM's `retirement_sector_gate` cell in
  `docs/codebase-site/data/mechanism-matrix/PJM.js` only — its letter set by the
  grade, its evidence citing this lane. No other shard; no new row (no new field).
- **Board lock:** the registry sidecar and its `VERDICT_MAP` entry only. The
  `ff-verdicts.json` / `program-status.json` snapshot row is **held** — the board is
  not this lane's to write.
