# PRECOMMIT — closeout-NEISO step 3: the ISO-NE scarcity-physics arm (7 legs)

Lane `closeout-neiso-wave1` → wave 2. Written 2026-10-02, **before any LP and before any number from the arm
exists**. Plan: `docs/backcast-closeout-plan-2026-10.md` §3.2 step 3. **SOLVES HELD** until the W0 settlement merges
and the desk releases this lane; then this session is parent for the 7 legs (`shard_prompt.py --all-years`, full
SHA, compose, verdict, `promote_keeper.py` only if nothing regresses).

Incumbent keeper (the control, rule 29(b)): `2026-09-26-neiso-119-anchor-fuelsec`, bundle
`results/calibration/neiso119_span` (basis `00d4a7691c2f30c39a72d9d99e31a2ce1d07546f`), CALIBRATED 2019–2025.
After W0 merges, the control is **W0's NEISO re-solve** if W0 promotes one; otherwise neiso-119. The arm's legs solve
on whichever is the keeper at launch, and the G-DRIFT audit (rule 29(b)) is done against that bundle's basis SHA.

## 1. What the arm is — four limbs, one phenomenon (event-day scarcity physics), rule 19 checked

| # | limb | ScenarioConfig | today in the keeper | measured driver | forward story (rule 13) |
|---|---|---|---|---|---|
| A | **AGT daily completion** — the hub-basis overlay's Algonquin prints come from a complete flow-day series instead of the Wednesday-only narrative prints | **new** `neiso_agt_daily_completion` (bool, default off; registry + matrix row + 9 shard cells in the wave-2 PR) | `gas_daily_shape` **K**, reading `algonquin_citygate_daily.csv` (≈ 52 prints/yr) | EIA New England Dashboard daily archive (S&P Global assessment, ~250 weekday prints/yr, 2019–2025; `fetch_eia_ne_dashboard_agt_daily.py`) + the Weekly-Update NGI prints | identical construction on a forward daily shape; mean-preserving at the measured monthly AGT basis (unchanged) |
| B | **ULSD daily oil shape** | existing `dual_fuel_oil_daily_parity` → **True** | False | EIA NY Harbor ULSD daily, now 2019–2025 (this lane's intake) | mean-preserving within the EIA-923 monthly receipt (unchanged level) |
| C | **Response-scoped reserve eligibility** | **new** `neiso_reserve_response_scoped` (bool, default off; registry + matrix row + 9 cells) | `_neiso_design` eligibility is a FUEL-NAME test: class 0 = {gas_cc, gas_ct, gas_st, coal, nuclear, oil}, class 1 = {gas_ct, oil}; spin shares class 1 and is not online-gated | EIA-860 Schedule 3.1 `Time from Cold Shutdown to Full Load` (`10M` = offline-eligible), CAMPD hourly ramp envelope — the existing `measured_ramp_capability` datatype (needs a NEISO registry module); LP's existing `online_gated` / `reserve_supply_cap` / ramp-capped headroom | unit physics, regenerated for any year; new entrants take class physics |
| D | **Measured nested requirements** replacing the three static rows | existing `neiso_dynamic_reserve_requirements` → **True** | False; static 600 / 1,200 / 1,800 MW | ISO Express hourly ROS requirement, now 2019-05-31 → 2025 (this lane's intake) | forward: the contingency-sized requirement from the forward fleet's largest units |

**Rule 19 (one mechanism per phenomenon).** D *replaces* the static `NEISO_RCPF_PRODUCTS` requirement values per
family (the ORDC step shape stays as published), it does not stack a second requirement. C *replaces* the fuel-name
masks in `_neiso_design`; it does not add a cap beside them. A and B refine the two inputs the existing
`gas_daily_shape` / dual-fuel parity mechanisms already read. Enumerated and **not** touched: `neiso_rcpf_enabled`
(post-solve overlay, G, a hard error under co-opt), the winter fuel-security family (dormant on every year,
`FINDING-neiso110`), `gas_coldsnap_derate` (dormant).

**Why C and D must go together (neiso-111 §6).** C alone leaves the ten-minute families never short (scoped class-1
supply ≥ 1,494.9 MW vs 1,200 in all 8,760 h of 2022) and short in 27 off-event 30-minute hours against the static
1,800. D alone never binds (class-0 supply 6,959 MW at Elliott). Together the 30-minute family crosses at Elliott by
82.5 MW under the strictest scoping. **Correction to the plan's wording, carried into the matrix cell:** the LP's NEISO
families are nested too (spin and ten-minute draw the same class-1 variable, and class-1 headroom also backs the class-0
row, `lp/reserve_rows.py::_build_reserve_rows`), so "static rows overstate by 1,246 MW" is not an LP quantity. Per
family, D tightens ten-minute (+350 MW at Elliott) and thirty-minute (+554) and loosens spin (−212). Measured means
2019–2025: spin 387–544 MW (static 600), ten-minute 1,544–1,751 (static 1,200), TOTAL 2,301–2,539 (static 1,800).

## 2. Exact choices fixed now (no sweeps, no second values)

**A — precedence and date basis.** One flow-day series per year:

1. A Weekly-Update NGI print (the settled index) is placed on its flow day = the next calendar day after its trade
   day. A dated weekly high/low is placed the same way.
2. A dashboard value fills every flow day with no NGI print. Its `label_date` is taken as the flow day (evidence:
   dashboard 12/22/22 6.54 and 12/23/22 30.16 against the ISO-NE IMM gas-day step $6.66 → $30.05 at HE 11 Dec 23; NGI
   trade-day prints match the dashboard one business day later across all 323 overlapping 2019–2025 pairs at
   corr 0.989, median |Δ| $0.02, 88 % within 5 %, against corr 0.872 / median $0.26 unshifted —
   `agt_dashboard_vs_ngwu.json`; the largest lagged miss is the Feb-2023 case below).
3. Days with neither (weekends/holidays) take the value in force under the existing staircase rule.
4. **No other source enters.** ISO-NE IMM figures are a multi-hub composite (Algonquin Citygates, Algonquin Non-G,
   Portland, TGP Z6-200L, …), not Algonquin; they are recorded as evidence only.
5. Mean preservation at the measured monthly AGT basis is unchanged (`iso_hub_daily_gas_prices`). Only the
   within-month shape moves.

Rule 1 rationale: (1) beats (2) because the dashboard is a 10:00 snapshot, not a settled index, and it is known to
miss the final assessment on at least one extreme day (flow 2023-02-03: dashboard 26.06 vs NGI 71.42 traded Feb 2
vs ISO-NE composite 76.42). Fixed before any solve, because the precedence choice is visible in the gas input.

**B** — `dual_fuel_oil_daily_parity=True`, no other change.

**C — eligibility by physics, not names (rule 18).**

| family | eligible capacity |
|---|---|
| spin (`ne_10min_spin`) | online units only (`online_gated`, ρ = 1), headroom capped at 10 × the unit's measured 1-minute ramp (`measured_ramp10_frac`); storage as today |
| ten-minute (`ne_10min_total`) | spin-eligible + offline units whose EIA-860 cold-start-to-full-load is `10M` (their `fast_start_mw`) |
| thirty-minute (`ne_30min_total`) | ten-minute-eligible + online headroom at 3 × the 10-minute ramp. Offline `1H`-bin units are **excluded**: the bin spans 10–60 min and cannot certify a 30-minute start. Declared choice; it is the one structural degree of freedom. |

EIA-860 rows with no cold-start entry take their class's 10-minute fraction online and are not offline-eligible. No
NEISO parameter is carried from PJM/MISO/CAISO (rule 25). Spin gets its own online-gated class, so the LP carries
three classes for NEISO instead of two.

**D — the two unpublished windows.** The loader hard-errors on an incomplete year (rule 34 needs all 7 years), so the
owner must pick one of the following before the wave-2 build. Recommendation (a).

| option | 2019-01-01 .. 05-30 (3,600 h) | 2020-12-10 .. 17 (149 h) |
|---|---|---|
| **(a) adjacent-year measured carry** | the same calendar hours of the 2020 published series, day-of-week aligned, labelled `source=carry_2020` | step-hold the last published hour before the outage (the parser's existing hole rule), with `MAX_GAP_HOURS` raised for 2020 only by a cited exception |
| (b) static rows in the gap | the static 600 / 1,200 / 1,800 for those hours (a mixed basis inside one year) | same |
| (c) drop D from 2019 and 2020 | arm D on 2021–2025 only (a per-year config split; rule 16 still met — one bundle) | — |

(a) keeps one basis across the year. The requirement is set by the largest contingencies (Seabrook, Mystic 8/9, the
HQ Phase II import), present in both 2019 and 2020, and the spin fraction (0.31) is the same regime. The Morning Report
daily requirement is not a substitute: it is a peak-hour planning number at 0.64–1.18× the hourly ROS TOTAL.

## 3. Pre-fixed readings (before any number)

| reading | expected | basis |
|---|---|---|
| Dec 23–27 2022 model delivered gas | rises from $12.5–15 toward the flow-day series (30.16 Dec 23; the dashboard prints 35.00 on 12/27 and nothing Dec 24–26 — read as the holiday strip, an inference), mean-preserved within the month | intake series |
| Dec 24 2022 model hub price | reaches oil parity (~$250 class); 1–3 RCPF hours on Dec 24 2022; 0–2 on Jun 24 2025 | neiso-111 §6 crossing 82.5 MW (strictest scoping; real design looser) |
| C3c 2022 / 2023 / 2025 | **stay CAVEAT** (2022 needs ≥ 59 h, 2023 ≥ 8, 2025 ≥ 10) | P(any C3c gate closes) **≤ 0.1** |
| C3a | Jan 2022 monthly bias (+$15.9) falls; annual C3a moves ≤ 2 pp in every year | shape-only, mean-preserving inputs |
| C1 / C3b / C2 / C4 | no status change in any year | — |
| reserve shortfall hours | ≤ 10 h/yr in every year (real Total30 shortage 0.5–3.6 h/yr) | IMM AMR Table 4-6 |

**Promotion rule (rule 1).** Promote if (i) no criterion goes PASS → FAIL in any year, (ii) |ΔC3a| ≤ 2 pp in every
year, (iii) no year's reserve shortfall exceeds 10 h, (iv) C8 forced-energy budget still passes. Promotion stands on
fidelity (rules 14/18), not on a gate. **Stop and report without promoting** if (iii) fails: that means the scoping is
too strict, and it is not tuned (rule 1); the record says so and the owner rules. A C3c PASS is reported, not targeted.

**Probability.** The arm closes a gate: ≤ 0.1. It removes the rule-18 defect and places Elliott/Feb-2023 gas on true
days: high. Some year breaches the 10 h shortfall stop: 0.25 (the 27 off-event 30-minute hours neiso-111 found against
the static requirement are the risk; D raises the requirement).

## 4. Build list for wave 2 (before any shard; one PR; fast tier first)

1. `neiso_agt_daily_completion` field + registry + `solve_surface_declared` + matrix row in `mechanism-matrix.js` + a
   cell in every shard (rule 28; the base file is touched once for the row, per its own rule). The merge of the
   dashboard CSV and the NGI prints under §2-A, in `data.fuel.hubs` behind the flag. Tests: the precedence rule on a
   3-day fixture, mean preservation exact.
2. `neiso_reserve_response_scoped` field + the same registration; `scripts/lib/ramp_capability/neiso.py` registry
   module; `_neiso_design` builds three classes behind the flag. Tests: 1-gen/1-zone/24-h fixtures — an offline `10M`
   unit serves ten-minute but not spin; an offline `1H` unit serves nothing; an online unit's spin is ramp-capped.
3. Owner's §2-D choice implemented in the reserve-requirements parser/loader with its source label.
4. Census before shards (zero LP): `fleet_only` rebuild of 2022 with the arm, reproducing neiso-111's scoped supply
   at Elliott hour 8633 within the §2-C design (expected looser than 2,271.6 MW).
5. Shards: `shard_prompt.py --iso NEISO --all-years --sha <40-char> --lane closeout-neiso-scarcity --bundle <keeper>
   --set neiso_agt_daily_completion=true --set dual_fuel_oil_daily_parity=true --set neiso_reserve_response_scoped=true
   --set neiso_dynamic_reserve_requirements=true`. Each leg also writes `unit_marginal_<Y>.parquet` (rule 15).

## 5. Not in this arm (named so nobody adds them mid-flight)

Any oil-steam or fast-start offer adder; pinning oil burn to CAMPD; an RCPF overlay on the co-opt; a NEISO
"print-level" (non-mean-preserving) AGT variant (the NYISO `nyiso_gas_daily_print_level` analogue — a separate
question with its own PRECOMMIT); the 2019 oil heat-rate defect (Canal 1/2 at 4.14, Mystic 7 at 7.60 —
`SPEC-closeout-neiso-w0-regression-guard` §2; it is W0's join or its own lane, not this arm's).
