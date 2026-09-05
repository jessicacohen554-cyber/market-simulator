# FINDING — capx D51: the MISO internal-supply accounting ratio re-identified on the dates-ON fleet — one term moved, 0.8546 → 0.8934; the A/B; NEISO leg 7 (owner ruling Q36); the records rider (D47 §6 items 2 and 4, D49 §5 item 5, owner ruling Q37)

**Lane:** capx D51 — the rule-23 `[R-FROZEN-DERIVE]` re-derivation D49 §2.6 routed (director
dispatch; capx ledger §0ae). Branch `claude/capx-d51-miso-ratio-rc83dw` (harness-assigned;
the dispatch named `claude/capx-d51-miso-accounting-ratio`), fresh off `origin/main`
`a35c9f9`. **Pre-declaration:** `docs/handoffs/PREDECL-capx-d51-2026-09-04.md`, pushed at
`483bb95` BEFORE the derive script existed and before any solve; graded at full magnitude in
§5, misses included. **Date:** 2026-09-04.

**NOTHING ARMS.** One `ScenarioConfig` field lands DEFAULT-OFF
(`adequacy_accounting_ratio_dated_net`); the re-identified value is a NEW registry entry the
gate alone resolves; the A/B registered SUFFIXED (`miso-t1h-d51-ratio`); NEISO leg 7 registered
SUFFIXED (`neiso-t1h-d45r-datesoff`); the bare `miso-t1h` / `neiso-t1h` verdict keys, every
keeper / shard verdict letter / marker, and the backcast namespace are untouched. Rules 12,
13, 14, 21, 22, 23, 24, 25, 27, 28 hold (§9). The owner arms or declines on the pre-stated
condition (§7).

---

## 0. Verdict (one paragraph)

**The ratio re-identifies to 0.8934 (0.878 / 0.909 per year) with D31's construction reproduced
to the decimal and one term moved; armed, it puts the positions exactly where the identity said
(1.0777 / 1.0194 / 0.9875 — the 2024 double-netting closed from 5.8 pts short of the market's
1.034 to 1.5), crosses the PY2024 cliff ($113.6 → $0/kW-yr) and returns the undated cohort to
the floor-capped regime (995 candidates / 79.7 GW fail in 2024 and every one is capped, where
D46 carried zero rows).** What the longer position releases is small — 477.4 MW of coal at the
2022 bridge, 1.1 % plant-grain precision, D32's near-random selection at one sixth of the
pre-declared magnitude (P5 MISS) — so `retire.total_gw` moves 9.799 → 10.276 GW (−40.8 %, FAIL
both) and the under-build stays with D32 R2/R3 and the additions lane, as D49 §2.6 said it
would. The BLK-10 backstop that built 2.4 GW of gas_ct on the short ledger no longer fires:
`add.by_tech.gas_ct` 4.415 → 1.472 (FAIL → PASS) and every addition SHARE moves with the
denominator, `add.shares.gas_cc` reading PASS → FAIL. The 2025 term is $230/kW-yr at the model's
own position, not the $91–110 D49 quoted at the market's 1.0174. NEISO leg 7 reproduces the D37
control to the decimal (P16 HIT: HEAD drift inert) and refutes P17's counter-example limbs: at
the shipped lever the dates flip improves or holds every gated retirement row, so **Q30's
default has no NEISO-side counter-example** — a finding, not a recommendation. Both legs HOLD.
On the pre-stated §5 condition, limbs (a), (b), (d) are met and (c) is **not met by the
letter** (a share row outside the named set moved) though its stated rationale — a second
object moving the position — is absent; the lane reports both readings and does not override
its own pre-registration. The owner decides (§7).

---

## 1. The re-identification — one term moved

### 1.1 What D31 identified, reproduced from the committed ledgers to the decimal

D31 §2: `ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO["MISO"]` = PRA Summer offered
Generation ZRC ÷ the model's census internal firm on the two clean overlap years, the
denominators being the D27 T1-H entering-fleet ledgers (`fleet_by_fuel_before` at 1 − EFORd
+ the prior solved year's wind × 0.166 / solar × 0.3875 / storage firm + the year's hydro
× 0.62). `scripts/data/derive_miso_adequacy_accounting_ratio.py` rebuilds that construction
from the committed D27 ledgers and gets D31's numbers back exactly:

| planning year ↔ fleet year (pools year) | PRA offered Generation (MW ZRC) | D31 denominator, rebuilt | D31 cites | per-year ratio |
|---|---:|---:|---:|---:|
| PY2023-24 ↔ 2023 (2021) | 122,375.6 | **143,822.1** | 143,822.1 | 0.85088 |
| PY2024-25 ↔ 2024 (2023) | 123,395.6 | **143,749.5** | 143,749.5 | 0.85841 |
| capacity-weighted | 245,771.2 | 287,571.6 | | **0.854643** (= the registry) |

