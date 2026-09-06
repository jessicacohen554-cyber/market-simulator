# PRECOMMIT — SCN-WS5A-POLICY-NEISO: the Stage A-POLICY case set, phase 0 at THE PIN

**Lane** SCN-WS5A-POLICY-NEISO · **Model** Opus (`claude-opus-5`, rule 27 `[R-PUSH]`) ·
**Date** 2026-09-06 · **Branch** `claude/scn-ws5a-policy-neiso-bhlkdp` · **Data profile**
`neiso` (full clone — `hydrate_data.py --profile neiso` reports every blob already local) ·
**Campaign** `scn-campaign-policy-2026-09-06`, kind `scenario`, `reference_case: REF` ·
**Charter** SCN-DESK ledger §5 policy charter **v6** (r#17) · **Predecessors**
`PRECOMMIT-scn-ws5a-resolve-2026-09-06.md` (THE PIN, the inherited G-DRIFT),
`FINDING-scn-ws5a-load-neiso-2026-09-06.md` (the pre-D77 REF this ISO was first read on) and
`PRECOMMIT-scn-ws5a-policy-ercot-2026-09-06.md` (the first policy lane's phase 0, the template).

**Pushed before the first solve** (rule 29 `[R-SCREEN]`). Every number below is zero-LP: a
resolved config at THE PIN, a committed artifact, or arithmetic on the two. Nothing here is
revised after a solve; §6's predictions are scored as written, misses at full magnitude.

---

## 0. THE PIN

```
bdfb3095e9fa0cd2bec3f4e843f320b42588c72b
```

Named by `PRECOMMIT-scn-ws5a-resolve-2026-09-06.md` §0 (precondition P1). Verified here:
`git merge-base --is-ancestor bdfb3095 origin/main` → **yes**; `origin/main` is **170 commits**
past it at PRECOMMIT time (`bbeb25fe`). **THE PIN IS NOT MOVED AFTER THE FIRST SOLVE.** Anything
on `main` after it is recorded as post-pin, never retro-fitted and never used to re-read a
result. My keys are therefore **pre-fingerprint keys** (capx D79 entered `cache_key()` after the
pin); the pin records them and §2 lists them.

## 0.1 Bottom line before any LP

1. **FOUR of thirteen chartered cases are killed at phase 0 on a proven LP-input identity, and
   one the charter told me to kill SURVIVES on a proven NON-identity.** Killed: `CARB-LO`,
   `CARB-MID`, `CARB-HI` (each differs from REF in exactly one field, `carbon_price_path`, whose
   only LP-affecting consumer resolves **identically to REF in all five years** under the S2
   floor — §4.1) and **`CARB-MID+LOAD-HI`, which is LP-identical to the COMMITTED `LOAD-HI` leg**
   at key `0d5c394b6c4e5cb6`, for the same reason (§4.2). **Nine legs, 45 solve-years, survive.**
2. **`CAP-STATE-TIGHT` IS NOT BYTE-IDENTICAL TO REF ON NEISO, AND MUST BE SOLVED.** The charter's
   phase-0 rule for case 13 — *"where the budget exceeds REF's CO2 in every year the row is
   slack, the case is byte-identical to REF and is KILLED"* — and `FINDING-scn-cap-2026-09-06.md`
   §3's NEISO verdict (*"under the case the LP is byte-identical to REF on NEISO … so the charter
   says do not solve it"*) both rest on a premise the code refutes: under the case the mass-cap
   row **REPLACES** the RGGI adder (the resolver's one-source invariant), so NEISO's resolved
   exogenous carbon price goes **$26.05 → $0.00/t in 2026 and $34.15 → $0.00/t in 2030** whether
   or not the row binds. That is a resolved-INPUT delta, which is what phase 0 measures, and the
   charter's own gate **G11** states the replace semantics that make it one. The slack test is
   additionally not evaluable pre-solve, because REF's CO2 was produced *under the carbon price
   the case removes* (§4.3). Killing it here would publish a false identity; it solves.
3. **NEISO's REF is CLEAN, so this lane's price side is campaign-grade** — unlike ERCOT's. 14/14
   invariants PASS, `unserved_mwh` **0.0 in every year**, reserve margin +0.168 → +0.084 all
   in-band, `hours_ge_500` = 0. Gate **G2** asserts that rather than discovering it (§7).
4. **NEISO's VRE runs at exactly its unconstrained CF ceiling — curtailment is 0.0000 TWh in
   every year — so charter gate G8 is VACUOUS on this ISO and is demoted to a reported
   measurement.** Derived zero-LP (`load_renewable_profiles` at the pin: wind 3.6642 + solar
   3.2520 = **6.9162 TWh**, identical to the committed REF's dispatched wind+solar to 4 dp) and
   independently confirmed by the committed delta report (`curtailed_mwh` ≤ 1.9e-9 in all ten
   REF/LOAD-HI leg-years). Consequence, pre-registered as **P-5**: in the first binding year the
   voluntary row has **no within-year response available at all**, so its escape must absorb the
   entire deficit and 2026 dispatch must be bit-identical to REF's.
5. **`VOL-MID` and `VOL-HI` resolve to the IDENTICAL volume on NEISO** — `V` = 8.4289 → 8.6828
   TWh in both — because `E_DC` is **exactly 0** (`DATACENTER_ADDITIONS_MW["NEISO"] == {}`), so
   `f_commit` (the only term that separates the two paths) multiplies zero, and `s_base` is 0.08
   in both. The pair is therefore a **pure WTP-ceiling experiment**, $4.5 vs $7.0/MWh, with every
   other input equal. ERCOT killed `VOL-MID` on slack; NEISO cannot, and gets a cleaner
   instrument than the charter anticipated.
6. **The voluntary row BINDS on NEISO in 2026–2028 and is slack in 2029–2030** (V 8.43/8.49/8.55
   vs eligible 6.92 TWh; then 8.62/8.68 vs 10.15/12.05) — the opposite ordering to ERCOT's, whose
   row binds only from 2028 (§3.2).
7. **The charter's G7 ceiling literal is corrected here as it was on ERCOT, and it binds
   differently**: `VOL-MID` survives on NEISO, so **both** committed cells are live —
   **$4.5/MWh on `VOL-MID`, $7.0/MWh on `VOL-HI` / `CES-P20+VOL-HI` / `ALL-CLEAN`** (§3.3).
8. **One structural asymmetry is declared before the cap solve rather than discovered in it:**
   the mass-cap row's dual (`co2_cap_price`) is exported but **reaches no capacity screen** —
   `evolve_fleet` takes `carbon_price=resolve_carbon_price(config, driver_year)`, which is 0.0
   under the case. So the QUANTITY arm prices dispatch only, while the PRICE arm (REF's RGGI
   adder) prices dispatch **and** investment. Pre-registered as **P-11**: `CAP-STATE-TIGHT`
   carries **0.0 MW of `gas_cc_ccs` in every year**, because at carbon 0 the repaired retrofit
   screen closes (capx D50's measured asymmetry, owner Q42).

---

## 1. Preconditions — verified, as a verdict table

| # | requirement | verdict | evidence |
|---|---|---|---|
| **P1** | RESOLVE's PRECOMMIT names the pin; NEISO's re-solved REF on main with G1 PASS | **MET** | `1b95d430` (#5214) §0 names `bdfb3095`; legs 1–2 (`61b9cce5`, `931866cc`, #5221) re-solved NEISO REF + LOAD-HI at it. G1 re-read here from the artifact: REF 2028 carries 22.5554 TWh of `gas_cc_ccs` against a total 9.8722 Mt — i.e. the converted class is no longer at its uncaptured host rate (pre-fix the same 2028 read 15.856 Mt on 1.72 TWh of CCS). |
| **P2** | NEISO's REF leg at the pin, at the **`-r2`** path | **MET** | `results/scn-campaign-load-2026-09-06-**r2**/NEISO/REF/`, key `8878d29743555b45`, 5/5 years, sidecar `frontend/data/hindcast/neiso-2026-2030-scn-campaign-load-2026-09-06-ref.json` (`meta.cache_key` = the same key). **My own resolve chain reproduces `8878d29743555b45` for REF and `0d5c394b6c4e5cb6` for LOAD-HI exactly** (§2), which is the chain validation. REF is **never re-solved**. |
| **P3** | the carbon form is the committed RFF path ladder | **MET at the pin** | `configs/scenario_campaign_matrix.yaml` at `bdfb3095`: `CARB-LO/MID/HI` → `carbon_price_path: low/mid/high`; `ALL-CLEAN` → `carbon_price_path: mid`. Resolved values in §4.1. |
| **P4** | rule 12 / ruling S14 concurrency | **NOT ESTABLISHED — first solve HELD, and the charter's own clause is why** | I cannot see another lane's process. What `main` shows at `bbeb25fe`: RESOLVE's CAISO and MISO legs are **outstanding** (`-r2` carries NEISO/NYISO/PJM only) with both PRECOMMITs pushed and 0 legs each, so up to two SCN solves may be live; and the **capx track is visibly mid-solve** — D65-B-R at leg 7 (`cd8b4411`) and D76 phase 3 on **NEISO + NYISO** (`5259d519`). The charter: *"if you cannot establish what else is solving, hold and ask rather than assume the slot is free."* Held; asked. See §8. |
| **P5** | `mass_cap_tons_by_year` + `CAP-STATE-TIGHT` exist | **MET, and IN SCOPE for NEISO — but not with the verdict the charter predicts** | Both live at the pin; the schedule names NEISO {2026: 20.67, 2030: 18.0, 2040: 11.4, 2050: 4.1} Mt and resolves 20.670 / 20.003 / 19.335 / 18.668 / 18.000 Mt across the window (§4.3). The case is **solved**, per §0.1 item 2. |

### 1.1 The constant families this lane consumes (desk standing change #1)

All read at **THE PIN** `bdfb3095`, verbatim:

| family | module | value at the pin |
|---|---|---|
| `CARBON_PRICE_PATHS` | `config/constants.py` (via `policy/carbon.py`) | `zero` {2026:0, 2030:0, 2040:0, 2050:0}; `low` {0, 8, 18, 25}; `mid` {0, 15, 35, 50}; `high` {0, 30, 70, 110} |
| `STATE_CARBON_PRICE_BY_ISO` | `policy/carbon.py` | keys `CAISO`, `NYISO`, **`NEISO` (RGGI)** — the measured 2023–2025 series; forward years take the **projected** program price |
| `CAP_AND_TRADE_PROGRAMS` | `policy/cap_and_trade.py` | `CAISO`, `NYISO`, **`NEISO`**, `PJM` |
| `VOLUNTARY_BASELINE_SHARE` | `config/constants.py` | low {2023: 0.06}; **mid {2023: 0.08}; high {2023: 0.08}** — *identical at mid and high* |
| `VOLUNTARY_COMMITTED_DC_FRACTION` | `config/constants.py` | low {2026: 0.0}; mid {2026: 0.5}; high {2026: 1.0} — **inert on NEISO, `E_DC` = 0** |
| `VOLUNTARY_WTP_CEILING_USD_PER_MWH` | `config/constants.py` | low 2.0; **mid 4.5**; **high 7.0** — both live cells on this ISO |
| `VOLUNTARY_BASELINE_ISO_WEIGHT["NEISO"]` | `config/constants.py` | `None` (needs-intake) ⇒ `w_ISO` = **1.0** |
| `VOLUNTARY_ELIGIBLE_FUELS_DEFAULT` | `config/constants.py` | `(wind, solar, offshore_wind, geothermal)` — ruling S10 as built. NEISO's fleet carries **wind + solar only** in every committed leg-year |
| `DATACENTER_ADDITIONS_MW["NEISO"]` | `config/constants.py` | **`{}`** — measured through the runner's own chain as `E_DC` = 0.0000 TWh in all five years |
| CES levels | `configs/scenario_campaign_matrix.yaml` | premium {10, 20, 30} $/MWh; target {2026: 0.55, 2035: 0.80, 2050: 1.00}; ACP $50/MWh |
| `federal_ces_*` crediting | resolved config | `clean_capture`; eligible = nuclear/wind/solar/hydro/geothermal/offshore_wind/**gas_cc_ccs**/hydrogen_ct/hydrogen_ccgt; `gas_cc_ccs` at **0.95**, every other eligible fuel at 1.0 |
| `QUEUE_CAP_GW["NEISO"]` / `QUEUE_CAP_PER_TECH_GW["NEISO"]` | `config/constants.py` | **4 GW/yr** total; wind 1.0, solar 2.0, **offshore_wind 2.0**, gas_cc 1.0, gas_ct 0.5, nuclear 0.5, geothermal 0.0 |
| NEISO import tranches / EFs | `model/interchange/spec.py`, `results/emissions.py` | `Highgate` 225 MW and `HQ_PhaseII` 1,830 MW at **EF 0** (firm hydro); `NB_north` 630, `NYISO_CT_base` 870, `NYISO_CT_peak` 870, `import_scarcity` 95 MW at `CARB_UNSPECIFIED_IMPORT_EF` = **0.428 t/MWh** |

---

## 2. The case set at THE PIN — resolved fields and cache keys

Resolved exactly as `runner.run_scenario_iso` does: `matrix_configs(base, sweep)` →
`resolve_policy_bundle` → `set_caiso_fsno_partition(False)` → `apply_iso_scenario_defaults`,
then `config.cache_key()`. Base: `configs/scenarios/neiso_scenario_base_2026_2030.yaml`.

**Chain validation — the two NEISO rows RESOLVE published, reproduced independently:**
`REF` `8878d29743555b45` and `LOAD-HI` `0d5c394b6c4e5cb6`, identical to
`PRECOMMIT-scn-ws5a-resolve` §3's NEISO lines **and** to the two committed
`full_horizon_summary.json` `cache_key` fields. The resolve chain used below is therefore the one
the solve will use, not a naive `cache_key()`.

| case | key at THE PIN | resolved-field delta vs REF | verdict |
|---|---|---|---|
| *REF (control, not solved)* | `8878d29743555b45` | — | **reused, committed at the `-r2` path** |
| `CARB-LO` | `89059734b9b32165` | `carbon_price_path: zero → low` | **KILLED — §4.2** |
| `CARB-MID` | `ee3f6db1f77352fd` | `carbon_price_path: zero → mid` | **KILLED — §4.2** |
| `CARB-HI` | `2b15ede95d461f6c` | `carbon_price_path: zero → high` | **KILLED — §4.2** |
| `CES-P10` | `4e5f93124767a5f4` | `federal_ces_enabled`, premium 10.0 | **SOLVE** |
| `CES-P20` | `8c5ab5fb0e2d9c8c` | premium 20.0 | **SOLVE** |
| `CES-P30` | `42328a83592ebfbb` | premium 30.0 | **SOLVE** |
| `CES-T80` | `ce37aefe169bb82b` | target {2026:0.55, 2035:0.80, 2050:1.00}, ACP 50.0 | **SOLVE** |
| `CARB-MID+LOAD-HI` | `7bbc4a70b0720cae` | vs **LOAD-HI**: `carbon_price_path: zero → mid`, and nothing else | **KILLED — §4.2** |
| `VOL-MID` | `f20b1a621b8d263a` | `voluntary_clean_demand_path: off → mid` | **SOLVE** |
| `VOL-HI` | `db27e8964840a36a` | `voluntary_clean_demand_path: off → high` | **SOLVE** |
| `CES-P20+VOL-HI` | `05e4e158385d3935` | premium 20.0 + voluntary high | **SOLVE** |
| `ALL-CLEAN` | `cbb53bd42bba88a6` | carbon mid + growth high + DC high + CES target + ACP 50 + voluntary high | **SOLVE** |
| `CAP-STATE-TIGHT` | `89264f98832068de` | `mass_cap_enabled` True, `mass_cap_program` co2, `mass_cap_tons_by_year` set | **SOLVE — §4.3** |

**Every case keys distinctly, and all nine solve keys are NEW**: `git grep` over every committed
`*.json` on `origin/main` returns **0 hits** for each of the nine, and `results/NEISO/` holds
**0 cache entries** in this container (gitignored, cloned fresh). No leg can collide with another,
with a pre-fix bundle, or with a warm cache.

**9 legs to solve, 45 solve-years.**

---

## 3. Phase 0 — the voluntary row, per year, from the run's own demand

`V(ISO, y) = s_base·w_ISO·E_nonDC + f_commit·E_DC`, computed by calling
`policy.voluntary_demand.resolve_voluntary_volume` on the demand the LP is handed —
`load_demand` → `runner._scale_demand` → `data.datacenter.add_load_layers`, the runner's own
chain — not by re-deriving the memo's arithmetic. Zone list: `['North', 'Central', 'Boston',
'Connecticut', 'HQ_import']`, the static NEISO topology `runner.py:1458` passes.

### 3.1 The resolved volumes (TWh)

| case | | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|---|
| REF / all non-VOL, non-LOAD-HI | `E_total` | 105.3618 | 106.1463 | 106.9367 | 107.7329 | 108.5351 |
| | `E_DC` | **0.0000** | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| **`VOL-MID`** | **V** | **8.4289** | **8.4917** | **8.5549** | **8.6186** | **8.6828** |
| **`VOL-HI`, `CES-P20+VOL-HI`** | **V** | **8.4289** | **8.4917** | **8.5549** | **8.6186** | **8.6828** |
| `ALL-CLEAN` (growth high, DC high) | `E_total` | 106.4428 | 107.7841 | 109.1422 | 110.5175 | 111.9102 |
| | `E_DC` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| | **V** | 8.5154 | 8.6227 | 8.7314 | 8.8414 | 8.9528 |

**`VOL-MID` and `VOL-HI` carry the SAME volume, to the MWh.** `s_base` = 0.0800 and `w_ISO` = 1.0
on both paths; the only term that separates them, `f_commit` (0.5 vs 1.0), multiplies an `E_DC`
that is exactly zero because `DATACENTER_ADDITIONS_MW["NEISO"]` is `{}`. The pair is a **pure WTP
ceiling ladder** and nothing else — the cleanest form of the instrument the memo describes, and
one the charter did not anticipate any ISO producing.

### 3.2 The regime test (memo Addendum A.3 / WS-3b §6) — the row BINDS EARLY and goes slack

Eligible generation `G` = wind + solar **as dispatched in the paired baseline** (NEISO carries no
`offshore_wind` or `geothermal` row in any committed leg-year; the fuel keys present are exactly
`biomass, coal, gas_cc, gas_cc_ccs, gas_ct, gas_st, hydro, import, nuclear, oil, solar, wind`).
`G_REF` and `G_LOAD-HI` from the `-r2` summaries — **identical to each other in every year**,
because VRE is at its CF ceiling in both.

| baseline `G` (TWh) | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| `G_REF` = `G_LOAD-HI` | 6.9162 | 6.9162 | 6.9162 | 10.1517 | 12.0494 |

| arm | 2026 | 2027 | 2028 | 2029 | 2030 | regime |
|---|---|---|---|---|---|---|
| **`VOL-MID`** vs `G_REF` | **8.43 > 6.92 (−1.5127)** | **8.49 > 6.92 (−1.5755)** | **8.55 > 6.92 (−1.6387)** | 8.62 < 10.15 (+1.5331) | 8.68 < 12.05 (+3.3666) | **binds 2026–28**, slack 2029–30 |
| **`VOL-HI`** vs `G_REF` | identical V to `VOL-MID` | | | | | **binds 2026–28**, slack 2029–30 |
| **`CES-P20+VOL-HI`** | identical V to `VOL-HI` | | | | | **binds 2026–28**, slack 2029–30 |
| **`ALL-CLEAN`** vs `G_LOAD-HI` | **8.52 > 6.92 (−1.5992)** | **8.62 > 6.92 (−1.7065)** | **8.73 > 6.92 (−1.8152)** | 8.84 < 10.15 (+1.3103) | 8.95 < 12.05 (+3.0966) | **binds 2026–28**, slack 2029–30 |

**No voluntary arm is killed on NEISO.** Every one binds in three of five years, so rule 29's
inert-year clause applies to 2029–2030 within each arm, not to the arm. The regime is the mirror
image of ERCOT's (slack early, binding late) and the reason is structural, not scale: NEISO's
eligible fleet is 4.1 GW against a 105 TWh load, and the row's 8 % of non-DC load is a bigger
number than the ISO's entire wind + solar output until the 2029 planned additions land.

**The deficit has NO within-year closure** (§0.1 item 4): eligible generation is already at its
hourly CF ceiling, `offshore_wind`/`geothermal` capacity is zero, and capacity entry is a
between-year screen under one-pass evolution (rule 10 `[R-ONE-PASS]`). So in the first binding
year the escape column must absorb the deficit exactly. That is prediction **P-5**.

### 3.3 The WTP ceiling — the charter literal, corrected, and BOTH cells live

`voluntary_wtp_ceiling_usd_per_mwh` ships `None`, so the resolver takes
`VOLUNTARY_WTP_CEILING_USD_PER_MWH[path]`. The charter's G7 names **$4.5/MWh** — the **mid** cell.
On ERCOT that correction meant "every surviving leg is `high`, so read $7.0". **On NEISO both
cells are live**, because `VOL-MID` survives here:

| arm | path | ceiling, measured from the resolved config |
|---|---|---|
| `VOL-MID` | mid | **$4.50/MWh** |
| `VOL-HI`, `CES-P20+VOL-HI`, `ALL-CLEAN` | high | **$7.00/MWh** |

G7 is bounded **per arm** (§7). Ruling S9's committed level is untouched.

---

## 4. Phase 0 — the carbon axis and the cap row

### 4.1 Resolved carbon $/tCO2 per year (`policy.carbon.resolve_carbon_price`)

| case | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| `REF` (RGGI adder, projected) | 26.0545 | 27.8783 | 29.8298 | 31.9179 | 34.1521 |
| `CARB-LO` | **26.0545** | **27.8783** | **29.8298** | **31.9179** | **34.1521** |
| `CARB-MID` | **26.0545** | **27.8783** | **29.8298** | **31.9179** | **34.1521** |
| `CARB-HI` | **26.0545** | **27.8783** | **29.8298** | **31.9179** | **34.1521** |
| `CARB-MID+LOAD-HI` | **26.0545** | **27.8783** | **29.8298** | **31.9179** | **34.1521** |
| every CES-only / VOL-only case, and `ALL-CLEAN` | 26.0545 | 27.8783 | 29.8298 | 31.9179 | 34.1521 |
| **`CAP-STATE-TIGHT`** | **0.0000** | **0.0000** | **0.0000** | **0.0000** | **0.0000** |

The RFF path operand for the same rows, for the record: `low` 0/2/4/6/8, `mid` 0/3.75/7.5/11.25/15,
`high` 0/7.5/15/22.5/30. **The RGGI trajectory dominates every registered path in every year of
the window** — the closest approach is `CARB-HI` at 2030, $30.00 against $34.15 — so
`max(program, path)` returns the program operand throughout. This reproduces
`FINDING-scn-ws1b-2026-09-06.md`'s "EXACTLY INERT on CAISO/NYISO/NEISO under the S2 floor" from
this lane's own resolve, at this lane's own pin, on the campaign base config. **That is gate G1
on the carbon axis, passed before any LP.**

### 4.2 The four carbon kills — the identity, argued rather than asserted

A field-level diff of every resolved case config (`dataclasses.fields`, `repr` comparison) shows
`CARB-LO/MID/HI` differ from `REF` in **exactly one field**, `carbon_price_path`, and
`CARB-MID+LOAD-HI` differs from `LOAD-HI` in **exactly one field**, the same one. A repo-wide
grep of `carbon_price_path` at the pin finds its consumers to be: `policy/carbon.py`'s
`resolved_base_trajectory_price` (the `max` at `:187`), the same module's `rff_path_price` and the
`carbon_path_below_program_warning` **guard** (which only logs), plus docstrings, a
`scenario_resolvers.py` policy-bundle preset (not reached — the campaign sets the field directly),
and `results/cache.py` epoch prose. **There is no other LP-affecting consumer.** Since the value
that consumer returns is identical to REF's in all five years (§4.1), the LP inputs of all four
cases are identical to their baseline's, and their dispatch, emissions, prices, duals and fleet
evolution must be too. The keys move (`89059734…` ≠ `8878d297…`) because the *field* differs; the
answer cannot. This is the same "key moves, answer cannot" class ERCOT recorded for its own REF
across the pin.

**Why `CARB-MID+LOAD-HI` is killed against `LOAD-HI` and not against `REF`.** Its LOAD-HI leg is
live — the charter names LOAD-HI as its pairing base for exactly that reason — and that leg is
already **committed at the pin** (`results/scn-campaign-load-2026-09-06-r2/NEISO/LOAD-HI/`, key
`0d5c394b6c4e5cb6`, reproduced by my own resolve chain). So the arm's answer already exists on
`main`, and its delta vs REF is precisely the LOAD-HI delta the load lane published
(`FINDING-scn-ws5a-load-neiso` §4): ΔCO2 +0.444 / +0.644 / +0.801 / +0.482 / +0.251 Mt on the
post-D77 pair. **The carbon leg of the campaign's one combined carbon+load case contributes
exactly nothing on NEISO**, and the §2 table reports that as the result rather than spending 5
solve-years to rediscover it.

### 4.3 `CAP-STATE-TIGHT` — why the charter's kill test does not apply, and what the case actually is

**The resolved budget** (`scheduled_power_sector_budget`, linear between the S12 knots):

| | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| NEISO budget (Mt CO2) | 20.670 | 20.003 | 19.335 | 18.668 | 18.000 |
| REF CO2 (Mt, **post-D77**, `-r2`) | 15.832 | 17.096 | 9.872 | 4.757 | 6.106 |
| naive margin (budget − REF) | +4.84 | +2.91 | +9.46 | +13.91 | +11.89 |

The naive margin is the test `FINDING-scn-cap-2026-09-06.md` §3 applied (on the pre-D77 REF; the
post-D77 REF widens it further), concluding "slack in all five, byte-identical, KILL". **Two
things are wrong with that conclusion, and both are code facts, not judgements:**

1. **The row REPLACES the adder, so the inputs differ whether or not the row binds.**
   `resolve_carbon_program` returns a `CarbonProgramResolution` carrying **exactly one** of
   `price_adder` / `cap_spec` (its `__post_init__` invariant). With `mass_cap_enabled` and a
   schedule naming NEISO, `_power_sector_cap` returns a spec in **every** year of the window, so
   the resolution takes the row path and `price_adder` is `None`. `resolved_base_trajectory_price`
   then reads `float(resolution.price_adder or 0.0)` — its documented ROW-PATH guard — and returns
   `max(0.0, rff_path_price("zero", y))` = **0.0**. Measured, not inferred: §4.1's last row. The
   case therefore removes a **$26.05 → $34.15/t** carbon signal from `data/fleet.py::assemble_mc`'s
   `carbon_mc_column` and from `evolve_fleet`'s screen, and installs an LP row in its place.
   The charter's own **G11** states this ("the row REPLACES the adder where active"); it is
   §3's kill sentence that contradicts it.
2. **The slack test is not evaluable pre-solve, because it compares the case's budget against
   emissions produced under the price the case removes.** REF's 2028–2030 CO2 is low precisely
   *because* the RGGI adder drove 22.6 / 36.3 / 25.9 TWh of `gas_cc_ccs` retrofits. Under the
   case that adder is 0, and at carbon 0 the repaired retrofit screen closes (capx D50, owner
   Q42 — *"at carbon 0 the repair closes the screen … and under RGGI it does not (NEISO 12.79 →
   12.38 GW)"*, the asymmetry measured on NEISO itself). So the case's own emissions are much
   more likely to resemble REF's **2027** level (17.10 Mt, the last pre-retrofit year) than its
   2030 level, against a 2030 budget of **18.000 Mt**. Whether the row binds is a solve result.

**Verdict: SOLVE.** A case is killed at phase 0 only on a *proven* identity (§4.2 is what one
looks like). This one is a proven **non**-identity. Gates **G10–G12** are live on NEISO and are
stated in §7; §9 routes the correction to SCN-DESK and to the SCN-CAP record.

---

## 5. G-DRIFT (rule 29(b)) — the control is the committed REF, and no control solve is earned

### 5.1 `1cc45bb2 .. bdfb3095` — inherited, and its NEISO premise is the OBJECT of the lane, not a confound

RESOLVE's §1 classified 34 non-merge solve-path commits: **4 LIVE** (capx D77, D65-B ISO-wide;
D67-ARM, D81 **PJM only**) and 30 INERT with a stated reason. For **NEISO**:

- **D77 / D65-B are LIVE and already spent.** They are why NEISO's REF was re-solved, and the
  re-solved REF *is* my control. I difference against the post-fix leg, so the seam repair is
  inside both sides of every delta and cancels. It is not a confound here; it was the object of
  the lane before mine.
- **D67-ARM / D81 are PJM-scoped and INERT for NEISO.** Re-measured on this lane's own resolved
  configs, not inherited: `capacity_adequacy_requirement_published_by_iso` = **`None`**,
  `capacity_market_supply_clearing_by_iso` = **`None`**, `retirement_sector_gate` = **`False`**
  on every one of the thirteen NEISO case configs at the pin.

⇒ **Form 4 is VALID for NEISO.** The committed `REF` (key `8878d29743555b45`) and `LOAD-HI`
(`0d5c394b6c4e5cb6`) **are** the control, solved at THE PIN by RESOLVE legs 1–2. **No control
solve is spent, and REF is never re-solved** (charter P2).

### 5.2 `bdfb3095 .. origin/main` — for the record; I solve at THE PIN regardless

`git diff bdfb3095 origin/main` over the charter's window (`src/market_sim scripts/lib
scripts/run_full_horizon.py scripts/run_ces_leg.py scripts/check_forecast_invariants.py configs/
data/raw/_validation-source data/raw/reference`): **18 files, +1,812 / −59, across 8 non-merge
commits.** `scripts/run_ces_leg.py`: **0 lines changed**. All eight INERT for a NEISO forecast leg:

| commit | what | INERT because |
|---|---|---|
| `bf97317f` | capx D78-R2 step 0 — delete the producer-less `exempt_unit_ids` | D78's seam needs `retirement_sector_gate` **and** a clearing-armed ISO; NEISO has **neither** (both measured `False`/`None`, §5.1). |
| `16210868` | capx D79 phase 1 — the solve-surface fingerprint enters `cache_key()` | Key-only, and it moved zero keys at landing. My pin is pre-D79, so my keys are the pre-fingerprint keys §2 lists. |
| `beb74f0f` | pjm-167 F1 — backcast EIA-860 vintage tracks the solved year | New field `eia860_vintage_tracks_solve_year: bool = **False**`; and its branch is `config.mode == "backcast" or config.hindcast`, neither true on a forecast leg. |
| `cd96fa26` | pjm-167 F2 — a published transfer limit enforced only if its own flows respect it | New field `pjm_interface_feed_admissibility_gate: bool = **False**`; PJM-scoped and backcast-facing; absent from NEISO's `default_scenario_overrides` and from every campaign case. |
| `14ae4d76` | miso-231 — the HOURLY neighbour-anchored MISO/PJM seam ladder | Default off, MISO-scoped (`model/interchange/miso.py`); the NEISO tranche table in `spec.py` is **byte-unchanged** (`git diff … spec.py` returns no NEISO/HQ/Highgate/NB_north line). |
| `7ff10b64` | `ruff format` on the miso-231 files | AST-identical, formatting only. |
| `486c115f` | constants facade re-export of two D75-R capacity-market names | A re-export; no value and no behaviour. |
| `6164231e` | capx D75-R-ARM — `pjm_vre_accreditation_vintage` armed for PJM | The whole `iso_configs.py` hunk is inside `_pjm_config`'s `default_scenario_overrides` (verified line by line); the shared default stays `False`. |

**No LIVE hunk for NEISO on either window ⇒ no control solve is earned under clause (b).**

---

## 6. What each surviving leg is expected to do — pre-registered, from measured responses

Sources, all measured before this lane and none of them a residual: the committed post-D77 NEISO
REF (`-r2` summary + the regenerated delta report at `931866cc`), **WS-2b §3** (the CES premium
ladder's saturation mechanism), **WS-3b §6** (the voluntary row's arithmetic), **capx D50 / owner
Q42** (the retrofit screen's carbon-0 asymmetry) and the code paths named in §4.

**The REF column every prediction differences against** (committed, post-D77):

| REF | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| `emissions_mt` | 15.8319 | 17.0960 | 9.8722 | 4.7566 | 6.1058 |
| `import_co2_mt_reported` | 4.536035 | 4.376392 | 4.487150 | 4.369626 | 4.765739 |
| `lw_price` / `avg_price` ($/MWh) | 51.892 / 51.20 | 51.403 / 50.50 | 52.626 / 51.56 | 51.586 / 50.48 | 54.022 / 53.22 |
| `clean_share` | 0.3485 | 0.3458 | 0.5255 | 0.6588 | 0.5877 |
| `curtailment_twh` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `unserved_mwh` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `gas_cc_ccs` (TWh) | 0.0000 | 0.0000 | 22.5554 | 36.2850 | 25.9318 |
| wind / solar capacity (MW) | 1400 / 2700 | 1400 / 2700 | 1400 / 2700 | 2112.6 / 3789.4 | 2400 / 4700 |
| `builds_renew_mw` / `retire_mw` | 0 / 0 | 0 / 2758.3 | 0 / 0 | 1802.0 / 1.6 | 1198.0 / 0 |

**The import line is 26–92 % of the in-ISO level on this REF** (4.54/15.83 = 28.7 % in 2026,
4.37/4.76 = **91.9 %** in 2029) — materially larger than the charter's "25–41 %", which was the
**pre-D77** reading. The denominator collapsed; the numerator did not. Every table in the FINDING
carries the import line beside `emissions_mt` (the WS-0 leakage duty), and this ratio is the
reason it is not decorative on NEISO.

### 6.1 The sharpest predictions — identities, not bands

**P-1 (the 2026 identity).** In **every** surviving arm except `CAP-STATE-TIGHT`, **2026 is
bit-identical to REF's 2026**: `emissions_mt` **15.8319**, `lw_price` **51.892**,
`import_co2_mt_reported` **4.536035**, `clean_share` **0.3485**, and `generation_by_fuel_mwh`
equal to 1e-6 in every fuel. *The argument, so a miss is diagnostic rather than a surprise:*
(a) the **CES premium** reaches only `capacity_evolution/new_entry.py::effective_eac_price_for_tech`
— grep at the pin finds no other consumer — so it is a screen input and never a marginal cost;
(b) the **CES target row** and the **voluntary row** are LP rows, but every resource they credit
is already at a bound in REF's 2026 optimum (VRE at its hourly CF ceiling, §0.1 item 4; nuclear
and hydro flat at 26.4822 / 6.9735 TWh across all five years; `gas_cc_ccs` zero before 2028), so
neither row can raise credited generation and both go straight to their escape column, whose cost
is a constant added to the objective and couples to nothing; (c) the escape's shadow price
therefore lands on eligible fuels' **reduced costs**, which their bound duals absorb, leaving the
energy-balance duals — and so `lw_price` — unmoved. **The first year in which any arm may differ
from REF is 2027**, through the prior year's dual entering `clean_attribute_price_by_fuel`.
*Scored as a hit only on exact agreement at the reported precision.*

**P-2 (the voluntary escape identity).** In the binding years the escape MWh equals the deficit
**exactly**, because nothing else can move: `VOL-MID` and `VOL-HI` 2026 escape = **1.5127 TWh**
(V 8.4289 − G 6.9162), and their duals are **$4.50** and **$7.00/MWh exactly**. 2027–2028 escapes
follow the same identity **only if the arm's own eligible generation is still 6.9162 TWh** — from
2027 the arms may have built, so the 2027–2028 escape is `V(y) − G_arm(y)`, not `V(y) − G_REF(y)`.
That distinction is pre-registered so a smaller escape is read as a build, not as a gate failure.

**P-3 (the cap-arm CCS identity).** `CAP-STATE-TIGHT` carries **0.0 MW / 0.0000 TWh of
`gas_cc_ccs` in every year 2026–2030**, because the retrofit screen sees `carbon_price` = 0.0
(§4.3) and capx D50 measured that a repaired screen closes at carbon 0. **If any `gas_cc_ccs`
appears, §4.3's second argument is wrong and I say so at full magnitude.**

### 6.2 Carbon — the arms are killed, so the prediction is about the KILL

**P-4.** The four killed arms are re-checked, not assumed: the FINDING states the one-field diff,
the five-year price identity and the consumer census as the evidence, and **spends no LP**. The
falsifier for a reader is cheap and named: any second LP-affecting consumer of
`carbon_price_path` at the pin would break the identity. I found none; if a reviewer finds one,
the four kills are void.

### 6.3 Voluntary — the dual, the escape, and the ordering

**P-5 (gate G8, demoted with its reason).** In the first binding year **curtailment of eligible
resources cannot fall, because it is already 0.0000 TWh** — REF dispatches wind and solar at
exactly their unconstrained CF ceiling (§0.1 item 4). G8's ordering test ("the first MWh a REC
buyer pays for is one that was dumped") is therefore **vacuously satisfied and carries no
information on NEISO**; it is reported as a measurement (Δcurtailment = 0.0000 expected in 2026)
and cannot kill an arm. Recorded so the campaign's cross-ISO row for G8 is not read as a pass
NEISO never earned.

**P-6 (the pure ceiling ladder).** `VOL-MID` and `VOL-HI` are **identical in 2026 in every
respect except the dual and the objective** ($4.50 vs $7.00/MWh on the same 1.5127 TWh, i.e.
$6.81 M vs $10.59 M of escape payment). They diverge **from 2027**, and only through the capacity
screen: the eligible techs' `clean_attribute_price_by_fuel` differs by exactly $2.50/MWh, so
`VOL-HI` builds **at least as much** eligible capacity as `VOL-MID` in every year, and strictly
more in at least one. **A crossing — `VOL-MID` building more than `VOL-HI` in some year — would
be a monotonicity failure and I report it as one, not as noise.**

**P-7.** Both voluntary arms' **CO2 and price deltas are small** — |ΔCO2| < 1.0 Mt and
|Δ`lw_price`| < $1.50/MWh in every year — because a $4.50–7.00/MWh attribute price is ~9–13 % of
a $52/MWh energy price and reaches dispatch not at all. The voluntary axis's NEISO content is the
**dual, the escape, and the build response**, not an emissions response.

### 6.4 CES — the ladder is expected to SATURATE on the QUEUE, and the target row escapes then binds

**P-8.** **`CES-P20` and `CES-P30` land within 1 % of each other** on `clean_share`, commissioned
VRE and `emissions_mt`, while **`CES-P10` separates**. WS-2b §3 measured exactly this shape on
ERCOT (CES-20 and CES-40 commissioning *identical* builds because the binding cap is
`iso_budget_exhausted`); NEISO's budget is **4 GW/yr** with per-tech caps wind 1.0 / solar 2.0 /
offshore_wind 2.0 GW, so the saturation ceiling is structural and low. **The mechanism transfers;
the ERCOT levels do not, and I predict none from them.**

**P-9.** Direction in all three premium arms: `clean_share` ↑, commissioned wind and solar ↑,
`emissions_mt` ↓, `avg_price` ↓, curtailment ↑ from its REF zero (the first non-zero curtailment
this ISO produces in the campaign would be here or in `CES-T80`).

**P-10 (gate G4 — a MIXED regime, not ERCOT's pure escape).** Computed from REF's own credited
generation against `target(y) × E_total(y)`, on the resolved crediting map (§1.1):

| | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| target | 0.5500 | 0.5778 | 0.6056 | 0.6333 | 0.6611 |
| obligation `target × D` (TWh) | 57.949 | 61.328 | 64.756 | 68.229 | 71.752 |
| REF credited (TWh) | 40.372 | 40.372 | 61.799 | 78.078 | 70.140 |
| shortfall | **17.577** | **20.956** | **2.957** | *met, +9.849* | **1.612** |

So `CES-T80`'s row is predicted to **escape in 2026, 2027 and (narrowly) 2028 and 2030, and be
MET in 2029** — dual = ACP **$50.0000/MWh exactly** in the escape years, and a strictly interior
dual in 2029. The 2028 and 2030 margins (3.0 TWh and 1.6 TWh against a 4 GW/yr build budget) are
**inside** what one year of queue-limited entry can close, so **either verdict in those two years
is consistent with the mechanism** and neither is a gate failure; 2026's 17.6 TWh gap is not
closable and 2029's surplus is not reversible, so those two are the discriminating years.
NEISO's credited share is dominated by `gas_cc_ccs` at 0.95 from 2028 — 21.4 of the 61.8 TWh in
2028 and 34.5 of 78.1 in 2029 — which is why the regime is non-monotone in a way ERCOT's is not.

**P-11 (the deployment prediction).** `CES-T80`'s $50/MWh dual is ~7× the largest voluntary
ceiling and ~1.7× the largest CES premium, so it should **exhaust the 4 GW/yr ISO queue budget in
every year from 2027** (`binding_cap = "iso_budget_exhausted"`), making it the campaign's largest
NEISO deployment response — and the arm where **offshore wind (2 GW/yr, zero MW in REF) first
enters**, if it enters anywhere.

### 6.5 The cap arm — the price-vs-quantity comparison the case exists for

**P-12.** `CAP-STATE-TIGHT`'s emissions **rise** against REF in every year, and rise most in
2028–2030 where REF's CCS fleet disappears (P-3): I predict 2030 CO2 in the range **16–20 Mt**
against REF's 6.106 — i.e. the case, named "TIGHT", is on NEISO a **policy LOOSENING** relative to
REF's own RGGI escalator over most of the window. **P-13.** The row is therefore predicted to
**bind in 2029 and 2030** (budgets 18.668 / 18.000 Mt) and be **slack in 2026–2027** (20.670 /
20.003 vs a pre-retrofit-era emissions level near 16–18 Mt), with `co2_cap_price` 0.0 exactly in
the slack years. *This is the least certain prediction in the document and the one most likely to
miss; it is stated because the alternative is to discover it.* **P-14.** In every binding year the
dual is compared side by side with REF's exogenous adder for the same year (26.05 → 34.15 $/t) —
gate G12 — and the comparison is reported **with the asymmetry §0.1 item 8 names**: the adder
prices dispatch *and* investment, the row prices dispatch only, so a dual below the adder does not
by itself mean the quantity instrument is looser.

### 6.6 The combined legs — both nettings (ruling S11)

**P-15.** `CES-P20+VOL-HI` carries the CES **premium** (a screen price, no row), so its only row
is the voluntary one and D-6 has **no dispatch content** there: the premium ($20) exceeds the
voluntary ceiling ($7) in every year, so the voluntary dual should be **irrelevant to deployment**
in that arm while remaining the row's own escape price. **P-16.** `ALL-CLEAN` is the one arm where
D-6 has content — a CES **target** row and the voluntary row both counting a clean MWh. Both
nettings are reported side by side per §7's G9: **counts-toward as the headline** (as built),
**additional** beside it, computed at the report layer as `federal_credited − V ≥ target(y)·D`
with its implied escape `max(0, target·D + V − federal_credited)` priced at the ACP, and the CES
dual under each. Neither is asserted as the answer; D-6 is open. On NEISO the two nettings differ
by `V` ≈ 8.5–9.0 TWh against obligations of 58–72 TWh, i.e. **12–15 % of the standard** — a large
enough wedge that the choice is not academic here.

---

## 7. Gates — STRUCTURAL and STOP-ONLY (rule 29). Nothing is gated on a residual.

| gate | statement | how measured |
|---|---|---|
| **G1** | the resolved-input premise reproduces at THE PIN | §4.1's carbon table (RGGI adder dominates every path in every year), §3.1's volumes from the runner's own demand chain, §2's key reproduction of REF and LOAD-HI. **Already PASS, pre-solve.** |
| **G1a** | every surviving arm except `CAP-STATE-TIGHT` is **bit-identical to REF in 2026** | P-1's list, `generation_by_fuel_mwh` to 1e-6. A miss is reported at full magnitude and root-caused, never absorbed. |
| **G2** | **REF-side precondition** (desk standing change #2) | REF carries: **14/14 invariants PASS**, `unserved_mwh` **0.0** in all five years, reserve margin +0.1681 → +0.0840 (I12 band [2.9 %, 17.9 %], all in-band), `hours_ge_500` **0**, `curtailment_twh` **0.0**. **Consequence, declared now: NEISO's price side IS campaign-grade** — levels and deltas are both quotable, unlike ERCOT's. Two standing caveats ride along, neither invalidating a delta: (a) NEISO's 2028–2030 CO2 sits on an 8.8 GW `gas_cc_ccs` fleet whose emission rate is only correct **post-D77**, which is exactly the pin I am on, so `FINDING-scn-ws5a-load-neiso` §2.3's "levels not quotable" is **retired for this lane's REF**; (b) the NEISO **zonal** load file for weather year 2024 is absent, so the demand chain falls back to the ISO-total shape — identical in REF and every arm, so every delta is protected, and stated rather than silent. |
| **G3** | **footprint confinement** | *CES* arms move eligible/ineligible shares, the CES dual and the entry ladder; *voluntary* arms move eligible-class rows, thermal rows and the escape column only; *cap* arm moves fossil rows, the retrofit ledger and imports. In every non-cap arm the **`import` fuel's own emissions stay 0.0** in `emissions_by_fuel_mt` (imports are a reported-only line, never inside `emissions_mt`), and nuclear + hydro move 0.0000 TWh unless an arm retires or builds one. |
| **G4** | **`CES-T80` dual identity** | dual = ACP **$50.0000/MWh exactly** in every year the target is unmet, and strictly interior where it is met. Escape MWh = `target(y)·D − credited`. P-10 pre-registers 2026/2027 as escape and 2029 as met — the two discriminating years; 2028 and 2030 are inside one year's build budget and either verdict passes. |
| **G5** | no **non-target load-bearing invariant** flips PASS → FAIL vs REF | I1–I14 per leg-year against REF's **14/14 PASS**. Any new FAIL outside the target mechanism kills the arm. |
| **G6** | no unserved energy appears where REF has none | REF is 0.0 in all five years, so this binds strictly on `CES-*`, `VOL-*` and `CAP-STATE-TIGHT`, whose mechanisms cannot raise demand. It does **not** bind on `ALL-CLEAN`, which raises load by construction. |
| **G7** | voluntary dual bounded, **per arm** | where the row binds: dual > 0 and **≤ the arm's own ceiling** — **$4.50/MWh on `VOL-MID`**, **$7.00/MWh on `VOL-HI` / `CES-P20+VOL-HI` / `ALL-CLEAN`** (§3.3). Where it escapes: dual = that ceiling **exactly** and escape MWh = the shortfall. In the slack years (2029–2030) dual = 0 exactly. |
| **G8** | **curtailment before thermal** | **VACUOUS ON NEISO and demoted to a report line** — REF's eligible curtailment is 0.0000 TWh by construction (§0.1 item 4), so there is no dumped MWh for a REC buyer to buy first. Measured and reported (expected Δcurtailment = 0.0000 in the first binding year); **cannot kill an arm here**, and the campaign's cross-ISO G8 row must not read NEISO as a pass it never earned. |
| **G9** | **both nettings** on `CES-P20+VOL-HI` and `ALL-CLEAN` | counts-toward as headline, additional beside it, CES dual under each — never one alone (ruling S11). |
| **G10** | **`CAP-STATE-TIGHT` row identity** | in every binding year `emissions_mt` equals the budget to 1e-6 relative and `co2_cap_price` > 0; in a slack year the dual is **0 exactly**. Slack is read as `budget − emissions` from §4.3's budget row (no `co2_cap_slack_t` is emitted — SCN-CAP §5 item 3). |
| **G11** | **one instrument at a time** | under the case, `resolve_carbon_program` returns a resolution with `cap_spec` set and `price_adder` **`None`** in every year, and `resolve_carbon_price` returns **0.0000** — i.e. the row REPLACES the adder and no federal price is ever composed on top (`carbon_price_path: zero`). **Already PASS, pre-solve** (§4.1, §4.3). |
| **G12** | **price vs quantity, reported side by side** | the row's dual per year beside the adder path's exogenous price for the same year (26.0545 / 27.8783 / 29.8298 / 31.9179 / 34.1521 $/t), **with the §0.1-item-8 asymmetry stated at the number**: the adder reaches both dispatch and the capacity screen; the dual reaches dispatch only. |

A gate **may kill an arm; it may never promote one**, and no gate reads a target residual.

---

## 8. Execution plan, and the first solve is HELD on P4

**Driver** — `run_ces_leg.py`, the driver the load and resolve lanes both used (0 lines changed
between `1cc45bb2` and the pin, and 0 between the pin and `origin/main`), at THE PIN, one leg per
invocation, years sequential:

```
H0=bdfb3095e9fa0cd2bec3f4e843f320b42588c72b
[ "$(git rev-parse HEAD)" = "$H0" ] || exit 90
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  uv run python scripts/run_ces_leg.py \
    --config configs/scenarios/neiso_scenario_base_2026_2030.yaml \
    --matrix configs/scenario_campaign_matrix.yaml \
    --case <CASE> --campaign scn-campaign-policy-2026-09-06 \
    --out-dir results/scn-campaign-policy-2026-09-06/NEISO/<CASE>
```

Order (cheapest discriminating first): `VOL-MID`, `VOL-HI`, `CES-P10`, `CES-P20`, `CES-P30`,
`CES-T80`, `CES-P20+VOL-HI`, `ALL-CLEAN`, `CAP-STATE-TIGHT`. Rebase **between** legs, never
during one. Logs to the session scratchpad, never the results tree — so this lane adds no
`.gitignore` stanza (the per-leg out-dir is slim by construction: `run_ces_leg.py` passes
`redirect_cache=False`, so only `full_horizon_summary.json` + `run_config.json` land there).

**Cache isolation, three ways, each measured** (§2): all nine keys are new against every committed
`*.json` on `origin/main` (0 grep hits each); `results/NEISO/` holds 0 entries in this container;
and no pre-fix bundle is ever linked or copied into a cache root at any point.

**Budget.** 9 legs × 5 solve-years. The committed REF sidecar measures NEISO at **326.4 s / 5
years (≈1.1 min per solve-year), peak RSS 3,682.7 MB** ⇒ **≈5.5 min/leg, ≈50 min of LP total**,
peak RSS ≈3.7 GB on a 15 GB box. NEISO is the campaign's cheapest ISO after ERCOT.

**Reporting.** REF's own headline row — including `import_co2_mt_reported`, `clean_share`,
`curtailment_twh`, `unserved_mwh` and `avg_price` — is recoverable **from a committed artifact**,
`results/scn-campaign-load-2026-09-06/NEISO/report/neiso_headline_deltas.csv`, which RESOLVE
**regenerated post-D77 at leg 2** (`931866cc`; its REF `emissions_mt` row 15.8319 / 17.0960 /
9.8722 / 4.7566 / 6.1058 is the `-r2` trajectory to 4 dp, not the pre-fix one). That closes the
gap the slim `full_horizon_summary.json` would otherwise leave — the summary carries **no** import
line — so the WS-0 leakage duty is dischargeable without REF's parquet cache, which this container
does not have and which is never re-solved. Arm-side scalars come from each leg's own cache
through the same `results/export.py::_summarize_year` seam.

**THE FIRST SOLVE IS HELD ON PRECONDITION P4.** I cannot establish what else is solving:
RESOLVE's CAISO and MISO lanes have pushed PRECOMMITs and 0 legs, so up to two SCN solves may be
live, and the capx track is visibly mid-solve (D65-B-R leg 7; **D76 phase 3 on NEISO + NYISO**).
The charter's own clause governs — *"if you cannot establish what else is solving, hold and ask
rather than assume the slot is free"* — so nothing is solved until the owner says the slot is
free. **Everything else in this document is complete and final.** NEISO is cheap (3.7 GB, ≈50 min
total) and r#17's launch order names it in the first pair, so it can take the slot the moment one
opens.

---

## 9. Routed to SCN-DESK — not executed, outside this lane's regions

1. **THE CHARTER'S CASE-13 KILL TEST IS UNSOUND, AND `FINDING-scn-cap-2026-09-06.md` §3's NEISO
   verdict with it.** Both say a slack budget makes `CAP-STATE-TIGHT` byte-identical to REF; on a
   program ISO it never can be, because the row **replaces** the adder (the charter's own G11) and
   the case's resolved carbon price is $0.00/t against REF's $26.05–34.15/t (§4.3). The kill test
   should read *"the case is byte-identical to REF only where `resolve_carbon_program` returns
   `None` — i.e. on a NON-program ISO (ERCOT, MISO)"*, which is exactly the identity the ERCOT
   lane proved for itself and is where the rule is sound. **NYISO and CAISO are unaffected in
   verdict** (their rows bind, so they solve either way) **but their lanes' phase-0 reasoning
   should be re-cut on the same correction**, and SCN-CAP §3's "the post-fix REF cannot change this
   verdict" sentence is true of the *binding* question and false of the *identity* question it is
   attached to.
2. **A second, structural finding inside the same case, for card D-1 / D-2's next presentation:**
   the mass-cap row's dual reaches **no capacity screen**. `evolve_fleet` is handed
   `carbon_price=resolve_carbon_price(config, driver_year)` (`runner.py:2322`), which is 0.0 under
   the case, and `co2_cap_price` has no consumer outside `results/export.py` / `outputs.py`. So
   the campaign's one QUANTITY instrument prices dispatch while every PRICE instrument prices
   dispatch and investment, and a quantity-vs-price comparison across the two is not
   like-for-like. Not repaired here (outside this lane's regions, and a real design question), but
   it must not be discovered inside a result table.
3. **The charter's "25–41 %" import-line figure for NYISO/NEISO is the PRE-D77 reading.** On the
   post-D77 NEISO REF the line is **26–92 %** of the in-ISO level, peaking in 2029 where the
   retrofit fleet takes in-ISO CO2 to 4.757 Mt against an unchanged 4.370 Mt of import-attributed
   CO2. The number in the charter should move with the pin; the duty itself is unchanged.
4. **`VOL-MID` is LIVE on NEISO and identical in volume to `VOL-HI`** — the mirror of the ERCOT
   lane's §9 item 4. Because `E_DC` is exactly zero, the mid/high pair on this ISO is a **pure WTP
   ceiling ladder** with no volume confound, which is the cleanest possible read on card
   **D-2(b)**'s ceiling level and on **D-3c**'s crediting leg. If the desk wants one ISO to carry
   the voluntary instrument's level evidence, NEISO is it.
5. **A slim-artifact gap the campaign got away with only by luck.** A registered leg's committed
   evidence is `full_horizon_summary.json` + `run_config.json`, and **neither carries
   `import_co2_mt_reported`, `clean_share`, `curtailment_twh` or `unserved_mwh`** — the WS-0
   leakage duty's own numbers. They survive for NEISO only because RESOLVE happened to regenerate
   the delta-report CSVs at leg 2. A lane whose REF cache is in another container and whose report
   CSVs were not refreshed cannot discharge the duty at all. Worth one line in the campaign's
   registration recipe: **the delta-report CSVs are part of a leg's committed evidence, not an
   optional extra.**

## 10. Duties

- **No default moved, no knob moved, no `ScenarioConfig` field added, no solve yet.** DOF
  ledger: **zero** free parameters. No `authorized_price_tuning` (a backcast offer-curve channel;
  untouched).
- **Consumed, never edited:** `configs/scenario_campaign_matrix.yaml`, the NEISO base YAML,
  everything under `src/`, `scripts/run_ces_leg.py`, `scripts/report_scenario_deltas.py`,
  `scripts/register_forecast_run.py`, and every committed bundle, sidecar and report CSV.
  `program-status.json`, `ff-verdicts.json` and the whole **backcast** namespace: untouched
  (§7.5 — this lane registers into the forecast namespace only).
- **Rule 29(c):** this lane produces no screen bundle and no control bundle — its legs are
  registered campaign arms, and the control is a committed one.
- **Rule 22 / R-AZ:** every solve year is 2026–2030, forecast mode, inside the §2.1b 5-year
  window; no holdout tier is touched, at launch or at registration.
- **Backcast byte-identity:** untouched by construction (`mode="forecast"` on every leg).
