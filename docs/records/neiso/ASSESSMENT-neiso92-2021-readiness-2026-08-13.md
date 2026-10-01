# ASSESSMENT — NEISO 2021 validation-touchpoint readiness

**Session:** neiso-92 (the prompt said "neiso-89"; that shorthand is TAKEN —
`ASSESSMENT-neiso89-final-prereqs-2026-08-07.md`, plus neiso-90 and neiso-91 are on the record.
Renumbered to the next free ordinal so the citation chain stays unambiguous.)
**Date:** 2026-08-13 · **HEAD:** `cfb8127` · **Branch:** `claude/neiso-2021-readiness-7pzqo9`
**Recipe under test:** `2026-08-06-neiso-87-control` (bundle `results/calibration/neiso87_control_A`)
**Scope:** Phase 1 ONLY — data readiness. **NO LP was constructed. NO year was solved, scored or
registered.** Rule 22 channel 1 (data readiness) is unrestricted by the holdout spend freeze.

---

## VERDICT: **NOT CLEAN — DO NOT SOLVE 2021.**

Four inputs are **DEGRADED** against the 2022–2025 standard. One of them — **nuclear availability**
— is severe enough on its own to reproduce the neiso-85 failure mode: a single absent measured input
that would dominate the monthly price residual with the correct sign, so the spend would measure a
data gap rather than forecast skill.

**The two inputs the prompt flagged as highest-risk both came back CLEAN.** The 2021 demand profile
is a dense, real 8760, and the gas basis is fully on the measured ISO-NE index with a correctly
winter-peaking shape. The blocking gaps are elsewhere, and were not on the prompt's list.

**All four gaps are FIXABLE with data prep alone** — every upstream source exists on disk. Under rule
22 as amended 2026-08-06 ("what is held out is the SCORE, never the DATA"), that prep needs **no
owner lift and no marker**: it is unrestricted, applies to every year 2019–2025 alike, and is the
work that must precede the spend.

---

## 1. Gate state (verified at HEAD, not assumed)

| Gate | State | Evidence |
|---|---|---|
| Holdout spend **freeze** | **ACTIVE** | `frontend/data/backcast/holdout-freeze.json` `active: true`, declared 2026-07-25, re-armed 2026-08-06 after the narrow neiso-86 lift. Outranks every marker. |
| Tier of 2021 | **validation** | `scripts/lib/holdout_policy.VALIDATION_YEARS = {2020, 2021, 2022}` |
| NEISO `complete` marker | **held** | `calibration-complete.json` `complete.NEISO`, declared 2026-07-07, `keeper` re-keyed to `2026-08-06-neiso-87-control` |
| NEISO `final` marker | **absent** | `final` block holds only `_note`. NEISO's locked test is **NEVER GRANTED** (owner decision D-23), not spent. **Untouched by this session.** |

So 2021 is marker-authorized but **freeze-refused**. Phase 2 requires an explicit owner lift naming
this spend. **This assessment recommends NOT requesting that lift yet** — see §5.

**On the keeper identity.** The prompt anticipated a neiso-88 combined 2022–2025 keeper bundle. **It
has not landed**: the registry holds exactly two NEISO runs (`2026-08-06-neiso-87-control`,
`2026-08-06-neiso-2022-corrected-basis`), the keeper shard still designates the former, and the log's
last entry records the combined bundle as blocked by this same freeze. Per the prompt's fallback,
`2026-08-06-neiso-87-control` is the recipe under test.

---

## 2. The readiness table

Graded against the **2022–2025 standard**, not against "exists". Row counts, ranges and provenance
are measured at HEAD this session.

### 2.1 EQUIVALENT — 2021 matches the tuned years

