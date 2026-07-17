# FF-0D — Forward-inputs & policy currency audit (2026-07)

**Session.** Wave-0 lane **L-INP** of the Forecast Finalization Program
(`docs/forecast-development-plan-2026-07.md` §6, FF-0D). **Audit only — no source
default was changed** (rules 5/13/14/23 read as binding). Verified against
`origin/main` HEAD `67e64ed` (2026-07-17). Findings feed the Wave-1 fix sessions
**FF-1C** (demand/DC currency + hydro fix) and **FF-1E** (entry-cost & policy
wiring); the prioritized list is §7.

**Method.** Read each forward input at HEAD, traced its citation, and confronted
it against the latest published source. Public documents were fetched via
WebSearch where the proxy allowed (headline figures below carry their URL); exact
per-year anchor tables inside large PDFs/XLSX and two blocked domains
(`atb.nrel.gov`, `federalregister.gov`) are logged as **MANUAL DOWNLOADS NEEDED**
(§7.3) — **no value was guessed** (rule 5). Refresh-channel reachability was
probed directly (OEDI S3 for ATB, EIA API for AEO).

**Verdict key.** `CURRENT` = latest available vintage, correctly wired ·
`STALE` = a newer published vintage exists · `UNWIRED` = present but not
reaching the solve (or shipping empty/fallback where a real source now exists) ·
`HAZARD` = wired but composes incorrectly with another input · `BUG` = defect ·
`OPTION` = design choice surfaced for the owner, decided nowhere here.

---

## 0. Verdict summary

| # | Forward input | Symbol / file | Verdict | Headline |
|---|---|---|---|---|
| 1a | Demand growth, 5 ISOs | `DEMAND_GROWTH_RATES` (constants.py:779) | **STALE** | 2024-vintage ISO forecasts; all superseded by 2025/2026 editions; PJM/NYISO/NEISO carry literal `TODO: verify` |
| 1b | Demand growth, **MISO** | (absent from the dict) | **UNWIRED** | MISO has no entry → flat **1%/yr** scalar fallback vs a published **+35% by 2035** forecast |
| 1c | DC block, 4 ISOs | `DATACENTER_ADDITIONS_MW` (constants.py:829) | **CURRENT (envelope)** | 2025-vintage anchors, consistent with latest forecasts; refine envelope→MW-by-year |
| 1d | DC block, MISO/NEISO | same, `{}` entries | **STALE / UNWIRED** | ship 0 MW; MISO now publishes a strong DC decomposition; ISO-NE 2026 CELT added a large-load framework |
| 1e | DC zonal siting | `DATACENTER_ZONE_SHARE` (constants.py:888) | **UNWIRED** | `{}` → load-share; ERCOT North/West + PJM Dominion siting is published |
| 1f | Growth × DC decomposition | `DEMAND_GROWTH_RATES` near rates | **HAZARD** | near rates still embed DC (CX-4 §3.5 co-change never landed); DC block is double-count-safe **only while `datacenter_load_path="off"`** |
| 2a | Gas / coal / oil paths | `HENRY_HUB_TRAJECTORIES`, `COAL_PRICE_TRAJECTORIES`, `OIL_PRICE_TRAJECTORIES` | **STALE (1 vintage)** | AEO2025-derived; AEO2026 exists & is API-fetchable; near-term reference gas sits **below** STEO Jul-2026 |
| 2b | Uranium / coal level / biomass | `NUCLEAR_FUEL_PRICE_HISTORICAL`, `COAL_PRICE_BASE`, `BIOMASS_PRICE_PER_MMBTU` | **CURRENT** | uranium derived to 2024 then hold-flat (no forward source exists — honest); coal level anchors AEO2024 |
| 3a | New-entry costs | `NEW_ENTRY_COSTS` (constants.py:4119) | **STALE + UNWIRED** | hardcoded "ATB 2024"; **not** read from the on-disk ATB parquet; ATB 2025 released 2025-07-01 |
| 3b | Tech-cost uncertainty spreads | `TECH_COST_MULTIPLIERS` (constants.py:4200) | **STALE (self-flagged)** | low/high spreads are engineering judgment, **not** ATB — now derivable from the on-disk Advanced/Conservative scenario column |
| 3c | Emerging tech | CCUS/H2/geothermal/offshore param dicts | **CURRENT-vintage** | consistent with on-disk ATB 2024; same wire/refresh path as 3a/3b |
| 3d | Financing basis | `real_discount_rate` (single) vs ATB per-tech WACC | **OPTION** | present the per-tech WACC option; decide nothing |
| 4a | IRA / OBBBA cliffs | `policy/ira.py` + `scenarios.py:480-526` | **CURRENT** | 2027 wind/solar cliff, 45U 2032, 45V 2027, 45Q 2032, other-clean 2033/34/35/36 — all OBBBA-cited |
| 4b | 45Y/48E phase-down years | `ira_other_clean_*` | **CURRENT w/ open caveat** | triangulated from 2 secondary sources; primary Fed-Register confirmation still a MANUAL DOWNLOAD |
| 4c | State RPS / ACP | `STATE_RPS_FLOORS`, `STATE_RPS_ACP` (constants.py:3956) | **CURRENT-ish (Tier 3)** | policy schedules current; PJM blend load-weights `TODO verify`; ACP order-of-magnitude |
| 4d | Confirmed retirements | `data/raw/confirmed-retirements/` | **CURRENT (2026-07-05)** | re-verified 12 days ago; pending items self-flagged in-registry |
| 5a | EIA-860 planned pipeline | `EIA860_OPERABLE_VINTAGE=2025` (fleet.py:6458) | **CURRENT** | 2025 Early Release; no 2026 vintage exists yet (EIA has not published it) |
| 5b | Weather-year pool | `WEATHER_YEAR_POOL*` (constants.py:4967) | **CURRENT** | widened 2026-07; default `weather_year=2024` |
| 5c | Hydro forecast fleet | `data/hydro.py:265` | **BUG** | exact-year filter zeros conventional hydro every year past the last EIA-923 vintage; charter for FF-1C |
| 6 | FC-5 benchmark tables | FF-0A inventory | **PLACEHOLDER** | FF-0A (rubric + `scripts/forecast_verdict.py`) not merged at HEAD — §6 is a stub |

