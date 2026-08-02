# xiso-1 — diurnal price-amplitude compression is SYSTEMIC, not NEISO-specific: 36/36 ISO-year-benchmark cells, mean 41 % of measured

**Date:** 2026-08-01 · **Scope:** cross-ISO audit, all six ISOs, 2023–2025 ·
**Arm A** of the xiso-1 brief. **NO LP SOLVED. No keeper changed, no bundle
produced, no dashboard registration** (same disposition as neiso-71/73/74).
**Probe:** `scripts/probes/_xiso1_diurnal_amplitude_audit.py` (read-only).
**Transcript:** `results/calibration/PROBE-xiso1-diurnal-amplitude-audit-2026-08-01.txt`.

---

## 0. The question and the answer

neiso-74 sized NEISO's keeper at **24–30 %** of the measured diurnal price
amplitude with its level and its phase both correct, and left one question:
**is that NEISO-specific or systemic?** Two other ISOs already carried a
same-shaped finding reached by different routes — miso-89 (29–47 % of the
observed seasonal peak-minus-night spread) and pjm-139/140/141 (31 / 33 / 32 %
of the overnight→evening-peak swing) — but nobody had measured all six ISOs
with **one** construction, so nobody knew whether this was three ISO-specific
defects or one property of the LP.

**It is systemic.** Every one of the **36** ISO × year × benchmark cells
compresses, in the same direction, with the same signature:

* **daily MAX under-priced in 36/36 cells** (−7.5 % … −65.5 %),
* **daily MIN over-priced in 36/36 cells** (+5.9 % … +146.0 %),
* hour-of-day **amplitude** 19.9 % … 92.2 % of measured, **mean 40.5 %** vs DA
  and **43.9 %** vs RT — while the annual **level** is right to a mean absolute
  **7.1 %**,
* **phase is right in 34 of 36 rows** (peak hour within ±1 h of measured; the
  hour-of-day profile correlates +0.85 … +0.98 with the actual everywhere).

The model knows *when* the peak is at every ISO. It clears it too low and holds
the overnight trough too high, everywhere, in every year, against both the DA
and the RT benchmark.

## 1. The measurement

**Model side** — each ISO's **current keeper** at HEAD, read from the live
keeper store and resolved through the registry (the probe re-runs against
whatever the keeper is, not a pinned path):

| ISO | keeper | bundle |
|---|---|---|
| ERCOT | `2026-07-31-ercot148-dam-event-cap` | `ercot148_dam_event_cap_arm` |
| PJM | `2026-07-31-pjm-143b-hy-level` | `pjm143_hy_level_B` |
| CAISO | `2026-07-31-caiso-151-firm-selfsched` | `caiso151_clip_B` |
| NYISO | `2026-08-01-nyiso109-zonal-margin-anchor` | `nyiso109_zonalanchor_B` |
| NEISO | `2026-07-31-neiso-72-hy-window` | `neiso72_hy_window_B` |
| MISO | `2026-07-31-miso-109b-hy-level` | `miso109_hy_level_B` |

`hourly/system_<year>.parquet`, `pass == "P1"`, zone duals load-weighted by the
model's own hourly zonal demand — the C3a basis. The `price` column is the
**delivered** model price: `run_calibration_full._system_frame` writes
`prices[z] + total_overlay`, so ERCOT's RTORDPA / DAM-AS / ORDC terms are
already inside it and the audit-only `*_overlay` columns are **not** re-added.

**Measured side** — `data/raw/_validation-source/actual_lmp_hourly_<ISO>.parquet`,
the committed hub-mean hourly DA/RT series that `scripts/data/derive_actual_lmp.py`
writes **on the model's own chronological 8760-hour calendar**. Model and
measured pair hour-for-hour with no re-keying; that is what makes one
construction portable across six ISOs, and it is why the whole audit costs zero
LP — every keeper since 2026-07-19 ships the sidecars.

**Admissibility.** This is an audit of committed artifacts, not a mechanism. It
reads measured prices and model output and reports; nothing is fed back into any
solve, so rule 13 `[R-MEASURED]` is not engaged. **Rule 25 `[R-ISO-SCOPE]`:
every number below is that ISO's own.** The cross-ISO table answers "is the
defect shared", never "does ISO X inherit ISO Y's number".

