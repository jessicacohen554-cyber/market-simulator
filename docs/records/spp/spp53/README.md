# SPP-53 instrument records (2026-09-07)

The scripts here are the records of what `FINDING-spp-53-2026-09-07.md` computed, kept beside their
outputs so every number in the FINDING is reproducible (the `spp14/` convention). They were run from
the session scratchpad and take it as `argv[1]` (`S`); the 2026 daily pulls live under `S/daily/`
(re-fetch with `pull_daily.py`, ~550 MB, not committed) and the 2023–25 roll-ups are the landed
`data/raw/spp-binding-constraints/RTBM-BC-*.csv.zip`.

| File | What |
|---|---|
| `pull_daily.py` | lists `/2026/<mm>/By_Day` and downloads every `RTBM-DAILY-BC-≥20260128.csv` via `scripts/data/fetch_spp_alt_portal.py`'s `listing`/`download` |
| `parse_2325.py` → `hourly_asp_2325.parquet`, `constraints_2325.parquet` (scratch) | the 2023–25 `BINDING` rows → hourly mean \|shadow price\| per constraint on the LMP builder's local non-leap clock; group rules copied VERBATIM from `../spp14/groups.py` |
| `psi_regression.py` → `psi_all.csv` | PRECOMMIT §2.1 leg 2: OLS + HC1 of the hourly RT hub spread on every constraint's hourly \|SP\| (133 regressors ≥ 263 h), leave-one-year-out |
| `registry_xcheck.py` → `registry_xcheck.csv` | the corridor constituents against `Flowgates.csv` / `Temp_Flowgate.csv` ratings (element-string join) |
| `extract_2026.py` → `daily_census_2026.csv`, `limits_2026_by_constraint.csv`, **the landed sidecar** | per-file field-count census (the schema break), the `n_s_corridor` rows → `rtbm_bc_corridor_limits_2026.parquet`, per-constituent limit-at-bind stats |
| `aggregate_ttc.py` → `tstar_table.csv` | PRECOMMIT §2.1 aggregation: `T*_f = L_f / ψ_f`, the binding-hours-weighted median, the R1–R4 checks, the S→N set |
