# FF-1E — Entry-cost ATB wiring + policy-currency verification (2026-07)

**Session.** Wave-1 lane **L-INP** of the Forecast Finalization Program
(`docs/forecast-development-plan-2026-07.md` §6, FF-1E). Executes the FF-0D
audit's `NEW_ENTRY_COSTS` / `TECH_COST_MULTIPLIERS` recommendations
(`docs/handoffs/ff-inputs-currency-audit-2026-07.md` §3.2/§3.3/§3.6, routed in
§7.2) and verifies the policy-currency items (§4). Branch
`claude/entry-costs-atb-source-hwxvbp` off `origin/main`.

**Scope guard.** Every changed number is a source-driven re-derivation from the
committed NREL ATB 2024 extract (rule 23), never a residual (rules 1/6/11). The
entry screen is **forecast-only** (capacity evolution runs only in
`mode="forecast"`; backcast has no evolution — `runner.py`), so all of this is
byte-identical in backcast (proven below).

---

## 0. Headline

1. **The on-disk ATB extract was incomplete — a real intake bug.** The committed
   `data/raw/nrel-atb/atb_2024_electricity_filtered.part{00,01}.csv` held only
   **600 rows / 4 cross-reference techs** (Biopower, Coal_FE, Geothermal,
   Hydropower) — the entry technologies `NEW_ENTRY_COSTS` needs (wind, solar,
   gas CC/CT/CCS, nuclear, battery) were **absent**. The earlier intake pushed
   only the first two alphabetical parts. Re-fetched the full **3,162-row** ATB
   2024 v3.0.0 extract from the OEDI S3 data lake (reproducible via
   `scripts/data/fetch_nrel_atb.py`, no network guessing — rule 5) and
   re-committed it as complete parts.
2. **`NEW_ENTRY_COSTS` + `TECH_COST_MULTIPLIERS` re-derived from ATB** on one
   documented basis, with a source-consistency test (§1).
3. **`CCUS_PARAMS` (the operative new-build CCS cost) reconciled** onto the same
   ATB basis so the forecast CCS-vs-gas_cc competition is coherent (§2).
4. **Per-tech WACC option** added, default-off / byte-identical (§3).
5. **Policy layer verified CURRENT** (IRA fields exact-match FF-0D; retirements
   current; RPS/ACP Tier-3, primary-source-blocked items documented) (§4).

---

## 1. `NEW_ENTRY_COSTS` / `TECH_COST_MULTIPLIERS` — derived from ATB 2024

