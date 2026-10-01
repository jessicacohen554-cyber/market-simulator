# FINDING — PJM RUBRIC-RESIDUAL: the screen KILLS the arm. PJM's reserve co-optimization is reachable in the forecast lane, fires, and supplies **0.15 % of the E&AS the failing set needs, mostly with the wrong sign**. The phase-0 attribution of PJM's backcast price tail to the co-opt is REFUTED.

**Lane:** PJM RUBRIC-RESIDUAL. **Branch:** `claude/pjm-rubric-residual-composition-xhw1kj`.
**DATA PROFILE: pjm.** Pre-declared in `PRECOMMIT-pjm-eas-operand-2026-09-07.md` (+
`ADDENDUM-pjm-eas-key-window-2026-09-07.md`), both pushed **before any LP**.
**NOTHING ARMS.** The arm is refuted and the harness flags stay default-`None`.

Per rule 29(c) this document carries **every number the lane will ever cite** from the screen
bundle; the bundle is deleted before merge and git history is the record.

---

## 0. Verdict

The screen did exactly what rule 29 `[R-SCREEN]` says a screen is for: it killed a plausible,
well-motivated arm for **~9 minutes of LP on one year** instead of a 5-year span, and it killed
it on the **mechanism's own arithmetic**, never on a band. Three of five gates are decisive:

| gate | result | measurement |
|---|---|---|
| **G1 reachability** | **PASS** | the co-opt is live in forecast mode — `energy+reserve co-opt (PJM): req mean 2639 MW, 4 ORDC steps, 1436 reserve-eligible units`; `PJM PER-GEN reserve co-opt ON: 40 R columns / 1405 member units, 2 balance families (pjm_primary, pjm_primary_mad), req means [2639, 2638] MW`. **366 of 1,399** offers moved, so it is not byte-inert. |
| **G2 price surface** | **FAIL** | pre-registered direction **UP**, floor **$60/MWh**. Measured: screen-price max **52.7715 → 52.3638 $/MWh** — it went **DOWN** by 0.41 (−0.8 %). Mean 36.9592 → 36.9546. |
| **G3 the operand** | **FAIL** | pre-registered floor **$12.7**/accredited MW-day, predicted band **$25–65**, predicted mean **$40.656**. Measured: **0.0416 → 0.0411** — it went **DOWN**, and lands **~1,000× below** the predicted band and **~300× below** the floor. |
| **G4 footprint** | reported | 1,399 units in both stacks, 0 only-in-either, 366 offers moved. |
| **G5 identity I2** | **PASS** | the screen's failing set IS the auction's uncleared set; D57's invariant survives the arm. |

**VERDICT: SCREEN KILLS THE ARM.** The remaining years were never spent.

---

## 1. The falsifiable point prediction, REFUTED at full magnitude

PRECOMMIT §5 predicted, from phase-0 C's Δ=40 $/MW-day row, that the armed 2022 clearing would
read price **$67.76**, position **1.04835**, uncleared **gas_st 0 · coal 6,647.8 · gas_cc
3,605.2 MW**. Measured:

| | control (registered `pjm-t1h`) | ARM | predicted |
|---|---|---|---|
| clearing price $/MW-day | 90.4111 | **90.4355** | 67.760 |
| cleared position | 1.042601 | **1.042595** | 1.04835 |
| n uncleared | 133 | **133** | — |
| uncleared coal MW | 1,172.069 | **1,172.069** | 6,647.812 |
| uncleared gas_st MW | 9,536.643 | **9,536.643** | 0 |
| uncleared gas_cc MW | — | **—** | 3,605.197 |
| marginal unit | `COAL_PJM_AEP_Ohio_p6166_committed` | **same** | — |

The uncleared set is **identical to the milli-MW in every fuel**, on the same marginal unit. The
prediction is not merely missed — the object it predicted a change in **did not move at all**.

