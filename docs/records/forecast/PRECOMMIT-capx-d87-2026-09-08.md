# PRECOMMIT — capx D87: the CCS retrofit screen consumes the clean-tier seam

**Lane:** capx D87 · **Branch:** `claude/capx-d87-ccs-clean-tier-seam` (fresh off `origin/main`
`d1b8d1bf`) · **Date:** 2026-09-08 · **Model:** Opus (rule 27 `[R-PUSH]`) · **Data profile:**
`nyiso` + `code`
**Charter:** capx ledger §0bf ← the D87/D88 READ
(`DESIGN-capx-d87-d88-s19-read-2026-09-08.md` §1.6) ← SCN ruling S19.

**This document is written BEFORE the edit and BEFORE any solve.** Every number below is
reconstructed from a COMMITTED artifact or read off the code at HEAD; no LP was spent to produce
any of it. The pre-registered screen gates in §6 are fixed here and are not revisited after the
arm runs.

---

## 0. HEADLINE

- **Phase 0 STOP GATE does NOT fire.** The reconstructed delta is **non-zero in every year of
  every one of the 12 live target-row bundles**, NYISO's 2028–2030 cohort included. The seam is
  live on the committed record and the lane proceeds. §2.
- **Phase 0 (ii) — MISO: NO, and structurally so.** The MI clean row's dual is **0.0 in every
  year of every committed MISO bundle**, because MI's first statutory knot is **2035** and
  `_clean_tier_target` returns `0.0` strictly before the first knot, while every committed
  MISO config with the tier armed ends at **2030**. Confirmed independently by three committed
  `duals.json` files that print MI at `-0.0` in all five years. **The MISO T1-F family is NOT in
  the blast radius** and the cache-epoch entry does not name it. §3.
- **G-DRIFT: form 4 is VALID on its primary basis** — the control recipe re-keys to its recorded
  `eb1b0e1df942db47` at HEAD, proved twice. The hunk audit finds **34 commits / 62 files** on the
  solve path since the control, of which exactly **one hunk is LIVE for a NYISO forecast**
  (SPP-49's unconditional simple-cycle heat-rate floor, footprint **3 plants / 10 rows / 19.0 MW
  net summer**, 0.042 % of the NYISO fleet, none of them `gas_cc`). Under rule 29 `[R-SCREEN]`(b)
  a LIVE hunk earns a control solve, so the screen is an **A/B at HEAD**, both arms solved
  concurrently. §5.
- **Two corrections to the READ**, recorded here because they change what the screen can see: the
  READ's "0.0 MW retrofit in every year of every `CES-T80` leg" is **false** (NYISO `CES-T80`
  retrofits 2.984 / 2.272 / 1.000 GW in 2028/2029/2030), and "NYISO is the one ISO with headroom"
  is **incomplete** (MISO and PJM `CES-T80` carry MORE 2030 headroom). Neither changes the
  chartered screen — NYISO 2030 is still the year this mechanism's own footprint is largest for
  the ISO the seam was measured on — but both are routed to SCN with the re-based rows. §2.4.

---

## 1. THE OBJECT AND THE REPAIR (unchanged from the READ; restated so the diff is pre-declared)

The retrofit screen prices each continuation's certificate through one resolver:

```python
# src/market_sim/model/capacity_evolution/ccs.py:475-476  (HEAD d1b8d1bf)
attr_unabated = effective_eac_price_for_unit(config, "gas_cc",     old_er, year)
attr_post     = effective_eac_price_for_unit(config, "gas_cc_ccs", new_er, year)
```

which folds two legs only — the legacy per-fuel scalar and the exogenous premium
(`federal_ces.py:586-590`, `:627-629`). The CES target row's dual lives in
`clean_attribute_price_by_fuel`, threaded from the prior year's `clean_region_duals`
(`runner.py:2331`, `:2351`) into `evolve_fleet` (`evolve.py:118`), and `evolve_fleet` never hands
it to `apply_ccs_retrofit` (`evolve.py:664-674`). The two sibling screens DO fold it
(`retirements.py:3634`, `new_entry.py:1202`).

**The repair, one seam:** thread `clean_attribute_price_by_fuel` from `evolve.py:664` into
`apply_ccs_retrofit` as a `None`-default keyword, and fold
`clean_credit_for_zone(by_fuel, fuel, zone_idx)` into BOTH legs through the existing `max()`:

```python
zi = zone_names.index(gen.zone) if zone_names and gen.zone in zone_names else None
attr_unabated = max(effective_eac_price_for_unit(config, "gas_cc",     old_er, year),
                    clean_credit_for_zone(clean_attribute_price_by_fuel, "gas_cc",     zi))
attr_post     = max(effective_eac_price_for_unit(config, "gas_cc_ccs", new_er, year),
                    clean_credit_for_zone(clean_attribute_price_by_fuel, "gas_cc_ccs", zi))
```

