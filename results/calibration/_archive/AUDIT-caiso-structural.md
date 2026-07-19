# CAISO backcast — structural input audit (2026-06-16)

Branch: `claude/caiso-structural-audit-xcsubz`. Scope: audit the **structural**
inputs (capacity, must-run, BTM, outages, zonal allocation, imports, market
design) to the CAISO backcast so that later offer-curve tuning dials in a model
whose physics are already correct — not one where the offer curve silently
compensates for a structural error. **Read-only diagnosis + surgical structural
fixes only. No `offer_curve_by_group` / band-multiplier changes** (that is the
next phase).

Baseline: `results/calibration/caiso_tune0_base` — a clean 3-year run on current
main + the committed per-tranche border-carbon fix:
`run_calibration_full.py --iso CAISO --year 2023 2024 2025 --commitment
--priced-interchange`. All numbers below are from this clean baseline (the prior
session's directional numbers predated the rebase and used uncommitted offer
deltas).

## Clean-baseline scorecard

| Year | model gas (cc+ct+st, incl CHP) | EIA-923 gas ref | EIA-930 gas | net import (target) | export-hrs | LMP mean (actual RT) | LMP min (actual min) |
|---|---|---|---|---|---|---|---|
| 2023 | 63.5 | 76.0 | 87.8 | **43.0 (28.5) → +14.5** | 0.0% | $84.2 (no actual) | $8.0 (—) |
| 2024 | **67.95 ≈ EIA-923 67.68** | 67.7 | 85.4 | 35.7 (30.8) → +4.9 | 0.0% | $57.4 ($32.9) → +$24 | $28.0 (−$40.6) |
| 2025 | 76.8 | 55.2 (incomplete) | 79.0 | 38.2 (35.8) → +2.4 | 0.0% | $63.1 ($33.6) → +$29 | $42.2 (−$39) |

All units TWh / $·MWh⁻¹. "EIA-923 gas ref" = `calibration_reference.json`
`generation_twh` (gas_cc+gas_ct+gas_st, by fuel incl. CHP). EIA-930 gas =
`NG: NG`. Actual LMP = `inputs/calibration/actual_lmp.json["CAISO"]` RT.

## Headline findings

1. **The "−9 TWh gas gap" vs EIA-930 is largely a benchmark-classification
   artifact, not a structural gas deficit.** EIA-930 CISO reports **no
   geothermal** (`NG: GEO` is 100 % NaN in 2023/24) and no biomass, so its
   `NG: NG` gas figure silently absorbs the ~8 TWh geothermal (The Geysers) +
   ~3 TWh biomass that EIA-923 and the model break out separately. For 2024
   (complete data) the model's **total gas (67.95) matches the EIA-923 reference
   (67.68) to <0.5 %**; the gap only appears against EIA-930's geo/bio-inflated
   85.4. **Do not raise the offer curve to "fix" the 2024 gas gap** — it is the
   wrong benchmark. (2023 gas *is* genuinely ~12 TWh low, but from over-import,
   not gas supply — see items 1/10.)

2. **The LMP error is an over-priced midday FLOOR, not a missing evening tail.**
   Model min price is **$28 (2024) / $42 (2025) and never reaches ≤ $0**; actual
   CAISO has p5 = −$10, min ≈ −$40. The floor is set jointly by (a) the model
   **importing in ~100 % of hours** (cheapest active import tranche PNW-hydro/
   midC at $28–36 floors the price) and (b) **gas_cc committed in 100 % of
   spring-midday hours** (mean 1.9 GW, never fully decommits). A scarcity adder
   (ORDC/AS) only lifts the tail and would make the floor worse — **do not add
   one to chase the fit.**

3. **The model never swings to export.** Real CAISO interchange swings from
   −6 GW (import, overnight) to **+2 GW (export, midday)**, exporting in 46–58 %
   of spring-midday hours. The model imports a **flat 4.6–5.3 GW all day, 0.0 %
   export hours**. This single structural defect is the root of both the high
   midday floor and the zero curtailment.

