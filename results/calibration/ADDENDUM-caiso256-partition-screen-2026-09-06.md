# ADDENDUM to PRECOMMIT-caiso255 — caiso-256 RESUMES the granted CT-only partition object. **The corpus re-fetch the handoff named as the only blocker is NOT needed: the repaired artifact pair is already on `main` (`df277e89`, PR #5133).** G-DRIFT is extended `d8b64997 → HEAD` by MEASUREMENT with the artifact reverted (every LP input bit-identical), so the ONE live hunk on the chain is the arm itself; S-1's "implied displacement" is fixed to a number BEFORE the screen; the comparator is the keeper RE-SCORED at HEAD. **Pushed BEFORE the screen solve is launched.**

**Session caiso-256 (second object), 2026-09-06.** Branch
`claude/caiso-storage-over-cycling-ymodu3`, HEAD `49011cc9` on `main`
`ba894c9c`. Keeper **`2026-09-05-caiso-252-b1-notrim`** (`caiso252_b1_notrim`,
`git_sha` `fa23c1f7`) UNCHANGED, DETERMINATION **CALIBRATED**. Rule 22:
2023–2025 only; no `complete`/`final` marker; freeze ACTIVE. The owner's grant
of `FINDING-caiso254 §4` OPTION 1 and everything in
`PRECOMMIT-caiso255-ct-only-partition-adoption-2026-09-06.md` and its four
addenda stand unchanged; this document adds and corrects, it relaxes nothing.

---

## §1 — STATE CORRECTION: THE ARTIFACT IS COMMITTED, THE SCREEN IS NOT RUN

The handoff (and `PRECOMMIT-caiso255b §7`) record that the only blocker is a
full OASIS re-fetch. That was true of the caiso-255 *continuation* instance,
which was fetching into a container that died. It is not true of `main`:

* the **first** caiso-255 instance completed the fetch (1,095 / 1,096), the
  `--pass1` store and the derive, named the screen year **2023** (`argmax_y F`,
  `ADDENDUM-caiso255-screen-year`, phase-0 artifact
  `_caiso254_partition_footprint_phase0.json`, `channels_agree: true`), and
  **committed the repaired pair** — `caiso_offer_curve_measured.json`,
  `caiso_offer_surface_condbinned.json` (+ the report-only
  `caiso_offer_surface_summary.csv`, consumed by no model path) — as
  `df277e89`, merged to `main` in PR #5133 at 07:36 UTC;
* that commit's own message is the governing record: *"ADOPTION IS PENDING
  THE RULE-29 SCREEN … If the screen's structural gates kill the arm, this
  artifact is reverted and the frozen 2026-08-02 construction stands — that is
  the registered stop rule, and this commit is the working record, not an
  adoption."* The container was lost before the screen launched.

Consequences, stated so they cannot drift:

1. **The arm is `main`.** A keeper replay at HEAD *is* the arm; the frozen
   construction is recoverable byte-exactly at `fa23c1f7` and is what
   `results/calibration/caiso252_b1_notrim` solved on.
2. **The keeper's committed bundle is therefore no longer reproducible at
   HEAD** — a replay would consume the repaired pair. This is a live fact
   about `main`, disclosed here; it changes no registered number.
3. **Nothing of the grant is spent or widened.** Phase 0, the screen year and
   the gate set are the merged ones; this session runs the screen.

## §2 — G-DRIFT, EXTENDED `d8b64997 → 49011cc9` BY MEASUREMENT

Rule-29(b) scope diff: **26 files, +2,879 / −164**. Rather than classify 26
files by reading, the caiso-255 identity probe was re-run at HEAD with the
three artifact files **temporarily reverted to their `fa23c1f7` bytes** on the
shared data tree (restored on exit, `git status` clean):

> `scripts/probes/_caiso255_gdrift_identity.py --keeper-sha fa23c1f7`
> → **VERDICT: ALL LP INPUTS BIT-IDENTICAL**, all three years
> (`results/calibration/_caiso256_gdrift_input_identity_artifact_reverted.json`).

So on the input side the artifact pair is the **only** thing that moves.
Instruments 1–2 report what moved and instrument 3 settles it:

| what moved | classification |
|---|---|
| `ScenarioConfig` defaults: `campd_bins_path`, `control_retrofit_path`, `plant_emission_rates_path`, `plant_emission_rates_v2_path`, `plant_registry_path` (path-registry relocation), `ccs_retrofit_vom_adder` (8.0 → 2.95, capacity-evolution step 2) | **INERT — measured**: every fleet array bit-identical; the CCS field is a forecast-only path |
| constants: `CAMPD_BINNING_ISOS`, `DEMAND_GROWTH_RATES`, `DATACENTER_*`, `ELECTRIFICATION_LAYERS`, `RGGI_MEMBER_STATES_BY_YEAR`, `EIA930_PS_FOLDED_INTO_WAT` (= `{MISO, PJM}`, CAISO absent) | **INERT — measured** (unit_ids / mc_base / demand identical) or non-CAISO |
| `df277e89`: the two artifact JSONs | **LIVE — this IS the arm** (phase 0: F 14,208 / 7,514 / 8,644 MW·$/MWh, 945 / 951 / 957 gas tranches moved, 0 non-gas) |

Construction and solve, which instrument 3 cannot see, read hunk by hunk:

| file | verdict |
|---|---|
| `pipeline/backcast_config.py` (+51) | INERT — `nyiso_ct_peaker_bands_measured`, hard-errors on any non-NYISO ISO; default off, absent from the recipe |
| `model/commitment.py` (+49), `pipeline/commitment.py` (+73) | INERT — `nyiso_gas_bridge_startup_aware` census plumbing; `screen_stats=None` is documented byte-identical; default off, absent from the recipe |
| `scripts/run_calibration.py` (+53), `run_calibration_full.py` (+50) | INERT — the two NYISO kwargs above, plus `apply_miso_gas_marginal_commodity`, which returns `None` unless `miso_gas_marginal_commodity_pricing` (default False) and then falls through to the previous call |
| `data/fuel/resolve.py` (+25), `fuel/basis/miso.py` (+164) | INERT — the same MISO gate |
| `data/fleet/campd_bins.py` (+40), `fleet/__init__.py` (+25) | INERT — CO2 booked as `measured × (1 − ccs_capture_fraction)` with the fraction 0.0 on every unabated unit: an exact IEEE no-op, and `emission_rate` measured identical |
| `results/cache.py` (+116) | INERT for values — cache-key epoch entries; a replay never hits a cache |
| `runner.py`, `capacity_evolution/*`, `config/capacity_market.py`, `data/avoidable_cost_rate.py`, `data/datacenter.py`, `policy/voluntary_demand.py` (+~650) | INERT — UNREACHED: forecast orchestration / capacity evolution; the calibration lane never calls `evolve_fleet` (`results/cache.py:337-339`) |
| `config/constants.py` (+165), `config/scenarios.py` (+645) | settled by instruments 1–3 above |
| `pipeline/solve.py` | unchanged on this span; the P1 basis seed stays UNREACHED on the replay driver (`ADDENDUM-caiso255-solve-path-correction §A.2`) |

**⇒ G-CTRL FORM 4 STANDS. No control solve.** The keeper's committed bundle is
the control, and the arm differs from it by exactly the artifact pair.

**One more thing the audit found, and it moves the comparator, not the arm.**
The *scorer* drifted since `fa23c1f7`: `scripts/calibration_verdict.py`
+224, `scripts/lib/holdout_policy.py` +73, `scripts/dashboard_add_run.py`
+81, `scripts/legitimacy_diagnostics.py` +40. Form 4 differences the arm
against the keeper **as scored by the same code**, so the keeper was
**re-scored at HEAD from its committed artifacts** (no solve):

> `scripts/calibration_verdict.py --run-id 2026-09-05-caiso-252-b1-notrim`
> → **CALIBRATED**, rubric **v3.6**; C1 PASS, C4 PASS (gas r/NRMSE
> **0.880/0.285, 0.909/0.261, 0.877/0.297**), C3a PASS (**+4.6 / +9.0 /
> +8.9 %**), C3b PASS, C3c CAVEAT (the single ledgered caveat), C6 PASS, C8
> PASS — identical to the committed sidecar to the printed digit.

Those are the numbers every gate below differences against.

## §3 — PRECONDITIONS THE ARM MUST MEET OR BE DISCARDED (checked from its own `run_config.json`, not asserted)

1. `resolved_inputs.seam_import_cap` reads `source = "mic_partition"` with
   **16,055 / 16,452 / 16,148 MW**, exactly as the keeper's. The
   `capacity-deliverability` clean partition is gitignored and was absent on
   this box at session start — the fleet rebuild warned *"Part A did NOT apply
   … keeps the BAKED 7,500 MW cap"* — so it was materialised
   (`scripts/data/curate_capacity_deliverability.py`, 5 partitions) before any
   solve. An arm that solved on the 7,500 fallback is not form-4 comparable and
   is thrown away.
