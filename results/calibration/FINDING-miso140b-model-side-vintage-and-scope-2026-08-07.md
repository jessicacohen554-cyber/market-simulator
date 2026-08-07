# FINDING — miso-140b: an INDEPENDENT REPLICATION of the MISO `*_lw` verification, plus the two checks it did not run — the MODEL side is on the same demand vintage, the comparator set is a singleton, and `load_demand` silently swaps its zonal split with `sys.path`

> **READ THIS FIRST — WHICH RECORD IS CANONICAL.** A **second miso-140 session
> ran concurrently** on the same §5.4 queue item 1 and landed on `main` first
> (PR #3696; PREREG `483091b3`, FINDING `46139909`). **That session discharges the
> item**, and its record —
> `results/calibration/FINDING-miso140-bench-lw-refresh-verified-2026-08-07.md` —
> is canonical. This document is the concurrent session's, kept because (a) it
> **replicates the comparator verification and every C3a figure independently, in
> every cell**, under a separately pre-registered protocol, which is the strongest
> evidence a load-bearing comparator can carry; and (b) it contributes **three
> results the canonical record does not**: §G-2 the **model-side** demand vintage,
> §G-3 the **comparator-set completeness** enumeration, and §6 the `load_demand`
> `sys.path` hazard. Where the two overlap they agree exactly; nothing below
> contradicts the canonical record, and **this session does not re-discharge the
> item**. The two sessions' gate numbering is independent — this document's G-2 is
> the *model-side vintage* test, the canonical G-2 is the *bench blast-radius*
> test; they are different questions and both pass.

**Session:** miso-140b, 2026-08-07, branch `claude/miso-140-calibration-rfb4o0`.
Charter: §5.4 **QUEUE ITEM 1** — refresh the MISO bench, re-verify every MISO C3a
from committed artifacts, state whether the keeper's determination changes.

**NO LP SOLVED. NO BUNDLE REGENERATED. NO KEEPER MOVED. NO MECHANISM ARMED. NO
`ScenarioConfig` FIELD ADDED. NO PARAMETER SET. NOTHING WRITTEN UNDER
`data/raw/`.** MISO keeper unchanged at **`2026-08-05-miso-132b-cc-committed`**
(bundle `results/calibration/miso132_ccmin_B`).

**PREREG** `results/calibration/PREREG-miso140-bench-refresh-verification-2026-08-07.md`,
pushed at **`78e2cec4`** BEFORE any adjudicating statistic, with four gating
gates, six falsifiable numeric predictions, and four look-alike traps named with
pre-committed counter-measurements.

**This is BENCH HYGIENE, NOT A LEVER.** Owner directive honoured: the target
remains the 2024/2025 mean-LMP level miss; no C7 lane, no C7 ledger.

---

## 1. Headline

**All four gating gates PASS. Every pre-registered number came in exactly.**

The §0 re-verification changed the lane before it started: **the refresh was
already committed at HEAD.** Session **pjm-160** did a cross-ISO `*_lw` refresh
on 2026-08-07 (`1d63141c` reference, `056eb164` MISO bench parts), and its
committed deltas reproduce miso-137 §5's diagnosis to the cent. So the half of
the charter still open was the half miso-138 §8 declined this as a ride-along to
protect: **is the committed refresh correct, complete, and consistent with the
model side it is compared against?**

It is, on all three counts, and now measured rather than asserted:

1. **G-1 — the refresh is CORRECT.** Recomputed independently from the committed
   `actual_lmp_hourly_MISO.parquet` × `eia_loader.load_demand` through the
   deriver's own path: **6 of 6 annual scalars and 72 of 72 monthly entries
   reproduce at Δ = 0.000000.** Not "within tolerance" — exact.
2. **G-2 — the MODEL side is on the SAME demand vintage.** The keeper's committed
   `hourly/system_<year>.parquet` demand matches `load_demand('MISO', y)` at HEAD
   to **0.0 MW max hourly Δ** and **0.0 relative annual energy**, all three years,
   all six zones. The vintage mismatch miso-137 diagnosed is **fully closed**, not
   half closed — which was the branch that would have made this session an
   escalation instead of a discharge.
3. **G-3 — the refresh is COMPLETE.** The set of committed MISO *comparators*
   that resolve through `load_demand` is a **singleton**: `derive_actual_lmp.py`
   → `actual_lmp.json` `*_lw` → bench `avgLMP`. Every other call site is a model
   *input*, not a comparator. C3c's tail carries no demand weighting at all
   (`derive_actual_tail.py` never calls `load_demand`), so it cannot have
   inherited the stale vintage.
4. **G-4 — the adjudication.** `calibration_verdict.py --run-id` at HEAD,
   committed artifacts only, no re-solve.

**The determination does NOT change. It stays `NOT-YET`**, sole FAIL C3a
`price_mean` (2025), sole ledgered caveat C3c (budget 1 of 1), all eight rubric
v3.1 criteria otherwise as before. **No promotion, no re-key, no escalation.**

---

## 2. Verdicts against the pre-registered gates

| gate | prediction | measured | verdict |
|---|---|---|---|
| **G-1** refresh correctness (GATING) | PASS 3/3 × 2/2, 2025 `rt_lw` 45.4555 → 45.46 | **PASS**, Δ = 0.0 on all 6 scalars **and** all 72 monthlies | **RIGHT** |
| **G-2** model-side vintage (GATING) | PASS (conf. 0.75) | **PASS**, 0.0 MW / 0.0 rel, 3/3 years | **RIGHT** |
| **G-3** scope completeness (GATING) | PASS, singleton | **PASS**, singleton; `actual_tail` demand-free | **RIGHT** |
| **G-4** C3a re-verification | RT −0.4 / −6.0 / −14.1; DA −4.4 / −8.4 / −15.8; NOT-YET | **exact, 6/6** | **RIGHT** |
| **G-5** drift (reporting) | expect to find a stale pre-v3.1 caveat claim | **found, and worse than predicted** — §5 | **RIGHT** |

---

## 3. G-4 — the re-verified scorecard, ONE BASIS AT A TIME (miso-133 bar)

`scripts/calibration_verdict.py --run-id 2026-08-05-miso-132b-cc-committed`,
rubric v3.1, scorable years 2023/2024/2025. **The model column is the same
number in both bases** — the model has one price series; RT and DA are two
different *actuals* to difference it against.

| year | basis | model $/MWh | actual $/MWh | C3a | prior bench | Δ pp | status |
|---|---|---:|---:|---:|---:|---:|---|
| 2023 | **RT (gated)** | 32.72 | **32.85** | **−0.4 %** | −0.5 % | **+0.1** | PASS |
| 2024 | **RT (gated)** | 30.37 | **32.30** | **−6.0 %** | −5.9 % | **−0.1** | PASS |
| 2025 | **RT (gated)** | 39.05 | **45.46** | **−14.1 %** | −14.0 % | **−0.1** | **FAIL** |
| 2023 | DA (diagnostic) | 32.72 | 34.23 | −4.4 % | −4.4 % | 0.0 | not gated |
| 2024 | DA (diagnostic) | 30.37 | 33.14 | −8.4 % | −8.3 % | −0.1 | not gated |
| 2025 | DA (diagnostic) | 39.05 | 46.35 | −15.8 % | −15.6 % | −0.2 | not gated |

`PRICE_MEAN_TOL = 0.10`, so 2023 and 2024 stay inside the band and 2025 stays
outside it. **No criterion flips.** The eight scored criteria:

| | C1 fuelmix | C2 sysvol | **C3a** | C3b shape | C3c tail | C4 dispatch | C6 gov | C8 forced |
|---|---|---|---|---|---|---|---|---|
| status | PASS | PASS | **FAIL** | PASS | CAVEAT | PASS | PASS | PASS |

**C3b was the prediction most at risk** and it held: the monthly vectors moved
too, but NRMSE reads **0.075 / 0.112 / 0.191** against a ≤0.20 bar — 2025 is
close to the bar, as it was before, and does not cross it. Determination
`NOT-YET`, on the scorer's own reason string: *"undocumented out-of-tolerance
(FAIL) criteria: price_mean"*.

---

## 4. The look-alike trap, and the counter-measurement that was pre-committed

**TRAP 1 fired exactly where the PREREG said it would: 2023's C3a "improved"
from −0.5 % to −0.4 %.** A comparator that moves in the model's favour is not an
improvement in the model.

*The pre-committed counter-measurement, discharged two independent ways:*

* **The model scalar did not move.** 32.72 / 30.37 / 39.05 at HEAD are the same
  values miso-137 §5 verified to the penny against the *pre-refresh* bench
  (32.7156 / 30.3676 / 39.0472).
* **The bundle was never touched.** `git log` on
  `results/calibration/miso132_ccmin_B/` ends at **`654abd8b`**, the miso-132(b)
  promotion commit. pjm-160 wrote only `bench/` and `status/`.

**So 100 % of the C3a movement is comparator-side, and it is ±0.1–0.2 pp.** The
honest summary, reported signed and unblended as required: on the gated RT basis
the gap gets **0.1 pp smaller in 2023** and **0.1 pp LARGER in 2024 and 2025**;
on the DA diagnostic it is flat in 2023 and **0.1–0.2 pp larger** in 2024/2025.
**Nothing here is progress against the miso-137 object.** The largest movement
this session could produce was **0.2 pp** against a **14 pp** gap, and the
direction on the failing year was *against* the model.

**TRAP 2 (accepting pjm-160's own attestation as the verification) — HELD.** Its
commit message asserts *"Keeper re-scored: no determination flip, no C3a
criterion flip."* That claim was treated as the hypothesis under test: G-1
recomputed the scalars from the parquet and G-4 re-ran the scorer, neither
reading the assertion as input, and the cached scorecard in `status/MISO.js` was
not opened until after the PREREG was pushed. The assertion turns out to be
true — but it is true *because it was checked*, not because it was written.

**TRAP 3 (declaring the lane discharged because a correctly-titled commit
exists) — HELD**, by G-2 and G-3 being gating rather than decorative.

**TRAP 4 (scope creep into a lever) — HELD.** No mechanism, no field, no arm, no
solve. Queue item 2 was not folded in.

---

## 5. G-5 — the drift, which is worse than I predicted, and which I am NOT repairing

The **live scorecard is truthful**: `frontend/data/backcast/status/MISO.js`
(regenerated by pjm-160 at 2026-08-07 05:53) is **record-for-record identical**
to this session's independent verdict run — same determination, same C3a rows,
same caveat set. The run payload embeds no C3a figures. **Nothing the dashboard
renders as a *verdict* is stale.**

What is stale is a **narrative string inside a ledger entry the scorer already
refuses**. `results/calibration/miso132_ccmin_B/calibration_attestation.json`
→ `exceptions` → the `price_mean` 2025 entry reads:

> *"…2023 (**−2.2 %**) and 2024 (**−8.0 %**) both PASS … contribute the bulk of
> the **$6.73/MWh** gap between the actual load-weighted mean **$45.39** and the
> model **$38.66**"*, magnitude *"**−14.0 %**"*.

**Five numbers, and none of them describes this keeper.** −2.2 / −8.0 belong to
an earlier keeper (miso-137 §5 already flagged that pair as stale against the
*pre-refresh* bench); the model scalar $38.66 is not this run's $39.05; and
$45.39 / −14.0 % are the pre-refresh comparator. The entry was carried forward
verbatim across promotions.

**It has zero scoring effect**, because under rubric v3.1 **C3c is the only
ledgerable criterion at all**, so this entry is inadmissible and C3a scores as an
undocumented FAIL — exactly what the reason string says. miso-139 §3 established
that; this session confirms it independently, **and so does the canonical
miso-140 record**, which reached the same disposition (carry, do not repair; it
belongs to the next MISO promotion, which regenerates the attestation).

**I am reporting it and NOT repairing it, deliberately.** Editing a committed
keeper bundle's attestation is a promotion-adjacent governance act, and the
correct disposition of an *inadmissible* entry — amend it or delete it (rule 26
`[R-DELETE]`) — is a rubric-transition decision, not a bench-hygiene commit. The
same applies to the MISO keeper shard's promotion prose, which still says
*"ledgered caveats unchanged at 2/3: C3a, C3c"*: that is a historical promotion
note written under rubric v3.0, and my PREREG ruled out re-writing history in a
promotion note. **MISO is the only ISO whose shard carries such a phrase** (0 in
CAISO/ERCOT/NEISO/NYISO/PJM), so this is a MISO-local record-repair item, and it
is written to the queue for whoever the owner assigns it to.

---

## 6. An unchartered hazard the verification surfaced — `load_demand` silently changes its ZONAL split with `sys.path`

**G-2 failed on its first run at 6.7–7.3 GW max hourly Δ with the annual energy
identical to the MWh.** That signature — same total, different split — was the
instrument, not the artifacts, and running it down produced a finding worth
carrying.

`eia930.zonal_shares._zonal_shares_from_raw` obtains MISO's measured hourly
zonal shares via `from scripts.data.curate_zonal_shares import _PARSE_FUNCS`,
which needs the **repo root** on `sys.path`. `data/clean` is gitignored and
therefore **absent in a fresh clone** (confirmed here), so that raw fallback is
the *only* measured route. When the import fails, `load_zonal_shares` returns
`None` **silently** and `load_demand` drops to the **static Gold-Book
`load_share`** — the same ISO total, a different zonal allocation. Measured on
MISO 2025:

| zone | measured TWh | static-fallback TWh | max hourly Δ MW |
|---|---:|---:|---:|
| MISO-West | 96.96 | 97.31 | 4,202 |
| MISO-East | 159.79 | 160.77 | 4,272 |
| MISO-South | 179.85 | 179.96 | **6,747** |
| *(ISO total)* | **663.81** | **663.81** | *identical* |

**The solve and scoring paths are NOT affected**, and I checked rather than
assumed: `run_calibration_full.py:74` and `calibration_verdict.py:51` both insert
the repo root. **The exposure is ad-hoc probes.** Of 749 files in
`scripts/probes/`, **9 touch `load_demand`/`load_zonal_shares` and 8 of those do
not put the repo root on `sys.path`** — so, invoked the documented way
(`python scripts/probes/x.py`), they receive static shares without a warning.

**Whether that matters depends on which projection a probe uses**, and the
distinction is exactly why G-1 was unaffected: the `*_lw` deriver weights by
`demand.sum(axis=0)`, the **ISO total**, which is invariant to the split. A probe
that uses the **per-zone** series gets silently different numbers. My own probe
is hardened both ways — it puts the repo root on `sys.path` **and** raises if
`load_zonal_shares` returns `None`, so it can never again compare two different
zonal splits without saying so. **This is reported, not fixed**: making the
loader warn or fail loudly is a `src/` change outside a hygiene lane's scope
(rules 19/24).

---

## 7. My prior, scored against interest

| prediction | stated | measured | verdict |
|---|---|---|---|
| **G-1** refresh reproduces | conf. 0.90 | exact, 6/6 + 72/72 | **RIGHT** |
| **G-2** model side same vintage | conf. 0.75 | 0.0 MW, 3/3 | **RIGHT** |
| **G-3** singleton comparator | conf. 0.80 | singleton | **RIGHT** |
| **G-4** RT −0.4 / −6.0 / −14.1, DA −4.4 / −8.4 / −15.8, NOT-YET | conf. 0.85 | **all six exact** | **RIGHT** |
| **G-5** find a stale pre-v3.1 caveat claim | conf. 0.50 | found, and 5 numbers wrong not 1 | **RIGHT, under-stated** |
| net: all gates pass, determination unchanged | 0.65 | yes | **too low** |

**Where I was wrong, recorded.** (a) My net 0.65 was too conservative — I priced
G-2 at 0.75 on a *claim* in pjm-160's commit message rather than on the fact that
the keeper solved after the last demand-input change, which was already knowable.
(b) I predicted the G-5 drift as "a stale caveat count"; it is a whole ledger
entry describing a **different run**, which is a larger record defect than I
priced. (c) I did not anticipate the `sys.path` hazard of §6 at all, and my own
probe walked straight into it — the pre-registered gates caught it only because
G-2 was gating and its failure signature was arithmetically impossible to
dismiss.

---

## 8. What this licenses — nothing armed, and the queue moves on

1. **Queue item 1 is discharged — by the canonical miso-140 record, corroborated
   here.** The MISO bench `*_lw` comparator is verified correct, complete and
   vintage-consistent; every MISO C3a is re-verified on it; the determination does
   not change. **The C3a comparator for every MISO run is now a checked quantity,
   checked twice, independently, under two separately pre-registered protocols** —
   which is more than the item asked for and the right amount for a comparator this
   load-bearing. What this session adds beyond the canonical record is §G-2 (the
   model side is on the same vintage), §G-3 (the comparator set is a singleton, so
   C3c cannot have inherited the defect), and §6 (the `load_demand` hazard).
2. **The 2024/2025 mean-LMP level miss is untouched and un-narrowed**, exactly as
   the charter said it would be. 2025 C3a now reads **−14.1 %** rather than
   −14.0 %, and the −6.0 / −14.1 trend on the gated basis is marginally *steeper*
   than the number the lane has been quoting.
3. **The object still stands where miso-137/139 left it** — a compressed price
   distribution, short **price** and not quantity in summer h12–17, with a
   measured ~12 GW idle-CT cushion any quantity mechanism must cross first. Rule:
   **bound the next candidate against that cushion before a solve is spent.**
4. **Queue item 2** (the flat `SUMMER_CLASS_DERATE` vs the net-summer `pmax`
   basis) is **untouched and still next**, with its own PREREG, and still not a
   lever (miso-139 §7 bounds the family at 30–39× too small).
5. **Two new record-repair items** are written to the queue and are **owner
   dispositions, not lever work**: the inadmissible C3a ledger entry in the
   keeper's attestation (§5), and the `load_demand` silent-fallback hazard (§6).

---

## 9. Rule duties

**Rule 15 `[R-DASHBOARD]`** — no LP solved, so there is **no run to register**
(the miso-131…139 precedent). The live dashboard scorecard was checked against an
independent verdict run and is truthful; keeper unchanged.
**Rule 28(b) `[R-MECH-MATRIX]`** — **no mechanism was tested, so no cell verdict
is minted.** A §5.4 queue stamp is written this session. No other ISO's cell
touched (rule 28(d)).
**Rule 22 `[R-HOLDOUT]`** — 2023/2024/2025 only; MISO holds neither a `complete`
nor a `final` marker. No out-of-training year was read, solved, scored or
registered, and the D-5(b) re-key duty does not apply.
**Rule 13 `[R-MEASURED]`** — no measured *outcome* entered anything; the only
inputs read are the committed actual price parquet, measured demand, and the
keeper's own committed sidecars, and none was fed back into a model quantity.
**Rules 1 / 21 / 24** — nothing sized to any residual, no tuning channel created,
nothing written under `data/raw/`, no `ScenarioConfig` field added.
**Rule 19 `[R-ONE-MECH]`** — one question; queue item 2 explicitly not folded in.
**Rules 20 / 23 / 25** — no free parameter added; no derive script re-run against
a residual; no non-MISO artifact touched.
**Rule 14 `[R-ACCURATE]`** — the refreshed comparator is kept although it makes
the failing year read *worse* (−14.0 → −14.1); that is the rule working.
**Owner directive** — no C7 work, and no progress claimed against the level miss.

---

## 10. The generalisable lesson — **A CORRECTION IS NOT VERIFIED BY THE COMMIT THAT MAKES IT**

The charter asked for a refresh. Re-verifying §0 found the refresh already
committed, by another ISO's session, with a commit message asserting the exact
conclusion this session was chartered to reach. The tempting move — the cheap
one — was to read that message, agree, and close the item.

Three things had to be measured before "already done" could become "done", and
none of them is visible from the commit: whether the new numbers **reproduce**
(G-1), whether the **other side of the comparison** moved with them (G-2), and
whether anything else carried the **same defect** (G-3). Only G-1 is about the
artifact that changed. The other two are about what it is compared against and
what shares its provenance — and G-2 is the one that would have turned a
discharge into an escalation.

The corollary arrived unasked: **the instrument that checks the correction needs
checking too.** G-2's first run reported a 7 GW mismatch that did not exist, and
the only reason it was not written up as a defect in the artifacts is that its
signature — identical totals, large per-cell deltas — is arithmetically
impossible for a vintage error and inevitable for a permutation. *A gate that can
fail for a reason outside the thing it is gating must be able to tell the two
apart before its verdict is quotable.*

Family: miso-133 *measure the slack, on one basis* → miso-135 *grain is a
property of the publication's purpose* → miso-136 *an absence claim is a
measurement, not a premise* → miso-137 *a threshold is a hypothesis, not a
definition* → miso-138 *measure an identification's ceiling where the answer is
known* → miso-139 *a mechanism's anchor is part of the mechanism; bound its reach
before debating its parameter* → miso-140 *a repair is not a verification* →
**miso-140b *…and a correction is not verified by the commit that makes it***.

---

**Probe** `scripts/probes/_miso140_bench_refresh_gates.py` ·
**Records** `results/calibration/_miso140_bench_refresh_gates.json`,
`results/calibration/_miso140_c3a_reverification.json` ·
**PREREG** `results/calibration/PREREG-miso140-bench-refresh-verification-2026-08-07.md` @ `78e2cec4`.
