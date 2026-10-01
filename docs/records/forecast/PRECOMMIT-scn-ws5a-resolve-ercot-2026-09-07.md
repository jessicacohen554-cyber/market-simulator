# PRECOMMIT — SCN-WS5A-RESOLVE-ERCOT: ERCOT's three load legs re-solved at THE PIN

**Lane** SCN-WS5A-RESOLVE-ERCOT (sub-lane of SCN-WS5A-RESOLVE, executing ruling **S8** for the
three legs it excluded) · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-07 ·
**Branch** `claude/scn-ws5a-resolve-ercot-0jqkt4` · **Data profile** `ercot` (full clone —
`hydrate_data.py --profile ercot` reports every blob already local) ·
**Campaign** `scn-campaign-load-2026-09-06` (unchanged — same ids, same cases, same reference
case `REF`) · **Cases** `REF`, `LOAD-HI`, `LOAD-HI-ORGANIC`, in that order ·
**Parent** `PRECOMMIT-scn-ws5a-resolve-2026-09-06.md` (whose §4 cache recipe and §5 gate form
this lane adopts) · **Trigger** `FINDING-scn-ws5a-policy-ercot-2026-09-06.md` §0 item 2 and §7
item 1 · **Protocol** `SUBLANE-scn-ws5a-policy-ercot-solve-protocol-2026-09-06.md` §1–§3, §6,
substituting these three cases and this out-dir · **Siblings**
`PRECOMMIT-/FINDING-scn-ws5a-resolve-{caiso,miso}-2026-09-06.md`.

**Pushed before the first solve** (rule 29 `[R-SCREEN]`). Every number below is zero-LP: a
resolved config at THE PIN, a committed pre-fix artifact, or arithmetic on the two. Nothing here
is revised after a solve; §5's predictions are scored as written, misses at full magnitude.

---

## 0. THE PIN — inherited, not chosen

```
bdfb3095e9fa0cd2bec3f4e843f320b42588c72b
```

`origin/main` at the parent lane's PRECOMMIT, and the sha the eleven `SCN-WS5A-POLICY-ERCOT`
legs solved at. This lane detaches onto **that sha**, so all fourteen ERCOT legs of both
campaigns finally sit at one base. Verified in this container:
`git merge-base --is-ancestor bdfb3095… origin/main` ⇒ **YES** (`origin/main` = `8a4bfd29` at
write time); `git rev-parse HEAD` = THE PIN with `git status --porcelain` **empty**.

