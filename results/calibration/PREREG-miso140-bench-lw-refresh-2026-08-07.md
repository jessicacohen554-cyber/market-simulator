# PREREG — miso-140: refresh the MISO scoring bench's load-weighted actual comparator, and re-verify every MISO C3a

**Session:** miso-140, 2026-08-07, branch `claude/miso-bench-refresh-c3a-e2zuk7`.
**HEAD at pre-registration:** `638cd378464c031385711aab6ef508c346ace809`.
**Pushed BEFORE any adjudicating statistic.** Everything below is written from
(a) source code read at HEAD, (b) committed artifacts inspected at HEAD, and
(c) the two prior findings named in §0. **No recomputed `*_lw` value and no
`calibration_verdict.py` invocation of my own exists at the time of this commit.**

**SCOPE BAR, STATED FIRST — this is BENCH HYGIENE, NOT A LEVER.** The object is
the comparator the scorer differences against, not the model. It **cannot close
the −14 % C3a gap and will not be reported as progress against it** in any
artifact this session produces. No mechanism is proposed, armed, probed or
tested; no price lever is chartered or folded in (rule 19 `[R-ONE-MECH]`); no
LP is solved; no run is registered; no matrix cell verdict moves
(rule 28(b) `[R-MECH-MATRIX]`).

---

## §0 State of record, from committed artifacts

Keeper `2026-08-05-miso-132b-cc-committed` (bundle `results/calibration/miso132_ccmin_B`),
determination **NOT-YET**, sole FAIL **C3a `price_mean`**, ledger budget spent
1 of 1 on C3c (miso-139 §0, re-verified there against
`calibration_verdict.py`).

The object, as chartered (miso-137 §5, G-0(i)): recomputing the committed MISO
`*_lw` actual scalars from the committed hourly parquet × today's
`eia_loader.load_demand` gave **45.4555 vs the committed 45.39** for 2025 RT
(2023 Δ −$0.023, 2024 Δ +$0.031, `da_lw` 2025 Δ +$0.064) against a ±$0.05
tolerance — **diagnosed as a stale demand vintage in the committed comparator,
not a price-series defect**: the legacy equal-hour `rt` field reproduces from
`actual_lmp_hourly_MISO.parquet` exactly, and `load_demand`'s weights are
identical today. The scorer was comparing a model dispatched on today's demand
against an actual weighted on an earlier one.

## §0b THE OBJECT MOVED BEFORE THIS SESSION OPENED — disclosed in full, in advance

**A cross-ISO session performed the mechanical refresh ~45 minutes before this
session started.** Disclosed here rather than discovered later, because it
changes what this PREREG can honestly claim to predict:

| commit | time (UTC) | what it did |
|---|---|---|
| `1d63141c` | 2026-08-07 ~06:0x | pjm-160 B5: re-derived `*_lw` in `data/raw/_validation-source/actual_lmp.json` for **all six ISOs** |
| `056eb164` | 2026-08-07 06:14:59 | pjm-160 B5: propagated the MISO `*_lw` into `frontend/data/backcast/bench/MISO/{2023,2024,2025}.json.gz` + regenerated `status/MISO.js` |

The leaf-level diff of `056eb164` on the three MISO bench parts is **19 / 22 / 20
changed leaves out of 8178 / 8109 / 8074, and every one of them is an
`avgLMP.*_lw` or `avgLMP.*_lw_mon` field.** The annual moves are exactly the
miso-137 deltas: `rt_lw` 32.87→32.85, 32.27→32.30, 45.39→**45.46**;
`da_lw` 34.24→34.23, 33.13→33.14, 46.29→**46.35**.

**Information I therefore hold GOING IN, and am not entitled to present as a
result I produced:** the committed `status/MISO.js` (regenerated 2026-08-07
05:53 by that session) already shows the post-refresh C3a as
**−0.4 / −6.0 / −14.1 %** (RT) and **−4.4 / −8.4 / −15.8 %** (DA diagnostic),
determination still **NOT-YET**, 2025 C3a still **FAIL**.

**What is therefore genuinely still open, and is what this session adjudicates:**

* **G-1 — is the refreshed comparator CORRECT?** Nobody has re-run the exact
  G-0(i) test that failed in miso-137 *against the new values*. A refresh that
  is merely *newer* is not a refresh that is *right*.
