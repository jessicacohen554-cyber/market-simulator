# Prompt Packs

Each `PP-NN-*.md` is a **build prompt**: a self-contained instruction to
implement or deepen one module, citing the ADRs (`../decisions/`) it must honor.
Packs turn decisions into code. A team member can open a pack in a fresh session
and execute it.

## Ordering & gating

Run in order; each pack lists its **upstream decisions**. Do not run a pack until
its ADRs are recorded (a pack that depends on an undecided question should trigger
the relevant planning session first).

| PP | Builds | Upstream decisions |
|---|---|---|
| PP-00 | Scaffold & `PortfolioConfig` | 0001, 0002 |
| PP-01 | Load intake & LMP coupling | PS-07, PS-08 |
| PP-02 | Resource catalog & costs | PS-01, PS-03, PS-05, PS-06 |
| PP-03 | CF profiles (first vendoring) | — |
| PP-04 | LP core (both modes, constraints) | PS-02, PS-04 |
| PP-05 | Sweep driver & CLI | 0002 |
| PP-06 | Outputs & reporting | PS-02, PS-04 |
| PP-07 | Tests | all |

## Current state

The minimal slice already ships a first cut of PP-00, PP-04, PP-05, PP-06 and a
synthetic PP-03. The packs below describe how to take each from "minimal working"
to "production", and mark what already exists.

## Rules for every pack

- Stay standalone: **no `import market_sim`**. Reused logic is copied into
  `src/lce_portfolio/vendored/` with a source + revision + re-sync header.
- Follow the LP rules that apply (no Python loop over hours in matrix
  construction; duals for prices; docstrings on every public function/module).
- Add/extend tests (PP-07) and update `PLAN.md`'s status table.
