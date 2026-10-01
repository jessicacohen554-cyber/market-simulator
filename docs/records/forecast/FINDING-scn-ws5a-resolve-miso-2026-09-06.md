# FINDING — SCN-WS5A-RESOLVE-MISO: ruling S8 executed on MISO, three legs, every gate PASS

**Lane** SCN-WS5A-RESOLVE-MISO · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-06 ·
**Branch** `claude/scn-ws5a-resolve-miso-0s8zln` · **THE PIN**
`bdfb3095e9fa0cd2bec3f4e843f320b42588c72b` · **Data profile** `miso` ·
**Campaign** `scn-campaign-load-2026-09-06` (unchanged — same three run ids, same cases, same
reference case) · **PRECOMMIT** `PRECOMMIT-scn-ws5a-resolve-miso-2026-09-06.md`, pushed at
`95ad76d4` **before the first solve** · **Inherited charter**
`PRECOMMIT-scn-ws5a-resolve-2026-09-06.md` (parent lane: NEISO/NYISO/PJM).

---

## 0. Bottom line

1. **All three legs re-solved fresh at the PIN keys, all five gates PASS on all three, zero
   STOPs.** No leg came within reach of a pre-fix bundle: `results/MISO/` did not exist before
   the first solve and each leg created exactly its own PIN-key directory.
2. **The identity holds exactly.** Over every retrofitted unit-year in every leg the LP's
   `emission_rate_co2` equals the host's measured pre-conversion CAMPD rate × (1 − 0.90) with
   **max relative deviation 0.000e+00** — not "within 1e-9", but bit-equal — and every one
   carries `fuel_type = gas_cc_ccs`.
3. **MISO's 2030 REF CO2 falls 412.6343 → 410.2013 Mt (−2.4330), and my pre-declared 0.5–2 Mt
   band is a MISS.** It misses high, by 0.43 Mt, through the exact mechanism the PRECOMMIT named
   as the one most likely to break it: **the retrofit set grew** (334.5 → 618.1 MW at 2030, and
   2028 now converts where the pre-fix run converted nothing) because D65-B cut the capture VOM
   adder 8.0 → 2.95 $/MWh. Scored as a miss at full magnitude; a moving retrofit set is
   pre-declared NOT a STOP.
4. **The desk's ≈1.1 Mt contamination estimate for MISO was ~2.2× too small** — the real figure
   is 2.43 Mt, 0.59 % of the 2030 level rather than 0.27 %. The estimate was right about the
   accounting term and could not have known about the coupled D65-B re-key, which contributes
   nearly half (§3.1). This does not change the qualitative call: MISO's levels were tolerably
   stale, and are now repaired.
5. **The LOAD-HI delta moves, and by the predicted amount.** ΔCO2 falls 72.8621 → **72.4163 Mt**
   (−0.4458), inside the pre-declared 0.2–1 Mt band, because the two arms carry unequal CCS
   generation and the correction therefore does not cancel.
6. **2026 and 2027 do not move at all**, in any arm, for any fuel — 10/10 fuel rows identical to
   the committed pre-fix control, to the digit. That is the D77+D65-B confinement to 2028+
   measured rather than argued.

---

## 1. THE PIN and the LIVE-set verification

THE PIN was quoted, not chosen: `git checkout -B claude/scn-ws5a-resolve-miso-0s8zln bdfb3095…`,
tree clean. **It was never moved.** `origin/main` advanced 198 commits during this session with a
live solve-path diff (18 files, +1,812 / −59); the lane did not rebase onto it, because the point
of the pin is that all 16 campaign legs share one base and a rebase would void the inherited
G-DRIFT audit. Post-pin `main` is recorded here and used for nothing.

The parent lane's G-DRIFT audit (`1cc45bb2..bdfb3095`) is inherited, and its shape re-confirmed
locally: **41 files, +5,362 / −433**. `scripts/run_ces_leg.py` and
`configs/scenarios/miso_scenario_base_2026_2030.yaml` are **0 lines changed** in the window, so
the driver and the case are not variables.

