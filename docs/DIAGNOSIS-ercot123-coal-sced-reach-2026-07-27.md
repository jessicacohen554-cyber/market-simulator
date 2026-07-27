# DIAGNOSIS — ERCOT-123: the unoffered 83 % of coal DAM headroom is OFFERED in real time; the reach defect is an instrument artifact and no offer-side mechanism is licensed

**Date** 2026-07-27 · **ISO** ERCOT · **Lane** ercot123-coal-sced-reach ·
**Keeper under audit** `2026-07-26-ercot115-coal-marginal-hr` (bundle
`results/calibration/ercot115_coal_floor_only`) — **unchanged by this session** ·
**Chartered by** `docs/DIAGNOSIS-ercot122-coal-offer-envelope-2026-07-27.md`
§4/§5.4 (which refuted the coal offer-LEVEL lever and routed the *reach*
question to the SCED TPO instrument) ·
**Method** Phase 1 only — raw-direct measurement from the 60-Day SCED
disclosure (`scripts/probes/ercot123_coal_sced_reach.py`, sections A–I).
**No LP was built. No year was solved. No arm was registered. No keeper file was
touched.**

**Outcome: Phase 1 does NOT license a mechanism, and Phase 2 was not run.** The
charter's decomposition routes to exactly one of four buckets; the measurement
refutes all four. Bucket (e), the only one that could license an offer-side
withholding mechanism, measures **0.0001–0.0002** of coal's RT-dispatchable
headroom. The DAM reach gap ERCOT-122 found is real as a DAM statistic but is an
**instrument artifact** as a statement about coal's offer behaviour: ERCOT coal
transacts its incremental energy in **real time**, not in the DAM. §7 states the
recommendation; §5 names the one residual the RT instrument does expose and
charters it as a successor rather than building it here.

---

## 1. Headline — the decomposition, and what it kills

Shares of **RT-dispatchable headroom** (`HASL − LSL`), MW-weighted over online
resource-intervals; bucket (c) is over the full telemetered range (`HSL − LSL`).
CC is the control, run through the identical decomposition.

| year | family | class | **(a) TPO-offered** | (b) self-sched | **(e) residual** | (c) AS-held | carries a curve |
|---|---|---|---|---|---|---|---|
| 2024 | tail | **COAL** | **0.9945** | 0.0054 | **0.0001** | 0.0197 | 0.9969 |
| 2024 | control | **COAL** | **0.9998** | 0.0000 | **0.0002** | 0.0204 | 1.0000 |
| 2025 | control | **COAL** | **0.9979** | 0.0019 | **0.0002** | 0.0181 | 0.9963 |
| 2025 | tail | **COAL** | **0.9964** | 0.0035 | **0.0001** | 0.0184 | 0.9876 |
| 2024 | tail | CC | 0.9570 | 0.0351 | 0.0079 | 0.0153 | 0.9518 |
| 2024 | control | CC | 0.9532 | 0.0321 | 0.0146 | 0.0137 | 0.9505 |
| 2025 | control | CC | 0.9810 | 0.0082 | 0.0107 | 0.0062 | 0.9714 |
| 2025 | tail | CC | 0.9852 | 0.0083 | 0.0065 | 0.0080 | 0.9798 |

**Coal offers 99.4–100.0 % of its RT-dispatchable headroom into SCED — a
*higher* reach than the CC control (95.3–98.5 %).** The class that exposes only
16–18 % of its headroom to the day-ahead energy merit order exposes essentially
**all** of it to real time. Over 98.8 % of online coal resource-intervals carry a
submitted TPO curve at all, against a DAM picture in which over half submit no
curve point whatsoever.

This is the answer the charter asked for, and it is decisive:

* **(e) GENUINELY UNOFFERED AND UNUSED — REFUTED.** 0.0001–0.0002 of headroom.
  There is no block to price. Any withholding wall built here would be a fitted
  wall on a measured-empty bucket (rule 13 `[R-MEASURED]`).
* **(b) SELF-SCHEDULED / PRICE-TAKING — REFUTED.** 0.000–0.005 of headroom, and
  *lower* than CC's 0.008–0.035. The independent price-side test agrees: the
  share of coal's offered MW priced below \$0 — the price-taking signature — is
  **0.0000–0.0002**, against CC's 0.0011–0.0344. Coal does not price-take in RT;
  its offers are genuinely economic. The charter's stated inversion ("the model's
  must-run share is too SMALL") is **not** supported on this instrument. See §4
  for the one honest qualification.
