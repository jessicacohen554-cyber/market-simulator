# PS-11 — End-User Reporting Deliverable

**DECIDED → ADR 0014 (2026-07-02).**

**Goal:** decide what the tool's end-user deliverable looks like — the artifact a
stakeholder actually reads and shares — so the reporting prompt pack (PP-09) can
be built without a decision stop.

**Origin:** today a run emits per-ISO Parquet frontiers + build-mix + run-metadata
JSON + a plain-text CLI summary (`outputs.py`, PP-06). There is no consolidated
human-readable report; results are narrated in chat or read off raw tables.

## Orientation (what already exists)

- `outputs.py` computes everything a report needs per solve: the enriched
  frontier row (matching%, premium $/MWh and $/yr, %-over-BAU, net/BAU cost,
  capital cost, avoided purchases, surplus MWh & revenue, grid-buy MWh,
  residual CO₂ (ADR 0013), shadow price, status), the long-form build-mix
  table, and full config provenance in the run-metadata JSON.
- `PortfolioResult` additionally carries the **hourly arrays** (per-resource
  gen, storage charge/discharge/SOC, grid buys, excess) — enough for an hourly
  dispatch view without re-solving.
- The parent repo's established reporting pattern is the **backcast dashboard**:
  static HTML + committed per-run JSON payloads under
  `frontend/data/backcast/`, published via GitHub Pages. One candidate pattern
  to mirror at run granularity.

## Questions put to the stakeholder (2026-07-02)

1. **Primary artifact** — static HTML per run vs markdown vs CSV/Excel vs a page
   in the repo's existing frontend?
   **Answer: self-contained static HTML report per run** (recommended default
   accepted).
2. **Content** — which views are must-have?
   **Answer: all four offered** — premium-vs-matching frontier chart; build-mix
   by setpoint; cost breakdown (capex/VOM, grid, surplus, vs BAU); residual-CO₂
   view; multi-ISO comparison table; hourly dispatch heatmap + SOC trace for a
   selected setpoint.
3. **Comparison axes** — single run vs side-by-side scenarios?
   **Answer: single run, comparison-ready** — PP-09 renders one run per report
   but defines a stable per-run payload so a later pack can overlay runs
   (low/mid/high costs, additionality on/off) without rework.
4. **Where results live** — gitignored per-run outputs vs a committed registry?
   **Answer (stakeholder, verbatim):** "This will be ported onto a desktop so
   results should be committed into a results parquet folder from which they
   can be read." → runs are written to a **committed `results/` folder** of
   Parquet + metadata per run; the report (and the future desktop port) read
   from that folder. This departs from the recommended gitignored default and
   from the current `.gitignore` (`data/outputs/*`).

## Outcome

ADR **0014** (accepted) specifies the deliverable: one self-contained HTML
report per run, generated from a versioned per-run report payload, with all runs
persisted under a committed `results/<run_id>/` Parquet folder. Section numbers
in the ADR are the citation targets for PP-09.

## PP-09 scope as implied (sketch)

- New `report.py` renderer module + `scripts/render_report.py` (regenerate from
  a committed run folder) + CLI integration (report emitted by default after
  `write_outputs`).
- Per-run report payload JSON (ADR 0014 §3) assembled from `SweepResult` — the
  only data contract the HTML touches.
- Self-contained HTML template (inline JS/CSS/data, no CDN) implementing ADR
  0014 §2 views.
- Committed `results/` store: run-id convention, directory layout, `.gitignore`
  carve-out, size discipline for hourly payloads (ADR 0014 §5).
- Tests: payload schema round-trip, renderer smoke test on the SAMPLE ISO,
  multi-ISO batch report.
