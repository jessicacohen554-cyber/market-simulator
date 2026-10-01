# PRECOMMIT — SPP-51 / `R-bc`: curtailment as an LP object whose price effect is real

**Lane** SPP-51 · **Base** `608cb21f455699b0f43460b444841daf5f258774` (`origin/main` at session
start; SPP-50 is merged and is an ancestor) · **Keeper** `2026-09-16-spp-42-commitment-feasibility`
(`spp42_span_a`, 2023–2025) · **Rung** `2026-09-19-spp-49-benchmark-membership`
(`spp49_benchmembership_span`, 2019–2022), stamped to the keeper.

**Written and pushed BEFORE any solve.** Every number below is zero-LP, read from committed
artifacts. The prediction in §5 is recorded here so it cannot be written to fit the result
(rule 1 `[R-STRUCT]` condition (c)).

---

## 0. Headline, stated before the evidence

1. **`R-bc` AS LITERALLY CHARTERED IS KILLED AT PHASE 0**, which is what the charter asked for
   ("kill it at phase 0 rather than at a screen"). A per-hour wind constraint row
   `W[z,t] ≤ K[z,t]` is **mathematically identical to lowering the bound** — same feasible
   region, same solution, and its dual does **not** enter λ. It is the SPP-63 ceiling under a
   new name. The only wind-side row whose dual *does* reach λ is a **cross-hour energy budget**,
   and that one fails rule 13 `[R-MEASURED]`'s forward test and moves the price the **wrong
   way**. §3.
2. **The charter's price premise is inverted by measurement, and this is the load-bearing new
   fact.** The model does not have too many negative-price hours — it has **3–6× too FEW**.
   2025: model **176** system load-weighted hours < $0 against **1,018** actual RT and **610**
   actual DA. The SPP-63 ceiling took 167 → **0**, i.e. *away* from the market. §2.
3. **The binding object is the THERMAL MIN-LOAD FLOOR, not a wind constraint** — which SPP-51c
   already root-caused ("the binding limb is R-2, the thermal-commitment floor") and which this
   lane now sizes. An existing, default-off, measured mechanism implements it exactly:
   `coal_mustrun_online_pmin` + `coal_sync_srmc_tranche`, whose own flag help reads *"so coal
   holds at its measured synchronization floor instead of **price-following to zero**"* — SPP's
   §2.3 defect verbatim. §4.
4. **AND IT IS TOO SMALL TO CLOSE C1, which this lane states against its own hypothesis and
   before solving.** Predicted **+0.85 TWh/yr** coal (range 0.02–1.38) against a **9.99 TWh**
   fossil miss — **~8.5 %** of the gap. It is chartered on rule 1 `[R-STRUCT]` / rule 14
   `[R-ACCURATE]` (the model is measurably wrong about a physical fact) and **not** on the
   residual. **This lane does not expect SPP to become calibrated.** §5.
5. **SPP's two registered runs are not a valid per-year control at HEAD** — both predate the
   rule 36 `[R-YEAR-ISOLATION]` warm-start flip (`cb1e60b7`, 2026-09-19) and both were solved as
   single multi-year invocations. So rule 29 `[R-SCREEN]` (b) form 4 is void here for a stated,
   documented reason, each shard solves its own control, and this lane delivers the **first
   measurement of the rule-36 contamination in SPP**, which rule 36(f) flags as UNMEASURED. §6.

---

## 1. Phase 0 item 1 — the census reproduces, and ONE number moved

`scripts/probes/_spp50_curtailment_headroom_census.py`, all four legs, re-run at base
`608cb21f`. **Every SPP number reproduces exactly** — the elasticity table, the OLS triplet
(`+0.911/+2.209`, `+0.785/+9.942`, `+0.731/+1.660`), the coal-floor table, the seven-year
wind/headroom table (`+10.1444` / `−9.9895` / `+0.1549`), and the decile table.

**One number moved, and it is not SPP's.** Cross-ISO census leg D, MISO row:

| field | SPP-50 (base `e5f966fd`) | here (base `608cb21f`) |
|---|---|---|
| MISO mean fossil | −16.566 | **−18.157** |
| MISO cancel | −11.926 | **−13.517** |

**Cause, identified rather than assumed:** MISO promoted `2026-09-19-miso-263-coal-ceiling`
(`af20325a`, merged `feb5155c`) between the two bases, so leg D reads a different MISO
registered set. MISO's wind ratio is unchanged at 1.0515 / sd 0.0000. This is another ISO's
lane doing its job, not drift in a shared input, and **no SPP quantity is affected**. Reported
as a finding per the charter rather than as a footnote. Rule 25 `[R-ISO-SCOPE]`: nothing about
MISO is acted on here.