### 1.2 The term that moves: the dated channel, measured, not retyped

The D27 (dates-OFF census) minus D46 (dates-ON, key `eff2c890746ec966`) `fleet_by_fuel_before`
difference, per fuel, IS the fossil-dates channel and nothing else — the reconciliation test
asserts it row-for-row against the D46 ledgers' own step-1b entries:

| entering year | coal | gas_st | gas_cc | oil | nameplate total | = backlog + drops + derates | accredited (1 − EFORd) |
|---|---:|---:|---:|---:|---:|---|---:|
| 2023 | 4,727.1 | 138.1 | 22.5 | 10.9 | 4,898.6 | 893.6 pre-start backlog + 2022 bridge 2,108.6 fossil drops + 1,896.3 derates | **4,508.5** |
| 2024 | 7,936.0 | 693.9 | 22.5 | 10.9 | 8,663.2 | + 2023's 2,162.3 drops + 1,602.4 derates | **7,977.6** |

Nuclear (Palisades, the non-fossil announced channel) and biomass are identical in both
ledgers: that channel was already in D27's census and is NOT part of the moved term. Since
Q30/D44 these megawatts leave the fleet at step 1b before the position is computed, so a ratio
that was identified with them still in the denominator nets them a second time.

### 1.3 The value

| | 2023 | 2024 | combined |
|---|---:|---:|---:|
| dated-net denominator | 139,313.6 | 135,771.9 | 275,085.5 |
| **ratio, re-identified** | **0.87842** | **0.90884** | **0.893436** |
| D31 | 0.85088 | 0.85841 | 0.854643 |
| scale r₁ / r₀ | | | 1.04539 |

D49's back-of-envelope prior (~0.88 / 0.91) lands within 0.002 of both per-year values.
Everything else is held exactly as D31 identified it — numerators, class bases, the
prior-year pool convention, the Summer season, the two-year mean, the D27 pools (the D33 VRE
additions are a model outcome and do not enter, as D31 held), the unscaled tie. **Zero free
parameters; nothing sized by the exit residual.** Shipped as
`ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_DATED_NET_BY_ISO["MISO"] = (122,375.6 +
123,395.6) / (139,313.6 + 135,771.9)` behind `adequacy_accounting_ratio_dated_net` (default
`False`, registered in `_CACHE_KEY_OPTIONAL_FIELDS` at `False`: default key
`4c6b03ae098b6e3e` and the bare `miso-t1h` recipe key `eff2c890746ec966` unmoved, verified;
armed `b538d37b36a88247`; backcast-coerced), resolved at all three D31 seams — the ledger /
CR-1 position, the floor's aggregate test and per-unit increments, the backstop's crediting —
through the one resolver `resolve_internal_supply_accounting_ratio(iso, config)` (one basis,
rule 19); any ISO absent from the dated-net registry falls through to D31's value even when
armed (rule 25). Harness flag `run_capacity_hindcast.py --adequacy-accounting-ratio-dated-net`.
Tests: `tests/unit/model/test_capacity.py::TestInternalSupplyAccountingRatioDatedNet` (value,
unarmed byte-identity, armed one-basis at all three seams, cache-key registration, backcast
coercion) and `tests/curation/test_derive_miso_adequacy_accounting_ratio.py` (D31 reproduction
exact, the moved term ≡ the ledger rows, registry ≡ derivation). Rule 28: base row
`adequacy_accounting_ratio_dated_net` + a cell in all six shards (MISO `fc: O`, the other
five ISO-exclusive `·`); `check_mechanism_matrix.py --base origin/main` and
`check_cache_key_registration.py` clean; 1,081 config/regression tests + the capacity suite
green.

### 1.4 A reconstruction residual, stated

The D46 ledger's 2024 position (0.976427) reconstructs EXACTLY from `fleet_by_fuel_before(2024)`
+ the 2023 pools (implied raw internal 135,772.0 = the dated-net denominator 135,771.9). The
2023 and 2025 ledger positions do not: 2023's implied raw internal is 142,812 against 139,314
built (+3,498, consistent with a position computed on the fleet before the bridge year's step-1b
rows landed — 142,998 on that hypothesis, −186 off), 2025's is 128,575 against 136,030 built
(−7,455, unexplained by any class-credit change I could construct). Recorded in the
pre-declaration §0 and here; §3 reads the arm's own ledgers rather than the construction.

---

## 2. What was solved

