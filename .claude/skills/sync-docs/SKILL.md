---
name: sync-docs
description: Reconcile the prose documentation with the code AFTER a session has settled on a final approach. Manually invoked at the end of a working session (never as a hook) — it diffs what changed, maps each change to the docs that describe it, verifies the new behaviour against source, and proposes reviewed doc edits plus a CHANGELOG entry. Use when the user says "sync the docs", "update the docs to match the code", "the approach is settled, document it", or at end-of-session wrap-up.
---

# Sync docs to settled code

A **manually-invoked** documentation reconciler. It is the deliberate,
end-of-session counterpart to a hook: you run it **only when you have settled
on the approach**, so mid-session experimentation carries zero documentation
overhead and never gets caught in write→re-run loops. It never blocks a task,
never fires automatically, and never runs the model.

**Golden rule:** code is the source of truth. This skill changes prose to
match code — it does **not** change code, `config/`, or data to match prose.
If the docs describe a *better* design than the code, surface that as a note
for the user; do not edit code here.

## When to use / not use

- **Use** at the end of a session once the code change is final and you want
  the docs to reflect it; or when the user explicitly asks to align docs.
- **Do not use** mid-experiment, on a dirty exploratory tree the user is still
  tweaking, or to document an intended-but-unbuilt feature (capture those as
  roadmap notes, not as current methodology — see Step 5).

## Inputs

Scope the run to what actually changed this session. In order of preference:

1. An explicit base the user names ("since I branched", "this PR").
2. The session's starting commit, if known.
3. `git diff main...HEAD` (committed work on the branch), plus
   `git diff` / `git status` for uncommitted working-tree changes.

```bash
git status --short
git diff --stat main...HEAD        # committed on this branch
git diff --stat                    # unstaged working tree
```

If the diff is empty or the user hasn't settled, stop and say so — there is
nothing to sync.

## Step-by-step

### 1. Determine the changed code surface
List the changed files under `src/market_sim/`, `config/`, `scripts/`,
`data/`. Group them by subsystem (dispatch, commitment, capacity, fleet/
binning, outages, fuel, emissions/policy, transmission, storage, calibration,
config/ISO topology, pipeline/solve-core, results schema, frontend).

### 2. Map each changed subsystem to its docs
Use the **code→doc map** below to find every doc that makes claims about the
changed subsystem. A single code change often touches several docs (e.g. a new
ISO topology hits `CLAUDE.md`, the methodology spec, and `docs/multi-iso/`).

### 3. Verify the *current* behaviour against source — do not trust memory
For each candidate doc claim, read the actual code (the function, the constant,
the config default) and confirm what it does **now**. Lesson learned: a prior
review wrongly "remembered" hydrogen fuel cost as gas-derived when
`data/hydrogen.py` clearly derives it from `min(wind_lcoe, solar_lcoe) /
electrolyzer_efficiency`. Quote `file:line` in the proposed edit so the user
can check. Pay special attention to:
- **Defaults that flip behaviour** (`use_campd_bins`, `commitment_enabled`,
  `outage_source`) — the *default* is what the doc should describe as the
  primary path; alternatives are "opt-in".
- **Forecast vs backcast** paths — this is a forecasting model; historic-data
  overlays (CAMPD outages, F923 fuel, plant-specific emissions, weather-year
  pinning) are **calibration/backcast** devices. Never document a backcast-only
  mechanism as the forecast methodology.
- **Numbers** (thresholds, multipliers, caps) — read them from `constants.py`/
  `scenarios.py`, don't paraphrase from the old doc.

### 4. Propose the edits, then apply on confirmation
Present a concise, per-file list of proposed changes (old claim → corrected
claim, with the `file:line` evidence). Apply with `Edit` after the user
confirms. Keep each doc's voice and structure; prefer surgical edits to
rewrites so the diff is reviewable. Preserve still-accurate content.

### 5. Separate "settled" from "roadmap"
Anything discussed but **not yet built** goes into a clearly-labelled roadmap/
"intended direction" note (in the relevant doc or `market-sim-build-plan.md`),
never into the methodology-as-built. Ask the user if unsure which bucket a
change belongs in.

### 6. Record it in the changelog
Append a dated `CHANGELOG.md` entry summarizing the settled change in one or
two lines (what changed in the model + which docs were realigned). This is the
durable session record.

### 7. Report
Summarize: files changed, the headline methodology deltas, and any roadmap
items parked for later. Do not commit/push unless the user asks.

## Code → doc map