* **(c) AS-RESERVED — REAL BUT NOT A LANE.** The awarded up-AS block is 3.3–5.2 %
  of coal's telemetered range and shows up as a 1.5–2.0 % `HSL − HASL`
  reduction. It is a genuine measured power reservation, and it is **already
  modelled** — `ercot_thermal_as_endogenous` prices thermal AS in the
  co-optimisation. Re-reserving it here would be a second mechanism on the same
  phenomenon (rule 19 `[R-ONE-MECH]`).
* **(d) TELEMETERED DOWN — NOT COAL-SPECIFIC, AND IT IS ANOTHER LANE'S.** See §3.

## 2. The charter's buckets (c) and (d) are the same quantity — measured apart

The charter defined (d) as "`HASL < HSL` — the unit itself declared the
capability away". That is not what `HASL` is. ERCOT forms `HASL` by subtracting
the resource's **up-direction AS responsibility** from `HSL`, so the charter's
(d) *is* its (c), and a decomposition using both would have double-counted.
Measured directly:

| year | family | class | `HSL−HASL` mean MW | awarded up-AS mean MW | corr | up-AS share of range |
|---|---|---|---|---|---|---|
| 2024 | tail | COAL | 5.17 | 13.67 | 0.619 | 0.0522 |
| 2024 | control | COAL | 5.72 | 12.41 | 0.624 | 0.0443 |
| 2025 | control | COAL | 5.10 | 11.61 | 0.768 | 0.0411 |
| 2025 | tail | COAL | 4.96 | 11.43 | 0.754 | 0.0425 |
| 2024 | tail | CC | 2.81 | 5.72 | 0.636 | 0.0312 |
| 2025 | tail | CC | 1.63 | 2.30 | 0.701 | 0.0089 |

The gap tracks the AS award (corr 0.62–0.77; the gap is at least the award in
71–98 % of intervals) but is only 38–46 % of it in aggregate — ERCOT does not
push every awarded MW into the `HASL` reduction. Either way the quantity is an
**ancillary-service reservation, not a derate**, and coal carries proportionally
*more* of it than CC (4.1–5.2 % of range vs 0.9–3.1 %). That asymmetry is real
and coal-specific, but at ~4 % of range it cannot carry an over-run of the
observed size, and rule 19 forbids stacking it on the co-optimisation.

## 3. The genuine derate layer — measured, and it exonerates coal

Measured where a derate actually lives (`max HSL(resource, year) − HSL`,
capability the unit is not telemetering at all):

| year | family | class | ref capability GW | derate share | intervals derated >5 % |
|---|---|---|---|---|---|
| 2024 | tail | **COAL** | 13.64 | **0.0630** | 0.289 |
| 2024 | control | **COAL** | 13.59 | **0.0486** | 0.211 |
| 2025 | control | **COAL** | 12.76 | **0.0597** | 0.232 |
| 2025 | tail | **COAL** | 12.75 | **0.0644** | 0.211 |
| 2024 | tail | CC | 64.87 | 0.0867 | 0.605 |
| 2024 | control | CC | 63.05 | 0.0981 | 0.654 |
| 2025 | control | CC | 67.48 | 0.0978 | 0.669 |
| 2025 | tail | CC | 62.58 | 0.0921 | 0.612 |

Coal derates **less** than CC on every subset (4.9–6.4 % vs 8.7–9.8 %), and is
derated >5 % in a fifth to a quarter of intervals against CC's ~two thirds. The
derate layer is not a coal-specific defect, and in any case it is the
**availability envelope's** territory (ERCOT-116 / ERCOT-121), not an offer
question. Routing (d) here would be routing to the wrong instrument.

## 4. The one honest qualification on bucket (b)

**The charter's denominator structurally cannot see the quantity bucket (b) was
meant to detect.** Coal's price-taking base is its **LSL** — min-load energy is
bought regardless of the energy curve — and `HASL − LSL` excludes it by
construction. Measured over the telemetered capability instead:

| year | family | class | LSL / HSL | loading (net output / HSL) |
|---|---|---|---|---|
| 2024 | tail | COAL | 0.4514 | 0.8372 |
| 2024 | control | COAL | 0.4246 | 0.7201 |
| 2025 | control | COAL | 0.4506 | 0.8295 |
| 2025 | tail | COAL | 0.4569 | 0.8758 |
| 2024 | tail | CC | 0.5934 | 0.9387 |
| 2025 | tail | CC | 0.5788 | 0.8967 |

