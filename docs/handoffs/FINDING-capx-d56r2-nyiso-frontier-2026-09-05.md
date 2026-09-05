# FINDING — capx D56-R2: NYISO `frontier` RE-DECLARED on `2026-09-05-nyiso-189-steam-identity` (owner ruling Q39) — the four-instrument alignment reads {ERCOT, NEISO, NYISO, PJM} on every leg; NOTHING is spent, NOTHING is solved — 2026-09-05

**Lane:** D56-R2, capacity-expansion track, GOVERNANCE RECORDS lane (pack §D56-R2; capx
ledger §0ah.3 / §4, "ISSUED r#37"). **Model:** Fable (a marker consequence). **Branch:**
`claude/capx-d56r2-nyiso-frontier-6b5xmj`, fresh off `origin/main` `ee7754c1`, rebased onto
`8342d74d` before the push; every provenance pin below names `8342d74d`, the sha the keeper,
marker and verdict were RE-READ at after that rebase (desk doctrine X-6b).
**Scope:** RECORDS ONLY — zero LP, zero solve, zero re-score, zero registration, no keeper
change, no promotion field touched, no out-of-training year touched in any way.

---

## 0. The result in one paragraph

`keepers/NYISO.json` carries a live `frontier` block again — declared 2026-09-05 on
`2026-09-05-nyiso-189-steam-identity` (`keeper_at_declaration`), `by` the Q39 ruling verbatim,
in the ERCOT/PJM/NEISO shape and NYISO's own 2026-08-23 field layout — with the reverted
2026-08-23 ratification (its 2026-08-30 currency annotation and `reverted_2026-08-30` record
inside it) preserved WHOLE beneath it as `frontier_withdrawn_2026_08_30`, one dated
`superseded` field appended, nothing deleted. `calibration-complete.json`'s
`complete.NYISO.frontier_basis` is rewritten from NONE CLAIMED to the declaration with the
prior text carried as a dated "WAS:" clause; every other byte of the entry, every other ISO,
`withdrawn`, `final` and `intake_log` are asserted identical. `scripts/audit_keepers.py --iso
NYISO` PASS (its S1 sync check asked for `build_status.py --iso NYISO`, which was run: only the
status part's `keeper.frontier` block and timestamp moved, the determination did not);
`check_gate_a_provenance.py` OK 6/6 with **no gate-(a) leaf moved — frontier is not a gate-(a)
input**; `check_mechanism_matrix.py` OK without a shard re-stamp. **The four-instrument test
(frontier · `complete` · gate-(a) · ISO-level determination) reads {ERCOT, NEISO, NYISO, PJM}
on all four instruments at `8342d74d`** — the split the D56-R finding §6 recorded on the
frontier leg alone is closed by the owner's choice. **This lane spent NOTHING and solved
NOTHING.**

---

## 1. The ruling, verbatim, with its provenance

**Q39** (capx ledger §3, ruled 2026-09-05 at r#37 on card C-10): *"RULED 2026-09-05 (r#37) —
RE-DECLARE FRONTIER ON nyiso-189 (both instruments, as the withdrawal removed both)."* Ledger
§0ah.3: *"Q39 (C-10): RE-DECLARE `frontier` on nyiso-189 too — both instruments, as the
withdrawal removed both. → D56-R2 (records lane)."* Card C-10 (ledger §0ag.5): the director's
recommendation, as owner ruling R-AG asked, was option **A** — *"re-declare `complete` AND
`frontier` together on nyiso-189"* — over B (`complete` only, frontier read as optional) and C
(decline both); the option served live is labelled *"Re-declare frontier on nyiso-189"* (pack
§D56-R2). The `complete` half was executed first by D56-R (PR #4763, Q38) with the frontier
leg left split "by the owner's pending choice"; this lane is the frontier half.

**What the lane decides: nothing.** The 2026-08-30 reversion's stated cause (`keepers/NYISO.json`
`reverted_2026-08-30.by`: *"NYISO is not frontier it was reverted bc it's not yet"*) was that the
designated keeper read NOT-YET and the `complete` marker had been withdrawn under the Q5
uniform rule — not a merits finding against the exhaustion claim. Both causes are gone (the
keeper lineage reads CALIBRATED since nyiso-188/189; `complete` re-declared by Q38), and the
owner has ruled the frontier back with the marker. The declaration's basis is therefore the
restored 2026-08-23 ratification's basis, `ASSESSMENT-nyiso154-frontier-2026-08-22.md`
§3/§2/§4, carried by the record (every promotion since — nyiso-155/157/159/177/185/186/187/188/
189 — a measured-input or identity repair with a stated G-DELTA and zero free parameters; the
rejections nyiso-190/191 standing alongside). The lane re-adjudicates no merit and moves no
cell verdict.

---

## 2. Step 1 — the artifact-only re-verification (run first, and again after the rebase)

`keepers/NYISO.json` `keeper` = `2026-09-05-nyiso-189-steam-identity` at `ee7754c1` and again
at `8342d74d` (the one upstream merge in the window, #4775 capx D57, touched two `src/`
constants files and nothing in `frontend/data/backcast/`, the log, or the ledger).
`python3 scripts/calibration_verdict.py --run-id 2026-09-05-nyiso-189-steam-identity` at both
pins, identical output:

| criterion | tier | status | detail |
|---|---|---|---|
| C1 fuel-mix by class | LOAD | PASS | 14/14; D-10 free 10/10 (pinned CC_CHP, ST_CHP) |
| C2 system volume | LOAD | PASS | |
| C3a mean LMP | LOAD | PASS | +4.9 / +1.7 / −8.3 % vs ±10 % |
| C3b price shape | LOAD | PASS | 0.119 / 0.166 / 0.177 vs ≤0.20 |
| **C3c price tail (RT hourly)** | SUPP | **CAVEAT [ledgered]** | model 3 / 0 / 4 h vs actual 10 / 13 / 42 h > $300 — ACCEPTED MODEL-CLASS LIMITATION, rubric v3.3 standing rule; NOT a PASS; 1 of 1 ledgerable slot |
| C4 dispatch correlation | SUPP | PASS | |
| C6 governance | PROT | PASS | attested, computed premises |
| C8 forced-energy share | PROT | PASS | |
| **Determination** | | **CALIBRATED** | grade 7 of 8, fails 0, 1 ledgered caveat |

The charter's premise (a CALIBRATED keeper; never a frontier on a NOT-YET keeper) holds. The
keeper did not move; the D-5(b) branch of step 1 was not needed.

---

## 3. Before/after — every changed field, both surfaces (the Q5-W §3 format, inverted)

### 3.1 `frontend/data/backcast/keepers/NYISO.json`

Serializer: the file's own — `json.dumps(obj, indent=2, ensure_ascii=True)` + trailing
newline (byte round-trip of the pre-edit file verified before editing). Edited on the parsed
object; every key other than `frontier` re-emitted from the SAME object (asserted by identity),
and the preserved block's contents asserted byte-verbatim against the pre-edit serialization
before its one appended field.

| Field | Before (`ee7754c1` = `8342d74d` for this file) | After |
|---|---|---|
| key order | iso · keeper · promotion_note · determination_note · de_designation_history · superseded · **frontier** · frontier_cleared · site_retention_note | iso · keeper · promotion_note · determination_note · de_designation_history · superseded · **frontier** · **frontier_withdrawn_2026_08_30** · frontier_cleared · site_retention_note |
| `frontier` | the 2026-08-23 ratification block carrying `withdrawn: "2026-08-30"`, `keeper_at_withdrawal`, `withdrawn_note` (the 2026-08-30 auditor's machine-readable mirror), `currency_annotation_2026-08-30` and `reverted_2026-08-30` — 13 fields; `frontierActive()` FALSE | **NEW live block, 8 fields in the ERCOT/PJM/NEISO shape + NYISO's own 08-23 layout:** `declared` 2026-09-05 · `keeper_at_declaration` nyiso-189 · `by` = Q39 verbatim (§3 + §0ah.3) with the C-10 option label and the D56-R / D56-R2 split · `note` = what it is (the exact inverse of the 2026-08-30 withdrawal, both causes gone), what it CLAIMS (the 08-23 basis carried by the record), what it does NOT claim (C3c ledgered at full magnitude, the winter locational premium blocked on identification, the handed-forward objects still open, no out-of-training year touched, NOT `final`), the four-instrument alignment statement, DECLARATIVE ONLY · `basis` = Q39 restoring ASSESSMENT-nyiso154 §3/§2/§4 on the re-verified keeper · `supersedes` = the 2026-08-30 reversion, with the five-layer genealogy (declared 07-31 → cleared 08-06 → ratified 08-23 → reverted 08-30 → re-declared 09-05) · `not_final` (unchanged in substance: `final` EMPTY, freeze ACTIVE on the locked tier, 2019/H1-2026 NEVER GRANTED, NOT-YET on the merits) · `recorded_by` (the lane, what it did not touch). NO `withdrawn` key ⇒ `frontierActive()` TRUE |
| `frontier_withdrawn_2026_08_30` | — | the former `frontier` block **MOVED WHOLE**, byte-verbatim (asserted), plus ONE appended dated field `superseded` ("SUPERSEDED 2026-09-05: NYISO `frontier` RE-DECLARED … retained WHOLE as the historical record … its `withdrawn` / `withdrawn_note` fields remain exactly as written and no longer govern the badge because `frontierActive()` reads `keeper.frontier`") — the D56-R nesting precedent (`prior_withdrawal_2026_08_30.superseded`) |
| `keeper`, `promotion_note`, `determination_note`, `de_designation_history`, `superseded`, `frontier_cleared`, `site_retention_note` | — | **byte-identical** (same objects re-serialized) — the owner's NYISO backcast lane's promotion fields untouched |
| blob | `19ff577be1f0`, 31,261 bytes / 96 lines | `1c18e0167016`, 40,050 bytes / 107 lines |

Reader check: `docs/codebase-site/js/calibration-status.js` `frontierActive()` returns
`!!(frontier && frontier.declared && !frontier.withdrawn)` → TRUE on the new block; the
sibling `frontier_withdrawn_2026_08_30` is read by nothing (`keeper_store`, `build_status`,
`audit_keepers`, the matrix checker all read `frontier` only; `keeper_store.write_keeper`
preserves unknown keys, `tests/scoring/test_keeper_store.py` pins that).

### 3.2 `frontend/data/backcast/calibration-complete.json`

Serializer: the file's own — `json.dumps(obj, indent=1, ensure_ascii=False)`, no trailing
newline (round-trip verified). Byte-identity asserted programmatically for `intake_log`,
`final`, `withdrawn` (CAISO alone), `complete.ERCOT`, `complete.NEISO`, `complete.PJM`, every
`complete.NYISO` field other than `frontier_basis` (the nested `prior_withdrawal_2026_08_30`
included), top-level key order and `complete` key order.

| Field | Before | After |
|---|---|---|
| `complete.NYISO.frontier_basis` | "NONE CLAIMED by this declaration. … card C-10 … is UNRULED in ledger §3 at origin/main 921bb4cd (no Q39 row exists) … the four-instrument alignment … stays SPLIT ON THE FRONTIER LEG PENDING THE OWNER'S CHOICE … If Q39 rules option A, the executing session re-declares `frontier` in the shard and rewrites this field to name it" | "DECLARED 2026-09-05 on keeper 2026-09-05-nyiso-189-steam-identity (= keeper_at_declaration) by OWNER RULING Q39 (capx ledger §0ah.3 / §3 Q39 … verbatim …; option selected 'Re-declare frontier on nyiso-189'), executed by governance records lane D56-R2 as the exact inverse of the 2026-08-30 withdrawal … The live declaration is keepers/NYISO.json `frontier` … FOUR-INSTRUMENT ALIGNMENT … reads {ERCOT, NEISO, NYISO, PJM} on all four at that pin … Frontier is a declarative badge: it grants NO tier (… NOTHING is spent), it is not a gate-(a) input (no forecast-board leaf moves), it is not `final` … **WAS (2026-09-05, D56-R, before Q39 was ruled): '<the prior text, verbatim and whole>'**" |
| top-level `note` | ended "… `frontier` NOT re-asserted (card C-10 / Q39 pending — the frontier leg of the four-instrument alignment stays split by the owner's pending choice, stated, never silent)." | **appended** (dated, `\|\|`-separated as the file's own convention): FRONTIER RE-DECLARED 2026-09-05 (Q39; D56-R2) on the same keeper — both instruments back; where the block lives; alignment on every leg; frontier grants no tier, `final` and the freeze untouched; "The pending-choice sentence above is superseded by this one." (Not in the charter's byte-identity list; appended rather than left stale, disclosed here.) |
| everything else | — | **byte-identical**, asserted |
| blob | `8107a141973a`, 157,317 bytes / 282 lines | `d50684315d8c`, 159,325 bytes / 282 lines (283 by `grep -c`, no trailing newline either side) |

### 3.3 `frontend/data/backcast/status/NYISO.js` — regenerated because the auditor asked

`audit_keepers.py --iso NYISO` FAILED its S1 sync check after the shard edit ("stale vs the
current verdicts … re-run: python scripts/build_status.py --iso NYISO"), because the status
part embeds the shard's `frontier` block (`build_status.py` attaches it AFTER `determine()`
runs). Rebuilt with `build_status.py --iso NYISO`; leaf-diff against the HEAD part: `generated`
(timestamp) and `keeper.frontier.*` ONLY — the determination, every criterion row, every
other keeper field unchanged. `shared.js` re-emitted byte-identical (not in the diff). Blob
`0e3b13b3baea` → `1eddbb8e71b1`. Regenerated, not hand-edited.

### 3.4 NOT touched, by design

`frontend/data/forecast/program-status.json` — frontier is not a gate-(a) input, so no leaf
moves: `isos.NYISO.gate.a_keeper_marker` stays `pass` on the D56-R derivation
(`read_live_at` `921bb4cd`), `gate_a_provenance` untouched, guard OK 6/6. Its D56-R detail
sentence "the frontier leg stated as split pending C-10" is now historical — flagged (§7), not
edited. `docs/codebase-site/data/mechanism-matrix/NYISO.js` — the checker did not ask (keeper
stamps and §5.x headers match; the shard's `gates` stamp sentence "frontier NOT re-asserted
(card C-10 / Q39 pending)" is likewise historical, flagged). `holdout-freeze.json`, `final`,
every registry sidecar, bench, bundle, `ff-verdicts.json`: untouched.

---

## 4. Four-instrument alignment — RE-READ AT `8342d74d`, ALL FOUR {ERCOT, NEISO, NYISO, PJM}

Derived programmatically from the live files (frontier = shard `frontier.declared` present
and `frontier.withdrawn` absent; `complete` = marker block keys; gate-(a) =
`program-status.json` `isos.<ISO>.gate.a_keeper_marker.status == "pass"`; determination =
`status/<ISO>.js` `keeper.iso_determination` else `keeper.determination`, fail-closed on
null):

| instrument | membership at `8342d74d` (after this lane) | source |
|---|---|---|
| `frontier` in `keepers/<ISO>.json` | **{ERCOT `2026-08-31`, NEISO `2026-07-11`, NYISO `2026-09-05`, PJM `2026-07-31`}** | keeper shards (NYISO: this lane) |
| `complete` marker | **{ERCOT, NEISO, NYISO, PJM}** | `calibration-complete.json` (membership unchanged since D56-R) |
| gate-(a) `status: pass` | **{ERCOT, NEISO, NYISO, PJM}** — guard OK 6/6 | `program-status.json` (untouched) |
| ISO-level determination CALIBRATED | **{ERCOT, NEISO, NYISO, PJM}** (CAISO NOT-YET, MISO NOT-YET) | `status/<ISO>.js` |

**ALIGNED.** The D56-R table (§6 there) had {ERCOT, NEISO, PJM} on the frontier leg against
{ERCOT, NEISO, NYISO, PJM} on the other three, "split by the owner's pending choice". Q39 was
that choice. Stated here for the audit desk (its Z-4 row and the v27 "FOUR-INSTRUMENT
ALIGNMENT" section); the audit board is not this lane's to edit.

`final` is still `_note` only; the freeze file is untouched; `holdout_policy` re-read from the
live marker: NYISO validation True / locked_test False (both unchanged from D56-R), ERCOT /
NEISO / PJM True / False, CAISO / MISO False / False, `frozen_tiers` = {locked_test}. **A
frontier badge grants no tier; nothing is spendable that was not already spendable, and
nothing was spent.**

---

## 5. Auditor, guard and test outputs (run after the edits, again after the rebase + re-stamp)

| Check | Result |
|---|---|
| `scripts/audit_keepers.py --iso NYISO` | **PASS — 0 failures, 0 warnings** (M1a/M1b hold; S1 asked for the status rebuild once, satisfied) |
| `scripts/audit_keepers.py --check` (CI form) | PASS 0/0, exit 0 |
| `scripts/check_gate_a_provenance.py` | **OK 6/6** — no gate-(a) leaf moved; frontier is not an input to it |
| `scripts/check_mechanism_matrix.py` | integrity OK; keeper stamps + §5.x headers match every shard — no re-stamp requested |
| `scripts/build_status.py --check` | in sync (6 keepers) after the NYISO rebuild |
| `scripts/legitimacy_diagnostics.py --keepers --no-d2-recompute` | exit 0 — Overall PASS; D-9 PASS; **D-6 holdout quarantine PASS over all registered bundles** |
| `scripts/check_registry_payload_parity.py` | OK (66 runs, 108 bundle dirs, 0 tolerated) |
| `scripts/check_forecast_staleness.py` | its pre-existing WARN (25 never-re-scored stamps) only, untouched by this lane |
| `pytest tests/scoring/{test_keeper_store,test_audit_keepers,test_gate_a_provenance,test_ff_readiness_battery,test_holdout_year_gate}.py -m "not integration"` | **100 passed**, 4 deselected — no test pin references the frontier set, so none moved |

---

## 6. What this lane did NOT do

- **Solved NOTHING.** No LP was built; no year of any tier was solved, scored or registered.
- **Spent NOTHING.** No NYISO year outside 2023–2025 exists in any sidecar, bench or bundle
  (D-6 PASS above); the validation tier's authorization is exactly as D56-R left it; the locked
  tier is untouched, never granted, and frozen for every ISO.
- Touched no keeper promotion field, no registry, bundle, bench, `ff-verdicts.json`,
  `holdout-freeze.json`, `program-status.json` or `final` byte; moved no matrix cell verdict;
  armed or disarmed no mechanism; edited no other ISO's file (rule 25).
- Re-adjudicated no merit of the frontier claim; decided nothing — Q39 is the owner's.

---

## 7. Flagged, not edited

1. `program-status.json` `isos.NYISO.gate.a_keeper_marker.detail` + `d56r_nyiso_redeclaration`
   block and the NYISO matrix shard's `gates` stamp all say "frontier … pending C-10 / Q39" —
   true at their own pins, historical now; neither surface is a gate-(a) input or a checker
   ask, so left for their owning desks' next refresh (the D7 / Q5-W discipline).
2. The capx ledger's D56-R2 row (§4 "ISSUED r#37") and the audit board's Z-4 / v27 alignment
   section — the directors' own documents; their LANDED / ALIGNED stamps belong to their next
   refreshes, on this finding.
3. `docs/codebase-site/model-validity.html`'s dated membership sentence — self-dating prose;
   no precedent lane edited it.
4. `keepers/NYISO.json` `promotion_note` still says "NO MARKER IS REQUESTED: NYISO holds
   neither `complete` nor `final` (D56 issued, not landed)" — the owner's backcast lane's
   field, true at its writing; not this lane's to touch.

---

## 8. Push verification (rule 27 — every edited data file, `git push` transport)

Single-commit pack on `claude/capx-d56r2-nyiso-frontier-6b5xmj`, base `8342d74d`. Each pushed
blob fetched back through the GitHub contents API on the branch ref and compared to the local
`git hash-object` — see the table stamped below after the push.

| file | local blob | remote blob | bytes / lines |
|---|---|---|---|
| `frontend/data/backcast/keepers/NYISO.json` | `1c18e0167016` | _(filled after push)_ | 40,050 / 107 |
| `frontend/data/backcast/calibration-complete.json` | `d50684315d8c` | _(filled after push)_ | 159,325 / 282 |
| `frontend/data/backcast/status/NYISO.js` | `1eddbb8e71b1` | _(filled after push)_ | 39,438 / 1 |
