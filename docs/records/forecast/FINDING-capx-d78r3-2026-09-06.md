# FINDING — capx D78-R3: on the per-delivery-year set D57 actually published, W5″ PASSES in every evaluable delivery year — the last held limb falls, and the structural derivation both confirms it and exposes its own false-positive class

**Lane:** capx D78-R3 (director r#51/r#52, the successor D78-R2 §9 items 1–3 routed). **Date:**
2026-09-06. **Model:** Opus. **DATA PROFILE:** `pjm`. **Branch:** `claude/capx-d78r3-perdy-set`.
Pre-registration `PRECOMMIT-capx-d78r3-perdy-set-2026-09-06.md`, pushed at **`e79a4ddd`, merged to
`main` before any per-DY per-class value was opened**, with **ADDENDUM 1** (G-DRIFT) and
**ADDENDUM 2** (the rebase re-audit) each pushed **before the leg it governs**. Instrument
`scripts/probes/d78r3_stack_census.py`, declared in PRECOMMIT §5.3 before it was written.

**NOTHING ARMS.** `retirement_sector_gate` stays default-off and un-overridden for PJM. No
`ScenarioConfig` field added or changed, no default flip, no `_pjm_config` edit, no
`retirements.py` decision logic, no parameter value, no keeper, no marker, **zero DOF**. The lane's
entire output is a declaration, a derivation, a re-grade and a recommendation to the owner.

---

## 0. Verdict

**W5″ — the limb that held D78-R2 and D78-R — PASSES on every evaluable delivery year.** Graded on
the set `FINDING-capx-d57` §4's **rows** publish per delivery year, rather than the year-invariant
set its headline suggests:

| DY | declared set | gated shared rows | moved | verdict |
|---|---|---:|---:|:--:|
| **2022/23** | {gas_ct, gas_st, oil} | **943** | **0** | **PASS** |
| **2023/24** | {gas_ct, gas_st} | **403** (gas_st vacuous) | **0** | **PASS** |
| **2024/25** | {oil} | **8** | **0** | **PASS** |
| 2025/26 | — no published row — | — | — | **NOT EVALUABLE** |

**Window verdict: PASS.** With limbs (b), (c) and (d) already MET in D78-R2, **all four
flip-condition limbs are now MET**, and §4's pre-stated rule returns the recommendation in §5.

**Nothing measured changed between D78-R2's FAIL and this PASS — only the declaration did.** The
404 `gas_ct` rows that moved in 2024–2025 are the same 404; they now sit **outside** the 2024/25
declared set, exactly as D57's own row says they should (*"the CT fleet's 2024 margin is small but
non-zero"*). The 8 `oil` rows — the one class that row still puts at the full bar — moved by
exactly zero, in both years.

**The structural derivation confirms the reading and exposes its own defect.** On the re-solved
control's stacks, `gas_ct` carries **12 distinct offers while barred and 72 once live**, and its
barred range is **identical to four decimals across DY2022/23 and DY2023/24** — the direct
signature of a class whose offer reads no price vector. But the derivation rule **also admits
`nuclear` in every delivery year**, which no record puts at any bar: nuclear's offer is uniform
because it is **exactly $0 — a price taker**, not a unit at its net-ACR bar. The pre-registered
**subset guard caught it in all four DYs and refused it entry to the gate**. The rule is
one-sided *and* it has a false-positive class; both are reported at full magnitude.

**Two procedural events are disclosed rather than smoothed:** a mid-session rebase (at the owner's
request) landed **owner ruling Q55**, which arms PJM's VRE devintage and moves the bare `pjm-t1h`
key off the graded control's — so the control leg's recipe changed, publicly, in ADDENDUM 2 before
it ran; and the leg I had already started was **killed after ~1 minute and discarded** rather than
argued past my own pre-registration.

---

## 1. What was and was not spent

| | |
|---|---|
| **W5″ re-grade (step 2)** | **ZERO LP.** No bundle re-solved, neither leg. |
| **control-P leg (step 1's derivation base)** | `results/hindcast/pjm-2021-2025-realized-t1h-d78r3-control-P`, key declared `a9c66d8ea25acb9d` → **realized `a9c66d8ea25acb9d`**, HEAD guard `bb728e43` **HELD**, **22:27:18 → 22:42:25 UTC ≈ 15.1 min**. Solve years {2021, 2023, 2024, 2025}, 2022 bridged. PJM solo, years sequential (rule 12). `data/clean` absent at session start, rebuilt in full first: **56/56 datatypes, 0 failures**. |
| **arm** | **NOT re-solved.** Forbidden by the charter and by D78-R2 §9 item 3. |
| retention | the control bundle is **DELETED BEFORE MERGE** (rule 29(c)). |

**Why a leg at all — and why the ledger predicted it.** No committed artifact carries the
control's per-DY per-class offer stack. This is the capx ledger's own doctrine (ii), r#51 §0av.5:
*"A DELETED CONTROL IS A DELETED DERIVATION BASE … D78-R2's instruments carry sector aggregates;
D78-R3 pays for that."* Rule 29(b)'s LIVE-hunk analogue earns the leg.

**One correction to that doctrine, in its favour.** D78-R2's instruments carry **more** than
sector aggregates: `window_compare2.json`'s `gates.W5prime.per_year[y].offer_diff_by_fuel` records
the **per-fuel mover count**, which *is* the W5″ gate operand. So the **re-grade cost zero LP** and
only the *derivation* had to be paid for. The refinement the doctrine wants is therefore narrower
than it feared: name, before deletion, which committed instrument carries each structure — here
the mover counts survived and the distinct-offer census did not.

## 2. The two absences the enumeration found — one of them unanticipated

PRECOMMIT §5 enumerated every artifact that could carry a per-DY per-class offer stack, before any
value was opened. **Two of the three the handoff named do not exist:**

1. **The control-P bundle is gone** — deleted before merge under rule 29(c), as D78-R2 §10 states.
   Anticipated.
2. **The D78-R2 ARM WAS NEVER REGISTERED.** `git ls-files` on
   `results/hindcast/pjm-2021-2025-realized-t1h-d78r2-sectorgate` returns nothing;
   `git log --diff-filter=A` on the path returns nothing; **merge `80c88b76` (PR #5227) landed 10
   files, docs and JSON only**. D78-R2 §11 deferred the registration to "after D65-B-R's batch
   registers" and it never landed. Only the scoring by-product
   `docs/hindcast-reports/…-d78r2-sectorgate-2026-09-06.md` is committed. *(Reported to the
   director, who carried it into r#52.)*

Neither is a stop. Rule 29(c)'s retention design is exactly that **the doc, not the parquet, is
the record**, so the re-grade runs on the committed instrument output plus the merged FINDING
(§3.1). But the arm's non-registration is an **unexecuted duty of D78-R2**, not a retention
decision, and it is carried to the card in §5.2.

## 3. Step 2 — W5″ re-graded per delivery year (**PASS**)

### 3.1 What it was graded on, and the source check that had to clear first

| operand | source | rank |
|---|---|---|
| moved shared rows, per fuel, per year — **the gate operand** | `window_compare2.json` → `gates.W5prime.per_year[y].offer_diff_by_fuel` | PRIMARY, committed, machine-readable |
| shared rows, per fuel, per year — separates a real pass from a vacuity | `FINDING-capx-d78r2` §5.1's per-fuel table | documentary (rule 29(c)) |
| `max |delta|` per class | **NOT RECOVERABLE** | reported `null` with its reason, never estimated |

**STOP S2 (source agreement) CLEARS on three independent identities in all four years** — and it
is a real check, not a tautology, because the two sources were not copied from each other: one is
a per-fuel partition, the other its totals.

| year | Σ §5.1 per-fuel shared | `shared_rows` | Σ zero-E&AS part | `zero_eas_shared_rows` | Σ movers | `offer_diff_rows` |
|---|---:|---:|---:|---:|---:|---:|
| 2022 | **1,399** | 1,399 ✓ | **943** | 943 ✓ | **0** | 0 ✓ |
| 2023 | **849** | 849 ✓ | **403** | 403 ✓ | **0** | 0 ✓ |
| 2024 | **835** | 835 ✓ | **412** | 412 ✓ | **679** | 679 ✓ |
| 2025 | **821** | 821 ✓ | **412** | 412 ✓ | **619** | 619 ✓ |

### 3.2 The grade, per delivery year

Delivery-year mapping from D57 §3.1's own `screen → DY` column. `max |delta|` is `null` throughout
for the reason above.

| DY (screen) | declared set | class | in set | shared | moved | status |
|---|---|---|:--:|---:|---:|:--:|
| **2022/23** (2022) | {gas_ct, gas_st, oil} | gas_ct | ✓ | 404 | **0** | **PASS** |
| | | gas_st | ✓ | 118 | **0** | **PASS** |
| | | oil | ✓ | 421 | **0** | **PASS** |
| | | coal / gas_cc / nuclear | — | 188 / 237 / 31 | 0 / 0 / 0 | reported |
| | | | | **943 gated** | **0** | **DY PASS** |
| **2023/24** (2023) | {gas_ct, gas_st} | gas_ct | ✓ | 403 | **0** | **PASS** |
| | | gas_st | ✓ | **0** | 0 | **VACUOUS** |
| | | coal / gas_cc / nuclear | — | 184 / 231 / 31 | 0 / 0 / 0 | reported |
| | | | | **403 gated** | **0** | **DY PASS** |
| **2024/25** (2024) | {oil} | oil | ✓ | 8 | **0** | **PASS** |
| | | **gas_ct** | — | 404 | **404** | **reported, not gated** |
| | | coal / gas_cc / nuclear | — | 180 / 212 / 31 | 180 / 95 / 0 | reported |
| | | | | **8 gated** | **0** | **DY PASS** |
| **2025/26** (2025) | — none published — | oil | — | 8 | **0** | reported |
| | | gas_ct / coal / gas_cc / nuclear | — | 404 / 166 / 212 / 31 | 404 / 163 / 52 / 0 | reported |
| | | | | — | — | **NOT EVALUABLE** |

**Window verdict = conjunction over {2022/23, 2023/24, 2024/25} = PASS.**

Three things are worth naming rather than leaving to inference:

- **`gas_st` in DY2023/24 is VACUOUS, not passed.** It has zero shared rows: under D74's
  no-default-cap convention Steam Oil & Gas leaves the screened stack after 2022 (§4.3 shows it
  absent from the control's 2023/24 stack entirely). D57's 2023/24 row lists `gas_st 77 / 1,982`
  because D57 ran before D74. The vacuity convention was fixed in PRECOMMIT §3 before any value
  was read, and the DY's verdict rests on `gas_ct`'s 403 rows.
- **DY2025/26 is reported, never gated.** D57 §4's arm-A panel stops at 2024/25 — its §3.1 2025 row
  is at the price cap where every offer clears, so no at-bar set was tabulated. **Reported anyway,
  because it is corroborating and costs nothing:** past the table's edge, `oil` — the last class
  D57 put at the bar — still moves by **exactly zero** (8 shared rows), while `gas_ct` moves in all
  404.
- **The 404 movers are not excused, they are relocated.** D78-R2's gate failed because
  `{gas_ct, gas_st, oil}` was applied to 2024/25, where D57's own row names only `oil`. The
  measurement is identical in both grades. What changed is which document sentence the gate was
  built from — its §4 table, not its §0/§8.1 headline.

## 4. Step 1 — the structural derivation on the control (D78-R2 §9 item 2)

**The rule, fixed in PRECOMMIT §2 verbatim from D78-R2 §9 item 2:** *a class sits at its full bar
in DY iff every one of its offers in the control's DY stack is the same value*, decided on **exact
IEEE-754 equality**, with a 1e-6 $/MW-day clustering count reported beside it.

### 4.1 S1 (G-CTL-ID) — the derivation base IS the graded control, byte-for-byte

| limb | required | measured |
|---|---|---|
| key | `a9c66d8ea25acb9d` | **`a9c66d8ea25acb9d`** ✓ |
| `control_band.json` reproduction | 11,514.910 / 2,120.754 / 1,003.400 to `MW_TOL` | **BYTE-IDENTICAL — sha256 `509320eb4d3de316` on both sides**, every per-year `decided_mw` / `sector1_decided_mw` / `capped_mw` / `cap_binds` / `g_y_mw` row and every aggregate |

The re-solved control reproduces D78-R2's control — solved at `65e12b21`, **165 commits earlier** —
**exactly**. That is an empirical confirmation of both G-DRIFT audits from a different direction
than the code argument, in the form D78-R2's own ADDENDUM 1 §5 obtained across 45 commits. *(The
committed instrument was restored after the comparison and is unmodified — verified.)*

### 4.2 The census

Distinct offer values per class per DY, on the control's own stack. **The exact and 1e-6 counts
never disagree anywhere** — so the tolerance choice was immaterial and could not have been tuned.

| DY | class | rows | distinct | offer range $/MW-day | at bar? | declared? |
|---|---|---:|---:|---|:--:|:--:|
| **2022/23** | oil | 421 | **1** | 76.1035 | **✓** | ✓ |
| | gas_st | 118 | 3 | 103.0421 – 103.1080 | ✗ | ✓ |
| | gas_ct | 404 | **12** | **56.4069 – 61.2066** | ✗ | ✓ |
| | nuclear | 31 | **1** | **0.0000** | **✓** | ✗ |
| | gas_cc | 237 | 18 | 0.0000 – 86.5177 | ✗ | ✗ |
| | coal | 188 | 39 | 0.0000 – 174.2108 | ✗ | ✗ |
| **2023/24** | gas_ct | 403 | **12** | **56.4069 – 61.2066** | ✗ | ✓ |
| | nuclear | 31 | **1** | 0.0000 | **✓** | ✗ |
| | gas_cc | 231 | 18 | 0.0000 – 86.5177 | ✗ | ✗ |
| | coal | 184 | 36 | 0.0000 – 174.2108 | ✗ | ✗ |
| | *(gas_st, oil absent from the stack)* | 0 | — | — | — | — |
| **2024/25** | oil | 8 | **1** | 76.1035 | **✓** | ✓ |
| | **gas_ct** | 404 | **72** | **28.4045 – 53.8697** | ✗ | ✗ |
| | nuclear | 31 | **1** | 0.0000 | **✓** | ✗ |
| | gas_cc | 212 | 12 | 0.0000 – 75.4453 | ✗ | ✗ |
| | coal | 180 | 60 | 53.9294 – 170.0782 | ✗ | ✗ |
| **2025/26** | oil | 8 | **1** | 75.2672 | ✓ | — |
| | gas_ct | 404 | **72** | 8.2165 – 66.5935 | ✗ | — |
| | nuclear | 31 | **1** | 0.0000 | ✓ | — |
| | gas_cc | 212 | 9 | 0.0000 – 79.7588 | ✗ | — |
| | coal | 166 | 48 | 0.0000 – 173.7367 | ✗ | — |

**This independently reproduces every distinct-offer count D78-R2 §5.1 published** (oil 1,
nuclear 1, gas_st 3, gas_ct **12 → 72**) from my own control leg.

**The sharpest structural result is the one D78-R2 could not see, because it did not have the
range.** `gas_ct`'s barred offers are **`56.4069 – 61.2066` in DY2022/23 and the identical
`56.4069 – 61.2066` in DY2023/24**, across 12 distinct values in both — then **72 values over
`28.4045 – 53.8697`** in 2024/25 and **72 over `8.2165 – 66.5935`** in 2025/26. A class at its bar
reads no price vector, so its offers cannot move between delivery years; a class with a live E&AS
operand must. **The barred years are byte-identical and the live years are not.** That is D57
§4's per-DY reading confirmed structurally, from the model's own stack, with no reference to the
arm.

An external cross-check falls out of it: the control's oil plateau is **76.1035 $/MW-day =
27.7778 $/kW-yr = 25 ÷ 0.90**, which is *exactly* D57 §3.1's 2022 marginal offer, **"$76.10
(27.78) · an oil unit (the oil plateau, 25 ÷ 0.90)"**. The stack this lane derives on is the same
population D57 tabulated, and the DY mapping is right.

### 4.3 The subset guard fired in every DY — and it caught a real false positive

| DY | derived | declared | subset holds? | in derived, not declared | in declared, not derived |
|---|---|---|:--:|---|---|
| 2022/23 | {nuclear, oil} | {gas_ct, gas_st, oil} | **NO** | **nuclear** | gas_ct, gas_st |
| 2023/24 | {nuclear} | {gas_ct, gas_st} | **NO** | **nuclear** | gas_ct, gas_st |
| 2024/25 | {nuclear, oil} | {oil} | **NO** | **nuclear** | — |
| 2025/26 | {nuclear, oil} | — none — | **NO** | nuclear, oil | — |

**`nuclear` derives at bar in every delivery year and belongs at none.** Its offers are uniform
because they are **exactly $0.0000** — it is a **price taker**, not a unit sitting at its net-ACR
bar. Uniformity is produced by two different mechanisms and the rule cannot tell them apart. Per
PRECOMMIT §2, **`nuclear` was NOT admitted to the gate**; the DECLARED set governed W5″ in every
DY, and the excess is reported here. *(In DY2025/26 `oil` appears as "excess" only because the
declared set is empty there — it is the same at-bar oil class, not a second false positive.)*

**The one-sidedness was pre-stated and is confirmed**: `gas_ct` (12 distinct while barred) and
`gas_st` (3) fail to derive in DYs where D57 puts them at the bar, because a unit's bar is
`GFC_g / (A_g × 365)` and both `GFC_g` and `A_g` vary within a class. **The derived set is a lower
bound on the at-bar set, and a class failing to derive is not evidence against its declared
status.**

**What this means for D78-R2 §9 item 2's proposal, stated plainly.** Item 2 offered the derivation
as the *better* route — *"derive it structurally on the CONTROL leg … rather than a literature
quotation."* **On this measurement it is not a replacement.** It is silent on `gas_ct` and
`gas_st`, the two classes that actually decide 2022/23 and 2023/24, and it *volunteers* a class no
record supports. What it does well is **corroborate**: the `12 → 72` fan-out and the identical
barred range are strong, independent, arm-free evidence for exactly the per-DY reading the
declaration takes. **The declaration leads and the derivation corroborates** — which is why the
PRECOMMIT gave the declared set the gate and the derivation the report, before any of this was
visible.

## 5. The flip condition, re-stated with (a) updated (D78-R2 §8)

| limb | condition | D78-R2 | **D78-R3** |
|---|---|---|---|
| **(a) purity** | W5″ on the window | **FAIL** — year-invariant set applied to a per-DY table | **MET** — PASS in all three evaluable DYs; 1,354 gated shared rows, **0 moved**; every mover outside the DY's declared set (§3.2) |
| **(b) fidelity** | W1 + W2 + W3 | MET | **MET** *(carried; D78-R2 §3 — pool falls by exactly the sector-1 rows in every year, arm-only set empty, zero sector-1 rows in any decision ledger, whole-ledger diff zero unclassified rows)* |
| **(c) composition** | window `economic` precision ≥ control's, every row non-sector-1 | MET | **MET** *(carried; 0.122 → 0.146)* |
| **(d) LOYO** | no fold lost that the control holds | MET, non-discriminating on recall | **MET, and still non-discriminating on recall** *(carried; the control holds no recall-PASS fold — ADDENDUM 1 said so before the arm ran. `tr10a`/`tr10b` PASS on all three folds in both legs and do discriminate.)* |

**W4′ and the whole-ledger diff are STOPs, not limbs**: both PASSED in D78-R2 (the arm landed on
the pre-registered point value `9,394.156` to the milli-MW; zero unclassified rows in five years
and every block), so neither kills, and by construction neither promotes.

**Limbs (b), (c) and (d) are CARRIED from D78-R2, not re-measured.** That is what D78-R2 §9 item 3
chartered, and this lane re-graded (a) alone. **S1 is what makes the carry sound**: the control
those limbs were measured against reproduces byte-for-byte here, 165 commits later.

### 5.1 §4's pre-stated rule, applied

PRECOMMIT §4, written before any value was opened: *"If W5″ PASSES on every evaluable DY, then
limbs (a)–(d) of D78-R2 §8 are ALL MET and this lane's recommendation is: RECOMMEND ARM — served
to the owner as a director card, Q56."*

# **RECOMMENDATION: RECOMMEND ARM.** Serve as owner card Q56.

`retirement_sector_gate` for PJM, armed the D57/Q44 / D67-ARM / Q55 way — through
`iso_configs.py::_pjm_config` `default_scenario_overrides`, never a shared `ScenarioConfig`
default flip, so every other ISO and every backcast keeper stays byte-identical and an explicit
`--no-retirement-sector-gate` keeps the pre-arm key. **Nothing arms in this lane.**

### 5.2 What the card must state, at full magnitude

1. **The evidence for limbs (b)–(d) rests on an arm bundle that is not committed anywhere.** The
   D78-R2 arm was never registered (§2). Its numbers survive in the merged FINDING, the committed
   `window_compare2.json`, and the hindcast report — which is rule 29(c)'s standard for a
   *deleted* bundle, but the arm was meant to be *registered*. **The arming lane closes this by
   construction**, since arming means solving and registering PJM T1-H on the new default; the
   card should require that, not waive it.
2. **`retire.total_gw` moved FAIL → PASS** (18.058 → 15.937 against 15.062 actual). It is
   **explicitly not a criterion in either direction** (rule 14) and is *not* an argument for
   arming — it is a consequence of removing candidates from a control that over-retires. A worse
   number would not have been an argument against.
3. **`unit_recall_gt300` FALLS** 0.650 (13/20) → 0.550 (11/20). A partition that removes matched
   sector-1 exits must lose recall. Reported; not a criterion.
4. **The 2025 clearing price moves a long way** — 358.267 → 236.945 $/MW-day — because the
   control's cleared position (0.998023) sits *short* of the requirement on the steep VRR limb and
   the arm's extra 1,671.625 MW carries it to 1.009595. Reported; not a criterion.
5. **Limb (d) cannot discriminate on recall** in either leg (the control holds no recall-PASS
   fold). The card should not read (d) as positive evidence.
6. **This lane did not re-measure (b), (c) or (d)**, and it did not solve the arm.

## 6. Reported at full magnitude, never gated (rule 14)

Carried from D78-R2 §7 unchanged; nothing in this lane re-measures them, and none is a criterion.

| quantity | control-P | arm |
|---|---|---|
| FC-3 `retire.total_gw` (actual 15.062) | 18.058 · err 0.199 · FAIL | 15.937 · err 0.058 · PASS |
| `unit_recall_gt300` | 0.650 (13/20) · FAIL | 0.550 (11/20) · FAIL |
| `plant_recall_frac` | 0.700 (14) | 0.700 (14) |
| `false_retire` | 8.065 GW · 0.447 · FAIL | 7.166 GW · 0.450 · FAIL |
| window `economic` release precision | 0.122 | **0.146** |
| window executed economic MW | 11,514.910 | 9,394.156 |

## 7. Governance attestation, limitations, retention

**Rule 1 `[R-STRUCT]`** — every gate is an identity, a record-quoted declaration or a
control-derived census; none is a residual, and the recommendation turns on structure alone. The
one metric that improved is explicitly excluded. **Rule 12** — PJM solo, one leg, years
sequential. **Rules 13/14** — no measured outcome fed back; every FC-3 metric reported at full
magnitude and gating nothing. **Rule 19** — one derivation rule; a second signal (cross-DY offer
invariance) was considered and **declined in the PRECOMMIT**, before the census showed it would
have worked. **Rule 21 `[R-DOF]`** — **zero DOF**; no parameter set, identified or tuned.
**Rules 24/25** — no tunable added or changed; PJM's own evidence, PJM's shard only. **Rule 26** —
nothing deprecated-but-parseable introduced. **Rule 27** — every push touching a ≥300-line file
blob-verified against local (the probe, 445→493 lines: remote/local line count and sha256 matched).
**Rule 28(b)** — PJM's `retirement_sector_gate` cell evidence updated in this session, `PJM.js`
only. **Rule 29** — the PRECOMMIT pushed before any per-DY per-class value was opened; both
addenda pushed before the leg they govern; STOP-only structural gates; the control bundle deleted
before merge (29(c)); the arm never re-solved.

**Stated limitations.**
1. **The derivation rule has a FALSE-POSITIVE CLASS** — price takers at $0 (`nuclear`, all four
   DYs). Caught by the subset guard, never admitted. §4.3.
2. **The derivation is one-sided and silent on the two classes that decide 2022/23 and 2023/24**
   (`gas_ct`, `gas_st`). It corroborates the declaration; it does not replace it. §4.3.
3. **`max |delta|` per class is not recoverable** — no committed artifact holds offer values for
   either leg and the arm was not re-solved. Emitted `null` with its reason; the gate operand
   (mover count) is unaffected.
4. **Limbs (b), (c), (d) are carried from D78-R2, not re-measured** (§5), and the arm bundle they
   rest on is unregistered (§2, §5.2 item 1).
5. **A leg was killed and discarded.** I started the bare control before the rebase re-audit was
   written; it was killed after ~1 minute, its partial bundle deleted, and **no number from it is
   cited**. It would in fact have been the wrong control (ADDENDUM 2 §2).
6. **Owner ruling Q55 changed the leg's recipe mid-lane.** The bare `pjm-t1h` recipe now keys
   `b518f5fe7d02f961`; the graded control needs `--no-pjm-vre-accreditation-vintage`
   (`a9c66d8ea25acb9d`). **This lane takes no position on Q55** — it needs the control that
   produced the graded comparison, nothing more.
7. **`git push` failed repeatedly over HTTP/2** and succeeded first-try on HTTP/1.1, as CLAUDE.md
   §Git documents. No `push_files` fallback was taken, so no ≥300-line file was stranded.
8. **RSS not captured** (`/usr/bin/time` absent), as in D78 / D78-R / D78-R2.

**Retention (rule 29(c)).** `results/hindcast/pjm-2021-2025-realized-t1h-d78r3-control-P` is
**deleted before merge**. Every number this lane will ever cite is in this document, the PRECOMMIT
with its two addenda, and `docs/handoffs/d78r3/{zero_eas_set,w5_regrade}.json`.

## 8. Matrix (rule 28) and what is routed on

- PJM's `retirement_sector_gate` cell stays **`O`** with this finding appended — the lane
  recommends, it does not arm, so the cell moves only when the owner rules.
  `mechanism-matrix/PJM.js` only; no other shard (rule 25).
- **Routed to the director:** (i) the arming card, Q56, with §5.2's six statements on its face;
  (ii) **the D78-R2 arm's non-registration**, already carried into r#52 — the arming lane closes
  it by solving and registering on the new default; (iii) a refinement to the ledger's doctrine
  (ii): a PRECOMMIT that names, before deletion, *which* structure each surviving instrument
  carries — here the mover counts survived (saving the re-grade entirely) and the distinct-offer
  census did not (costing 15.1 min).

## 9. Reproduction

```
uv run python scripts/probes/d78r3_stack_census.py --regrade          # zero LP
bash docs/handoffs/d78r3/run_ctl.sh                                   # ~15 min
uv run python docs/handoffs/d78r2/window_compare2.py \
    --ctl results/hindcast/pjm-2021-2025-realized-t1h-d78r3-control-P --band-only   # S1
uv run python scripts/probes/d78r3_stack_census.py --census \
    --ctl results/hindcast/pjm-2021-2025-realized-t1h-d78r3-control-P
```
