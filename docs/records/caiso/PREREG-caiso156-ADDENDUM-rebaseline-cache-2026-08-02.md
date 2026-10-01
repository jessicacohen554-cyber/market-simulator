# PREREG ADDENDUM — caiso-156: keeper re-baseline + the arm-B cache-key collision

**Written and committed BEFORE any arm solves and BEFORE the derive is edited**
(house rule; caiso-139..157 precedent). The parent prereg
`PREREG-caiso156-ct-heat-rate-meter-screen-2026-08-02.md` was written on
2026-08-02 *before* caiso-157 merged and before three keeper promotions landed.
This addendum corrects the stale baseline and records a construction hazard
found during pre-solve verification.

* **Session:** caiso-158 (executing the caiso-156 charter).
  **Branch:** `claude/caiso-backcast-calibration-6ubjfb`.
* **Nothing in the parent prereg's adjudication is changed.** No gate is added,
  dropped or re-thresholded; no expected direction is revised; the exclusion
  rule of §1 is untouched; the solve scope of §3 is unchanged (CAISO, NYISO,
  PJM, NEISO solve; MISO and ERCOT re-derive only). §B below is a *construction
  protocol* required to satisfy the parent's own K1 and K3 as already written —
  without it those two gates cannot mean what they say.

---

## A. Keeper re-baseline — §3's table re-verified from bundle meta this session

Three keepers moved after the parent prereg was written. Arming was re-read
from each CURRENT keeper's committed `meta.json` (never assumed, never carried
over from the parent):

| ISO | keeper (CURRENT) | bundle | arms `measured_ct_heat_rates`? | vs parent §3 |
|---|---|---|---|---|
| CAISO | `2026-08-02-caiso157-partition-restore-b` | `caiso157_restore_B` | **YES** | **MOVED** (was caiso153-reid-b) |
| NYISO | `2026-08-02-nyiso112-ramp-plus-peaker` | `nyiso112_combined_D` | **YES** | **MOVED** (was nyiso109-zonal-margin-anchor) |
| PJM | `2026-07-31-pjm-143b-hy-level` | `pjm143_hy_level_B` | **YES** | unchanged |
| NEISO | `2026-07-31-neiso-72-hy-window` | `neiso72_hy_window_B` | **YES** | unchanged |
| MISO | `2026-07-31-miso-109b-hy-level` | `miso109_hy_level_B` | **NO** (flag absent from meta) | unchanged |
| ERCOT | `2026-08-02-ercot150b-zonal-anchor` | `ercot150_zonalanchor_B` | **NO** (flag absent from meta) | **MOVED** (was ercot149-gas-event-cap) |

**The parent's central claim survives the re-baseline unchanged: FOUR committed
keepers consume this artifact, and they are the same four ISOs** (CAISO, NYISO,
PJM, NEISO). Only two of the four keeper *ids* changed; MISO still does not arm
it and ERCOT still does not (it remains inert-by-wiring, ERCOT-146 cell `I`).
The parent's arm table (§4) therefore stands as written, with arm A/B for each
ISO replaying the CURRENT keeper id above rather than the parent's stale id.

Rule 16 is unaffected: every listed bundle carries exactly [2023, 2024, 2025].

## B. The arm-B cache-key collision — a silent void, and the protocol that closes it

