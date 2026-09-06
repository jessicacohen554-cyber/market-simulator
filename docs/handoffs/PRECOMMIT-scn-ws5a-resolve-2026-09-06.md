# PRECOMMIT — SCN-WS5A-RESOLVE: ruling S8 executed, the 13 contaminated legs re-solved post-D77

**Lane** SCN-WS5A-RESOLVE · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-06 ·
**Branch** `claude/scn-ws5a-resolve-post-d77-m8m5ft` · **Data profile** `all` (full clone —
`hydrate_data.py --profile all` reports every blob already local) ·
**Campaign** `scn-campaign-load-2026-09-06` (unchanged — same ids, same cases, same reference
case) · **Charter** SCN-DESK ledger §5, refresh #13 (ruling **S8**, card D-10) + **S5**'s
model-grain paired check · **Predecessor** `PRECOMMIT-scn-ws5a-load-2026-09-06.md` + its
ADDENDUM (the freeze at `1cc45bb2`) and `STATUS-scn-ws5a-load-2026-09-06.md`.

**Pushed before the first solve** (rule 29). Every number below is zero-LP: a resolved config
at THE PIN, a committed pre-fix artifact, or arithmetic on the two. Nothing here is revised
after a solve; §6's predictions are scored as written, misses at full magnitude.

---

## 0. THE PIN

```
bdfb3095e9fa0cd2bec3f4e843f320b42588c72b
```

`origin/main` at PRECOMMIT time. Verified by `git merge-base --is-ancestor`:

| required ancestor | what it is | ancestor of THE PIN |
|---|---|---|
| `fc583339` | capx **D77** merge (the CCS retrofit emission-rate repair) | **yes** |
| `b1f77621` | capx **D65-B** merge (Acts A+B, the re-key event) | **yes** |
| `1cc45bb2` | the load campaign's frozen pin | **yes** |

**THE PIN IS NOT MOVED AFTER THE FIRST SOLVE.** Anything landing on `main` after it is
recorded in the FINDING as post-pin, never retro-fitted and never used to re-read a result.
This is the sha the six `SCN-WS5A-POLICY-<ISO>` lanes read as their precondition **P1**.

## 0.1 Bottom line before any LP

1. **Every one of the 16 campaign legs re-keys at THE PIN** (§3, measured). D65-B moves
   `ccs_retrofit_vom_adder` 8.0 → 2.95, which is **not** a `_CACHE_KEY_OPTIONAL_FIELDS`
   member and so re-keys every config unconditionally. The cache blocker the STATUS doc
   named — "D77 moves no key, so a re-solve HITS the pre-fix bundle" — is therefore
   **defeated by construction at THE PIN**, on top of the two belt-and-braces isolations
   in §4. It was a real hazard at the pin the STATUS doc was written on; it is not one here,
   and that is a measurement, not an assumption.
2. **ERCOT is measured clean and is NOT re-solved.** All three ERCOT legs carry
   `gas_cc_ccs = 0.0 TWh` in **every** year 2026–2030 (§2). D77 and D65-B are inert on a
   fleet that converts nothing; their keys move, their answers cannot.
3. **PJM carries TWO live mechanisms beyond D77/D65-B, and neither was in the desk's scope.**
   capx **D67-ARM** arms `capacity_adequacy_requirement_published_by_iso = {"PJM": True}`
   through `_pjm_config`'s `default_scenario_overrides` — measured on the resolved PJM legs,
   so a campaign case does not have to set it — and capx **D81** is live on PJM by its own
   epoch predicate (forecast × clearing-armed × `fossil_announced_exits_enabled`, all three
   measured true on PJM alone). **PJM's pre-vs-post difference is therefore not attributable
   to D77 alone**, and §6 pre-declares that rather than discovering it afterwards. The desk's
   r#14 note that D67-ARM is "INERT for every SCN leg (a `{iso: bool}` gate no campaign case
   sets)" is **corrected here**: the ISO's own default arms it.
4. **Nothing else on the solve path is live for a load leg.** 30 of the 34 solve-path commits
   in the window classify INERT with a stated reason (§1); the four LIVE ones are D77, D65-B
   (both by design, both ISO-wide) and D67-ARM + D81 (PJM only).

