# FINDING — SCN-WS5A-RESOLVE: ruling S8 executed, the contaminated campaign legs re-solved post-D77

**Lane** SCN-WS5A-RESOLVE · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-06 ·
**THE PIN** `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b` ·
**PRECOMMIT** `docs/handoffs/PRECOMMIT-scn-ws5a-resolve-2026-09-06.md` (pushed before the first
solve; every gate, prediction and G-DRIFT classification below was written there first) ·
**Campaign** `scn-campaign-load-2026-09-06`, re-solved into
`results/scn-campaign-load-2026-09-06-r2/`.

---

## 0. The one-line result

**The campaign's CO2 levels were overstated by up to 57 %, and the repair does not cancel out of
the deltas.** Every contaminated leg this lane owns is re-solved at THE PIN, gated 5/5, and
re-registered under its original run id with the pre-fix artifacts deleted. `gas_cc_ccs` now
carries `measured host CAMPD rate × (1 − 0.90)` at every retrofitted unit-year — verified unit by
unit against the evolution ledger's `old_emission_rate`, zero failures across every leg — and
2026/2027 are **byte-identical to the pre-fix bundle on every fuel**, which is the empirical proof
that both D77 and D65-B are confined to 2028+.

## 1. THE PIN, and the G-DRIFT that justifies differencing against the incumbent

**THE PIN is `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b`** — `origin/main` at PRECOMMIT time, a
descendant of both `fc583339` (capx D77) and `b1f77621` (capx D65-B). It was recorded in the
PRECOMMIT and pushed **before the first LP**, and **it never moved**: every leg's
`run_config.json` carries a `git.sha` that is a descendant of THE PIN with a **zero diff** over
`src/market_sim scripts configs data/raw` and `git.dirty = False`. (The per-leg sha differs
because each leg's own artifact commit lands between legs; the invariant asserted by the guard is
the substantive one — descendant of THE PIN, zero solve-path diff, clean solve path — which is the
convention the LOAD lane itself recorded when its eight legs carried six distinct shas.)

**G-DRIFT (rule 29(b)) over `1cc45bb2..bdfb3095`** classified 34 non-merge commits / 41 files /
+5,362 −433 hunk by hunk: **4 LIVE, 30 INERT**, each with its reason, in PRECOMMIT §1. The LIVE
four are capx **D77** (the object of the lane), capx **D65-B** Acts A+B, and — **PJM only** — capx
**D67-ARM** and capx **D81**. `scripts/run_ces_leg.py` changed **0 lines**; every
`configs/scenarios/*_scenario_base_2026_2030.yaml` changed **0 lines**.

**No control solve was spent** (rule 29(b) form 4): the incumbent campaign's committed bundles ARE
the control. On PJM the two extra LIVE mechanisms are a genuine confound and §3.4 measures how
much of PJM's movement they can account for rather than absorbing them.

---

## 2. Scope, and the cache blocker

**13 of the campaign's 16 legs carry mis-rated `gas_cc_ccs`.** ERCOT's three are the only clean
ones — its retrofit ledger is empty in all three legs, so no unit ever carries a capture fraction —
and they are **not re-solved**; G-DRIFT lets them stand at `1cc45bb2`. This lane owns and has
delivered **7 of the 13** (NEISO 2, NYISO 3, PJM 2); CAISO's 3 and MISO's 3 were handed to sibling
sessions under the owner's rule-12 instruction (*"You run PJM and then issue separate prompts for
Caiso and miso to run in parallel"*), each carrying this lane's PIN, recipe and gates.

**THE CACHE BLOCKER, and why it never fired.** D77 moves no cache key, so a naive re-solve at the
same key would HIT the pre-fix bundle and silently return exactly the numbers it was meant to
replace. Three independent isolations were in place, and phase 0 proved the strongest of them
**before** any LP:

1. **A new out-dir per leg**, `results/scn-campaign-load-2026-09-06-r2/<ISO>/<CASE>/`. No pre-fix
   bundle was ever linked or copied into the new root; the WS-4c harness helper was not used.
