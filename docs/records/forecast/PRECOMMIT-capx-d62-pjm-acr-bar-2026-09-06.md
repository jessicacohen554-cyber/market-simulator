# PRECOMMIT — capx D62: PJM's published default gross ACR as the going-forward BAR (+ the tariff reactive leg)

**Lane:** capx D62 (director r#43, re-issue of the r#41 charter). Branch
`claude/capx-d62-pjm-acr-bar`. Base `fca3b65619b2bcde1e2a970e49827094e6a73d2f`.
DATA PROFILE `pjm`. Model Opus.
**Binding charter:** `docs/handoffs/capx-director-prompt-pack-2026-08.md` §D62 +
`docs/handoffs/FINDING-capx-d61-2026-09-05.md` §4 (construction, vintage rule, signs, STOPs).
**Written BEFORE any build, any Phase-0 arithmetic and any solve.** Every number this lane will
ever cite from a screen or control bundle is recorded here or in its FINDING (rule 29(c):
those bundles are deleted before the PR merges; git history is the record).

---

## 1. The mechanism, fixed here (rule 19 [R-ONE-MECH]: one object, two seams)

**Object:** PJM's own published **default gross Avoidable Cost Rate** (Manual 18 Rev 62
§5.4.8.4(B)) as the retirement screen's going-forward bar AND — through the D57 clearing's
`offer_g = max(0, GFC_g − EAS_g) / (A_g × 365)`, which reads the SAME `going_forward_cost` —
the sell-offer cap. One bar, offer and exit (DESIGN-capx-d54 §3.5 identity). Plus the tariff's
**reactive component** as the SINGLE out-of-market leg of the screen's margin.

| # | Piece | Where |
|---|---|---|
| 1 | `capacity_going_forward_bar_published_by_iso: dict[str, bool] \| None = None` — a per-ISO gate in the D57 `{iso: bool}` form. **No scalar field**: the values are DATA. Registered in `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` at `"None"`; CLI on `run_full_horizon.py` and `run_capacity_hindcast.py` (+ the `--no-` form); recorded in `run_config.json`. **NOT armed in this lane** — no `_pjm_config` override. | `config/scenarios.py` (outside the D50 block, outside SCN-WS1a's D34-guard region, outside SCN-WS2a/2b's `federal_ces_*` block), `config/capacity_market.py` resolver |
| 2 | **Seam 1 — THE BAR.** `resolve_going_forward_bar(iso, fuel_class, delivery_year)` returns the published class value on **nameplate** (`$/MW-day × 365 → $/kW-yr`) when the gate is on for that ISO; else the ATB path (`getattr(config, fom_field) × multiplier`) **unchanged**. Under the published bar `retirement_fom_multiplier_*` does **not** apply — the published number is already the avoidable cost "assuming the unit would otherwise retire" (M18 §5.4.4). Stated in a comment, never tuned. | `model/capacity_evolution/retirements.py::apply_economic_retirements`, the `going_forward_cost` line |
| 3 | **Seam 2 — REACTIVE.** The tariff's reactive component enters `net_revenue` **before** the capacity leg, ONCE, as `pmax_mw × reactive_per_mw_yr`, for every thermal unit — so the offer inherits it exactly as the screen does. The SOLE out-of-market credit: no uplift, no AS annual rate, no regulation, no black start (rule 19; D61 §2b's rule-13 adjudication). | same margin loop, before the `supply_clearing_armed` branch |
| 4 | Data: `data/raw/capacity-market/avoidable-cost-rate/pjm/pjm.csv` (already intaken, two vintage columns) + the reactive row(s) added by this lane with source doc + page. | `capacity-market-avoidable-cost-rate` datatype |

### 1.1 THE VINTAGE RULE — fixed here, before any solve (rule 21 [R-DOF])

* **DY ≤ 2025/26** reads the *"Through the 2025/2026 Delivery Years"* column (2022/23 $, nameplate).
* **DY ≥ 2026/27** reads the *"For the 2026/2027 Delivery Year and Subsequent"* column.
* Classes printed **"n/a"** in the first column — **Steam Oil & Gas** — read the **first published
  value** ($64/MW-day, the 2026/27 column), and that fact is written into the DOF-ledger row.
