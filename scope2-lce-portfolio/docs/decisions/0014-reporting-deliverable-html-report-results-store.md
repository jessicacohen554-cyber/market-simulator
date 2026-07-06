# 0014 — Reporting deliverable: self-contained HTML run report + committed results store

- **Status:** accepted
- **Date:** 2026-07-02
- **Session:** PS-11 (planning-session doc removed at handoff cleanup; in git history)
- **Implemented by:** PP-09

## Context

The tool's outputs today (PP-06) are machine artifacts: per-ISO Parquet
frontier + build-mix tables, a run-metadata JSON, and a plain-text CLI summary.
There is no consolidated human-readable report, so results get narrated in chat
instead of handed over as a document. Every metric a report needs is already
computed per solve (`outputs.py`, `PortfolioResult` — including the hourly
gen/storage/grid arrays), so this is purely a presentation + persistence
decision. The parent repo's proven pattern is the backcast dashboard: static
HTML with committed per-run JSON payloads. The stakeholder additionally plans a
**desktop port** that must read prior results from the repo, which constrains
where results live.

## Options considered

1. **Self-contained static HTML report per run** (chosen) — one file, inline
   JS/CSS/data, opens from disk, interactive charts, shareable as-is; mirrors
   the repo's dashboard idiom at run granularity. Con: renderer code to build.
2. **Markdown report** — diff-friendly, GitHub-viewable; but charts are static
   images and interactivity/multi-view layout is clumsy.
3. **CSV/Excel workbook** — best for downstream analyst manipulation, no
   visualization; the Parquet tables already serve this need.
4. **Page in the existing `frontend/` dashboard** — full registry plumbing and
   publish workflow like calibration; heavier than a per-run tool warrants now,
   and couples the standalone tool to the market-sim frontend (tension with
   ADR 0001 isolation).

Persistence options: gitignored per-run outputs (recommended default), a
committed dashboard registry, or a hybrid. **Stakeholder chose committed**:
"This will be ported onto a desktop so results should be committed into a
results parquet folder from which they can be read."

## Decision

### §1 Primary artifact

Each run produces **one self-contained static HTML report**,
`results/<run_id>/report.html`. Fully offline: all JS, CSS, and data inline —
no CDN, no server, no external fetch. It renders exclusively from the report
payload (§3); it never re-reads Parquet at view time.

### §2 Report content

Required views, in order:

- **§2.1 Provenance header** — run id, ISO(s), mode, tool version, config
  echo (from run-metadata), per-setpoint solver status. Any non-`optimal`
  setpoint is flagged inline, not hidden.
- **§2.2 Frontier chart** — matching % vs premium $/MWh across setpoints
  (both modes; axis roles follow `mode`). Hover shows the full frontier row
  (premium $/yr, %-over-BAU, shadow price).
- **§2.3 Build-mix by setpoint** — stacked bars of build MW per resource per
  setpoint; split-storage techs (ADR 0006) additionally report selected energy
  MWh alongside power MW.
- **§2.4 Cost breakdown by setpoint** — capital+VOM cost, grid purchase cost
  (BAU − avoided), surplus revenue (netting per ADR 0005), net cost vs BAU
  cost, premium $/yr. Sign convention: revenues negative in the stack.
- **§2.5 Residual-CO₂ view** — residual tCO₂/yr (ADR 0013) vs setpoint,
  plotted with matching %; omitted (like the CLI summary) when the emission
  rate was off for the whole sweep.
- **§2.6 Multi-ISO comparison table** — when the run covers >1 ISO
  (`--all-isos`): matching % and premium at each common setpoint per ISO, one
  report for the batch. Single-ISO runs omit the section.
- **§2.7 Hourly dispatch view** — for **one selected setpoint** (default: the
  highest-matching optimal setpoint; user-selectable among those included in
  the payload, §3): a 24×365 heatmap of unmatched grid-buy MWh (or matched
  fraction) plus storage SOC trace. Purpose: show *when* matching fails.