No new `ScenarioConfig` field, no new constant, no RPS leg (rules 21 `[R-DOF]`, 24
`[R-REGISTRY]`, 19 `[R-ONE-MECH]`). `None` ⇒ `clean_credit_for_zone` returns `0.0`
(`clean_tiers.py:303-310`) ⇒ `max(x, 0.0) == x` for every non-negative `x`.

**The symmetric form is deliberate and is pre-declared here.** `attr_unabated`'s new leg folds to
0 today for a second, independent reason beyond the READ's: NYISO's committed
`federal_ces_eligible_fuels` is
`[nuclear, wind, solar, hydro, geothermal, offshore_wind, gas_cc_ccs, hydrogen_ct, hydrogen_ccgt]`
— **`gas_cc` is absent**, so `federal_ces_row_fuel_credit` mints no `gas_cc` key and
`clean_credit_by_fuel` returns no `gas_cc` vector at all. The leg is written anyway, because
leaving it asymmetric "because it is zero" is the exact shape this seam came from.

**Boundaries (charter).** This lane owns `ccs.py:475-476` and the `evolve.py:664` threading and
nothing else. It does NOT touch `ccs.py`'s conversion block (`:590-591`), `arrays.py:3651`, or
`evolve.py`'s `_retrofitted_ids` / exempt-set lines — capx **D88** owns those — nor the
evolution-ledger adequacy-block writer (**D83**). Not in scope: D77's routed parasitic-uplift
item, the level of `ccs_retrofit_vom_adder`, anything under `_AGGREGATABLE_FUELS`.

---

## 2. PHASE 0 (i) — THE PRE-SOLVE DELTA, RECONSTRUCTED FROM COMMITTED ARTIFACTS

### 2.1 The charter's stated instrument does not exist, and what replaces it

The charter says to reconstruct the NYISO cohort "from its COMMITTED `duals.json`". **NYISO has
no committed `duals.json`** — a census over `git ls-tree` finds 32 in the whole repository, all
in `scn-campaign-policy-2026-09-06/{CAISO,ERCOT,MISO}/`, and **zero** under `NYISO/`, `NEISO/` or
`PJM/`. (The `--kind`-agnostic reader in `run_ces_leg` gained `clean_region_duals` in the
trajectory only at SCN-FIX3, 2026-09-07 — one day AFTER this campaign.)

So the dual is reconstructed from the **row's own feasibility state**, which every NYISO leg
does commit. The federal CES row carries an ACP escape column priced at
`federal_ces_acp_usd_per_mwh` (`lp/costs.py:249-261`, `model.py:391-396`), so:

| row state | dual |
|---|---|
| credited share **below** target ⇒ escape column at a positive level | **= ACP exactly** ($50.00) |
| credited share **at** target ⇒ escape at zero, row binding | **endogenous, ∈ (0, ACP]** |
| credited share **above** target ⇒ row slack | 0 |

The credited share is computed at full precision from each leg's own
`full_horizon_summary.json` `trajectory[].generation_by_fuel_mwh`, credited by
`_credit_fractions_from_codes`'s `clean_capture` map (every eligible fuel 1.0, `gas_cc_ccs` at
`federal_ces_ccs_capture_fraction` = 0.95), over the row's own **demand** basis
(`total_gen_mwh + storage_discharge_mwh − storage_charge_mwh`; the row's obligation is
`target(year) × each zone's annual demand`, `federal_ces.py:225-235`). The target path is the
committed `{2026: 0.55, 2035: 0.80, 2050: 1.00}` linearly interpolated.

### 2.2 The method is VALIDATED against committed truth before it is used

Applied to the three ISOs that DO commit `duals.json`, the classifier predicts the committed
federal dual in **29 of 30** bundle-years exactly, and the one exception is the informative one:

| leg | year | gap vs target (demand basis) | predicted | committed `clean_region_duals` |
|---|---|---|---|---|
| CAISO `CES-T80` | 2026–2029 | −0.0871 … −0.0024 | ACP 50.00 | `[50.0]` ✓ |
| CAISO `CES-T80` | 2030 | **+0.000038** | binding, ∈(0,50] | `[6.9465]` ✓ (endogenous) |
| ERCOT `CES-T80` | 2026–2030 | −0.1492 … −0.2668 | ACP 50.00 | `[50.0]` ✓ |
| MISO `CES-T80` | 2026–2030 | −0.2668 … −0.3962 | ACP 50.00 | `[-0.0, -0.0, 50.0]` ✓ |
| CAISO / ERCOT / MISO `ALL-CLEAN` | all | all short except none | ACP 50.00 | `50.0` in every row ✓ |

