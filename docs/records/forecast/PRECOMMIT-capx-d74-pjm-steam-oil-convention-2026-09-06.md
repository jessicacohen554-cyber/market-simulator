# PRE-REGISTRATION — capx D74: the PJM "Steam Oil & Gas" no-default-cap price-taker convention — fixed BEFORE any code and BEFORE any solve

**Lane:** capx D74 (director r#46). Branch `claude/capx-d74-pjm-steam-oil-gsxcx5`, fresh off
`origin/main` `6887484f`, fast-forwarded to `2eb65038` before this text. Companion:
`DESIGN-capx-d74-pjm-steam-oil-convention-2026-09-06.md` (the phase-0 record, the census, the
mechanism choice). Instrument: `docs/handoffs/d74/phase0-2026-09-06.{py,json}`. DATA PROFILE
`pjm`. Model Fable. **Date:** 2026-09-06. **Pushed before the first line of mechanism code.**
The cache keys of §5 that need the field to exist are added as **Addendum A in the build commit,
before the first solve** — never after a number is seen.

**NOTHING ARMS.** One `{iso: bool}` gate, default-off; no scalar field; suffixed registration;
the owner decides on §7.

---

## 1. The mechanism, fixed here (rule 19 [R-ONE-MECH]: one object, one limb of one published table)

| # | piece | where |
|---|---|---|
| 1 | `capacity_no_default_cap_convention_by_iso: dict[str, bool] \| None = None` — the FIFTH per-ISO capacity gate, resolved through ONE predicate `config/capacity_market.py::resolve_capacity_no_default_cap_convention(config, iso)`, which REQUIRES `resolve_capacity_going_forward_bar_published(config, iso)` (the convention is a limb of the published table; over an ATB bar there is no "NA" cell — returns False, logs once). **No scalar field.** Registered in `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` at `"None"`, `TIER_TAGS` 1, coerced to `None` in a plain backcast. CLI `--capacity-no-default-cap-convention` (+ `--no-`) on `run_capacity_hindcast.py` and `run_full_horizon.py`, recorded in `run_config.json` through the resolved predicate (`Derived`) beside the raw mapping (`FromConfig`). **Not armed:** no `_pjm_config` override. | `config/scenarios.py` (END of the field list, beside its four siblings), `config/capacity_market.py` |
| 2 | **THE PREDICATE.** `data/avoidable_cost_rate.py::no_default_cap_class(iso, fuel_type, delivery_year) -> bool`: True iff the ISO's published table carries `gross_acr` rows for the fuel's class but NONE in the column the fixed D62 vintage rule selects for that delivery year — i.e. exactly the limb `_row_for` reports as basis `"first_published"`. Reads the same clean partition, the same crosswalk, the same vintage rule; adds no number. | `data/avoidable_cost_rate.py` |
| 3 | **THE SEAM.** `retirements.py::apply_economic_retirements`, the candidate loop: beside `if g.unit_id in exempt_unit_ids: continue`, a second exemption `if no_default_armed and no_default_cap_class(iso, g.fuel_type, year): continue` (gate resolved ONCE per screen call, like `published_bar_armed`). An exempted unit is not in `margins`, so `_settle_capacity_supply_clearing` puts its `A_g` in `Q_0` at $0 by the existing `accredited_total − Σ A_g(screened)` construction (I1 structural) and the D57 identity holds by construction (a price taker clears; an exempt unit cannot fail). `resolve_going_forward_bar_per_kw_yr` untouched. | `retirements.py` |
| 4 | **LEDGER.** Additive block `no_default_cap_price_takers = {year, units, mw, mw_by_fuel, classes}` per screen year via `event_sink` → `evolve.py` `events`; absent off the gate (every ledger byte-identical). | `retirements.py`, `evolve.py` |
| 5 | **Tests.** `tests/unit/model/test_d74_no_default_cap_convention.py`: OFF path byte-identical + cache-neutral (absent / `None` / `{"PJM": False}`); the gate refuses without the published-bar gate; the predicate is what `pjm.csv` says (True for gas_st/oil at DY 2022–2025, False at 2026+, False for coal/CC/CT/nuclear in every year, False for `gas_cc_ccs`); the toy-stack identity (an exempt unit is in `Q_0`, cleared, never in `margins`); no scalar companion field exists. | `tests/` |
| 6 | **Matrix** (rule 28c): base row `capacity_no_default_cap_convention` + a cell in ALL SIX shards (PJM `fc: O` pending the A/B; ERCOT `·`; CAISO/MISO/NYISO/NEISO `U` — each names why its own record has no elective-default table, rule 25). `check_mechanism_matrix.py --base origin/main` and `check_cache_key_registration.py --base origin/main` green before push. | `docs/codebase-site/data/mechanism-matrix*.js` |

### 1.1 THE CLASS × DELIVERY-YEAR RULE — fixed here (rule 21 [R-DOF])

Read from `pjm.csv` (M18 Rev 62 §5.4.8.4(B), printed p.143–144): **Steam Oil & Gas has no default
gross ACR for DY ≤ 2025/26 and $64/MW-day for DY ≥ 2026/27.** Model `gas_st` and `oil` both map
to that class (the D62 crosswalk, unchanged). So the convention applies to `gas_st` and `oil` in
screen years 2022–2025 and to nothing else; in screen year 2026+ every class has a default and the
gate is inert by the table. **No column, class, year or convention may be selected by a result**;
a different reach is a change to `pjm.csv` with a source page. The `oil` crosswalk (oil CTs and
diesels folded into the steam class) is D62's and is NOT re-mapped inside this A/B (design §6.2).

---

## 2. G-DRIFT — the code-level drift audit (rule 29(b)) — **VERDICT: LIVE (carried from D67), form 4 VOID, controls at HEAD**

**Anchors, resolved** (the charter's `5bb70047` needed the shallow clone deepened; `f0e050e820c1159a`
is a cache key, as D67 §1(a) records): D57 arm A landed at `5bb70047` and was solved at `a30696a0`
(both ancestors of HEAD); the D62 arm landed at `aa5c339c`. Both committed controls carry the
**pre-hunk** screen peaks — `screen_peak_demand_mw` 137,706.8 / 142,664.3 / 147,800.2 / 153,121.0 /
158,633.4 in BOTH bundles, identical to the digit — and the LIVE hunk D67 §2.2 measured is at HEAD
unchanged: `constants.py` `DEMAND_GROWTH_RATES["PJM"]["mid"]["near"] = 0.064645`, moving the T1-H
screen peak −10,819 / −7,574 / −3,977 / 0 / +4,386 MW across 2021–2025. **Form 4 is VOID for both
committed controls**, exactly as D67 and D58 found; **same-HEAD controls are EARNED and will be
solved** (§4). Nothing below revives form 4.

**Config axis:** the bare recipe resolves to `aef81c84c4609c76` and the D62-armed recipe to
`b98060898fceb3da` at HEAD — both equal to their committed values (phase 0 §4 of the design; D58 §5
and D67 §1(b) read the same bare key). Every field added since either landing drops at its
default on this recipe.

**Code axis, `aa5c339c..HEAD` on the solve path** (29 files, +2,419 / −120), hunk-level on the
seam files and by class elsewhere — the D67 §2.3 discipline, stated as such:

| file(s) | hunks | class |
|---|---|---|
| `capacity_evolution/retirements.py` (+60) | D67's `resolve_published_reliability_requirement_mw` + its one call in `gross_adequacy_requirement_mw`, gated `capacity_adequacy_requirement_published_by_iso` = `None` | **INERT** (gated off; returns `None` → the FPR path byte-identical) |
| `capacity_evolution/adequacy.py`, `data/avoidable_cost_rate.py` | **unchanged** since `aa5c339c` | — |
| `config/capacity_market.py` (+156) | D67's resolver + `RTO_RELIABILITY_REQUIREMENT_MW_BY_ISO` (data, read only under the D67 gate) | **INERT** |
| `config/constants.py` (+166) | `VOLUNTARY_*` registries (SCN-WS3b), consumed only when `voluntary_clean_demand_path != "off"`; the recipe's path is `"off"` | **INERT** |
| `config/scenarios.py` (+362) | new default-off fields (D67, SCN-WS3b, nyiso-198 `cc_duct_peaking_row_scoped`, D77 …) — key unmoved (above) | **INERT** |
| `runner.py` (+44) | `append_voluntary_region` threaded with `zone_demand`; returns arrays unchanged when the path is `"off"` | **INERT** |
| `policy/voluntary_demand.py` (new), `policy/carbon.py` (+27) | the voluntary row (off); `price_adder or 0.0` None-guard (carbon price resolves 0.0 on this recipe, D62 §2 measured) | **INERT** |
| `data/fleet/campd_bins.py` (+73), `data/fleet/__init__.py` (+25), `capacity_evolution/ccs.py` (+16), `new_entry.py` (+9) | D77: `emission_rate_co2 × (1 − ccs_capture_fraction)`, fraction 0.0 on every unabated unit (exact no-op); `ccs_capture_fraction` stamped only on retrofits (none before 2028) and on new CCS entrants (none in window); nyiso-198 `cc_duct_peaking_pct(row_scoped)` default False → the pre-change branch | **INERT** |
| `data/fleet/assembly.py`, `data/offer_curves.py` (4 each) | the same `row_scoped=False` passthrough | **INERT** |
| `data/fleet/eia860.py` (+48), `data/disk_memo.py` (new), `data/egrid_sheets.py` (27) | wall-clock A-4: the eGRID boundary heat-rate repair set memoised across processes in a content-hashed JSON; same pure function, same bytes → same set (a stale memo is impossible by construction: the key is the sha256 of both source files) | **INERT** (value-identical caching) |
| `data/datacenter.py` (+31) | `add_load_layers` sits on the screen-peak path, but the hindcast harness runs with `datacenter_load_path` / `electrification_path` `"off"` (runner.py:2536); the hunk is read in the build commit's Addendum A and classified there | **INERT (to be confirmed in Addendum A)** |
| `model/lp/model.py` (+12) | a log line (simplex iterations / objective) | **INERT** |
| `pipeline/solve.py` (+151), `utils/heap.py` (−40) | #5033 the same-year P1 basis seed: armed only when `MARKET_SIM_P1_BASIS_SEED != "0"` (global default `"0"`; only `run_calibration.py` flips it, `run_capacity_hindcast.py` never references it) AND `xyear_warmstart is None` (the forecast harness passes an explicit bool — D58 §6 ground 1); `malloc_trim` removal is memory hygiene | **INERT** on this recipe (D58 §6's three grounds, re-verified at `solve.py:473-477`) |
| `pipeline/backcast_config.py` (+62) | NYISO-scoped `nyiso_ct_peaker_bands_measured`, backcast path only | **INERT** |
| `results/cache.py` (+58) | cache-epoch ledger prose | **INERT** |
| `scripts/run_capacity_hindcast.py` (+60), `run_full_horizon.py` (+74) | additive CLI (D67 flag, `--retirement-sector-gate` plumbing) | **INERT** |
| `scripts/lib/invariant_ledger.py`, `scripts/lib/load_forecast/*` | not imported under `src/market_sim/` | **INERT** |

**Consequence.** Every hunk since the D62 landing is INERT for this recipe; the LIVE hunk is the
SCN-LOAD growth-rate change that predates both committed controls. So the committed D62 arm and
D57 arm A are valid as READS of what those solves did (every phase-0 number above is such a read),
and the A/B's differencing pairs are solved at HEAD (§4). The audit is recorded before any arm is
solved and is not revisited.

---

## 3. PHASE 0 — the zero-LP STOP gate: **PASS** (design §4; `d74/phase0-2026-09-06.json`)

S0 reproduces the committed D62 arm clearing through the code path to |Δprice| ≤ 0.00024 $/MW-day
and 0.0000 pt in all four delivery years. S74 (the convention on the committed stacks) predicts:
2022/23 **46.7823 $/MW-day, position 1.0537 — unchanged**; Q_0 30,577.9 → 43,102.7 MW (+8,801.9
gas_st, +3,722.8 oil); uncleared coal 238 / CC 2,052 / **CT 15,539** (from 3,086 in the same
reconstruction; the ledger's 3,235.7 differs by plateau tie-order). 2023/24 52.61 (from 54.72),
position 1.0526. 2024/25 and 2025/26 identical (no unit of the class is left in those stacks).

---

## 4. SCREEN (rule 29 [R-SCREEN]) — named here, before it runs

**SCREEN YEAR = the 2022 screen, DY 2022/23** — the year the class's UNCLEARED MW is largest in the
D62 arm ledgers: **12,524.7 MW** (8,801.9 gas_st + 3,722.8 oil) against 1,115.8 MW in 2023/24 and
0 in 2024/25 and 2025/26 (`uncleared_mw_by_fuel`, read in phase 0). Measured, not the biggest
residual. The 2022 screen prices on the 2021 solve (2022 is the rule-22 bridge), so the **screen
span is `--start-year 2021 --end-year 2022`**: one solved year, exactly D62's screen. *(The
charter's "minimum span 2024–2025" was written for a 2025 object; the measured object is 2022/23
and its span is 2021–2022 — stated, not re-interpreted.)*

**Three legs on the screen span, all at HEAD, PJM solo, sequential (rule 12; a PJM year is
~7 GB on a 15 GB box):**

| leg | recipe | role |
|---|---|---|
| **arm** | D57 recipe + `--capacity-going-forward-bar-published` + `--capacity-no-default-cap-convention` | the mechanism |
| **control-P** | D57 recipe + `--capacity-going-forward-bar-published` | the D62 posture at HEAD — the primary differencing pair |
| **control-B** | D57 recipe (bare) | the shipped posture at HEAD — what D58 and D67 also solve |

Recipe: `run_capacity_hindcast.py --iso PJM --start-year 2021 --end-year 2022 --vintage 2020
--fuel-variant realized --entry-screen-diagnostics --out-dir <fresh dir>` (the D48 fields and the
D57 clearing ride PJM's `default_scenario_overrides`). HEAD GUARD around every solve:
`H0=$(git rev-parse HEAD); <solve>; [ "$(git rev-parse HEAD)" = "$H0" ] || exit 90`. Rebase
between legs only, with a re-audit of the delta before the next leg.

**The screen gate is STRUCTURAL and a STOP gate only** (it may kill the arm, never promote it; it
is not gated on any residual):

| # | question | pass condition (arm vs control-P, same HEAD) |
|---|---|---|
| G1 | the arithmetic | 2022/23 price within ±0.05 $/MW-day and position within ±0.001 of control-P (the plateau absorbs it); `price_takers_mw` = control-P's + Σ A_g of every gas_st/oil unit in control-P's stack, to ±1 MW |
| G2 | footprint confined | every offer in the arm's `offer_stack` is byte-identical to control-P's for the same unit; no gas_st/oil unit appears in the arm's stack; VRE / hydro / storage / import / DR credits, `requirement_mw`, `census_mw`, `entry_decided_mw_by_tech`, `renewable_additions`, the exogenous coal exit and `floor_retained` identical |
| G3 | the identity (I2) | the set of `decided` / `entry_capped` / `re_confirmed` rows equals the set of uncleared offers, to the unit (the D62 §4.3 ULP boundary cases disclosed, not counted) |
| G4 | the convention's own identity | ZERO `pipeline_events` rows at any gas_st / oil unit in 2021–2022; the ledger block `no_default_cap_price_takers` carries exactly the class's units and MW |
| G5 | no non-target load-bearing flip | FC-2 rows on the screen year identical; the 2022 `retirements` rows differ ONLY through the admission cap's re-fill from the remaining pool |

Then, and only if the screen clears, **the full T1-H window (2021–2025 realized) as ONE
`--start-year 2021 --end-year 2025` invocation per leg** — arm, control-P and control-B at HEAD
(the D67 §7.1 precedent: both arms at HEAD once form 4 is void) — the arm registered SUFFIXED
(`pjm-2021-2025-realized-t1h-d74-nodefaultcap` → `pjm-t1h-d74-nodefaultcap`); the controls are
never registered. The screen and control bundles are throwaway diagnostic probes: never registered,
never a keeper, never quoted as a keeper number, and **DELETED from `results/` before the PR
merges** (rule 29(c)); this document and the FINDING carry every number.

---

## 5. Cache keys (resolved through `run_capacity_hindcast.build_config` → `apply_iso_scenario_defaults` → `cache_key()`)

| config | key | status |
|---|---|---|
| bare `pjm-t1h` recipe at HEAD (control-B, full span) | **`aef81c84c4609c76`** | measured (phase 0); = D58 §5 / D67 §1(b) |
| + published bar (control-P, full span) | **`b98060898fceb3da`** | measured (phase 0); = the committed D62 arm |
| + published bar + this gate (arm, full span) | *Addendum A* | computed in the build commit, before the first solve; no collision permitted |
| screen-span (2021–2022) keys, all three legs | *Addendum A* | idem |
| `ScenarioConfig()` default / bare backcast pins | unmoved | asserted by test |

**K-a:** any collision, or a realized key ≠ its Addendum-A value unexplained from the resolved
config → STOP for that leg.

---

## 6. PRE-DECLARED SIGNS — graded at full magnitude, misses included (design §5)

1. **2022/23 price and position UNCHANGED** vs control-P (±0.05 $/MW-day, ±0.001).
2. **2022/23 uncleared**: gas_st 8,802 → **0**, oil 3,723 → **0**, CT 3,236 → **15,200–15,900** firm.
3. **2022 `pipeline_events` rows at gas_st / oil units: ZERO** (control-P: 535 decided incl. 8,265
   gas_st + 4,137 oil nameplate).
4. **2022 admitted (`decided`) MW re-fills**: 11.5–13.5 GW nameplate, of which CT 8.5–11 GW
   (control-P: 12,659.7, of which CT 0).
5. **2023/24**: price ratio DOWN by ≈ 0.04–0.08 and position UP by ≈ 0.03–0.07 pt vs control-P.
6. **2024/25 and 2025/26**: `requirement_mw` and the non-screened part of `Q_0` **identical to
   the MW**; the census moves ONLY by the executed-exit delta (ST/oil retained minus CT executed),
   **+0.5 to +3.5 GW**, and the 2024/25 price moves **DOWN** vs control-P by that channel alone.
7. **FC-3**: gas_st 10.297 → **0.8–2.0** GW (actual 2.702); oil 4.188 → **≤ 0.10** (actual 0.613);
   gas_ct 0.000 → **8–11** (actual 0.808); coal 5.3–6.0; gas_cc 0.1–2.3; `retire.total_gw`
   **17.5–20.5, no sign claimed**; unit recall 11/20 → **8/20**; economic release precision
   **falls**.
8. **FC-2 identical**; CO2 within ±0.3 %; determination **HOLD**.

Rule 14's line, stated before the solve: the composition is expected to get WORSE on gas_ct and
better on gas_st / oil, and neither is the criterion. A mechanism that is the market's own offer
rule stays in on structure; the CT plateau at the clearing price with zero E&AS is the object it
exposes (D61 §1.5, D54 §6 item 1) and is routed, not absorbed.

---

## 7. The P9-style flip condition — the arming recommendation, PRE-STATED

Recommend **ARM for PJM** (`capacity_no_default_cap_convention_by_iso: {"PJM": True}` in
`iso_configs._pjm_config` `default_scenario_overrides`, alongside — and only alongside — an armed
published bar, since the gate is a limb of that table) **iff ALL of**:

- **(a) footprint purity** — G2 / G5 hold on the full span: every offer outside the class
  byte-identical to control-P's, `R` and the non-screened `Q_0` identical to the MW in every DY,
  entry and renewable rows identical;
- **(b) the identity** — G3 / G4 hold in every screen year: zero pipeline rows at a
  Steam-Oil-&-Gas unit through DY 2025/26, and the class re-enters the screen exactly when the
  table publishes its default (asserted by test at DY 2026/27);
- **(c) the arithmetic** — G1 holds: the 2022/23 price and position land on phase 0's own numbers.

Recommend **HOLD-and-route** if (a) fails (a second seam moved). Recommend **DECLINE** if (b) or
(c) fails (the code is not the rule this document states). **`retire.total_gw`, recall and
precision are explicitly NOT conditions in either direction** — a worse gas_ct band under the arm
is the pre-declared signature of the CT plateau, not evidence against the class's offer rule; a
better gas_st band is not evidence for it.

---

## 8. STOPs — any one kills the arm; none is promoted past

1. **Phase-0 mismatch** — S0 off 0.001 $/MW-day or 0.0001 pt in any year (**NOT FIRED**, §3).
2. **The bare `pjm-t1h` key or the D62 arm key moved by THIS lane** — `aef81c84c4609c76` /
   `b98060898fceb3da` must be unmoved with the field absent, explicitly `None`, and explicitly
   `{"PJM": False}`.
3. **Any other ISO's key moved.**
4. **A residual-selected convention** (rule 21) — §1.1 is fixed and not revisited after a number.
5. **`requirement_mw` or the non-screened `Q_0` moving in ANY delivery year**, or the 2024/25 price
   moving by any channel other than the executed-exit census delta of §6 item 6 (D62's STOP 5,
   carried and sharpened by what D62 learned: the census channel IS the mechanism propagating,
   and it is bounded by the exit arithmetic).
6. **The price landed through any scalar not in `pjm.csv`.**
7. **Wall/RSS beyond the D57 envelope** (14 min / 9.3 GB per solve year).
8. **Any gas_st / oil unit in a `pipeline_events` row of a DY ≤ 2025/26 under the arm, or any such
   unit absent from `Q_0`** (the convention's own identity broken).

---

## 9. Rules, stated

Rule 1 — structure first (the manual's text and the ownership census choose the mechanism; the
price is pre-declared NOT to move). Rules 13 / 14 — the predicate is a published market-design
fact that regenerates per delivery year; the self-supply / FRR fraction of steam is reported as
NOT separable and NOT proxied (design §1.4); every BRA / SOM figure is a validation observable.
Rule 19 — one mechanism, one limb; ownership stays D58's. Rule 21 — zero DOF. Rule 22 — 2021–2025
realized hindcast, forecast mode; no out-of-training year solved or scored. Rules 24 / 25 — no
scalar field; PJM's table and PJM's cell. Rule 27 — every ≥300-line file edited locally, exact
bytes pushed, blob-verified. Rule 28 — base row + six cells in the build commit; CI checks green.
Rule 29 — phase 0 zero-LP first; the screen year named above from the footprint; structural
STOP-only gates; controls at HEAD earned by a LIVE hunk; screen/control bundles deleted before
merge.

## 10. Collision register (this lane's writes)

`config/scenarios.py` (one field at the end of the D57 family + three registrations),
`config/capacity_market.py` (one resolver beside its four siblings), `data/avoidable_cost_rate.py`
(one predicate), `capacity_evolution/retirements.py` (the candidate loop + gate resolution + ledger
block; **not** the requirement seam, which is D67's), `capacity_evolution/evolve.py` (one ledger
line), `scripts/run_capacity_hindcast.py` + `run_full_horizon.py` (the flag pair),
`scripts/register_forecast_run.py` (one `VERDICT_MAP` entry), the matrix base row + six shard
cells, one new test file, the docs under `docs/handoffs/`. D58 (`retirement_sector_gate`, PJM shard
cell) and D75 (`RENEWABLE_ELCC_CURVES_BY_ISO`) are live on other seams — rebase before every push,
never drop another lane's hunk.

---

## Addendum A — recorded in the build commit, BEFORE the first solve

**A.1 Cache keys**, resolved through `run_capacity_hindcast.build_config` →
`apply_iso_scenario_defaults` → `cache_key()` with the field in place; repo-wide collision scan
(`results/`, `frontend/`, `docs/`, `src/`, `scripts/`, `tests/`) empty for every new key:

| leg | span | key |
|---|---|---|
| control-B (bare `pjm-t1h` recipe) | 2021–2025 | **`aef81c84c4609c76`** (unmoved) |
| control-P (+ published bar) | 2021–2025 | **`b98060898fceb3da`** (unmoved = the committed D62 arm) |
| **arm** (+ published bar + this gate) | 2021–2025 | **`b88464cb413789af`** |
| explicit `--no-` of this gate over the bar | 2021–2025 | `b98060898fceb3da` (drops at `None`, as registered) |
| control-B | 2021–2022 (screen) | **`fdba733e592eb425`** |
| control-P | 2021–2022 (screen) | **`efc626966c2b5892`** |
| **arm** | 2021–2022 (screen) | **`cfa43af80d3b4923`** |

**A.2 STOPs 2 and 3, measured** — every key below is identical at HEAD with the field and at
`origin/main` `2eb65038` without it: `ScenarioConfig()` `e5ecd4105ada3e58`; bare backcast ERCOT
`6a2845e50951394e` / CAISO `f7d05fc51e9bc861` / PJM `6f61207df8f4b398` / MISO `9d11af0c1bf5cc5a` /
NYISO `b791330712d6c2fe` / NEISO `7a1ca5f8884a1dd5`; bare T1-H ERCOT `82b27751be747552` / CAISO
`7da58199acd362ee` / PJM `aef81c84c4609c76` / MISO `687bd75f2828bea1` / NYISO `6e70a637b3465542` /
NEISO `f3988df3068020d1`. **NOT FIRED.** `check_cache_key_registration.py --base origin/main`:
"1 new field(s), all registered"; `check_mechanism_matrix.py --base origin/main`: exit 0
(pre-existing anchor-digit warnings only, not this PR's).

**A.3 The one hunk §2 deferred.** `data/datacenter.py` (+31) adds a new read-only helper
`datacenter_block_energy_mwh` (SCN-WS3b's voluntary-row volume operand) and changes nothing in
`add_load_layers`; the hindcast runs with the data-center path `"off"` besides. **INERT.** The
§2 verdict stands: LIVE on the SCN-LOAD hunk only, controls at HEAD.

**A.4 Build as pre-registered.** Field + three registrations + backcast coercion in
`scenarios.py`; resolver + refused-log set in `capacity_market.py` (re-exported through the
`constants` facade, as its four siblings are); `no_default_cap_class` in `avoidable_cost_rate.py`;
the candidate-loop exemption + ledger block in `retirements.py`; one ledger line in `evolve.py`;
the flag pair on both harnesses; the `VERDICT_MAP` entry; the matrix base row + six shard cells;
`tests/unit/model/test_d74_no_default_cap_convention.py` (25 tests) — all green with the D62 tests
and the constants-facade regression.
