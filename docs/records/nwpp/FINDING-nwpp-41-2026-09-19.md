# FINDING — NWPP-41: the C1 coal-taxonomy seam, closed by structure; C4 routed

**Lane** NWPP-41 · **DATA PROFILE** nwpp · **2026-09-19**
**Keeper** `2026-09-19-nwpp41-coal-taxonomy-own` · bundle `results/calibration/nwpp41_span_A`
**Control** lane NWPP-40's committed bundle, rule 29(b) form 4, **no control solve**

---

## §0 Result

**C1 fuel-mix went FAIL (5 rows) → PASS. C4 coal hourly shape still FAILS and was deliberately not
pursued.** Both were pre-registered in `PRECOMMIT-nwpp-41-2026-09-17.md` §A1.3 and both landed as
written. NWPP now has its **first keeper**, promoted on the owner's pre-solve ruling *"Promote after
the C1 fix lands"*.

**The determination is `NOT-YET`, and a keeper is not a calibration.** C4 is the sole failing
criterion; the basis shrank from `{fuelmix, dispatch_corr}` to `{dispatch_corr}`. NWPP is also
**PRICE UNSCORED** (rubric v3.8) — no admissible hourly price series exists, so C3a/C3b/C3c are not
scored in any year and nothing here certifies a price level, shape or tail. NWPP gets no `complete`
entry and no `frontier`; both are separate owner acts.

| criterion | tier | NWPP-40 control | NWPP-41 |
|---|---|---|---|
| C1 fuel-mix by class | LOAD | **FAIL, 5 rows** | **PASS** (18/18 all, 14/14 free) |
| C2 system volume | LOAD | PASS | PASS |
| C3a / C3b / C3c | LOAD / SUPP | SKIPPED (no price series) | SKIPPED |
| C4 dispatch correlation | SUPP | FAIL r .511 / .535 / .475 | **FAIL** r .539 / .546 / .502 |
| C6 governance | PROT | PASS | PASS |
| C8 forced-energy share | PROT | PASS | PASS (0.0 % forced, every class, every year) |
| C5a CO2 *(report-only)* | — | −65.9 / −58.7 / −54.8 % | −15.1 / −23.7 / −21.4 % |
| **determination** | | NOT-YET | **NOT-YET** |

---

## §1 What was wrong: two defects at one seam, both plumbing

### 1.1 C1 — the model dispatched a class the benchmark has no row for

`data/raw/_processed-legacy/coal_supply_NWPP.csv` **had never been derived**. So
`coal_supply_class` returned `""` for all 17 NWPP coal plants, and
`run_calibration_full.py:414` — which calls `_coal_supply_class(code)` with **no fuel_code**, leaving
its third fallback arm dead — binned every one of them to the bare class **`COAL`**. The benchmark
passes the EIA-923 row's *own* fuel code to the **same resolver** and therefore itemizes `COAL_PRB` /
`COAL_BIT` / `COAL_WC`. Five C1 rows failed on that asymmetry alone, with the dispatch innocent.

**The seam was bigger than the coal rows.** `calibration_verdict._gen_totals` computes the model's
total by summing over **benchmark** keys (`m_gen = sum(gm.get(g, 0.0) for g in cf)`), so the model's
entire coal output was excluded from its own denominator and *every other class's share read high* —
which is why 2024 `CC_REGULAR` read **+3.6 pp** in the control and reads **+1.4 pp** now.

The file is now derived: **17 rows, md5 `4bc7f9a61724ec4562599230ca77e4c6`, 9 prb / 6 bituminous /
2 waste, 0 unresolved**, by `scripts/data/derive_coal_supply.py --iso NWPP --census-vintage 2023 2024
2025`.

### 1.2 Rule 25 `[R-ISO-SCOPE]` — the PRB price proxy was pooling Texas

Found while fixing C1 and fixed with it, because the same derived file feeds both.
`_prb_monthly_actuals` pooled `data.coal.COAL_PLANT_SUPPLY`, **every plant of which is in Texas**, so
an NWPP coal plant with no EIA-923 Schedule-2 filing of its own priced against **ERCOT's** delivered
PRB cost.

