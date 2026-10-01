# PRECOMMIT — capx D95: D94's two key-provenance UNKNOWNs

Lane: capx D95 (relaunch) · Opus · DATA PROFILE code · ZERO LP · branch `claude/capx-d95-d94-key-unknowns`
Charter: `docs/handoffs/capx-director-prompt-pack-2026-08.md` "D95"; ledger §0bk.
Written and pushed BEFORE any edit under `scripts/`, `src/` or `docs/governance/`.

## 0. STATE AT MY HEAD — the UNKNOWN set is the charter's two

`scripts/check_key_provenance.py` at checkout `c64e69eb` (EXIT 1):

    245 committed run configs at c64e69eb: 188 reproduce, 29 have no key, 28 mismatch
      16 KNOWN (listed exceptions), 10 LAG (Q66 class rule), 2 UNKNOWN
    [G1_UNKNOWN] results/ff-t3-neiso-golden/d94/vre_long/run_config.json
    [G1_UNKNOWN] results/ff-t3-neiso-golden/d94/vre_short/run_config.json

Same two records the charter names. G6 reads 0. Branch base is `origin/main` `645f5e0c`.

## 1. PART 1 — THE ATTRIBUTION (measured before this file was written, zero LP)

This lane ran Part 1 before writing this file, because Part 1 is read-only experiment. What is
pre-declared below is the **disposition** and every number the FINDING will report.

1. **The config-side rules did not move.** The at-declaration key of each payload is identical
   under the pin's own code (`924017c8`, worktree, repo roots) and under HEAD:
   `vre_short` `f04fd06348e1623d`, `vre_long` `e51aa9785953fa49`. The D91 single-field search
   (undrop each of `_CACHE_KEY_OPTIONAL_FIELDS`, drop each payload field) gives **zero hits** at
   HEAD **and** at the pin. The four fields registered after the pin
   (`cc_block_summer_rating`, `unit_outage_precod_clip`, `fleet_zone_vintage_coords`,
   `ercot_partial_outage_day_guard`) are absent from both payloads and cannot enter the hash.
   So **(a) and (b) do not apply.**
2. **The recorded keys were hashed WITH a non-empty solve-surface block.** At the pin,
   `moved_rows("NEISO") = {"RGGI_MEMBER_STATES_BY_YEAR": "94d8b85ac442ecfd"}`, and
   `head_key(payload, surface=True)` there reproduces **both** recorded literals exactly
   (`1be407901f4f8000`, `df7b178ae9ccbe41`). Each bundle's own committed
   `NEISO/<key>/solve_surface.json` records the same `moved` block.
3. **At HEAD, injecting that recorded block reproduces both literals exactly.** No subset of
   HEAD's live NEISO block (7 rows) reproduces either.
4. **Two surface events moved NEISO's block after the pin, both on `main`, both needed**
   (first-parent evaluation of `moved_rows` at every merge touching a `SURFACE_MODULES` file):
   * **`a669e4a4`** (PR #6603, R-PJM-2, commit `72c8c7ee` "2019 RGGI rows"), merged
     2026-09-25T01:38Z: `RGGI_MEMBER_STATES_BY_YEAR` `94d8b85a` → `e432156b`, in **all nine**
     ISOs' projections (and PJM's `CAP_AND_TRADE_PROGRAMS`, `PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE`,
     `PJM_RGGI_ZONE_SHARE`). **It is an ancestor of D94's PR tip `3981a7a0`**, so at D94's own
     merge (`136bb40a`) the two records already did not reproduce. D94 §5's "both reproduce"
     was measured before its last rebase.
   * **`5f8d153c`** (PR #6611, COAL-SUB, commits `8eaf34b5`/`05437cc0`), merged
     2026-09-25T03:27Z: six rows newly off declaration in **all nine** ISOs —
     `GENERIC_BASE_OFFER_CURVE`, `LABELS`, `MAINTENANCE_MONTHLY_SHAPE`,
     `MIN_STABLE_PCT_PHYSICAL`, `PLANT_CLASSES`, `THERMAL_AVAILABILITY` (ERCOT also
     `CORRELATED_OUTAGE_CURVE`).
5. **Why the census is blind to it.** The census accepts a record that reproduces under EITHER
   construction: surface at declaration, or HEAD's live surface. That covers D79's designed
   re-key only for a record solved while its ISO's surface sat AT declaration. The two d94 legs
   are the **first committed records ever solved on a moved surface** (10 committed
   `solve_surface.json`; the other eight record `moved: {}`). A historical block matches neither
   construction once the surface moves again.

## 2. PART 2 — DISPOSITION DECLARED: (c), SURFACE RE-KEY. NO CODE EDIT.

* No existing exception class covers it. Recipe `surface` accepts only `"declaration"` or
  `"live"`. `vintage` AST-extracts `scenarios.py` only and models no surface; at the pin the
  vintage/at-declaration key is `f04fd063…`, not the literal.
* Per the charter I **do not invent a class**, I **do not append** to
  `key-provenance-exceptions.json`, and I **do not** add a lag-table row (it is not a field lag).
* It is reported for an **owner card**: "should the census accept a record's own committed
  `solve_surface.json` `moved` block as a third construction?" The FINDING carries the zero-code
  probe: that construction reproduces **9 of the 10** records with a `solve_surface.json` (the
  tenth, `d90-rescore`, is already a Q66 `LAG`), reproduces both d94 legs, and changes no
  at-declaration verdict.

## 3. PREDICTIONS (checked in the FINDING)

* P1. Census at `645f5e0c` (branch base): the same **2 UNKNOWN**, the same 10 LAG and 16 KNOWN.
  EXIT 1. Record count may differ from 245 only by new committed configs.
* P2. After this lane: **byte-identical** census (this lane edits no code, table or record).
* P3. D96 exposure: D96's `neiso-t3` legs, if they solve on any pin at or after `5f8d153c`,
  record a **non-empty** NEISO block (7 rows today). They will reproduce under the live
  construction until the next NEISO surface move, then turn `G1_UNKNOWN` by this same
  mechanism. If they land before my merge, I check them.

EXIT criterion met by naming: two residuals, each with a live owner (the owner card, §2).
