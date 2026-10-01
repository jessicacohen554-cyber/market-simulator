# FINDING — SCN-WS5A-RESOLVE-CAISO: ruling S8 executed on CAISO's three legs

**Lane** SCN-WS5A-RESOLVE-CAISO · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-06 ·
**Branch** `claude/scn-ws5a-resolve-caiso-0rkx2k` · **THE PIN**
`bdfb3095e9fa0cd2bec3f4e843f320b42588c72b` · **Campaign** `scn-campaign-load-2026-09-06`
(same ids, same cases, `reference_case: REF`) · **Pre-registration**
`PRECOMMIT-scn-ws5a-resolve-caiso-2026-09-06.md`, pushed at `c538ecfb` **before the first
solve** — every gate, key and prediction below was declared there and is scored as written.

---

## 0. Bottom line

1. **All five gates PASS on all three legs, and all three are proven fresh solves.** G1's
   identity holds at **3.79e-16** against a 1e-9 tolerance, on every retrofitted unit-year in
   every leg; 2026 and 2027 are **exactly** unmoved for every fuel; no invariant flips.
2. **The repair is much larger than the accounting arithmetic predicted, and my pre-declared
   band MISSES on the high side.** 2030 REF CO2 falls **31.1595 → 19.9574 Mt (−11.2021)**
   against a predicted 3–8 Mt. The accounting correction alone was ~5.04 Mt; the rest is a
   CARB-priced merit-order response the arithmetic could not have produced (§3.2).
3. **The delta moves, as predicted, but by slightly less than the predicted band.** The LOAD-HI
   ΔCO2 at 2030 falls **10.2307 → 9.2508 Mt**, i.e. by **0.980 Mt** against a predicted
   1–3 Mt. Direction and mechanism right; magnitude just outside the band. Both misses are
   reported at full magnitude and neither is re-read favourably.
4. **The predecessor's open question is answered.** CAISO's implied `gas_cc_ccs` **class** rate
   at 2030 REF is now **0.0375 t/MWh** (2.437997 Mt / 64.9875 TWh), against **0.1496** pre-fix
   — inside the ≤ ~0.05 t/MWh bound that 90 % capture implies, which no ISO's retrofit fleet
   met before D77.
5. **Not pre-declared by anyone, and routed:** the **DC shape gap** (LOAD-HI − ORGANIC) at 2030
   **more than doubles**, −0.1129 → **−0.2376 Mt**, while the peak gap is **byte-identical** at
   −1.924 GW. The defect was understating the shape axis's own CO2 signature, not only the
   level — which sharpens, rather than softens, the synthesis §1.1 reading that the campaign
   varied the less important axis.

---

## 1. THE PIN and the CAISO-only LIVE set

THE PIN is the parent lane's, not chosen here. Ancestry re-verified with
`git merge-base --is-ancestor`: `fc583339` (capx **D77**) **YES**, `b1f77621` (capx **D65-B**)
**YES**, `1cc45bb2` (the pre-fix pin) **YES**. This lane branched off THAT sha, so every leg of
the campaign sits at one base. THE PIN was never moved; the HEAD GUARD held on all three legs
(`H1 == H0 == c538ecfb…`, all `rc=0`), and no `git fetch` or rebase ran during a leg.

The G-DRIFT audit `1cc45bb2..bdfb3095` is the parent lane's (PRECOMMIT §1) and was **not
re-audited**. What this lane owed and did was verify, on **its own resolved CAISO configs**,
that the parent's PJM-only classifications actually hold here:

| field | measured, all three legs | consequence |
|---|---|---|
| `capacity_adequacy_requirement_published_by_iso` | **`None`** | capx **D67-ARM** cannot arm |
| `capacity_market_supply_clearing_by_iso` | **`None`** | capx **D81** and capx **D78** both fail this conjunct |
| `retirement_sector_gate` | **`False`** | capx **D78** fails its other conjunct too |
| `caiso_offer_surface_conditional` (with `offer_curve_by_group = {}`) | **`False`** | the CAISO measured offer-surface pair is unarmed |
| `hindcast` / `capacity_screen_peak_measured_hindcast` | **`False` / `False`** | capx **D76** |
| `capacity_no_default_cap_convention_by_iso` | **`None`** | capx **D74** |
| `mass_cap_tons_by_year` / `mass_cap_enabled` | **`None` / `False`** | SCN-CAP |
| `nyiso_ct_peaker_bands_measured`, `nyiso_gas_bridge_startup_aware`, `pjm_vre_accreditation_vintage` | **`False`** ×3 | nyiso-199/200/201, capx D75-R |
| `set_overrides` | **`{}`** | capx D60-R4's changed branch is never entered |