The CAISO 2030 row fixes the classifier's boundary: a gap within ~1e-4 of zero is **binding with
an endogenous dual**, not slack, and not ACP.

### 2.3 The NYISO cohort

| year | credited (TWh) | demand (TWh) | share | target | gap | **that year's dual** | **the screen that reads it** |
|---:|---:|---:|---:|---:|---:|---|---|
| 2026 | 60.4855 | 154.0944 | 0.392523 | 0.550000 | −0.157477 | **ACP $50.00** | 2027 (inert, < 2028 gate) |
| 2027 | 60.4855 | 155.9150 | 0.387939 | 0.577778 | −0.189839 | **ACP $50.00** | **2028** |
| 2028 | 82.2666 | 157.7571 | 0.521476 | 0.605556 | −0.084079 | **ACP $50.00** | **2029** |
| 2029 | 101.0933 | 159.6210 | 0.633333 | 0.633333 | **−0.000000** | **endogenous ∈ (0, 50]** | **2030** |
| 2030 | 106.7740 | 161.5070 | 0.661111 | 0.661111 | **+0.000000** | endogenous ∈ (0, 50] | (past the horizon) |

**Δ`attr_post` = dual × 0.95, Δ`attr_unabated` = 0** (§1). So:

| retrofit screen year | Δ`attr_post` ($/MWh) | committed retrofit (GW) | cap headroom (GW) | **predicted direction & bound** |
|---:|---|---:|---:|---|
| **2028** | **+47.50** | 2.984 | **0.016** | UP, but **cap-saturated: ≤ +16 MW** |
| **2029** | **+47.50** | 2.272 | **0.728** | UP, **up to +728 MW** (to the 3 GW cap) |
| **2030** | **+(0, 47.50]** | 1.000 | **2.000** | UP, **up to +2,000 MW**; magnitude conditional on the 2029 endogenous dual, which the committed record cannot supply |

`uplift_window` rises by
`Σ_t [max(p_t − mc_post + attr_post^new + q45, 0) − max(p_t − mc_post + attr_post^old + q45, 0)] × avail × annualize`,
i.e. by at most `Δattr × 8760 × avail` per MW-yr and by `Δattr ×` (in-the-money hours) once a host
is already in the money. At the leg's own measured `gas_cc_ccs` capacity factor (37.926 TWh on
5.256 GW in 2029 ⇒ CF 0.824) that is ≈ **$0.33 M/MW-yr** against a learning- and
CO2-scaled retrofit capex of ≈ $1.67 M/MW — a ~5-year payback from the certificate alone, inside
the 15-year minimum remaining life. **The binding constraint therefore becomes the 3 GW/yr cap
and the eligible host pool, not the payback gate** — which is why the table's bounds are cap
bounds, and why 2028 barely moves.

### 2.4 Two corrections to the READ, and why the screen year does not change

The full reconstruction over all 12 live target-row bundles (all 60 bundle-years) is in
§2.5. Two of its rows contradict the READ:

1. **"That is the measured 0.0 MW in every year of every `CES-T80` leg" is FALSE.** NYISO
   `CES-T80` converts **2.984 GW in 2028, +2.272 in 2029, +1.000 in 2030**; `gas_cc` falls
   11.199 → 5.943 GW across the same window. The retrofit screen is not silent under a target
   row — it is running on §45Q, carbon and fuel economics with the certificate at zero. **What
   is zero is the certificate's CONTRIBUTION, not the retrofit set.** The defect's magnitude is
   therefore the DIFFERENCE from the premium legs, not the whole set.
2. **"NYISO is the one ISO with headroom" is INCOMPLETE.** 2030 cap headroom under `CES-T80`:
   **MISO 3.000 GW** (it retrofits 0.000 that year), **PJM 3.000 GW** (0.000), **NYISO 2.000 GW**,
   NEISO 1.214, CAISO 0.108, ERCOT 0.002.

**The chartered screen stands, on rule 29's own test.** The screen year must be the year the
mechanism's own measured footprint is largest *for the screened ISO*, chosen before the solve and
never against a residual: for NYISO that is unambiguously **2030** (2.000 GW of headroom vs 0.728
in 2029 and 0.016 in 2028). NYISO is also the ISO the seam was measured on (SCN-WS5A) and the
lane's declared data profile. Changing the screen ISO now, to the ISO where the arm would move
the most MW, would be selecting the arm's venue on its expected effect — which is the choice rule
1 `[R-STRUCT]` forbids. Both corrections are ROUTED to SCN in the FINDING; this lane does not
re-state the six ISO policy FINDINGs' numbers itself.

