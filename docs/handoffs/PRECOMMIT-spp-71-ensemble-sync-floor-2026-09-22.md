# PRECOMMIT — SPP-71, card R-bc: PRICE-FORMING CURTAILMENT

**Pushed BEFORE any solve.** Base `b969ffaa567412e82fb2544ab628e91007183eaa`.
Lane branch `claude/spp-price-forming-curtailment-w7bmfr`. Parent runs NO LP (rule 32(a)).

---

## 0. HEADLINE — the charter's channel is refused on a proof, and the object is relocated

The R-bc charter (`FINDING-spp-64` §9) asks for "a reduced-form curtailment that enters as an
**LP constraint whose dual reaches the zonal price** — the same standing the transmission limit
already has — so that when it binds, wind is marginal, the price goes to its offer, and the
curtailment and the negative-price hour are **one event**."

**The first half of that sentence and the second half are incompatible, and the proof is two
lines.** Let the row be any upper limit on wind delivery, `Σ_w W_w(t) ≤ D(t)`, dual μ ≥ 0.

> If the row binds, wind sits at `D(t)` with its own CF bound slack. The marginal MWh of load in
> that zone therefore **cannot** be served by wind — the row forbids it — so the energy-balance
> dual λ is the marginal cost of the next unit in the stack, a positive thermal offer. **Wind is
> not marginal and the price cannot reach its offer.** ∎

This holds whether the limit is written as a variable bound (what `spp_curtailment_ceiling`
does, `data/curtailment_share.py`: *"applied as a multiplier on the CF upper bound"*) or as an
LP row. `FINDING-spp-64` §3 diagnosed the bound and prescribed the row; **the row has the same
defect, because the defect is the DIRECTION OF THE INEQUALITY, not the object it is attached
to.** Re-channelling the ceiling family cannot work, and this lane does not attempt it.

**What CAN take a zonal price to the wind offer is supply pushed UP from below.** When a
must-hold generation floor binds and the zone's remaining load is already served, wind is the
unit that must back down — so wind is marginal, λ = −26.000, and the curtailment and the
negative-price hour are **one event**, exactly as chartered. The R-bc object is therefore a
**supply-side synchronization floor**, and SPP's keeper already carries it (`coal_sync_srmc_tranche`
+ `coal_mustrun_online_pmin`, SPP-51). **It is in the wrong place, and the defect is measured.**

---

## 1. Phase 0, step 1 — the failing rows re-verified at base (`scripts/calibration_verdict.py`)

Keeper 14 span `2026-09-20-spp-67-yearown-rate` re-scores **CALIBRATED**, 0 FAILS, **1 ledgered
C3c** (2023 0h / 2024 7h / 2025 1h against RT 42 / 59 / 68 >$200), C1 16/16 · free 12/12,
C2/C3a/C3b/C4/C6/C8 PASS. Unchanged from the promotion record. The six failing rows the brief
names are the **rung's** (2019–2022), and SPP-69/70 verified them at 1bbe9f17; this lane does not
re-derive them.

## 2. Phase 0, step 2 — THE DESIGN, fixed before any residual was read

**Provenance of the design, stated because rule 1 `[R-STRUCT]` makes the order load-bearing:**
the construction below was derived from the *structural* record — `RESULT-spp-51` §(the repair is
incomplete) and `RESULT-spp-66`'s transferable lesson — **before** this lane ran its own phase-0
probe. It was not selected by looking at a residual, and no variant was swept.

### 2.1 What the code does today

`src/market_sim/data/fleet/arrays.py`, the `coal_sync_any` block (≈L3024–3061). For each coal
plant *p* with a measured synchronization Pmin:

```
frac_p = online_frac_p                     # measured CAMPD synchronized SHARE of hours
k      = round(frac_p * 8760)
floor_p(t) = coal_sync_pmin_mw_p   for t in the top-k hours by SYSTEM LOAD
           = 0                     in every other hour
```

(`frac_p ≥ _COAL_SYNC_FORCE_ALL = 0.99` short-circuits to all hours. **No SPP coal plant reaches
it** — the fleet max is 0.9870 — so SPP's bottom-hour floor from this branch is exactly
**0.0 MW**.)

### 2.2 Why that placement is wrong, and it is a CONSTRUCTION error rather than a level error