| leg | run id | registers as | key (pre-declared → realized) | posture delta from its comparator | wall | order |
|---|---|---|---|---|---:|---|
| rider (d) | `neiso-2021-2025-realized-t1h-d45r-datesoff` | **`neiso-t1h-d45r-datesoff`** | `5925e67c572a910f` → **match** | `fossil_announced_exits_enabled` True → False vs the bare `neiso-t1h` (D45-R L5); config-identical to `neiso-t1h-d37-control` (2026-09-02 HEAD) | 4.8 min | first |
| A/B arm | `miso-2021-2025-realized-t1h-d51-ratio` | **`miso-t1h-d51-ratio`** | `b538d37b36a88247` → **match** | `adequacy_accounting_ratio_dated_net` False → True vs the bare `miso-t1h` (D46, `eff2c890746ec966`, re-resolved unmoved at HEAD) | 18.9 min | solo, after |

Both: `--start-year 2021 --end-year 2025 --vintage 2020 --fuel-variant realized
--entry-screen-diagnostics`, solved {2021, 2023, 2024, 2025}, 2022 bridged, `SOLVE-YEAR PARITY`
held, no leakage-guard violation, the holdout freeze asserted by the run banner. Sequential
(rule 12). **Environment:** 4 cores / 15 GB / no swap; full clone; `data/clean` ABSENT at
session start and rebuilt in full (`regenerate_clean.py`, 54 datatypes, 0 failures, ~90 min —
the CAMPD `emissions` curation dominates) so both legs solved on the same input surface as
their comparators. The harness does not instrument peak RSS for a T1-H leg; `free` read ~7 GB
in use mid-solve.

**Mid-session HEAD move, disclosed.** capx D50 (`ccs_retrofit_capex_co2_scaling`, a default-off
registered field) and miso-210 / nyiso-188 / nyiso-189 landed on `origin/main` during the
solves. The branch was rebased before the final push; conflicts were confined to the appended
cache-key registrations in `scenarios.py` (both fields kept, D50's first), the matrix base
row's line anchors (repaired with `--fix-anchors`), the regenerated parameter registry, and
`ff-verdicts.json`'s tail (D50's two keys and mine — re-spliced, insert-only). All four keys
above re-resolve unmoved at the rebased HEAD (`ScenarioConfig()` `4c6b03ae098b6e3e` included),
so D50's field is inert for both legs by registration. The gate-(a) failure this lane found on
the pre-rebase base (MISO's board row keyed to miso-202 after the owner's miso-210 promotion)
was re-keyed on `main` by the director desk in the interim; `check_gate_a_provenance.py` reads
OK at the rebased HEAD.

---

## 3. The A/B — `miso-t1h-d51-ratio` vs the bare `miso-t1h` (D46)

### 3.1 The position, the requirement, the term (the ledgers' own rows)

| screen year | requirement (both) | position D46 → D51 | predicted (PREDECL P2) | market's own | coal capacity term D46 → D51 ($/kW-yr) | ledger reserve margin D46 → D51 |
|---|---:|---|---|---:|---|---|
| 2021 (seed) | 115,042 | — | — | — | — | 0.098 → 0.146 |
| 2023 | 121,644 | 1.0322 → **1.0777** | 1.070–1.085 (c. 1.078) | 1.049 offered | 0 → 0 | −0.010 → +0.033 |
| 2024 | 122,429 | 0.9764 → **1.0194** | 1.015–1.024 (c. 1.019) | 1.034 offered | **113.6 → 0** | −0.015 → +0.025 |
| 2025 | 119,509 | 0.9488 → **0.9875** | 0.965–0.995 | 1.0174 cleared | **458.4 → 229.9** | 0.052 → 0.077 |