4. **The prior "over-flat solar" hypothesis is wrong.** Model solar shape
   matches EIA-930 (peak/24h-mean 2.63 vs 2.61). Model solar (39.8 TWh 2023)
   slightly *exceeds* EIA-930 grid solar (37.1) — consistent with the model
   **under-curtailing** the ~2.5 TWh that real CAISO curtails — but the shape is
   correct.

---

## Item-by-item

### 1. Zonal totals vs EIA-923 — PASS with two caveats
Aggregated EIA-923 plant-level net generation to the model zones via
`zone_assignment.build_zone_lookup("CAISO")` (the same lat/lon/FIPS logic) and
compared to the model per-zone dispatch (`dispatch/<year>_P2.parquet`).

EIA-923 zonal (TWh, 2024): solar SP15 33 / ZP26 10 / NP15 6; wind ZP26 7.8;
hydro NP15 19.8; nuclear NP15 18.4; geothermal NP15 6.9 / ZP26 0.9.
Model zonal placement of solar (SP15-heavy), wind (ZP26), hydro (NP15) and
nuclear (NP15) all track EIA-923 to within a few %. **PASS.**
- `WECC_import` carries **zero in-state generation** (it is the priced
  import/export node only) — confirmed. **PASS.**
- **Caveat A — geothermal mis-zoned.** Geothermal is injected as part of the
  "OTHER" must-run, allocated **by zone demand share** (`_must_run_profiles`,
  `run_calibration_full.py:678`), so it lands SP15-heavy (NP15 3.6 / SP15 5.1 /
  ZP26 0.6 in 2023). Physically The Geysers is ~87 % NP15. Energy total is right;
  the zonal split is wrong. Minor (affects NP15/SP15 spread, not system LMP).
- **Caveat B — 2023 gas under-allocated** (model 63.5 vs EIA-923 ~76–80), the
  symptom of the 2023 over-import (item 10), not a zone-assignment error.

### 2. Capacity correctness — PASS
- **Solar:** capacity ~22 GW (`constants.py`), profile from measured EIA-930 /
  CAISO-HSL hourly shape (`renewables.py`), vintage-ramped by EIA-860 COD.
  Shape is correctly midday-peaked (item-4 headline). Model dispatches ~2.5 TWh
  more than EIA-930 grid solar → **under-curtailment** (the surplus is absorbed
  into load/storage instead of curtailed/exported — ties to items 6/9/10). No
  BTM double-count: `td_loss_factor=0`, EIA-930 demand is generation-side and
  already nets BTM solar.
- **Storage:** EIA-860 fleet, vintage-ramped (`storage_vintage_ramp=True` for
  CAISO). Year-end power **9.6 / 13.2 / 17.5 GW** (Li-ion + 2.1 GW pumped) for
  2023/24/25 — correctly sized to the real ~7–8 / ~10–11 / ~13–15 GW build-out.
  **PASS.**
- **Nuclear:** Diablo Canyon 2,240 MW, monthly-CF refuel pattern. **PASS.**
- **Wind:** matches EIA-930 (16.5 / 20.3 / 19.8). **PASS.**

### 3. Must-run floors — the price-floor co-driver
Enumerated CAISO must-run/min-gen:
- **Nuclear** — availability-capped by monthly CF, no hard Pmin. ~1.8 GW midday.
- **Geothermal + "OTHER"** — injected as flat must-run netted from demand
  (`_INJECTED_MUSTRUN_CLASSES`). ~0.9 GW midday.
- **Biomass** — kept as LP units for CAISO (skipped from injection). ~0.46 GW.
- **CHP steam-following** (`chp_steam_following=True`) — per-plant grid-delivered
  flat floor minus BTM (item 4). CA CHP is small.
