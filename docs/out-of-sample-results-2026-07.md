# Out-of-sample results (2026-07) — S4 / audit D-6 + D-8

**Scope of this session.** The assigned task (legitimacy audit §5.3, §7 D-6/D-8;
`docs/legitimacy-scrub-prompts-2026-07.md` S4 item 2–3) was to (1) score the
designated untrained holdouts — **2022** and **H1-2026** — once each with the
FROZEN current keeper configs, and (2) run the D-8 frozen-coefficient stability
checks. During the session the owner instructed: *"Don't run any 2022 or 2026
model runs. These are holdout years to avoid overtraining."* Per that
instruction **no holdout LP solve was run** (D-6 steps 1–2 not executed). What
this document delivers:

- **D-6 (holdout scoring): NOT RUN.** Both because of the owner's instruction
  and — established independently below — because the **scoring-target and
  fleet-overlay data for 2022 / H1-2026 are not in the repository**, so the
  holdout is un-scorable from repo data today regardless of the run decision.
- **D-8 (frozen-coefficient stability): RUN, in full.** Uses only the 2023–2025
  in-sample CAMPD / EIA-930 data the coefficients were fitted on — no holdout
  year is touched. This is the one out-of-sample-*discipline* number this
  session can honestly produce.

> **Methodological note (recorded, not a challenge to the instruction).** The
> D-6 protocol — solve a frozen config on a held-out year *once*, score once,
> and never re-tune against the result — is the standard technique for
> *measuring* overfit without causing it; overtraining would arise only if the
> configs were subsequently tuned to the holdout, which the protocol forbids.
> "Score the holdout once" and "avoid overtraining" are not in conflict under
> that discipline. The instruction is respected here in full; this note simply
> records why the D-6 table is absent so a future session can re-open it if the
> owner chooses.

---

## 1. Holdout data-coverage assessment (why D-6 is un-scorable from repo data)

A holdout score needs three things for the target year: **driver inputs**
(demand, fuel), **fleet + overlay inputs** (CAMPD unit-level binning, outages,
delivered fuel), and — decisively — **bench actuals to score against**
(EIA-930 fuel-mix, CAMPD generation). Coverage of the repo's `data/raw/` for the
two holdout windows:

| Input | Datatype / path | 2022 | H1-2026 | Role |
|---|---|:--:|:--:|---|
| Demand (hourly) | `eia-930-hourly/*.parquet` | ✅ 2015–2026 | ✅ | driver |
| Demand (ERCOT native, zonal) | `zone-specific-demand/…`, `ercot/ACTUALSYSLOAD*` | ✅ | ✅ | driver |
| Gas — Henry Hub | `gas-prices/henry_hub_{daily,monthly}.csv` | ✅ 1997–2026 | ✅ | driver |
| Gas — delivered/citygate (EIA-923) | `gas-prices/eia_citygate_*`, zonal hub | ❌ 2023–2025 only | ❌ | driver (backcast) |
| **Fleet — CAMPD unit-level (binning)** | `campd-unit-level/{ST}_{YEAR}.parquet` | ❌ **2023–2025 only** | ❌ | fleet build |
| Outages (CAMPD >10-day overlay) | `ercot-outages.csv`, `campd-*-outages*.csv` | ❌ 2023–2025 only | ❌ | overlay (backcast) |
| **Bench — EIA-930 fuel-mix actuals** | `{ISO}_fueltype.parquet`, `eia-930/*BALANCE*` | ❌ **2023–2025 only** | ❌ | **scoring target** |
| **Bench — CAMPD generation actuals** | `campd-unit-level/*` | ❌ **2023–2025 only** | ❌ | **scoring target** |

**Conclusion.** Only the *driver* series (demand, Henry Hub) reach back to 2022
and forward to 2026. Every **scoring target** (EIA-930 fuel-mix and CAMPD
generation) and every **fleet/overlay** input (CAMPD unit-level binning,
delivered gas, outage windows) is present **only for 2023–2025**. A 2022 or
H1-2026 backcast could therefore be *driven* but **not scored** — there is no
in-repo actuals series to compute the C1/C2/C3/C4 fail counts against. This is a
data-intake blocker that would have to be cleared (intake 2022 + 2026-H1
EIA-930 fuel-mix, CAMPD unit-level, and delivered-gas via the `data-intake`
skill) **before** any D-6 holdout score is meaningful, independent of the
solve-or-not decision. No partial-coverage ISO exists: the gap is uniform
across all six ISOs because it is in the shared datatypes.

