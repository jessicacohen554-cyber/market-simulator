# FINDING — Y-28: cache-key & solve-surface identity repair (2026-09-24)

Lane **Y-28**, Model Audit & Release-Finalization Program, director board v42 §3/§5
(director pin `40f4ed7a`; worked on `origin/main` @ `a4708b25`). DATA PROFILE: code.
No LP solved. No keeper shard, registry, bundle or matrix shard touched. No pin
literal re-baselined to silence a test; no test skipped, xfailed or deleted.

## 1. Culprit verdict — `coal_mustrun_requires_measured_row`: BYTE-IDENTICAL AT DEFAULT, REGISTERED

- Field landed by **pjm-h14, `f7d6112ca` (2026-09-20)**, `scenarios.py`, default `False`,
  with **no `_CACHE_KEY_OPTIONAL_FIELDS` entry** — so it entered every config's hash and
  moved the pinned default key **`547053bdfccd4264` → `b91f98d9017002db`** (backcast
  **`f61891696e671969` → `5c3581517d0a680d`**).
- **Sole consumer** (grep over `src/`): `data/fleet/campd_bins.py` ~L2654, which zeroes the
  COAL must-run share only inside
  `and getattr(config, "coal_mustrun_requires_measured_row", False)`. At `False` the branch
  never runs: no tranche, row or column changes. Byte-identical at default by construction.
- **Remedy (the one the pin test prescribes):** registered in `_CACHE_KEY_OPTIONAL_FIELDS`
  (very end, HOUSE-3 shared-field convention) and declared at `"False"` in
  `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` in the same commit.
  `scripts/check_cache_key_registration.py`: *"875 fields, 330 registered, all resolve; 330
  declared defaults all match HEAD; 310 solve-surface names … all declared"*.