**Derivation** (`scripts/data/derive_entry_costs_from_atb.py`, asserted by
`tests/test_atb_entry_cost_consistency.py`): each tech's base snapshot is ATB's
**Moderate** CAPEX / Fixed O&M at a documented base year — **2026**
(= `REAL_DOLLAR_BASE_YEAR` / model start year) for every tech ATB publishes from
2022, **2030** for new nuclear (ATB's earliest nuclear year). ATB's 2022-USD
values are converted to the model's constant-2026-USD basis with the model's own
`INFLATION_RATE` (2.2 %/yr, factor 1.022⁴ = 1.090947). The `low`/`high` capex
multipliers are ATB's **actual** Advanced/Moderate and Conservative/Moderate
CAPEX ratios at the same base year (dimensionless — the deflator cancels).

Why re-derive rather than nudge: the pre-FF-1E values carried an "NREL ATB 2024"
label but matched **no single ATB year** (Moderate-case closest year: wind
≈ 2037, solar ≈ 2032, gas_cc ≈ 2049, nuclear_smr ≈ 2039) — hand-set estimates,
not a read of the file.

**`base_cf`, `learning_rate`, `lifetime_yr` are unchanged** (ATB's CF/heat-rate
and the Wright's-Law learning rates are outside the committed CAPEX/FOM extract),
as are the `learning_rate` **multipliers** (ATB publishes trajectories, not
learning rates — the trajectory-divergence channel stays a documented DOF-ledger
judgment parameter).

### Cost-vintage delta ledger (2026 USD)

| tech | capex before → after | FOM before → after | mult low before→after | mult high before→after |
|---|---|---|---|---|
| wind | 1300 → **1676.6** (+29 %) | 28 → **33.7** | 0.85 → **0.9784** | 1.12 → **1.0551** |
| solar | 1100 → **1562.2** (+42 %) | 16 → **22.3** | 0.65 → **0.9629** | 1.15 → **1.0513** |
| gas_cc | 1200 → **1583.3** (+32 %) | 30 → **36.1** | 0.95 → **0.9923** | 1.08 → **1.0076** |
| gas_ct | 1250 → **1428.7** (+14 %) | 21 → **27.9** | 0.95 → **1.0** | 1.08 → **1.0** |
| nuclear_smr | 6800 → **10527.6** (+55 %) | 100 → **148.4** | 0.80 → **0.6649** | 1.25 → **1.3141** |
| nuclear_large | 8500 → **8309.0** (−2 %) | 130 → **190.9** | 0.90 → **0.8497** | 1.15 → **1.554** |
| gas_cc_ccs | 2300 → **3104.7** (+35 %) | 45 → **71.1** | 0.85 → **0.9605** | 1.20 → **1.0395** |

Two findings the accurate data forced (both are ATB reality, not regressions):

- **ATB 2024 costs new SMR *above* large LWR** (Moderate CAPEX @2030 $9,650 vs
  $7,616/kW, 2022$) — a FOAK/economies-of-scale premium. The old values had SMR
  *cheaper* with no source. `test_capacity.py` updated (SMR LCOE > large).
- **ATB's near-year cost-case spread is narrow** for mature techs (gas_ct
  *identical* across all three cases → multiplier 1.0) and **wide** for FOAK
  nuclear. The old engineering-judgment multipliers conflated near-year level
  spread with long-run trajectory divergence; the latter is carried by the
  (unchanged) `learning_rate` multiplier.

---

## 2. `CCUS_PARAMS` reconciliation (operative CCS cost)

`gas_cc_ccs` is the one entry tech with no direct ATB match (the model runs 90 %
capture; ATB 2024 publishes only 95 %/97 % CCS). It is mapped to ATB's **95 %
CCS** class as the nearest cost proxy — its 90 %-capture *physics* (heat-rate
penalty, emission rate) stay on `CCUS_PARAMS`/`ccs_capture_rate`; only the
capex/FOM cost basis is ATB's.

Crucially the **operative** new-build CCS screen is `capacity._emerging_lcoe`,
which reads `CCUS_PARAMS["gas_cc_ccs_90"]["capex_kw"]` — **not**
`NEW_ENTRY_COSTS["gas_cc_ccs"]` (that feeds only `compute_lcoe`). Leaving
`CCUS_PARAMS` on its prior `$2,500/kW / $22/kW-yr` basis while gas_cc rose to ATB
2026$ ($1,583) made the capture island look nearly free (≈$900/kW increment vs
ATB's ≈$1,500/kW). Both are now `$3,104.7/kW / $71.1/kW-yr` (ATB 95 % CCS @2026,
2026$); the source-consistency test asserts they agree. Retrofit-screen behavior
is unaffected (it reads only `NEW_ENTRY_COSTS["gas_cc_ccs"]["learning_rate"]`).

**Geothermal / offshore (documented, not re-derived):** the committed extract's
geothermal class is HydroFlash (hydrothermal), a *different* resource from the
model's EGS — ATB's EGS classes are not in the CAPEX/FOM extract, so EGS keeps
its Fervo/ARPA-E basis. Offshore's ATB classes *are* in the extract and its
values sit below the near-year ATB Moderate level (same anchored-later pattern),
but offshore is a minor ISO-gated build and FF-0D graded it CURRENT-vintage, so a
full re-derivation (both classes, floating's 2028 start, CF rows) is flagged as a
bounded follow-up. Both carry ATB cross-reference notes in `constants.py`.

---

## 3. Per-tech WACC OPTION (FF-0D §3.6 — added, not flipped)

`ScenarioConfig.per_tech_wacc_enabled` (default **False**). Off → every tech's
LCOE annuity uses the single `real_discount_rate`, byte-identical and
cache-key-stable (`per_tech_wacc_enabled` is in `_CACHE_KEY_OPTIONAL_FIELDS`).
On → `constants.ATB_TECH_WACC_REAL` (NREL ATB 2024 "WACC Real" Market, per tech
@ base year) via `scenarios.resolve_real_discount_rate`, threaded through every
new-entry / emerging-tech CRF in `capacity.py`.

Values (real): wind 0.0504, solar 0.0423, gas 0.0536, nuclear 0.0565, offshore
0.0515, geothermal 0.0515 (vs the single 0.0568). **Left OFF** — ATB's Market
WACC embeds the PTC/ITC tax-equity benefit the model *also* credits explicitly,
so enabling it risks double-counting; that interaction is the owner's call at the
FF-2D gate, not FF-1E's.

---

## 4. Policy currency (FF-0D §4 — verified CURRENT)

- **IRA / OBBBA (§4.1):** all fields exact-match FF-0D's CURRENT table —
  `ira_wind_solar_last_year=2027`, `ira_45u_last_year=2032`,
  `ira_h2_45v_last_year=2027`, `ira_ccus_45q_last_year=2032`, other-clean
  2033/2034/2035/2036, `ira_45q_credit_window_years=12`, `ira_ptc_wind=26.0`.
  **No correction needed.**
- **45Y/48E primary confirmation (§4.2):** still a MANUAL DOWNLOAD —
  `federalregister.gov` returns a redirect/bot-wall in this environment (302,
  unchanged from FF-0D). The 2033–2036 steps remain triangulated from two
  secondary sources; unchanged.
- **State RPS / ACP (§4.3):** deferred here to the item-2 session and now
  **landed** in `docs/handoffs/ff-1e-policy-currency-2026-07.md` — the precision
  refresh DID surface a citable delta: the **MA Class I RPS ACP was stale
  ($67.62 → $40/MWh, 225 CMR 14.08 2021 reset)**, dropping `STATE_RPS_ACP["NEISO"]
  65 → 50; the PJM load weights were refreshed to the primary Monitoring Analytics
  2024 annual file (OH/VA understated, KY omitted). CAISO $50 / NYISO $40 / PJM
  $45 verified/kept. All forecast-only (backcast byte-identical). (This session
  itself made no RPS/ACP change — the delta was found by the dedicated cited-
  values pass, not this entry-cost session.)
- **Confirmed retirements (§4.4):** registry current; no new binding instrument
  (re-confirmed 2026-07-19 — Brandon Shores 2031 RMR extension still PENDING
  FERC, new DOE §202(c) orders are retirement *deferrals*). **No additions.**

---

## 5. Tests + verification

- `tests/test_atb_entry_cost_consistency.py` (new): asserts every ATB-derived
  constant equals the derivation; CCUS_PARAMS agrees with NEW_ENTRY_COSTS; the
  WACC option is default-off/byte-identical and cache-key-stable.
- `tests/test_capacity.py::test_nuclear_smr_costlier_than_large` and
  `tests/test_emerging_tech.py::test_ccus_needs_high_carbon_price`: updated to
  the accurate-data behavior (rationale in-test).
- T0 smoke (NEISO 2026-2028 forecast) + invariants: see §6.
- Backcast byte-identity: see §6.

## 6. Smoke / invariants / byte-identity

**Full test suite:** 4,349 passed. The 61 failures the suite reports are
**pre-existing** — every one fails identically on the base tree (0972a7b) with
the FF-1E changes stashed (date-dependent staleness tests, environment/data-
dependent runner/export/hydro/clean-io tests). FF-1E introduces **zero** new
failures. The three tests the entry-cost change legitimately moved
(`test_nuclear_smr_costlier_than_large`, `test_ccus_needs_high_carbon_price`,
`test_ccs_learning_independent_of_gas_cc`) were updated to the accurate-data
behavior and pass.

**T0 smoke — NEISO 2026-2028 forecast (after, ATB costs):** runs to completion.
Entry-additions ledger (`evolution_<year>.json` fleet deltas):

| year | fleet MW delta by fuel |
|---|---|
| 2026 | none (base year) |
| 2027 | gas_ct +1064.9, gas_cc +1000.0 |
| 2028 | gas_cc_ccs +3000.0 (per-ISO cap), gas_cc −2000.0, coal −54.0 |

`check_forecast_invariants.py`: physics green — **I1 energy balance
1.5e-11 MW**, I2 no-NaN/inf, I3 unserved/dump ok, I5 no retire-and-reenter,
I8 planned-additions gating, I9 storage, I10 RPS-dual, **I11 one-pass**,
I13 cobweb, **I14 price sanity in band**. Two FAILs + one WARN are **not** the
cost change: I7 (2026 accredited firm 27,171 < req 28,797) and I12 (2026 reserve
margin 9.2%) are **base-year fleet adequacy** — 2026 has zero entry deltas, so
that fleet is identical before/after the cost change — surfacing in a
degraded-data smoke env (the log notes a missing NEISO zonal-load file and
reconciled corrupt summer-capacity rows). I4 (2028 coal off 54 MW) is a
capacity-accounting reconciliation of the 2028 coal retirement, not a physics
violation. The cost change **runs cleanly and keeps the physics invariants
green**; the cost-vintage effect is the different entry mix (§1 ledger).

**Backcast byte-identity — NEISO 2024 (168 h):** the calibration bundle content
hash is **byte-identical** with the FF-1E code and with the three runtime files
(`constants.py`, `scenarios.py`, `capacity.py`) reverted to pre-FF-1E — hash
`e542fe15…` both runs. Proves empirically what the structure guarantees: the
entry screen and its ATB costs are read only in forecast capacity evolution
(`runner` gates evolution on `mode=="forecast"`), and the per-tech-WACC option
defaults off, so a backcast is unaffected.
