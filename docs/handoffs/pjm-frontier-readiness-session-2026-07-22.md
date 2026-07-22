# PJM frontier readiness — M-3 gas bridge + DAM-availability edits (session 2026-07-22)

**Status: code COMPLETE and unit-VERIFIED against real main (7155067).**
Delivered as a ready-to-apply patch (`pjm-frontier-readiness-2026-07-22.patch`,
**attached to the delivering session** — see §6) because the edits touch files
≥300 lines that cannot be pushed through `mcp__github__push_files` (CLAUDE.md
rule 27 — no regenerated large-file rewrites) and `git push` 413s on this
remote. A local-git session (Opus/Fable) applies the patch and pushes the
source. **The probe (Item 2 second half) is a follow-on resourced session — see
§4.**

## 0. Environment note (READ FIRST)

This container, like `claude/pjm-frontier-readiness-ljrun0` before it, booted
with a **stale clone** pinned to `066fb98` (~1500 commits behind), and every
`git fetch` times out through the proxy. The working tree used for this session
was reconstructed by streaming the `codeload` tarball of `7155067` over HTTPS
(git protocol is proxy-blocked; plain HTTPS is not). All edits + tests below ran
against that true-`7155067` tree. **The recurring stale-clone boot is an
environment/clone-cache issue on the owner's side** — a local-git session avoids
it entirely.

## 1. Item 1 — DAM-availability overlay (the two verbatim edits)

Applied exactly as `docs/handoffs/pjm-dam-availability-wiring-2026-07.md`
prescribes:

* `src/market_sim/config/scenarios.py` — added `pjm_dam_availability: bool =
  False` immediately after `ercot_thermal_dam_availability`.
* `src/market_sim/data/fleet.py` — generalized the ERCOT thermal-DAM guard in
  `generators_to_fleet_arrays` to select `_meas` by ISO+flag (ERCOT →
  `ercot_thermal_dam_availability_series`, PJM → `pjm_dam_availability_series`);
  the bidirectional cap-1.0 water-fill body is unchanged, and the `logger.info`
  is now ISO-generic (`%s` + `_iso`).

**Verify:** `pytest tests/test_pjm_dam_availability.py tests/test_outages.py`
→ `test_pjm_dam_availability` ALL PASS; the ERCOT DAM fleet-application tests
still pass (guard generalization did not regress ERCOT). `test_outages.py`:
**48 passed, 2 failed, 1 skipped** — the two failures
(`ErcotThermalDamAvailabilityTest::test_committed_series_shape_and_values`,
`NEISOUnitOutageSmokeTest::test_coal_target_is_merrimack_only_all_years`) are the
**pre-existing stale ST_GAS-rearchitecture assertions the DAM handoff already
called out** (they expect `{CC_REGULAR, CT_PEAKER}` but the series now includes
`ST_GAS`). Unrelated to these edits.

## 2. Item 2 — M-3 PJM gas-CC commitment bridge (mechanism)

The PJM analogue of `ercot_gas_commitment_bridge`, mirrored exactly. Committed-
state evidence is `data/raw/_validation-source/pjm_gas_bridge_params.json`
(already on main): `pjm_gas_bridge_min_load_frac = 0.564` (cap-weighted p50 of
`avg_ecomin/avg_ecomax` over 302 physics-segmented CC units, 76.8 GW; overnight
ecomin-positive fraction 0.968).

Files changed:

* `config/scenarios.py` — `pjm_gas_commitment_bridge=False`,
  `pjm_gas_bridge_min_load_frac=0.564`, `pjm_gas_bridge_startup=True`,
  `pjm_gas_bridge_da_horizon=True` (after `ercot_gas_bridge_da_horizon`) +
  `TIER_TAGS` 1/2/1/1.
* `pipeline/commitment.py` — `_pjm_gas_bridge_floor`,
  `pjm_gas_bridge_p1_floor_fleet`, `build_pjm_gas_bridge_p1_prep`
  (`fuel_types=("gas_cc",)`, tag `MECH_PJM_GAS_COMMITMENT_BRIDGE`). A
  `_pjm_gas_bridge_guard` **raises `ValueError` when armed alongside
  `pjm_reserve_commitment_scoped`** (path B) — rule 19, one mechanism per
  phenomenon (both commit the PJM gas fleet from the P0 pattern).
* `pipeline/year.py` **and** `runner.py` — build the prep and add it to the
  `p1_fleet_prep` chain: `ra_p1_prep or ercot_bridge_prep or pjm_gas_bridge_prep
  or pjm_fleet_prep`. (Both orchestrator seams from PR #2753 are wired
  identically; each prep is ISO-exclusive, so ≤1 is ever non-None.)
* `pipeline/__init__.py` — export `build_pjm_gas_bridge_p1_prep` +
  `pjm_gas_bridge_p1_floor_fleet`.
* `data/floor_mechanisms.py` — `MECH_PJM_GAS_COMMITMENT_BRIDGE = 18` + `MECH_NAMES`
  + `MECH_ABLATION_FIELDS {"pjm_gas_commitment_bridge": False}`.