- **gas_cc committed band** — *the* floor driver. In 2024 spring-midday (11–14h),
  **gas_cc is committed in 100 % of hours, mean 1.9 GW, min 8 MW, p5 733 MW** —
  it never fully decommits through the solar glut, so the committed-band bid
  sets the clearing price (~$36) when real CAISO has free renewables/exports
  marginal. Aggregate inflexible midday floor ≈ nuclear 1.8 + geo/other 0.9 +
  biomass 0.5 + gas_cc ≥0.7 ≈ **~4 GW**, on top of a flat 2.8 GW import.
- No hydro/biomass/geothermal *hard* must-run; gas_st summer/off-season must-run
  flags are **off** for CAISO. Petra Nova / ERCOT `CHP_PMIN_CF_BY_PLANT` do not
  apply to CAISO.

Root cause read: the floor is **not** an over-large physical must-run; it is
gas_cc failing to decommit midday (committed-tranche structure / P2 screen) **and**
the flat midday import (item 10) keeping residual load positive. Fixing either
unlocks the spring lows. The decommit lever borders on offer-curve territory
(committed band) — flagged for the next phase, not changed here.

### 4. BTM on CHP steam cogen — PASS (small for CAISO)
`chp_steam_following=True`; BTM self-supply split by sector
(`CHP_BTM_PCT_BY_SECTOR`: merchant 35 %, industrial/commercial 50 %, ST_CHP
90 %) is netted off-grid; the grid-delivered steam-following min-gen is the
flat residual. CA CHP fleet is modest (CC_CHP 8.8 + CT_CHP 6.6 TWh in 2024), so
its contribution to the midday floor is secondary to gas_cc. No change.

### 5. Ancillary services / reserves — genuine market-design omission (decide w/ user)
**Correctness:** AS is core CAISO market design. CAISO **co-optimizes energy +
AS** in the IFM (day-ahead) and RTUC/RTD (real-time): four products (Reg Up,
Reg Down, Spin, Non-Spin), each market-cleared; requirements bind (contingency
reserve ≈ max(largest contingency, 5 % hydro + 7 % thermal) per WECC/NERC).
Because it is co-optimized, capacity held for reserves is **withheld from
energy** — a real coupling the model currently omits (no reserve requirement, no
AS carve-out for CAISO). So the model is **incomplete** here, independent of fit.
**Fit:** an AS-reserve-withholding carve-out (the ERCOT `as_reserve_withholding`
mechanism) lifts *tight-hour/evening* prices. CAISO's dominant error is the
*midday floor*, so adding it naively would worsen midday and mask the cause.
**Recommendation:** worth adding for fidelity, but **with** the reserve
requirement and **after** the floor is fixed — not as a fit-patch. Needs CAISO
OASIS cleared-AS data (`queryname=AS_RESULTS`/`AS_REQ`, free, no auth);
`scripts/fetch_caiso_oasis.py` can be extended to pull it. **Do NOT port the
ERCOT ORDC** post-solve overlay — CAISO is RA-backed ($2,000 cap, no ORDC) and
the model already over-prices.

### 6. VOLL / scarcity / negative prices — structural floor confirmed
- VOLL = $2,000 (`iso_configs.py`), the slack price. Slack does **not** spuriously
  bind (model max LMP $83.7 in 2024, well below cap) — no false scarcity.
- Export sinks exist (`export_solar` 2,500 MW @ $8, `export_curtail` 4,000 MW @
  $0) and **can** drive price to $0, but they **never engage** because the model
  is a net importer every hour. The model min price ($28/$42) = the cheapest
  *active import tranche* (PNW-hydro $28), never the export/curtail floor or
  negative. **What prevents ≤ $0:** the model imports in ~100 % of hours, so the
  marginal resource is always ≥ the cheapest import block — it never has surplus
  to push into the export sink. Ties directly to items 3/10.

### 7. Unit-outage overlay — PASS
Source `inputs/raw-data/campd-unit-outages-CAISO.csv` (1,961 observed CAMPD
maintenance windows across 64 CA gas/CC plants) → 229 / 229 / 261 plant-tranches
derated for 2023/24/25. Coverage is sensible (limited to CO₂-reporting thermal,
mostly CA gas — exactly the relevant fleet). It is observed, not over-derating,
and since the model *under*-prices the tail it is not silently removing
tail-needed capacity or pinning units. **PASS, no change.**