**Measured this session, before any solve.** The parent §4 specifies that both
arms carry a config that is *value-identical* ("the merged config is
unchanged"; K4 gates exactly that). That is correct and desirable for
attribution — but combined with the check-before-run cache (rule 7
`[R-PARQUET]`) it voids arm B:

1. `ScenarioConfig.cache_key()` hashes `asdict(self)` — **ScenarioConfig fields
   only**. The CT heat-rate artifact is a CSV read at fleet-build time; its
   bytes are not a config field and never enter the hash. Verified: no `note`,
   `out_dir`, `git_sha`, `basis_sha`, `timestamp` or `label` field exists on
   `ScenarioConfig`, so no provenance value differentiates the arms either.
2. Two configs armed exactly as the arms will be armed hash **identically**:

   ```
   ScenarioConfig(iso='CAISO', mode='backcast', measured_ct_heat_rates=True).cache_key()
     arm A -> b8ba9f5ddbabf057
     arm B -> b8ba9f5ddbabf057      IDENTICAL
   ```

   (Sanity check that the key is live at all: the unarmed config hashes
   `74e4d97968003b7e`, so the flag itself does move the key — it is only the
   *artifact bytes behind the flag* that are invisible to it.)
3. `runner.py:1369` short-circuits on exactly that key —
   `if is_cached(iso, cache_key, year): result = load_result(...)` — and
   `runner.py:2149` `save_result(...)` populates it. `CACHE_ROOT` is the
   **global** `paths.RESULTS_ROOT` (`/results`), not the arm's `--out-dir`;
   neither `run_calibration_full.py` nor `replay_keeper.py` redirects it.
   `.gitignore:229-233` documents the tree as "transient per-ISO LP outputs
   keyed by cache_key (`results/<ISO>/<cache_key>/`)".

**Consequence had this gone unnoticed:** arm A solves and writes
`results/<ISO>/b8ba9f5.../year_{2023,2024,2025}.parquet`; arm B hits
`is_cached`, loads arm A's dispatch, and **never re-solves against the corrected
artifact**. Every A/B would report `max |Δ CT_PEAKER class-hour MW| = 0.000` in
all four ISOs — and the parent's K3 reads that number as *liveness*. A void
experiment would have been indistinguishable from a genuine "the correction is
score-inert everywhere" finding, and would have been reported as one. This is
the caiso-157 failure class exactly: a silent no-op that still produces a
legitimate-looking bundle.

**Protocol, frozen here (construction hygiene, not a gate):**

* The per-ISO LP cache dir `results/<ISO>/` is **removed immediately before
  every arm solve**, arm A and arm B alike, so each of the eight arms is a
  provably cold solve. (`results/calibration/` — the bundle tree — is a
  sibling and is never touched by this.)
* The cache tree is verified ABSENT for the target ISO immediately before each
  arm starts, and the arm's own solve log is checked for the cached-year path
  (`log_year_cached_timing`) being taken. An arm that logs a cache hit is
  discarded and re-solved cold; it is never registered.
* This is recorded per arm in the FINDING alongside the K1 md5s.

**Scope of the claim.** This addendum fixes the *experiment*. Whether the
engine should hash input-artifact provenance into `cache_key` (so that any
corrected measured input invalidates its own cache automatically) is a real
defect of the same class, but it is core-infrastructure surgery affecting every
ISO and every cached run, and it is **out of this charter** — filed as a
follow-up lane item in the FINDING, not fixed here.

## C. K1 baseline — pre-fix artifact bytes recorded before the derive is touched

md5 of the committed (pre-fix) artifacts at this commit, for the parent's K1
gate. Arm A must solve against exactly these; arm B against their post-fix
successors:

```
18060431490625666b52487050516659  campd_ct_heat_rates_CAISO.csv
762f68d0c1954e923a40d466d6ab6946  campd_ct_heat_rates_CAISO_units.csv
6dd5eca1ebae03397303ebd1e5811b0f  campd_ct_heat_rates_ERCOT.csv
686da86085c3c118d9b4aaa7e98d9eea  campd_ct_heat_rates_ERCOT_units.csv
5826cfa2adc02a1105023c774565da7a  campd_ct_heat_rates_MISO.csv
b54cce274b9033e95a7bd46d9263fd3d  campd_ct_heat_rates_MISO_units.csv
9f14549543c3042a2f12d4dad09f800f  campd_ct_heat_rates_NEISO.csv
bded2473e9962f62f929aa3848dc3dd8  campd_ct_heat_rates_NEISO_units.csv
749f4ffff41f05fa9b67b6f011b770ec  campd_ct_heat_rates_NYISO.csv
829de9cde164773fe2089ffd5982361b  campd_ct_heat_rates_NYISO_units.csv
8d48c2bb98d2ce044bed2a438d4b87ec  campd_ct_heat_rates_PJM.csv
db012a4cf01a82ac9d4e23f26c9b7a5b  campd_ct_heat_rates_PJM_units.csv
```

All twelve are `data/raw/_processed-legacy/`. The container's per-ISO cache
tree was verified absent at this commit (`results/{CAISO,PJM,NYISO,NEISO}` do
not exist), so arm A is cold by construction.

## D. Unchanged from the parent prereg

The exclusion rule (§1), the pre-derive measurement and its table (§2), the
solve scope and per-ISO guards (§3), the arm construction and `--set` channel
(§4), every predicted direction (§5), every gate K1–K6 and the determination
gates (§6), the promotion rule and LOYO treatment (§7), and the deliverables
(§8) are carried over verbatim. Rule 22 is unchanged and re-affirmed: solve
years are 2023 2024 2025 only, `--holdout-authorized` is not passed, CAISO and
NYISO hold no marker, and the holdout spend freeze is ACTIVE.
