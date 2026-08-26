# FINDING — NYISO gate re-score + leg-(c) harmonisation (capx D-7)

**Session:** capx D-7 NYISO GATE RE-SCORE (capacity-expansion / Forecast Finalization track)
**Date:** 2026-08-26 · **Branch:** `claude/capx-d7-nyiso-gate` · **Base:** `main` @ `bcb25217b228`
**Charter:** `docs/handoffs/capx-director-prompt-pack-2026-08.md` §"D7-NYISO — gate re-score +
leg-(c) harmonisation", plus the refresh-#6 update in
`docs/handoffs/capx-director-ledger-2026-08.md` §0c.
**Scope:** RECORDS ONLY. No LP, no solve, no scoring, no registration.

---

## 0. Headline

**NYISO's gate now reads (a) PASS · (b) PASS · (c) fail · (d) none, `open: false`** — the reading
the charter predicted, and it is confirmed here **against the criteria rather than asserted**
(§2). NYISO is the first ISO in the program to clear the T1→T2 rubric bar and the only one with
legs (a) and (b) both passing.

Three things were carried onto `frontend/data/forecast/program-status.json`:

1. **A re-score that had already landed.** The board was stale by one: it still read NYISO as
   FC-1 FAIL / gate (b) fail, when the bare `nyiso-t1f` key has read 14/14 invariants PASS,
   FC-2 PASS and `PROMOTE-WITH-CAVEATS` since 2026-08-25.
2. **The owner's signed card-A disposition (A-A).** CAISO and NYISO leg (c) `na` → `fail`,
   `"c"` added to both `closed_on`. NEISO's `fail` unchanged.
3. **The program-wide base-year I7 scoring instruction** from
   `FINDING-capx-d2b-i7-ledger-2026-08-25.md` §7, into three prose fields.

**No gate opened. No determination other than NYISO's moved. Leg (d) was not touched.**
Four items are **flagged and not edited** (§5) — including one that the charter's own framing
would have let me write more confidently than the evidence supports (§5.2).

---

## 1. What now stands between NYISO and an open gate

**Exactly two things, and neither is a model defect.**

| leg | reads | what would close it |
|---|---|---|
| **(c) crossover input gap** | `fail` | **A measurement.** No NYISO T1-X has ever been run, so FC-4 is unmeasured. Chartered as director lane **D10** by the same signature that failed the leg. This is the one leg a run can close. |
| **(d) owner authorization** | `none` | **A signature.** There is NO standing authorization; each full-horizon campaign is authorized separately (§2.1b(2)(d)). Untouched by this session. |

**And one thing to read alongside leg (a), which is not a blocker but is a durability question.**
Gate (a) passes on the charter's literal test, but its `complete` marker now rests on a **NOT-YET
keeper**. If owner question **Q5** resolves the CAISO-precedent way, leg (a) closes too and
NYISO's lead position is not real. See §2.1 and §5.1.

So: NYISO is blocked on **an unmeasured instrument and an unsigned authorization**, standing on
**a marker whose basis is under owner review**. That is the honest three-sentence state of the
program's lead ISO.

---

## 2. NYISO's four legs, re-read against the criteria

Criteria text: `docs/forecast-development-plan-2026-07.md` §2.1b(2)(a)–(d). Every input below was
read live at `bcb25217b228`; nothing was inferred from the board's prior text.

### 2.1 Leg (a) — backcast calibration proof → **PASS** (on the test as written)

The test is **two conjunctive conditions**: a designated **full-span** keeper (rule 16) **AND** an
entry for the ISO in the **`complete` block**. `final` is never required for forecast work.

| condition | evidence read | holds? |
|---|---|---|
| designated full-span keeper | `keepers/NYISO.json` → `2026-08-25-nyiso-155-hydro-repair`; `registry/2026-08-25-nyiso-155-hydro-repair.json` → `years: [2023, 2024, 2025]` | **yes** — full span |
| entry in `complete` | `calibration-complete.json` → `complete` = {NEISO, **NYISO**, PJM} | **yes** |

