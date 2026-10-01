# FINDING — capx D95: D94's two key-provenance UNKNOWNs are a SOLVE-SURFACE re-key (disposition c)

Lane capx D95 (relaunch) · Opus · ZERO LP · DATA PROFILE code · branch `claude/capx-d95-d94-key-unknowns`
PRECOMMIT: `docs/handoffs/PRECOMMIT-capx-d95-2026-09-25.md` (pushed first, `c58309bc`).

## 0. THE ATTRIBUTION, AND THE CENSUS BEFORE / AFTER

**Cause: the NEISO solve surface (capx D79), not a cache-key field.** Both d94 legs were hashed with
the `__solve_surface__` block `{"RGGI_MEMBER_STATES_BY_YEAR": "94d8b85ac442ecfd"}`, which was live at
their pin `924017c8`. Two later merges on `main` moved NEISO's block, and each is enough on its own to
break the match:

| merge | lane | NEISO rows it moved | ISOs re-keyed |
|---|---|---|---|
| **`a669e4a4`** (PR #6603, commit `72c8c7ee` "2019 RGGI rows"), 2026-09-25T01:38Z | R-PJM-2 | `RGGI_MEMBER_STATES_BY_YEAR` `94d8b85a` → `e432156b` | all nine (PJM also `CAP_AND_TRADE_PROGRAMS`, `PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE`, `PJM_RGGI_ZONE_SHARE`) |
| **`5f8d153c`** (PR #6611, commits `8eaf34b5` / `05437cc0`), 2026-09-25T03:27Z | COAL-SUB | newly off declaration: `GENERIC_BASE_OFFER_CURVE`, `LABELS`, `MAINTENANCE_MONTHLY_SHAPE`, `MIN_STABLE_PCT_PHYSICAL`, `PLANT_CLASSES`, `THERMAL_AVAILABILITY` | all nine (ERCOT also `CORRELATED_OUTAGE_CURVE`) |

**The reproducing literal.** At HEAD, `head_key(payload, surface=True)` with the moved-rows block set to
`{"RGGI_MEMBER_STATES_BY_YEAR": "94d8b85ac442ecfd"}` gives `1be407901f4f8000` (`vre_short`) and
`df7b178ae9ccbe41` (`vre_long`). Both equal the recorded literals. That block is also what each
bundle's own committed `NEISO/<key>/solve_surface.json` records under `moved`.

`scripts/check_key_provenance.py`:

| state | census line | UNKNOWN | exit |
|---|---|---|---|
| `c64e69eb` (session checkout) | `245 … 188 reproduce, 29 have no key, 28 mismatch — 16 KNOWN, 10 LAG, 2 UNKNOWN` | the two d94 legs | 1 |
| `c58309bc` = `645f5e0c` + PRECOMMIT (branch base) | `244 … 188 reproduce, 28 have no key, 28 mismatch — 16 KNOWN, 10 LAG, 2 UNKNOWN` | the two d94 legs | 1 |
| after this lane | **byte-identical**: this lane edits no code, table or exception record | same | **1** |

The one-record drop between the two base lines is a no-key record that `main` removed. In the deepened
clone the ladder also resolves the pin, so the fail line becomes "2 mismatch(es) reproduce under NO
recipe", the charter's quote. **EXIT stays 1.** Under the charter's exit clause both residuals are named,
with a live owner (§3).

## 1. PART 1 — ATTRIBUTION BY EXPERIMENT

1. **The config-side key rules did not move for these payloads.** The at-declaration key is identical at
   the pin (worktree at `924017c8`, repo roots) and at HEAD: `f04fd06348e1623d` / `e51aa9785953fa49`.
   Between `924017c8` and HEAD, `scenarios.py` added four registered optional fields
   (`cc_block_summer_rating`, `unit_outage_precod_clip`, `fleet_zone_vintage_coords`,
   `ercot_partial_outage_day_guard`), each with a drop default. It also added the COAL-SUB
   `__post_init__` fold and a MISO coal-sigmoid re-derivation. None of these can reach a stored
   payload's hash: `head_key` hashes the record's own dict, and none of the four fields is in it.
2. **D91 single-field drop search.** For each of `_CACHE_KEY_OPTIONAL_FIELDS` I tried an undrop, and for
   each of the 875 payload fields I tried an unconditional drop. That gives **0 hits at HEAD and 0 hits
   at the pin.** So this is not a Q66 lag (a) and not a still-unregistered field (b). G6 reads 0.
3. **Surface fingerprint, tested separately.** At the pin, `moved_rows("NEISO")` is exactly
   `{RGGI_MEMBER_STATES_BY_YEAR: 94d8…}`, and the live construction reproduces both literals. At HEAD I
   tried every one of the 2⁷ subsets of HEAD's live NEISO block. **None reproduces.** Only the recorded
   block does.
4. **The bisection.** I evaluated `moved_rows` for all nine ISOs at every first-parent merge on `main`
   between merge-base `3affcd71` and HEAD that touches a `SURFACE_MODULES` file or
   `solve_surface_declared.py`. The rows first differ at `a669e4a4`, and then again at `5f8d153c`.
   `cae5e663` (I-CAISO) and `f79b5e77` (R-SOCO-B) move CAISO and SOCO rows only. The merges after
   `5f8d153c` leave NEISO unchanged.
5. **Correction to D94 §5.** `a669e4a4` is an ancestor of D94's own PR tip `3981a7a0`. So at D94's merge
   `136bb40a` the two records **already** did not reproduce. D94's "both reproduce" was measured before
   its last rebase. The charter's premise ("something that landed after `924017c8`") holds, but the
   first mover landed **before** D94 merged, not after.

## 2. WHY THE CENSUS CANNOT SEE THIS: THE STRUCTURAL GAP

The census counts a record as reproducing under **either** of two constructions: the surface at its
declaration, or HEAD's live surface. That covers D79's designed re-key only for a record solved **while
its ISO's surface sat at declaration**. Once the surface moves, such a record still reproduces at
declaration.

**The two d94 legs are the first committed records ever solved on a moved surface.** There are 10
committed `solve_surface.json` files, and the other eight record `moved: {}`. A record that carries a
historical block matches neither construction as soon as its ISO's surface moves again.

**This will recur, and it will not stay rare.** Since `5f8d153c`, **every** ISO's surface is off
declaration (6–10 rows each). So every solve from now on records a non-empty block, and it will turn
`G1_UNKNOWN` at that ISO's next surface move. **D96 is directly exposed:** its `neiso-t3` legs solve
at a later pin. D96 had not landed on `main` at `645f5e0c`, so there was nothing of it to check.

## 3. PART 2 — DISPOSITION (c): REPORTED FOR AN OWNER CARD, NOTHING ENCODED

* **Which rows moved, and which ISOs re-key:** the table in §0. `RGGI_MEMBER_STATES_BY_YEAR` and the six
  COAL-SUB rows re-key all nine ISOs. The PJM RGGI rows re-key PJM.
* **Does an existing exception class cover it?** **No.** The recipe key `surface` accepts only
  `"declaration"` or `"live"`. `vintage` AST-extracts `scenarios.py` alone and models no surface: at the
  pin its key is the at-declaration `f04fd063…`, not the literal. `lag`, `pre-ledger-flip` and
  `split-root` each act on fields or roots.
* As the charter directs, I **invented no class**, **appended nothing** to
  `key-provenance-exceptions.json`, and **added no lag-table row**, since this is not a field lag.
* **The card to put to the owner:** *"Should the key-provenance census accept a third construction:
  the record hashed with the `moved` block from its own committed `solve_surface.json`?"* A zero-code
  probe, run over all 10 committed `solve_surface.json` bundles, measured:
  * **9 of 10 reproduce** under it. The tenth is `ff-t3-neiso-golden/d90-rescore`, which is already a
    reported Q66 `LAG` (seam undrop) and is unaffected.
  * **Both d94 legs reproduce** under it.
  * **The eight bundles with `moved: {}` are unchanged**, because the construction then collapses to
    the at-declaration key.
  * It needs **no** new data: the evidence is committed next to every bundle since D79.
  * **What it cannot cover:** a record with no `solve_surface.json`. That is every pre-D79 bundle, and
    none of those was solved on a moved surface.

  **The alternative is to do nothing.** The census then goes red once per ISO surface move for every
  post-`5f8d153c` record, and each time a lane like this one is needed to clear it.

**OWNER (live): the owner, via a capx director card (next free Q).** Until it is ruled on, the two
residuals stay `G1_UNKNOWN`, and so does every future record of this class.

## 4. BOUNDARIES

* Zero LP.
* No edit under `src/`, `scripts/` or `docs/governance/`. No `ScenarioConfig` field touched, no surface
  row re-declared (D79 assigns that to the ISO lanes), no exception or lag row added.
* Rule 27 does not fire: no pushed file is 300 lines or more.
* Probe scripts lived only in the session scratchpad. The method is reproducible from §1:
  `scripts.lib.key_provenance.head_key(payload, surface=True)` with `moved_rows` set to the recorded
  block.
