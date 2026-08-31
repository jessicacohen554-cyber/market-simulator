# FINDING — c3c-Q2: **CONFIRMED, agreeing with nyiso-164** — reality was NOT NYCA-short in its own price tail, and NYISO's C3c ledger stands. This session first measured the OPPOSITE, and this finding records the false positive, its refutation by exact re-derivation, and the **two live defects in a committed calibration reference** that produced it — the session's one original contribution

**Session c3c-Q1/Q2, 2026-08-31, branch `claude/c3c-scarcity-charter-audit-uxmjon`.**
Executes Q2 of `docs/CHARTER-c3c-scarcity-program-2026-08-31.md` §5 under owner
ruling R-E, opened by Q1 returning REAL
(`docs/FINDING-c3c-q1-pjm-phantom-audit-2026-08-31.md`). **ZERO SOLVE: no LP, no
solver, no year scored, no run registered, no bundle modified, no holdout year
touched (2023–2025 only; `--holdout-authorized` never passed).**

**Keeper resolved fresh at session start AND end: `2026-08-30-nyiso-159-loss-surface`
— UNCHANGED, NOT-YET on {C3a-2025 −11.5 %, C3c}.** Nothing here touches a keeper,
shard, marker, determination or matrix cell. **No NYISO shard is edited.**

> ## PRIOR-ART NOTICE AND CONCESSION
>
> **Charter Q2 was already executed, at HEAD, by session nyiso-164**
> (`docs/FINDING-nyiso164-c3c-product-level-2026-09-01.md`; artifact
> `results/calibration/_nyiso164_nyca_shortage_check.json`; probe
> `scripts/probes/nyiso164_nyca_shortage_check.py`), which returned **CONFIRMED —
> the kill gate fires**. This session ran in parallel, reached the **opposite**
> answer, discovered their record afterwards, re-derived the measurement
> independently, and **reproduced their numbers exactly**. *(Independent
> reimplementation, corrected: NYCA-tier tail-hour mean $306.74 / $254.62 /
> $393.31; median $248.22 / $239.96 / $403.74; max $761.73 / $552.89 / $1,101.85;
> ceiling test 0/65 — every figure identical to theirs.)*
>
> **nyiso-164 is right and this session's first reading was wrong.** The verdict
> below is theirs. §2 states why they are right; §3 states exactly how this
> session got it wrong; §4 is the part that is new and worth keeping.

Committed instrument: `scripts/probes/c3c_q2_nyiso_nyca_shortage.py` (no LP, no
solver) → `results/calibration/_c3c_q2_nyiso_nyca_shortage.json`. **That probe
carries the DEFECTIVE construction of §3 and its module docstring says so** — it
is retained as the reproducible record of the false positive, not as a
measurement to cite. **For the correct measurement, cite
`scripts/probes/nyiso164_nyca_shortage_check.py`.**

---

## 0. VERDICT — the kill gate FIRES; NYISO's C3c ledger is CONFIRMED

The charter's gate: *"if reality's tail hours show no NYCA-level shortage,
NYISO's C3c ledger is CONFIRMED and the leg closes as CAISO's did."* It shows
none. **The leg closes.** C3c stands as a ledgered model-class limitation on
NYISO's own evidence rather than by inheritance from CAISO/MISO — which resolves
the charter §3 inheritance question in the direction opposite to the one §3
suspected. This closes nothing about C3c itself and moves nothing about C3a-2025.

## 1. THE OBSERVABLE — and the one thing both sessions got right

NYISO's regions nest (NYCA ⊃ East F–K ⊃ SENY G–K ⊃ NYC J / LI K), so zones
**A–E** (WEST, GENESE, CENTRL, NORTH, MHK VL) — outside East/SENY/NYC/LI — price
the **NYCA tier alone**. Verified here independently: A–E price identically, max
cross-zone spread **0.000000 $/MW** in every hour of all three years. The
construction is sound and is not in dispute.

Source: `data/raw/NYISO-AS/NYISO_as_rt_<year>.csv` (NYISO MIS RT AS clearing
prices, in-repo; nothing fetched). Reality's tail: `actual_lmp_hourly_NYISO.parquet`,
`rt` > $300 (rubric §5 NYISO threshold) — 10 / 13 / 42 hours.

