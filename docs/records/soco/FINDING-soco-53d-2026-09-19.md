# FINDING — SOCO-53d (2026-09-19): the model runs SOCO's steam boilers like peaking turbines

**Lane** SOCO-53d · **Model** Opus 5 · **Date** 2026-09-19 ·
**Branch** `claude/soco-commitment-mechanism-rnlt19` · **Data profile** `soco` ·
**PRECOMMIT** `docs/handoffs/PRECOMMIT-soco-53d-2026-09-19.md` (pushed at `0b3f2fdc`, before the
solve) · **Control** `2026-09-19-soco53c-egrid-family-hr`, bundle
`results/calibration/soco53c_family`, basis `0f8ebad9` ·
**Run** `2026-09-19-soco53d-campaign-commitment`, bundle `results/calibration/soco53d_campaign`,
recoverable in full at `730ae912e0e608695e3425e00daa00ad18138706`.

---

## 1. HEADLINE

SOCO's gas boilers start **5.0–9.7 times a year** and are **synchronized 63.9–92.0 % of all hours**.
The model gives every one of them `min_run_hours = min_down_hours = 0`, no committed state at all,
and cycles the same plants **10–349 times a year in blocks of 2–11 h median**. It is operating
SOCO's steam boilers as if they were peaking turbines, and buying the energy a synchronized boiler's
minimum-load block would carry from combustion turbines instead. That is the root cause SOCO-53 and
SOCO-53c both named and neither could reach, and this lane arms it.

**The gates improve, and that falsifies this lane's own prediction.** The PRECOMMIT declared the
failing-row set unchanged; instead the 2023 `ST_GAS` row crosses back **into** band, so **C1 goes
from two failing rows to one**, C1 all **12/14 → 13/14** and free **8/10 → 9/10**. The pass is
narrow — 0.09pp of share margin — and is reported as such rather than banked. 2023 `CT_PEAKER`
stays failed at **+9.898 TWh / +4.12pp**, so **the headline defect is not fixed**, which the
PRECOMMIT said first. Determination is **`NOT-YET`** (rubric v3.8, PRICE UNSCORED) on both sides.

**Zero free parameters were added** (rule 21 `[R-DOF]`: n_entries 3 / n_residual 1, unchanged), and
the promotion is **open and the owner's** (rule 31 `[R-RETAIN]`): the keeper is unchanged and
nothing has been pruned.

---

## 2. THE MEASUREMENT, which is the lane's real product

At plant grain on SOCO's own CAMPD boiler record, 2023–2025, with CAMPD **boiler** `unitType`s
paired to the plant's own model boiler rows by capacity rank and restricted to those paired to a
`gas_st` row. A plant is SYNCHRONIZED in any hour at least one of its kept units is online by that
unit's own threshold — the union of the per-unit masks, because a threshold on the plant *sum*
fragments a multi-unit plant whose units cycle independently (Gaston 2023: 56 blocks of median 5 h
by the sum, 10 of median 305 h by the union — the same turbine-conduct artifact one layer down).

| plant | model `gas_st` MW | measured campaigns/yr | measured campaign p25 / p50 (h) | measured synchronized share | **MODEL** runs/yr (2023 P1) | **MODEL** run p50 (h) |
|---|---|---|---|---|---|---|
| 26 E C Gaston | 1,020.0 | 9.7 | 64 / 286 | 0.639 | 61 | 9 |
| 2049 Jack Watson | 721.0 | 5.0 | 76 / 546 | 0.920 | 349 | 11 |
| 728 Yates | 714.0 | 5.3 | 192 / 394 | 0.843 | 20 | 5 |
| 10 Greene County | 516.1 | 7.7 | 132 / 384 | 0.752 | 121 | 10 |
| 3 Barry | 160.0 | 5.3 | 38 / 77 | **0.063** | 10 | 2 |

The arithmetic closes against the benchmark: plant CF × plant HSL × 8760 summed over the five plants
is **8.96 TWh** against the 2023 metered `ST_GAS` **9.076 TWh**, so the measured campaign picture
*is* the actual the model is scored against.