| Input | Evidence | Grade |
|---|---|---|
| **Demand** `eia-930/eia_demand_profiles.parquet` | NEISO 2021: **8760 rows, 0 NaN, 0 zeros, 0 duplicate hours**, hours 0–8759, mean 13,377 MW, 5,477 distinct values, `normalized` sums to 1.000119 (2022 1.000056 / 2023 1.000108 / 2025 1.000221). Dense and real, **not** partial or backfilled. See §3.1 for the one artifact hour. | **EQUIVALENT** |
| **Gas basis** `gas_basis_by_iso_month.csv` | 2021 is **12/12 months on the measured ISO-NE MA gas index**, each row carrying its own `isonewswire.com` monthly-recap URL. **Zero proxy rows** — no `N3050MA3`. (2018 is the known MIXED year, 8 measured + 4 proxy; 2015–2017 fully proxy.) Graded hardest per the prompt; see §3.2. | **EQUIVALENT** |
| **EIA-923 monthly gas** (delivered-fuel level) | Same-recipe reproduction on the keeper's own config: **12/12 months with receipts** in 2021, identical to every tuned year. Hub overlay covers **8760 h = 100.0 % of the year**, identical to every tuned year. | **EQUIVALENT** |
| **LMP actuals** `_validation-source/actual_lmp_hourly_NEISO.parquet` | 2021: 8760 rows, **1 NaN** in `rt` and `da` — the same 1 NaN the tuned year 2023 carries (2018–2023 all carry 1; 2024/2025 carry 0). 0 duplicate hours. RT range −42.31 … 375.28, mean 44.84. Clock verified in §3.3. | **EQUIVALENT** |
| **Unit outage windows** `campd-unit-outages-NEISO.csv` | Single file, **one uniform 2018-01-01 → 2026-12-31 detector pass** (not a stale per-year derive). 2021: **397 windows / 32 units / 35 plants / 2,228,524 MW-days / median 12.2 d / mean 26.2 d**, 0 null `plant_group`. Tuned band: 2022 340/1.97M/12.5 d, 2023 367/2.18M/15.1 d, 2024 317/1.88M/10.5 d. 2021 sits naturally in a monotone declining series. `capacity_source` mix in family. | **EQUIVALENT** |
| **Plant emission rates** `plant_emission_rates_v2.parquet` | NEISO 2021: **187 rows / 78 plants**, 145 `measured` + 42 `heat_backfilled` = **77.5 % measured**. Tuned years 78.8 / 79.3 / 78.4 / 78.2 %. Row count sits in the monotone 189 (2018) → 156 (2025) fleet decline. | **EQUIVALENT** |
| **Renewable capacity** `_validation-source/NEISO_2021_renewable_capacity.csv` | Exists. **121 lines — byte-identical row count and schema to 2022/2023/2024/2025.** Wind North 1,320.3 MW (2021) → 1,481.6 MW (2025), sensible monotone growth. | **EQUIVALENT** |
| **Weather — zone temp** `neiso-weather/neiso_zone_temp_daily.csv` | 2021: **1,460 rows = 365 days × 4 zones, 0 NaN**. Identical structure every year 2018–2025 (1,464 in leap years). Feeds `temp_dependent_derate`, `neiso_gas_coldsnap_derate`. | **EQUIVALENT** |
| **Weather — load-weighted** `neiso_load_weighted_temp_daily.csv` | 2021: **365 rows, 0 NaN**. Identical every year 2018–2025. | **EQUIVALENT** |
| **CAMPD unit-level** `campd-unit-level/{CT,MA,ME,NH,RI,VT}_2021.parquet` | All six NEISO states present for 2021, same as every year 2018–2026. | **EQUIVALENT** |
| **EIA-930 fuel type** `ISNE_fueltype.parquet` | 2021: **140,160 rows = 8760 h × 16 fuel types** — exactly the 2022/2023/2025 count (2020/2024 are 140,544, leap). | **EQUIVALENT** |
| **Calibration reference** `_validation-source/calibration_reference.json` | `isos.NEISO.2021` present with the **same four keys** as every tuned year (`demand`, `generation_twh`, `henry_hub_actual`, `renewables`). 2021 carries **no** `eia923_incomplete` flag — 2025 does. | **EQUIVALENT** (better than 2025) |
| **eGRID vintage** `fleet-egrid/eGRID2021_data.xlsx` | Present, between eGRID2020 and eGRID2022. Vintage parity holds. | **EQUIVALENT** |
| **F923 delivered fuel** `eia923_monthly_fuel_costs.parquet`, `eia923_monthly_generation.parquet`, `fossil_co2_rates.parquet` | All three cover **2018–2026**, 2021 included. | **EQUIVALENT** |
| **Year-invariant derived params** — `chp_power_only_heat_rates_NEISO`, `campd_ct_heat_rates_NEISO`, `thermal_tranches_NEISO`, `coal_takeorpay_NEISO`, `coal_supply_NEISO`, `cc_capacity_reconcile_NEISO`, `bin_assignments_NEISO` | **No year column in any of them** — pooled fleet parameters applied identically to every year. 2021 gets exactly what 2023–2025 get, by construction. | **EQUIVALENT** |
| **Reserve / AS requirements** | NEISO reserve requirements are **published static constants** (`ne_30min_total` 1,800 / `ne_10min_total` 1,200 / `ne_10min_spin` 600 MW), not a year-keyed data file — `data/raw/NEISO-AS/*` holds READMEs only. Year-independent by construction. | **EQUIVALENT** |
| **Winter fuel inventory** `winter-fuel-inventory/isone/isone.csv` | 13 rows of ISO-NE OFSA capacity/logistics **program constants** (`delivery_year` ∈ {2014/2015, 2018, 2022/2024}) — structural, deliberately excluding measured burn outcomes. Applied identically to all years. Feeds `neiso_winter_fuel_inventory`, `neiso_winter_fuel_mustrun`, `neiso_oil_burn_budget`. | **EQUIVALENT** |