### 2.5 The full reconstruction (all 12 live target-row bundles)

Dual per year, then that year's committed retrofit and the cap headroom. `ACP` = short, dual
= $50.00; `(0,50]` = binding, endogenous.

| bundle | 2026 | 2027 | 2028 | 2029 | 2030 | retrofit GW 2028/29/30 | 2030 headroom |
|---|---|---|---|---|---|---|---|
| CAISO `CES-T80`   | ACP | ACP | ACP | ACP | (0,50] | 2.997 / 2.997 / 2.892 | 0.108 |
| CAISO `ALL-CLEAN` | ACP | ACP | ACP | ACP | ACP | 2.982 / 2.997 / 2.989 | 0.011 |
| ERCOT `CES-T80`   | ACP | ACP | ACP | ACP | ACP | 0.000 / 2.951 / 2.998 | 0.002 |
| ERCOT `ALL-CLEAN` | ACP | ACP | ACP | ACP | ACP | 2.996 / 3.000 / 3.000 | 0.000 |
| MISO  `CES-T80`   | ACP | ACP | ACP | ACP | ACP | 0.335 / 0.284 / 0.000 | **3.000** |
| MISO  `ALL-CLEAN` | ACP | ACP | ACP | ACP | ACP | 2.998 / 3.000 / 3.000 | 0.000 |
| NEISO `CES-T80`   | ACP | ACP | ACP | (0,50] | (0,50] | 2.965 / 2.940 / 1.786 | 1.214 |
| NEISO `ALL-CLEAN` | ACP | ACP | ACP | (0,50] | (0,50] | 2.950 / 2.955 / 2.804 | 0.196 |
| **NYISO `CES-T80`** | ACP | **ACP** | **ACP** | **(0,50]** | (0,50] | **2.984 / 2.272 / 1.000** | **2.000** |
| NYISO `ALL-CLEAN` | ACP | ACP | ACP | (0,50] | (0,50] | 2.984 / 2.995 / 1.000 | 2.000 |
| PJM   `CES-T80`   | ACP | ACP | ACP | ACP | ACP | 0.408 / 1.841 / 0.000 | **3.000** |
| PJM   `ALL-CLEAN` | ACP | ACP | ACP | ACP | ACP | 2.992 / 2.998 / 3.000 | 0.000 |

**No bundle-year carries a zero dual. The STOP GATE does not fire.**

---

## 3. PHASE 0 (ii) — THE MI CLEAN ROW: **NO**, AND THE CODE SETTLES IT WITHOUT A MEASUREMENT

