# PRECOMMIT — pjm-h14: PJM's COAL_BIT over-run is TWO UNMEASURED DEFAULTS COMPOUNDING on the coal synchronization floor. Test `coal_mustrun_requires_measured_row` (2026-09-20)

**Session:** pjm-h14 · **Branch:** `claude/serene-feynman-l0ldz5` · **ZERO LP IN THE PARENT**
(rule 32 `[R-SHARD]` (a)). Six shards, **one year each** (rule 36 `[R-YEAR-ISOLATION]` (a)).
**Keeper under test:** `2026-09-20-pjm-h13-meritalloc-span` (2023–2025, CALIBRATED, eight criteria
PASS, zero caveats) + folded touchpoint `2026-09-20-pjm-h13-meritalloc-touchpoint` (2020–2022,
NOT-YET).

**EVERY GATE BELOW IS FIXED BEFORE ANY SOLVE AND IS NEVER RE-READ ONCE A NUMBER LANDS.**

---

## 0. The chartered lever, and where phase 0 took it (rule 28(a))

The handoff's **LEVER A** was *"COAL_BIT's economic over-run in 2020-2022 … localise the over-run by
season/zone/load-decile before proposing any mechanism"*, with the rules 1/13 offer-curve band
multipliers named as an available authorized channel. Phase 0 did exactly that localisation and it
**did not land on the offer curve**. It landed on a floor, which is a better card under rule 1
`[R-STRUCT]`: a structural repair with **zero free parameters** beats a declared multiplier.

What the localisation said, in order (probes §7):

1. **The over-run is a LEVEL defect, not a shape one.** The 2020 Δ is **+0.56 to +1.36 TWh in every
   one of the 24 hours of the day** and positive in **every one of the ten load deciles**
   (d1 +1.30 … d10 +3.08). A merit-order or peak-hour story predicts neither.
2. **It is not a swap with gas.** On the SCORED basis (`classFull`, the series C1 uses) 2020 reads
   COAL_BIT **+28.128** with CC_REGULAR **+0.265** — gas is essentially exact — and the hourly
   mirror test is weak in both years (corr(Δcoal, ΔCT) = −0.005 in 2020, −0.219 in 2021). LEVER B's
   "pure merit-order shift between coal and CT" is **not supported by the hourly data**, and this
   PRECOMMIT records that rather than assuming it.
3. **It is not forcing, on D-2's own reading** — `coal_mustrun` forces 2.05 TWh (1.23 % of class) in
   2020 and 0.75 TWh (0.39 %) in 2021, exactly as the handoff said. **That reading is incomplete,
   and §3 shows why.**
4. **The model does not TURN COAL OFF.** Per-plant, 2020: Cheswick is metered offline **6,868 of
   8,760 h** (median CF 0) and the model runs it with **744** off-hours at median CF 65; Avon Lake
   is metered off 8,042 h and modelled off 4,344. The 2021 miss is **+21.38 of +23.98 TWh** on the
   measured-CF 0.10–0.45 **cyclers**.

---

## 1. The defect, stated as a fact about code and named plants

Two independent unmeasured defaults compound on the same population.

**(i) The tranche default.** A coal plant absent from the ISO's CAMPD thermal-tranche artifact falls
through `campd_bins._DEFAULT_TRANCHE_PCT_BY_GROUP["COAL"] = (45.0, 5.0, 2.0)` and is handed a
**45 %-of-nameplate must-run tranche** — while that constant's own comment describes its population
as *"rarely-online units with no reliable observed floor"* (`campd_bins.py:1245-1258`, applied at
`:2480-2484`).

**(ii) The window default.** `assembly.py:542` resolves the rule-17 window as
`coal_sync_online_frac(...).get(plant_code, 1.0)`, and its own comment says
*"Plants absent from the artifact keep the force-all default (1.0)."* In
`arrays.py::_compose_min_gen_floors` that `frac` is what relaxes a **measured** cycler's floor to its
top-`frac` load hours; at 1.0 the floor is held in **all 8,760 hours**.