* **G-2 — is the propagation into the bench faithful and CONFINED?** The bench
  part is a separate artifact from `actual_lmp.json`; the scorer reads the
  bench. And pjm-160's own PJM task 1 (`f6e88aa3`) regenerated bench parts on a
  *corrected nameplate union* — a blast radius that must **not** silently reach
  MISO under a comparator-refresh mandate.
* **G-3 — what does `calibration_verdict.py` say when I run it myself**, on
  committed artifacts, for all three years and both bases.

## §0c Provenance of the weights, as read from source at HEAD

Recorded now so that §2's verification is checkable against a written claim:

* **Deriver:** `scripts/data/derive_actual_lmp.py::_lw_fields` → `lw_retrofit`
  (CLI `--lw-retrofit`), non-ERCOT branch.
* **Price series:** `data/raw/_validation-source/actual_lmp_hourly_MISO.parquet`,
  filtered to `year`, densified onto 8760 hours. Committed `src`: *"MISO RT/DA
  LMP, system reference hourly series … verified hour-for-hour identical to the
  INDIANA.HUB series in the D6 per-hub staging"*. **Last touched `f434590d`,
  i.e. unchanged by the pjm-160 refresh** — the refresh moved weights, not prices.
* **Weights:** `market_sim.data.eia_loader.load_demand("MISO", year, get_iso_config("MISO"))`,
  summed over zones (`w = demand.sum(axis=0)`). Verified at HEAD to return
  `(6, 8760)` over `MISO-West, MISO-Plains, MISO-Illinois, MISO-Indiana,
  MISO-East, MISO-South`, totalling **640.993 / 644.633 / 663.810 TWh** for
  2023 / 2024 / 2025.
* **Statistic:** `_lw_stats` — NaN-aware, `w > 0` masked, `round(·, 2)`; monthly
  cells on the fixed non-leap month-start hour table.
* **Committed `src_lw`:** *"system hub hourly series load-weighted by measured
  system demand (eia_loader.load_demand)"*.

---

## §1 Pre-registered expectations

### G-1 — reproducibility of the refreshed reference

Recompute `_lw_fields("MISO", y)` at HEAD for y ∈ {2023, 2024, 2025} and compare
to the committed `actual_lmp.json`.

**Expected: EXACT equality in all 78 cells** — 2 bases × 3 years annual (6) plus
2 × 3 × 12 monthly (72) — at the deriver's own 2-dp rounding. Rationale: my
recompute and pjm-160's retrofit run the *identical* code path over the
*identical* committed inputs. Predicted annual values:

| year | `rt_lw` | `da_lw` |
|---:|---:|---:|
| 2023 | **32.85** | **34.23** |
| 2024 | **32.30** | **33.14** |
| 2025 | **45.46** | **46.35** |

I additionally pre-register the unrounded 2025 RT value as **45.4555 ± 0.0005**,
reproducing miso-137's G-0(i) recompute to the fourth decimal. A recompute that
lands on the *old* 45.39 would mean the refresh was derived from something other
than today's `load_demand`, and is a **fail**, not a curiosity.

### G-2 — faithfulness and confinement of the propagation

Compare the committed bench parts to the committed `actual_lmp.json`, and
independently confirm that **no non-`*_lw` leaf** differs from the pre-refresh
bench parts (`056eb164^`).

**Expected: all 78 `*_lw` cells equal, and exactly 0 non-`*_lw` leaves changed**
(observed pre-registration: 19 / 22 / 20 changed leaves, 100 % of them `*_lw`).

### G-3 — the C3a re-verification

`scripts/calibration_verdict.py --run-id 2026-08-05-miso-132b-cc-committed`,
committed artifacts only, **NO RE-SOLVE**, all three years in one invocation
(rule 16 `[R-ALLYEARS]` — never a single-year re-score).

**Expected** (model scalars unchanged; only the comparator moved):

| year | model | actual RT | C3a expected | DA diagnostic expected |
|---:|---:|---:|---|---|
| 2023 | 32.72 | 32.85 | **−0.4 % PASS** | −4.4 % |
| 2024 | 30.37 | 32.30 | **−6.0 % PASS** | −8.4 % |
| 2025 | 39.05 | 45.46 | **−14.1 % FAIL** | −15.8 % |

Determination expected **NOT-YET**, sole FAIL **C3a**, ledger 1 of 1 on C3c.

**Direction, pre-registered so it cannot be spun later:** the refresh makes 2025
**worse** (−13.97 % → −14.09 %), 2024 **worse** (−5.90 % → −5.98 %) and 2023
**better** (−0.46 % → −0.40 %). The net effect on the blocker year is adverse.
This refresh is incapable of being good news about the gap.

