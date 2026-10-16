# DESIGN — a reliability-commitment (RUC) pass for the MILP UC stage, 2026-10-16

**Lane:** UC-RUC-DESIGN (Opus) · **Chartered by:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`), owner ruling r16 (2) 2026-10-16, PR #7273.
**Scope:** zero LP. A design, zero-LP evidence from committed bundles, a PRECOMMIT draft and a matrix-row proposal. No `src/` change,
no solve, no matrix code change. Nothing here is armed until the owner approves the design.
**Basis:** `main` `5bdc2c58` (engine uc-1.8, `41cd55dc`). Evidence bundles: `docs/records/spp/ucmilp/data/ucmilp4_spp_u4_span/`
(UC-4 SPP, uc-1.7), the CAISO/NYISO UC-4 PRECOMMITs and interim RESULTs on `claude/ucmilp-4-caiso` / `claude/ucmilp-4-nyiso`.
Evidence script: Appendix A (reads committed sidecars and the EIA-930 frame the demand loader reads; no LP).

## 0. Summary

1. **What is missing.** The UC window commits against the measured DA load forecast (r13 ruling 1) and nothing re-commits after it.
   Every RTO runs a reliability commitment after its DA market: it commits *additional* units against the ISO's own load forecast
   plus reserves. It never de-commits DA units, and it pays start/no-load through make-whole outside the LMP (§1).
2. **The mechanism (one, rule 19).** A RUC pass inside the existing UC stage, run only on days the DA commitment cannot serve.
   It re-solves those days' windows with `u ≥ u_DA`, the RUC load basis as demand, and a commitment-cost-only objective.
   It feeds the same MECH 28 bounds into a second P1, and its cost goes to the uplift sidecar. **Zero free parameters.** A year
   with no shortfall is byte-identical to the arm without RUC (§2).
3. **RUC load basis.** SPP archives its MTLF hourly vintages at source; the research for this doc downloaded and checked them.
   That makes the faithful ID-RUC basis measurable: the vintage in force at the ID-RUC cycle before each operating hour. It
   is not on disk yet. Until it is intaken, the only basis that adds no free parameter is the realised load (the P1 demand),
   declared as an upper bound (perfect intraday foresight). Recommended: intake first (§2.2, §5 Q5).
4. **Zero-LP evidence, SPP U4 (§3).**
   - The RUC would act only in 2024: 39 hours on 16 days.
   - In 2019–22 and 2025 there are zero trigger hours, so those years are identical to U4.
   - In 2024 the uncovered need is at most 1.31 GW. Offline integer capacity is at least 2.89 GW (nameplate) in every one of the 39
     hours, so the shortfall is closable in capacity terms.
   - Price: removing the reserve adder on the 16 days would move 2024 C3a from **+47.6 % to about +25 %**. Removing it in all
     hours gives about **+16 %**.
   - **So the RUC closes the scarcity, not the whole 2024 gap.** The rest is a year-long tight-reserve adder (3,231 h, $9.4/MWh
     load-weighted, against $2–3 in other years). It traces to the same 2024 DF series, and that series should be audited
     (rule 14) before it is called structure (§3.3).
5. **First test arm (§4).** SPP, U4 + RUC. Under the GATESPEC keeper verdict the outcome is **R before any solve**: U4's 2025 flips
   (C3b, C1 ST_GAS) sit in a year the RUC cannot touch. The arm is therefore a structural test against U4, its nearest ancestor.
   It costs two legs (2023, 2024) if the owner accepts the identity argument for the five zero-trigger years (§5 Q3).

## 1. What each UC ISO's RUC does (cited)

Read 2026-10-16 from the primary sources listed under the table. **UNVERIFIED** marks a claim not confirmed in the effective
document.

| ISO | process | timing | load basis and reserves | de-commit DA units? | objective | cost / price |
|---|---|---|---|---|---|---|
| **SPP** | DA-RUC (Protocols §4.3.2); ID-RUC (§4.4.1) | DA-RUC at 13:45 CPT, or 45 min after DA results if later. ID-RUC at least every 4 h, up to 15 min before RT. A short-term ID-RUC every 15 min covers the next ≥ 120 min | **SPP Mid-Term Load Forecast (MTLF)**, not bid-in demand (§4.1.2.1: "The DA Market relies on bid-in demand so these load forecasts are not used in that process"). Includes Operating Reserve | only as an exception (excess supply / emergency, §4.3.2.2(3)(b), §4.3.2.4) | **commitment cost only**: start-up + no-load + cost at minimum output; energy above minimum and reserve offers excluded (§4.3.2.2(2)) | RUC make-whole (Settlements Calculation Guide §2.7.8); price-setting of RUC units **UNVERIFIED** |
| **CAISO** | RUC, the step after the IFM inside the DAM (Tariff §31.5) | after the IFM, same DA run | **CAISO Forecast of BAA Demand** vs IFM physical supply, virtuals excluded (§31.5.3). Reserves not procured; the forecast may be raised for an IFM AS shortfall (§31.5.3.1.6) | **no**: uncommitted capacity only (§31.5.5, §31.5.5.2–.3) | RUC availability bids + start-up + min-load + transition; **no energy bids** (§31.5.5.2) | availability paid at RUC price; start-up / min-load via Bid Cost Recovery (§11.8, per §31.5.6) |
| **NYISO** | DAM SCUC Pass 2, "Bulk Power System Forecast Load Commitment"; Supplemental Resource Evaluation (SRE) | Pass 2 inside DAM SCUC; SRE post-DAM or intraday | **ISO zonal DA load forecast**, ignoring bids and virtuals (M-11 §4.3); MST §4.2.3: "committing sufficient Capacity to meet the ISO's Load forecast and provide associated Ancillary Services" | **no**: Pass-1 units locked at ≥ their Pass-1 output | "only incremental uplift costs", no energy cost | BPCG (MST Att. C). LBMPs come from the bid-load passes |
| **MISO** | Reliability Assessment Commitment: Multi-Day, Post-DA (Forward), Intraday; plus LAC | Post-DA RAC 14:30–18:00 EPT on OD-1; intraday as needed; LAC from OH-4 | **MISO 7-day hourly load forecast**, "not used to clear the Day-Ahead" market. Includes Operating Reserve | only for a projected surplus (BPM-002 §6.3) | commitment cost, "not the cost to serve the forecasted Energy" | Revenue Sufficiency Guarantee (BPM-002 §6.1.4, BPM-005); fast-start units may set price via ELMP |
| ERCOT | DRUC, HRUC (Nodal Protocols §5) | DRUC after DAM close; HRUC before every operating hour | **ERCOT load forecast** + RUC AS demand curves (§5.5.2(1)) | only for otherwise unresolvable transmission constraints (§5.5.2(9)) | start-up + minimum-energy offers; energy on proxy curves (§5.5.2(16)) | make-whole / clawback (§5.7.1–.2). **$250/MWh offer floor** for RUC units in SCED (§6.5.7.3(d)) plus the Reliability Deployment Price Adder |
| ISO-NE | Reserve Adequacy Analysis (RAA) | after the DA re-offer period | ISO load forecast vs DA cleared demand | **UNVERIFIED** | **UNVERIFIED** | NCPC (**UNVERIFIED**); since DASI (ER24-275) part of the gap is cleared in the DA market |

**Sources:**
- **SPP:** Integrated Marketplace Protocols Rev 119 (2026-07-17), DA-RUC pp.165–171, ID-RUC from p.172.
  MTLF definition: "rolling hourly basis for the next seven days for input into Reliability Unit Commitment".
  <https://www.spp.org/Documents/77252/Integrated%20Marketplace%20Protocols%20119%20-%20Active%20Version.zip>
- **CAISO:** Tariff §31 as of 2026-05-01, <https://www.caiso.com/documents/section-31-day-ahead-market-as-of-may-1-2026.pdf>.
- **NYISO:** MST §4.2.3, <https://www.nyiso.com/documents/20142/33562316/MST%204.2.pdf>. M-11 §4.3 was read from a v6.5 discussion
  draft; confirm against the effective manual.
- **MISO:** BPM-002-r23 §6 (pp.240–250), read from a KY PSC exhibit, <https://psc.ky.gov/pscecf/2022-00402/>. The current revision
  is **UNVERIFIED**.
- **ERCOT:** Nodal Protocols §5 and §6 (2026-08-01).
- **ISO-NE:** SOP-RTMKTS.0050.0010; read from search snippets only.

**Load-forecast data at source (downloaded and checked 2026-10-16):**
- **SPP:** portal `mtlf-vs-actual` publishes **one file per hour** (`OP-MTLF-YYYYMMDDHH00.csv`: `Interval, GMTIntervalEnd, MTLF,
  Averaged Actual, BAA`; 7 days forward). Years are archived as one zip each (`/2024/2024.zip`, ~9,100 vintages, 16.9 MB; folders
  2013–2026). The file-browser API needs no login.
- **CAISO:** OASIS `SLD_FCST` returns DAM / 2DA / 7DA hourly and RTM (15- and 5-min), one vintage per run id. HASP/RUC runs return no
  data. Whether DAM is exactly the forecast RUC used is **UNVERIFIED**.
- **NYISO:** `isolf` publishes one vintage a day, posted about 07:30 D-1.
- **MISO and ERCOT archives:** not checked.
- **EIA-930 DF** is the BA's "day-ahead demand forecast" (form instructions, OMB 1905-0129).
- **SPP's EIA-930 DF vs MTLF:** over 177 days of Jul–Dec 2024, the DF best matches the MTLF vintage stamped 00:00 on D-1 (median
  |Δ| 28 MW, 44.5 % of hours exact). The match worsens for every later vintage (median about 180 MW by D-1 afternoon). **Inference:**
  the model's DA basis is an *early* D-1 MTLF. It is not the vintage the 13:45 DA-RUC used, and it is not the ID-RUC's.

**Common structure, which the design keeps:**
- The RUC runs **after** DA economics.
- It commits to the **ISO's own load forecast** (not bid-in demand) **plus reserves**.
- It is **add-only**.
- The objective is **commitment cost**: start-up, no-load and minimum-load energy. Energy bids are excluded (SPP, CAISO, NYISO
  Pass 2, MISO; ERCOT uses proxy curves).
- Its cost is **make-whole outside the LMP**.

**Where the model already stands.** The UC window already commits to the ISO's own forecast (EIA-930 DF), not to bid-in DA demand,
plus the co-optimized reserve requirement. For SPP that is an early D-1 MTLF vintage, close to the DA-RUC target. The missing object is the **intraday** recommitment (SPP
ID-RUC, MISO intraday RAC, ERCOT HRUC, NYISO SRE / RTC commitment) on an updated forecast. For SPP 2024, that is what covers a DA
forecast that was 2 GW low.

## 2. The mechanism

### 2.1 Sequence (per year, inside the existing UC stage)

```
P0 ─► UC-DA windows (commitment demand = DF; unchanged, uc-1.8) ─► inject MECH 28 ─► P1a
        │
        └─ screen (zero LP): hours of P1a with reserve shortfall > 0 or energy slack > 0
              none ─► P1a IS the scored P1 (byte-identical to the arm without RUC)
              some ─► RUC windows on the affected days ─► u_final ─► inject MECH 28 ─► P1b (scored)