**Every classification that could break for MISO was re-checked on this lane's own resolved
configs, not inherited:**

| mechanism | arming condition | MISO resolved | verdict |
|---|---|---|---|
| capx **D77** | any converted unit | cohort non-empty from 2028 | **LIVE** |
| capx **D65-B** | `ccs_retrofit_vom_adder` / `_fixed_cost_co2_scaling` | **2.95** / **True** | **LIVE** |
| capx **D67-ARM** | `capacity_adequacy_requirement_published_by_iso` | **`None`** | INERT |
| capx **D78** | `retirement_sector_gate=True` **AND** clearing-armed | **`True`** / clearing **`None`** | INERT |
| capx **D81** | forecast AND clearing-armed AND `fossil_announced_exits_enabled` | forecast ✓ / clearing **`None`** / `True` | INERT |

**D78 is the one that could have broken, and it does not.** MISO is the only campaign ISO
satisfying D78's *first* arming condition — `retirement_sector_gate = True`, arriving through
`iso_configs.py:1100`'s `default_scenario_overrides`. Its second condition is a clearing-armed
ISO and MISO's clearing resolves `None`. The inertness is **asserted by test**, not argued:
`tests/unit/model/test_capacity.py:7250`
(`test_exit_exempt_is_byte_identical_to_exempt_when_the_clearing_is_off`, capx D78 T2) names
"MISO's armed keeper posture" explicitly and asserts the entire screen output — pipeline rows,
retired, `floor_retained`, state, survivors — identical under both decision rules. The cache
epoch entry ("Epoch 2026-09-06d") reaches it from the other side. D81's own epoch entry scopes
its blast radius to "forecast mode on an ISO whose `capacity_market_supply_clearing_by_iso` row
is on (PJM alone at this date)".

