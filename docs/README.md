> Status: ACTIVE — the docs index (layer L0).

# docs — index & information architecture

Entry point to the market-sim documentation. Docs are organized in **four layers**,
from the single front door down to dated records. Start at the top and descend only
as far as your question needs.

```
L0  docs/README.md ................ this index (you are here)
L1  model-methodology-spec.md ..... THE spec (economic/market design, LP formulation)
    docs/codebase/ ............... code-derived engineering reference (what the code does)
L2  living per-area references .... standing methodology/reference docs (table below)
L3  dated records ................. diagnoses, findings, memos, handoffs, sessions
```

- **L0 (this file)** — where everything hangs off. One row per *living* doc below.
- **L1 — the two canonical references.** [`../model-methodology-spec.md`](../model-methodology-spec.md)
  is the market-design/economics spec (the authority when methodology is ambiguous;
  CLAUDE.md: "the spec wins"). [`codebase/`](codebase/) is the code-derived
  engineering reference — 8 pages + [`codebase/README.md`](codebase/README.md) — and
  it **follows the code** where code and prose diverge. (Known stale:
  `codebase/07-runner-and-cli.md`, enumerated in
  [`user-manual.md` §10](user-manual.md#10-known-doc-divergences-found-while-writing-this-manual)
  — another lane's surface.)
- **L2 — living per-area references.** Standing methodology and reference docs that
  are maintained, not frozen. Indexed one-row-each below.
- **L3 — dated records.** Point-in-time diagnoses, findings, decision memos, plans,
  and session notes. These are the evidence base: cited, never rewritten. They are
  **not** indexed row-per-file here — there are **well over a thousand**
  (1,265 `.md` files under `docs/` at 2026-09-05, of which the L1/L2 living set
  indexed on this page is under 60). They are reached through their own class
  indexes — [`handoffs/README.md`](handoffs/README.md) and
  [`sessions/README.md`](sessions/README.md) — and by filename convention (below).

## Status-header convention (standing rule for new docs)

Every **new** doc gets a status banner as its first line, so its lifecycle is
legible without opening it:

```
> Status: ACTIVE | RECORD (frozen <date>) | SUPERSEDED-BY <path> | ARCHIVED
```

- **ACTIVE** — living reference or in-flight plan; keep current.
- **RECORD (frozen `<date>`)** — a point-in-time record (diagnosis, finding, memo,
  handoff, session note). Frozen at the date; cited, not edited.
- **SUPERSEDED-BY `<path>`** — replaced; the pointer names the successor. Kept for
  history; do not act on it.
- **ARCHIVED** — executed/retired; content may remain citable but the doc drives
  nothing.

Most existing L3 docs predate this convention and carry no banner — treat an
un-bannered dated doc as `RECORD`. Adding banners to the backlog is a separate
docs-governance task (refactor plan §7-G), not this index's job.

## L1 — canonical references

| Path | Status | Area |
|---|---|---|
| [`../model-methodology-spec.md`](../model-methodology-spec.md) | **FINALIZED 2026-09-05** | Spec — market design, LP formulation, capacity evolution (THE spec). Describes the shipped model; no build-agent content, no performance targets, rules cited by `[R-*]` ID only |
| [`../market-sim-build-plan.md`](../market-sim-build-plan.md) | ACTIVE — **disposition is an open owner question** | Phase plan, extraction manifest, directory structure. This is Phase-0 build-plan content; whether it should survive alongside a finalized methodology spec was raised by the DOCS-A audit (§10) and is not a docs lane's call |
| [`codebase/README.md`](codebase/README.md) | ACTIVE | Engineering reference — index of the 8 code-derived pages |

## L2 — living per-area references

One row per living doc: **path · status · area · superseded-by**. (Programs/plans
that are actively driving work are ACTIVE and live here; the dated evidence they
produced is L3.)

| Path | Status | Area | Superseded-by |
|---|---|---|---|
| [`user-manual.md`](user-manual.md) | ACTIVE | Operations — THE user manual: install, data setup (hydrate + per-corpus fetch + `data/clean`), CLI reference (`market-sim run/sweep/ensemble/matrix` + the two calibration CLIs), configs, outputs, operational constraints, troubleshooting | — |
| [`calibration-and-validation-methodology.md`](calibration-and-validation-methodology.md) | ACTIVE | Calibration | — |
| [`calibration-determination-rubric.md`](calibration-determination-rubric.md) | ACTIVE | Calibration — the keeper rubric (v2.x) | — |
| [`forecast-determination-rubric.md`](forecast-determination-rubric.md) | ACTIVE | Forecast — the forecast (FR) rubric | — |
| [`reference-price-interface.md`](reference-price-interface.md) | ACTIVE | Calibration — reference-price/scoring interface | — |
| [`verifying-dashboard-numbers.md`](verifying-dashboard-numbers.md) | ACTIVE | Calibration — dashboard/number verification | — |
| [`calibration-report.md`](calibration-report.md) | ACTIVE | Calibration — dashboard registration guide | — |
| [`backcast-artifact-contract.md`](backcast-artifact-contract.md) | ACTIVE | Calibration — bundle/registry/payload/bench/dashboard schema (field tables, the three byte codecs, FROZEN list) | — |
| [`binning-methodology.md`](binning-methodology.md) | ACTIVE | Dispatch/fleet — CAMPD per-plant binning & tranche offer curves | — |
| [`offer-curve-methodology.md`](offer-curve-methodology.md) | ACTIVE | Dispatch/offer — offer-curve construction | — |
| [`thermal-cycling-adders.md`](thermal-cycling-adders.md) | ACTIVE | Dispatch — cycling/startup adders | — |
| [`ordc-overlay.md`](ordc-overlay.md) | ACTIVE | Overlays — ERCOT ORDC scarcity | — |
| [`nyiso-rcpf-overlay.md`](nyiso-rcpf-overlay.md) | ACTIVE | Overlays — NYISO RCPF scarcity | — |
| [`capacity-deliverability-wiring.md`](capacity-deliverability-wiring.md) | ACTIVE | Capacity — locational deliverability gate | — |
| [`cod-vintage-ramp.md`](cod-vintage-ramp.md) | ACTIVE | Capacity — COD vintage ramp | — |
| [`probabilistic-emissions-methodology.md`](probabilistic-emissions-methodology.md) | ACTIVE | Emissions — probabilistic emissions | — |
| [`storage-dispatch-data-sources.md`](storage-dispatch-data-sources.md) | ACTIVE | Storage — dispatch data sources | — |
| [`parameter-citations.md`](parameter-citations.md) | ACTIVE | Data provenance — every numeric input traced to a primary source | — |
| [`data-dictionary.md`](data-dictionary.md) | ACTIVE | Data — the on-disk data contract | — |
| [`data-licensing.md`](data-licensing.md) | ACTIVE | Data — source licensing | — |
| [`adding-new-data-types.md`](adding-new-data-types.md) | ACTIVE | Data — how to intake a new datatype | — |
| [`us-gen-ownership.md`](us-gen-ownership.md) | ACTIVE | Data/ownership — US generation ownership (moved from repo root, PR #2551) | — |
| [`multi-iso/README.md`](multi-iso/README.md) | ACTIVE | Multi-ISO — protocol & reference index (nine registered regions) | — |
| [`multi-iso/spp-addition-plan-2026-09.md`](multi-iso/spp-addition-plan-2026-09.md) | ACTIVE | Multi-ISO — the SPP addition program: cards, waves, lane table, manifest, gates, prompt pack; desk handoff [`handoffs/spp-desk-handoff-2026-09-06.md`](handoffs/spp-desk-handoff-2026-09-06.md), ledger [`handoffs/spp-desk-ledger-2026-09.md`](handoffs/spp-desk-ledger-2026-09.md) | — |
| [`forecast-development-plan-2026-07.md`](forecast-development-plan-2026-07.md) | ACTIVE | Forecast — THE forecast program (tiers, lanes, waves, §9 doc ledger) | — |
| [`handoffs/forecast-scenario-readiness-plan-2026-09.md`](handoffs/forecast-scenario-readiness-plan-2026-09.md) | ACTIVE | Forecast — scenario-readiness lane plan (carbon price, national CES, voluntary clean demand, load growth, system-wide emissions); subordinate to the FF plan | — |
| [`refactor-consolidation-plan-2026-07.md`](refactor-consolidation-plan-2026-07.md) | ACTIVE | Governance/refactor — consolidation program charter | — |
| [`refactor-consolidation-prompt-pack-2026-07.md`](refactor-consolidation-prompt-pack-2026-07.md) | ACTIVE | Governance/refactor — companion prompt pack | — |
| [`gap-register-2026-07.md`](gap-register-2026-07.md) | ACTIVE | Forecast — live gap register | — |
| [`data-register-2026-07.md`](data-register-2026-07.md) | ACTIVE | Data — live data register | — |
| [`holdout-data-equivalency-register-2026-07.md`](holdout-data-equivalency-register-2026-07.md) | ACTIVE | Governance — holdout/equivalency register | — |
| [`out-of-sample-results-2026-07.md`](out-of-sample-results-2026-07.md) | ACTIVE | Calibration — locked-test/out-of-sample results (touch-once) | — |
| [`forecasting-entry-exit-assessment.md`](forecasting-entry-exit-assessment.md) | ACTIVE | Forecast — entry/exit verdict (updated by FF-2C/FF-4B) | — |
| [`forecast-invariant-findings.md`](forecast-invariant-findings.md) | ACTIVE | Forecast — invariant findings (validation base) | — |
| [`model-legitimacy-audit-2026-07.md`](model-legitimacy-audit-2026-07.md) | ACTIVE | Governance — audit that CLAUDE.md rules 17–26 derive from | — |
| [`mechanism-testing-matrix.md`](mechanism-testing-matrix.md) | ACTIVE | Governance/calibration — cross-ISO mechanism testing matrix: protocol, ISO-similarity analysis, per-ISO lever queues (rule 28; canonical data sharded per ISO since 2026-08-11: base `codebase-site/data/mechanism-matrix.js` + per-ISO `codebase-site/data/mechanism-matrix/<ISO>.js`, rendered at the Mechanism Matrix page) | — |
| [`forecast-validation-plan.md`](forecast-validation-plan.md) | SUPERSEDED | Forecast | [`forecast-development-plan-2026-07.md`](forecast-development-plan-2026-07.md) |
| [`forecast-methodology-gaps-2026-06.md`](forecast-methodology-gaps-2026-06.md) | SUPERSEDED | Forecast | [`gap-register-2026-07.md`](gap-register-2026-07.md) |
| [`forecast-methodology-gaps-prompts-2026-06.md`](forecast-methodology-gaps-prompts-2026-06.md) | SUPERSEDED | Forecast (STALE — do not execute) | [`forecast-development-plan-2026-07.md`](forecast-development-plan-2026-07.md) |
| [`code-docs-cleanup-plan.md`](code-docs-cleanup-plan.md) | SUPERSEDED | Governance/refactor | [`refactor-consolidation-plan-2026-07.md`](refactor-consolidation-plan-2026-07.md) |
| [`data-reorg-plan.md`](data-reorg-plan.md) | ARCHIVED | Data — executed (data/raw + data/clean split shipped) | — |
| [`iso-model-unification-plan.md`](iso-model-unification-plan.md) | ARCHIVED | Multi-ISO — largely executed (self-status'd, phases 0–2 + Phase-4 halves) | — |
| [`calibration-best-so-far.md`](calibration-best-so-far.md) | SUPERSEDED | Calibration — stale keeper snapshot (ERCOT) | `frontend/data/backcast/keepers.json` + dashboard |
| [`calibration-best-so-far-pjm.md`](calibration-best-so-far-pjm.md) | SUPERSEDED | Calibration — stale keeper snapshot (PJM) | `frontend/data/backcast/keepers.json` + dashboard |
| [`calibration-best-so-far-nyiso.md`](calibration-best-so-far-nyiso.md) | SUPERSEDED | Calibration — stale keeper snapshot (NYISO) | `frontend/data/backcast/keepers.json` + dashboard |
| [`calibration-best-so-far-neiso.md`](calibration-best-so-far-neiso.md) | SUPERSEDED | Calibration — stale keeper snapshot (NEISO) | `frontend/data/backcast/keepers.json` + dashboard |

> The four `calibration-best-so-far*` snapshots are **not** keeper truth. Keeper
> status lives in `frontend/data/backcast/keepers.json` and the dashboard
> (`docs/codebase-site/calibration-status.html`); treat the snapshots as history.

Living log/reference docs also tracked outside this table (frequently appended, not
row-indexed to avoid churn): [`calibration-log.md`](calibration-log.md),
[`calibration-session-log.md`](calibration-session-log.md), and the repo-root
[`../CHANGELOG.md`](../CHANGELOG.md).

## Moved

Relocations already merged into the tree. Update these rows (and add new ones) as
the refactor-consolidation moves land.

| Was | Now | By |
|---|---|---|
| `us-gen-ownership.md` (repo root) | [`us-gen-ownership.md`](us-gen-ownership.md) | root-cleanup PR #2551 (merged) |
| `docs/multi-iso/` — 27 executed session/investigation notes | [`sessions/multi-iso/`](sessions/multi-iso/) | 2026-07 docs reorg (see [`handoffs/multi-iso-triage-2026-07.md`](handoffs/multi-iso-triage-2026-07.md)) |
| the 8 merged `docs/_*_log_entry.md` staging files + the two `_caiso79_*.patch.xz.b64` payloads | [`sessions/`](sessions/) | `phase-refactor/stale-refs-docs` (this session) |
| the 5 executed one-shot `docs/*-session-prompt.md` prompts (now banner'd `RECORD`) | [`sessions/`](sessions/) | `phase-refactor/stale-refs-docs` (this session) |
| `src/market_sim/pipeline/stage7_getattr_extraction_design.md` | [`handoffs/stage7_getattr_extraction_design.md`](handoffs/stage7_getattr_extraction_design.md) | `phase-refactor/stale-refs-docs` (this session) |

The `phase-refactor/stale-refs-docs` moves listed above have **landed** — the
docs-index author's earlier "pending moves" note is now resolved: the staging
files and executed session prompts are in [`sessions/`](sessions/) and the
stage-7 design doc is in [`handoffs/`](handoffs/).

## L3 — dated records (reached by class, not row-indexed)

L3 is the bulk of `docs/` and is **not** individually indexed here. Reach it by:

| Class | Where | Index |
|---|---|---|
| Handoffs, design specs, decision memos, plans | [`handoffs/`](handoffs/) (**489** top-level docs + 4 in 3 per-lane subdirectories) | [`handoffs/README.md`](handoffs/README.md) — regenerated 2026-09-05 |
| Frozen session/investigation notes | [`sessions/`](sessions/) (+ `sessions/multi-iso/`) — **41** | [`sessions/README.md`](sessions/README.md) |
| Hindcast run reports | [`hindcast-reports/`](hindcast-reports/) — **48** | — (filename = ISO-years-mode-date) |
| Root-level dated diagnoses | `docs/DIAGNOSIS-*.md` (**45**) | — (filename = ISO-topic-date) |
| Root-level dated findings | `docs/FINDING-*.md` (**171**) | — (filename = ISO-topic-date) |
| Per-ISO dated investigation notes | `docs/{ercot,caiso,pjm,miso,nyiso,neiso}-*-2026-*.md` | — |
| Audits / peer reviews / prompt packs | `docs/*-audit-*.md`, `docs/*peer-review*.md`, `docs/*-prompt-pack-*.md` | — |

Most root-level `docs/*.md` files carry a date suffix and are L3 records of this
kind — **419 of the 466** top-level files at 2026-09-05. When in doubt, open the
doc: its own header (or, for newer docs, its status banner) is authoritative over
this index.

> **These counts are a dated snapshot and they move fast.** The handoffs index
> sat at 172 rows against 489 files for seven weeks before the 2026-09-05
> regeneration. Re-derive rather than trust a number here; the class *locations*
> and the filename conventions are what this page is for.

## Further reading (newcomer path)

1. [`../README.md`](../README.md) — repo README / quickstart.
2. [`../model-methodology-spec.md`](../model-methodology-spec.md) — the spec.
3. [`codebase/README.md`](codebase/README.md) — how the code is actually built.
4. [`multi-iso/README.md`](multi-iso/README.md) — the region topology & protocol.
5. [`calibration-determination-rubric.md`](calibration-determination-rubric.md) /
   [`forecast-determination-rubric.md`](forecast-determination-rubric.md) — how a run
   is judged.
6. The dashboard — `docs/codebase-site/backcast-runs.html` (run explorer) and
   `calibration-status.html` (keeper summary) — for live results.

---

*Index built 2026-07-19 against `claude/docs-index-layer-sdjsr0`; L3 class counts
and the `handoffs/` index re-derived 2026-09-05 by DOCS-B (model-audit WS4). L2
statuses use in-file banners and the `forecast-development-plan-2026-07.md` §9
ledger; ambiguous plans are classified best-effort. The status-header convention
above makes future docs self-describing so this index stays thin.*