## 2. WHY nyiso-164 IS RIGHT — the ceiling test, reproduced independently

A **nonzero upstate price means the NYCA constraint BOUND, not that its demand
curve ACTIVATED.** The separation that decides it:

> A reserve holder's opportunity cost is bounded by (LMP − marginal cost) ≤ LMP.
> An RCPF demand-curve (shortage) price is not bounded by LMP.

So a NYCA-tier price *below* the concurrent LMP is consistent with pure
opportunity cost; one *above* it requires the demand curve. Reproduced here from
the committed CSVs, independently of their probe:

| year | tail h | NYCA-tier mean | median | max | h ≥ $40 | h ≥ $750 | **h NYCA price > concurrent LMP** | ratio median | ratio max |
|---|---|---|---|---|---|---|---|---|---|
| 2023 | 10 | $306.74 | $248.22 | $761.73 | 10 | 1 | **0 / 10** | 0.573 | 0.869 |
| 2024 | 13 | $254.62 | $239.96 | $552.89 | 11 | 0 | **0 / 13** | 0.536 | 0.936 |
| 2025 | 42 | $393.31 | $403.74 | $1,101.85 | 41 | 4 | **0 / 42** | 0.654 | 0.923 |

**The NYCA-tier reserve price never exceeds the concurrent LMP in any of the 65
tail hours**, and sits at a stable ~0.54–0.65 × LMP. That is the signature of
**energy** scarcity dragging reserve opportunity costs up — not a NYCA reserve
shortage the model fails to see. It is the same opportunity-cost-versus-shortage
distinction this session's own Q1 turns on for PJM (Q1 §3); Q1 applied it
rigorously to the model side and Q2's first pass failed to apply it to the
reality side.

nyiso-164's two corroborating separations are recorded and not re-derived here:
**quantization** (tail-hour values 10/10, 13/13, 33/42 distinct, one exact RCPF
rung hit in three years) and **the operator record** (a declared NYCA-wide
reserve pick-up covers 8 of 65 tail hours, against 35/40/26 pick-ups a year spread
across all months). And on the model side, independently confirmed here: the three
NYCA families carry **zero dual and zero ORDC shortfall in all 26,280 hours** of
every year, with `held_mw` at exactly the requirement.

## 3. HOW THIS SESSION GOT IT WRONG — two defects, both real, both in one input

This session's first pass measured the NYCA tier from the **committed derived
reference** `data/raw/_validation-source/actual_as_reserve_NYISO.parquet`, column
`nyca_reserve_adder`, rather than from the raw CSVs. It reported 40/42 tail hours
NYCA-priced, **21/42 at or above $750**, and a tail-hour mean of **$925** —
"reality WAS short at NYCA level". Every one of those numbers is wrong, and the
two reasons are independent:

### Defect A — the price aggregate SUMS a cumulative cascade (the substantive one)

`process_nyiso_as.py::build_reference` computes
`stack = spin_10 + nonsync_10 + op_30`. **NYISO's three posted products are
cumulative, not incremental**, and the data proves it: `spin_10 ≥ nonsync_10 ≥
op_30` holds in **96,360 / 96,624 / 96,360 of 96,360 / 96,624 / 96,360 rows —
100.0000 %, all 11 zones, all three years** — and all three are *exactly equal*
in 82–84 % of rows. A 10-minute spinning MW satisfies all three nested
requirements and earns `spin_10`, **not the sum**. Summing triple-counts one
shadow price: in the hours WEST is priced, `sum / max` is **exactly 3.0× in
28.1 % / 73.2 % / 79.1 %** of them (mean 1.58 / 2.54 / 2.73). *Worked example:
2023-09-05 17:00 EDT, WEST — `spin_10 = nonsync_10 = op_30 = $661.77`; the true
NYCA price is $661.77, the summed "stack" is $1,985.32.*

That inflation is precisely what broke the ceiling test: on the summed basis the
"NYCA price" exceeds the concurrent LMP in 46 of 65 tail hours at median ratios
1.14–1.96, manufacturing the appearance of demand-curve pricing. On the correct
basis it exceeds it in **0 of 65**.

### Defect B — the clock is a naive positional map across a DST boundary