### §3 Report payload (data contract)

The renderer's only input is `results/<run_id>/report.json`:

- Top-level `payload_version` (integer, starts at 1) — any breaking schema
  change bumps it; the renderer refuses versions it doesn't know.
- Contains: provenance block (§2.1 fields), the full frontier table rows, the
  long-form build-mix rows, and an `hourly` block holding the §2.7 arrays for
  a small set of setpoints (default: the selected one only; `--report-hourly
  all` includes every setpoint).
- **Hourly size discipline:** hourly series are rounded to 3 significant
  figures and included only for the setpoints named in `hourly`; full-precision
  hourly data stays in Parquet. Keeps committed payloads small (repo push-size
  rule, CLAUDE.md "413" workflow).
- The payload is **comparison-ready but single-run**: PP-09 renders exactly one
  run per report; a future overlay pack may consume N payloads side-by-side
  (low/mid/high sensitivity, additionality on/off) without schema change —
  which is why `iso`, `mode`, `sensitivity`, and `additionality_only` are
  mandatory provenance fields.

### §4 Comparison scope

Single run per report in PP-09. No N-run overlay UI now; the stable payload
(§3) is the extension point. Cross-ISO comparison *within one batch run* is in
scope (§2.6); cross-run comparison is explicitly deferred.

### §5 Persistence: committed `results/` store

- New top-level `scope2-lce-portfolio/results/` directory, **committed** (the
  stakeholder's desktop port reads from it). Layout, one directory per run:
  `results/<run_id>/` containing `<iso>_frontier.parquet`,
  `<iso>_build_mix.parquet`, `<iso>_run_metadata.json` (one triple per ISO in
  the run), plus `report.json` and `report.html`.
- **Run id:** `<iso|multi>_<mode>_<YYYYMMDD-HHMMSS>`, overridable with
  `--run-id`. Re-using an existing run id overwrites that directory (a run is
  reproducible from its config; the metadata JSON is the provenance).
- `data/outputs/` remains the gitignored scratch default for ad-hoc runs; a
  run is persisted by pointing `--out-dir` at `results/<run_id>/` (the CLI
  gains a `--results` convenience flag that composes the run id). `.gitignore`
  is **not** loosened for `data/outputs/`.
- Size discipline: Parquet is compact; the only guarded artifact is the
  payload's hourly block (§3). No retention policy yet — revisit if the folder
  grows past what the push workflow tolerates.

### §6 Renderer implementation shape

- New module `src/lce_portfolio/report.py`: `build_report_payload(sweeps,
  configs, …) -> dict` and `render_report(payload) -> str` (HTML text). Pure
  functions over already-computed results; no LP interaction.
- `write_outputs` chain emits payload + HTML **by default** (opt out with
  `--no-report`); `scripts/render_report.py <run-dir>` regenerates the HTML
  from a committed run folder (e.g. after a template improvement) without
  re-solving.
- Standalone rule holds (ADR 0001): no `import market_sim`, no dependency on
  `frontend/`; the HTML template lives inside the tool's own tree.

## Consequences

- The deliverable of a run becomes a document (`report.html`) instead of a
  narration; per-run Parquet stays the analyst-facing raw data.
- New committed `results/` tree — run outputs enter version control for the
  first time; commits carrying runs follow the small-commit/`push_files`
  workflow.
- `outputs.py` gains a payload-assembly seam; `cli.py` gains
  `--run-id`/`--results`/`--no-report`/`--report-hourly`.
- Rules out (for now): a published LCE dashboard page, N-run overlay UI, any
  retention policy. All three are deliberate deferrals with named extension
  points (§3, §4, §5).
- Follow-up: PP-09 implements §1–§6; tests for payload schema round-trip,
  renderer smoke test on SAMPLE, and multi-ISO batch report.
