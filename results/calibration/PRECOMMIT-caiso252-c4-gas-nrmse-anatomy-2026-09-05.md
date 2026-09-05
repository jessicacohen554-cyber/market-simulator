# PRECOMMIT — caiso-252: THE C4 `dispatch_corr` 2025 CELL — a ZERO-LP ANATOMY OF THE GAS-FLEET HOURLY NRMSE, KEEPER DIFFERENCED AGAINST PRIOR KEEPER

**Session caiso-252, 2026-09-05.** Branch
`claude/caiso-252-backcast-calibration-4xvfvn` off `main` `95739d60`. Keeper
**`2026-09-05-caiso-251-b1-nomargin`** (`caiso251_arm_nomargin`; finding-stated
solve basis `90b2ef51` — the bundle's `meta.json` `git_sha` `f9c1fa0d` is
UNREACHABLE at HEAD, the branch having been rebased after the solve, so
`90b2ef51` is the audit base), **NOT-YET**. The SOLE failing criterion is
**C4 `dispatch_corr` (SUPPORTING)** on ONE cell: 2025 gas-fleet hourly
**NRMSE 0.305 against ≤ 0.30**, r 0.870. 2023 (0.285) and 2024 (0.264) PASS.
C3a PASSES all three years (+4.83 / +9.44 / +9.35 %). Prior keeper
`2026-09-05-caiso-246-b1-spot` (`caiso246_b1_spot_coverage`, still on disk and
still carrying its run payload) read 0.283 / 0.266 / **0.298** on the same cell.

**Pushed to `origin` BEFORE the estimator is coded and before any cell of the
object is measured.** Rule 22 `[R-HOLDOUT]`: 2023–2025 only, fail-closed; CAISO
holds no `complete` and no `final` marker; the holdout freeze is ACTIVE.

---

## §0 — THE OBJECT

Queue item **A** of the caiso-251 handoff, ranked first: the one C4 cell. The
handoff names the prime suspect (caiso-251 §5.4: **CC_REGULAR over-generates**
as it absorbs the import energy the arm displaced — import −0.213 / −1.393 /
−1.083 TWh, CC_REGULAR +0.184 / +0.947 / +0.740 TWh, CT_PEAKER +0.079 / +0.734
/ +0.414 TWh, ST_GAS −0.055 / −0.336 / −0.095 TWh) and lists three candidate
carriers: **(i) CC_REGULAR's shape, (ii) the import displacement, (iii) the CT
tranches that newly clear.** Its instruction is explicit: *do NOT arm anything
before the decomposition names a carrier.* This PRECOMMIT is that
decomposition, registered before it is run.

### §0.1 — What C4 actually scores (read from `scripts/calibration_verdict.py`)

CAISO is a `CEMS_GAS_ANCHOR_ISOS` member from vintage 2023, so C4's gas row is
recomputed by `_cems_gas_hourly_fit` from **committed artifacts only**:

* **actual** `A(h) = Σ_p campd_p(h)·npl_p/100 − btm_mw + cogen_mw` — the bench
  part's per-plant CAMPD hourly CF% (uint8, b64) over the CEMS-covered gas
  plants (85 in the 2025 part: 43 CT_PEAKER, 26 CC_REGULAR, 7 CT_CHP, 6 CC_CHP,
  3 ST_GAS), a flat BTM-CHP removal, plus the flat non-CEMS cogen block
  (`e930.gas_cogen_grid`, 6.416 TWh in 2025);
* **model** `M(h) = Σ_p m_p(h)·npl_p/100 − btm_mw + fill_mw` — the run
  payload's per-plant model CF% for the SAME plants, plus a flat fill up to the
  committed gas fuel-row level (51.17 TWh model vs 50.84 actual in 2025);
* `NRMSE = sqrt(mean((M−A)²)) / mean(A)`, `r` = Pearson; tolerance
  NRMSE ≤ 0.30, r ≥ 0.70; both rounded to 3 dp.

Every term is on the model's local-clock non-leap 8760 index (CAMPD
`interval_start_local` → `hour`; the same clock caiso-168's `_model_hour`
maps onto). Both flat terms are Pearson-invariant; NRMSE carries them as level.
The fleet-level bias is therefore fixed by the fuel-row gap (+0.33 TWh ≈ +38 MW
on a ~5,800 MW mean) and is NOT the object — the 0.305 is **shape**, and the
question is *whose* shape.

### §0.2 — Admissibility