```

**RUC window.** It is the existing `UcWindowModel` on the same 24 + 12 h slice. There is no new model class (rule 19). Four
things change:

| element | DA window (today) | RUC window |
|---|---|---|
| demand | commitment demand (DF) | **RUC basis** (§2.2) |
| integer lower bound | 0 (carried history aside) | **`u ≥ u_DA[c,t]`**: add-only, never de-commits a DA unit |
| objective on dispatch columns | offer/base cost | **ε** (the rule-9 tiebreaker): energy cost leaves the decision |
| objective on commitment | start + no-load | start + no-load + **minimum-load energy** `mlf·pbar·a·mc_uc` per unit-hour |
| penalties | VOLL, reserve demand-curve steps | **unchanged** (the same values P1 uses) |
| min-up / min-down / reserve u-gate / spin sub-row | as built | unchanged |

- Result: the RUC adds units only where avoiding a penalty is worth more than the commitment cost. That is a reliability
  commitment, not an economic re-dispatch.
- Each day's window keeps 24 h, as today.
- **Sweep rule:** the RUC re-solves forward from the first triggered day. It stops once the carried state equals the DA
  schedule's and no RUC-started unit still owes min-up. The worst case is about `ut_h`/24 extra days per episode (SPP coal
  median 60 h, so 3 days).
- `u_final` is the RUC schedule on swept days and the DA schedule elsewhere.

**Why a P1a screen and not a per-window screen.** A fixed-`u` LP feasibility check per window costs presolve plus root LP, about
2–3.5 s/window (uc_solve_log phase sums). Over 365 windows that is 15–20 min, which SPP 2024 cannot afford (§2.5). The
P1a screen costs nothing extra: P1a is the P1 we already solve.

The screen is used only to choose **where** the RUC runs. The RUC window then decides **what** to add, on the RUC basis, and may
add nothing. Two declared approximations:
- A shortfall seen by the full-year P1 but absent in the 36 h window adds nothing.
- A window-only shortfall that P1 resolves (storage SOC or budgets differ between P1 and the window) is not swept.

### 2.2 Inputs and rule-13 admissibility

| input | backcast | forecast | rule 13 |
|---|---|---|---|
| `u_DA`, the DA schedule | the UC-DA pass (already solved) | same | model-internal |
| RUC basis | **SPP MTLF intraday vintage** once intaken; until then **P1 demand (realised load)**, an upper bound | P1 demand (the forecast-year load) | admissible: the same quantity exists forward from forward drivers and moves with them; it is the input P1 already clears on, not an output |
| trigger | P1a reserve shortfall / slack | same | model-internal |
| penalties | P1's VOLL and reserve demand curves (tariff-cited, on `main`) | same | — |
| `mlf`, `pbar`, `ut_h`, `dt_h`, no-load, start cost | uc-params (frozen derives, rule 23) | same | already admitted |

**RUC load basis: what exists.**
- **On disk:** only the EIA-930 DA forecast (already the DA basis) and metered load. `data/raw/load-forecast/` holds long-term
  planning forecasts and is irrelevant here.
- **At source** (§1): SPP MTLF, **one vintage per hour, archived per year** (confirmed). CAISO OASIS `SLD_FCST` keeps one vintage
  per run id (DAM / 2DA / 7DA / RTM); its RTM run is an intraday forecast. NYISO `isolf` keeps one D-1 vintage a day, so it has no
  intraday series.
- **Without an intraday series,** the only basis that adds no free parameter is the realised load. An error draw or a haircut
  would be a number chosen by us (rules 5, 13).
- **SPP measured basis (`uc_ruc_load_basis="iso_intraday_forecast"`):** for operating hour *h*, the MTLF vintage issued at the
  last ID-RUC cycle at least one cycle before *h*. The cycle is the protocol's "at least every 4 h" (§4.4.1), a cited value,
  not a free one. Rule 13 (backcast): the same quantity is a forecast of forward load; forward it collapses to the error-profile
  form, like the DA basis.
- **Fallback basis (`"actual"`):** realised load, declared as an upper bound (perfect intraday foresight, zero ID-RUC error).
  It is admissible, but it overstates the RUC wherever the intraday forecast also missed. Rule 14 prefers the measured basis
  for SPP.
- **Rule-14 alignment check for the intake:** SPP's MTLF BAA is `SPP` / `SWPW`, while the model's demand is EIA-930 SWPP. The
  intake must reconcile the footprint, as FIX-7 did for the DF.
- **Forecast mode:** the DA demand is realised × (1 + the mean error profile). For ISOs whose profile is positive in nearly all
  season-hours (SPP, MISO), the RUC is near-inert forward: the mean profile has no bad days. That is a known limit of a mean
  profile, not of the RUC (§5 Q5).

### 2.3 Interaction with MECH 28 and the u-gate

- **Same bounds, same tag.** `u_final ≥ u_DA` goes through `UcStage.floor_and_ceiling` / `inject` unchanged: ceiling `a·u/n`,
  floor `mlf·pbar·a·u` filled in merit order, one tag `MECH_UC_SCHEDULE`. There is no new floor family (rule 19).
- **D-4 / rule 20.** The RUC-added floor energy (`u_final − u_DA` unit-hours × floor) is reported separately in
  `legitimacy_diagnostics` as a sub-row of MECH 28 (`uc_ruc`). Rule 17 holds by construction: driver = a P1a shortfall,
  window = the triggered days plus min-up, forward story = §2.2.
- **u-gate (uc-1.6) and the SPP spin sub-row.** These are unchanged. An added integer member's headroom enters the reserve rows
  through `u`, so RUC units supply spin and contingency directly. That is the channel the 2024 shortfall needs (spin short 35 h,
  contingency 28 h).
- **Markup.** Integer clusters already bid zero amortized start markup in P1 (R3), so RUC units bid `mc_base`. A RUC unit
  can set the LMP only as an ordinary online unit. Its commitment cost is never in a dual (rule 4). ERCOT is different: it floors
  RUC units' SCED offers at $250/MWh (§6.5.7.3(d)). That would be a separate, ERCOT-only, cited price rule, out of scope here.
- **Uplift.** `compute_uplift` runs on `u_final` / `v_final`. The sidecar adds `ruc_added_units` and `ruc_start_usd` /
  `ruc_noload_usd` per cluster-day, so RUC make-whole is reported apart from DA make-whole. It is never priced.

### 2.4 Free parameters (rule 21)

**Zero.**

| field | type | default | values |
|---|---|---|---|
| `uc_reliability_commitment` | bool | off | requires `unit_commitment_milp` and `uc_commitment_demand_source="da_forecast"`; refused otherwise, because with `"actual"` it is a no-op |
| `uc_ruc_load_basis` | enum | `"actual"` | `"actual"`; `"iso_intraday_forecast"` (SPP MTLF vintage at the 4-h ID-RUC cycle, §2.2) added with its intake |

- The trigger tolerance reuses the LP's own feasibility tolerance. It is not a new constant.
- Penalties, window length, look-ahead, gap and time limit are the DA window's registered values.

### 2.5 Wall and memory (vs the ~70–75 min container lifetime, r16)

| term | SPP 2024 (U4 measured) | RUC addition (estimate) |
|---|---|---|
| P0 + UC-DA + P1a | 3,612 s (60 min) | — |
| RUC windows | — | ~16 trigger days + sweep ≈ 30–50 windows × 7–9 s ≈ 4–7 min |
| P1b | — | ≈ P1, 150 s |
| **total** | 60 min | **≈ 67–70 min: at the reclaim limit** |

- **Zero-trigger years cost nothing extra** (P1a is final).
- **Memory:** RUC windows are the DA windows' size, and P1b replaces P1a. Expected peak is about the U4 peak (8.44 GiB) plus the
  held P1a result (< 1 GiB), inside SPP's 10.6 GiB gate (r16 ruling 1).
- **Mitigation for 2024, requested as an owner ruling (§5 Q4):** read `u_DA` from the U4 leg's committed `uc_schedule_2024`
  when the run's `uc_input_digest` equals the one recorded in that leg's `uc_solve_log`. Digest equality certifies the same
  DA problem; in-process reuse (`_LAST_SOLVED`) already relies on it. That drops the 2024 leg to about P0 + P1a + RUC + P1b
  ≈ 15 min. It is cross-run reuse, so it needs a ruling. Without it, 2024 runs at the edge of the container's life, with the
  E9 monthly checkpoints as the stop artifact.

### 2.6 ISOs it applies to

- **Shared field, armed per run** (like `uc_commitment_demand_source`), on any UC ISO that commits on the DA forecast.
- **Expected to bind:**
  - **SPP:** 2024 only, on U4 evidence.
  - **NYISO:** DF below actual on 82–89 % of hours in every year, mean −0.30 to −0.45 GW. NYISO's own SCUC already carries a
    forecast-load commitment pass (§1).
  - **CAISO:** DF below actual 2021–25 (mean −0.18 to −1.56 GW). Gated on a rule-14 audit first: p5 reaches −6.3 GW in 2025
    and 363–364 days a year carry an hour below −1 GW, which looks like a basis drift in the CISO DF/demand pair rather than
    forecast error.
- **Expected near-inert:**
  - **MISO:** DF above actual on 78–95 % of hours.
  - **NEISO and ERCOT:** UC-DIAG measured peak DF bias ≈ 0.
- **Not applicable:** PJM, NWPP and SOCO run no UC arm.

## 3. Zero-LP evidence

### 3.1 SPP U4 (uc-1.7), per year: what the RUC would see

| year | DF − actual mean (MW) | under-forecast h | P1 trigger h / days | max uncovered need (MW)¹ | offline integer cap at trigger h, min (MW) | RUC effect |
|---|---|---|---|---|---|---|
| 2019 | +830 | 2,028 | **0 / 0** | 0 | — | identical to U4 |
| 2020 | +1,078 | 1,140 | **0 / 0** | 0 | — | identical |
| 2021 | +967 | 1,188 | **0 / 0** | 0 | — | identical |
| 2022 | +894 | 1,630 | **0 / 0** | 0 | — | identical |
| 2023 | +561 | 2,735 | not solved in U4 (held) | ? | ? | unknown |
| 2024 | **−239** | **5,516** | **39 / 16** | **1,305** | **2,889** | need/offline ≤ 0.45 in every hour |
| 2025 | +2,073 | 2,327 | **0 / 0** | 0 | — | identical |

¹ Need = the largest family shortfall (spin is nested in contingency, so families are not summed) plus energy slack. Trigger
hours: 35 reserve-short and 4 slack-only.

**2024 detail:**
- DF − actual at the 39 trigger hours: −0.63 to −3.17 GW, mean −2.02 GW, negative in **39 of 39**.
- The under-forecast alone exceeds the largest single-family shortfall in 39 of 39 hours, so a RUC on actual load sees every
  one.
- Trigger days: 04-13, 05-17, 06-10, 06-22, 06-28, 07-08…10, 07-22…23, 08-16, 08-25…26, 09-29, 10-03, 10-21.
- Daily maximum need sums to 6.9 GW-days.
- Offline capacity is nameplate `(n − u)·pbar`, not availability-adjusted, so it is an upper bound. The ≥ 2.2× margin makes
  outage unlikely to bind.

### 3.2 What the RUC would add (bounds, no LP)

Integer fleet 2024: CC 22 clusters (median `pbar` 256 MW, `mlf` 0.54, `ut_h` 16); coal 30 (445 MW, 0.40, 60 h); ST_GAS 31
(117 MW, 0.26, 54 h). Added floor energy ≈ Σ daily need × `mlf` × `max(ut_h, episode)`:

| if covered by | added floor energy 2024 | added unit-hours (order) |
|---|---|---|
| CC | ≈ 0.06 TWh | ~400 |
| ST_GAS | ≈ 0.10 TWh | ~1,500 |
| coal | ≈ 0.17 TWh | ~900 |

- Every case is ≤ 0.06 % of SPP load. The energy displaced at the floor is small.
- The price effect concentrates on the 16 days.
- RUC make-whole is bounded by the start and no-load of these units, at most a few $M, against U4 2024 uplift of $28.7 M.

### 3.3 Would it close the SPP 2024 failure? (no LP; the bundle's `system_2024` / `reserve_family_2024`)

| 2024, load-weighted P1 price | $/MWh | C3a vs the implied LW actual ($25.4) |
|---|---|---|
| U4 as solved | 37.55 | +47.6 % |
| reserve dual stripped on the 16 RUC days | 31.76 | **≈ +24.8 %** |
| reserve dual stripped in every hour | 29.59 | ≈ +16.3 % |
| control (keeper) | — | −11.2 % |

- **Scarcity: yes.** All 35 reserve-shortfall hours and the 169 MWh unserved sit on RUC days, with capacity to spare.
- **C3a: about half.** The RUC days hold 63 of the 101 hours above $200; the 39 trigger hours alone carry $6.3/MWh of the annual
  load-weighted mean (mean price there $1,096). What remains is
  roughly +16 to +25 %, above the ±10 % band.
- **The remainder** is a tight-but-not-short reserve adder on 3,231 h (mean $9.39/MWh load-weighted, against $3.10 in 2022 and
  $1.98 in 2025). A reliability RUC, faithfully, does not commit for that: there is no shortfall to avoid.
- **The lever behind both is one input:** 2024 is the only SPP year whose EIA-930 DF runs below actual on average (63 % of
  hours; every other year 13–31 %). Before the residual is called structure, the 2024 SWPP DF should be audited against SPP's
  own MTLF archive (rule 14; §5 Q2). A one-year sign flip of a BA's reported forecast is the kind of thing a reporting change
  produces.

### 3.4 Other ISOs (EIA-930 DF − actual, MW; QA cut not applied)

| ISO | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | UC-4 shortfall seen |
|---|---|---|---|---|---|---|---|---|
| NYISO mean | −446 | −304 | −412 | −399 | −324 | −430 | −379 | 2021–22: 0 MWh unserved (interim B) |
| CAISO mean | +586 | +124 | −179 | −416 | −525 | −1,089 | −1,555 | 2019–20: reserve dual $0 every hour |
| CAISO p5 | −813 | −926 | −1,290 | −2,299 | −3,025 | −4,867 | −6,306 | — |
| MISO mean | +2,313 | +1,962 | +1,316 | +1,961 | +2,083 | +1,593 | +1,471 | 2019–20: no shortfall reported |

- **NYISO:** a steady under-forecast. The RUC would trigger only where P1a goes short, and none has yet in the solved years.
- **CAISO 2023–25:** the negative tail is too large and too regular to be forecast error. Audit before any CAISO RUC arm.
- **UC-3 (uc-1.5)** committed on actual load, so it is not RUC evidence.

Reproduce (zero LP; `.venv`):
`python ruc_evidence.py docs/records/spp/ucmilp/data/ucmilp4_spp_u4_span SPP 2019,2020,2021,2022,2024,2025`. The script is
quoted in Appendix A. It reads `system_<y>`, `reserve_family_<y>`, `uc_schedule_<y>` and `uc_solve_log_<y>.clusters`, plus
`commitment_demand.ba_forecast_error_mw`.

### 3.5 Alternatives considered and rejected

| alternative | why not |
|---|---|
| Commitment demand = max(DF, actual) in the one DA pass | Undoes r13 ruling 1 on every under-forecast hour (5,516 h in SPP 2024). Commits economically, not for reliability. No RUC uplift attribution. |
| RUC window on every day | Exactly equivalent where P1a is clean: with a commitment-cost objective a feasible day adds nothing. Costs 2× UC wall, so SPP 2024 ≈ 110 min, past the container's life. |
| A reserve margin or commitment adder | A magic number tuned to a residual (rules 1, 5, 13). |
| Stochastic DA error draws | Out of scope; a forecast-uncertainty-layer question (§5 Q5). |

## 4. PRECOMMIT draft — UC-5-SPP, arm U5 = U4 + RUC

*(A draft. It becomes a PRECOMMIT only when a lane re-writes it at its pin, after the owner approves this design and the build lands.)*

- **Pin:** the build lane's engine string (uc-1.9 expected), full 40-char SHA. G-DRIFT vs `41cd55dc`: every hunk is LIVE only behind
  `uc_reliability_commitment`.
- **Control (rule 29(b)):** keeper `2026-10-03-closeout-spp-nuc-keeper`. **Comparator:** U4 (`ucmilp4_spp_u4_span`).
- **Recipe:** the U4 recipe verbatim plus `--set uc_reliability_commitment=true` and `--set uc_ruc_load_basis='"iso_intraday_forecast"'`
  (if owner Q5 = intake first; otherwise `"actual"`, declared as the upper bound). Zero DOF added.
- **Years:** all seven, one shard each, launched serially, gate 10.6 GiB (r16). If owner Q3 = yes: solve 2023 and 2024 only,
  and adopt 2019–22 / 2025 from the U4 legs on the zero-trigger identity. The adoption is checked by each U5 leg's `uc_solve_log`
  showing `ruc.trigger_hours = 0`, or, with no new legs, by the committed U4 sidecars (0 shortfall, 0 slack).
- **Predetermined under GATESPEC kill #3 (stated now):** U4's 2025 flips (C3b 0.153 → 0.220; C1 ST_GAS) are in a zero-trigger
  year. U5 therefore reads **R vs the keeper** whatever 2024 does. The structural readings below decide whether the RUC is a
  real mechanism for the D-6 card.

**Readings (bars = half the distance to target, GATESPEC §5 convention):**

| # | reading | U4 | bar |
|---|---|---|---|
| R1 | 2024 reserve-shortfall hours (any family) | 35 | ≤ 17 |
| R2 | 2024 unserved MWh | 169 | ≤ 84 |
| R3 | 2024 C3a | +47.6 % | ≤ +28.8 % (half-way to +10 %) |
| R4 | 2024 C3b | 0.625 | ≤ 0.413 (half-way to 0.20) |
| R5 | 2023 | not solved | reported: trigger h, shortfall h, C3a/C3b; no bar (no U4 value) |
| S1 | identity: years with 0 trigger hours | — | `uc_schedule` hash and P1 dispatch equal to U4 (S1 fail = kill) |
| S2 | RUC structure | — | reported: trigger h/days, swept windows, added unit-hours by class, added floor TWh (`uc_ruc` D-4 sub-row), RUC uplift $M and share, starts ÷ CEMS |
| S3 | add-only | — | `u_final ≥ u_DA` in every cluster-hour (fail = kill) |

**Kills (any ⇒ record and stop, no re-tune):**
1. An infeasible or time-limited RUC window.
2. S1 or S3 fails.
3. Unserved > control + 500 MWh in any year.
4. Non-determinism on a repeated leg.

A leg past the container's life or over the memory gate is a coverage stop, not a kill.

**Verdict for the structural question, fixed now:**
- **"RUC closes the DA-forecast seam":** R1 and R2 met, S1–S3 clean.
- **"RUC lifts the 2024 price fit":** R3 met.
- **Expected from §3.3:** R1, R2 and R3 met; R4 uncertain; C3a 2024 still FAIL.

**Wall row:** GATESPEC §6.1 plus RUC columns (trigger days, RUC windows, RUC s, P1b s).

### Matrix row proposal (text only; the build PR adds it with a cell in every shard, rule 28)

> `{ id: "uc_reliability_commitment", cat: "commit", name: "UC reliability-commitment (RUC) pass — add-only recommit of slow-start
> clusters on days the DA-forecast commitment leaves P1 short; commitment-cost objective; same MECH 28 bounds; make-whole sidecar",
> def: "scenarios.py uc_reliability_commitment (bool, default False; requires unit_commitment_milp and uc_commitment_demand_source=
> 'da_forecast') + uc_ruc_load_basis ('actual' | 'iso_intraday_forecast' = SPP MTLF vintage at the 4-h ID-RUC cycle). pipeline/uc.py: P1a → zero-LP screen (reserve
> shortfall or slack hours) → UcWindowModel re-solve of the triggered days with u ≥ u_DA, demand = RUC basis, dispatch cost ε,
> commitment cost = start + no-load + min-load energy, P1 penalties; forward sweep until the carried state rejoins the DA schedule →
> inject (MECH_UC_SCHEDULE) → P1b. Never prices (rule 4); RUC make-whole columns in uc_uplift; D-4 sub-row uc_ruc. Zero DOF.
> DESIGN-ucmilp-ruc-stage-2026-10-16.md.", mode: "B" }`
>
> Cells: every ISO `U`. SPP note: "§3 zero-LP: binds 2024 only (39 h/16 d)". CAISO note: "DF basis audit first".