2. **Every key moves at THE PIN anyway.** D65-B's `ccs_retrofit_vom_adder` 8.0 → 2.95 is **not** a
   `_CACHE_KEY_OPTIONAL_FIELDS` member, so it re-keys every config unconditionally. Measured in
   phase 0 for all 16 legs: **16 of 16 keys move**. A pre-fix bundle is therefore not merely
   avoided, it is **unreachable**.
3. **The container's default cache root was empty** — `results/<ISO>/` is gitignored and this was a
   fresh clone.

**Gate G5** re-proves this per leg from the artifacts (§4). No leg reproduced its pre-fix numbers.

---

## 3. The result, leg by leg

CO2 in Mt; `gas_cc_ccs` in TWh; `lw` is the load-weighted price in $/MWh. "pre" is the committed
pre-fix bundle at `1cc45bb2`; "post" is the re-solve at THE PIN.

### 3.0 The headline table — 2030, the campaign's terminal year

| leg | CO2 pre | CO2 post | change | share of level | CCS TWh pre → post |
|---|---|---|---|---|---|
| NEISO REF | 13.368 | **6.106** | −7.262 | **−54.3 %** | 16.72 → 25.93 |
| NEISO LOAD-HI | 14.776 | **6.357** | −8.419 | **−57.0 %** | 16.89 → 29.00 |
| NYISO REF | 20.893 | **10.903** | −9.990 | **−47.8 %** | 24.42 → 37.41 |
| NYISO LOAD-HI | 26.234 | **14.020** | −12.214 | **−46.6 %** | 30.18 → 43.70 |
| NYISO LOAD-HI-ORGANIC | 26.313 | **14.168** | −12.145 | **−46.2 %** | 29.99 → 43.47 |
| PJM REF | 470.455 | **463.039** | −7.416 | **−1.58 %** | 3.50 → 14.80 |
| PJM LOAD-HI | 619.078 | **608.471** | −10.607 | **−1.71 %** | 11.62 → 20.80 |

**2026 and 2027 do not move in any leg** — CO2, price and every fuel row are identical to the
pre-fix bundle to the digit (G2b/G3, measured over *all* fuels, not just the zero-carbon four).
That is the empirical confinement proof: `apply_ccs_retrofit` returns early below
`ccs_retrofit_available_year` = 2028, and D65-B's two fields are read at the same call site.

**The contamination was worse than the LOAD lane's own pre-declaration in NEISO and NYISO.** It
declared 41.9 % / 25.3 % of the 2030 level as mis-rated CCS on an accounting argument; the solved
answer is 54.3 % / 47.8 %, because the correction is not only accounting — correctly-rated abated
gas is genuinely cheaper per tonne of CO2, so the screen converts **more** units and the corrected
fleet displaces unabated gas. NEISO's 2030 retrofit cohort goes 28 units in REF and 33 in LOAD-HI;
CCS output roughly **doubles** in NEISO and rises ~55 % in NYISO.

### 3.1 NEISO — 14/14 invariants PASS, both arms, before and after

| year | REF pre → post | LOAD-HI pre → post | ΔCO2 pre → post |
|---|---|---|---|
| 2026 | 15.832 → 15.832 | 16.276 → 16.276 | +0.444 → +0.444 |
| 2027 | 17.096 → 17.096 | 17.740 → 17.740 | +0.644 → +0.644 |
| 2028 | 15.856 → **9.872** | 16.897 → **10.673** | +1.041 → **+0.801** |
| 2029 | 14.021 → **4.757** | 15.279 → **5.239** | +1.258 → **+0.482** |
| 2030 | 13.368 → **6.106** | 14.776 → **6.357** | +1.408 → **+0.251** |

**The load-response delta collapses by 82 %** — from +1.408 Mt to +0.251 Mt at 2030. This is the
lane's single largest prediction miss and it is reported at full magnitude in §5. The mechanism is
visible in the cohorts: pre-fix the two arms carried nearly identical CCS output (16.72 vs 16.89
TWh, a 0.18 TWh gap), so the correction was expected to cancel out of the delta. Post-fix the arms
**diverge** — 25.93 vs 29.00 TWh, a **3.07 TWh** gap, and 28 vs 33 retrofitted units — because the
cheaper corrected CCS makes the *marginal* retrofit economic in the high-load arm and not in the
reference. The repair did not just re-rate a fixed fleet; it moved the fleet, and it moved it
differently in the two arms.