**The three MISO fields the window added are OFF and inert by construction:**
`miso_gas_marginal_commodity_pricing` (`apply_miso_gas_marginal_commodity` returns `None` at its
first statement, `basis/miso.py:482`; `resolve_fuel_prices` then takes the incumbent
`apply_miso_winter_citygate_daily` branch verbatim, `fuel/resolve.py:228–230`);
`miso_gas_variable_transport` (read only inside the armed branch); and
`miso_seam_neighbour_anchored_ladder` (`interchange/miso.py:305`: "byte-identical when
`False`"). `data/raw/reference/miso_ct_netload_drag.json` has **no consumer under
`src/market_sim/`**.

**Verdict: MISO's pre-vs-post difference is the CCS repair (D77 + D65-B) and nothing else.**

---

## 2. G1 identity, G2 confinement, G3 pre-2028 inertness

### 2.1 G1 — the identity table, per year, per leg

Read at zero LP from the committed artifacts: the cumulative cohort and each host's
`old_emission_rate` from `results/MISO/<key>/evolution_<year>.json`'s `ccs_retrofits` rows
(capx D65-B-R step 0 persists them); the LP's own per-unit rate from
`results.outputs.read_fleet_context(...)` → `emission_rate` zipped with `unit_ids` / `fuel_types`.

| leg | year | cumulative cohort | units checked in fleet | **max rel dev** | wrong `fuel_type` |
|---|---|---|---|---|---|
| REF | 2026 | 0 | 0 | *(empty — valid, not vacuous)* | 0 |
| REF | 2027 | 0 | 0 | *(empty)* | 0 |
| REF | 2028 | 1 | 1 | **0.000e+00** | 0 |
| REF | 2029 | 3 | 3 | **0.000e+00** | 0 |
| REF | 2030 | 3 | 3 | **0.000e+00** | 0 |
| LOAD-HI | 2028 / 2029 / 2030 | 1 / 4 / 4 | 1 / 4 / 4 | **0.000e+00** | 0 |
| ORGANIC | 2028 / 2029 / 2030 | 1 / 4 / 4 | 1 / 4 / 4 | **0.000e+00** | 0 |

**2026–2028 is stated honestly.** The PRECOMMIT pre-declared that MISO's *pre-fix* cohort is
empty until 2029, so an empty 2026–2028 identity table would be valid but not evidence. In the
event the repair **opens 2028** (the D65-B effect), so 2026–2027 are empty-but-valid and 2028 is
a real one-unit check. Nothing here is reported as a vacuous PASS.

**The cohort is two physical hosts, split into offer tranches:**

| unit | zone | MW | host measured rate | × 0.10 | LP rate measured |
|---|---|---|---|---|---|
| `CC_REGULAR_MISO-Plains_p7985_econ` | MISO-Plains | 334.5 | 0.5761275284750648 | 0.05761275 | **0.057613** |
| `CC_REGULAR_MISO-Plains_p7985_committed` | MISO-Plains | 134.0 | 0.5761275284750648 | 0.05761275 | **0.057613** |
| `CC_REGULAR_MISO-Indiana_p1007_econ` | MISO-Indiana | 149.7 | 0.578016901556924 | 0.05780169 | **0.057802** |
| `CC_REGULAR_MISO-Indiana_p1007_committed` *(load arms only)* | MISO-Indiana | 103.8 | 0.578016901556924 | 0.05780169 | **0.057802** |

**G5(e) is the same fact read from the other end:** across all converted units in 2029 and 2030
the LP rate spans **0.057613–0.057802** in every leg — an order of magnitude below the
uncaptured host rate, and nowhere near the ~0.37 signature of the pre-fix defect.

### 2.2 G2 — confinement, and the limit stated plainly

**(a) PASS, all three legs, every year: 0 non-cohort units moved their `emission_rate`** from
their own 2026 value.

**(b) PASS, all three legs: 2026 and 2027 generation-by-fuel identical to the committed pre-fix
bundle for EVERY fuel** — 10 fuels compared per year, 0 differing by more than 1 MWh; CO2 and
load-weighted price identical to 4 dp (REF 2026 368.535300 / $44.5990; REF 2027 371.172700 /
$53.7870).

**The limit, stated rather than dressed up: a per-unit diff against the pre-fix bundle is NOT
computable.** `results/<ISO>/` is gitignored and the pre-fix parquets were never materialized on
this fresh container, so the committed pre-fix record is slim (`full_horizon_summary.json` +
`run_config.json`) and carries no per-unit rates. G2(a) tests confinement *within* the post-fix
bundle against its own 2026 baseline; G2(b) tests the whole 2026/2027 fuel vector against the
committed control. Together they are **weaker than a per-unit diff and stronger than G3 alone** —
that is the honest description, and it is the available substance rather than a restatement of G3.

### 2.3 G3 — pre-2028 inertness, measured

Zero-carbon generation identical to the pre-fix control to 6 dp in 2026 **and** 2027, in all
three legs: nuclear **90.198884**, hydro **9.292516**, wind **94.368276**, solar **9.200799** TWh.
`apply_ccs_retrofit` returns at `year < ccs_retrofit_available_year` = 2028; this is the
empirical confirmation that **both** D77 and D65-B are confined to 2028+.

---

## 3. Levels and deltas, pre vs post

### 3.1 The 2030 REF level, and where the fall comes from

| year | CO2 pre | CO2 post | Δ | CCS TWh pre → post | CCS MW pre → post | LW $ pre → post |
|---|---|---|---|---|---|---|
| 2026 | 368.5353 | 368.5353 | **+0.0000** | 0.0000 → 0.0000 | 0.0 → 0.0 | 44.60 → 44.60 |
| 2027 | 371.1727 | 371.1727 | **+0.0000** | 0.0000 → 0.0000 | 0.0 → 0.0 | 53.79 → 53.79 |
| 2028 | 382.4341 | 381.2997 | **−1.1344** | 0.0000 → 2.1476 | **0.0 → 334.5** | 91.94 → 91.97 |
| 2029 | 390.0939 | 387.9419 | **−2.1520** | 2.0175 → 4.1227 | 334.5 → 618.1 | 90.71 → 90.73 |
| 2030 | **412.6343** | **410.2013** | **−2.4330** | 2.5047 → 4.6908 | 334.5 → 618.1 | 206.36 → 206.36 |

**The fall decomposes into two terms and the arithmetic closes to 0.0012 Mt.** At 2030 REF, with
the cap-weighted host rate 0.576585 t/MWh:

| term | quantity | Mt |
|---|---|---|
| re-rate the 2.5047 TWh that was **already** CCS and mis-booked at the host rate | 2.5047 × 0.576585 × 0.9 | **1.2998** |
| the enlarged cohort: +2.1861 TWh swapped out of unabated `gas_cc` into CCS | 2.1861 × (0.576585 − 0.0576585) | **1.1344** |
| **sum** | | **2.4342** |
| **measured** | | **2.4330** |
| residual | | **−0.0012** (0.05 %) |

So **the accounting correction is 53 % of the move and the enlarged retrofit set is 47 %** — which
is exactly why the desk's ≈1.1 Mt estimate (an accounting-only figure, and on the smaller pre-fix
cohort) undershot.

