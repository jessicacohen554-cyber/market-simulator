# Handoff finalization package — status & prompt index

**Written 2026-07-06.** This directory stages the remaining work to make
`scope2-lce-portfolio/` a fully self-contained, pull-out-able handoff tool.
Each `HP-0N-*.md` file contains one complete, ready-to-paste session prompt
with a model assignment. Run them in dependency order below; each session
verifies, commits, and pushes its own work.

## Current-state assessment (what's done vs. what's open)

| Requirement | State |
|---|---|
| LP core, both modes, split storage, CCS, hydro budgets, additionality | **Done** (ADRs 0004–0019; 259 tests) |
| Facility→ISO auto-aggregating 8760 load intake | **Done** (ADR 0010, `intake.py`) — draft template now committed in `data/templates/` |
| Hourly 8760 LMP intake | **Done** (ADR 0011) — draft template committed |
| Annual-average LMP comparison mode | **Open → HP-01** (template committed; intake/report path not yet wired) |
| HTML interface launched from the project launcher | **Done** (ADR 0016: `launcher/run_lce.sh|.bat` → local HTML UI → queue → LP solve → styled report) |
| Report/visualization in codebase-site style | **Done** (PP-11 restyle; self-contained, no CDN) |
| Results cached/logged | **Done** (committed `results/<run-id>/` store + `run_metadata.json`) — visible past-runs browser in the UI is **Open → HP-03** |
| Self-contained data for pull-out (CF profiles, real LMPs, CO₂ rates) | **Open → HP-02** (currently gitignored/rebuilt from the market-sim tree) |
| Handoff documentation (markdown + HTML explainer site) | **Open → HP-04** |
| Final extraction QA (folder runs alone outside the repo) | **Open → HP-05** |
| Directory cleanup (build scaffolding removed) | **Done 2026-07-06** (planning-sessions/, prompt-packs/, management-handoff, project-plan removed; ADRs + design docs + validation memos kept; history in git) |

## Prompt index, model assignments, and order

| # | Prompt | Model | Why this tier | Depends on |
|---|---|---|---|---|
| HP-01 | Annual-average LMP intake mode + template generator | **Sonnet** | Mechanical schema/plumbing + tests; semantics already decided in the template README | — |
| HP-02 | Bundle pull-out data (CF profiles, real 2024 LMPs, CO₂ rates) + extraction smoke test | **Sonnet** | Data wiring + gitignore flips + scripted verification | — (parallel-safe with HP-01) |
| HP-03 | Launcher: past-runs browser, run log, template & annual-average integration | **Sonnet** | UI/server plumbing on an existing hardened server; PP-13 security posture is a checklist to preserve, not re-derive | HP-01 |
| HP-04 | Handoff docs: `docs/how-it-works.md` + self-contained HTML explainer site | **Sonnet** | Writing + visual design against an existing design system | HP-01–03 |
| HP-05 | Final adversarial extraction QA + signoff | **Opus** | Cross-cutting audit needs stronger reasoning; single pass, budget-bounded | HP-01–04 |

Budget notes: **no Fable tasks** — nothing left requires novel LP/math design.
Opus appears exactly once (final audit). HP-01 and HP-02 can run as two
concurrent sessions; everything else is sequential.

## Ground rules every session must honor

- **Standalone:** no `import market_sim` anywhere; verify with
  `grep -rn "import market_sim" src/ || echo OK-standalone`.
- **Self-contained HTML:** launcher page, run reports, and the HP-04 site use
  inline CSS/JS only — no CDN, no external fonts, no network fetch.
- Tests green before commit: `python -m pytest tests/ -q` from the tool dir
  (use `../.venv/bin/python` inside the repo, any 3.11+ env with
  `requirements.txt` outside it).
- Push discipline: small commits rebased on latest `origin/main`; if
  `git push` returns HTTP 413 once, switch to `mcp__github__push_files` —
  never loop on the large push.
- No PRs unless the stakeholder asks. No raw model IDs in commits/code.