The load-weighted price also falls in both arms from 2028 (REF 2030 $67.67 → $54.02) — abated gas
at a corrected rate is inframarginal more often.

### 3.2 NYISO — the same mechanism, half the magnitude, and the campaign headline survives

| year | REF pre → post | LOAD-HI pre → post | ORGANIC pre → post |
|---|---|---|---|
| 2026 | 23.692 → 23.692 | 25.384 → 25.384 | 25.373 → 25.373 |
| 2027 | 24.591 → 24.591 | 27.065 → 27.065 | 27.091 → 27.091 |
| 2028 | 24.111 → **17.163** | 27.665 → **20.271** | 27.728 → **20.337** |
| 2029 | 23.754 → **13.708** | 27.648 → **15.986** | 27.747 → **16.093** |
| 2030 | 20.893 → **10.903** | 26.234 → **14.020** | 26.313 → **14.168** |

ΔCO2 (LOAD-HI − REF) at 2030 falls **+5.340 → +3.117 Mt**, a 42 % reduction — inside the
pre-declared 1–3 Mt band (a HIT, §5).

**The synthesis's §1.1 headline survives the repair.** The DC-shape gap (ΔORGANIC − ΔLOAD-HI) at
2030 goes **+0.0797 → +0.1479 Mt**. It roughly doubles, but on a level of 14–26 Mt it is ~0.1 Mt
either way: doubling the data-centre block still moves NYISO's CO2 by ~1 % of its own load
response and ~0.1 % of the four-ISO total. **"The DC volume axis is worth almost nothing; its
shape is worth everything" is unaffected**, and is if anything slightly strengthened — the
post-fix gap is larger while the post-fix load response is smaller.

### 3.3 PJM — the confound is declared, and then measured away

PJM is the one ISO where THE PIN carries mechanisms beyond the CCS repair: capx **D67-ARM**
(the published whole-RTO Reliability Requirement replacing the `screen peak × FPR` reconstruction
at the `gross_adequacy_requirement_mw` seam) and capx **D81**. Both were declared LIVE in the
PRECOMMIT §1.1 as a confound this lane would report rather than absorb.

**Measured, they moved nothing.** Differencing PJM REF's full per-year record against the pre-fix
bundle, **every capacity-evolution row is identical in all five years**:

| row | 2028 | 2029 | 2030 |
|---|---|---|---|
| `retire_mw` | 2,600 → 2,600 | 1,232.4 → 1,232.4 | 460 → 460 |
| `builds_thermal_mw` | 0 → 0 | 7,056.8 → 7,056.8 | 6,742.4 → 6,742.4 |
| `builds_thermal_backstop_mw` | 0 → 0 | 3,056.8 → 3,056.8 | 5,056.8 → 5,056.8 |
| `builds_renew_mw` / `builds_storage_mw` | 0 / 2,400 | 6,000 / 4,000 | 1,500 / 4,000 — all identical |
| `peak_demand_mw` | 182,820 → 182,820 | 191,760 → 191,760 | 201,520 → 201,520 |
| `total_cap_mw` / `thermal_mw` / `vre_mw` / `firm_clean_mw` | identical | identical | identical |

Only `co2_mt`, `lw_price`, `reserve_margin`, `storage_charge/discharge_mwh` and `hours_ge_100`
move at all, and **2026 and 2027 are identical on every one of them** (373.195 / 393.675 Mt in
both bundles). The `reserve_margin` motion is 0.15–0.37 pp with a **sign that flips year to year**
(−0.37 / +0.15 / +0.14 pp), which is a re-accredited retrofit fleet, not a changed requirement
operand.