* Screen year Y prices delivery year **Y/Y+1** (the D57 convention, unchanged).
* **I MAY NOT PICK BETWEEN COLUMNS, ESCALATIONS OR A UCAP/NAMEPLATE CONVENTION BY THE RESULT.**
  That is the rule-21 failure mode D61 §3 names; a lane that finds itself doing it stops.

The values this rule selects, resolved from `pjm.csv` now and not re-decided later
($/MW-day nameplate → $/kW-yr = ×365/1000):

| model fuel class | M18 technology_class | DY ≤ 2025/26 | DY ≥ 2026/27 | model ATB bar (D61 `BAR`) |
|---|---|---:|---:|---:|
| `coal` | Coal | 80 → **29.20** | 94 → 34.31 | 58.5 |
| `gas_cc` | Combined Cycle | 56 → **20.44** | 113 → 41.25 | 30.0 |
| `gas_ct` | Combustion Turbine | 50 → **18.25** | 52 → 18.98 | 21.0 |
| `gas_st` | Steam Oil & Gas | *n/a* → **23.36** † | 64 → 23.36 | 35.0 |
| `oil` | Steam Oil & Gas | *n/a* → **23.36** † | 64 → 23.36 | 25.0 |
| `nuclear` | Nuclear – Multi Unit | 445 → **162.43** | 537 → 196.01 | 130.0 |

† the "n/a" limb of the vintage rule above.

---

## 2. G-DRIFT — the code-level drift audit (rule 29(b), clause b: **NO CONTROL SOLVE**)

**Control = the committed bare `pjm-t1h` bundle** `results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/f0e050e820c1159a/` (D57 arm A, registered as the `pjm-t1h` recipe).
Its `run_config.json` records `git.sha = a30696a0`, `basis_sha = db057c5d…`, solved 2026-09-05T04:47Z.
`a30696a0` **is an ancestor of HEAD** (verified), so `git diff a30696a0 HEAD` is purely "what main
has taken since" — no branch-side reversals.

Audit command (the charter's path list, **widened** by `scripts/run_capacity_hindcast.py`, which is
the harness that actually runs T1-H):

```
git diff a30696a0 fca3b656 -- src/market_sim scripts/run_full_horizon.py \
    scripts/run_capacity_hindcast.py scripts/lib
```

