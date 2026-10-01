# HANDOFF — SCORER-COAL-1: a CEMS-anchored coal target for the C1 fossil reconcile (cross-ISO)

```
SESSION SCORER-COAL-1 — cross-ISO benchmark lane (owner card "Route to scorer lane", NWPP-NEXT-11, 2026-09-29)
DATA PROFILE: code  (widen per ISO only if a bench part must be re-rendered)
MODEL: Opus or Fable (rule 27: scorer / render code)
CLAUDE.md is binding. Pay particular attention to rules 1, 14, 15, 19, 26, 27 and 35. This lane runs NO LP solve.

DIRECTIONS (owner, standing)
- Present every decision for the owner as clickable decision cards (AskUserQuestion), NEVER as inline text.
- When done: create a PR, rebase, and merge it. Archive any sessions you launched. Say which branches can be deleted.
- Report every determination change at full magnitude, in every ISO, in both directions.

THE QUESTION
- scripts/render_calibration_html.py::reconcile_vintage_classes scales EVERY fossil class by ONE factor so the EIA-923
  gas + coal (+ oil) total matches EIA-930. It is ISO-agnostic. The docstring names its own limitation: "a CAMPD-per-class
  target (complete in every vintage) is the follow-up refinement (docs/handoffs/pjm-cc-overrun-benchmark-basis-g21-2026-07.md §6)".
- NWPP evidence (docs/handoffs/FINDING-nwppnext11-coal-c1-c4-decomposition-2026-09-29.md §1):
  - k is 0.87–0.92 in 2019–2024 and applies to coal too.
  - EIA-930's coal cell matches EIA-923 coal within 1 % in 2020 and 2024.
  - So a gas-side 930 shortfall is charged to coal: about 2.5 of the 4.2 TWh "COAL_PRB 2020 over-run".
- The bench already carries e930.coal_cems (CEMS-net coal, the model's class map), the C2 G-21b anchor.

WHAT TO DO (zero LP)
1. Measure, for every ISO and every registered keeper year, three quantities: the uniform factor k; 923 coal against the
   930 coal cell against coal_cems; and how much of each C1 coal record's miss comes from k.
   Read committed bench parts plus scripts/run_calibration_full._eia923_frame; do not re-solve.
2. Design options, each stated before any number selects it (rule 1):
   (a) Leave coal at its own 923 grid level (CEMS-validated) and reconcile only the gas family to the 930 residual.
   (b) Anchor coal to coal_cems × an in-run k_coal, as C2's G-21b fallback does.
   (c) Status quo.
   Check each against the docstring's reasons for abandoning the per-family reconcile (PJM/MISO 930 coal mis-split),
   and against the preliminary-vintage (2025) up-scale path.
3. Re-score EVERY keeper under each option with calibration_verdict (stdlib), and table every record that moves.
   Present the choice as a decision card. Do not land a scorer change without the owner's ruling.
4. If the owner rules to change it:
   - bump the rubric version in calibration_verdict.py with the ruling quoted;
   - re-render the bench parts through the single writer (render_calibration_html);
   - re-score and rebuild the status pages per ISO (build_status.py --iso);
   - update docs/rubric notes and rule-history if a rule's text moves.
   Per-ISO keeper files are touched only through their own status rebuild, never hand-edited.

NOT IN SCOPE
- Any solve, any keeper promotion, any change to demand construction. NWPP's plant-basis demand
  (derive_nwpp_plant_basis_energy.py) reads classFull. Flag it if the chosen option would move that artifact (rule 23:
  re-derivation needs a data change, and a benchmark-basis change must be argued as one). Do not re-derive it here.
```