**Why the adequacy-requirement arm cannot show up here, mechanistically.** PJM's REF sits at a
**−16 % reserve margin**: the reliability floor is violated by ~30 GW and the reserve-margin build
backstop is **at its annual rate cap** in every year it builds. Moving the requirement operand the
backstop tests cannot move a build that is already clamped by the rate cap — the requirement is
larger than the model's reconstruction, and the backstop was already building all it may. **So
PJM's entire movement is attributable to the CCS repair**, and the PRECOMMIT's own hedge ("the
total is not predicted") turns out to have been unnecessary. That is a correction in this lane's
favour on measurement, and it is stated as one.

**The attribution splits inside the CCS repair, and it is mostly NOT D77.** PJM prices carbon at
$0, so re-rating a fixed CCS fleet is nearly pure accounting: 3.50 TWh at the mis-rated ~0.37
t/MWh versus the corrected ~0.037 is about **−1.2 Mt**. The observed 2030 fall is **−7.416 Mt**.
The rest comes from **D65-B's VOM cut** (8.0 → 2.95 $/MWh), which pulls `gas_cc_ccs` from **3.50
to 14.80 TWh** — abated gas displacing unabated gas and coal on the merit order. On a
carbon-priced ISO the two channels reinforce; on PJM the dispatch channel is the larger one, and
the two must not be quoted as "the D77 correction".

---

## 4. The STOP gates — 5/5 PASS on every leg

Pre-registered in PRECOMMIT §5. Structural and **kill-only**: a PASS means "the mechanism did what
its own arithmetic says", promotes nothing, and is never gated on a residual (rules 1
`[R-STRUCT]`, 29 `[R-SCREEN]`). Scored zero-LP from each leg's own bundle by
`score_gates.py` (session-local; every number it produced is in this document, per rule 29(c)).

| leg | G1 identity | G2a confine | G2b all-fuel 26/27 | G3 zero-carbon | G4 no flip | G5 fresh solve |
|---|---|---|---|---|---|---|
| NEISO REF | PASS | PASS | PASS | PASS | PASS | PASS |
| NEISO LOAD-HI | PASS | PASS | PASS | PASS | PASS | PASS |
| NYISO REF | PASS | PASS | PASS | PASS | PASS | PASS |
| NYISO LOAD-HI | PASS | PASS | PASS | PASS | PASS | PASS |
| NYISO LOAD-HI-ORGANIC | PASS | PASS | PASS | PASS | PASS | PASS |
| PJM REF | PASS | PASS | PASS | PASS | PASS | PASS |
| PJM LOAD-HI | PASS | PASS | PASS | PASS | PASS | PASS |

**G1 (the ruling-S5 paired check at model grain)** is the load-bearing one: for **every**
retrofitted unit-year in every leg, the persisted `FleetContext.emission_rate` equals the
evolution ledger's recorded `old_emission_rate × (1 − 0.90)` to relative tolerance **1e-9**, and
the unit's `fuel_type` is `gas_cc_ccs`. **Zero failures** across every unit-year of every leg.
This is readable at zero LP only because capx D65-B-R step 0 persists `old_emission_rate` into the
ledger's `ccs_retrofits` rows — G-DRIFT classified that commit INERT for the solve and it turned
out to be the thing that makes the gate cheap.

**G2b is stronger than the pre-registered G3** and was run instead of merely alongside it: rather
than checking the four zero-carbon classes in 2026/2027, it checks **every fuel row** in both
years against the pre-fix bundle at 1 MWh tolerance. Zero rows move, on any leg. Confinement to
2028+ is therefore a measurement over the whole generation vector, not an argument from the code.

**G2a** additionally asserts that no unit **outside** the retrofit cohort moves its
`emission_rate` across the horizon within the post-fix bundle. Zero failures.

**G4 reports rather than stops** where a flip's cause is re-ordered dispatch (pre-declared). No
leg produced one: NEISO and NYISO are **14/14 PASS** before and after, and each PJM arm carries exactly its
own pre-fix set — REF `{I7, I12}` (the reliability-floor and reserve-margin-band pair its −16 %
margin implies) and LOAD-HI `{I3, I7, I12}` (I3 additionally, from the 63.7 TWh it sheds) — with
**no ident added and none healed on either**. The committed declarations in
`invariant-failures.json` already matched both sets exactly, so none was added and none was stale.