**One-paragraph read.** The **policy** layer (IRA/OBBBA, confirmed retirements) and
the **fleet-snapshot** layer (EIA-860 2025 ER, weather pool) are current and well
cited — leave them. The **demand** layer is the stale frontier: five ISOs on
2024 forecasts, MISO on a 1%/yr fallback while it publishes the largest DC-driven
outlook in the country, and a latent double-count that makes the (already-landed)
DC block unusable at anything but `off` until the CX-4 §3.5 decomposition lands.
The **cost/fuel** layer is one vintage behind (AEO2025, ATB 2024) *and* the ATB
values are hand-transcribed rather than read from the parquet already on disk —
so FF-1E can close the largest self-flagged gap (`TECH_COST_MULTIPLIERS`) with
**zero network** by wiring the on-disk file. One outright **bug** (hydro).

---

## 1. Demand growth + data-center block

### 1.1 `DEMAND_GROWTH_RATES` — STALE (all 5 present ISOs)

At HEAD the dict (constants.py:779-811) is sourced to **2024** ISO documents:
header cites *"EIA STEO July 2025, ERCOT CDR Dec 2024, CAISO IEPR 2024"*; PJM
cites *"PJM Load Forecast Report 2024"* with a literal **`TODO: verify`**; NYISO
cites *"Gold Book 2024"* + `TODO: verify`; NEISO cites *"CELT 2024"* + `TODO:
verify`. Every one of those has a newer edition:

| ISO | HEAD mid near/long | Latest published forecast (2025/2026) | Assessment |
|---|---|---|---|
| ERCOT | 0.05 / 0.025 | **2025 LTLF3**: peak → **139 GW by 2030**; a **preliminary 2026–2032 LTLF** was released 2026-04-15. LFL energy +~60% y/y into 2025. | Near-term likely low vs the LFL surge; refresh to LTLF3 / 2026 preliminary. |
| PJM | 0.035 / 0.018 | **2026 Load Forecast (posted 2026-01-14)**: summer peak **160→222 GW by 2036** (10-yr **+3.6%/yr**), 253 GW by 2046 (20-yr +2.4%/yr); near-term **trimmed** on stricter DC vetting. | **Long-era 1.8% understates** DC-driven growth that the 2026 forecast sustains well past the 2030 transition. |
| CAISO | 0.015 / 0.010 | **2025 IEPR / CED 2025-2045**: 1-in-2 peak **46.1 (2025) → 52.9 GW (2030, +15% ≈ 2.8%/yr) → ~68 GW (2040)**. | Near-era 1.5% is low vs the ~2.8%/yr CEC peak path; refresh IEPR 2024→2025. |
| NYISO | 0.015 / 0.010 | **2025 Gold Book** published (baseline tables XLSX available). | Vintage bump 2024→2025; exact MW-by-year needs table extraction (§7.3). |
| NEISO | 0.015 / 0.010 | **2026 CELT (May 2026)**: net energy 116,679 (2025) → 127,660 GWh (2035, ~1.0%/yr); winter net peak **20,483 (2026/27) → 26,411 MW (2035/36)** (~2.6%/yr). First large-load & battery forecasts added. | Vintage bump 2024→2026; peak path steeper than the flat 1.0% long rate. |

