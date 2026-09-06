# FINDING — pjm-168: the two pjm-167 screens, run. F1 is KILLED by G3; F2 CLEARS 6/6.

**Session:** pjm-168 · **Date:** 2026-09-06 · **HEAD:** `b5925d26`
**Branch:** `claude/pjm-calibration-f1-f2-screens-x34r7s`
**Keeper:** `2026-08-15-pjm-162-inputclock` (`pjm_debugb_inputclock_A`) — **UNCHANGED, not promoted**
**Base bundle (replayed):** `pjm_tp2022_2021_k162` (touchpoint `2026-09-05-pjm-2022-2021-touchpoints`)
**PRECOMMITs executed:** `docs/handoffs/PRECOMMIT-pjm167-fleet-vintage-screen-2026-09-06.md` (F1, G1–G7)
and `docs/handoffs/PRECOMMIT-pjm167-interface-feed-admissibility-2026-09-06.md` (F2, H1–H6)

Rule 29 `[R-SCREEN]` bundles. **Never registered, deleted before merge** (clause c) — every number
this session will ever cite is in this document.

---

## 0. The answer

> **F1 (`eia860_vintage_tracks_solve_year`) does exactly what it claims to the fleet, and is
> KILLED by its own pre-registered gate G3.** Six of seven gates pass, G1 to the megawatt. G3
> fails because the +9,986 MW of restored coal nameplate produced **no headroom**: the model
> converted it into **+9,342 MW of additional peak coal dispatch and +29.18 TWh**, and stayed
> pinned at **95.0 %** of its (now larger) ceiling against the 95.4 % it started at.
>
> That is not "the diagnosis was wrong about the fleet" — the fleet defect is real and measured.
> It is **the diagnosis was wrong about what BINDS**. PJM 2021 is not coal-capacity-bound; the
> model runs coal to whatever rail it is given. With the correct 2021 registry it now **overshoots
> the metered coal peak by +3,619 MW** (46,297 vs EIA-930's 42,678) and overshoots two of the
> three coal benchmark bases on energy. The object is the **coal-vs-gas offer ordering**, not the
> registry — which is precisely the F4 hypothesis (`gas_offer_margin_anchor` extrapolation),
> still unbuilt.
>
> **Rule 16 `[R-ALLYEARS]` + rule 29 both independently bar promoting F1 here**: it is a
> one-year screen bundle, and PRECOMMIT F1 §5's step 2 (the protective 2023–2025 in-sample
> re-solve, scored leave-one-year-out) was **never spent**, because the kill rule forbids it.
>
> **F2 (`pjm_interface_feed_admissibility_gate`) CLEARS its screen 6/6** and is the session's
> live result. It removes the EMAAC VOLL artifact **entirely** (99,100 MWh over 74 h → **0**),
> collapses the inverted east–west wedge (+$20.95 → **+$1.21**, actual −$5.43), flips C3b
> FAIL → PASS, flips no gated criterion, and is **bit-identical on the keeper's own 2023** —
> so arming it cannot move PJM's calibration determination, only repair its held-out years.
> **A cleared screen promotes nothing** (rule 29): it earns the next step, which is an owner
> decision, not this session's.

**The environment blocker recorded in pjm-167 §9 and PRECOMMIT F2 §6 is BROKEN, not worked
around** — see §4. Both screens solved on a 16 GB box.

---

## 1. F1 — the gate table, at full magnitude

Arm vs control, **same HEAD `b5925d26`**, 2021 only, both solved this session (PRECOMMIT §3 earns
a same-HEAD control; the G-DRIFT audit was undischargeable at 59 files / +9,088 lines).