**Retirements, reported at full magnitude and gating in neither direction** (rule 1
`[R-STRUCT]`): byte-identical in both arms over 2021–2022 — `coal/announced 3,301.4 ·
gas_st/economic 8,693.3 · gas_cc/announced 74.6 · gas_st/announced 43.0 · oil/announced 51.2 ·
biomass/announced 8.4` MW. The run log's own line: `year 2022: R-NEW pipeline executed 103
exit(s), 8693 MW`, and `screen revenue stack [gas_st]: net_rev=0.0 $/kW-yr,
going_forward_bar=35.0 $/kW-yr` — **still exactly zero**.

## 2. WHY it is inert on the operand — measured, not inferred

The 366 moved offers, by fuel, in $/MW-day (**negative = offer fell = E&AS rose**, the direction
the mechanism needed):

| fuel | n | min | median | max |
|---|---|---|---|---|
| coal | 120 | +0.0031 | **+0.0910** | +0.1723 |
| gas_cc | 130 | −0.0071 | **+0.1206** | +0.1864 |
| gas_ct | 74 | −0.0061 | **−0.0061** | +0.0074 |
| gas_st | 42 | +0.0007 | **+0.0008** | +0.0008 |

Largest single move anywhere in the stack: **0.1864 $/MW-day** (`CC_CHP_PJM_EMAAC_p55801_
committed`). Against a required **≥12.7**, that is **1.5 %** of the threshold at the extreme and
**0.006 %** for gas_st — and for coal and gas_cc the median sign is **positive**, i.e. those
offers *rose*.

**The cause is a supply/requirement ratio the mechanism cannot escape, and the model's own code
predicted it.** The run logs `deliverable ramp mean 51.0 GW` of reserve supply against `req mean
2639 MW` — a factor of **19**. `pjm_reserve_supply_cap`'s own field docstring says exactly this
failure mode: *"The bare PJM co-opt draws reserve on ~38 GW of full-fleet headroom vs the ~3.4 GW
Primary requirement, so the published vertical ORDC step never fires; this re-scopes reserve
SUPPLY to the deliverable slice."* **The re-scoping is armed here and is not enough**: 51.0 GW of
10-minute deliverable ramp still clears a 2.6 GW requirement without ever approaching the ORDC
knee. So no reserve scarcity forms, `reserve_signal_mean` stays **0.0 in the arm exactly as in
the control**, and the energy dual gains no reserve opportunity cost to pass to the screen.

## 3. What this REFUTES in the lane's own phase 0 — stated against interest

Phase-0 D measured the 103 decided gas_st units earning **$40.656 per accredited MW-day** on the
committed PJM **backcast** 2021 surface versus ~$0.004 in the hindcast, and this lane attributed
that four-order-of-magnitude gap to the reserve co-optimization, citing `FINDING-pjm138`'s
"system energy IS reserve opportunity cost" and the `ordc_scarcity_overlay` **G** cell's
"the in-LP co-opt already owns the phenomenon".

**That attribution is now refuted by direct measurement.** Arming the co-opt — all three fields,
in the lane that lacked them — moves the hindcast price tail by **−0.41 $/MWh**, not by the
+$160 the backcast/hindcast gap would require. The co-opt is therefore **not** the cause of
PJM's backcast price tail, and the $52.77 → $213.46 difference between the two surfaces is
produced by something else in the backcast recipe.

Phase-0 D was a correctly-measured *contrast* (same units, same marginal costs, same
availability, two committed price surfaces) but a **wrong causal attribution** of that contrast
to the one config difference the lane happened to be looking at. The instrument was sound; the
inference from it was not. This is the single most useful thing the screen produced, and it is
why the screen exists.

**What survives from phase 0 unchanged**, because none of it depended on that attribution:
- the operand is measured at **0.000404 of GFC** ($122,869 against $304,263,925), with
  `reserve_uplift` and `reserve_signal_mean` exactly 0.0 — now confirmed a *second* time, in the
  armed run, at 0.0411 $/accredited MW-day;
- `screen_price_max = 52.7715 $/MWh` sits **below** the gas-steam fleet's marginal cost
  ($51.16–58.24), so `max(0, price − mc)` is structurally zero, not small;
- the whole gas_st over-exit is the **2022** decision (103 units / 8,693.3 MW; 2023 has 4 units /
  55.7 MW; 2021/2024/2025 have none) — the footprint that named the screen year;
- the **hard threshold at ≈$12.7/MW-day** below which the 2022 uncleared set is exactly
  unchanged, and the monotone rotation out of gas_st into coal above it;
- the offline re-clearing reproduces the committed clearing on the screen year exactly;
- **D57 voided the harness's stated reason** for withholding scarcity from PJM's screens
  (`run_capacity_hindcast._build_config`: *"RPM net-CONE × UCAP already enters the screens via
  `capacity_revenue_per_mw_yr`, so the master flag is a harmless no-op there"*) by replacing that
  exogenous payment with an endogenous clearing whose input **is** the E&AS margin. The screen
  does not touch that argument — it only removes the reserve co-opt as its answer.

## 4. Is this a keeper candidate? **NO — and the "structure improved, gates regressed" carve-out does not apply**

It is worth being explicit, because the carve-out is real and this is not it. Rule 1
`[R-STRUCT]` protects a mechanism that is **structurally correct** even when the residual
worsens. Here **there is no structural gain to weigh**:

- the mechanism is **measurably inert on the object it was proposed to fix** — the operand moved
  by 0.0005 $/MW-day against a 12.7 requirement, i.e. it did not move;
- the retirement bands are **byte-identical**, so nothing regressed *or* improved;
- the one thing that did move, the price surface, moved **the wrong way** (−0.41 $/MWh);
- and rule 29 is explicit that a screen **"may kill an arm; it may never promote one."**

**Nothing is promoted. No keeper is proposed, and the PJM keeper is unchanged.**

**One genuinely open question this leaves, routed rather than absorbed:** PJM's calibrated
backcast keeper runs `energy_reserve_coopt` / `pjm_reserve_pergen` / `pjm_reserve_supply_cap`
**True** while the forecast lane runs them **False**, and `run_capacity_hindcast._build_config`'s
own docstring says the hindcast *"must exercise the capacity screens under the same price
formation the forecast uses for the ISO."* That lane inconsistency is real and is **not**
resolved by this finding — what this finding establishes is only that closing it **does not fix
the E&AS operand** and costs a small price-surface regression. Whether the forecast lane should
carry PJM's reserve footing for **consistency** is an owner-facing question about every PJM
forecast run's cache key, not something a killed screen may carry.

## 5. The successor, re-routed by the refutation

The operand is still zero and the composition residual is untouched. But the successor is no
longer "restore the reserve co-optimization" — it is **"find what actually puts the tail in
PJM's backcast price surface, since the co-opt demonstrably does not."** The two surfaces differ
by `mode` (backcast vs forecast), `scarcity_pricing_enabled` (False vs True), the fleet basis
(measured backcast fleet vs 2020-vintage evolved), the demand basis, and the offer curves — and
the co-opt is now **eliminated** from that list by measurement. A successor lane should difference
the two surfaces on the remaining axes at zero LP before spending another arm; the ~19× reserve
supply/requirement ratio measured here (§2) also says that **any** PJM mechanism whose route to
the screen runs through reserve scarcity is dead on arrival at this fleet size, which retires a
whole family of candidate levers, not just this one.

## 6. Governance

- **Rule 29 `[R-SCREEN]`**: phase 0 first (zero LP, committed artifacts only); screen year **2022**
  named in the PRECOMMIT before the screen ran, on the mechanism's own measured footprint;
  gates **structural and STOP-only**; the bands reported and gating in neither direction.
- **Rule 29(b)**: G-DRIFT clean — PJM solve-surface fingerprint unmoved (`0f749d17202c32d9`,
  211 rows, `moved {}`), the control's config re-keys to `fb16fda2ddb0a94a` at HEAD, every
  changed hunk since `10cda1fa` INERT for PJM. **Form 4 held; no control solve was spent.**
- **Rule 29(c)**: the screen bundle `results/capacity-hindcast/pjm-screen-eas-2021-2022-arm`
  (key `8966e7cea75efc4e`) is **deleted before merge**; every number is above.
- **Rule 16 `[R-ALLYEARS]`**: untouched — the screen was a throwaway probe, never registered,
  never a keeper, never quoted as a keeper number.
- **Rule 28**: `energy_reserve_coopt`'s PJM cell gains its forecast-lane posture and citation in
  PJM's shard this session (`fc: "R"`); `ordc_scarcity_overlay` stays **G** and was never
  re-opened; Q55/Q56 and the sector gate were not re-opened.
- **Two errors of this lane's own, corrected in the open**: the declared arm key was computed on
  the wrong year window (`ADDENDUM-pjm-eas-key-window-2026-09-07.md`), and a docs-only commit
  tripped `run_screen.sh`'s HEAD-equality guard while the substantive freeze held (same
  addendum). Neither moved a gate, a threshold or a number.

### 6.1 Environment, recorded because it is not the control's

The control records pandas 3.0.3 / numpy 2.4.6 / scipy 1.17.1 / highspy 1.14.0 / pyarrow 24.0.0
/ pydantic 2.13.4; this session pinned all six to those versions before solving. Three further
conditions, none of them this lane's and none on the PJM hindcast path:

1. **The container lacked the legacy `US/*` timezone aliases** (`ZoneInfoNotFoundError:
   'US/Central'`), which breaks `curate_ercot_wtx_congestion` and is used on the solve path by
   `src/market_sim/results/scarcity.py` and `src/market_sim/data/eia930/envelopes.py`. Fixed here
   with `pip install tzdata` **before** the solve. A lane solving in a fresh container needs this.
2. **`data/raw/lmp-data/CAISO/CAISO_dam_hourly_2022.csv`, added on `main` by caiso-261
   (`174ba0bd`), lacks the `MGHG` column** that `curate_lmp.parse_caiso_file` reads
   unconditionally → `KeyError: 'MGHG'` aborts the **entire `lmp` datatype for every ISO**. Not
   repaired here (another ISO's lane); PJM has no import node so `neighbor_price`/clean-lmp is
   not on its path.
3. **`emissions-unit-annual` OOMs at 15 GB** (exit −9), twice, including alone at 2020 after
   2019 wrote. Only a docstring reference in `src/`; not on the PJM hindcast path.

Also incidental, not repaired: `run_capacity_hindcast.py --help` raises `ValueError: unsupported
format character ','` from an unescaped `%` in a help string, and
`pipeline/year.py::run_year_solve` has no caller in `src/market_sim/` (the live
`apply_reserve_coopt` call site is `runner.py:3527`).

### 6.2 Pre-existing RED on `main`, verified rather than assumed

Verified against clean `origin/main` (`git diff HEAD origin/main -- src/market_sim scripts tests`
empty at the time): FR-22 parity — 3 FAILs, exactly `miso_seam_neighbour_{anchored_ladder,
hourly_ladder,hourly_spp}`; `test_cache_solve_surface` — 2 failures
(`{'NUCLEAR_MONTHLY_CF_BY_YEAR': '00a8e8726fd0edd6'} != {}`); `test_caiso_st_gas_peak_measured` —
`1.154 != 1.166`; S1 status staleness — **with a correction to the brief**: `status/shared.js`
already carries SPP in `iso_order`; what `audit_keepers` actually flags is `status/ERCOT.js` and
`status/PJM.js`. None repaired.

The owed `FINDING-capx-d78arm` §9.1 cherry-pick was **already landed** (`4ad49fe3`, ancestor of
`origin/main`); nothing was owed.
