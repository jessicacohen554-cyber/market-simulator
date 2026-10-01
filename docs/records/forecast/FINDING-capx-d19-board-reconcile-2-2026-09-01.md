# FINDING — capx-D19 BOARD RECONCILE 2 (2026-09-01)

**Lane:** capx-D19 "BOARD RECONCILE 2" — the r#22 director-ledger §0s.5 queue row
("Four stale cross-ISO board facts · QUEUED — deliberately after D8-V + D4-M ·
Reconcile to a settled board, not one being written under it (D13 precedent)").
**Branch:** `claude/capx-d19-board-reconcile-q2yno5` (the harness-assigned name;
the charter names `claude/capx-d19-board-reconcile-2` — recorded, not repaired,
per the D4-I3 precedent of branch-name divergence).
**Class:** RECORDS ONLY. Zero solves, zero re-scores, zero registrations, and —
after the mid-session merge described in §0a — **zero gate-leg status moves by
this lane**. One file edited (`frontend/data/forecast/program-status.json`)
plus this finding.
**Charter provenance:** the r#23 director-pack §D19 section was in an unpushed
commit at dispatch (git transport failure at the r#23 refresh); the lane ran on
its dispatch charter — six stale facts, each verified against committed records
before any edit.

## §0a A mid-session merge, reconciled around rather than overwritten

While this lane was editing (base `6c7f82da`), origin/main advanced to
`e2fa8ab0` and commit `a1600ebc` — the **audit-program gate-(a) repair lane**,
executing owner ruling R-I (2026-08-31) — rewrote all six `gate.a_keeper_marker`
cells and `gate_a_provenance`, **flipping ERCOT's leg (a) fail → pass on the
ercot-247 marker**: the core of this lane's chartered fact 4, done first and
done richer (its cell carries the R-I two-determination citation — the
ISO-level partition rollup CALIBRATED beside the registered run-level NOT-YET).
Per the charter's collision instruction (rebase before every push, leave the
other lane's writes intact), this lane **rebased onto e2fa8ab0, kept every
audit-lane write byte-identical (asserted), dropped its own competing cell
rewrite, and reconciled the REMAINDER the repair left inconsistent**:

- ERCOT `gate.closed_on` still read `['a','b']` — contradicting the cell's own
  PASS — and `marker_complete` still read `false`; both reconciled.
- The audit lane re-keyed four cells' keeper citations but not the top-level
  keeper DISPLAY fields, leaving ERCOT/CAISO/MISO/NYISO displaying stale ids
  against both their own cells and the shards; reconciled (§2.7–8).
- Every cross-ISO surface (headline, gate_reading, tier ladder, membership
  rows) — untouched by the audit lane — reconciled per the original charter,
  with the ERCOT leg-(a) prose now CARRYING the audit lane's committed flip
  rather than making one.

## §0 What the board now says that it did not

1. **The §2.1b gate has opened — once, per-campaign, and the authorization is
   spent.** The headline/gate_reading were written for a board on which leg (d)
   was "none everywhere"; the NEISO gate block has carried the Q13 grant, the
   spend and `open: true` since 2026-08-31. The top-level prose now carries it:
   NEISO holds all four legs, the campaign (`neiso-2026-2050-t3-golden-bau`,
   25/25 years, 29.2 min / 3.50 GB) scored a T3 HOLD, and no standing
   authorization exists anywhere.
2. **ERCOT is the third `complete` member** (ercot-247, 2026-08-31; `complete`
   = {ERCOT, NEISO, PJM}, verified directly in `calibration-complete.json` at
   `6c7f82dac015` and re-verified at `e2fa8ab0051d`). The leg-(a) flip itself
   is the audit lane's (§0a); this lane carried it into the cross-ISO prose,
   the leg-count table, and the ERCOT block's remaining fields. Nothing opened
   — ERCOT's gate stays closed on (b).
3. **The program's first two clean FC maps** are on the top-level prose: bare
   `neiso-t1f` + `nyiso-t1f` PROMOTE with caveats [] (D8-V published,
   2026-08-31), and the exact gate cells D8-V flagged by name are annotated.
4. **The blocker map matches the per-ISO blocks again:** PJM {I7, I12} (S-6,
   three measured I7 years; smallest live I7 miss now PJM 2028, 3,260 MW) and
   MISO {I3} (S-123-V closed MISO's I7 in all five years; MISO leaves the
   adequacy family, now 3/6, and joins the I3 row).
5. **A ten-hour projection is now a 29.2-minute measurement:** the `readiness`
   prose and the tier-ladder T3 row carry the registered, FC-6-scored golden
   instead of "deferred (§2.1b, Wave 4 withdrawn)".

## §1 The six chartered facts — disposition

| # | Charter fact | Disposition |
|---|---|---|
| 1 | tier_ladder T3 row "deferred (§2.1b, Wave 4 withdrawn)" | FIXED — status `first campaign RUN (NEISO, 2026-08-31)`; note carries the registered + FC-6-scored (D21) record, HOLD, per-campaign authorization. Routed by `t3_golden_campaign.flagged_not_edited[0]`. |
| 2 | `readiness` still calls the golden a projection | FIXED — rewritten around the measurement (29.2 min / 3.50 GB, mechanically clean, structurally-failing HOLD). Routed by `t3_golden_campaign.flagged_not_edited[1]`. |
| 3 | headline/gate_reading written for "no ISO holds leg (d)" | FIXED — both rewritten (D13 convention); the retired "leg (d) is none everywhere / every ISO's open is false" claim named in a bracketed correction. Routed by `t3_golden_campaign.flagged_not_edited[2]`. |
| 4 | ERCOT gate (a) passes on the literal test (ercot-247) | VERIFIED against `calibration-complete.json` + `keepers/ERCOT.json` as chartered — then, mid-session, the audit-program gate-(a) repair lane landed the cell flip (§0a). Its cell KEPT VERBATIM; this lane reconciled the remainder: closed_on `['a','b']` → `['b']`, gate note appended, keeper display re-keyed 231 → 234, marker_complete → true, and the cross-ISO prose. |
| 5 | The D8-V-flagged gate cells | FIXED, exactly the flagged set and no more — `isos.NEISO.gate.b_t1f_verdict.detail` and `isos.NYISO.gate.b_t1f_verdict.detail` annotated (statuses untouched; both already `pass`). |
| 6 | The two PROMOTEs / stale caveat + blocker prose | VERIFIED (bare keys PROMOTE, caveats [], @ 836e48e1) then FIXED — gate_reading leg (b), tier-ladder T1-F note, both gate notes' leg-(b) parentheticals, headline blocker prose, adequacy/I3/open_frontier membership rows. |

## §2 Per-edit before → after

Every edit is one of three shapes: **rewrite** (headline, gate_reading,
readiness — the D13 convention, each retired claim named in a bracketed
`[CORRECTED 2026-09-01 by lane D19 …]` inside the new text), **append** (an
annotation added to the end of a preserved field), or **value swap** (status /
id / list membership). The full BEFORE text of every field is one `git show`
away (parent of this commit, `e2fa8ab0`); the load-bearing before/after:

1. `generated`: `2026-08-31` → `2026-09-01`.
2. `sources[0]` (append): before claimed FOUR bare t1f records still carry
   FFR-3A-2 (ERCOT, CAISO, PJM, MISO); the append states the re-verified
   census — TWO (ERCOT, CAISO @ 8ba59281); pjm = S-6 + D8-V @ 836e48e1
   (preserved `pjm-t1f-ffr3a2`), miso = S-123-V + D8-V (preserved
   `miso-t1f-pre-s123`), nyiso/neiso = D8-V-published PROMOTEs.
   `sources[27]` appended: this finding.
3. `headline` (rewrite): retired — "BOARD RECONCILED TO THE r#13 STATE", "NO
   ISO CLEARS THE §2.1b FULL-SOLVE AUTHORIZATION GATE", "Leg (d) is `none` for
   all six", "THREE ISOs now hold exactly two of the four legs … NO ISO HOLDS
   THREE", the "two non-HOLD T1-F determinations" framing (they are now
   PROMOTE, caveats []). Now: the four numbered facts of §0, the live FC-1
   fail sets, and the leg-count table ending "NEISO (a)+(b)+(c)+(d spent) ·
   ERCOT (a)+(c) · PJM (a)+(c) · NYISO (b)+(c) · MISO (c) · CAISO none".
4. `gate_reading` (rewrite): retired — "reaches FOUR of six", "I7 FAILs in
   THREE — CAISO, MISO, PJM — and I12 … in TWO", "PJM {I7} · MISO {I7}", "In
   PJM and MISO, I7 is now the ONLY FC-1 failure left", "The SMALLEST live
   miss is now MISO 2027 (3,659 MW)", "2029 plausibly joining … which lane S-6
   measures" (S-6 measured it: 2028+2029+2030 fail, 2030 = 5,655 MW), "LEG (a)
   passes for the two `complete` members, NEISO and PJM", "both
   PROMOTE-WITH-CAVEATS", "LEG (c) … FAILS FOR TWO, NEISO and CAISO" (D14
   closed NEISO), "LEG (d) is 'none' everywhere", "nobody holds three". Now:
   fail sets as re-verified from the bare keys; leg (a) ×3 {ERCOT, NEISO, PJM}
   (the audit lane's flip cited as the carrier of ERCOT's cell); leg (b) ×2
   PROMOTE caveats []; leg (c) ×5, fails only CAISO; leg (d) held by NEISO
   alone, granted-and-spent; the base-year I7 instruction carried, now
   3-for-3 vindicated (NYISO extcap, NEISO hydro, MISO S-123), live base-year
   leg CAISO 2026 alone; closing paragraph states this reading **moves no
   gate-leg status at all**.