### 8. Hydro — FIXED (2025 −9 TWh repin)
2025 model hydro budget was **12.32 TWh vs 21.3 actual (−9)**. Root cause: the
2025 EIA-923 is an early release carrying only 26 of ~185 plants. The repin
mechanism (`--hydro-eia930-monthly` → `measured_monthly_hydro` →
`load_hydro_budget(monthly_target_mwh=…)`, NEISO-2025 precedent) existed but was
**silently broken for CAISO 2025**: `measured_monthly_hydro` used the strict
8760-hour frame loader, which rejects the CISO 2025 extract (8,751 local-year
rows, 9 short of a clean year), so the repin no-oped on the one year it is meant
to fix. **Fix applied** (`eia_loader.measured_monthly_hydro` now uses the
gap-filling frame loader) — see "Fixes applied". 2023/24 and
NEISO/NYISO/ERCOT/SPP 2025 are byte-identical (their strict frames already load).

### 9. Demand / interchange shape + duck curve — structural root cause
- `td_loss_factor=0`, generation-side demand; priced-interchange path consistent
  (no double count). **PASS.**
- **Duck curve — the structural cause of the floor.** Real CAISO 2024 spring
  net-load bottoms ~+2–3.3 GW midday but interchange **swings to +2.3 GW export**
  and gas runs 6–7.7 GW (not price-setting — curtailable solar/exports are
  marginal). The model's net interchange is **flat ~4.6–5.3 GW import all day,
  0.0 % export**, so its midday net-load served by domestic thermal stays high,
  gas_cc stays marginal, and the price floors. This is the single highest-value
  structural defect.

### 10. Import-node seasonality / shape — root of floor + cross-year volume
CAISO uses a **static** 6-tranche import curve (`IMPORT_TRANCHES["CAISO"]`,
11.4 GW) with **no per-year ladder** (`IMPORT_TRANCHES_BY_YEAR` has no CAISO
entry) and **no time-of-day/seasonal shape**. Two consequences:
- **Over-volume, non-uniform:** +14.5 TWh (2023), +4.9 (2024), +2.4 (2025). The
  cheap-gas 2023 ($2.54) over-imports most because the static tranche prices sit
  below domestic gas merit order. A **per-year ladder** (raising 2023 import
  prices) addresses the cross-year tension — `build_import_generators` already
  takes `year` and applies `IMPORT_TRANCHE_EF`, so a CAISO ladder slots in.
- **Flat shape → the floor:** a single static curve clears a near-constant import
  every hour and **cannot swing to export midday**, which is the duck-curve
  defect of item 9. Capturing spring PNW-hydro midday abundance (cheap imports
  that crash spring prices) **and** the midday export needs **time-of-day /
  seasonal import-availability shaping** — a market-design change.
**Recommendation:** per-year ladder = correction (do, with care re circularity);
daily/seasonal shaping = market-design addition (decide with user). Both are
larger than a surgical fix and are **not** applied here.

### 11. Anything else
- **Geothermal (~8 TWh):** modeled (injected via "OTHER" must-run, energy from
  EIA-923) but **mis-zoned** (demand-share, item 1) and **invisible in EIA-930**
  (`NG: GEO` all-NaN → folded into `NG: NG`, item-1 headline). The single most
  consequential reporting quirk in the CAISO benchmark.
- **Biomass over +2.3 TWh** (model 5.37 vs EIA-923 3.06 in 2024) — CAISO keeps
  biomass as LP units that over-run; displaces ~2 TWh gas. Minor; a candidate
  targeted fix (inject biomass as must-run at EIA-923 level, like geothermal) but
  it changes merit order, so flagged not applied.
- **Gas price:** SoCal basis handled via measured EIA-923 ISO-month delivered gas
  (`gas_monthly_actuals`) + daily Henry-Hub shape — correct.
