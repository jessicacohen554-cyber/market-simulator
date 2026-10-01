# NYISO 2022 validation-touchpoint DATA-READINESS ASSESSMENT — nyiso-134, 2026-08-14

> **STATUS: all three blocking defects were FIXED later the same session — see §7.**
> The owner directed the data be fetched, and it was: D-1, D-2 and D-3 are closed
> with measured inputs across **2018/2019–2022**, not just 2022. The original
> finding below is preserved verbatim as the diagnosis of record; §7 records what
> landed, what the fixes measured, and the one item that is a genuine source gap.
> **No LP has been solved. The readiness verdict is now the freeze, not the data.**

**VERDICT (as found): NOT READY. The 2022 solve is REFUSED on the merits.**
Three measured inputs the frozen keeper consumes are **DEGRADED** for 2022 relative to
2023–2025, and **all three fail silently** — no exception, no warning, no log line. A
touchpoint run on them would not have been measuring the keeper's forecast skill.

The holdout spend freeze is also ACTIVE and independently blocks the spend, but that is
**not** the reason for this verdict: the data defects below would block the solve even
with an owner lift in hand.

Phase 1 (data readiness) is rule 22 channel 1 — unrestricted, no-LP — and was executed in
full. **No LP was constructed, solved or scored for any year. No 2022 model output exists.
Nothing was registered.**

---

## 0. Session identity and prompt deviations

| item | prompt said | actual | why |
|---|---|---|---|
| shorthand | `nyiso-133` | **`nyiso-134`** | `nyiso-133` is SPENT — `2026-08-08-nyiso-133-cod-arm` and `-cod-control` are both registered (`frontend/data/backcast/registry/`). The prompt's own instruction was to verify against the registry; this is that verification. Two independent sources agree on `nyiso-134`: the registry, and `docs/calibration-log/nyiso.md`'s **tail**, which already reads *"Next number: **nyiso-134**"*. (The "Next shorthand: nyiso-117" strings the prompt flagged are stale **mid-file** lines from older entries, not the live marker.) |
| assessment filename | `ASSESSMENT-nyiso133-2022-readiness-2026-08-13.md` | `ASSESSMENT-nyiso134-2022-readiness-2026-08-14.md` | tracks the corrected shorthand and today's date (2026-08-14), matching repo convention (`ASSESSMENT-<shorthand><N>-<topic>-<date>.md`, cf. `ASSESSMENT-neiso87-declaration-2026-08-06.md`). |

---

## 1. Gate state at HEAD (verified, not assumed)

**Holdout spend freeze — `frontend/data/backcast/holdout-freeze.json`: `"active": true`.**
Declared 2026-07-25, lifted narrowly twice (2026-08-05 PJM+NEISO 2022; 2026-08-06 NEISO 2022
corrected basis) and **re-armed both times**. No lift in `history` names a NYISO spend of any
kind. The freeze outranks the marker and is checked first
(`scripts/lib/holdout_policy.py` §FREEZE_FILE). Standing basis — the CAMPD economic-layup
residual — is unchanged.

**NYISO marker — `calibration-complete.json`:**
- present in `complete`; `tier_authorized` = *"validation ONLY"*; keeper `2026-08-08-nyiso-132-cf-arm`.
- **absent from `final`** (that block holds only a `_note`). `locked_test` reads
  *"NOT AUTHORIZED … has never scored 2019 or H1-2026."* Untouched by this session.
- The entry's `tier_authorized` text still names a **2018** rung. That is **stale**: 2018 was
  dropped 2026-08-06 and now falls through `holdout_policy.tier_for_year`'s fail-closed default
  to **locked** tier (`VALIDATION_YEARS = {2020, 2021, 2022}`). 2018 was not touched.

**Tier of 2022:** `tier_for_year(2022)` → `validation` → authorized by `complete`, suspended by
the freeze.

**Baseline re-verified from committed artifacts only (no solve):**
`scripts/calibration_verdict.py --run-id 2026-08-08-nyiso-132-cf-arm` →
**CALIBRATED-WITH-CAVEATS**, C1/C2/C3a/C3b/C4/C6/C8 all PASS, **C3c the lone ledgered caveat**
(budget 1 of 1). Matches the marker's recorded determination exactly.

All 15 registered NYISO runs are `years=[2023, 2024, 2025]`. **NYISO has never solved 2022.**

---

## 2. The three blocking defects

### D-1 — RGGI allowance cost is silently ZERO in 2022 `[BLOCKING]`

