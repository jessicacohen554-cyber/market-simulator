# HP-04 — Handoff documentation: mechanics markdown + self-contained HTML explainer site

**Model:** Sonnet · **Depends on:** HP-01, HP-02, HP-03 · **Unblocks:** HP-05
**Targets:** `docs/how-it-works.md` (new), `docs/site/` (new),
`README.md`, `PLAN.md`, `launcher/README.md` (link), `src/lce_portfolio/launcher.py` (footer link only)

Paste the block below into a fresh Claude Code session on
`jessicacohen554-cyber/market-simulator`.

```text
You are finalizing the standalone Scope 2 LCE portfolio tool in
scope2-lce-portfolio/ (repo jessicacohen554-cyber/market-simulator). Develop
on a fresh branch off latest origin/main named scope2/hp-04-docs-site (or
your session's designated branch); push there; open NO pull request.
Preconditions: HP-01/02/03 are merged (annual-average LMP, bundled data,
launcher runs browser) — verify before starting; document accurately
whatever subset actually landed rather than describing unshipped features.

GOAL
Produce the handoff documentation package: (1) ONE canonical markdown
mechanics document, and (2) a small self-contained HTML explainer site inside
the tool folder, visually in the family of the parent repo's codebase-site
but with zero view-time dependency on it — the folder must be pull-out-able.

CONTEXT (read first)
- scope2-lce-portfolio/: README.md, PLAN.md, docs/00-overview.md,
  docs/01-lp-formulation.md, docs/02-data-inputs.md, docs/03-resource-catalog.md,
  docs/04-lmp-export.md, docs/decisions/DECISIONS.md (all 19 ADRs),
  data/templates/README.md, launcher/README.md, docs/handoff/README.md
- Design-system reference: how src/lce_portfolio/report.py vendors the
  codebase-site tokens INLINE (the PP-11 pattern: palette
  #F8F9FC page / white cards / #E5E7EB borders / navy #1A2744 dark band,
  fuel colors solar #F59E0B, wind #22C55E, hydro #0EA5E9, nuclear #6366F1,
  gas #6B7280, storage #E67E22, ccs #26A69A, hydrogen #10B981; system font
  stacks only, NO Google Fonts import). Copy tokens from report.py, not
  from docs/codebase-site/.

DELIVERABLE 1 — docs/how-it-works.md
The single narrative mechanics doc a new developer reads after README.md:
- what the tool answers and for whom (one paragraph);
- architecture walkthrough: intake → profiles → resources → LP → sweep →
  outputs → report → launcher, naming each module and its contract;
- the LP in plain language + the actual variable/constraint list (summarize
  docs/01-lp-formulation.md, link to it — don't duplicate the math);
- data contracts: the two input templates (load-by-facility auto-aggregation,
  hourly vs annual-average LMP semantics and the flat-price caveat), bundled
  data inventory + provenance sidecars, what regenerates vs what ships;
- matching/premium/residual-carbon semantics with pointers to ADRs
  0005/0007/0012/0013/0017/0018/0019;
- the launcher: how a run flows from form → queue → CLI → results store →
  cached report; the run log; the security posture in three bullets;
- how to pull the folder out and run it standalone (the HP-02
  scripts/verify_standalone.sh procedure);
- limits & non-goals (single node per ISO, price-taker, no unit commitment,
  forecast-LMP path on hold per ADR 0015).
Every factual claim must be checked against the code as it exists NOW.

DELIVERABLE 2 — docs/site/ (self-contained HTML explainer)
- index.html (overview, quickstart, launcher tour) plus at most 2–3 more
  pages (e.g. mechanics.html mirroring deliverable 1 with diagrams;
  inputs.html for the template contracts; decisions.html ADR summary table).
  Shared inline <style> per page or one site.css inside docs/site/ — but
  NOTHING outside the scope2-lce-portfolio folder, no CDN, no external
  fonts, no JS frameworks; hand-rolled inline SVG for the architecture /
  data-flow diagrams. Must render correctly opened via file:// from a
  pulled-out copy of the folder.
- Visual bar: clean, intuitive, visually appealing — the codebase-site
  family look (navy header band, white cards, fuel-color accents, data-table
  idiom, AA-contrast text, no horizontal page scroll at 390 px). Keep it
  content-first: this explains mechanics; it does not re-render results.
- Cross-linking: README.md and PLAN.md link to docs/site/index.html and
  docs/how-it-works.md; launcher page footer gains a relative link to the
  site (one-line launcher.py change; keep its tests green).

FINISH
- Prune stale references: any doc that still points to removed
  planning-session/prompt-pack files, or describes pre-HP behavior, gets
  corrected in the same commit that documents the feature.
- Verify: python -m pytest tests/ -q (launcher link change covered);
  grep -rn "import market_sim" src/ || echo OK; open-file sanity on every
  site page (no external refs — mirror report.py's no-external-references
  smoke test with a new test for docs/site/*.html).
- Small imperative commits rebased on origin/main; git push; on a single
  413 switch to mcp__github__push_files. No PRs, no raw model IDs. Finish by
  listing the doc/site inventory and confirming verify output.
```
