# PRECOMMIT — SPP PRICE FAMILY: the price miss is **LOAD-driven, not fuel-driven**, and it splits into TWO objects, not three

**Lane:** SPP PRICE-FAMILY. **Branch:** `claude/spp-price-family-calibration-de9ddj`. **DATA PROFILE: spp.**
**Pushed BEFORE any LP.** Control = the committed keeper bundle `spp42_crosswalk_B`
(`2026-09-07-spp-2-crosswalk-hydro`), rule 29(b) form 4, validated by the G-DRIFT audit in §5.

---

## 0. What phase 0 established, at zero LP

The target was "the whole price family fails". Phase 0 says it is **not one family**. It is two
objects with different causes, and one of them is not reachable by any offer-curve lever.

| | finding | evidence |
|---|---|---|
| **C3a + C3b** | ONE cause: the model's **mid-stack is ~10 % too dear, load-weighted** — it prices the bulk of hours above the measured surface and its supply curve is too shallow. | §1, §2 |
| **C3c** | A **DIFFERENT object**: SPP's >$200 hours are **not high-load hours** and carry market heat rates of 79–93× gas. No band multiplier reaches them. | §3 |
| **C1 (2024 gas split)** | **NOT reachable through this lane's authorized channel** — it is a `pct_peaking` structural-share question, which rule 1(a) forbids this channel from touching. Reported, routed, not attempted. | §4 |

**The tail is a merit-order outcome, not a shortage outcome.** Zero slack and zero dump in all
8,760 hours of 2023 and of 2024; 2025 carries **one** slack hour (89.3 MWh, the SPP-57 object the
keeper already names). `scarcity_pricing_enabled` and `scarcity_price_overlay` are both `False`
and `energy_reserve_coopt` is `False` — SPP has **no scarcity mechanism of any kind**.

---

## 1. The decomposition — SPP INVERTS the PJM result

The PJM PRICE-TAIL lane (`FINDING-pjm-price-tail-2026-09-07.md`) established the method. Run on
SPP's own committed keeper hourlies, SPP's own hourly RT LMP
(`data/raw/_validation-source/actual_lmp_hourly_SPP.parquet`, which reproduces the scorer's
42 / 59 / 68 hours >$200 exactly) and SPP's own delivered gas (EIA `N3045KS3` / `N3045OK3`,
$/Mcf ÷ 1.037), pooled over 36 months:

| statistic | **ACTUAL SPP** | MODEL | PJM 2021, for contrast |
|---|---|---|---|
| `corr(monthly price, delivered gas)` | **+0.2720** | +0.6969 | +0.9531 |
| `corr(monthly price, monthly load)` | **+0.7791** | +0.5984 | +0.2449 |
| implied market heat rate, **CV** | **0.3874** | 0.2514 | 0.082 |
| `corr(implied market HR, delivered gas)` | **−0.6012** | — | −0.0235 |

**SPP's price surface is load-driven and its market heat rate is not constant** — the opposite of
PJM on every line. So the lever that reaches SPP's price miss is the **offer stack**, not the fuel
series. That is a *result*, not an assumption, and it is what sends this lane to the offer curve
rather than to `gas_monthly_actuals` / `gas_daily_shape`.

**The measured-input question is answered too, and negatively for this lane.** SPP prices gas from
a flat annual scalar (`gas_price_override` 2.54 / 2.19 / 3.52) with `gas_monthly_actuals=False`
and `gas_daily_shape=False`, while `gas_plant_monthly_fuel_pricing=True` already supplies EIA-923
plant-monthly delivered prices. A richer gas series is a live rule-14 `[R-ACCURATE]` question and
is **left open, not closed** — but the decomposition says it cannot be the C3a/C3b cause, because
the measured price surface does **not** follow gas (+0.272) while the model's **already does**
(+0.697). The model is *more* fuel-coupled than the market it is reproducing.

---

## 2. The mechanism, named and measured

