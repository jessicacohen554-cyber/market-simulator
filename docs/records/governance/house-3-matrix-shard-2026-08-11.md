# HOUSE-3 — Mechanism-matrix per-ISO sharding + backcast generated-preview un-tracking (2026-08-11)

> Session: FABLE, manager dispatch (sitting Addendum AJ.2). NO model behaviour
> changed: every edit is docs-data, a CI guard script, a site loader, or
> `.gitignore`. NO solve, NO keeper contact, NO `ScenarioConfig` change, NO
> matrix verdict change — this lane moved where verdicts LIVE, never what they
> say (proof in §2).

## The manager's sentence

**YES — two ISOs can now discharge rule 28 concurrently with ZERO shared-file
edits.** A lane's rule-28(b)/(e) duty (cell verdict + `fc` + `ev` citation +
per-ISO note + keeper/gates stamps) is a one-file edit to
`docs/codebase-site/data/mechanism-matrix/<ISO>.js`; no other lane's duty
touches that file. The single deliberate exception is rule 28(c): the PR that
ADDS a new mechanism writes the base row plus one cell line in every shard —
by design that happens once, in the field-adding PR, not in per-ISO lanes.

**The one-line instruction a future lane follows to discharge rule 28:**

> Edit ONLY `docs/codebase-site/data/mechanism-matrix/<ISO>.js` — set your
> mechanism's `cell:` (and `fc:`/`ev:`/`note:`), bump the shard's `updated:`,
> and on a keeper promotion re-stamp the same file's `keeper:`/`gates:`; add
> new-mechanism rows (base + all six shards) only in the PR that adds the
> `ScenarioConfig` field.

## 1. Shape before / after, and the collision evidence

**Before** (one file, `docs/codebase-site/data/mechanism-matrix.js`, 2,556
lines / 1.3 MB): each of the 211 rows packed all six ISOs into two six-char
strings on ONE line — `cells: "KKKKKK"`, `fc: "OOOOOO"`, position = ISO — plus
a mixed-ISO `ev:` object and a shared `keepers:`/`gates:` header. So a PJM
lane and a MISO lane updating DIFFERENT ISOs' verdicts for the same mechanism
edited the same character of the same line. 21 distinct lanes touched the file
2026-08-08..10; the MISO leg alone took three union-merges (b9232406,
bb1d8e32, afc706b4) and one edit was silently LOST then restored (c5593684).

**After** (mirroring the 2026-07-19 keeper sharding —
`frontend/data/backcast/keepers/README.md`, the binding precedent):

- **Base** `docs/codebase-site/data/mechanism-matrix.js` —
  `window.MECH_MATRIX_BASE`: `version/updated/isos/categories` + one row per
  mechanism carrying only mechanism-level content (`id/cat/name/def/mode/note`
  and genuinely cross-ISO `ev` keys such as `All`). The pre-shard header's
  mixed-ISO stamp log is kept verbatim, frozen behind an explicit marker.
  Edited once per mechanism, by the rule-28(c) PR.
- **Shards** `docs/codebase-site/data/mechanism-matrix/<ISO>.js` —
  `window.MECH_MATRIX_SHARDS.<ISO>`: `iso/updated/keeper/gates` + a `cells:`
  map with ONE LINE PER MECHANISM:
  `mech_id: { cell: "K", fc: "O", ev: "…", note: "…" },` (`fc`/`ev`/`note`
  optional; a missing `fc` means forecast posture = the backcast cell, the
  legacy row-level convention applied per ISO). Unknown/n-a stays expressible:
  `.` is n/a, `U` untested — the CI guard requires every shard to cover the
  full base id set explicitly, so a forgotten cell can never silently render.
  Per-ISO column re-stamp history goes at the END of the owning shard;
  the pre-2026-08-11 history stays in the base's frozen log.
- **Assembler** `docs/codebase-site/data/mechanism-matrix-assemble.js`
  reconstitutes the legacy `window.MECH_MATRIX` monolith shape client-side;
  `scripts/lib/mech_matrix.py` (new, stdlib-only) is its Python twin —
  `load_merged()` returns exactly the old shape, mirroring
  `keeper_store.load_merged()`.

