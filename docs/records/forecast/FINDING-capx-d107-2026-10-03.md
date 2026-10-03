# FINDING — capx D107: VERDICT_MAP re-point to the pre-D105/D106 verdicts + report-only `keeper_carry` (zero LP)

**Lane** capx D107 (code shard, zero LP) · **date** 2026-10-03 · DATA PROFILE: `code` · **pinned source_revision**
`51422d1b5f02bff56e85b26ebbb36090eed14599` (the charter's pin; behind `origin/main`) · **branch base** `origin/main`
`e7aa5d27cb587ba07b9ec38d91d2d2e8f79581e4` at fetch (the pin plus PRs #7152–#7155: PJM/MISO/SOCO keeper promotions and
the D110 `program-status.json` re-key; none touch this shard's files — `git diff --stat <pin> origin/main` over the
five files this lane reads or edits shows only CHANGELOG.md, +4 lines) · **branch** `claude/capx-d107-verdictmap-carry`
· **authority** the D105 §5 / D106 §5 routed follow-ups and FINDING-capx-d103-2026-10-03.md §3 (implemented as
written) · **rules** 21 [R-DOF], 24 [R-REGISTRY], 27 [R-PUSH], 32 [R-SHARD].

**Headline.** Two generated-sidecar defects closed and one report-only instrument added, no scored number moved.
(a) `scripts/register_forecast_run.py::VERDICT_MAP` re-points `neiso-2026-2030-d50-ccscapex` → `neiso-t1f-pre-d105`
and `nyiso-2026-2030-d60-arm` → `nyiso-t1f-pre-d106` (both keys verified present in `ff-verdicts.json`), so the
superseded D50 / D60-R3 runs stop baking the D105 / D106 verdicts into their generated registry sidecars; the D105 /
D106 run ids gain explicit rows to the live `neiso-t1f` / `nyiso-t1f` keys. (b) `scripts/build_forecast_dof_ledger.py`
emits a `keeper_carry` block — `carried_residual` / `carried_measured` / `not_applicable_in_forecast` — from the
designated keeper's rule-21 attestation, keeper → bundle resolved through the backcast registry sidecar's `bundle`
field, never a path rule. A test builds a ledger with and without the block and asserts the scored surface
(`status`, `n_entries`, `n_identified`, `n_unidentified`, `n_unattested`, `n_by_group`, `entries`) and the FC-7 score
at every tier are identical.

## 1. What was read

CLAUDE.md rules 21 / 24 / 27 / 32; `FINDING-capx-d103-2026-10-03.md` §3 (the design); `FINDING-capx-d105` §4–5 and
`FINDING-capx-d106` §4–5 (the preserved `-pre-d105` / `-pre-d106` keys, the new run ids and sidecars, and the routed
"re-point VERDICT_MAP" follow-up each names); `scripts/register_forecast_run.py` (VERDICT_MAP, `_verdict_key`:
`meta.verdict_key` wins, the map is the fallback); `scripts/build_forecast_dof_ledger.py` (`build_ledger`,
`_registry_identification`); `frontend/data/backcast/keepers/{NEISO,NYISO}.json` (`keeper` =
`2026-10-02-w0-neiso` / `2026-10-02-w0-nyiso`); `frontend/data/backcast/registry/<keeper>.json` (`bundle` =
`results/calibration/w0_neiso_span` / `w0_nyiso_span` — the field `promote_keeper.py`, `audit_keepers.py` and
`calibration_verdict.py` already read); both keepers' `calibration_attestation.json` `free_parameters.entries`
(NEISO 6 entries / 4 residual, NYISO 8 / 6 — D103 §2's census, unchanged).

## 2. Task (a) — VERDICT_MAP

| run id | before | after | key in `ff-verdicts.json` |
|---|---|---|---|
| `neiso-2026-2030-d50-ccscapex` | `neiso-t1f` | **`neiso-t1f-pre-d105`** | yes |
| `nyiso-2026-2030-d60-arm` | `nyiso-t1f` | **`nyiso-t1f-pre-d106`** | yes |
| `neiso-2026-2030-d105-w0neiso` | absent (sidecar `meta.verdict_key` only) | **`neiso-t1f`** | yes |
| `nyiso-2026-2030-d106-w0nyiso` | absent (sidecar `meta.verdict_key` only) | **`nyiso-t1f`** | yes |

The D105 / D106 sidecars already carried `meta.verdict_key = <iso>-t1f`, which `_verdict_key` prefers, so their
rendering does not change; the explicit rows make the map self-consistent (every live-key move in the map's own
chain has both halves) and are what the test pins. ERCOT's `ercot-2026-2030-d50-ccscapex` → `ercot-t1f` row is
untouched: no re-solve has moved `ercot-t1f` off that arm. No `ff-verdicts.json` value was edited.

**Pre-existing, not this lane's (reported, not fixed):** four VERDICT_MAP values have no key in the committed
`ff-verdicts.json` — `pjm-t1h-d74-nodefaultcap`, `pjm-t1h-d78r-sectorgate`, `pjm-t1h-pre-d67`,
`pjm-t1h-pre-d75rarm`. Those rows render score-only today (`_load_verdicts().get(key)` → `None`). The new test is
scoped to the four D107 rows so it does not fail on them; a PJM lane owns the resolution.

## 3. Task (b) — `keeper_carry` (report-only)

Implemented as D103 §3 wrote it, with the one unknown it flagged pinned: `_keeper_bundle(keeper, repo=REPO)` reads
`frontend/data/backcast/registry/<keeper>.json` and returns `REPO / rec["bundle"]`, `None` when the sidecar is absent,
unreadable or carries no `bundle`; a keeper id never implies a directory. `_keeper_carry(iso, keeper, repo=REPO)`
reads that bundle's `calibration_attestation.json` `free_parameters.entries` and sorts each by the curated
`KEEPER_CARRY` row (`(iso, name)` then `("*", name)`): no row or `live=False` → `not_applicable_in_forecast`; live and
`identification == "residual"` → `carried_residual` with `source` = `carried residual — <keeper>
free_parameters[<name>]; identification unchanged from the backcast keeper (rule 21); live in forecast via <field>`;
live otherwise → `carried_measured`. Each record carries `name`, `identification`, `keeper`, `forecast_field`, `why`,
`root_cause`; the block carries `note` (report-only), `keeper`, `keeper_bundle` and the three counts. `build_ledger`
appends it after every scored field is final, only when `registry_identification` resolved a keeper, and never reads
it back. `build_ledger`, `_registry_identification` gain a keyword `repo: Path = REPO` so the tests point them at a
synthetic tree; the CLI is unchanged.

Rebuilt against the committed D105 / D106 bundles (`--stdout --no-git`, nothing written):

| bundle | keeper → bundle | carried_residual | carried_measured | not_applicable_in_forecast | scored |
|---|---|---|---|---|---|
| `results/ff-t1f-d105/neiso` | `2026-10-02-w0-neiso` → `results/calibration/w0_neiso_span` | `offer_curve_smoothing` | `IMPORT_TRANCHES/EXPORT_TRANCHES[NEISO]` | `offer_curve_by_group`, `offer_curve_committed_below_floor[NEISO]`, `wefor_multiplier`, `reliability_floor coefficients` | 7 entries / 0 UNIDENTIFIED (unchanged) |
| `results/ff-t1f-d106/nyiso` | `2026-10-02-w0-nyiso` → `results/calibration/w0_nyiso_span` | `offer_curve_smoothing`, `NYISO_LOCAL_SELFSUPPLY_FRAC['Long_Island']`, `IMPORT_TRANCHES/EXPORT_TRANCHES[NYISO]` | — | `offer_curve_by_group`, `offer_curve_committed_below_floor[NYISO]`, `wefor_multiplier`, `reliability_floor coefficients`, `campd_ct_run_lengths_NYISO.csv (fast-start v3 horizon)` | 3 entries / 0 UNIDENTIFIED (unchanged) |

This is D103 §2's census to the row. The two uncurated names (`offer_curve_committed_below_floor[<ISO>]`, NYISO's
CAMPD CT run-length file) report `forecast_field: null`, `why: null` under `not_applicable_in_forecast` — D103 §3's
posture for an uncurated row (never claimed live). The committed `dof_ledger.json` files were not regenerated (not
chartered; the block lands in the next ledger a lane builds).

## 4. Tests

* `tests/scoring/test_register_forecast_verdict_map.py` (new, 7 cases): each D107-touched key exists in the committed
  `ff-verdicts.json` (key set only, no value read); the D50 / D60 rows resolve to the preserved keys and not the live
  ones; the D105 / D106 rows resolve to the live keys; `_verdict_key` prefers `meta.verdict_key`.
* `tests/scoring/test_forecast_dof_ledger.py::KeeperCarryIsReportOnlyTests` (7 cases) on a synthetic
  shard → registry → attestation tree: block present with the expected three lists for an ISO with a keeper and
  curated rows; absent with no keeper shard, with a registry sidecar whose bundle does not resolve, and with an
  attestation carrying no ledger; the bundle resolves only through the sidecar's `bundle` field (a sidecar without
  it → `None`); **with-vs-without the block, every scored field is byte-identical (`json.dumps(sort_keys=True)`) and
  `forecast_verdict._score_dof_ledger` returns the same row at t1 / t2 / t3**; a carried residual never identifies
  a scored entry (`n_unidentified == n_entries` either way).
* `uv run --frozen ruff check` + `ruff format --check` on the four touched files: clean.
* `uv run --frozen pytest -n auto -m "not slow and not integration and not fulldata" tests/scoring`: 1708 passed,
  18 skipped, 2 xfailed (the charter's `tests/scripts` does not exist; `tests/scoring` is where both touched test
  modules live).

## 5. Deviations and hard stops

* None of the hard stops were reached: no LP, no `run_*` / solve script, no hydration, no `src/market_sim/` edit, no
  edit to `ff-verdicts.json`, `calibration-complete.json`, any keeper shard, rubric file, `program-status.json`,
  `scripts/forecast_verdict.py` or `.github/workflows/`.
* The branch was cut from `origin/main` `e7aa5d27` rather than the pin `51422d1b`, as the charter instructed; the
  four PRs between them do not touch this lane's files.
* The pre-existing four dangling PJM VERDICT_MAP values (§2) are reported, not fixed.