**G5** proves the fresh solve five ways per leg: (a) the key was absent from the ISO's cache root
before the solve; (b) the leg's `run_config.json` key equals the phase-0 predicted key at THE PIN;
(c) `git.dirty = False` on a descendant of THE PIN; (d) wall time and a five-entry `per_year_perf`
are a solve's, not a cache read's; (e) the leg does **not** reproduce the pre-fix CO2 trajectory.

### 4.1 One leg was solved twice, and the first result was discarded

**PJM LOAD-HI failed G5 on its first solve and was re-solved.** The first run (21:05:37–21:34:48Z,
rc=0) passed G1, G2a, G2b, G3 and G4, and failed **G5 leg (c)**: its `run_config.json` recorded
`git.dirty = true`. The cause was mine — I drafted this document into the working tree while the
LP was running. The recorded `changed_files` is **exactly one untracked markdown file** under
`docs/handoffs/` and `diffstat` is **empty**: no tracked file changed, and there is no causal path
from a markdown file to an LP.

**That argument was available and it is not the point.** G5 was pre-registered as a STOP gate
before any solve. Reinterpreting a failed gate after seeing the result — even correctly — is the
fitted-gate move rule 29 `[R-SCREEN]` exists to forbid, and a gate that can be argued around after
the fact is not a gate. So the bundle and its cache entry were deleted and the leg re-solved on a
tree verified clean at launch (`git status --porcelain` empty; `results/` is in
`persist.GIT_STATE_EXCLUDE`, so the leg's own out-dir cannot dirty it).

**The clean re-solve reproduces the discarded run to the digit in every year.** That is the
expected result for a deterministic single-threaded HiGHS solve and it confirms the dirt was
inert — but it is stated here as an *observation after the fact*, not as the reason the leg was
accepted. The leg was accepted because it passed the gate. Cost: **29.8 min**. The other six legs
all carry `git.dirty = False`, so the seven are uniform.

---

## 5. Predictions, scored as written

The PRECOMMIT §6 pre-declared a sign and an order of magnitude per ISO before any LP. Misses are
reported at full magnitude.

| # | prediction | result |
|---|---|---|
| **P-A** | rate falls exactly 10× at unit level (G1); CO2 falls every year from 2028; **2026/2027 do not move** | **HIT, all three limbs**, every leg |
| **NEISO level** | falls, order **4–8 Mt** | **HIT** — −7.262 Mt (REF, 2030) |
| **NYISO level** | falls, order **4–9 Mt** | **MISS (high)** — −9.990 Mt. The band was built from the accounting share alone and did not allow for the retrofit cohort growing |
| **PJM CCS channel** | falls ~2 Mt; total not predicted | **HIT on the channel** (~−1.2 Mt of pure re-rating); the total −7.416 Mt is dominated by D65-B's dispatch response (§3.3) |
| **P-B NEISO Δ** | moves **< 0.3 Mt** | **MISS, and the lane's largest** — Δ moved **1.157 Mt** (+1.408 → +0.251), nearly 4× the band. Cause diagnosed in §3.1: the repair pulled the two arms' retrofit **sets** apart (28 vs 33 units; CCS gap 0.18 → 3.07 TWh), so the correction could not cancel |
| **P-B NYISO Δ** | falls **1–3 Mt** | **HIT** — falls 2.223 Mt (+5.340 → +3.117) |
| **P-B PJM Δ** | CCS component falls 3–6 Mt; total reported | **HIT** — falls 3.191 Mt (+148.623 → +145.432). The arms carry 14.80 vs 20.80 TWh of corrected CCS, so it does not cancel here either |
| **P-C** | 2030 retrofit capacity rises in ≥3 of 5 re-solved ISOs, and ≥1 falls | **partially scored** — rises in NEISO, NYISO and PJM (this lane's three); the "≥1 falls" limb needs CAISO/MISO |
| **P-D** | no new invariant FAIL class; NEISO/NYISO stay 14/14 | **HIT** — NEISO/NYISO 14/14 both arms; PJM's set unchanged at `{I7, I12}` |

**The two misses share one root cause and it is the lane's main substantive finding**: the repair
is not an accounting correction applied to a frozen fleet. Correctly-rated CCS is cheaper per
tonne, so the retrofit **screen converts more units**, and it converts *different* numbers of them
in the two load arms. Any estimate of D77's effect built from "mis-rated TWh × rate error" — which
is what both the LOAD lane's per-ISO contamination shares and this lane's own prediction bands
were — is a **lower bound on the level and says nothing about the delta**.

---

## 6. Corrections this lane owes the record

1. **The desk ledger r#14's classification of capx D67-ARM is wrong for this campaign.** It reads
   *"a `{iso: bool}` gate no scenario case sets, INERT for every SCN leg"*. The gate is not set by
   a **case** — it is set by **`iso_configs._pjm_config`'s `default_scenario_overrides`**, so it
   arms on every PJM leg regardless of the case. Measured on both resolved PJM configs. It was
   declared LIVE in this lane's PRECOMMIT §1.1 before any solve. Its *effect* here is nil (§3.3),
   but "no case sets it" is not why, and the next lane that reasons from that sentence on a PJM
   ISO where the backstop is **not** clamped would be reasoning from a false premise.
2. **This lane's own PRECOMMIT hedged PJM's total and did not need to.** §6 said "the total is not
   predicted — D67-ARM and D81 are live here and can move the level by more, in either direction."
   The measurement in §3.3 shows every capacity row identical, so PJM's total **is** attributable
   to the CCS repair. Corrected in the lane's favour, on evidence, after the fact — and recorded
   here rather than by editing the PRECOMMIT.
3. **The contamination shares the LOAD lane pre-declared are lower bounds, not estimates.** 41.9 %
   (NEISO) and 25.3 % (NYISO) were computed as accounting shares of a frozen fleet; the solved
   answers are 54.3 % and 47.8 %. Neither is a defect in the LOAD lane's arithmetic — it is the
   difference between re-rating a fleet and re-solving one. Anyone quoting a *pre*-solve
   contamination share for CAISO or MISO should treat it the same way.

---

## 7. Duties

- **No default moved, no knob moved, no `ScenarioConfig` field added, no new case, no solve
  outside the declared list, no year past 2030.** **DOF ledger: ZERO free parameters.** No
  `authorized_price_tuning` block — rule 1 `[R-STRUCT]`'s carve-out is a backcast offer-curve
  channel and is untouched by a forecast lane.
- **Consumed, never edited:** `configs/scenario_campaign_matrix.yaml`, `configs/scenarios/*.yaml`,
  `scripts/run_ces_leg.py`, `scripts/run_full_horizon.py`, `scripts/report_scenario_deltas.py`,
  `scripts/collate_scenario_campaign.py`, `scripts/register_forecast_run.py`,
  `scripts/check_forecast_invariants.py`, everything under `src/market_sim/`, `program-status.json`,
  `ff-verdicts.json`, the entire backcast namespace, and every other lane's or ISO's files.
- **Registration (rule 15 / forecast plan §7.5).** Each leg re-registered under its **original run
  id** into the forecast namespace with `--kind scenario` and the campaign/case extra-meta; the
  pre-fix slim artifacts under `results/scn-campaign-load-2026-09-06/<ISO>/<CASE>/` **deleted in
  the same commit** (rule 26 `[R-DELETE]`: a stale bundle at a valid key is a re-armable wrong
  answer). **ERCOT's three pre-fix legs are untouched and stay at `1cc45bb2`.**
- **Invariant declarations.** `scripts/check_forecast_invariants.py --sidecar-dir` re-run before
  every push; PJM's `{I7, I12}` declarations in `frontend/data/hindcast/invariant-failures.json`
  carried forward unchanged (the re-solve neither added nor healed an ident), NEISO's and NYISO's
  stay absent because both are 14/14. The audit is **EXIT 0** at every pushed commit, as it is on
  main.
- **Rule 12 `[R-PARALLEL]`.** Years sequential within every invocation; NEISO and NYISO run as the
  only solving lane; **PJM run entirely alone**, on the owner's explicit slot confirmation
  (*"You run PJM and then issue separate prompts for Caiso and miso to run in parallel"*). CAISO
  and MISO were handed to sibling sessions **after** PJM's legs, never beside them.
- **Rule 29(c) DELETE BEFORE MERGE** does not apply: these are not screen or control bundles.
  Every leg is a registered campaign arm replacing its own predecessor at the same run id, which
  is what rule 15 requires and what ruling S8 chartered.
- **Nothing outside this lane's declared regions was edited.** The desk-ledger correction in §6 is
  **routed to SCN-DESK here rather than written into the ledger**, which is another lane's file.

---

## 8. Cost — the re-solve row set for card D-5

The synthesis §8 cost table is what card **D-5** (the Stage-B grant) has been held for. Its own
closing recommendation was that *"what should gate it is not cost but the D77 re-solve (card
D-10)"*. This section supplies the re-solve's measured cost so D-5 can be decided on a complete
table.

**Measured re-solve cost, this lane's three ISOs** (7 of the 13 legs; each leg's own
`total_wall_s` and `global_peak_rss_mb`):