* `scripts/legitimacy_diagnostics.py` — import + D-4 window
  `(MECH_PJM_GAS_COMMITMENT_BRIDGE, "CC_REGULAR"): (0, 24)`.
* `scripts/derive_pjm_gas_bridge_params.py` (NEW) — reuses the FROZEN
  `derive_pjm_offer_surface` segmentation constants/helpers to regenerate the
  evidence JSON (rule 21: re-derives only on source-corpus update).
* `tests/test_pjm_gas_commitment_bridge.py` (NEW) — the 8-case ERCOT contract
  ported to PJM + a PJM-specific rule-19 mutual-exclusion test + the D-3
  registry/ablation test.

**Verify:** the M-3 + ERCOT-bridge + floor-ablation + legitimacy + commitment +
pipeline-commitment suites → **182 passed** (editable install, no manual
PYTHONPATH). `assert_ablation_coverage()` passes (mechanism 18 classified).

## 3. Pre-existing failures on real main (NOT caused by this work)

Beyond the 2 `test_outages` stale assertions (§1), a full run of the
scenario/pipeline suites surfaces **9 pre-existing facade/re-export identity
failures** in `tests/test_pipeline_api.py` + `tests/test_pipeline_facade_shims.py`
(e.g. `rc._apply_ttc_overrides is ttc.apply_ttc_overrides`). Diagnosis:
`scripts/run_calibration.py` on `7155067` DEFINES these as **local functions**
(lines 196/223/289), so the `is`-identity the tests assert is False — test/code
drift in files this session never touched. Confirmed independent of the M-3/DAM
changes (they fail on the pristine tree). Flagged here so they are not
mis-attributed to this patch; a separate cleanup should reconcile those shims.

## 4. Item 2 (second half) — the probe — DEFERRED to a resourced session

Not run here. Rationale (not a decision, a resource ceiling):

* **RAM:** this box has **15 GB**. A PJM per-plant, 8-zone, 8760h, 3-year solve
  (×2 for the A/B) is memory-heavy (CLAUDE.md caps per-plant multi-zone runs at
  ~2 concurrent) — real OOM risk on 15 GB.
* **Corpora:** `data/raw/pjm-da-virtuals` and `pjm-energy-offers` are gitignored
  and absent (stub only); they need regeneration via `scripts/fetch_pjm_*` from
  DataMiner2. The fetch uses PJM's **anonymous public** subscription key (no
  private credential needed) and HTTPS works through the proxy, but it is
  GB-scale / 36 months and slow.
* **Merge ordering:** the mechanism is not on main yet. Register the probe as a
  dashboard run of the *merged* code (rule 15), not this local branch.

**Runbook (post-merge, on a ≥32 GB box):**
```bash
# 1. regenerate the keeper's gitignored corpora
python scripts/data/fetch_pjm_energy_offers.py --years 2023 2024 2025
python scripts/data/fetch_pjm_da_virtual_surface.py --years 2023 2024 2025   # + any other fetch_pjm_* the keeper needs
# 2. A/B replay the pjm-115 keeper (2026-07-19-pjm-gasshape-interpfix), all years in one bundle (rule 16)
python scripts/run_calibration_full.py --iso PJM --year 2023 2024 2025 \
    <keeper recipe flags from results/calibration/pjm_gasshape_interpfix_main/meta.json> \
    --set pjm_gas_commitment_bridge=true --out-dir results/calibration/pjm_m3_gasbridge
# 3. score STRUCTURE not MAE (rule 1): overnight LMP overshoot / D-1p flat-overnight
#    residual, + C8 forced-share (<30%) + D-4 off-window (<5%) from legitimacy_diagnostics.json
# 4. register on the dashboard (calibration-report skill) — keeper OR rejected probe (rule 15)
```

## 5. Item 3 — holdout — NOT started

Requires explicit owner authorization (CI `quarantine-gates` hard-fails
out-of-training solves). Ask before touching 2022 / 2019 / H1-2026.

## 6. How to land this patch (local-git session)

The patch (`pjm-frontier-readiness-2026-07-22.patch`, 937 lines / sha256
`065b7057…1beb844`) is delivered as a **session attachment** (it could not be
pushed via the API without risking rule-27 truncation of a 937-line blob). Save
it into the repo first, then:

```bash
# save the attached patch to the repo root (or anywhere), then:
git fetch origin main && git checkout -B claude/pjm-frontier-readiness origin/main
git apply pjm-frontier-readiness-2026-07-22.patch   # verified: applies clean to 7155067
python -m pytest tests/test_pjm_gas_commitment_bridge.py tests/test_ercot_gas_commitment_bridge.py \
    tests/test_floor_mechanisms_ablation.py tests/test_legitimacy_diagnostics.py \
    tests/test_pjm_dam_availability.py -q     # expect all green
git add -A && git commit && git push -u origin claude/pjm-frontier-readiness
```
The patch was round-trip verified: `git apply --check` is clean against a fresh
`7155067` checkout, and the applied tree reproduces the verified worktree.
