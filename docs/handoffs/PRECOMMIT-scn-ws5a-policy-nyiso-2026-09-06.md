# PRECOMMIT — SCN-WS5A-POLICY-NYISO: the Stage A-POLICY case set, phase 0 at THE PIN

**Lane** SCN-WS5A-POLICY-NYISO · **Model** Opus (`claude-opus-5`, rule 27 `[R-PUSH]`) ·
**Date** 2026-09-06 · **Branch** `claude/scn-ws5a-policy-nyiso-rsc94n` · **Data profile**
`nyiso` (full clone — `hydrate_data.py --profile nyiso` reports every blob already local) ·
**Campaign** `scn-campaign-policy-2026-09-06`, kind `scenario`, `reference_case: REF` ·
**Charter** SCN-DESK ledger §5 policy charter **v6** (r#17) · **Predecessors**
`PRECOMMIT-scn-ws5a-resolve-2026-09-06.md` (THE PIN, the inherited G-DRIFT),
`FINDING-scn-ws5a-load-nyiso-2026-09-06.md` (the pre-fix REF this ISO's load lane published)
and `PRECOMMIT-scn-ws5a-policy-ercot-2026-09-06.md` (the first policy lane's phase 0, the
template for this one).

**Pushed before the first solve** (rule 29 `[R-SCREEN]`). Every number below is zero-LP: a
resolved config at THE PIN, a committed artifact, or arithmetic on the two. Nothing here is
revised after a solve; §6's predictions are scored as written, misses at full magnitude.

---

## 0. THE PIN

```
bdfb3095e9fa0cd2bec3f4e843f320b42588c72b
```

Named by `PRECOMMIT-scn-ws5a-resolve-2026-09-06.md` §0 (precondition P1). Verified here:
`git merge-base --is-ancestor bdfb3095 origin/main` → **yes**; `origin/main`
(`bbeb25fe`) is **170 commits** past it at PRECOMMIT time. **THE PIN IS NOT MOVED AFTER THE
FIRST SOLVE.** My keys are therefore **pre-fingerprint keys** (capx D79 entered `cache_key()`
after the pin); the pin records them and §2 lists them.

## 0.1 Bottom line before any LP

1. **Four of thirteen chartered cases are KILLED on a proven LP identity; nine survive.**
   `CARB-LO`, `CARB-MID` and `CARB-HI` resolve to **exactly REF's carbon price in every one of
   the five years** — the ruling-S2 floor, measured (§4.1) — and `carbon_price_path` has no
   other LP-reaching consumer (§4.2), so the three arms are LP-input-identical to REF.
   `CARB-MID+LOAD-HI` is the same identity applied to the load pairing: it is **LP-identical to
   the committed `LOAD-HI` leg**, which is what the campaign YAML's own comment on the case
   pre-declares for a program ISO. None of the four is solved.
2. **NO voluntary leg is killed — NYISO is the structural INVERSE of ERCOT, and this is the
   campaign's second regime reading.** ERCOT's `VOL-MID` was slack in all five years because
   197–235 TWh of eligible wind+solar dwarfed V. NYISO's eligible fleet generates **7.31 TWh
   (2026–28) / 11.89 TWh (2029–30)**, against V = **13.86 → 18.29 TWh** at `mid` and
   **15.68 → 24.68 TWh** at `high`. The row **binds in every year of every voluntary arm**
   (§3.2). The cause is ruling **S10**: NYISO's clean fleet is hydro (26.2 TWh) and nuclear
   (27.0 TWh), and the renewable-only eligible set credits **neither**.
3. **`CAP-STATE-TIGHT` survives, and the post-D77 REF has changed which years bind.** SCN-CAP
   §3 measured the row binding on NYISO in all five years against the **pre-D77** REF. Re-done
   here at THE PIN against the **re-solved** REF: the budget binds in **2026 and 2027 only**
   (margins +0.53 and +2.17 Mt) and is **slack by 4.5 / 7.2 / 9.3 Mt in 2028–2030** (§4.3),
   because D77 + D65-B cut REF's 2028–2030 CO2 from 24.11/23.75/20.89 to
   **17.16/13.71/10.90 Mt**. It solves on the 2026–2027 binding, and §6 pre-registers the
   mechanism-aware prediction that it in fact binds in **all five** years — with emissions
   **higher** than REF's in 2028–2030.
4. **NYISO's REF is the campaign's cleanest, so this lane's price side is NOT
   disclosure-only.** 14/14 invariants PASS, `unserved_mwh` 0.0, `hours_ge_500` 0,
   `backstop_built_mw` 0.0, reserve margin +0.185 → +0.201 in all five years (§7 gate **G2**).
   ERCOT's shortage caveat does not transfer here; every price, captured price and deployment
   level below is campaign-grade. The **level** caveat that does bind is the leakage line:
   imports carry **10.2–11.7 Mt**, ~41 % of the scored in-ISO total, in REF alone.
5. **Two charter literals confirmed in this ISO's favour.** The v6 G7 correction is right and
   binds asymmetrically here: `VOL-MID` **survives** on NYISO, so the `$4.5/MWh` mid ceiling is
   a live bound for one arm and `$7.0/MWh` for the other three (§3.3). And **G8 is vacuous on
   NYISO** — REF curtails **exactly 0.0 MWh** of wind and solar in every year and arm
   (potential = delivered to the MWh, measured §3.4) — so the "curtailment before thermal"
   ordering has no object; a NON-zero Δcurtailment would itself be the finding.

---

## 1. Preconditions — verified

| # | requirement | verdict | evidence |
|---|---|---|---|
| **P1** | RESOLVE names the pin; NYISO's REF re-solved post-D77 with G1 PASS | **MET** | `1b95d430` (#5214) §0 names `bdfb3095`. NYISO's three legs are RESOLVE legs 3–5 (`016e2fbe`, `fc2d80ac`, `86062a0a`), all on `main`; desk r#16 records G1 identity to 1e-9 on 13/36/37 converted NYISO units and NYISO 2030 CO2 26.31 → 14.17 Mt on the LOAD-HI arm. |
| **P2** | NYISO's REF leg at the pin, at the **`-r2`** path | **MET** | `results/scn-campaign-load-2026-09-06-r2/NYISO/REF/`, key **`f10cc93084b4c0db`**, sidecar `frontend/data/hindcast/nyiso-2026-2030-scn-campaign-load-2026-09-06-ref.json` (`provenance.scored_at_sha` `931866ccbbb7`, `cache_epoch` `f10cc93084b4c0db`, 5/5 years, 14/14 PASS). The key is **exactly** RESOLVE §3's declared NYISO REF pin key, reproduced independently by this lane's own resolve chain (§2) — that is the identity that proves I am reading the post-fix REF and not the pre-fix one at `…-09-06/NYISO/REF/` (key `aed447f88457dff7`, CO2 20.894 Mt at 2030 vs the re-solved 10.903). **REF is never re-solved as an answer** (§8 declares the one rematerialization and its gate). |
| **P3** | the carbon form is the committed RFF path ladder | **MET at the pin** | `git show bdfb3095:configs/scenario_campaign_matrix.yaml`: `CARB-LO/MID/HI` → `carbon_price_path: low/mid/high`; `ALL-CLEAN` → `carbon_price_path: mid`. Resolved values measured in §4.1. |
| **P4** | rule 12 concurrency (as relaxed by ruling **S14**) | **NOT ESTABLISHED — first solve HELD, and the owner is asked** | This container shows no LP running (`ps` clean, 15 GB free, 4 cores). But the slot is a **desk-wide** property and I cannot see other sessions: at r#17 the SCN track had ERCOT policy holding ten prepared legs and RESOLVE-CAISO (4.87 GB) + RESOLVE-MISO (9.65 GB) each with a pushed PRECOMMIT and 0 legs, and the capx track's queue contends for the same box. The charter's own clause governs: *"if you cannot establish what else is solving, hold and ask rather than assume the slot is free."* **Nothing is solved until the owner names the slot.** NYISO is a light ISO (peak RSS **3.5–3.9 GB** measured on the REF/LOAD-HI legs), so it pairs safely with anything except a second NYISO. |
| **P5** | `mass_cap_tons_by_year` + `CAP-STATE-TIGHT` exist | **MET, and IN scope for NYISO** | Both live at the pin (SCN-CAP `89b0a9f4`). NYISO is in `CAP_AND_TRADE_PROGRAMS` and is named by the schedule; §4.3 redoes SCN-CAP's binding table at this pin against the re-solved REF. |

## 1.1 The constant families this lane consumes (desk standing change #1)

All read at **THE PIN** `bdfb3095`, verbatim, by the phase-0 instrument
(`docs/handoffs/scn-ws5a-policy-nyiso/phase0-nyiso-2026-09-06.py`, whose JSON output is
committed beside it):

| family | module | value at the pin |
|---|---|---|
| `CARBON_PRICE_PATHS` | `config/fuel_trajectories.py` | `zero` {2026:0, 2030:0, 2040:0, 2050:0}; `low` {0, 8, 18, 25}; `mid` {0, 15, 35, 50}; `high` {0, 30, 70, 110} |
| `STATE_CARBON_PRICE_BY_ISO` | `policy/carbon.py` | `NYISO` present (RGGI) — resolved trajectory §4.1 |
| `CAP_AND_TRADE_PROGRAMS` | `policy/cap_and_trade.py` | `CAISO`, `NYISO`, `NEISO`, `PJM` — **NYISO in scope** |
| `VOLUNTARY_BASELINE_SHARE` | `config/constants.py` | low {2023: 0.06}; mid {2023: 0.08}; high {2023: 0.08} |
| `VOLUNTARY_COMMITTED_DC_FRACTION` | `config/constants.py` | low {2026: 0.0}; **mid {2026: 0.5}**; high {2026: 1.0} (ruling S9) |
| `VOLUNTARY_WTP_CEILING_USD_PER_MWH` | `config/constants.py` | low 2.0; **mid 4.5**; **high 7.0** |
| `VOLUNTARY_ELIGIBLE_FUELS_DEFAULT` | `config/constants.py` | `(wind, solar, offshore_wind, geothermal)` — ruling S10 as built; **NYISO has only wind + solar** |
| `VOLUNTARY_BASELINE_ISO_WEIGHT["NYISO"]` | `config/constants.py` | `None` (needs-intake) ⇒ `w_ISO` = 1.0 |
| `federal_ces_eligible_fuels` (default) | `config/scenarios.py` | nuclear, wind, solar, hydro, geothermal, offshore_wind, gas_cc_ccs, hydrogen_ct, hydrogen_ccgt; crediting `clean_capture`, `gas_cc_ccs` at **0.95** |
| `eac_price_*` (all seven) | resolved config | **`None` on every case** — so the CES premium is the *only* exogenous EAC and `max(legacy, premium × credit)` is the premium (§6.3) |
| CES levels | `configs/scenario_campaign_matrix.yaml` | premium {10, 20, 30} $/MWh; target {2026: 0.55, 2035: 0.80, 2050: 1.00}, ACP $50/MWh (interpolated 0.5500 / 0.5778 / 0.6056 / 0.6333 / 0.6611) |
| mass-cap schedule | same YAML | `NYISO: {2026: 23.16e+6, 2030: 20.2e+6, 2040: 12.8e+6, 2050: 4.6e+6}` t (ruling S12) |
| CCS fields (post-D77/D65-B) | resolved config | `ccs_retrofit_vom_adder` **2.95**, `ccs_retrofit_capex_co2_scaling` **True**, `ccs_retrofit_fixed_cost_co2_scaling` **True**, `ccs_retrofit_capture_rate` 0.9, `ccs_retrofit_available_year` 2028 |

---

## 2. The case set at THE PIN — resolved fields and cache keys

Resolved exactly as `runner.run_scenario_iso` does: `matrix_configs(base, sweep)` →
`resolve_policy_bundle` → `set_caiso_fsno_partition(False)` → `apply_iso_scenario_defaults`,
then `config.cache_key()`. Base: `configs/scenarios/nyiso_scenario_base_2026_2030.yaml`.

**Chain validation — the three NYISO rows RESOLVE published, reproduced independently:**
`REF` **`f10cc93084b4c0db`**, `LOAD-HI` **`c2ceaefa4afafcda`**, `LOAD-HI-ORGANIC`
**`27f19f22105ab6cb`** — identical to `PRECOMMIT-scn-ws5a-resolve` §3's NYISO lines. The
resolve chain used below is therefore the one the solve will use, not a naive `cache_key()`.

| case | key at THE PIN | override vs REF | verdict |
|---|---|---|---|
| *REF (control)* | `f10cc93084b4c0db` | — | **reused, committed** (§8 rematerializes the bundle, never the answer) |
| `CARB-LO` | `68294f45fda64aed` | `carbon_price_path: low` | **KILLED — §4.2** |
| `CARB-MID` | `91d435c848c57fb6` | `carbon_price_path: mid` | **KILLED — §4.2** |
| `CARB-HI` | `3608ca88c0a19d4e` | `carbon_price_path: high` | **KILLED — §4.2** |
| `CES-P10` | `3c96d694c18e5547` | `federal_ces_enabled`, premium 10.0 | **SOLVE** |
| `CES-P20` | `9da7c76372c98406` | premium 20.0 | **SOLVE** |
| `CES-P30` | `89a70dd1140c6731` | premium 30.0 | **SOLVE** |
| `CES-T80` | `eb1b0e1df942db47` | target {2026:0.55, 2035:0.80, 2050:1.00}, ACP 50.0 | **SOLVE** |
| `CARB-MID+LOAD-HI` | `80b8a2ec7406f75d` | carbon mid + growth high + DC high | **KILLED — §4.2 (≡ `LOAD-HI`)** |
| *`LOAD-HI` (the pairing base)* | `c2ceaefa4afafcda` | growth high + DC high | **reused, committed** (§8) |
| `VOL-MID` | `9528d708b81b5074` | `voluntary_clean_demand_path: mid` | **SOLVE** |
| `VOL-HI` | `893acae55a1a898f` | `voluntary_clean_demand_path: high` | **SOLVE** |
| `CES-P20+VOL-HI` | `566335c8ca37dc17` | premium 20.0 + voluntary high | **SOLVE** |
| `ALL-CLEAN` | `e13b0d801b1ffce1` | carbon mid + growth high + DC high + CES target + ACP 50 + voluntary high | **SOLVE** |
| `CAP-STATE-TIGHT` | `76c60ac152400146` | `mass_cap_enabled` + the S12 schedule | **SOLVE — §4.3** |

**Every case keys distinctly**, so no leg can collide with another or with a pre-fix bundle.

**9 legs to solve, 45 solve-years**, plus the 2 rematerializations of §8 (10 more solve-years,
neither a new answer and neither registered).

---

## 3. Phase 0 — the voluntary row, per year, from the run's own demand

`V(ISO, y) = s_base·w_ISO·E_nonDC + f_commit·E_DC`, computed by calling
`policy.voluntary_demand.resolve_voluntary_volume` on the demand the LP is handed —
`load_demand` → `runner._scale_demand` → `data.datacenter.add_load_layers`, the runner's own
chain — not by re-deriving the memo's arithmetic. Zone list, as the LP sees it:
`Upstate_West, Capital_Hudson, Lower_Hudson, NYC, Long_Island, NYISO_external` (the priced
import node is the sixth).

### 3.1 The resolved volumes (TWh)

| posture | | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|---|
| **DC mid** (`VOL-MID`, `VOL-HI`, `CES-P20+VOL-HI`) | `E_total` | 154.094 | 155.915 | 157.757 | 159.621 | 161.507 |
| | `E_DC` | 3.641 | 5.925 | 8.209 | 10.493 | 12.777 |
| | **V (mid)** | **13.857** | **14.962** | **16.068** | **17.177** | **18.287** |
| | **V (high)** | **15.677** | **17.924** | **20.173** | **22.423** | **24.676** |
| **DC high** (`ALL-CLEAN`) | `E_total` | 158.369 | 162.448 | 166.632 | 170.923 | 175.325 |
| | `E_DC` | 5.443 | 8.861 | 12.278 | 15.696 | 19.114 |
| | **V (high)** | **17.677** | **21.148** | **24.627** | **28.114** | **31.611** |

`s_base` = 0.08 at both mid and high; `w_ISO` = 1.0; `f_commit` = 0.5 (mid) / 1.0 (high).

### 3.2 The regime test (memo Addendum A.3 / WS-3b §6) — nothing is killed

Eligible generation `G` = wind + solar **as dispatched in the paired baseline** (NYISO has no
offshore-wind or geothermal row in any committed leg; the fuel keys present are exactly
`biomass, gas_cc, gas_cc_ccs, gas_ct, gas_st, hydro, import, nuclear, oil, solar, wind`).
`G_REF` from `results/scn-campaign-load-2026-09-06-r2/NYISO/REF/`; `G_LOAD-HI` from the
LOAD-HI leg, the nearest committed baseline for `ALL-CLEAN`'s DC-high / growth-high posture.

| baseline `G` (TWh) | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| `G_REF` (wind 5.305/7.569 + solar 2.009/4.323) | 7.314 | 7.314 | 7.314 | 11.892 | 11.892 |
| `G_LOAD-HI` | 7.314 | 7.314 | 7.314 | 11.892 | 11.892 |

| arm | 2026 | 2027 | 2028 | 2029 | 2030 | regime |
|---|---|---|---|---|---|---|
| **`VOL-MID`** vs `G_REF` | 13.86 > 7.31 (**−6.54**) | 14.96 > 7.31 (**−7.65**) | 16.07 > 7.31 (**−8.75**) | 17.18 > 11.89 (**−5.29**) | 18.29 > 11.89 (**−6.40**) | **BINDS all five** |
| **`VOL-HI`** vs `G_REF` | 15.68 (−8.36) | 17.92 (−10.61) | 20.17 (−12.86) | 22.42 (−10.53) | 24.68 (−12.78) | **BINDS all five** |
| **`CES-P20+VOL-HI`** | identical V to `VOL-HI` | | | | | **BINDS all five** (its own arm's `G` may exceed `G_REF`; §6.4) |
| **`ALL-CLEAN`** vs `G_LOAD-HI` | 17.68 (−10.36) | 21.15 (−13.83) | 24.63 (−17.31) | 28.11 (−16.22) | 31.61 (−19.72) | **BINDS all five**, largest shortfall |

**Why NYISO is the inverse of ERCOT, stated as a mechanism and not a surprise.** The regime is
decided by ruling **S10**'s eligible set, not by how clean the ISO is. NYISO's REF clean share
is 0.39 — *higher* than ERCOT's 0.35 — but **hydro (26.2 TWh) and nuclear (27.0 TWh) carry it,
and neither is voluntary-eligible**. Its whole eligible fleet is 3.9 GW of wind+solar rising to
6.7 GW in 2029. So the same annual-matching convention that makes the row inert on a
wind-and-solar ISO makes it bind hard on a hydro-and-nuclear one. This is direct evidence for
open card **D-3c** (all-eligible vs new-builds-only crediting) from the opposite direction to
ERCOT's, and it is routed as such (§9).

### 3.3 The WTP ceiling — per arm, and both committed cells are live here

`voluntary_wtp_ceiling_usd_per_mwh` resolves **`None`** on every case, so the resolver takes
`VOLUNTARY_WTP_CEILING_USD_PER_MWH[path]`. Unlike ERCOT, **`VOL-MID` survives phase 0 on
NYISO**, so both committed cells bind a gate here:

| arm | path | ceiling |
|---|---|---|
| `VOL-MID` | mid | **$4.50/MWh** (ruling S9's cell) |
| `VOL-HI`, `CES-P20+VOL-HI`, `ALL-CLEAN` | high | **$7.00/MWh** |

Gate **G7** is bounded **per arm** at that arm's own ceiling (the v6 correction).

### 3.4 G8's object does not exist on NYISO — declared before the solve, not discovered after

`results/scn-campaign-load-2026-09-06/NYISO/report/nyiso_curtailment_by_tech.csv` (the load
campaign's committed report) records, for **every** case and **every** year 2026–2030,
`potential_mwh == delivered_mwh` to the MWh for both wind and solar, and
`curtailment_twh = 0.0` in the headline frame. The pre-D77 and post-D77 fleets are the same
VRE fleet (the D77 seam is a thermal emission rate), so this carries to the re-solved REF and
is re-measured on it at scoring time.

**Consequence:** the memo's ordering claim — *the first MWh a REC buyer pays for is one that
was being dumped* — has **no MWh to reorder** in NYISO. Gate G8 is therefore recorded **N/A
with its reason**, and it is replaced by the sharper statement it degenerates to: **a non-zero
Δcurtailment in any voluntary arm is a FINDING against the mechanism**, because the row can
only *reduce* the incentive to spill an eligible MWh. The first MWh a NYISO REC buyer pays for
must come from **entry** or from the **escape column** — which is why §6.4 predicts the escape
regime rather than a dispatch response.

---

## 4. Phase 0 — the carbon axis, the three kills, and the cap row

### 4.1 Resolved carbon $/tCO2 per year (`policy.carbon.resolve_carbon_price`)

| case | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| `REF` | 23.6363 | 25.2908 | 27.0612 | 28.9555 | 30.9824 |
| `CARB-LO` | **23.6363** | **25.2908** | **27.0612** | **28.9555** | **30.9824** |
| `CARB-MID` | **23.6363** | **25.2908** | **27.0612** | **28.9555** | **30.9824** |
| `CARB-HI` | **23.6363** | **25.2908** | **27.0612** | **28.9555** | **30.9824** |
| `CARB-MID+LOAD-HI` | 23.6363 | 25.2908 | 27.0612 | 28.9555 | 30.9824 |
| `ALL-CLEAN` | 23.6363 | 25.2908 | 27.0612 | 28.9555 | 30.9824 |
| every CES-only / VOL-only case | 23.6363 | 25.2908 | 27.0612 | 28.9555 | 30.9824 |
| **`CAP-STATE-TIGHT`** | **0.0000** | **0.0000** | **0.0000** | **0.0000** | **0.0000** |

**Δ = exactly 0.000000 in every carbon arm, in every year.** This extends WS-1b's measurement
(which read the pair at 2027 only, `NYISO 25.2908 / 25.2908 / 0.0000`) across the whole T1-F
window, and it is gate **G1** on the carbon axis, passed before any LP. The mechanism is
ruling S2's floor: `resolved = max(RGGI trajectory, RFF path)`, and the RGGI trajectory
($23.64 → $30.98/t) exceeds even the `high` path's 2030 knot ($30.00) in every year, so the
`max()` returns the program and naming a federal path changes nothing.

### 4.2 The three carbon kills and the load-pairing kill — the identity, argued not asserted

`carbon_price_path` is a string. Its **only** LP-reaching consumer is
`policy.carbon.resolved_base_trajectory_price` → `max(program, rff_path_price(path, year))`
(one call site, `carbon.py:187`, rule 19 `[R-ONE-MECH]`). Every other appearance in `src/` is a
comment, a docstring, a cache-key registration, or the `__post_init__` tripwire
`carbon_path_below_program_warning` (a `warnings.warn`, no return value reaching any array) —
verified by `grep -rn carbon_price_path src/market_sim`. The CAISO-only border-carbon adder is
the one downstream consumer of the *resolved price*, and NYISO never enters it.

So for `CARB-LO` / `CARB-MID` / `CARB-HI`: **one field differs from REF, that field's single
consumer returns an identical value in all five years, and therefore every LP input is
identical to REF's.** The keys move (`carbon_price_path` is a tier-1 keyed field) — the same
*"key moves, answer cannot"* class as ERCOT's `CAP-STATE-TIGHT` — but no LP input does. The
three arms are byte-identical to REF and are **not solved**.

`CARB-MID+LOAD-HI` is the same identity applied one pairing over: its fields are
`carbon_price_path: mid` + `demand_growth_path: high` + `datacenter_load_path: high`, of which
the carbon half is proven inert, leaving exactly `LOAD-HI`'s two fields. It is therefore
**LP-identical to the committed `LOAD-HI` leg** (key `c2ceaefa4afafcda`), not to REF — so its
answer exists, and §8 rematerializes that bundle so the case is *reported* with its full delta
set rather than merely dismissed. The campaign YAML pre-declares exactly this: *"on
CAISO/NYISO/NEISO this case's carbon half is exactly REF, so the case is LOAD-HI with a carbon
label and the delta it measures is the load delta alone."*

**What these four kills are NOT evidence of.** They say a *federal RFF* price of $8–30/t is a
no-op where RGGI already charges $23.64–30.98/t. They say **nothing** about whether carbon
pricing works in New York — NYISO is already carbon-priced, at **6.7× (2027) falling to 2.1× (2030)** the `mid`
path's own level in the years that path is non-zero. Quoting "no effect" from these rows would
invert their meaning (WS-1b §3.8's caution, restated because it now applies to four of my
thirteen cases).

### 4.3 `CAP-STATE-TIGHT` — the resolved budget, and SCN-CAP's table redone at THE PIN

`resolve_carbon_program` returns a `cap_spec` (never a `price_adder`) in every year under the
case, and `price_adder` (never a `cap_spec`) in every year under REF — the resolver invariant,
measured, and that is gate **G11** passed pre-solve: **one instrument at a time, never both**.
`scheduled_power_sector_budget` returns the S12 schedule interpolated linearly:

| year | budget (Mt) | **re-solved** REF CO2 (Mt) | margin (REF − budget) | binds? | *(SCN-CAP §3, pre-D77 REF)* |
|---|---|---|---|---|---|
| 2026 | 23.16 | 23.6923 | **+0.53** | **YES** | +0.53 YES |
| 2027 | 22.42 | 24.5911 | **+2.17** | **YES** | +2.17 YES |
| 2028 | 21.68 | 17.1630 | **−4.52** | no | *+2.43 YES* |
| 2029 | 20.94 | 13.7082 | **−7.23** | no | *+2.81 YES* |
| 2030 | 20.20 | 10.9030 | **−9.30** | no | *+0.69 YES* |

**SCN-CAP predicted this re-check and named the years it thought could flip.** Its §3 wrote:
*"NYISO-2030's 0.69 Mt … [is] the one a re-solved REF could plausibly cross; the policy lanes
redo this table at their pin."* Measured: **three years cross, not one** — 2028, 2029 and 2030
— because D77 + D65-B did not merely re-account the CCS rate, they pulled far more retrofit
capacity in (REF now carries 2,984 / 5,256 / 6,256 MW of `gas_cc_ccs` generating
22.8 / 30.0 / 37.4 TWh). The case **still solves** on the 2026–2027 binding; §6.5 pre-registers
why I nevertheless expect it to bind in **all five**.

---

## 5. G-DRIFT (rule 29(b)) — the committed REF is the control, and no control solve is earned

### 5.1 `1cc45bb2 .. bdfb3095` — inherited, with NYISO's own premise re-stated

RESOLVE's §1 classified 34 non-merge solve-path commits: **4 LIVE** (capx D77, D65-B ISO-wide;
D67-ARM, D81 **PJM only**) and 30 INERT with a stated reason. For **NYISO**, D77 and D65-B are
LIVE **and are the object of the re-solve, not a confound** — which is precisely why this lane
differences against the `-r2` REF and never against the pre-fix one. The two PJM-only
mechanisms are inert here, re-measured on this lane's own resolved NYISO config rather than
inherited: `capacity_adequacy_requirement_published_by_iso` → **`None`**,
`capacity_market_supply_clearing_by_iso` → **`None`**, `retirement_sector_gate` → **`False`**,
`pjm_vre_accreditation_vintage` → **`False`**.

⇒ **Form 4 is VALID for NYISO.** The committed re-solved `REF` (`f10cc93084b4c0db`) and
`LOAD-HI` (`c2ceaefa4afafcda`) **are** the control. No control solve is spent.

### 5.2 `bdfb3095 .. origin/main` — for the record; I solve at THE PIN regardless

`git diff bdfb3095 origin/main` over the rule-29 window (`src/market_sim`, `scripts/lib`,
`run_full_horizon.py`, `run_ces_leg.py`, `check_forecast_invariants.py`, `configs/`,
`data/raw/_validation-source`, `data/raw/reference`): **18 files, +1,812 / −59, across 8
non-merge commits.** All eight INERT for a NYISO forecast leg:

| commit | what | INERT because |
|---|---|---|
| `6164231e` | capx D75-R-ARM — `pjm_vre_accreditation_vintage` armed for PJM | Arrives through `_pjm_config`'s `default_scenario_overrides`; measured **`False`** on the resolved NYISO config, and its predicate additionally requires `pjm_accreditation_design_vintage` (**`False`** here). |
| `486c115f` | constants facade re-export of two D75-R names | Import surface only; no behavioural statement. |
| `7ff10b64` | `ruff format` on the miso-231 files | AST-identical by the commit's own verification. |
| `14ae4d76` | miso-231 hourly neighbour-anchored MISO↔PJM seam ladder | New field, default off, and MISO-scoped (`_inject_seam_ladder` is byte-identical unarmed). NYISO has no MISO seam. |
| `cd96fa26` | pjm-167 F2 — published transfer limit gated on its own flows | New field `pjm_interface_feed_admissibility_gate` default `False`; PJM-scoped and backcast-facing. Absent from the resolved NYISO config. |
| `beb74f0f` | pjm-167 F1 — backcast EIA-860 vintage tracks the solved year | New field `eia860_vintage_tracks_solve_year` default `False`, and its branch is `mode == "backcast" or hindcast` — both false on a forecast leg (measured: `mode=forecast`, `hindcast=False`). |
| `16210868` | capx D79 phase 1 — the solve-surface fingerprint enters `cache_key()` | **Key-only, and it moved zero keys at landing.** It carries no LP input. My pin is pre-D79, so §2's keys are the pre-fingerprint keys. |
| `bf97317f` | capx D78-R2 step 0 — delete the producer-less `exempt_unit_ids` | D78's seam needs `retirement_sector_gate` **and** a clearing-armed ISO; NYISO measured `False` / `None`. |

**No LIVE hunk ⇒ no control solve is earned under clause (b), on either window.**

---

## 6. What each surviving leg is expected to do — pre-registered, from measured responses

Sources, all measured before this lane and none of them a residual: **WS-1b §3.8** (NYISO's
exact carbon identity), **WS-2a** (the NEISO CES target-row escape regime), **WS-2b §3** (the
ERCOT CES premium ladder's saturation mechanism), **WS-3b §6** (the voluntary row's
arithmetic), **SCN-CAP §1** (the mass-cap row's dual identity, proven on the trivial-first LP),
and the committed re-solved NYISO REF itself. Where a level cannot transfer across ISOs I
predict a **direction and a mechanism**, never a level borrowed from another market.

### 6.1 The REF this lane differences against, restated as numbers (gate G2)

| year | CO2 Mt | import CO2 Mt | lw $/MWh | clean share | credited/demand | reserve margin | unserved | curtail |
|---|---|---|---|---|---|---|---|---|
| 2026 | 23.6923 | 10.455* | 50.19 | 0.3924 | 0.3925 | 0.1851 | 0.0 | 0.0 |
| 2027 | 24.5911 | 10.156* | 49.18 | 0.3879 | 0.3879 | 0.1774 | 0.0 | 0.0 |
| 2028 | 17.1630 | — | 50.92 | — | 0.5205 | 0.1704 | 0.0 | 0.0 |
| 2029 | 13.7082 | — | 49.28 | — | 0.5864 | 0.2083 | 0.0 | 0.0 |
| 2030 | 10.9030 | — | 54.95 | — | 0.6229 | 0.2009 | 0.0 | 0.0 |

\* the 2026–2027 import line is the **pre-D77** REF's, quoted because those two years are
below `ccs_retrofit_available_year` and the seam cannot reach them; 2028–2030 are deliberately
left blank rather than filled from a contaminated bundle, and are measured on the
rematerialized REF at scoring time (§8).

### 6.2 The sharpest prediction — a cross-lane identity, not a band

**P-1.** The rematerialized `REF` at key `f10cc93084b4c0db` reproduces the committed
`full_horizon_summary.json` **exactly**: `co2_mt` 23.6923 / 24.5911 / 17.1630 / 13.7082 /
10.9030, `lw_price` 50.193 / 49.18 / 50.92 / 49.28 / 54.95, and every
`generation_by_fuel_mwh` row to 1e-6 relative. *Why this is an identity and not an analogy:*
same code (THE PIN), same config (key equality is a hash of the resolved config), same weather
year, and the solve path is deterministic. **Scored as a hit only on an exact match**; any
drift is a real finding about solve determinism at the pin and is reported at full magnitude,
never explained away. Same for `LOAD-HI` at `c2ceaefa4afafcda`. This is gate **G13**.

**P-2.** No solved arm's 2026 is byte-identical to REF's. NYISO has **no** free year: unlike
ERCOT, whose RFF 2026 knot is $0, every surviving NYISO case's mechanism (a CES premium, a CES
target row, a voluntary row, a mass cap) is live from 2026. I therefore expect a non-zero delta
in **every** solved leg-year, and a zero would be the finding.

### 6.3 CES premium — direction, the dominant channel, and where it saturates

The premium reaches dispatch through `apply_eac_to_mc` as `max(legacy eac_price_*, premium ×
credit)`. **Every `eac_price_*` field resolves `None` on NYISO** (§1.1), so the effective EAC
*is* the premium for every eligible unit — the arms are provably not identical to REF, which is
the phase-0 non-kill.

**P-3.** CO2 falls and clean share rises monotonically REF → P10 → P20 → P30 in every year.
**P-4.** **The dominant channel is the CCS retrofit screen, not dispatch reordering.** NYISO's
eligible clean fleet is already fully dispatched (zero curtailment, §3.4) and hydro is
monthly-budget constrained and so dispatch-inert by construction; the one *elastic* eligible
resource is `gas_cc_ccs`, which credits at **0.95 × premium** ($9.5 / $19.0 / $28.5 per MWh) in
both dispatch and the retrofit screen. So I predict retrofit capacity **above** REF's
2,984 / 5,256 / 6,256 MW in 2028–2030 in all three arms, monotone in premium, and CO2 falling
with it. **P-5.** 2026–2027 (below `ccs_retrofit_available_year`) move **least**: the only
channels are the entry screens and a small reordering, so I predict **|ΔCO2| < 1.0 Mt** in
2026 and 2027 in all three arms, against **|ΔCO2| > 1.0 Mt** in at least one of 2028–2030 in
`CES-P20` and `CES-P30`. *This is the sharpest falsifiable split in the CES block.*
**P-6.** **Saturation, but by a different cap than ERCOT's.** WS-2b measured the ERCOT ladder
saturating on the 12 GW/yr renewable queue budget so that CES-20 and CES-40 commissioned
identical builds. NYISO's binding cap should be the **3 GW/yr/ISO CCS retrofit cap** instead,
because the retrofit is the elastic margin here. I predict `CES-P20` and `CES-P30` land
**within 15 %** of each other on ΔCO2 while `CES-P10` separates from `CES-P20` by **more**
than that — sub-linear, saturating from above. **P-7.** `avg_price` falls in all three arms
(clean units bid their credit lower), and `negative_price_hours` — **0 in every REF year** —
goes **> 0 in `CES-P30`** (a $30/MWh credit drives wind/solar zone adders to −$30 and the
dump cost with them). A zero there would say the premium never sets the margin in NYISO.

### 6.4 CES target and the voluntary rows — the duals, and why both escape

**P-8 (gate G4).** `CES-T80` is in the **escape regime in every year**: measured from the
committed REF, credited MWh (nuclear + hydro + wind + solar + 0.95 × `gas_cc_ccs`) over the
run's own demand is **0.3925 / 0.3879 / 0.5205 / 0.5864 / 0.6229** against a target of
**0.5500 / 0.5778 / 0.6056 / 0.6333 / 0.6611**, i.e. a shortfall of **24.27 / 29.60 / 13.41 /
7.49 / 6.17 TWh**. So `dual = ACP $50.0000 exactly` and `escape MWh = target(y)·D − credited`.
**The one year I flag as genuinely uncertain is 2030**: its 6.17 TWh gap is ~1.6 GW of further
CC→CCS conversion away from closing, and a $50/MWh signal is a very large one. If 2030 (or
2029) comes back with a strictly interior dual `0 < dual < 50`, that is **G4 passing on its
other leg**, not a miss — the gate is stated as an identity in both directions.
**P-9.** `CES-T80` produces the **largest deployment response of any leg**: the $50/MWh dual
reaches the entry and retrofit screens through the existing `clean_attribute_price_by_fuel`
seam, so I predict renewable builds and CCS retrofits at their annual caps in every year from
2027, exceeding `CES-P30`'s.
**P-10 (gate G7).** `VOL-MID`: dual = **$4.5000/MWh exactly** in all five years, escape MWh
≈ 6.5 / 7.6 / 8.8 / 5.3 / 6.4 TWh before any dispatch response. `VOL-HI` and
`CES-P20+VOL-HI`: dual = **$7.0000/MWh exactly**, escape ≈ 8.4 / 10.6 / 12.9 / 10.5 / 12.8 TWh.
`ALL-CLEAN`: dual = **$7.0000/MWh exactly**, escape ≈ 10.4 / 13.8 / 17.3 / 16.2 / 19.7 TWh.
The shortfalls are 0.9–2.4× the entire eligible fleet's output, far beyond what a $4.5–7/MWh
signal can build against a ~$50/MWh energy price, so I expect the escape rather than an
interior dual in **every** voluntary leg-year.
**P-11.** Because the escape absorbs the shortfall at a ceiling that is **9–14 %** of NYISO's
energy price, the voluntary arms' **CO2 and price deltas are small**: I predict
**|ΔCO2| < 1.5 Mt** in every year of `VOL-MID` and `VOL-HI`. The voluntary axis's NYISO content
is the **dual, the escape volume and the eligible-fleet entry response**, not an emissions
response. **P-12.** `VOL-HI`'s escape exceeds `VOL-MID`'s in every year and its ΔCO2 is at
least as negative — the ordering, not the level, is the claim.
**P-13 (gate G8, the degenerate leg).** Δcurtailment = **exactly 0.0** in every voluntary
leg-year, because REF curtails nothing (§3.4). A non-zero value is a finding against the row.

### 6.5 `CAP-STATE-TIGHT` — the price-vs-quantity result, and the non-obvious prediction

The naive phase-0 reading (§4.3) is "binds 2026–27, slack 2028–30". **I predict it binds in all
five years, and that 2028–2030 emissions come back HIGHER than REF's.** The mechanism: the case
sets `state_carbon_pricing: true` **with** the row, so the row **replaces** the $23.64–30.98/t
RGGI adder (G11, measured). REF's low 2028–2030 CO2 is *caused by* that adder — it is what
makes the CCS retrofit screen clear (the NYISO load FINDING §5 and capx D50's asymmetry both
say the screen is armed by the state carbon program). Remove the adder and the retrofits do
not clear; emissions revert toward the ~24 Mt trajectory of 2026–2027; that exceeds the
2028–2030 budgets of 21.68 / 20.94 / 20.20 Mt; so the row binds and the dual rises until
emissions equal the budget.

**P-14 (gate G10).** `emissions_mt` equals the budget to **1e-6 relative** in every binding
year, and `co2_cap_price_usd_per_t` > 0 there; in any slack year the dual is **0 exactly** and
`n_co2_caps_binding` = 0.
**P-15.** ΔCO2 vs REF = **−0.53 / −2.17 Mt** in 2026–2027 and **+4.5 / +7.2 / +9.3 Mt** in
2028–2030 (i.e. the case's CO2 = the budget in all five years). *This is the most reasoned and
most likely to miss prediction in the lane; the alternative outcome — the cap slack from 2028
with `dual = 0` and CO2 ABOVE 20.2 Mt — would mean the schedule is not a binding constraint at
all in the back half, which is a different but equally reportable result.*
**P-16 (gate G12).** The endogenous dual **exceeds** the exogenous RGGI adder it replaced in
every binding year: `co2_cap_price` > 23.6363 (2026), > 25.2908 (2027), and if 2028–2030 bind,
> 27.06 / 28.96 / 30.98. Reported side by side, which is the price-vs-quantity comparison the
case exists for. **P-17.** A "tight" mass cap on WS-1a's 80 %-by-2050 slope is **looser than
the RGGI price path** on NYISO from 2028 once CCS is in the fleet. If P-15 holds, the campaign's
headline reading of this case is not "the cap cuts emissions" but *"a quantity instrument
calibrated to a 2025 anchor under-delivers against a price instrument once an abatement
technology arrives"* — and that is the case's value, not a defect in it.

### 6.6 The combined legs — both nettings (ruling S11)

**P-18.** `CES-P20+VOL-HI` carries the CES **premium** (a price, no row), so D-6 has **no
dispatch content** there: the premium ($20) exceeds the voluntary ceiling ($7) in every year,
so one certificate is sold to the higher bidder through the screens' existing `max()` and I
expect the **voluntary dual to be irrelevant to deployment** in this arm while remaining the
row's own escape price. Its eligible generation should exceed `CES-P20`'s (the premium builds
VRE), so its escape MWh should be **smaller** than `VOL-HI`'s — the one place the two axes
interact measurably.
**P-19.** `ALL-CLEAN` is the one arm where D-6 has content (a CES **target** row and the
voluntary row both count a clean MWh). Both nettings are reported side by side per §7's duty,
with the CES dual under each; **counts-toward is the headline** (as built), **additional**
beside it — computed at the report layer as `federal_credited − V ≥ target(y)·D`, with its
implied escape `max(0, target·D + V − federal_credited)` priced at the ACP. Neither is
asserted as the answer; D-6 is open. Under counts-toward I expect both rows in escape and both
duals at their ceilings ($50 and $7); under the additional reading the CES escape grows by
**V** (17.7 → 31.6 TWh), i.e. the two readings differ by **more than the entire eligible
fleet's output** — the largest D-6 spread the campaign will produce, and the reason NYISO is
the ISO where the open card actually bites.

---

## 7. Gates — STRUCTURAL and STOP-ONLY (rule 29). Nothing is gated on a residual.

| gate | statement | how measured |
|---|---|---|
| **G1** | the resolved-input premise reproduces at THE PIN | §4.1's carbon identity (Δ = 0.000000, five years, four arms); §3.1's volumes from the runner's own demand chain; §4.3's budgets from `scheduled_power_sector_budget`. **Already PASS, pre-solve.** |
| **G2** | **REF-side precondition** (desk standing change #2) | REF carries the adequacy state WS-5A measured: **14/14 invariants PASS**, `unserved_mwh` 0.0, `hours_ge_500` 0, `backstop_built_mw` 0.0, reserve margin +0.185 → +0.201, all five years. **Consequence, declared now:** NYISO's price, captured-price and deployment **levels ARE campaign-grade** — no year is disclosure-only. The one standing level caveat is the **leakage line** (imports ≈ 41 % of scored in-ISO CO2), which is disclosed beside every CO2 number, not used to discount one. |
| **G3** | **footprint confinement** | *CES-premium* arms move eligible-class rows, the thermal rows they displace, and the retrofit ledger — nothing else; *CES-target* arms additionally move the FEDERAL_CES dual and escape column; *voluntary* arms move eligible-class rows, thermal rows and the escape column only, with every non-eligible zero-carbon row (nuclear, hydro) moving only through dispatch, never through crediting; *cap* arms move fossil rows and imports only. |
| **G4** | **`CES-T80` dual identity** | dual = ACP **$50.0000 exactly** in every year the target is unmet, escape MWh = `target(y)·D − credited`; a strictly interior dual **only** where it is met. Both directions are a PASS; a dual outside `[0, 50]`, or an ACP-valued dual with the target met, is the STOP. |
| **G5** | no **non-target load-bearing invariant** flips PASS → FAIL vs REF | I1–I14 per leg-year against REF's **14/14 PASS**. Any new FAIL outside the target mechanism kills the arm; a FAIL *caused by* the target mechanism is reported with its cause named and **declared in `invariant-failures.json` in the registration commit**. |
| **G6** | no unserved energy appears where REF has none | REF has **zero** unserved in all five years, so this binds strictly: `unserved_mwh` must be 0.0 in every solved leg-year of `CES-*`, `VOL-*` and `CAP-STATE-TIGHT`. It binds **more weakly** on `ALL-CLEAN`, which raises load by construction: there a non-zero value is reported with the load half named, not a STOP. |
| **G7** | voluntary dual bounded, **per arm** | where the row binds: dual > 0 and **≤ that arm's own ceiling** — **$4.50/MWh on `VOL-MID`**, **$7.00/MWh on `VOL-HI` / `CES-P20+VOL-HI` / `ALL-CLEAN`**; where it escapes: dual = that ceiling **exactly** and escape MWh = the shortfall. |
| **G8** | curtailment before thermal | **N/A ON NYISO, with its reason (§3.4)**: REF curtails 0.0 MWh of wind and solar in every year, so the ordering has no object. Replaced by its degenerate form: **Δcurtailment must be 0.0**; a non-zero value is a finding against the row. |
| **G9** | **both nettings** on `CES-P20+VOL-HI` and `ALL-CLEAN` | counts-toward as headline, additional beside it, the CES dual under each — never one alone (ruling S11). |
| **G10** | **`CAP-STATE-TIGHT` cap identity** | in every binding year `emissions_mt` = the §4.3 budget to **1e-6 relative** and `co2_cap_price_usd_per_t` > 0; in a slack year the dual is **0 exactly** and `n_co2_caps_binding` = 0. |
| **G11** | **one instrument at a time** | `carbon_price_path: zero` resolves to the STATE program only (never a federal price), and under the case the row **replaces** the adder: `resolve_carbon_program` returns a `cap_spec` with `price_adder is None`, and `resolve_carbon_price` = **0.0000** in all five years. **Already PASS, pre-solve (§4.3).** |
| **G12** | **cap footprint + the price-vs-quantity report** | the case moves fossil rows and imports only, and its endogenous dual is reported **beside** REF's exogenous adder in the same year ($23.6363 → $30.9824/t). |
| **G13** | **rematerialization identity** (§8) | the re-run `REF` and `LOAD-HI` bundles reproduce their committed `full_horizon_summary.json` trajectories **exactly** (CO2 and price to the published digits; `generation_by_fuel_mwh` to 1e-6 relative). **A miss is a STOP** — it would mean the pin is not reproducible, which outranks every other result in this lane. |

A gate **may kill an arm; it may never promote one**, and no gate reads a target residual.

---

## 8. Execution plan — and the one declared deviation, with its gate

**Driver** — `run_ces_leg.py`, the driver the load and resolve lanes both used (0 lines changed
between `1cc45bb2` and the pin), at THE PIN, one leg per invocation, years sequential:

```
H0=bdfb3095e9fa0cd2bec3f4e843f320b42588c72b   # or a DOC-ONLY descendant, zero solve-path diff
[ "$(git rev-parse HEAD)" = "$H0" ] || exit 90
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  uv run python scripts/run_ces_leg.py \
    --config configs/scenarios/nyiso_scenario_base_2026_2030.yaml \
    --matrix configs/scenario_campaign_matrix.yaml \
    --case <CASE> --campaign scn-campaign-policy-2026-09-06 \
    --out-dir results/scn-campaign-policy-2026-09-06/NYISO/<CASE>
```

The branch is cut **from THE PIN** and carries only documentation and campaign artifacts on
top of it, so `HEAD` is either the pin itself or a **doc-only descendant with a zero
solve-path diff** — the load ADDENDUM §5 convention RESOLVE ran under, stated here so the
`git.sha` recorded in each `run_config.json` is readable. `git fetch` + rebase happen **between
legs, never during one**. Logs go to the session scratchpad, never the results tree, so this
lane adds no `.gitignore` stanza.

**THE ONE DECLARED DEVIATION — `REF` and `LOAD-HI` are REMATERIALIZED, not re-answered.**
Charter P2 says *"Never re-solve REF"*, and the answer is never re-derived: §2 reuses the
committed key and §6.1 reuses the committed numbers. But `report_scenario_deltas.py` reads each
case's **cached bundle** (`results/NYISO/<key>/`), not its slim summary, and this container's
`results/NYISO/` holds **0 entries** — so without REF's bundle the charter's own deliverable
("`report_scenario_deltas.py` per case vs REF with `import_co2_mt_reported` beside
`emissions_mt` in every table") cannot be produced at all, and the leakage duty, the by-fuel
and by-zone tables and the curtailment table would all be silently dropped. I therefore run
`REF` and `LOAD-HI` as bundle-rematerialization legs at their **own committed keys**, under
gate **G13**: they must reproduce the committed trajectories exactly, and a miss is a STOP
reported as the lane's headline. `LOAD-HI` is included because it **is** `CARB-MID+LOAD-HI`
(§4.2), so rematerializing it is what lets a killed case still be *reported* with its full
delta set and its import line rather than merely dismissed. **Neither is registered** — both
ids already exist under `scn-campaign-load-2026-09-06`, and a second registration of the same
config would be a duplicate, not a run. This is declared here, before the fact, and routed to
SCN-DESK (§9 item 1) as a charter defect the other four program-ISO lanes will also hit.

**Cache isolation.** All nine case keys (§2) are new — no NYISO bundle has ever occupied them —
and `results/NYISO/` is gitignored and **empty** in this container, so no stale bundle is
reachable and the two rematerializations write into keys nothing else uses.

**Registration.** Kind `scenario`, campaign `scn-campaign-policy-2026-09-06`, one run id per
(ISO, case) — `nyiso-2026-2030-scn-campaign-policy-2026-09-06-<case>` — with **every invariant
FAIL declared in `frontend/data/hindcast/invariant-failures.json` in the same commit** (the
Y-24 ratchet at the registration seam; the audit is EXIT 0 on SCN today and stays so). One
commit per case.

**Budget.** 9 solve legs + 2 rematerializations × 5 solve-years = **55 solve-years**. NYISO
measured **3.3–4.1 min/solve-year** on the re-solved legs (REF 1,097 s, LOAD-HI 1,197 s,
LOAD-HI-ORGANIC 1,211 s total) ⇒ **≈18–21 min/leg, ≈3.5 h of LP total**, peak RSS **3.5–3.9 GB**
on a 15 GB box. Well inside §2.1b (every invocation is 5 solve-years).

**THE FIRST SOLVE IS HELD ON RULE 12 / precondition P4** until the owner names the slot.
Nothing is solved before that.

## 9. Routed to SCN-DESK — not executed, outside this lane's regions

1. **The charter's deliverable and its "never re-solve REF" clause collide in a fresh
   container.** `report_scenario_deltas.py` reads bundles; a policy lane inherits only slim
   artifacts; `results/<ISO>/` is gitignored. Every one of the five program-ISO policy lanes
   will hit this. Handled here by the §8 rematerialization under gate G13 and declared, but the
   charter should say which of the two it wants — or WS-0 should teach the report to fall back
   to the committed summary for the reference case.
2. **NYISO is the counter-example that D-3c has been missing.** ERCOT's §9 item 4 recorded that
   `VOL-MID` can never be live there under all-eligible crediting. NYISO shows the opposite
   failure mode of the *same* convention: an ISO that is 39 % clean has its voluntary row bind
   at V/G = 1.4–3.4× its whole eligible fleet, because hydro and nuclear carry its clean share and
   neither is eligible. The card now has both tails, and they argue for different fixes.
3. **SCN-CAP's re-check prediction landed, and bigger than it expected.** Its §3 named
   NYISO-2030 (+0.69 Mt) as the margin a re-solved REF could cross; **three years crossed**.
   Worth carrying to D-1(c) alongside the PJM regional-RGGI fallthrough, because it says the
   S12 slope's back half is not binding on a post-D77 fleet.
4. **The campaign YAML's voluntary and cap comment blocks are stale post-S9/S10/S12** in the
   same words-only way ERCOT's §9 item 3 recorded for the tail-regime block — e.g. the
   voluntary block still narrates the S5 hold. Prose only; joins the same cheap sweep.

## 10. Duties

- **No default moved, no knob moved, no `ScenarioConfig` field added, no solve yet.** DOF
  ledger: **zero** free parameters. No `authorized_price_tuning` (a backcast offer-curve
  channel; untouched).
- **Consumed, never edited:** `configs/scenario_campaign_matrix.yaml`, the NYISO base YAML,
  everything under `src/`, `scripts/run_ces_leg.py`, `scripts/report_scenario_deltas.py`,
  `scripts/collate_scenario_campaign.py`, `scripts/register_forecast_run.py`, every committed
  bundle and sidecar. `program-status.json`, `ff-verdicts.json` and the whole **backcast**
  namespace: untouched (§7.5 — this lane registers into the forecast namespace only).
- **Written by this lane:** `docs/handoffs/PRECOMMIT-…`/`FINDING-scn-ws5a-policy-nyiso-*.md`,
  `docs/handoffs/scn-ws5a-policy-nyiso/` (the phase-0 instrument + its JSON),
  `results/scn-campaign-policy-2026-09-06/NYISO/**` (slim only),
  `frontend/data/hindcast/nyiso-…-scn-campaign-policy-…json` + the forecast namespace files the
  registration writes, `frontend/data/hindcast/invariant-failures.json` (append only),
  the plan §5.1 / ledger §3 rows for NYISO, and **NYISO's matrix shard only**.
- **Rule 29(c):** this lane produces no screen bundle and no control bundle — its legs are
  registered campaign arms, and the control is a committed one.
- **Rule 27:** no existing source file ≥300 lines is rewritten; every push touching one is
  verified by fetch-back.
- **Backcast byte-identity:** untouched by construction (forecast-mode only, `mode="forecast"`
  on every leg).