The measured coal base share is **0.42–0.46** on these probe days, against the
model's 0.28 (`FINDING-ercot117` §5.3, which measured 0.49–0.52 on the full RT
instrument and already holds this lane). So the base-share mismatch is real and
this session corroborates it — but it is **not** the charter's bucket (b), it is
**already an open chartered lane**, and its direction is adverse: raising the
must-run base of a class the model already **over-runs** adds forced energy at
the bottom. That is the same arithmetic trap ERCOT-122 caught on the offer-level
lever, and it is flagged here rather than walked into. It stays with ERCOT-117
§5.3, un-renumbered.

## 5. What the RT instrument DOES expose — a missing upper tail, sized and chartered

Measured RT supply as a share of telemetered `HASL`, on the `FINDING-ercot117`
§1.1 convention (curve-carrying units floored at LSL) so it is directly
comparable to that session's model-side figures:

| year | family | class | ≤\$20 | ≤\$25 | ≤\$30 | ≤\$40 | ≤\$100 | ≤\$500 |
|---|---|---|---|---|---|---|---|---|
| 2024 | tail | COAL | 0.705 | 0.916 | 0.925 | 0.948 | 0.963 | 0.997 |
| 2024 | control | COAL | 0.673 | 0.920 | 0.929 | 0.950 | 0.965 | 1.000 |
| 2025 | control | COAL | 0.657 | 0.919 | 0.941 | 0.949 | 0.961 | 0.999 |
| 2025 | tail | COAL | 0.644 | 0.908 | 0.931 | 0.942 | 0.961 | 0.998 |

Below \$25 the model **already matches**: `FINDING-ercot117` §1.1 measured the
model's coal at 0.66 at ≤\$20 and 0.91 at ≤\$25 against the 0.64–0.71 / 0.91–0.92
here — same knee, same level, confirming ERCOT-122's refutation of the
offer-LEVEL lever from the RT side as well.

Above \$25 the two diverge. The measured curve needs **\$500** to reach 1.00; the
model's coal stack is **fully offered by \$32–34** (ERCOT-122 §3: dearest bands
COAL_PRB peak \$32.17 summer / \$34.00 shoulder 2023, \$29.81 in 2025). So the
model over-offers coal by roughly **5–7 pp of HASL in the \$32–100 clearing band
and ~4 pp above \$100** — real coal keeps a thin, genuinely expensive tail out of
the merit order that the model has no representation of at all.

Full-year ERCOT RT price distribution (share of hours, full span, not probe-day):

| year | <\$25 | \$25–30 | \$30–35 | \$35–40 | \$40–60 | \$60–100 | ≥\$100 |
|---|---|---|---|---|---|---|---|
| 2024 | 0.712 | 0.090 | 0.055 | 0.033 | 0.057 | 0.035 | 0.018 |
| 2025 | 0.466 | 0.158 | 0.097 | 0.072 | 0.122 | 0.062 | 0.025 |

**Indicative sizing, explicitly labelled as a hand calculation:** ~5–7 pp of the
9.1–9.6 GW of online coal HASL (interval-mean, this instrument), over the 14 % (2024) / 28 % (2025) of hours
clearing ≥\$35, is of order **0.6–1.6 TWh/yr**. The probe deliberately does *not*
compute this in code — a probe-day supply share is not an annual weight, and
multiplying them would manufacture an annual statistic the instrument cannot
support. Treat it as an order of magnitude only.