---

## 2. The measurement that re-frames the lane — the model has too FEW negative hours

Committed `hourly/system_<year>.parquet` (P1, load-weighted across both zones) against the
committed `data/raw/_validation-source/actual_lmp_hourly_SPP.parquet`. Both are on the
SPP-51c-repaired clock.

| year | model h < $0 | model h at exactly −26.000 | model h < −26 | **actual RT h < $0** | actual RT h < −26 | actual DA h < $0 |
|---|---|---|---|---|---|---|
| 2019 | 0 | 0 | 0 | **547** | 22 | 165 |
| 2020 | 41 | 41 | 0 | **936** | 96 | 404 |
| 2021 | 243 | 232 | 0 | **1,108** | 118 | 639 |
| 2022 | 294 | 282 | 0 | **995** | 69 | 479 |
| 2023 | 237 | 200 | 0 | **992** | 77 | 483 |
| 2024 | 225 | 169 | 0 | **1,172** | 100 | 641 |
| 2025 | 176 | 126 | 0 | **1,018** | 86 | 610 |

Three things this fixes in the lane's framing:

* **The model is short of negative-price hours by 3–6×**, in all seven years. Whatever closes
  SPP's price floor must produce MORE negative hours, not fewer. The ceiling produced **zero**.
* **The model's floor is structurally exactly −26.000** — wind's flat `−ira_ptc_wind` offer —
  and it never goes below, in any year or zone. The market goes below −26 in **22–118 h/yr**.
  That residual is **not reachable by any mechanism in this lane** and is named in §7 as a
  successor, not claimed here.
* **Essentially every model negative hour is a wind-marginal hour** (126–282 of them sitting at
  exactly −26.000). So wind *is* already the price-setter when it is interior — the defect is
  that it is interior far too rarely.

---

## 3. Phase 0 item 2 — the constraint row, specified, and the literal charter killed

Wind enters as a bounded column (`model/lp/bounds.py:96-105`, `model/lp/costs.py:100-103`):
`0 ≤ W[z,t] ≤ cf[z,t]·cap[z]·curtail_share[z,t]`, cost `c_W = −ira_ptc_wind = −26.0`. Energy
balance is the equality row whose dual **is** the zonal price λ[z,t] (rule 4 `[R-DUALS]`).

Stationarity for W in hour t, with `μ⁻, μ⁺ ≥ 0` the bound multipliers and a candidate row's
dual ν entering with coefficient a:

```
c_W − λ[z,t] + a·ν − μ⁻ + μ⁺ = 0
```

**Form A — per-hour cap `W[z,t] ≤ K[z,t]` (a = 1, one row per zone-hour).** The row and the
bound `W ≤ K` define the **identical feasible region**. At the optimum W = K, W is at a bound of
the row, and λ is set by whichever *other* column is marginal; the row's dual merely absorbs the
rent, `ν = λ − c_W`. **λ is unchanged.** This is the ceiling, renamed. **KILLED — and this is
the charter's own kill criterion, applied to the charter's own object.** It also explains
SPP-63 exactly: removing wind's ability to be interior removed every negative hour (167 → 0).

**Form B — cross-hour energy budget `Σ_t W[z,t] ≤ E_z` (a = 1, ONE row, dual ν ≥ 0 in $/MWh).**
Here the algebra does work: for any hour where W is interior, `λ[z,t] = c_W + ν = −26 + ν`. The
dual genuinely enters the price. **Rejected anyway, on two independent grounds, neither of them
the residual:**
* *Rule 13 `[R-MEASURED]` forward test.* An annual budget fixed at `(1 − 0.0965013)·Σ potential`
  forces exactly 9.65 % curtailment in a forecast year **whatever the net load does**. It cannot
  "respond to changed conditions" — it is the measured *outcome* re-imposed, which is precisely
  what rule 13 forbids. It is also not a physical object: nothing in SPP enforces an annual wind
  energy cap.
* *It moves the price the wrong way.* ν ≥ 0 **lifts** the floor off −26.000 uniformly, reducing
  negative hours — against §2, which says the model needs 3–6× more of them.

**Conclusion, and the one place this lane departs from its charter.** The charter's operational
test — *"a mechanism whose dual does not reach the energy balance price is the ceiling again"* —
is **mis-specified as a screen for this object**, and applying it literally rejects every
admissible candidate including the correct one. Prices *are* duals (rule 4), and λ is set by
**which column is marginal**. The ceiling fails not for lacking a dual but for **removing wind's
ability to be marginal**. The correct test, which this lane adopts and states here before
solving, is:

