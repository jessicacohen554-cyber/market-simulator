# FH-3 — as-known driver vintages for T1-FF Arm K (data intake)

**Session:** FH-3 of `docs/hindcast-forward-plan-2026-07.md` §6 (Wave FH), 2026-08-02.
**Scope:** DATA + CITATIONS ONLY. **No LP solved, no default changed, nothing registered on any
dashboard, no CI workflow added.** Branch `claude/fh-3-aeo2023-demand-vintages-dz38iq`, cut fresh
from `origin/main` @ `9950a5c`.

**Headline:** Arm K at base 2023 is **unblocked**. `hindcast_asknown_aeo2023` exists, cited to
AEO2023 Table 13; the standing NEEDS-CITATION gap on `hindcast_asknown_aeo2021` is closed by
**correcting** it (its old values match no basis of the AEO2021 series); and
`DEMAND_GROWTH_RATES_VINTAGES` is populated for **11 of 12** ISO-vintage cells from the editions
published at the time. One cell — **CAISO as-of-2021** — is a MANUAL DOWNLOAD (§4), left absent
rather than guessed.

Governance: this is rule-22 channel-1 data intake — **no-LP**, no solve, no scoring, no
registration. The holdout freeze is untouched. No out-of-training year is solved or scored; the
AEO and ISO load forecasts intaken here are forward projections, not measured actuals for a
solve/scoring year.

---

## 1. What landed

| Deliverable | File | Note |
|---|---|---|
| AEO2021 raw fuel prices (1,116 rows) | `data/raw/eia-aeo/eia_aeo2021_fuel_prices.csv` | gas + coal + oil + GDP deflator × 3 scenarios |
| AEO2023 raw fuel prices (1,044 rows) | `data/raw/eia-aeo/eia_aeo2023_fuel_prices.csv` | same |
| Fetch-script edition support | `scripts/data/fetch_eia_aeo.py` | `SCENARIOS_BY_AEO[2021/2023]`, GDP-deflator series, `default_start` |
| `hindcast_asknown_aeo2023` (NEW) | `config/fuel_trajectories.py` | unblocks Arm K base 2023 |
| `hindcast_asknown_aeo2021` (CORRECTED) | `config/fuel_trajectories.py` | rule 23 — cites the data |
| `DEMAND_GROWTH_RATES_VINTAGES` (NEW) | `config/constants.py` | 11/12 cells, FH-2's declared shape |
| Registry citations | `frontend/data/parameters.json`, `docs/parameter-citations.md` | 2 added, 2 repaired |
| Raw README | `data/raw/eia-aeo/README.md` | as-known section |