**The merit order barely moves, as predicted, and the by-fuel table proves it.** 2030 REF:
`gas_cc` 277.5006 → 275.3173 TWh (−2.1833) against `gas_cc_ccs` 2.5047 → 4.6908 (+2.1861) — a
**one-for-one swap to 0.003 TWh**. Coal is **identical** at 220.4139 TWh; nuclear, hydro, wind,
solar, oil identical; biomass +0.0001, `gas_ct` −0.0049, `gas_st` +0.0016. Load-weighted price is
unmoved to 2 dp in every year. With `carbon_price_path = "zero"` a mis-rated `emission_rate_co2`
reaches marginal cost only through the carbon adder, so the repair is an accounting correction
plus a retrofit-screen response — not a dispatch re-ordering. That is MISO's signature and it is
the opposite of NEISO's.

### 3.2 The LOAD-HI delta

| | pre-fix | post-fix | move |
|---|---|---|---|
| LOAD-HI 2030 CO2 | 485.4964 | 482.6176 | −2.8788 |
| REF 2030 CO2 | 412.6343 | 410.2013 | −2.4330 |
| **ΔCO2 (LOAD-HI − REF)** | **72.8621** | **72.4163** | **−0.4458** |

**Inside the pre-declared 0.2–1 Mt band.** It moves because the arms carry unequal CCS generation
at 2030 (post-fix REF 4.6908 vs LOAD-HI 5.5455 TWh), so the correction does not cancel.

### 3.3 P5 — the LOAD-HI / ORGANIC CCS identity survives the repair

Pre-fix, MISO's two load arms carried **identical** `gas_cc_ccs`: 3.7192 TWh / 484.1 MW at 2030.
Post-fix they are **still identical**: **5.5455 TWh / 721.9 MW**, and their cohorts are the same
four units. MISO's DC-volume axis remains a *shape* effect on the retrofit channel as well as on
the energy channel — ORGANIC's 2030 CO2 differs from LOAD-HI's by **0.0688 Mt** (482.5488 vs
482.6176), against a 3.91 GW peak difference.

### 3.4 Predictions, scored as written

| # | prediction | measured | verdict |
|---|---|---|---|
| **P1** | 2030 REF CO2 falls, order **0.5–2 Mt** | **−2.4330 Mt** | **MISS** — direction right, band overshot by 0.43 Mt, by the pre-named mechanism |
| **P2** | LOAD-HI ΔCO2 falls **0.2–1 Mt** from 72.8621 | **−0.4458 Mt** | **HIT** |
| **P3** | 2026 and 2027 do not move at all | 0.0000 Mt, 10/10 fuels identical, both years, all arms | **HIT** |
| **P4** | no new invariant FAIL ident | {I3, I7, I12} unchanged on all three legs | **HIT** |
| **P5** | *(report item)* does the LOAD-HI/ORGANIC CCS identity survive? | **yes**, 5.5455 TWh / 721.9 MW both | reported |

