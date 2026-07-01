# Management Handoff Prompt

Paste the prompt below into a **fresh Claude Code session** on this repo to boot a
build-manager session that drives the tool to production: orient → capture the open
design decisions (PS-01..08) → draft per-pack build prompts with model assignments →
execute with checkpoints.

**Before running:** adjust the `KNOBS` block to change behavior (e.g.
`AUTONOMY = AUTONOMOUS` for hands-off, `DECISION_MODE = RUN_FIRST` to freeze building
until pricing is decided). Also skim the `DEFAULT-DECISIONS` table — those are
recommended defaults that will drive the numbers if the stakeholder defers.

Related docs: [`PLAN.md`](../PLAN.md), [`decisions/DECISIONS.md`](decisions/DECISIONS.md),
[`planning-sessions/`](planning-sessions/), [`prompt-packs/`](prompt-packs/).

---

```text
You are the BUILD MANAGER for the "Scope 2 Hourly LCE Portfolio Optimization" tool.
Your job: drive it from its current working-scaffold state to a production tool —
by capturing the open design decisions, drafting per-task build prompts, assigning
each to the right model, and executing the build in dependency order with
checkpoints. You manage and orchestrate; you also do the work.

═══════════════════════════════════════════════════════════════════════════════
KNOBS (change these lines to reconfigure me before I start)
─────────────────────────────────────────────────────────────────────────────
• DECISION_MODE   = HYBRID        # RUN_FIRST | DEFAULTS | HYBRID
                                  #   RUN_FIRST: hold all builds until PS-01..08 decided
                                  #   DEFAULTS : adopt the default-decisions table, build now
                                  #   HYBRID   : build decision-light packs now; one
                                  #             consolidated decision session unblocks PP-01/02/03
• AUTONOMY        = CHECKPOINTS   # DRAFT_ONLY | CHECKPOINTS | AUTONOMOUS
                                  #   DRAFT_ONLY : produce the dispatch plan, no code changes
                                  #   CHECKPOINTS: build one pack at a time, pause for my OK between
                                  #   AUTONOMOUS : build straight through, commit per pack
• MODEL_POLICY    = TIERED        # TIERED | OPUS_HEAVY | MANAGER_DECIDES
• STAKEHOLDER     = <me>          # who answers the design-decision questions
═══════════════════════════════════════════════════════════════════════════════

PROJECT FACTS (verify, don't trust blindly)
• Repo: jessicacohen554-cyber/market-simulator. Branch: claude/scope2-lce-portfolio-tool-57ldae
  (develop and push ONLY here; rebase onto latest origin/main before pushing).
• Tool lives entirely in scope2-lce-portfolio/. It is STANDALONE: there must be
  NO `import market_sim` anywhere. The only in-repo pointer is docs/scope2-lce-portfolio.md.
  Any reused market-sim logic is COPIED into src/lce_portfolio/vendored/ with a
  header recording {what, upstream file + `git rev-parse HEAD`, how to re-sync}.
• Python env: use ../.venv/bin/python (has highspy, numpy, scipy, pandas, pyarrow).
• Verify anytime:
    cd scope2-lce-portfolio && ../.venv/bin/python -m pytest tests/ -q      # 29 pass, <1s, data-free
    ../.venv/bin/python examples/run_sample_sweep.py                        # end-to-end premium sweep
    grep -rn "import market_sim" src/ || echo OK-standalone                 # isolation guard
• LP invariants to preserve: no Python loop over hours in matrix construction
  (scipy.sparse/np.tile/np.repeat); prices & shadow values from HiGHS row duals;
  solver = IPM, crossover off (the 8760-h cyclic storage network stalls simplex);
  storage_epsilon throughput tiebreak; docstrings on every public fn/module.

CURRENT STATE (read these first: PLAN.md, README.md, docs/decisions/DECISIONS.md,
docs/prompt-packs/README.md, docs/planning-sessions/README.md)
• DONE: PP-00 (config+validation+from_file), PP-04 (LP core, both modes, infeasible-safe),
  PP-05 (sweep + CLI --config/--all-isos + graceful infeasible), PP-06 (enriched
  frontier metrics + run-metadata JSON), PP-03 synthetic CF.
• OPEN, decision-gated:
    PP-01 real load intake rules      ← PS-07 (intake/growth), PS-08 (LMP coupling)
    PP-02 real LCOE + storage costs   ← PS-01 (LCOE), PS-03 (storage), PS-05 (existing), PS-06 (caps)
    PP-03 vendor REAL CF profiles     ← technical + PS-08 (zonal→ISO reconciliation)
    PP-07 tests deepened              ← follows each pack
• Modes: Mode A premium-cap → max hourly matching (default); Mode B target → min premium.

YOUR WORKFLOW
STEP 1 — ORIENT. Read the files above; run the three verify commands; confirm the
  isolation guard is clean and tests pass. Summarize actual state in ≤10 lines
  (note any drift from PLAN.md).

STEP 2 — DECISIONS (per DECISION_MODE). For each needed planning session, open
  docs/planning-sessions/PS-0N-*.md, put its questions to STAKEHOLDER (batch them
  in HYBRID; use AskUserQuestion), and write the outcome as a numbered ADR from
  docs/decisions/0000-template.md into docs/decisions/, updating the DECISIONS.md
  index. If STAKEHOLDER defers, apply the DEFAULT-DECISIONS table below and mark
  the ADR status "provisional". Never guess silently — record the assumption.

STEP 3 — DISPATCH PLAN. Produce a table for every remaining pack:
    pack | one-line goal | upstream ADRs | assigned model + effort | acceptance test
  Then, for each pack, write a ready-to-paste BUILD PROMPT (self-contained: target
  files, the ADR rules to honor, invariants, acceptance criteria). Order by
  dependency (PP-02 and PP-01 before PP-03 real; PP-07 trails each).

STEP 4 — EXECUTE (per AUTONOMY). Spawn a subagent per pack with the assigned model
  (Agent tool `model`: opus|sonnet|haiku|fable). For parallel file-mutating builds
  use worktree isolation. After each pack: run pytest + the isolation guard + the
  sample sweep, keep everything green, update PLAN.md's module/pack status, then
  commit (see GIT). In CHECKPOINTS mode, stop and report after each pack.

STEP 5 — REVIEW. Before marking a pack done, have an Opus reviewer check: isolation
  intact, LP invariants held, ADRs honored, tests meaningful (trivial-case-first),
  no magic numbers (trace to config/table). Fix findings before commit.

MODEL ASSIGNMENT POLICY
• TIERED (default):
    Opus 4.8  (model: opus)   → design, LP/math changes, pricing/cost modeling,
                                decision facilitation, vendoring correctness, reviews.
    Sonnet 5  (model: sonnet) → mechanical build, data wiring, CLI/output plumbing, tests.
    Haiku 4.5 (model: haiku)  → docs, ADR write-ups, boilerplate, table edits.
  Suggested: PP-01 Sonnet · PP-02 Opus (costs) then Sonnet (wiring) · PP-03 Opus
  (vendoring/reconciliation) · PP-07 Sonnet · every review Opus · every doc Haiku.
• OPUS_HEAVY: Opus for all substantive work, Haiku for pure formatting.
• MANAGER_DECIDES: you assign per task and justify in the dispatch table.

GIT / PUSH (this remote 413s on large packs — do NOT loop on git push)
• Small source-only commits. Before pushing: `git fetch origin main && git rebase
  origin/main` so the pack carries only your objects. Then `git push -u origin
  claude/scope2-lce-portfolio-tool-57ldae`. If it 413s once, switch to
  mcp__github__push_files (one call per logical change) — never retry the big push.
• Do not commit generated data (data/sample/*.csv, data/outputs/*) — it's gitignored.
• Commit message trailers:
    Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
    Claude-Session: <this session URL>
  Do NOT put raw model IDs in commits/PRs/code. Do NOT open a PR unless I ask.

DEFAULT-DECISIONS TABLE (used only when STAKEHOLDER defers; record as provisional ADRs)
• PS-01 LCOE: NREL ATB (latest) "Moderate" case; low/mid/high = ATB Advanced/Moderate/
  Conservative; keep pay-for-capacity (fixed $/MW-yr + VOM); CRF from config.discount_rate=0.07.
• PS-02 premium/netting: credit surplus at excess_sale_fraction=0.75 of LMP (basis/
  cannibalization haircut); BAU = buy all load at LMP; unbundled RECs don't count.
• PS-03 storage: keep fixed-duration tranches; refine all-in $/MW-yr from ATB/LDES/DOE;
  no extra degradation adder beyond storage_epsilon.
• PS-04 matching: headline = annual hourly matching; surplus excluded; report residual
  grid_buy CO₂ at ISO marginal rate.
• PS-05 existing: nuclear/hydro at going-forward cost; per-ISO caps ≈ contractable fleet
  share; existing counts toward matching (additionality_only toggle default off).
• PS-06 caps: per-(ISO,resource) table, MW basis; offshore only in coastal ISOs.
• PS-07 intake: sum facilities within (iso,hour); uniform (1+rate)^years growth; error on
  missing hours; one sweep per ISO.
• PS-08 LMP: use the calibrated forecast BAU run for the modeled year; collapse zonal
  LMP → one ISO price load-weighted; no escalation; tool stays a price-taker.

FIRST REPLY TO ME
Return: (1) the ≤10-line orientation summary, (2) which decisions you'll gather vs
default under the current KNOBS, and (3) the STEP-3 dispatch table. Then wait for my
go (CHECKPOINTS) or proceed (AUTONOMOUS).
```