| # | gate | pass condition | measured | verdict |
|---|---|---|---|---|
| **G1** | fleet identity | arm COAL registry 48,708 ±1 MW; control 38,722 ±1 | **arm 48,708.3 / control 38,722.3** | **PASS** |
| **G2** | direction & order of magnitude | coal peak rises ≥2,000 and ≤9,986 MW | **36,955 → 46,297 = +9,342** | **PASS** |
| **G3** | ceiling released | arm dispatched coal peak / registry pmax **< 90 %** | **95.0 %** (control 95.4 %) | **FAIL** |
| **G4** | phantom capacity gone | arm `ST_GAS` peak ≤ 7,411 MW | **5,968** (control 8,692 = 117.3 %) | **PASS** |
| **G5** | footprint confined | nuclear/wind/solar/hydro/biomass/OTHER each < 1.0 % | largest **nuclear −0.11 %** | **PASS** |
| **G6** | no non-target load-bearing flip | C2, C4 not PASS → FAIL | `sysvol` PASS→PASS, `dispatch_corr` PASS→PASS | **PASS** |
| **G7** | EMAAC not made worse | arm slack MWh ≤ control | **74,165 ≤ 99,100** (74 h → 56 h) | **PASS** |

**KILL RULE APPLIED (PRECOMMIT §4): G3 fails ⇒ the arm is dead, and the remaining years are
never spent.** Step 2 was NOT run. Nothing is promoted.

### 1.1 The G1 census reproduces FINDING-pjm167 §3.3 exactly, inside the solve path

Zero-LP, `run_year(fleet_only=True)` on the bundle's own recipe
(`scripts/probes/_pjm168_f1_fleet_census.py`; artifact
`results/calibration/_pjm168_f1_census_2021.json`):

| class (MW) | control | arm | Δ | pjm-167 §3.3 predicted Δ |
|---|---|---|---|---|
| **COAL** | 38,722.3 | **48,708.3** | **+9,986.0** | +9,986 ✅ |
| CC_REGULAR | 59,856.9 | 54,600.4 | −5,256.5 | −5,256 ✅ |
| ST_GAS | 11,111.2 | 7,410.6 | −3,700.6 | −3,701 ✅ |
| CT_PEAKER | 25,988.8 | 25,223.0 | −765.8 | −766 ✅ |
| **TOTAL** | 210,817.1 | 210,751.1 | **−66.0** | −66 ✅ |

The solve path confirms it independently: the control loads **1,922 generators** in every year
(the frozen 2025 Early Release), the arm loads **2,124** — the year-matched `vintage_2021`
registry — and the downstream objects move with it (194 → 196 ramp groups, 1,332 → 1,389 member
tranches, 37.5 → 39.3 GW deliverable ramp).

### 1.2 Why G3 fails, and what it means

G3's pre-registered rationale: *"the claim is that 2021 is capacity-bound; if the ratio stays
pinned the diagnosis is wrong."* It stayed pinned.

| | control | arm | actual |
|---|---|---|---|
| dispatched coal peak MW | 36,955 | **46,297** | **42,678** (EIA-930 metered) |
| peak / own registry pmax | 95.4 % | **95.0 %** | — |
| coal TWh | 152.27 | **181.45** | 930 **183.55** · classFull **165.22** · CEMS **157.16** |

pjm-167 §3.4 predicted the ratio would fall to 75.9 % — that arithmetic held the *dispatch* peak
fixed at 36,955 and divided by the bigger registry. The model did not behave that way: it spent
almost the whole restoration. Model − actual coal energy moves **−31.28 → −2.10 TWh** on EIA-930,
but **−12.95 → +16.23** on `classFull` and **−4.89 → +24.28** on CEMS. Which way F1 "improves"
coal is therefore **basis-dependent** — the same three-bases trap pjm-158 recorded and pjm-167 §6
re-flagged. Only the 930 basis (which C2 scores against) reads as a near-perfect fix; on the other
two the arm is a large new overshoot.

### 1.3 Reported only — NOT gated, and not a promotion argument

Reading any of these as a pass condition is the fitted-mechanism selection rule 1 `[R-STRUCT]`
forbids (PRECOMMIT §4). They are recorded because the owner's standing rule for this lane requires
the structural case be put beside the gate table.

| quantity (2021) | control | arm | actual |
|---|---|---|---|
| load-weighted RT LMP | $48.43 | **$44.44** | $38.53 (`bench.avgLMP.rt_lw`) |
| C3a error | +25.7 % | **+15.3 %** | — |
| `CC_REGULAR` TWh | 307.92 | 295.24 | 279.20 (`classFull`) |
| `ST_GAS` TWh | 11.87 | 6.90 | 3.79 |
| `CT_PEAKER` TWh | 15.68 | 11.05 | 20.63 |
| GAS family TWh | 346.51 | 322.77 | 930 311.74 · classFull 313.04 |
| EMAAC slack | 99,100 MWh / 74 h | 74,165 MWh / 56 h | 0 |

