# PRECOMMIT — capx D78-R3: the zero-E&AS set declared PER DELIVERY YEAR, derived structurally on the control, and W5″ re-graded on it

**Lane:** capx D78-R3 (successor to D78-R2 under rule 29; the successor's pre-registration
D78-R2 §9 items 1–3 routed). **Date:** 2026-09-06. **Model:** Opus.
**DATA PROFILE:** `pjm`. **Branch:** `claude/capx-d78r3-perdy-set`, off `origin/main` at
**`0f7a48426df2dda5714853297439a1a51e5ef3f0`** (`0f7a4842`).

**NOTHING ARMS.** `retirement_sector_gate` stays default-off and un-overridden for PJM. No
`ScenarioConfig` field is added, changed or flipped; `_pjm_config` is untouched; no default,
override, keeper, marker or parameter moves; `retirements.py`'s decision logic is not edited.
Zero DOF. The lane's whole output is a declaration, a derivation, a re-grade and a
recommendation.

---

## 0. Disclosure — what I had already read when I wrote this, and why the pre-registration still binds

The gate on this lane is *"any per-class number read before the PRECOMMIT is pushed."* Its
purpose is that the declaration, the derivation rule, the tolerance and the grade rule cannot be
selected against the answer. Stating exactly where I stand, because a pre-registration that
overclaims its own ignorance is worth less than one that doesn't:

- **I have read `FINDING-capx-d78r2-2026-09-06.md` §5.1 in full**, as the handoff ordered
  ("READ FIRST … FINDING-capx-d78r2 (all of it, sections 5, 8, 9, 10 twice)"). That table
  carries per-fuel shared/moved counts for 2022–2025 and four distinct-offer counts (oil 1,
  nuclear 1, gas_st 3, gas_ct 12 → 72). The handoff's own step 0(b) quotes those four numbers
  back at me. So I know the shape of the likely answer, and I say so here rather than performing
  a blindness I do not have.
- **What I have NOT read, and will not read until this document is pushed:** any value inside
  `docs/handoffs/d78r2/window_compare2.json` or `control_band.json`; any offer stack in any
  committed ledger. I established both files' schemas by reading the code that *wrote* them
  (`window_compare2.py`), never their contents.
- **What actually makes this binding, then**, is not ignorance but provenance and fixity:
  1. the declared set (§1) is quoted from **`FINDING-capx-d57-2026-09-05.md` §4**, written
     2026-09-05, before either D78-R2 or this lane existed, and it is the same set D78-R2 §9
     item 1 routed;
  2. the derivation rule (§2) is quoted **verbatim** from D78-R2 §9 item 2, merged at `80c88b76`;
  3. the tolerance, the subset guard, the vacuity convention, the STOPs and the grade rule are
     fixed **here**, in advance, and are not adjustable later — and the grade rule's two branches
     are both written out below so neither can be composed after the fact.

## 1. (a) THE DECLARED SET — per delivery year, quoted from D57 §4's ROWS, not its headline

