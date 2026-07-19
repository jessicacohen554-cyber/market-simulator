# Per-ISO keeper lanes (sharded keeper store)

One file per ISO — `<ISO>.json` — names that market's **current calibration
keeper**: the newest, most structurally faithful run (CLAUDE.md #1/#11/#12:
keeper = most faithful, not lowest error). `index.json` fixes the display
order and is edited only when an ISO joins/leaves the model.

Shard shape:

```json
{
  "iso": "ERCOT",
  "keeper": "<run id>",
  "frontier": { "declared": "...", "note": "..." },   // optional, owner-declared
  "note": "..."                                        // optional
}
```

**Why shards (2026-07-19).** Keeper promotions used to rewrite one shared
`keepers.json` plus the monolithic generated `status.js`, so two sessions
promoting keepers for *different* ISOs always collided and forced rebases.
Now a promotion touches only its own lane:

1. Edit `keepers/<ISO>.json` → set `"keeper"` to the new run id (this fires
   the keeper-audit hook → run the `calibration-keeper-auditor` subagent).
   Or: `python scripts/lib/keeper_store.py --set <ISO> <run-id>`.
2. `python scripts/build_status.py --iso <ISO>` → rebuilds only
   `status/<ISO>.js` (and the deterministic `status/shared.js`, which only
   changes bytes when the rubric itself changed).
3. Commit `keepers/<ISO>.json` + `status/<ISO>.js` with the run's own files.

Different-ISO promotions merge cleanly; only same-ISO promotions serialize
(as they should). Log entries likewise go to the per-ISO continuation files
under `docs/calibration-log/` — never append cross-ISO shared files in a
promotion commit.

Readers: use `scripts/lib/keeper_store.py` (`load_merged()` returns the old
monolith shape). The dashboard composes the shards client-side
(`docs/codebase-site/js/bc-data.js`); the Calibration Status page renders
from the `status/` parts. Frontier blocks are owner-declared designations —
purely declarative, never gating, never touching the verdict. Keepers named
here are never pruned by the top-15 retention sweep, and this list drives
`calibration-status.html`.