### 2.2 DEGRADED — 2021 is materially worse than the tuned years

| Input | Evidence | Grade |
|---|---|---|
| **Nuclear availability** (per-reactor overlay **and** its monthly anchor) | **BOTH LAYERS ABSENT FOR 2021.** `data/raw/nuclear-availability-NEISO.csv` covers **2023-01-01 → 2025-12-31 only** (3,288 rows, 3 reactors). `constants.NUCLEAR_MONTHLY_CF_BY_YEAR['NEISO']` covers **2023, 2024, 2025 only**. A 2021 solve therefore falls through both and lands on the **static climatological pattern** `NUCLEAR_MONTHLY_CF['NEISO']` = [1.0, 0.99, 0.95, 0.95, 0.98, 1.0, 1.0, 1.0, 0.97, 0.96, 0.98, 1.0], mean 0.982. **Sized in §3.4: +0.96 TWh of phantom nuclear in 2021, +1.25 TWh of it in October alone.** | **DEGRADED — BLOCKING** |
| **Interchange seam tranches** | `IMPORT_TRANCHES_BY_YEAR['NEISO']` and `EXPORT_TRANCHES_BY_YEAR['NEISO']` both cover **2023, 2024, 2025 only**. 2021 falls back to the static pooled entry, which `model/interchange/spec.py` documents as "the **POOLED 2023-2025 derivation**". NEISO imports (HQ Phase II 1,830 MW, NB 630 MW, NY ties 1,740 MW) are a large share of supply, so this embeds 2023–2025 HQ water value and NY–NE arbitrage conditions into a 2021 solve. | **DEGRADED** |
| **EIA-860 CHP designation by vintage** | `_processed-legacy/eia860_chp_by_year.parquet` covers **2023, 2024, 2025 only**. `data/chp.py::_chp_by_plant` falls back to "the single committed operable-generator sheet (the most recent vintage)" — documented and graceful, but 2021 is classified on a **2025-era** CHP snapshot while each tuned year gets its own vintage. CHP status is stable year-to-year, so materiality is low; parity is still broken. | **DEGRADED (minor)** |
| **Parasitic load factors** | `_processed-legacy/parasitic_load_factors.parquet`, NEISO rows: `{0: 463, 2022: 564, 2023: 428, 2024: 453, 2025: 205}`. **No 2021.** Falls back to the `year == 0` pooled-measured default. Note **2022 has year-specific rows and 2021 does not** — so this is a gap against the already-spent touchpoint too. | **DEGRADED (minor)** |