Mechanical `ev`-key normalization, values untouched: two legacy per-ISO key
spellings (`MISO:`→ the MISO shard, `NE:`→ the NEISO shard) fold into their
canonical letters; non-per-ISO keys (`All`, `F`, `A`, one `evidence` string)
stay on the base row. No citation was deleted anywhere.

## 2. Byte-faithfulness proof (the gate on this lane)

The migration is mechanical, not editorial. The base file was produced by
**surgical span removal** from the pre-shard monolith (parse with source
spans, cut only `keepers:`/`gates:`/`cells:`/`fc:`/per-ISO-`ev` spans), so
every kept byte — notes, comments, layout — is the original byte; shards were
emitted from the parsed per-ISO values.

Proof, three layers, all run against the real pre-shard file:

1. **Parser equivalence:** the Python JS-subset parser's read of the whole
   1.3 MB monolith is `==` Node's evaluation of the same file (exact dict
   equality, all 211 rows).
2. **Round-trip identity (committed as a standing test):**
   `tests/unit/config/test_mechanism_matrix_shard_migration.py` freezes the
   pre-shard monolith as `tests/fixtures/mechanism_matrix_preshard_2026-08-11.js.gz`
   and asserts `assemble(split_monolith(fixture))` reproduces it EXACTLY per
   mechanism × ISO — cells and fc characters verbatim row-by-row, every `ev`
   citation value byte-identical, keepers/gates stamps identical. 7 tests.
3. **Committed-files + browser-path verification (run at migration, recorded
   here):** `scripts.lib.mech_matrix.load_merged()` over the COMMITTED base +
   shards is canonically equal to the pre-shard parse
   (`canonical(load_merged()) == canonical(pre-shard)` → True), and Node
   loading base + 6 shards + `mechanism-matrix-assemble.js` — exactly what the
   page does — produced `window.MECH_MATRIX` with **0 of 211 rows differing in
   cells or fc strings**, identical keepers and gates. 1,266 (mechanism × ISO)
   cells carried, zero verdict changes.

Had any cell changed value, the instruction was stop-and-report; none did.

## 3. Consumer inventory (what reads the matrix, and how each was verified)

| Consumer | Change | Verified how |
| --- | --- | --- |
| `scripts/check_mechanism_matrix.py` (CI guard, `mechanism-matrix-guard` job) | Parses base + shards via `scripts/lib/mech_matrix`; integrity = base rows well-formed **+ every shard covers exactly the base id set with 1-char K/R/I/G/O/U/. verdicts**; failure messages name the base or ISO-shard file to edit; keeper-stamp guard reads the shards' `keeper:`; mention-checks (28(c) diff gate, both shrink-only ratchets, CLI advisory) search base+shards concatenated; anchors checked per-file with per-file `--fix-anchors`; enforced half (new-`ScenarioConfig`-field-needs-a-row) STAYS enforced | Validate mode green (integrity OK, keeper stamps match, 238 anchor warnings — byte-identical count to origin/main's pre-shard state, i.e. zero new drift); diff-gate `--base origin/main` green; negative tests: a deleted shard line and a bad verdict char both FAIL naming `mechanism-matrix/ERCOT.js` |
| `docs/codebase-site/mechanism-matrix.html` (renderer) | Loads base + 6 shards + assembler; renderer IIFE unchanged except a per-ISO-notes line in the expanded note | Node-simulated the exact script sequence: assembled `window.MECH_MATRIX` has identical `isos/keepers/gates/categories` and 211 rows with byte-identical `cells`/`fc` strings and all `ev` values vs the pre-shard file, so the table renders identically (only in-row evidence-key ORDER can differ: cross-ISO keys now precede per-ISO letters) |
| `scripts/mechanism_matrix_gap_sweep.py` (writes the ratchet baseline) | Row cells via `load_merged()`; per-row mention blob = base chunk + that row's shard ev/notes; whole-store blob = base + shards | Ran `--iso NYISO`: columns still closed (0 absent / 0 prose / 0 armed-no-cell / 0 shared-gap), matching the committed baseline; checker-vs-sweep parity pinned by the existing `test_mechanism_matrix_shared_ratchet.py` (23 matrix tests green) |
| `scripts/prune_iso_runs.py` (advisory citation scan) | Advisory files = base + shard dir (run-id citations live in shard `ev` now) | Code path reuses the existing dir-scan branch, extended to `*.js` |
| `.claude/hooks/mechanism-matrix-reminder.sh` (SessionStart) | Duties re-pointed at `mechanism-matrix/<ISO>.js`; `updated` = freshest stamp across base + shards | Executed: prints sharded guidance, exit 0 |
| `.github/workflows/ci.yml` | Trigger paths + `docs/codebase-site/data/mechanism-matrix/**` | Path filter addition only; guard job command unchanged |
| Docs that say WHERE to write | `CLAUDE.md` rule 28 (WHERE only — duties unchanged), `docs/mechanism-testing-matrix.md` §1 protocol + header, `docs/README.md` index row | Re-read; every write-path reference now names the shard |
| Tests | `test_mechanism_matrix_keeper_stamp.py` rewritten to the shard API; `test_mechanism_matrix_shared_ratchet.py` reads `matrix_all_text()`; new `test_mechanism_matrix_shard_migration.py` | 23 passed; full `tests/unit/config` 494 passed |

