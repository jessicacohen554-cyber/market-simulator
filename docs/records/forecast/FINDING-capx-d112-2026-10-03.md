# FINDING — capx D112: rung-0 gate-(a) re-key (MISO/SOCO, R-53/R-54) (2026-10-03)

**Lane:** capx D112 (zero LP, DATA PROFILE: code), standing duty Q34 (rung 0 of ledger §0bn.2a), the TWENTY-FIFTH
firing and the one that reads the two promotions D110 §1.1 named but could not follow.
**Read at:** origin/main `32afdd8754dbeb80a5c7a65f9619809ba24936ca` (PR #7157, the R-55 desk-ruling merge). The
charter pinned `e7aa5d27cb587ba07b9ec38d91d2d2e8f79581e4` (the D110 merge, PR #7155); origin/main had moved past
it by three merges (#7153 R-53 → `410f2900`, #7154 R-54 → `4c6f3ab3`, #7157 R-55 → `32afdd87`), so the branch was
cut from the newer main and every keeper / status / marker file below was read at `32afdd87`. The pin is an
ancestor of the read sha (verified after deepening the shallow clone).
**Scope:** `frontend/data/forecast/program-status.json` only (plus this record and one CHANGELOG entry). This lane
changes NO verdict, NO FC cell, NO tier, NO leg status, NO `complete` entry, NO keeper shard, NO status sidecar,
NO `ff-verdicts.json` byte. Nothing solved, scored or registered. Edited by targeted string edits at uniquely
anchored positions (D110's method), never a `json.dumps` round-trip; the flattened before/after diff (§4) shows
only the paths named in §1–§2.

## 1. Rung 0 — the nine-row keeper table (old → new)

Board determination = `frontend/data/backcast/status/<ISO>.js` `keeper.determination` (rubric 3.17), read live.
`complete` = `calibration-complete.json` `complete` block: **NEISO** (`2026-10-02-w0-neiso`) and **NYISO**
(`2026-10-02-w0-nyiso`); ERCOT / CAISO / SPP / PJM in `withdrawn`; MISO, NWPP, SOCO in neither (never held one).

| ISO | program-status keeper before (at `32afdd87`) | designated keeper (`keepers/<ISO>.json` at `32afdd87`) | re-keyed? | board | `complete`? | gate (a) |
|---|---|---|---|---|---|---|
| ERCOT | 2026-10-02-closeout-l1-coal-fuel | 2026-10-02-closeout-l1-coal-fuel | no | NOT-YET | no (withdrawn) | NOT MET (unchanged) |
| CAISO | 2026-10-02-closeout-caiso-w1-arm2 | 2026-10-02-closeout-caiso-w1-arm2 | no | NOT-YET | no (withdrawn) | NOT MET (unchanged) |
| PJM | 2026-10-03-closeout-pjm-nuc-keeper | 2026-10-03-closeout-pjm-nuc-keeper | no | NOT-YET | no (withdrawn, Q73) | NOT MET (unchanged) |
| MISO | 2026-10-02-w0-miso-fix2 | **2026-10-03-closeout-miso-nuc-r** | **yes** (R-53, PR #7153 → `410f2900`) | NOT-YET | no (never) | NOT MET (unchanged) |
| NYISO | 2026-10-02-w0-nyiso | 2026-10-02-w0-nyiso | no | CALIBRATED | **yes** (Q74) | **MET** (unchanged) |
| NEISO | 2026-10-02-w0-neiso | 2026-10-02-w0-neiso | no | CALIBRATED | **yes** | **MET** (unchanged) |
| SPP | 2026-10-03-closeout-spp-nuc-keeper | 2026-10-03-closeout-spp-nuc-keeper | no | NOT-YET | no (withdrawn) | NOT MET (unchanged) |
| NWPP | 2026-10-03-nwpp-next-24-head | 2026-10-03-nwpp-next-24-head | no | NOT-YET | no (never) | NOT MET (in `gate_a_provenance`, Q68) |
| SOCO | 2026-10-03-closeout-soco-2-nuclear | **2026-10-03-closeout-soco-3-coalpile** | **yes** (R-54, PR #7154 → `4c6f3ab3`) | NOT-YET | no (never) | NOT MET (in `gate_a_provenance`, Q68) |

Two of nine `isos.<ISO>.keeper` fields were stale — exactly the two D110 §1.1 deferred. Each re-keyed row
carries the prior id in its `keeper_corrected_by` Supersedes chain with the prior chain text nested whole (MISO
prepends to the D101 chain; SOCO prepends to the D110 entry). The `gate.a_keeper_marker.detail` leaves had already
been re-keyed by `promote_keeper.py` (the file names `2026-10-02-w0-miso-fix2 -> 2026-10-03-closeout-miso-nuc-r`
and `2026-10-02-w0-soco-fix2 -> 2026-10-03-closeout-soco-3-coalpile` there) and are byte-unchanged; no leg status
moves.

**MISO `gate_a` re-derived live** at `32afdd87`: `read_live_at` → `32afdd87`, `derived_by` → this lane (D110's
derivation kept inline), `reason` → the live reading with the prior reason carried beneath. Keeper present, never
in `complete`, board NOT-YET: gate (a) **NOT MET — no reading moved**; only the keeper id moved. The other six
board rows' `gate_a` objects are untouched (their keeper ids did not move): MET for NEISO and NYISO, NOT MET
elsewhere, exactly as D110 left them. **SOCO** stays inside `gate_a_provenance` per owner ruling Q68 (no `gate_a`
object before a `complete` declaration): keeper `2026-10-03-closeout-soco-3-coalpile`, board NOT-YET, never in
`complete` → NOT MET, recorded in `gate_a_provenance.d112_rekey.derived_by`; NWPP likewise NOT MET, unchanged.

**Stale `note` prose (NWPP, SOCO):** both rows' G5 `note` fields still named their pre-D110 keepers
(`2026-10-03-closeout-nwpp-anchor-roster`, `2026-10-02-w0-soco-fix2`). Each receives an appended, dated
`[CORRECTION capx D112 …]` sentence naming the live keeper, its ruling and PR, the unchanged NOT-YET determination
and the Q68 posture; the G5 text is kept verbatim, not deleted.

**`gate_a_provenance`:** top-level stamp re-keyed to `derived_at_sha 32afdd87` / `2026-10-03` / this lane; a new
`d112_rekey` block carries the full derivation text and nests D110's top-level stamp (`6277de60`) as
`prior_stamp`; the existing `d110_rekey` and `r69b_rulings` blocks are untouched.

### 1.1 Rulings read, none pending

Close-out plan §5 at `32afdd87` carries R-55 (PJM COAL_BIT *"Find a mechanism to get it to decommit"*, lane
closeout-PJM-decommit chartered). It is a lever ruling, not a promotion: no keeper moved under it and the desk notes
(third batch) record the serialised PJM/MISO/SOCO promotion queue as drained with the slot free. No promotion
ruling is recorded-but-unlanded at this sha, so the next rung-0 firing has nothing deferred from here.

## 2. Gate-(a) readings — did any move?

**No.** Gate (a) is MET for NEISO and NYISO and NOT MET for the other seven, byte-for-byte the same readings D110
left (`reading`, `literal_test_s2_1b_2_a`, `keeper_present`, `complete_member`, `board_determination` unchanged on
every row; only MISO's `reason` / `read_live_at` / `derived_by` prose moved). The two promotions changed keeper
identity only; both ISOs remain NOT-YET on the board and absent from `complete`.

## 3. Checks run (all exit 0 before AND after the edit)

Before the edit (clean tree at `32afdd87`; the three gates were run at `e5b36c81`, the sha origin/main held when the
session opened, and the only commit between it and `32afdd87` touches `docs/backcast-closeout-plan-2026-10.md`,
none of the gates' inputs): `scripts/audit_keepers.py` PASS (0 failures, 4 warnings) · `scripts/check_forecast_parity.py`
(9 keeper postures, 0 unaccounted, 30 filed gaps, 0 registry failures, 0 errors) · `scripts/check_registry_payload_parity.py`
(9 runs OK, 9 bundle dirs swept). After the edit: identical readings, all EXIT 0; `json.load` re-parses the file;
fast lane `pytest tests/scoring/test_promote_keeper.py -n auto -m "not slow and not integration and not fulldata"`
→ 13 passed.

## 4. Flattened before/after diff (every changed leaf)

```
ADDED    gate_a_provenance.d112_rekey.{derived_at_sha, derived_at_date, derived_by}
ADDED    gate_a_provenance.d112_rekey.prior_stamp.{derived_at_sha, derived_at_date, derived_by}
CHANGED  gate_a_provenance.derived_at_sha, gate_a_provenance.derived_by
CHANGED  isos.MISO.keeper, isos.MISO.keeper_corrected_by
CHANGED  isos.MISO.gate_a.reason, isos.MISO.gate_a.read_live_at, isos.MISO.gate_a.derived_by
CHANGED  isos.SOCO.keeper, isos.SOCO.keeper_corrected_by, isos.SOCO.note
CHANGED  isos.NWPP.note
```

## 5. Deviations and leftovers

* Charter pin `e7aa5d27` was behind origin/main; branched from `32afdd87` and recorded both SHAs (as instructed).
  origin/main moved from `e5b36c81` to `32afdd87` during the session's first fetch; the branch was re-cut on the
  newer sha before any edit.
* The "before" gates were executed at `e5b36c81`, not `32afdd87` (§3 explains why the readings are the same).
* No `r#` desk-refresh number is claimed for this firing; the stamp counts it as the twenty-fifth Q34 firing.
* NWPP and SOCO `isos` rows exist on the board (G5 snippet) although Q68 admits a board row only after `complete`;
  as in D110, their keeper id / note were corrected and no `gate_a` object was added. Whether the rows should
  exist at all remains a desk question.
* Mechanism-matrix `U` row for the PJM CT frontier (D110 §0bn.2b.4 leftover) is still with the desk; not this lane's file scope.
