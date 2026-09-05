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

---

## ADDENDUM A — THE ARM: DISARM `caiso_dsw_daytime_evening_trim` (restore the daytime WEIM clean-transfer window to hod 6–21), screened on 2025 FIRST

**Registered BEFORE the override is coded and before any year is solved.** Owner
instruction (2026-09-05, this session, verbatim): *"tackle the next run in this
session that you think could address the 2025 miss on C4. Do not run a control
and only run 2025 first to see if it passes then if it does run 2023 and 2024."*

### A.1 — Why this arm, from the phase-0 evidence

FINDING-caiso252 §3.1 put the C4 2025 cell's counterpart at the model's import
diurnal shape: hour for hour the CC over-generation at **18–23** is an import
shortfall (2025, hod 18–21: **−590 / −925 / −970 / −894 MW** vs EIA-930 net; ≈
**−1.24 TWh** over the four hours; CC error **+1,425 / +1,423 / +1,379 / +1,402
MW**). The zero-LP structural read of the import stack shows WHY: the WEIM
clean-transfer depth rows cover **hod 0–5** (overnight, caiso-93), **hod 6–17**
(daytime, caiso-94 as trimmed by caiso-97) and the surplus-trigger hours
(caiso-87) — **no at-hub row exists for 18–23**, and the spot ladder there
(Malin + $5 wheel; Palo Verde + $4 wheel + border carbon on the gas rungs) is
priced above the evening λ. The firm blocks are already floored at 85 % of
capability in those hours (`_caiso252_firm_aah_phase0.json`: an
availability-assessment-hour price-taking arm on them would deliver **0.16
TWh** in 2025 — killed at phase 0, not coded).