**So CAISO's LIVE set is exactly `{D77, D65-B}`**, and CAISO's pre-vs-post difference IS the CCS
repair and nothing else. Form 4 is VALID: the committed pre-fix bundle is the control and **no
control solve was earned or spent**.

---

## 2. G1 identity, per year, and G2/G3

### 2.1 G1 — every retrofitted unit-year at `host measured rate × (1 − 0.90)`

Read at **zero LP** from the committed artifacts: the cumulative cohort and each host's
`old_emission_rate` from `results/CAISO/<key>/evolution_<year>.json`'s `ccs_retrofits` rows
(capx D65-B-R step 0), against the LP's own per-unit rate from
`read_fleet_context(...).emission_rate` zipped with `.unit_ids` / `.fuel_types`. No replay.

| leg | year | cohort | units checked | max rel. deviation | all `gas_cc_ccs` |
|---|---|---|---|---|---|
| REF | 2026 / 2027 | 0 | 0 | — (no cohort) | — |
| REF | 2028 | 10 | **10** | **3.79e-16** | yes |
| REF | 2029 | 18 | **18** | **3.79e-16** | yes |
| REF | 2030 | 22 | **22** | **3.79e-16** | yes |
| LOAD-HI | 2028 / 2029 / 2030 | 10 / 17 / 23 | **10 / 17 / 23** | **3.79e-16** | yes |
| LOAD-HI-ORGANIC | 2028 / 2029 / 2030 | 10 / 17 / 23 | **10 / 17 / 23** | **3.79e-16** | yes |

Tolerance was 1e-9; the measurement is seven orders inside it. Concrete rows (REF, 2030):

| unit | host measured rate | `host × 0.10` | model rate | rel. dev |
|---|---|---|---|---|
| `CC_REGULAR_ZP26_p55182_econ` | 0.366424 | 0.03664240 | 0.03664240 | 3.79e-16 |
| `CC_REGULAR_SDGE_p55985_econ` | 0.372145 | 0.03721450 | 0.03721450 | 3.73e-16 |
| `CC_REGULAR_NP15_p55333_econ` | 0.372758 | 0.03727584 | 0.03727584 | 3.72e-16 |

**G1 = PASS on all three legs.**

### 2.2 G2 confinement — and the limit of what it can claim

**(a) PASS on all three legs:** within the post-fix bundle, every unit **not** in the cumulative
cohort holds the same `emission_rate` in every year as in 2026 (rel/abs tol 1e-12).

**(b) PASS on all three legs:** 2026 and 2027 generation-by-fuel is identical to the committed
pre-fix bundle for **EVERY** fuel — 11 fuels in 2026, 10 in 2027 — not merely the zero-carbon
ones, and the year totals and CO2 agree to four decimals (REF 2026 31.3061 both, 239.352 TWh
both; 2027 34.5149 both, 247.128 TWh both).

**Stated plainly, as the PRECOMMIT required:** a **per-unit diff against the pre-fix bundle is
NOT computable**. `results/<ISO>/` is gitignored and the pre-fix parquets were never
materialized on this fresh container, so the committed pre-fix record is slim
(`full_horizon_summary.json` + `run_config.json`) and carries no per-unit rates. (a) and (b) are
what is actually available, and they are **a weaker claim** than a per-unit pre-vs-post diff
would be: (a) tests confinement *within* the new bundle, (b) tests identity *against* the old
one only at by-fuel grain. They are recorded as that, not as a restatement of the stronger check.

### 2.3 G3 pre-2028 inertness — measured, not argued

Nuclear 18.1972, hydro 18.8032, wind 16.4618, solar 56.8047 TWh — **identical to the digit** in
2026 and 2027, in all three legs, pre and post. `apply_ccs_retrofit` returns at
`if year < ccs_retrofit_available_year` (2028), so this is the empirical confirmation that
**both** D77 and D65-B are confined to 2028+. **G3 = PASS.**