### 2.3 NOT A BLOCKER — the prompt's third bullet, corrected

| Item | Finding |
|---|---|
| `frontend/data/backcast/bench/NEISO/2021.json.gz` | **Correctly reported missing** (bench holds 2022–2025). But it is **not a prerequisite**: `render_backcast.py::_write_bench_part` writes the part from `build_payload`, which reads **the registering bundle's own committed input snapshots** (`bundle_input_path(bdir, "eia923"/"eia930"/"campd")`). The bench part is an **OUTPUT of registration**, produced automatically when a 2021 run is registered, then read by `calibration_verdict.py`. Nothing needs building in advance. Its `_lw` load-weighted rubric-v2.4 fields live in `bench.avgLMP` (`rt_lw`, `da_lw`, `rt_lw_mon`, `da_lw_mon`) and are computed at render time from the LMP actuals + demand, both of which 2021 has. |

---

## 3. The load-bearing measurements

### 3.1 Demand — 2021 is dense and real; its one artifact is smaller than 2024's

2021 carries exactly **one** defective hour: **2021-11-07 01:00 = 2,598 MW**, between neighbours of
11,178 and 10,394 MW. 2021-11-07 is the **DST fall-back date**, and this is EIA-930's well-understood
duplicate-hour artifact. It is unique to 2021 among 2021–2025 (the other four years' DST days are
clean).

It is **not** a coverage or backfill problem, and it is **not worse than the training window**:

| year | hours < 7,000 MW | worst | nature |
|---|---|---|---|
| 2021 | **1** | 2,598 MW (11-07 01h) | DST fall-back artifact |
| 2022 | 0 | — | — |
| 2023 | 0 | — | — |
| **2024 (tuned)** | **3** | **0 MW** (06-27 01h/15h/17h) | **three outright zeros** |
| 2025 | 12 | 6,032 MW | 04-20 and 05-11 midday — real spring low-net-load days, not artifacts |

A tuned year carries three **zero-MW** hours; 2021 carries one low-but-nonzero hour. On this axis
2021 is **no worse than the window it is being compared against**.

### 3.2 Gas basis — fully measured, correctly winter-peaking

Source census of `gas_basis_by_iso_month.csv`, NEISO rows, by year:

| years | source family | months |
|---|---|---|
| 2015–2017 | EIA N3050MA3 proxy | 12/12 proxy |
| **2018** | MIXED | 8 measured + **4 proxy** (the known unrepairable Mar–Jun hole) |
| **2019–2025** | **ISO-NE MA gas index (measured)** | **12/12 measured** |

**2021 is 12/12 measured.** Its own values are unambiguously winter-peaking: Jan +2.2574, Feb
+3.2163, Dec +4.6223 against Jun −0.4482, Jul −0.6505, Aug −0.1441.

### 3.3 Same-recipe reproduction — the delivered-gas chain on the keeper's own config

`scripts/probes/_neiso92_2021_gas_chain.py` (new, committed) re-points the neiso-85 decomposition at
the **designated keeper's** `run_config.json` — the neiso-85 probe's own source bundle
(`neiso2022_touchpoint`) having since been pruned — and widens it to the whole ladder. This is the
like-for-like construction neiso-85 used, so the ratios are directly comparable to its published
numbers.

Final delivered gas, **winter (Jan/Feb/Dec) ÷ summer (Jun–Aug)**:

