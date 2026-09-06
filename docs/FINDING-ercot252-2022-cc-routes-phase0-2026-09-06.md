# FINDING — ERCOT 2022 C1 / CC_REGULAR: the two in-model routes are KILLED at zero-LP phase 0; the measured 2022 load-resource RRS series is BUILT (ercot-252, 2026-09-06)

> Status: RECORD of a rule-22 `[R-HOLDOUT]` touchpoint-loop step-2 diagnosis plus a data
> intake. **No LP was solved. No run was registered. No parameter, recipe, keeper, marker
> or determination changed. Nothing was identified on 2022.** Every number below is read
> from committed artifacts (`results/calibration/ercot250_2022_touchpoint_carveout/`), from
> the raw 60-Day DAM Disclosure files on disk, or from the series this session built.
> The locked test (2019 / H1-2026) was not touched.
>
> Keeper at measurement: `2026-09-05-ercot248-two-config-keeper` (unchanged). Touchpoint on
> the site: `2026-09-05-run250-2022-touchpoint-carveout`, folded into the keeper (unchanged).

## 0. The object, restated once

The 2022 validation touchpoint fails C1 on one class: **CC_REGULAR 121.693 vs 132.087 TWh
= −10.39 TWh** against a ±8.00 TWh band (share −2.36 pp, inside ±3 pp), so the gap to close
is **+2.39 TWh** of CC_REGULAR. Established by ercot-249/250/251 and not re-derived here:
the miss is an input gap (the absent 2022 HSL archive ⇒ a `forecast_uncurtailed` bound
grossed up ×1.076 / ×1.079 with both curtailment ceilings self-disabled ⇒ **+6.419 TWh**
net renewable excess displacing thermal one-for-one at a measured CC_REGULAR capture of
0.555); the in-sample CC_REGULAR sign is positive in all three training years; the
predicate repair was screened on 2023 and killed on C3a; the HSL archive is ungettable from
this environment. This session was chartered to work the remaining routes in order.

## 1. Result in one table