Three of the four C1 classes move in the sign pjm-167 §3.4 predicted; `CT_PEAKER` moves the wrong
way, as §3.4 also predicted (❌ there), and worsens from −5.0 to −9.6 TWh against `classFull`.

---

## 2. F2 — the interface-feed admissibility gate

**The gate fires exactly as pre-registered, before any dispatch is read.** At the declared
`PJM_INTERFACE_FEED_MAX_EXCEEDANCE_FRAC = 0.05` bar (PRECOMMIT F2 §2, never swept), the 2021 solve
drops precisely the two consumed series §3 named and no others, loudly:

- `Average Eastern` — 27.9 % of 8,759 covered hours exceed the posted limit, by up to 5,242 MW,
  85 distinct values ⇒ dropped from `PJM_Central_PA→PJM_EMAAC`, **and** the joint
  `pjm_east_interface_cut` is NOT APPLIED for the year (links keep static per-link TTCs — the
  forecast-lane posture).
- `Average Western` — 6.7 %, up to 3,885 MW ⇒ dropped from `PJM_AEP_Ohio→PJM_West_APS`.

This is the recorded, non-silent fall-through pjm-119 requires. **F2 rides on the CONTROL, not on
F1**, because F1 is dead — PRECOMMIT F2 §5's "F2 on top of whatever F1 leaves" degenerates to
"F2 on top of the control", and the confound the ordering existed to avoid is gone.

### 2.1 The F2 gate table

Arm vs the SAME control bundle as F1 (`pjm168_vintage_ctrl` — both gates off, so one control
serves both screens), same HEAD, 2021.

| # | gate | pass condition | measured | verdict |
|---|---|---|---|---|
| **H1** | the identity it asserts | the two named series dropped, every other mapped series byte-identical | **exactly 3 log-line removals**; the other four mapped series identical to the MW (see below) | **PASS** |
| **H2** | the artifact is gone | arm EMAAC slack **= 0 MWh** | **0 MWh** (control 99,100 over 74 h) | **PASS** |
| **H3** | direction | arm EMAAC−rest wedge **< +$10/MWh** | **+$1.21** (control +$20.95) | **PASS** |
| **H4** | footprint confined | non-EMAAC zones <2 %; nuclear/wind/solar/hydro <1 % | largest **+0.00 %** | **PASS** |
| **H5** | no non-target load-bearing flip | C1, C2, C4 not PASS → FAIL | `fuelmix` FAIL→FAIL, `sysvol` PASS→PASS, `dispatch_corr` PASS→PASS | **PASS** |
| **H6** | in-sample inertness | a 2023 arm bit-identical to the keeper's committed 2023 `hourly/` | **bit-identical, max\|Δ\|=0 on all 4 sidecars** (§2.3) | **PASS** |

**F2 CLEARS ITS SCREEN.** Under rule 29 a cleared screen **promotes nothing** — it means the arm
is not killed and has earned the next step.

**H1 in full.** Diffing the interface-cap log lines control → arm gives exactly three removals and
nothing else:

- `Average Western` dropped from `PJM_AEP_Ohio→PJM_West_APS` (was hourly 3,513–5,536, mean 4,255)
- `Average Eastern` dropped from `PJM_Central_PA→PJM_EMAAC` (was hourly 4,971–7,526, mean 5,908)
- the joint EAST interface cut on 4 links NOT APPLIED (was the same 4,971–7,526 envelope)

The four other mapped series are **byte-identical** — `AEP/DOM Post-Contingency` (0–5,893, mean
3,140), `Average Central` (2,589–3,615, mean 2,965), `Bedington-BlackOak Pre min Post`
(0–2,338, mean 1,679), `AP-South Pre min Post` (1,810–6,589, mean 4,108) — same statics on the
reverse directions. The P0 objective falls 11.338e9 → 11.088e9, the sign a released binding
constraint must have.

### 2.2 Reported only — NOT gated (C3a/C3b are the TARGETS, PRECOMMIT F2 §4)