→ **PASS.** The keeper id was **re-keyed** from `2026-08-22-nyiso-152-duty-complete` (superseded
2026-08-25). **The verdict did not move and I did not move it.**

**The tension, recorded not resolved.** The live keeper's determination is **NOT-YET** (C3a 2025
−10.8 %, C3c 1/0/0 h; C1 14/14, C2/C3b/C4/C6/C8 PASS), where the superseded keeper read
CALIBRATED. It was promoted **by explicit owner ruling** on structural integrity over gate
regression — the hydro truncated-vintage repair pair, restoring a 26.5 TWh/yr class from a
3-plant/2.0 %-retention 2025 vintage to 147 plants — with the D-5(b) worse-determination stop
fired, escalated, and resolved by that ruling. NYISO's **frontier** status returned to the owner
on the same promotion.

A `complete` marker therefore now rests on a NOT-YET keeper: **the identical fact pattern that
withdrew CAISO's marker on 2026-08-06** ("a `complete` marker cannot stand on a NOT-YET keeper").
Both precedents are on the record and point opposite ways. **That is owner question Q5**
(ledger §0c.2, §3) and explicitly not this session's. Per the charter I did **not** re-read leg
(a) downward on my own initiative: the literal test holds, and the tension is written into the
cell so a reader meets it there rather than inferring a soundness the record does not support.

### 2.2 Leg (b) — POC gates green → **PASS**

Read from the **bare `nyiso-t1f`** key (session `capx-D2-extcap-intake`, `scored_at_sha`
`ea4e4faf65de`, 2026-08-25) — **not** from `nyiso-t1f-ffr3a2` or `nyiso-t1f-ff2d`, which are
deliberately preserved baselines.

| category | live status | required at t1f? |
|---|---|---|
| FC-1 structural (I1–I14) | **PASS** (14/14) | **R** |
| FC-2 adequacy/equilibrium | **PASS** (I12 in-band, I13 no cobweb, backstop share 0.0 %) | **R** |
| FC-3 capacity skill | n/a (0 rows) | **—** not applicable |
| FC-4 crossover skill | n/a (0 rows) | **—** not applicable |
| FC-5 external corridor | SKIPPED | rpt |
| FC-6 driver response | SKIPPED | **O** optional |
| FC-7 provenance/DOF | **CAVEAT** (DOF ledger absent) | **R** |
| FC-8 runtime | **PASS** (13.1 min) | R\* never blocking |

**This is the leg I was most at risk of asserting, so it is worked in full.** The bare
§2.1b(2)(b) sentence reads *"FC-1 PASS, FC-2 no-FAIL, **FC-3/FC-4 in-band, FC-6 green**"* — and
on that sentence alone NYISO does **not** obviously pass, because FC-3/FC-4 are `n/a` and FC-6 is
`SKIPPED`. The resolution is not a judgement call: the rubric's **executable form** of the same
gate (`docs/forecast-determination-rubric.md` §3) gives the per-tier applicability row, and at
**t1f** it reads **FC-3 = `—`, FC-4 = `—`** (not applicable — they are the *t1h* and *t1x*
instruments) and **FC-6 = `O`** (optional). The rubric's own clause is *"a category `SKIPPED`
**that the tier requires** ⇒ HOLD"*. Neither is required at t1f, so neither holds the gate.

Every category the t1f tier **requires** is scored — FC-1, FC-2, FC-7, FC-8 — with **no FAIL** and
**one CAVEAT**, which is exactly the rubric's `PROMOTE-WITH-CAVEATS` row. → **PASS**, and the
board's leg-(b) convention is determination-keyed (NEISO's `fail` cell leads *"HOLD — …"*), so
HOLD → PROMOTE-WITH-CAVEATS is the flip.

**The reading is stated in the cell so it can be checked, not inherited silently** (§5.3). A
corroborating structural point: **leg (c) exists as a separate leg carrying the FC-4
"measured and reported" requirement** — were FC-4 already required by leg (b), leg (c) would be
redundant. The charter is coherent only on the applicability-table reading.