`online_frac` is a measured *marginal probability* — the share of hours the plant is
synchronized. The code spends that probability as a **degenerate distribution**: it asserts
P(synchronized | top-k load hour) = 1 and P(synchronized | any other hour) = 0. That is a
placement **hypothesis**, and it is false on the plant's own physics: a coal unit has a min-down
of 12–48 h and a five-figure start cost, so its online hours are multi-day **runs** that span
load troughs. It cannot shut for a six-hour overnight trough and restart.

Two independent confirmations already on the record:

* **SPP-51** measured the consequence: the armed floor's coal minimum reaches **0.15–2.53 %** of
  the class's own annual max against a real SPP PRB fleet at **8.1–17.5 %**.
* **SPP-66** spent seven year-solves re-ranking the same window on net load and it went the
  **wrong way in six of seven years**, and named the successor in its own words: *"A commitment
  floor's job at the bottom is not 'be where the class runs most', it is 'stop the class
  collapsing where it would otherwise go to zero' … a successor must target the floor's LEVEL or
  COVERAGE at the bottom, not re-rank its window."*

**And the repo's own D-4 window registry already declares the correct answer.**
`scripts/legitimacy_diagnostics.py:354–381`, `(MECH_COAL_MUSTRUN, None): (0, 24)`, with the
citation: *"the driver-justified window is ALL 24 hours BY DRIVER … the floor is already
hour-of-day-blind … So there is no hour-of-day the driver says it is off."* The declaration says
24 hours; the code implements a load-ranked window that is 0 MW at the bottom. **The arm makes
the code agree with the declaration the repo already carries.**

### 2.3 THE ARM — the continuous-relaxation image of the same measured commitment

```
floor_p(t) = coal_sync_pmin_mw_p * online_frac_p          for EVERY hour t
```

still clipped downstream to `pmax_p × availability_p(t)`, so an outage hour relaxes it exactly as
today, and still composed with `np.maximum` against any other floor.

* **It is an LP row (a `min_gen` lower bound) whose dual reaches the zonal price.** When it binds
  and the zone's load is already served, wind backs down, wind is marginal, λ = −26.000. The
  curtailment and the negative-price hour are ONE event — the charter's requirement, met by a
  row whose inequality points the right way.
* **It is the LP-relaxation of the binary commitment, not an approximation of convenience.** This
  is a pure-LP dispatch model with no integrality (CLAUDE.md, *"Pure LP — no MIP"*); a plant is
  already a set of continuous tranches. `E[floor_p(t)] = pmin_p × P(synchronized)` = `pmin_p ×
  frac_p` is what a Bernoulli commitment variable relaxes to. The top-k window is the *degenerate*
  relaxation; this is the faithful one.
* **It spends the SAME measured annual synchronized MWh.** `pmin × frac × 8760` either way. Only
  the placement moves.