The requirements are byte-identical: the ratio moved the supply side and nothing else. The
2024 position lands 0.0002 from the identity's value on the D46 fleet (the two entering
fleets are the same MW); 2025 lands 0.003 below the same-fleet identity, which is exactly the
477.4 MW executed in 2024 × 0.92 × 0.8934 ÷ 119,509. The reserve margins the ledger carries
(D42 §7.4's routed I7-class negatives in 2023/2024) are positive in every year.

### 3.2 The regime, screen by screen (`pipeline_events`)

| screen | D46 | D51 |
|---|---|---|
| 2022 bridge | 1,497 `entry_capped` / 76,751 MW; 0 decided | 1,492 capped / 76,273 MW; **5 decided / 477.4 MW coal** |
| 2023 | 948 capped / 74,223; 0 decided | 943 capped / 73,746; 5 `re_confirmed` / 477.4 |
| 2024 | **no rows** (every unit clears on the $113.6 term) | **995 capped / 79,692 MW** (coal 36,729 / 182 tranches; gas_ct 22,799; gas_cc 10,473; gas_st 6,509; oil 3,183 — capacity revenue 0 on every row); 5 `executed` / 477.4 |
| 2025 | no rows | no rows (the $230 term clears every bar) |

The 2024 regime flip is the whole rule-14 sign of the lane: the cohort D49 §2.3 found
"capacity-cleared" in 2024 is back below the bar and back in the floor's hands, capped to a
unit. The 2022 release is the position's only exit-side effect: **John P Madgett p4271 123.2 /
R S Nelson p1393 170.3 / D B Wilson p6823 178.9 MW plus 5.1 MW at Prairie Creek p1073 and
Muscatine p1167** — the floor's cheapest-firm-cost order picking coal tranches in D32 §3.2's
float-noise buckets. Prairie Creek and Muscatine are real-exit plants; the three large
tranches are not: **plant-grain precision of the released MW 1.1 %** (5.1 of 477.4), and of
ALL released MW 98.5 % → 94.0 %. Why so little was released (PREDECL P5 bracketed 1.5–5.5 GW):
the admission cap's counterfactual at the 2024 horizon is long by only ~0.4 GW accredited under
r₁, not the 1.3–4.2 GW the pre-declaration bracketed from the realized 2024 requirement — the
counterfactual nets every pending dated row through the horizon, credits no entry that
commissions between decision and execution, and projects the peak on the growth path, all of
which the pre-declaration named but under-weighted. The 2023 and 2024 screens' counterfactuals
(horizons 2025 / 2026) are short, as predicted: 0 admitted.

### 3.3 FC-3, row by row (only the rows that moved are bold)

| row | D46 (bare `miso-t1h`) | D51 arm | actual | band |
|---|---:|---:|---:|---|
| `retire.total_gw` | 9.799 (−43.6 %) | **10.276 (−40.8 %)** | 17.369 | FAIL → FAIL |
| coal | 7.877 | **8.355** | 12.434 | |
| gas_st / oil / gas_ct / gas_cc / nuclear / biomass | 0.849 / 0.154 / 0.132 / 0.002 / 0.768 / 0.016 | identical to the decimal | 2.127 / 0.543 / 0.399 / 0.858 / 0.812 / 0.196 | |
| `retire.unit_recall_gt300` (plant-grain) | 16/19 (0.737) | 16/19 (0.737) | — | PASS both |
| `false_retire` (per-fuel excess) | 0.0 | 0.0 | — | PASS both |
| LOYO recall −2023 / −2024 / −2025 | 8/16 / 14/15 / 15/18 | **9/16** / 14/15 / 15/18 | — | holds 2/3 both |
| T-R10a / b | PASS (vacuous) | PASS (first mover coal, 2024, 0.477 GW) | | |
| BLK-10 backstop | 2,414.8 MW gas_ct (2025) | **0** | | |
| `add.by_tech.gas_ct` | 4.415 | **1.472** | 1.355 | **FAIL → PASS** |
| `add.by_tech.gas_cc` / wind / solar / storage | 4.146 / 8.0 / 4.946 / 4.0 | identical | 3.867 / 7.2 / 18.6 / 0.744 | PASS / PASS / FAIL / FAIL both |
| `add.shares` gas_ct | 0.173 | **0.065** | 0.042 | **FAIL → PASS** |
| `add.shares` gas_cc | 0.163 | **0.184** | — | **PASS → FAIL** |
| `add.shares` wind / solar / storage | 0.314 / 0.194 / 0.157 | **0.355 / 0.219 / 0.177** | — | FAIL both |
| FC-3 band-FAIL list | 8 rows | **7 rows** | | |
| determination | HOLD | HOLD | | FC-7 CAVEAT both (no DOF ledger) |

**The additions mechanics, so the share moves are not misread.** With the 2024 term at $0 the
2024 thermal entry decisions (gas_cc 3,000 + gas_ct 1,471.6 MW, COD 2026/27) do not fire; they
re-fire in 2025 at the $230 term (COD 2027/28). The scorer's decision basis counts both, so
`by_tech.gas_cc` is identical and `by_tech.gas_ct` loses exactly the backstop's 2,414.8 MW plus
the 528 MW of 2025 gas_ct the backstop's short ledger had also drawn. Every share is a ratio
of a total that just lost 2.9 GW, so wind / solar / storage / gas_cc shares rise by arithmetic;
their `by_tech` MW did not move. `add.shares.gas_cc` crossing its band is that arithmetic.

---

## 4. Rider (d) — NEISO leg 7, `neiso-t1h-d45r-datesoff`, graded against D45-R PREDECL §4.2 P16 / P17

Run exactly as declared (owner ruling Q36): L5's recipe + `--no-fossil-announced-exits`, key
`5925e67c572a910f` = `neiso-t1h-d37-control`'s by construction (the explicit `False` collapses
onto the pre-flip key; a fresh out-dir, never a served bundle). Registered suffixed; the
d37-control record untouched.