| $/MMBtu delivered PRB | 2023 | 2024 | 2025 |
|---|---|---|---|
| ERCOT's pool (what NWPP was using) | 1.818 | 1.760 | 1.622 |
| NWPP's own four reporters | **2.463** | **2.134** | **2.066** |

This is not a corner case for this footprint. **Colstrip and Centralia file no price in any year** —
2,377.3 of 8,910.2 MW of coal, **26.7 %** — so the proxy prices a quarter of the coal fleet.

**Rule 14 `[R-ACCURATE]` is the basis, never the residual.** Rule 14's misalignment exception cannot
apply: this is the same measured quantity, for the right market, instead of the wrong one.

### 1.3 Proven zero-LP before any solve, and confined exactly

`scripts/probes/_nwpp41_coalrank_phase0.py`, via the sanctioned `replay_keeper.run_year_kwargs` →
`run_year(..., fleet_only=True)` path on the control's own recipe:

- **non-coal offer max|Δ| = $0.0000000000**, 0 rows moved
- **`pmax` and `availability` max|Δ| exactly 0**, all three years
- only the plants with no filing of their own move: **Colstrip (6076), Hardin (55749)** in every
  year, **TS Power (56224)** additionally in 2025 (its 2025 receipt is not yet filed)
- Colstrip committed offer 34.252 → 27.226 / 34.550 → 25.640 / 34.850 → 25.640 $/MWh; coal
  capacity-weighted mean offer −0.653 / −0.828 / −0.886
- against the **unscoped** alternative Colstrip would have gone to 23.766 / 23.016 / 21.560 — the
  scoping is worth **+$2–4/MWh** and is the whole point

The C1 half was likewise proven zero-LP on the committed control bundle: **C1 5 FAIL → 0 with the
dispatch byte-identical**, C2 and C4 byte-identical. No LP was needed to establish the fix.

---

## §2 The solve, and why no control solve was spent

ONE shard, ONE `--year 2023 2024 2025` invocation, years sequential inside it (rules 12 / 16
`[R-ALLYEARS]` / 32(b) `[R-SHARD]`). **The parent ran no LP** (rule 32(a)): phase 0, composition,
benchmark rebuild, diagnostics, attestation, scoring, registration and promotion are all zero-LP.

**Provenance, verified rather than assumed.** Pinned to the immutable
`666343a2bf86f204c5ca6c672a680da32150a640`; the shard added **exactly three** commits (two per-year
evidence pushes, then the bundle at `1fb4b6b5c680ca5ae0ef9375eb11b7cbbb08d64d`) and **never rebased,
pulled or synced** — confirmed with `git merge-base --is-ancestor`.

**Control differencing, form 4.** `scenario_config` differs from the control in **exactly two
fields**: `coal_prb_proxy_own_iso` (absent → `True`, the arm) and
`neiso_coldsnap_derate_dualfuel_unswitched` (absent → `False`, NEISO-gated, at its default). The
second is the `G-DRIFT` **INERT** classification rule 29(b) asks for, so no LP was spent establishing
HEAD drift.

**Real per-pass cost, from the runner's own log** (`NWPP41-attempt2-solve-log-excerpt.txt`):

| pass | seconds | minutes | simplex iterations | iters/s | vs NWPP-40 |
|---|---|---|---|---|---|
| 2023 P0 | 1,220.7 | 20.3 | 515,050 | 421.9 | 0.99× |
| 2023 P1 | 7,043.0 | 117.4 | 588,306 | 83.5 | — |
| 2024 P0 | 1,702.7 | 28.4 | 347,060 | 203.8 | — |
| 2024 P1 | 18,406.5 | 306.8 | 1,046,904 | 56.9 | **2.26×** |
| 2025 P0 | 2,187.2 | 36.5 | 360,716 | 164.9 | — |
| 2025 P1 | 14,291.5 | 238.2 | 1,006,273 | 70.4 | **0.90×** |
| **span** | **44,960.5** | **749.3** | 3,864,309 | | **1.36×** |

