# FINDING — Lint hygiene lane (R-Z + R-AC), 2026-09-04

**Lane:** `claude/lint-hygiene-r-z-ac-zooe9c` → PR #4666. Executes X-1 of the
audit program board (`docs/handoffs/audit-program-director-board-2026-08.md`
v23) under owner rulings R-Z + R-AC (2026-09-03); program
`docs/model-audit-release-plan-2026-08.md`. Base: main at `8d5a3e16`.
DATA PROFILE: code. No solve; no test, marker, keeper shard,
`program-status.json`, matrix shard or workflow touched.

## 1. What was measured at the pin (lockfile ruff 0.15.17, `uv run ruff`)

The handoff's numbers were re-derived rather than trusted. Each command was
captured directly to a file (`cmd > f 2>&1; echo $?`), never through a pipe.

| command | at `8d5a3e16` (main) | after R-AC | after R-Z |
|---|---|---|---|
| `ruff check .` | exit 1 — 5 errors: E731 ×3, E402, E401, ALL under `docs/handoffs/d37/` and `d45/` | exit 0 | exit 0 |
| `ruff format --check .` | exit 1 — 11 files | exit 1 — 7 files | exit 0 (1356 files already formatted) |

The handoff expected ten format files (four probe scripts + six source/test
files). The re-measurement found **eleven**: the seventh source/test file,
`tests/unit/pipeline/test_caiso_ct_peaker_committed_measured.py`, landed with
caiso-241 (#4663, merged after the handoff was written). It is in R-Z's scope
by the handoff's own instruction ("re-measure").

## 2. R-AC — `docs/handoffs` excluded (commit `3a3b445a`)

`"docs/handoffs"` added to `[tool.ruff] extend-exclude` in `pyproject.toml`,
between the `results` entry and the HOUSE-1 `constants.py` block, with a
citation comment in the style of the existing entries. Rationale recorded in
the comment: the per-run capx probe scripts committed under `docs/handoffs/`
are session artifacts kept beside their finding, the same class as
`scripts/probes`; they re-reddened the `Ruff lint + format` job twice after
the source tree was repaired (R-W #4611/#4621, then R-X #4635). No probe
script was edited. The `constants.py` exclusion and every other entry are
byte-unchanged.

## 3. R-Z — seven files formatted (commit `b9384baf`)

Mechanical `uv run ruff format` on exactly the seven files listed by
`ruff format --check .` after R-AC. Layout only (the diff is line-wrapping and
parenthesis placement; ruff's own AST-equivalence check guards semantics).
`constants.py` was not formatted.

| file | lines after | ≥300 → blob-verified |
|---|---|---|
| `scripts/gen_nyiso177_attestation.py` | 329 | yes |
| `src/market_sim/data/fleet/campd_bins.py` | 2682 | yes |
| `src/market_sim/data/offer_curves.py` | 1646 | yes |
| `tests/regression/test_hourly_sidecars.py` | 241 | n/a |
| `tests/unit/data/test_campd_per_unit_attribution.py` | 338 | yes |
| `tests/unit/data/test_unit_outage_st_capacity_basis.py` | 339 | yes |
| `tests/unit/pipeline/test_caiso_ct_peaker_committed_measured.py` | 136 | n/a |

**Rule 27 `[R-PUSH]` verification:** the branch was pushed with `git push`
(exact on-disk bytes, small pack). Each of the five files ≥300 lines was then
fetched back from commit `b9384baf` through the GitHub contents API and its
reported blob SHA compared with the local `git rev-parse HEAD:<path>`; all
five match (`5a2b0f13`, `e06b6f52`, `f3581959`, `08a6847e`, `e060fb53`).

## 4. Gate scripts at the branch head

| gate | exit |
|---|---|
| `audit_keepers.py --check` | 0 |
| `check_registry_payload_parity.py` | 0 |
| `check_mechanism_matrix.py --base origin/main` | 0 |
| `check_forecast_staleness.py` | 0 |
| `check_bench_freshness.py` | 0 (20 parts, 0 STALE) |
| `check_golden_manifest.py` | 0 |
| `check_gate_a_provenance.py` | **1 — pre-existing on main, not this lane's** |

`check_gate_a_provenance` reports that CAISO's `gate.a_keeper_marker` in
`frontend/data/forecast/program-status.json` still cites the superseded keeper
`2026-09-03-caiso-240-b1-stgas` while the CAISO keeper shard now designates
`2026-09-03-caiso-241-b1-ctpeaker` (re-keyed by #4663). Two independent
grounds establish that this is main's state rather than this branch's: the
script reads only the keeper shards, `calibration-complete.json` and
`program-status.json`, none of which this branch changes (`git diff
--name-only origin/main..HEAD` is pyproject.toml plus the seven formatted
files); and the same step already failed on the caiso-241 branch's final
ci.yml run (33799163697, job `FR-21 forecast-board staleness`, step
`check_gate_a_provenance` → failure). Editing `program-status.json` is
forbidden for this lane; the re-key belongs to the CAISO lane (audit board
F-5).

## 5. CI record for PR #4666 (from the run's own API record)

ci.yml run **33838799570** (event `pull_request`, head `b9384baf`, the R-Z
commit; https://github.com/jessicacohen554-cyber/market-simulator/actions/runs/33838799570).

| job | conclusion | note |
|---|---|---|
| `Ruff lint + format` (job 100916660380) | **success** | step `Ruff lint` → success (`All checks passed!`); step `Ruff format check` → success (`1356 files already formatted`) |
| `Fast test tier` (job 100916660350) | **failure** — INHERITED, not this lane's | `2 failed, 7846 passed, 34 skipped, 2 xfailed`. The two: `tests/scoring/test_forecast_parity.py::test_all_six_keepers_resolve` (CAISO `caiso_ct_peaker_committed_measured` armed in the keeper with no forecast consumer / registry declaration) and `tests/scoring/test_gate_a_provenance.py::test_live_board_passes` (the §4 CAISO gate.a re-key). The caiso-241 branch's last run 33799163697 (job 100794050048) failed on EXACTLY the same two tests with the same `2 failed, 7846 passed` summary before this branch existed; both are the pytest twins of the FR-22 / FR-21 script failures below, and every one of the seven formatted test files passed. |
| ruff version CI installed | **0.15.17** | from the lint job's `Install dependencies` step log: `+ ruff==0.15.17`, i.e. the lockfile binary |

Other jobs on the run, all inherited from main and untouched by this lane
(each failed identically on the caiso-241 branch's last run 33799163697
before this branch existed):

- `FR-21 forecast-board staleness (WARN only)` → failure at
  `check_gate_a_provenance` (the CAISO gate.a re-key, §4).
- `FR-22 backcast->forecast parity` → failure: three keeper-armed fields with
  no forecast consumer / registry declaration (`ercot_storage_as_soc_reserve`,
  `caiso_ct_peaker_committed_measured`, `nyiso_seam_deliverability_envelope`).
- `Forecast-invariant artifact audit` → failure: registered T1-H / T3 runs
  with I7 / I3 FAILs not declared in `invariant-failures.json`.

Green on the run: Structural refactor guards, Rule-28 mechanism-matrix guard,
Cache-key registration guard, Rule-22 quarantine gates, Pinned default cache
key.

## 6. Owner note

Once #4666 merges, `Ruff lint + format` may be added to the required-check
set (R-AB was flipped without it). The `docs/handoffs` exclusion is what
keeps it green against future probe-script commits; a NEW source/test file
still has to pass `ruff format --check` on its own PR.