5. `readiness` (rewrite): "Ten hours of compute today would buy a
   mechanically-clean but structurally-flawed golden run" → the measurement
   (25/25 years, 29.2 min / 3.50 GB, structurally-failing HOLD on five
   gates), with the old sentence quoted as the prediction it was.
6. `tier_ladder[1].note`: "All six ISOs HOLD." → four HOLD; NYISO + NEISO
   PROMOTE, caveats [] (stale since 2026-08-25; flagged by Q5-W).
   `tier_ladder[2].note`: "ERCOT + PJM HOLD; FC-4 CO2 drives both fails." →
   five legs, ALL HOLD, CAISO never run, D5-R co2-attribution caveat.
   `tier_ladder[4].note`: + "the one opening to date … does not reach T2".
   `tier_ladder[5]`: status + note per §1 fact 1.
7. `isos.ERCOT` remainder (the audit lane's `a_keeper_marker` cell kept
   verbatim): `closed_on` `['a','b']` → `['b']`; `note` append (leg (a) PASS
   via the audit lane; holds (a)+(c), superseding "exactly ONE"; nothing
   opened); `keeper` `2026-08-24-231-tie-zone-measured` →
   `2026-08-25-234-eastex-identity`; `marker_complete` `false` → `true`.
8. Keeper DISPLAY re-keys for the three other ISOs whose audit-re-keyed cells
   exposed stale display fields — CAISO `2026-08-17-caiso-200-h1-memberpanel`
   → `2026-08-26-caiso-220-c1-crosswalk`, MISO `2026-08-22-miso-177-rho-measured`
   → `2026-08-30-miso-191-bexit`, NYISO `2026-08-30-nyiso-157-par-attribution`
   → `2026-08-30-nyiso-159-loss-surface`. **The one edit class beyond the six
   chartered facts** (the D13 precedent of flagging the inseparable extra):
   display consistency only, each value copied from `keepers/<ISO>.json`
   (re-read at `e2fa8ab0051d`, asserted equal to the shard in the assertion
   script) and identical to the id each ISO's own gate-(a) cell now cites; no
   gate verdict reads off the display field and none moves.