**Loader validation.** The NEISO row reproduces neiso-74 exactly on the swapped
loader — level **+2.8 %**, daily MAX **−26.2 %**, daily MIN **+32.6 %**, spread
**$14.62 vs $58.27**, **86/365** days over the 1.25× hurdle, hour-of-day range
**$13.30 vs $44.47**, peak h17 both sides. The portable construction is the same
measurement.

## 2. The answer table — amplitude as % of measured

Hour-of-day mean range, model ÷ actual. (The hour-of-day profile is the robust
statistic: it averages 365 days per hour, so no single scarcity event can drive
it. §5 shows the tail-censoring control.)

**vs measured DA**

| ISO | 2023 | 2024 | 2025 | level error (%) |
|---|---|---|---|---|
| ERCOT | 52.9 % | 38.2 % | 36.7 % | −36.4 / −7.8 / −7.4 |
| PJM | 31.6 % | 36.5 % | 34.2 % | +5.5 / +1.3 / −6.7 |
| CAISO | 46.5 % | 52.9 % | **75.9 %** | −7.9 / −0.3 / +6.3 |
| NYISO | 52.0 % | 50.9 % | 44.5 % | +8.0 / −0.4 / −5.8 |
| NEISO | 27.1 % | **23.6 %** | 29.9 % | +3.9 / +5.0 / +2.8 |
| MISO | 34.0 % | 36.3 % | 25.2 % | −3.2 / −6.4 / −12.8 |
| **all** | **mean 40.5 %** | min 23.6 % | max 75.9 % | mean abs 7.1 % |

**vs measured RT**

| ISO | 2023 | 2024 | 2025 | level error (%) |
|---|---|---|---|---|
| ERCOT | 55.6 % | 41.0 % | 39.8 % | −26.5 / −3.4 / −4.6 |
| PJM | 32.6 % | 32.1 % | 31.9 % | +8.8 / +2.2 / −4.9 |
| CAISO | 66.1 % | 73.1 % | **92.2 %** | +3.6 / +8.4 / +9.4 |
| NYISO | 63.8 % | 48.8 % | 40.9 % | +10.9 / +1.7 / −5.8 |
| NEISO | 27.3 % | 23.0 % | 34.2 % | +7.2 / +10.3 / +5.9 |
| MISO | 35.2 % | 32.2 % | **19.9 %** | +0.5 / −4.7 / −11.0 |
| **all** | **mean 43.9 %** | min 19.9 % | max 92.2 % | mean abs 7.2 % |

**The level is right and the amplitude is not, at every ISO.** Mean absolute
level error 7.1 % (DA); mean amplitude shortfall ~59 %. The two are an order of
magnitude apart, and the level passes largely by cancellation — the trough is
over-priced by as much as the peak is under-priced.

**Reconciliation with the pre-existing cousins** (rule 19 `[R-ONE-MECH]` — this
is the same defect measured a third way, not a new one):

| prior finding | its statistic | its number | this audit, same ISO |
|---|---|---|---|
| pjm-141 | overnight→evening-peak swing | 31 / 33 / 32 % | 31.6 / 36.5 / 34.2 % (DA) |
| miso-89 | seasonal HE16–18 − HE01–03, $200-censored | 29–47 % | 26.3–33.9 % censored daily spread (DA) |
| neiso-74 | hour-of-day range | 27.1 / 23.6 / 29.9 % | identical (loader check, §1) |
| nyiso-109 | trough→peak swing | 69 / 49 / 45 % | 52.0 / 50.9 / 44.5 % (DA) |

Four independent constructions, four ISOs, the same magnitude — nyiso-109's
2023 reads higher than this audit's (69 % vs 52 %) because its statistic is a
trough→peak swing on its own basis rather than the hour-of-day mean range; 2024
and 2025 agree closely. Treat the existing PJM, MISO and NYISO diagnoses as the
ISO-local reports of **this** defect — do not re-derive them.

## 3. Phase is right; only amplitude is wrong

34 of 36 rows put the hour-of-day peak within ±1 h of the measured peak and the
trough within ±1 h. The two exceptions are **CAISO 2025** (model h22 vs measured
h18 — the model's peak sits in the post-sunset net-load ramp rather than the
measured evening peak) and **NYISO 2025** (h19 vs h17). Hour-of-day profile
correlation runs **+0.853 … +0.980** across all 36 rows. Whatever produces the
compression preserves the *shape* of the daily cycle and shrinks its *gain*.