**So the plants with the LEAST evidence carry the STRONGEST and WIDEST floor** — the exact inverse of
both defaults' stated intent. Rule 17 `[R-FLOOR-WINDOW]` fails on all three clauses: no external
driver, no hours-it-may-bind justification, no forward story.

**Why the population is large, and why re-deriving does not close it.** The committed
`thermal_tranches_PJM.csv` has **no `year` column** and is derived on **2023–2025** — identified here
by re-running that window against the **frozen** deriver and recovering a **byte-equal key set**
(256 rows, 29 COAL, same keys). Its plant universe is `load_fleet_from_csv(iso, cfg)`, a **year-blind
current-vintage EIA-860 fleet**, so every coal plant that ceased operating before that vintage is
absent **in every derive year**: six per-year re-derives with the frozen script **gained ZERO rows**.
Meanwhile the backcast fleet still contains them.

Measured on the model's own fleet (`run_year(..., fleet_only=True)`, zero LP):

| | plants | MW | asserted must-run | TOTAL metered output |
|---|---:|---:|---:|---:|
| **uncovered (2020)** | **36** | **15,774.7** | **58.04 TWh** | **22.97 TWh** (2.5×) |
| covered (2020) | 29 | 33,597.0 | 65.14 TWh | 121.36 TWh |

The roster the arm is chartered on, 2020, asserted must-run vs whole-year metered:

| plant | MW | asserted | metered |
|---|---:|---:|---:|
| FirstEnergy Bruce Mansfield | 2,490 | **9.82 TWh** | **0.00 TWh** |
| W H Sammis | 2,210 | 8.71 | 4.56 |
| Homer City | 1,888 | 7.44 | 2.86 |
| Conesville | 1,530 | 6.03 | 1.18 |
| Chalk Point Steam | 670 | 2.64 | **0.00** |
| Avon Lake | 627 | 2.47 | 0.27 |
| Dickerson | 519 | 2.05 | **0.00** |

**AND THE MODEL'S COAL FLEET IS ITSELF YEAR-BLIND — reported, not taken.** The same 65 plants /
49,372 MW appear in 2020 *and* 2024, so Bruce Mansfield (retired 2019) and Conesville (retired 2020)
are carried into 2023–2025 as well. That is the `eia860_vintage_tracks_solve_year` object, one level
upstream, and **this lane does not take it** (rule 19 `[R-ONE-MECH]`): bundling a fleet-vintage
change with a floor change would make any verdict unattributable, which is precisely what cost
pjm-h12 its charter. It is named here so a successor has it.

**Why D-2 reads only 1.23 %.** D-2 counts `coal_mustrun` forced energy as the MWh the LP would not
have produced anyway. A floor placed on a **cheap** tranche of a plant the LP already wants to run
mostly does not register there — which is exactly why rule 17's instrument is **D-4**, and why §2's
first deliverable exists.

---

## 2. The two deliverables

### 2.1 The DIAGNOSTIC repair (no solve path, no dispatch, no criterion)

`MECH_COAL_MUSTRUN` carried **no `D4_WINDOWS` entry**, so **D-4 emitted no coal rows in any ISO** and
the coal synchronization floor was the one commitment floor the rule-17 diagnostic could not see.
Verified on the incumbent keeper pair's own committed `legitimacy_diagnostics.json`: the D-4 `floor`
set is `{cc_mustrun_per_plant × CC_REGULAR, chp_steam, ct_netload_drag, st_netload_drag}` — **zero
coal rows**. That is the state rule 20 `[R-FORCED-BUDGET]` describes in terms.

`(MECH_COAL_MUSTRUN, None): (0, 24)` is added. The window is **(0, 24) by driver**: the floor is
already hour-of-day-blind and instead load-ranked, so there is no hour-of-day its driver says the
plant is off, and what D-4 then scores is entirely the **per-plant conduct leg** —
`fail = median(measured MW over the plant's own BINDING hours) <= 0`.