| row | d37-control (2026-09-02 HEAD, lever OFF, dates OFF) | **L7** (this HEAD, same config) | L5 (`neiso-t1h`, dates ON, lever OFF) | actual |
|---|---:|---:|---:|---:|
| `retire.total_gw` | 7.566 (+51.4 %) | **7.566 (+51.4 %)** | 6.763 (+35.3 %) | 4.997 |
| coal economic | 0.791 | **0.791** | 0.534 (+0.129 announced) | 0.846 |
| gas_cc | 5.335 (econ 3,978 + confirmed 650 + derate 707) | **identical** | 4.107 (econ 2,632; announced 15 + derate 873; confirmed 196 + 391) | 1.884 |
| gas_st / gas_ct / oil | 1.438 / 0.0 / 0.0 | **identical** | 1.438 / 0.006 / 0.547 (announced) | 0.480 / 0.319 / 1.208 |
| recall ≥300 MW (plant) | 4/6 (0.667) | **4/6 (0.667)** | 4/6 (0.833) | |
| `false_retire` | 4.410 (58.3 %) | **4.410 (58.3 %)** | 3.182 (47.0 %) | |
| LOYO recall / false | 4/6 · 0/4 · 3/4; 4.41 / 1.47 / 4.404 | **identical** | 4/6 · 1/4 · 3/4; 2.85 / 1.61 / 3.50 | |
| additions wind / solar / gas_cc / gas_ct / storage | 2.0 / 2.056 / 2.0 / 0.5 / 0.0 | **identical** | identical | |
| positions 2023 / 2024 / 2025 | (not recorded — pre-D45 ledger) | **1.2555 / 1.2399 / 1.0155** | 1.2082 / 1.1790 / 1.0199 | FCA 14/15/16 ≈ 1.03–1.06 |
| determination | HOLD | HOLD | HOLD | |

**P16 — HIT to the decimal.** Every score row, every window channel and every LOYO fold
reproduce the d37-control, so the 13 `src/` commits between the two HEADs are measured inert
for a NEISO T1-H solve, and the L5-vs-d37-control reading D45-R made is the same-HEAD one-field
pair L5 − L7. What L7 adds is the position observability the older ledger lacks.