---

## 1. G-DRIFT (rule 29(b)) — `1cc45bb2 .. bdfb3095`, hunk by hunk

Window: the rule-29 window plus the forecast entry chain the charter names —

```
git diff 1cc45bb2 bdfb3095 -- src/market_sim scripts/lib scripts/run_full_horizon.py \
  scripts/run_ces_leg.py scripts/check_forecast_invariants.py configs/ \
  data/raw/_validation-source data/raw/reference
```

**41 files, +5,362 / −433, across 34 non-merge commits.** Recorded before the first solve so
it cannot be written to fit a result. `scripts/run_ces_leg.py` itself: **0 lines changed.**
`configs/scenarios/*_scenario_base_2026_2030.yaml`: **0 lines changed** — the only file under
`configs/` that moved at all is `scenario_campaign_matrix.yaml`.

### 1.1 LIVE — four mechanisms, every one named in advance

| commit | mechanism | live for | why LIVE |
|---|---|---|---|
| `ae8dd2a0` | **capx D77** — the CCS retrofit emission-rate seam | NEISO, NYISO, CAISO, PJM, MISO | `ccs_capture_fraction` is now composed into `apply_plant_emission_rates{,_v2}`, so a converted unit is no longer restored to its uncaptured host rate. This is the object of the lane. **Inert on ERCOT**: its retrofit ledger is empty in all three legs (§2), so no generator ever carries a non-zero capture fraction. |
| `fb93b76e` | **capx D65-B** Acts A+B | all six (behaviour: the five with a retrofit ledger) | `ccs_retrofit_vom_adder` 8.0 → **2.95** $/MWh and `ccs_retrofit_fixed_cost_co2_scaling` default `False` → **True**; both measured resolved on every leg (§3). Live from `ccs_retrofit_available_year` = 2028 wherever the screen converts a unit; on ERCOT it re-keys without moving an answer. |
| `26474700` | **capx D67-ARM** (owner ruling Q52) | **PJM only** | `capacity_adequacy_requirement_published_by_iso = {"PJM": True}` arrives through `_pjm_config`'s `default_scenario_overrides`, measured on both resolved PJM legs. It replaces the `screen peak × FPR` reconstruction at the `gross_adequacy_requirement_mw` seam that the reliability floor, the reserve-margin build backstop **and** the CR-1 position all reach through — and the backstop ladder is PJM's only responding channel in this campaign (WS-4b (a)). No other ISO's `default_scenario_overrides` moved in the whole window (measured: one added line in `iso_configs.py`). |
| `18432bda` | **capx D81** | **PJM only** | Its own epoch predicate is forecast mode × `capacity_market_supply_clearing_by_iso` on × `fossil_announced_exits_enabled` on. Measured on the resolved legs: PJM is `{"PJM": True}` + `True`; every other ISO resolves the clearing to `None`. |

### 1.2 INERT — the other 30 commits, each with its reason