**It cannot move a criterion, by construction.** Coal's D-2 forced share is 0.39–3.74 % of class
energy against rule 20's 30 % budget, so the over-budget escalation that reads D-4 never engages.
New coal D-4 rows on the CONTROL are a **REPORTED rule-17 finding on the incumbent**, not a
determination change, and are published at full magnitude either way.

### 2.2 The MECHANISM

`coal_mustrun_requires_measured_row` (`scenarios.py`, dataclass default **`False`**). Armed, a COAL
plant with **no measured row** in the ISO's thermal-tranche artifact carries **no must-run tranche**;
that capacity falls to the **economic band**, so the plant keeps every MW and the LP decides it on
price. The synchronization floor goes with it as a **CONSEQUENCE, not a second mechanism** (rule 19):
`assembly.py` sizes `coal_sync_pmin_mw` from the `mustrun`/`sync` tranche capacity, so a zero
must-run leaves nothing to floor. **One seam** (`campd_bins.py::fleet_to_bins`, at the existing
fallback line).

- **Rule 21 `[R-DOF]`: ZERO free parameters.** The arm asserts no level and adds no scalar — it
  **withdraws** an assertion that has no measurement behind it. There is no value to tune.
- **Rule 23 `[R-FROZEN-DERIVE]` is NOT engaged.** Nothing is re-derived and no committed value moves.
  xiso-5's standing refusal to REGENERATE `thermal_tranches_<ISO>.csv` without a cited data change is
  untouched, and this arm deliberately does not need it.
- **Rule 13 `[R-MEASURED]`: forward-native**, not a backcast overlay (it is not in
  `_BACKCAST_ONLY_OVERLAY_FIELDS`). In a forecast year "does this plant have observed commitment
  conduct?" is the same question with the same answer shape.