**The trim's own record supplies the new evidence rule 28(a) requires to re-test
an owner-armed cell.** caiso-97 trimmed the daytime window 6–21 → 6–17 because,
on the 2026-07-18 keeper, the model OVER-imported in the evening (hod 17–21
**+1.9 / +2.1 / +2.2 TWh/yr** above EIA-930; FINDING-caiso94 §4A: evening ×
non-autumn "model UNDER-prices the peak, a clean-import lever there
overshoots"). The measured admissibility of the row itself was never in
question — §4A measured the evening 18–21 raw-hub spread **clean (0 % wedge)** in
autumn and clean in non-autumn. On the current keeper the sign has **reversed**:
the evening is UNDER-imported by 0.6–1.0 GW and CC over-generates in exactly
those hours. The condition that justified the trim no longer holds; the
condition that admits the row (measured no-wedge) still does.

### A.2 — The arm, exactly

`--replay-bundle results/calibration/caiso251_arm_nomargin` plus **ONE**
recipe delta: the recorded override bag's `caiso_dsw_daytime_evening_trim`
**True → False**. Effect (`inject_caiso_dsw_daytime_clean`, unchanged code):
the `WECC_DSW_DSW_daytime_clean` row's window becomes hod 6–21 and its depth
the already-committed untrimmed measurement `CAISO_DSW_DAYTIME_CLEAN_DEPTH_BY_YEAR`
(5,441 / 5,762 / **5,998** MW; p95 corridor net import over the 6–21
trigger-OFF window, CV 0.040, LOYO ≤ 8.1 %, `derive_caiso_daytime_clean_depth.py`
— frozen, not re-derived here). **Zero new parameters, zero new fields, no
derive re-run.** Priced at the raw Palo Verde hub, EF 0, no wheel, `pmin` 0 —
a capability the LP clears below, never a floor (no D-2 row). A
`run_replay_bundle` override + CLI flag (`--caiso-dsw-daytime-evening-trim /
--no-…`, default `None` = the recipe's value) is added mirroring the
caiso-251 `gas_offer_margin` override; with the flag absent the path is
byte-identical.

**Phase-0 footprint (`scripts/probes/_caiso252_evening_trim_phase0.py`, two
on-recipe rebuilds differing in this one override):** the disarm ADDS
**3,770 / 3,755 / 3,645 / 3,371 MW** of capability at hod 18 / 19 / 20 / 21 in
2025, armed in **355–361** trigger-OFF hours per evening hour (2,965 armed
hours in all; the 6–17 hours move by 30–210 MW from the depth change, 1,528 h);
no other WECC row moves; the unit count is identical. At the keeper's
committed duals the row would clear in **35 %** of its armed hours —
**1.562 TWh** in 2025 (hod 18: 1,255 MW mean; 19: 769; 20: 827; 21: 1,045).
2024: 1.236 TWh; 2023: 1.032 TWh. **2025 carries the largest footprint**, so it
is the rule-29(a) screen year on the footprint criterion as well as by the
owner's instruction.

### A.3 — Admissibility

* Rule 1 `[R-STRUCT]`: the row is the WEIM clean-transfer construction the
  lane has carried since caiso-87/93/94; the question is only its window.
* Rule 13 `[R-MEASURED]`: the depth is a frozen measured percentile of the
  corridor series; the window is the caiso-94 daytime band as originally
  registered; the hub price is measured and forward-substitutable. No
  same-year outcome enters.
* Rule 14 `[R-ACCURATE]`: the measured no-wedge admissibility (§4A) holds in
  the evening; the trim was a model-state judgement, not a measurement.
* Rule 19 `[R-ONE-MECH]`: nothing is stacked — one row's window widens; the
  overnight (0–5) and surplus rows are untouched; the 22–23 gap is NOT touched
  (a second change to a differently-charted window, queued, not bundled).
* Rule 23 `[R-FROZEN-DERIVE]`: no derive is re-run; the untrimmed depth is the
  committed 2026-07-17 measurement.
* Rule 28(a): re-testing an owner-armed trim on **new, sign-reversed
  evidence** (A.1) and with the trim's own pre-registered rationale as the
  falsifier (A.5, G-OVERSHOOT).

### A.4 — Direction hazard, declared

More evening import at the raw hub → evening λ falls → **C3a favourable**
(model too high). **This is the SEVENTH consecutive favourable direction** for
the CAISO lane (caiso-241/242/243/246/246§5.2/251, now 252). Declared here:
**C3a is EXCLUDED from the promotion basis in both directions, and so is C4**
(the target). The owner's continuation criterion (A.6) governs whether 2023
and 2024 are solved; it does not promote anything.

### A.5 — Gates

| gate | passes iff | kind |
|---|---|---|
| **G-FOOT** | ≥ 90 % of the `DSW_daytime_clean` row's ADDED energy (arm − keeper, 2025) lands in hod 18–21; no non-WECC row's capability differs from the keeper's | structural, STOP |
| **G-DIR** | the row's 2025 energy rises by ≥ 0.5 TWh AND CC_REGULAR's 2025 dispatch in hod 18–21 FALLS | structural, STOP |
| **G-OVERSHOOT** (the caiso-97 objection, re-armed as this arm's falsifier) | the arm's 2025 evening (hod 18–21) net import lands within **[measured − 0.5 TWh, measured + 0.8 TWh]** of the EIA-930 hod-18–21 total (the keeper sits at −1.24). Above +0.8 the trim's original justification stands and the arm is REFUSED regardless of C4 | structural, STOP |
| **G-NOBREAK** | on 2025, computed from the bundle's own sidecars against the committed bench: no C1 class row moves from inside its band to outside it; the load-weighted price stays inside the ±10 % C3a band | structural, STOP |
| **G-OWNER** | the owner's continuation criterion: 2025 gas-fleet C4 recomputed by the scorer's own `_cems_gas_hourly_fit` construction from the screen bundle's `dispatch/2025_P1.parquet` (plant series built exactly as `render_calibration_html` builds `mw_pc`) reads **NRMSE ≤ 0.30 and r ≥ 0.70**. PASS → solve 2023 + 2024 into the same bundle; FAIL → stop, report | owner-directed continuation, NOT a promotion basis |
| G-HOLDOUT | every solved year ∈ {2023, 2024, 2025} | — |
| G-C6/C8/DOF | attested C6, C8 PASS, DOF ledger residual count does not rise (the trim is not a ledger row) | governance |

G-CTRL form 4 is VALID (PRECOMMIT §4, every hunk INERT); the owner has also
ruled no control. The only LIVE hunk at solve time will be this session's own
override plumbing, inert when the flag is absent.

### A.6 — Predictions, written to bind

| # | prediction | uncomfortable reading if it fails |
|---|---|---|
| **P-A1** | the row's 2025 energy rises by **[0.8, 2.0] TWh** (the phase-0 1.56 at fixed duals, shaded down because the arm lowers the very λ it clears against, up for the 6–17 depth change) | < 0.8: the LP re-prices the evening below the hub and the row barely clears — the deficit is not this row's; > 2.0: the phase-0 duals understated the margin |
| **P-A2** | CC_REGULAR 2025 dispatch in hod 18–21 falls by **≥ 0.5 TWh**, and CT_PEAKER's by ≥ 0.05 TWh | the import displaces storage or ST_GAS instead of CC — the C4 counterpart was mis-named |
| **P-A3** | **OVERSHOOT at the window's first hour**: the arm's hod-18 import lands ABOVE measured (the keeper's hod-17 already sits +1.6 GW over), while hod 19–21 land at or below measured; the 18–21 block lands within [−0.5, +0.8] TWh (G-OVERSHOOT passes) | block > +0.8: caiso-97 was right on this keeper too, arm refused |
| **P-A4** | 2025 C4 gas NRMSE lands in **[0.285, 0.300)** — PASS by a small margin (the 22–23 and 05–06 errors are untouched by construction) | ≥ 0.300: the evening is not enough of the cell (owner stop); < 0.285: I under-sized the evening's share |
| **P-A5** | 2025 C3a falls by **0.3–1.0 pp** and stays PASS (reported, excluded) | > 1.0 pp: the row is setting λ in far more hours than the 35 % phase-0 count |
| **P-A6** | the 2025 `import` klass rises by 1.0–1.8 TWh; C1's 2025 rows keep their status (CC/CT SKIPPED on preliminary 923; no PASS→FAIL) | |
| **P-A7** | if 2023/2024 are solved: C4 stays PASS in both (2023 ≤ 0.285, 2024 ≤ 0.264 — i.e. it does not WORSEN either), and no load-bearing criterion regresses to a new failure | a 2023/2024 C4 worsening means the window helps only where the evening is under-imported — the arm would then be year-specific, which is the caiso-97 objection in another form |
| **P-A8** | the 2025 22–23 CC error is essentially unchanged (within ±150 MW) — the arm does not reach the night gap | a large move at 22–23 means the LP re-commits CC across the boundary |

### A.7 — Promotion rule, registered now

The arm is a keeper candidate **iff** (a) G-FOOT, G-DIR and G-OVERSHOOT pass on
2025, (b) 2023 and 2024 are solved into the same bundle (rule 16) with no
load-bearing criterion regressing to a NEW failure in any year, and (c) the
governance gates hold. **C3a and C4 do not enter (a)–(c).** If G-OWNER fails
on 2025 the full span is not solved and the keeper is unchanged — the owner's
instruction — and that is reported as the result, not re-run. If G-OVERSHOOT
fails the arm is refused **even if C4 passes**.

### A.8 — Stop rule

1. G-FOOT / G-DIR / G-OVERSHOOT / G-NOBREAK failing on the 2025 screen ⇒ the
   remaining years are never spent; the screen bundle is deleted after its
   numbers are extracted to `_caiso252_screen2025.json` (rule 29; ~90 MB).
2. No second flag, no window other than 6–21, no depth re-derive, no touch of
   the 22–23 gap, no tuning under any outcome.
3. No gate is re-run to a pass or redefined after its result.
4. The screen bundle is never registered and never quoted as a keeper number.