`market_sim.config.constants.STATE_CARBON_PRICE_BY_ISO["NYISO"] = {2023: 13.49, 2024: 20.71, 2025: 22.09}`
— **no 2022 key.**

`policy.carbon.state_carbon_price` returns `None` when `year not in program`; the caller falls
through to the scenario carbon path, and the keeper ships `carbon_price_path="zero"`,
`carbon_price=0.0`, `state_carbon_pricing=True`. Measured directly:

```
state_carbon_price(NYISO, 2022) = None      -> $0.00/tCO2 charged
state_carbon_price(NYISO, 2023) = 13.49     -> $13.49/tCO2 charged
```

So 2022 would price every in-state fossil unit with **no RGGI allowance cost at all**, while
each in-sample year carries one.

**Materiality**, computed from the model's own `plant_emission_rates_v2` NYISO-2022 rows
(382 units, 93.1 TWh net):

| class | tCO2/MWh-net | $/MWh omitted per $1/tCO2 | at ~$13/tCO2 |
|---|---|---|---|
| Combined cycle | 0.4141 | 0.414 | **$5.53** |
| Combustion turbine | 0.5401 | 0.540 | **$7.21** |
| Tangentially-fired steam | 0.6025 | 0.603 | **$8.04** |
| Dry-bottom wall-fired steam | 1.1873 | 1.187 | **$15.85** |
| **fleet** | **0.4558** | **0.456** | **$6.08** |

$6.08/MWh is **8.1 % of the 2022 RT mean LMP ($74.77)**. Critically the omission is **not a
level shift**: the CC-to-steam spread is **2.9×**, so dropping it **re-orders the merit
stack**, differentially advantaging the dirtiest units.

**This is a fixable gap, not a source gap.** `config/fuel_trajectories.py` documents the exact
recipe — the simple mean of the calendar year's four quarterly RGGI auction clearing prices,
cited to RGGI, Inc. press releases (`rggi.org/auctions/auction-results`), with each
constituent auction listed for 2023–2025. Extending to 2022 is a four-number transcription
(auctions A55–A58) from the same source by the same producer. *(The 2022 clearing prices are
not asserted here — they must be transcribed and cited, not recalled.)*

---

### D-2 — the 2022 solve would run on a transmission line that did not exist yet `[BLOCKING]`

`constants.NYISO_INTERFACE_TTC_BY_YEAR` and `NYISO_INTERFACE_TTC_BY_MONTH` both cover
**2023, 2024, 2025 only**. Both appliers in `pipeline/ttc.py` **return unchanged on a missing
year** (`if not overrides: return iso_config` / `if not monthly: return ttc`) — a silent no-op.

The interface is **Upstate_West → Capital_Hudson (Central-East)**, whose limit steps up when
the NY Transco AC Transmission project enters service — **December 2023**, per the module's own
docstring. Resolved values, measured end-to-end:

| solve year | Central-East limit used | source | monthly envelope |
|---|---|---|---|
| **2022** | **2,850 MW flat** | *** static topology fallback — no 2022 row *** | **none (flat scalar)** |
| 2023 | 1,750 MW | year table (pre-upgrade) | present, 1,450–2,725 MW |
| 2024 | 2,850 MW | year table (post-upgrade) | present, 2,525–3,075 MW |
| 2025 | 2,850 MW | year table (post-upgrade) | present, 2,500–3,175 MW |

**2022 is a pre-upgrade year and would be solved on the post-upgrade limit.** Against the
model's own pre-upgrade value (1,750 MW for 2023) that is **+1,100 MW, +63 %**, of
upstate→downstate transfer capability that was **not built until the following December**.
2022 additionally loses the measured monthly envelope every in-sample year carries.

The direction is the damaging one: extra Central-East capability **relieves** the upstate→
downstate congestion that forms downstate scarcity prices. NYISO's sole open caveat — **C3c,
the price tail** — is precisely a downstate (Zone J/K) transfer-limit and price-formation
problem (`FINDING-nyiso130-li-transfer-security-limit-2026-08-06.md`). A 2022 C3c result on
this input would be **uninterpretable**: a miss could not be separated from the phantom line,
and a pass would be spurious. This is the NYISO precedent-(1) failure mode exactly — the
keeper silently running against the wrong availability/limit envelope.

**Fix:** add the measured 2022 Central-East annual limit and 12-month envelope to both tables,
from the same NYISO DAM interface-posting source as 2023–2025. **Or**, at minimum, make both
appliers fail loud on a missing backcast year rather than silently returning the forecast-
topology static value — the mechanism-must-never-silently-no-op contract already used by
`nyiso_li_lcr_tsl` (which raises `ValueError`).