**The capacity-rank pairing is unambiguous at every plant** (within 5–10 % on all fifteen units) and
it surfaced one disagreement: CAMPD files **Barry unit 4 (HSL 367 MW) as Pipeline Natural Gas**
while the model carries a **362 MW `coal` row** there. The model's class assignment governs for this
mechanism, because the floor is applied to model rows — but that is a real question about 362 MW of
SOCO coal and it is **routed, not adopted** (§8).

---

## 3. THE MECHANISM, AND WHAT IT DELIBERATELY DOES NOT ARM

`ScenarioConfig.soco_gas_st_campaign_commitment` (default off, SOCO-gated) runs the shared
ISO-neutral detector `model.commitment.caiso_ra_mustoffer_min_gen` on `gas_st` alone at the P0→P1
seam, with exactly **two** of its legs: the **measured minimum-RUN extension** and the
**online-hours LSL state floor**. Three things are refused ex ante, each with its reason:

- **The restart legs (`startup_bridge`) stay off.** SOCO's boilers do not two-shift: 68.7 % of
  their 386 measured downtime gaps exceed 72 h and account for 98.6 % of all gap-hours, and only
  150 unit-hours across three years fall inside the 8 h min-down. That is exactly the `R` verdict
  SOCO-53 recorded on `gas_commitment_bridge`, and **this lane does not re-test it** (rule 28(a)).
- **`startup_aware` stays off**, because it asks whether an individual unit's margin **against an
  LMP** repays its published startup cost. That is a merchant test, and SOCO is a
  vertically-integrated cost-based balancing authority with no LMP, no offers and no market at all
  (card S5, gate G17) — the same ground on which `tranche_startup_amortization` is refused `G` here.
- **A `CT_PEAKER` leg is refused** on SOCO's own evidence: the model already reproduces SOCO's CT
  run *shape* (model p50 3–16 h against a measured 8–9 h) and gets the *number of starts* wrong
  (100–349 against 57–60), so a min-run floor would make CT run **more**, the wrong direction.

**Every parameter is a per-plant measured statistic** from
`scripts/data/derive_campd_gas_st_campaign_params.py` →
`campd_gas_st_campaign_params_SOCO.csv` (sha256[:16] `cc1be8f33fa267b2`), read through
`data.gas_st_campaign`, which applies only `flag == "ok"`:

| plant | `min_load_frac` (PLANT basis) | `min_run_hours` | `sync_share` | flag |
|---|---|---|---|---|
| 26 | 0.0657 | 64 | 0.6392 | `ok` |
| 2049 | 0.1000 | 76 | 0.9202 | `ok` |
| 728 | 0.0829 | 192 | 0.8429 | `ok` |
| 10 | 0.1365 | 132 | 0.7516 | `ok` |
| 3 | 0.1628 | 38 | **0.0632** | **`not_campaign_duty`** |

Level is the PLANT-basis minimum stable load (the basis a floor multiplied by plant `pmax` requires
— caiso-135); horizon is the **p25** of the plant's own campaign-length distribution (the LOW order
statistic, because an observed run bounds a min-run CONSTRAINT from above — the nyiso-90 / SPP-44
convention). Nothing is inherited from NYISO's 0.239 or SPP's 0.090 (rule 25 `[R-ISO-SCOPE]`).

---

## 4. WHAT THE RUN DELIVERED

### 4.1 Class volumes, arm − control (TWh)

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| **`ST_GAS`** | **+0.387** | **+0.383** | **+0.509** |
| **`CT_PEAKER`** | **−0.190** | **−0.165** | **−0.180** |
| `CC_REGULAR` | −0.121 | −0.157 | −0.245 |
| `COAL_PRB` | −0.069 | −0.039 | −0.051 |
| `COAL_BIT` | 0.000 | −0.012 | −0.028 |
| `CC_CHP` / `CT_CHP` / `ST_CHP` | +0.0000 / −0.0001 / +0.0000 | +0.0000 / −0.0003 / −0.0000 | +0.0000 / −0.0001 / −0.0002 |
| nuclear, hydro, wind, solar, biomass, oil | **0.000** | **0.000** | **0.000** |