* **ZERO new free parameters, ZERO new data** (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`). It reads
  the identical two columns the keeper already reads — `mustrun_online_pct` and `online_frac` from
  `data/raw/_processed-legacy/thermal_tranches_SPP.csv`. DOF ledger stays **5 entries / 3
  residual**, verified current at base (`build_dof_ledger.py --iso SPP --check`).
* **It subsumes the `frac ≥ 0.99` short-circuit continuously** — at frac ≈ 1 the formula returns
  the full pmin every hour, which is what that branch does discretely.
* **Rule 17 `[R-FLOOR-WINDOW]`:** (a) driver = the plant's CEMS-measured synchronization Pmin and
  its measured online share; (b) hours it may bind = all 24, which is the D-4 declaration already
  cited above, and the CLASS is never measured offline (measured SPP COL minimum is 1,565–3,817 MW
  in every year); (c) forward story = the same artifact regenerates from the next CAMPD vintage
  with no model input.
* **Rule 18 `[R-PHYSICS]`:** eligibility is `coal_sync_pmin_mw > 0`, a measured per-plant
  parameter — no class tuple.
* **Rule 13 `[R-MEASURED]`:** the quantity is a measured synchronization rate, produced for a
  forward year from the then-current CAMPD conduct, and it responds to changed conditions (a fleet
  that cycles more measures a lower `online_frac` and carries a lower floor).

### 2.4 Rule 19 `[R-ONE-MECH]` enumeration — MANDATORY, and what this REPLACES

| mechanism | status | relation to this arm |
|---|---|---|
| `coal_sync_srmc_tranche` + `coal_mustrun_online_pmin` | **armed in keeper 14** | **THIS IS THE SAME MECHANISM.** The arm replaces its PLACEMENT rule in place. Never stacked — the top-k branch is not executed when the arm is on. |
| `spp_curtailment_ceiling` | **R** (SPP-63 / re-refused SPP-68) | same phenomenon (wind curtailment), opposite inequality. **STAYS OFF** and is never co-armed. §0 proves why re-channelling it cannot work. |
| `commitment_floor_window_netload` | **R** (SPP-66) | the *window re-rank* this arm deliberately does not repeat. **STAYS FALSE.** The arm removes the window rather than re-ranking it. |
| N↔S `TransferLink` (3,400 MW, SPP-53) | live, single | untouched. Its dual is the only other price-forming row on SPP wind. |
| `internal_congestion_split` | **U**, recommended-against (SPP-29 / SPP-64 §8) | **NOT OPENED.** No topology change. |
| `offer_curve_by_group` (uniform 0.93) | **K** | **BYTE-IDENTICAL** in both legs. Sequenced behind this card (SPP-70); not touched. |
| `pmin_mw` / `min_run_hours` / `min_down_hours` / `startup_cost_per_mw` | 0 on every SPP fossil unit | unchanged. The arm adds no unit-commitment parameter. |
| `energy_reserve_coopt`, `ordc_scarcity_overlay`, `negative_renewable_offers`, `spp_gas_commitment_bridge`, `tranche_startup_amortization` | I / U / R | untouched. |

### 2.5 Phase 0, step 4 — the binding-constraint archive, and why this lane reads NO shares

`data/raw/spp-binding-constraints/` is served. **This lane does not use it and opens no
membership question.** The arm is a fleet-physics repair with no flowgate input, so card P1's
SPP-54-vs-SPP-57 ranking stays exactly where `FINDING-spp-64` §8 left it — unopened, and needing
its own PRECOMMIT that fixes membership before reading shares. Recording this explicitly so a
successor does not read a membership judgement into this document that it does not contain.

---

## 3. THE GATE (rule 25 `[R-ISO-SCOPE]`, rule 28 `[R-MECH-MATRIX]`)

New field `ScenarioConfig.coal_sync_ensemble_level: bool = False`, default **off**, so every other
ISO and every committed run config is byte-identical by construction. PJM and MISO arm this same
family and are unaffected. Armed for SPP via per-run CLI `--coal-sync-ensemble-level` only — **no
ISOConfig default override, no `default_scenario_overrides`.** Matrix row added to
`docs/codebase-site/data/mechanism-matrix.js` plus a cell line in **every** shard (rule 28(c)).

---

## 4. G-DRIFT and the control — THE CONTROL IS SOLVED, NOT ASSUMED

Keeper 14's `basis_sha` is `40eeb43adf013114fccc23a90518a3683d5bf377`; fetched explicitly (trap
(r)). `git diff <basis> HEAD` over the audited solve path shows **14 changed files / 3,424
insertions**, including `arrays.py` (+130), `campd_bins.py` (+179) and `scenarios.py` (+315) —
i.e. LIVE hunks sit on the exact block this arm edits.

**This lane therefore does not rely on rule 29(b) form 4 at all.** Each shard solves its **own
control AND its arm at the same pinned HEAD**, one year per shard, exactly as SPP-51 did. The
differencing is then exact by construction and no HEAD-drift audit can be wrong about it. Cost:
14 year-solves at SPP's measured 178–256 s/year ≈ 50 min of LP total, ~7–8 min per shard, inside
the rule-32(b) 20-minute ceiling.

---

## 5. PRE-REGISTERED PREDICTIONS — all four conditions, per year, BEFORE the solve

### 5.0 The REALISED floor, not the nominal one — a correction this lane owes itself

A first sizing used the nominal fleet floor `Σ_p pmin_p × online_frac_p` = **3,324.5 MW** (24 COAL
plants in the pooled artifact; full level `Σ pmin` = 4,090.3 MW, matching SPP-51's 4,090.3). **That
number overstates the arm by ~3× and no prediction below uses it.** The LP applies the floor **per
plant** and clips it to that plant's own `pmax × availability`, and SPP's coal outages are
concentrated in exactly the shoulder hours where net load is lowest — so the realised fleet floor
swings with availability instead of standing at a constant.

`scripts/probes/_spp71_floor_delta.py` rebuilds keeper 14's own fleet through the sanctioned
`fleet_only` reconstruction and re-implements **both** placements from the same primitives. **The
reimplementation reproduces the bundle's realised coal `min_gen` exactly — max |Δ| 0.0 MW, mean
|Δ| 0.0 MW, r = +1.0000, in all seven years** — so the counterfactual is quoted on an instrument
that reproduces the incumbent:

| realised fleet coal floor, MW | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| window **min** (today) | 416.2 | 179.5 | 216.6 | 113.5 | 33.3 | 29.7 | **27.4** |
| **ensemble min** (arm) | 2,127.0 | 1,501.7 | 1,380.6 | 1,381.8 | 945.9 | 1,262.3 | **1,057.9** |
| window **p01** | 773.8 | 644.1 | 632.7 | 619.6 | 404.8 | 335.2 | 150.9 |
| **ensemble p01** | 2,336.8 | 1,664.7 | 1,500.2 | 1,426.6 | 1,353.3 | 1,400.5 | 1,173.1 |
| **annual MWh ensemble/window** | 0.9937 | 0.9885 | 0.9892 | 0.9853 | 0.9945 | 0.9859 | 0.9854 |

**P-0 — THE IDENTIFICATION, and it is the strongest single result here.** The construction is fixed
by two measured columns with nothing chosen against any outcome, and (i) it spends the **same**
measured annual synchronized MWh to within 0.6–1.5 % — placement only, the residual being the
per-plant availability clip — and (ii) it moves the bottom-hour floor from **1.3 % of the measured
SPP coal fleet minimum to 49.7 %** in 2025 (27.4 → 1,057.9 MW against a measured 2,128 MW), and
**never exceeds** the measured minimum in any year. 2019→2025 the arm's floor sits at
0.56 / 0.66 / 0.81 / 0.63 / 0.60 / 0.53 / 0.50 × the measured fleet minimum, against
0.11 / 0.08 / 0.13 / 0.05 / 0.02 / 0.01 / 0.01 × today. **It roughly halves the structural gap and
cannot over-force.**

### 5.1 The GATE predictions — small, and stated as small

Holding the LP's own dispatch fixed and letting the floor bite only where it exceeds what the LP
already produced. This is a **first-order** estimate: it cannot see the LP re-optimising the rest
of the stack in those hours, so the price leg is a **lower** bound and the volume leg is roughly
right.

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| hours the floor bites | 22 | 478 | 505 | 439 | 299 | 456 | 368 |
| **P-1** hours at wind offer NOW | 0 | 169 | 505 | 511 | 393 | 461 | 435 |
| **P-1 predicted** | **9** | **254** | **566** | **572** | **439** | **517** | **491** |
| actual RT negative hours | 547 | 936 | 1,108 | 995 | 992 | 1,172 | 1,018 |
| **P-2** wind displaced, TWh | 0.005 | 0.129 | 0.237 | 0.269 | 0.119 | 0.196 | 0.202 |
| **P-5** coal added, TWh | 0.006 | 0.197 | 0.269 | 0.303 | 0.154 | 0.265 | 0.255 |
| gas displaced, TWh | 0.001 | 0.068 | 0.032 | 0.033 | 0.035 | 0.069 | 0.053 |
| **P-3** mean price shift, $/MWh | −0.03 | −0.29 | −0.22 | −0.22 | −0.16 | −0.20 | −0.18 |
| price CV now → predicted | .180→.191 | .392→.456 | 1.216→1.230 | .771→.784 | .489→.512 | 1.000→1.020 | .615→.634 |
| actual price CV | 1.563 | 1.390 | 4.072 | 1.191 | 1.333 | 1.592 | 1.625 |

**P-1 (condition 2) — negative hours UP in all seven years, by +9 to +85, closing roughly 10–15 %
of the gap.** Not the 50–60 % the nominal sizing suggested. Direction right, magnitude modest.

**P-2 (condition 1) — wind volume DOWN, and this is the arm's weakest leg by a wide margin.**
0.005–0.269 TWh against a wind excess of +1.2 / +8.3 / +9.0 / +9.9 / +8.9 / +11.7 / +11.6 TWh —
**about 2 % of the excess.** **R-bc does not close SPP's wind volume defect and this lane predicts
in advance that it will not.**

**P-3 (condition 4) — C3a moves −$0.03 to −$0.29, i.e. −0.1 % to −1.5 % of the mean. No C3a status
flip is predicted in any year; 2020's +19.3 % FAIL improves only marginally.** Price CV rises in
all seven years, toward the actual, so **C3b is predicted to improve slightly in every year** —
but by far less than the distance to the actual CV.

**P-4 (condition 3) — congestion rent. NOT SIZED, no prediction offered**; it needs the flow
solution. Reported from the solve at full magnitude either way.

**P-5 — coal volume UP 0.006–0.303 TWh. A declared RISK**: SPP-69's scored C1 has COAL_PRB already
LONG in 2021 (+7.10), 2022 (+9.95) and 2025 (+5.42) TWh. ~0.26–0.30 TWh added there makes those
rows marginally worse; it helps 2019 (−1.72) and 2020 (−7.10) marginally.

### 5.2 WHY THIS IS STILL WORTH SEVEN SHARDS, said before the result is known

The gate movement predicted above is small. The lane spends the LP anyway, and the reason is
rule 1 `[R-STRUCT]`, not optimism: **the structural leg is large and the construction is identified
with zero free parameters.** The floor goes from 1–13 % of the measured fleet minimum to 50–81 % of
it, the repo's own rule-17 declaration already says the floor should be hour-of-day-blind, and the
cost is ~50 minutes of LP across seven parallel shards. **If the arm is refused it will be on a
kill limb in §6, never on "the residual didn't move" — and if it is kept it will be on the
structural leg, with the small gate movement reported at full magnitude and not dressed up.**

Stated equally plainly: **this lane does NOT expect R-bc to close C1, C3b or C3c**, and if the
owner's question is "does SPP now have a lever that closes its open gates", the honest pre-solve
answer is **no** — §8 and the RESULT will say so.

---

## 6. KILL LIMBS — pre-registered, and any ONE of them refuses the arm

1. **K-1 — the floor lands off its own measured target.** If the arm's realised fleet coal minimum
   **exceeds** the measured EIA-930 SWPP COL minimum in any year, the construction is over-forcing
   and is refused. §5.0 predicts 0.50–0.81× in every year, so this limb has real headroom to trip.
2. **K-2 — load-bearing regression.** Any C3a or C3b status flip PASS→FAIL in any of 2023/2024/2025
   (the CALIBRATED span) refuses the arm as a keeper candidate. P-3 predicts none.
3. **K-3 — the price leg does not move.** If negative hours fail to rise in at least five of seven
   years, the mechanism is not price-forming and the card is dead as chartered. P-1 predicts a rise
   in all seven.
4. **K-4 — C8 `[R-FORCED-BUDGET]`.** If the D-2 coal forced share crosses the 30 % merchant cap in
   any year, the floor is dispatch rather than scaffolding and is refused. Control reads 4.41–17.69 %.
5. **K-5 — C1 net.** If summed |C1 error| worsens in more than four of seven years, the volume cost
   exceeds the price benefit and the arm is reported, not promoted.

**Rule 1 `[R-STRUCT]` applies in BOTH directions and is stated here so it cannot be applied
selectively afterwards:** this arm is a construction repair identified by measured data and by the
repo's own D-4 declaration, so a worse residual does **not** by itself refuse it — only the limbs
above do. Equally, a better residual does not promote it if the structural leg fails.

---

## 7. SHARD PLAN (rules 32 / 34 / 36)

Seven shards, **one per year 2019–2025** (rule 36 `[R-YEAR-ISOLATION]`), each solving **control +
arm** at one pinned HEAD, each pushing its **full** bundle including `dispatch/<year>_P1.parquet`
(rule 34(a): `.gitignore` NEGATION then a PLAIN `git add`; `-f` is refused by the auto-mode
classifier). The parent composes, scores, registers and puts the promotion question (rule 31).

Config signatures each shard hard-stops on — the keeper and the rung DIFFER (trap (n)):

| | 2019–2022 (rung side) | 2023–2025 (span side) |
|---|---|---|
| `mid_vintage_exit_carry` | **True** | **False** |
| `gas_price_override` $/MMBtu | 2019 2.57 · 2020 2.03 · 2021 3.72 · 2022 6.45 | 2023 2.54 · 2024 2.19 · 2025 3.52 |

`offer_curve_by_group` must read SHA-256 `090abd793b5fa5a7…` in **both** legs of every shard.

---

## 8. WHAT THIS PRECOMMIT DOES NOT CLAIM

* It does **not** claim the arm closes C1. P-2 says it moves ~8 % of the wind excess.
* It does **not** claim it reaches C3c. SPP-29 closed that route; nothing here re-opens it.
* It does **not** adjudicate `internal_congestion_split`, and it reads no flowgate share.
* It does **not** re-open `offer_curve_by_group`, which stays byte-identical (trap (o)).
* Every number above is model-**SELECTION** evidence. `[R-HOLDOUT]` was removed 2026-09-09, so no
  year here is out-of-sample and none of this is a certified skill claim.
