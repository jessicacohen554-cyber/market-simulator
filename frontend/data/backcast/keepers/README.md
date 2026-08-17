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

## Class-E retention rule (ADOPTED 2026-08-16 — owner sitting, closes BLOAT-2)

The standing retention rule for the backcast dashboard's three stores
(registry sidecar / `runs/<id>.js` payload / `results/calibration/<bundle>`
dir), adopted verbatim from `docs/bloat-removal-plan-2026-08.md` §7 item E2 at
the 2026-08-16 BLOAT-2 owner card:

1. **Payload lifetime = registry membership** (already enforced; adopt as the
   stated rule). A payload exists iff its sidecar exists.
2. **Per-ISO cap stays the rule-15 top-15**, executed by `prune_iso` at
   registration time (current counts are at/below cap).
3. **Immunity set as implemented**: current keeper, `keeper_at_declaration`,
   ablation-referenced twins, structural-prior sources.
4. **Bundle linkage**: pruning a run prunes its bundle dir in the same commit
   (already wired) — plus a **quarterly parity sweep** extension: fail if any
   `results/calibration/<bundle>` maps to no retained sidecar `bundle` field
   and is not otherwise keep-required (closes the last drift channel; extend
   `check_registry_payload_parity.py` or `audit_keepers.py`, one PR, no data
   change).

Enforcement homes: points 1–3 are `scripts/dashboard_add_run.py`
(`prune_iso` + `_protected_run_ids`) plus the two parity directions of
`scripts/check_registry_payload_parity.py`. Point 4's sweep is
`check_registry_payload_parity.check_bundle_retention` (built at adoption,
same PR): it runs inside the always-on CI parity gate, a strict superset of
the quarterly cadence the rule asks for. Keep-required carve-outs the sweep
honors, and why: the §5.2 `_`-prefixed working/archive dirs
(citation-checked KEEP), bundles referenced by a
`results/regression-goldens/*/manifest.json` capture record, and the
checker's documented `KEEP_REQUIRED_UNMAPPED_BUNDLES` allowlist (empty at
adoption) for a keep-required bundle that legitimately outlives its sidecar
(the `keeper_at_declaration` / structural-prior classes — normally
sidecar-mapped via the prune immunity, so an entry there is the exception,
never the rule). Root-level loose records are files, and
`results/hindcast/` / `results/regression-goldens/` live under other
`results/` roots — all outside the sweep's scope by construction.