## 5. Open questions for the owner

1. **Approve the design**: one RUC pass inside the UC stage, P1a-screened, add-only, commitment-cost objective, zero DOF.
   This also needs a wording change to CLAUDE.md's "No other pass is a MIP" (the RUC is a second MIP pass of the UC stage) and to
   spec §1.6. That belongs to a lane owning those files (rule 27).
2. **Audit the 2024 SWPP DF first?** Recommended, zero LP. Compare EIA-930 SWPP DF against SPP's MTLF archive for 2023–24. The
   research found DF ≈ the D-1 00:00 MTLF vintage for Jul–Dec 2024, so the audit is direct: does the MTLF itself under-forecast
   in 2024, or does only the EIA-930 report?
   If 2024 is a reporting change, the right fix is the DA basis (rule 14), and the RUC test shrinks to what genuinely remains.
   The same audit is needed for CAISO 2023–25 before any CAISO arm.
3. **Identity adoption.** May U5 adopt U4's 2019–22 / 2025 legs on the zero-trigger proof (2 solves) instead of re-solving all
   seven? A G-DRIFT-style INERT-with-reason argument, verified per leg. With the measured MTLF basis the zero-trigger proof is
   unchanged, because the trigger is P1a's shortfall.
4. **DA-schedule reuse across runs** by `uc_input_digest` equality (§2.5). It takes SPP 2024 from about 70 to about 15 min. Allow
   it, or keep rule 36's isolation strict and accept the reclaim risk on 2024?
