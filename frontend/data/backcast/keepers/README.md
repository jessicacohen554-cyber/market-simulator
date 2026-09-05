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

4. **Re-key the forecast gate-(a) stamp in THIS SAME PR** — see the
   2026-09-01 block below (owner ruling R-T). It is one field in
   `frontend/data/forecast/program-status.json`, and it is the promoting
   lane's duty, not a follow-up.

Different-ISO promotions merge cleanly; only same-ISO promotions serialize
(as they should). Log entries likewise go to the per-ISO continuation files
under `docs/calibration-log/` — never append cross-ISO shared files in a
promotion commit.

## 2026-09-01 — two owner rulings that bind promotion lanes (R-T, R-V)

Recorded by the audit-program records lane v20 at pin `07472e7c`. Both are
owner rulings from the 2026-09-01 third director sitting; the audit board
(`docs/handoffs/audit-program-director-board-2026-08.md`, items J-2 and J-4)
and the program ledger (`docs/model-audit-release-plan-2026-08.md` §8) carry
the full record. **Nothing above this heading is changed by this block.**

### R-T — a keeper-promotion PR re-keys the forecast gate-(a) stamp in the same PR

**This is step 4 of the promotion procedure above, and it is the promoting
lane's duty.** When you set `keeper` in `keepers/<ISO>.json`, also update that
ISO's `gate.a_keeper_marker` in `frontend/data/forecast/program-status.json`
to name the new run id — **in the same PR**, alongside `status/<ISO>.js`.

- **It is a STAMP re-key, not a verdict change.** `scripts/check_gate_a_provenance.py`
  compares keeper identity and marker state and **reads no determination**, so
  a leg that read `fail` before will read `fail` after. Re-keying a stale stamp
  never moves a gate verdict; leaving it stale just makes the forecast board
  name a keeper that no longer exists.
- **Why it moved to the promoting lane.** The guard is a *detector* — it fires
  on the *next* PR, after the staleness already exists. In the MISO
  `191-bexit → 198-oomlevel` promotion the stamp stayed wrong for **nine merged
  PRs** (#4552 → #4561) and needed a separate one-push owner grant to repair.
  Carrying the re-key in the promotion PR makes that window **zero**. Two
  earlier one-push grants (R-N for CAISO, R-T for MISO) exist only because this
  duty did not; there should not be a third.
- Verify locally before pushing: `python3 scripts/check_gate_a_provenance.py`
  (exit 0). CI enforces it at PR time once branch protection lands.

### R-V — keeper freeze on ERCOT, NEISO and PJM

**No keeper promotion in these three lanes** until PERF-B's byte-green loop
completes **or the owner lifts the freeze**. They are the three ISOs holding a
`complete` marker and the three whose stage-0 goldens are CURRENT; the freeze
exists to keep those goldens from going stale under them.

- **MISO, CAISO and NYISO are EXPLICITLY UNFROZEN** and promote as normal.
- **This freeze is prose-enforced.** No script checks it — `audit_keepers.py`
  validates marker/keeper identity and knows nothing about a promotion embargo.
  If you are promoting in a frozen lane, you will not be stopped by a gate; do
  not promote.
- ⚠️ **It is NOT `holdout-freeze.json`.** That file is a *spend* freeze on the
  locked-test tier for all six ISOs (CLAUDE.md rule 22). This is a *promotion*
  freeze on three ISOs. Different scope, different subject, different lifting
  authority; neither implies the other.

**🔵 LIFTED 2026-09-05 — owner ruling R-AR (audit-program sitting, 21:55Z),
verbatim: *"Lift R-V now for all three."*** The freeze above is **no longer in
force**: ERCOT, NEISO and PJM promote as normal, like the other three lanes. The
note is kept rather than deleted because it is the record of what bound these
lanes between 2026-09-01 and 2026-09-05, and because its stated rationale is
still the live risk. **R-AR AMENDS R-AN**, which had attached the lift to the G2
declaration; the lift is **not** conditioned on that declaration, which at the
time of writing has still not been made (`main` reads `protected: false`).
**What the lift changes, stated plainly.** The freeze existed *"to keep those
goldens from going stale under them"*. With it lifted, **stage-0 has no
protection left**: NEISO and PJM are the only two `perfb-stage0` entries still
CURRENT, and either can now go stale by promotion. That is a consequence of the
lift, not an objection to it — the two **ERCOT** entries had already gone stale
*inside* the freeze when the owner-directed ercot-248 consolidation moved
ERCOT's `keeper` field at 2026-09-05 19:01:23Z (`4b7a515e`, PR #4808:
`2026-08-25-234-eastex-identity` → `2026-09-05-ercot248-two-config-keeper`,
every per-year artifact copied byte-for-byte, zero solve, `complete.ERCOT`
re-keyed with its rule-22 D-5(b) re-verification reading CALIBRATED and not
worse). A prose-enforced freeze did not stop the owner's own act, which is
evidence it was not achieving its purpose. **If you are promoting in one of
these three lanes, the R-AI stage-0 re-capture obligation is what now applies —
not this freeze.** Recorded by the audit records lane v31 at pin `fb51bd82`;
full account in `docs/handoffs/audit-program-director-board-2026-08.md` (v31
block, R-AR) and `docs/model-audit-release-plan-2026-08.md` §8.

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