| commit(s) | what | INERT because |
|---|---|---|
| `bf37a0dc`, `9440f17d`, `90ce9a91` | same-year P1 basis seed; `malloc_trim` removal | The seed's gate is `_xwarm AND xyear_warmstart is None AND env`; the forecast passes an **explicit bool** (`ScenarioConfig.forecast_xyear_warmstart`), so `xyear_warmstart is None` is false on this path and the seed can never arm. The `malloc_trim` removal is RSS/wallclock only. (Same classification capx D77 §4.1 reached and then confirmed empirically.) |
| `5d639e31` | capx D60-R4; `apply_set_overrides` → `with_overrides` | **Both** the old and new `apply_set_overrides` short-circuit `if not overrides: return config`, and every campaign leg carries `set_overrides = {}` — the case overrides ride `matrix_configs`, not `--set` (load ADDENDUM §5). The changed branch is never entered. |
| `83f391b0`, `7ec0f110` | SCN-FIX2: the carbon ladder's committed RFF-path form; the voluntary relabel | Touches the `CARB-LO/MID/HI` and `CARB-MID+LOAD-HI` rows and comment text only — the `REF` / `LOAD-HI` / `LOAD-HI-ORGANIC` blocks are byte-unchanged (measured diff). Every re-solved leg resolves `carbon_price_path = "zero"` (§3). |
| `75a1a732`, `256fc7d1`, `89b0a9f4` | SCN-CAP: `mass_cap_tons_by_year`, `CAP-STATE-TIGHT` | `mass_cap_tons_by_year` resolves `None` and `mass_cap_enabled` `False` on every leg, so `_power_sector_cap`'s new first read falls through to the incumbent path. The case is a different case. |
| `0a5046ce`, `e185d0dd`, `2c5b8242`, `ac198783` | SCN-WS3b voluntary demand | `voluntary_clean_demand_path` resolves `"off"` on every leg (§3); the field is cache-optional at `off`. `constants.py` is **purely additive** in the whole window (zero deletions — only the seven `VOLUNTARY_*` names). `data/datacenter.py`'s `datacenter_block_energy_mwh` is a new read-only helper with no caller on the demand path. |
| `cd975929` | nyiso-199 `nyiso_ct_peaker_bands_measured` | Default `False`, NYISO-scoped, absent from NYISO's `default_scenario_overrides` (unchanged in the window). |
| `70e0d806`, `9a7f1390` | nyiso-200/201 `nyiso_gas_bridge_startup_aware` + a screen-stats diagnostic | Both `pipeline/commitment.py` hunks gate on `startup_aware = bool(getattr(config, "nyiso_gas_bridge_startup_aware", False))`, default `False`; `model/commitment.py`'s addition is a `screen_stats is not None` diagnostic. |
| `cde54404`, `7fa9f096`, `3c17b49a`, `208a714d` | miso-224/225 gas at marginal commodity, variable transport, neighbour-anchored seam ladder | Three new fields, all default `False`. `apply_miso_gas_marginal_commodity` returns `None` at its first statement when unarmed, and `resolve_fuel_prices` then takes the incumbent branch verbatim; `_inject_seam_ladder` is byte-identical when `neighbour_anchored=False`. |
| `0e769df0` | miso-230 CT net-load drag (`data/raw/reference/miso_ct_netload_drag.json`) | A new frozen record with **no consumer under `src/market_sim/`** — read only by `scripts/data/derive_miso_ct_netload_drag.py` and `scripts/probes/`. |
| `df277e89`, `c274f1a0`, `48bcd0ec` | the CAISO measured offer-surface artifact pair (net: reverted then re-applied) | Their consumers are `pipeline/backcast_config.py` (never entered by a `mode="forecast"` run) and the conditional surface loader, which gates on `caiso_offer_surface_conditional` — measured **`False`** on the resolved CAISO legs, with `offer_curve_by_group = {}`. |
| `64477801` | capx D74 no-default-cap convention | `capacity_no_default_cap_convention_by_iso` resolves `None` on every leg, and the gate additionally refuses without the D62 published bar. |
| `f3d0396e` | capx D75-R PJM VRE ELCC vintage | `pjm_vre_accreditation_vintage` default `False`; `resolve_renewable_vintage_credit` returns at `not vre_accreditation_vintage_armed(...)`. |
| `8ad280ed` | capx D76 measured-hindcast screen peak | Gate is `config.capacity_screen_peak_measured_hindcast AND config.hindcast`; both false on a forecast leg. |
| `fd0d01e1` | capx D78 sector-gate offer seam | Needs `retirement_sector_gate=True` **and** a clearing-armed ISO. Measured: PJM has the clearing on but the sector gate **off**; MISO has the sector gate on but the clearing **off**. No leg satisfies both. |
| `820cae83` | capx D65-B-R step 0 (persist the retrofit screen's per-host scaling record) | Writes additional fields into the evolution ledger's `ccs_retrofits` rows. Artifact content, not a solve input — and it is what makes this lane's G1 identity readable from the bundle. |
| `bbcd4755` | Y-24 undeclared-invariant ratchet | `enforce_invariant_declaration_gate` sits at the **registration** seam, not the solve. Live for this lane's *procedure* (§5), not for any LP. |
| `06121d4e`, `7ffd808b`, `bf1964bf`, `110e9d99` | capx-D73 phase 1 (zero-LP route over committed `run_config.json`); D67 facade-inventory names; two `ruff format` passes | No behavioural statement on the solve path. |

### 1.3 Verdict

**Form 4 is VALID for the four LIVE mechanisms and only for them**: the incumbent campaign's
committed bundles ARE the control, and the difference they measure is D77 + D65-B (all five
re-solved ISOs) and, on PJM alone, D67-ARM + D81 as well. **No control solve is earned or
spent** (rule 29(b)): the audit answers the code question, and the LIVE hunks are the object
of the lane rather than a confound to be differenced away — except on PJM, where they are a
confound and are declared as one rather than absorbed.

---

## 2. Scope — 13 legs, and why ERCOT's three are not among them

Measured from the committed pre-fix summaries (`generation_by_fuel_mwh["gas_cc_ccs"]`, TWh):

| ISO | legs | 2028 | 2029 | 2030 | re-solve? |
|---|---|---|---|---|---|
| NEISO | REF / LOAD-HI | 1.72 / 1.08 | 8.55 / 8.13 | 16.72 / 16.89 | **yes (2)** |
| NYISO | REF / LOAD-HI / ORGANIC | 10.40 / 13.17 / 12.99 | 14.55 / 18.64 / 18.43 | 24.42 / 30.18 / 29.99 | **yes (3)** |
| PJM | REF / LOAD-HI | 0.00 / 0.00 | 3.50 / 11.62 | 3.50 / 11.62 | **yes (2)** |
| CAISO | REF / LOAD-HI / ORGANIC | 13.63 / 14.96 / 14.91 | 21.88 / 25.98 / 25.83 | 45.16 / 51.85 / 51.37 | **yes (3)** |
| MISO | REF / LOAD-HI / ORGANIC | 0.00 / 0.00 / 0.00 | 2.02 / 2.57 / 2.57 | 2.50 / 3.72 / 3.72 | **yes (3)** |
| **ERCOT** | REF / LOAD-HI / ORGANIC | **0.00** | **0.00** | **0.00** | **NO — measured clean** |

**13 of 16.** This is the STATUS doc's corrected D-10 scope, reproduced here from the
artifacts rather than inherited: the desk's original card scoped six legs on a claim PJM
falsified, and ERCOT is the only exempt ISO.

Order of execution (rule 12 `[R-PARALLEL]`, years sequential inside every invocation):

1. **NEISO** REF + LOAD-HI and **NYISO** REF + LOAD-HI + LOAD-HI-ORGANIC — may start at once
   (≈11 min and ≈61 min respectively at the campaign's measured rates; peak RSS 3.49 / 3.80 GB).
2. **PJM** REF + LOAD-HI (≈80 min, 8.90 GB) — **alone**.
3. **CAISO** REF + LOAD-HI + LOAD-HI-ORGANIC (≈65 min, 4.87 GB) — **alone**.
4. **MISO** REF + LOAD-HI + LOAD-HI-ORGANIC (≈80 min, **9.65 GB peak RSS on a 15 GB box**) —
   **alone; nothing else may solve.**

[r#14] The capx track's per-plant slot is contended (D65-B-R's batch, D78-R, D81). **Before
each of the PJM / CAISO / MISO legs this lane confirms with the owner that no capx per-plant
solve is live**, and records the answer in the FINDING. The slot is never assumed.
`git fetch` + rebase happen **between** legs, never during one; every solve is wrapped in a
HEAD GUARD (`[ "$(git rev-parse HEAD)" = "$H0" ] || exit 90`).

---

## 3. Phase 0 (zero LP) — every leg re-keys, and the resolved case fields

Resolved exactly as `runner.run_scenario_iso` does — `matrix_configs(base, sweep)` →
`resolve_policy_bundle` → `set_caiso_fsno_partition` → `apply_iso_scenario_defaults` — so the
key below is the key the solve will compute, not a naive `config.cache_key()`.

| ISO | case | pre-fix key (committed) | key at THE PIN | moved |
|---|---|---|---|---|
| NEISO | REF | `5e2c52ea81694c10` | `8878d29743555b45` | **YES** |
| NEISO | LOAD-HI | `8e603f9d81b73da7` | `0d5c394b6c4e5cb6` | **YES** |
| NYISO | REF | `aed447f88457dff7` | `f10cc93084b4c0db` | **YES** |
| NYISO | LOAD-HI | `470338150a2f85a0` | `c2ceaefa4afafcda` | **YES** |
| NYISO | LOAD-HI-ORGANIC | `bf50c8305ba3c4ee` | `27f19f22105ab6cb` | **YES** |
| PJM | REF | `7088c5643b559a84` | `67a786980ac38749` | **YES** |
| PJM | LOAD-HI | `94061c158317a8a5` | `d1da885b4fdc4e6b` | **YES** |
| CAISO | REF | `54a70e9a6e396cad` | `2d16a246bb372e4a` | **YES** |
| CAISO | LOAD-HI | `7687ac2d1265ec14` | `86bfde6ed2896b99` | **YES** |
| CAISO | LOAD-HI-ORGANIC | `a3472da093262e47` | `ff8c04bc4eef6605` | **YES** |
| MISO | REF | `b08a51a33ab6bb9d` | `f1b3caa22b3f14ff` | **YES** |
| MISO | LOAD-HI | `6f4fff944c9b5528` | `9688b06c1b0a5a54` | **YES** |
| MISO | LOAD-HI-ORGANIC | `eca5bcfb14a379ad` | `b87deb7735c242a0` | **YES** |
| *(ERCOT, not solved)* | REF / HI / ORG | `6e40769352a572ba` / `31cf71afda5c610d` / `c5255cea87fbaacf` | `de9c68e19316910e` / `ec2ea8193e2e45a1` / `0c87f2f2467e95b3` | YES (key only) |

**Every key moves**, for the reason capx D65-B's own epoch entry states: `ccs_retrofit_vom_adder`
is not a `_CACHE_KEY_OPTIONAL_FIELDS` member and its value change re-keys unconditionally.
Cross-check: the live forecast default key is `547053bdfccd4264`
(`tests/regression/test_persisted_identity.py::PINNED_DEFAULT_CACHE_KEY`), i.e. post-D65-B,
which is the same fact from the other side.

**Resolved case fields, measured (identical structure in all six ISOs unless noted):**

| field | REF | LOAD-HI | LOAD-HI-ORGANIC |
|---|---|---|---|
| `demand_growth_path` | mid | high | high |
| `datacenter_load_path` | mid | high | mid |
| `electrification_path` | off | off | off |
| `carbon_price_path` | zero | zero | zero |
| `federal_ces_enabled` | False | False | False |
| `voluntary_clean_demand_path` | off | off | off |
| `mass_cap_enabled` | False | False | False |
| `ccs_retrofit_vom_adder` | **2.95** | 2.95 | 2.95 |
| `ccs_retrofit_capex_co2_scaling` | True | True | True |
| `ccs_retrofit_fixed_cost_co2_scaling` | **True** | True | True |
| `ccs_retrofit_capture_rate` | **0.9** | 0.9 | 0.9 |
| `mode` / `start_year` / `end_year` | forecast / 2026 / 2030 | idem | idem |

Per-ISO, the two fields that decide §1.1's PJM-only classifications:

| ISO | `capacity_adequacy_requirement_published_by_iso` | `capacity_market_supply_clearing_by_iso` | `retirement_sector_gate` |
|---|---|---|---|
| **PJM** | **`{'PJM': True}`** | **`{'PJM': True}`** | False |
| MISO | None | None | True |
| NEISO / NYISO / CAISO / ERCOT | None | None | False |

---

## 4. THE CACHE RECIPE — three independent isolations, each provable

The STATUS doc's blocker: *"D77 moves no cache key, so a re-solve at the same key HITS the
pre-fix bundle and returns the numbers it was meant to replace."* True at the pin it was
written on. Defeated here three times over:

1. **A NEW out-dir per leg** — `results/scn-campaign-load-2026-09-06-r2/<ISO>/<CASE>/`.
   Nothing is ever written into the pre-fix tree, so a mis-step cannot overwrite the control
   this lane differences against.
2. **THE KEY ITSELF MOVED** (§3). A post-pin solve computes a key no pre-fix bundle occupies,
   so the stale bundle is unreachable even from a warm cache. This is the decisive isolation
   and it is a measurement.
3. **THE CONTAINER'S DEFAULT CACHE IS EMPTY.** `results/{ERCOT,CAISO,PJM,MISO,NYISO,NEISO}/`
   each hold **0 entries** — the tree is gitignored and this container was cloned fresh, so
   the pre-fix bundles' parquet caches do not exist locally at all. Only the committed slim
   artifacts (`full_horizon_summary.json` + `run_config.json`) are present.

**NEVER used:** the WS-4c harness helper that links arm bundles into the shared cache root.
No pre-fix bundle is linked, copied or moved into any cache root at any point.

### 4.1 Driver — `run_ces_leg.py`, and why not `run_full_horizon.py --out-dir`

The charter's recipe names `run_full_horizon.py --out-dir` for its `CACHE_ROOT` redirect.
**Confirmed at `scripts/run_full_horizon.py:736–750`**: `solve_and_summarize` sets
`cachemod.CACHE_ROOT = out_dir` when `redirect_cache=True`, which is `run_full_horizon.main`'s
behaviour, and restores it at line 814. **But that redirect is unreachable from a campaign
leg**: `run_ces_leg.py::run_leg` passes `redirect_cache=False` by design (its docstring: the
bundle and `report_ces_campaign.py` assemble every leg by `cache_key` out of the DEFAULT
cache), and it is hard-coded, not a CLI option.

Driving the legs through `run_full_horizon.py` instead would mean building each config from
`reference_config(iso, ...)` rather than from the campaign's own base YAML expanded through
`matrix_configs` — a different config-construction path, for a **same-id re-registration**
whose whole point is that the case is unchanged. That trade is refused: a config-divergence
risk is a worse defect than the one being repaired.

So the legs run through **exactly the driver the load lane used**, with isolations 1–3 above
carrying the burden the redirect was meant to carry. `run_ces_leg.py` is unchanged in the
window (0 lines), so the driver itself is not a variable. Per-leg command:

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  uv run python scripts/run_ces_leg.py \
    --config configs/scenarios/<iso>_scenario_base_2026_2030.yaml \
    --matrix configs/scenario_campaign_matrix.yaml \
    --case <CASE> --campaign scn-campaign-load-2026-09-06 \
    --out-dir results/scn-campaign-load-2026-09-06-r2/<ISO>/<CASE>
```

Logs are written to the session scratchpad, never into the results tree, so this lane adds
no `.gitignore` stanza and touches no file outside its declared regions.

### 4.2 The per-leg cache-hit proof (gate **G5**), recorded for every one of the 13

A leg is a fresh solve only if **all five** hold:

| # | evidence |
|---|---|
| a | `results/<ISO>/<PIN key>/` did not exist before the solve (`ls` recorded pre-solve) |
| b | the leg's `run_config.json` `cache_key` equals the §3 PIN key for that leg |
| c | its `git.sha` is THE PIN (or a descendant of it with a zero solve-path diff, per the load ADDENDUM §5 convention — this lane commits while later legs solve) and `git.dirty == false` |
| d | `total_wall_s` is a solve's, not a cache read's (order 10²–10³ s, and per-year `wall_s` present for all five years) |
| e | its 2028–2030 `gas_cc_ccs` emission rate is `measured host × 0.10`, not ~0.37 (gate **G1**) |

**A leg whose trajectory reproduces the pre-fix bundle to the digit is a CACHE HIT and a
STOP** — reported, never registered.

---

## 5. STOP gates — structural, kill-only, never gated on a residual

Pre-registered. A gate PASS means only "the mechanism did what its own arithmetic says"; it
promotes nothing and contributes to no determination (rules 1 `[R-STRUCT]`, 29 `[R-SCREEN]`).

| # | gate | STOP condition |
|---|---|---|
| **G1** | **identity** (ruling S5's paired check at model grain, D77 §4b gate 1) — for every retrofitted unit-year in every re-solved **REF**, `emission_rate_co2 == measured host CAMPD rate × (1 − 0.90)` to rel. tol **1e-9** | any converted unit off the identity |
| **G2** | **confinement** — no unit **outside** the retrofit cohort moves its `emission_rate_co2` versus the pre-fix bundle | a non-converted unit's rate moves |
| **G3** | **pre-2028 inertness, measured** — every zero-carbon class's generation (nuclear, hydro, wind, solar) identical to the pre-fix bundle in **2026 and 2027** | any 2026/2027 zero-carbon row moves |
| **G4** | **no collateral flip** — no non-target load-bearing invariant flips PASS → FAIL versus the pre-fix leg | a flip whose cause is **not** re-ordered dispatch. A flip *caused by* re-ordered dispatch (I3 / I7 / I12) is **reported with its cause named**, not a STOP — §6 pre-declares which ISOs can produce one |
| **G5** | **cache-hit test** (§4.2) | any leg failing a–e |

**G1 is scored on the REFs** (the charter's instruction) and reported for the load arms where
the ledger permits. **G3 is a measurement, not an argument**: `apply_ccs_retrofit` returns at
`if year < config.ccs_retrofit_available_year` (2028), so 2026–2027 should be inert — but
D65-B also ships in this pin and its two fields are read at the same call site, so the
pre-2028 rows are the empirical check that both repairs are confined to 2028+.

**Explicitly NOT a STOP**, pre-declared: the retrofit **set** moving (capacity or membership),
the merit order re-ordering, CO2 falling by any magnitude, the LOAD-HI delta moving, or a
2030 retrofit cohort shrinking because correctly-rated CCS depresses the price that justified
the next retrofit (D77 §4.3 measured exactly that on NEISO). None of these is a defect; all
are the repair working.

---

## 6. Predictions — pre-declared per ISO, scored as written

Baseline = the committed pre-fix 2030 CO2 level; contamination = each per-ISO FINDING's own
pre-declared figure. **Every prediction is about sign and order of magnitude, never a target.**

| ISO | pre-fix 2030 REF CO2 | pre-declared contamination | **P: 2030 REF level at THE PIN** |
|---|---|---|---|
| NEISO | 13.368 Mt | 5.60 Mt = **41.9 %** | **FALLS**, order **4–8 Mt** (D77's own NEISO A/B measured −6.41 Mt off this exact control) |
| NYISO | 20.894 Mt | 5.29 Mt = **25.3 %** | **FALLS**, order **4–9 Mt** — RGGI is priced, so the dispatch response adds to the accounting correction |
| CAISO | 31.160 Mt | 5.04 Mt = **16.2 %** | **FALLS**, order **3–8 Mt** — CARB priced, same mechanism |
| PJM | 470.455 Mt | 1.98 Mt = **0.42 %** | the **CCS channel falls ~2 Mt**; the **total is not predicted** — D67-ARM and D81 are live here and can move the level by more, in either direction (§1.1 item 3) |
| MISO | 412.634 Mt | ≈1.1 Mt = **0.27 %** | **FALLS**, order **0.5–2 Mt**; carbon is 0, so this is accounting plus a small screen response |

**P-A (the mechanism's sign).** In every re-solved ISO the 2028–2030 `gas_cc_ccs` *emission
rate* falls by exactly 10× at the unit level (G1), and CO2 falls at the ISO level in every
year from 2028. **2026 and 2027 do not move** (G3).

**P-B (where the LOAD-HI delta moves, and where it cancels).** The correction cancels out of
a delta only when both arms carry the same CCS generation. Measured pre-fix CCS TWh at 2030,
REF → LOAD-HI:

| ISO | REF | LOAD-HI | arm gap | **P: does ΔCO2 move?** |
|---|---|---|---|---|
| NEISO | 16.72 | 16.89 | **+0.18** | **barely** — Δ pre-fix 1.408 Mt; predict it moves **< 0.3 Mt**. (The NEISO FINDING §2.3's "≈6.3 % of ΔCO2 rode on defective units" is ~0.09 Mt, inside that band.) |
| NYISO | 24.42 | 30.18 | **+5.75** | **YES, falls** — predict Δ (pre-fix 5.340 Mt) falls by **1–3 Mt** |
| CAISO | 45.16 | 51.85 | **+6.69** | **YES, falls** — predict Δ (pre-fix 10.231 Mt) falls by **1–3 Mt** |
| PJM | 3.50 | 11.62 | **+8.12** | **YES, falls** on the CCS channel — predict the CCS component of Δ (pre-fix 148.62 Mt) falls by **3–6 Mt**; the observed total also carries D67-ARM/D81 and is reported, not predicted |
| MISO | 2.50 | 3.72 | **+1.21** | **YES, small** — predict Δ (pre-fix 72.86 Mt) falls by **0.2–1 Mt** |

**P-C (the retrofit set moves, and mostly grows).** D65-B cuts the capture VOM adder 8.0 →
2.95 $/MWh and scales the fixed-cost legs by the host's captured-CO2 factor, both of which
*improve* the retrofit's screened uplift; D77 works the other way at the margin (cheap abated
CC depresses the price that justifies the next retrofit — D77 §4.3). I predict the **2030
retrofit capacity rises in at least three of the five** re-solved ISOs, and that at least one
falls. This is a prediction about a mechanism I do not control and is the one I most expect
to be wrong.

**P-D (no new invariant FAIL class).** No re-solved leg gains a FAIL ident absent from both
its own pre-fix set and the ISO's other arms. The ISOs at risk of an I3/I7/I12 flip are
**PJM** (D67-ARM moves the adequacy requirement the backstop and the floor test) and, second,
**CAISO/MISO** (already carrying I7+I12; a changed retrofit set moves capacity). NEISO and
NYISO are 14/14 PASS pre-fix and I predict they stay 14/14.

---

## 7. Duties this lane accepts

- **No default moves, no knob moves, no `ScenarioConfig` field added, no new case, no solve
  outside the 13, never a year past 2030.** Every leg is the shipped posture at THE PIN plus
  the committed campaign case. **DOF ledger: ZERO free parameters**; no `authorized_price_tuning`
  (rule 1's carve-out is a backcast offer-curve channel and is untouched by a forecast lane).
- **Consume, never edit:** `configs/scenario_campaign_matrix.yaml`, `scripts/run_ces_leg.py`,
  `scripts/run_full_horizon.py`, `scripts/report_scenario_deltas.py`,
  `scripts/collate_scenario_campaign.py`, `scripts/register_forecast_run.py`,
  `scripts/check_forecast_invariants.py`, everything under `src/`, and every other ISO's or
  lane's files. If a change outside this lane's declared regions (ledger §4) becomes
  necessary, the lane **STOPS and routes to SCN-DESK in its FINDING**.
- **Rule 15 / §7.5:** re-registration is into the **forecast** namespace under the same
  campaign and the SAME run ids. The backcast registry is never touched;
  `program-status.json` and `ff-verdicts.json` are never touched.
- **Rule 26 `[R-DELETE]`:** each re-registration commit **deletes** that ISO's pre-fix slim
  artifacts under `results/scn-campaign-load-2026-09-06/<ISO>/` and replaces the sidecar body
  in the same commit — a stale bundle at a valid key is a re-armable wrong answer. **ERCOT's
  three legs stay exactly as they are.**
- **Invariant declarations in the same commit as each re-registration**
  (`frontend/data/hindcast/invariant-failures.json`), including **deleting** any declared
  ident the re-solve no longer fails. `scripts/check_forecast_invariants.py --sidecar-dir`
  is run before every push and must stay EXIT 0.
- **Rule 27 `[R-PUSH]`:** no existing source file ≥300 lines is rewritten; every push
  touching one is fetch-back verified (line count + hash).
- **Rule 29(c):** no screen bundle and no control bundle is produced — the 13 legs are
  registered campaign arms and the control is the committed pre-fix bundle (§1.3).
- **Rule 28(b):** the `datacenter_load_block` cell of the **five re-solved ISOs'** matrix
  shards is re-stamped with the post-fix evidence as the **last** commit, after rebase; one
  appended line each, no verdict letter moved.
- **Backcast byte-identity: untouched** — forecast-mode only, no default moved by this lane.
- **No CI workflow is created.** Every solve runs in-session.
