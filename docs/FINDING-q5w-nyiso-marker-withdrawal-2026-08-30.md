# FINDING — Q5-W: NYISO `complete` marker WITHDRAWN (CAISO precedent, uniform) — 2026-08-30

**Lane:** Q5-W governance records lane (chartered at the capx director's refresh-#12
decision card, `docs/handoffs/capx-director-ledger-2026-08.md` §0i.2; prompt canonical
in the pack; issuance record ledger §4).
**Scope:** RECORDS ONLY — no LP, no solve, no re-score, no registration, no keeper
change, no out-of-training year touched in any way.
**Branch:** `claude/q5w-nyiso-marker-withdrawal-5yzj0s`, off `origin/main`
`4544d019309c`.

---

## 1. The ruling, verbatim, with its provenance

Owner ruling delivered 2026-08-30 at the capacity-expansion director's refresh-#12
decision card. The option selected on the card, **verbatim label**:

> **"Withdraw the marker (CAISO precedent)"**

Recorded: `docs/handoffs/capx-director-ledger-2026-08.md` §0i item 2 (the refresh's
own record of the ruling) and §3 Q5, whose row now reads: *"RE-RULED 2026-08-30 (r#12
decision card) — WITHDRAW THE MARKER (CAISO precedent), superseding the r#8 WAIT. The
recurrence clause fired (nyiso-157 promotion re-keyed the marker onto a second
consecutive NOT-YET keeper, fail set widened). Written reconciliation, now uniform: a
`complete` marker cannot stand on a NOT-YET keeper; the structural-integrity formula
governs KEEPER promotions only. Execution = lane Q5-W. Re-entry is a new owner
declaration once the keeper again scores CALIBRATED (winter-intake route)."*

Ledger §0i.2 records that the ruling was taken **against the director's
recommendation** (option (i), adopt the standing formula for the marker too) — noted
plainly, per the ledger's own text.

**Genealogy (ledger §3 Q5 + §0e.2 + §0i):** Q5 opened at refresh #6 (2026-08-26) when
the nyiso-155 promotion put a NOT-YET keeper under the `complete` marker — the
identical fact pattern that withdrew CAISO's marker on 2026-08-06 — with the two
precedents pointing opposite ways. Ruled **WAIT FOR WINTER INTAKE** at the r#8 sitting
(2026-08-30), with the recurrence clause governing the next appearance. The clause
**fired the same day**: the nyiso-157 promotion (`2dc64b5`, PR #4323) re-keyed the
marker onto a **second consecutive NOT-YET keeper** with the fail set **widened**
(nyiso-155 {C3a-2025, C3c} → nyiso-157 {C3a-2025 −12.0 %, C3b-2025 0.203 knife-edge,
C3c silenced-lone}). The owner re-ruled at the r#12 card: withdraw.

## 2. The written reconciliation (what Q5 resolves to)

**A `complete` marker cannot stand on a NOT-YET keeper.** The 2026-08-06 CAISO
precedent applies **uniformly** — to every recurrence, whatever produced the NOT-YET:
a rubric re-score (CAISO, rubric v3.1) or a structure-over-gates keeper promotion
(NYISO, nyiso-155/157). The **structural-integrity formula remains the standard for
KEEPER promotions** — nyiso-155 and nyiso-157 stand untouched as keepers, and
`frontend/data/backcast/keepers/NYISO.json` was not touched by this lane — **but it no
longer sustains a `complete` marker** on a NOT-YET determination. The two precedents
no longer contradict: they govern different objects (keeper vs marker).

The rule is also recorded where the marker lives: appended, dated, to the top-level
`note` of `frontend/data/backcast/calibration-complete.json` (§3.1 below).

## 3. Before/after — every changed field, both surfaces

### 3.1 `frontend/data/backcast/calibration-complete.json`

| Field | Before (origin/main `4544d019`) | After |
|---|---|---|
| `complete` membership | {NEISO, **NYISO**, PJM} | {NEISO, PJM} — NEISO and PJM entries **byte-identical**, verified programmatically |
| `complete.NYISO` | 17-field entry: declared 2026-07-31 · keeper `2026-08-30-nyiso-157-par-attribution` · determination NOT-YET (D-5(b) re-verified 2026-08-30) · keeper_at_declaration `2026-07-30-nyiso-100-silretire` · 11-entry rekey_history · frontier/freeze/redeclaration history | **REMOVED** from `complete`; every field carried into the withdrawal record (below) except `keeper_rekey_policy` (standing-policy boilerplate duplicated in the file-level note — a deliberate, enumerated drop; the CAISO precedent entry carries no such field) |
| `withdrawn.NYISO` | The 2026-07-19 phantom-outage withdrawal record (declared 2026-07-13, keeper_at_declaration nyiso-61, `superseded` 2026-07-31) | **NEW 2026-08-30 withdrawal record in the CAISO precedent's field layout**: declared 2026-07-31 · withdrawn 2026-08-30 · keeper_at_declaration `2026-07-30-nyiso-100-silretire` · keeper_at_withdrawal `2026-08-30-nyiso-157-par-attribution` · one_shot_status (nothing spent, verified) · reason (the ruling + basis) · by (r#12 card provenance) · **reentry** (new owner declaration on a CALIBRATED keeper) · original_grant_by / determination_at_withdrawal / locked_test / tier_authorized_at_declaration / redeclaration / freeze_interaction / keeper_at_prior_rekey / determination_at_prior_rekey / **rekey_history (11 entries, verbatim)** / frontier_status / frontier_basis_WITHDRAWN_2026_08_06 / marker_reexamination_open (all carried verbatim) · **`prior_withdrawal_2026_07_19`** = the old 2026-07-19 record **nested whole, byte-verbatim** — nothing erased |
| top-level `note` | ended at the rubric-v3.1 / CAISO-withdrawal sentence | **appended** (dated): the Q5 UNIFORM RULE — "a `complete` marker cannot stand on a NOT-YET keeper" is standing and uniform; the structural-integrity formula governs keeper promotions, never sustains a marker; NYISO withdrawn under it 2026-08-30; re-entry = new owner declaration on a CALIBRATED keeper |
| `withdrawn.CAISO`, `final`, `intake_log` | — | **byte-identical**, verified programmatically |

Schema note: `withdrawn.<ISO>` stays one dict per ISO (the shape
`scripts/ff_readiness_battery.py::_marker_state` reads — `keeper_at_declaration` +
`withdrawn` fields present on the new record). Nesting the prior withdrawal whole
inside the new record is the file's own preservation convention (cf.
`frontier_basis_WITHDRAWN_2026_08_06`, `_withheld_exception_history`) and required no
governance choice the precedent does not cover: the old record already carried its own
`superseded` annotation from the 2026-07-31 re-declaration.