`build_reference` maps the CSV's naive **prevailing**-Eastern `Time Stamp` onto
the model's 8760 index positionally
(`hoy = _MONTH_START_HOUR[month-1] + (day-1)*24 + hour`). The model's NYISO clock
is fixed standard time, `Etc/GMT+5` (`derive_actual_lmp._STD_TZ["NYISO"]`), which
`actual_lmp_hourly_NYISO.parquet` rides. The two differ by one hour through the
whole DST season — **5,710 of 8,760 hours, 65.2 % of the year** — which is where
every tail hour sits. nyiso-164 found and repaired this independently (their §3);
their offset scan peaks at 0 after repair.

### Both defects are IN THE COMMITTED FILE, verified

The committed `nyca_reserve_adder` reproduces the naive positional SUM in
**8,759 / 8,759 hours of every year** — so this is what the artifact contains,
measured, not inferred.

## 4. THE ORIGINAL CONTRIBUTION — a live defect in a committed calibration reference

The two defects are not this session's arithmetic; they are **in a committed,
shipped artifact** that a future session will read exactly as this one did.

* **What is defective:** `data/raw/_validation-source/actual_as_reserve_NYISO.parquet`
  — every column (`nyca_reserve_adder`, `nyc_reserve_adder`, and each
  `reserve_<model_zone>`), on both counts, in every year present.
* **Builder:** `scripts/data/process_nyiso_as.py::build_reference` — the `stack`
  sum and the positional `hoy` map.
* **Blast radius — NO keeper, NO scored result, NO determination.** The only
  consumer is `scripts/data/derive_nyiso_rcpf_overlay.py` (`_actual_as_reserve`,
  `_MODEL_ZONE_TO_NYISO_AS`), the **post-solve RCPF comparator for co-opt-off runs
  only**. `nyiso_rcpf_enabled` defaults False and is False in the NYISO keeper,
  and rule 19 `[R-ONE-MECH]` makes enabling it alongside the armed
  `energy_reserve_coopt` a hard error. Nothing gated depends on it. **It is a trap
  for diagnostic sessions, not a defect in any result** — and it caught this one.
* **A repair is feasible and cheap, and is NOT done here.** `build_reference`
  reads the **committed** per-year CSVs, so the artifact is regenerable in-session
  with no fetch. Two changes: take the cascade **max** (equivalently `spin_10`)
  instead of the sum, and localize `Time Stamp` to `America/New_York` before
  re-indexing on `Etc/GMT+5` via the repo's own `_std_hour_index`. This session
  does neither: it is chartered zero-solve measurement, the artifact is a
  committed calibration reference, and rewriting one mid-audit — on the strength
  of the audit that was misled by it — is exactly the scope creep the charter
  forbids. **Filed for a data lane or an owner grant.** Rule 14 `[R-ACCURATE]`
  applies: the accurate reading is the raw CSV cascade, and the derived reference
  should be made to agree with it.

## 5. WHAT THIS SETTLES

**Settled.** NYISO's C3c ledger is **CONFIRMED on NYISO's own evidence**. The
charter §3 inheritance worry — that NYISO's caveat inherited a CAISO/MISO
diagnosis its own reserve timing does not support — is answered: split by tier the
picture agrees with CAISO at the tier that governs the residual. At the
**locational** tier the model binds in reality's tail hours and so does reality
(agreement, and the genuine difference from CAISO); at the **system (NYCA)** tier
neither is short (also agreement) — and the NYCA tier is the one that would have
to be short for a system-wide price tail to be a reserve phenomenon. The residual
above the model's $90 locational adder is **not a missing reserve product**.

**Not settled, and deliberately not asserted.** This does not close C3c and does
not move C3a-2025.

**Matrix.** **No cell moves and no shard is edited** — rule 26 duty (b) is not
triggered (nothing tested, armed or adjudicated), duty (c) not triggered (no new
`ScenarioConfig` field). Rule 25 `[R-ISO-SCOPE]`: the Q1 PJM finding does not
enter NYISO's column. nyiso-164's DO-NOT-REDO list is honoured and **reinforced,
not re-opened** — in particular *"arming a NYCA-level family/requirement so the
tail can price (refuted)"* is now refuted twice, independently.