**The tranche mechanism exists in SPP and carries no price differentiation at all.** SPP's keeper
takes the shared `offer_curve_by_group` default, in which **every band of every class SPP has is
1.0** — `CC_REGULAR`, `CT_PEAKER`, `ST_GAS`, `COAL_*` all read `committed=econ_low=econ_high=
peak=1.0`. Only the three `*_INTERMEDIATE` curves carry non-neutral bands. So each plant's four
tranches are **price-identical** and the LP is indifferent among them.

The keeper's own band ledger confirms this is not a theory (`class_band_hourly_<year>.parquet`):

| class, 2023 | committed | econ_low | econ_high | **peak** |
|---|---|---|---|---|
| `CC_REGULAR` | 12.41 TWh / 8,578 h | 12.41 / 8,663 | 12.42 / 8,660 | **4.18 TWh / 8,624 h** |
| `CT_PEAKER` | 1.43 / 8,752 | 9.02 / 8,759 | 8.13 / 8,759 | **1.42 TWh / 8,759 h** |
| `COAL_PRB` | 14.10 / 8,689 | 16.70 / 8,731 | 13.65 / 8,729 | **1.27 TWh / 8,723 h** |

**A peak band that runs in 8,759 of 8,760 hours is not a peak band.** Every band runs in
essentially every hour, at its structural share — the signature of a flat curve, reproduced in
2024 and 2025.

**What that costs, measured on the load axis.** Market heat rate by system-load percentile
(SPP's own RT LMP ÷ SPP's own delivered gas; model on the identical axis):

| load pct | 0-10 | 10-25 | 25-50 | 50-75 | 75-90 | 90-95 | 95-98 | 98-99.5 | 99.5-100 |
|---|---|---|---|---|---|---|---|---|---|
| measured MHR | 6.81 | 5.53 | 5.42 | 5.64 | 7.33 | 9.49 | 10.66 | 12.14 | **13.61** |
| model MHR | 7.89 | 7.70 | 7.92 | 7.96 | 9.19 | 11.32 | 12.23 | 13.01 | **13.59** |

**Reported honestly against this lane's own first reading:** the model's stack is **not flat** on
this axis — it rises +72 % top-to-bottom against the measured +100 %, and at the very top the two
agree to 0.2 %. The earlier monthly-tercile statement (+2 % vs +37 %) was **confounded by the gas
axis** and is withdrawn as a characterisation. The correct one: **the model is too dear
everywhere below the top ~2 % of hours, worst in the middle** (25-75 pct, where over half the
hours live, +41 to +46 %), and correct at the top.

**And the mean miss is real in all three years, not just 2023.** Against the $200-capped actual —
i.e. with the scarcity object this lever cannot produce removed from the comparator — the model
reads **+16.6 % / +10.8 % / +12.5 %**, against the +14.1 / +7.4 / +7.2 % the scorer shows. The
measured tail contributes only 0.53 / 0.76 / 1.32 $/MWh (2.2 / 3.1 / 4.7 %) of the measured
load-weighted mean, so the 2024/2025 C3a "PASS" is partly the measured tail padding the actual.

---

## 3. Why C3c is a different object, and is NOT this lane's target

The 60 highest measured RT hours of each year:

| year | median measured price | median measured **market HR** | median **load percentile** | hours >$200 also in the **top 5 % of load** |
|---|---|---|---|---|
| 2023 | $234.60 | **84.10** | 43.7 | **3 of 42** |
| 2024 | $244.25 | **92.77** | 84.4 | **5 of 59** |
| 2025 | $313.35 | **79.29** | 40.3 | **3 of 68** |

System-wide median market HR is 5.3–7.1. **SPP's price spikes happen at ordinary load at market
heat rates of 80–93×.** Reaching them through band multipliers would require the entire stack to
be ~10× dearer, which would destroy every other criterion. C3c is a **scarcity/conduct** object
and belongs to **SPP-55 (VRL-based scarcity design)**, which the matrix already reserves for it.
It is an accepted ledgered caveat under rule 22's C3c standing rule and is **not** this lane's
promotion test. **This lane predicts C3c does not materially move, and will report it either way.**