- **Rule 25 `[R-ISO-SCOPE]`:** gated default off; no other ISO's keeper moves, and PJM's cell enters
  as its own test (`U` → this lane's verdict).

---

## 3. G-DRIFT (rule 29 `[R-SCREEN]` (b)) — form 4 is VALID, NO control solves

Audit window `<keeper basis_sha> → HEAD`, recorded in §7 of the RESULT once the six legs land.
pjm-h12 measured `hubs.py::_basis_bridge_blackouts` at **nil** for PJM (2022 control reproduced the
committed keeper, **0 of 78,840 price cells moved**) and pjm-h13 re-audited the following window with
every hunk INERT. **The keeper pair's committed bundles ARE the control** — six arm shards, no
control solves.

**Control config signature (both bundles):** `mode=backcast`, `use_campd_bins=True`,
`coal_mustrun_per_plant=True`, `coal_mustrun_online_pmin=True`, `coal_sync_srmc_tranche=True`,
`coal_bit_passthrough_sigmoid=True` (floor 0.65), `netload_drag_merit_allocation=True`,
`mustrun_plant_exclusions=False`, `mustrun_commitment_feasibility_clip=False`, and
**`coal_mustrun_requires_measured_row` ABSENT (the field is new at this HEAD; unarmed it is False and
the control bundles are byte-identical)**.

---

## 4. THE GATES — declared ex ante, never re-read

**Baselines, read off the incumbent keeper pair's own committed artifacts:**
- C1 COAL_BIT Δ TWh: 2020 **+28.128**, 2021 **+20.744**, 2022 **+3.543**, 2023 **+2.090**,
  2024 **−1.175**, 2025 **+8.173**.
- D-4 coal rows: **ZERO** (no `D4_WINDOWS` entry). The control's coal D-4 baseline is therefore
  **produced by this lane's own §2.1 change and reported before the arm is scored**.
- Determination: span **CALIBRATED**, eight criteria PASS, zero caveats; touchpoint **NOT-YET**.

| gate | bar | kills the card if |
|---|---|---|
| **G1 — the arm fires, and conserves capacity** | coal must-run tranche capacity falls by > 0 MW in **every** year **and** total coal capacity is unchanged to **< 1 MW** in every year | it is inert, or it is secretly a capacity change rather than a band swap |
| **G2 — SCOPE: only UNMEASURED plants move** | **zero** plants carrying a measured artifact row change their must-run tranche, in **every** year | it reaches past its own population (rules 19/25) |
| **G3 — RULE 17 IS SERVED** *(this lane's justification gate)* | on the arm, D-4 `coal_mustrun` **conduct FAIL rows fall to ZERO in every year**, i.e. no plant is left floored across hours whose own meter reads a zero median | the card's own justification fails |
| **G4 — the NAMED plants** | **Bruce Mansfield (6094), Chalk Point Steam (65285) and Dickerson (65284)** — metered **0.000 TWh** in 2020 — carry **zero** coal must-run floor MW on the arm, in every year | it repairs a different population than the one it was chartered on |
| **G5 — nothing stacked** | no mechanism **outside the coal must-run family** moves its D-2 forced share by > **0.5 %** in any year | it is not one mechanism |

**G5 is scoped by FAMILY, not by D-2 id** — pjm-h13 correction #2, discharged before the solve. The
appliers this flag reaches are enumerated now: the single seam `campd_bins.py::fleet_to_bins`
(must-run tranche %), and through it, by construction, `assembly.py`'s `coal_sync_pmin_mw` /
`coal_sync_online_frac` and `arrays.py`'s `MECH_COAL_MUSTRUN` floor. **The coal must-run family is
therefore `{coal_mustrun}` plus the tranche split itself**; every other D-2 id is "outside".

**G3 is this lane's G6** — the gate written to test the card's own justification, which is what
caught pjm-h12's charter and what pjm-h13's G3 was.

### 4.1 THE ASYMMETRY — what is REPORTED and can never move a gate (rule 1 `[R-STRUCT]`)

Written down **before** the solve, so no number can be re-read into a criterion:

- **Every scored band — C1, C2, C3a, C3b, C3c, C4, C8 — and the determination itself.** A
  structurally-correct mechanism **stays in even if the residual worsens**, and nothing here is
  selected because a residual moved. **COAL_BIT's C1 miss is the REASON the lane looked, and it is
  NOT a gate**: if COAL_BIT gets worse and G1–G5 pass, the card still stands and the regression is
  surfaced to the owner as a promotion fact (rule 30(c): a held-out year never downgrades the ISO).
- **The training span 2023–2025.** The arm touches 36 uncovered plants there too, so the span can
  move. A downgrade from `CALIBRATED` is **reported, never used to select or reject** the mechanism.
- **The control's NEW coal D-4 rows** (§2.1) — a rule-17 finding on the incumbent, published at full
  magnitude.
- **The model's year-blind coal fleet** (§1) — named, routed to a successor, not taken.
- **Price, trough price, seam flow, D-A diurnal amplitude.** This card makes **no** price prediction.
  pjm-h12's G4/G5 made these gates on a causal chain and refuted 0/6; this charter does not repeat it.

### 4.2 Stated as a LIMIT, not buried — two things phase 0 does NOT establish

**(a) A PRE-SOLVE FOOTPRINT DOES NOT PREDICT A D-4 VERDICT** (pjm-h13 correction #3, and pjm-h13
mis-predicted through this same limit after flagging it). Every number in §1 is a **tranche capacity
and the floor it implies**, before availability clipping and before the LP. D-4 scores the hours the
floor **binds in the solved dispatch**. **Only the solve can move G3.**
**(b) The arm removes a floor; it does not remove a cheap BAND.** The released capacity lands in the
economic band and can still clear on price, so the C1 response may be far smaller than 58 TWh — and
under §4.1 that is not a criterion in either direction.

---

## 5. Shard plan (rules 32 / 34 / 36)

Six shards, **one year each**, all against their own committed control, all pushing their **full**
bundle including `dispatch/<year>_P1.parquet` (rule 34(a): `.gitignore` **negation** scoped to the
per-year legs + **plain `git add`**, never `git add -f`).

| year | source bundle | out-dir | branch |
|---|---|---|---|
| 2020 | `pjm_h13_meritalloc_touchpoint` | `results/calibration/pjm_h14_coalmustrun_2020` | `claude/pjm-h14-coalmustrun-2020` |
| 2021 | `pjm_h13_meritalloc_touchpoint` | `…_2021` | `claude/pjm-h14-coalmustrun-2021` |
| 2022 | `pjm_h13_meritalloc_touchpoint` | `…_2022` | `claude/pjm-h14-coalmustrun-2022` |
| 2023 | `pjm_h13_meritalloc_span` | `…_2023` | `claude/pjm-h14-coalmustrun-2023` |
| 2024 | `pjm_h13_meritalloc_span` | `…_2024` | `claude/pjm-h14-coalmustrun-2024` |
| 2025 | `pjm_h13_meritalloc_span` | `…_2025` | `claude/pjm-h14-coalmustrun-2025` |

Arming needs **no further code change**:
`replay_keeper.py <source> --out-dir <dir> --years <year> --set coal_mustrun_requires_measured_row=true --note "<...>"`.

Rule 34(c): PJM's registered year set is **{2020, 2021, 2022, 2023, 2024, 2025}**, enumerated from
the two sidecars **before** anything is pruned (rule 35(b)). All six are launched; none is omitted.

**Retrievability (rule 34(e)):** each bundle lands on its shard branch and the parent composes and
lands the keeper bundles on `main` **before** its PR merges (rule 33(f)(4)(ii)). Shard branches are
transport, not storage.

**Composition (rule 32(d)):** the parent composes the per-year legs into a span (2023–2025) and a
touchpoint (2020–2022), **regenerates `legitimacy_diagnostics.json` over each COMPOSITE with
`--json-out`** (pjm-h13 correction #1 — per-leg D-4 borrows `ct_only` vintage flags across sibling
years and is **not** comparable to a composed span), rebuilds the benchmark parquets
(`run_calibration_full.py --rebuild-benchmark`, correction #5), scores, and registers with
`--no-prune`.

---

## 6. What this lane will NOT do

- **Not re-test `mustrun_commitment_feasibility_clip`** — `R` at pjm-h12 D-3 (rule 28(a) DO-NOT-REDO).
- **Not rebuild an hourly seam ladder** — killed at zero LP by pjm-h12 D-2.
- **Not arm `mustrun_plant_exclusions`** in the same run — a different floor family; bundling it
  makes any verdict unattributable.
- **Not take the year-blind coal fleet** (§1) or `eia860_vintage_tracks_solve_year` — named, routed.
- **Not REGENERATE `thermal_tranches_PJM.csv`** — xiso-5's rule-23 refusal stands and this card does
  not need it.
- **Not touch the three truncated ladder rungs (Q1)** or any other open owner question (Q3–Q6, the
  pjm-h12 D-3 promotion, the proposed rule 32(c)(8) addendum). All carried forward in the RESULT.

---

## 7. The phase-0 probes, all committed, all zero LP

| probe | what it establishes |
|---|---|
| `pjm_h14_coal_phase0.py` | the over-run is flat in hour-of-day and present in every load decile; the mirror test against CT/CC |
| `pjm_h14_balance_phase0.py` | the C1 class table on the SCORED `classFull` basis; CC_REGULAR is exact in 2020/2021 |
| `pjm_h14_coal_plants_phase0.py` | per-plant attribution; the lay-up and cycler cohorts; model-vs-meter off-hours |
| `pjm_h14_tranche_census_phase0.py` | artifact coverage per year; the 45 % fallback roster; the rule-17 statement |
| `pjm_h14_vintage_footprint_phase0.py` | the six per-year re-derives gain **zero** rows; the covered cohort's own-year drift |
| `pjm_h14_fleet_tranches_phase0.py` | the model's OWN coal tranches via `fleet_only=True` — 36 plants / 15.8 GW / 58.04 TWh asserted |
| `pjm_h14_arm_footprint_phase0.py` | control-vs-arm tranche capacities: G1/G2's pre-solve footprint |