9. `isos.NEISO.gate.b_t1f_verdict.detail` + `isos.NYISO.…` (append): the
   cells still opened "PROMOTE-WITH-CAVEATS"; each now carries the D8-V
   publication (7-entry / 1-entry ledger, PROMOTE, caveats [], first clean FC
   maps), statuses untouched.
10. `isos.NEISO.gate.note` + `isos.NYISO.gate.note` (append): the stale
    leg-(b) "PROMOTE-WITH-CAVEATS" parentheticals annotated the same way.
11. `isos.CAISO.gate.c_crossover_gap.detail` (append): "leg (c) fails in
    exactly TWO ISOs, NEISO and CAISO" was made stale the same day by D14 —
    now annotated: fails ONLY in CAISO; cell status and basis (no `caiso-t1x`
    key, re-verified) unchanged.
12. `honest_unfit[1]` ("I7 / I12 — A2"): title "(4/6 ISOs …)" → "(3/6 ISOs …,
    MISO's I7 CLEARED 2026-08-31)"; `isos` drops MISO → {ERCOT, CAISO, PJM};
    `isos_formerly` gains MISO; detail append records the S-123-V closure, the
    measured PJM three-year set, and the I7/I12-vs-I3 parity flag. `status`
    ("OPEN — dominant") deliberately byte-identical — see §4.1.