---

### D-3 — SCR/EDRP demand response silently clamps to the wrong Gold Book `[BLOCKING, bounded]`

Keeper arms `nyiso_scr_edrp=True`, `nyiso_scr_edrp_reserve_eligible=True`, strike **$500/MWh**.

`data/nyiso_demand_response.load_scr_edrp_enrollment` does
`gb_year = min(max(year, _MIN_GB_YEAR), _MAX_GB_YEAR)` — **clamped to the on-disk range**. The
enrollment CSV carries `gold_book_year` ∈ {2023, 2024, 2025} only, so a **2022 solve clamps up
to the 2023 Gold Book**. The 2022 Gold Book is not on disk (`data/raw/NYISO/` holds 2023, 2024,
2025, 2026).

| Gold Book vintage | summer DR MW | winter DR MW | YoY (summer) |
|---|---|---|---|
| 2023 | 1,234.4 | 802.0 | — |
| 2024 | 1,294.4 | 1,005.1 | +4.9 % |
| 2025 | 1,487.9 | 1,027.2 | +14.9 % |

A ~1.23 GW block of emergency DR would be placed at the wrong vintage. The observed drift
(+4.9 %/+14.9 %) bounds the error at roughly **60–190 MW** — modest in absolute terms, but it
sits at a **$500/MWh strike**, i.e. squarely in the scarcity-price region that C3c measures.
Unlike D-1 and D-2 this is a bounded quantity, so it is the softest of the three; it is still
a silent, wrong-vintage substitution in the exact band under caveat.

**Fix:** fetch the 2022 Gold Book and extend the CSV with the committed producer
(`scripts/data/build_nyiso_scr_edrp.py`) — same source, same recipe, one new vintage.

---

## 3. What passed — including the highest-risk item

### 3.1 CAMPD unit-outage windows — **EQUIVALENT, proven by same-recipe reproduction**

The prompt's designated highest risk, given the 2026-07-19 marker withdrawal (a keeper tuned
against a stale-detector extract, 1,598 vs 2,641 windows). **That defect does not reproduce.**

The extract is a **single blob** (`34f9adee…`, unchanged across every commit touching it) with
one continuous 2018→2026 span — there is no per-year file and so no seam at which 2022 could
carry a different vintage. A full re-derivation at HEAD defaults
(`derive_campd_unit_outages.py --iso NYISO --years 2018…2026`) proves the recipe exactly:

```
committed ∪ layup  ==  no-guard re-derivation     True
committed ∩ layup  ==  ∅  (disjoint)              True
only-in-committed (orphans, any year)             0
```

| year | committed | layup | sum | re-derived | exact |
|---|---|---|---|---|---|
| 2018 | 621 | 349 | 970 | 970 | ✓ |
| 2019 | 516 | 430 | 946 | 946 | ✓ |
| 2020 | 537 | 332 | 869 | 869 | ✓ |
| 2021 | 539 | 411 | 950 | 950 | ✓ |
| **2022** | **533** | **317** | **850** | **850** | **✓** |
| 2023 | 540 | 389 | 929 | 929 | ✓ |
| 2024 | 464 | 404 | 868 | 868 | ✓ |
| 2025 | 491 | 353 | 844 | 844 | ✓ |
| 2026 | 182 | 52 | 234 | 234 | ✓ |

Every committed window re-derives, in every year, with **zero** orphans: the committed extract
is the `--merit-order-guard` pass and the residual is exactly the layup split. 2022 was
produced by **the same pass with the same flags** as 2023–2025.

Envelope comparability (2022 vs the 2023–2025 band):

| metric | 2022 | 2023–2025 range | inside? |
|---|---|---|---|
| windows | 533 | 464 – 540 | ✓ |
| median duration (d) | 14.30 | 12.20 – 14.85 | ✓ |
| capacity-weighted MW-days | 3.459 M | 2.877 – 3.059 M | slightly above; inside the full 2018–26 span (2.877–3.746 M) |
| distinct units | 92 | 84 – 99 | ✓ |

### 3.2 Gas chain — **EQUIVALENT** (the NEISO precedent does not reproduce)

`gas_basis_by_iso_month` NYISO 2022 is on the **in-sample Iroquois-Z2 − Henry-Hub**
construction — hub label and `source` string byte-identical to 2018–2025, *not* the old
citygate proxy (which survives only in 2015–2017 and 2026).