2. `resolved_inputs.hydro_plant_modes.partition_present = true` (flag off, as
   the keeper), `campd_unit_outages` and `thermal_tranches` sha256 identical to
   the keeper's.
3. `MARKET_SIM_WARMSTART_XYEAR = 0` and the P1 basis seed unreached, evidenced
   from the driver's log line, per `ADDENDUM-caiso255-solve-path-correction`.

## §4 — S-1 OPERATIONALIZED, BEFORE THE SOLVE

PRECOMMIT-caiso255 §7.2 registers S-1 as "CT_PEAKER energy RISES, within a
factor of 3 of the displacement F(y) implies" without saying how F implies a
displacement. Fixed here, and measured (`_caiso256_s1_implied_displacement.py`,
two `fleet_only` rebuilds on the keeper recipe with the frozen and the
repaired pair swapped on disk, unit_ids verified identical):

> **ΔE_implied = Σ_i pmax_i × #{ t : mc_new_i ≤ λ_{z(i),t} < mc_old_i }** over
> every CT_PEAKER tranche whose P0 offer fell, λ = the keeper's committed P1
> zonal price.
>
> 2023: **784 of 828** CT_PEAKER tranches fell, **0 rose**;
> **ΔE_implied = 935.5 GWh**; **S-1 band = [311.8, 2,806.4] GWh** of
> CT_PEAKER energy RISE against the keeper's 2023 CT_PEAKER **1.6447 TWh**.

**Disclosed before the result:** this is a first-order, price-held-fixed
count, so it is biased **high** (once one tranche clears, λ falls and the next
does not). The registered factor of 3 is the absorber. If the arm's rise lands
**below 311.8 GWh, S-1 FAILS and the arm dies** exactly as the PRECOMMIT
says; the estimator is this session's, its bias is stated here, and whether to
re-charter on a different estimator would be the owner's call after the fact —
not something this session may do once the number is known. The largest
contributors are the SDGE LA-basin peakers (p57482 / p57515 econ tranches,
mc_old ≈ 75.5–76.3 → mc_new ≈ 73.5–75.0 $/MWh, 329–592 band-hours each).

## §5 — HOW S-2 / S-3 / S-4 ARE SCORED (instruments named now)

* **S-2** — nuclear / hydro / wind / solar annual energy from
  `hourly/class_hourly_2023.parquet`, arm vs keeper, each **< 0.5 %** of the
  keeper's class energy. Storage, import and the CC classes reported.
* **S-3 (C1 stop gate)** — arm class TWh against the keeper `_verdict.json`
  C1 records' `actual` ± the same tolerance (±5.27 TWh & ±3 pp share, 2023);
  any class PASS → FAIL is a STOP-and-ESCALATE.
* **S-4 (C4 stop gate)** — the caiso-252 screen construction
  (`_caiso252_screen2025.py`: per-plant `dispatch/2023_P1.parquet` →
  `_cems_gas_hourly_fit` on the committed bench part) against the HEAD-scored
  keeper **0.880 / 0.285**; a flip is r < 0.70 or NRMSE > 0.30 —
  STOP-and-ESCALATE.
* **C3a EXCLUDED both ways; neither C3a nor C4 promotes; `co2` excluded.**

Scorer: `scripts/probes/_caiso256_screen2023.py`, artifact
`results/calibration/_caiso256_screen2023.json`. **Every number this session
will ever cite from the screen bundle lives in the FINDING; the bundle
(`results/calibration/caiso256_screen2023`) is deleted before the PR merges
(rule 29(c)).**

## §6 — LAUNCH RECORD

```
MARKET_SIM_P1_BASIS_SEED=0 PYTHONPATH=.:src uv run python scripts/replay_keeper.py \
    results/calibration/caiso252_b1_notrim \
    --out-dir results/calibration/caiso256_screen2023 --years 2023 \
    --note "caiso-256 rule-29 SCREEN of the CT-only partition (owner grant, FINDING-caiso254 §4 option 1): keeper replay with the df277e89 artifact pair on disk; throwaway, deleted before merge"
```

Launched only after this document is pushed. If the screen clears, the full
span is ONE invocation `--years 2023 2024 2025` into
`results/calibration/caiso256_ctonly`, registered the same session, promoted
iff PRECOMMIT-caiso255 §5(8) holds — (a) S-1/S-2 pass, (b) no load-bearing
criterion (C1 / C2 / C3a / C3b) regresses to a NEW failure in any year,
(c) C6 attested and C8 passes; C3a and C4 do no promotion work in either
direction. Otherwise the artifact pair is reverted to `fa23c1f7` on `main`,
which is the stop rule `df277e89` itself records.