---

## 4. The channel, declared

**Rule 1 `[R-STRUCT]` / rule 13 `[R-MEASURED]` AUTHORIZED PRICE-TUNING CHANNEL — `offer_curve_by_group`
band multipliers.** Every condition is met and is stated here rather than asserted:

- **(a) bands only.** `committed` / `econ_low` / `econ_high` / `peak`. **No `phys_*`. No
  `econ_low_share`. No `pct_peaking`.** Verified on the resolved config: the arm's `CT_PEAKER`
  keeps `econ_low_share=0.526, pct_peaking=7.0` and `COAL_PRB` keeps `econ_low_share=0.55`,
  unchanged from the control.
- **(b) ONE config across every scored year.** One quadruple, derived on the **pooled** 2023+2024+2025
  panel, applied to all three. No per-year value exists anywhere in this lane.
- **(c) set EX ANTE, declared here, NEVER swept against the gates.** The values are in §4.1 and the
  disclosure of how they were reached — including a superseded first attempt — is §4.2.
- **(d) merit-order adjustment across classes is INTENDED.**
- **(e) declared in the run's `authorized_price_tuning` attestation block** (C6 FAILS without it)
  and carried as a **free parameter in the DOF ledger** (rules 20/21), identification source
  *"price residual, authorized channel (rules 1/13 amendment 2026-09-05)"* — not a measured source.

**Rule 25 `[R-ISO-SCOPE]` holds absolutely.** Every number below is computed from SPP's own hourly
RT LMP and SPP's own KS/OK delivered gas. No ERCOT/PJM/MISO/CAISO/NYISO/NEISO multiplier, drag
coefficient or basis value is carried in, and the arm is passed per-run via `--offer-curve-json`,
so no generic fallback moves off 1.0.

**The measured-offer route does not exist for SPP, and that is why this is the channel.** The repo
carries `pjm-energy-offers`, `miso-energy-offers` and `caiso-public-bids`; SPP publishes **only**
reserve MCP (`data/raw/spp-or-mcp`) and no energy-offer corpus. There is no measured SPP offer
curve to prefer under rule 14.

### 4.1 THE DECLARED VALUES — one config, all years

```json
{"committed": 0.845, "econ_low": 0.794, "econ_high": 1.018, "peak": 1.118}
```

applied to **every** class SPP dispatches: `CC_REGULAR, CC_CHP, CT_PEAKER, CT_CHP, ST_GAS, ST_CHP,
COAL_PRB, COAL_LIGNITE, COAL_BIT, COAL_WC, COAL`.

**Derivation (one rule, stated before it was run).** For each band's stack position — `committed`
0-25th, `econ_low` 25-75th, `econ_high` 75-95th, `peak` 95-100th percentile of system load — the
multiplier is

> `median-free, LOAD-WEIGHTED mean measured market heat rate (RT LMP capped at $200) ÷ load-weighted mean model market heat rate`, pooled over 2023+2024+2025.

Two methodological choices, both made on stated grounds and neither on an outcome:
1. **Load-weighted, not median** — because the criterion these bands price into (C3a) is a
   *load-weighted* mean, so the derivation must sit on the same statistic.
2. **Capped at $200** — because the >$200 surface is a **different mechanism** (§3, SPP-55).
   Crediting the offer curve with scarcity rent it provably cannot generate would double-count.

| band | pctile | hrs | measured MHR (lw, ≤$200) | model MHR (lw) | **ratio** |
|---|---|---|---|---|---|
| `committed` | 0-25 | 6,556 | 6.6842 | 7.9133 | **0.8447** |
| `econ_low` | 25-75 | 13,135 | 6.3842 | 8.0364 | **0.7944** |
| `econ_high` | 75-95 | 5,251 | 10.0604 | 9.8778 | **1.0185** |
| `peak` | 95-100 | 1,314 | 14.0776 | 12.5902 | **1.1181** |

The shape is the point: **lower bands down, upper bands up** — the stack steepens. The
load-weighted uniform equivalent is **0.8971**.