### 4.2 The scored C1 rows

| year | class | control model / actual / Δ | arm model / actual / Δ | control | arm |
|---|---|---|---|---|---|
| 2023 | `CT_PEAKER` | 14.622 / 4.534 / **+10.088** (+4.20pp) | 14.432 / 4.534 / **+9.898** (+4.12pp) | **FAIL** | **FAIL** |
| 2023 | `ST_GAS` | 3.124 / 10.483 / **−7.359** (−3.07pp) | 3.511 / 10.483 / **−6.972** (−2.91pp) | **FAIL** | **PASS** |
| 2024 | `CT_PEAKER` | 11.504 / 4.785 / +6.719 (+2.68pp) | 11.338 / 4.785 / +6.553 (+2.62pp) | PASS | PASS |
| 2024 | `ST_GAS` | 3.098 / 8.879 / −5.781 (−2.33pp) | 3.480 / 8.879 / −5.399 (−2.17pp) | PASS | PASS |

The 2023 `ST_GAS` band is **±7.19 TWh and ±3.00pp**. The control is outside **both** legs; the arm
is inside both, by **0.22 TWh and 0.09pp**. **That is a narrow pass and it should be read as one.**
Every other 2023 and 2024 row passes on both sides and moves by less than 0.16 TWh.

### 4.3 Gates

| | control | arm |
|---|---|---|
| determination | `NOT-YET` (PRICE UNSCORED) | `NOT-YET` (PRICE UNSCORED) |
| C1 | **FAIL, 2 rows** | **FAIL, 1 row** |
| C1 all · free | **12/14 · 8/10** | **13/14 · 9/10** |
| C2 / C4 / C6 / C8 | PASS | PASS |
| C3a / C3b / C3c | UNSCORABLE | UNSCORABLE |
| `grade_summary` | scored 5, target 4, fails 1 | scored 5, target 4, fails 1 |
| caveats | 0 ledgered, 0 protective | 0 ledgered, 0 protective |
| DOF | n_entries 3 / n_residual 1 | **unchanged** |

C2's ungated 2025 coal row improves +12.3 % → **+12.1 %**; 2025 gas moves +1.5 % → +1.6 %.

### 4.4 The structural evidence, which is independent of the gates

**D-1 `ST_GAS` off-peak CV falls toward the measured actual in every year** — the signature of
replacing turbine conduct with campaign conduct:

| year | model CV control → arm | actual CV | `cv_ratio` control → arm | gate |
|---|---|---|---|---|
| 2023 | 0.709 → **0.545** | 0.281 | 2.528 → **1.942** | ≥0.5, pass |
| 2024 | 0.864 → **0.658** | 0.263 | 3.281 → **2.499** | ≥0.5, pass |
| 2025 | 0.608 → **0.448** | 0.207 | 2.941 → **2.166** | ≥0.5, pass |

That is prediction **P6 confirmed exactly**, and it is the result the residual cannot show.

### 4.5 Rules 17 and 20, measured on the committed floors

The floor touches `ST_GAS` rows at the four population plants **and nothing else**, in all three
years. Per-plant, against that plant's **own measured synchronized share**:

| plant | 2023 bind / meas | 2024 bind / meas | 2025 bind / meas | median floored block (h) |
|---|---|---|---|---|
| 10 Greene County | 0.312 / 0.752 | 0.273 / 0.752 | 0.500 / 0.752 | 202 / 395 / 321 |
| 26 E C Gaston | 0.197 / 0.639 | 0.055 / 0.639 | 0.138 / 0.639 | 326 / 113 / 86 |
| 728 Yates | 0.137 / 0.843 | 0.536 / 0.843 | 0.747 / 0.843 | 459 / 216 / 334 |
| 2049 Jack Watson | 0.808 / 0.920 | 0.647 / 0.920 | 0.758 / 0.920 | 194 / 161 / 244 |
| **3 Barry** | **0.000** / 0.063 | **0.000** / 0.063 | **0.000** / 0.063 | — |

