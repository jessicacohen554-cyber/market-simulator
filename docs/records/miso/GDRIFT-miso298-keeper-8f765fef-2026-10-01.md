# G-DRIFT audit — miso-298: keeper legs 8f765fef vs the miso-298 pin (rule 29(b))

Addendum to `docs/records/miso/GDRIFT-miso297-keeper-8f765fef-2026-10-01.md`, which classified every hunk from the
keeper solve SHA `8f765fef0ed79c89687b6bf686cb65f611a9fea4` to `06394e307d6ff61be5339dfb8f35e73b3b471b85` (190 files,
0 LIVE). This record classifies only what landed on `main` after `06394e30`, up to the miso-298 branch point
`7a65272a29b748377526d0ae1fbdbb693d766b90` (44 commits). The lane's own commits add only `docs/records/miso/*`,
`scripts/probes/_miso298_*.py` and `results/phase0/miso/_miso298_*.json`.

**Registry re-key check (whole range, run in the venv by the parent):** `uv run python scripts/solve_surface_register.py
--diff 8f765fef0ed79c89687b6bf686cb65f611a9fea4 HEAD` → 317 → 336 names; 19 added (declared, move no key); 2 moved:
`ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR` (ERCOT), `ISO_BA_JOINS` (PJM). **Per-ISO totals: ERCOT 1, PJM 1, MISO 0.**

**Scope of the addendum:** `git diff --stat 06394e30 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/replay_keeper.py scripts/lib scripts/calibration_verdict.py
scripts/legitimacy_diagnostics.py data/raw/reference data/raw/_validation-source pyproject.toml uv.lock` → **7 files,
+380 / −80**. `scripts/run_calibration.py`, `scripts/replay_keeper.py`, `data/raw/reference`,
`data/raw/_validation-source`, `pyproject.toml` and `uv.lock` are unchanged in the range.

| file | hunk | class | reason |
|---|---|---|---|
| `scripts/lib/unit_marginal.py` (new, +138) | the slim per-unit sidecar writer (`write_unit_marginal`: `unit_hourly` minus `red_cost` plus an int8 `marginal` flag) | **INERT for dispatch** | a pure function of a file the solve has already written; reads nothing the LP reads, writes nothing the LP, the scorer or `legitimacy_diagnostics` reads. It is the rule-15 sidecar every miso-298 leg must carry (shard check HARD 6) |
| `scripts/run_calibration_full.py` (+10/−1) | `solve_and_persist`: capture the `unit_hourly` path and call `write_unit_marginal` after it is written | INERT for dispatch | runs after P1 has solved and the dispatch parquet is persisted; the only new effect is one more file in `hourly/` |
| `src/market_sim/config/scenarios.py` (+31) | `ercot_ordc_published_curve: bool = False` (+ `_CACHE_KEY_OPTIONAL_FIELDS`, `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` "False", `TIER_TAGS`) | INERT | new field, default `False`, absent from the keeper recipe, dropped from the cache key at default; 0 changed defaults |
| `src/market_sim/model/lp/costs.py` (+13/−4) | `ordc_penalties` may be `(n_steps, T)`; the `(n_steps,)` case becomes `pen[np.newaxis, :]` broadcast into the block | INERT | the `(n_steps,)` branch assigns the same values to the same cells (`block[:, off:off+n] = pen` ≡ `= pen[None, :]`); MISO carries no `(n_steps, T)` family |
| `src/market_sim/model/reserves/spec.py` (+54/−24) | `build_reserve_dispatch_kwargs`: promote the penalty stack to 2-D only `if any(np.ndim(p) == 2 ...)`; `_ercot_ordc_curve` helper used by `_ercot_design` and `_ercot_multiproduct_design` | INERT | the promotion is skipped when every family is 1-D (MISO); the helper is called only from the two ERCOT designs; `_ercot_ordc_curve(published=False)` reproduces the old `mean(mu)/mean(sigma)` static curve line for line |
| `src/market_sim/results/scarcity.py` (+124/−7) | `_lolp_half(obd_half_shift=False)` = the legacy `mu/2, sigma/√2, shift_sigma` call; `ercot_ordc_published_curve_active` (gated `ercot_ordc_published_curve and iso == "ERCOT"`); `ercot_published_mu_sigma_hourly`; `resolve_lolp_params(year=None)` new first branch under that gate; `ercot_ordc_demand_steps` hourly path under `np.ndim(mu) > 0` | INERT | every new branch is under the ERCOT-gated predicate or the array-valued `mu`/`sigma` that only that predicate produces; MISO's `resolve_lolp_params` falls through to the unchanged `ordc_lolp_params_path` / flat branches |
| `src/market_sim/data/fleet/campd_bins.py` (+13/−42) | `campd_fuel_split_selector`: under `campd_per_unit_attribution` + `campd_unit_fuel_split` now RAISES (NWPP-NEXT-16 deleted `PER_UNIT_FUEL_SPLIT_TAG`); the tag's two resolver branches removed | INERT | MISO recipe `campd_per_unit_attribution=False`, so the `per_unit and fuel_split` branch is never entered and `fuel_split` never equals the deleted tag; the `not per_unit` path (`split_remap` → `plain-splitremap` tag) is byte-identical |

**Verdict: 0 LIVE hunks in `06394e30..7a65272a`; together with the miso-297 record, 0 LIVE in `8f765fef..pin`.** Rule 29(b)
form 4 holds: the committed keeper `results/calibration/miso280_span` is the control; no control solve is earned.

Record-only differences a HEAD replay shows (not solve-affecting): `solve_surface.fingerprint`/`rows` (19 shared names
added to the projected set; the MISO key's `moved` set is unchanged), `scenario_config` gains the new `False` field, and
every leg gains `hourly/unit_marginal_<year>.parquet` (rule 15).