---

## §2 DECISION RULE — when the keeper's determination may change

Pre-committed, before G-3 is run:

1. **The determination may change ONLY as a mechanical consequence of the moved
   comparator** — i.e. iff a scored criterion's status flips (PASS↔FAIL), or a
   caveat/gate changes, under identical model scalars.
2. **Pre-registered expectation: NO criterion flip, NO determination change.**
   C3a is gated at ±10 %. The largest comparator move is **+$0.066 on 2025 RT
   (0.145 % of level)**, worth **0.12 pp** of C3a; 2025 sits **4.1 pp** outside
   the band, 2024 **4.0 pp** inside it, 2023 **9.6 pp** inside. No year is
   within an order of magnitude of its boundary.
3. **If a flip nevertheless occurs:** (a) re-verify with a second independent
   invocation **before any keeper text moves**; (b) run the
   `calibration-keeper-auditor` agent scoped `--iso MISO`; (c) state the flip
   explicitly in the finding, the handoff and the PR body.
4. **A determination change caused by bench hygiene is REPORTED AND ESCALATED,
   never banked.** It does not promote, demote or re-designate a keeper — the
   keeper stays `2026-08-05-miso-132b-cc-committed` in every branch of this
   PREREG. A comparator refresh is not evidence about a model.
5. **Symmetry clause.** An *improving* flip gets exactly the treatment of a
   worsening one. Under no branch is any part of this session reported as
   progress against the −14 % C3a gap.

---

## §3 Stop rules

* **S1 — non-reproducible reference.** If G-1 fails (fresh derive ≠ committed
  `actual_lmp.json`), report the discrepancy, **overwrite nothing from my own
  numbers**, and stop for diagnosis. A reference that does not reproduce is a
  *worse* defect than a stale one, and mine would be the third vintage.
* **S2 — propagation gap.** If the bench parts disagree with a reproducing
  `actual_lmp.json` on any `*_lw` cell, repair the **bench parts only** from
  `actual_lmp.json` (the propagation is mechanical) and record the repair.
* **S3 — blast radius.** If any **non-`*_lw`** leaf would change, **STOP**.
  miso-140 is authorized to move the comparator weights and nothing else; a
  nameplate/`classFull`/`e930`/`co2` change arriving under a comparator mandate
  is a different session's decision.
* **S4 — holdout.** Rule 22 `[R-HOLDOUT]`: MISO holds **no** marker in
  `calibration-complete.json`. **2023, 2024, 2025 only.** No out-of-training
  year is read, solved, scored or registered.

---

## §4 What this session will NOT do

* **No solve.** Rule 15 `[R-DASHBOARD]`: no LP runs, so there is **no run to
  register** (the miso-131…137 precedent). Keeper unchanged.
* **No lever, no cell verdict.** Rule 28(b): no mechanism tested ⇒ no
  `mechanism-matrix.js` verdict moves. The only matrix edit is the §5.4 queue
  stamp retiring item 1 and promoting item 2.
* **No touching queue item 2** (flat summer capacity haircut vs net-summer
  `pmax` basis) — its own session, rule 19.
* **No anchor-convention successor.** It is an OPEN OWNER DECISION and is not
  queued; it is not opened here.
* **No C7 COAL_PRB** — deprioritized by owner order, not a lane.
* **No re-opening `temp_derate_mean_anchored`** — REFUSED-AT-G0 (miso-139);
  no new evidence is offered here.
* **No other ISO's artifacts.** The five other ISOs' `*_lw` also moved in
  `1d63141c`; adjudicating them is not a MISO lane's business, and keeper shards
  are strictly per-ISO.

---

## §5 Rule duties discharged by this session

**Rule 13/21/24** — nothing sized on any residual, no parameter derived or
re-derived, no tuning channel created. The comparator is a **measured input
recomputed from unchanged measured sources**, and it moves the target *away*
from the model.
**Rule 16 `[R-ALLYEARS]`** — all three years re-verified in one invocation.
**Rule 22 `[R-HOLDOUT]`** — training window only.
**Rule 25 `[R-ISO-SCOPE]`** — MISO artifacts only.
**Rule 27 `[R-PUSH]`** — Opus; blob verification after any push touching a
≥300-line file.

---

**Finding to follow:** `results/calibration/FINDING-miso140-…-2026-08-07.md` ·
**Handoff:** `docs/handoffs/miso-140-bench-refresh-2026-08-07.md`.