**Rule 17 `[R-FLOOR-WINDOW]` holds by measurement in all twelve plant-years**, and the floored
blocks have a median length of **86–459 h**: they are campaigns, not gap fills. Barry carries zero
floored unit-hours because the derive's ex-ante campaign-duty gate refuses it — prediction **P8
confirmed exactly**.

**Rule 20 `[R-FORCED-BUDGET]`:** `ST_GAS` forced share **0.0944 / 0.1001 / 0.1160** against the 30 %
merchant cap; **C8 PASSES on the budget** and the escalation path is never entered. D-4 passes with
off-window share **exactly 0.0** in all three years, and its per-plant unit-conduct rider passes at
Yates with a measured zero-share of 0.0 / 0.0088 / 0.0.

### 4.6 Marginal emission rate

Every `hourly/system_<year>.parquet` carries `marginal_emission_rate`. P1 load-weighted mean
**0.6240 / 0.6092 / 0.6363** tCO2/MWh on the arm against **0.6333 / 0.6163 / 0.6353** on the
control; p10 / median / p90 **0.4187 / 0.5935 / 0.8194** (2023), **0.3833 / 0.5833 / 0.8717**
(2024), **0.3833 / 0.5848 / 1.0896** (2025); zero-share **0.00 / 0.00 / 0.15 %**, unchanged. The p90
falls materially in 2023 and 2024 (1.0896 → 0.8194 and 1.0088 → 0.8717) — the floor putting a
committed gas-steam block on the margin in hours a combustion turbine would otherwise have set it.

---

## 5. THIS LANE'S OWN PREDICTIONS, SCORED HONESTLY

| # | prediction | outcome |
|---|---|---|
| P1 | `ST_GAS` +0.4 to +0.7 TWh every year | **directionally right, band slightly optimistic**: +0.387 / +0.383 / +0.509. The falsifier (no rise, or >1.5 TWh) did not fire, but 2023 and 2024 landed just below the declared floor. |
| P2 | `CT_PEAKER` −0.05 to −0.35 TWh | **CONFIRMED**: −0.190 / −0.165 / −0.180. |
| P3 | `CC_REGULAR` −0.05 to −0.35 TWh, no status change | **CONFIRMED**: −0.121 / −0.157 / −0.245. |
| P4 | failing-row SET unchanged, no row changes status | **FALSIFIED**, in the favourable direction: 2023 `ST_GAS` crosses into band and C1 goes 2 fails → 1. Reported exactly as plainly as an adverse falsification would be. |
| P5 | forced share 0.15–0.30, falsifier below 0.10 | **FALSIFIED in 2023** (0.0944; 2024 sits on the boundary at 0.1001). The substance — C8 passes on the budget — held; the magnitude was over-predicted, see §6. |
| P6 | D-1 `ST_GAS` CV falls toward the actual, `cv_ratio` stays above 1.0 | **CONFIRMED exactly** (§4.4). |
| P7 | `*_CHP` move < 0.001 TWh, COAL < 0.5 TWh, non-thermals byte-identical | **CONFIRMED**: max \|Δ\| on any CHP class is 0.0003124 TWh; COAL max 0.079; nuclear/hydro/wind/solar/biomass/oil exactly 0.000. |
| P8 | Barry zero floored hours; binding ≤ measured sync in all twelve plant-years | **CONFIRMED exactly** (§4.5). |

---

## 6. WHY P5 MISSED, and what it says about the offline estimator

The PRECOMMIT's §4.2 offline floor volumes (0.867 / 0.818 / 0.908 TWh) came in at **0.731 / 0.710 /
0.856** delivered, and the *forced* energy D-2 counts is lower still (0.376 / 0.405 / 0.535 TWh).
Two causes, both nameable:

1. **D-2 counts energy dispatched AT a binding floor**, not the floor's nominal volume. Where a
   plant dispatches above its floor the floor is not forced energy at all. The PRECOMMIT called
   §4.2 an upper bound but used it directly in the P5 band, which was the error.
2. **The offline estimator used the keeper's committed P1 dispatch as a proxy for the P0 pattern**
   the seam actually reads, because the keeper commits no P0. The PRECOMMIT named that proxy and
   predicted its direction — *"more likely below than above"* — which was right; the magnitude was
   under-called by roughly a factor of two.

Neither is a defect in the mechanism. Both are a defect in the estimator, and the fix for a future
lane is to compare against D-2's own construction rather than the floor array's sum.

---

## 7. A/B INTEGRITY, AND THE BENCH POSTURE

**G-DRIFT (rule 29(b) form 4).** `git diff 0f8ebad9 HEAD` over the solve path returns exactly **one
changed file, `config/paths.py`, +8 lines**: an additive `EXPORTS_DIR` constant. Classified **INERT
mechanically** — its only reader anywhere in the repo is `scripts/data/derive_ercot_hub_rt_lmp_csv.py`,
nothing under `src/market_sim/` reads it, and `paths` is not one of the seven
`solve_surface.SURFACE_MODULES`. **No control solve was spent.**

**Cache-key inertness, measured rather than assumed.** Over all **20** committed `run_config.json`
files on disk, **zero keys move** at the new field's declared default, and an armed run keys
distinctly. `check_cache_key_registration.py` passes (853 fields, 308 registered, all declared
defaults match HEAD).

**SOCO's bench parts were deliberately NOT rebuilt.** `dashboard_add_run.py` auto-rebuilds the parts
for a run's years as a side effect of registering; those rebuilds were **reverted** and
`metrics.json` re-written on the committed bench, exactly as SOCO-53c did. `check_bench_freshness`
is red on 31 of 44 parts across every ISO (13 more carry engine drift) from commit `ed96378e`
(caiso-284) editing `render_calibration_html.py`, a `PAYLOAD_SOURCE`; this lane touched no
fingerprint source, and rebuilding SOCO's alone would have scored the arm against a different
benchmark from its control and destroyed the form-4 comparison. Applying the nyiso-239 `OIL_GROUPS`
repair to SOCO alone while seven ISOs stay stale is a **cross-ISO** decision, not a lane's.
**Recorded for the owner: on the rebuilt bench the arm reads the same C1 13/14 · free 9/10.**

---

## 8. ROUTED — and the first item falsifies the premise this lane was handed

1. **`measured_st_heat_rates` (SOCO-53e) — the cost side is NOT exhausted on `ST_GAS`, and its own
   predecessor made it so.** `measured_ct_heat_rates` moved `CT_PEAKER` to **11.2666** while
   `ST_GAS` still rides eGRID at **10.9613**. Measured on SOCO's own CAMPD boiler record (net
   basis, the same 0.99 parasitic factor the CT derive uses), SOCO's gas-steam fleet is
   **10.4223** cap-weighted — the model is **+0.539 MMBtu/MWh, +5.2 %, too dear on 3,131 MW**:

   | plant | measured net HR | model HR | Δ |
   |---|---|---|---|
   | 26 E C Gaston | 10.642 | 11.551 | **−0.909** |
   | 2049 Jack Watson | 9.938 | 10.413 | −0.475 |
   | 10 Greene County | 9.795 | 10.256 | −0.461 |
   | 728 Yates | 10.359 | 10.814 | −0.455 |
   | 3 Barry | 13.512 | 12.610 | +0.902 |

   SOCO-53 §2.2's *"the model over-separates the classes by 2.8×"* was measured on the **pre-arm**
   fleet. At HEAD the model separation is **+0.305** against a measured **+0.713**, so it now
   **under-separates by 2.3×** — `ST_GAS` is too dear *relative to* `CT_PEAKER`, which is the sign
   of the defect. At $3.2–3.6/MMBtu delivered that is $1.5–3.3/MWh, enough to move Gaston
   (43.23 → ~40.1) and Yates (43.24 → ~41.6) below a large part of the CT stack. It is the exact
   sibling of SOCO's promoted keeper mechanism, a pure rule 14 `[R-ACCURATE]` repair with zero free
   parameters, and it is **probably the larger lever**. Not armed here because rule 19
   `[R-ONE-MECH]` forbids stacking a second mechanism on the same phenomenon in one run.
   **Consequence for this run, stated rather than hidden:** the floor's binding pattern depends on
   the P0 pattern, which depends on a cost input known to be wrong in a stated direction, so §4.5's
   binding shares are owed a re-measurement after SOCO-53e lands.