## 6. WHAT THIS IMPLIES FOR THE nyiso-161 WINTER-FACE WAIVER CARD — stated, not ruled

**The card is not this session's to rule** (ruling R-F: parked on this report; the
DIRECTOR re-serves it). Per the dispatch, what our result implies — and nothing
further:

The card (`docs/DECISION-CARD-nyiso161-winter-face-waiver-2026-08-30.md` §2)
decomposes C3a-2025's −11.48 % as **winter face −$3.92**, **summer face −$3.94
("ten scarcity-event days — the ledgered C3c limitation seen in the mean")**, and
shoulder +$0.59, and argues that removing the winter face returns the year to
≈ −5.6 % (in band), whereupon C3c becomes the lone failing criterion and the
rule-22 standing rule reads **CALIBRATED**.

**Our result STRENGTHENS the card's characterisation of its summer half, and
removes an objection to it.** Had this session's first reading stood, the summer
face would have been a published, in-representation reserve-shortage quantity the
model simply fails to bind — i.e. a *defect*, not a model-class limitation, and
the phrase "the ledgered C3c limitation" would have been contradicted. It does not
stand. On the corrected measurement the summer face **is** the ledgered C3c
limitation: reality's tail hours are energy-scarcity hours whose reserve prices
are opportunity-cost consequences, not a reserve product the model is missing.
The card's premise survives an audit that could have broken it.

Three qualifications, so this is not read as more than it is: (a) it bears only on
the **summer** half — the winter face's identification block (AORR access) is
untouched; (b) it is a statement about *characterisation*, not about the
arithmetic, the caveat budget, or the standing rule, none of which this session
moves; (c) **we rule nothing on the card and change nothing about it.**

## 7. DO-NOT-REDO (new, binding)

* **Re-asking whether NYISO reality was NYCA-short in its C3c tail hours.**
  Answered twice, independently: nyiso-164, and this session's corrected
  re-derivation reproducing it to the cent. **0 of 65 tail hours** price NYCA
  reserve above the concurrent LMP.
* **Measuring any NYISO reserve quantity from
  `actual_as_reserve_NYISO.parquet` until §4 is repaired.** Both the aggregate and
  the clock are wrong; use `data/raw/NYISO-AS/NYISO_as_rt_<year>.csv` directly,
  take the cascade **max** (not the sum), and localize prevailing → `Etc/GMT+5`
  before indexing. This finding exists partly so the next session does not lose a
  day to it.
* **Summing `spin_10 + nonsync_10 + op_30`** as a NYISO reserve price, anywhere.
  The cascade is cumulative — verified in 100.0000 % of 289,344 rows.
* Carried forward unchanged: nyiso-164 §10's retirements, nyiso-144, nyiso-143,
  nyiso-110 §10, caiso-144 §G.

*Evidence:* **`docs/FINDING-nyiso164-c3c-product-level-2026-09-01.md` +
`results/calibration/_nyiso164_nyca_shortage_check.json` +
`scripts/probes/nyiso164_nyca_shortage_check.py` (the prior — and CORRECT —
execution)** · `scripts/probes/c3c_q2_nyiso_nyca_shortage.py` →
`results/calibration/_c3c_q2_nyiso_nyca_shortage.json` (this session's DEFECTIVE
construction, retained as the record of the false positive) ·
`data/raw/NYISO-AS/NYISO_as_rt_<year>.csv` + `data/raw/NYISO-AS/README.md` ·
`data/raw/_validation-source/actual_as_reserve_NYISO.parquet` (the defective
reference) · `scripts/data/process_nyiso_as.py::build_reference` ·
`scripts/data/derive_nyiso_rcpf_overlay.py` (its only consumer) ·
`scripts/data/derive_actual_lmp.py::_STD_TZ` ·
`results/calibration/nyiso159_lossarm_B/` · `src/market_sim/model/reserves/spec.py`
(`NYISO_RCPF_PRODUCTS`, `NYISO_RCPF_LOCATIONAL`, `_nyiso_design`) ·
`docs/DECISION-CARD-nyiso161-winter-face-waiver-2026-08-30.md` §2 ·
`docs/FINDING-c3c-q1-pjm-phantom-audit-2026-08-31.md` ·
`docs/CHARTER-c3c-scarcity-program-2026-08-31.md`.