The READ left this open (§4 item 1: "Unmeasured … Named as the charter's first zero-LP
measurement"). It does not need a `--fleet-only` replay: **the registry and the trajectory
convention answer it.**

```python
# src/market_sim/config/capacity_market.py — MISO_CLEAN_TIER_REGIONS
"MI": {"obligated_zone": "MISO-East", "obligated_load_share": 0.57,
       "floors": {2035: 0.80, 2040: 1.00, 2045: 1.00},
       "qualifying_fuels": (..., "gas_cc_ccs")},
"MN": {..., "floors": {2030: 0.80, ...},
       "qualifying_fuels": (nuclear, hydro, wind, solar, hydrogen_ct, hydrogen_ccgt, biomass)},
```
```python
# src/market_sim/policy/clean_tiers.py:56-67
def _clean_tier_target(floors, year) -> float:
    """Return a clean-tier target at ``year`` — ZERO before the first knot."""
    if year < min(floors):
        return 0.0
```

**MI's first knot is 2035.** A census of every committed `run_config.json` finds **55 configs
with a clean-family row armed, and every single one ends at 2030 or earlier** — the four MISO
T1-F bundles (`ff-t1f-d45r/d60/d65br/miso`, `ff-t1f-s123/verify`) and the three
`scn-campaign-load-…-r2/MISO/*` legs all span 2026–2030; the seven `results/hindcast/miso-…-t1h-*`
bundles span 2021–2025. So MI's obligation is **0.0 in every year of every committed bundle**, a
zero-obligation row is trivially slack, and its dual is 0.

**Corroborated by committed truth**: `scn-campaign-policy-2026-09-06/MISO/CES-T80/duals.json`
prints `clean_region_duals = [-0.0, -0.0, 50.0]` (MN, MI, federal) in **all five years**, and
`MISO/ALL-CLEAN` prints `[-0.0, -0.0, 50.0, 7.0]` likewise.

**MN cannot substitute**: its first knot is 2030 (so 2026–2029 are zero, and the 2030 screen reads
the 2029 dual), and its `qualifying_fuels` **excludes `gas_cc_ccs`** outright, so
`clean_credit_by_fuel` mints no `gas_cc_ccs` vector from MN's row in any year.

**Conclusion: the MISO T1-F family is NOT in the blast radius, and the cache-epoch entry does not
name it.** What WOULD put it there is a MISO run whose horizon reaches 2035 with
`miso_clean_tier_rows` armed; no such bundle is committed.

**The voluntary row is likewise inert**: `VOLUNTARY_ELIGIBLE_FUELS_DEFAULT` is
`(wind, solar, offshore_wind, geothermal)` (`constants.py:5351-5356`), and every one of the 21
committed configs with `voluntary_clean_demand_path != "off"` carries
`voluntary_eligible_fuels = null`, i.e. the default. No committed voluntary row admits CCS gas.

---

## 4. BLAST RADIUS AND THE CACHE-EPOCH ENTRY

**Reachable at HEAD: exactly the 12 live target-row bundles**, years 2028–2030 —
`scn-campaign-policy-2026-09-06/<ISO>/{CES-T80, ALL-CLEAN}` × CAISO, ERCOT, MISO, NEISO, NYISO,
PJM. The 13th target-row config, `scenario-probes/scn-ws2a/neiso-2026-t0-target`, is a 2026-only
T0 leg, below `ccs_retrofit_available_year` = 2028, and is inert.

**Not reachable, each for its own reason:**
- **Every backcast keeper** — `__post_init__` refuses a target row in `mode="backcast"`
  (`scenarios.py:17528-17533`), AND a backcast rebuilds its base fleet each year and never enters
  `evolve_fleet`, AND `apply_ccs_retrofit` returns before any pricing below 2028
  (`ccs.py:354-355`). Three independent gates.
- **Every `ff-t1h` hindcast (2021–2025)** and the crossover window — below the 2028 year gate.
- **Every MISO clean-tier bundle** — §3.
- **Every premium (`CES-P*`) and voluntary leg** — no clean row on `gas_cc_ccs` ⇒ `by_fuel` has no
  entry ⇒ `max(x, 0.0) == x`.

**Keys: ZERO move.** `clean_attribute_price_by_fuel` is a runtime prior-year value, not a
`ScenarioConfig` field; `ccs.py` / `evolve.py` / `federal_ces.py` are not `SURFACE_MODULES`
(`solve_surface.py:57-65`). So the 12 bundles sit at exactly the key a post-fix run computes and
**will CACHE-HIT stale unless purged** — the "Epoch 2026-09-06b" same-key-invalidation class
(`results/cache.py:371`). The epoch entry this lane owes names those 12 and nothing else.

**No scored cell moves**: `frontend/data/forecast/ff-verdicts.json` keys no verdict to a
target-row run.

---

## 5. G-DRIFT (rule 29 `[R-SCREEN]`(b)) — CONTROL VALIDITY

**Control:** `results/scn-campaign-policy-2026-09-06/NYISO/CES-T80`, recorded
`cache_key = eb1b0e1df942db47`, `git.sha = bdfb3095e`, solved years 2026–2030, wall 1,818.9 s,
peak RSS 3,556.2 MB.

### 5.1 Primary basis — the recorded cache key. **PASS, proved twice.**

1. The committed `run_config.json`'s 813-field `scenario_config` dict, rebuilt into a HEAD
   `ScenarioConfig`, computes **`eb1b0e1df942db47`** — identical. Twelve fields have been ADDED to
   `ScenarioConfig` since (`cc_summer_derate_reconciled_basis`, `eia860_vintage_tracks_solve_year`,
   `ercot_ep_gas_basis_monthly`, `ercot_zonal_spread_ep_referenced`,
   `f923_gas_price_plausibility_screen`, `gas_offer_margin_anchor_vintage`,
   `miso_seam_neighbour_hourly_ladder`, `miso_seam_neighbour_hourly_spp`,
   `netload_drag_layup_window_mask`, `pjm_interface_feed_admissibility_gate`,
   `pjm_thermal_accreditation_vintage`, `spp_gas_commitment_bridge`); all twelve drop out of the
   hash at their defaults, which is what a same-key add means.
2. The LIVE RECIPE — `_load_ladder(configs/scenarios/nyiso_scenario_base_2026_2030.yaml,
   configs/scenario_campaign_matrix.yaml)["CES-T80"]` with NYISO's own
   `ISOConfig.default_scenario_overrides` applied (`nyiso_requirement_forecast_peak`,
   `nyiso_requirement_vintage_factors`, both True) — also computes **`eb1b0e1df942db47`**.
   *(Recorded so the next lane does not repeat the detour: the pre-resolution ladder config keys
   `e221c666e0670d57`, because `default_scenario_overrides` are applied at solve time, not by the
   ladder loader. That is not drift.)*

So the D79 solve-surface fingerprint has not moved for NYISO and no config default flip reaches
this recipe.

### 5.2 Hunk classification. **34 commits / 62 files / 3,576 non-comment added lines.**

The cache key is necessary but not sufficient — behaviour outside the seven `SURFACE_MODULES`
does not re-key — so every changed hunk on a **NYISO forecast 2026–2030** path is classified:

| module(s) | change | verdict |
|---|---|---|
| `config/solve_surface{,_declared}.py` (904) | D79 fingerprint, landed at zero key moves | **INERT** — and §5.1 proves it for this name |
| `capacity_evolution/retirements.py`, `__init__.py` | capx D84 thermal ELCC vintage | **INERT** — three binding gates, all fail for NYISO: `pjm_thermal_accreditation_vintage` default `False` and absent from the recipe; `THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO` contains **PJM alone**; requires `accreditation_design_vintage_armed` |
| `capacity_evolution/retirements.py`, `evolve.py` | capx D78-R2 deletes `exempt_unit_ids` | **INERT** — the parameter had no producer at HEAD and `evolve.py` passed `frozenset()`; deleting a skip over an empty set is a no-op |
| `runner.py` (D83) | bridge-year evolution-ledger writer | **INERT** — inside `if is_bridge:`, reachable only from `HINDCAST_BRIDGE_YEARS`; and it is a ledger writer |
| `runner.py`, `results/cache.py`, `scenarios.py` (D76-ARM-B) | measured hindcast capacity-screen peak, default flipped True | **INERT** — `__post_init__` coerces it back to the frozen declaration whenever `not config.hindcast`; this control is `mode="forecast"`, `hindcast=False` |
| `data/fuel/plant_prices.py` (SPP-49 P19), `scenarios.py:18083-18087` | F923 own-month plausibility screen, default **True** | **INERT** — `__post_init__` coerces the field to `False` unless `(mode=="backcast" or hindcast) and gas_plant_monthly_fuel_pricing`; and the function is a no-op outside backcast mode |
| `data/renewables.py` (SPP-48/32) | SPP added to `_UNCURTAILED_FALLBACK_ISOS`, `_WIND_ZONE_SHAPE_ISOS`, `RENEWABLE_ZONE_ALLOCATION`; new SPP curtailment reader | **INERT** — NYISO is in none of those sets; another ISO's branch |
| `model/reserves/spec.py` (SPP-55) | `if iso == "SPP": _spp_design(...)` + SPP constants | **INERT** — another ISO's branch |
| `model/reserves/spec.py` (ercot-253) | `ercot_as_plan_requirement_mw` → `ercot_as_measured_requirement_mw` | **INERT** — inside `_ercot_multiproduct_design` |
| `results/scarcity.py` (ercot-252/253) | ERCOT AS readers | **INERT** — ERCOT-only readers |
| `model/interchange/{spec,miso,import_nodes,registry}.py` | MISO/SPP seam ladders, PJM interface feed | **INERT** — MISO/SPP/PJM branches; `miso_seam_neighbour_hourly_*` and `pjm_interface_feed_admissibility_gate` default `False` |
| `data/transfer_interface_limits.py` | PJM Eastern Interface feed | **INERT** — gated `pjm_interface_feed_admissibility_gate`, default `False` |
| `data/fleet/arrays.py` (nyiso-212) | `_reconciled_summer_ratios` | **INERT** — gated `cc_summer_derate_reconciled_basis`, default `False`, absent from the recipe |
| `data/fleet/floors.py` (ercot-256) | net-load-drag lay-up window mask | **INERT** — gated `netload_drag_layup_window_mask` (default `False`) AND `mode != "backcast"` returns early |
| `data/neighbor_price.py` (pjm-172 F-A) | `_measured_henry_hub_annual` | **INERT** — fires only when `year < min(trajectory)`; every `HENRY_HUB_TRAJECTORIES` entry's first knot is ≤ 2023, so it is unreachable in a 2026–2030 forecast. The sibling `_assert_hr_gas_elastic_keys_unique()` raises or does nothing |
| `data/zone_assignment.py`, `config/iso_configs.py`, `config/paths.py`, `pipeline/{backcast_config,kwargs}.py` | SPP zones / `_spp_config` / SPP paths / `elif iso == "SPP"` | **INERT** — another ISO; `backcast_config.py` is not on a forecast path |
| `pipeline/persist.py`, `results/export.py` | `solve_surface` stamp into the run record | **INERT** — recording only |
| `data/eia930/{actuals,envelopes,demand}.py` (SPP-41/31) | `_screen_fuel_spike_columns` at the shared loader seam, **ungated, repo-wide** | **INERT for NYISO — MEASURED, not assumed.** Run over NYIS 2019–2025: **0 hours repaired in every year except 2024**, where exactly **1 hour** is repaired and it is in **`NG: OTH`** (h6759, 16,117 MW vs a 3,290 MW p99.9). `NG: OTH` is threaded for the per-class **benchmark** only (`actuals.py:136-142`); its sole other reader is ERCOT-specific (`actuals.py:546-563`). NYIS `NG: WND` / `NG: SUN` / `NG: WAT` — the series that reach the LP's renewable bound and hydro — are **untouched in every year**. SPP-41's own measured-effect note agrees: the only NYISO series that moves is `other`, 3.3846 → 3.3197 TWh |
| **`data/fleet/eia860.py` (SPP-49 R-2)** | **`_apply_simple_cycle_hr_floor` — "a CONSTRUCTION, not a gate: frame-level and unconditional"** | **LIVE** |

### 5.3 The one LIVE hunk, measured

`_apply_simple_cycle_hr_floor` clamps to `EGRID_CT_HR_PHYSICAL_FLOOR` = 9.0 MMBtu/MWh any plant
whose OP rows are all `GT`/`IC`, that carries no `chp` flag, and whose eGRID `heat_rate` is below
the floor. Applied at `_rows_to_generators:1188`, i.e. **after** the `status == "OP"` filter at
`:1174-1176`. Evaluated against `data/raw/eia-860/eia860_generators.parquet` filtered to `NYIS`:

| plant | prime mover | technology | eGRID HR → 9.0 | net summer MW |
|---|---|---|---|---|
| 2681 Greenport | IC | Petroleum Liquids | 8.000 | 5.4 |
| 57186 Chautauqua LFGTE | IC | Landfill Gas | 6.053 | 9.6 |
| 59453 Albany Medical Ctr Cogen | GT | Natural Gas Fired CT | 5.773 | 4.0 |

**NYISO footprint: 3 plants / 10 rows / 19.0 MW net summer** — 0.042 % of the leg's own
45,205 MW total capacity, and **not one of them is a `gas_cc`**, so none is a retrofit candidate.
(For the record, per BA: PJM 26 plants / 977.3 MW, MISO 19 / 789.1, SWPP 11 / 1,167.8, ERCO 4 /
638.0, CISO 3 / 214.7, ISNE 1 / 1.5.)

### 5.4 Consequence — the screen is an A/B at HEAD

Rule 29 `[R-SCREEN]`(b): *"A **LIVE** hunk is the only thing that earns a control solve, and then
only for the years the screen needs."* One hunk is LIVE, so **the committed bundle is NOT used as
the control**. The screen solves **both arms at HEAD**, concurrently (rule 12 `[R-PARALLEL]`:
separate invocations, separate `--out-dir`, years strictly sequential inside each). This removes
the drift question entirely rather than bounding it, and it costs ~30 min of wall clock rather
than 60 because the two are concurrent (2 × ~3.6 GB peak RSS against 15 GB available).

The committed bundle is still the reference the FINDING re-bases the campaign's rows against; it
is simply not the screen's control.

---

## 6. THE SCREEN — PRE-REGISTERED HERE, BEFORE THE EDIT AND BEFORE THE SOLVE

### 6.1 Recipe and arms

```
# CONTROL (HEAD, unpatched)                       # ARM (HEAD + the §1 repair)
python scripts/run_ces_leg.py \                   python scripts/run_ces_leg.py \
  --config configs/scenarios/nyiso_scenario_base_2026_2030.yaml \
  --matrix configs/scenario_campaign_matrix.yaml \
  --case CES-T80 --campaign capx-d87-screen \
  --out-dir results/capx-d87-screen/<control|arm>/NYISO/CES-T80
```

ISO NYISO, `mode="forecast"`, 2026–2030, weather year 2024, `use_campd_bins=True`,
`ccs_retrofit_available_year=2028`, `ccs_retrofit_max_gw_per_year=3.0`,
`federal_ces_acp_usd_per_mwh=50.0`, `federal_ces_ccs_capture_fraction=0.95`, premium 0.0.

**THE SCREEN YEAR IS 2030**, named here before the solve, because 2030 is the year this
mechanism's own measured footprint is largest for NYISO (2.000 GW of cap headroom against 0.728
in 2029 and 0.016 in 2028 — §2.3). It is not the year with the largest residual; no residual
enters this choice. A 2030 forecast decision is path-dependent on 2026–2029, so the arm solves the
control's own five-year horizon and the verdict is read on 2030, with 2028 and 2029 as
confirmatory rows.