2. **Barry unit 4** — 362 MW the model prices as coal and CAMPD files as gas (§2).
3. **E C Gaston (26) — the fuel-subfamily lever**, unchanged from SOCO-53c's routing.
4. **SOCO-53b — the 2025 EIA-923 hydro input hole**, unchanged; hydro is byte-identical here.
5. **NWPP-41's ERCOT-pooled PRB proxy reaches SOCO** (6002 Miller, 6073 Daniel, 6257 Scherer);
   `coal_prb_proxy_own_iso` is a cheap rule-14/25 data lever.
6. **`test_soco_token_collides_with_no_other_raw_name` gains one more offender and was NOT
   patched.** The test is RED at HEAD; this lane's artifact follows the established convention
   (`campd_gas_st_campaign_params_SOCO.csv`, exactly as SOCO-53's committed
   `campd_ct_heat_rates_SOCO.csv`). Verified: it fails identically with and without this lane's
   file. The fix is a naming-convention decision across every SOCO artifact and belongs to the
   SOCO desk.

---

## 9. GATES

| gate | state |
|---|---|
| `check_cache_key_registration` | **PASS** — 853 fields, 308 registered, all declared defaults match HEAD |
| `check_mechanism_matrix` | **PASS** — integrity OK over the base row + 9 ISO shards; keeper stamps and §5.x prose headers match |
| `floor_mechanisms.assert_ablation_coverage()` | **PASS** — 26 mechanisms, all classified |
| `tests/unit/data/test_gas_st_campaign_params.py` | **PASS** (6) — pins all eight measured values against the PRECOMMIT |
| `tests/unit/pipeline` + `tests/unit/model/test_commitment.py` | **PASS** (366) |
| `tests/unit/config` | 205 pass, **1 pre-existing RED** (§8.6) |
| `ruff check` / `ruff format` | clean on every file this lane touched; two pre-existing errors in another lane's `scripts/gen_nyiso229_attestation.py`, verified at HEAD |
| `check_registry_payload_parity` | **RED on the two pre-existing dirs only** — `caiso279_ablate_dswcouple_span` and `soco15_spp_arm`. Named; **neither deleted** (rule 31) |
| `check_bench_freshness` | **RED repo-wide, 31 of 44 stale**, from `ed96378e`; not this lane's (§7) |
| `check_gate_a_provenance` | SOCO's only line is the expected NOTE ("has a keeper shard but no entry on the forecast board" — card S10 routes the forecast namespace to the capx director); **no gate-(a) stamp was created** |
| `audit_keepers --check --iso SOCO` | **E11 warning** (expected, documented) + **E13 failure** — see §9.1 |

### 9.1 E13 fires again, and for the same structural reason SOCO-53 recorded

> `2026-09-19-soco53d-campaign-commitment` is registered for SOCO but not the keeper and stamped to
> no keeper — a superseded run left behind a promotion.