D57 §4's table is indexed **by delivery year** and its governing panel is **arm A (UCAP basis)** —
the basis actually armed by D57 §8.1 (`pjm_accreditation_design_vintage` +
`pjm_demand_response_supply` + `capacity_market_supply_clearing_by_iso["PJM"]`, the "D48 basis:
UCAP through DY 2024/25, DR counted, pre-CIFP FPR" of §3.1). Arm B is HEAD's ELCC-class basis and
is **not** the armed configuration, so its rows do not govern.

Column quoted: *"units / firm MW **AT THE FULL BAR (zero E&AS)**"*.

| DY | D57 §4 arm-A row, verbatim | **DECLARED SET** |
|---|---|---|
| **2022/23** ($50.00) | `gas_ct 404 / 24,244 · gas_st 115 / 8,802 · oil 421 / 3,723 · gas_cc 40 / 1,145 · coal 2 / 30` | **{gas_ct, gas_st, oil}** |
| **2023/24** ($34.13) | `gas_ct 403 / 24,243 · gas_st 77 / 1,982 · gas_cc 1 / 73` | **{gas_ct, gas_st}** |
| **2024/25** ($28.92) | `oil 8 / 3,723` **(the CT fleet's 2024 margin is small but non-zero)** | **{oil}** |
| **2025/26** | **NO ROW EXISTS** — §4's arm-A panel stops at 2024/25 | **none — NOT EVALUABLE** |

**Two readings of that table are pre-committed here, because both could otherwise be made to
move later.**

1. **The set is CLASS-level, not unit-level.** `gas_cc 40 / 1,145` and `coal 2 / 30` in 2022/23,
   and `gas_cc 1 / 73` in 2023/24, are *partial* fleets — 40 of ~237 gas-CC units, 2 of ~188 coal
   — so those classes are not "at their bar"; a handful of their units are. They are **excluded**,
   which is the same reading D78-R2 §9 item 1 took. `gas_st 77 / 1,982` in 2023/24 is likewise
   partial (77 of 115) and is nonetheless **included**, because the handoff's (a) and D78-R2 §9
   item 1 both name it — and because including a class can only make W5″ **stricter**, never
   looser. The asymmetry is deliberate and is recorded now so it cannot be re-argued after a
   result.
2. **DY2025/26 has no published set.** D57 §3.1's 2025 row reads *"451.61 (164.84) = the cap …
   every offer clears"* — at the cap there is no crossing and §4 tabulated no at-bar set for it.
   Per the handoff's (a): **the window's last DY has no published set and W5″ is NOT evaluable
   there.** Its measurements are **REPORTED, never gated**.

**Delivery-year ↔ solve-year mapping**, fixed here from D57 §3.1's own `screen → DY` column
(`2022 → 2022/23`, `2023 → 2023/24`, `2024 → 2024/25`, `2025 → 2025/26`): the
`capacity_clearing` block of `evolution_<Y>.json` is DY **Y/Y+1**. The 2021 ledger carries an
**empty stack** (D78-R2 §5: *"2021 … ✓ (empty stack)"*), so there is no DY2021/22 and 2021 is
outside W5″ entirely.

## 2. (b) THE STRUCTURAL DERIVATION RULE — stated before any count is read

**The rule, verbatim from D78-R2 §9 item 2:** *a class sits at its full bar in DY iff every one of
its offers in the control's DY stack is the same value.*

Operationally, on the control leg's `capacity_clearing.offer_stack` rows
`(unit_id, fuel, offer_$/MW-day, A_g, cleared)`, restricted to the DY's stack and grouped by
`fuel`:

> **class C is DERIVED-AT-BAR in DY iff `n_distinct_exact(C, DY) == 1`**, where
> `n_distinct_exact` counts distinct `float` offer values under **exact IEEE-754 equality**.

**THE TOLERANCE, fixed now: exact float equality (byte-equal doubles) is the primary and only
deciding test.** A second count, `n_distinct_1e6` — distinct values after clustering at
**1 × 10⁻⁶ $/MW-day** — is computed and **REPORTED alongside**, never substituted. Where the two
counts disagree for a class, the **exact** count governs the derivation and the disagreement is
reported. (1e-6 is chosen to sit between the instrument's own `OFFER_TOL` = 1e-9 and any
plausible economically-meaningful offer difference; it is a reporting lens, not a gate.)

**The rule is ONE-SIDED, and that is pre-stated rather than discovered.** Class-uniformity is
*sufficient* evidence of a class at a uniform bar and is **not necessary**: a unit's bar is
`GFC_g / (A_g × 365)`, so a class every one of whose units sits at its own bar still shows
`n_distinct > 1` whenever `GFC_g` or `A_g` varies within the class. D78-R2 §5.1 already publishes
such a case — **gas_st, 3 distinct values, in a DY where D57 puts the whole class at the bar**.
Therefore:

- **the derived set is a LOWER BOUND on the at-bar set**;
- **a class failing to derive is NOT evidence against its declared status**; and
- **`derived ⊊ declared` is the EXPECTED outcome, not an anomaly.**

**THE SUBSET GUARD.** For every DY, `derived(DY) ⊆ declared(DY)` **must hold**. A class the
record does not put at its bar may **not** be admitted by the control's arithmetic alone. If the
derivation admits a class outside the declared set, that class is **NOT added** to the gate; the
excess is **REPORTED** as a finding about the derivation rule, and **the DECLARED set governs
W5″ regardless**. The declared set governs whether or not `derived == declared`.

**One second signal considered and DECLINED.** A unit at its bar reads no price vector, so its
offer could also be tested by invariance *across* DYs. It is not adopted: accreditation `A_g`
moves by DY under the D48 vintage design, so the bar moves too, and adding a selector of my own
invention to a pre-registration is precisely the latitude this lane exists to remove (rule 19,
one mechanism per phenomenon). The distinct-count rule is the sole derivation rule.

## 3. (c) W5″ — restated on the per-DY set

For each **evaluable** DY (one with a non-empty declared set, i.e. 2022/23, 2023/24, 2024/25):

- **GATED:** every **shared** row (a unit present in BOTH legs' stacks for that DY) whose `fuel`
  is in the DY's **declared** set has an offer delta between control and arm of **exactly zero**,
  at the instrument's own `OFFER_TOL` = **1e-9 $/MW-day**.
- **REPORTED, NEVER GATED:** every class **outside** the DY's declared set — moved and unmoved
  alike, with count and MW where recoverable. A mover outside the set is **not a failure**; it is
  the propagation account behaving as D57 §4 says it must.
- **VACUITY, fixed now:** a declared class with **zero shared rows** in a DY is **VACUOUS** — it
  neither passes nor fails. The DY's verdict is taken over its declared classes with ≥ 1 shared
  row, and every vacuity is reported. **If every declared class of a DY is vacuous, that DY is
  NOT EVALUABLE** and drops out of the conjunction exactly as DY2025/26 does.
- **Pass/fail is PER DY.** The **window verdict is the conjunction over the DYs where the
  declared set is non-empty AND at least one of its classes is non-vacuous.**

Structural limbs (`A_g` identical, `fuel` identical, no unknown fuel) are **not re-graded**: D78-R2
§5 measured them 0 / 0 / clean in all five years and they are not what this lane corrects.

## 4. (d) THE GRADE RULE — both sentences, written now

> **If W5″ PASSES on every evaluable DY**, then limbs (a)–(d) of D78-R2 §8 are **ALL MET** and
> this lane's recommendation is: **RECOMMEND ARM** — served to the owner as a director card,
> Q56.
>
> **If ANY evaluable DY FAILS**, this lane's recommendation is **HOLD**, and the FINDING names
> the failing class, its DY, and its moved-row count.

**No other outcome exists.** A partial pass, a "pass with reservations", or a re-weighting of the
DYs is not available to me. `retire.total_gw`, recall, precision, `false_retire` and every other
FC-3 metric are **NOT criteria in either direction** (rule 14) and are reported at full magnitude.

## 5. (e) WHERE THE STRUCTURE LIVES — enumerated BEFORE reading, and what the enumeration found

Every committed artifact that could carry a per-DY per-class **offer stack**, checked at
`0f7a4842` by `git ls-files` and by reading the code that writes each JSON. **Two of the three
artifacts the handoff names do not exist**, and one of those absences is not the one the handoff
anticipated:

| artifact | status at `0f7a4842` | carries a per-DY per-class offer stack? |
|---|---|---|
| `results/hindcast/pjm-2021-2025-realized-t1h-d78r2-control-P` (the CONTROL) | **ABSENT** — deleted before merge, rule 29(c), as D78-R2 §10 states | — |
| `results/hindcast/pjm-2021-2025-realized-t1h-d78r2-sectorgate` (the ARM) | **ABSENT — NEVER REGISTERED.** `git ls-files` returns nothing; `git log --diff-filter=A` on the path returns nothing; merge `80c88b76` (PR #5227) landed **10 files, docs and JSON only**. D78-R2 §11 deferred the registration to "after D65-B-R's batch registers" and it never landed. Only the scoring by-product `docs/hindcast-reports/…-d78r2-sectorgate-2026-09-06.md` is committed, and it carries score tables, not stacks. | — |
| `docs/handoffs/d78r2/control_band.json` | committed | **NO.** Written by `window_compare2.py --band-only` as `{"control": summarise(…), "w4_prime_band": …}` — per-year **sector aggregates** (decided rows/MW, sector-1 rows/MW) only. The handoff's assertion (director r#51 §0av.5(ii)) is **CONFIRMED**. |
| `docs/handoffs/d78r2/window_compare2.json` | committed | **NO stack, but MORE than sector aggregates.** `gates.W5prime.per_year[<y>]` carries `shared_rows`, `only_control_rows`, `only_arm_rows`, `offer_diff_rows`, `cleared_diff_rows`, `zero_eas_shared_rows`, `zero_eas_offer_diff_rows/units[:20]` and — decisively — **`offer_diff_by_fuel`, the per-fuel count of MOVED shared rows**. `gates.LEDGER…capacity_clearing` carries `stack_shared` / `stack_offer_movers` as totals. **No offer VALUES, no per-class shared counts, no distinct-offer counts.** |
| `results/hindcast/pjm-2021-2025-realized-t1h-d78-sectorgate` (D78-**R**'s arm, key `bb6a60239d69508b`) | committed, all five `evolution_*.json` (CORRECTION 1) | carries stacks — but it is a **sector-gate ARM**, at a **different code state** (guarded `99245361`, 19 files / +2,975 −54 behind on `retirements.py` / `capacity_market.py` / `adequacy.py`). **FORBIDDEN as a derivation base** (handoff 0(e): deriving on the arm's stack is forbidden; it is the object being graded). Not read. |
| other committed PJM bundles (`-realized`, `-d45r`, `-d57-clearing`, `-d62-pubbar`, `-d74-nodefaultcap`) | committed, with stacks | **NONE is the control recipe.** No committed bundle anywhere carries key **`a9c66d8ea25acb9d`** (checked: 0 matches in `git ls-files results/hindcast/`, 0 directories on disk). A different key is a different config is a different stack. |

### 5.1 Consequence 1 — the control-P re-solve is EARNED

**No committed artifact carries the control's per-DY per-class offer stack.** Under rule 29(b)'s
LIVE-hunk analogue — a **deleted derivation base** is the same species of obstacle as a live
solve-path hunk, and no zero-LP route reconstructs an LP-produced offer stack — the
**control-P re-solve is EARNED** as the derivation base:

```
bash docs/handoffs/d78r2/run_full.sh control-P      # bare pjm-t1h, key a9c66d8ea25acb9d
```

~21 min (D78-R2 §1: 19:20:30 → 19:41:33), PJM solo, years sequential (rule 12), HEAD guard on.
It is **DELETED BEFORE MERGE under rule 29(c)**, and every number this lane will ever cite from
it appears in this document's addendum or in the FINDING.

**A G-DRIFT audit is owed before it and is recorded in an ADDENDUM, not here**, because the
control I solve is at `0f7a4842` while the committed mover counts came from a control at
`65e12b21`: `git diff 65e12b21..0f7a4842 -- src/market_sim scripts/run_capacity_hindcast.py
scripts/lib data/raw/_validation-source data/raw/reference`, every hunk classified INERT with its
reason or LIVE.

### 5.2 Consequence 2 — W5″ is re-graded on the INSTRUMENT OUTPUT, and the ARM IS NOT RE-SOLVED

The handoff's step 2 names bundles; the bundles are gone. The re-grade therefore runs on the
**committed instrument output plus the merged documentary record**, which is exactly the
retention design rule 29(c) states (*"the PRECOMMIT / FINDING doc carries every number the
session will ever cite from such a bundle — the record is the doc, never the parquet"*):

| operand | source | rank |
|---|---|---|
| **moved shared rows, per fuel, per year** — the gate operand | `window_compare2.json` → `gates.W5prime.per_year[<y>].offer_diff_by_fuel` (a fuel **absent** from that dict has **zero** movers, by the dict comprehension's construction) | **PRIMARY**, machine-readable, committed |
| **shared rows, per fuel, per year** — needed to separate a real pass from a vacuity | `FINDING-capx-d78r2` §5.1's per-fuel table | documentary (rule 29(c)) |
| totals (`shared_rows`, `offer_diff_rows`, `zero_eas_*`) | `window_compare2.json` | cross-check on the two above |
| **max \|delta\| per class** | **NOT RECOVERABLE** — no committed artifact holds offer *values* for either leg, and the arm is not re-solved | reported as `null` **with that reason**, never estimated |

**`max_abs_delta` will be emitted as `null`.** It is reporting detail, not the verdict operand:
the gate is "delta exactly zero at 1e-9", which `offer_diff_rows` answers exactly. Fabricating or
back-filling it is not available.

**THE ARM IS NOT RE-SOLVED, under any circumstance** (handoff STOP gate; D78-R2 §9 item 3). If
the two sources above cannot support the re-grade, the lane **STOPs and routes** rather than
solving to make a grade possible.

### 5.3 The helper (declared here, as the handoff requires)

The derivation needs a read-only per-DY per-class distinct-offer census, which no committed
script emits. **`scripts/probes/d78r3_stack_census.py`** — read-only, reuses
`docs/handoffs/d78/screen_compare.py::stack_rows`, opens ledgers, writes JSON, touches no config
and no solve path. Declared now; kept under `scripts/probes/` per the handoff.

## 6. STOPs — every one fixed now

| # | STOP | on trip |
|---|---|---|
| **S1** | **G-CTL-ID.** The re-solved control must (i) realize key **`a9c66d8ea25acb9d`** and (ii) reproduce `control_band.json`'s aggregates — window decided **11,514.910 MW**, sector-1 decided **2,120.754**, `Σg_y` **1,003.400** (D78-R2 §4 / ADDENDUM 1 §2) — to **MW_TOL = 0.001**. | The derivation base is **not the same object** as the graded control. The derivation is reported **NOT TRANSFERABLE**; **W5″ is unaffected** (the declared set governs) and the lane still grades and recommends. |
| **S2** | **Source agreement.** `offer_diff_by_fuel` must be consistent with FINDING §5.1's published table for every fuel × year. | A disagreement between the committed JSON and the merged FINDING is a **STOP**: reported, routed, no verdict written. |
| **S3** | **HEAD guard.** `main` must not move under the control leg. | Leg discarded and re-solved; disclosed in an addendum, as D78-R2's ADDENDUM 2 did. No number from a guard-tripped leg is cited. |
| **S4** | **Unknown fuel.** A stack row carrying a fuel outside `FUEL_VOCAB` = {gas_cc, gas_ct, gas_st, gas_cc_ccs, coal, oil, nuclear}. | STOP — the partition's shape is not what the declaration assumes. |
| **S5** | **Scope.** Any diff outside `docs/`, `scripts/probes/`, and PJM's matrix shard. | Stop the line. |

**The derivation runs regardless of the W5″ verdict**, and vice versa: the two are ordered by
convenience, not by dependence, and neither result may be used to reshape the other. The derived
set never enters the gate (§2's subset guard); the W5″ verdict never re-opens the declaration.

## 7. Governance

**Rule 1 `[R-STRUCT]`** — every gate here is an identity or a record-quoted declaration; none is a
residual, and the recommendation turns on structure alone. **Rule 13/14** — no measured outcome is
fed back; the FC-3 metrics are reported at full magnitude and gate nothing. **Rule 19** — one
mechanism; the second derivation signal was considered and declined. **Rule 21 `[R-DOF]`** —
**zero DOF**: no parameter is set, identified or tuned. **Rules 24/25** — no tunable added or
changed; PJM's evidence only, PJM's shard only. **Rule 27** — every push touching a ≥ 300-line
file is blob-verified. **Rule 28(b)** — PJM's `retirement_sector_gate` cell's evidence citation is
updated in this session, in `mechanism-matrix/PJM.js` only. **Rule 29** — this document is pushed
**before any LP and before any per-DY per-class value is opened**; the G-DRIFT audit and the
control's realized key/aggregates go in an **ADDENDUM pushed before the grade they govern**; the
control bundle is **deleted before merge** (29(c)); STOP-only gates throughout.

## 8. Deliverables

1. this PRECOMMIT (pushed first, alone);
2. `docs/handoffs/d78r3/zero_eas_set.json` — per DY: `n_distinct_exact` and `n_distinct_1e6` per
   class, the derived set, the declared set, the subset check, and the artifact each was read
   from (plus the control's key / HEAD / wall, D78-R2 §1's form, if re-solved);
3. `docs/handoffs/d78r3/w5_regrade.json` — per DY per class: shared rows, moved rows,
   `max_abs_delta` (`null`, with reason), and the per-DY and window verdicts;
4. `FINDING-capx-d78r3-2026-09-06.md` — the per-DY table (declared vs derived vs measured), the
   W5″ verdict per DY, D78-R2 §8's limb table re-stated with (a) updated, and §4's recommendation
   sentence **verbatim**;
5. PJM's matrix shard cell evidence citation;
6. `scripts/probes/d78r3_stack_census.py`.

**Nothing arms. No default, no override, no `ScenarioConfig` field, no decision logic.**