13. `honest_unfit[2]` ("I3"): `isos` + MISO; detail append with the S-123-V
    magnitudes and the rule-25 attribution boundary (D4-I3's finding that
    FR-6's energy-only cause cannot explain capacity-market I3s).
14. `open_frontier[4]` (append): "I7 FAILs live in THREE ISOs (CAISO, MISO,
    PJM) and I12 in TWO" → I7 ×2 (CAISO, PJM), I12 ×3 (+PJM); live base-year
    I7 leg CAISO 2026 alone.
15. `d19_board_reconcile` lane block added (note / lane / derived_from /
    what_changed / what_did_NOT_change / flagged_not_edited), including the
    §0a merge record.

## §3 The assertion record (D8-RE/D8-V pattern)

Asserted programmatically before commit (script in the session scratchpad;
BEFORE = the origin/main copy at `e2fa8ab0051d`, i.e. **including** the audit
lane's writes):

- **Changed-path set == the intended set, exactly** (20 paths + the new
  `d19_board_reconcile` subtree): `generated`, `sources`, `headline`,
  `gate_reading`, `readiness`, `tier_ladder`,
  `isos/ERCOT/gate/{closed_on,note}`, `isos/ERCOT/{keeper,marker_complete}`,
  `isos/{CAISO,MISO,NYISO}/keeper`,
  `isos/{NEISO,NYISO}/gate/b_t1f_verdict/detail`,
  `isos/{NEISO,NYISO}/gate/note`, `isos/CAISO/gate/c_crossover_gap/detail`,
  `honest_unfit`, `open_frontier`. Zero removed paths.
- **The audit lane's writes kept verbatim:** all six `gate.a_keeper_marker`
  cells and `gate_a_provenance` byte-identical to e2fa8ab0.
- **Zero gate-leg status moves by this lane:** every gate cell's `status`
  equal before/after, asserted per cell across all six ISOs.
- **Append-only proven** (new value `startswith` old) for: `sources[0]`, both
  b-cell details, both gate notes, the ERCOT gate note, the CAISO (c) detail,
  `honest_unfit[1].detail`, `honest_unfit[2].detail`, `open_frontier[4].detail`.
- **Byte-identical, every ISO:** all t1f/t1x/t1h/t3 determination fields,
  every `fc` map, every `blocking_rows` list, every candidate/golden/flip/
  provenance/tier_reached field; keeper + marker fields except the four
  named re-keys and ERCOT's `marker_complete`; every gate-cell detail except
  the three named appends; `open` for all six (ERCOT still `false`, NEISO
  still `true` — **no gate opened and none closed by this lane**);
  `closed_on` for the five non-ERCOT ISOs; the whole NEISO `d_owner_auth`
  cell as the T3 lane wrote it. Each keeper re-key asserted equal to its
  `keepers/<ISO>.json` shard.
- **Byte-identical, cross-ISO:** all 16 prior lane blocks (`refresh` …
  `d4m_ercot_t1h`, `gate_a_provenance` included), `program`, `flip_config`,
  `iso_order`, `readiness_limits`; `sources[1..26]`; `tier_ladder` rows 0 and
  3; `honest_unfit` rows 0, 3, 4 (incl. `honest_unfit[1].status`);
  `open_frontier` rows 0–3 and 5–9.
- **Outside the file:** `git status` shows the board + this finding as the
  only changes — `ff-verdicts.json` and the entire backcast namespace
  untouched. JSON dump settings proven byte-roundtrip-identical before
  editing. `check_forecast_staleness.py` after the edit: no new warning (its
  two WARNs — unreachable newest-scored sha in the blobless clone; 31
  undated verdict stamps — are pre-existing classes, the second recorded by
  D8-V).

## §4 Flagged, not edited

1. **The "dominant" label.** With MISO out, adequacy (I7/I12) reaches three
   ISOs and I3 now also reaches three (ERCOT, CAISO, MISO — plus the NEISO T3
   golden's out-year I3 on a different tier). Whether "THE dominant T1-F
   blocker" still describes adequacy is a characterization, not a record: the
   row keeps its adjudicated title phrase and "OPEN — dominant" status, the
   parity fact is stated beside them, and any re-ranking is the director's. A
   reconcile lane that starts re-ranking is adjudicating.
2. **`isos.*.tier_reached`** still reads "T1" for NEISO though a T3 campaign
   is registered and scored. The T3 lane deliberately did not move it and the
   field's semantics (highest tier RUN vs highest tier PASSED) are defined
   nowhere; defining them is not a records act. Routed.
3. **MISO `gate.closed_on` stray "FC-2"** (flagged by D13) — now doubly stale
   (MISO's FC-2 reads PASS since S-123-V), still cosmetic, still not a §2.1b
   leg, still routed: the director did not point this lane at it.
4. **The `closed_on` "d"-omission inconsistency** (flagged by D7) persists for
   the five closed ISOs; NEISO's is moot (leg (d) granted-and-spent,
   `closed_on []`). Pre-existing, cosmetic, routed.
5. **`honest_unfit` "I3" row title** still reads "ERCOT scarcity slack" while
   membership is now three ISOs. Cosmetic; the MISO append carries its own
   citation and the rule-25 boundary.
6. **tier_ladder statuses "scored (FF-2D)"** on T1-F/T1-X/T1-H — historical
   shorthand for the original scoring battery; the notes now carry the live
   vintages. Cosmetic, routed.
7. **Division-of-labour note on the audit merge** (recorded, nothing left to
   fix): the audit lane's ERCOT cell already read "(a) PASS · (b) fail · (c)
   pass · (d) none" while `closed_on` still carried 'a' — reconciled by this
   lane; stated in both lane blocks so the two commits' halves are explicit.

## §5 Guardrail compliance

Zero solves, zero re-scores, zero registrations; **no verdict and no gate-leg
status moved by this lane** — ERCOT's (a) flip is the audit-program repair
lane's committed write (owner ruling R-I), kept verbatim and carried. Backcast
namespace READ-ONLY (rule 15): `calibration-complete.json` and the keeper
shards read at `6c7f82dac015` / re-verified at `e2fa8ab0051d`, never written;
no keeper shard, status file, marker, bench or registry byte touched. No
ScenarioConfig field, no mechanism, no matrix cell (rule 28 not triggered). No
out-of-training year solved, scored or registered (rule 22; the freeze stays
tier-scoped to the locked test). No GitHub Actions workflow. Collision
discipline honoured: origin/main advanced mid-session (`6c7f82da` →
`e2fa8ab0`); the lane rebased onto it, kept the incoming writes byte-identical
(asserted), and re-derived its own edits against the new baseline. No FC-5
content written anywhere (the D25 deconfliction). Push per CLAUDE.md Git &
Pushing; `program-status.json` blob-verified after push (rule 27).