**It is not a superseded run left behind a promotion.** It is a newly registered candidate whose
promotion the owner has not ruled on, and E13 has no state for that. The red is the unavoidable
consequence of obeying three rules at once — rule 15 `[R-DASHBOARD]` (register the moment it
finishes), rule 31 `[R-RETAIN]` (never delete before the owner rules) and rule 35(f) / E13 (every
registered run is the keeper or stamped to it). Each way to turn it green breaks one of them:
pruning deletes a result before the ruling; stamping `holdout.keeper` would be **factually false**
(rule 30 `[R-TOUCHPOINT-FOLD]` (a) is for the keeper's own recipe on a *held-out year*, and this is
a *different config on the same years*); promoting pre-empts the owner. **Either ruling clears it
immediately.** This is the identical analysis `FINDING-soco-53-2026-09-17.md` §9.1 recorded, and it
recurs because the gap in E13 was never closed — the routed fix is a `candidate: true` sidecar field
or an E13 exemption for a run registered after the current keeper's date with no promotion recorded.

**E11** ("lineage recipe diff not computable") is the documented post-prune degradation
`FINDING-soco-53c` §8.1 names, and it is **pre-existing and unrelated to this run**: it concerns the
*former* keeper `2026-09-17-soco53-measured-ct-hr`, whose bundle rule 35(a) pruned. It is unchanged
from the baseline measured before this lane registered anything. **If the owner promotes, E11
becomes computable for this promotion**, because the outgoing keeper's bundle
(`results/calibration/soco53c_family`) is on disk and committed.

---

## 10. COST, AND WHERE EVERY BYTE LIVES (rules 31 / 33 / 34)

- **Parent LP cost: ZERO.** The parent ran no LP of any length (rule 32(a)). Every number in §2,
  §5's predictions, §6's estimator post-mortem and §8's heat-rate finding is zero-LP.
- **One shard, one `--year 2023 2024 2025` invocation**, ~10 minutes wall, pinned to `0b3f2fdc`.
- **The arm's bundle is RETRIEVABLE IN FULL and a promotion costs ZERO re-solves** (rule 34(e)):
  the slim + `hourly/` set is committed on this branch, and the complete 33-file bundle — including
  `dispatch/{2023,2024,2025}_P1.parquet` and the per-plant `unit_hourly` — is recoverable with
  `git checkout 730ae912e0e608695e3425e00daa00ad18138706 -- results/calibration/soco53d_campaign`.
  `results/calibration/_shared/SOCO/` (8 files) is on the same SHA.
- **The control is recoverable at `c91dde5e4cfbecd4e1da14ebba9209923ef9d500`.**
- **The shard container is ARCHIVED** (rule 33(a): fetched, checked out, verified first).
  **Its branch `claude/soco-53d-campaign` is DELIBERATELY KEPT** (rule 33(f) step 3): it carries the
  per-plant layer a registration needs, and deleting it while the promotion is undecided is the
  ercot-255 failure mode rule 31 forbids in those words. It goes once the owner rules.
- **Nothing was deleted.** The two parity-red bundle dirs are named, not removed.

---

## Log entry

## soco-53d — 2026-09-19 — the model runs SOCO's steam boilers like peaking turbines

SOCO's gas boilers start five to ten times a year and are synchronized between 64 % and 92 % of all hours. The model gives every one of them `min_run_hours = min_down_hours = 0`, no committed state at all, and cycles the same plants 10 to 349 times a year in blocks of two to eleven hours median. It is operating a 3,131 MW steam fleet as if it were a peaking fleet, and buying the energy a synchronized boiler's minimum-load block would carry from combustion turbines instead. That is the root cause SOCO-53 named and SOCO-53c could not reach, and this lane arms it: `ScenarioConfig.soco_gas_st_campaign_commitment`, the shared ISO-neutral detector run on `gas_st` alone with exactly two of its legs — the measured minimum-run extension and the online-hours minimum-stable-load state floor.

Three things are refused before the solve, each with its reason rather than by omission. The restart legs stay off because SOCO's boilers do not two-shift — 98.6 % of their measured downtime-hours sit in gaps longer than 72 hours, which is the `R` verdict SOCO-53 already recorded on `gas_commitment_bridge` and which this lane therefore does not re-test. The commitment-real run screen stays off because it asks whether a unit's margin against an LMP repays its startup cost, which is a merchant test on a footprint with no LMP, no offers and no market — the same ground on which `tranche_startup_amortization` is refused here. And no CT leg is armed, because the model already reproduces SOCO's turbine run shape and gets only the number of starts wrong, so a minimum-run floor would push CT the wrong way.