### 3.2 `frontend/data/forecast/program-status.json`

| Field | Before | After |
|---|---|---|
| `generated` | 2026-08-26 | 2026-08-30 |
| `isos.NYISO.gate.a_keeper_marker.status` | **pass** | **fail** — on the withdrawn marker; charter §2.1b(2)(a)'s second condition (an entry in the `complete` block) no longer holds |
| `isos.NYISO.gate.a_keeper_marker.detail` | keeper nyiso-155-hydro-repair; "both charter conditions hold… PASS on the literal test… Q5 tension recorded, NOT this session's to resolve" | rewritten: keeper re-keyed to `2026-08-30-nyiso-157-par-attribution` (the promotion the marker stood on at withdrawal, NOT-YET fail set stated); the withdrawal + ruling citation; the Q5 tension **RESOLVED** the CAISO-precedent way; records-act-not-re-score statement; re-entry condition |
| `…a_keeper_marker.read_live_at` / `corrected_by` | `bcb25217b228` / capx-D7 gate re-score (2026-08-26) | `4544d019309c` / Q5-W marker withdrawal (2026-08-30) — the same derivation-stamp convention the D1/D7 records refreshes used; **no forecast-provenance field names written** (the D7 discipline: no `scored_at_sha`/`scored_at_date`/`schema`/`session`) |
| `isos.NYISO.gate.closed_on` | `["c"]` | `["a", "c"]` (the board-wide 'd'-omission inconsistency left as flagged by D7 — not this charter's to fix) |
| `isos.NYISO.gate.note` | "THE PROGRAM'S LEAD ISO, AND THE ONLY ONE WITH LEGS (a) AND (b) BOTH PASSING… Q5 unresolved… lead position only as durable as its answer" | rewritten: lead dissolved; (a) fail · (b) PASS · (c) fail · (d) none; the three things between NYISO and an open gate; the 2026-08-26 durability warning resolved exactly as written; lead may pass to NEISO on S-4V (ledger §0i.2) |
| `isos.NYISO.marker_complete` | true | false |
| `isos.NYISO.keeper` (display) | `2026-08-25-nyiso-155-hydro-repair` | `2026-08-30-nyiso-157-par-attribution` (re-key to the live designated keeper, the same re-key duty D1/D7 performed; the shard itself untouched) |
| `headline` | "NYISO IS THE FIRST ISO IN THE PROGRAM TO CLEAR THE T1→T2 RUBRIC GATE… (a) PASS · (b) PASS… the only ISO with legs (a) and (b) both passing… Q5, unresolved, and NYISO's lead position is only as durable as its answer" | rewritten: lead dissolved **by owner ruling, not by any re-score**; the uniform rule; leg (b) untouched (still the program's only non-HOLD T1-F); no ISO holds (a)+(b) both; re-entry route; records-act statement |
| `gate_reading` | "Leg (a) passes for the three `complete` members (NEISO, NYISO, PJM)." | that one sentence replaced (two members, NYISO fail on the marker, no ISO holds (a)+(b) both) + one appended not-a-re-score sentence; **everything else in the field byte-unchanged** |
| `sources` | 19 entries | 21 — appended the r#12 ruling citation and this FINDING |
| *(new)* `q5w_marker_withdrawal` | — | records block in the `d7_gate_rescore` convention: note (not a scoring stamp, avoids provenance field names) · lane · derived_at_date/sha · derived_from · what_changed · what_did_NOT_change · flagged_not_edited |

**Untouched on the board, verified programmatically (sort-key JSON equality against
the pre-edit doc):** leg (b) `b_t1f_verdict` (bare `nyiso-t1f` verdict,
PROMOTE-WITH-CAVEATS — no marker moves a bare verdict), legs (c)/(d), NYISO's
`t1f_determination`/fc map/blocking_rows, and the **entire blocks of all five other
ISOs** — including NEISO's, per the S-4V deconfliction instruction (§6).

## 4. The validation-tier consequence — and the verification the task ordered

**NYISO's 2020–2022 touchpoint authorization lapses with the marker** (CLAUDE.md rule
22: validation-tier spends are governed by the `complete` marker +
`--holdout-authorized`; the tier-scoped freeze is UNTOUCHED — `holdout-freeze.json`
not edited, `frozen_tiers` still `{locked_test}`, locked test frozen for every ISO).

Verified post-edit against the live file via `scripts/lib/holdout_policy.py`:

| ISO | authorized(validation) | authorized(locked_test) |
|---|---|---|
| **NYISO** | **False** (was True) | False (unchanged — never authorized) |
| NEISO | True (unchanged) | False |
| PJM | True (unchanged) | False |
| CAISO | False (unchanged) | False |

**Was any NYISO out-of-training year ever solved/registered? NO — verified from the
committed record, not assumed** (the expected answer; no surprise to report):

- All **15** NYISO registry sidecars at HEAD (`frontend/data/backcast/registry/*.json`,
  `iso == "NYISO"`) declare `years` drawn only from **{2023, 2024, 2025}**.
- `frontend/data/backcast/bench/NYISO/` holds exactly `2023.json.gz` / `2024.json.gz`
  / `2025.json.gz`.
- The CI-tier D-6 sweep over **all registered bundles** (§5) confirms the only
  registered out-of-training touchpoints in the repository are **PJM 2022** and
  **NEISO 2022**, each under its own still-standing marker — none for NYISO.
- Timeline cross-check: the spend freeze covered the validation tier for all but the
  marker's last four days (tier-scoped lift 2026-08-26, card 6), and no touchpoint was
  run in the 2026-08-26 → 2026-08-30 spendable window either.

So **nothing was spent under the withdrawn marker and nothing is lost**. The locked
test (2019, H1-2026) was never authorized (NYISO absent from `final` throughout) and
is unaffected.

## 5. Audit + gate results (run in this session, after the edits)

| Check | Result |
|---|---|
| `scripts/audit_keepers.py` (full) | **PASS — 0 failures, 0 warnings.** All six ISO keeper checks pass (NYISO keeper `2026-08-30-nyiso-157-par-attribution` untouched and passing); the `holdout`, `marker` and `status` sweeps pass. **M1 iterates the `complete` block = {NEISO, PJM}: with NYISO absent there is no NYISO entry to verify, exactly as the charter expects.** Nothing else moved. |
| `scripts/audit_keepers.py --check` (CI form) | exit 0 |
| `scripts/legitimacy_diagnostics.py --keepers --no-d2-recompute` (CI quarantine gate) | exit 0 — **Overall PASS**; D-9 overlay quarantine PASS; **D-6 holdout quarantine PASS over all registered bundles** (the two registered touchpoints, PJM 2022 + NEISO 2022, read `authorized one-shot` under their own markers) |
| `scripts/check_registry_payload_parity.py` | OK (56 runs checked, 93 bundle dirs swept, 0 known-unsynced tolerated) |
| `scripts/check_forecast_staleness.py` | exit 0 — the Q5-W records block is **not** read as a re-score (no provenance field names written); its pre-existing WARN about 31 never-re-scored verdict stamps is board state that predates and is untouched by this session |
| `scripts/check_mechanism_matrix.py` | clean (no matrix file touched; no ScenarioConfig field added — rule 28 duties not engaged) |

## 6. Rendering surfaces — checked, and what was (not) rebuilt

Per the charter: rebuild exactly what the CAISO withdrawal precedent rebuilt, nothing
more. Checked at HEAD:

- **`scripts/build_status.py` does not read `calibration-complete.json`** (verified:
  it scores `keepers/<ISO>.json` shards through `calibration_verdict.determine()`,
  which also never reads the marker file). The CAISO withdrawal commit (`0a42a13a`,
  2026-08-06) rebuilt `status/*.js` because that same commit changed the **scorer**
  (rubric v3.1) — the marker move itself forces no status rebuild. This lane changes
  no scorer and no keeper shard, so **no `status/*.js` rebuild is owed, and none was
  run**.
- The forecast board (`program-status.json`) is the one live surface that bakes the
  marker into a verdict — flipped in this same session (§3.2), which is the charter's
  point.
- `docs/codebase-site/data/backcast/` and the deploy-generated
  `manifest.js`/`completeness.js` are rebuilt by the Pages deploy from the committed
  files (Git & Pushing §3) — nothing to commit.
- `scripts/ff_readiness_battery.py::_marker_state` reads the `withdrawn` block at
  runtime (generated artifact, not committed) — the new record carries the two fields
  it reads (`keeper_at_declaration`, `withdrawn`).

**Flagged, not edited** (each outside this charter, with owner/lane routing):

1. `isos.NEISO.gate.note` on the forecast board still says leg (a) *"passes for THREE
   ISOs — NEISO, NYISO and PJM — the full membership of the `complete` block"* — now
   stale (membership is {NEISO, PJM}). **Left to the NEISO/S-4V lane** per this
   prompt's deconfliction instruction (edit only your own blocks); the corrected
   membership is stated in the board's headline, gate_reading, and the
   `q5w_marker_withdrawal.flagged_not_edited` field.
2. Board `tier_ladder` T1-F row note "All six ISOs HOLD." — stale since the 2026-08-25
   `nyiso-t1f` re-score (PROMOTE-WITH-CAVEATS), pre-existing, names no marker.
3. `docs/codebase-site/model-validity.html` carries *"As of 2026-08-19 three ISOs hold
   a `complete` marker (NEISO, NYISO, PJM …)"* — self-dating prose, true as of its own
   date; the CAISO precedent did not edit that page and neither does this lane.
4. `docs/handoffs/capx-director-ledger-2026-08.md` lane row Q5-W ("ISSUED r#12") — the
   director's own document; its LANDED stamp belongs to the director's next refresh.

## 7. Re-entry condition (explicit)

**Re-entry is a NEW explicit owner declaration, never an automatic restoration**:
NYISO re-enters `complete` only when the owner declares it again on a designated
keeper that scores **CALIBRATED**. Expected route (the withdrawn marker's own
successor note + ledger §0i.2): **Leg 2 of
`INTAKE-SPEC-nyiso156-winter-locational-2026-08-30`** (owner-executable AORR access)
closes the winter face; the keeper returns to CALIBRATED via the C3c standing rule;
the owner re-declares. The nyiso-156b intake authorization is **unaffected** by this
withdrawal — data intake needs no marker (rule 22: what is held out is the score,
never the data or the architecture).

## 8. What NYISO's gate now reads

**(a) fail on the withdrawn marker · (b) PASS (PROMOTE-WITH-CAVEATS, untouched) ·
(c) fail (T1-X never run; closable by chartered lane D10, unaffected) · (d) none.**
No ISO now holds legs (a) and (b) both passing; the gate-board lead may pass to NEISO
on S-4V's measurement. Re-entry requires a new owner declaration on a CALIBRATED
NYISO keeper (winter-intake route).