Non-consumers left alone: `scripts/_miso148_merge_matrix.py` (the miso-148
union-merge repair one-off — historical evidence of the collision problem,
obsolete for the sharded store) and `scripts/probes/*` that merely cite the
matrix in prose.

## 4. Second surface — backcast generated preview files un-tracked

`frontend/data/backcast/{manifest,benchmark,completeness}.js` are now
**gitignored and removed from tracking** (`git rm --cached`), mirroring the
proven forecast-namespace pattern (`.gitignore` §6a, deploy as single writer).

**Deploy-dependency finding (read `.github/workflows/deploy-pages.yml`):** the
deploy does NOT depend on the committed copies in any way. It stages the
checkout into `_site` and then runs `scripts/build_manifest.py --site-dir
_site`, which REGENERATES all three files into
`_site/frontend/data/backcast/` from the committed registry sidecars + bench
parts, BEFORE `scripts/build_codebase_site_backcast.py` reads them — and it
reads them from `_site`, not from the repo. So the committed copies were
overwritten on every deploy and served only the raw-checkout `file://`
preview; four lanes still paid merge cost on them in two days.
**Local `file://` preview now requires running `python scripts/build_manifest.py`
first, exactly as the forecast side already does** (verified locally: it
rebuilt all three from the 66 committed sidecars). `rubric-consts.js` is also
deploy-regenerated but was NOT in this dispatch's scope and stays tracked.

## 5. Third surface — scenarios.py insertion convention (documentation only)

`_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` are
legitimately shared (9 lanes in two days) and were NOT restructured. Their
header comments now state the collision-minimising insertion rule: order is
semantically irrelevant (the hash sorts), so new entries land **by ISO
cluster** — end of your ISO's run of entries, shared fields at the very end,
legacy entries never reordered — so two field-adding lanes for different ISOs
insert on different lines. Same discipline in both containers, same commit.
`scripts/check_cache_key_registration.py` verified green after the edit
(160 registered, all defaults match HEAD).

## 6. Files touched

Data: `docs/codebase-site/data/mechanism-matrix.js` (base),
`docs/codebase-site/data/mechanism-matrix/{ERCOT,CAISO,PJM,MISO,NYISO,NEISO}.js`
(new), `docs/codebase-site/data/mechanism-matrix-assemble.js` (new).
Lib/guard: `scripts/lib/mech_matrix.py` (new), `scripts/check_mechanism_matrix.py`,
`scripts/mechanism_matrix_gap_sweep.py`, `scripts/prune_iso_runs.py`.
Site: `docs/codebase-site/mechanism-matrix.html`.
Hook/CI: `.claude/hooks/mechanism-matrix-reminder.sh`, `.github/workflows/ci.yml`.
Tests: `tests/unit/config/test_mechanism_matrix_shard_migration.py` (new),
`tests/fixtures/mechanism_matrix_preshard_2026-08-11.js.gz` (new),
`test_mechanism_matrix_keeper_stamp.py`, `test_mechanism_matrix_shared_ratchet.py`.
Untracking: `.gitignore` + `git rm --cached` of the three backcast preview files.
Docs: `CLAUDE.md` (rule 28 WHERE reference), `docs/mechanism-testing-matrix.md`,
`docs/README.md`, `CHANGELOG.md`, this handoff.
`src/market_sim/config/scenarios.py`: comment-only (§5).