### 2.3 Leg (c) — worth-the-compute evidence → **fail**

§2.1b(c) requires **both** FF-3E readiness green **and** the T1-X crossover input gap (FC-4)
**measured and reported**. NYISO's readiness is green (`c_readiness` = battery green); FC-4 is
**absent** — no `nyiso-t1x` key exists in `ff-verdicts.json` and FC-4 reads `n/a` with zero rows.
**Only the readiness half is green, so the leg does not pass.** → **fail**, per the owner's signed
card A (§3).

### 2.4 Leg (d) — explicit owner authorization → **none**

`d_owner_auth` = `none`, "no authorization exists." **Not touched, not readable as anything else,
and no ISO's gate opens from this session.**

### 2.5 Result

`(a) PASS · (b) PASS · (c) fail · (d) none`, `open: false`. **This matches the charter's predicted
reading. No leg had to be forced, and none read otherwise.**

---

## 3. The signed card-A harmonisation

**Authority:** owner signature **A-A**, 2026-08-25 in-session
(`docs/DECISION-CARD-capx-director-open-rulings-2026-08-25.md` §5, consequences at §5.1).
**Basis:** an unrun leg is not a measured one — the reading already adjudicated for NEISO at
neiso-88 (2026-08-06), now applied without exception.

| ISO | leg (c) before | after | `closed_on` before → after |
|---|---|---|---|
| NEISO | `fail` | `fail` (unchanged) | `["b","c","d"]` (unchanged) |
| CAISO | `na` — "not run (FF-2D scope)." | **`fail`** | `["a","b"]` → `["a","b","c"]` |
| NYISO | `na` — "not run." | **`fail`** | `["b"]` → `["c"]` |

NYISO's `"b"` drops because leg (b) now **passes** — that is a consequence of §4.1, not of card A.

The capx-D1 refresh **found** this inconsistency and **escalated rather than edited** it, because
applying it moves a gate leg and that exceeded a records-only remit; it recorded the escalation in
the board's own `d1_board_refresh.escalated_not_edited` field so it could not be lost between
sessions. **The owner's signature is what licenses the edit**, and this lane is the carrier card A
§5.1 names for it. **Nothing opened:** all three gates were already `open: false` on other legs.

**A cross-ISO fact worth stating, which the board did not previously make legible.** Leg (c) now
reads `fail` for **all six ISOs**, for **two materially different reasons** that should not be
conflated:

- **Measured and out of band** — ERCOT (price to 68.7 %, co2 to 50.6 %), PJM (co2 to 54.2 %),
  MISO (co2 to 75.5 %). The gap was measured and it is large.
- **Never measured** — NEISO, CAISO, NYISO. No T1-X run exists.

The `gate_reading` prose was sharpened to say this. A reader who saw six `fail`s without the split
would draw the wrong conclusion about what each ISO needs.

---

## 4. Every changed field, before → after

`frontend/data/forecast/program-status.json` — **42 changed/added leaf paths**, enumerated by a
structural diff against `HEAD`. The file round-trips byte-identically through
`json.dumps(indent=1)`, so the committed diff contains **only** these fields.

### 4.1 NYISO — the landed re-score
*Citation for all rows: `docs/handoffs/FINDING-capx-d2-nyiso-extcap-2026-08-25.md` §0/§4/§7; live
bare key `nyiso-t1f`.*

