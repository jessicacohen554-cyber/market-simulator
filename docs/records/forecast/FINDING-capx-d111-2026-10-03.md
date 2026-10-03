# FINDING — capx D111: FF rubric v1.2 — report-only supersession-delta annotation (owner ruling D108)

**Lane** capx D111 (code shard) · **date** 2026-10-03 · **zero LP** · DATA PROFILE: `code` · **authority** owner ruling
D108 "Report-only delta row" (capx desk session `session_01DumBRwSKvzgGTMGTuyUMPS`, 2026-10-03; the desk's
`FINDING-capx-d108-2026-10-03.md` carries the card and lands in the desk's own ledger PR) · **branch**
`claude/capx-d111-ff-rubric-delta` from `origin/main` `410f2900e5e2f1a28359d1b97200afeef75d52fd` · **charter pin**
`51422d1b5f02bff56e85b26ebbb36090eed14599` (PR #7151 merge; first parent of `6277de60a`, 10 commits behind the branch
base — the ten are the MISO/PJM close-out keeper merges, none touching the scorer, the rubric, the tests, the board or
the four bundles: `git diff --stat <pin> <base>` over those paths is empty).

**Headline.** `scripts/forecast_verdict.py` gains `--prior-summary` and a `supersession_delta` block (`RUBRIC_VERSION`
1.1 → 1.2); `docs/forecast-determination-rubric.md` is amended at header, §3, §7, §8, §9. The block is report-only at
every tier (`status: "rpt"`, `gating: false`), attached after `_determine()` has returned, so it cannot reach a status,
a determination, a reason or a caveat; absent prior ⇒ absent key (not SKIPPED, not a caveat). Verified zero-LP on the
two real supersessions: every FC status and the determination are byte-identical to the committed sidecars (PROMOTE
both), and the deltas land on the ruling's expected numbers. `frontend/data/forecast/ff-verdicts.json` is untouched.

## 1. Interface chosen (the narrowest that fits the scorer)

The scorer reads committed artifacts named on its CLI and never a board file, so the prior enters as **one more
committed artifact**: `--prior-summary <prior bundle>/full_horizon_summary.json`, loaded by `load_artifacts` into
`art["prior_summary"]`. The `<key>-pre-<lane>` board entry is the *reason* a caller passes it (the registrar that writes
the board, `scripts/register_forecast_run.py`, is D107's file and is not touched here). No `--prior-verdict` (a verdict
carries no trajectory) and no `--prior-bundle` directory convention (the scorer takes files, not directories).

Block shape (`supersession_delta`, in the full verdict and carried whole into the `--json-out` sidecar):
`status`, `gating`, `rubric`, `note`, `prior`/`current` (`iso`, `run_dir`, `cache_key`, `solved_years` — read from
the two summaries, never a path), `metrics`, `years[]` (one `{prior, current, delta}` cell per metric per paired
year), `unpaired_years` (`prior_only` / `current_only`, excluded from the totals), `window` (`years`,
`co2_mt_cumulative`, `lw_price_mean`). Metrics: `co2_mt`, `lw_price`, `max_hourly_price`, `hours_ge_100`,
`reserve_margin`, `gas_cc_ccs_gen_share` (= `generation_by_fuel_mwh.gas_cc_ccs / total_gen_mwh`; a fuel key absent
from a year is a 0.0 share — the summary writes only fuels present; a missing/zero `total_gen_mwh` is `None`).
Deltas are `current − prior` rounded to 6 places. `render_text` prints the table under the determination basis.

## 2. Real-bundle verification (zero LP; `--tier t1f`, each bundle's own `run_config` / `dof_ledger` / `invariants`)

**NEISO `results/ff-t1f-d105/neiso` (`66fb439918cbefd6`) vs prior `results/ff-t1f-d50/neiso` (`18515067bf4d2fbe`)**
— determination **PROMOTE** (committed sidecar PROMOTE; categories/reasons/caveats/notes byte-identical).

| year | co2_mt | lw_price $/MWh | max_hourly_price | hours_ge_100 | reserve_margin | gas_cc_ccs share |
|---|---|---|---|---|---|---|
| 2026 | 16.31 → 16.01 (−0.30) | 52.13 → 51.74 (−0.39) | 69.7 → 65.9 (−3.8) | 0 → 0 | 0.160 → 0.168 (+0.008) | 0 → 0 |
| 2027 | 17.60 → 17.21 (−0.39) | 53.27 → 51.19 (−2.09) | 280.4 → 236.6 (−43.8) | 5 → 3 (−2) | 0.049 → 0.051 (+0.002) | 0 → 0 |
| 2028 | 16.81 → 9.90 (−6.91) | 58.05 → 52.20 (−5.85) | 283.6 → 239.5 (−44.1) | 13 → 4 (−9) | 0.030 → 0.038 (+0.008) | 0.020 → 0.193 (+0.173) |
| 2029 | 15.35 → 4.73 (−10.62) | 62.47 → 51.45 (−11.02) | 284.9 → 240.9 (−44.0) | 9 → 3 (−6) | 0.029 → 0.043 (+0.014) | 0.092 → 0.313 (+0.221) |
| 2030 | **14.98 → 5.97** (−9.00) | 69.70 → 53.73 (−15.97) | **282.8 → 84.3** (−198.5) | 2 → 0 (−2) | 0.066 → 0.084 (+0.018) | 0.164 → 0.223 (+0.059) |
| 2026–30 window | cumulative 81.04 → 53.81 (−27.23) | mean 59.13 → 52.06 (−7.06) | | | | |

**NYISO `results/ff-t1f-d106/nyiso` (`374fa81075c95ff8`) vs prior `results/ff-t1f-d60/nyiso` (`19a9690bb12c8459`)**
— determination **PROMOTE** (committed sidecar PROMOTE; categories/reasons/caveats/notes byte-identical).

| year | co2_mt | lw_price $/MWh | max_hourly_price | hours_ge_100 | reserve_margin | gas_cc_ccs share |
|---|---|---|---|---|---|---|
| 2026 | 23.74 → 24.17 (+0.44) | 50.21 → 50.87 (+0.65) | 64.8 → 66.0 (+1.2) | 0 → 0 | 0.185 → 0.185 (+0.001) | 0 → 0 |
| 2027 | 24.64 → 25.06 (+0.42) | 49.18 → 49.75 (+0.57) | 62.6 → 64.6 (+2.0) | 0 → 0 | 0.184 → 0.180 (−0.004) | 0 → 0 |
| 2028 | 24.24 → 17.64 (−6.60) | 54.13 → 51.31 (−2.82) | 65.1 → 66.6 (+1.5) | 0 → 0 | 0.178 → 0.171 (−0.008) | 0.065 → 0.142 (+0.077) |
| 2029 | 23.78 → 14.12 (−9.66) | 55.42 → 49.10 (−6.32) | 69.3 → 66.8 (−2.5) | 0 → 0 | 0.221 → 0.207 (−0.014) | 0.092 → 0.188 (+0.096) |
| 2030 | **20.98 → 11.49** (−9.49) | 61.08 → 55.12 (−5.96) | 77.3 → 74.3 (−3.0) | 0 → 0 | 0.223 → 0.203 (−0.020) | 0.152 → 0.233 (+0.081) |
| 2026–30 window | cumulative 117.37 → 92.49 (−24.88) | mean 54.00 → 51.23 (−2.78) | | | | |

Expected by the ruling: NEISO 2030 CO2 14.98 → 5.97, max price 282.8 → 84.3; NYISO 2030 CO2 20.98 → 11.49 — all hit.
Reserve-margin and share cells above are rounded to 3 places for the table; the sidecars carry 6.

## 3. What a re-registration would do to `ff-verdicts.json` (file untouched — the desk decides)

Against the live `neiso-t1f` / `nyiso-t1f` entries, the new sidecars differ ONLY in: `rubric_version` `"1.1"` → `"1.2"`;
`provenance.scored_at_sha` / `scored_at_date` (the FR-21 stamp, re-stamped on every score); the added
`supersession_delta` block; and `notes` — the board entries carry the desk's hand-authored registration note (D105/D106
prose) that the registrar appends and the scorer never emits (pre-existing, not this change). Determination,
`categories`, `reasons`, `caveats` are identical. The `-pre-d105` / `-pre-d106` entries would be the natural
`--prior-summary` sources for a re-score; none of the four keys is rewritten here.

