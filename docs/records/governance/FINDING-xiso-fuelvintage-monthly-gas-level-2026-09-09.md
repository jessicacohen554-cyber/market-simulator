# FINDING + PRECOMMIT — the monthly gas LEVEL and the 2019-2022 retiree window, six ISOs (xiso-fuelvintage-1)

**Session:** xiso-fuelvintage-1 · **Date:** 2026-09-09 · **ZERO LP.**
**Scope:** CAISO, PJM, MISO, NYISO, NEISO (+ SPP measured but out of scope). **NOT ERCOT** —
ERCOT's copy of both fixes is session ercot-261's; nothing in ERCOT's keeper, shard,
calibration log or matrix cell is touched beyond the rule-28(c) same-PR cell mint.
**Owner instruction (2026-09-09):** monthly fuel data is for EVERYTHING; both fixes belong in
every year; no attribution arms.

> **Nothing here is a keeper claim.** No LP was solved, no year was scored, no run was
> registered, no ISO's determination moved. Both changes land **default-off / provably
> additive**, so every committed keeper bundle in every ISO is byte-identical at HEAD.

---

## 0. Bottom line

| | |
|---|---|
| **Card A (retiree window)** | **DONE and committed.** Artifact 477 → 1,094 units; **31,919 MW** restored to a 2019 solve, **12,945 MW** to 2021. Verified strictly additive. |
| **Card B (monthly gas level)** | **BUILT, default off, not solved.** One shared seam, zero free parameters, admission map measured and pinned. |
| **The prompt's premise on Defect 1** | **PARTLY FALSE, and the correction matters.** Four of six non-ERCOT ISOs *already* price gas on a measured monthly level. **MISO and SPP are the two that do not** — and SPP is out of scope. |
| **Where the fuel defect actually is** | **MISO** (in scope), SPP (out of scope), ERCOT (ercot-261's). PJM/CAISO/NYISO/NEISO have a *different*, milder question. |
| **The biggest single number found** | MISO **Feb-2021** gas is **11.245 $/MMBtu below measured** (~**84 $/MWh** at a 7.5 MMBtu/MWh CC heat rate) — and it is **not fixable from this source**, because Louisiana prints no N3045 month in 2019-2021. |
| **C3b risk (what killed ercot-254)** | Real, and **structurally lower here** — §6. |

---

## 1. CORRECTION: `meta.json` is a CLI echo, not the config

The prompt's fuel table was read off each keeper bundle's `meta.json`, which records only
the calibration CLI flags. The authoritative config is `run_config.json` →
`scenario_config`. Read there, the six non-ERCOT keepers are:

| ISO | keeper bundle | `gas_monthly_actuals` | `gas_hub_basis_overlay` | `gas_daily_shape` | zonal basis |
|---|---|---|---|---|---|
| CAISO | `caiso260_demand_vintage` | **True** | **True** | True | — |
| PJM | `pjm_debugb_inputclock_A` | **True** | False | True | `pjm_zonal_gas_basis` |
| **MISO** | `miso247_fullspan_K` | **False** | **False** | True | `miso_zonal_gas_basis` |
| NYISO | `nyiso213_summer_seam` | **True** | **True** | True | — |
| NEISO | `neiso106_offerlevel` | **True** | **True** | True | — |
| **SPP** | `spp51c_oversupply` | **False** | **False** | **False** | — |
| *(ERCOT)* | *`ercot256_five_year_keeper`* | *False* | *False* | *True* | *`ercot_zonal_gas_basis`* |

So `gas_monthly_actuals = False in every ISO` is wrong for four ISOs, and
`gas_hh_monthly_shape = True in ERCOT ONLY` is right but incomplete — the other ISOs
carry a measured monthly level by a *different* route (F923 ISO-month receipts and/or a
measured hub index), which is why they do not need the ERCOT shape.

**The claim that survives, sharpened, and it is the load-bearing one:** the *annual*
LEVEL underneath is one national scalar everywhere, and **MISO and SPP have nothing on
top of it but the generic climatological shape.**

### 1a. The fingerprint

Monthly coefficient of variation of the model's own delivered-gas series
(`fuel.trajectories._gas_series`, each ISO on its keeper's gas recipe):

| ISO | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| CAISO | 0.196 | 0.194 | 0.361 | 0.233 | 0.936 | 0.278 | 0.215 |
| PJM | 0.227 | 0.228 | 0.217 | 0.176 | 0.258 | 0.284 | 0.290 |
| **MISO** | **0.094** | **0.094** | **0.094** | **0.094** | **0.094** | **0.094** | **0.094** |
| NYISO | 0.297 | 0.183 | 0.233 | 0.208 | 0.231 | 0.415 | 0.553 |
| NEISO | 0.468 | 0.397 | 0.442 | 0.476 | 0.615 | 0.819 | 0.863 |
| **SPP** | **0.094** | **0.094** | **0.094** | **0.094** | **0.094** | **0.094** | **0.094** |
| *(ERCOT)* | 0.091 | 0.120 | 0.098 | 0.217 | 0.103 | 0.179 | 0.142 |

**0.094 in every year is the `GAS_MONTHLY_SEASONALITY` constant, exactly.** MISO's and
SPP's gas price shape is identical in Winter Storm Uri and in a mild spring. That is the
defect, and it is two ISOs' — not six.

---

## 2. CARD A — the retiree window (DONE, committed `7934e92c`)

This is the open **`docs/handoffs/fleet-vintage-retiree-window-charter-2026-08.md`**
(task 2), not a new lever. `RETIREMENT_WINDOW_START: 2023 → 2019`, on the program's
supported span (rule 22 as amended 2026-08-06) — **never on a residual** (rule 23).

Two things the charter did not anticipate:

1. **The source zips are gone.** `data/raw/eia-860/` commits extracted parquet *vintages*
   instead. The reader is now source-agnostic.
2. **A bare rebuild would have DROPPED 161 real units, not added any.** EIA prunes older
   retirements from each release: rebuilding from the currently-available sources gives
   **423** rows against the shipped **477** (−111 of 2023, −50 of 2024). The `preserve`
   argument carries the shipped rows verbatim; `until_year` bounds newly-read rows from
   above.

**Verified additive.** The 477 shipped rows are content-identical after the rebuild
(sha256 `b1f1a953…` over the column- and key-sorted CSV; only the parquet's physical
column order changes, a staleness in the shipped file). Pinned as a **STOP condition** by
`tests/unit/data/test_retiree_window_extension.py` — never a hash to update.

### 2a. Capacity restored, net summer MW

| solve year | total | CAISO | PJM | MISO | NYISO | NEISO | SPP | *(ERCOT)* |
|---|---|---|---|---|---|---|---|---|
| 2019 | **31,919** | 1,700.6 | 13,294.9 | 9,127.8 | 3,671.9 | 1,696.5 | 1,277.9 | *1,149.7* |
| 2020 | **20,735** | 1,120.5 | 8,094.5 | 5,865.5 | 3,261.5 | 956.0 | 1,212.8 | *224.4* |
| 2021 | **12,945** | 278.6 | 5,687.1 | 4,063.3 | 1,570.2 | 949.0 | 174.0 | *222.8* |
| 2022 | **7,685** | 60.1 | 4,535.9 | 2,187.4 | 526.6 | 201.3 | 174.0 | *0.0* |
| **2023-2025** | **0** | 0 | 0 | 0 | 0 | 0 | 0 | *0* |

**The training window is untouched by construction**, which is what keeps every committed
keeper's control valid.

By class, 2019-2022 additions (summer MW): PJM coal **10,649.9**; MISO coal **6,673.5**;
NYISO nuclear **2,050.9** (Indian Point 2 + 3) and coal 1,487.0; NEISO nuclear **673.6**
(Pilgrim) and oil 574.2; MISO nuclear 601.4 (Palisades); CAISO gas-CC 703.0 + gas-ST 480.0.

The charter's own §4 estimate was 264 plants / 21,467.5 MW at a 2019 cutoff; this build
lands **436 plants / 52.8 GW total artifact**, of which **31.9 GW** is the 2019 addition.
The charter counted plants absent from the operable snapshot at one vintage; this unions
five vintages, which is why it is larger.

### 2b. A SEPARATE gap, routed not absorbed

The currently-committed (newer) release sheet also carries **107 units / 497.7 MW of
2023-2025 retirements** the original build's vintages did not — mostly sub-10 MW units,
largest NEISO-2025 166.5 MW and SPP-2024 140.3 MW. They are **real** and they are
**missing from every keeper's training fleet**. They are excluded here because adding them
would change 2023-2025 and re-key every committed bundle. **This is a training-window
change and belongs to a session scoped to one**, per ISO, with its own control.

---

## 3. CARD B — the phase-0 fuel table (the deliverable that decides everything)

Measured level = EIA `N3045<ST>3` monthly, $/Mcf ÷ 1.036, blended across the ISO's
footprint states by its EIA-860 installed gas capacity there. Model level = the monthly
means of `_gas_series` on each ISO's keeper gas recipe. `$/MWh` at 7.5 MMBtu/MWh (EIA
Table 8 legacy CC); a CT-marginal hour is ~1.4×.

**Admission** (declared ex ante, never swept): the states used print in all twelve months
AND carry a strict majority of the ISO's gas capacity.

| ISO | year | admit | basket share | model ann. | measured ann. | Δ ann. | max month gap | = $/MWh | mae |
|---|---|---|---|---|---|---|---|---|---|
| CAISO | 2019-21 | **inert** | 0.02 | — | — | — | — | — | — |
| CAISO | 2022 | ADMIT | 1.00 | 7.724 | 9.526 | +1.801 | **16.058** (Dec) | **120.4** | 2.173 |
| CAISO | 2023 | ADMIT | 1.00 | 6.952 | 7.038 | +0.085 | 2.888 (Mar) | 21.7 | 1.077 |
| CAISO | 2024 | ADMIT | 1.00 | 3.372 | 3.608 | +0.236 | 2.222 (Jan) | 16.7 | 0.684 |
| CAISO | 2025 | ADMIT | 1.00 | 4.065 | 4.273 | +0.208 | 1.285 (Jun) | 9.6 | 0.551 |
| PJM | 2019 | ADMIT | 0.58 | 3.205 | 2.502 | −0.703 | 1.326 (Dec) | 9.9 | 0.704 |
| PJM | 2020 | ADMIT | 0.78 | 2.484 | 1.936 | −0.548 | 1.178 (Feb) | 8.8 | 0.552 |
| PJM | 2021 | ADMIT | 0.72 | 4.109 | 3.581 | −0.528 | 1.075 (Dec) | 8.1 | 0.527 |
| PJM | 2022 | ADMIT | 0.98 | 7.121 | 6.479 | −0.641 | 1.374 (Feb) | 10.3 | 0.646 |
| PJM | 2023 | ADMIT | 0.98 | 3.255 | 2.485 | **−0.770** | 1.415 (Feb) | 10.6 | 0.775 |
| PJM | 2024 | ADMIT | 0.98 | 2.856 | 2.387 | −0.469 | 0.736 (Feb) | 5.5 | 0.473 |
| PJM | 2025 | ADMIT | 0.91 | 3.934 | 3.745 | −0.189 | 1.720 (Jan) | 12.9 | 0.479 |
| **MISO** | **2019-21** | **inert** | 0.30-0.34 | — | — | — | — | — | — |
| MISO | 2022 | ADMIT | 1.00 | 6.718 | 6.588 | −0.130 | 2.315 (Feb) | 17.4 | 1.364 |
| MISO | 2023 | ADMIT | 1.00 | 2.839 | 3.019 | +0.179 | 1.000 (Jan) | 7.5 | 0.264 |
| MISO | 2024 | ADMIT | 1.00 | 2.489 | 2.558 | +0.069 | 1.551 (Jan) | 11.6 | 0.330 |
| MISO | 2025 | **inert** | 0.40 | — | — | — | — | — | — |
| NYISO | 2019 | ADMIT | 1.00 | 3.054 | 3.006 | −0.048 | 1.082 (Feb) | 8.1 | 0.293 |
| NYISO | 2020 | ADMIT | 1.00 | 2.102 | 2.134 | +0.033 | 0.473 (Nov) | 3.5 | 0.257 |
| NYISO | 2021 | ADMIT | 1.00 | 4.399 | 3.869 | −0.530 | 0.977 (Feb) | 7.3 | 0.595 |
| NYISO | 2022 | ADMIT | 1.00 | 8.443 | 7.056 | **−1.387** | 3.644 (Jan) | 27.3 | 1.550 |
| NYISO | 2023 | ADMIT | 1.00 | 3.357 | 2.920 | −0.437 | 1.330 (Jan) | 10.0 | 0.753 |
| NYISO | 2024 | ADMIT | 1.00 | 2.797 | 2.687 | −0.110 | 0.774 (Dec) | 5.8 | 0.319 |
| NYISO | 2025 | ADMIT | 1.00 | 5.560 | 4.371 | **−1.189** | **5.107** (Jan) | **38.3** | 1.180 |
| NEISO | 2019 | ADMIT | 0.70 | 3.175 | 3.921 | +0.746 | 2.124 (Feb) | 15.9 | 0.757 |
| NEISO | 2020 | ADMIT | 0.70 | 2.003 | 2.817 | +0.814 | 2.018 (Jan) | 15.1 | 0.818 |
| NEISO | 2021 | ADMIT | 0.70 | 4.534 | 5.257 | +0.723 | 2.922 (Dec) | 21.9 | 0.994 |
| NEISO | 2022 | ADMIT | 1.00 | 9.157 | 10.551 | +1.393 | 5.150 (Feb) | 38.6 | 1.500 |
| NEISO | 2023 | ADMIT | 1.00 | 2.936 | 5.240 | **+2.303** | **10.610** (Jan) | **79.6** | 2.302 |
| NEISO | 2024 | ADMIT | 0.92 | 3.030 | 3.981 | +0.951 | 4.131 (Feb) | 31.0 | 1.100 |
| NEISO | 2025 | ADMIT | 0.70 | 6.226 | 6.114 | −0.112 | 1.654 (Dec) | 12.4 | 0.717 |
| *(SPP)* | *2022* | *ADMIT* | *1.00* | *6.158* | *7.654* | *+1.496* | *13.368 (Jan)* | *100.3* | *2.361* |
| *(SPP)* | *2024* | *ADMIT* | *1.00* | *1.929* | *2.811* | *+0.882* | *3.432 (Jan)* | *25.7* | *0.880* |

Footprint weights (`data/raw/reference/iso-gas-capacity-state-weights.csv`): CAISO CA .983
NV .017 · PJM PA .281 OH .174 VA .142 IL .131 NJ .101 MD .060 · MISO **LA .238** MI .147
WI .095 IN .095 TX .091 MN .076 · NYISO NY .938 NJ .062 · NEISO MA .376 CT .325 RI .120
ME .095 NH .084 · SPP **OK .375** TX .185 KS .108 MO .106.

### 3a. The outlier months the prompt named, checked

- **Feb 2021 (Uri).** ERCOT (out of scope) is the extreme: model $10.20 vs measured
  $59.73, gap **49.53**. **MISO**: model $4.42 vs measured $15.67, gap **11.245**
  (~84 $/MWh) — on a **55 %** basket that **excludes Louisiana**, so the true gap is
  larger, not smaller. SPP 2021: **no coverage at all** (Oklahoma, 37.5 %, prints nothing).
- **Dec 2022 (Elliott).** Present but modest: PJM Dec-2022 gap −0.80, NYISO +1.04, NEISO
  +4.55. **The Mid-Atlantic ISOs' Elliott is NOT a monthly-level defect** — a 4-day event
  is invisible in a monthly mean, which is exactly the within-month smearing ercot-254 §3b
  diagnosed one resolution up. Their Elliott lever is `gas_daily_shape` (already armed) or
  a daily basis, not this.
- **2022 European spike.** NEISO +1.393 annual, CAISO's own Dec-2022 western crisis
  **+16.058** in one month.

### 3b. Coverage is the binding constraint, and it bites where it hurts most

The gaps are **EIA withholdings**, not an intake defect (`SOURCES_eia_delivered_gas_
electric_power_by_state.md`: "pre-2022 is thin or absent for AL, AR, CO, FL, KY, **LA**, ME,
MN, MO, MS, NH, **OK**, OR, WA, WV, WY"). **Louisiana — 23.8 % of MISO's gas capacity and
the state Uri hit hardest — prints no N3045 month in 2019, 2020 or 2021.** So MISO's own
Uri year is **not priceable from this source**, and the seam refuses rather than blend a
basket that omits the hot state. A national (`N3045US3`) backfill was considered and
**rejected**: it would put a national number back into exactly the state-months where the
local price departs most from national, which is the defect being repaired.

---

## 4. CARD B — the seam (BUILT, default off, committed `7648daa0`)

`ScenarioConfig.gas_electric_power_monthly_level`, CLI
`--gas-electric-power-monthly-level`; `src/market_sim/data/fuel/electric_power.py`.

**Rule 19 `[R-ONE-MECH]` — three strictly-ordered levels, each superseding the last, never
stacking:**

```
national annual  <  state-average monthly  <  measured hub index
(HH traj/override  (THIS SEAM: replaces the      (gas_hub_basis_overlay:
 + flat basis        annual x shape AND            NEISO Algonquin, CAISO
 x generic shape)    gas_monthly_actuals)          SoCal/PG&E, NYISO Transco Z6)
```

The seam is applied **before** `apply_hub_basis_overlay`, so an ISO that already prices
gas off a measured **constrained-hub index** keeps it. That is deliberate: a hub index is
the marginal unit's own opportunity cost; N3045 is an average delivered cost across every
purchase in the state. **The more local measured marginal series wins.**

**Every existing basis mechanism, level vs spread** (the enumeration Card B asks for):

| mechanism | ISO(s) armed | level or spread? | interaction |
|---|---|---|---|
| `GAS_BASIS_DIFFERENTIAL` | all | **level** (one flat annual constant) | **superseded** |
| `gas_seasonality` / `gas_hh_monthly_shape` | all / ERCOT | **shape** (mean-preserving) | superseded (the seam sets the monthly level outright) |
| `gas_daily_shape` | all but SPP | **shape** (mean-preserving per month) | **kept** — applies on top, different timescale |
| `gas_monthly_actuals` (F923 ISO-month) | CAISO PJM NYISO NEISO | **level** | **superseded** |
| `gas_hub_basis_overlay` | CAISO NYISO NEISO | **level** (measured hub) | **supersedes the seam** |
| `pjm_zonal_gas_basis` | PJM | **spread** (mean-zero) | kept, orthogonal |
| `miso_zonal_gas_basis` | MISO | **spread** (mean-zero) | kept, orthogonal |
| `nyiso_zonal_gas_basis` | NYISO | **spread** (mean-zero) | kept, orthogonal |
| `ercot_zonal_gas_basis` / `ercot_ep_gas_basis_monthly` | *(ERCOT)* | **level + spread** | **must never be armed with the seam** (same phenomenon) |

**Forward reproducibility (rule 13).** The construction is *blend(state monthly delivered
gas)*; for a forward year it regenerates from a forward monthly gas curve through the
identical blend, and it responds to conditions (a mild winter's cheap February reaches the
merit order). A year with no admissible print returns `None` and the caller is unchanged,
so every forecast run is byte-identical.

**DOF ledger (rule 21).** Free parameters: **zero.** The weight table is a frozen derive
off EIA-860 (`scripts/data/derive_iso_gas_state_weights.py`); the unit conversion is the
EIA heat content 1.036 MMBtu/Mcf; the two admission conditions are declared here, ex ante,
and are **never swept against a gate** (rule 1 (c)).

---

## 5. PRE-REGISTERED EXPECTATIONS, per ISO

Registered **before any solve**. Report every criterion at full magnitude; do not gate on
the target (rule 1). These land because they are **correct** (rule 14): a worse fit is a
root-cause investigation, never a revert to the estimate.

### 5a. Capacity (Card A) — applies to 2019-2022 solves only

| ISO | 2021 MW added | prediction |
|---|---|---|
| PJM | 5,687 (coal-dominated) | **Prices FALL** in 2021/2022. Largest effect of any ISO. Coal generation UP, gas CC down. |
| MISO | 4,063 (coal + Palisades) | **Prices FALL** in 2021/2022, second-largest. |
| NYISO | 1,570 (Indian Point 3 + coal) | **Prices FALL** modestly in 2020/2021; 2020 (3,262 MW incl. Indian Point 2) is the bigger year. Nuclear generation UP. |
| NEISO | 949 (Pilgrim + oil) | 2019/2021 only; **~2.1 TWh of nuclear restored in 2019** (charter §4 — 91 % of NEISO 2019's C1 error budget). 2022 immaterial (201 MW). |
| CAISO | 279 (2021) / 1,121 (2020) | **NO material movement in 2021.** A large 2021 move is a BUG to investigate, not a win. |
| all | 2023-2025 | **EXACTLY ZERO change.** Any nonzero delta means capacity-denominated code is reading retired units (charter task 3) — STOP and root-cause. |

### 5b. Fuel (Card B) — sign and rough magnitude from §3

| ISO | admitted years | predicted direction | predicted magnitude | note |
|---|---|---|---|---|
| **MISO** | 2022-24 only | gas **UP** 2023/24 (+0.18/+0.07), **DOWN** 2022 (−0.13) | small on the annual, **material in January** (1.0-1.6 $/MMBtu ⇒ 7.5-11.6 $/MWh) | the ISO the seam was built for; **inert in 2019-2021**, so a 2020/2021 MISO solve tests Card A ALONE |
| **PJM** | all 7 | gas **DOWN** in every year | −0.19 to −0.77 $/MMBtu annual; every month of 2023 lower | replaces the F923 receipt level, which runs high in 12/12 months. **Coal UP, prices DOWN.** Largest and most uniform fuel move of any ISO |
| **NYISO** | all 7 | gas **DOWN**, 2022 and 2025 most | −1.39 / −1.19 annual; Jan-2025 −5.11 | **but the hub overlay covers 12/12 months every year and supersedes**, so the seam should be **NEAR-INERT**. A large NYISO move means the ordering is wrong — STOP |
| **NEISO** | all 7 | gas **UP** if it fires | +0.75 to +2.30 annual | same: hub overlay covers 12/12 and supersedes ⇒ **NEAR-INERT expected**. See §6a — NEISO's real question is not this flag |
| **CAISO** | 2022-25 | gas **UP** slightly | +0.09 to +0.24 annual (2023-25) | hub overlay supersedes ⇒ **NEAR-INERT expected**; **inert by coverage 2019-2021** |

**Flatness check:** MISO 2023 measured monthly cv is 0.148 against a model 0.094 — a small
difference, so MISO 2023 must barely move. **If it moves a lot, that is a bug.**

**Outlier months must stay right.** Whatever each model currently gets right in Feb-2021
and Dec-2022 must not break. In particular MISO Feb-2021 is **inert by coverage** here, so
it cannot break — and it also cannot be fixed by this seam. Said plainly rather than
implied.

### 5c. C3b, explicitly, per ISO

C3b is the gate that killed ercot-254. Pre-registered:

- **PJM** — highest risk. A uniform −0.5 to −0.8 $/MMBtu level cut moves every hour; C3b
  (monthly-shape NRMSE) could go either way, and the *annual* C3a level almost certainly
  moves down. **Predicted: C3a improves or is flat; C3b within ±0.03.**
- **MISO** — low risk in 2022-2024 (annual Δ ≤ 0.18 $/MMBtu); the move is concentrated in
  January, which is where C3b's monthly shape is measured, so **C3b is the criterion most
  likely to move — predicted improvement, magnitude < 0.05.**
- **CAISO / NYISO / NEISO** — near-inert by the ordering, so **C3b predicted unchanged to
  3 decimals.** A move is evidence the seam is firing where it should not.

---

## 6. Why C3b will not break the way ercot-254 broke — and where the risk really is

`RESULT-ercot254-monthly-ep-basis-2026-09-07.md` §3b diagnosed the failure precisely:
the monthly EP level applied **February 2021's $59.73/MMBtu to all 672 February hours**,
while the real Uri gas spike lasted about **five days**. C3c went 234 → 688 h against 258
actual; the 454 extra hours were February's non-storm hours. The annual smearing was
fixed and a **within-February** smearing was exposed underneath.

Four things differ here:

1. **No ISO in scope has a Uri-scale month admitted.** ERCOT's Feb-2021 gap is 49.5
   $/MMBtu. The largest admitted gap in scope is **NEISO Jan-2023 at 10.6** and **CAISO
   Dec-2022 at 16.1**; every other admitted month is under 5.2. The failure mode scales
   with the outlier, and the outlier is 3-5× smaller.
2. **MISO's Uri month is refused, not smeared.** The one in-scope ISO-month with a
   30-sigma event is exactly the one the coverage test declines to price. ercot-254's
   defect is structurally unreachable in MISO 2021 here.
3. **`gas_daily_shape` is already armed in all five in-scope keepers** (it was NOT part of
   ercot-254's arm as the level repair). The measured Henry Hub *daily* within-month shape
   multiplies on top of this monthly level, mean-preserving per month — so a month's cost
   is distributed across its days by the real commodity swing rather than flat. That is
   precisely the "next resolution finer" ercot-254 §6 named as its successor, and it is
   already in every recipe.
4. **The hub-index ordering protects the three ISOs with the biggest level gaps.** NEISO,
   NYISO and CAISO — the three largest annual Δ — are the three whose measured hub index
   supersedes the seam, so their level does not actually move.

**Where the risk really is: PJM.** It is the only in-scope ISO with (a) no hub overlay,
(b) a uniform level cut in every month of every year, and (c) full seven-year admission.
PJM's arm is the one that must be screened first. **Pre-registered STOP:** if PJM's screen
year shows any load-bearing criterion (C1/C2/C3a/C3b) flipping PASS → FAIL, the arm dies
there and the remaining years are never spent (rule 29).

### 6a. A discrepancy this session did NOT resolve, stated not absorbed

For **NEISO Jan-2023**, two measured sources disagree by **3.2×**: the ISO-NE published
Algonquin Citygate index gives HH 3.273 + 1.46 = **$4.73/MMBtu**, and N3045 MA/CT/RI
delivered-to-electric-power reads **$15.34**. This is why NEISO's keeper series sits
2.303 $/MMBtu below measured on the 2023 annual — the single largest level gap in the
table.

They measure different things: a **day-ahead index** versus the **average delivered cost
actually paid**, including the intraday and balancing purchases New England generators
without firm transport make in January. The marginal **offer** is set by the index, so the
hub index correctly keeps priority — this is rule 14's misalignment exception, invoked
explicitly. **But a 3.2× gap between two measured series for one quantity is not a closed
question**, and it is NEISO's real fuel lever, not this flag. Routed to the NEISO lane.

---

## 7. Governance

- **Rule 22 `[R-HOLDOUT]`:** both changes are data prep + a default-off field. No year was
  solved, scored or registered; **no marker is engaged and none is requested.** Per-ISO
  marker reads for the LP sessions are in the handoff prompts.
- **Rule 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`:** both land because they are correct. Neither
  was selected on a residual, and the admission conditions are declared here before any
  solve and are never swept.
- **Rule 19 `[R-ONE-MECH]`:** §4's ordering table; nothing stacks.
- **Rule 21 `[R-DOF]` / 24 `[R-REGISTRY]`:** zero free parameters; one registered field
  with a CLI flag, in the cache key and the mechanism matrix.
- **Rule 25 `[R-ISO-SCOPE]`:** one construction, measured, everywhere — no per-ISO fitted
  curve. The ERCOT and SPP matrix cells are minted `U` by rule 28(c)'s same-PR duty only;
  **no ERCOT or SPP adjudication is made or implied.**
- **Rule 31 `[R-RETAIN]`:** no bundle was produced, so nothing is at risk of loss.
- **Coordination:** at the time of writing `origin` carries no ercot-261 branch, so **this
  session owns the shared fuel seam and built it**. ERCOT must never arm
  `gas_electric_power_monthly_level` alongside `ercot_ep_gas_basis_monthly` or
  `ercot_zonal_gas_basis`'s EP level term — they price the same phenomenon.