P1 is the one the PRECOMMIT named as most likely to be wrong, and it was, for the stated reason.
Recorded at full magnitude rather than re-banded after the fact.

---

## 4. Gate verdicts

| gate | REF | LOAD-HI | ORGANIC | note |
|---|---|---|---|---|
| **G1** identity | **PASS** | **PASS** | **PASS** | max rel dev 0.000e+00 everywhere; every converted unit `fuel_type = gas_cc_ccs` |
| **G2** confinement | **PASS** | **PASS** | **PASS** | (a) 0 non-cohort rates moved; (b) 10/10 fuels identical 2026+2027 |
| **G3** pre-2028 inertness | **PASS** | **PASS** | **PASS** | nuclear/hydro/wind/solar identical to 6 dp |
| **G4** no collateral flip | **PASS** | **PASS** | **PASS** | FAIL set {I3, I7, I12} unchanged; no new ident, none resolved |
| **G5** cache-hit proof | **PASS** | **PASS** | **PASS** | (a)–(e), §5 |

**STOPS: NONE.** Nothing was killed and nothing is promoted — a gate PASS here means only "the
mechanism did what its own arithmetic says" (rules 1 `[R-STRUCT]`, 29 `[R-SCREEN]`).

**Pre-declared NOT a STOP, and observed:** the retrofit set moved and **grew** in every leg
(REF 334.5 → 618.1 MW, both load arms 484.1 → 721.9 MW at 2030) and now opens a year earlier, in
2028, where the pre-fix run converted nothing. This is D65-B's cheaper capture VOM making the
screen clear sooner — the opposite sign to D77's self-limiting effect that shrank NEISO's 2030
cohort (D77 §4.3). Both are the repair working.

---

## 5. G5 — the cache-hit proof, per leg

**Pre-solve, recorded before the first leg: `results/MISO/` DID NOT EXIST** (the directory was
absent, and all three PIN keys absent with it). Each leg then created exactly its own PIN-key
directory; after all three, `results/MISO/` holds exactly `f1b3caa22b3f14ff`,
`9688b06c1b0a5a54`, `b87deb7735c242a0` and nothing else. **No pre-fix bundle was linked, copied
or moved into any cache root at any point**, and the WS-4c harness helper was never used.

| # | evidence | REF | LOAD-HI | ORGANIC |
|---|---|---|---|---|
| a | `results/MISO/<PIN key>/` absent pre-solve | ✓ (whole tree absent) | ✓ | ✓ |
| b | `run_config.json` `cache_key` = the phase-0 PIN key | `f1b3caa22b3f14ff` ✓ | `9688b06c1b0a5a54` ✓ | `b87deb7735c242a0` ✓ |
| c | `git.sha` = THE PIN or a descendant with zero solve-path diff; `dirty == false` | `95ad76d4` / false ✓ | `b4bbd3c3` / false ✓ | `dcc04801` / false ✓ |
| d | `total_wall_s` is a solve's, per-year `wall_s` for all 5 | 1879.5 s, 5/5 ✓ | 1846.8 s, 5/5 ✓ | 1854.0 s, 5/5 ✓ |
| e | 2029–2030 `gas_cc_ccs` rate = host × 0.10 | 0.057613–0.057802 ✓ | ✓ | ✓ |
| — | trajectory ≠ pre-fix in every year (a cache hit would reproduce it to the digit) | ✓ | ✓ | ✓ |

**The three keys were reproduced at zero LP in phase 0, before any solve**, through the
`runner.run_scenario_iso` chain (`matrix_configs` → `resolve_policy_bundle` →
`set_caiso_fsno_partition(False)` → `apply_iso_scenario_defaults` → `.cache_key()`), and the
three *pre-fix* keys read back out of the committed `run_config.json` files matched the charter's
table as well. Both columns reproduced independently, so the base is THE PIN.