> **Does the mechanism change WHICH column is marginal in the hours it binds?**

Form A fails it (wind is at a bound either way). Form B passes it but fails rule 13. **The
thermal min-load floor passes it**: forcing coal on in an oversupply hour pushes wind off its
upper bound and makes **wind** the marginal column, taking λ from coal SRMC (~$16–20) to
−26.000. That is the market's own mechanism — *curtailment IS the negative-price event*, as this
cell's own matrix text already says — and it is the object §4 arms.

---

## 4. Phase 0 item 3 — the mechanism, and ZERO free parameters

**ARM, for SPP only:** `coal_mustrun_online_pmin=true` **and** `coal_sync_srmc_tranche=true`
(the second is inert without the first — `fleet/assembly.py:524-532` conjoins them).

What it does (`fleet/campd_bins.py:1341-1356`, `fleet/assembly.py:505-535`,
`fleet/arrays.py:2875-2903`): the coal min-load band is re-sized from the all-hours available-CF
`mustrun_pct` to the **measured online-net-MW synchronization Pmin** `mustrun_online_pct`, split
by the measured take-or-pay share into a fuel-free `_mustrun` tranche and a full-SRMC `_sync`
tranche, and **both are forced on** via `coal_sync_pmin_mw → min_gen`, which replaces `pmin` as
the LP lower bound.

**Why SPP needs it, measured** (`data/raw/_processed-legacy/thermal_tranches_SPP.csv`, 24
`status=ok` COAL rows, 17,810 MW nameplate):

| | MW | plants at zero |
|---|---|---|
| current band (`mustrun_pct`, keeper posture) | 2,855.2 | **12 of 24** |
| online-Pmin band (`mustrun_online_pct`) | **4,090.3** | 0 |

**Half of SPP's coal fleet carries no min-load band at all today**, while CAMPD says every one
of them holds 7.9–60.0 % of nameplate when synchronized. That is the rule 14 `[R-ACCURATE]`
basis, and it is a fact about the fleet, not about the residual.