**Seasonal-inversion test** (the neiso-85 defect, winter mean vs summer mean $/MMBtu):

| year | winter (J/F/D) | summer (J/J/A) | W−S | verdict |
|---|---|---|---|---|
| **2022** | **4.864** | **1.214** | **+3.650** | **OK — winter > summer** |
| 2023 | 1.760 | 0.380 | +1.380 | OK |
| 2024 | 1.602 | 0.123 | +1.479 | OK |
| 2025 | 6.029 | 0.830 | +5.199 | OK |

2022's spread sits **between** the in-sample years. Correct pipeline-constrained Northeast
shape; no inversion.

**Independent anchor** — derived annual Transco Z6 NY vs the published NYISO SOM annual:

| year | derived | SOM published | ratio |
|---|---|---|---|
| **2022** | 6.647 | 7.04 | **0.944** |
| 2023 | 2.028 | 1.94 | 1.045 |
| 2024 | 2.079 | 2.19 | 0.949 |
| 2025 | 4.178 | 4.64 | 0.900 |

2022's 0.944 is **inside** the in-sample band (0.900–1.045) and nearer its centre than 2025.

Downstream gas rows all at parity: `transco_z6_ny_daily` 239 prints (in-sample 223–233),
`transco_z6_iroquois_monthly` 12 rows, `nyiso_downstate_ct_gas_basis_monthly` 12,
`nyiso_zonal_gas_hub` 5 zone rows, `nyiso_som_hub_fuel_annual` 2022 present
(Iroquois Z2 $8.82 / Transco $7.04). Henry Hub 2022 resolves to **$6.45** through the same
`_henry_hub_actual` lookup that returns the keeper's recorded 2.54/2.19/3.52.