That is a genuine, measured, coal-specific offer-**shape** defect, and it is
**not** the closed offer-LEVEL lane: ERCOT-122 refuted a rebasis of the level
(`econ_low` / top-of-curve p50, which would move the model's coal *down*); this
is the **upper tail** of the same distribution, measured on a different
instrument at ~99 % curve coverage rather than the 21–47 % coverage that
invalidated the pooled `econ_high`. The two measurements agree with each other —
ERCOT-122's ~\$42.8 was the p50 of the minority who submit that high, and this
session finds that minority's MW is ~5 pp of HASL.

**It is nevertheless NOT built here.** The charter fires Phase 2 only on "bucket
(e) or (b) with a measured level"; this is neither — it is bucket (a)'s price
composition, a quantity first measured this session. It is also ~0.6–1.6 TWh against
the ERCOT-116 envelope's +6.8/+9.2/+12.9 TWh, identified on 2024–2025 probe days
with **no 2023 instrument in existence**, and it would interact directly with the
existing COAL_PRB `peak` band and the ercot115 marginal-HR floor — an
enumeration rule 19 requires *before* a mechanism, not after. It is chartered as
the successor in §7.2 with its own pre-commit.

## 6. Cross-checks — all three required checks pass

**(i) Bench reconciliation.** The SCED CLLIG fleet's telemetered net output
against the EIA-930 benchmark coal series on the same hours:

| year | family | hours | SCED mean MW | bench mean MW | ratio | corr |
|---|---|---|---|---|---|---|
| 2024 | tail | 300 | 7,664 | 7,827 | 0.979 | 0.956 |
| 2024 | control | 264 | 6,914 | 7,058 | 0.980 | 0.964 |
| 2025 | control | 264 | 7,777 | 7,986 | 0.974 | 0.964 |
| 2025 | tail | 240 | 8,189 | 8,293 | 0.988 | 0.971 |

Ratio 0.974–0.988, corr 0.956–0.971. The instrument measures the fleet we score
against. The small consistent shortfall is the expected direction: the ERCOT-121
§1a SCORING-data caveat (Parish 3470's bench series carries its gas steamers) is
**carried unfixed**, as the charter required.

**(ii) Probe-day sampling.** DAM reach recomputed on the SAME probe days and
hours, against the full-year figure:

| year | class | full year | probe days | delta |
|---|---|---|---|---|
| 2024 | COAL | 0.1844 | 0.1741 | −0.0103 |
| 2025 | COAL | 0.1610 | 0.1556 | −0.0054 |
| 2024 | CC | 0.5941 | 0.5970 | +0.0029 |
| 2025 | CC | 0.6775 | 0.6713 | −0.0062 |

Deltas ≤0.010 on both classes and both years — the probe days are representative
on the very instrument that generated the charter, and ERCOT-122's
0.184/0.161 reproduce. The DAM↔RT comparison is on one footing.

**(iii) CC control.** Run through the identical decomposition in every section.
The result is coal-specific in the *opposite* direction from the charter's
expectation: coal's RT reach **exceeds** CC's. Nothing here looks damning for
coal and matches CC, so nothing is being mistaken for a coal mechanism — the
control that saved ERCOT-122 from a false conclusion does the same job here.

**(iv) Utilization, an added check.** Evaluating each unit's own TPO curve at the
prevailing hourly RT settlement price and comparing to its telemetered output:

| year | family | output / own offered-at-price | summer | non-summer |
|---|---|---|---|---|
| 2024 | tail | 0.957 | 0.963 | 0.953 |
| 2024 | control | 0.981 | 0.975 | 0.987 |
| 2025 | control | 0.968 | 0.964 | 0.972 |
| 2025 | tail | 0.973 | 0.981 | 0.970 |

**At the actual clearing price, real ERCOT coal delivers 96–98 % of what its own
RT offer curve makes available**, with only a 1.6–4.0 pp offset and no material
summer/non-summer split. Real coal is not being held back below its offers.
Combined with §1, the real fleet's coal output is very nearly "everything it
offers, at the price" — which is exactly what the model does. (Hourly-price
approximation: the 5-minute SCED LMP is not on disk, so interval-level dispersion
around the hourly mean adds noise in both directions; the bias is second order
over ~20,000 intervals per subset but the number is an approximation and is
labelled as one.)

## 7. Recommendation — recommend-and-STOP (keeper untouched; owner decides)

1. **Phase 2 is NOT run, and the reach question is CLOSED.** ERCOT-122 §4's
   reading — "the error is in how much coal is offered, not what it is offered
   at" — is **refuted on the RT instrument**. The model's ~100 % coal offer reach
   is *correct*; ERCOT-121 §1a's "all five Oak Grove tranches at max 744/744 h"
   is not an offer-reach defect and should not be pursued as one. Do not re-open
   the DAM reach statistic as evidence of coal offer behaviour: it measures QSE
   self-supply bypassing DAM transaction, exactly as `FINDING-ercot117` §1.1
   suspected, and ERCOT coal's incremental energy is transacted in real time.
2. **Successor charter — the coal offer-curve UPPER TAIL** (§5). Extend the
   model's coal stack with a measured high-priced top tranche (~5–7 pp of
   available capability above the current \$32–34 top), *re-shaping the existing
   COAL_PRB `peak` band rather than adding a mechanism* (rule 19). Its
   pre-commit must: enumerate every mechanism already flooring or capping coal
   (D-2 attribution, the ercot115 marginal-HR floor, the ERCOT-116 envelope);
   declare ex ante that the parameter is identified on **2024–2025 SCED only** so
   its 2023 application is an **extrapolation**, and gate that (rule 24 LOYO
   per-year, 2-of-3 is FAIL); and carry the C7/C8 exposure — the direction
   *reduces* coal forcing, which should help the live COAL_LIGNITE 2023 D-1 C7
   FAIL (0.745/0.294), but that must be gated, not assumed.
