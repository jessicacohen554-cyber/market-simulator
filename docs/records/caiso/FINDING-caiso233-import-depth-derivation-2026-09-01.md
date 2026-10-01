# FINDING — caiso-233: the CAISO import DEPTH ladder is a MEASURABLE and YEAR-STABLE object (corridor p98 CV **0.042**, total p99.9 CV **0.056**), but the ported NEISO estimator **FAILS both pre-registered honesty gates** and the pre-registered stop condition fired — **NO SOLVE**. The failure is diagnosed, not softened: **the instability is inherited entirely from the FIRM carve-out (CV 0.16, 4× the depth's own 0.042) and from a scarcity rung built as a 2–10 % remainder of a large minuend (CV amplification 9.8×)**. The one rung pair that passes (`DSW_CCGT`/`DSW_CT`, CV 0.026) passes by **arithmetic cancellation, not stability** — disclosed against interest, and NOT admitted. What the exercise *does* establish, durably and for the first time: the incumbent 8,800 MW spot ladder makes CAISO's total import stack **1.5–3.1 GW DEEPER than the measured p99.9 envelope** of actual net import, in the direction C3a needs. NO LP, NO SOLVE — committed bytes only (2026-09-01)

**Keeper `2026-09-01-caiso-231-b1-ungrounded` UNCHANGED. No mechanism armed, no
`ScenarioConfig` field added, no LP built, no solver called, nothing registered,
no matrix cell verdict moved.** `calibration-complete.json` (no CAISO marker) and
`holdout-freeze.json` (ACTIVE) untouched; every read stayed inside **2023–2025**.

Pre-registration: `PRECOMMIT-caiso233-import-depth-derivation-2026-09-01.md`
(gates and stop condition fixed before execution; §6 records the firing).

Instruments (committed):

* `scripts/data/derive_caiso_import_depths.py` — the derivation + both gates.
* `scripts/probes/_caiso233_import_depth_decomp.py` — the failure decomposition.
* `results/calibration/_caiso233_import_depth_derivation.json`,
  `_caiso233_import_depth_decomp.json`.

Every number reproduces from `data/raw/eia-930-interchange/CISO interchange
hourly.parquet` on the model clock (`_caiso_interchange_model_clock`,
`CAISO_CORRIDOR_DIBA`), the committed per-year MIC firm blocks in
`IMPORT_TRANCHES_BY_YEAR`, and the committed keeper artifacts.

---

## §A — The object, and a correction to the charter's enumeration

The charter's criterion (SPOT, uncited, invariant across all three years) selects
a set of four; its **enumeration** substitutes `DSW_solar_PV` for `PNW_midC`.
`DSW_solar_PV` is a member of `caiso.CAISO_FIRM_IMPORT_TRANCHES`, is MIC-measured
and moves 1,251 → 1,813 → 1,805 across the three years, so it fails the charter's
own invariance test and is **already closed**. The corrected object is

    PNW_midC 1,800  DSW_CCGT 1,800  DSW_CT 2,200  WECC_scarcity 3,000  =  8,800 MW

— which is also the set `_caiso186os_dof_repair.py` labels `RESIDUAL (static, no
cited primary source)` and the figure caiso-191 adjudicated. The two firm rungs
are **held fixed** throughout (rule 1 `[R-STRUCT]`: a grounded quantity is never
re-opened to move a residual).

## §B — The pre-registered gates: FAIL, both legs

Ported estimator (NEISO precedent, §2 of the PRECOMMIT), gates at the PRICE limb's
own constants **CV ≤ 0.20 / LOYO ≤ 0.25**:

| rung | 2023 | 2024 | 2025 | pooled | incumbent | CV | G-STABILITY |
|---|--:|--:|--:|--:|--:|--:|:--|
| `PNW_midC` | 1,770 | 1,010 | 1,145 | 1,300 | 1,800 | **0.253** | **FAIL** |
| `DSW_CCGT` | 2,375 | 2,275 | 2,420 | 2,380 | 1,800 | 0.026 | ok |
| `DSW_CT` | 2,375 | 2,275 | 2,420 | 2,380 | 2,200 | 0.026 | ok |
| `WECC_scarcity` | 785 | 180 | 1,080 | 1,000 | 3,000 | **0.550** | **FAIL** |
| **TOTAL** | 7,305 | 5,740 | 7,065 | 7,060 | **8,800** | | |

LOYO (derive on two years, predict the held-out year; bar 25 %):