**54 files, +3,904 / −539.** Classified **HUNK BY HUNK** — never at file level. That discipline is
here because D65's G-DRIFT classified `retirements.py` at file level and missed an ungated change to
an existing helper (D55's `_floor_retention_merit`); `retirements.py` is D62's own seam-1 file.

### 2.1 The two director-verified facts, RE-VERIFIED here (not assumed)

| claim | verification | result |
|---|---|---|
| D58's PJM sector-gate arming has NOT landed | `get_iso_config("PJM").default_scenario_overrides` = `{pjm_accreditation_design_vintage: True, pjm_demand_response_supply: True, capacity_market_supply_clearing_by_iso: {PJM: True}}` | **CONFIRMED** — no `retirement_sector_gate`, no `locality_capacity_curves` |
| `src/market_sim/` has ZERO commits since `d66d5e6b` | `git diff --stat d66d5e6b fca3b656 -- src/market_sim` | **CONFIRMED** — empty |

### 2.2 `retirements.py` — HUNK BY HUNK (10 hunks; the file the D65 lesson binds)

| # | hunk | what | verdict |
|---|---|---|---|
| 1 | `@@ -60,+5` | 5 D59 locality imports | INERT — import-only |
| 2 | `@@ -74,+1/−1` | `+ map_area` on an existing import line | INERT — import-only |
| 3 | `@@ -754,+82` | NEW `UTILITY_SECTOR`, `sector_gated_unit_ids` (D53) | INERT — new symbols; only caller is `evolve.py` under `retirement_sector_gate`, **off for PJM** (2.1) |
| 4 | `@@ -933,+1` | new kwarg `locality_price_per_firm_mw_yr=None` on `capacity_revenue_per_mw_yr` | INERT at default |
| 5 | `@@ -977,+10` | `price = max(price, locality)` guarded `is not None` | INERT — None ⇒ skipped |
| 6 | `@@ -987,+233` | NEW D59 helpers (`LocalityPosition`, `locality_capacity_curves_armed`, `_locality_udr_icap_mw`, `_locality_requirement_icap_mw`, `locality_capacity_positions`, `locality_prices_by_zone`) | INERT — new symbols; every table is NYISO-keyed, PJM absent |
| 7 | `@@ -2487,+1` | new param `locality_prices_by_zone=None` on `apply_economic_retirements` | INERT at default |
| 8 | `@@ -2950,+5` | `_locality_price = (locality_prices_by_zone or {}).get(g.zone)` ⇒ None | INERT |
| 9 | `@@ -2958,+6/−1` | the ONLY deleted code line in the file: the same `capacity_revenue_per_mw_yr(...)` call re-wrapped with `locality_price_per_firm_mw_yr=None` | INERT — identical arguments |
| 10 | `@@ -3013,+3` | new ledger field `locality_price_per_kw_yr` (0.0 when None) | INERT — **diagnostics accounting**; changes `pipeline_events` bytes, no decision (disclosed §2.5) |

**No ungated change to any existing helper. No `_floor_retention_merit`-class hunk.**

### 2.3 The rest of the solve path — every changed file, with its reason

| file(s) | change | verdict + reason |
|---|---|---|
| `capacity_evolution/evolve.py` | `_sector_exempt` (gated `retirement_sector_gate`) unions into `exempt_unit_ids`; `locality_prices_by_zone`/`locality_cost_ratio_by_zone` threaded | INERT — gate off ⇒ `frozenset()` union is identity; None threaded |
| `capacity_evolution/new_entry.py` | locality siting block `if locality_prices_by_zone and zone_names:`; `_thermal_zone_by_tech.get(tech, zone)` | INERT — empty dict ⇒ block skipped, `.get` returns `zone` |
| `capacity_evolution/ccs.py` (D65 Act A) | `delta_fom_per_mw_yr_ref × fixed_cost_scale`, `vom_adder × fixed_cost_scale` | INERT ×2 — `ccs_retrofit_fixed_cost_co2_scaling=False` ⇒ `fixed_cost_scale = 1.0` (identical arithmetic); **and** `ccs.py:350 `if year < ccs_retrofit_available_year` (2028) returns before any flag read, so `apply_ccs_retrofit` never runs in a 2021–2025 window |
| `capacity_evolution/__init__.py` | re-exports of the D53/D59 symbols | INERT — facade |
| `model/storage.py` | locality-weighted `base_price` under `if locality_prices_by_zone and design.capacity_market` | INERT — None/empty ⇒ skipped |
| `model/lp/rows.py`, `model/lp/model.py` (SCN-WS2a) | clean-tier family: vector-form qualifying spec, `region_gen_coeff`, clean block moved out of the RPS branch, the "requires RPS family" hard error removed | INERT ×2 — (a) `_build_rps_region_rows` builds `data_r` in lock-step with `groups_r` and concatenates in the same order, so `coeff=None` ⇒ `concatenate(data_groups) ≡ np.ones(cols.size)`, byte-identical; (b) **moot for PJM**: `_rps_region_grain_active(cfg,"PJM") = False` and `_clean_region_arrays_for_year(cfg,"PJM",2023,…) = None` (measured) — neither family builds a row |
| `policy/clean_tiers.py` | `append_clean_region`, `fuel_credit`, `_region_fuel_fractions`; `clean_credit_by_fuel` reads fractions | INERT — name-tuple regions credit 1.0 (semantics preserved); and PJM has no clean-region arrays at all |
| `policy/federal_ces.py` | `append_federal_ces_region`, `FEDERAL_CES_REGION_LABEL`, `premium_for_year` refactor | INERT — `federal_ces_target_by_year=None` and `federal_ces_enabled=False`; `append_federal_ces_region(cfg,…,None)` returns `None` (measured) |
| `policy/cap_and_trade.py` + `runner.py` `assemble_mc` seam (SCN-WS1a G-C3) | **UNGATED**: `carbon_price` → `carbon_mc = carbon_mc_column(...)` | INERT — **measured**: `resolve_carbon_price(cfg, y) == 0.0` for y ∈ 2021…2025 (`carbon_price_path="zero"`, `pjm_rggi_allowance_pricing=False`), and gate 1 of `carbon_mc_column` returns **the identical object** — `carbon_mc is carbon_price` → `True` in all five years |
| `runner.py` D59 block | `locality_positions` / `locality_prices` / `locality_cost_ratio` under `locality_capacity_curves_armed(config, iso)` | INERT — gate off for PJM ⇒ all three empty ⇒ `(locality_prices or None)` is None everywhere |
| `runner.py` `_clean_region_arrays_for_year` | replaces the inline `if miso_clean_tier_rows` at two sites | INERT — returns `None` for PJM (measured) |
| `model/interchange/spec.py` (SCN-WS1a G-C2) | border adder off `resolve_carbon_price` instead of the raw field | INERT — inside `if use_corridors:` and `use_corridors = caiso_per_hub or caiso_ref_seam`, both False for PJM |
| `data/outages.py` (nyiso-196) | `denom` replaces `cap[tgt]`; `per_unit` slot grows to 3 elements | INERT — `denom = cap[tgt]` unless `extract_basis is not None`, and `extract_basis` is None because `unit_outage_extract_basis_share=False`; identical arithmetic |
| `data/fleet/arrays.py` | 4 call sites pass `extract_basis_share=getattr(config,…,False)` | INERT — False |
| `data/cod_ramp.py` (wall-clock A-1) | **UNGATED** vectorization of `_load_cod_map`'s per-plant groupby → `_reduce_cod_groups` | INERT — **verified**: `tests/unit/data/test_cod_ramp.py` (the shipped dict-equality gate against the pre-vectorization loop) **46 passed / 8 subtests passed**, 127 s |
| `data/egrid_sheets.py` (new) + `data/zone_assignment.py` + `data/fleet/eia860.py` (wall-clock A-2) | **UNGATED** `pd.read_excel` → `read_egrid_sheet` (content-addressed parquet mirror) at 3 solve-path reads | INERT — **verified**: on `egrid2023_data_rev2.xlsx` (the only workbook carrying PLNT23/UNT23) all three reads are `IDENTICAL=True` on values, column order and dtypes — PLNT23×2 (12,612×6), UNT23 (26,186×3) |
| `data/offer_curves.py` (miso-217) | `_with_intermediate_phys` | INERT ×2 — gated `miso_intermediate_gas_offer_margin` (False) AND `iso == "MISO"`; returns `inter` itself |
| `data/fleet/eia860.py` | new `eia860_plant_sectors` + directory-keyed cache | INERT — new symbol, D53's only consumer |
| `config/capacity_market.py` | NYISO locality tables + 3 resolvers | INERT — every table NYISO-keyed |
| `config/constants.py` | facade re-exports; `NUCLEAR_MONTHLY_CF_BY_YEAR["ERCOT"][2022]` added; `DATACENTER_ZONE_SHARE["MISO"]` populated | INERT — other ISOs' rows. The SCN-WS4a cache-epoch entry states it in terms: *"every OTHER ISO — ERCOT and PJM already carried published overrides and are byte-identical"* |
| `config/iso_configs.py` | PJM `default_scenario_overrides` = the D57 arming; MISO + NYISO overrides | INERT — **identity-preserving**: at `a30696a0` the arm passed the three PJM flags explicitly; at HEAD they are inherited. Effective configs compared field-by-field below |
| `config/scenarios.py` | 7 new fields, all default-off, all registered; validators; backcast coercions | INERT — see the cache-key measurement below. `ccs_retrofit_capex_co2_scaling` default flip handled separately |
| dead-code deletions: `data/som_conduct.py` (module), `data/reserve_requirements.load_reserve_requirements`, `data/outages.read_clean_outages` + `CT_DEPLOYMENT_CSV`, `data/eia923.plant_state_map`, `data/floor_mechanisms.tag_raised`, `data/benchmark_corridor.load_benchmark_corridor`, `data/miso_outages.FORECAST_PARQUET`, `config/paths.TX_UNIT_OUTAGES_CSV`, `config/plant_taxonomy.is_fossil`, `config/constants.{CCS_RETROFIT_HR_PENALTY_REFERENCE, ERCOT_SCED_INTERVALS_PER_HOUR, ERCOT_DC_TIE_CAPABILITY_MW}`, `results/metrics.py` (module), `pipeline/result.py` (module) | removals | INERT — a live reference would raise `ImportError`/`AttributeError`, never change a number silently |
| `pipeline/solve.py`, `utils/heap.py` | `malloc_trim()` at the P0→P1 seam | INERT — frees already-free arenas; observes nothing |
| `results/emissions.py`, `results/export.py`, `results/outputs.py` (SCN-WS0) | additive summary keys (`emissions_by_fuel_mt`, `emissions_by_zone_mt`, `import_co2_mt_reported`, `unserved_mwh`, `co2_cap_price*`); `DispatchResult.emissions` derived on parquet read | INERT — **diagnostics/output accounting**; the derived array equals every consumer's own existing fallback (disclosed §2.5) |
| `matrix.py`, `results/cache.py`, `scripts/lib/*`, `scripts/run_full_horizon.py`, `scripts/run_capacity_hindcast.py` | scenario-matrix reporting, the cache-epoch ledger (prose), bench/holdout/scorer helpers, additive CLI (`--locality-capacity-curves`, `--retirement-sector-gate`, `--ccs-retrofit-fixed-cost-co2-scaling`, `--set`) | INERT — harness/records; no solve-path arithmetic |

### 2.4 The one thing that DID move: the recipe's cache key (D60, not this lane)

Measured at HEAD by rebuilding the T1-H PJM recipe through `run_capacity_hindcast.build_config`
and `apply_iso_scenario_defaults` (the seam-resolved config, which is what the solve runs):

```
seam-resolved PJM T1-H key at HEAD                          aef81c84c4609c76
   … with ccs_retrofit_capex_co2_scaling forced back to False   f0e050e820c1159a   ← the committed arm-A key, EXACTLY
```

Field-by-field against the committed `scenario_config`, the seam-resolved HEAD config differs in
**exactly one value** — `ccs_retrofit_capex_co2_scaling: False → True` (capx D60 executing owner
ruling Q42) — plus **7 new fields**, every one of them registered in `_CACHE_KEY_OPTIONAL_FIELDS`
with its declared default and therefore dropped from the hash
(`ccs_retrofit_fixed_cost_co2_scaling`, `federal_ces_acp_usd_per_mwh`, `federal_ces_target_by_year`,
`locality_capacity_curves`, `miso_intermediate_gas_offer_margin`, `retirement_sector_gate`,
`unit_outage_extract_basis_share`). The three PJM gates the arm passed explicitly are inherited
identically from `_pjm_config`.

**This is a KEY move with a provably ZERO VALUE effect**, and it is the designed behaviour of the
capx D24-R (b′-1) construction: the flip leaves the frozen drop-value at `False`, so the armed
default enters the hash. The value cannot move because `ccs.py::apply_ccs_retrofit` returns at its
**first statement**, `if year < config.ccs_retrofit_available_year` (2028), before any read of the
flag — and the T1-H window ends in 2025. The cache-epoch ledger says the same thing in its own
words: *"every BACKCAST and every hindcast/crossover horizon ending before 2028, whose behaviour is
byte-identical … and that call site is the field's only consumer in the source tree."*

**It is D60's move, not this lane's.** The STOP that binds me is "the bare `pjm-t1h` key moved by
**THIS lane**": my field must leave **`aef81c84c4609c76`** (HEAD's bare key) unmoved, and must not
move any other ISO's key. That is test T-2 below.

### 2.5 Disclosed non-decision output diffs (so a reader does not read them as drift)

A HEAD-run bare recipe would produce ledger/summary bytes that differ from the committed control in
two places, neither of which touches a decision, a price or a quantity:
1. every `pipeline_events` margin row gains `locality_price_per_kw_yr: 0.0` (D59);
2. each annual summary gains `emissions_by_fuel_mt`, `emissions_by_zone_mt`,
   `import_co2_mt_reported`, `import_co2_basis`, `unserved_mwh`, `co2_cap_price_usd_per_t`,
   `co2_cap_price_by_cap`, `n_co2_caps_binding` (SCN-WS0), and `DispatchResult.emissions` is
   populated on parquet read instead of `None`.

### 2.6 G-DRIFT VERDICT

**Every solve-path hunk is INERT for a PJM `mode="forecast", hindcast=True`, 2021–2025 T1-H run.
NO LIVE HUNK. ⇒ G-CTRL form 4 is valid: the committed `f0e050e820c1159a` bundle IS the control,
and NO control solve is spent.** The single non-inert consequence is a cache-key advance owned by
D60 whose value effect is provably nil on this horizon (§2.4).

---

## 3. PHASE 0 — the zero-LP STOP gate

Reproduce **S0** (the committed clearing) and **S6** (every class bar at the published default gross
ACR) of `docs/handoffs/d61/reclear-2026-09-05.py` **through the code path** — the new
`resolve_going_forward_bar` feeding `clear_capacity_supply_stack` — against the committed arm-A
ledgers `results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/f0e050e820c1159a/evolution_<year>.json`.

**Tolerance: 0.000 $/MW-day and 0.000 pt in all four delivery years, both scenarios. Any mismatch is
a STOP** — the lane reports the mismatch and spends no LP.

D61's committed targets (`reclear-2026-09-05.json`):

| DY | S0 price · ratio · Δpos | S6 price ratio · Δpos | S6 uncleared firm |
|---|---|---|---|
| 2022/23 | 76.10 · 1.52× · −0.48 | **1.06 · +0.10** | coal 0.2 · CC 2.1 · ST 8.8 · oil 3.7 GW |
| 2023/24 | 82.81 · 2.43× · −0.98 | **1.56 · −0.27** | — |
| 2024/25 | 165.84 · 5.73× · −2.79 | 5.04 · −2.34 (all clear) | — |
| 2025/26 | 451.61 (cap) · −3.88 | cap | none |

---

## 4. SCREEN (rule 29 [R-SCREEN])

**SCREEN YEAR = the 2022 screen, DY 2022/23.** Named **here, before the screen runs**, and chosen
because it is the year the mechanism's own measured footprint is **largest** — every CT / ST / oil
offer sits on the bar plateau (D61 §1.1: 330/404 CT units, 115 gas_st, 421 oil at exactly zero
E&AS) and coal's ATB-vs-published gap is widest (58.5 vs 29.2, 2.0×). It is **not** the year with
the biggest residual, and the gate below is **not** gated on the target residual.

**The screen gate is STRUCTURAL and a STOP gate only. It may kill the arm; it may never promote it.**

| # | structural question | pass condition |
|---|---|---|
| G1 | direction + order of magnitude | 2022/23 price ratio falls from 1.52× into D61 §2d's bracket **0.87–1.06**; position rises from −0.48 pt into **+0.1…+0.3 pt** |
| G2 | footprint confined to the bar rows | every unit whose offer changes is a screened thermal unit whose `fuel_class` has a published ACR row; no VRE / storage / import / DR credit moves; `Q_0 + Σ A_g == accredited` still holds (I1) |
| G3 | offer == exit identity (I2) | the set of `decided`/`entry_capped`/`re_confirmed` `pipeline_events` rows equals the set of uncleared offers on `capacity_clearing.offer_stack`, to the unit; every such row carries `capacity_cleared: false`, `capacity_revenue_usd: 0.0` |
| G4 | reactive enters ONCE | each unit's `net_revenue` gains exactly `pmax_mw × reactive_per_mw_yr`; no double count with the clearing's `EAS_g` |
| G5 | no non-target load-bearing criterion flips PASS → FAIL | FC-2 / FC-3 rows on the screen year |

Then, and only if the screen clears, **the full T1-H window (2021–2025 realized, the D57 recipe) as
ONE `--start-year 2021 --end-year 2025` invocation and ONE bundle**, registered under a suffixed key
with its `-pre-d62` prior preserved. The screen bundle is a throwaway diagnostic probe: never
registered, never a keeper, never quoted as a keeper number, and its year is re-solved inside the
full bundle (rule 16 untouched). Per rule 29(c) it is **DELETED from `results/` before the PR
merges**; this doc and the FINDING carry every number.

---

## 5. PRE-DECLARED SIGNS — verbatim from the charter, graded at full magnitude

> 2022/23 ratio 1.52 → ≈1.06 (0.87–1.06), position −0.48 → +0.1 to +0.3 pt, coal uncleared 5.4 →
> ≤ 0.2 GW, steam 8.8 GW UNCHANGED, oil 3.7 GW uncleared unless reactive+energy clears it; 2023/24
> 2.43 → ≈1.56 (1.28–1.56), position −0.98 → −0.3 to 0; 2024/25 5.73 → 5.04 then FROZEN (all offers
> clear); 2025/26 unchanged.
> FC-3: economic coal exits UP from 0.44 GW, gas-steam 9.5 GW unchanged, gas-CC 2023 entry below
> +4 GW, retire.total_gw toward 15.06 actual; determination expected to STAY HOLD.

Two things this lane commits to reporting even when they read badly (D61 §3 falsifier iii):
an operand that **OVER-shoots** (a ratio below 1×) is a finding about the record's offer conduct,
**not** a failure and **not** a reason to shade the bar back up; and the **gas-steam over-exit stays
over-exited** — 8.8 GW of steam is uncleared under every D61 scenario including S3b, because real
steam sellers cleared while earning $0 E&AS and recovering 0 % of avoidable cost, i.e. they offered
BELOW their cap. That is the offer-convention object (D67), not a revenue stream.

---

## 6. STOPs — any one kills the arm; none is promoted past

1. **Phase 0 mismatch** (§3) — any row off 0.000 $/MW-day or 0.000 pt.
2. **The bare `pjm-t1h` key moved by THIS lane** — HEAD's bare key `aef81c84c4609c76` must be
   unmoved with the field absent, explicitly `None`, and explicitly `{"PJM": False}`.
3. **Any other ISO's key moved.**
4. **A residual-selected column or convention** (rule 21) — the vintage rule of §1.1 is fixed and
   is not revisited after seeing a number.
5. **The 2024/25 price moving** — every offer already clears there; if it moves, something other
   than the chartered mechanism moved.
6. **The price landed through any scalar not in `pjm.csv`.**
7. **Wall/RSS beyond the D57 envelope** (14 min / 9.3 GB) without the co-opt.

---

## 7. Rules, stated

* **Rule 13 / 14** — the bar is the mechanism's OWN published operand (M18 §5.4.8.4(B)) replacing an
  ATB **proxy**; the reactive component is a FERC-approved tariff quantity that regenerates from
  every Net CONE filing. Both pass D61 §2b's forward-form test. Nothing is identified from a residual.
* **Rule 19** — ONE bar for offer and exit; ONE out-of-market leg (reactive). No uplift, no
  regulation, no black start, no AS annual rate, no ORDC overlay.
* **Rule 21 [R-DOF]** — ZERO free parameters. The DOF-ledger rows are the published values with
  `pjm.csv` + M18 §5.4.8.4(B) as identification source, and the "n/a" limb of the vintage rule is
  named in its own row.
* **Rule 22** — no out-of-training solve: 2021–2025 realized hindcast, forecast mode, only.
* **Rule 25 [R-ISO-SCOPE]** — PJM's data and PJM's matrix cell only; the gate is per-ISO in form and
  every other ISO's cell enters `U`.
* **Rule 27 [R-PUSH]** — edit locally, push exact on-disk bytes, blob-verify every ≥300-line file
  after push.
* **Rule 28 [R-MECH-MATRIX]** — one base row + a cell line in all six shards, in this PR.
* **Rule 29(c)** — any screen or control bundle is deleted from `results/` before the PR merges.
* **Nothing arms in this lane.** No `_pjm_config` override; arming is a later owner card.

## 8. Collision register (this lane's writes)

`config/scenarios.py` (field placed **outside** the D50 block, **outside** SCN-WS1a's D34-guard
region and **outside** SCN-WS2a/2b's `federal_ces_*` block — D65-B will rewrite the first two after
D60-R3), `config/capacity_market.py` (resolver, beside the D57 sibling),
`model/capacity_evolution/retirements.py` (seam 1 + seam 2, beside D57's settlement hunk and D53's
sector-gate hunk — rebase before every push), `scripts/run_capacity_hindcast.py` +
`scripts/run_full_horizon.py` (CLI), `data/raw/capacity-market/avoidable-cost-rate/pjm/` (+ schema),
`tests/`, `docs/codebase-site/data/mechanism-matrix.js` + the six shards, this doc + the FINDING.

**NOT written by this lane:** `frontend/data/forecast/program-status.json` and `ff-verdicts.json`
belong to D60-R3 (dispatched concurrently). **Registration + the artifact-only re-score WAIT until
D60-R3's finding has merged** (`git log origin/main --grep=D60-R3`); if it has not by the time the
solves are done, everything else is pushed as a CHECKPOINT with the owed items named.