Peak RSS **4.78 GiB**, no swap used. Container preflight WARNED that ceiling 13.36 + 5.0 GiB swap =
18.4 GiB sat below its 24 GiB target; irrelevant here at 4.78 GiB peak, but recorded because it would
matter for a per-plant MISO/PJM year (rule 32(c)(8)).

**The per-pass penalty is genuinely non-uniform — 0.99× / 2.26× / 0.90× — and 2024 P1 is the sole
outlier.** Its iteration count is **1.8× 2023 P1's** *and* its iterations/s is the slowest of the
six, so 2024 P1 was both a harder LP and a slower one. **No mechanism is attached to that**, and none
is claimed; it is reported as an observation about this year's LP (rule 1 `[R-STRUCT]`).

---

## §3 What was pre-registered, and one surprise that is not a claim

Both §A1.3 predictions landed: **C1 5 FAIL → 0** and **C4 still FAIL**. Neither is a surprise.

Two things moved that were **not** predicted, and both are **side effects reported, not achievements
claimed** — this lane touched no dispatch mechanism, and rule 1 forbids reading a residual move as a
result:

1. **C4's coal correlation improved** — r 0.511 / 0.535 / 0.475 → 0.539 / 0.546 / 0.502 and NRMSE
   0.321 / 0.408 / 0.451 → 0.301 / 0.397 / 0.432. Still FAIL in all three years. Re-pricing two
   plants shifts coal's merit order, so a small shape move is expected; it does not touch the
   structural cause in §4.
2. **Reported-only C5a CO2 improved sharply** — −65.9 / −58.7 / −54.8 % → −15.1 / −23.7 / −21.4 %.
   The **likely** mechanism is per-class emission-rate coverage restored by the taxonomy fix, since
   *less* coal dispatch would push the error the **other** way. Stated as the likely mechanism rather
   than an isolated one — no ablation was run — and it changes no determination, because C5a is
   reported-only under rubric v2.9.

**Rule 21 `[R-DOF]`: zero free parameters added.** `build_dof_ledger.py` emits **3 entries /
3 residual** on this bundle, **identical to the control's**. The arm is a boolean selecting *which
measured series* the fallback proxy pools, so its identification is **measured-physical**, not
residual. It was set ex ante in the PRECOMMIT before any solve and **never swept** — and there is no
NWPP price residual to sweep against.

**Gate G5 / rule 1 carve-out: NONE, and verified from dispatch rather than asserted.** Three groups
in the shared config carry non-unity bands — `CC_INTERMEDIATE`, `CT_INTERMEDIATE`,
`ST_GAS_INTERMEDIATE` — and all three carry **zero NWPP energy in all three years**, so no band
touching this footprint was moved. `scripts/gen_nwpp41_attestation.py` machine-checks that against
the bundle's own `hourly/class_hourly_<year>.parquet` and **refuses** a bundle that reads otherwise.
`econ_low_share` 0.55 is a **structural share**, which rule 1 excludes from the band channel by name.

---

## §4 C4 — diagnosed, ROUTED, not attempted (owner ruling)

The desk ruled *"route it, don't attempt it here"*, and this lane did not reach for the residual.

- The coal offer stack is **bimodal**: a **$4.50 must-run tranche in the money 100 % of hours**
  against **$37.7–42.8** for everything else, versus a **$26.15 mean price**. So **~90 % of model
  coal is price-insensitive**, and **~4,600 MW of available coal sits out of merit 87 % of hours**.
- **Availability was measured and ruled out** as the cause.
- The measured fleet's midday trough **deepens with solar** — peak/trough **1.21 → 1.32 → 1.40**
  across 2023–2025 — where the model reads **1.02**. The model has essentially no diurnal coal shape.
- **D-1** confirms it: FAIL on `COAL` in all three years (off-peak `cv_ratio` 0.016 / 0.022 / 0.075),
  plus `ST_GAS` in 2025.
- **The successor is blocked on `bin_assignments_NWPP.csv`**, which is absent for every legacy-bin
  ISO (NWPP, SPP, SOCO). That is the routed item, and it is a data/tooling gap, not a tuning one.

---

## §5 Carried at full magnitude, absorbed nowhere