| held out | `PNW_midC` | `DSW_CCGT` | `DSW_CT` | `WECC_scarcity` | worst | G-LOYO |
|---|--:|--:|--:|--:|--:|:--|
| 2023 | 38.7 % | 1.5 % | 1.5 % | **40.1 %** | 40.1 % | **FAIL** |
| 2024 | 45.5 % | 6.8 % | 6.8 % | **491.7 %** | 491.7 % | **FAIL** |
| 2025 | 19.7 % | 2.9 % | 2.9 % | **57.9 %** | 57.9 % | **FAIL** |

**Both gates fail. The pre-registered stop condition fired: no solve, no arms, no
registration.** The bar was not moved and the gated rung set was not re-scoped to
the subset that passes — that re-scoping is precisely the rule-13 act the
PRECOMMIT forbade, and §D explains why it would also have been *wrong on the
merits*.

## §C — WHY it fails: the estimator, not the object

**§C1 — the measured depths ARE year-stable.** CV across 2023–2025 of the raw
measured corridor percentiles, before any carve-out or differencing:

| | p50 | p95 | **p98** | p99.9 |
|---|--:|--:|--:|--:|
| `WECC_PNW` | 0.837 | 0.036 | **0.042** | 0.064 |
| `WECC_DSW` | 0.036 | 0.040 | **0.042** | 0.044 |
| **TOTAL** | 0.089 | 0.055 | **0.058** | 0.056 |

Every depth statistic the derivation actually uses is stable at **CV 0.04–0.06**,
comfortably inside the 0.20 bar. *(PNW's p50 CV 0.837 is not instability: PNW is
net-EXPORT in 51/38/31 % of hours, so its median sits near zero and its CV is
meaningless. The high tail is unaffected — p98 is +2,566…+2,841 MW in every year.)*
**The object is measurable. The estimator is what fails.**

**§C1a — the rule-14 caveat check passes, and is now checkable rather than
assumed.** The `IMPORT_TRANCHES` provenance block rejects EIA-930 for the FIRM
limb because "their low percentiles are negative: midday solar exports net against
firm imports". That objection is a statement about the **low** tail and does not
transfer to the spot limb, which is by construction the depth **above** the firm
base. Confirmed above: negative-hour shares are 51/38/31 % (PNW), 5.8/5.4/4.9 %
(DSW), 14/11/9 % (total), while every p98/p99.9 used is strongly positive.

**§C2 — the instability is INHERITED FROM THE FIRM CARVE-OUT.**

| derived rung | CV(measured p98) | CV(firm carve-out) | → CV(rung) | |
|---|--:|--:|--:|---|
| `PNW_midC` | 0.042 | **0.165** | **0.253** | opposed → **AMPLIFIES** |
| `DSW_CCGT` / `DSW_CT` | 0.042 | **0.162** | 0.026 | co-directional → **CANCELS** |

The carve-out is **4× noisier than the depth it is subtracted from** — the DMM RA
import measurement moved 1,072 → 1,566 MW (PNW) and 1,251 → 1,805 MW (DSW) across
three years, and 2025 carries the 2024 DMM figure as a declared open data gap. The
NEISO precedent carves out **Highgate's published converter rating**, a *constant*;
CAISO's analogue is a *year-varying measurement with its own error*. That is the
structural reason the port does not transfer.

**§C3 — the scarcity rung is a difference of large numbers.**

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| p99.9(total) | 9,630 | 9,112 | 10,435 |
| − Σ marginal p98 | 8,842 | 8,931 | 9,359 |
| **= scarcity** | **788** | **181** | **1,076** |
| remainder as share of minuend | 8.2 % | 2.0 % | 10.3 % |

CV(minuend) 0.056 and CV(subtrahend) 0.025 — both stable — produce
**CV(remainder) 0.547**: a **9.8× amplification**, and the 491.7 % LOYO error is
the 2024 remainder of 181 MW in the denominator. A rung defined as a 2 % residue of
a 9 GW quantity is not identifiable from three years of data by construction.

**§C4 — and the subtrahend is not a coherent simultaneous depth anyway.** The sum
of marginal p98s exceeds the p98 of the *total* by **969 / 1,126 / 514 MW**,
because the corridors are only moderately correlated (pooled hourly
r = **+0.484**, 26,280 h). Summing marginal percentiles over imperfectly
correlated seams over-provisions routine depth, so the scarcity remainder is
measuring the simultaneity gap as much as any emergency capability.

## §D — The `DSW_CCGT`/`DSW_CT` pass is a CANCELLATION ARTIFACT (against interest)