---

## 2. D-8 — frozen-coefficient stability (RUN)

**Design.** For each *fitted-to-the-scored-years* coefficient family, refit on a
**training subset** of the calibration years and measure (a) how far the
coefficients move vs the all-years fit the keeper ships, and (b) how well the
training fit predicts the held-out calibration year. This exercises the audit's
"regression floors absorbing residual" concern using **only 2023–2025** data —
no holdout year. Harness: `scripts/d8_coefficient_stability.py`
(bundle: `results/calibration/d8-coefficient-stability/`); it imports and reuses
each mechanism's **own frozen derive/probe fit code**, so the numbers are on the
identical estimand the keeper uses. Validation of faithfulness: the ERCOT
all-years drag fit reproduces the shipped `ScenarioConfig` default exactly
(slope 0.00703, cap 0.47).

### 2A. Net-load drag hinge — leave-2025-out

Fit the evening-ramp `frac = clip(slope·netGW + intercept, 0, cap)` floor on
**2023–24 only**, then predict the 2025 floor energy and compare to the
all-years fit. `pred2025 floor` is the drag's *minimum* the LP exceeds
economically (NOT a match to total CT energy — the measured column is context,
not an error bar).

| ISO | slope (train→full) | drift | zero-cross GW (train→full) | cap (train→full) | pred-2025 floor TWh (train→full) | floor drift | measured 2025 CT TWh |
|---|---|:--:|---|---|---|:--:|:--:|
| **ERCOT** | 0.00693 → 0.00703 | **−1.5%** | 20.9 → 20.3 | 0.468 → 0.47 | 2.84 → 2.97 | **−4.2%** | 7.0 |
| **PJM** | 0.00930 → 0.01108 | **−16.1%** | 88.3 → 90.1 | 0.416 → 0.46 | 6.64 → 7.16 | **−7.2%** | 22.3 |
| **CAISO** | 0.01064 → 0.00901 | **+18.1%** | 11.3 → 12.5 | 0.411 → 0.356 | 1.59 → 1.20 | **+32.2%** | 1.36 |

- **ERCOT** — the template mechanism — is **stable**: slope drift −1.5%,
  zero-crossing moves 0.6 GW, floor-energy prediction within 4.2%. Leaving 2025
  out barely moves the ERCOT drag. This is the one coefficient family with clean
  cross-year identification.
- **PJM** slope drifts 16% and the cap moves 0.42→0.46; the applied floor energy
  still predicts within 7%, so the *level* is more robust than the slope. The
  hinge is moderately, not well, identified across years.
- **CAISO** is the least stable: slope drifts 18% and, because the CAISO floor
  is nearly the entire measured CT energy (floor 1.2 vs measured 1.36 TWh — a
  much higher forced share than ERCOT/PJM, where the floor is a fraction of CT),
  the 32% floor-energy prediction drift lands directly on dispatched volume. The
  CAISO CT floor is close to fitting the CT class outright, and its year-to-year
  identification is weak.

### 2B. Temperature-CF reliability floor — leave-2025-out

Recompute per-(zone,class,limb) `floor_pct = commit_frac · min_stable_pct` on
2023–24 CAMPD, and score the 2025-only value. Only the **hot (tmax)** limbs
cleared the enable gate anywhere; all reported limbs below are ones the train or
hold fit would enable.

**Headline: every limb's enable flag flips True→False from 2023–24 to 2025-only,
but this is dominated by a sample-size artifact, not coefficient collapse.** The
enable gate requires `n ≥ 30` flagged (design-cooling) days; a *single* year
supplies only ~3–23 such days per zone×class, so 2025-alone fails `N_MIN`
mechanically. The shipped coefficient uses all three years pooled and clears the
gate. The honest signal is therefore the **`floor_pct` drift** and the **ρ
stability**, not the flip:

| ISO | zone / class | floor_pct (train→2025) | drift | ρ (train→2025) | flag |
|---|---|---|:--:|---|---|
| ERCOT | Houston / CT_PEAKER | 0.339 → 0.298 | **+13.5%** | 0.47 → 0.87 | large drift |
| ERCOT | Houston / CC_REGULAR | 0.512 → 0.520 | −1.6% | 0.39 → 0.87 | stable |
| ERCOT | North / CT_PEAKER | 0.105 → 0.105 | 0.0% | 0.49 → 0.50 | stable |
| PJM | EMAAC / ST_GAS | 0.103 → 0.076 | **+35.8%** | 0.37 → 0.81 | large drift |
| PJM | SWMAAC / CT_PEAKER | 0.320 → 0.379 | **−15.6%** | 0.31 → 0.25 | large drift; ρ weak |
| PJM | ATSI / CT_PEAKER | 0.307 → 0.328 | −6.6% | 0.37 → 0.18 | ρ decays |
| PJM | ComEd / COAL | 0.389 → 0.375 | +3.5% | 0.49 → 0.18 | ρ decays |
| PJM | **ComEd / CC_REGULAR** | 0.490 → 0.520 | −5.7% | **0.35 → −0.19** | **ρ SIGN FLIP** |
| PJM | ATSI / CC_REGULAR | 0.516 → 0.520 | −0.9% | 0.41 → 0.05 | ρ collapses |
| PJM | West_APS / COAL | 0.354 → 0.357 | −0.9% | 0.39 → 0.55 | stable |
| PJM | Central_PA / ST_GAS | 0.117 → 0.115 | +1.8% | 0.39 → 0.50 | stable |
| CAISO | **SP15 / ST_GAS** | 0.079 → 0.058 | **+35.7%** | **0.41 → −0.16** | **ρ SIGN FLIP** |
| CAISO | **SP15 / CC_REGULAR** | 0.330 → 0.296 | +11.6% | **0.69 → −0.10** | **ρ SIGN FLIP** |

- **Coefficient level is mostly stable** (most `floor_pct` drifts < 6%), but
  **five limbs drift > 11%** (ERCOT Houston CT +13.5%, PJM EMAAC ST_GAS +35.8%,
  PJM SWMAAC CT −15.6%, CAISO SP15 ST_GAS +35.7%, CAISO SP15 CC_REGULAR +11.6%)
  — beyond a defensible physical-uncertainty band.
- **The identification is fragile**: several PJM limbs' Spearman ρ decays toward
  zero out-of-training, and **three limbs flip ρ sign** — PJM ComEd CC_REGULAR
  (+0.35 → −0.19) and **both** CAISO SP15 limbs (ST_GAS +0.41 → −0.16;
  CC_REGULAR +0.69 → −0.10) — the exact "sign flip = unidentified" signature D-8
  is designed to catch. For these limbs the temperature→commitment relationship
  reverses out-of-training, so it is not physically identified. CAISO is the
  worst-affected ISO (both its scored limbs sign-flip).

### 2C. Coal passthrough sigmoid — leave-2024-out identifiability

The `COAL_SIGMOID_DEFAULTS` params (`floor`, `ceil`, `gas_mid`, `gas_slope`) are
**hand-tuned** to a per-month coal-vs-gas breakeven across 2023–25 — there is no
automated objective to mechanically refit, so a literal "refit-without-2024" is
not defined. What *is* rigorously computable is **identifiability**: which years'
monthly delivered-gas actually sample each end of the logistic. A sigmoid's
cheap-gas asymptote (`floor`) is identified only by months **below** `gas_mid`;
its dear-gas asymptote (`ceil`) only by months **above**.

Monthly delivered-gas ($/MMBtu) coverage vs each ISO's `gas_mid`:

| ISO (`gas_mid`) | year | gas min–max (mean) | months below / above `gas_mid` |
|---|:--:|---|:--:|
| **ERCOT** (2.85) | 2023 | 1.84–2.41 (2.04) | **12 / 0** |
| | 2024 | 1.52–1.99 (1.69) | **12 / 0** |
| | 2025 | 2.72–3.56 (3.02) | 4 / 8 |
| **PJM** (3.40) | 2023 | 2.89–3.79 (3.21) | 9 / 3 |
| | 2024 | 2.57–3.37 (2.86) | **12 / 0** |
| | 2025 | 3.77–4.94 (4.19) | **0 / 12** |

- The sigmoid's two asymptotes are anchored by **disjoint single years**: the
  **cheap-gas `floor` by the cheapest year (2024)** and the **dear-gas
  `ceil`/`gas_mid` by 2025** (the only above-`gas_mid` year for both ISOs;
  wholly-above for PJM). 2023 is a redundant near-`gas_mid` middle.