### 4.2 DISCLOSURE — a superseded first derivation, and a diagnostic that must not be mistaken for a sweep

Reported against interest, in the order it happened:

1. This lane **first** derived the same ratios on **medians, uncapped**, and got
   `0.774 / 0.699 / 0.793 / 0.900`. Those are **superseded**, for the two reasons in §4.1 — not
   because of what they scored. Their first-order effect is recorded anyway: a ~0.75 uniform
   equivalent, i.e. roughly −14 to −20 % on C3a.
2. This lane **also ran a uniform-multiplier table** (0.70…1.00 against the C3a band) as a
   **coupling diagnostic**, to test whether the model's mean depends on the missing tail. It
   answered that question — it does not (§2) — and it is **not** the selection instrument. It was
   run *before* the revised derivation, which is the uncomfortable ordering, so it is disclosed
   rather than omitted, exactly as the PJM lane disclosed its own G-OA sequencing error.
3. **The derivation was run once and not adjusted after its prediction was seen.** The
   pre-registration is this document.

### 4.3 PRE-SOLVE PREDICTION (first order: price ≈ marginal offer, so a band multiplier scales it)

Band-composition-weighted effective multiplier, from the keeper's own band energies:

| year | band mix (com/lo/hi/peak) | effective | model LW | → predicted | actual | predicted C3a |
|---|---|---|---|---|---|---|
| 2023 | .271/.346/.312/.070 | ×0.9007 | 27.879 | 25.11 | 24.44 | **+2.8 %** |
| 2024 | .244/.355/.323/.078 | ×0.9043 | 26.348 | 23.83 | 24.53 | **−2.9 %** |
| **2025** | .272/.350/.312/.066 | **×0.8992** | 29.970 | **26.95** | 27.96 | **−3.6 %** |

---

## 5. G-DRIFT — the code-level drift audit (rule 29(b)), so no control solve is spent

`git diff 33034499 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference` → 11 files. Every hunk classified:

| file | classification for SPP backcast | reason |
|---|---|---|
| `config/constants.py` | **INERT** | CAISO `NUCLEAR_MONTHLY_CF_BY_YEAR[2022]` — another ISO's branch, a year SPP does not solve |
| `config/fuel_trajectories.py` | **INERT** | CAISO `STATE_CARBON_PRICE_BY_ISO[2022]` — another ISO; SPP runs `carbon_price=0.0`, `carbon_price_path="zero"` |
| `model/interchange/spec.py` | **INERT** | CAISO DSW depth 2022 rows — another ISO's constants |
| `config/scenarios.py` + `results/cache.py` | **INERT** | capx D76 `capacity_screen_peak_measured_hindcast` `False→True`, under the `config.hindcast` predicate a `mode="backcast"` run never enters. `cache.py`'s own census lists SPP's `*-plain-backcast` key `989da50bbf0f99d8` **UNMOVED** |
| `_validation-source/caiso_supply_consistent_demand_2022.csv` | **INERT** | CAISO artifact |
| `_validation-source/actual_lmp_hourly_area_SPP.parquet` | **INERT for the SOLVE** | a scoring-side SPP LMP artifact; it enters no LP input |
| `pipeline/backcast_config.py` | **INERT (already in the control)** | the SPP coal identity bands — the keeper's OWN spp-42 change, which its `run_config.json` records as `dirty` and which it solved WITH |
| **`data/eia930/actuals.py`** | **LIVE** | SPP-41's `NG:` unit-slip screen — it repairs the LP's own delivered wind bound |

**The one LIVE hunk is bounded, by measurement, to 2023 alone.** Running the screen over the SWPP
frame for each year: **2023** NaNs exactly **one** hour (`NG: WND` h3907 = 3,589,445 MW vs a
22,597 MW p99.9), removing **3.5894 TWh**; **2024 removes 0.0000 TWh; 2025 removes 0.0000 TWh.**

⇒ **For 2024 and 2025 the audit is all-INERT, form 4 is valid, and the keeper's committed bundle
IS the control.** For 2023 it is not, and this lane does not difference 2023 against the keeper.