**Sequencing.** The arm is edited and solved only once capx **D88**'s duplicate-`unit_id` guard is
on `main`, so that if folding the dual grows the NYISO retrofit set into a later re-mint the
SCREEN says so rather than a downstream scorer.

### 6.2 Gates — STRUCTURAL, STOP-ONLY. Each may kill the arm; none may promote it.

**G1 — the identity, and the centrepiece.** In the ARM's `evolution_2028.json` and
`evolution_2029.json` retrofit rows: `attr_post_usd_per_mwh == 47.50` (= ACP 50.00 × 0.95) and
`attr_unabated_usd_per_mwh == 0.0`. In `evolution_2030.json`: `0 < attr_post_usd_per_mwh ≤ 47.50`
and `attr_unabated_usd_per_mwh == 0.0`. In the CONTROL, all six values are `0.0`.
**FAIL kills the arm** — the mechanism is not doing what its own arithmetic says.
*(Read-out, not a gate: the 2030 arm's `attr_post / 0.95` IS the 2029 endogenous dual, which no
committed artifact can supply. It is reported, never scored.)*

**G2 — direction and order.** ARM − CONTROL retrofit MW: **2028 ∈ [0, +16] MW** (cap-saturated),
**2029 ∈ (0, +728] MW**, **2030 ∈ (0, +2,000] MW**. A DECREASE in any year, a 2029 or 2030 delta
of exactly zero, or any year exceeding its stated bound, **kills the arm**.

