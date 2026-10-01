# FINDING — SOCO-64 (2026-09-24): the measured evidence for a CT start cost, and why it does not answer the G reason — phase 0 only, no solve

**Lane** SOCO-64 · **DATA PROFILE** soco · **Model** Opus (rule 27).
**Owner ruling on reopening `tranche_startup_amortization` for SOCO:** BLANK in the lane prompt. So this lane
ran **phase 0 only**: no field added, `_SOCO_OFFER_CURVE` untouched, no PRECOMMIT, no shard, no registration.
**Keeper / control of record:** `2026-09-24-soco61-dark-unit`, unchanged. Verified at `origin/main`
`06d7de40`: `keepers/SOCO.json` names it, and no `claude/soco64*` ref existed apart from this lane's branch.
**Per-plant legs:** recovered at zero LP from the SOCO-61 shard SHAs (all three fetched) into
`results/calibration/soco61_arm_<Y>`. Gitignored; 0 files tracked.
**Probe:** `scripts/probes/_soco64_phase0.py` (subcommands `noload conduct horizons reach c4`; reuses
`_soco63_phase0`'s class map, fleet arrays, greedy re-stack and C1 rescore). **LP cost: zero.**

---

## 1. HEADLINE

| question | answer |
|---|---|
| Is there measured evidence that SOCO's CTs carry a start cost the keeper omits? | **Yes.** CEMS: CT units start **56×/unit-yr** in **9 h** runs, and **58 %** of CT energy comes from runs < 12 h. Boilers, CC and coal run 105–439 h. |
| Does a start cost on the CT econ/peak tranches reach the object? | **Yes, in the right direction, at every scale tested.** Arm B, the registered field's own scope: 2023 CT_PEAKER **+5.23 → +2.78 TWh** and ST_GAS **−5.50 → −3.29 TWh**. Margins widen from 0.81 / 0.74 to **1.83 / 1.66 pp**, and per-plant errors fall. |
| Does the non-selective form reach it? | **No.** Arm A (econ/peak starts on every class) leaves ST_GAS at −5.50. The model's ST econ tranches cycle daily on a hot boiler, so they pay a *larger* amortized start than the CTs. |
| Does the joint form (SOCO-63 §5) reach it? | **No, it goes the wrong way.** 2023 CT_PEAKER lands at **+7.18 TWh, FAIL by 0.01 pp**. For CTs it collapses to the identity band. For CC it carries an extrapolated no-load term. |
| **Does (a)–(c) answer SOCO-53's G reason?** | **No.** The G reason is a market-design category, not an evidence gap, and no measurement can change a category. Phase 0 found something that bears on it: **the keeper already charges this same NREL start markup on SOCO's CT and CC `_committed` tranches** (§6). |

## 2. (a) MEASURED NO-LOAD HEAT INPUT

**A construction fix, declared ex ante.** `derive_unit_bands` fits `heatInput` against normalized load
`x = (P − LSL)/(HSL − LSL)`. Its intercept `c0` is therefore the heat input **at LSL**, not at zero output.
It is not the no-load term. The no-load term is the same fitted curve **evaluated at P = 0**. Two checks are
reported beside it: the literal `c0` and a linear IO intercept. Pooled 2023–2025, unit grain on the committed
`campd_{ct,st,cc,coal}_heat_rates_SOCO_units.csv` class map, and shares of `HSL × own hr_gross`.

The table gives the no-load share of full-load input, cap-weighted by HSL, as [p25 **p50** p75]:

| class | units | LSL/HSL p50 | quadratic @ P=0 | linear intercept | literal c0 (@ LSL) |
|---|---|---|---|---|---|
| CT_PEAKER | 74 | 0.67 | [0.061 **0.173** 0.261], **18 negative** | [0.169 **0.224** 0.247] | [0.667 0.742 0.840] |
| ST_GAS | 12 | 0.18 | [0.037 **0.052** 0.054] | [0.028 **0.030** 0.046] | [0.188 0.205 0.301] |
| CC_REGULAR | 58 | 0.60 | [0.244 **0.281** 0.342] | [−0.001 **0.013** 0.103] | [0.549 0.616 0.667] |
| COAL | 15 | 0.41 | [0.047 **0.056** 0.103] | [0.022 **0.044** 0.064] | [0.405 0.440 0.587] |

**Reading.** CTs and CCs are measured only between ~60 % and 100 % of HSL, so the intercept is a long
extrapolation. The two fits disagree: CC reads 0.28 on one and 0.01 on the other, and 18 of 74 CT quadratic
intercepts are negative. The CT linear value, **~0.22**, is consistent with simple-cycle physics (20–30 %).
Boilers and coal are measured down to 18–41 % of HSL, and their no-load share is small: **3–6 %**.

**Measured, but only an estimate for CT and CC.**

## 3. (b) MEASURED START AND RUN-LENGTH CONDUCT (CEMS opTime > 0 runs)

| class | unit-yrs | starts / unit-yr p50 | median run (h) | energy in runs < 12 h | total starts 2023 / 2024 / 2025 |
|---|---|---|---|---|---|
| CT_PEAKER | 236 | **56** | **9.0** | **57.6 %** (61.9 / 57.6 / 53.9) | 4,913 / 5,420 / 5,534 |
| ST_GAS | 36 | 9 | 263 | 0.0 % | 121 / 113 / 113 |
| CC_REGULAR | 173 | 19.5 | 105 | 0.1 % | 1,926 / 2,276 / 2,111 |
| COAL | 45 | 7 | 439 | 0.0 % | 109 / 134 / 147 |

**What `compute_monthly_markup` would amortize over** (the control's P1 tranche runs; the legs carry no P0).
Values are the MWh-weighted p50 of each tranche-month's mean run length.

| class | `_committed` | `econ*` | `peak` | runs per tranche-month |
|---|---|---|---|---|
| CT_PEAKER | 8.8 / 8.4 / 7.6 h | 10.2 / 9.6 / 8.3 h | 10.2 / 9.4 / 8.3 h | ~30 |
| ST_GAS | 720 / 658 / 523 h | **9.8 / 8.9 / 7.6 h** | 10.1 / 9.4 / 7.9 h | ~28–31 on econ |
| CC_REGULAR | 720 h | 720 / 720 / 371 h | 720 h | 1–2 |
| COAL | 21 / 13 / 720 h | 14 / 10 / 509 h | 13 / 10 / 714 h | varies |

- **CT:** the model's run length (8–10 h) matches the measured 9 h.
- **ST:** the model's econ tranches cycle daily on a committed boiler (measured campaigns are 263 h). An "econ
  start" on a boiler is a load change on a hot unit, not a start.

## 4. (c) START COST — CONSTRUCTION CHOSEN EX ANTE

**Chosen before any reach was computed** (probe docstring): the NREL/SR-5500-55433
`BIN_STARTUP_COST_PER_MW` table the model already carries: **CT 20 / ST 35 / CC 50 / coal 100 $/MW**.

- It is the one registered start-cost constant, and it is already live on CT and CC `_committed` (§6). A
  second number for the same unit's start would break rule 19.
- It includes the wear component that a fuel-only construction omits.

**Fuel-only measured start, reported as a lower bound and never selected.** This is the CEMS heat burned
between sync and reaching LSL, at $3.34/MMBtu (the CT mean delivered gas, 2023–2025).

| class | warm-up p50 | warm-up heat | fuel-only | NREL |
|---|---|---|---|---|
| CT | 1.0 h | 1.07 MMBtu/MW | **$3.6/MW** | $20 |
| ST | 10 h | 6.22 | $20.8 | $35 |
| CC | 2 h | 4.16 | $13.9 | $50 |
| coal | 11.9 h | 12.48 | $41.7 (priced at gas; indicative only) | $100 |

**Fuel is 18–42 % of the NREL figure.** The CT amortized start at NREL is ~$20 / 10 h ≈ **$2/MWh**.

## 5. (d) REACH — greedy re-stack on the keeper legs, arm minus greedy control, zero LP

**Method** (SOCO-63 §4, unchanged). Energy-limited classes and `_mustrun` tranches are held at the solved
dispatch. Markups are static, computed on the control's own dispatch. This is a first-order screen, not a
solve. The greedy control's bias against the solved run (2023: CT 9.79 vs 9.56, ST 3.21 vs 3.80 TWh) cancels in
the difference.

| arm | scope |
|---|---|
| **A** (prompt's non-selective form) | NREL start on econ*/peak of CT, ST, CC and coal |
| **B** (the registered field's own scope) | CT econ + peak, and CC peak |
| **B-v3** | B, with the horizon capped at the CEMS plant median |
| **J** | A, plus SOCO-63 incremental bands with the measured no-load share re-added on econ (`marg + nl_share`) |
| **Z** | the G cell applied consistently: strip the live CT/CC `_committed` markup (§6) |

### Rows (share margin to ±3.00 pp; 2025 rows are SKIPPED as preliminary by the scorer)

| row | keeper | A ×1 | **B ×1** | B ×0.5 | B ×2 | B-v3 | J | Z |
|---|---|---|---|---|---|---|---|---|
| 2023 CT_PEAKER | +5.23 / 0.81 | +5.53 / 0.68 | **+2.78 / 1.83** | +3.71 / 1.44 | +1.99 / 2.16 | +2.64 / 1.89 | **+7.18 FAIL** | +5.43 / 0.73 |
| 2023 ST_GAS | −5.50 / 0.74 | −5.50 / 0.74 | **−3.29 / 1.66** | −4.03 / 1.35 | −2.65 / 1.93 | −3.16 / 1.71 | −6.07 / 0.50 | −5.69 / 0.66 |
| 2023 CC_REGULAR | +2.30 / 1.7 | +1.99 / 1.82 | +2.23 / 1.72 | +2.29 / 1.70 | +2.22 / 1.72 | +2.21 / 1.73 | −1.38 / 2.78 | +2.71 / 1.52 |
| 2024 CT_PEAKER | +2.36 / 2.02 | +3.11 / 1.72 | +0.32 / 2.84 | +1.05 / 2.54 | −0.31 / 2.91 | +0.20 / 2.88 | +4.44 / 1.19 | +2.54 / 1.94 |
| 2024 ST_GAS | −4.69 / 1.19 | −4.54 / 1.25 | −3.00 / 1.86 | −3.56 / 1.64 | −2.58 / 2.03 | −2.87 / 1.92 | −5.00 / 1.07 | −4.87 / 1.12 |
| 2024 CC_REGULAR | +3.14 / 0.81 | +3.01 / 0.86 | +3.10 / 0.82 | +3.13 / 0.81 | +3.08 / 0.83 | +3.07 / 0.83 | −1.50 / 2.66 | +3.51 / **0.66** |
| 2024 COAL_PRB | −4.19 / 1.45 | −4.57 / 1.40 | −3.98 / 1.64 | −4.12 / 1.58 | −3.77 / 1.72 | −3.96 / 1.65 | −0.93 / 2.86 | −4.54 / 1.41 |

**No status moves in any arm except J**, which fails 2023 CT_PEAKER.

### Per-plant Σ|model − 923|, TWh (keeper → arm B ×1)

| year | CT_PEAKER | ST_GAS | CC_REGULAR |
|---|---|---|---|
| 2023 | 8.68 → **6.86** | 5.35 → **3.36** | 11.97 → 11.81 |
| 2024 | 7.06 → 5.32 | 4.51 → 2.82 | 9.29 → 9.12 |
| 2025 | 6.19 → 5.40 | 4.99 → 3.77 | 10.49 → 10.56 |

For comparison: arm A leaves CT and ST per-plant error flat or worse (2023 CT 8.68 → 8.82). J worsens CT in
every year (2023 CT 8.68 → 9.97).

### C4 coal (r / NRMSE), keeper → arm

| year | keeper | A | **B ×1** | B ×2 | J | Z |
|---|---|---|---|---|---|---|
| 2023 | 0.904 / 0.210 | 0.916 / 0.204 | **0.912 / 0.199** | 0.917 / 0.192 | 0.860 / 0.218 | 0.907 / 0.213 |
| 2024 | 0.843 / 0.235 | 0.870 / 0.239 | **0.844 / 0.229** | 0.855 / 0.221 | 0.806 / 0.217 | 0.842 / 0.241 |
| 2025 | 0.882 / 0.200 | 0.891 / 0.184 | **0.885 / 0.202** | 0.886 / 0.204 | 0.857 / 0.236 | 0.877 / 0.199 |

**Distance** (generation-weighted offer, 2023, $/MWh):

| arm | CT_PEAKER | ST_GAS | COAL | CC_REGULAR |
|---|---|---|---|---|
| B | 34.00 → 36.15 | 34.35 (unchanged) | — | — |
| A | 34.00 → 36.15 | 34.35 → **36.86** | 28.16 → 30.20 | — |
| J | — | 34.35 → 38.06 | — | 23.52 → **27.87** |

- **Arm A:** ST outruns CT, which is why A does not move the split.
- **Arm J:** CC rises by the extrapolated 0.28 no-load share.

### Why J fails, structurally

In a pure LP, incremental HR plus no-load ÷ HSL ≈ average HR. The CT joint band p50 measures **0.984 / 0.982**,
which is essentially the identity. So for CTs the joint form adds nothing beyond the start term. For CC, the
no-load term is the unstable extrapolation of §2. **SOCO-63 §5's "joint form might be admissible" is answered:
it is not a distinct carrier.**

## 6. (e) RULE 19 — WHAT ALREADY PRICES THE SAME TRANCHES

**Keeper census, zero LP** (solved `mc` minus the rebuilt fleet `mc_base`, 2023):

| tranche | carries a start markup in the keeper? |
|---|---|
| CT_PEAKER `_committed` (18) | **YES**: NREL $20/MW amortized over run length; **median $4.82/MWh, max $20.00** |
| CC_REGULAR `_committed` (18) | **YES**: NREL $50/MW; median $0.07, max $50.00 |
| CT / CC econ*, peak | no (exactly 0.000) |
| ST_GAS, all tranches | no (`gas_st_startup_cost` off) |
| COAL, all tranches | no (`coal_warm_committed` on, SOCO-58) |

| existing carrier | relation to arm B |
|---|---|
| NREL CT `_committed` start (live) | **Same constant, same `compute_monthly_markup` channel.** B extends it to the CT tranches that are *additional units* (each tranche pays one start). It replaces nothing and stacks nothing. |
| `coal_warm_committed` (K) | Untouched by B. Arm A would put a $100/MW start on coal econ tranches, which CEMS says are loading on a warm boiler (439 h runs). That is refused physically. |
| `gas_st_startup_cost` / `soco_gas_st_campaign_commitment` (K) | These own ST. Arm A's ST econ start charges daily load-following on a committed boiler as if it were a start. That is refused physically. |
| PRB sigmoid | Coal fuel term. Untouched by A or B. |
| `measured_*_heat_rates` (K) | The base HR, and it keeps the no-load fuel inside the average. B adds no no-load term, so nothing is double counted. J re-adds no-load explicitly (§5). |

**Scope by measured physics, not class name (rule 18).** The CEMS run length separates the tranches whose
dispatch *is* a start from the rest:

- CT units run 9 h and start 56×/yr;
- boilers, CC and coal units run 105–439 h.

That is exactly where arm B puts the start and arm A does not. A reopen should cite the measured run length as
the eligibility test, not the fast-start eligibility list the code comment borrows from ISO-NE.

## 7. (f) THE G TEST

**SOCO-53 §2.4, verbatim:**
> **`tranche_startup_amortization` → `G`, no reopen condition.** It is the FERC Order-825 **fast-start pricing**
> object (bid markup only), and **SOCO has no clearing price, no offers and no market**. Arming a market-design
> pricing rule on a footprint with no market is rule 1 `[R-STRUCT]` verbatim.

**In plain words: (a)–(c) do not answer it.** The reason is a statement about *what the mechanism is*, a
pricing rule, and not a claim that SOCO's CTs lack start costs. More CEMS data cannot turn a pricing rule into
a cost, and "2023 ST_GAS would widen its margin" is not an argument (rules 1, 14). Nothing fails today either
way.

**What phase 0 found that does bear on it** is a zero-LP census of the keeper, not a CEMS statistic:

1. **The keeper already runs this object in SOCO.** The same `compute_monthly_markup` NREL start amortization is
   live on 18 CT and 18 CC `_committed` tranches (§6), with no market. SOCO-58 removed the coal limb because
   the boiler is warm (a physics reason), not because SOCO has no market. **So "SOCO must carry no start
   amortization" is not what the keeper does.** Either the G reason is wrong as stated, or the keeper is
   inconsistent with it.
2. **In this LP the markup is an objective cost, not only a price adder.** SOCO's own dispatch is cost-based.
   A production-cost-minimizing commitment includes start costs by definition, and SOCO has no clearing price,
   so the only role of the term that is observable in SOCO is the cost role. **This is an argument, not a
   measurement.** Whether it re-characterizes the object is the owner's call.

**The two consistent positions, with their numbers:**

| position | what it implies | measured consequence |
|---|---|---|
| **Keep G, apply it consistently** | strip the live CT/CC `_committed` markup | arm Z: 2023 CT/ST margins 0.73 / 0.66 (slightly worse); 2024 CC_REGULAR margin **0.81 → 0.66** |
| **Reopen as a cost, scoped by measured run length** | arm B: the existing field, NREL $20/MW, no new scalar | 2023 CT/ST margins **1.83 / 1.66**; per-plant CT −1.8, ST −2.0 TWh (2023); C4 flat to better; 2024 CC unchanged (0.82) |

**Not measured, and stated:**

- the NREL level itself: fuel-only is $3.6/MW against $20, and the balance is literature wear;
- the true P0 horizon (the P1 proxy is used);
- LP interactions beyond the greedy first order.

B keeps its direction at ×0.5 and at ×2, and does not overshoot. 2024 CT_PEAKER reaches −0.31 TWh at ×2, still
PASS.

## 8. GOVERNANCE / GATES

- No `ScenarioConfig` field. No bundle, sidecar, payload or bench part. No offer band touched, and no
  `authorized_price_tuning` key. `actual_lmp.json` gets no SOCO block.
- The keeper's reads are unchanged: C1 14/14 · free 10/10 · C2/C4/C6/C8 PASS · C3a/b/c UNSCORABLE · grade
  5/5/0 · DOF 13/1. The scorer's literal "PHYSICALLY-CALIBRATED (PRICE UNSCORED)" is not SOCO's determination.
- **Matrix (rule 28(b)):** no verdict changed. SOCO-64 notes were prepended to `tranche_startup_amortization`
  (G) and `committed_band_measured_basis` (U) in the SOCO shard, plus a §5.8 note.
- **E13 standing:** `2026-09-20-soco53g-prb-own-iso` is still unruled, and rule 31 forbids deleting it.
  Re-raised; the standing recommendation is decline.

## 9. THE OWNER QUESTION

**Reopen `tranche_startup_amortization` for SOCO (yes/no)?** It would be reopened under these terms:

- re-characterized as a **cost-based start cost in the dispatch objective**, not a fast-start pricing rule;
- **scoped by measured CEMS run length**, which makes it the field's own CT econ/peak scope (plus CC peak);
- at the NREL $20/MW already live on CT `_committed`, with no new scalar.

**Evidence for yes:** CT 56 starts/unit-yr, 9 h runs, 58 % of CT energy from runs < 12 h. The keeper already
amortizes the same start on CT/CC `_committed`. First-order reach: 2023 CT **+5.23 → +2.78**, ST
**−5.50 → −3.29 TWh**, per-plant CT/ST error −21 % / −37 %, no row worse.

**Evidence for no:** SOCO-53's category argument still reads literally, and none of the above is a measurement
that refutes it. If no, a consistency lane should decide on arm Z: strip the live `_committed` markup, at a
cost of 2024 CC_REGULAR margin 0.81 → 0.66 pp.

**If YES:** PRECOMMIT (G-DRIFT plus these predictions, pushed and SHA-pinned), then three year-isolated shards
per SOCO-61 PRECOMMIT §7, ~9 min/yr. Recommendation: **yes**, but only on the cost re-characterization. It is
the owner's ruling to make.

Leftover refs for the owner to delete (a session cannot delete refs):

- `claude/soco61-arm-{2023,2024,2025}`;
- `claude/soco60-arm-*`;
- `claude/soco60-armB-*`.

SOCO-64 created **no** shard branches.

## 10. WHERE EVERY BYTE LIVES

Nothing was solved, so there is **no promotion question**. The keeper bundle on `main` is untouched. The scratch
CSVs (`soco64_noload.csv`, `soco64_conduct.csv`) and the fleet `.npz` arrays live only in this container's
scratchpad. They are regenerable in ~5 min with `_soco64_phase0.py noload` / `conduct` and
`_soco63_phase0.py fleet`.

## Log entry

```
## soco-64 — 2026-09-24

MEASURED EVIDENCE FOR A CT START COST, AND WHY IT DOES NOT ANSWER THE G REASON
-- PHASE 0 ONLY, ZERO LP. Owner reopen ruling blank: no field, no solve,
_SOCO_OFFER_CURVE untouched. Keeper 2026-09-24-soco61-dark-unit unchanged.

(a) No-load heat input: derive_unit_bands' c0 sits at LSL, not P=0; evaluated
at P=0 the no-load share of full-load input (cap-wtd p50) is CT 0.17 quad /
0.22 linear (18/74 quad negative), ST 0.05, CC 0.28 quad vs 0.01 linear, coal
0.06 -- CT/CC are extrapolations from 60-100 % of HSL. (b) CEMS conduct: CT
56 starts/unit-yr, 9 h median runs, 58 % of CT energy in runs <12 h; ST 9 /
263 h, CC 19.5 / 105 h, coal 7 / 439 h. Model CT tranches run 8-10 h (matches);
ST econ tranches cycle ~10 h on a committed boiler. (c) Start cost chosen ex
ante = the NREL table already live (CT $20/MW); fuel-only measured $3.6/MW is a
lower bound. (d) Greedy restack on keeper legs: arm B (field's own scope, CT
econ/peak + CC peak) 2023 CT +5.23 -> +2.78, ST -5.50 -> -3.29 TWh (margins
1.83/1.66 pp), per-plant CT 8.68 -> 6.86, ST 5.35 -> 3.36; C4 flat/better;
x0.5/x2/v3 same direction. Non-selective arm A does not move ST (ST econ pays a
bigger amortized start than CT). Joint arm J (SOCO-63 bands + no-load) FAILS
2023 CT (+7.18, margin -0.01): CT joint band 0.98 = identity, CC carries the
extrapolated no-load. (e) KEEPER CENSUS: the same NREL markup is ALREADY LIVE
on 18 CT _committed (median $4.82, max $20/MWh) and 18 CC _committed tranches.
(f) (a)-(c) do NOT answer SOCO-53's G reason (a market-design category, not an
evidence gap). The census does bear on it: the keeper already runs the object;
either the G is wrong as stated or the keeper is inconsistent. Consistent-G arm
Z (strip committed markup): 2024 CC_REGULAR margin 0.81 -> 0.66.

OWNER QUESTIONS: (1) reopen tranche_startup_amortization for SOCO as a
cost-based start cost scoped by measured CEMS run length (arm B, NREL $20/MW,
no new scalar)? recommendation yes, on the cost re-characterization only; if
no, rule on arm Z for consistency. (2) decline 2026-09-20-soco53g-prb-own-iso
(E13)? Leftover refs for the owner: claude/soco61-arm-*, claude/soco60-arm-*,
claude/soco60-armB-*. Records: docs/handoffs/FINDING-soco-64-2026-09-24.md,
scripts/probes/_soco64_phase0.py.
```
