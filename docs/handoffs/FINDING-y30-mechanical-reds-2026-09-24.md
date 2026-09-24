# FINDING — Y-30: mechanical CI reds (2026-09-24)

Lane **Y-30**, Model Audit & Release-Finalization Program. Charter: director board
v42 §4 rows 3–4 and §5 (`docs/handoffs/audit-program-director-board-2026-08.md`).
Director pin `40f4ed7a`; worked on a fresh branch off `main` @ `fd04cfda`.
Source failure list: CI run 36017508801, job 107693710480 (86 failed / 2 errors).

**Zero LP.** No solve, no keeper shard, registry sidecar, matrix verdict or scorer
threshold touched. No test skipped, xfailed or deleted; no `timeout-minutes` changed.
Cache-key / solve-surface pins (Y-28) and gate-(a) / golden-manifest / FR-22 /
SOCO-E13 / bench-stamp (Y-29) left alone.

## 1. Disposition table

Legend: **fixed** = code/infra repaired; **test-updated** = the test was stale
behind a legitimate change, updated with the commit that moved it; **routed** =
input drift from a frozen derive, expectation NOT touched (rule 23
`[R-FROZEN-DERIVE]`), handed to the desk named.

| # | Red | Disposition | What / why |
|---|-----|-------------|------------|
| 1 | Ruff F401+F841 `scripts/gen_nyiso229_attestation.py` | fixed | unused `numpy` import and dead `drift` list removed (`schema_drift`/`moved` carry the logic) |
| 2 | `ruff format` ×4 files (incl. `src/market_sim/data/fleet/eia860.py`, 4,269 lines) | fixed | formatted locally with the lockfile's ruff **0.15.17**; `git push` of on-disk bytes, blob verified after push (rule 27) |
| 3 | Refactor guard: `run_calibration_full.py` → missing `scripts/test_recorded_config_gas_anchor_mirror.py` | fixed | two defects, both as diagnosed in `soco-desk-ledger-2026-09.md` R-k: (i) the docstring cited `tests/unit/scripts/…`, the file is at `tests/unit/data/…` (nyiso-231); (ii) `_SCRIPT_REF_RE` had no left boundary, so a nested `…/scripts/x.py` read as a repo-root script. Docstring corrected; regex given a lookbehind. Measured over every tracked code file: **0** resolvable repo-root references lost |
| 4 | Import cycle `model.lp <-> model.lp.model` | fixed | `lp/model.py` did `from market_sim.model.lp import p0_cache`, which depends on the package `__init__` (which imports `lp.model`). Now `import market_sim.model.lp.p0_cache as p0_cache`, the submodule edge it actually needs. `test_persisted_identity.py` not edited |
| 5 | `test_flag_registry` (`coal_sync_ensemble_level`) | test-updated | new coal-family flag from SPP-71, `6edc996d` (2026-09-22) |
| 6 | `test_constants_facade` (`GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR`) | test-updated | `constants.py` already re-exported it; only the frozen inventory lagged. Landed by soco-55, `d891efa2` |
| 7 | `test_clean_io` (`coal-receipts`, `coal-stocks`) | test-updated | snapshot refreshed; intakes miso-258 `3857d801` / miso-259 `43ab70d5` |
| 8 | `test_data_dictionary_sync` (same two schemas) | fixed | `render_data_dictionary.py` gained both in `DATATYPE_ORDER`, `NARRATIVE` and `NATIONAL_SCOPE`; dictionary re-rendered (+55 lines, the two sections only; `--check` was clean on base) |
| 9 | `test_data_profiles_tokens` (SOCO) | test-updated | every `data/raw` name containing `soco` is SOCO's own (47 names enumerated, e.g. `campd-unit-outages-perunit-SOCO.meta.json`, `thermal_tranches_SOCO.csv`); the stem allowlist (`startswith("soco")` or `_soco_`) was narrower than SOCO's suffix naming. Now a delimited-token regex, which still fails `socorro`/`prosoco` — the collision G3 guards |
| 10 | `test_run_year_kwargs_recipe` (`caiso291_bridge_candidacy_census.py`) | fixed | `rebuild_state` now uses `bundle_fleet.full_run_year_kwargs` + `replay_keeper.derived_run_year_inputs` + `bundle_gas_price`, the sanctioned path, not a by-name filter. Not executed here (needs CAISO data); parses and lints clean |
| 11 | `test_script_import_env_hygiene` (`MARKET_SIM_P1_BASIS_SEED`) | test-updated | PERF-C S1, `d45d57f9` (2026-09-20), pinned the seed explicitly in both scripts' `DETERMINISM_ENV` |
| 12 | `test_audit_keepers_lineage` E11 (`composed_from`, `model_changes_note`) | fixed | `audit_keepers.E11_META_PROVENANCE` resynced to `replay_keeper._IGNORE`. `audit_keepers.py` output byte-identical before/after (its rc=1 comes from Y-29's items) |
| 13 | `test_cache_config_agreement` ×2 errors (`shard-artifacts/nyiso223/2022/run_config.json`) | fixed | **CI checkout gap, not missing data**: the file is tracked, but the fast tier's sparse cone did not include `/shard-artifacts/`, and `git ls-files` lists the index, not the worktree. The test class says "SKIP-when-sparse, prune-monotone"; it now skips absent members (a prune, by construction). `/shard-artifacts/` (36 files, 7.1 MiB) added to the cone so the replay stays live in CI |
| 14 | `test_spp67_year_own_curtailment_rate` ×7 | fixed (reclassified) | **Also a checkout gap, not drift.** The loader reads `data/raw/spp-hsl/spp_wind_curtailment_annual.csv` (17.6 KB) and returns `None` when absent; the path was outside the cone. Passes locally at the committed values. Added to the cone |
| 15 | `test_calibration_verdict` coverage 0.9677 | test-updated | the month is **MISO 2021 DA October**, 30/31 days, because MISO's own archive has no Oct 28 file (staged by `5e6d3224`, 2026-09-13). The 0.90 threshold's own comment already allows a month to lose "~3 days" to publication gaps; every threshold in (0.3654, 0.9677) gives the same partition, so 0.90 is still outcome-neutral. The empty-interval upper edge moved 0.9910 → 0.9677 with the cite. **Threshold unchanged** |
| 16 | `test_soco_zonal_gas_hub::test_no_applier_is_armed_for_soco` | test-updated | the only matching field is `soco_gas_st_campaign_commitment` (soco-53d, `1b289fcf`), a gas-steam commitment floor read only by `pipeline/commitment.py`. It never reads `SOCO_ZONAL_GAS_HUB_PATH`, so G8 still holds; excluded by name, with the reason |
| 17 | `test_caiso_per_hub_intertie` (`KeyError WECC_DSW_DSW_lateevening_clean`) | test-updated | caiso-269 (2026-09-10) added `DSW_lateevening_clean` to the hub map as an **armed-only** depth tranche, like the surplus/overnight/daytime siblings the test already exempts |
| 18 | `test_fleet::test_neiso_includes_mystic_cc` (`'oil'` vs `'gas_cc'`) | test-updated | `7934e92c` (2026-09-09) widened the retiree window 2023 → 2019, which correctly adds Mystic unit 7 (512.4 MW) and GT1 (9.1 MW), both oil, both retired 2021-06, to plant 1588. The CC assertions now apply only to the ≥2023 rows; the pre-2023 rows are pinned to ≥2019 |
| 19 | `test_gas_offer_zonal_anchor_vintage` ×2 (NYISO) | **routed → NYISO desk** | see §2.1 |
| 20 | `test_caiso_st_gas_peak_measured` (1.154 vs 1.166) | **routed → CAISO desk** | see §2.2 |
| 21 | `test_emissions::TestVendoredParityScope2` | **routed → owner** | see §2.3 |

## 2. Routed — input drift, expectation untouched

### 2.1 NYISO: `GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["NYISO"]` is stale against its repaired source

- **Measured at HEAD.** The runtime window mean (2023–2025) is below the registered
  table by the same amount in every zone: Upstate_West 2.0039 vs 2.0346,
  Capital_Hudson / Lower_Hudson / Long_Island 3.8739 vs 3.9046, NYC 2.7306 vs 2.7612
  (Δ ≈ −0.0307, i.e. −0.092 summed across the three years). Per-year Capital_Hudson:
  3.3370 / 2.8220 / 5.4627.
- **Cause, verified by substitution rather than inferred.** With the three files moved
  by the 2026-09-14 Transco Z6 repair swapped back to their pre-repair contents
  (`4cabc24f^` = `64622852`: `gas-prices/transco_z6_ny_daily.csv`,
  `gas-prices/transco_z6_iroquois_monthly.csv`, `gas_basis_by_iso_month.csv`), **both
  tests pass**. Files restored afterwards; `git status` clean. The repair itself is
  legitimate: `4cabc24f` (daily series, Elliott recovered) and `c0a9d5ba` (monthly
  anchor + basis recomputed), both cited to a source-coverage defect.
- **So the source moved and the frozen derive did not.** Rule 23 permits
  re-deriving `derive_gas_offer_margin_anchor.py` for NYISO **because its source data
  changed**, with this data change cited, but the table is solve-affecting (it feeds
  the NYISO offer margin), so the re-derive, and what it does to the NYISO keeper, is
  the NYISO desk's call. Y-30 did not re-baseline it.

### 2.2 CAISO: `ST_GAS_PEAK_MEASURED_HR_MULT_BY_ISO["CAISO"]` vs its artifact

- **Measured.** `caiso_offer_curve_measured.json` `CT_PEAKER.bands.peak` = **1.154**.
  The registry value and the test's `ST_GAS_BANDS["peak"]` are **1.166**.
- **Cause.** The artifact was re-derived by caiso-255 (`derived_utc`
  2026-09-06T06:21Z): the partition repair split ST_GAS out of the CT bucket. The
  registry value was pinned from the pre-partition (contaminated) CT bucket. The
  artifact now describes a different population, so the identity the test pins ("the
  registry value IS the committed artifact's peak") broke because the source was
  re-derived. The registry was not re-derived with it.
- **Decision for the CAISO desk.** Does `caiso_st_gas_peak_measured` still deliver
  "the SAME number the CAISO ST_GAS class band already carries", given the class band
  is 1.166 and the de-contaminated measurement is 1.154? Re-derive and ledger it, or
  record why the pre-partition value is the correct population for ST_GAS. Y-30 did
  not change it.

### 2.3 Owner: the scope2 vendored-parity test outlived its subject

`TestVendoredParityScope2` loads
`scope2-lce-portfolio/src/lce_portfolio/vendored/fossil_avg_rate.py`. The whole
`scope2-lce-portfolio/` directory was deleted by the owner on 2026-09-18 (`8f0d41df`,
"Delete scope2-lce-portfolio directory"). No mechanical fix exists: the only green
routes are restoring a directory the owner removed, or deleting/skipping the test,
and this lane is forbidden to do either. **The owner must decide.** Two stale
references to the removed tool remain for whoever acts:
`docs/scope2-lce-portfolio.md` (the pointer doc) and the `/scope2-lce-portfolio/`
line in `ci.yml`'s fast-tier sparse cone (harmless: it matches nothing).

## 3. Observations routed, not acted on

- **NEISO, Mystic 7 / GT1 carry `plant_group == ""`.** The two oil units the
  window widening added to plant 1588 come back from `load_retired_within_window`
  with an empty `plant_group`, while the CC rows carry `CC_REGULAR`. The test update
  does not depend on this. The NEISO desk should decide whether a blank class on a
  2019–2022 retiree is intended (only unclassified at this read seam) or an
  unassigned-class gap in the widened rows.
- **Shallow clones cite the boundary commit.** This container's clone is shallow
  (266 commits), so `git log -S` pinned four additions to `b0d7f1d8`, which is just
  the shallow boundary. The test comments were corrected to the real commits (found
  through the GitHub API) before push. One earlier commit message on this branch
  (`c4c4c273`) still says "PR #6468 additions". Any lane doing provenance from a
  session clone should check `git rev-parse --is-shallow-repository` first.

## 4. Fast tier, before and after

Both measured under the exact CI fast-tier sparse cone (patterns extracted from each
ref's own `ci.yml`), `pytest -n 2 -m "not slow and not integration and not fulldata"`,
in separate worktrees:

| | ref | failed | errors | passed |
|---|---|---|---|---|
| before | `origin/main` `fd04cfda` | 87 | 2 | 10,181 |
| after | this branch | 66 | 0 | 10,202 |

Every remaining failure on the branch belongs to one of: Y-28 (cache-key /
solve-surface pins), Y-29 (bench-stamp, FR-22 / forecast parity, gate-(a) markers,
`price_unscored` registered runs), or §2 above.

**21 failures and both errors cleared, zero new failures** (set difference of the
two `FAILED`/`ERROR` lists: empty on the after-only side). 70 skipped on both sides, so
the sparse-safe skip in row 13 added no skips under the new cone. Wall time was about
10 min each. (`main` reads 87 where the CI run read 86 because it had moved on to
`fd04cfda`.)

The 66 that remain:

| owner | count | tests |
|---|---|---|
| Y-28 | 49 | `test_persisted_identity` cache-key + solve-surface pins (9), `test_cache_solve_surface` sidecar (1), and the 39 per-mechanism `…default_cache_key…unmoved` / arming-key pins |
| Y-29 | 13 | `test_gate_a_provenance` (1), `test_golden_manifest_provenance` (8), `test_bench_stamp_payload` (1), `test_ff_readiness_battery` (1), `test_forecast_parity` (2) |
| routed, §2 | 4 | NYISO anchor ×2, CAISO ST_GAS peak, scope2 vendored parity |

The `test_calibration_verdict_price_unscored` subtest failures CI reported (SOCO/NWPP
registered runs) are Y-29's registry items too.