**P17 — the re-routing sign HOLDS, the counter-example limbs do NOT.** L5 − L7: oil 0.0 →
0.547 (announced; predicted 0.5–0.7 ✓), gas_cc economic 3,978 → 2,632 MW (DOWN ✓), total DOWN
7.566 → 6.763 ✓. But coal economic 0.791 → **0.534, not 0.0** (the falsifier "> 0.3 GW" fired);
recall 4/6 → **4/6** (plant-grain 0.667 → 0.833, UP), `false_retire` 4.410 → **3.182** (DOWN),
where P17 predicted recall 4/6 → 3/6 and false-retire rising with the flip. **At the shipped
lever the dates flip improves or holds every gated retirement row.** The recall loss D46
measured (4/6 → 3/6) belongs to the lever-ARMED pair (`neiso-t1h-pre-d46` vs D46's armed leg);
part of D46's coal-to-zero was the armed lever's higher bar, exactly as the D45-R finding's
NEISO shard note already suspected. **Reported to the owner as a finding, never a
recommendation: Q30's global default has no NEISO-side counter-example at the shipped
posture.** Nothing arms or disarms.

---

## 5. The pre-declaration, graded at full magnitude

| # | pre-declared | measured | grade |
|---|---|---|---|
| P1 | combined 0.885–0.900 (c. 0.8934); per-year 0.875–0.882 / 0.905–0.912; D31 reproduced within 0.1 MW | 0.893436; 0.87842 / 0.90884; D31 reproduced to 0.0 MW | **HIT** (the derive equals the disclosed hand arithmetic; STOP band not touched) |
| P2 | positions 1.070–1.085 / 1.015–1.024 / 0.965–0.995 | 1.0777 / 1.0194 / 0.9875 | **HIT ×3** (2023 and 2024 on the central value to 3 d.p.) |
| P3 | terms $0 / $0 / $200–390; NOT D49's $91–110 | $0 / $0 / $229.9 | **HIT ×3** |
| P4 | 2024 `pipeline_events` non-empty, ~70–80 GW failing, capped or admitted; 2025 no failures | 995 rows / 79.7 GW, all capped; 2025 none | **HIT** |
| P5 | 2022 admits 1.5–5.5 GW coal (c. 3.0), executed 2024; `retire.total_gw` 11.3–15.3; coal 9.4–13.4; other fuels identical; `false_retire` 0; recall 16–17/19; new-MW precision 5–25 %; all-MW precision 75–90 % | admits **0.477 GW** coal, executed 2024; total **10.276**; coal **8.355**; other fuels identical; 0.0; 16/19; new-MW precision **1.1 %**; all-MW **94.0 %** | direction HIT (coal-only, 2024-executed, non-coal untouched, false_retire 0, recall held); **MAGNITUDE MISS ×4** — the release is one sixth of the low edge, so total / coal / both precisions land outside their bands (the falsifier "admits 0" did not fire). The miss is the admission counterfactual's headroom (§3.2), which I bracketed from the realized 2024 requirement instead of the cap's own projected one |
| P6 | 2024 thermal entry decisions shrink or vanish; backstop 0.9–2.5 GW; `add.by_tech.gas_ct` 2.9–4.5 FAIL; wind / solar / gas_cc / storage rows unchanged to the decimal | 2024 decisions vanish (re-fire 2025); backstop **0**; gas_ct **1.472 PASS**; `by_tech` wind / solar / gas_cc / storage identical; **every SHARE row moved**, `add.shares.gas_cc` PASS → FAIL | first limb HIT; backstop **MISS** (the 2025 storage entry closes the residual gap before the backstop is tested — a mechanism I did not trace); gas_ct **MISS in the good direction** (PASS); `by_tech` HIT; shares **MISS** — I wrote "scored rows unchanged" without tracing that a share is a ratio of a total the backstop was part of |
| P7 | LOYO recall ≥ 2/3; false folds 0.0; HOLD; FC-7 CAVEAT; no other key moves | 2/3 (9/16 · 14/15 · 15/18); 0.0; HOLD; CAVEAT; only the suffixed key inserted | **HIT** |
| P8 | 20–30 min, ≤ 10.5 GB, four solve years, parity held | 18.9 min (below the band); RSS not instrumented (~7 GB observed); parity held | HIT on years / parity; wall below band; RSS unmeasured |
| keys | `b538d37b36a88247` / `5925e67c572a910f` realized | both matched; no collision | **HIT** |
| P16 / P17 | as D45-R §4.2 wrote them | §4 | P16 HIT to the decimal; P17 sign HIT, counter-example limbs MISS (coal 0.534 not 0.0; recall held; false-retire fell) |
| STOP / kills | K-a…K-g | none fired | — |

**Tally:** every structural and directional prediction hit — the identity's positions to three
decimals, the cliff, the regime flip, the fuel composition, the recall, the LOYO — and the
magnitude predictions on the two things the position DOES downstream (how much the admission
cap releases; what the backstop and the shares do) missed, both because I reasoned about a
mechanism's aggregate without tracing its own arithmetic (the cap's projected horizon; the
storage entry ahead of the backstop; the shares' denominator). The D49 §2.6 priors this lane
was asked to test against: the ratio ~0.88 / 0.91 — HIT; "the 2024 position near 1.03" —
1.019, not 1.03, for the reason the pre-declaration gave (the model's fleet is 1.5 pts short
of the market's because it under-builds); "2025 ≈ $91–110" — $230, the D49 figure having been
evaluated at the market's position rather than the model's.

---

## 6. The records rider (a)–(c), (e) — done, zero solves

- **(a) Provenance-only stubs (D47 §6 item 2).** `ercot-t1f-pre-d46` and `caiso-t1f-pre-d46`
  carry a dated note in `ff-verdicts.json` and the ERCOT / CAISO board blocks gain a
  `t1f_provenance` field: their records have NO resolved cache key (a prose `cache_epoch`,
  `run_id` null, scoring sha `8ba592814d92`), so no delta may be read against them in either
  direction (D47 §2: un-diffable, not weakly attributable). Retained as the FFR-3A-2 vintage's
  historical record only. Determinations untouched.
- **(b) NEISO `golden` → GOLDEN-3 (D47 §6 item 4).** The board field now describes
  `neiso-2026-2050-t3-golden3-bau` (`67678e58b2d0526c`, D46; FC-7 PASS via D47's
  pre-declared attestation, `scored_at_sha 71dd390ed56f`; HOLD; the CCS wave 83 → 60 rows,
  2028–2031 only) with the GOLDEN-2 text preserved verbatim beneath it in a
  `[PRIOR GOLDEN FIELD PRESERVED VERBATIM (GOLDEN-2): …]` block — the D37 / D45-R
  `t1h_provenance` precedent.
- **(c) D49 §5 item 5 — oil is not screened after 2022.** Appended to the MISO shard's
  `economic_retirement_screen` cell: 549 oil rows fail the 2022 bridge screen, then 0 (D46) /
  10 (control) oil rows appear in any later screen while 3.51 GW of oil stays in
  `fleet_by_fuel_before`; "oil passes" in 2023–2025 is an absence of candidates, not a margin
  reading. Unexplained at D49/D51; routed (§8).
- **(e) Forecast rubric v1.0 → v1.1 (owner ruling Q37).** §5 gains the second
  attestation-authorship limb — *a follow-up lane may author a forecast attestation iff it is
  PRE-DECLARED before authoring, moves only the attestation row, and re-scores artifact-only*
  — with the sequence-proof, byte-identity and preserve-then-overwrite conditions spelled out,
  citing `FINDING-capx-d47-golden3-attestation-2026-09-04.md` §1 as the model case and capx
  ledger §3 Q37 as the signature; the §0 artifact table's author column, the §9 version
  history and `scripts/forecast_verdict.py::RUBRIC_VERSION` ("1.0" → "1.1") move with it;
  CHANGELOG entry. Text only — no threshold, no re-score; every committed
  `rubric_version: "1.0"` record stands as scored. `register_forecast_run.py --reindex`
  assembles the namespace clean; `tests/scoring` green (344 passed).
- A top-level `d51_records_rider` block on the board records all of the above.

**Gate (a).** On the session's original base (`a35c9f9`) `scripts/check_gate_a_provenance.py`
FAILED before any edit of this lane — MISO's `gate.a_keeper_marker` cited the superseded
keeper miso-202 after the owner's miso-210 promotion. The re-key is the director desk's
standing duty (Q34), so this lane did not touch the row; the desk re-keyed it on `main` during
the session and the check reads OK at the rebased HEAD. Recorded, not routed.

---

## 7. Arming recommendation — on the pre-stated condition (PREDECL §5)

| limb | condition | reading |
|---|---|---|
| (a) | derive value in [0.85, 0.93]; D31 reproduction exact | 0.8934; exact — **MET** |
| (b) | 2024 position within ±2.5 pts of the market's offered 1.034 | 1.0194, 1.5 pts short — **MET** (the D49 object, 5.8 pts, closed to the tolerance D31 closed the original defect to) |
| (c) | no scored FC-3 row outside the retirement block and `add.by_tech.gas_ct` / `add.shares.gas_ct` moves | `add.shares.gas_cc` PASS → FAIL, and the wind / solar / storage share values moved — **NOT MET by the letter** |
| (d) | LOYO recall holds ≥ 2/3 | 9/16 · 14/15 · 15/18 — **MET** |

The pre-stated rule reads: (c) fails → HOLD-and-route, on the rationale that "a second object
is moving the position". The measured cause of the (c) miss is not a second object: the
position itself, longer by the identity, stops the BLK-10 backstop, 2.9 GW of gas_ct leaves the
additions total, and every share — a ratio of that total — moves by arithmetic while every
`by_tech` MW outside gas_ct is identical to the decimal. The limb's letter and its rationale
therefore disagree, because I wrote the letter without tracing the shares' denominator; that
is a pre-declaration defect recorded against myself, not a reason to re-narrate. **The lane
reports both: by the letter of §5, HOLD-and-route; on the substance §5 was written to test,
the double-netting is closed, nothing else moves the position, the ratio is an identity with
zero DOF, and the rule-14 sign holds (exits harder, not easier, in 2024; the cohort back in the
floor's hands). The owner decides; the lane does not override its own pre-registration.** If
the owner arms: `adequacy_accounting_ratio_dated_net=True` for MISO via
`default_scenario_overrides` (rule 25), the bare `miso-t1h` re-solved on the live-vintage
convention with the D46 record preserved at `miso-t1h-pre-d51`, and the same field carried
into the MISO t1f leg (whose I7 FAIL 2026–2029 D45-R measured on the 0.8546 ledger). If the
owner declines, the D31 value keeps resolving and the D49 double-netting stands as a
documented, measured understatement of the MISO position of ~4.5 % of internal supply.

---

## 8. Routed to the director

1. **The arming decision (§7)** — a letter-vs-substance divergence in the lane's own
   pre-registration, decided by the owner, never by the lane.
2. **The admission cap's horizon headroom** (§3.2) — the object that decides what a longer
   position releases: the counterfactual's projected peak, the un-credited entry between
   decision and execution, and the pending-row netting together left ~0.4 GW accredited of
   headroom where the realized 2024 requirement implied 1.3–4.2. Not a defect claim (the cap's
   own docstring names two of the three as documented limits) — a measurement handed to the
   D32 R2/R3 lane, which owns the floor-capped regime the cohort now sits in again.
3. **The backstop is tested after the storage entry** (§3.3, P6 MISS) — recorded so the next
   lane pricing a BLK-10 response does not bracket it from the entering position alone.
4. **The 2023 and 2025 ledger positions do not reconstruct from their entering fleets on the
   D31 construction** (§1.4: +3,498 / −7,455 MW raw); 2024 reconstructs exactly. Not this
   lane's question; a position-observability lane should say what the runner's `fleet` and
   pools are at the point of computation in a bridge-adjacent and a final year.
5. **NEISO (§4):** Q30's default has no NEISO-side counter-example at the shipped lever; the
   D46 recall loss is the armed-lever pair's. A finding for the owner's file on Q28/Q30, not a
   recommendation.
6. **D49 §5 item 5, oil unscreened after 2022** — now on the MISO matrix cell (§6c); still
   unexplained.

---

## 9. Governance attestation

- **Rule 12.** Two invocations, never concurrent; years sequential inside each.
- **Rule 13 / 14 / 21 / 23.** The ratio's operands are the committed PRA rows and the committed
  D27 / D46 ledgers; the moved term is a fleet-posture change (D44), never a residual; no
  parameter was sized by any score; the cleared PRA quantities enter nothing. The derive
  script and its reconciliation test freeze the value to the data.
- **Rule 22.** Solve years {2021, 2023, 2024, 2025}, 2022 bridged and never scored; scoring and
  LOYO bounded to 2023–2025; the holdout freeze active and asserted by both run banners;
  nothing scored against H1-2026; no marker touched.
- **Rule 24 / 28.** One `ScenarioConfig` field, registered at its default in the same commit;
  matrix base row + six shard cells in the mechanism commit; the MISO cells re-stamped with the
  measured verdict (`fc: O`); the NEISO `fossil_announced_exits` cell carries leg 7;
  `check_mechanism_matrix.py --base origin/main` and `check_cache_key_registration.py` clean
  before and after the rebase.
- **Rule 25.** MISO's ratio never transfers: the dated-net registry holds MISO alone and the
  other five shards carry an ISO-exclusive `·` cell; NEISO's shard is edited only for its own
  leg-7 measurement.
- **Rule 27.** Every ≥300-line file was edited locally (Edit / format-preserving scripts) and
  pushed as on-disk bytes over `git push`; after every push, and again after the rebased
  force-with-lease push, each such file's remote blob was fetched and compared to the local
  hash — all OK (`scenarios.py`, `capacity_market.py`, `constants.py`, `retirements.py`,
  `adequacy.py`, `run_capacity_hindcast.py`, `register_forecast_run.py`, `forecast_verdict.py`,
  `ff-verdicts.json`, `program-status.json`, the matrix base and shards, the rubric,
  `CHANGELOG.md`, `parameter-citations.md`, the two `run_config.json`s). `ff-verdicts.json` was
  edited by insert-only splices (its post-D50 bytes no longer round-trip a JSON dump, so a
  re-dump would have rewritten every escape).
- **Rule 15 / registration.** Both bundles' slim sets (meta, `run_config.json`,
  `forecast_verdict.json`, `score.json`, the evolution ledgers under their `.gitignore`
  carve-outs, the diagnostics `.npz`), canonical sidecars, hindcast reports, `VERDICT_MAP`
  rows and the two suffixed `ff-verdicts.json` keys are committed in this chain; the generated
  forecast namespace is left to the Pages deploy.
- **Edit surface.** Verdict keys: two inserted, none modified beyond the rider's two stub
  notes; the bare `miso-t1h` / `neiso-t1h` untouched; no keeper, shard verdict letter beyond
  the new row's own cells, marker, freeze file or backcast file touched; no default flipped;
  no parameter value beyond the new registry entry.
- **Tests.** 1,081 config + regression (`test_soundness` excluded: its known clean-partition
  dependency, mid-regeneration), 507 capacity / override / identity / matrix, 344 + 347 scoring,
  61 harness provenance / posture — all green at the pre-rebase and rebased HEADs.
- **Owner message mid-session (2026-09-04, "is this a keeper candidate — if so promote"):**
  answered in-session — this is a forecast-lane mechanism, not a backcast keeper; nothing was
  promoted or armed; the recommendation is §7.

## 10. Reproduction

```
uv run python scripts/regenerate_clean.py
uv run python scripts/data/derive_miso_adequacy_accounting_ratio.py
uv run python scripts/run_capacity_hindcast.py --iso NEISO --start-year 2021 --end-year 2025 --vintage 2020 --fuel-variant realized --entry-screen-diagnostics --no-fossil-announced-exits --out-dir results/hindcast/neiso-2021-2025-realized-t1h-d45r-datesoff
uv run python scripts/run_capacity_hindcast.py --iso MISO --start-year 2021 --end-year 2025 --vintage 2020 --fuel-variant realized --entry-screen-diagnostics --adequacy-accounting-ratio-dated-net --out-dir results/hindcast/miso-2021-2025-realized-t1h-d51-ratio
# per bundle: score_capacity_hindcast.py --bundle <dir>; --flip-gate-extras; forecast_verdict.py --tier t1h --hindcast-score <cache>/score.json --run-config <dir>/run_config.json --json-out <dir>/forecast_verdict.json; register_forecast_run.py --bundle <dir>
uv run python scripts/probes/_capxd42_plant_grain.py results/hindcast/miso-2021-2025-realized-t1h-d51-ratio
```