| route | class | what this session did | verdict |
|---|---|---|---|
| **R1** HSL 2022 upload | owner-side data | not re-attempted (the 2026-07-10 README record stands; this container carries no ERCOT credential) | **OPEN — owner action**, still the only route that closes C1 without a trade |
| **R2** provenance-predicate repair | owner decision | not armed | **OPEN — owner decision** (`RESULT-ercot251` §6) |
| **R3** `ercot_load_resource_reserve` on 2022 | data intake + recipe gate | series **BUILT** (§3); rule-29 phase-0 on the committed sidecar (§2) | **KILLED as a C1 route** — energy footprint ≤ 0.194 TWh vs 2.39 needed; lowers the C3c tail |
| **R4** `ercot_reserve_supply_cap_from_year` 2023 → 2020 | recipe gate | rule-29 phase-0 (§2.3) | **KILLED as a C1 route** — energy-inert by construction; a C3c/C3a recipe question, put to the owner |
| **R5** training-window CC root cause | — | not opened (ESTABLISHED #2) | — |

**Net:** with R3 and R4 eliminated at zero LP, **every route that can move 2022's C1 is the
renewable bound** — R1 or R2 — and both are the owner's. No solve was spent establishing
this, and none should be until one of them is decided.

## 2. Zero-LP phase 0 (rule 29 `[R-SCREEN]` clause 0) — why neither reserve lever can reach C1

### 2.1 The instrument

The committed `hourly/reserve_family_2022.parquet` of the folded touchpoint carries, per
reserve family and hour, the balance-row **dual**, the requirement, the held MW and the ORDC
shortfall. An LP row whose dual is zero has zero marginal cost of reserve in that hour:
lowering its right-hand side changes the objective by nothing and the energy dispatch only
among cost-degenerate alternatives, which leave class-level energy totals unchanged. So a
requirement credit can move class energy **only in the hours the row's dual is positive**,
and the credited MW summed over those hours is a hard upper bound on the energy it can
re-dispatch. That bound is computable before any solve — which is what rule 29 clause 0
asks for — and it is scored against the object's own arithmetic, never against a residual.

### 2.2 R3 — the load-resource RRS credit

The 2022 reserve rows are slack almost all year:

| family | requirement mean MW | held mean MW | hours dual > 0 | hours dual > $0.5 | hours dual > $5 | dual p99 | shortfall hours | shortfall GWh |
|---|---|---|---|---|---|---|---|---|
| `ercot_ordc_total` | 10,700 | 10,665 | **199** | 73 | 34 | $0.15 | 199 | 310.5 (max 5,217 MW) |
| NonSpin | 3,898 | 4,597 | 8 | 8 | 8 | $0.00 | 8 | 8.6 |
| RRS_withheld | 2,863 | 3,479 | 8 | 8 | 8 | $0.00 | 0 | 0 |
| RegUp_withheld | 359 | 1,427 | 8 | 8 | 8 | $0.00 | 0 | 0 |
| ECRS | 0 | 1,162 | 1 | 1 | 1 | $0.00 | 0 | 0 |

Union of hours with any family's dual above $0.5: **73**; above zero: **199**.

Overlaying the measured 2022 load-resource RRS series built in §3 (mean 1,042 MW) on those
hours:

| binding set | hours | Σ LR credit over the set | as a share of the 2.39 TWh gap |
|---|---|---|---|
| total-family dual > 0 | 199 | **0.194 TWh** (mean 976 MW) | 8.1 % at 100 % capture |
| total-family dual > $0.5 | 73 | 0.071 TWh | 3.0 % |
| total-family dual > $5 | 34 | 0.034 TWh | 1.4 % |

At the measured 0.555 CC_REGULAR capture the reachable move is ~0.11 TWh — **an order of
magnitude short of the 2.39 TWh the band needs**, with the whole 8,561-hour remainder
provably inert. The arm does not reach a solve.

**Its C3c direction is wrong as well.** The credit lowers the total-family requirement, so it
removes shortfall: Σ min(LR, shortfall) over the 199 shortfall hours is **148.8 of 310.5 GWh**,
and 77 of the 199 hours are covered in full. The touchpoint already under-produces the tail
(64 h vs 196 h actual, RT > $200); arming the credit on 2022 would push it lower. This is the
same direction the field's own docstring records for the training years, where it is a
correction to an over-tight co-opt — in 2022, with the supply cap off (from_year 2023), the
co-opt is not tight, and there is nothing for the credit to correct.

### 2.3 R4 — the RTOLCAP reserve-supply cap

`ercot_reserve_supply_cap` adds rows capping **held** reserve at the measured on-line
responsive capability. The cap can only lower the reserve the LP counts; it forces no headroom
and no commitment, and a cap below the requirement is relieved by nothing the LP can do —
the difference is priced by the ORDC as shortfall, not redispatched. Its energy footprint is
therefore zero by construction outside the hours the reserve rows bind, and inside them it is
bounded by the same class of number as §2.2. **It is not a C1 route.**

What it IS, measured on the committed 2022 RTOLCAP series (mean 11,432 MW, min 3,161):

| quantity | 2022 | 2023 (for scale) |
|---|---|---|
| hours RTOLCAP < the 10,700 MW total requirement | **4,149** | 2,862 |
| hours RTOLCAP + RTOFFCAP < 10,700 | 800 | — |
| Σ (requirement − RTOLCAP)⁺ | **9,779 GWh** | — |
| touchpoint's current ORDC shortfall | 310 GWh over 199 h | — |
| measured RTORPA > 0 / > $50 / > $200 hours | 2,696 / 152 / 53 | 1,705 / — / — |

Arming the cap on 2022 would put the ORDC on the curve in roughly half the year, against a
touchpoint that is short in 199 hours. That is a **price-formation** change aimed at the C3c
object (ercot-249 §3: the model selects the scarce hours and prices them at nothing) — exactly
what ercot-249 §4 already raised as an owner recipe decision. This session adds the magnitude
and stops: the from_year was set on a premise the data contradicts (the series exists back to
2020, verified again), rules 14 and 22 both point at arming it, its only live years are all
held out, and it therefore **cannot be screened without spending 2022**. Owner call, unchanged.

### 2.4 Screen year, drift audit, control — not applicable

No arm reached a solve, so no PRECOMMIT, screen year, G-DRIFT hunk audit or control was
required. For the record: the keeper's and touchpoint's solve shas (`0207d69`, `17ab9e5`,
`49647dd6`) do not resolve in this clone (the 2026-08-16 history rewrite), so a hunk-level
G-DRIFT audit would not have been performable here either way; the phase-0 above is scored
against the committed sidecar and against measured series, which no drift can move.

## 3. Data intake — the measured 2022 (and 2020, 2021) load-resource RRS series

Rule 22's own clarification governs: *what is held out is the score, never the data* — a
measured input belongs in every year and needs no authorization to prepare. R3's data gap is
now closed; whether a solve consumes it is the `ercot_load_resource_reserve_from_year` recipe
gate, which this session did **not** touch (§4).

### 3.1 Source — better than 2023's, not worse

The 60-Day DAM Disclosure **Load Resource Data** files
(`data/raw/ercot-AS/60d_DAM_Load_Resource_Data_{2018..2022}.parquet`, owner drop landed
2026-09-06) carry the per-Load-Resource cleared DAM **awards** — not offers. The 2023 series
had to be a measured-shape / cleared-level hybrid because only the *offers* file exists for
2023; for the back years the load-side Responsive Reserve is read directly off the awards.
Generator `RRSUFR Awarded` is 0 in every 2022 file (verified), so the load-resource total is
the whole product.

Two facts of the source the builder handles explicitly:

* **Posting-year keying.** Each file spans deliveries Nov 2 (Y−1) .. Nov 1 (Y); a delivery
  year needs the Y and Y+1 files. Delivery 2018–2021 are fully covered. Delivery **2022
  Nov 2 – Dec 31** (1,441 h, 16.4 %) is not — the posting-year-2023 Load Resource file is not
  in the repo, though the Gen Resource half of that same disclosure is (`data/raw/ercot/`).
* **The RRS split.** `RRS Awarded` is the only RRS column until **2022-10-14**; from
  **2022-10-15** both the Gen and Load Resource files carry `RRSPFR/RRSFFR/RRSUFR Awarded`
  instead (Gen PFR turns on the same day). Pre-split the LR award is undifferentiated;
  post-split the LR PFR share is ~4 % (Oct 15 – Nov 1: UFR ~976 MW, PFR ~40 MW). The series
  carries the **LR RRS total** across the split so 2022 is internally consistent, at the cost
  of a ~40 MW definitional difference from the UFR-only 2023+ series. Stated, not hidden.

### 3.2 The one reconstructed window — 2022 Nov 2 – Dec 31

Filled by the measured residual identity `LR_RRS(t) = ASPLAN_RRS(t) − gen_RRS_awards(t) −
offset`, with `offset` the within-year mean of `(plan − gen − LR)` over the **7,319 covered
2022 hours = 753.1 MW** (the self-arranged / un-awarded RRS share; corr(plan − gen, LR) =
**0.921**; monthly offsets 704–829 MW, i.e. stable). No parameter is chosen against any model
residual — two measured sources are reconciled inside the same year, the same class of
construction the 2023 series documents for its Oct 2 – Dec 9 gap. Check: the reconstructed
tail averages 1,106 MW against 1,029 MW for the covered post-split Oct 15 – Nov 1 window, and
its hour-of-day shape correlates 0.80 with that window's. The parquet metadata records the
window, the offset, the covered-hour count and the correlation.

### 3.3 What was written

| file | `rrsufr_mw` mean / min / max (MW) | covered h | reconstructed h |
|---|---|---|---|
| `ercot_2022_as_up_mw.parquet` | **1,042** / 227 / 1,430 | 7,319 | 1,441 (§3.2) |
| `ercot_2021_as_up_mw.parquet` | 562 / 30 / 1,001 | 8,760 | 0 |
| `ercot_2020_as_up_mw.parquet` | 595 / 241 / 898 | 8,760 | 0 |

2022 monthly means (MW): 1,129 · 1,164 · 1,266 · 1,191 · 1,076 · 932 · 792 · 804 · 916 ·
1,030 · 1,182 · 1,033. For scale, the committed 2023 / 2024 / 2025 series average 884 / 904 /
787 MW. Other columns (`regup_mw`, `nspin_mw` from ASPLAN 2022; `rrspfr_mw` the generator
awards; ECRS/NSPNM zero) are schema parity and consumed by nothing.

Builder: `scripts/data/build_ercot_as_backyear.py` (default `--year 2020 2021 2022`; 2018 and
2019 are one flag away and were deliberately not built here — they are locked-test-tier
years and their preparation belongs with the `final` declaration, though rule 22 permits it).
Clock: the same `prevailing_he_to_cst` / `_prevailing_to_standard` conversions the 2023–2025
builders use. Tests: `tests/iso/ercot/test_ercot_as_backyear.py` (split continuity, CPT→CST
placement, the reconstruction rule, the no-plan zero-fill).

## 4. What this session did NOT do, and why

* **No `from_year` was changed.** The carve-out recipe carries `ercot_load_resource_reserve
  = True, from_year 2023` and `ercot_reserve_supply_cap = True, from_year 2023`. Moving either
  to 2022 is byte-identical in every training year and live only on held-out years, so it can
  neither be identified on 2023–2025 nor screened where its footprint is largest without
  spending 2022 — the same governance shape as R2. §2 shows the C1 case for doing so is
  empty anyway; the C3c case for R4 is the owner's.
* **No 2022 re-solve, no registration, no re-stamp**, so rule 30(a)'s duties are not
  triggered; the site still carries exactly one 2022 run.
* **R1 was not re-attempted.** The handoff and the README both say not to as a first move;
  `env` carries no ERCOT credential; nothing about the access wall has changed since
  2026-07-10.
* **No mechanism-matrix verdict changed.** The LR credit and the cap are sub-scalars of the
  `ercot_multiproduct_as` row (nyiso-121 census convention); the ERCOT shard's evidence string
  for that cell now cites this phase-0. Cell stays `K`.
* Rule 30(c): ERCOT's determination is the train-tier verdict, **CALIBRATED**, untouched.

## 5. Put to the owner — the three open decisions, in the order they close the object

1. **R1 — the 2022 HSL archive** (NP4-732-CD / NP4-737-CD, or NP4-742/745 GEO) dropped into
   `data/raw/ercot-hsl/np6/2022/`, then `build_ercot_hsl.py --year 2022` and a touchpoint
   re-solve. Zero DOF, no trade, closes C1 by the arithmetic of ercot-251 §3.
2. **R2 — admit the provenance-predicate repair or not** (`RESULT-ercot251` §6: as a
   correctness fix despite the price cost / leave as-is / admit and route the price
   consequence to the C3c price-function work). If admitted: re-apply, re-solve 2022, report
   C1 and C3a together.
3. **R4 — `ercot_reserve_supply_cap_from_year` 2023 → 2020**, now with its magnitude: the cap
   binds in 4,149 of 8,760 hours in 2022. A C3c/C3a decision, not a C1 one; and, if taken,
   whether `ercot_load_resource_reserve_from_year` moves with it (the ercot-212 `net_credits`
   pairing nets the LR series off the cap rows, so the two are one recipe decision, not two).

## 6. Provenance

Session ercot-252, 2026-09-06, branch `claude/ercot-cc-regular-gap-h1y3am`. Companion
records: `docs/FINDING-ercot249-250-2022-touchpoint-2026-09-05.md` (+ Addendum 1),
`docs/FINDING-ercot251-nohsl-curtailment-gate-2026-09-06.md`,
`docs/RESULT-ercot251-nohsl-ceiling-screen-2026-09-06.md`,
`docs/handoffs/holdout-2022-completeness-ercot-nyiso-2026-09-05.md` §2,
`data/raw/ercot-AS/README.md` (back-year series section), `docs/calibration-log/ercot.md`
(ercot-252).