## 4. Attribution — the same offer band is marginal at both ends of the day, at all six ISOs

2025 P1, hour-of-day means, trough hour → peak hour. The signature neiso-74
found at NEISO holds everywhere: the peaking classes are **already loaded at the
overnight trough**, so the merit order never traverses a new rung between night
and peak.

| ISO | demand swing | largest absorber | peaking/oil classes online at trough |
|---|---|---|---|
| ERCOT | 16,118 MW (h03→h16) | solar +16,007 MW (99.3 %) | **3/4** — CT_CHP, CT_PEAKER, ST_GAS, 1,865 MW |
| PJM | 20,739 MW (h03→h17) | CT_PEAKER +6,541 (31.5 %), CC_REGULAR +6,287 (30.3 %) | **3/4** — 1,983 MW |
| CAISO | 8,463 MW (h03→h17) | solar +8,078 MW (95.5 %) | **2/4** — 187 MW |
| NYISO | 5,033 MW (h04→h19) | hydro +1,886 (37.5 %), ST_GAS +926 (18.4 %) | **4/4** — 1,096 MW |
| NEISO | 4,117 MW (h02→h17) | CC_REGULAR +2,045 MW (49.7 %) | **4/4** — 329 MW |
| MISO | 17,423 MW (h02→h17) | CT_PEAKER +3,141 (18.0 %), ST_GAS +2,050 (11.8 %) | **3/4** — 2,874 MW |

Two distinct patterns sit inside one defect, and they should not be conflated:

* **The absorber is a zero-MC resource** (ERCOT, CAISO — solar covers 95–99 % of
  the model's own diurnal demand swing). Here the *thermal* stack barely moves
  between night and peak by construction, and yet these are the **two ISOs with
  the LEAST compression** (CAISO 76 %/92 % in 2025, ERCOT 37–56 %).
* **The absorber is thermal** (NEISO CC_REGULAR, PJM/MISO CT_PEAKER + ST_GAS,
  NYISO hydro + ST_GAS). Here the model does traverse the stack — and these are
  the **most compressed** ISOs. The stack it traverses is too flat: the same
  offer band that is marginal at h02 is still marginal at h17.

The correlation across six ISOs runs the *opposite* way to the naive story: the
compression is worst where the model relies on the thermal merit order to make
the diurnal price and mildest where a large zero-MC block forces a traversal of
the whole stack every day. **That is an observation on six points, not a
mechanism and not a lever** — it is stated here because any successor should
have to explain it.

## 5. Controls — reported against interest

Three ways the headline could be an artifact, all measured:

1. **Load-weighting basis (model side).** Re-running the model amplitude on a
   simple zone mean instead of the demand-weighted C3a basis moves it by
   **≤4.3 pp** at every ISO-year (ERCOT 2025 36.7→34.5 %, PJM 2025 34.2→31.9 %,
   CAISO 2025 75.9→80.2 % — the largest — and NEISO identical to 3 s.f., its
   model zones carrying essentially no price separation). Not a weighting
   artifact.
2. **Hub basis (measured side).** MISO is the only ISO with a committed hourly
   *zonal* actual. Its 5-zone mean has a **smaller** hour-of-day range than the
   hub-mean ($21.75 / $22.56 / $39.93 vs $23.16 / $25.34 / $41.95), so scoring
   against the zonal actual **softens** the finding — MISO amplitude
   34.0→36.2 %, 36.3→40.8 %, 25.2→26.5 %. The defect survives the control that
   works against it, at a magnitude ≤4.5 pp.
3. **Scarcity tail.** Body-censoring at $200 (miso-89's convention) *raises*
   several RT ratios substantially (MISO 2025 12.2→17.9 %, NEISO 2024
   12.9→15.2 %, PJM 2025 19.8→22.6 %), confirming that part of the raw RT daily
   spread is genuinely the price tail. That is why the headline is quoted on the
   **hour-of-day range**, which is tail-insensitive, and why the raw daily-spread
   ratios are the *weaker* claim, not the reported one.

Further caveats, stated rather than buried:

* **ERCOT 2023 is the least interpretable row.** Its amplitude reads 52.9 % but
  its level is off **−36.4 %** — that is ERCOT's known standing C3a FAIL, not an
  amplitude statement. Read ERCOT 2024–25 (38.2 / 36.7 %) as its number.
* **CAISO 2025 vs RT is 92.2 %** — one ISO-year where the defect is very nearly
  absent. That single cell is the strongest evidence *against* reading this as a
  mechanical property of an LP with duals: an LP can reproduce the measured
  amplitude, and at CAISO it does.
* **CAISO 2023 DA covers 360 of 365 days** (OASIS retention); days with a
  missing hour are dropped from the daily statistics and counted, never
  interpolated.

## 6. No criterion sees this — at ANY ISO

neiso-74 flagged this for NEISO. It is general, and confirmed by reading the
scorer rather than by inference:

* **C3a** (`score_price_mean`) is a **level** test. All six models pass it or
  miss it by single-digit percent while running at ~41 % amplitude.
* **C3b** (`score_price_shape`) is a **12-month load-weighted NRMSE** — the
  monthly vector, for **every** ISO, not just NEISO. It is structurally blind to
  hour-of-day: a model can reproduce every month's mean exactly and carry any
  intraday amplitude at all.
* **C3c** is a **tail-hour count**, not an amplitude.
* **C7 / D-1** score **class dispatch** shape (`profile_r` / `cv_ratio`), not
  price, and are SKIPPED at NEISO entirely.

The sharpest statement of the gap: **PJM's keeper is fully `CALIBRATED` —
`price_mean` PASS, `price_shape` PASS, `price_tail` PASS — while reproducing
31.6 / 36.5 / 34.2 % of the measured diurnal price amplitude.** Four of six
keepers pass C3b outright; the two that don't (ERCOT, and MISO's ledgered
caveats) fail it for reasons that are not this.

**Whether the rubric should carry a diurnal-amplitude criterion is an OWNER
CALL.** neiso-74 filed it; this audit does not act on it and did not change the
scorer. What this audit adds is that the gap is not one ISO's — it is the
rubric's, at all six. If the owner wants it gated, the statistic is already
computed here and is cheap (zero LP, keeper sidecars only): hour-of-day mean
range, model ÷ measured, per ISO-year.

## 7. What this audit does and does not license

**Does:** it establishes that six ISOs share one defect, so a *structural*
account of it is a single cross-ISO question rather than six ISO-local ones —
and it gives every ISO's lane its own measured size to judge a successor
against.

**Does not:**

* It does **not** open any adjudicated cell. PJM's diurnal-amplitude family is
  **owner-closed with an empty lever queue** (matrix item 13: `measured_offer_surface`
  R under both conditionings, re-binning barred by rule 23, reserve/scarcity
  owner-closed, `ramp_envelopes` spent, daily gas series barred by the zero
  within-day σ, `gas_commitment_bridge` R at pjm-142). NEISO's named
  identification (§5.6 item 1, DA-bid offer formation) still requires its own
  owner charter — neiso-74 gave it a target, not a charter, and this audit does
  not grant one either.
* It does **not** transfer a verdict (rule 25). NEISO's 24–30 % is not MISO's
  25–36 %; each lane judges its own.
* **It licenses no parameter.** Any adder, multiplier, or hinge sized to close a
  38-percentage-point amplitude gap would be a value fitted to a residual —
  rules 5 `[R-NO-MAGIC]`, 21 `[R-DOF]`, 24 `[R-REGISTRY]`. The defect being
  systemic makes that *more* tempting and no more admissible.
* **A successor must not be graded on the amplitude ratio alone.** neiso-74's
  own caveat generalizes: NEISO's real PS fleet realizes only 45 % of the
  DA-price perfect-foresight optimum, so a price-shape correction that lands the
  amplitude on 100 % while ignoring the non-arbitrage limits would overshoot the
  physical quantities it is supposed to explain.

## 8. Governance

Years 2023–2025 only; the holdout spend freeze is ACTIVE and nothing outside the
training window was read (rule 20 `[R-HOLDOUT]`). No LP solved, no config
changed, no bundle written, **no dashboard registration** — rule 15
`[R-DASHBOARD]` binds bundles, and this audit produces none. Matrix row
`diurnal_price_amplitude` added with all six ISO cells (rule 28c); §5.7 audit
row updated; `docs/calibration-log/governance.md` appended.

**DO-NOT-REDO:** do not re-measure cross-ISO diurnal amplitude. Re-run
`scripts/probes/_xiso1_diurnal_amplitude_audit.py` instead — it reads the live
keeper store, so it re-reports against whatever the keepers are, at zero LP cost.