### 5.1 Disclosed: the literal HEAD guard tripped on legs 2 and 3, and why that is not a defect

Legs 2 and 3 printed `HEAD GUARD FAILED`. The cause is this lane's own registration commits,
which land while the next leg solves — the convention the parent charter's G5(c) explicitly
admits ("THE PIN **or a descendant with a ZERO solve-path diff**"; the load ADDENDUM §5
convention, "this lane commits while later legs solve"). The commits touch only `results/`,
`frontend/data/hindcast/` and `docs/`.

**The substantive check the guard exists for is clean and was run:**
`git diff 95ad76d4 HEAD -- src/market_sim scripts configs data/raw` is **EMPTY** — zero
solve-path change across the whole session. Each leg's own `run_config.json` records the
authoritative fact (`git.sha`, `dirty=False`, row c above). This is reported rather than
suppressed; the fix for a future lane is to capture `H0` after all commits, or to guard on the
solve-path diff instead of on the sha.

---

## 6. Cost — wall and RSS per solve-year

| leg | total wall | peak RSS | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|---|---|
| REF | 31.3 min | **9.98 GB** | 594.3 s / 9983 MB | 225.7 / 8362 | 271.9 / 8382 | 353.8 / 9055 | 433.4 / 9393 |
| LOAD-HI | 30.8 min | 9.90 GB | 547.9 / 9895 | 182.2 / 8412 | 255.1 / 8167 | 357.0 / 8926 | 504.1 / 9338 |
| ORGANIC | 30.9 min | 9.89 GB | 613.3 / 9894 | 188.1 / 8418 | 262.7 / 8169 | 341.3 / 8927 | 448.1 / 9315 |

**93.0 min of LP for 15 solve-years, 6.20 min per solve-year, all rc=0, 5/5 years each.** Peak
RSS **9.98 GB on a 15 GB box** — rule 12's one-invocation-at-a-time cap for per-plant multi-zone
ISOs is **necessary, not cautious**, and the three legs were run strictly serially with nothing
else solving. Per solve-year this is ~19 % above the load campaign's MISO rate (5.23 min), on a
container also holding a freshly built `data/clean`.

**Precondition cost, for the next lane's planning:** `data/clean` is DERIVED and gitignored, so a
fresh container has none and `run_scenario_iso` hard-fails on MISO's `confirmed-retirements`
clean partition. `scripts/regenerate_clean.py` rebuilt **56 datatypes with 0 FAIL**, and it is
the session's single largest wall-clock item — start it before phase 0, not after.

---

## 7. Routed

1. **The campaign is now split across two roots, and the collation must cover both.** The five
   re-solved ISOs' legs live under `results/scn-campaign-load-2026-09-06-r2/<ISO>/<CASE>/`
   (charter-mandated new out-dir) while **ERCOT's three clean legs stay under the original
   root**. `collate_scenario_campaign.py` discovers legs by `root.rglob("full_horizon_summary.json")`,
   so a collation over one root only will silently drop the other set — which is precisely the
   "sums over DIFFERENT ISO sets" defect `STATUS-scn-ws5a-load-2026-09-06.md` already routed
   against that tool, arriving by a second route. **Owner: the parent lane** (it runs the
   collation; this lane did not). MISO's own bundle and report are refreshed and left at the
   campaign's canonical path `results/scn-campaign-load-2026-09-06/MISO/{bundle,report}/` so a
   reader at the campaign root still finds MISO.
2. **The desk's per-ISO contamination figures are accounting-only and undershoot wherever the
   retrofit set moves.** MISO's card figure was ≈1.1 Mt (0.27 %); measured 2.43 Mt (0.59 %),
   because D65-B rides the same pin and enlarges the cohort (§3.1: 53 % accounting / 47 % cohort).
   The other four re-solved ISOs will show the same structure, with the split depending on how
   much their screens move. Worth a line on the desk's card so nobody reconciles a repaired level
   against the pre-declared contamination and calls it a discrepancy.