- **CARB carbon** applied to in-state fossil MC (`carbon_price=0` → state program)
  and to import tranches by per-tranche EF (committed fix) — correct.

---

## Ranked structural fixes (before offer-curve tuning)

**Corrections — do now (surgical, clearly correct):**
1. ✅ **2025 hydro repin** (`measured_monthly_hydro` gap-filling-loader fix +
   `--hydro-eia930-monthly`). Applied + tested. Recovers 12.3 → 21.3 TWh. (See
   before/after below.)
2. **Score CAISO gas against EIA-923, not EIA-930** (documentation/analysis
   correction — the model is already correct). Prevents mis-tuning the offer
   curve to close a phantom ~9 TWh gap that is geo/bio fold-in. No code change to
   the model; update the calibration framing (this doc supersedes the prior
   SUMMARY's EIA-930 gas targets).

**Market-design additions — decide with the user (do NOT apply as fit-patches):**
3. **Import-node daily/seasonal shaping** (item 9/10) — the highest-value lever
   for the midday floor and the export swing. Time-of-day import availability so
   the node imports overnight and exports midday.
4. **CAISO per-year import ladder** (item 10) — fixes the cross-year over-import
   (especially 2023). Smaller scope than #3; can be done together.
5. **AS co-optimization / reserve requirement** (item 5) — genuine market-design
   omission; add *after* the floor is fixed, with OASIS cleared-AS data.

**Next-phase (offer curve, out of scope here):**
6. gas_cc midday **decommit** (committed-tranche structure / P2 screen) — the
   other half of the floor; borders offer-curve tuning.

**Optional / low-priority structural tweaks:**
7. Geothermal zonal placement (NP15 vs demand-share) — item 1 caveat A.
8. Biomass over-generation cap (−2.3 TWh) — item 11.

---

## Fixes applied (this session)

### Fix 1 — `measured_monthly_hydro` gap-filling loader (2025 hydro repin)
`src/market_sim/data/eia_loader.py`: `measured_monthly_hydro` now loads the
gap-filling EIA-930 frame (`_eia_hourly_frame_filled`) instead of the strict
8760-hour frame, so the current-year extract (CISO 2025 = 8,751 local-year rows)
no longer makes the EIA-930 repin silently no-op. Tests:
`tests/test_hydro.py::TestCAISOHydroBudget::test_measured_monthly_hydro_repins_incomplete_2025`,
`::test_2025_eia930_repin_recovers_full_budget`.

Byte-identical for every ISO whose strict frame already loads (NEISO/NYISO/
ERCOT/SPP 2025) and only active under the opt-in `--hydro-eia930-monthly` flag.

**2025 before/after** (`caiso_tune0_base` vs `caiso_hydro2025_fix`, the fixed run
adds `--hydro-eia930-monthly`):

| metric | before | after | reference |
|---|---|---|---|
| hydro (TWh) | 12.32 | **19.73** | 21.3 |
| gas cc+ct+st (TWh) | 76.80 | 70.08 | EIA-930 79.0 |
| net import (TWh) | 38.16 | 37.54 | 35.8 |
| LMP mean ($) | 63.08 | 60.00 | RT 33.6 |
| LMP min ($) | 42.18 | 39.97 | −39 |
| Apr LMP ($) | 47.6 | 46.3 | RT 19.9 |

The repin recovers +7.4 TWh of hydro, displacing ~6.7 TWh gas and ~0.6 TWh
import, and shaves the whole monthly LMP curve ~$2–3 (it does **not** fix the
floor — that is the import-shape / commitment issue, items 9/10/3, as expected).

**Recommended production flag combo:** `--hydro-backfill-year 2024
--hydro-eia930-monthly`. The eia930-monthly leg alone repins only the 26 survey
reporters, scaling them so hard that some hit their MW ceiling (21.32 TWh budget
but only 19.73 deliverable). Backfilling the ~134 non-reporting plants from 2024
first restores the full MW envelope; the eia930 repin then pins the total, giving
160 plants / 21.29 TWh deliverable (vs 20.39 for backfill alone, which carries
2024's wetness). The demonstration run above used eia930-only to isolate the
loader fix; the keeper should use both.

**Jacobian:** not re-derived — the hydro fix changes the 2025 hydro *level*, not
the thermal-class merit-order band sensitivities the offer-curve Jacobian
measures.

---

## Phase 2 — interchange shaping result + corrected floor diagnosis

### Fix 2 (built, default-off) — measured interchange shaping
`transmission.inject_interchange_shape` + `eia_loader.measured_interchange_envelope`
shape the priced node's import-tranche availability and export-sink floor by the
measured EIA-930 month×hour-of-day net-interchange envelope (p90), so the node
imports overnight and can export the midday surplus instead of clearing a flat
all-hours import. Opt-in via `--interchange-shaping` / `config.interchange_shaping`
(default off; byte-identical for every other run/ISO). Tests:
`tests/test_transmission.py::TestInterchangeShaping`,
`tests/test_eia_loader.py::TestInterchangeEnvelope`.

**Result — NEGATIVE for the floor (do not enable for the keeper):**

| metric (2024) | before (flat node) | after (shaped) | actual |
|---|---|---|---|
| net import (TWh) | 35.7 | 18.2 | 30.8 |
| spring-midday import (MW) | 2308 | 119 | ~ −1500 (export) |
| export hours | 0.0 % | 0.0 % | ~11 % |
| LMP mean ($) | 57.4 | 64.7 | 33.0 |
| LMP min / p5 ($) | 28 / 39 | 32 / 44 | −41 / −10 |
| gas (TWh) | 67.95 | 85.1 | EIA-923 67.7 |

The diurnal shape *worked* (midday imports backed off 2308→119 MW), but the floor
went **up**: capping the cheap midday import ($28 PNW) just substituted ~$40
domestic gas as the marginal unit. The model **still never exports (0 %)** because
it is never *long* — in the 400 cheapest shaped hours it imports only 332 MW and
gas_cc is committed in 100 % of them.

### Corrected floor diagnosis
CAISO's over-priced midday floor is **not** an interchange artifact. Root cause:
**the model is never long midday** — supply never exceeds demand, so the marginal
resource is always domestic gas or a priced import (≥ ~$28–40); it can never reach
the export sink ($8/$0) or negative prices because it has no surplus to dump.

Real CAISO *is* long midday (it exports ~+2 GW and curtails), which is why its
prices collapse to ~$0/negative. Two market-design mechanisms make it long that
the model lacks:
1. **RA must-offer commitment** — Resource-Adequacy gas stays online at min-load
   through midday (can't economically cycle off for the evening ramp) → forced
   oversupply. The model instead economically *decommits* gas to ~2 GW midday and
   imports the rest, staying balanced.
2. **Negative renewable offers** — CA solar/wind bid below $0 (RPS/REC/PTC value)
   in oversupply; the model's solar is must-take at $0 and never marginal.

The earlier-session hypotheses ("over-flat solar", "let gas decommit midday") and
this session's first instinct ("the flat import node floors price") are all
**wrong about the mechanism**: the floor is a *longness / marginal-offer*
phenomenon (RA commitment + renewable bidding), not capacity, solar shape, or
interchange.

### Next phase — three parallel workstreams (see `results/calibration/NEXT-caiso-floor-prompts.md`)
1. **RA must-offer minimum-commitment floor** — make the model long midday (the
   real floor fix).
2. **Negative / curtailable renewable offers** — price the surplus at ≤$0 (the
   negative tail); pairs with (1) and with the shaped export envelope (Fix 2).
3. **AS reserve-requirement formula** (WECC MORC, default-off) — the evening tail;
   independent of the floor; placeholder until OASIS cleared-AS data can be pulled
   (outbound network is blocked in the remote env, so OASIS is currently
   unreachable).