| Code area | Docs that describe it |
|---|---|
| `model/dispatch.py` (LP vars, objective, constraints, duals=price) | `model-methodology-spec.md` §1–2; `CLAUDE.md` (Objective / Key Constraints) |
| `model/commitment.py` (P0/P1/P2, startup amortization, screens) | `model-methodology-spec.md` (Unit-commitment section) & §7.2; `docs/calibration-log.md`, `docs/calibration-session-log.md` |
| `model/capacity.py` (retire / new entry / CCS retrofit) | `model-methodology-spec.md` §5; `CLAUDE.md` (Capacity Evolution) |
| `model/transmission.py`, `config/iso_configs.py` (topology/TTC) | `model-methodology-spec.md` Scope & §1.3; `CLAUDE.md` (What This Is); `docs/multi-iso/00…`, `04…` |
| `model/storage.py` | `model-methodology-spec.md` §1.3, §1.5.5, §5.5; `CLAUDE.md` |
| `data/fleet.py`, `data/raw/reference/custom-bin-assignments.csv` (CAMPD bins, tranches, offer curves) | `docs/binning-methodology.md`; `model-methodology-spec.md` (Fleet representation); `CLAUDE.md` |
| `data/outages.py` (backcast overlay) + `data/fleet.py` seasonal POF/WEFOR (forecast) | `model-methodology-spec.md` (Outage modelling) & §7.2; `results/calibration/SUMMARY-outage-overlay.md` |
| `data/fuel.py`, `data/eia923.py`, `data/hydrogen.py` | `model-methodology-spec.md` §1.5.1; `docs/parameter-citations.md`; `docs/binning-methodology.md` (fuel pricing) |
| `results/emissions.py`, `policy/carbon.py`, `policy/rps.py`, `policy/ira.py`, `policy/eac.py` | `model-methodology-spec.md` §1.4, §1.5, §5.3 |
| `config/scenarios.py` (`ScenarioConfig`), `config/constants.py` | `model-methodology-spec.md` §4; `docs/parameter-citations.md`; `docs/thermal-cycling-adders.md` |
| `results/calibration.py`, `scripts/run_calibration*.py` | `docs/calibration-log.md`, `docs/calibration-session-log.md`, `docs/calibration-report.md`, `docs/calibration-best-so-far.md`, `results/calibration/SUMMARY-*.md` |
| `results/cache.py`, `results/export.py`, `results/outputs.py` | `docs/data-dictionary.md` |
| `data/ownership.py`, `data/ownership_config.py` | `us-gen-ownership.md` |
| `frontend/`, `*.html` (color palettes) | `docs/DESIGN_SYSTEM.md` |
| `pipeline/*.py` (spec, kwargs, prior, result, backcast_config, commitment, solve — shared per-year solve core) | `model-methodology-spec.md` §5.1; `CLAUDE.md` (Architecture; Dispatch & Commitment) |
| `scripts/legitimacy_diagnostics.py` (D-1/D-2/D-4 legitimacy diagnostics + gates) | `docs/calibration-determination-rubric.md`; `docs/forecast-determination-rubric.md`; `docs/model-legitimacy-audit-2026-07.md`; `CLAUDE.md` (rules 17–26) |
| `scripts/` layout & standing tooling (keeper-rotation rule) | `scripts/README.md` |
| the forecast program (tier ladder, lanes/waves, entry/exit) | `docs/forecast-development-plan-2026-07.md`; `docs/forecast-determination-rubric.md` |
| the codebase-site / dashboard (`docs/codebase-site/*.html`) | `docs/codebase-site/PLAN.md`, `docs/codebase-site/UPDATE-PLAN-2026-07.md`; `docs/verifying-dashboard-numbers.md` (generated at deploy — `.github/workflows/deploy-pages.yml`) |
| any `src/market_sim/` subsystem — "what does the code do here?" | `docs/codebase/` (code-derived engineering pages + `codebase/README.md`) |
| repo-wide conventions (naming, layout, workflow) | `CONVENTIONS.md`; `CLAUDE.md`; docs IA index `docs/README.md` |
| anything | `CHANGELOG.md` (always append), `README.md` (only if the elevator pitch changed) |

Keep this map current: when a new doc or major module is added, add the row
here as part of the same sync.

## Guardrails

- **Read-only on code.** This skill edits Markdown only. If a doc/code
  mismatch is actually a code bug, report it — don't "fix" it by editing prose.
- **No model runs.** Documentation reconciliation never solves the LP or
  regenerates results (that's `/calibration-report`'s job).
- **Reviewable diffs.** Surgical edits over wholesale rewrites; preserve voice
  and still-true content.
- **Date-stamped snapshots stay put.** Run-specific files
  (`calibration-best-so-far.md`, `SUMMARY-*.md`) are point-in-time records —
  don't rewrite history; if they're stale-as-current, add a dated banner
  instead.