| year | winter $/MMBtu | summer $/MMBtu | ratio | shape |
|---|---|---|---|---|
| 2020 | 3.133 | 1.543 | **2.030** | normal |
| **2021** | **7.307** | **3.310** | **2.207** | **normal (winter dearer)** |
| 2022 (repaired) | 16.190 | 7.693 | **2.104** | normal |
| 2023 | 5.362 | 2.244 | **2.390** | normal |
| 2024 | 6.764 | 1.791 | **3.778** | normal |
| 2025 | 15.480 | 3.219 | **4.808** | normal |

**2021 = 2.207 is in family** with the tuned years and carries the correct sign. For contrast, the
defect neiso-85 caught was 2022 at **0.397 — inverted**. Coverage is identical across all six years:
EIA-923 **12/12** months with receipts, hub overlay **8760 h = 100.0 %**.

> **Provenance note.** These figures are HEAD data on the keeper's config, so 2025 reads 4.808 where
> neiso-85 published 4.608. The difference is the neiso-87 Aug-2025 basis repair (`+0.04`
> interpolation → measured `−0.38`) that landed **after** the keeper bundle was solved. This is
> disclosed defect (i) in the keeper shard: **the committed keeper's 2023–2025 numbers and a 2021
> solve at HEAD would sit on different basis vintages for one month of 2025.** Rule 22 as amended
> requires measured inputs be applied *consistently across all years*, so the standing
> recommendation to re-solve the keeper at HEAD should be settled in the same session that closes
> the gaps below.

### 3.4 Nuclear availability — the blocking gap, sized

The fallback chain in `data/fleet/arrays.py:248` is: per-year EIA-923 anchor
(`NUCLEAR_MONTHLY_CF_BY_YEAR`) → else static climatology (`NUCLEAR_MONTHLY_CF`, with `(1 − eford)`
layered on) → then the per-reactor NRC daily overlay on covered dates.
`outages.nuclear_unit_availability_series` returns `{}` for an uncovered year, so callers "degrade to
the smear unchanged" — **silently**. For NEISO 2021, **both** measured layers are absent.

Reconstructing actual monthly nuclear CF from EIA-930 ISNE `NUC` against a 3,389 MW fleet
(Millstone 2 + Millstone 3 + Seabrook 1) validates the method — the committed anchor tracks it
closely in every year it exists (2023 0.787 vs 0.780, 2024 0.902 vs 0.890, 2025 0.941 vs 0.925) —
and then exposes the gap:

| year | actual mean CF | static-fallback mean | **annual phantom nuclear** | worst month |
|---|---|---|---|---|
| 2020 | 0.858 | 0.942 | **+2.51 TWh** | Apr +1.18 TWh |
| **2021** | **0.911** | **0.942** | **+0.96 TWh** | **Oct +1.25 TWh** |
| 2022 | 0.922 | 0.942 | **+0.61 TWh** | May +0.80 TWh |

**October 2021 is the problem.** Actual nuclear CF was **0.425** — a deep refuelling outage — against
a fallback that would hold the fleet at ~0.92. That is **~1,900 MW of phantom baseload running all
month**, ≈ **1.25 TWh ≈ 14 % of October NEISO load**, displacing gas at the margin in precisely the
month 2021's autumn gas ramp was building (October delivered gas $4.75/MMBtu, October RT LMP
$55.9/MWh, climbing to $58.9 in November and $59.4 in December).

This is the **neiso-85 pattern exactly**: one absent measured input, month-concentrated, systematic
in sign, large enough to dominate the monthly residual. A 2021 spend against it would measure the
data gap.

### 3.5 LMP clock — verified, not assumed

The prompt requires 2021 be on the fixed chronological clock. Tested by correlating hourly RT LMP
against hourly load — a broken clock collapses this:

| year | corr(load, RT) | corr(load, log RT) | peak-hour alignment |
|---|---|---|---|
| **2021** | **0.459** | **0.475** | load h19 / price h17 — **OK** |
| 2022 | 0.496 | 0.534 | load h19 / price h17 — OK |
| 2023 | 0.403 | 0.523 | load h19 / price h17 — OK |
| 2024 | 0.327 | 0.451 | load h19 / price h17 — OK |
| 2025 | 0.586 | 0.628 | load h19 / price h17 — OK |

2021 sits **inside** the tuned band (0.327–0.586) with identical peak-hour alignment. Its monthly
mean RT shape is also coherent with its own fuel input — a Feb peak ($71.5, the Feb-2021 cold event)
and an autumn ramp (Oct $55.9 → Dec $59.4) matching the late-2021 global gas surge and the Dec-2021
basis of +4.6223.

---

## 4. A finding about the already-spent 2022 touchpoint

Gaps §2.2 #1 (nuclear), #2 (interchange) and #4 (parasitic factors) **also applied to 2022**, which
has now been spent twice (`2026-08-05-neiso-2022-touchpoint`, then
`2026-08-06-neiso-2022-corrected-basis`, the current `holdout_touchpoint`).

- `NUCLEAR_MONTHLY_CF_BY_YEAR['NEISO']` has no 2022 → **+0.61 TWh phantom nuclear** in that run
  (Apr +0.52, May +0.80 TWh, against real refuelling at CF 0.700 / 0.625).
- `IMPORT/EXPORT_TRANCHES_BY_YEAR['NEISO']` has no 2022 → the pooled 2023–2025 seam curve.

The keeper shard's touchpoint block asserts **"AVAILABILITY-ENVELOPE PARITY IS VERIFIED"**. That
statement is true **as scoped** — it is explicitly about the uniform CAMPD fossil-outage detector
regeneration, and that verification stands unchallenged. But it does **not** cover the nuclear
availability envelope, and the nuclear gap is **not** recorded anywhere in that block.

This is **not** a retraction of the 2022 determination and no artifact is edited here. It is a
disclosure: 2022's `CALIBRATED-WITH-CAVEATS` was obtained with ~0.6 TWh of phantom nuclear in the
spring. Since 2022 is validation tier — **iterable by design** — the correct disposition is to
re-spend it *after* the fix, together with 2021, not to re-interpret it now.

---

## 5. What must happen before 2021 is solved

**Do not request a freeze lift yet.** A lift spent on the current inputs would burn the touchpoint on
a known-defective nuclear envelope — the precise error the freeze exists to prevent and the precise
error neiso-85 already paid for once.

The fix path is **entirely data prep**, which rule 22 (as amended 2026-08-06) places outside the
freeze: *"Data intake needs NO per-ISO/per-window authorization and no marker. Prep it, apply it to
every year, keep it consistent."* Every upstream source is already on disk.

