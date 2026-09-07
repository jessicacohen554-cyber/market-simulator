> Status: **FINAL** — the operator-facing user manual (layer L2). Verified
> command-by-command on a clean clone at the DOCS-B finalization pass
> (2026-09-05, model-audit WS4 / gate G2).

# market-sim — User Manual

**Audience.** Anyone who has to *run* this model: install it, hydrate its data,
launch a forecast or a backcast, and find the outputs. It is deliberately a
**consolidation of verified facts**, not a tutorial and not a methodology text.

**How this doc was built (and how to keep it honest).** Every command, flag,
default and path below was verified against the code that implements it on
`origin/main`, argparse read directly and `--help` executed in a synced `uv`
environment — first at `ce779f9` (2026-08-16), then **re-executed end to end on a
clean clone** at the DOCS-B finalization pass (2026-09-05), which is where the
counts and keys below were last re-derived. Where prose elsewhere in the repo
disagrees with the code, the code wins and this manual follows the code; the
divergences found while writing it are listed in
[§10](#10-known-doc-divergences-found-while-writing-this-manual). Source
citations sit in HTML comments beside each claim.

**What this manual is not.**

- Not the methodology. That is [`../model-methodology-spec.md`](../model-methodology-spec.md) (LP formulation, pricing, capacity evolution).
- Not the engineering reference. That is [`codebase/`](codebase/) — what the code does, page by page.
- Not the calibration/scoring regime. That is [`calibration-and-validation-methodology.md`](calibration-and-validation-methodology.md) plus the two determination rubrics.
- Not the governance rulebook. That is [`../CLAUDE.md`](../CLAUDE.md). Rules are cited here by their stable `[R-*]` IDs; ordinals drift, IDs do not.

---

## Contents

1. [What you are installing](#1-what-you-are-installing)
2. [Install](#2-install)
3. [Data setup](#3-data-setup)
4. [CLI reference](#4-cli-reference)
5. [Configuration files](#5-configuration-files)
6. [Where outputs land](#6-where-outputs-land)
7. [Operational constraints](#7-operational-constraints--read-before-your-first-solve)
8. [Running the tests](#8-running-the-tests)
9. [Troubleshooting](#9-troubleshooting)
10. [Known doc divergences](#10-known-doc-divergences-found-while-writing-this-manual)

---

## 1. What you are installing

An LP-based electricity-market dispatch and policy simulator. Hourly (8760)
generation, prices, emissions and capacity evolution across six U.S. ISOs,
2026→2050, plus a historical-**backcast** mode that re-runs a past year against
actuals (EIA-930, CAMPD, eGRID, EIA-923) for calibration.

| | |
|---|---|
| Solver | HiGHS via `highspy` — **pure LP, no MIP**. Prices are LP duals. |
| Python | ≥ 3.11 <!-- pyproject.toml requires-python = ">=3.11" --> |
| ISOs | `ERCOT`, `CAISO`, `MISO`, `PJM`, `NYISO`, `NEISO` <!-- src/market_sim/config/iso_configs.py SUPPORTED_ISOS, verified at runtime --> |
| Forecast horizon default | 2026 → 2050 <!-- config/constants.py START_YEAR=2026 END_YEAR=2050 --> |
| Hours per year | 8760, fixed non-leap calendar (Feb 29 dropped) <!-- config/constants.py HOURS_PER_YEAR=8760 --> |

ERCOT is the calibrated reference ISO; the others carry topology and
plant-to-zone assignment with varying backcast maturity.

**Two things surprise every new operator**, so they are stated up front:

1. **A default forecast invocation is refused.** **Four of the eight** shipped
   scenario configs — including `ercot_base.yaml`, the one the README and the
   codebase pages point at — exceed the §2.1b solve-window cap and hard-fail
   without an explicit owner authorization flag.
   See [§4.1](#41-the-21b-solve-window-cap--read-this-first).
2. **A fresh clone cannot solve anything.** `data/clean` is derived and
   gitignored, several `data/raw` corpora are now untracked, and a few loaders
   raise rather than no-op. See [§3](#3-data-setup).

---

## 2. Install

### 2.1 Get the code — use a partial clone

The git pack a full clone transfers is **≈5.5 GiB**, most of it immutable
`data/raw` source data. Since the 2026-08-16 history rewrite a full bare clone
does complete (≈162 s measured through the egress proxy), so it no longer stalls
outright — but minutes versus seconds still argues for the partial clone. **A
shallow clone is not the fix** (`--depth 1` still transfers the whole tip tree).
Use a **blobless partial clone**:

```bash
ORIGIN=https://github.com/jessicacohen554-cyber/market-simulator

git clone --filter=blob:none --sparse --no-checkout "$ORIGIN" market-simulator
cd market-simulator
git sparse-checkout set --no-cone '/*' '!/data/raw/'
git checkout main
```

That is the whole codebase — code, tests, docs, dashboard — without `data/raw`:
a few seconds of transfer for a ~306 MB checkout. Full rationale, measurements
and three non-obvious hydration traps: [`fast-clone.md`](fast-clone.md).

> **In a partial clone, never resolve a blob you do not intend to download.**
> Any git read of a missing blob silently fetches it, so a stray
> `cat-file --batch-check` over `data/raw` pulls the whole corpus. Read trees
> only, and run read-side git calls under `GIT_NO_LAZY_FETCH=1` so a regression
> fails loudly.

### 2.2 `uv` — the canonical path

`uv` + `pyproject.toml` + `uv.lock` is what CI uses and what dependency versions
are pinned against. Use it for development, calibration runs, and anything you
intend to debug.

```bash
uv sync                       # creates .venv from pyproject.toml + uv.lock
uv run market-sim --help
uv run python -m pytest -q -m "not slow and not integration and not fulldata"
```

### 2.3 pip — fallback only

`requirements.txt` is a **generated**, fully-pinned export of the runtime
dependencies (no dev extras), provided only for environments without `uv`.

```bash
pip install -r requirements.txt
```

Do not hand-edit the pins. Regenerate from the lockfile:
<!-- requirements.txt:1-12 header — generated, NOT the source of truth -->

```bash
uv export --format requirements-txt --no-dev --no-emit-project --no-hashes > requirements.txt
# then re-add the file's header comment block
```

### 2.4 The launcher — convenience only

`run-simulator.sh` (macOS/Linux) and `run-simulator.bat` (Windows) bootstrap a
plain `venv` + `pip install -e .` on first run and open a local web UI at
`http://127.0.0.1:8765/`.
<!-- run-simulator.sh — venv bootstrap then exec tools/launcher.py; PORT=8765 in tools/launcher.py -->

```bash
./run-simulator.sh
```

**Caveats — read before relying on it:**

- It is **not** the reference install. It builds a plain `venv` from
  `pyproject.toml` only; `uv.lock`'s exact pins are not applied, so the
  environment can drift from CI's.
- It is **ERCOT-only**. The UI drives
  `run_calibration_full.py --plant-tranche-config <sheet>` against an editable
  per-plant tranche sheet and regenerates the ERCOT backcast payloads.
  <!-- tools/launcher.py module docstring -->
- Its comparison baseline resolves dynamically through the ERCOT keeper shard →
  registry sidecar → bundle dir, and **degrades to "no baseline"** if any link
  is missing (e.g. a clone without that bundle hydrated). It no longer hardcodes
  a bundle path.
  <!-- tools/launcher.py:_resolve_baseline() — the run10_peak85 hardcode was removed by DEBUG-A, docs/handoffs/debug-sweep-2026-08.md triage row 3 -->
- It shells out to the same solver as everything else, so every constraint in
  [§7](#7-operational-constraints--read-before-your-first-solve) applies
  unchanged.

Prefer `uv` for anything that matters.

---

## 3. Data setup

The data story changed materially in August 2026 (the BLOAT-B corpus
conversions). It now has **four** independent steps, and skipping any of them
produces a loud failure at input-load time, not a silent degradation.

```
   clone (partial)  →  hydrate data/raw  →  per-corpus fetch  →  rebuild data/clean
   §2.1                §3.1                 §3.2                §3.3
```

### 3.1 Hydrate `data/raw` — per-session data profiles

`scripts/hydrate_data.py` pulls `data/raw` subtrees on demand from
`configs/data-profiles.yaml`.

```bash
python3 scripts/hydrate_data.py --list       # profiles + coverage
python3 scripts/hydrate_data.py --profile pjm
python3 scripts/hydrate_data.py --show       # current clone state
python3 scripts/hydrate_data.py --dry-run --profile ercot
python3 scripts/hydrate_data.py --profile code   # drop data/raw again
```
<!-- verified: uv run python scripts/hydrate_data.py --help → {--profile,--list,--show,--dry-run,--force} -->

| Profile | Packed | Use |
|---|---:|---|
| `code` | 0 | Docs, governance, dashboard, review, CI — anything that does not solve. **The default.** |
| `shared` | ~1.2 GB | Cross-ISO data-contract / curation / schema work. |
| `pjm` `miso` `neiso` | ~1.3 GB | That ISO's calibration or forecast lane (`shared` + the ISO's subtrees). |
| `nyiso` | ~1.4 GB | ” |
| `caiso` | ~2.2 GB | ” |
| `ercot` | ~5.9 GB | ERCOT is the heavy one. |
| `all` | ~7.2 GB | Genuinely cross-ISO solves only. |
<!-- configs/data-profiles.yaml profiles block; approx_gb measured 2026-08-13, indicative -->

Budget **~1.5×** on disk — checked-out files are uncompressed. Hydration is
incremental, so widening later (`--profile ercot`) re-fetches nothing already
local.

### 3.2 Per-corpus fetch — the untracked corpora

Several `data/raw` corpora now have their **payloads untracked at tip**. Every
converted corpus keeps the same tracked artifacts: `README.md`,
`SHA256SUMS.txt`, and a verified source-URL table.

> ⚠ **Recovery is re-fetch ONLY. Do not reach for a pin sha.** An earlier
> revision of this manual said history was kept and offered
> `git restore --source=<pin-sha>` as an always-available route to the exact
> bytes. **That is no longer true.** The
> `cleanup-large-blobs.yml` history rewrite was executed for real on
> **2026-08-16** (an explicit owner decision) and force-pushed: it stripped the
> untracked payloads from history along with 7,254 superseded blobs, so the
> pin shas recorded in the corpus READMEs are **dead references**, and so is
> every pre-2026-08-16 commit-sha citation outside
> `docs/governance/citation-commit-map.txt`. Some payloads are now
> **unrecoverable from this repository at all** — the CAISO OASIS GRP dailies
> and pre-slim SCED columns past MIS retention among them. Read the corpus
> README before concluding data is missing.
> <!-- CLAUDE.md "Cloning & session data"; docs/FINDING-history-rewrite-2026-08-16.md -->

| Corpus | Why untracked |
|---|---|
| `data/raw/ercot/SCED/` 2024-04→2026-02 + `rtcb-format-2026/` | Size; the ERCOT-157 window 2023-03→2024-03 **stays tracked** (irreplaceable). |
| `data/raw/caiso-dam-outages/daily/*.xlsx` | Size; the derived `caiso-dam-outage-windows.parquet` every runtime consumer reads **stays tracked**. |
| `data/raw/lmp-data/CAISO/*_csv.zip` (OASIS GRP dailies) | Past OASIS retention — history-as-archive is the only recovery. |
| `data/raw/{ERCOT,MISO,PJM-AS,NYISO}` publication PDFs | Hand-read citation sources; no code consumer. |
| `data/raw/NYISO/nyiso load reports *.zip` | Zero consumers. |
| Three probe-only 60-day SCED extracts | Frozen-probe consumers only. |
| `pjm-energy-offers`, `caiso-public-bids`, `miso-energy-offers`, `pjm-da-virtuals` | **Licensing**, not size — non-member redistribution restrictions. |
<!-- .gitignore BLOAT-B-2 / BLOAT-B-5 conversion blocks; docs/bloat-removal-plan-2026-08.md §8 -->

**Recovery — re-fetch from source** (regenerates; byte-identity is not
guaranteed). This is the primary and, for most corpora, the only route. Each
corpus README names its fetch script, e.g.:

```bash
python scripts/data/fetch_caiso_dam_outages.py 2021-06-18 <today>
python scripts/data/fetch_pjm_da_virtuals.py --years 2023 2024 2025 --feeds hrl_da_incs_decs
```
<!-- fetch_pjm_da_virtuals.py --help verified: {--years,--months,--feeds{hrl_da_incs_decs,hrl_dmd_bids},--force,--sleep} -->

Verify against the tracked manifest:

```bash
cd data/raw/<corpus> && sha256sum -c SHA256SUMS.txt
```

> **Licensed fetches are not hermetic.** `fetch_pjm_da_virtuals.py` is a live
> PJM DataMiner2 API call (36 monthly files for a 3-year span) and through a
> proxied egress it returns intermittent **502 Bad Gateway** mid-pagination. The
> script backs off and resumes on its own and the files land intact, but budget
> wall-clock for it and do not treat the run as reproducible.
> <!-- docs/FINDING-debug-b-pjm-input-clock-2026-08-15.md §8 item 2 -->

### 3.3 Rebuild `data/clean` — required, and slow

`data/clean` is **derived and gitignored**. Several loaders raise rather than
no-op when their partition is absent, so a fresh clone aborts at input-load time
before any LP work.

```bash
python scripts/regenerate_clean.py --list      # the datatype list (55 at 2026-09-05)
python scripts/regenerate_clean.py             # all
python scripts/regenerate_clean.py lmp load    # a subset
```
<!-- re-verified 2026-09-05: --list emits 55 datatypes; each maps to scripts/data/curate_<datatype>.py -->

**Budget ~2 hours** for a full rebuild across all ISOs. Curation scripts are
independent — a failure in one is reported and the rest continue — and the only
expected skips are genuinely absent non-local sources.
<!-- docs/FINDING-debug-b-pjm-input-clock-2026-08-15.md §8 item 1: ~2 h wall-clock measured over the then-50 datatypes -->

> **Plan a fresh-clone replay accordingly.** A PJM keeper replay from a clean
> container needs the ~2 h `regenerate_clean.py` rebuild **plus** the live
> licensed `pjm-da-virtuals` fetch before the first LP row is built. If you are
> registering a bundle in-session under `[R-DASHBOARD]`, that is scheduling time
> you must allow for.

---

## 4. CLI reference

Two families, and they do different jobs:

| Family | Command | Mode | Job |
|---|---|---|---|
| **Forecast** | `market-sim run\|sweep\|ensemble\|matrix` | forecast | 2026→2050 trajectories, sweeps, ensembles, named-case matrices |
| **Backcast** | `scripts/run_calibration_full.py` | backcast | The bundle-producing calibration harness — solve, persist, report |
| **Backcast (light)** | `scripts/run_calibration.py` | backcast | Solve + print an EIA comparison; **no bundle**, no dashboard artifacts |

Entry points for the forecast CLI are interchangeable:
<!-- pyproject.toml:23 market-sim = "market_sim.runner:main"; src/market_sim/__main__.py -->

```bash
uv run market-sim …
uv run python -m market_sim …
```

### 4.1 The §2.1b solve-window cap — read this first

**Every `market-sim` subcommand refuses a forecast window wider than 5
solve-years** unless `--full-solve-authorized` is passed.
<!-- config/schedulable.py::MAX_UNAUTHORIZED_SOLVE_YEARS = 5, ::add_authorization_flag; runner.py::_add_authorization_flag attached to all four subparsers -->

- The window is resolved from the config, falling back to `START_YEAR`/`END_YEAR`
  (2026–2050 = **25** solve-years) when the YAML carries no year fields — so a
  YAML that simply omits them is over-cap.
  <!-- config/schedulable.py::config_horizon -->
- **Backcast configs are exempt**: a backcast window is governed by `[R-HOLDOUT]`'s
  tiers via `run_calibration_full.py --holdout-authorized`, not by §2.1b.
  <!-- config/schedulable.py::assert_config_schedulable — `if config.mode != "forecast": return None` -->
- `sweep` and `matrix` check **every expanded member**, not just the base.
  <!-- runner.py, the sweep and matrix dispatch branches of main() -->
- The flag is *authorization*, not a bypass. Pass it only with an explicit,
  session-logged per-campaign owner authorization.

Measured against the eight shipped scenario configs:

| Config | Horizon | Default invocation |
|---|---|---|
| `configs/scenarios/ercot_ces_base_2026_smoke.yaml` | 2026–2026 | ✅ runs (1 yr) |
| `configs/scenarios/ercot_ces_poc_2026_smoke.yaml` | 2026–2026 | ✅ runs (1 yr) |
| `configs/scenarios/pjm_ces_base_2026_smoke.yaml` | 2026–2026 | ✅ runs (1 yr) |
| `configs/scenarios/ercot_ces_poc_2026_2030.yaml` | 2026–2030 | ✅ runs (5 yr, at the cap) |
| `configs/scenarios/ercot_base_2026_2032.yaml` | 2026–2032 | ❌ **REFUSED** (7 yr) |
| `configs/scenarios/ercot_base.yaml` | 2026–2050 | ❌ **REFUSED** (25 yr) |
| `configs/scenarios/ercot_ces_base_2026_2050.yaml` | 2026–2050 | ❌ **REFUSED** (25 yr) |
| `configs/scenarios/pjm_ces_base_2026_2050.yaml` | 2026–2050 | ❌ **REFUSED** (25 yr) |
<!-- verified by executing assert_config_schedulable(cfg, False, ...) over configs/scenarios/*.yaml, 2026-08-15 -->

The refusal text names the schedulable instruments (T0, T1-F 2026–2030, T1-X
2023–2027, T1-H 2021–2025 — all ≤5 yr) and the gate conditions.

### 4.2 `market-sim run` — a single scenario

```bash
market-sim run --config <scenario.yaml> [--iso ISO] [--full-solve-authorized]
```

| Flag | Default | Meaning |
|---|---|---|
| `--config` | *required* | Path to a scenario YAML. |
| `--iso` | config's own `iso` | Override the ISO. |
| `--full-solve-authorized` | off | §2.1b authorization ([§4.1](#41-the-21b-solve-window-cap--read-this-first)). |
<!-- runner.py::_build_parser, the `run` subparser -->

Loads a `ScenarioConfig`, runs every year in the window **sequentially** for one
ISO via `run_scenario_iso`, and returns the deterministic `cache_key`.
<!-- runner.py::run_scenario_iso; the `run` dispatch branch of main() -->

```bash
market-sim run --config configs/scenarios/ercot_ces_poc_2026_2030.yaml
market-sim run --config configs/scenarios/ercot_ces_poc_2026_smoke.yaml --iso CAISO
```

### 4.3 `market-sim sweep` — a parameter sweep

```bash
market-sim sweep --sweep <sweep.yaml> [--workers N] [--full-solve-authorized]
```

| Flag | Default | Meaning |
|---|---|---|
| `--sweep` | *required* | Path to a sweep YAML. |
| `--workers` | `min(2, cpu_count − 1)` | Worker processes. |
<!-- runner.py::_build_parser, the `sweep` subparser; default resolved by pipeline/members.py::resolve_workers with cap=DEFAULT_MEMBER_CAP=2 -->

Expands a `SweepDefinition` into `(config, iso)` pairs and runs them across a
process pool. **Separate members are the parallelism unit; years inside a member
stay sequential.**

> ⚠ **An explicit `--workers` is honoured as given — it is not clamped.**
> The `[R-PARALLEL]` cap of 2 is the *default*, not a ceiling, on `sweep` and
> `ensemble`. Only `matrix` hard-caps. Raising it on a per-plant ISO OOMs.
> <!-- pipeline/members.py::resolve_workers "an explicit value is honoured as given"; matrix.py::run_matrix clamps -->

### 4.4 `market-sim ensemble` — weather-year or sampler distribution

```bash
market-sim ensemble --config <scenario.yaml> [--iso ISO] \
    [--weather-years 2023 2024 2025] [--workers N] [--out dist.json]

market-sim ensemble --config <scenario.yaml> --sampler <spec.yaml> \
    [--draws N] [--seed N] [--out-dir DIR] [--structural-prior]
```

Two mutually-shaping paths — the member axis is either the **weather year** or a
**multivariate draw**:

| Flag | Default | Meaning |
|---|---|---|
| `--config` | *required* | Forecast scenario YAML. |
| `--iso` | config's own | Override the ISO. |
| `--weather-years` | ISO's verified pool | Weather-only path. **Ignored when `--sampler` is given.** |
| `--sampler` | none | Uncertainty-sampler YAML (PB-2). Switches the member axis to the draw. |
| `--draws` | spec's `n` | Overrides the spec. **Requires `--sampler`.** |
| `--seed` | spec's `seed` | Overrides the spec. **Requires `--sampler`.** |
| `--workers` | `min(2, cpu_count − 1)` | See the warning in [§4.3](#43-market-sim-sweep--a-parameter-sweep). |
| `--out-dir` | none | Sampler output surface (draws/metrics/bands parquet + `ensemble_meta.json`). **Requires `--sampler`.** |
| `--out` | none | Weather-year distribution JSON. Weather-only path; skipped if omitted. |
| `--structural-prior` | off | Folds the D-7 structural-error prior into the emissions band (PB-3). **Requires `--sampler` and `--out-dir`.** |
<!-- runner.py::_build_parser, the `ensemble` subparser, and its dispatch branch in main() -->

Note the cap arithmetic: an ensemble solves the window **once per member**, so an
over-cap window is over-cap many times over. The §2.1b check is applied to the
window (its unit); member count is reported by the drivers.
<!-- runner.py, the `ensemble` dispatch branch of main() -->

### 4.5 `market-sim matrix` — named-case scenario matrix

```bash
market-sim matrix --config <base.yaml> --matrix <cases.yaml> \
    [--iso ISO] [--workers N] [--out-dir DIR]
```

| Flag | Default | Meaning |
|---|---|---|
| `--config` | *required* | Base forecast scenario YAML — cases override **onto** it. |
| `--matrix` | *required* | A **cases-mode** sweep YAML, e.g. `configs/scenario_matrix.yaml`. |
| `--iso` | base config's own | Override the ISO. |
| `--workers` | 2 | **Hard-capped at 2**, never exceeded even if you ask for more. |
| `--out-dir` | `results/ensemble/<matrix_id>/` | Output directory. |
<!-- runner.py::_build_parser, the `matrix` subparser; matrix.py::MAX_CONCURRENT_CASES = 2, applied as min(workers, MAX_CONCURRENT_CASES) -->

`configs/scenario_matrix.yaml` ships **13 named AEO/IPM-style cases** over five
axes. Its label is load-bearing: this is a *deterministic scenario range, **not**
a probability band* — no likelihoods attach to the 13 points.
<!-- matrix.py::LABEL; configs/scenario_matrix.yaml header + 13 cases verified -->

The matrix CLI takes **no year arguments at all** — the horizon rides the base
YAML and its cases may override it, which is exactly why an unguarded
`market-sim matrix` was the forecast-readiness audit's headline FR-25 hole. Both
the base and every expanded case are cap-checked.
<!-- runner.py, the `matrix` dispatch branch of main() -->

### 4.6 `scripts/run_calibration_full.py` — the backcast harness

This is the entry point that produces **dashboard-registrable bundles**. It
exposes several hundred long options — the great majority of them per-ISO
mechanism gates that belong to a specific keeper recipe, not to routine
operation. The tables below are the operational subset.

> ⚠ **`run_calibration_full.py --help` currently CRASHES.** At the
> 2026-09-05 re-verification it exits with
> `ValueError: unsupported format character ')'` from inside
> `argparse.format_help()`. The cause is a literal `%` in the
> `--caiso-st-gas-peak-measured` help string (`"(+6.0 %)"`), which argparse
> tries to interpolate; it needs `%%`. **The parser itself is fine** — every
> flag parses and every documented invocation below runs normally; only the
> rendered `--help` catalogue is unavailable. Until it is fixed, read the flag
> list from the argparse block in the script. Routed to the calibration desk by
> DOCS-B (docs-only lane, cannot patch `scripts/`).
> <!-- reproduced 2026-09-05 on a clean clone: uv run python scripts/run_calibration_full.py --help -->

```bash
python scripts/run_calibration_full.py --iso PJM --year 2023 2024 2025
```

**Core:**

| Flag | Default | Meaning |
|---|---|---|
| `--iso` | `ERCOT` | ERCOT runs the full plant-level diagnostic; other ISOs run energy-only. |
| `--year` | `2023 2024` | One or more backcast years. Multi-year ISOs solve **all** scorable years in one invocation (`[R-ALLYEARS]`). |
| `--hours` | 8760 | Dispatch horizon; lower it only for a smoke test. |
| `--out-dir` | `results/calibration/<iso>/<timestamp>` | Bundle root. |
| `--note` | none | Free-text note recorded in the bundle's `run_config.json` beside the full config and git provenance. |
| `--holdout-authorized` | off | Authorizes a solve over an out-of-training year. **Also** requires the ISO to carry **that year's tier marker** — `complete` for a validation year (2020–2022), `final` for a locked-test year (2019, H1-2026). Without both, an out-of-window `--year` hard-fails (`[R-HOLDOUT]`, [§7.5](#75-holdout-discipline--r-holdout)). |
<!-- scripts/run_calibration_full.py argparse block; --note/--out-dir help text verified from --help at ce779f9, before --help regressed (see the warning above) -->

**Re-report and replay (no fresh dispatch):**

| Flag | Meaning |
|---|---|
| `--report DIR` | Skip solving; print the report from an existing bundle. |
| `--replay-bundle DIR` | Re-solve a committed bundle's **exact recipe** — `DIR/meta.json` supplies every solve kwarg, so a keeper reproduces without spelling it flag-by-flag. All other solve flags are ignored on this path (**the bundle is the config**); `--out-dir`/`--note` override destination and provenance, `--year` overrides the span (still holdout-gated). |
| `--rebuild-benchmark DIR` | Rebuild a bundle's benchmark parquets off its meta and re-report. No re-solve. |
<!-- verified from --help; the three paths stay at the global warm-start default OFF for reproducibility -->

**Performance and provenance:**

| Flag | Default | Meaning |
|---|---|---|
| `--no-xyear-warmstart` | off (i.e. warm-start **ON**) | Cross-year LP warm-start is **ON by default** for a fresh calibration solve — each year's optimal basis warm-starts the next year's P0 (~2.3× faster on warm years, basis-neutral). Pass this for a cold, basis-independent A/B baseline. No effect on `--report`/`--replay-bundle`/`--rebuild-benchmark`. |
| `--reuse-solved PRIOR_BUNDLE` | off | Copy per-year solve artifacts from a prior bundle instead of re-solving years whose effective config **and** full recipe match, with code + data pinned. Refuses on a dirty tree, changed `src`/`scripts`/`data`, a moved `highspy`, or differing per-year inputs. **Reused years are not fresh evidence** — keeper promotion still requires a full fresh solve of every year. |
| `--persist-p0-commitment` | off | Additionally write the bit-packed P0 on/off pattern + startup-run ratios. **Write-only and additive — cannot change a solve.** |
| `--zero-forcing-ablation` | off | Solve the D-3 ablation **twin** of this config (every merchant floor/bridge neutralized), landing in `<out-dir>-ablation`, covering the same full span. `audit_keepers` E9 requires it. Launch as a *concurrent separate invocation* from the keeper (`[R-PARALLEL]`). |
<!-- all four verified verbatim from the rendered --help -->

**The archived P2 pass.** P0/P1 are the only production passes and **every run is
scored on P1**. The legacy P2 commitment flags (`--commitment`,
`--ercot-as-aware-commitment`, `--run-p2`, `--no-coal-p2`,
`--persist-p2-state`, `--class-commitment-overrides`) are hidden from `--help`
and **hard-error** unless `--enable-legacy-p2` is passed. No keeper uses P2.
<!-- run_calibration_full.py --enable-legacy-p2 gate with argparse.SUPPRESS on the P2 flags; run_calibration.py raises parser.error on the same set -->

### 4.7 `scripts/run_calibration.py` — light backcast diagnostic

Solves the requested years and prints an EIA comparison report. It does **not**
write a dashboard-registrable bundle — use `run_calibration_full.py` for
anything that will be registered.

```bash
python scripts/run_calibration.py --iso ERCOT --year 2024 --hours 168
```

| Flag | Default | Meaning |
|---|---|---|
| `--year` | *required* | One or more calibration years. |
| `--iso` | `ERCOT` | ISO to calibrate. |
| `--hours` | 8760 | `168` for a quick smoke test. |
| `--ttc-wn` / `--ttc-wsc` / `--ttc-pn` | none | Override ERCOT West↔North / West↔South_Central / Panhandle↔North transfer capability (MW). |
| `--coal-passthrough` | none | Override the PRB take-or-pay fuel-cost fraction; `1.0` disables the discount. |
| `--priced-interchange` / `--no-priced-interchange` | per-ISO (on for **CAISO**) | Serve interchange through the priced import/export node instead of the measured schedule added to demand. |
| `--reference-price-interface` | off | Serve the priced seam through the forecast-grade reference-price interface. Implies `--priced-interchange`; gated to ISOs in `INTERFACE_NEIGHBORS` (PJM). |
| `--negative-renewable-offers` / `--no-…` | per-ISO base value (on for CAISO) | Floor curtailable wind/solar offers at the negative keep-running value so oversupply sets sub-$0 prices. |
| `--mass-cap-enabled`, `--mass-cap-tons`, `--mass-cap-program` | off / none / none | Thread the carbon resolver's power-sector mass-cap row instead of the measured price adder. **Diagnostic-only; never a keeper default.** |
| `--no-xyear-warmstart` | off (warm-start **ON**) | As in §4.6. |
| `--enable-legacy-p2` | off | Unlocks the archived P2 pass. |
<!-- scripts/run_calibration.py argparse block; re-verified 2026-09-05 against the rendered --help (which still renders), reporting "Default per ISO: on for CAISO" -->

Warm-start precedence, highest first: `--no-xyear-warmstart` → an explicitly-set
`MARKET_SIM_WARMSTART_XYEAR` env var → default **ON**.
<!-- run_calibration.py::resolve_xyear_warmstart_default -->

---

## 5. Configuration files

### 5.1 `configs/` layout

```
configs/
├── scenarios/                    # 8 scenario YAMLs (market-sim run/ensemble/matrix base)
├── scenario_matrix.yaml          # the 13-case AEO/IPM-style matrix (cases mode)
├── ces_premium_matrix*.yaml      # federal-CES premium matrices
├── uncertainty_ercot*.yaml       # uncertainty-sampler specs (market-sim ensemble --sampler)
└── data-profiles.yaml            # hydration manifest (scripts/hydrate_data.py) — NOT a scenario
```

### 5.2 Scenario YAML

A scenario file lists **only overrides**; every unspecified field takes its
`ScenarioConfig` default. `ScenarioConfig` carries **~800 fields** (794 at this pass), so this is the
normal shape of a scenario:
<!-- re-derived 2026-09-05: len(dataclasses.fields(ScenarioConfig)) == 794. The
     exact count moves with every gated mechanism; read it from the code, not
     from here. -->

```yaml
# configs/scenarios/ercot_base.yaml
mode: forecast          # "forecast" (default) | "backcast" — never inferred
iso: ERCOT
start_year: 2026
end_year: 2050
```

Fields worth knowing before you write your first config:

| Field | Default | Note |
|---|---|---|
| `mode` | `forecast` | The explicit switch. Backcast-only devices (historic outage overlays, F923 delivered fuel prices, same-year CEMS rates, weather-year pinning) key off it. |
| `iso` | `ERCOT` | One of the six supported ISOs. |
| `start_year` / `end_year` | `None` → 2026 / 2050 | **Omitting them is not "unset"** — it inherits 2026–2050, i.e. 25 solve-years, i.e. §2.1b-refused. |
| `weather_year` | `2024` | Tier 0. |
| `voll` | `5000.0` | $/MWh. |
<!-- verified at runtime against ScenarioConfig(); config/schedulable.py::config_horizon documents the START_YEAR/END_YEAR fallback -->

The **full resolved config** is written beside every cached result, so a run is
always reconstructible from its own output ([§6.1](#61-the-forecast-run-cache)).

### 5.3 Sweep and matrix YAML

`SweepDefinition` has **two mutually exclusive** expansion modes — setting both
raises.
<!-- src/market_sim/config/sweeps.py:29-67 -->

**Cartesian `sweep:`** — `{field: [values]}` expands to every combination:

```yaml
sweep:
  gas_price_path: [low, mid, high]
  carbon_price: [0, 25, 50]
# 3 × 3 = 9 configs
```

**Named `cases:`** — `{case_name: {field: value}}` expands to exactly one config
per case, **preserving case identity** so downstream output can label each
member:

```yaml
mode: cases
cases:
  REF: {}
  GAS-LO:
    gas_price_path: low
```

Both expand *onto* a base config. `market-sim sweep` passes **no base**, so a
cartesian sweep expands onto a bare default `ScenarioConfig` (2026–2050 — see
[§4.1](#41-the-21b-solve-window-cap--read-this-first)); `market-sim matrix`
passes the explicit `--config` base. **A `cases:` file belongs to `matrix`, not
`sweep`.**
<!-- runner.py:3989 SweepDefinition.from_yaml(args.sweep).generate() with no base; runner.py:4040 generate(base_config) -->

---

## 6. Where outputs land

### 6.1 The forecast run cache

```
results/
└── {ISO}/
    └── {cache_key}/
        ├── year_2026.parquet
        ├── year_2026_p1.parquet     # only when a commitment pass ran
        ├── …
        └── config.yaml              # the full resolved ScenarioConfig
```
<!-- results/cache.py::get_cache_path → CACHE_ROOT/iso/cache_key/year_{year}[_{pass}].parquet; _CONFIG_FILENAME; CACHE_ROOT = paths.RESULTS_ROOT = <repo>/results. Cited by symbol, not line: the line numbers in this file drifted between ce779f9 and 2026-09-05. -->

- `cache_key` is a deterministic 16-hex-char hash of the resolved config — not a
  human-readable name; `config.yaml` supplies the readability. Read the current
  default key from the code — `ScenarioConfig().cache_key()` — never from a doc:
  it moves on every declared cache-key epoch (it was `603c2498bf71d21d` when this
  manual was written and `e5ecd4105ada3e58` at the 2026-09-05 re-verification,
  advanced by the `ccs_retrofit_capex_co2_scaling` default flip). The live pin is
  recorded in `src/market_sim/results/cache.py`.
  <!-- re-derived 2026-09-05; the epoch ledger lives in results/cache.py -->
- Each parquet holds every hourly output for that ISO-year: dispatch by unit,
  zonal prices, emissions, storage SOC, curtailment, flows, slack.
- **Before solving a scenario-year the runner checks for the parquet and skips
  if present**, so runs are stop/resume capable. To force a re-solve, delete the
  year file (or change the config, which changes the key).
  <!-- results/cache.py::is_cached; runner.py per-year loop step 5 -->
- `results/{ISO}/` is **gitignored for six of the seven ISOs** — forecast caches are
  transient and reproducible from config. Only `results/calibration/` bundles are
  tracked. **`results/SPP/` has no `.gitignore` entry yet**, so an SPP forecast
  cache lands untracked-but-not-ignored until that line is added
  (`FINDING-spp-35-2026-09-07.md` §5, routed — `.gitignore` is not that lane's file).
  <!-- .gitignore lines 271-276; git check-ignore over all seven, 2026-09-07:
       ERCOT/CAISO/PJM/MISO/NYISO/NEISO ignored, SPP not -->
- `MARKET_SIM_DATA_ROOT` relocates the whole `data/` + `results/` root if you
  need the cache off the repo volume.
  <!-- config/paths.py::DATA_ROOT -->

### 6.2 Calibration (backcast) bundles

```
results/calibration/<bundle-name>/
├── meta.json                     # the recipe — every solve kwarg (what --replay-bundle reads)
├── run_config.json               # full config + git provenance + --note
├── metrics.json
├── calibration_attestation.json
├── legitimacy_diagnostics.json
└── hourly/
    ├── class_hourly_<year>.parquet
    ├── system_<year>.parquet
    ├── reserve_family_<year>.parquet
    └── storage_<year>.parquet
```

Keeper bundles additionally **commit** their `hourly/` sidecars so later
diagnostic sessions read the keeper's class-dispatch and price hourlies instead
of replaying the solve. The heavy per-unit artifacts
(`hourly/unit_hourly_*.parquet`, `network_*.parquet`, `dispatch/`, `solve.log`)
are gitignored.
<!-- CLAUDE.md [R-DASHBOARD]; the .gitignore calibration-bundle block -->

### 6.3 Ensemble and matrix output

`results/ensemble/<matrix_id>/` by default for `matrix`; `--out-dir` for the
sampler ensemble's draws/metrics/bands parquet + `ensemble_meta.json`; `--out`
for the weather-year distribution JSON.

### 6.4 The dashboards

Results live on the dashboards, not in chat. **Backcast and forecast namespaces
never cross.**

| | Run explorer | Status board |
|---|---|---|
| **Backcast** | `docs/codebase-site/backcast-runs.html` (`#iso=<ISO>&run=<id>`) | `docs/codebase-site/calibration-status.html` |
| **Forecast** | `docs/codebase-site/forecast-runs.html` | `docs/codebase-site/forecast-status.html` |
<!-- CLAUDE.md [R-DASHBOARD] -->

Registration path (backcast): `scripts/dashboard_add_run.py` → `build_manifest.py`.
A run is **not done** until its bundle and dashboard files are committed and
pushed **in the same session it was produced** (`[R-DASHBOARD]`). Retention is
top-15 per ISO across three stores that must stay in lockstep — sidecar, payload,
bundle — all governed by `dashboard_add_run.py`; verify with
`scripts/check_registry_payload_parity.py` before every dashboard push.
<!-- scripts/README.md "Dashboard retention (top-15 per ISO, all three stores)" -->

The root `backcast-results.html` is a **frozen redirect stub** — never
regenerate it. `frontend/data/backcast/{manifest,benchmark,completeness}.js` and
`docs/codebase-site/data/backcast/` are **deploy-generated**; `deploy-pages.yml`
is their single writer.

---

## 7. Operational constraints — read before your first solve

These are not style preferences. Each one has a measured failure behind it.

### 7.1 Years are sequential; invocations are parallel — `[R-PARALLEL]`

- **Within one invocation, years run sequentially. Never parallelize the year
  loop.** A single year's LP already uses several GB; concurrent year solves OOM
  on most ISOs. The year loop in `runner.py` is intentionally sequential.
- **Across invocations, run independent solves concurrently** — different ISOs or
  configs, each with its own `--out-dir`, launched as concurrent background jobs.
- **Cap separate-invocation concurrency at ~2** for per-plant multi-zone LPs.
<!-- CLAUDE.md [R-PARALLEL] -->

### 7.2 Worker defaults and caps

| CLI | `--workers` default | Explicit value |
|---|---|---|
| `market-sim sweep` | `min(2, cpu_count − 1)` | **honoured as given — not clamped** |
| `market-sim ensemble` | `min(2, cpu_count − 1)` | **honoured as given — not clamped** |
| `market-sim matrix` | 2 | **hard-capped at 2** |
<!-- pipeline/members.py::DEFAULT_MEMBER_CAP=2 and ::resolve_workers; matrix.py::MAX_CONCURRENT_CASES -->

`workers == 1` runs members in-process with no subprocess overhead — the right
choice when debugging.

### 7.3 Memory

Verified measurements, not folklore:

| Configuration | Peak RSS |
|---|---:|
| Single ERCOT per-plant solve (run188 class) | ~12.7 GB |
| PJM zone-aggregate reserve co-optimization, single year | ~13.9 GB |
| PJM zone-aggregate co-opt, tightest year of a 3-year run | ~14.5 GB |
| Two concurrent ERCOT per-plant solves on a 15 GB box | **OOM** |
<!-- docs/PRECOMMIT-ercot192-coal-limbs-2023-reapplication-2026-08-12.md §RSS; docs/multi-iso/pjm-reserve-ordc.md Phase-2 EMPIRICAL re-gate -->

Years release memory between them, so the **per-year peak** is what matters, not
a multi-year sum.

> **A widely-quoted "co-optimization OOMs above ~16 GB" claim is stale and was
> empirically falsified.** The pjm-62 memtest measured the zone-aggregate co-opt
> at ~13.9–14.5 GB, comfortably inside a 15 GB box; the earlier figure came from
> a heavier retired config. What remains plausibly memory-heavy is the **per-gen**
> `R[g] ≤ ramp10[g]` build, which is untested.
> <!-- docs/multi-iso/pjm-reserve-ordc.md — "Phase 2 re-gate, EMPIRICAL": claim #3 explicitly falsified -->

Practical guidance: budget ~16 GB for a single per-plant ERCOT solve and **do not
run a second concurrently on the same box**.

### 7.4 The §2.1b solve-window cap

See [§4.1](#41-the-21b-solve-window-cap--read-this-first). Every `market-sim`
subcommand carries it; backcast configs are exempt and gated by `[R-HOLDOUT]`
instead.

### 7.5 Holdout discipline — `[R-HOLDOUT]`

**There are three tiers, not two, and they carry separate markers** — one
declaration must never spend both.

| Tier | Years | Discipline | Marker that authorizes it |
|---|---|---|---|
| Train / calibration | 2023–2025 | The only years tuned against. Every keeper is built and scored here, all three in one bundle (`[R-ALLYEARS]`). | none needed |
| Validation holdout | 2022, laddering back to 2020 | **Iterable.** A miss may send you back to re-tune 2023–2025 and re-solve — that is its purpose. A validation number is *selection evidence*, **never** a certified out-of-sample skill number. | `complete` |
| Locked test | **2019** and **H1-2026** | **Touch-once, ever.** Scored exactly once per ISO on the frozen keeper config; the result is recorded whatever it is. No calibration change may respond to it. | `final` |

The program's working span is **2019–2025** for all ISOs; 2018 and earlier are
dropped and fail closed to locked-test tier. **No ISO has ever spent a
locked-test year.**

What is held out is the **score**, never the data or the architecture: measured
inputs are collected once and applied consistently across *all* years, and the
keeper recipe is one recipe. The only restricted act is looking at the answer —
solving, scoring or registering an out-of-training year.

`scripts/lib/holdout_policy.py` is the tier map and is **fail-closed** (a year in
no enumerated set is treated as locked test).
`run_calibration_full.py --holdout-authorized` additionally requires the ISO to
carry **that year's tier marker** — `complete` for a validation year, `final` for
a locked-test year — and a `--year` spanning both tiers needs both. The
`holdout-freeze.json` spend freeze outranks the markers for the tiers in its
scope and is checked first. Do not route around any of it.
<!-- re-verified 2026-09-05 against CLAUDE.md [R-HOLDOUT] and scripts/lib/holdout_policy.py; the pre-finalization text mislabelled 2022 as locked-test and omitted 2019 entirely -->

### 7.6 Keepers span all years — `[R-ALLYEARS]`

Every multi-year ISO's calibration run covers every scorable year in a **single
`--year` invocation and a single bundle** (CAISO / PJM / NEISO / NYISO / MISO →
`--year 2023 2024 2025`). A single-year solve is a throwaway diagnostic probe and
must **never** be registered as a keeper. The README's `--year 2024` quickstart is
a smoke test, nothing more.

### 7.7 No LP solves on CI runners

Solves are in-session, years sequential, ≤2 concurrent workers. The data-touching
CI jobs get their inputs through **sparse, blobless checkouts** rather than a full
one — the repo's tip no longer fits a standard runner's disk. See
[§9.5](#95-ci-is-red-and-it-is-not-your-change).

---

## 8. Running the tests

```bash
# Fast lane — every edit / pre-commit. Hermetic unit tests, parallel.
uv run python -m pytest -q -n auto -m "not slow and not integration and not fulldata"

# Full lane — pre-push / CI. Everything, serial.
uv run python -m pytest -q
```

- `--strict-markers` is on: a typo'd `@pytest.mark.<x>` is a hard error.
- There is **no default `-m` deselection** — a bare `pytest` runs the full suite;
  the fast lane is opted into on the command line.
- The full lane runs **serial** because the data-backed and LP tests each hold
  several GB and must not run concurrently (`[R-PARALLEL]`).
- Markers: `slow` (regenerates clean data / runs the model / builds a full-8760
  LP), `integration` (real data tree), `fulldata` (needs real `data/raw`, applied
  automatically by the `requires_raw` helper), `golden` (byte-identity or
  band-regression guard).
<!-- docs/testing.md "The two lanes" + "Marker taxonomy" -->

**The fast tier hard-requires `data/raw`.** On a data-less or partial checkout,
`data/raw`-reading tests fail *by design*; `integration`-marked tests
additionally need `data/clean` regenerated ([§3.3](#33-rebuild-dataclean--required-and-slow)).
On a **full** checkout the fast tier passes with zero expected failures — if it
is red there, that is a regression to fix, not ambient noise.

**Never fix a golden failure by regenerating the golden.** A golden FAIL is a
finding. Byte-identity keeper goldens: capture before with
`scripts/capture_keeper_goldens.py`, gate after with
`scripts/regression_gate.py --mode byte` (atol=rtol=0).

---

## 9. Troubleshooting

Seeded from the 2026-08 debug sweep's triage table and the DEBUG-B replay
finding — these are the failures that actually happened, with their measured
root causes.
<!-- docs/handoffs/debug-sweep-2026-08.md; docs/FINDING-debug-b-pjm-input-clock-2026-08-15.md §8 -->

### 9.1 `REFUSING market-sim run: 2026-2050 is 25 solve-years, over the §2.1b cap of 5`

**Working as designed.** Your config's horizon — or the 2026–2050 default it
inherited by omitting `start_year`/`end_year` — exceeds the cap. Options, in
order of preference: use a ≤5-year window; use one of the shipped instruments
(T1-F 2026–2030, T1-X 2023–2027, T1-H 2021–2025); or obtain and log an explicit
per-campaign owner authorization and pass `--full-solve-authorized`. Do not
reach for the flag first.

### 9.2 A loader raises on a fresh clone (`transfer-interface-limits`, virtual bids, …)

**`data/clean` is missing, or a licensed corpus is.** Several loaders raise
rather than silently no-op — deliberately, so a solve never quietly runs on
absent inputs. Run `scripts/regenerate_clean.py` (~2 h, [§3.3](#33-rebuild-dataclean--required-and-slow)),
and fetch any licensed corpus your recipe needs (e.g.
`pjm_da_virtual_bids` → `data/raw/pjm-da-virtuals`, [§3.2](#32-per-corpus-fetch--the-untracked-corpora)).

### 9.3 A `data/raw` file the docs mention is simply not there

**It is probably an untracked corpus payload, not a broken clone.** Check that
corpus's `README.md` for its pin sha and re-fetch command, then use either
recovery route in [§3.2](#32-per-corpus-fetch--the-untracked-corpora). Also
confirm your hydration profile actually covers it
(`scripts/hydrate_data.py --show`).

### 9.4 `test_eia_loader` zonal-share failures

**Environment, not code.** All 64 tests pass on a clean **full** checkout. The
failure mode (8 reds across CAISO/ERCOT/MISO — none NYISO) appears only on a
checkout without `data/raw/zone-specific-demand`. The README's old
"4 known-failing CAISO/NYISO cases" note was stale in *both* directions and has
been retired.
<!-- debug-sweep-2026-08.md triage row 1: 64/64 pass full-data 2026-08-14; 8 fail with the dir hidden -->

### 9.5 CI is red, and it is not your change

Three infrastructure failure signatures dominated this repo's CI. Two are now
fixed on main; recognise all three so you do not chase them.

| Symptom | Status | What it is |
|---|---|---|
| `Fast test tier` dies **inside `actions/checkout`**, pytest never invoked | **FIXED** (on main) | The tier hard-requires `data/raw`, and a full checkout of the tip (≈8.7 GiB pack + ≈9.0 GiB worktree) no longer fits a runner's 15 GB disk. PERF-A replaced it with a **measured sparse checkout** — `actions/checkout` adds `--filter=blob:none` automatically once `sparse-checkout` is set, so the job materializes only the subset the tier opens. First complete fast-tier run in the repo's history: checkout 80 s, pytest 9m03s, all green. |
| `golden-data-tier.yml` killed at `curate_emissions.py` with **exit code 143** | **FIXED** (on main) | Runner-VM SIGTERM from a ~10 GiB RSS peak, not a code fault. `curate_year()` was rewritten Arrow-side/streaming (per-file conversion, row-group-chunked writes): peak RSS **10.05 → 5.17 GiB** (2023) and **9.91 → 4.71 GiB** (2024), output verified byte-identical in the data region. The tier then ran **green** — run `31913648051`, 11m33s, loud-failure guard PASS, zero data-missing skips. |
| `ci.yml` runs show as `cancelled` | **Still true** | `ci.yml` is `pull_request`-triggered with no concurrency group; PRs merge and delete their branches before the ~7–15 min run finishes, cancelling it. Nothing is wrong with the workflow. |
<!-- ci.yml fast-tests sparse block on main @ ce779f9 (PERF-A 2026-08-15); docs/handoffs/perf-recheck-2026-08.md §1.2/§1.3/§1.5; scripts/data/curate_emissions.py streaming rewrite + plan §8 GOLDEN-TIER-FIX entry (run 31913648051); ci.yml trigger re-verified `on: pull_request` only -->

Two further jobs (`FR-22 parity`, `Forecast-invariant artifact audit`) are red
**by design** as other lanes' live signals.

> **Both data-tier failures were fixed on 2026-08-15**, hours before this manual
> was written; they are kept here because they dominated CI for weeks and the
> symptoms are still in circulation. If you hit either signature again, it is a
> regression in the sparse-checkout block or in `curate_year()`'s streaming path
> — not the old capacity problem.

### 9.6 A backcast bundle looks wrong after a fresh clone replay

Check `meta.json`'s `reuse` field. Under `--reuse-solved`, years that matched are
**byte-copies of a prior solve**, not fresh evidence. Keeper promotion requires a
full fresh solve of every year — `reuse: null`.

### 9.7 `--commitment` / `--no-coal-p2` hard-errors

P2 is **archived**. P0/P1 are the only production passes and every run is scored
on P1. If you genuinely need P2 as a last resort, pass `--enable-legacy-p2`
alongside it — but no keeper uses it and it is part of no recommended
configuration.

### 9.8 `git push` fails with HTTP 408 or 500

HTTP/2 negotiation, not pack size:

```bash
git config http.version HTTP/1.1
```

Then retry. Start from a freshly-fetched `origin/main` so the pack carries only
your own objects.

### 9.9 `run_calibration_full.py --help` exits with a `ValueError`

**Known, and it is not your environment.** `ValueError: unsupported format
character ')'` out of `argparse.format_help()` — a literal `%` in the
`--caiso-st-gas-peak-measured` help string that argparse tries to interpolate.
Only the rendered `--help` is affected; **the parser works and every documented
invocation runs**. Read the flag catalogue from the script's argparse block
until it is fixed. See [§4.6](#46-scriptsrun_calibration_fullpy--the-backcast-harness).

### 9.10 A solve is slower than expected

The cold P0 solve is **74–83 %** of a year's wallclock (ERCOT ~183–272 s/yr,
MISO ~292–339 s/yr) and the obvious solver levers — IPM+crossover, thread
scaling, HiGHS parallel/PAMI, presolve-on — are all **benched and rejected on
record**. Do not re-run them. Confirm instead that cross-year warm-start is on
(it is the default on the calibration path; `--no-xyear-warmstart` turns it off)
and that you are not accidentally running more than ~2 concurrent solves.
<!-- docs/handoffs/wallclock-baseline-2026-07.md via docs/model-audit-release-plan-2026-08.md §1 -->

---

## 10. Known doc divergences found while writing this manual

Recorded here rather than silently fixed — `docs/codebase/07-runner-and-cli.md`
is another lane's surface. Two of the three entries below are now resolved:
`model-methodology-spec.md` was finalized by DOCS-B (2026-09-05), and this
manual's own counts were re-derived in the same pass. The
`07-runner-and-cli.md` rows remain open and are re-routed to that lane's owner.

> **Why every "line N" claim below is stated as a symbol, not a number.** This
> table originally rebutted stale line numbers *with* line numbers, and by the
> 2026-09-05 re-verification every one of its own replacements had drifted too
> (`_build_parser` 3838 → 4822, `main` 3971 → 4955, `run_scenario_iso` 984 →
> 1232, the calibration parser 7954 → 8811). Line-number citations into source
> are not maintainable at this repo's rate of change; cite `module::symbol`.

**`docs/codebase/07-runner-and-cli.md`:**

| Claim | Verified state |
|---|---|
| "`_build_parser()` (runner.py:1056) defines **three** subcommands; `main()` (line 1119)" | **Four** subcommands: `run`, `sweep`, `ensemble`, `matrix`. |
| "`run_scenario_iso` (runner.py:137)" | The symbol exists; the line number does not resolve. |
| "`argparse` at line 4201" (run_calibration_full) | Same — the parser is built near the end of the script, not at 4201. |
| `sweep --workers` "default `cpu_count − 1`" | `min(2, cpu_count − 1)` — the uncapped default was an `[R-PARALLEL]` violation and was fixed. |
| Example: `market-sim sweep --sweep configs/scenario_matrix.yaml --workers 8` | Wrong twice: `scenario_matrix.yaml` is a **cases** file (belongs to `matrix` with a `--config` base; via `sweep` it expands onto a bare default config and is §2.1b-refused), and `--workers 8` defeats the `[R-PARALLEL]` default. |
| `--commitment` / `--no-coal-p2` listed as ordinary flags | Both are **archived**, hidden from `--help`, and hard-error without `--enable-legacy-p2`. |
| Example: `market-sim run --config configs/scenarios/ercot_base.yaml` | **Refused** by the §2.1b cap as written. |
| §7.2 lists no `matrix` subcommand and no `--full-solve-authorized` | Both exist on all four subcommands. |
| Stray `</content>` at end of file | Line 161. |

**`docs/testing.md`:** opens with "~355 files"; the tiered layout it documents is
correct, the count is not — and the point is proved by the count itself having
moved twice since: **447** `test_*.py` at `ce779f9`, **524** at the 2026-09-05
re-verification (**531** `.py` in total, counting helpers and `conftest`).
**Remove the hard count entirely rather than re-pinning it.** Also AUDIT-A
gap-register row D5.
<!-- re-derived 2026-09-05: find tests -name "test_*.py" | wc -l == 524; find tests -name "*.py" | wc -l == 531 -->

**`model-methodology-spec.md`:** **RESOLVED.** Audited by DOCS-A
([`handoffs/methodology-finalization-audit-2026-08.md`](handoffs/methodology-finalization-audit-2026-08.md))
and finalized by DOCS-B on 2026-09-05 — the Phase-0 build-agent content and the
never-met performance targets are gone, §5.2 is restructured around
`retirement_rule`, and every rule citation carries a stable `[R-*]` ID.

---

## Further reading

- [`../README.md`](../README.md) — elevator pitch + quickstart.
- [`../model-methodology-spec.md`](../model-methodology-spec.md) — the methodology (LP formulation, pricing, capacity evolution).
- [`codebase/README.md`](codebase/README.md) — the code-derived engineering reference.
- [`fast-clone.md`](fast-clone.md) — clone/hydration mechanics in full.
- [`testing.md`](testing.md) — test layout, markers, golden systems.
- [`calibration-report.md`](calibration-report.md) — dashboard registration.
- [`../CLAUDE.md`](../CLAUDE.md) — the governance rules (`[R-*]` IDs).
- [`../scripts/README.md`](../scripts/README.md) — what lives where under `scripts/`.