**LDC non-firm transport — real, not padded** (the prompt's specific concern, since National
Grid's archive bottoms out Oct-2021). 24 rows for 2022 (2 LDCs × 12), each citing a distinct,
correctly-numbered statement: `statnfdr-5-eff-01-01-22` … `statnfdr-16-eff-12-01-22`, for both
KEDNY and KEDLI. Rates step on tariff effective dates and hold between — the correct physical
behaviour, matching the in-sample pattern (2022: 4–5 distinct values per LDC; in-sample 3–6).

### 3.3 Bench / scoring series — **EQUIVALENT**

`actual_lmp_hourly_NYISO.parquet`: 2022 carries a full **8,760** rows in **both** markets with
**zero** nulls — cleaner than 2025 (2 RT nulls). The **fixed chronological clock** is confirmed
by exact agreement with the register's stated re-clocked annual means:

| year | DA | RT |
|---|---|---|
| 2018 | 34.87 | 35.15 |
| 2019 | 25.36 | 24.96 |
| 2020 | 19.23 | 19.41 |
| 2021 | 37.07 | 37.04 |
| **2022** | **72.73** | **74.77** |

(register: DA 2018–2022 = 34.87 / 25.36 / 19.23 / 37.07 / **72.73** — exact.)

Rubric-v2.4 **`_lw` parity**: 2022 carries all five load-weighted fields
(`da_lw`, `da_lw_mon`, `rt_lw`, `rt_lw_mon`, `src_lw`), 13 fields total — **identical to
2023–2025**. (Only 2026 lacks them, a known separate item.)

`actual_tail.json` `isos.NYISO`: **2020–2025** ✓. `actual_lmp.json` NYISO: 2018–2026 ✓.
`calibration_reference.json` `isos.NYISO`: 2022, 2023, 2024, 2025 ✓.
`NYISO_2022_renewable_capacity.csv` present ✓.

### 3.4 Everything else verified at parity

| input | 2022 | in-sample comparator | grade |
|---|---|---|---|
| `plant_emission_rates_v2` NYISO | **382 unit rows / 120 plants**; 347 measured / 35 backfilled (90.8 % measured) | 2023 86.8 %, 2024 84.7 %, 2025 91.4 % | **EQUIVALENT** — measured share inside band; fleet CO2 461.0 kg/MWh-net falls monotonically between 2021 (472.5) and 2023 (442.3). Reproduces the register's quoted unweighted means **exactly** (2021 557.9 / 2022 571.0 / 2023 521.7) |
| Reserve requirements hourly | **61,320 rows** | 61,320 in each of 2023/24/25 — identical | **EQUIVALENT** |
| `actual_as_reserve_NYISO` | 8,760 | 8,760 | **EQUIVALENT** (validation-side only, rule 13) |
| Capacity deliverability | 2022 → delivery year **2022/2023**; `import_limit` = G-J 3425 / LI 325 / NYC 2900 | 2023/24: 3425 / 325 / 2875 | **EQUIVALENT on the path the keeper uses.** `nyiso_li_tsl_n11_security=False`, so the reader is `import_limit_by_area`, which resolves; the mechanism **raises** rather than no-ops if absent. The `transfer_security_limit` row missing from the raw 2022/23 block is **not consumed** by this keeper |
| Nuclear availability | 1,460 rows (4 reactors × 365) | 1,460 / 1,464 | **EQUIVALENT**. `NUCLEAR_MONTHLY_CF_BY_YEAR["NYISO"]` **does** carry 2022 (unlike the other five ISOs) |
| Demand profiles (EIA-930) | 8,760 | 8,760 | **EQUIVALENT** |
| Zonal load actuals (P-58) | `NYISO_load_actuals_2022.csv` | 2018–2025 series | **EQUIVALENT** |
| CAMPD unit-level + facility-level NY & NJ | `{NY,NJ}_2022` both grains | 2018–2026 complete | **EQUIVALENT** |
| Weather — zone temp / downstate TMAX | 1,825 zone-days / 365 days | 1,823–1,830 / 365–366 | **EQUIVALENT** |
| `IMPORT_TRANCHES_BY_YEAR["NYISO"]` | 2022 present, 7 rungs, physical levels | 2023–2025 same shape | **PRESENT** (see §4 caveat) |
| Firm-import floor | `NYISO_FIRM_IMPORT_FLOOR_FRAC` = {HQ_hydro 1.0, IESO 0.0} — **year-invariant** | same | **EQUIVALENT.** The register's old "`firm_import_floor_by_year` missing 2022" note is **stale**: that constant belongs to **MISO**; NYISO uses the year-invariant fraction path |
| Neighbour LMPs (PJM, NEISO) | 2022 present in both | 2018–2025 | **EQUIVALENT** |
| Interface flows (P-32) | 2022 present | 2018–2026 | **EQUIVALENT** |
| Wind PTC | falls back to `ira_ptc_wind = 26.0`, the correct 2022 statutory rate; `wind_ptc_vintage_offers=False` | — | **EQUIVALENT by fallback**, immaterial |
| Pooled measured params — CT/CHP heat rates, ramp envelopes, gas-bridge min-load/min-run, bin assignments, CC reconcile | identified once over **`2023-2024-2025`** or year-agnostic | same object | **EQUIVALENT — and correctly so.** Applying a training-window identification unchanged to the touchpoint is what rule 22 requires; re-identifying on 2022 would be the violation |
| `nyiso_proxy_lmp_hourly_NEISO` (2023–25 only) | — | — | **N/A** — consumed only by `derive_neiso_import_tranches.py`, a NEISO-lane script; never read by the NYISO solve |

---

## 4. Disclosed caveats — real, but not blocking

1. **Transco Dec-2022 Winter-Storm-Elliott hole.** Daily prints stop at **2022-12-21** ($6.29);
   Dec 22–31 is empty, and Elliott hit Dec 23–26. `_nyiso_hub_daily_gas_prices` builds day
   factors with `np.interp`, which **constant-extends** past the last print, so the model would
   see a flat pre-spike December tail; the monthly level is itself the mean of available prints.
   **But this is a coverage property 2022 shares with the in-sample years, not a 2022 defect:**

   | year | Dec prints | last print day | trailing gap |
   |---|---|---|---|
   | **2022** | **15** | **21** | **10 d** |
   | 2023 | 14 | 20 | 11 d |
   | 2024 | 12 | 18 | 13 d |
   | 2025 | 14 | 31 | 0 d |

   2022's gap is the **smallest** of 2022/2023/2024 and it has the **most** December prints. The
   EIA weekly archive simply has no editions 2022-12-22 → 2023-01-12. What differs is
   consequence, not lineage: the same-sized hole contains a major event in 2022 and contains
   nothing in 2023/2024 (Dec means $2.28/$3.30, maxima $3.70/$4.35). The annual level is
   nonetheless anchored — the SOM ratio 0.944 is inside the in-sample band (§3.2). **Grade:
   EQUIVALENT on provenance, coverage and recipe; disclose the December event-capture limit
   before quoting any Dec-2022 or winter-tail result.** Rule 14 forbids fabricating the dailies.

2. **Import-tranche reproduction quality out-of-training.** The register discloses duration
   RMSE **719 MW** for 2022 against the committed years' **≤328 MW**, and instructs that it be
   graded before any authorized use. The ladder is measured rather than fitted, so this is a
   disclosure, not a defect. **Not independently re-measured this session** — carried forward
   as the register states, and it should be graded when D-1/D-2/D-3 are fixed.

3. **`bench/NYISO/2022.json.gz` — MISSING, and NOT independently buildable.** Confirmed by
   reading the producer: bench parts are written by `render_backcast.generate` →
   `_write_bench_part`, fed by `render_calibration_html.build_payload`, which reads the
   **bundle's own solve artifacts** (`system.parquet`, per-year bundle inputs) and derives its
   year set from the bundle. There is no actuals-only path. The file is therefore a
   **by-product of registering a 2022 run**, not a prerequisite for one — it will be emitted
   automatically by `dashboard_add_run.py` when an authorized 2022 solve is registered. It is
   **not** an independent data gap and needs no separate intake.

4. **Fleet statics remain a year-agnostic snapshot** for 2022 as for every year. The register's
   sharpened pre-2021 concern (Indian Point 2 and 3, retired Apr-2020 / Apr-2021) **does not
   reach 2022** — both units were already retired before it. Standing in-sample caveat only.

---

## 5. Fix path to a legitimate 2022 touchpoint

Ordered by materiality. All three are **input intake or a fail-loud guard** — none is a
parameter, none is tuned to anything, and none touches the keeper recipe. Under the 2026-08-06
owner clarification (*"what is held out is the SCORE, never the DATA"*) all of this is
unrestricted, needs no marker and no lift, and **must be applied consistently across every year
2019–2025**, not just 2022.

| # | action | DOF | producer |
|---|---|---|---|
| D-1 | Transcribe the four 2022 RGGI auction clearing prices (A55–A58) and add the 2022 key to `STATE_CARBON_PRICE_BY_ISO["NYISO"]`, citing the press releases exactly as 2023–2025 do. Check `NEISO` at the same time (same gap, same source, converted at ×1.10231). | **0** | `config/fuel_trajectories.py` comment block records the recipe verbatim |
| D-2 | Add the measured 2022 Central-East annual limit + 12-month envelope to `NYISO_INTERFACE_TTC_BY_YEAR` / `_BY_MONTH` from the same NYISO DAM interface postings as 2023–2025. **Separately and regardless**, make `apply_iso_year_ttc` / `apply_iso_monthly_ttc` **fail loud** for a backcast year with no entry instead of silently returning the forecast-topology static value — a silent fallback to a *later* topology is a latent trap for every out-of-training year, not just 2022. | **0** | `pipeline/ttc.py`, `config/constants.py` |
| D-3 | Fetch the 2022 Gold Book and extend `nyiso_scr_edrp_enrollment.csv` with its vintage. Consider making the `min/max` clamp warn when it substitutes a vintage. | **0** | `scripts/data/build_nyiso_scr_edrp.py` |

After the three land, re-run this readiness assessment (it is cheap and fully scripted), then
the 2022 touchpoint needs only an **owner lift of the still-active freeze**. Everything else in
§3 is already at parity and needs no work.

**A note on why the freeze being active does not make this assessment moot.** Had the freeze
been lifted on the strength of NYISO's `complete` marker alone, the run would have proceeded
and produced a plausible-looking number on a model that was missing its carbon price and had a
transmission line built a year early. Both defects are invisible at runtime. The gate did its
job.

---

## 6. Provenance

Every number above was measured this session from committed artifacts at HEAD
(`cfb8127`), branch `claude/nyiso-2022-readiness-rzrxek`. No LP was constructed or solved; no
model output was compared against any 2022 actual; the only artifact written outside this
document is a scratchpad re-derivation of the outage extract (`/tmp/.../scratchpad/`,
not committed) and the routine `data/clean/` curation partition (derived, gitignored).

Cross-checked against `docs/holdout-data-equivalency-register-2026-07.md` NYISO sections
(2026-07-12 §2022 intake, 2026-07-13 ladder intake, 2026-07-31 residual closure) and the
`calibration-complete.json` `intake_log`. Two register statements are **corrected** by direct
measurement: the "firm-import floor missing 2022" item (§3.4 — wrong constant, NYISO's path is
year-invariant), and the unit-outage "MISSING 2022 + DEGRADED vintage" item (§3.1 — resolved by
the 2026-07-24 uniform pass and proven here by exact reproduction). Three defects are **new**
and were not in the register: D-1, D-2 and D-3.

---

## 7. RESOLUTION — all three defects closed (same session, 2026-08-14)

Owner direction after the Phase-1 report: *"Ok go get the data"*, then
*"Get 2018-2021 while you're at it"*. Done. Each fix uses the **same producer and
the same recipe** as the incumbent years, and in every case the recipe was
**verified against the committed 2023–2025 values before** the new years were
written — so the new rows rest on a construction proven to reproduce what is
already there. **Zero free parameters. No LP was solved.**

Applying these across the whole span (not just 2022) is what rule 22's
2026-08-06 clarification requires: an input is either the best measured
representation or it is not, and if it is, it belongs in **every** year.

### D-1 — RGGI allowance price: CLOSED, 2018–2022

Fetched RGGI, Inc.'s published *Allowance Prices and Volumes* table (the exact
source already cited for A59–A70) and landed **auctions A39–A58** as per-auction
rows in `data/raw/policy/carbon-auction-results/carbon-auction-results.csv`
(20 new rows; the datatype curates to 42).

