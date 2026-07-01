# Vendored code

This directory holds logic **copied** from the market simulator (`src/market_sim`)
so the LCE portfolio tool is 100% standalone — there is no `import market_sim`
anywhere in this project.

## Rules

1. Every vendored module records at the top:
   - **What** was copied (function/behavior),
   - **From** which upstream file **and git revision** (`git rev-parse HEAD`),
   - **How** to re-sync (what to re-copy and what local adaptations to keep).
2. Keep vendored code minimal — copy only the slice you need, not whole modules.
3. Never import from `market_sim` to "save" a copy. The isolation guarantee is the
   whole point.
4. When upstream changes, re-sync deliberately (see each module's header) rather
   than silently drifting.

## Current contents

- *(none yet)* — the first planned vendoring is the renewable capacity-factor
  shape logic from `src/market_sim/data/renewables.py`, added in
  `docs/prompt-packs/PP-03-cf-profiles.md`. Until then, `profiles.py` uses
  synthetic shapes.