1. **Coal volume is materially under-dispatched.** 2025 model coal **27.21 TWh vs 42.26 actual**; the
   C2 2025 coal row reads **−28.8 %** and was **SKIPPED** on the preliminary EIA-923 vintage, so it
   did not gate. This is the same root cause as C4 and is the bigger half of it.
2. **Energy balance −10.02 TWh** in 2025 (model gen 288.81 vs EIA-930 net gen 298.83) against a
   ±3.0 tol — the served-interchange construction lane NWPP-40 declared.
3. **Chief Joseph 2025 pond-balance dual** sits at a constant **−325.17 $/kcfs·h for 5,808 of 8,760
   hours** with pond = 0 and spill = 0, where 2023 and 2024 show zero plant-hours with |dual| > 1
   anywhere. Unchanged by this lane and still the first cascade-specific question for the next one.
4. **NWPP-SNV VOLL hours 23 + 34** — a path-rating question, never a VOLL one.
5. **Every NWPP-40 disclosure is inherited verbatim** into this attestation and still applies: the
   price-unscored posture, the G-A3 amplitude miss, the 16 %-coupled hydro set, the 2025 data posture
   (263 conventional-hydro plants carrying 2024 water), the two-regime PRM mismatch, the demand
   convention and its 30 raw-feed artifacts, the interim $2,000 VOLL, the NW↔OR Tier-3 placeholder,
   and the Colstrip / Centralia fuel-price gap.

**The same defect reaches other ISOs and was deliberately NOT fixed here**: **MISO (12 affected
plants), PJM (2), SPP (3–5)** likewise price their unfiled coal plants against Texas PRB deliveries.
Rules 25 `[R-ISO-SCOPE]` / 28(d): a verdict in one ISO never fills another's cell, and each target
lane derives its own rank file from its own market's data. Their matrix cells stay **`O`** with the
affected plant lists recorded.

---

## §6 The promotion (rule 35 `[R-PROMOTE]`)

Executed in order, with each gate where the rule puts it:

1. **35(b) — year union enumerated BEFORE the delete**: `{2023, 2024, 2025}`, from the single prior
   registered run. The incoming keeper covers it exactly, so **35(c) holds by construction** — no
   held-out year, nothing to stamp, nothing outstanding.
2. **First-keeper, not a supersession**: no `keepers/NWPP.json` existed, so 35(a)/(e) had no outgoing
   keeper's three stores. `keepers/index.json` gains `NWPP` on the README's *"ISO added"* reading —
   a first keeper is not a promotion edit — **said out loud** rather than left to inference.
3. `build_status.py --iso NWPP` → `[NWPP:NOT-YET]`.
4. **35(e) — `audit_keepers --iso NWPP` run BETWEEN promotion and prune**: E1 passed (incoming stores
   resolve) and **E13 failed exactly as designed**, naming the superseded run. **After** the prune:
   **0 failures, 0 warnings**.
5. `prune_iso_runs.py --iso NWPP` removed the three stores together. **No `--force-uncite` needed**:
   the only citation was in the mechanism matrix, which does not block — and it was rewritten to cite
   the **lane** first, so nothing dangles. The tracked attempt-1 launch log is **deliberately left**:
   35(d) says the delete touches the three stores and nothing else.
6. **Rule 28 duties, same session**: NWPP.js gains its first keeper/gates stamps;
   **`hydro_cascade_coupling` O → K** (the promotion ruling arrived and the coupling rides armed in
   the keeper — the cell flips on the **ruling**, not on any residual); `coal_prb_proxy_own_iso` `K`
   re-stamped with solved evidence; both prior cell texts kept verbatim; `§5.9` prose header
   re-stamped, and `check_mechanism_matrix` now reports headers match every keeper shard.

**Two steps Addendum 9 listed that are no-ops, stated rather than silently skipped**:
`calibration-complete.json` has **no NWPP entry to re-key** (declaring an ISO complete is a separate
owner act, and an ISO reading NOT-YET is not a candidate), and `program-status.json` has **no NWPP
forecast stamp** for the README's R-T duty to re-key.