| quantity (2021) | control | F2 arm | actual |
|---|---|---|---|
| EMAAC slack | 99,100 MWh / 74 h | **0 MWh / 0 h** | 0 |
| EMAAC − rest wedge | +$20.95 | **+$1.21** | −$5.43 (NJ Hub − AEP-Dayton) |
| C3b `price_shape` | **FAIL** | **PASS** | — |
| C1 / C2 / C4 | FAIL / PASS / PASS | FAIL / PASS / PASS | — |

C3b flipping FAIL → PASS is a **target** improving, not a gate — recorded, never a pass condition.

*(Instrument note: the +$20.95 control wedge is an unweighted mean of hourly (mean EMAAC price −
mean non-EMAAC price); pjm-167 §2.3's +$34.50 uses a different aggregation. The two estimators
disagree on level and agree on sign and collapse, and H3's threshold binds on the ARM.)*

### 2.3 H6 — in-sample inertness, proved twice

**Zero-LP, decisive.** `interface_series_admissibility` evaluated on the committed clean
partitions for every series the model consumes (`constants.PJM_INTERFACE_LINK_MAP`), exceedance %:

| series | 2021 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| Average Eastern | **27.9\*** | 2.1 | 0.0 | 0.0 |
| Average Western | **6.7\*** | 0.5 | 0.0 | 0.0 |
| Average Central | 1.2 | 0.0 | 0.0 | 0.0 |
| AEP/DOM Post | 0.0 | 0.0 | 0.0 | 0.0 |
| AP-South Pre / Post | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| Bedington-BlackOak Pre / Post | 0.9 / 0.6 | 0.5 / 0.0 | 1.0 / 0.0 | 0.2 / 0.0 |

`*` = inadmissible at the declared 5.0 % bar. **No consumed series fails in 2023, 2024 or 2025**,
so the gate takes the identical branch across the whole keeper span — reproducing PRECOMMIT F2 §3
on the model's own consumed set. **In the solve path:** a 2023 arm with the gate ARMED
(`results/calibration/pjm168_h6_2023arm`, replaying the KEEPER `pjm_debugb_inputclock_A`) emits
**zero INADMISSIBLE lines** and is **BIT-IDENTICAL** to the keeper's committed 2023 sidecars —
`max|Δ| = 0` and exact frame equality on all four:

| sidecar | rows × cols | exact-equal | max abs numeric Δ |
|---|---|---|---|
| `class_hourly_2023` | 166,440 × 5 | **True** | **0** |
| `system_2023` | 78,840 × 9 | **True** | **0** |
| `reserve_family_2023` | 17,520 × 10 | **True** | **0** |
| `storage_2023` | 17,520 × 6 | **True** | **0** |

So the keeper is byte-identical under F2 and **no in-sample re-solve is owed** — proved, not
assumed, exactly as H6 required.

### 2.4 A defect this screen found in the mechanism itself

pjm-167 built F2 but could never execute it, and it **crashed the first time its own gate fired**:
with `Average Eastern` inadmissible the joint cut is all-`+inf`, `build_pjm_east_interface_cut_groups`
still returned a degenerate group, and the INFO summary at `run_calibration.py:2978` reduced
`np.min` over an empty finite subset — `ValueError: zero-size array to reduction operation
minimum`. Fixed here by dropping the group when no finite limit remains, which is the posture the
gate's own upstream WARNING already declares ("the joint EMAAC import cut is NOT APPLIED this
year"); the summary then reduces over a non-empty set. **Byte-inert when the gate is off** (with
the gate off `east_lim` always carries finite values, so the new branch is never taken), so no
keeper, no other ISO and no other run is touched. This is why a screen is run before arming.

---

## 3. Matrix (rule 32 duty (b))

Both cells were `O` (open, built, not armed) in `docs/codebase-site/data/mechanism-matrix/PJM.js`:

- `eia860_vintage_tracks_solve_year` → **`R` (rejected)**: screened 2021 arm-vs-control at
  `b5925d26`, killed by pre-registered STOP gate G3 (ratio pinned 95.4 % → 95.0 %). Evidence: this
  document §1. **Do not re-test without new evidence** — but note the rejection is of *F1 as the
  repair for the 2021 miss*, not of the fleet-vintage defect, which is measured and real (§1.1).
