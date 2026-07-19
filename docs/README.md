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
  it **follows the code** where code and prose diverge.
- **L2 — living per-area references.** Standing methodology and reference docs that
  are maintained, not frozen. Indexed one-row-each below.
- **L3 — dated records.** Point-in-time diagnoses, findings, decision memos, plans,
  and session notes. These are the evidence base: cited, never rewritten. They are
  **not** indexed row-per-file here (there are ~300 of them); they are reached
  through their own class indexes — [`handoffs/README.md`](handoffs/README.md) and
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
| [`../model-methodology-spec.md`](../model-methodology-spec.md) | ACTIVE | Spec — market design, LP formulation, capacity evolution (THE spec) |
| [`../market-sim-build-plan.md`](../market-sim-build-plan.md) | ACTIVE | Spec — phase plan, extraction manifest, directory structure |
| [`codebase/README.md`](codebase/README.md) | ACTIVE | Engineering reference — index of the 8 code-derived pages |

## L2 — living per-area references

One row per living doc: **path · status · area · superseded-by**. (Programs/plans
that are actively driving work are ACTIVE and live here; the dated evidence they
produced is L3.)

| Path | Status | Area | Superseded-by |
|---|---|---|---|
| [`calibration-and-validation-methodology.md`](calibration-and-validation-methodology.md) | ACTIVE | Calibration | — |
| [`calibration-determination-rubric.md`](calibration-determination-rubric.md) | ACTIVE | Calibration — the keeper rubric (v2.x) | — |
| [`forecast-determination-rubric.md`](forecast-determination-rubric.md) | ACTIVE | Forecast — the forecast (FR) rubric | — |
| [`reference-price-interface.md`](reference-price-interface.md) | ACTIVE | Calibration — reference-price/scoring interface | — |
| [`verifying-dashboard-numbers.md`](verifying-dashboard-numbers.md) | ACTIVE | Calibration — dashboard/number verification | — |
| [`calibration-report.md`](calibration-report.md) | ACTIVE | Calibration — dashboard registration guide | — |
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
| [`multi-iso/README.md`](multi-iso/README.md) | ACTIVE | Multi-ISO — protocol & reference index (six ISOs) | — |
| [`forecast-development-plan-2026-07.md`](forecast-development-plan-2026-07.md) | ACTIVE | Forecast — THE forecast program (tiers, lanes, waves, §9 doc ledger) | — |
| [`refactor-consolidation-plan-2026-07.md`](refactor-consolidation-plan-2026-07.md) | ACTIVE | Governance/refactor — consolidation program charter | — |
| [`refactor-consolidation-prompt-pack-2026-07.md`](refactor-consolidation-prompt-pack-2026-07.md) | ACTIVE | Governance/refactor — companion prompt pack | — |
| [`gap-register-2026-07.md`](gap-register-2026-07.md) | ACTIVE | Forecast — live gap register | — |
| [`data-register-2026-07.md`](data-register-2026-07.md) | ACTIVE | Data — live data register | — |
| [`holdout-data-equivalency-register-2026-07.md`](holdout-data-equivalency-register-2026-07.md) | ACTIVE | Governance — holdout/equivalency register | — |
| [`out-of-sample-results-2026-07.md`](out-of-sample-results-2026-07.md) | ACTIVE | Calibration — locked-test/out-of-sample results (touch-once) | — |
| [`forecasting-entry-exit-assessment.md`](forecasting-entry-exit-assessment.md) | ACTIVE | Forecast — entry/exit verdict (updated by FF-2C/FF-4B) | — |
| [`forecast-invariant-findings.md`](forecast-invariant-findings.md) | ACTIVE | Forecast — invariant findings (validation base) | — |
| [`model-legitimacy-audit-2026-07.md`](model-legitimacy-audit-2026-07.md) | ACTIVE | Governance — audit that CLAUDE.md rules 17–26 derive from | — |
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

**Pending moves (row will need updating).** The `phase-refactor/stale-refs-docs`
session had **not** landed when this index was written, so the following are still at
`docs/` root and are indexed here against the *current* tree. When that session
lands, they move to [`sessions/`](sessions/) and these rows must be updated:

- the 8 staging files — `_caiso79_*`, `_caiso80_log_entry.md`, `_caiso81*_log_entry.md`,
  `_pjm112_input_clock_log_entry.md`, `_pjm_phase_drift_log_entry.md`,
  `_rubric25_log_entry.md`, and the two `_caiso79_*.patch.xz.b64` payloads;
- executed one-shot session prompts (`*-session-prompt.md`).

## L3 — dated records (reached by class, not row-indexed)

L3 is the bulk of `docs/` and is **not** individually indexed here. Reach it by:

| Class | Where | Index |
|---|---|---|
| Handoffs, design specs, decision memos, plans | [`handoffs/`](handoffs/) (~171 docs) | [`handoffs/README.md`](handoffs/README.md) |
| Frozen session/investigation notes | [`sessions/`](sessions/) (+ `sessions/multi-iso/`) | [`sessions/README.md`](sessions/README.md) |
| Hindcast run reports | [`hindcast-reports/`](hindcast-reports/) | — (filename = ISO-years-mode-date) |
| Root-level dated diagnoses | `docs/DIAGNOSIS-*.md` (15) | — (filename = ISO-topic-date) |
| Root-level dated findings | `docs/FINDING-*.md` (6) | — (filename = ISO-topic-date) |
| Per-ISO dated investigation notes | `docs/{ercot,caiso,pjm,miso,nyiso,neiso}-*-2026-0{6,7}.md` | — |
| Audits / peer reviews / prompt packs | `docs/*-audit-*.md`, `docs/*peer-review*.md`, `docs/*-prompt-pack-*.md` | — |

Most root-level `docs/*.md` files with a `-2026-06`/`-2026-07` date suffix are L3
records of this kind; when in doubt, open the doc — its own header (or, for newer
docs, its status banner) is authoritative over this index.

## Further reading (newcomer path)

1. [`../README.md`](../README.md) — repo README / quickstart.
2. [`../model-methodology-spec.md`](../model-methodology-spec.md) — the spec.
3. [`codebase/README.md`](codebase/README.md) — how the code is actually built.
4. [`multi-iso/README.md`](multi-iso/README.md) — the six-ISO topology & protocol.
5. [`calibration-determination-rubric.md`](calibration-determination-rubric.md) /
   [`forecast-determination-rubric.md`](forecast-determination-rubric.md) — how a run
   is judged.
6. The dashboard — `docs/codebase-site/backcast-runs.html` (run explorer) and
   `calibration-status.html` (keeper summary) — for live results.

---

*Index built 2026-07-19 against `claude/docs-index-layer-sdjsr0`. L2 statuses use
in-file banners and the `forecast-development-plan-2026-07.md` §9 ledger; ambiguous
plans are classified best-effort. The status-header convention above makes future
docs self-describing so this index stays thin.*