| field | before | after |
|---|---|---|
| `t1f_determination` | `"HOLD"` | `"PROMOTE-WITH-CAVEATS"` |
| `fc.FC-1` | `"FAIL"` | `"PASS"` |
| `fc.FC-2` | `"CAVEAT"` | `"PASS"` |
| `fc.FC-7` / `fc.FC-8` | `"CAVEAT"` / `"PASS"` | **unchanged** |
| `blocking_rows` | 2 rows: FC-1 I7 (36/51 MW) as "sole T1-F blocker"; FC-2 CAVEAT (I12 WARN 7.8 %, backstop 23.8 %) | 3 rows: no live FC-1/FC-2 blocker; FC-2 cleared; FC-7 CAVEAT flagged as program-wide, not NYISO's |
| `gate.b_t1f_verdict.status` | `"fail"` | `"pass"` |
| `gate.b_t1f_verdict.detail` | `"HOLD — FC-1 FAIL on I7 alone: 2026 32,085 < 32,121 MW (36 MW) and 2027 32,339 < 32,390 MW (51 MW)…"` | PROMOTE-WITH-CAVEATS, sourced to the bare key with the §2.2 criteria re-read written in |
| `keeper` (display) | `"2026-08-22-nyiso-152-duty-complete"` | `"2026-08-25-nyiso-155-hydro-repair"` |

**The substance behind the FC-1 flip**, carried onto the board with the finding's own honesty note
rather than without it: I7's 2026/2027 misses closed via
`ADEQUACY_EXTERNAL_TIE_FIRM_MW["NYISO"] = 3,168.5 × (1 − 0.1321) = 2,749.9 MW` UCAP, sourced from
2026 Gold Book Table V-1 on the FF-2B construction — **a sourced constant, never a number tuned to
the invariant** (it overshoots the adjudicated 35.7 MW gap by ~77×, inside the pre-declared
O(10²–10³) band). Accredited firm now exceeds requirement in all five years by +2,918.9 to
+4,177.4 MW. **But the 2026 PASS is over-determined**: epoch demand drift moved the 2026 peak
−341.4 MW and would alone have flipped that year by a thin +332.9 MW. The intake buys **structural
margin, not the sign**. That qualifier is on the board, not just in the source finding.

### 4.2 NYISO — gate (a) re-key (verdict unmoved)

| field | before | after |
|---|---|---|
| `gate.a_keeper_marker.status` | `"pass"` | **`"pass"` — unchanged** |
| `gate.a_keeper_marker.detail` | keeper `nyiso-152-duty-complete`, "determination CALIBRATED" | keeper `nyiso-155-hydro-repair`, full-span verified at its registry `years`, NOT-YET determination stated, Q5 tension recorded |
| `gate.a_keeper_marker.read_live_at` | `"cb7aadf8408a"` | `"bcb25217b228"` |
| `gate.a_keeper_marker.corrected_by` | `"forecast-gate-refresh (2026-08-22, FR-21)"` | `"capx-D7 gate re-score (2026-08-26) — keeper id re-keyed…; verdict unmoved."` |

`read_live_at` / `corrected_by` are **derivation** fields, not `forecast-provenance/v1` names —
the distinction the board's own `gate_a_provenance` note exists to protect (§6).

### 4.3 Gate (c) harmonisation — see §3 table
`isos.NYISO.gate.c_crossover_gap.{status,detail}`, `isos.CAISO.gate.c_crossover_gap.{status,detail}`,
`isos.NYISO.gate.closed_on`, `isos.CAISO.gate.closed_on`. Both details cite card A §5/§5.1 in-cell.

### 4.4 NYISO — new `gate.note` (added)
States the four legs, the two things standing between NYISO and an open gate, the Q5 caveat on
leg (a)'s basis, and the flagged `closed_on` bookkeeping item (§5.4).

### 4.5 Cross-ISO prose — the base-year instruction and the corrected counts