**G3 — the cap holds.** No year's retrofit total exceeds 3,000 MW in either arm.

**G4 — 2026–2027 inertness.** Every 2026 and 2027 ledger row byte-identical between arm and
control, and **no non-CCS ledger row moves** in those two years. (`apply_ccs_retrofit` returns at
`ccs.py:354-355` before any pricing below 2028, so this is a construction check, not a hope.)

**G5 — no non-target load-bearing criterion flips.** The leg's I1–I14 invariant list stays PASS in
the arm, and no `full_horizon_summary` invariant that PASSes in the control FAILs in the arm.

**G6 — byte-identity off the target row.** Proven **by construction and by test, never by an LP**:
every `CES-P*` and voluntary leg has no clean row on `gas_cc_ccs`, so `by_fuel` carries no entry,
so `clean_credit_for_zone` returns `0.0`, so `max(x, 0.0) == x`. The `None`-family unit test in
§7 is the proof; no control solve is spent on it. Likewise every backcast keeper and every
`ff-t1h` hindcast, on the three independent gates of §4.

### 6.3 What the screen may NOT do

It is never read against a price, emissions or capacity residual; it never contributes to a
determination; it may kill the arm and never promote it. A gate reading "did the retrofit set get
closer to the premium legs" would be fitted-mechanism selection and is not among the gates above.