The two DSW rungs pass both gates decisively (CV 0.026, LOYO ≤ 6.8 %), and they are
exactly the rungs FINDING-caiso140 §C identified as the binding
"2.7–3.0 GW economic-import plateau". It would be easy — and wrong — to admit them
as a partial swap.

**They are not independently stable.** §C2 shows both inputs carry the *same*
0.16 carve-out noise as `PNW_midC`; DSW passes only because its measured depth and
its firm block happened to move **in the same direction** (+645 MW and +554 MW
2023→2025) so the errors subtracted out, while PNW's moved in **opposite**
directions (−128 MW and +494 MW) so they added. With n = 3, co-directional movement
of two independently-noisy series is a **coincidence of this sample, not a
structural property** — and the 2025 firm value is not even an independent
observation, since it carries 2024's DMM figure forward.

A partial swap would therefore be admitting a rung whose apparent stability is an
artifact of an error cancellation that no forward year is obliged to repeat. It is
refused, and the refusal is recorded here rather than left implicit.

## §E — What the exercise DOES establish: the incumbent ladder is over-deep

This is the durable contribution, and it is a **measurement**, not a fit.

| year | incumbent total ladder | measured p98 | measured p99.9 | measured max | **ladder − p99.9** |
|---|--:|--:|--:|--:|--:|
| 2023 | 11,123 | 7,873 | 9,630 | 13,136 | **+1,493** |
| 2024 | 12,171 | 7,805 | 9,112 | 13,312 | **+3,059** |
| 2025 | 12,171 | 8,845 | 10,435 | 15,080 | **+1,736** |

*(MW. Ladder = 8,800 MW spot + the year's DMM RA firm block.)*

**CAISO's model import stack is 1.5–3.1 GW deeper than the 99.9th percentile of
what the seam has ever actually delivered**, and the derived total (7,060 MW
pooled, §B) is **20 % shallower** than the incumbent 8,800 MW. The direction is
consistent with the standing residual: FINDING-caiso232 §D measures
corr(monthly residual, model import volume) = **+0.419** and December — the model's
highest-import month at 7,082 MW — as the flattest, largest positive residual. An
over-deep stack of above-market-priced import capability is a mechanism that would
produce exactly that.

**This is stated as a target for a future lane, NOT acted on here.** It is not a
derivation of the four rungs — it is a bound on their sum, and the pre-registered
gate that would have licensed a swap failed. Converting it into a depth cut now
would be fitting a total to a residual with no per-rung identification, which is
the rule-13 act this session exists to avoid.

## §F — What a viable estimator would need (so the next lane does not re-run this)

1. **Do not carve the firm block out of the measured depth.** The carve-out
   injects 0.16 CV into a 0.042 CV measurement. Either derive the **total** stack
   depth against the total flow distribution and let the firm block sit inside it,
   or derive the spot depth on the subset of hours in which the firm block is
   verifiably at schedule.
2. **Do not define scarcity as a residue.** Size it directly against the total
   flow distribution (e.g. the p99.9−p98 *interval*), not as
   p99.9(total) − Σ marginal p98, which amplifies noise 9.8× and double-counts the
   0.5–1.1 GW simultaneity gap.
3. **Gate the quantity that is actually identifiable.** The measured record
   identifies the **total** envelope (CV 0.056) far better than any per-rung split;
   an estimator whose gated object is the total, with rungs placed by a fixed
   zero-DOF convention inside it, is the NYISO precedent and is the obvious next
   candidate — **pre-registered before it is run**, not selected after seeing which
   estimator passes.
4. **DO-NOT-REDO: the straight NEISO port.** It is measured, decomposed and
   refused here on its own pre-registered gates. Re-running it is not new evidence.

## §G — Record changes

* Keeper, markers, freeze, determination (**NOT-YET**, C3a sole load-bearing
  FAIL at +4.1 / +12.5 / +15.6 %): **UNCHANGED**.
* **No dashboard registration** — no run was solved (rule 15 applies to completed
  runs; the caiso-134/140/150/202/232 disposition).
* Matrix (rule 28(b), **CAISO shard only**) — **evidence append, no verdict move**:
  `import_hub_pricing` (K) gains this session's depth measurement and the
  DO-NOT-REDO on the ported estimator. No `ScenarioConfig` field was added, so
  rule 28(c) does not apply.
* The DOF ledger entry `spot_capacity` stays **OPEN** — still
  `RESIDUAL (static, no cited primary source)`, now with a measured envelope
  bound, a refuted estimator, and a specification for the next one.