| field | before → after |
|---|---|
| `headline` | *"all six read HOLD"* → NYISO clears the T1→T2 bar (the other five still HOLD); the §2.1b gate still opens for no one; both jobs described as carrying, not minting; the Q5 caveat named |
| `gate_reading` | I7 in five ISOs + I12 in two = **6/6** → I7 in **four** + I12 in two = **5/6**, with the live per-ISO fail sets enumerated; leg-(c) six-way split (§3); base-year instruction |
| `honest_unfit["I7 / I12 — A2"].title` | *"(6/6 ISOs)"* → *"(5/6 ISOs; NYISO CLEARED 2026-08-25)"* |
| `honest_unfit["I7 / I12 — A2"].isos` | `[ERCOT, CAISO, PJM, MISO, NYISO, NEISO]` → `[ERCOT, CAISO, PJM, MISO, NEISO]` |
| `honest_unfit["I7 / I12 — A2"].isos_formerly` | *(absent)* → `["NYISO"]` (plain list, matching the sibling `I4 / A1` row's convention; the "why" lives in `detail`, since the status page renders `isos` only) |
| `honest_unfit["I7 / I12 — A2"].detail` | rewritten: NYISO removed with its citation and honesty note; hydro root cause retained for the remaining four; NYISO's close identified as a **second, independent route** into the same family (external capacity omitted from the ledger), routing to lanes S-2/S-4; base-year instruction appended |
| `open_frontier[rank 5].detail` | *"I7 FAILs live in FIVE ISOs (… NYISO)"* → **FOUR**; base-year instruction appended |

**The base-year instruction, carried verbatim in substance into all three fields** (charter job 3,
from `FINDING-capx-d2b-i7-ledger-2026-08-25.md` §7): **no base-year I7 leg is a
capacity-evolution defect.** `evolve_fleet` is skipped when `fleet is None`, so **the base year
runs no evolution at all** — no adequacy backstop, no retirement screen, no entry. MISO 2026
(6,037 MW) and CAISO 2026 (6,577 MW) are base-year legs grading **input data only**, and **neither
backstop tuning nor floor relaxation is ever the answer to one**; the answers are requirement
re-vintage, external-capacity intake and ledger differencing (S-1/S-2/S-3; B-1 then NQC for
CAISO). NYISO's own I7 closed exactly that way — by a sourced intake, not by tuning — which is why
the instruction now sits next to the row it just vacated.

### 4.6 Records fields

| field | before → after |
|---|---|
| `generated` | `"2026-08-24"` → `"2026-08-26"` |
| `sources[0]` | claimed *"all six t1f records carry provenance session=FFR-3A-2, scored_at_sha=8ba59281"* → **corrected**: five do; the bare `nyiso-t1f` carries the 2026-08-25 re-score (`capx-D2-extcap-intake` / `ea4e4faf65de`), FFR-3A-2 preserved under `nyiso-t1f-ffr3a2` |
| `sources[10..14]` | five appended: the extcap finding, the decision card, the i7-ledger finding, the director ledger (Q5), the determination rubric §3 |
| `d7_gate_rescore` | **new block** — records-only note, derivation sha/date, `derived_from`, `what_changed`, `what_did_NOT_change`, `flagged_not_edited` |

`sources[0]` mattered: it asserted a provenance uniformity that **this session's own job (1)
disproves**. Left standing, it would have told the next reader the bare key was FFR-3A-2 — the
precise mis-read the vintage convention exists to prevent.

---

## 5. Flagged, NOT edited

Per the charter: a correction that would move a gate outcome beyond the signed card-A change is
**escalated, not applied**. All four are recorded in `d7_gate_rescore.flagged_not_edited` so they
survive this session.

### 5.1 Gate (a)'s basis is unsettled (owner — Q5)
A `complete` marker resting on a NOT-YET keeper vs. the 2026-08-06 CAISO withdrawal. **Gate (a)
passes on the literal test and I did not re-read it downward.** Q5 decides whether NYISO's lead
position is real. Not mine; not editable by a records lane.

### 5.2 Leg (b)'s reading rests on the rubric §3 table, not the §2.1b sentence
Stated in §2.2, in-cell, and here — because the charter's own framing (*"gate (b)'s FC-1/FC-2 now
PASS"*) would have let me write the leg as a clean two-category pass, when the criterion sentence
names four things and two of them are unmeasurable at t1f. **The reading holds**, and the leg is
`pass`; but it holds on the applicability table, and a future reader is entitled to check that
rather than inherit it. If anyone ever reads §2.1b(2)(b) literally at t1f, **no ISO can ever pass
leg (b)** — worth an owner sentence at the next rubric bump.

### 5.3 `closed_on` omits `"d"` for NYISO and CAISO
Leg (d) is `none` for all six and **does** close the gate; NEISO's list carries `"d"`, CAISO's and
NYISO's do not. Board-wide inconsistency predating this session. Correcting it is outside the
signed card-A change, and `open: false` is correct either way. **Recorded, not edited.**

### 5.4 MISO's `closed_on` contains a non-leg entry
`isos.MISO.gate.closed_on` = `["a","b","FC-2","c"]`. `"FC-2"` is a **rubric category, not a gate
leg** — the list is `a|b|c|d`-valued everywhere else. Almost certainly a records slip. It touches
no verdict (MISO's gate is closed on (a) and (b) regardless) and MISO is not my ISO, so it is
**flagged only**. Routing to whichever lane next touches MISO's board block.

### 5.5 Hydro construction divergence (director's item, unresolved)
The backcast now consumes the **repaired** NYISO hydro input (147 plants, EIA-930 monthly pin)
while the forecast consumes the **clamped complete census** (`modelled_hydro_nameplate_mw` clamped
to `EIA923_LATEST_FINAL_VINTAGE`). Two constructions of one physical quantity. Flagged by the
director at ledger §0c.3 as *a question worth a paragraph, not an established defect*. **It does
not reach NYISO's I7 PASS** — that credit was computed on the clamped census by construction, and
the clamp's docstring names this exact hazard. Carried forward as a question; **no cell verdict
minted** (rule 28).

---

## 6. Governance

**Rule 28 [R-MECH-MATRIX]:** this session tested no mechanism and **minted no cell verdict**.
`docs/mechanism-testing-matrix.md` was **not modified**. No cell's fc posture was contradicted by
my reading; §5.5 is carried as a question, not a posture claim.

**Rule 22 [R-HOLDOUT]:** no out-of-training backcast year solved, scored or registered. The
holdout spend freeze stays **ACTIVE**, `final` stays **empty**, `complete` = {NEISO, NYISO, PJM}.
The backcast keeper shards, `registry/`, `status/*.js` and `calibration-complete.json` were
**read only** (rule 15) — verified: the commit touches two files.

**Rule 13:** no measured-outcome feedback. Nothing was tuned; the one substantive number carried
(2,749.9 MW UCAP) is a published Gold Book operand sourced by another lane.

**Not a scoring stamp.** No LP built, no year solved, no run re-scored or registered. The new
`d7_gate_rescore` block **deliberately avoids** the `forecast-provenance/v1` field names
(`scored_at_sha`, `scored_at_date`, `schema`, `session`, `cache_epoch`) — verified programmatically
— so `scripts/check_forecast_staleness.py` can never read this refresh as evidence of a re-score.
This is the discipline the board's own `gate_a_provenance` note establishes and that
`d1_board_refresh` followed.

**Untouched:** every backcast keeper shard, `status/*.js`, `calibration-complete.json`, all offer
curves and commitment bridges, every other ISO's determination, and **leg (d) everywhere**. No
GitHub Actions workflow added; no CI offloaded.

**Verified after edit:** all six ISOs `open: false`; leg (d) byte-unchanged for all six;
ERCOT/PJM/MISO/NEISO ISO blocks byte-unchanged; NEISO leg (c) byte-unchanged.

---

## 7. Successors

- **D10** — NYISO T1-X crossover. Chartered by the same signature; closes leg (c) on a **measured**
  FC-4. The only lane that can move NYISO's gate without an owner signature.
- **Q5** — owner. Whether a `complete` marker may rest on a NOT-YET keeper. Decides whether
  leg (a) — and NYISO's lead position — survives.
- **§5.2** — one owner sentence at the next rubric bump reconciling §2.1b(2)(b)'s literal text with
  the rubric §3 applicability table at tier t1f.
- **§5.3 / §5.4** — `closed_on` bookkeeping, for whichever lane next touches those board blocks.
