# FINDING — capx D13: BOARD RECONCILE — Q7 executed, PJM restated, stale prose repaired — 2026-08-30

**Lane:** capx **D13 BOARD RECONCILE** (capacity-expansion / Forecast Finalization track),
chartered in the r#13 batch (`docs/handoffs/capx-director-ledger-2026-08.md` §0j.4;
issuance record ledger §4).
**Scope:** **RECORDS ONLY** — no LP solved, no year scored, no run registered, no verdict
minted or edited, no keeper or marker touched, no out-of-training backcast year touched in any
way. Every number written to the board already existed in a committed FINDING or verdict record
and is cited in place.
**Branch:** `claude/capx-d13-board-reconcile-fs66gh`, off `origin/main` `8412c3f623e7`.
**Surfaces edited:** exactly two —
`frontend/data/forecast/program-status.json` and
`docs/DECISION-CARD-capx-director-open-rulings-2026-08-25.md`.

---

## 0. Headline

1. **OWNER RULING Q7 EXECUTED — "MEASURED CLOSES THE LEG."** Gate leg (c) flips **fail → pass**
   for **ERCOT, PJM and MISO**. Each has a measured, registered FC-4 and a green readiness
   battery, which is the charter-literal §2.1b(2)(c) test and the reading card A-A was signed
   on. **All three FC-4s are FAIL and are quoted in their cells at full magnitude** — the leg
   records that the crossover input gap was *measured*, not that it is small. NYISO's D10 PASS
   stands; **NEISO and CAISO stay `fail`**, because neither has ever run a T1-X, which is the one
   failure card A-A deliberately preserved.
2. **NO GATE OPENED — verified field by field (§4).** Every ISO's `gate.open` is still `false`,
   every `closed_on` still names at least one leg, and no ISO gained a fourth leg. Post-Q7 leg
   counts: **NEISO (a)+(b) · NYISO (b)+(c) · PJM (a)+(c) · ERCOT (c) · MISO (c) · CAISO none.**
   Three ISOs hold two legs by three *different* pairs; **nobody holds three**; leg (d) is `none`
   for all six.
3. **PJM's I7 miss is RESTATED UPWARD, on purpose: 366 MW → 5,858 MW** (3.39 % of gross peak,
   2030) under the owner-signed hold-last-FPR convention (card C-A), with **2029 plausibly
   joining** as a second failing year — an **inference, flagged**, which lane S-6 measures.
   The 2026–2028 checker bars rise 0.96 / 1.83 / 3.18 pp of peak. **PJM's leg (b) does not
   move: fail before, fail after.** Any reading of PJM's I7 gap as "366 MW" is dead.
4. **The stale top-level prose is repaired.** The headline and `gate_reading` had fallen behind
   this board's own per-ISO blocks and asserted three things that were **false**: that no ISO
   holds (a)+(b) (NEISO has since S-4V), that leg (b) passes only for NYISO (two: NYISO and
   NEISO), and that leg (c) fails for all six (after D10 and Q7 it passes for four). Each is
   corrected **in place, with a bracketed note naming what it used to say** — never silently.
5. **D11-R currency and the Q8 ruling are stamped on the ERCOT block**; the Q7/Q8/Q9 rulings are
   appended to the decision card as a dated **§6 addendum**, so the signature record stays one
   document.
6. **Nothing was re-scored.** No `fc` scorecard entry, determination, tier field or
   `ff-verdicts.json` key changed — asserted and machine-verified (§4).

---

## 1. The rulings executed, verbatim with provenance

Delivered 2026-08-30 at the capacity-expansion director's **refresh-#13 sitting**, recorded at
`docs/handoffs/capx-director-ledger-2026-08.md` §0j.3 and §3.

**Q7 —**