- **Leave-2024-out is the binding test.** For PJM, removing 2024 removes the
  deepest cheap-gas observations; 2023 still has 9 below-mid months but at a
  ~$0.35/MMBtu-higher floor, so the fitted `floor` would ride up (less
  cheap-gas discount) with no data to contradict it. For ERCOT, 2023 is also
  fully below `gas_mid`, so the `floor` survives leave-2024-out — but note
  **`gas_mid` = 2.85 sits above *every* month of 2023 and 2024**: the
  midpoint/`ceil` are identified by **2025 alone**. Either way, each of the
  four sigmoid parameters is effectively pinned by a **single** gas regime —
  the family is **weakly identified / borderline unidentified** on three years
  of three distinct gas regimes, exactly the audit's concern.

---

## 3. Per-ISO verdict on forecast-skill evidence

**ERCOT.** *Best-supported of the three.* The net-load drag — ERCOT's headline
structural mechanism and the template copied to other ISOs — is genuinely
cross-year stable (slope −1.5%, floor-energy −4.2% out-of-training), which is
real evidence the drag reflects a persistent net-load→commitment relationship
rather than a 2025-fitted residual. The temperature-CF floors are mostly stable
at the level, with one > 13% limb drift. But the forecast-skill *claim* remains
**unproven, not disproven**: the D-6 out-of-sample dispatch score that would test
it cannot be produced — the 2022/2026 bench actuals are absent from the repo, and
per instruction no solve was run. The coal sigmoid's `gas_mid`/`ceil` ride on
2025 alone.

**PJM.** *Weaker identification.* The drag hinge slope drifts 16% leave-2025-out
(level more robust, 7%), and the temperature-CF floors show the clearest
instability in the study — multiple ρ decays and a **sign flip** (ComEd
CC_REGULAR) that flags an unidentified limb, plus a 36% floor drift on EMAAC
ST_GAS. The coal `floor` is anchored on 2024 and would drift up if 2024 were
removed. On the D-8 evidence, several PJM reliability-floor coefficients are not
yet at "physically identified"; treat PJM forecast skill as **asserted, largely
unverified**.

**CAISO.** *Least stable, highest forced-share.* The CT drag slope drifts 18%
and — because the CAISO floor is ~90% of the measured CT energy (vs a small
fraction for ERCOT/PJM) — the 32% out-of-training floor-energy drift lands
directly on dispatched volume. A floor that nearly equals the class it floors,
and that moves this much year-to-year, is close to fitting the CT class rather
than deriving it. It is also the worst ISO on the temperature-CF limbs: **both**
scored SP15 limbs (ST_GAS, CC_REGULAR) sign-flip ρ out-of-training and one
drifts 36%. This is the weakest forecast-skill evidence of the three and aligns
with the audit's CAISO CT-forcing finding (§5.4, L-rows). No CAISO coal sigmoid
exists (no coal fleet), so 2C is N/A.

**MISO / NYISO / NEISO.** Not evaluated this session (D-8 focused on the three
ISOs whose drag mechanisms the audit names). Data to extend D-8 to them is
present (CAMPD unit-level + EIA-930 hourly + zone temps for 2023–25); the harness
is ISO-generic for the temperature-CF and coal-coverage parts and could be
pointed at them in a follow-up.

---

## 4. Dashboard registration

D-6 produced **no backcast run/bundle** (no solve was run), so there is nothing
to register on the run-explorer dashboard as a holdout probe. The D-8 output is a
coefficient-stability analysis, not a scored `dispatch/<year>.parquet` bundle;
it lives at `results/calibration/d8-coefficient-stability/summary.json` and is
reported here. If the owner later authorizes the D-6 solves (after the 2022/2026
bench-data intake), those runs would be registered as `probe` entries per the
usual `calibration-report` flow.

## 5. Open follow-ups (root-cause items, not fixes)

1. **Intake 2022 + H1-2026 bench + fleet data** (EIA-930 fuel-mix, CAMPD
   unit-level, delivered gas) so D-6 becomes scorable. Un-scorable today.
2. **Temperature limbs with ρ sign flips — PJM ComEd CC_REGULAR and both CAISO
   SP15 limbs (ST_GAS, CC_REGULAR).** Unidentified out-of-training; re-examine
   whether these tmax limbs should ship for those zone/classes at all.
3. **CAISO CT drag forced-share.** Floor ≈ measured CT energy + 18% slope drift
   → the floor is fitting the class. Cross-reference the audit's D-2 forced-
   energy attribution and L-row scrub for CAISO CT.
4. **Coal sigmoid single-year-per-parameter identification.** `gas_mid`/`ceil`
   ride on 2025; `floor` on 2024. Document as literature/physically-anchored
   where possible rather than presenting as a 3-year fit.