- `pjm_interface_feed_admissibility_gate` → **stays `O`**, evidence replaced. It CLEARED 6/6, but
  it is still **default-OFF and in no keeper**, and the cell vocabulary's `K` means *armed in the
  designated keeper*. Marking a cleared-but-unarmed mechanism `K` would misstate PJM's keeper
  composition, so the cell moves only when a keeper actually arms it. Evidence: §2.

---

## 4. The pjm-167 environment blocker is BROKEN

pjm-167 §9 and PRECOMMIT F2 §6 record three OOM kills and conclude *"no PJM per-plant LP fits this
container … the cap on this box is zero"*, and the handoff required a ≥24 GB box.

**This session ran three PJM per-plant LPs to completion on a 16.0 GB box.** The container permits
`swapon`, which pjm-167 did not test. A 12 GB swapfile plus `vm.swappiness=10` (with the same
`MALLOC_ARENA_MAX=2` + single-threaded BLAS/OMP mitigations) carries the allocation peak:

| | peak anon-RSS | swap used | outcome |
|---|---|---|---|
| pjm-167 attempt 3 (no swap) | 13.96 GB | — | **OOM-killed** |
| pjm-168 F1 control | **13.50 GB** | 0.64 GB | completed (P0 442 s, P1 154 s) |
| pjm-168 F1 arm | 12.5 GB steady | 0.6 GB | completed (P0 518 s, P1 182 s) |

The peak sits ~1.5 GB above what 15.4 GB of usable RAM absorbs at the moment of the matrix build,
and recedes immediately after. **Recipe for any future PJM lane on a 16 GB box:**

```bash
fallocate -l 12G /home/user/swapfile && chmod 600 /home/user/swapfile
mkswap /home/user/swapfile && swapon /home/user/swapfile && sysctl vm.swappiness=10
export MALLOC_ARENA_MAX=2 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
```

Rule 12 `[R-PARALLEL]`'s cap remains **one** PJM per-plant invocation at a time — these solves were
run strictly sequentially, and two concurrently is what killed pjm-167's first attempt.

---

## 5. Recommendation — what the owner is actually being asked

**F1: closed.** Rejected by its own STOP gate; do not re-test without new evidence. The fleet
defect it targets is real and now needs a different owner — see the handoff.

**F2: the decision is whether to ARM `pjm_interface_feed_admissibility_gate` for PJM.** What the
screen establishes, and what it does not:

- It is **free in-sample**: bit-identical on the keeper's 2023, and the zero-LP admissibility test
  clears every consumed series in 2023/2024/2025. Arming cannot change PJM's `CALIBRATED`
  determination, because it cannot change the runs that determination is computed from.
- It **repairs the held-out years**, which is the whole reason it exists: 2021's EMAAC VOLL goes to
  zero and the inverted east–west gradient collapses to +$1.21.
- It is a **rule 14 `[R-ACCURATE]` named-exception** call, not a licence to drop measured data —
  the pre-2023 posting is a different time/area aggregation under one series name, and the
  fall-through is loud and recorded, per pjm-119.
- **This session does not arm it.** Rule 29: a cleared screen promotes nothing. Arming is a
  config change to the ISO's default overrides and an owner act.

Because F2 is inert in-sample, arming it does **not** require a 2023–2025 re-solve; what it does
require is re-running the 2021/2022 touchpoints on the armed recipe and folding them to the keeper
(rule 30 `[R-TOUCHPOINT-FOLD]`), which is the next session's job.

## 6. What this does NOT establish

- **F1's fleet defect is not refuted.** §1.1 is a measured registry error and stands; what G3
  refutes is that fixing it repairs the 2021 miss.
- **No number here is an out-of-sample skill claim.** 2021 is validation tier — iterable
  model-SELECTION evidence (rule 22), never quotable as certified out-of-sample skill.
- **No parameter was identified against 2021 or 2022.** Both arms are single declared config
  flips on the committed keeper recipe.
- **Nothing is promoted and no keeper moved.** `2026-08-15-pjm-162-inputclock` is untouched.