---

## 3. §3 The 2030 level and the LOAD-HI delta, pre vs post

### 3.1 Levels

| leg | 2030 CO2 pre | 2030 CO2 post | move |
|---|---|---|---|
| **REF** | **31.1595** | **19.9574** | **−11.2021 Mt (−35.9 %)** |
| LOAD-HI | 41.3902 | 29.2082 | −12.1820 Mt |
| LOAD-HI-ORGANIC | 41.5031 | 29.4458 | −12.0573 Mt |

Full REF trajectory (2026 → 2030), pre → post:
31.3061 → 31.3061 · 34.5149 → 34.5149 · 33.3190 → **30.1194** · 31.3551 → **21.9693** ·
31.1595 → **19.9574**. First motion is 2028, exactly the retrofit-availability year.

### 3.2 Why the fall is more than twice the accounting correction

The pre-declared contamination — 45.161 TWh × the over-rating — was **≈5.04 Mt**, and that
figure assumed the CCS **volume** stayed put. It did not, and the reason is priced:

- CAISO carries `state_carbon_pricing = True` (`carbon_price_path = "zero"`; CARB is the
  binding instrument, not the campaign's carbon axis). The resolved CARB price is
  **$34.37/t (2028) → $36.78 (2029) → $39.36 (2030)**.
- Correcting a converted unit's rate from ≈0.366 to ≈0.0366 t/MWh removes
  **≈$12.97/MWh** from its marginal cost at 2030 (`0.3298 × 39.36`), against a heat-rate
  penalty and a $2.95/MWh capture VOM that only partly offset it.
- So the converted fleet moves **down** the stack and runs near baseload. At 2030 REF the
  cohort's **capacity barely moves (8,687.0 → 8,885.7 MW, +2.3 %)** while its **generation
  rises 45.161 → 64.988 TWh (+43.9 %)** — a capacity factor of **59.3 % → 83.5 %**. The energy
  it takes comes out of unabated `gas_cc`, which falls **53.090 → 38.258 TWh (−14.832)**.

That displacement — abated MWh replacing unabated MWh one-for-one — is the second and larger
half of the 11.20 Mt. It is the merit-order re-ordering the PRECOMMIT pre-declared as **NOT a
STOP**, and the load-weighted price falls with it ($75.29 → $71.55 in REF).

### 3.3 The LOAD-HI delta

| year | Δ pre | Δ post | moved |
|---|---|---|---|
| 2026 | +2.9948 | +2.9948 | **0.0000** |
| 2027 | +4.8146 | +4.8146 | **0.0000** |
| 2028 | +6.7986 | +6.7638 | −0.0348 |
| 2029 | +8.4537 | +7.6361 | −0.8176 |
| **2030** | **+10.2307** | **+9.2508** | **−0.9799** |

The ORGANIC delta moves the same way (+10.3436 → +9.4884, −0.8552 at 2030). **The correction
does not cancel out of the delta**, exactly as predicted and for the predicted reason — the arms
carry unequal CCS generation (post-fix 64.988 vs 68.641 TWh at 2030) — but it moves **0.98 Mt**
where 1–3 Mt was declared.

### 3.4 The finding nobody pre-declared: the DC **shape** gap doubles

| year | ΔCO2 (LOAD-HI − ORGANIC) pre | post | Δpeak pre | post |
|---|---|---|---|---|
| 2028 | −0.0671 | −0.0618 | −1.163 GW | **−1.163 GW** |
| 2029 | −0.1077 | **−0.1330** | −1.543 GW | **−1.543 GW** |
| 2030 | −0.1129 | **−0.2376** | −1.924 GW | **−1.924 GW** |

The peak gap is **byte-identical** pre and post — the shape mechanism itself is untouched, as it
must be, since the DC block's relocation is a demand-side construction the CCS rate cannot
reach. What moved is the **emissions consequence** of that same shape difference, because the
marginal unit displaced by the relocated block is now a differently-priced one. The predecessor
FINDING's headline for CAISO — *"the ORGANIC arm was worth solving, and two lanes said it
wasn't"* — is **strengthened**: the arm's CO2 signature at 2030 is 2.1× what the pre-fix solve
reported.

---

## 4. Gate verdicts

| gate | REF | LOAD-HI | LOAD-HI-ORGANIC |
|---|---|---|---|
| **G1** identity | **PASS** | **PASS** | **PASS** |
| **G2(a)** non-cohort rate invariance | **PASS** | **PASS** | **PASS** |
| **G2(b)** 2026/27 by-fuel identity vs pre-fix | **PASS** | **PASS** | **PASS** |
| **G3** pre-2028 inertness | **PASS** | **PASS** | **PASS** |
| **G4** no collateral flip | **PASS** — `{I7, I12}`, no new ident | **PASS** — `{I3, I7, I12}` | **PASS** — `{I3, I7, I12}` |
| **G5** cache-hit proof | **PASS** (a–e) | **PASS** (a–e) | **PASS** (a–e) |

**No gate fired; no leg was killed.** G4 is a clean PASS rather than a reported-with-cause case:
every leg's post-fix non-PASS set is **exactly** its pre-fix set — nothing new, nothing cleared —
so the I3/I7/I12 movement the PRECOMMIT anticipated did not need the "caused by re-ordered
dispatch" clause at all.

**Pre-declared as NOT a STOP, and observed:** the retrofit set moved (+198.7 MW REF, +32.1 MW
both load arms; cohort 22 in REF vs 23 in the load arms at 2030), the merit order re-ordered,
and CO2 fell by more than the accounting figure. All of these are the repair working.

---

## 5. G5 — the cache-hit proof, per leg

The STATUS doc's blocker was that D77 moves no cache key, so a naive re-solve would hit the
pre-fix bundle. Defeated three ways, each measured:

| evidence | REF | LOAD-HI | LOAD-HI-ORGANIC |
|---|---|---|---|
| **(a)** `results/CAISO/<PIN key>/` absent pre-solve (`ls` recorded) | **absent** | **absent** | **absent** |
| **(b)** `run_config.json` / summary `cache_key` == PRECOMMIT §2 PIN key | `2d16a246bb372e4a` ✓ | `86bfde6ed2896b99` ✓ | `ff8c04bc4eef6605` ✓ |
| **(c)** `git.sha` a PIN descendant, zero solve-path diff, `dirty == false` | `c538ecfb`, **diff empty**, `false` | idem | idem |
| **(d)** `total_wall_s` a solve's, all five per-year `wall_s` | **1704.2 s**, 5/5 | **1689.5 s**, 5/5 | **1635.4 s**, 5/5 |
| **(e)** 2028–30 rate is `host × 0.10`, not ~0.37 | ✓ (§2.1) | ✓ | ✓ |
| trajectory reproduces the pre-fix bundle to the digit? | **NO** | **NO** | **NO** |

On (c): the solve HEAD is `c538ecfb`, which is THE PIN plus this lane's own PRECOMMIT commit —
a docs-only commit, so
`git diff bdfb3095 c538ecfb -- src/market_sim scripts configs data/raw/_validation-source
data/raw/reference` is **empty**. That is the PRECOMMIT's declared "descendant with a ZERO
solve-path diff" case, verified rather than assumed.

Three independent isolations, all held: a new out-dir per leg
(`results/scn-campaign-load-2026-09-06-r2/CAISO/<CASE>/`); the key itself moved (D65-B's
`ccs_retrofit_vom_adder` 8.0 → 2.95 is not a `_CACHE_KEY_OPTIONAL_FIELDS` member); and the
container's default cache was **empty** (`results/CAISO/` did not exist). The WS-4c harness
helper that links arm bundles into a shared cache root was **never used**; no pre-fix bundle was
linked, copied or moved anywhere.

---

## 6. Cost — wall and RSS per solve-year

| leg | wall | peak RSS | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|---|---|
| REF | **28.4 min** | 4.95 GB | 835.1 s | 253.3 s | 235.5 s | 174.6 s | 205.4 s |
| LOAD-HI | **28.2 min** | 4.89 GB | 796.9 s | 234.0 s | 217.1 s | 252.4 s | 188.9 s |
| LOAD-HI-ORGANIC | **27.3 min** | 4.86 GB | 817.0 s | 201.4 s | 213.2 s | 207.9 s | 195.7 s |

**84.0 min of LP / 15 solve-years / 5.60 min per solve-year**, one leg at a time, nothing else
solving on the box (verified 0 concurrent solve processes before each leg). The 2026 year is
fleet build and is 3–4× the later years, as the predecessor measured. Against the predecessor's
65 min for the same 15 solve-years this is **+29 %**, attributable to the re-ordered dispatch
(the CCS cohort now sets price in many more hours) and not investigated further.

**Precondition cost, for whoever schedules the next fresh-container lane:**
`scripts/regenerate_clean.py` took **~50 min** (56 datatypes; `curate_emissions.py` is the long
pole at ~25 min). `data/clean` is derived and gitignored, so a fresh container has none and
`run_scenario_iso` hard-fails on `confirmed-retirements` before any LP starts. It is worth
starting it in the background at session open, as this lane did, and doing phase 0 while it runs.

---

## 7. Routed

1. **To the parent lane (SCN-WS5A-RESOLVE), for the synthesis ADDENDUM it owns.** CAISO's
   rollup: 2030 REF **31.1595 → 19.9574 Mt**; LOAD-HI **41.3902 → 29.2082**; ORGANIC
   **41.5031 → 29.4458**; LOAD-HI ΔCO2 **10.2307 → 9.2508**; ORGANIC ΔCO2
   **10.3436 → 9.4884**; 2026/2027 unmoved in every leg. This lane did **not** edit the
   synthesis, STATUS, the desk ledger, `program-status.json`, `ff-verdicts.json`, the backcast
   registry, or any ISO shard but CAISO's.
2. **The DC shape gap doubling (§3.4) is a cross-ISO question this lane cannot answer.** Whether
   the same 2× appears in NYISO and MISO — the other two ISOs with a solved ORGANIC arm — is
   worth one zero-LP read of their re-solved sidecars by whoever holds them.
3. **The predecessor's §7 item 2 is answered for CAISO and only for CAISO.** The implied class
   rate is 0.1496 → **0.0375 t/MWh**, inside the ≤0.05 bound. The 4× cross-ISO spread the
   predecessor could not explain should be re-measured post-fix across all five re-solved ISOs
   before anyone concludes the repair "lands uniformly" — one ISO landing correctly does not
   establish it.
4. **The predecessor's §7 item 3 stands and is now sharper.** `caiso-2026-2030-d46-remeasure` is
   stale at HEAD; the divergence it showed was concentrated in the retrofit fleet, and that
   fleet has now moved again (volume +43.9 % at 2030).
5. **DESTINATION DEVIATION, declared not silent.** The charter names
   `results/scn-campaign-load-2026-09-06/CAISO/{bundle,report}/` as the refresh target, but
   `run_ces_leg.py --assemble` discovers legs from the out-dir's own parent, and that path's
   three per-case dirs were deleted by the charter's **own** rule-26 clause in the leg commits.
   A bundle left there would carry the pre-fix cache keys and reference deleted legs — the exact
   re-armable wrong answer rule 26 targets. Both artifacts are therefore written beside the legs
   they describe, at `results/scn-campaign-load-2026-09-06-r2/CAISO/{bundle,report}/`, and the
   stale pre-fix pair is deleted. **Nothing downstream moves:**
   `collate_scenario_campaign.py` rglobs for `full_horizon_summary.json` and never reads
   `bundle/` or `report/`, so the parent lane's collation over the repaired set is unaffected.
   Flagged here for SCN-DESK rather than resolved unilaterally as a charter amendment.
6. **Second-order defect still open (capx D77 §2.2, not this lane's).** `ccs.py` computes the
   residual off the **unpenalized** host rate while the retrofit raises the heat rate 12 %, so
   the residual is ~12 % lower than the physics implies. Every number above inherits that, and
   correcting it would move the §45Q credit and hence the retrofit set. Named here because
   CAISO's post-fix class rate (0.0375) sits below the naive `0.366 × 0.10 × 1.12 ≈ 0.041`, and
   a reader should know why.

---

## 8. Predictions — scored as written, misses at full magnitude

| # | pre-declared | measured | verdict |
|---|---|---|---|
| **P-A** | 2030 REF CO2 **FALLS** from 31.160 Mt by order **3–8 Mt** | **−11.2021 Mt** | **MISS on magnitude** — direction right, fall **40 % larger** than the top of the band. The band was built on the accounting correction plus "a CARB-priced dispatch response" without sizing the second term; the dispatch response turned out to be the **larger** half (§3.2). |
| **P-B** | LOAD-HI **ΔCO2 FALLS by 1–3 Mt** from 10.231 | **−0.9799 Mt** (10.2307 → 9.2508) | **MISS, marginally** — 0.02 Mt below the band's floor. Direction, mechanism and the "does not cancel" claim all correct; the magnitude was over-stated. |
| **P-C** | 2028–30 unit rate falls exactly 10×; CO2 falls every year from 2028; **2026 and 2027 do not move at all** | rate identity to 3.79e-16; CO2 falls 2028/29/30 in all legs; 2026/27 identical for **every** fuel | **HIT** |
| **P-D** | no new invariant FAIL ident in any leg | `{I7,I12}` / `{I3,I7,I12}` / `{I3,I7,I12}` — unchanged, nothing new, nothing cleared | **HIT** |
| **P-E** | *no directional prediction made* for the 2030 retrofit capacity | 8,687.0 → 8,885.7 MW (REF, +198.7); 8,936.3 → 8,968.4 (both load arms, +32.1) | **N/A by design** — recorded, not scored. Declining to predict here was the right call: the interesting motion was in **utilization** (CF 59.3 % → 83.5 %), not capacity, and no prediction was framed on that axis. |

**Two of four scored predictions miss on magnitude, in opposite directions.** Both errors share
one cause: the pre-declared bands were sized from the **accounting** correction and treated the
dispatch response as a modifier. In a CARB-priced ISO with a 45 TWh retrofit fleet it is the
dominant term for the level and a partly-offsetting one for the delta. That is a lesson about
how to size a band for a priced ISO, not a defect in the repair, and it is recorded here rather
than absorbed.

---

## 9. Files

**Added / changed by this lane, all inside its declared regions:**

- `docs/handoffs/PRECOMMIT-scn-ws5a-resolve-caiso-2026-09-06.md` (new, pushed pre-solve)
- `docs/handoffs/FINDING-scn-ws5a-resolve-caiso-2026-09-06.md` (this file)
- `results/scn-campaign-load-2026-09-06-r2/CAISO/{REF,LOAD-HI,LOAD-HI-ORGANIC}/` — the three
  legs' slim artifacts (`full_horizon_summary.json` + `run_config.json`)
- `results/scn-campaign-load-2026-09-06-r2/CAISO/{bundle,report}/` — refreshed (§7 item 5)
- `frontend/data/hindcast/caiso-2026-2030-scn-campaign-load-2026-09-06-{ref,load-hi,load-hi-organic}.json`
  — re-registered under the **SAME** ids; only `cache_key`, `bundle`, `total_wall_s`, the
  trajectory, `registered_utc` and `provenance.scored_at_sha` move
- `results/scn-campaign-load-2026-09-06/CAISO/` — **DELETED** (rule 26): the three pre-fix
  per-case dirs and the stale bundle/report pair. ERCOT's three legs and every other ISO's are
  untouched.
- `docs/codebase-site/data/mechanism-matrix/CAISO.js` — `datacenter_load_block` cell, **one
  appended line**, no verdict letter moved (last commit, after rebase)

**`frontend/data/hindcast/invariant-failures.json` needed NO edit**: each leg's post-fix
non-PASS set is exactly its existing declaration (`ref` → `["I12","I7"]`, both load arms →
`["I12","I3","I7"]`), so there was nothing to add and no stale ident to delete.
`scripts/check_forecast_invariants.py --sidecar-dir frontend/data/hindcast` is **EXIT 0** after
every commit, as it was on `main` before.

**Duties discharged.** No default moved, no knob moved, no `ScenarioConfig` field added, no new
case, no solve outside the three, no year past 2030. **DOF ledger: ZERO free parameters**; no
`authorized_price_tuning`. Everything under `src/`, `scripts/`, `configs/` consumed, never
edited. Rule 27: no source file ≥300 lines was rewritten. Rule 29(c) not engaged — these are
registered campaign arms, not screen or control bundles. Backcast byte-identity untouched
(forecast-mode only). No CI workflow created; every solve ran in-session.