---

## 6. THE SCREEN (rule 29(a)) — declared before it runs

**SCREEN YEAR = 2025.** Two structural reasons, neither of them a residual:

1. **It is the year the mechanism's own footprint is largest** — the rule's own criterion.
   Re-priced energy: 2023 **787.2 M$** (−2.768 $/MWh × 284.4 TWh), 2024 **732.6 M$**
   (−2.522 × 290.5), **2025 911.3 M$ (−3.021 $/MWh × 301.7 TWh)** — largest on both the per-MWh
   and the total measure.
2. **Its control is valid at HEAD** (§5), so the screen costs one solve and no control solve.

Note against interest: **2025 is a year where C3a currently PASSES (+7.2 %)**, and 2023 is the
worst residual (+14.1 %). Screening on 2025 is therefore the opposite of picking the year the
residual is biggest.

**Pre-declared cache keys, computed on the window actually solved** (`start_year`/`end_year` both
`None`, `mode="backcast"`, `hindcast=False`):

| year | CONTROL | ARM | distinct |
|---|---|---|---|
| 2023 | `82d7cb4c4214fad3` | `63e04fd869454b0b` | yes |
| 2024 | `bc2a307f96da7e17` | `e5e3250987fdd8fe` | yes |
| **2025** | `8cc2254194c87b50` | **`41e1184659764e92`** | yes |

### 6.1 THE STOP GATE — structural, STOP-only, never read against the target residual

It asks only whether the mechanism does what its own arithmetic says. **It may kill the arm; it
may not promote it.** All four legs must hold.

- **G-1 — direction and order of magnitude.** The 2025 load-weighted mean price must **fall**, by a
  fraction within half-to-1.5× the pre-solve prediction of **−10.08 %**: realized LW mean in
  **[25.47, 28.47] $/MWh**. *(This tests the mechanism's own predicted delta, not C3a.)*
- **G-2 — the identity the mechanism asserts (steepening).** The model's market-heat-rate ratio
  between the >95th and the 25-75th load percentiles must **RISE** by **≥ 10 %** from the control's
  2025 value of **1.6208** — i.e. **≥ 1.783** (measured SPP is 2.1088). A stack that does not
  steepen has not done the thing this arm exists to do.
- **G-3 — footprint confinement.** The change confines itself to thermal price/merit order:
  non-thermal annual energy (wind + solar + nuclear + hydro) moves **< 1 %**, and unserved energy
  stays **≤ 200 MWh** (control: 89.3 MWh in 1 h).
- **G-4 — no non-target load-bearing criterion flips PASS → FAIL.** C2 stays PASS and C4 stays
  PASS (r ≥ 0.70, NRMSE ≤ 0.30) on 2025.

**If the screen kills the arm, that is the session's result and the remaining years are never
spent.** If it clears, the full span goes as ONE `--year 2023 2024 2025` invocation in ONE bundle
(rule 16), and only that bundle can be a keeper candidate. **The screen bundle is a throwaway
diagnostic probe: never registered, never quoted as a keeper number, and DELETED before merge
(rule 29(c)) — every number this lane will ever cite from it lands in the FINDING.**

## 7. What this lane does NOT claim

- **C1's 2024 gas split is not attempted.** `CT_PEAKER +9.94 TWh / CC_REGULAR −8.60 TWh` is a
  peaker class running baseload — 92.6 % of a CT's capacity sits outside its `peak` band because
  `pct_peaking=7.0`. That is a **structural share**, which rule 1(a) forbids this channel from
  touching. Reported at full magnitude, routed, not fitted around.
- **C3c is not this lane's target** (§3) and is expected not to move materially.
- The gas-series question (`gas_monthly_actuals` / `gas_daily_shape` / an SPP zonal basis —
  `data/raw/spp_zonal_gas_hub.csv` exists and is unarmed) stays **OPEN**, not closed. §1 shows it
  is not the C3a/C3b cause; it was not tested as an arm here.