**FH-2 merged mid-session (PR #3278)**, shipping `DEMAND_GROWTH_RATES_VINTAGES = {}` plus
`ScenarioConfig.demand_growth_vintage` and `resolve_demand_growth_table` — mechanism only, values
explicitly left to FH-3. This branch was rebased onto that and **populates the same table**; no
second table was invented and no part of FH-2's mechanism was redesigned. FH-3's one change to
FH-2's code is the case-level refusal in §5, which the values themselves made reachable.

---

## 2. Gas — the as-known Henry Hub paths

### 2.1 The dollar-basis decision (the one judgement call here)

Both as-known entries carry **nominal $/MMBtu of each projection year**, not the AEO's published
real value. Converted with the **same edition's own projected** GDP chain-type price index
(AEO Table 20, series `eci_indx_NA_NA_gdp_NA_NA_y09eq1d3z`, 2012=1.000), rebased on that
edition's history year:

```
nominal(y) = real(y) × deflator(y) / deflator(edition history year)
```

Two reasons:

1. **Commensurability.** `hindcast_realized` is nominal spot ($3.91 in 2021, $2.54 in 2023 …) and
   the model's cost stack — VOM, offer curves, the 2023–2025 price benches — is nominal. Leaving
   Arm K in a stale real-dollar base would put a pure dollar-year shift inside the Arm R → Arm K
   spread, which plan §2.1 defines as *gas-forecast error*. The shift is not second-order:
   2020$ → nominal 2025 is **+7.6 %**, 2022$ → nominal 2025 is **+9.0 %**.
2. **As-of honesty.** The deflator used is the edition's own *projection* — all a forecaster had at
   the time. Using a realized deflator published later would leak post-base-year information into
   an ex-ante path (plan §4's as-of test).

The `low`/`mid`/`high` forecast paths above them keep the AEO's published real values, because
their edition's dollar year sits alongside the years they price. An as-known vintage is 2–5 years
stale by construction, so it cannot.

### 2.2 `hindcast_asknown_aeo2023` — NEW (AEO2023 Reference, published 2023-03-16, real 2022$)

Deflator base 2022 = 1.269200.

| year | real (2022$) | deflator | ratio | nominal | **landed** |
|---|---|---|---|---|---|
| 2023 | 5.266376 | 1.321666 | 1.041338 | 5.484077 | **5.48** |
| 2024 | 4.072381 | 1.353926 | 1.066755 | 4.344235 | **4.34** |
| 2025 | 3.489514 | 1.383368 | 1.089953 | 3.803405 | **3.80** |

2022 omitted per the rule-22 bridge (matching `hindcast_realized`).

**Sanity anchor** (not an input): AEO2023's own 2022 history value is 6.524 (2022$, ratio 1.0),
**1.6 % above** the realized 2022 Henry Hub annual average of $6.42 — confirming the deflator base
is the edition's history year and the rebasing is right.

**Read this honestly:** the as-known path is **2.2× the realized 2023 price** ($5.48 vs $2.54).
AEO2023 was frozen in late 2022 at the top of the post-invasion gas spike and did not see the 2023
collapse. That is the ex-ante driver error Arm K **exists to measure** — not a defect to reconcile,
and not a reason to substitute a better-informed vintage (rule 13).

### 2.3 `hindcast_asknown_aeo2021` — CORRECTED (AEO2021 Reference, published 2021-02-03, real 2020$)

Deflator base 2020 = 1.133393.

| year | real (2020$) | deflator | ratio | nominal | **landed** | *was* |
|---|---|---|---|---|---|---|
| 2021 | 3.100730 | 1.145347 | 1.010547 | 3.133434 | **3.13** | *3.07* |
| 2023 | 2.992324 | 1.174500 | 1.036269 | 3.100853 | **3.10** | *2.86* |
| 2024 | 2.801792 | 1.194232 | 1.053679 | 2.952188 | **2.95** | *2.88* |
| 2025 | 2.880324 | 1.219112 | 1.075630 | 3.098164 | **3.10** | *2.93* |

**Why corrected rather than cited (rule 23 — the change cites the DATA, never a residual).** The
prior values were flagged `NEEDS CITATION` in `parameter-citations.md` and match **no basis** of
the AEO2021 Reference series: not the published real 2020$ figures, not their nominal conversion,
not a uniform offset, and not a year-shift of either (checked: the closest coincidence,
old-2024 = 2.88 ≈ AEO-2025 = 2.880, does not extend to any other year). The old code comment's
claim that "2020$ ≈ 2026$ at this precision" is also wrong — that is a ~20 % drift, not a rounding
difference. Being unreconstructible, they are **replaced** by the API-fetched series rather than
back-cited.

**Consequence, stated because it is not free:** the two registered T1-H runs that used this path,
`ercot-2021-2025-asknown` and `pjm-2021-2025-asknown`, were produced on the old values and **no
longer reproduce at HEAD**. They stand as historical artifacts; any re-read of their
realized-vs-asknown spread must re-solve. Nothing was de-registered by this session.

### 2.4 Provenance

Both series are pulled from the EIA Open Data API v2 `aeo` route by
`scripts/data/fetch_eia_aeo.py --aeo-year 2021|2023` (Table 13 Henry Hub spot; Table 20 GDP price
index), landing immutable raw CSVs. Scenario ids `ref2021`/`ref2023` were verified against each
edition's own `facet/scenario` listing, not guessed. **Re-fetchable, forward-regenerating, rule-13
admissible.**

---

## 3. Demand-growth vintages

### 3.1 Construction rule (uniform; nothing is interpolated)

- **METRIC** = the edition's own published central **ANNUAL ENERGY** forecast for the ISO/planning
  footprint. Energy, not peak, because `_scale_demand` applies a **flat hourly scalar** — the
  model's growth rate *is* an energy growth rate and peak follows mechanically.
- **near** = CAGR from the edition's first forecast year to `DEMAND_GROWTH_TRANSITION_YEAR` (2030).
- **long** = CAGR from 2031 to the edition's last forecast year, **only** when the edition carries
  ≥ 3 post-2030 forecast years; otherwise **edge-held to near** and marked below.
- **CASES** = only what the edition publishes as a full low/base/high **series**.

### 3.2 The table

| vintage | ISO | case | near | long | source (edition · table) |
|---|---|---|---|---|---|
| 2021 | ERCOT | mid | **2.003 %** | 2.003 % † | 2021 LTLF, *Monthly Peak Demand and Energy Forecast 2021-2030* (2020-12-28) |
| 2021 | PJM | mid | **0.343 %** | 0.316 % | 2021 Load Forecast Report (Jan 2021), Table E-1 RTO net energy |
| 2021 | NYISO | low | −1.114 % | 0.542 % | 2021 Gold Book (Apr 2021), Table I-1a Energy-GWh |
| 2021 | NYISO | **mid** | **−0.375 %** | 1.038 % | ″ |
| 2021 | NYISO | high | 0.499 % | 2.148 % | ″ |
| 2021 | NEISO | mid | **1.073 %** | 1.073 % † | 2021 CELT (Apr 2021), Table 1.5.2 net annual energy |
| 2021 | MISO | mid | **1.173 %** | 0.965 % | 2021 SUFG/Purdue Independent Forecast (Nov 2021), Table 49 |
| 2021 | CAISO | — | **MISSING** | — | MANUAL DOWNLOAD, §4 |
| 2023 | ERCOT | mid | **2.433 %** | 2.433 % † | 2023 LTLF, *Monthly Peak Demand and Energy Forecast 2023-2032* (2023-01-18) |
| 2023 | PJM | mid | **1.564 %** | 1.104 % | 2023 Load Forecast Report (Jan 2023), Table E-1 |
| 2023 | NYISO | low | 0.379 % | 3.035 % | 2023 Gold Book (Apr 2023), Table I-1a |
| 2023 | NYISO | **mid** | **0.544 %** | 2.731 % | ″ |
| 2023 | NYISO | high | 1.838 % | 4.222 % | ″ |
| 2023 | NEISO | mid | **2.029 %** | 2.029 % † | 2023 CELT (May 2023), Table 1.5.2 |
| 2023 | MISO | low | 0.363 % | 0.567 % | 2023 SUFG/Purdue (Nov 2023), Table 86 (Low) |
| 2023 | MISO | **mid** | **1.016 %** | 0.713 % | ″ Table 49 (base) |
| 2023 | MISO | high | 1.615 % | 0.841 % | ″ Table 80 (High) |
| 2023 | CAISO | mid | **1.298 %** | 1.322 % | CEC CEDU 2022 STATE baseline (Jan 2023), Form 1.2 |

† long **edge-held** — the edition carries < 3 post-2030 forecast years. **This is not a modelling
risk:** T1-FF Phase A (2023–2025) and Phase B (2021–2025) solve no year past 2030, so `long` never
binds in any T1-FF window. It is carried for table-shape completeness only.

Source values (first-year / 2030 / 2031 / last-year, in the edition's own units) are recorded
inline against every cell in `constants.py`, so each number is checkable without this doc.

### 3.3 What this measures — the §4-row-6 BLOCKER, quantified

This is the point of the intake. The live `DEMAND_GROWTH_RATES` table is a 2025/26 vintage, and
`DEMAND_GROWTH_TRANSITION_YEAR = 2030` means **every historic year takes the `near` rate**:

| ISO | live near | as-of-2021 near | as-of-2023 near |
|---|---|---|---|
| ERCOT | **8.5 %** | 2.00 % | 2.43 % |
| PJM | **3.6 %** | 0.34 % | 1.56 % |
| MISO | **3.1 %** | 1.17 % | 1.02 % |
| NYISO | **1.8 %** | −0.38 % | 0.54 % |
| NEISO | **1.3 %** | 1.07 % | 2.03 % |
| CAISO | **2.8 %** | *(missing)* | 1.30 % |

ERCOT is the extreme case the plan called out: the live 8.5 %/yr compounded 2021→2023 is **+17.7 %**,
against **+4.0 %** on the as-of-2021 edition and roughly **+2 %** actual. A base-2021 T1-FF run on
the live table would have been reading a demand error larger than most of the effects it is meant to
measure.

The NYISO 2021 `mid` being **negative** is real and worth stating plainly: the 2021 Gold Book
forecast New York energy *declining* to 2030 on efficiency and codes, then rising on
electrification. It is not a sign-error.

### 3.4 Disclosed caveats

1. **Metric basis differs from the live table.** The live `DEMAND_GROWTH_RATES` is peak-CAGR-based
   for several ISOs; this table is energy-CAGR-based throughout (§3.1). The two diverge wherever an
   ISO's peak and energy diverge under electrification — the live NEISO block already flags exactly
   this. **No T1-FF comparison is affected**, because plan §2.1 puts *both* arms on the vintage
   table; the live table is not in the T1-FF read at all. Flagged for FH-4 so the difference is not
   mistaken for a vintage effect if a T1-FF number is ever set beside a T1-F number.
   Related, and worth a separate look: the live NEISO `mid` of 1.3 %/yr is described as a blend of a
   1.0 % energy CAGR and a 2.6 % winter-peak CAGR, but **no blend weight is stated**, so that cell
   is not reproducible from its own comment. Not fixed here (out of scope, and rule 23 forbids
   touching it without a source-data change) — recorded as an open docs/derivation gap.
2. **MISO editions are published inside their base year** (Nov 2021 / Nov 2023) — the latest-published
   drivers here. A November publication already "knew" most of its base year. The effect on a T1-FF
   run is small because the growth factor at the base year is ≈ 1 and the rate only compounds
   forward, but it is a genuine as-of imperfection. The strictly-clean alternatives (the Nov-2020
   and Nov-2022 SUFG editions) are reachable at the same URL pattern and are listed in §4 as an
   optional tightening, not a blocker.
3. **CAISO footprint.** The CEC forecast is **statewide**; the model's CAISO carries ~80 % of
   California load. The statewide growth *rate* is used as the CAISO proxy — the same approximation
   the live CAISO block makes.
4. **Most cells carry `mid` only.** Only NYISO (both vintages) and MISO 2023 publish a full
   low/base/high series. Transporting the live table's band width onto a vintage central would be
   inventing a growth rate no edition published, which the brief explicitly forbids. See §5.2.

---

## 4. MANUAL DOWNLOADS NEEDED

| # | Item | Why it is needed | Where it was looked for |
|---|---|---|---|
| **M1** | **CEC California Energy Demand STATE baseline forms, 2020/2021 vintage** (CED 2019 Revised, CEDU 2020, or CED 2021-2035 — whichever the CEC treats as adopted-and-current at Jan 2021) | The **only missing cell**: `DEMAND_GROWTH_RATES_VINTAGES[2021]["CAISO"]`. Blocks CAISO in **Phase B** (base 2021) only; Phase A (base 2023) is complete. | `energy.ca.gov` planning-library `demand-side-0/-1` pages list only CEDU 2022 and CED 2023+; the 2020/21-vintage forms are not linked from the current pages. Likely retrievable from the CEC eFiling docket by `tn=` once the transaction number is known. |
| M2 | *(optional)* MISO SUFG Independent Forecasts, **Nov-2020** and **Nov-2022** editions | Tightens §3.4 caveat 2 — removes the inside-the-base-year publication date for MISO. Not a blocker. | Reachable at `purdue.edu/discoverypark/sufg/.../MISO-forecast-report-<yr>.pdf`; the 2021/2022/2023 editions all resolved, so 2020 very likely does. Not pulled because the current cells are already edition-sourced. |
| M3 | *(optional)* Published low/high **series** for ERCOT / PJM / NEISO / CAISO in these vintages | Would let the `low`/`high` cases be filled from published scenarios instead of left absent (§5.2). | ERCOT's 2021 scenario file is a **weather**-year spread, not an economic low/high; PJM's report publishes 90/10 *weather* extremes only; ISO-NE CELT publishes a central case. A genuine economic band may exist in each ISO's supplementary forecast materials. |

**Nothing above was interpolated, back-filled, or approximated.** M1 is left absent in the table
rather than seeded from the CEDU 2022 vintage, which would be a post-base-year leak.

---

## 5. A silent fallback the values made reachable — found and closed

Landing values into FH-2's mechanism exposed a live gap in `resolve_demand_growth_rate`
(`config/scenario_resolvers.py`). FH-2 refuses an unknown **vintage** and a missing **ISO**, but
the **case** axis fell through:

```python
path_rates = iso_rates.get(config.demand_growth_path)
if not isinstance(path_rates, dict):
    return config.demand_growth_rate      # <-- 1 %/yr scalar default
```

While the registry was empty this was unreachable. It is not unreachable now: most vintage cells
carry **`mid` alone** (§3.1 — no edition-published low/high series, and inventing a band would
breach rule 5), so a perfectly ordinary `--demand-growth-path low` run against
`(2021, "PJM")` **silently returned 0.01/yr** — a number no edition ever published, answering an
as-of question with today's scalar default. Demonstrated before the fix:

```
PJM 2021 path=mid   -> 0.0034
PJM 2021 path=low   -> 0.01   ← silent
PJM 2021 path=high  -> 0.01   ← silent
```

That is the same leak class the seam exists to close, so it is fixed rather than documented: a
missing case inside a present `(vintage, ISO)` now **raises**, naming the case and the cases on
offer, exactly parallel to the missing-ISO refusal. The non-vintage lane is untouched — with
`demand_growth_vintage=None` the scalar fallback still applies, byte-identical, and FH-2's
`test_default_rate_unchanged_by_the_seam` still passes.

Two FH-2 tests asserted the pre-FH-3 state and were updated, not deleted:
`test_registry_ships_empty_at_fh2` → `test_registry_populated_by_fh3` (per its own instruction,
*"if this ever fails, the values landed"*), now shape-checking every cell; and
`test_unknown_vintage_raises_at_config_build`, whose probe year was 2021 — a **real** vintage since
this intake — retargeted to 2019 so the guard keeps its meaning. Four tests added: the landed
vintage builds and resolves, the missing-case refusal, the published NYISO band still interpolates
(including its negative central near rate), and no vintage cell inherits the live table's value.
**32 passed** in that suite; **465 passed** across `tests/unit/config/` + the T1-FF harness suite.

Still open for FH-4, unchanged by this: **`(2021, "CAISO")` is absent entirely** and raises as a
missing ISO until M1 lands.

---

## 6. Coal / oil (plan §4 row 8) — data landed, consumption still blocked

**The data is no longer the obstacle.** Both editions' coal and oil series came down with the gas
pull and are on disk in the same raw CSVs:

| series | AEO2021 (real 2020$) 2021→2025 | AEO2023 (real 2022$) 2023→2025 |
|---|---|---|
| coal delivered to electric power ($/MMBtu) | 1.991 → 1.894 | 2.057 → 2.037 |
| coal minemouth average ($/MMBtu) | 1.529 → 1.493 | 1.836 → 1.972 |
| oil, electric-power distillate ($/gal) | 2.437 → 2.500 | 4.525 → 3.834 |
| oil, electric-power residual ($/gal) | 1.325 → 1.894 | 2.782 → 2.609 |

**The degeneracy is confirmed and is a *mechanism* problem, not a data problem.**
`resolve_annual_coal_price` (`data/fuel/trajectories.py:146-151`) computes
`growth_ratio = value(year) / value(min(trajectory))`, and `COAL_PRICE_TRAJECTORIES` starts at
**2025**, so for any year ≤ 2025 `_hold_flat_extrapolate` returns the 2025 knot and the ratio is
**exactly 1.0** → flat `COAL_PRICE_BASE[iso]`. Same shape for oil.

**Why FH-3 stops here, deliberately.** Adding pre-2025 knots to the existing dicts would move
`anchor_year` and therefore rescale **every forecast year 2026-2050** — a default change, which this
session is forbidden to make. The correct fix mirrors gas: a separate
`hindcast_asknown_aeo<yr>` coal/oil path plus a `coal_price_path` / `oil_price_path` hindcast
selector in the harness. That selector **does not exist**, so landing the constants now would create
dead tables. It is a small, well-specified follow-up for FH-2 (mechanism) once the value is wanted —
the raw data it needs is already committed and cited.

**DISCLOSE line for plan §4 row 8, until then:** *coal and oil prices in every T1-FF year resolve to
the flat per-ISO `COAL_PRICE_BASE` / `OIL_PRICE_PER_MMBTU` level and carry **zero historic signal**.
Any T1-FF result is therefore conditional on coal- and oil-price error being immaterial to it; for
coal-heavy ISOs (MISO, PJM) that assumption should be checked before a headline skill number is
quoted. The AEO2021/AEO2023 coal and oil series are on disk and cited — only the resolver is
missing.*

---

## 7. Verification performed

- `tests/unit/config/` + `tests/scoring/test_full_forward_hindcast.py`: **465 passed, 18 subtests**
  (post-rebase onto FH-2). FH-2's own contract suite `test_fh2_as_of_channels.py`: **32 passed**.
- The Arm-K refusal test was **retargeted, not deleted**: it now asserts base **2022** (a year with
  no intaken vintage) still hard-errors, and a new test asserts base 2023 resolves. The guard keeps
  its coverage after the intake.
- `scripts/check_mechanism_matrix.py`: integrity OK, keeper stamps match.
- `scripts/validate_parameters.py`: the new constant is covered; the pre-existing missing-citation
  count went **48 → 47** (main's own backlog is untouched otherwise) and both warning counts are
  unchanged from baseline (83 unmatched / 105 value-mismatch), i.e. this session added no registry
  noise.
- Rule 27 blob verification after every push touching a file ≥ 300 lines
  (`fuel_trajectories.py`, `constants.py`, `fetch_eia_aeo.py`, `test_full_forward_hindcast.py`,
  `parameter-citations.md`): local hash + line count compared against the pushed blob. All matched.

## 8. What this session did NOT do

- No solve, no score, no dashboard registration, no PR.
- No default changed. `DEMAND_GROWTH_RATES_VINTAGES` is inert until FH-2's field reads it; the
  corrected `hindcast_asknown_aeo2021` is reachable only through `--arm asknown`.
- No `ScenarioConfig` field, no cache-key entry, no mechanism-matrix row — all FH-2's, and all
  landed in PR #3278. The one resolver change is the case-level refusal in §5, which is a
  fail-closed guard on FH-2's existing seam, not a new mechanism.
- No CI workflow, no GitHub-Actions job.
- FH-4 / Phase A remains **BLOCKED** on the separate §3.3 harness-defect gate (I6 over-retirement,
  26.8 % of prior thermal in 2025). That is a retirement-lane defect and is untouched here. What
  this session changes is that when that gate lifts, **Arm K no longer blocks with it.**