**Recipe validation:** recomputing the incumbent years from the fetched table
reproduces the committed constants **exactly** — NYISO 13.49 / 20.71 / 22.09 and
NEISO 14.87 / 22.83 / 24.35 for 2023/2024/2025.

`STATE_CARBON_PRICE_BY_ISO` now carries, in $/short ton (NYISO, as published) and
$/tonne (NEISO, ×1.10231 — the existing harmonization asymmetry preserved):

| year | auctions | NYISO | NEISO |
|---|---|---|---|
| 2018 | A39–A42 | 4.41 | 4.86 |
| 2019 | A43–A46 | 5.42 | 5.97 |
| 2020 | A47–A50 | 6.41 | 7.07 |
| 2021 | A51–A54 | 9.47 | 10.44 |
| **2022** | **A55–A58** | **13.46** | **14.84** |

**2022 = $13.46/short ton**, so the omission measured in §2 is **$6.13/MWh**
(0.4558 tCO2/MWh-net × 13.46), 8.2 % of the 2022 RT mean — the "~$13" estimate
in §2 was sound, and the figure is now measured rather than assumed.

**A blocker inside the fix:** `curate_carbon_auction_results.py` hard-coded
`_QUARANTINED_YEARS = {2022, 2026}` and **raised** on those rows, citing rule 22.
That encoded the **pre-2026-08-06** regime the owner explicitly replaced ("this
REPLACES the former per-window intake authorization regime, which had it
backwards"), and it is *why* the constant had no 2022 key. Removed, with the
clarification quoted at the site. The spend gates are untouched and still live
where they belong (CLI year gate, D-6 quarantine, `audit_keepers`, the freeze) —
they gate solve/score/register, which this module does not do. Its test was
re-pointed from "rejects the year" to "intakes it".

**NEISO is extended too** (same auctions, same fetch). Declared blast radius:
NEISO's registered 2022 touchpoint `2026-08-06-neiso-2022-corrected-basis` is now
**stale w.r.t. HEAD** — it was scored with no RGGI cost. That is a NEISO-lane
call, flagged not actioned. CAISO is **not** extended: CARB comes from a source
that blocks automated fetches, so its 2018–2022 block stays an open CAISO-lane
gap (rule 25).

### D-2 — Central-East TTC: CLOSED, 2018–2022, and the trap is shut

Fetched **96 monthly NYISO MIS `atc_ttc` postings** (2018–2025, 0 failures) and
extended `derive_nyiso_central_east_ttc.py` to the full span. **Recipe
validation:** re-deriving 2023/2024/2025 reproduces the committed annual values
(1750 / 2850 / 2850) **and every committed monthly value, exactly**.

**The finding was worse than §2 estimated.** Measured 2022 annual mean is
**1,825 MW**, so the silent static fallback of 2,850 MW overstated Central-East
by **1,025 MW (+56 %)** — and the monthly detail is the real damage, because 2022
was mid-construction:

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | **Nov** | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| measured | 2625 | 2575 | 1575 | 1275 | 1125 | 2200 | 2475 | 2425 | 1700 | 1175 | **725** | 1975 |
| model would use | 2850 | 2850 | 2850 | 2850 | 2850 | 2850 | 2850 | 2850 | 2850 | 2850 | **2850** | 2850 |
| overstatement | 1.1× | 1.1× | 1.8× | 2.2× | 2.5× | 1.3× | 1.2× | 1.2× | 1.7× | 2.4× | **3.9×** | 1.4× |

**November 2022's real limit was 725 MW against a model 2,850 — 3.9×.** A 2022
C3c result on that input would have been meaningless.

Annual means now landed: 2018 **2475**, 2019 **2475**, 2020 **2400**,
2021 **2025**, 2022 **1825** — a physically coherent decline into the
construction period, then the post-upgrade step to 2850 in 2024.

**The structural half is done too.** Both appliers in `pipeline/ttc.py` now
**fail loud** instead of silently no-opping, scoped to years *at or beyond* the
table's span — a year *past* the table stays a no-op, because there the static
value is correct (it **is** this series' measured post-upgrade annual mean, and
the forward channel is the transmission-expansion registry on top of it). So
forecast runs and forward-edge probes are unaffected while the historical trap is
shut. Pinned by a new test; the existing forward-edge no-op test still passes.

### D-3 — SCR/EDRP Gold Book vintages: CLOSED, 2019–2022 (2018 is a real source gap)

The 2018–2022 Gold Books are **not** at the `20142/2226333/<year>-Gold-Book-Public.pdf`
pattern — every one 404s. They live under different Liferay document IDs and
filenames (`-Final-Public` plus a UUID path segment; 2018 under `20142/0` with a
different title entirely). All five fetched and committed alongside the existing
2023–2026 editions.

**Recipe validation:** a parser for the *Projection of SCR and EDRP Enrollment*
table reproduces the committed 2023/2024/2025 transcriptions **exactly** — 33
zone-rows × 4 values, zero diffs — before being used on the new years.

**2018 is MEASURED-ABSENT, and is recorded as a negative result rather than
forced.** That edition has **no per-zone table at all**: it reports NYCA totals
only (p.39 prose — summer SCR 1,219 MW / EDRP 18 MW, winter 884 / 45 — and
Tables IV-1a/IV-1b). The zonal projection table first appears in 2019. Splitting
the 2018 total by another year's zonal shares would be a fabricated input
(rule 14; "never pad, proxy or force"), so it was not done. No practical loss:
2018 was dropped from the program span on 2026-08-06 and is locked-tier,
i.e. unsolvable regardless.

**A second, hidden defect found while fixing this one.** Landing the vintages
changed nothing at first: `nyiso_demand_response` hard-coded
`_MIN_GB_YEAR = 2023` / `_MAX_GB_YEAR = 2025`, so the clamp still floored every
earlier year at 2023 **even with the data present**. The bounds are now **derived
from the CSV**, so adding a vintage is a pure data change and this class of
silent-substitution cannot recur. Each year now resolves to its own vintage:

| solve year | 2019 | 2020 | 2021 | **2022** | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| summer DR MW | 1314.0 | 1288.0 | 1199.0 | **1169.8** | 1234.4 | 1294.4 | 1487.9 |

2022 moves **1234.4 → 1169.8 MW**, a 64.6 MW correction — inside the 60–190 MW
band §2 predicted, and at a $500/MWh strike.

### What is still open

1. **The holdout spend freeze is ACTIVE** and untouched. It is now the *only*
   thing between here and the 2022 touchpoint; the data objection is withdrawn.
   Lifting it remains an owner action naming the spend.
2. **Import-tranche reproduction quality** (§4.2) — the register's disclosed
   719 MW duration RMSE for 2022 vs ≤328 MW in-sample. Still **not
   re-measured**; it should be graded before the touchpoint is quoted.
3. **The Transco Dec-2022 Elliott hole** (§4.1) is unchanged and unfixable from
   the free archive — disclose it before quoting any Dec-2022 or winter-tail
   result.
4. **CAISO 2018–2022 CARB prices** and **NEISO's now-stale 2022 touchpoint** —
   both flagged above, both other lanes' calls.

### Verification

`ruff check` clean; `ruff format --check` clean; mechanism-matrix guard exit 0
(integrity OK, keeper stamps match). Full suite: **6,849 passed, 21 failed** —
and **all 21 are pre-existing or test-isolation artifacts, none from this work**,
established by re-running the same failures on a stashed pristine tree (18
reproduce identically; the 2 ERCOT `retirement_rule='pipeline'` failures
reproduce on the untouched tree; the 1 `consume_phase3d` failure passes in
isolation, an ordering artifact). New tests were added for the TTC fail-loud
guard and for per-vintage SCR/EDRP resolution.

The raw ATC/TTC postings (~17 MB) are **not committed** — unverified
redistribution terms, following the existing `ATC_TTC.zip` precedent — but the
deriver prints the exact per-month re-fetch command when they are absent, so the
derivation is reproducible from a bare checkout. The Gold Book PDFs **are**
committed, matching the precedent for the 2023–2026 editions.