Sources: ERCOT [LTLF / news](https://www.ercot.com/news/release/04152026-ercot-releases-preliminary),
PJM [2026 Load Report](https://www.pjm.com/-/media/DotCom/library/reports-notices/load-forecast/2026-load-report.pdf) ·
[Inside Lines](https://insidelines.pjm.com/pjms-updated-20-year-forecast-continues-to-see-significant-long-term-load-growth/),
CAISO [CED 2025-2045 / 2025 IEPR](https://www.energy.ca.gov/data-reports/reports/integrated-energy-policy-report-iepr/2025-integrated-energy-policy-report-0),
NYISO [2025 Gold Book](https://www.nyiso.com/documents/20142/2226333/2025-Gold-Book-Public.pdf),
ISO-NE [2026 CELT](https://isonewswire.com/2026/05/01/iso-ne-forecast-shows-steady-increase-in-regional-electricity-use-through-2035/).

> **Benchmarks are context, not fit targets (rule 13).** These numbers scope
> *what a current forecast says*, so FF-1C swaps a stale published vintage for a
> current one — a source-driven re-derivation (rule 23), never a nudge toward a
> backcast residual.

### 1.2 MISO — UNWIRED (the single largest demand gap)

`DEMAND_GROWTH_RATES` has **no MISO key**. `resolve_demand_growth_rate`
(scenarios.py:6457-6460) resolves a missing ISO to the scalar
`config.demand_growth_rate`, whose default is **`0.01` (1%/yr flat)**
(scenarios.py:162). Meanwhile MISO's own **September-2025 Long-Term Load
Forecast** projects peak **121 GW (2025) → ~163 GW by 2035 (+35%, ≈3.1%/yr)**,
with **8–14 GW of data centers in 2026–2027 alone** and DC reaching ~20% of MISO
energy by 2030. A 1%/yr flat forecast for the ISO with arguably the steepest
DC-driven curve is a structural currency defect, not a rounding error.
Source: [Utility Dive](https://www.utilitydive.com/news/miso-long-range-forecast-data-center/817917/),
[RTO Insider](https://www.rtoinsider.com/130187-miso-load-forecast-165gw-peak-2035/).

**FF-1C action:** add a MISO `DEMAND_GROWTH_RATES` block (low/mid/high near+long)
from the Sept-2025 MISO LTLF, and a MISO `DATACENTER_ADDITIONS_MW` block (§1.4).

### 1.3 `DATACENTER_ADDITIONS_MW` — CURRENT (envelope) for 4 ISOs; empty for MISO/NEISO

The block mechanism **has landed** (`data/datacenter.py::resolve_datacenter_mw`,
threaded into runner demand assembly; `datacenter_load_path` default `"off"` ⇒
byte-identical to today). Anchors were extracted as **envelope values** from the
CX-4 memo §2.1 headline figures (each traced in-line, constants.py:829-879):

- **ERCOT** mid 37 GW / high 122–158 GW by 2030–2035 — consistent with the 2025
  LTLF3 138–139 GW-by-2030 adjusted peak.
- **PJM** mid 30 GW by 2030 / high 60 GW by 2040 — consistent with the DC-dominant
  2026 forecast (though PJM *trimmed* near-term DC on stricter vetting — the mid
  anchor should be re-confirmed against the 2026 report's own DC component).
- **CAISO** mid +1.8 GW (2030) / +4.9 GW (2040) — **still matches the 2025 IEPR
  verbatim** (the 2025 IEPR carried the same DC adder). CURRENT.
- **NYISO** mid >3 GW / high >10 GW by 2031 — from the 2025 Gold Book large-load
  adjustment. CURRENT-vintage.

Verdict **CURRENT (envelope)**: right vintage, right magnitude; the refinement is
envelope → the ISO's MW-by-year table (memo §3.3), a precision improvement, not a
staleness fix.

### 1.4 MISO / NEISO DC blocks — ship `{}` (0 MW)

Per CX-4 §2.2 "no source ⇒ ship 0," MISO and NEISO carry `{}`. That was honest at
the 2026-07-06 branch point, but **both now have sources**:

- **MISO** publishes an explicit DC decomposition (8–14 GW 2026–2027; DC = 20% of
  energy by 2030, 25% by 2040). A MISO block is now sourceable — pairs with the
  §1.2 demand-rate fix.
- **NEISO** 2026 CELT added a **large-load forecast framework** (data-center /
  crypto / large industrial), though the ISO-NE quantum is modest (~110 MW to
  peak in the 2030s per the CELT summary). A small sourced block is now possible;
  its materiality is low, so this is lower priority than MISO.

Verdict **STALE/UNWIRED** — the "no source" basis for `{}` no longer holds.

### 1.5 `DATACENTER_ZONE_SHARE` — UNWIRED (empty → load-share)

`{}` at HEAD (constants.py:888); `datacenter_zone_shares` falls back to each
zone's `load_share` (data/datacenter.py:135-169). The CX-4 memo (§3.3) names two
**published** siting skews the empty table forgoes: **ERCOT** North (Oncor) + West
per the LFL queue geography, and **PJM** Dominion (DOM) per the LTLF zonal DC
split (DOM is the documented DC epicenter). Populating those two from published
queue geography is a "published-siting-only" data-intake (memo's rule: never
invent a split). Verdict **UNWIRED**.

### 1.6 Growth × DC double-count — HAZARD

`DEMAND_GROWTH_RATES`' near rates **still embed the DC boom** (constants.py:776
comment: *"Near-term (2026-2030): elevated by data center and industrial load"*).
The CX-4 **§3.5 decomposition co-change** — re-derive the near era as
**organic-ex-DC** under a 2030 energy-continuity constraint so the explicit block
*relocates* rather than *adds* DC load — **has not landed**. Consequences:

- **At HEAD default (`datacenter_load_path="off"`):** no double-count, but the DC
  load rides the system's **peaky** weather-year shape — the exact error the flat
  block exists to fix. So at default the landed block delivers **no benefit** and
  the shape error persists.
- **With the block ON (`mid`/`high`):** DC load is counted **twice** — once
  implicitly in the elevated near rate, once explicitly in the block.

**Therefore `datacenter_load_path` cannot be turned on in any keeper until the
§3.5 decomposition lands.** The BAU-posture decision (FF-1C item 3: default `off`
vs `mid`) is **coupled** to it — "mid" is only admissible after decomposition.
This is the highest-severity item-1 finding.

---

## 2. Fuel-price path vintages

### 2.1 Gas / coal / oil — STALE by one AEO vintage

All three forward trajectories were **re-derived 2026-07 (P-1D, rule 23)** from
**AEO2025** Table 13/15/12, from the API-fetched
`data/raw/eia-aeo/eia_aeo2025_fuel_prices.part*.csv` — well-cited and internally
consistent (`low`→High-OGS, `mid`→Reference, `high`→Low-OGS). The staleness is
purely vintage:

- **AEO2026 exists.** The `HENRY_HUB_TRAJECTORIES` header itself notes *"AEO2026
  was released April 8, 2026 … re-run `scripts/fetch_eia_aeo.py --aeo-year 2026`
  when that vintage is wanted"* (constants.py:921-922). The fetch script defaults
  to 2025 and accepts `--aeo-year 2026` (scripts/fetch_eia_aeo.py:294) against the
  EIA API v2 — **auto-fetchable in-session** (unlike ATB, §3).
- **Near-term reference gas already reads low.** Model AEO2025 `mid` = **2.74
  (2026) / 2.62 (2027)** $/MMBtu vs **STEO July-2026 ≈ $3.60–3.70 (2026) / <$3.50
  (2027)**. The reference near-term is below the current short-term outlook —
  independent evidence the 2026/2027 anchors are stale on the low side.
  Source: [EIA STEO Jul-2026](https://www.eia.gov/outlooks/steo/report/natgas.php).

Verdict **STALE (1 vintage)**; FF-1E refresh is `--aeo-year 2026` + re-derive +
re-cite, then a plausibility check vs STEO (context, not a fit target).

### 2.2 Uranium / coal level / biomass — CURRENT

- **`NUCLEAR_FUEL_PRICE_HISTORICAL`** (constants.py:1623): derived from the EIA
  Uranium Marketing Annual (U3O8 + SWU) through **2024**, then **hold-flat in real
  terms** for 2025-2050 — because *neither EIA nor AEO publishes a forward
  SWU/U3O8 trajectory*. The hold-flat is the documented non-speculative default,
  not staleness — CURRENT. (Refreshes only when the UMAR adds a data year.)
- **`COAL_PRICE_BASE`** (constants.py:1199): per-ISO **level** anchors cite AEO
  2024; the forward **shape** comes from the AEO2025 `COAL_PRICE_TRAJECTORIES`
  (the rule-14 basin-misalignment exception keeps a single national series off the
  per-ISO levels). The level anchors could refresh with the AEO2026 pass but are
  second-order. CURRENT-ish.
- **`BIOMASS_PRICE_PER_MMBTU`** = 2.5 (AEO 2024) — trivial, CURRENT.

---

## 3. New-entry costs & tech-cost multipliers vs the on-disk NREL ATB

### 3.1 What's on disk

`data/raw/nrel-atb/atb_2024_electricity_filtered.part{00,01}.csv` — the **ATB 2024
v3.0.0** electricity module, filtered to this model's tech set. Long-form schema:
`technology, techdetail, core_metric_parameter (CAPEX/FOM/…), core_metric_case
(Market/R&D), scenario (Advanced/Moderate/Conservative), core_metric_variable
(year), value`. Crucially the **`scenario` column is exactly the low/mid/high axis**
`TECH_COST_MULTIPLIERS` needs (Advanced=low, Moderate=mid, Conservative=high).

### 3.2 `NEW_ENTRY_COSTS` — STALE + UNWIRED

- **UNWIRED:** the values are **hand-transcribed constants** (constants.py:4119)
  labelled "NREL ATB 2024," **not** read from the parquet already on disk. The
  entry screen consumes the dict, not the file — so the on-disk ATB is decorative.
- **STALE:** **ATB 2025 was released 2025-07-01**
  ([NREL ATB](https://atb.nrel.gov/)); the constants are ATB 2024.

### 3.3 `TECH_COST_MULTIPLIERS` — STALE, self-flagged

The dict's own comment (constants.py:4193-4199) states the low/high spreads are
**"engineering-judgment magnitudes … this environment could not reach
atb.nrel.gov to pull the exact 2024 scraped case ratios, so a follow-up should
replace these with exact figures the next time ATB is re-pulled."** That follow-up
is now trivially satisfiable **from the file already on disk**: the ATB 2024
Advanced/Conservative-vs-Moderate CAPEX ratios per tech ARE the exact multipliers,
computable with **zero network**. This is the single cheapest currency win in the
audit.

### 3.4 Refresh channel — ATB 2025 needs a MANUAL DOWNLOAD

The fetch script pulls from the **OEDI S3 data lake** (`atb.nrel.gov` is blocked).
Direct probe of the bucket this session:

```
oedi-data-lake.s3.amazonaws.com/ATB/electricity/{csv,parquet}/  → 2019 … 2024 only
```

**OEDI has not yet mirrored ATB 2025** (both csv/ and parquet/ top out at 2024). So
the ATB 2025 refresh is **not** an in-session `--atb-year 2025` fetch — it needs a
manual pull from atb.nrel.gov or a wait for the OEDI mirror (§7.3). This sharpens
the FF-1E recommendation into **two separable steps**:

1. **Wire / re-derive from the on-disk ATB 2024 now** (no network): closes the
   UNWIRED half of 3.2 and the self-flagged 3.3 gap immediately, source-consistent
   and testable (rule 23).
2. **Intake ATB 2025 separately** (MANUAL DOWNLOAD) as a vintage bump on top.

### 3.5 Emerging tech (CCUS / H2 / geothermal / offshore) — CURRENT-vintage

`CCUS_PARAMS`, `HYDROGEN_TURBINE_PARAMS`, `GEOTHERMAL_PARAMS`,
`OFFSHORE_WIND_PARAMS` (constants.py:4246-4360) all cite ATB 2024 (+ NETL Rev 4,
DOE H2 Program, BNEF, Fervo). Consistent with the on-disk vintage; they ride the
same wire/refresh path as 3.2/3.3. (Minor: `parameter-citations.md` renders the DC
block rows and some ATB rows as `auto-generated / needs-citation` even though the
constants.py comments carry full citations — a doc-generator gap, not a data gap;
worth a `/sync-docs` pass but out of FF-0D scope.)

### 3.6 Financing basis — OPTION (decide nothing)

The screen uses a **single `real_discount_rate`** for every technology. ATB
publishes a **per-technology WACC** (its financial-case structure), which the
literature (ReEDS financing multipliers, plan §4) treats as a real driver of
relative entry economics (capital-heavy nuclear/offshore vs gas). **Option for
FF-1E/owner:** add a `ScenarioConfig` per-tech-WACC field, **default preserving
today's single-rate behaviour**, ATB-cited; flipping it on is an owner decision at
the FF-2D gate, not FF-1E's. Presented per the prompt — **no recommendation, no
change here.**

---

## 4. Policy currency

### 4.1 `policy/ira.py` + IRA config fields — CURRENT (OBBBA)

The OBBBA (Pub. L. 119-21, enacted 2025-07-04) schedule is correctly encoded and
cited (scenarios.py:483-526, ira.py):

| Field | HEAD default | OBBBA basis | Verdict |
|---|---|---|---|
| `ira_wind_solar_last_year` | **2027** | §45Y/§48E: BOC < 2026-07-04 + in-service ≤ 2027-12-31; annual model treats 2027 as last credit year | CURRENT |
| `ira_45u_last_year` | **2032** | §45U(e) terminates for electricity produced after 2032-12-31 | CURRENT |
| `ira_h2_45v_last_year` | **2027** | §45V construction start ≤ 2027-12-31 (OBBBA cut from 2033) | CURRENT |
| `ira_ccus_45q_last_year` | **2032** | §45Q(d)(1) begin-construction-before-2033 proxy; OBBBA §70522 preserved 45Q | CURRENT |
| `ira_other_clean_{last_full,75,50,end}` | **2033/2034/2035/2036** | §45Y/§48E tech-neutral step-down for storage/nuclear/geo/hydro | CURRENT (caveat 4.2) |
| `ira_45q_credit_window_years` | **12** | §45Q(a)(3)-(4) statutory window | CURRENT |
| `ira_ptc_wind` | **26.0 $/MWh** | inflation-adjusted §45 wage-compliant rate | CURRENT |

The cliff is correctly modelled as **binary** for wind/solar
(`compute_dispatch_credits`, ira.py:128) and a **step schedule** for other-clean
(`ira_phaseout_fraction`, ira.py:196). §45U's gross-receipts phase-down is
implemented (ira.py:89). The `_POLICY_BUNDLES` `tight`/`rollback` bundles shift all
`ira_*_last_year` fields uniformly via `ira_year_offset` (scenarios.py:6478).

### 4.2 45Y/48E phase-down — CURRENT with one open MANUAL DOWNLOAD

The 2033/34/35/36 step years are **triangulated from two agreeing secondary OBBBA
alerts** (not primary text): `data/raw/policy/ira-credit-parameters/README.md`
records that `federalregister.gov` redirects to a bot-wall in this environment, so
the **Treasury/IRS final-rule confirmation is still an open MANUAL DOWNLOAD**
(§7.3). The landed values follow the 2-source agreement and are internally
consistent; the flag is a provenance upgrade, not a suspected error. (The intake
CSV `ira-credit-parameters.csv` exists as the citation store but the config fields
are the consumed values — the model's constants-carry-citations convention, same
as `NEW_ENTRY_COSTS`; not a wiring defect.)

### 4.3 State RPS / ACP — CURRENT-ish (Tier 3)

`STATE_RPS_FLOORS` (constants.py:3956) encodes SB 100 / CLCPA / MA-CES / the
PJM-load-weighted blend, and `STATE_RPS_ACP` (constants.py:4029) the REC-price
ceilings, both rule-13-admissible policy parameters. Two standing `TODO/verify`
notes remain and are worth closing in FF-1E:

- **PJM RPS blend** is `Tier 3` with *"load weights are approximate; verify against
  the exact Monitoring Analytics PJM-load-by-state file"* — the blended 18.5%→33%
  path and the ~$45 blended ACP both hang on approximate load weights.
- **ACP levels** are order-of-magnitude ("~$40 NYISO," "~$65 NEISO blend") — verify
  against each state's current ACP schedule (they escalate/decline on published
  tracks, e.g. MD declining to $22.35 by 2030).

No RPS **statute** change since intake was found; this is a precision/vintage
tighten, not a staleness correction.

### 4.4 Confirmed-retirements registry — CURRENT (re-verified 2026-07-05)

`data/raw/confirmed-retirements/` was fully re-verified **12 days ago** (README
"updated 2026-07-05, second intake pass — all six ISOs seeded"): PJM 14 rows,
CAISO 10, MISO 4, ERCOT 2, NEISO 2, NYISO 0 (honest zero — every forward NYISO
deactivation notice found had been reversed). Both prior primary-document caveats
(Rockport 1, Diablo Canyon) were resolved. Pending items are **self-flagged
in-registry** and are the re-check list for the next intake vintage — not gaps
this audit can close without new instruments appearing:

- **PJM Brandon Shores 1-2 + H.A. Wagner 3-4:** RMR through 2029-05; a **2031
  extension is PENDING FERC** (Talen/PJM joint filing) — `exit_year` held at 2029
  until it clears. Re-check.
- **PJM Eddystone 3-4:** `superseded=true` by the DOE §202(c) order chain (current
  order 202-26-24 effective through 2026-08-22) — another 90-day renewal decision
  is due **before 2026-08-22**. Re-check that date.
- **PJM Kincaid 1-2:** Vistra WARN notice (2026-05-04) for ~Oct-2027 closure noted
  as **not** a superseding instrument (CEJA 2030 remains binding; economic screen
  may retire earlier). No action.
- **MISO:** direct Attachment Y fetch failed at intake — **human browser
  cross-check** recommended at the next vintage.

**FF-0D disposition:** registry is current; the pending flags are a next-intake
re-query list (§7.2), not a fix this session makes. A targeted scan surfaced no
major new binding instrument in the 2026-07-05 → 2026-07-17 window worth an
emergency add.

---

## 5. Fleet-snapshot inputs + the hydro bug

### 5.1 EIA-860 planned pipeline — CURRENT

`EIA860_OPERABLE_VINTAGE = 2025` (fleet.py:6458); the top-level parquets are the
**2025 Early Release** (`eia8602025ER.zip`, operating years through 2025); vintage
dirs 2018-2024 back the hindcasts. `load_planned_additions` reads
`eia860_generator_proposed.parquet` (U/V/TS statuses, effective year >
vintage) — the current release. README confirms **no 2026 vintage exists** (EIA
has not published the calendar-2025 annual release). CURRENT — nothing to refresh
until EIA publishes.

*Note (not a forecast-pipeline issue):* the RD-5 coverage gap (Indian Point 3,
Palisades dropped/moved in the current release) is handled for **hindcast actuals**
via `_validation-source/retired_sheet_coverage_gaps.csv`; it does not affect the
forecast planned-additions path.

### 5.2 Weather-year pool — CURRENT

`weather_year` default **2024** (scenarios.py:71); `WEATHER_YEAR_POOL = (2023,
2024, 2025)` with a per-ISO `WEATHER_YEAR_POOL_BY_ISO` **widened 2026-07**
(`docs/weather-pool-coverage-2026-07.md`). Posture is current and documented;
`HYDRO_CLIMATOLOGY_YEARS = (2021…2025)`. No action.

### 5.3 Hydro forecast fleet drop — BUG (charter for FF-1C)

**Confirmed the NYISO-forecast-2035 finding at the source.**
`_load_hydro_generation` (data/hydro.py:265) filters the EIA-923 monthly-generation
table with an **exact-year match** `gen["year"] == year`. The forecast path calls
`build_hydro_fleet` with the **literal calendar year**; EIA-923 tops out at 2026,
so **every forecast year ≥ 2027 finds zero rows**, `load_hydro_budget` raises, and
`build_hydro_fleet`'s `except (FileNotFoundError, ValueError): return [], None`
**silently empties the conventional-hydro fleet** (~3.3 GW / ~9% of NYISO's 2026
fleet; also hits CAISO/NEISO/PJM hydro in every year past the last EIA-923
vintage). Forecast-path-only; a real **BUG**, not a currency item.

**Chartered fix for FF-1C** (hold-last-vintage, mode-aware, backcast
byte-identical):

- In `build_hydro_fleet`'s **forecast branch only** (`forecast_budget=True`), clamp
  the plant-lookup year: `shape_year = min(year, LATEST_EIA923_YEAR)` before
  `_load_hydro_generation`, so the **shape** falls back to the newest real vintage
  while `forecast_budget` keeps setting the **level** to normal-water-year
  climatology (the docstring's stated intent). The `hydro.py:621 shape_year = year`
  seam is the natural clamp point.
- Do **not** touch the backcast branch (`eia930_monthly`/`backfill_year`) — prove
  byte-identity there (the exact-year match is correct when solving a real
  historical year).
- Trivial-first test: forecast 2028 for an ISO with hydro asserts a non-empty
  hydro fleet whose nameplate equals the clamped-vintage fleet; backcast 2024
  hashes identical.
- Secondary (flagged, not chartered here): the `firm_clean_mw`-vs-dispatch hydro
  accounting disagreement (NYISO doc §1 finding 2) — an adequacy-ledger root-cause
  that sits in **FF-2B**, not the hydro loader fix.

---

## 6. FC-5 benchmark-table inventory — PLACEHOLDER (FF-0A not merged)

FF-0A (the forecast determination rubric + `scripts/forecast_verdict.py`, which
owns the FC-5 external-corridor benchmark list) is **not merged at HEAD** —
neither `docs/forecast-determination-rubric.md` nor `scripts/forecast_verdict.py`
exists. Per the FF-0D prompt, this section is a stub until FF-0A's §3 inventory
lands. What FC-5 will need to confront 2030/2035/2040 capacity mix, energy mix and
CO₂ (plan §3 FC-5) is partially on disk already; a provisional gap read pending the
real inventory:

- **On disk / wired:** AEO2025 fuel-price + (via `cross-model-corridor-2026-07-13`)
  the AEO2025 / NREL StdScen / CDR / Gold Book / CELT corridor context; capacity
  hindcast actuals; ISO forecast headlines gathered here (§1).
- **Likely intake gaps (to confirm against FF-0A):** machine-readable **AEO2026**
  capacity/generation/emissions tables (not just fuel prices — the current AEO
  intake is fuel-prices-only, `eia_aeo2025_fuel_prices.*`); **NREL StdScen 2024/2025**
  capacity-mix tables; the ISO planning documents' **capacity-expansion** tables
  (CDR, PJM RTEP, Gold Book, CELT, IEPR) as structured benchmark rows.

**Action:** when FF-0A merges, replace this section with its concrete FC-5 list and
file each missing benchmark as an intake row in §7.2 (do **not** intake here —
FF-0D is audit-only, and FF-0A explicitly owns the inventory).

---

## 7. Prioritized fix / intake list

Routed to the two Wave-1 L-INP sessions. **P0** = blocks correct forecast behavior /
is a bug; **P1** = material currency; **P2** = precision / optional.

### 7.1 → FF-1C (demand & DC currency + hydro fix)

| Pri | Item | Action | Source | Rule note |
|---|---|---|---|---|
| **P0** | Hydro forecast fleet drop (§5.3) | Clamp `shape_year=min(year, LATEST_EIA923_YEAR)` in `build_hydro_fleet` forecast branch; backcast byte-identical; test | in-repo bug | fix, not tuning |
| **P0** | Growth×DC double-count (§1.6) | Land CX-4 §3.5 organic-ex-DC re-derivation **before** any non-`off` DC path; 2030 energy-continuity constraint per ISO | EIA STEO ex-DC + ISO organic/DC splits | rule 1 (right structure) |
| **P0** | BAU DC posture (§1.6) | Present `datacenter_load_path` default `off` vs `mid` to owner **with the §3.5 dependency stated** (mid inadmissible pre-decomposition); record decision in plan §2.1 | corridor evidence | owner decides |
| **P1** | Demand rates, 5 ISOs (§1.1) | Refresh `DEMAND_GROWTH_RATES` low/mid/high near+long to 2025/2026 forecasts (ERCOT LTLF3/2026-prelim, PJM 2026, CAISO CED-2025, NYISO 2025 GB, ISO-NE 2026 CELT) | §1.1 URLs + §7.3 tables | rule 23 (cite the data change) |
| **P1** | MISO demand rate (§1.2) | Add MISO `DEMAND_GROWTH_RATES` block from the Sept-2025 MISO LTLF (replaces the 1%/yr scalar fallback) | MISO LTLF 2025 | rule 23 |
| **P1** | MISO DC block (§1.4) | Add MISO `DATACENTER_ADDITIONS_MW` (low/mid/high) from MISO's published DC futures (8-14 GW 2026-27; 20% energy by 2030) | MISO LTLF 2025 | §5 citation |
| **P2** | DC anchors → MW-by-year (§1.3) | Refine ERCOT/PJM/NYISO envelope anchors to the ISO MW-by-year tables; re-confirm PJM mid vs its trimmed 2026 DC component; CAISO already matches IEPR-2025 | §7.3 tables | precision |
| **P2** | DC zonal siting (§1.5) | Populate `DATACENTER_ZONE_SHARE` for ERCOT (North/West) + PJM (DOM) from published queue geography only | ERCOT LFL geo, PJM LTLF zonal | published-siting-only |
| **P2** | NEISO DC block (§1.4) | Optional small block from the 2026 CELT large-load framework (low materiality) | ISO-NE 2026 CELT | §5 citation |

### 7.2 → FF-1E (entry-cost & policy wiring)

| Pri | Item | Action | Source | Rule note |
|---|---|---|---|---|
| **P0** | `TECH_COST_MULTIPLIERS` self-flagged gap (§3.3) | Derive low/high spreads from the **on-disk ATB 2024** Advanced/Conservative-vs-Moderate CAPEX ratios (zero network); add source-consistency test | `data/raw/nrel-atb/atb_2024_*.csv` | rule 23; closes the in-code TODO |
| **P1** | `NEW_ENTRY_COSTS` wiring (§3.2) | Wire the entry screen to the curated ATB parquet **or** re-derive the constants from it (FF-1E picks; either carries the ATB vintage citation + a source-consistency test) | on-disk ATB 2024 | rule 23 |
| **P1** | Fuel paths → AEO2026 (§2.1) | `fetch_eia_aeo.py --aeo-year 2026`, re-derive gas/coal/oil via `derive_fuel_trajectories.py`, re-cite; plausibility-check near-term vs STEO (context only) | EIA API (fetchable) | rule 23 |
| **P2** | ATB 2025 vintage bump (§3.4) | Intake ATB 2025 as a bump on the wired 2024 base — **MANUAL DOWNLOAD** (OEDI mirror lacks 2025) | atb.nrel.gov | §7.3 |
| **P2** | PJM RPS blend + ACP schedules (§4.3) | Verify PJM load weights vs Monitoring Analytics "% of PJM Load by State"; refresh ACP levels vs current state schedules | PJM-EIS, state ACP tables | rule 23 |
| **P2** | Financing basis option (§3.6) | Add per-tech-WACC `ScenarioConfig` field, default = today's single-rate behavior, ATB-cited; do **not** flip | ATB financial cases | owner decides at FF-2D |
| **P2** | Confirmed-retire re-query (§4.4) | Next intake: PJM Brandon Shores/Wagner 2031 FERC extension; Eddystone §202(c) renewal (due <2026-08-22); MISO Attachment Y browser cross-check | ISO/FERC postings | intake discipline |

### 7.3 MANUAL DOWNLOADS NEEDED (proxy-blocked or table-in-PDF; never guessed)

| # | Document | Needed for | Why manual |
|---|---|---|---|
| M1 | **NREL ATB 2025** full electricity CSV/parquet | §3.4 vintage bump | `atb.nrel.gov` blocked; OEDI S3 mirror has ≤2024 only (probed this session) |
| M2 | **Treasury/IRS §45Y/§48E final rule** (Fed. Reg. 2025) | §4.2 primary confirmation of 2033/34/35/36 steps | `federalregister.gov` → `unblock.federalregister.gov` bot-wall |
| M3 | **MISO Sept-2025 LTLF** MW-by-year + DC-futures tables | §1.2/§1.4 MISO demand + DC blocks | headline via press; exact per-year table in the LTLF workbook/PDF |
| M4 | **NYISO 2025 Gold Book** baseline forecast tables (XLSX) | §1.1 NYISO demand + §1.3 DC anchor precision | per-zone MW-by-year inside the XLSX |
| M5 | **ERCOT 2025 LTLF3 / 2026 preliminary LTLF** MW-by-year | §1.1 ERCOT demand + §1.3 anchor precision | PUCT filing PDF |
| M6 | **ISO-NE 2026 CELT** load + large-load tables | §1.1 NEISO demand + §1.4 optional DC block | CELT XLSX/PDF |
| M7 | **CAISO CED 2025-2045** demand tables | §1.1 CAISO demand refresh (DC adder already confirmed unchanged) | CEC filebrowser XLSX |
| M8 | **AEO2026** capacity/generation/emissions tables | §6 FC-5 corridor (beyond fuel prices) | current AEO intake is fuel-prices-only; pull once FF-0A defines FC-5 |

> ISO-forecast **headline** figures were web-confirmed this session (§1 URLs) and
> form the sanity envelope those exact tables must sit inside; the manual pulls are
> for the **per-year anchor precision** FF-1C/1E write into constants — the audit
> guesses none of them (rule 5).

---

## 8. Scope attestation

- **No source default changed.** Every finding is read-only; the only file this
  session writes is this audit. `DEMAND_GROWTH_RATES`, `DATACENTER_ADDITIONS_MW`,
  the fuel paths, `NEW_ENTRY_COSTS`, `policy/ira.py`, the registries and
  `data/hydro.py` are **unchanged at HEAD `67e64ed`**.
- **Rule 13 held.** Benchmarks scope currency; no number here is a fit target, and
  every fix routed to FF-1C/1E is a source-driven re-derivation (rule 23), never a
  residual patch.
- **Quarantine (rule 22) untouched.** No solve, no scoring, no holdout contact —
  this is a documentation audit.
- **No PR** (not requested); the deliverable is this file on
  `claude/ff-0d-input-audit-rozzgu`.

*Produced 2026-07-17 (FF-0D, Opus, audit-only). Feeds FF-1C (demand/DC + hydro) and
FF-1E (entry-cost & policy wiring).*