5. **RUC basis.** Recommended: fund the SPP MTLF vintage intake (about 17 MB/yr, no login) before the arm, and run U5 on the
   measured basis. The same intake answers Q2, since the DF matches the D-1 00:00 vintage. The alternative is to run U5 now on
   realised load as a declared upper bound. Forward, the mean error profile makes the RUC near-inert for over-forecasting ISOs;
   day-level forward error is a forecast-uncertainty-layer item, not this lane.
6. **Order vs the other open SPP object** (ST_GAS under-commitment, UC-4 §8 item 1). The RUC does not touch it, and the 2025
   flips that fix U5's keeper verdict at R come from it.

## Appendix A — evidence script (scratch; not committed as a probe, rule on `scripts/probes/`)

```python
"""Zero-LP RUC evidence over a committed UC-4 slim span (no LP)."""
import json, sys
import numpy as np, pandas as pd
from market_sim.data.commitment_demand import ba_forecast_error_mw
D, iso = sys.argv[1], sys.argv[2]
for y in [int(v) for v in sys.argv[3].split(",")]:
    s = pd.read_parquet(f"{D}/hourly/system_{y}.parquet").query("`pass`=='P1'")
    rf = pd.read_parquet(f"{D}/hourly/reserve_family_{y}.parquet").query("`pass`=='P1'")
    sch = pd.read_parquet(f"{D}/hourly/uc_schedule_{y}.parquet")
    cl = pd.DataFrame(json.load(open(f"{D}/uc_solve_log_{y}.json"))["clusters"]).set_index("cluster")
    H = range(8760)
    slack = s.groupby("hour").slack.sum().reindex(H).fillna(0).to_numpy()
    fam_max = rf.groupby("hour").shortfall_mw.max().reindex(H).fillna(0).to_numpy()
    e, _ = ba_forecast_error_mw(iso, y)                      # DF - actual, model hours
    sch = sch.join(cl[["pbar_mw"]], on="cluster")
    off = ((sch.n - sch.u).clip(lower=0) * sch.pbar_mw).groupby(sch.hour).sum().reindex(H).fillna(0).to_numpy()
    need = fam_max + slack
    hrs = np.where(need > 1e-3)[0]
    print(y, np.nanmean(e), hrs.size, len(set(hrs // 24)), need.max(),
          off[hrs].min() if hrs.size else None, (np.maximum(-np.asarray(e)[hrs], 0) >= fam_max[hrs]).sum())
```