3. **`miso-2026-2030-d60-arm` remains stale as a description of HEAD** — the load lane's routed
   item (+14.7 % energy; I3 fails in REF where the board key has it passing) is untouched by this
   repair and still stands. Records item for the capx director.
4. **Not a defect, but worth the desk knowing:** MISO's retrofit cohort is **two plants**
   (p7985 MISO-Plains, p1007 MISO-Indiana) split into offer tranches. A cohort that small means
   MISO's CCS channel is sensitive to single-plant economics, so a future screen change can move
   this ISO's number discontinuously.

**Nothing outside this lane's declared regions was touched, so nothing else is routed as a STOP.**

---

## 8. Files

**Written by this lane**
- `docs/handoffs/PRECOMMIT-scn-ws5a-resolve-miso-2026-09-06.md` (pushed at `95ad76d4`, before the first solve)
- `docs/handoffs/FINDING-scn-ws5a-resolve-miso-2026-09-06.md` (this document)
- `results/scn-campaign-load-2026-09-06-r2/MISO/{REF,LOAD-HI,LOAD-HI-ORGANIC}/{run_config.json,full_horizon_summary.json}`
- `results/scn-campaign-load-2026-09-06/MISO/{bundle,report}/` — refreshed on the repaired legs
- `frontend/data/hindcast/miso-2026-2030-scn-campaign-load-2026-09-06-{ref,load-hi,load-hi-organic}.json` — re-registered under the **same three run ids**; only `git_sha`, `cache_epoch` and the out-dir change
- `docs/codebase-site/data/mechanism-matrix/MISO.js` — `datacenter_load_block` cell, one appended evidence line, no verdict letter moved (rule 28(b); last commit after rebase)

**Deleted (rule 26 `[R-DELETE]`)** — `results/scn-campaign-load-2026-09-06/MISO/{REF,LOAD-HI,LOAD-HI-ORGANIC}/`,
each in the same commit as its case's re-registration, plus the stale pre-fix `bundle/report` pair
whose `meta.json` named the now-nonexistent pre-fix cache keys. A stale bundle at a valid key is a
re-armable wrong answer; git history is the record.

**Consumed, never edited** — everything under `src/`, `scripts/`, `configs/`; every other ISO's
files; the parent lane's PRECOMMIT/FINDING; `FINDING-scn-ws5a-load-synthesis-2026-09-06.md`;
`STATUS-scn-ws5a-load-2026-09-06.md`; the readiness plan; the desk ledger;
`program-status.json`; `ff-verdicts.json`; the backcast registry; every ISO shard but MISO's.
Rollup numbers reach the parent lane through **this document**, not by editing the synthesis.

**Duties discharged** — no default moved, no knob moved, no `ScenarioConfig` field added, no new
case, no solve outside the three, no year past 2030. **DOF ledger: ZERO free parameters**; no
`authorized_price_tuning` (rule 1's carve-out is a backcast offer-curve channel, untouched by a
forecast lane). Rule 15 / forecast plan §7.5: forecast namespace only, same run ids. Invariant
declarations unchanged — the FAIL set is identical pre and post, so no key was added or deleted;
`check_forecast_invariants.py --sidecar-dir frontend/data/hindcast` is **EXIT 0** and was run
before every push. Rule 27: no source file ≥300 lines rewritten; all nine pushed
artifacts ≥300 lines fetch-back verified (line count + blob hash **MATCH**). Rule 29(c) does not
apply — these are registered campaign arms, not screen or control bundles; the control is the
committed pre-fix bundle (form 4). **Backcast byte-identity untouched.** No CI workflow created;
every solve ran in-session.

**This is NOT a keeper and cannot be one** — "keeper" is a backcast-calibration concept (rules 1 /
15, the C1–C8 rubric, `frontend/data/backcast/keepers/<ISO>.json`). This is a forecast scenario
campaign registered `--kind scenario` into the forecast namespace; it has no keeper shard, no
determination and nothing that can be promoted.