| ISO | legs | solve-yrs | wall min | **min/solve-yr** | peak RSS GB | vs. its pre-fix min/solve-yr |
|---|---|---|---|---|---|---|
| NEISO | 2 | 10 | 10.8 | **1.08** | 3.60 | 1.09 → **1.08** (−1 %) |
| NYISO | 3 | 15 | 58.5 | **3.90** | 3.84 | 4.06 → **3.90** (−4 %) |
| PJM | 2 | 10 | 73.1 | **7.31** | 8.76 | 7.90 → **7.31** |
| **this lane** | **7** | **35** | **142.4** | **4.07** | — | — |
| CAISO (sibling) | 3 | 15 | *pending* | — | — | 4.33 → — |
| MISO (sibling) | 3 | 15 | *pending* | — | — | 5.23 → — |

**The re-solve costs essentially the same as the original solve** — within a few percent per
solve-year in every ISO measured, which is the expected result since the recipe is the identical
LP at a moved key. So the honest budget line for a D77-class repair is: **a re-pin costs a full
re-run of every contaminated leg**, not a discount on one.

**Restated campaign total.** Stage A-LOAD's original 16 legs / 80 solve-years cost **313.7 min =
5.23 h of LP**. The S8 re-solve re-runs **13 of those 16 legs / 65 solve-years**; on the
per-solve-year rates measured above and the sibling ISOs' own pre-fix rates as the estimate for
their halves, the re-solve is **≈286 min ≈ 4.8 h**, bringing the campaign's
**all-in cost to ≈10.0 h of LP** for a six-ISO × 3-case × 5-year Stage A.