This is a **measurement from committed bytes**: two run payloads
(`runs/2026-09-05-caiso-251-b1-nomargin.js`, `runs/2026-09-05-caiso-246-b1-spot.js`),
the three CAISO bench parts, and the two bundles' `hourly/class_hourly_<year>.parquet`
sidecars. **No `ScenarioConfig` field, no flag, no derive, no LP, no run
registered, no promotion** in this phase. Rule 29(b) `[R-SCREEN]`: **the prior
keeper's committed payload is the control** — the keeper-vs-prior difference is
exactly the caiso-251 arm, solved on the SAME bench, so the ΔNRMSE
(0.298 → 0.305) decomposes with zero LP.

**If the decomposition names a carrier, ANY arm is registered as an ADDENDUM to
this PRECOMMIT before it is coded** (its mechanism, its rule-29(a) screen year
chosen on the mechanism's own footprint, its structural screen gate, its
predictions, and its direction hazard). It is not registered here because the
handoff forbids choosing it before the carrier is known.

### §0.3 — The direction hazard, declared now for whatever follows

No arm is proposed in this phase, so no direction is spent. Declared in
advance: an arm aimed at this cell has **C4 as its target**, and C4 is
**EXCLUDED from any promotion basis in both directions** (the caiso-251
discipline). If the carrier is the CC_REGULAR half of the CC/CT split (object
B), its measured direction is **UPWARD on CC offers** (caiso-230 §7:
+0.55 / +0.70 / +0.71 $/MWh) — **ADVERSE to C3a**, which now sits at +9.44 /
+9.35 % against a ±10 % band. That would be the lane's first adverse-direction
arm after six consecutive favourable ones, and the C3a consequence is a real
risk to a LOAD-BEARING criterion, to be registered as such in the addendum —
never waved through as "structural" without its own G-COUPLE-class gate.

---

## §1 — THE ESTIMATOR, NAMED, WITH ITS FALSIFIERS

`scripts/probes/_caiso252_c4_gas_nrmse_anatomy.py` →
`results/calibration/_caiso252_c4_gas_nrmse_anatomy.json`. Stdlib + numpy +
pandas over `calibration_verdict.load_artifacts`.

### §1.1 — G-REPRO (the gate on the instrument)

Reproduce the scorer's own construction plant-for-plant. **PASSES iff** the
recomputed (r, NRMSE) for the keeper in 2023 / 2024 / 2025 and the prior keeper
in 2023 / 2024 / 2025 each match the committed `_verdict.json` rows
(0.877/0.285, 0.905/0.264, 0.870/0.305; 0.879/0.283, 0.905/0.266, 0.872/0.298)
to **≤ 0.001** after the scorer's 3-dp rounding. A miss means the instrument is
not the scorer and nothing below is read.

### §1.2 — The exact decompositions

With `e(h) = M(h) − A(h) = Σ_c e_c(h) + k` (classes `c` from the bench part's
`group`; `k` the flat fill-minus-cogen constant):

* **(a) by class, exact:** `MSE = Σ_c cov(e_c, e) + mean(e)²`. The per-class
  term `MSE_c := cov(e_c, e)` sums to `var(e)` exactly (cross-terms included,
  attributed to each class by covariance). Reported with each class's own
  RMSE, bias (mean `e_c`, MW) and bias² share.
* **(b) by hour-of-day, exact:** `MSE = (1/24) Σ_{hod} MSE_hod`.
* **(c) by month, exact:** `MSE = Σ_m (n_m/8760) MSE_m`.
* **(d) keeper vs prior keeper, exact:** `ΔMSE = Σ_c ΔMSE_c + Δmean(e)²`, and
  the same Δ by hour-of-day, by month, and by plant.
* **(e) the import-displacement leg** (the two bundles' `class_hourly`
  sidecars): `Δimport(h)`, `ΔCC_REGULAR(h)`, `ΔCT_PEAKER(h)`, `ΔST_GAS(h)`;
  the Pearson r of `ΔCC_REGULAR(h)` on `Δimport(h)`; and the share of ΔMSE
  carried by the hour subset `Δimport(h) < −500 MW` (an exact subset split of
  the mean).
* **(f) plant grain:** `cov(e_p, e)` per plant in 2025 and its Δ against the
  prior keeper — the carrier at the grain the scorer actually uses.
* **(g) CC_REGULAR's diurnal error profile** (mean `e_CC` by hour-of-day) in
  2024 and 2025, to test "CC's shape" directly against "CC's level".

No tolerance, window or class membership is chosen here: the classes are the
bench part's, the clock is the scorer's, the subset threshold in (e) is fixed
at −500 MW now and is not re-picked.

---

## §2 — PREDICTIONS, WRITTEN TO BIND

The caiso-251 lesson: predictions that fail in the favourable direction are a
mis-calibrated prior, not a hard test. These are two-sided or name the
uncomfortable alternative explicitly.