- **Result:** default key back to `547053bdfccd4264`, backcast back to `f61891696e671969`.
- **What it costs:** an armed config (`True` — the PJM keeper's recipe) is non-default, so its
  key is **unchanged**. A default-`False` config's key reverts to its pre-2026-09-20 value, which
  is correct because the field is inert at `False`; any bundle cached under the unregistered key
  between 2026-09-20 and now is simply a cache miss, never a wrong serve.

## 2. Solve-surface pins — six ISOs advanced, **no value moved, no key moved**

`scripts/solve_surface_register.py --diff 15beb03c6` (the 2026-09-10 commit that last wrote the
pins; clone deepened with `git fetch --deepen`, no graft) → worktree:
**"304 → 310 names; 21 value(s) moved, 6 added, 0 removed"**. Every one of the 21 moved values
reaches **only NWPP and/or SOCO** (per-ISO totals ERCOT/CAISO/MISO/PJM/NYISO/NEISO = 0); neither
is pinned. The pinned-ISO digests moved purely because four **added, declared** names joined the
fingerprint:

| Name | ISOs (rows) | Added to constants.py | Declared | Consumer |
|---|---|---|---|---|
| `PPA_COST_RECOVERY_YR` | all six (+1) | `3fc20b976` 2026-09-20 (marginal-abatement pricing) | `da38d1086` (hydro-1) | `scripts/build_mac_sidecar.py` only — not a solve |
| `REGIONAL_RENEWABLE_CF` | all six (+1) | `3fc20b976` 2026-09-20 | `da38d1086` (hydro-1) | `scripts/build_mac_sidecar.py` only |
| `NYISO_CUTSET_TTC_ENVELOPE_BY_MONTH` | NYISO (+1) | `5af5d6fbc` 2026-09-10 (nyiso-224) | same commit | `pipeline/ttc.py` under `nyiso_total_east_cutset_ttc` (default False) |
| `HYDRO_PONDAGE_EXTRA_NID_BY_PLANT` | NYISO (+1) | `da38d1086` 2026-09-20 (hydro-1) | same commit | `scripts/data/build_hydro_pondage.py` → `hydro_pondage_bound` (default off) |

Not pinned-ISO rows: `GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR` (soco-55 `d891efa2a`),
`ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE` (soco60b `f560408f6`) — SOCO/NWPP only.

| ISO | old pin | new pin |
|---|---|---|
| ERCOT | `5ab10cf3fa2f1447` (229) | `2cdbcd6c3ab52c81` (231) |
| CAISO | `cba92d202f32f9fd` (204) | `0b6c20ac2fb77cee` (206) |
| MISO | `9f0845000dc8af6e` (210) | `c3ff7c56ddbb573d` (212) |
| PJM | `905116f13849914f` (214) | `5c08117448da7c28` (216) |
| NYISO | `1eefed492204fab7` (209) | `211ef7751502c924` (213) |
| NEISO | `9d35c270c69e9eee` (197) | `54e04ca0b469de51` (199) |

`moved_rows` is unchanged: `{}` for MISO/PJM/NYISO/NEISO; exactly the already-ledgered rows for
ERCOT and CAISO. **Cost: nothing through this surface** — additions declared at their live hash
re-key nothing, so no keeper's bundle differs from a fresh solve because of a registry row. No row
was re-declared in `config/solve_surface_declared.py`. Dated cause block written above
`PINNED_SURFACE_ROWS_BY_ISO` in `tests/regression/test_persisted_identity.py`.

Root cause of the drift (process, not code): three lanes (nyiso-224, the marginal-abatement lane,
hydro-1) declared new surface names correctly but none advanced the pin — the same defect the
2026-09-08 and 2026-09-10 cause blocks already named.

## 3. Fast tier — before / after

`uv run python -m pytest -n 2 -m "not slow and not integration and not fulldata"`, local:

- **Before** (`origin/main` @ `a4708b25`): **79 failed** (74 nodes + 5 subtests), 10,195 passed.
- **After** (this branch): **34 failed** (29 nodes + 5 subtests), 10,235 passed, 61 skipped, 3 xfailed.

**45 healed, 0 new.** Healed: 9 in `test_persisted_identity.py` (default + backcast + checkout-path-invariance key pins, six surface pins) and 36 downstream pinned-key tests across 25 files (`test_d67arm_pjm_requirement` ×8, `test_ercot_stageb_arming` ×2, `test_d60_arming_batch` ×2, `test_capacity` ×2, `test_ccs_retrofit` ×2, `test_iso_override_precedence`, `test_d53_sector_gate_miso_arming`, `test_caiso_ra_mpb_anchor`, `test_reserve_config`, `test_scarcity`, …) — **all healed by (a) alone**; none needed a separate registration. **Every key-pin / surface-pin failure is healed.** Nothing remaining is a cache-key or
surface-pin test. Classification of the remaining 29 nodes (routed, not worked — out of Y-28 scope):

| Remaining failure | Class / owner |
|---|---|
| `test_persisted_identity::test_no_module_level_import_cycles` | import cycle — Y-30 |
| `test_gate_a_provenance`, `test_golden_manifest_provenance` ×8, `test_ff_readiness_battery`, `test_forecast_parity` ×2, `test_audit_keepers_lineage` e11, `test_bench_stamp_payload` d | gate-(a)/golden-manifest/keeper-provenance — Y-29 |
| `test_soco_zonal_gas_hub`, `test_data_profiles_tokens` (soco), `test_constants_facade::test_moved_surface_is_complete` (soco-55's `GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR` not re-exported by the facade) | SOCO records / facade — Y-29/Y-30 |
| `test_flag_registry::TestCoalFamilyKwargMapping` (SPP-71 `coal_sync_ensemble_level` in solve kwargs, not in the test's expected set) | mechanical red — Y-30 |
| `test_clean_io`, `test_data_dictionary_sync`, `test_caiso_per_hub_intertie`, `test_run_year_kwargs_recipe`, `test_calibration_verdict` coverage-threshold, `test_caiso_st_gas_peak_measured`, `test_fleet` Mystic, `test_gas_offer_zonal_anchor_vintage` ×2, `test_emissions` vendored parity | data drift / mechanical — Y-30 |

None is a separate unregistered `ScenarioConfig` field: `check_cache_key_registration.py` is
clean and the default/backcast pins pass.