## 4. Tests and checks

`tests/scoring/test_forecast_verdict.py` + `SupersessionDeltaTests` (version 1.2; absent prior ⇒ absent block, no caveat,
no note; two-summary fixture numerically right incl. absent-fuel 0.0 share and window totals; unpaired years listed and
excluded; statuses/determination/reasons/caveats/notes byte-identical with vs without the prior at EVERY tier) and
`test_cli_prior_summary_round_trip` (tiny synthetic summaries in `tmp_path`, scored through `main()`, sidecar carries
the block; absent without the flag). `ruff check` / `ruff format --check` clean on both touched Python files.
Fast lane over every test importing the scorer (`test_forecast_verdict`, `_t2`, `test_hindcast_run_config_artifact`,
`test_score_crossover`, `test_ff2d_emit_run_config`, `test_forecast_dof_ledger`, `test_driver_battery`,
`test_full_horizon_instruments`): **239 passed, 1 skipped, 36 subtests passed**.

## 5. Not touched (charter hard stops)

`scripts/register_forecast_run.py`, `scripts/build_forecast_dof_ledger.py` (D107), `frontend/data/forecast/program-status.json`
(D110), `scripts/calibration_verdict.py`, `docs/calibration-determination-rubric.md` (rule 37), `src/`, workflows,
`ff-verdicts.json`. No LP, no hydration beyond `code`.