> **RULED 2026-08-30 (r#13 sitting) — MEASURED CLOSES THE LEG**, per the charter-literal
> §2.1b(c) test ("measured and reported" + readiness green) and card A-A as signed ("closes on a
> measured FC-4"). ERCOT/PJM/MISO leg (c) → pass-on-measurement, FC-4 FAIL magnitudes stay at
> full magnitude; NYISO's PASS stands; the in-band reading is superseded. Execution = lane D13.
> No §2.1b gate opens (all three fail other legs).

**Q8 —**

> **RULED 2026-08-30 (r#13 sitting) — HOLD UNTIL D12**, at the finding's §5 recommendation. The
> gas half is inert on the live reserve leg, so arming now would bake in the VRE/storage-only
> split; D12 adjudicates the scarcity basis first and its report re-opens the decision. Matrix
> cell stays **O**.

The authority Q7 rests on, quoted so the reading can be checked rather than taken:

* **Charter §2.1b(2)(c)**, in full: *"**(c) Worth-the-compute evidence.** The T1-X crossover
  input gap (FC-4) **measured and reported** for the ISO, plus FF-3E's readiness battery green
  … and its projected wall/RSS cost table — together, the honest answer to 'what would 10 hours
  of compute buy.'"* **The word "in-band" does not appear.** The leg asks whether the gap is
  known, because its purpose is to price the compute honestly — not to re-test model quality,
  which is leg (b)'s job. Were FC-4 already required to be in-band by leg (b), leg (c) would be
  redundant; the NYISO leg-(b) cell has carried exactly that argument since capx-D7.
* **Card A-A as signed** (`docs/DECISION-CARD-capx-director-open-rulings-2026-08-25.md` §1.3,
  §5.1): *"the director charters a **NYISO T1-X crossover run** so leg (c) closes on a measured
  FC-4 **rather than on an unscored cell**."* The contrast the signature draws is
  **measured vs. unrun**, not passing vs. failing.

**The defect Q7 settles.** From the moment lane D10 registered NYISO's T1-X (2026-08-30) the
board carried **two contradictory leg-(c) semantics at once** — D7's in-band reading on
ERCOT/PJM/MISO and D10's pass-on-measurement reading on NYISO. The director found this at r#13
and **escalated rather than edited**, because resolving it moves three gate legs.

---

## 2. Before / after — every changed cell

### 2.1 Gate legs (the only status changes in this session)

| ISO | leg | before | after | basis |
|---|---|---|---|---|
| ERCOT | `c_crossover_gap` | `fail` | **`pass`** | Q7; measured FC-4 `ercot-2023-2027-crossover-ffr3a3-t1x` |
| PJM | `c_crossover_gap` | `fail` | **`pass`** | Q7; measured FC-4 `pjm-2023-2027-crossover-ffr3a3-t1x` |
| MISO | `c_crossover_gap` | `fail` | **`pass`** | Q7; measured FC-4 `miso-2023-2027-crossover-ffr3a4-t1x` |
| CAISO | `c_crossover_gap` | `fail` | `fail` (annotated) | no `caiso-t1x` key exists — re-verified |
| NEISO | `c_crossover_gap` | `fail` | `fail` (annotated) | no `neiso-t1x` key exists — re-verified; lane D14 chartered |
| NYISO | `c_crossover_gap` | `pass` | `pass` (annotated) | D10's measured FC-4; unchanged |
| **all six** | `a_keeper_marker`, `b_t1f_verdict`, `c_readiness`, `d_owner_auth` | — | **identical** | untouched (PJM's leg-(b) *detail* restated; its status is `fail` before and after) |

`closed_on`: **MISO `['a','b','FC-2','c']` → `['a','b','FC-2']`** — the leg no longer closes the
gate, so `"c"` had to go. ERCOT's `['a','b']` and PJM's `['b']` never listed `"c"` and are
unchanged; CAISO's `['a','b','c']`, NYISO's `['a']` and NEISO's `['c','d']` are unchanged.

### 2.2 The three flipped cells, in substance

Each rewritten `c_crossover_gap` detail states, in this order: that it flipped on Q7 with the
citation; the charter-literal test and that **in-band is not part of it**; which registered T1-X
supplies the measurement; that this is card A-A's reading and supersedes D7's; **the FC-4 FAIL
magnitudes at full magnitude**; and that nothing opened and nothing was re-scored. The
magnitudes carried forward verbatim from the committed records:

| ISO | FC-4 verdict | magnitudes now quoted in the cell |
|---|---|---|
| ERCOT | **FAIL** | price 2023 68.7 % / 2024 41.2 % / 2025 22.5 %; co2 49.2 / 42.7 / 50.6 % (all six over K_iso = 1.5); gas_twh 2023 19.6 %, 2024 10.0 %; coal_twh 2023 35.0 %, 2024 44.1 % — **the largest measured price gap in the program** |
| PJM | **FAIL** | co2 45.1 / 40.4 / 54.2 % over the K_iso = 3.0 band; coal_twh 2024 23.9 % FAIL; price 2025 15.7 %, coal_twh 2023 13.0 %, gas_twh 2024 6.7 % CAVEAT |
| MISO | **FAIL** | co2 63.3 / 58.9 / 75.5 % and gas_twh 2024 15.1 % over band — **the largest measured co2 gap in the program**; price 13.6 / 13.9 / 27.4 % CAVEAT |

The prior 2026-08-24 vintage corrections in the ERCOT and PJM cells (the FF-2D "price converges
69 % → 9 %" claim; PJM's "CO2 43-58 %") are **preserved inside the rewritten text**, not dropped.

### 2.3 The two cells that stay `fail`, annotated rather than left silent

* **NEISO** — annotation states that Q7 was applied and does not reach it: no `neiso-t1x` key
  exists (re-verified this session), FC-4 reads n/a with zero rows, so the leg is **genuinely
  unrun** — the one failure card A-A preserved ("an unrun leg is not a measured one"). Names
  **lane D14** as the chartered closer and states the consequence: on a measured FC-4 NEISO
  becomes the first ISO in program history holding (a)+(b)+(c), leaving only leg (d).
* **CAISO** — same annotation, plus the honest queue fact: **no CAISO T1-X is chartered** (D14
  covers NEISO only), so its leg (c) stays `fail` until CAISO gets its own. That is the honest
  reading, not a penalty, and CAISO's gate is closed on (a), (b) and (c) regardless.

### 2.4 The corrected D10 cell (the task's explicit ask)

NYISO's `c_crossover_gap` asserted, in a parenthetical: *"exactly as every other measured ISO
(ERCOT/PJM/MISO all carry FC-4 FAIL and their leg (c) reads pass)."* **That was false when
written** — at the moment D10 registered the cell, all three read `fail` on the D7-era in-band
reading.

It is **annotated, not rewritten**, in a clearly-labelled `[D13 ANNOTATION 2026-08-30 — ONE
CLAIM IN THIS CELL WAS FALSE WHEN WRITTEN, AND IS TRUE ONLY AFTER TODAY'S EDIT.]` block that
states the falsity, the two-semantics defect it revealed, the Q7 escalation and ruling, and that
the sentence is **true as of this edit**. The rationale is recorded in the annotation itself:
*the sentence is the record of what D10 asserted, and the annotation is the record of how it
became true.* NYISO's leg (c) itself is unaffected — it passed on its own measured FC-4 before
this edit and passes on it after.

### 2.5 The S-5 PJM restatement

Source: `docs/handoffs/FINDING-capx-s5-pjm-horizon-edge-2026-08-30.md` §0/§3, under the
owner-signed **card C-A**. Applied to **`gate.b_t1f_verdict.detail`** and
**`blocking_rows[0]`**:

| field | before | after |
|---|---|---|
| 2030 requirement | 150,454 MW (year-less composite, factor 0.871017) | **155,946 MW** (hold-last FPR 0.9401 → factor 0.902813) |
| 2030 I7 miss | **366 MW** | **5,858 MW** — 3.39 % of gross peak (16×) |
| 2029 | silent (graded PASS against the wrong bar) | **plausibly a second failing year — INFERENCE, FLAGGED**; S-6 measures it |
| 2026–2028 bars | 0.871017 flat | **+0.96 / +1.83 / +3.18 pp of peak**; those years revert to "ungraded pending S-6" |
| FC-2 I12 2030 excursion | −0.2 pp | −3.4 pp, still a single recorded excursion → **FC-2 stays CAVEAT, not FAIL** |
| **leg (b) status** | **`fail`** | **`fail`** — unchanged; determination stays HOLD |

Three disciplines are written into the cell so neither surface can mislead: the 2029 reading is
labelled an **inference** everywhere it appears (no committed artifact carries PJM's 2029 supply
side); the rule 23 `[R-FROZEN-DERIVE]` publication check is recorded (PJM's 2029/30 parameters
are **not yet published** — the 2029/30 BRA is December 2026 — so hold-last stands and the
registry carries an intake pointer at the table edge); and **`ff-verdicts.json` is NOT
hand-edited** — `pjm-t1f` still carries the FFR-3A-2 scorer's 366 MW row, and the two surfaces
will read differently until S-6's run re-scores the leg mechanically. That divergence is stated
in the cell itself.

The supply-side leniency S-5 left on the record is carried too: the external-tie entry
1,281.7 MW is the 2026/27 BRA cleared UCAP held static against PJM's published 2027/28 figure of
1,005.9 MW (−275.8 MW) — a correction that would **widen** the miss.

### 2.6 The D11-R / Q8 currency stamp (ERCOT)

New ERCOT-block field **`d11r_entry_volume_rule`**, recording: `entry_margin_exhaustion` shipped
**default-OFF**, zero DOF confirmed (the walk re-invokes `runner._lookahead_reprice_signal`
itself, delta-anchored, byte-identical off); the four-anchor terminal reserve margin — shipped
25.19 / disarm 40.24 / fwd-exp 40.38 / offline 18.7 / **live arm 22.02 %** (−3.17 pp); **B-2
cobweb survives** (−12.65/+5.20/+10.47 vs −10.46/+6.11/+10.54); the **named degradation** that
the **gas half is inert on the live reserve leg**; the 2023–2025 addition bands failing in both
arms with the arm worse on four of five (attached evidence, never the adjudication basis, rule 1);
matrix cell **O**; and **Q8: arming HELD until D12 adjudicates the scarcity basis**, with D12
released by this report. A short ERCOT `gate.note` points at it so the stamp is visible on the
rendered board. **No FC verdict, `flip_config` posture, default or gate leg moved from it.**

### 2.7 The stale top-level prose

Rewritten: `headline` and `gate_reading`. The false claims retired, each named in place:

| claim carried on the board | status | correction |
|---|---|---|
| "no ISO holds (a) and (b) both" | **FALSE since S-4V (2026-08-30)** | NEISO holds both — the program lead |
| "Leg (b) now passes for ONE — NYISO — and fails for the other five" | **FALSE since S-4V** | passes for **two**: NYISO and NEISO, both PROMOTE-WITH-CAVEATS on their bare t1f keys |
| "LEG (c) NOW FAILS FOR ALL SIX ISOs" | **superseded by D10, then Q7** | passes for **four** (ERCOT, PJM, MISO, NYISO); fails for **two** (NEISO, CAISO) |
| "it is 5 of 6" / "I7 FAILs in FOUR — CAISO, MISO, NEISO, PJM" / "In PJM and NEISO, I7 is the ONLY FC-1 failure left" | **FALSE since S-4V** | **4 of 6**; I7 FAILs in **three** (CAISO, MISO, PJM); in **PJM and MISO** I7 is the only FC-1 failure left |
| "PJM and NEISO are closest on magnitude (366 MW …; 218 MW …)" | **dead on both halves** | PJM restates to 5,858 MW; NEISO's leg closed. The **smallest live miss is MISO 2027, 3,659 MW** |

The honest-accounting tone is preserved and, where the facts allow, sharpened: the new headline
still leads with **no ISO clears the §2.1b gate**, states that leg (d) is `none` everywhere and
that nothing here opens a gate, and closes by naming what the board's two non-HOLD determinations
sit behind (a withdrawn marker; an unrun crossover) — plus the newly-worse PJM number.

Also added: a **`d13_board_reconcile`** provenance block (`note` / `derived_from` /
`what_changed` / `what_did_NOT_change` / `flagged_not_edited`), in the shape of the existing
`d1_board_refresh`, `d7_gate_rescore`, `q5w_marker_withdrawal` and `s4v_neiso_refresh` blocks,
and five `sources` entries (the ledger §0j.3 rulings; the S-5, D10 and D11-R findings; this
finding). The block deliberately carries **no forecast-provenance/v1 field names**, so the
staleness checker can never read a board edit as a scoring event — verified in §4.

### 2.8 One edit beyond the five chartered items, disclosed

The S-4V refresh **routed two more NEISO-membership staleness items to the director** rather than
editing cross-ISO prose outside its charter (`s4v_neiso_refresh.flagged_not_edited`). They are
the *same sentence, the same fact and the same records class* as the `gate_reading` repair this
lane is chartered to make, and leaving them false while correcting the identical statement two
fields above would have been worse than the alternative. Both are repaired, disclosed here and in
the board's own `d13_board_reconcile.what_changed`, and are trivially revertible:

* `honest_unfit` **"I7 / I12 — A2"**: title `5/6 ISOs` → `4/6 ISOs (… NEISO CLEARED
  2026-08-30)`; `isos` drops NEISO (`['ERCOT','CAISO','PJM','MISO']`), `isos_formerly` becomes
  `['NYISO','NEISO']`; a bracketed repair note appended. **Status stays `OPEN — dominant`.**
* `open_frontier` rank 5 **"Base-year adequacy accounting"**: *"I7 FAILs live in FOUR ISOs
  (CAISO, MISO, NEISO, PJM)"* → *"THREE ISOs (CAISO, MISO, PJM)"*; bracketed repair note
  appended. **Rank, lane and the rest of the detail untouched.**

Membership corrections only: no status, lane, rank or measurement changed.

---

## 3. What was NOT touched

* **`frontend/data/forecast/ff-verdicts.json`** — not opened for write. No key, verdict,
  determination, magnitude or provenance stamp changed. (Provenance *prose* in
  `program-status.json`'s `sources` is the only place verdict records are described, which the
  charter permits.)
* **Every backcast surface** — `frontend/data/backcast/keepers/*.json`, `status/*.js`,
  `calibration-complete.json`, `bench/`, the registry. Untouched.
* **Rule 22 `[R-HOLDOUT]`** — **no out-of-training backcast year was solved, scored or
  registered.** The holdout freeze is untouched and remains tier-scoped: the locked test is
  frozen for every ISO, and the validation tier is governed by the `complete` marker plus
  `--holdout-authorized` — this session invoked neither and ran no solve of any kind.
* **`src/`, `ScenarioConfig`, `constants.py`, any solve path** — untouched. No mechanism was
  proposed, tested or armed, so no matrix shard is edited (the D11-R cell **O** was stamped by
  its own lane, per rule 26 duty (b); this lane only records its currency).
* **No GitHub Actions workflow** was added or changed.
* `flip_config`, `readiness`, `tier_ladder`, `readiness_limits`, and every prior
  session-provenance block are preserved verbatim.

---

## 4. Verification (run in this session, after the edits)

**(a) No gate opened — machine-checked, field by field.** Diffing the pre-edit snapshot against
the written file across all six ISOs × five leg fields:

```
CHANGED LEGS: [('ERCOT','c_crossover_gap','fail','pass'),
               ('PJM',  'c_crossover_gap','fail','pass'),
               ('MISO', 'c_crossover_gap','fail','pass')]
```

— **exactly the three legs the ruling names, and nothing else.** Every `gate.open` is `false`
before and after; every `closed_on` still names at least one leg:

| ISO | legs held (after) | count | `open` |
|---|---|---:|---|
| NEISO | (a), (b) | 2 | false |
| NYISO | (b), (c) | 2 | false |
| PJM | (a), (c) | 2 | false |
| ERCOT | (c) | 1 | false |
| MISO | (c) | 1 | false |
| CAISO | — | 0 | false |

**No ISO holds three of four; leg (d) is held by nobody.**

**(b) Nothing re-scored.** `fc`, `t1f_determination`, `t1x_determination`, `t1h_determination`,
`tier_reached`, `keeper`, `marker_complete`, `marker_final`, `flip`, `golden` and `candidate`
compared before/after for all six ISOs: **all identical.** `ff-verdicts.json` is byte-unchanged
(`git status` shows it unmodified).

**(c) The board still parses and renders.** `json.loads` round-trips byte-identically at
`indent=1`, and `scripts/register_forecast_run.py --reindex` completed clean
(*"wrote 15 runs … assembled manifest.js + program-status.js"*, exit 0). The generated
namespace files are gitignored, as designed.

**(d) The staleness checker does not read this as a scoring event.**
`scripts/check_forecast_staleness.py` reports the seed class as **"1 stamped, 0 scored"** and the
gate evidence unchanged (`verdicts`, newest `60e19610e454`). The two WARNs it prints (fresher
non-gate hindcast sidecars; 31 of 43 verdict stamps carrying no scored-at date) are pre-existing
and unrelated.

**(e) Rule 27 `[R-PUSH]`.** `program-status.json` is a >300-line-scale file; it was edited **on
disk** (never regenerated from response content) and the pushed blob is verified against local
in §6.

---

## 5. Flagged, not edited

1. **MISO `gate.closed_on` still carries the entry `"FC-2"`**, which is not a §2.1b gate leg (the
   legs are a/b/c/d) and renders as *"GATE CLOSED · on a, b, FC-2"*. Pre-existing, cosmetic,
   outside the five chartered edits. Routed to the director.
2. **PJM's restated I7 magnitude lives on the board only.** `pjm-t1f` in `ff-verdicts.json` still
   carries the FFR-3A-2 scorer's 366 MW row; the two surfaces read differently until **S-6**
   re-scores the leg mechanically on the corrected bar. Stated in the cell so neither surface can
   mislead a reader on its own.
3. **PJM 2029 is an inference**, labelled as one everywhere. S-6 is the instrument.
4. **CAISO's leg (c) has no chartered closer** — D14 covers NEISO only. A queue observation for
   the director, not a recommendation.
5. **FC-7 (DOF ledger absent) remains a CAVEAT on every T1-F leg in the program** (lane D8).
   Unchanged and un-addressable from a records lane.

---

## 6. Reproduction and push verification

```bash
# the gate-leg diff of §4(a), from the pre-edit snapshot
git show origin/main:frontend/data/forecast/program-status.json > /tmp/before.json
python3 - <<'PY'
import json
b=json.load(open('/tmp/before.json'))
a=json.load(open('frontend/data/forecast/program-status.json'))
LEGS=['a_keeper_marker','b_t1f_verdict','c_crossover_gap','c_readiness','d_owner_auth']
print([(i,L,b['isos'][i]['gate'][L]['status'],a['isos'][i]['gate'][L]['status'])
       for i in a['iso_order'] for L in LEGS
       if b['isos'][i]['gate'][L]['status']!=a['isos'][i]['gate'][L]['status']])
print([(i,a['isos'][i]['gate']['open']) for i in a['iso_order']])
PY

# the board still assembles
python3 scripts/register_forecast_run.py --reindex
python3 scripts/check_forecast_staleness.py
```

**Post-push blob verification (rule 27)** — every pushed file fetched back from
`origin/claude/capx-d13-board-reconcile-fs66gh` and compared to the local on-disk bytes; all
three **MATCH** on line count, byte count and SHA-256:

| file | lines | bytes | sha256 (first 16) |
|---|---:|---:|---|
| `frontend/data/forecast/program-status.json` | 706 | 106,266 | `e86f65d6b3130f7d` |
| `docs/DECISION-CARD-capx-director-open-rulings-2026-08-25.md` | 434 | 26,672 | `d029347dc0460f37` |
| `docs/FINDING-capx-d13-board-reconcile-2026-08-30.md` | 343 | 21,496 | `e2dcb118c5fd7032` |

(The finding's own row is the pre-append blob; this table is added in the follow-up commit that
carries it.) All three files were edited **on disk** and pushed as the exact local bytes — no
file was regenerated from response content, and nothing was staged as a partial or placeholder
version.