| # | Gap | Fix | Source (verified present) |
|---|---|---|---|
| 1 | Nuclear availability, both layers | Extend `NUCLEAR_MONTHLY_CF_BY_YEAR['NEISO']` to **2019–2022** from EIA-923 monthly nuclear energy, then run `scripts/data/derive_nuclear_availability.py` for those years to extend `nuclear-availability-NEISO.csv` | `data/raw/nrc-reactor-status/2021PowerStatus.txt` **exists** (2018–2026 all present); EIA-923 monthly generation covers 2018–2026. **NYISO already carries 2018–2025**, so the deriver is proven over this span. |
| 2 | Interchange seam tranches | Extend `IMPORT/EXPORT_TRANCHES_BY_YEAR['NEISO']` to 2019–2022 via `scripts/data/derive_neiso_import_tranches.py` | Needs the ISNE interchange extract widened first — `eia-930-interchange/ISNE interchange hourly.parquet` currently holds **2023–2025 only**. This is a **fetch**, not a derive. **[PATCHED 2026-08-14, neiso-93: there is a SECOND blocking fetch this row missed — `_validation-source/nyiso_proxy_lmp_hourly_NEISO.parquet` also holds 2023–2025 only, and its producer `build_nyiso_proxy_lmp_neiso.py` reads `*damlbmp_zone_csv.zip` archives that are gitignored and absent from the repo. Both were cleared in neiso-93: the NYISO zips re-fetched from MIS (84/84), and the EIA-930 extract widened via a new keyless `--source bulk` route (no `EIA_API_KEY` exists in these environments). See `FINDING-neiso93-envelope-repair-2026-08-14.md` §3.]** |
| 3 | EIA-860 CHP by vintage | Extend `eia860_chp_by_year.parquet` to 2019–2022 | EIA-860 annual releases; low materiality, can ride along. |
| 4 | Parasitic load factors | Add NEISO 2021 (and 2019/2020) rows | Same EIA-923 gross/net basis already used for 2022–2025. **[CORRECTED 2026-08-14, neiso-93: this row's premise is WRONG. The counts `{0: 463, 2022: 564, …}` in §2.2 are the file's TOTAL rows by year, not NEISO's — they sum to its 2,113 rows. By plant-id intersection the file holds ERCOT 130/130, PJM 410/411, MISO 280/485, NYISO 27/106 and **ZERO NEISO plants in ANY year**, tuned years included. The gap is larger than stated, and the fix covers 2019–2025, not 2019–2021. See `FINDING-neiso93-envelope-repair-2026-08-14.md` §5.]** |

Do all four **across the whole 2019–2025 span at once**, not for 2021 alone — that is what rule 22's
consistency clause requires, and it is what makes 2019 genuinely ready when its one-touch moment
comes.

**Then**, and only then: re-solve the keeper at HEAD across 2023–2025 on the corrected envelope
(this also closes the keeper's disclosed defect (i), the stale Aug-2025 basis row), confirm the
in-sample determination is not degraded, and only after that request a freeze lift naming
**2021 + 2022** as one validation re-spend.

**Sequencing matters:** gaps 1–4 change the availability envelope, so they change the in-sample
result too. Re-training must happen on 2023–2025 **before** the touchpoint is re-read — rule 22's
touchpoint loop, step 3.

---

## 6. What this session did NOT do

- **No LP was constructed and no year was solved, scored or registered** — not 2021, not any year.
- **No run was registered** on the backcast dashboard; `bench/NEISO/2021.json.gz` was **not** built
  (it is an output of registration, §2.3).
- **The freeze was NOT lifted** and NOT modified. It remains ACTIVE, exactly as found.
- **2019, H1-2026 and the `final` block were not touched** in any way.
- **No parameter was tuned, and nothing was fitted to 2021.**
- **No mechanism was tested**, so no mechanism-matrix cell verdict was minted (rule 28d). The NEISO
  shard is stamped with this assessment as evidence only.
- No committed artifact of the 2022 touchpoint or the keeper was edited; §4 is a disclosure, not a
  retraction.

---

## 7. Artifacts

| Path | What |
|---|---|
| `results/calibration/ASSESSMENT-neiso92-2021-readiness-2026-08-13.md` | This assessment |
| `scripts/probes/_neiso92_2021_gas_chain.py` | Same-recipe delivered-gas chain reproduction on the keeper's config, 2020–2025 |
| `results/calibration/_neiso92_gas_chain.json` | Its output — per-stage monthly series + per-year coverage |

**Prior art:** `FINDING-neiso85-2022-seasonal-inversion-2026-08-05.md` (the precedent this gate
exists to prevent repeating), `FINDING-neiso86-gas-basis-intake-2026-08-06.md` (the repair that
makes 2021's basis clean), `ASSESSMENT-neiso87-declaration-2026-08-06.md` §3 (why 2019 is
unsolvable — demand floors at 2021).