**DOF ledger — zero new free parameters (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`).** Both fields
are existing registered `ScenarioConfig` booleans with CLI flags; every number they consume
(`mustrun_online_pct`, `online_frac`, the take-or-pay share) is a **measured column of a
committed artifact**, frozen under rule 23 `[R-FROZEN-DERIVE]` and not re-derived here. No
level, depth, share, multiplier or shape constant is introduced, and **nothing is swept**.

**Rule 19 `[R-ONE-MECH]` — what already floors SPP coal: NOTHING.** `reliability_floor=false`,
`coal_mustrun_online_pmin=false`, `coal_sync_srmc_tranche=false`, `spp_gas_commitment_bridge=false`,
`class_commitment_overrides={}`, `reliability_floor_overrides={}` in the keeper's own
`run_config.json`; SPP-51c measured the model's thermal annual minimum at **254.3 MW across a
~40 GW fleet**. This **replaces nothing and stacks on nothing** — it is SPP's first commitment
floor. It is explicitly **reconciled with** the already-armed `vre_curtailment_oversupply_allocation`
water-fill as SPP-51c required: the water-fill concentrates the headroom into the low-net-load
hours, and this floor is what makes the LP unable to absorb it there.

**Rule 25 `[R-ISO-SCOPE]`.** Arming is per-run CLI, SPP only. Shared dataclass defaults stay
`False`; no other ISO's config, artifact or keeper is touched, and **no verdict is transferred**
— PJM and MISO arm parts of this family in their own runs and that is neither evidence for nor
against SPP. No code is changed, so every other ISO is byte-identical by construction.

---

## 5. Phase 0 item 4 — THE PREDICTION, recorded before the solve

Computed at zero LP on the keeper's own committed `class_hourly`/`system` sidecars plus the
committed tranche artifact: aggregate floor per hour under the mechanism's **as-coded** top-k
peak-load window, deficit `Σ_t max(0, F_t − coal_t)`.

| year | model coal TWh | **predicted coal added (TWh)** | h below floor |
|---|---|---|---|
| 2019 | 80.731 | +0.022 | 83 |
| 2020 | 65.142 | +0.702 | 983 |
| 2021 | 94.585 | +0.930 | 697 |
| 2022 | 98.588 | +0.899 | 687 |
| 2023 | 70.831 | +1.339 | 982 |
| 2024 | 64.794 | +1.380 | 1,269 |
| 2025 | 84.798 | +0.672 | 606 |
| **mean** | | **+0.849** | |

**Cross-checked independently:** census leg B measures the model sitting below the real fleet's
own p1 floor by **0.62–1.25 TWh/yr**. Two unrelated routes land on the same ~1 TWh. A
correctly-windowed floor (same MW, every hour, scaled by `online_frac`) would give **+1.554
TWh/yr** — so the as-coded window costs ~45 % of the available effect (§7, R-bd).

**Signed predictions, all falsifiable, all recorded before the solve:**

| # | quantity | predicted direction | predicted magnitude |
|---|---|---|---|
| P-1 | C1 COAL_PRB + COAL_LIGNITE | **UP** | +0.85 TWh/yr mean (0.02–1.38) |
| P-2 | C1 wind | **DOWN** | ≈ equal and opposite, −0.6 to −0.9 TWh/yr |
| P-3 | **C1 gap closure** | partial | **~8.5 %** of the 9.99 TWh fossil miss |
| P-4 | system hours < $0 | **UP** | 149–293 → several hundred; still short of 1,018–1,172 actual RT |
| P-5 | C3a mean LMP | **DOWN** | the model is too expensive (SPP-47: +$5.05 in 2020, 10 of 12 months high), so down is toward the market |
| P-6 | C3b monthly NRMSE | **DOWN (improves)** | the floor gap (+$6.81, model min month $16.46 vs $9.65) narrows |
| P-7 | model price < −26 | **UNCHANGED at 0** | structurally unreachable; §7 |

**P-4/P-5/P-6 are the opposite sign from the SPP-63 ceiling** (which took negative hours to 0,
lifted load-weighted price +6.1 % and blew C3b 0.167 → 0.253). **That sign flip is this lane's
central claim** and the single cleanest way to falsify it.

**The named risk, pre-registered rather than discovered later.** Rule 20 `[R-FORCED-BUDGET]`
caps a material merchant class at 30 % of its energy at binding floors. The floor **capacity**
is 29.5–44.9 % of coal energy — a loose upper bound on the D-2 statistic, which counts energy at
a *binding* floor and will read lower, but **C8 is the protective gate genuinely at risk and it
may fail.** If it does, rule 20's conditional-pass route requires a cited `D4_WINDOWS` entry and
a D-1 shape pass; **the as-coded peak-load window is the wrong window for an oversupply floor
(§7) and may well fail D-4.** This lane will report that outcome rather than re-cut anything.

---

## 6. Rule 29 `[R-SCREEN]` (b) — why form 4 is void here, and each shard solves its own control

Not a code-hunk argument. **Both SPP registered runs predate the rule 36 `[R-YEAR-ISOLATION]`
default flip** (`cb1e60b7`, 2026-09-19 — verified with `git merge-base --is-ancestor` against
`1f586ed7` and `11066408`: both **NO**), and both were solved as **single multi-year
invocations** with `MARKET_SIM_WARMSTART_XYEAR` / `MARKET_SIM_P1_BASIS_SEED` ON. Rule 36(e)
**withdraws** the neutrality claim for those knobs, and 36(f) states every keeper carries the
artifact and **its size in SPP is UNMEASURED**.

So the keeper's committed numbers are **not** a like-for-like control for a per-year solve at
HEAD, and differencing against them would confound the mechanism with the contamination. The
solve-path drift is also large and live on this lane's own files (`1f586ed7..HEAD`: 62 files,
+8,701 lines, including `renewables.py` +146, `lp/bounds.py` +16, `lp/costs.py` +8,
`floor_mechanisms.py` +23) — a LIVE hunk, which rule 29(b) says is what earns a control solve.

**Each shard therefore solves TWO legs at one pinned HEAD: CONTROL (keeper recipe, unchanged)
and ARM (the single `--set` delta).** Both via `scripts/replay_keeper.py`, so the recipe is the
keeper's by construction and the only difference is the two booleans. SPP is a 2-zone ISO
(~150 s/year), so both legs fit one shard far inside rule 32's 20-minute ceiling.

**Free deliverable, and it is owed:** control(HEAD, isolated year) − keeper(committed) is the
**first measurement of the rule-36 cross-year contamination in SPP**.

---

## 7. Successors, named now so they are not rediscovered

* **R-bd — the floor's WINDOW is wrong for this driver.** `fleet/arrays.py:2884-2903` places the
  sync floor on the **top-k system-PEAK-LOAD hours** (`_COAL_SYNC_FORCE_ALL = 0.99`; SPP's
  `online_frac` tops out at 0.987, so **no SPP coal plant** gets an all-hours floor). But the
  zero-coal hours sit in the **bottom 6–14 % of load** (median load rank 0.055–0.139), so the
  as-coded window covers only **24–52 %** of them (capacity-weighted 25.6–52.1 %). Rule 17
  `[R-FLOOR-WINDOW]` wants the window to match the driver, and a synchronized coal unit is
  synchronized *through the overnight trough*. The physically right ranking is **net** load, not
  load — and it regenerates forward (more wind → lower net load → more cycling), so it is
  rule-13 admissible. **Not done here** because that function is shared and PJM/MISO runs arm
  this family (rule 25); it needs its own gate and its own PRECOMMIT.
* **R-be — the price floor below −26 is structurally unreachable.** The model's minimum is
  exactly `−ira_ptc_wind = −26.000` and `dump_cost ≈ 26.001` caps it at −26.001; the market goes
  below −26 in 22–118 h/yr. No floor, ceiling or allocation reaches this. It needs a wind offer
  that is not flat (vintage/PTC-eligibility heterogeneity), which is `wind_ptc_vintage_offers` —
  **currently default-off and NOT re-proposed here.**
* **R-ba (unchanged) — the ST_GAS / CT_PEAKER merit-order inversion.** ST_GAS short −3.94 to
  −8.66 TWh in every one of seven years and worsening. Untouched by this object.

---

## 8. Governance

* **Rule 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`:** chartered on the measured fact that SPP's real
  PRB fleet never falls below 8.1–17.5 % of its own annual max while the model takes it to
  exactly 0.0 MW, and that 12 of 24 SPP coal plants carry no min-load band at all. **Not** on
  the residual — §5 predicts it closes only ~8.5 % of C1 and says so before solving. No offer
  curve is touched; the band multipliers stay at the keeper's uniform 0.93 and are **not**
  proposed as the closer (DO-NOT-REDO respected).
* **Rules 21/24:** zero new fields, zero new free parameters; `build_dof_ledger.py --iso SPP
  --check` is run against the arm bundle.
* **Rule 28 `[R-MECH-MATRIX]`:** `coal_sync_srmc_tranche` and `coal_mustrun_online_pmin` are
  **absent from the matrix in every one of the nine shards** — a pre-existing duty-(c) gap, not
  this lane's. Since this lane TESTS them, it adds the two base rows plus a cell line in **every**
  ISO shard, in this lane's PR, and mints **SPP's cells only** (rule 28(d)).
* **Rules 32/34/36:** the parent runs no LP; **one shard per year, seven years** (2019–2025, the
  union of SPP's two registered runs, enumerated before anything is pruned per rule 35(b)); each
  shard pushes its **full** bundle including `dispatch/<year>_P1.parquet` via a `.gitignore`
  negation and a **plain** `git add`.
* **Rule 31 `[R-RETAIN]`:** nothing is deleted, and the promotion question is asked explicitly in
  the RESULT before this session ends.
* **`[R-HOLDOUT]` is removed:** no year is protected, so every number here is model-**SELECTION**
  evidence and none of it is a certified out-of-sample skill claim.

---

## 9. CORRECTION to §8, recorded before any result was read

§8 states that `coal_sync_srmc_tranche` and `coal_mustrun_online_pmin` are "absent from the matrix
in every one of the nine shards" and that this lane owes two new base rows. **That is wrong, and
the error was mine.** Both are registered — as **SUB-SCALARS inside the `coal_mustrun_per_plant`
family row's `def`** (`docs/codebase-site/data/mechanism-matrix.js:1753-1754`), which is the
repo's documented rule 28(c) convention from the xiso-3 census for a field that SIZES or SPLITS
another row's own tranche. My grep matched only top-level `id:` keys and so missed them.

**Consequence: this lane owes NO new base row and NO nine-shard cell fan-out.** It owes exactly
what rule 28(b) requires — an update to **SPP's own cell of `coal_mustrun_per_plant`**, which
currently reads `U` ("SPP-21 shard seed, no verdict minted"). Nothing else about §4–§7 changes;
no prediction, gate or magnitude is affected, and no solve had run when this was written.

Also recorded, since it is the DO-NOT-REDO check this correction makes readable: the family's
sub-scalars are `K` at MISO (`coal_mustrun_online_pmin`, keeper `2026-08-04-miso-127-onlinepmin`)
and armed on PJM's keeper. Rule 28(d): **neither transfers.** SPP enters as `U` and derives its
band from its own `thermal_tranches_SPP.csv` CAMPD conduct, which is what §4 does.