Level, horizon and membership are per-plant measured rows of a new derive artifact built from SOCO's own CAMPD boiler record, with boiler unit types paired to each plant's own model `gas_st` rows by capacity rank. Zero free parameters were added and the DOF ledger is unchanged at three entries and one residual. The derive refuses Barry on its own meter — its two 80 MW boilers are synchronized 6.3 % of the year, standby iron rather than campaign iron — and the committed floors confirm Barry carries zero floored unit-hours in all three years. The campaign-duty gate selects nothing: SOCO's population separates by an order of magnitude, so every value between 0.07 and 0.63 gives the identical partition, and it was declared in the PRECOMMIT and never swept.

The gates improve, and that falsifies this lane's own prediction. The PRECOMMIT declared the failing-row set unchanged; instead the 2023 `ST_GAS` row crosses back into band, from −7.359 TWh and −3.07pp to −6.972 and −2.91 against bands of ±7.19 TWh and ±3.00pp, so C1 goes from two failing rows to one and C1 all/free from 12/14 · 8/10 to 13/14 · 9/10. The pass is narrow — 0.09pp of share margin — and is recorded as narrow rather than banked. 2023 `CT_PEAKER` stays failed at +9.898 TWh, so the headline defect is not fixed, and the PRECOMMIT said so first, having measured before the solve that the floor's marginal class is `CC_REGULAR` in 1,170 of the 3,988 incremental hours against `CT_PEAKER` in only 681. Determination is NOT-YET both ways. Two other predictions are scored honestly as misses: the ST_GAS gain landed just below its declared band in two years, and the forced-share prediction was over-called by roughly a factor of two because the offline estimator summed the floor array rather than reproducing D-2's own construction.

The result that does not depend on a gate is the shape. D-1's `ST_GAS` off-peak coefficient of variation falls from 0.709, 0.864 and 0.608 to 0.545, 0.658 and 0.448, toward the measured 0.281, 0.263 and 0.207, with the ratio staying comfortably above its floor — the signature of replacing turbine conduct with campaign conduct on a class the model was cycling hundreds of times a year against a metered handful. Rule 17 holds by measurement in all twelve plant-years: every delivered binding share lands at or below that plant's own synchronized share, and the floored blocks have a median length of 86 to 459 hours, so what the mechanism places are campaigns rather than gap fills. Rule 20 passes on the budget at forced shares of 0.094, 0.100 and 0.116 against a 30 % cap, and D-4's off-window share is exactly zero in all three years. One changed solve-path file since the keeper's basis was audited INERT mechanically, so no control solve was spent, and over all twenty committed run configs zero cache keys move at the new field's default.

The lane also falsified the premise it was handed. The handoff stated that cost levers are exhausted; on `ST_GAS` they are not, and the predecessor's own arm made it so. `measured_ct_heat_rates` moved `CT_PEAKER` to 11.2666 while `ST_GAS` still rides eGRID at 10.9613, and SOCO's gas-steam fleet measures 10.4223 on its own CAMPD meter — the model is 5.2 % too dear on 3,131 MW, with Gaston out by −0.909 alone. SOCO-53's "the model over-separates the classes by 2.8×" was measured on the pre-arm fleet; at HEAD the model under-separates by 2.3×, which is the sign of the defect. `measured_st_heat_rates` is the exact sibling of SOCO's promoted keeper mechanism, a pure rule-14 repair with zero free parameters, probably the larger lever, and it is routed as SOCO-53e rather than stacked here. The promotion of this run is open and is the owner's; the keeper is unchanged, nothing was pruned, and both bundles are retrievable by immutable SHA so a promotion costs zero re-solves. Record: `docs/handoffs/FINDING-soco-53d-2026-09-19.md`.