**Disclosed, because it changes how the ancestry claim is evidenced.** The three merge shas the
parent PRECOMMIT §0 cites as required ancestors — `fc583339` (capx D77), `b1f77621`
(capx D65-B), `1cc45bb2` (the load campaign's frozen pin) — **do not resolve in this clone**
(`git rev-parse --verify` fails on all three; so does `20f9ce9f`, the sha the committed ERCOT
REF leg itself records). `git fetch origin main` in this container reported a **forced update**
(`+ b1964e71...8a4bfd29`), i.e. the shas were rewritten out from under the citations, exactly
the failure mode CLAUDE.md's history-rewrite clause names. **This lane does not assert the
ancestry it cannot verify.** It substitutes a *stronger* check, which is a measurement on the
objects that actually decide the solve rather than on commit identity: §1 differences the
**resolved `ScenarioConfig`** at THE PIN against the **committed pre-fix leg's own
`scenario_config`**, field by field, and finds exactly the two D65-B fields moved. A sha is a
label for that change; the field diff *is* the change.

**THE PIN IS NOT MOVED AFTER THE FIRST SOLVE.** Anything landing on `main` after it is recorded
in the FINDING as post-pin, never retro-fitted and never used to re-read a result. Every solve
is wrapped in the HEAD GUARD `[ "$(git rev-parse HEAD)" = "$H0" ] || exit 90`; `git fetch` /
branch switches happen **between** legs, never during one.

## 0.1 Bottom line before any LP

1. **All three ERCOT keys re-key at THE PIN and reproduce the expected values, 3/3** (§2).
   `REF de9c68e19316910e`, `LOAD-HI ec2ea8193e2e45a1`, `LOAD-HI-ORGANIC 0c87f2f2467e95b3` —
   each equal to `PRECOMMIT-scn-ws5a-policy-ercot` §2 / ADDENDUM A(a) and to the parent
   RESOLVE PRECOMMIT §3's ERCOT row. A key that did not reproduce would have been a STOP.
2. **The S8 exclusion premise is falsified at the config level, before any LP.** Ruling S8
   excluded ERCOT's three legs as "CCS-clean at `1cc45bb2`", and the parent PRECOMMIT §0.1
   item 2 wrote *"D77 and D65-B are inert on a fleet that converts nothing; their keys move,
   their answers cannot."* The full `scenario_config` diff (§1) shows **two substantive fields
   move for ERCOT** — `ccs_retrofit_vom_adder` **8.0 → 2.95** and
   `ccs_retrofit_fixed_cost_co2_scaling` **False → True** — both of which are **inputs to the
   retrofit screen**, not to the retrofitted fleet's rating. An input that improves a screen's
   uplift is not inert because the screen's pre-change output was zero; it is inert only if it
   cannot cross the threshold. The eleven policy legs measured that it does: every one converts
   2,764–3,000 MW/yr from 2028 at THE PIN. **This is the LIVE-hunk case of rule 29(b) and the
   control solve is EARNED.**
3. **For ERCOT the LIVE set is exactly {D77, D65-B}** (§1). No PJM-only mechanism reaches it:
   `capacity_market_supply_clearing_by_iso` and `capacity_adequacy_requirement_published_by_iso`
   are `None`, `pjm_accreditation_design_vintage` / `pjm_vre_accreditation_vintage` /
   `retirement_sector_gate` are `False`, on all three cases — so unlike PJM, ERCOT's
   pre-vs-post difference **is** the CCS repair and nothing else.
4. **The default cache is EMPTY — `results/ERCOT/` does not exist on this container** (§3,
   recorded pre-solve). All six keys, pre-fix and PIN, are ABSENT. No pre-fix parquet bundle is
   reachable at any key, moved or not.
5. **0.0 % of ERCOT's pre-fix CO2 is `gas_cc_ccs`** — the committed legs carry `gas_cc_ccs`
   **absent from `generation_by_fuel_mwh` and `capacity_by_fuel_mw` in all five years of all
   three arms** (§3.2). So ERCOT is the campaign's *only* re-solved ISO where the correction
   cannot be an accounting one: whatever moves must move because the **screen** moved. That
   makes ERCOT the cleanest available test of D65-B's dispatch channel, and it is why §5's
   predictions are about the retrofit *set*, not about a re-rating.

---

## 1. The ERCOT LIVE set — measured on this lane's own resolved configs (rule 29(b))

The parent's G-DRIFT is inherited for its window and not rewritten; ADDENDUM A(e) of
`PRECOMMIT-scn-ws5a-policy-ercot` covers `bdfb3095..992760ec` (post-pin drift, which cannot
reach a leg that solves **at** the pin). What this lane owes, and what the S8 exclusion got
wrong, is the *pre*-pin question: **what differs between the committed pre-fix leg and a solve
at THE PIN, for ERCOT.** Answered by diffing the resolved `ScenarioConfig` at THE PIN against
the committed `run_config.json`'s `scenario_config` block for `REF` — every field, not a
selected set:

| field | committed pre-fix leg | at THE PIN | verdict |
|---|---|---|---|
| `ccs_retrofit_vom_adder` | **8.0** | **2.95** | **LIVE** — capx D65-B Act A |
| `ccs_retrofit_fixed_cost_co2_scaling` | **False** | **True** | **LIVE** — capx D65-B Act B |
| `ccs_retrofit_capex_co2_scaling` | True | True | inert (already armed pre-fix, capx D50) |
| `ccs_retrofit_capex_kw` / `_hr_penalty` / `_max_gw_per_year` / `_min_remaining_life` | 1521.4 / 0.12 / 3.0 / 15 | identical | inert |
| `ccs_retrofit_capture_rate` / `_available_year` | 0.9 / 2028 | identical | inert |
| `capacity_market_supply_clearing_by_iso` | None | None | inert — PJM-only (capx D57) |
| `capacity_adequacy_requirement_published_by_iso` | None | None | inert — PJM-only (capx D67) |
| `pjm_accreditation_design_vintage` / `pjm_vre_accreditation_vintage` | False / *(absent)* | False / False | inert — PJM-only (D48 / D75-R) |
| `retirement_sector_gate` | False | False | inert — PJM/MISO-armed (D53 / D78) |
| `fossil_announced_exits_enabled` / `confirmed_exits_enabled` / `forecast_fossil_retirement_economic` | True / True / True | identical | inert (unchanged) |
| `capacity_deliverability_limits` / `reserve_margin_build_enabled` | False / None | identical | inert |
| **every other shared field** | — | — | **identical** |

The complete diff is **five** entries, of which three are a serialization form change
(`caiso_/ercot_/miso_/neiso_/pjm_offer_surface_netload_pcts` and
`miso_offer_surface_position_bins`: JSON `list` → Python `tuple`, same values) and two are the
D65-B pair above. **Twelve fields exist at THE PIN and not in the pre-fix config**
(`capacity_no_default_cap_convention_by_iso`, `capacity_screen_peak_measured_hindcast`,
`mass_cap_tons_by_year`, `miso_gas_marginal_commodity_pricing`, `miso_gas_variable_transport`,
`miso_seam_neighbour_anchored_ladder`, `nyiso_ct_peaker_bands_measured`,
`nyiso_gas_bridge_startup_aware`, `pjm_vre_accreditation_vintage`,
`voluntary_clean_demand_path`, `voluntary_eligible_fuels`,
`voluntary_wtp_ceiling_usd_per_mwh`) — **every one measured `False` / `None` / `"off"` on all
three cases**, i.e. new fields at their default-off value, arming nothing. **No field exists
pre-fix and not at THE PIN.**

**D77 is a code change, not a config one** (`model/capacity_evolution/ccs.py`: the retrofitted
host's persisted `emission_rate_co2` and the per-year CAMPD re-derivation seam), so it does not
appear in this table and is carried as LIVE on the parent's audit. It is scored empirically by
gate **G5** below rather than argued.

**Conclusion.** For ERCOT the LIVE set is **{D77, D65-B}**, exactly CAISO's and MISO's, and
**not** the empty set S8 assumed. Form 4 (differencing against the committed keeper/leg) is
**invalid from 2028** for these legs and the control solve is earned; it remains valid for
2026–2027, where `apply_ccs_retrofit` returns at `if year < ccs_retrofit_available_year`
(2028) — which gate **G1** turns into a measurement rather than an argument.

---

## 2. Phase 0 (zero LP) — the three keys, reproduced at THE PIN

Resolved exactly as `runner.run_scenario_iso` does: `matrix_configs(base, sweep)` →
`resolve_policy_bundle` → `set_caiso_fsno_partition(False)` → `apply_iso_scenario_defaults` →
`.cache_key()`. A naive `config.cache_key()` in a fresh process does **not** reproduce the
solve's key, so the whole chain is walked (protocol §6 `rekey.py`, run at
`HEAD = bdfb3095e9fa0cd2bec3f4e843f320b42588c72b`).

| case | pre-fix key (committed `run_config.json`) | key at THE PIN | expected (policy §2 / parent §3) | verdict |
|---|---|---|---|---|
| REF | `6e40769352a572ba` | **`de9c68e19316910e`** | `de9c68e19316910e` | **MATCH** |
| LOAD-HI | `31cf71afda5c610d` | **`ec2ea8193e2e45a1`** | `ec2ea8193e2e45a1` | **MATCH** |
| LOAD-HI-ORGANIC | `c5255cea87fbaacf` | **`0c87f2f2467e95b3`** | `0c87f2f2467e95b3` | **MATCH** |

**3/3 MATCH.** All three keys move, for the reason capx D65-B's epoch entry states:
`ccs_retrofit_vom_adder` is not a `_CACHE_KEY_OPTIONAL_FIELDS` member and re-keys
unconditionally. The cache blocker the STATUS doc named is therefore defeated by construction,
and that is a measurement, not an assumption.

Resolved case fields, measured on all three legs:

| field | REF | LOAD-HI | LOAD-HI-ORGANIC |
|---|---|---|---|
| `demand_growth_path` | mid | **high** | **high** |
| `datacenter_load_path` | mid | **high** | mid |
| `electrification_path` | off | off | off |
| `carbon_price_path` | zero | zero | zero |
| `federal_ces_enabled` | False | False | False |
| `voluntary_clean_demand_path` | off | off | off |
| `mass_cap_enabled` | False | False | False |
| `ccs_retrofit_vom_adder` | **2.95** | 2.95 | 2.95 |
| `ccs_retrofit_fixed_cost_co2_scaling` | **True** | True | True |
| `ccs_retrofit_capex_co2_scaling` | True | True | True |
| `ccs_retrofit_capture_rate` / `_available_year` | 0.9 / 2028 | idem | idem |
| `mode` / `start_year` / `end_year` | forecast / 2026 / 2030 | idem | idem |

`LOAD-HI-ORGANIC` is `LOAD-HI` with the data-centre axis held at `mid` — the shape-vs-volume
pair the load synthesis's headline rests on. ERCOT prices carbon at **zero** on every leg, which
matters for §5: unlike CAISO, ERCOT has no carbon channel to amplify a CCS re-rating, so any
2028+ movement here is the **screen** and the **merit order**, nothing else.

---

## 3. The cache recipe, the pre-solve state, and the pre-fix baseline

**Three independent isolations, each provable** (parent §4, adopted verbatim):

1. **A NEW out-dir per leg** — `results/scn-campaign-load-2026-09-06-r2/ERCOT/<CASE>/`. Nothing
   is ever written into the pre-fix tree, so a mis-step cannot overwrite the control being
   differenced against.
2. **THE KEY ITSELF MOVED** (§2) — a post-pin solve computes a key no pre-fix bundle occupies,
   so a stale bundle is unreachable even from a warm cache.
3. **THE DEFAULT CACHE IS EMPTY** — `results/ERCOT/` **does not exist** on this container
   (`ls: cannot access 'results/ERCOT': No such file or directory`, recorded pre-solve, gate
   **G2(a)**). All six keys — `de9c68e19316910e`, `ec2ea8193e2e45a1`, `0c87f2f2467e95b3` and
   the three pre-fix keys — recorded **ABSENT** individually. The tree is gitignored and this
   container was cloned fresh, so only the committed slim artifacts are present.

**NEVER used:** the WS-4c harness helper that links arm bundles into the shared cache root. No
pre-fix bundle is linked, copied or moved into any cache root at any point.

**Precondition executed:** `data/clean` is DERIVED and gitignored, so a fresh container has none
and `run_scenario_iso` hard-fails on the confirmed-retirements clean partition.
`PYTHONPATH=. uv run python scripts/regenerate_clean.py` was started **before** this PRECOMMIT
was written and must complete before the first solve.

### 3.1 Driver — `run_ces_leg.py`, per leg, one at a time

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  uv run python scripts/run_ces_leg.py \
    --config configs/scenarios/ercot_scenario_base_2026_2030.yaml \
    --matrix configs/scenario_campaign_matrix.yaml \
    --case <REF|LOAD-HI|LOAD-HI-ORGANIC> --campaign scn-campaign-load-2026-09-06 \
    --out-dir results/scn-campaign-load-2026-09-06-r2/ERCOT/<CASE>
```

Exactly the driver the load lane and the eleven policy legs used; `run_ces_leg.py` is unchanged
in the window, so the driver is not a variable. `run_full_horizon.py` is **not** substituted —
its `--out-dir` cache redirect is real but unreachable from a campaign leg
(`run_ces_leg.run_leg` hard-codes `redirect_cache=False`), and driving through it would build
each config from `reference_config()` instead of the campaign base YAML expanded through
`matrix_configs`: a config-divergence risk under a **same-id re-registration** whose whole point
is that the case is unchanged. Logs go to the session scratchpad, never into the results tree,
so no `.gitignore` change is owed. Legs run **one at a time**, years sequential inside each
(rule 12 `[R-PARALLEL]`); nothing else solves on this box. Budget from the committed pre-fix
legs (457.6 / 372.5 / 343.2 s, peak RSS 4.20 / 3.88 / 3.53 GB) and the eleven policy legs at
THE PIN (~6.5–7 min/leg, ~4.2 GB): **~20–30 min of LP for 15 solve-years**, well inside the
container's 15 GB.

### 3.2 The pre-fix baseline this lane differences against — committed, `dirty=false`

`REF` at sha `20f9ce9f`; `LOAD-HI` and `LOAD-HI-ORGANIC` at `73c109cb` (both unresolvable in
this clone, §0 — the artifacts themselves are the record).

| case | year | CO2 Mt | lw $/MWh | gen TWh | unserved TWh | curt TWh | clean share | `gas_cc_ccs` TWh | `gas_cc_ccs` MW |
|---|---|---|---|---|---|---|---|---|---|
| REF | 2026 | 214.3926 | 91.037 | 597.138 | 0.3816 | 4.3337 | 0.3953 | **0.000** | **0.0** |
| REF | 2027 | 255.9732 | 982.313 | 674.266 | 4.6218 | 4.9079 | 0.3519 | **0.000** | **0.0** |
| REF | 2028 | 285.6966 | 3215.987 | 728.366 | 41.3892 | 4.9079 | 0.3257 | **0.000** | **0.0** |
| REF | 2029 | 305.1914 | 3846.002 | 796.427 | 76.3864 | 4.9079 | 0.3246 | **0.000** | **0.0** |
| REF | **2030** | **328.8742** | 4437.529 | 862.526 | 127.2204 | 4.9194 | 0.3172 | **0.000** | **0.0** |
| LOAD-HI | 2026 | 256.0182 | 769.484 | 673.090 | 2.6565 | 4.3337 | 0.3507 | 0.000 | 0.0 |
| LOAD-HI | 2027 | 298.7734 | 4039.415 | 742.300 | 71.3224 | 4.9079 | 0.3196 | 0.000 | 0.0 |
| LOAD-HI | 2028 | 301.5261 | 4990.954 | 751.341 | 227.7885 | 4.9079 | 0.3158 | 0.000 | 0.0 |
| LOAD-HI | 2029 | 321.8841 | 4998.435 | 819.947 | 360.9840 | 4.9079 | 0.3102 | 0.000 | 0.0 |
| LOAD-HI | **2030** | **342.2814** | 4999.549 | 885.504 | 538.8695 | 4.9079 | 0.3071 | 0.000 | 0.0 |
| ORGANIC | 2026 | 255.2594 | 1134.070 | 670.104 | 5.8733 | 4.3337 | 0.3522 | 0.000 | 0.0 |
| ORGANIC | 2027 | 294.8318 | 3855.498 | 736.413 | 77.4506 | 4.9079 | 0.3222 | 0.000 | 0.0 |
| ORGANIC | 2028 | 301.5756 | 4973.122 | 751.439 | 227.7751 | 4.9079 | 0.3157 | 0.000 | 0.0 |
| ORGANIC | 2029 | 321.9044 | 4999.756 | 819.987 | 360.9301 | 4.9079 | 0.3102 | 0.000 | 0.0 |
| ORGANIC | **2030** | **342.2844** | 4999.994 | 885.510 | 538.8587 | 4.9079 | 0.3071 | 0.000 | 0.0 |

Pre-fix **ΔCO2 (LOAD-HI − REF)**: 2026 **+41.6256** · 2027 **+42.8002** · 2028 **+15.8295** ·
2029 **+16.6927** · 2030 **+13.4072** Mt.
Pre-fix **DC-shape gap (ORGANIC − LOAD-HI)**: 2026 **−0.7588** · 2027 **−3.9416** ·
2028 **+0.0495** · 2029 **+0.0203** · 2030 **+0.0030** Mt.

Pre-fix invariant sets, read from the committed sidecars on `origin/main`
(`frontend/data/hindcast/ercot-2026-2030-scn-campaign-load-2026-09-06-{ref,load-hi,load-hi-organic}.json`):
**FAIL `{I3, I12}` on all three arms**; **WARN `{I13, I14}` on `REF`** and **`{I14}` on both
load arms**. All three are declared in `invariant-failures.json` as exactly `["I12", "I3"]`, and
the checker is EXIT 0 on `main` today. (The policy FINDING §1.1 records the same REF set, and
notes that an arm losing the `I13` WARN is not a flip.)

**The line that makes this lane different from CAISO's and MISO's.** `gas_cc_ccs` is **absent
from every fuel dict in every year of every arm** pre-fix — not zero-valued, absent. There is no
mis-rated stock to correct. So ERCOT's post-fix movement, whatever its size, is **entirely** a
changed retrofit *decision* plus its dispatch consequences; none of it is the accounting half
that dominates PJM's and part of CAISO's.

---

## 4. STOP gates — structural, kill-only, never gated on a residual

Pre-registered here, before the first solve. A gate PASS means only *"the mechanism did what its
own arithmetic says"*; it promotes nothing and contributes to no determination (rules 1
`[R-STRUCT]`, 29 `[R-SCREEN]`). **G1–G4 are the four the sub-lane charter names; G5 is added by
this lane** because ruling S5's model-grain identity is readable at zero LP from the evolution
ledger and refusing a free check would be a worse defect than running one.

| # | gate | STOP condition |
|---|---|---|
| **G1** | **PRE-2028 BYTE-IDENTITY.** For each leg, **2026 and 2027** are identical to that leg's committed pre-fix bundle on `co2_mt`, `lw_price` and **every** entry of `generation_by_fuel_mwh`, to **1e-6** relative. The D65-B seam is inert below `ccs_retrofit_available_year` = 2028 (`apply_ccs_retrofit` returns early), so **any 2026–27 drift is a real finding, not a tolerance** | any 2026/2027 row moves beyond 1e-6 |
| **G2** | **CACHE-HIT PROOF**, per leg, all five (parent §4.2 a–e): (a) `results/ERCOT/<PIN key>/` did not exist before the solve — **recorded, §3**; (b) `run_config.json` `cache_key` equals the §2 PIN key; (c) `git.sha` is THE PIN, or a descendant with a **zero** solve-path diff (this lane commits while later legs solve — the parent's stated convention), and `git.dirty == false`; (d) `total_wall_s` is a solve's, not a cache read's, with per-year `wall_s` for all five years; (e) the leg does not reproduce the pre-fix 2028–2030 CO2 trajectory | any leg failing a–e. **A leg reproducing the pre-fix bundle to the digit is a CACHE HIT and a STOP** — reported, never registered |
| **G3** | **THE CONVERSION QUESTION — a REPORTING gate, and the point of the lane.** If the pin `REF` converts CCS from 2028: record converted **MW and TWh per year** beside the eleven policy legs' **2,932–2,996 MW** (`FINDING-scn-ws5a-policy-ercot` §4). If it does **NOT** convert: **say so at full magnitude** — it means the policy legs' conversion IS a policy response and this lane's own §0.1 item 2 reading, and the policy FINDING's contamination reading, are **WRONG**. Not a STOP in either direction; a STOP would let the lane's prior pick the answer | — (reported, never a kill) |
| **G4** | **NO COLLATERAL FLIP.** No non-target load-bearing invariant flips PASS → FAIL versus the leg's own committed pre-fix sidecar (pre-fix FAIL `{I3, I12}` on all three) | a flip whose cause is **not** re-ordered dispatch. A flip **caused by** re-ordered dispatch (I3 / I7 / I12) is **REPORTED WITH ITS CAUSE NAMED**, not a STOP |
| **G5** | **IDENTITY (added).** Ruling S5's paired check at model grain / capx D77 §4b gate 1: for **every** retrofitted unit-year in every leg, the LP's persisted `FleetContext.emission_rate` equals the evolution ledger's recorded `old_emission_rate × (1 − 0.90)` to rel. tol **1e-9**, and the unit's `fuel_type` is `gas_cc_ccs`. Zero LP — `evolution_<year>.json`'s `ccs_retrofits` rows zipped with `read_fleet_context(...)`. **Vacuous-true if nothing converts**, and reported as vacuous rather than as a PASS | any converted unit off the identity |

**Explicitly NOT a STOP**, pre-declared: the retrofit **set** appearing where there was none, its
capacity or membership moving in either direction, the merit order re-ordering, CO2 falling or
rising by any magnitude, unserved energy rising, the LOAD-HI delta moving, or the DC-shape gap
moving. All of these are the repair working, and ERCOT's is the case where the set moving from
**empty** is the expected outcome.

**What G1 can and cannot claim, stated honestly.** A **per-unit** pre-vs-post diff is **NOT
computable**: `results/ERCOT/` is gitignored and the pre-fix parquets were never materialized on
this container, so the committed pre-fix record is slim (`full_horizon_summary.json` +
`run_config.json`) plus the report CSVs. G1 is therefore an **ISO-aggregate, all-fuel** identity
over two years, not a unit-level one — a real and sufficient confinement check for a seam that is
year-gated, and weaker than a unit diff would be. It is recorded as what it is.

---

## 5. Predictions — pre-declared, scored as written, misses at full magnitude

The charter's two are taken verbatim and not restated more favourably; P-C…P-F are this lane's.

**P-A (the pin REF converts, at the cap).** The re-solved `REF` converts **~2,900–3,000 MW in
2028** — the `ccs_retrofit_max_gw_per_year` = 3.0 GW/ISO/yr cap binding, as it does in all
eleven policy legs (2,932–2,996 MW). The pin `LOAD-HI` likewise.

**P-B (the adequacy cost of the capture derate).** 2029 and 2030 **unserved energy RISES** by
roughly **+2.3 / +2.9 TWh** in `REF` — the capture parasitic derate on the ~5.9 / ~8.9 GW of
cumulative converted CC, the magnitude the policy legs' carbon arms measured against the
contaminated REF (`FINDING-scn-ws5a-policy-ercot` §2.1). If the pin REF converts the same
~3 GW/yr, that derate is already **inside** REF and the policy arms' +2.28 / +2.89 TWh should
**collapse toward zero** — which is the whole reason the delta was declared non-campaign-grade.

**P-C (CO2 falls, and by less than CAISO's or NEISO's share).** `REF` 2030 CO2 **FALLS** from
**328.874 Mt** by order **5–20 Mt** (1.5–6 %). ERCOT prices carbon at **$0**, so there is no
carbon channel: the fall is abated gas displacing unabated gas and coal on the merit order,
plus the ~90 % rating on the converted block itself. Explicitly **not** predicted to reach
NEISO's −54 % or NYISO's −48 %; ERCOT's converted block is ~9 GW against a 78 GW thermal fleet
and a 128 TWh shortage.

**P-D (2026–2027 do not move at all).** G1 holds on all three legs, all fuels, both years.

**P-E (no new FAIL class).** No re-solved leg gains an invariant ident absent from its own
pre-fix set `{I3, I12}`. **Risk named in advance:** ERCOT's REF sheds 41–127 TWh and LOAD-HI
228–539 TWh, so `I3` is already failing in every arm and a changed unserved level cannot add a
class there; `I7` (reliability floor) is the one that could newly fail if the derate pushes the
margin through a band edge, and it would be a **reported** dispatch-caused flip, not a STOP.

**P-F (the one I most expect to be wrong).** The **LOAD-HI ΔCO2** at 2030 (pre-fix
**+13.4072 Mt**) — I make **no directional prediction**. Both arms convert at the same annual
cap, so the correction may cancel almost exactly out of the delta (unlike NEISO, where the arms'
cohorts diverged and the delta collapsed 82 %); but LOAD-HI's fleet is larger and its shortage
four times deeper, so the *marginal* retrofit's economics differ. Reported at whatever it lands.
Likewise the **DC-shape gap** (pre-fix +0.0030 Mt at 2030): reported, not predicted — the load
synthesis's §1.1 headline is checked against it in the FINDING, not defended.

---

## 6. Duties this lane accepts

- **No default moves, no knob moves, no `ScenarioConfig` field added, no new case, no solve
  outside these three, never a year past 2030, and never a re-solve of a policy leg.**
  **DOF ledger: ZERO free parameters**; no `authorized_price_tuning` (rule 1's carve-out is a
  backcast offer-curve channel, untouched by a forecast lane).
- **Consume, never edit:** everything under `src/`, `scripts/`, `configs/`, `data/`, and every
  other ISO's files. **Not touched:** any other lane's PRECOMMIT/FINDING, the policy lane's
  `results/scn-campaign-policy-2026-09-06/` tree, the backcast registry,
  `program-status.json`, `ff-verdicts.json`, and any ISO's files but ERCOT's. A needed change
  outside these regions is a **STOP** routed to SCN-DESK in the FINDING — including the policy
  FINDING's owed **ADDENDUM B** (re-differencing the eleven committed policy legs against this
  lane's REF), which is the parent lane's or a follow-up's and is **not executed here**.
- **Rule 15 `[R-DASHBOARD]` / forecast plan §7.5:** re-registration is into the **forecast**
  namespace under the same campaign and the **SAME run ids**
  (`ercot-2026-2030-scn-campaign-load-2026-09-06-{ref,load-hi,load-hi-organic}`) — only the
  sidecar's `git_sha`, key provenance, out-dir and trajectory change. The backcast registry is
  never touched.
- **Rule 26 `[R-DELETE]`:** each re-registration commit **deletes** that case's pre-fix slim
  artifacts under `results/scn-campaign-load-2026-09-06/ERCOT/<CASE>/` in the same commit — a
  stale bundle at a dead key is a re-armable wrong answer, and git history is the record. The
  campaign-root **`bundle/` and `report/` pair is REBUILT in place** from the three post-fix
  caches (the convention MISO/NEISO/NYISO/PJM followed, so a reader at the campaign root still
  finds ERCOT), while the **leg** artifacts live under the charter-mandated `-r2` out-dir.
- **Invariant declarations in the same commit as each re-registration**
  (`frontend/data/hindcast/invariant-failures.json`), including **deleting** any declared ident
  the re-solve no longer fails. Only ERCOT's keys are touched; rebase before each push.
  `scripts/check_forecast_invariants.py --sidecar-dir frontend/data/hindcast` must be **EXIT 0**
  before every push — it is EXIT 0 on `main` today and must stay so.
- **Rule 27 `[R-PUSH]`:** no existing source file ≥300 lines is rewritten; every push touching
  one is fetch-back verified (line count + hash). Transport by pack size; run payloads are not
  produced by a forecast registration, so `push_files` and a small-pack `git push` are both
  available.
- **Rule 29(c)** does not apply: these are **registered campaign arms**, not screen or control
  bundles — nothing to delete before merge.
- **Rule 28 `[R-MECH-MATRIX]`:** no new mechanism is proposed or tested; the FINDING states
  whether ERCOT's `ccs_retrofit`-family cell needs a stamp and does it in-session if so.
- **Ledger/plan:** the SCN-DESK ledger §1 RESOLVE row and the load synthesis's pin table are
  updated to record that ERCOT now sits at THE PIN. No other lane's region is touched.
- **Backcast byte-identity: untouched** — forecast-mode only, no default moved by this lane.
- **No CI workflow is created.** Every solve runs in-session (CLAUDE.md, GitHub Actions).
- **No PR is opened.**