| # | prediction | what its failure would mean |
|---|---|---|
| **P-1** | G-REPRO ≤ 0.001 on all six (r, NRMSE) pairs | the instrument is not the scorer; stop |
| **P-2** | CC_REGULAR's 2025 class share `MSE_CC / var(e)` lies in **[0.45, 0.75]** — the majority, but NOT the whole | < 0.45: CT (or CC_CHP) carries the cell, the handoff's prime suspect is wrong; > 0.75: CC is the whole object and the split framing is moot |
| **P-3** | the keeper-vs-prior **ΔMSE in 2025 is carried by CC_REGULAR: `ΔMSE_CC ≥ 0.60·ΔMSE`** | carrier (iii) — the newly clearing CT tranches — or a diffuse cross-term change |
| **P-4** | import displacement is absorbed by CC in the same hours: Pearson `r(ΔCC_REGULAR(h), Δimport(h)) ≤ −0.50`, AND the hours with `Δimport < −500 MW` carry **≥ 50 %** of the 2025 ΔMSE while being **< 40 %** of hours | the CC over-generation is not the import displacement — it is a different mechanism (a merit-order/shape change within the domestic stack) |
| **P-5** | the 2025 MSE is evening-concentrated: Pacific **17–21** (5 of 24 hours) carry **≥ 0.35** of the MSE, and **10–15** carry **≤ 0.15** | a midday/solar-belly or morning-ramp error, which would point at the storage/import seam rather than the evening gas ramp |
| **P-6** | CC_REGULAR's 2025 bias on the CEMS-covered basis is **POSITIVE and in [+40, +150] MW** (the +0.74 TWh keeper-vs-prior rise landing on a modest prior over-run), yet **its bias² is < 25 % of `MSE_CC`** — CC is a SHAPE error, not a level error | bias outside the band or bias² ≥ 25 %: the CC object is a LEVEL object and the CC-hot charter is a level charter |
| **P-7** | the 2025 ΔMSE is NOT a Sep–Nov artifact of the caiso-246 daily-spot overlay months: Sep–Nov carry **≤ 40 %** of the 2025 ΔMSE, and no single month carries **> 20 %** of the 2025 MSE | the degradation is localized to the overlay months — a different carrier (the caiso-246 coverage repair), and object A would then be a caiso-246 question |
| **P-8** | the class ranking is stable: CC_REGULAR is the top `MSE_c` class in **all three years**; the 2025 failure is a threshold crossing on the same structure | a 2025-specific carrier (a class that ranks first only in 2025) |
| **P-9** | plant concentration: the top-5 plants by `cov(e_p, e)` carry **≥ 40 %** of the 2025 MSE | a diffuse fleet-wide shape error with no plant-level handle |
| **P-10** | the CT leg HELPED: `ΔMSE_CT_PEAKER < 0` in **both** 2024 and 2025 (the newly clearing CT tranches clear in hours the real CT ran) | ΔMSE_CT > 0: the tranches clear in the WRONG hours — carrier (iii) is live and the caiso-251 CT volume gain is partly shape-wrong |

**Numbers registered for interest, not scored:** the model-vs-actual mean gas
level (fixed by the fuel row), the per-class TWh on the CEMS-covered basis,
and the count of hours in the P-4 subset.

---

## §3 — STOP RULE

1. **G-REPRO fails ⇒ nothing is read; the session reports the instrument
   defect.**
2. **Nothing is armed from this phase.** A carrier named here earns an ADDENDUM
   (§0.2), pushed before any arm is coded, with its own rule-29(a) screen year
   and structural gate. If no addendum can be written admissibly — the carrier
   sits behind a DO-NOT-REDO cell (`gas_offer_net_revenue_margin` is `R`;
   per-year measured multipliers are rule-13 inadmissible; the storage
   charge-side census is closed, caiso-168 §8 / caiso-250 §7) — the session
   reports the negative and the keeper is unchanged.
3. **C4 is never the gate of anything that follows** (§0.3). No threshold in
   §1.2 is re-picked after seeing a result.
4. **No prediction is re-scored to a pass.** A failed prediction is reported at
   full size and its uncomfortable reading is the one carried forward.
5. Rule 22: no year outside {2023, 2024, 2025} is read, in any artifact.

---

## §4 — G-DRIFT (rule 29(b)): `90b2ef51 → 95739d60`, recorded BEFORE anything is solved

`git diff 90b2ef51 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source
data/raw/reference`: **26 files, +450 / −330.** Every hunk is **INERT for a
CAISO backcast**, with its reason:

| change | why it cannot reach this ISO's backcast solve |
|---|---|
| `data/offer_curves.py` (+71) — `_with_intermediate_phys` | gated `config.miso_intermediate_gas_offer_margin` (default `False`, absent from the keeper's `run_config`) **AND** `config.iso == "MISO"`; returns the same curve object when off |
| `config/scenarios.py` (+136) | the field above at its default; `ccs_retrofit_capex_co2_scaling` default flip `False → True` — its ONLY consumer is `capacity_evolution/ccs.py::apply_ccs_retrofit`, which returns at `if year < ccs_retrofit_available_year` (2028) before reading it; `mode="backcast"` never enters capacity evolution at all |
| `config/iso_configs.py` (+126) | `default_scenario_overrides` for **MISO** (`adequacy_accounting_ratio_dated_net`), **PJM** (accreditation / DR / supply-clearing) and **NYISO** (requirement devintage) — capacity-market fields on other ISOs; `_caiso_config` untouched |
| `results/cache.py` (+34) | docstring: the cache-epoch ledger entry for the D60 key flip; a key advance is a cache MISS, never a changed number, and a `--replay-bundle` writes to its own `--out-dir` |
| `config/constants.py` | forecast-only capacity-market imports; ERCOT `NUCLEAR_MONTHLY_CF_BY_YEAR[2022]` (other ISO, out-of-window year); three constants DELETED with **0 references** in `src`/`scripts`/`tests` (`CCS_RETROFIT_HR_PENALTY_REFERENCE`, `ERCOT_SCED_INTERVALS_PER_HOUR`, `ERCOT_DC_TIE_CAPABILITY_MW`) |
| `capacity_evolution/ccs.py`, `evolve.py` | docstrings only |
| dead-code deletions: `benchmark_corridor.load_benchmark_corridor`, `eia923.plant_state_map`, `fleet/eia860._committed_vintage_years`, `floor_mechanisms.tag_raised`, `miso_outages.FORECAST_PARQUET`, `outages.read_clean_outages` + `CT_DEPLOYMENT_CSV`, `reserve_requirements.load_reserve_requirements`, `data/som_conduct.py`, `pipeline/result.py` (`YearSolveResult`), `results/metrics.py`, `plant_taxonomy.is_fossil`, `paths.TX_UNIT_OUTAGES_CSV` | grep at HEAD: **0 live references** to every deleted symbol (the single hit on `load_reserve_requirements` is the comment that records its deletion); `pipeline/__init__.py` drops the export of the deleted placeholder |
| `scripts/lib/outage_detect.py` (+17) — stack-duplicate merge in `build_merit_order_panel` | reached only from `scripts/data/derive_campd_unit_outages.py`; `CAMPD_STACK_DUPLICATE_UNITS` registers facility **8906 (NYISO) only**, so the mask is empty and the panel byte-identical for every CAISO extract |
| `scripts/lib/{reldeploy_zonal_report,session_score,zonal_sufficiency}.py`, `pipeline/reference.py` | docstring path renames only |
| `data/raw/reference/nyiso-market-solar-capacity.csv` (+65) | NYISO-only artifact, 2022 rows |

**Conclusion: G-CTRL form 4 is VALID at this HEAD — the committed keeper
`caiso251_arm_nomargin` is the control for any arm this session might solve,
and the prior keeper `caiso246_b1_spot_coverage` is the control for the
phase-0 differencing.** As at caiso-251, this is a reading of code and inherits
my reading; it is falsifiable by re-running the same diff.

---

## §5 — TWO HOUSEKEEPING OBSERVATIONS, RECORDED, NOT ACTED ON

* **All three CAISO bench parts read STALE at HEAD** (`check_bench_freshness.py`:
  part fingerprint `4e78c85427bb` vs builder `b2f21b9a00d3`). Cause: commit
  `677b605a` (PR #4808, the dead-code cleanup) changed **one comment line** in
  `scripts/render_calibration_html.py`, which is a `BUILDER_SOURCES` member,
  and the fingerprint is content-derived. It is cross-ISO (the Y-8 re-render
  `a725bfc3` stamped all 14 parts at `4e78c85427bb`) and carries no numeric
  change; it is not CAISO's to repair alone and is filed alongside the handoff's
  item G.
* **The handoff's named reusable instruments were DELETED on main by the same
  PR** (`_caiso244_import_level_anatomy.py`, `_caiso247_*`, `_caiso249_*`,
  `_caiso250_*`, `_caiso251_*`, `caiso168_storage_bid_phase0.py`) under the
  owner's "deleted, never archived; git history is the record" instruction.
  This session reads them from `d6891edd` where it needs a construction and
  writes its own probe; it does not restore them.

---

## §6 — DELIVERABLES

This PRECOMMIT (pushed first); the probe + JSON; a FINDING; the
`docs/calibration-log/caiso.md` entry; a matrix-shard evidence append on the
cell the carrier lands on (rule 28(b)); and, only via a registered addendum, any
arm with its screen, full-span bundle, post-solve chain and same-session
registration (rules 12 / 15 / 16 / 29).