**What this says for D-5.** The cost argument is unchanged — a Stage B of comparable shape is
still affordable on one box in a session. What the re-solve adds is a **second** cost line the
Stage-B charter should carry explicitly: *any mechanism repair landing mid-campaign re-runs the
campaign*. The mitigation is not cheaper LPs, it is **sequencing** — freeze the capx mechanism set
before a campaign opens, or accept a ~1× re-run as its contingency. Stage A paid that contingency
once, in full.

---

## 9. What is left, and to whom

- **CAISO ×3 and MISO ×3** are with sibling sessions, each carrying THE PIN, this lane's cache
  recipe, the same five gates and the same registration/deletion duties. Their numbers reach the
  synthesis addendum (§8 of `FINDING-scn-ws5a-load-synthesis-2026-09-06.md`) through their own
  FINDINGs. **Until both land, the six-ISO rollup in that addendum is on the four-ISO common set
  and says so.**
- **Routed to SCN-DESK** (another lane's files, not edited here): the r#14 D67-ARM classification
  correction (§6 item 1), and the fact that the desk's pre-solve contamination shares are lower
  bounds (§6 item 3).
- **Nothing is promoted.** This is a forecast scenario campaign: no keeper, no determination, no
  C1–C8 gate, nothing that *can* be promoted (`STATUS-scn-ws5a-load-2026-09-06.md`).