**Parity gate: zero NWPP findings.** Its two REDs — `caiso279_ablate_dswcouple_span` and
`soco15_spp_arm` — are **committed on `origin/main`** and belong to the CAISO and SOCO/SPP lanes
(the CAISO-286 session lists the first among its own pending decisions). Reported and **not touched**:
a lane prunes its own ISO only, and rule 31 forbids deleting another lane's result.

---

## §7 Corrections to this lane's own interim readings

Recorded because the lane already retracted one claim mid-run (PRECOMMIT §A4.1) and the discipline
only means anything if it keeps applying.

1. **My projected span ran high.** I projected 1,080–1,220 min from status elapsed. The runner
   reports **749.3 min** of LP (≈820 min wall; the gap is preflight, loading, benchmark and writes).
   The status line's minutes are **not** LP-pass time.
2. **My per-pass ratios were estimates, and two of three were wrong in direction.** 2024 P1 I
   estimated 2.24× and it was **2.26×** — good. But I said attempt 2 was "tracking **faster** than
   attempt 1" on that pass (2.03× vs 2.27–2.41×); at 2.26× it is **inside** attempt 1's band, not
   below it. And I never estimated 2025 P1, which came in at **0.90× — faster than the reference**,
   against my 2.0–2.5× projection.
3. **A pre-registered death test produced a false positive.** `worker_epoch` jumped 1 → 5, which I had
   written down as the death signal. The restarts happened **after** the push, while the shard sat
   idle. **The tree, not the epoch, is the authority**; had I read the epoch alone I would have
   declared a completed solve dead.
4. **The shard's own "% done / N min left" is elapsed ÷ 264 restated**, not solver progress — caught
   at the 12:21Z check-in before it produced a claim.
5. **My first signature check was wrong twice**, and the bundle was fine both times: I looked for
   `hydro_backfill_year` / `hydro_eia930_monthly` in `scenario_config` when they live in `meta.json`,
   and I counted `econ_low_share` as a non-unity band when rule 1 excludes structural shares by name.
6. **Addendum 9 §A9.2 ordered scoring before registration.** The scorer reads *committed* artifacts
   including the per-(ISO, year) benchmark parts that `dashboard_add_run` writes, so **registration
   comes first**. Corrected here.

---

## §8 Retrievability (rule 34(e))

- **Bundle**: committed to this branch in the NWPP-40 **slim 20-file shape** (attestation, the five
  `hourly/` sidecar families × 3 years, diagnostics, meta, metrics, run_config).
- **Full 36-file bundle**, including `dispatch/{2023,2024,2025}_P1.parquet`, is recoverable at
  `git checkout 1fb4b6b5c680ca5ae0ef9375eb11b7cbbb08d64d -- results/calibration/nwpp41_span_A`
  (rules 34(a) / 33(d) — full sha, never a branch name).
- **Solve log excerpt** rescued to `docs/handoffs/NWPP41-attempt2-solve-log-excerpt.txt` from
  `57dd26098604a627aa956d117e4bb02e425613f3` before the shard was archived (rule 33(f)(1)).
- **A promotion from this state costs zero re-solves.**

## §9 The two-attempt history

**Attempt 1 was lost to a platform restart** mid-2025-P1 after ~13 h; a pre-registered liveness test
caught it. Its 2023+2024 survived at `14f485ce21b322d600b67aecfe7ef2da41fd87a9` and **passed the
acceptance test**. Reuse was foreclosed — verified in code, not assumed: `plan_reuse_solved` gates on
`dispatch/<year>_P1.parquet` **and** the bundle-root `system.parquet`, which the runner writes only
after the last year. Cost was stated, the owner ruled *"relaunch full span, fresh container"*, and
attempt 2 ran clean.

**Cross-attempt determinism was confirmed on two years before the third finished**: 2023 and 2024
reproduced attempt 1 to four decimals on every coal class. The attempt-1 loss cost wall-clock and
nothing else.

Housekeeping: both keep-alive poke triggers deleted; the shard archived after fetch + checkout +
verify (rule 33(a)) with its full sha recorded above (33(d)).