---

## 7. DELIVERABLES

1. The fix — `ccs.py:475-476` + the `evolve.py:664` threading, `None`-default keyword.
2. A seam test in `tests/unit/model/test_ccs_retrofit.py`: (a) a target-row config with a live
   `gas_cc_ccs` clean credit buys a retrofit a zero-premium config does not; (b) a `None` family
   is byte-identical to HEAD; (c) `attr_unabated` folds a `gas_cc` credit when one exists
   (symmetry, even though no committed config mints one).
3. The cache-epoch entry naming the 12 target-row bundles of §4 — and **not** the MISO T1-F
   family (§3).
4. The NYISO mechanism-matrix shard cells `ccs_retrofit_screen` and `federal_ces`
   (rule 28 `[R-MECH-MATRIX]` duty b). No new `ScenarioConfig` field ⇒ duty (c) is not engaged.
5. `docs/handoffs/FINDING-capx-d87-2026-09-08.md` — re-bases the campaign's target-row rows and
   **ROUTES** the six ISO policy FINDINGs' `CES-T80` numbers to the SCN desk for re-statement,
   including the two §2.4 corrections. This lane does not re-state them itself.

## 8. RULE 31 `[R-RETAIN]` POSTURE

`results/capx-d87-screen/**` is added to `.gitignore` the moment it is written, which discharges
rule 29 `[R-SCREEN]`(c) in full — the parity gate only ever sees committed directories. **No
solved bundle is deleted from local disk**, whatever this lane's own reading of the result, until
the owner has ruled on promotion. The container is ephemeral, so the promotion question is asked
explicitly in the close, with a plain statement that the bundles will not survive the session.

## 9. WHAT THIS PRECOMMIT TOUCHED

`docs/handoffs/PRECOMMIT-capx-d87-2026-09-08.md` — this file. Nothing else: no `src/`, no test,
no config, no matrix shard, no registration, no result bundle. Zero LP.