3. **ERCOT-117 §5.3 (the coal price-taking base) stays where it is**, corroborated
   by §4 here (measured 0.42–0.46 vs model 0.28) and with its adverse direction
   now on the record. **ERCOT-120** remains a separate, un-renumbered lane,
   unaffected by this session.
4. **Two inherited owner decisions, surfaced once and not decided here.**
   (a) Whether to run the ERCOT-122 offer-level arm as a **registered controlled
   refutation** for the record — ERCOT-122 recommended against (the direction is
   arithmetic) and this session's §5 adds independent RT-side confirmation that
   the model already matches below \$25, which strengthens that recommendation;
   it remains one `replay_keeper` away and DIAGNOSIS-ercot122 §5.1 is its
   pre-commit. (b) The **committed-band data gap**: the SCED disclosure **does**
   carry `Min Gen Cost` (present, and populated on 29–31 % of online coal
   resource-intervals across the four subsets), but it is the
   **RT** instrument on 82 probe days, not the DAM committed band. Flagged as
   existing; **not** used, transformed, or approximated toward reconstructing the
   DAM committed band, which stays an owner decision.
5. **New data-contract finding, for whoever intakes SCED next.** ERCOT **revised
   the 60-Day SCED disclosure schema in December 2025**: `HASL`/`LASL` and the
   `Ancillary Service <svc>` **award** block are dropped outright and replaced by
   `AS Capability <svc>` + `Ramp Rate Up/Down`, and `Telemetered Net Output`
   loses its trailing space. AS *capability* is not AS *award*, and `HASL` is not
   recoverable from the new layout. This probe coalesces the two net-output
   spellings and **drops the Dec-2025 intervals explicitly** (15,146 of 85,694
   and 17,387 of 87,792 online rows on the two affected subsets; delivery days
   2025-12-10, 2025-12-15, 2025-12-20) rather than letting them silently NaN out
   of the aggregates. Any future SCED loader must handle the revision explicitly.

## 8. Closed items honoured; scope and environment

No year solved, no run registered, no arm built;
`frontend/data/backcast/keepers/ERCOT.json` untouched. The session's diff against
`origin/main` is **one new file**, `scripts/probes/ercot123_coal_sced_reach.py`
— no `ScenarioConfig` field, cache-key surface, solve path, or existing artifact
was touched, so no config pin moved and no existing run can change. Holdout years
untouched (rule 22 `[R-HOLDOUT]`): the SCED subsets are 2024–2025, in-window, and
no 2022-or-earlier SCED was read; §I2's price distribution is 2024–2025 only. No
GitHub Actions workflow was added. Rule 23 `[R-FROZEN-DERIVE]` honoured — every
quantity is read from the raw disclosure against the charter's measurement
question; no residual entered any derivation, and no derive script was
re-derived (the CC and coal artifacts are untouched and byte-identical).

Closed lists honoured: the coal offer-**LEVEL** lane as an over-dispatch/clawback
fix and the pooled `econ_high` 2.856 (ERCOT-122 §1/§3) — §5 independently
*confirms* the refutation below \$25 and is explicit that the upper-tail finding
is a different moment on a different instrument, not a re-opening; the EP-rebasis
lane as a C3c fix and the peak-p50/quantile-ladder legs (ERCOT-119); age/temp
coal derates (ERCOT-121 §1a); the pooled HH-0.50 artifacts;
`ercot_zonal_gas_basis` ablations; the West/Panhandle topology split. The wtx
Panhandle stack and CC offer-dispersion lanes were not touched.

**Sampling bound, carried on every number above.** The SCED evidence is **82
probe days across 2024–2025 only** — no 2023 SCED exists on disk and no full-span
SCED exists at all. Three of the four subsets sample **hours 11–22 only**; the
hour-of-day bias is bounded directly rather than assumed, on the one all-24-hour
subset (`2025_ercot86_tail_days`): coal (a) 0.9929 in h11–22 against 0.9998 in
h23–h10, (e) 0.0002 against 0.0001, i.e. coal's RT reach is if anything *higher*
overnight and the headline conclusion does not depend on the daytime sampling.
Nothing here is an annual statistic.

**Pre-existing test state (reported, not chased, pins untouched):**
`tests/regression/test_persisted_identity.py` cache-key pin fails on clean
`origin/main` — 2 failed, 9 passed — and this session's diff against main is
empty apart from the new probe, so the failure is inherited, not caused.
