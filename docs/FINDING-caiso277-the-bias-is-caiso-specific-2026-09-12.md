# FINDING — caiso-277: THE MARGINAL-OFFER BIAS IS **CAISO-SPECIFIC**, NOT A PROGRAM-LEVEL OBJECT. The caiso-277 charter's own premise is falsified, and caiso-276's successor recommendation is withdrawn.

**Session caiso-277, 2026-09-12. Cross-ISO measurement, CAISO lane. ZERO LP, ZERO fleet
rebuilds, no arm, no `ScenarioConfig` field, no run registered, no keeper changed in any ISO.**
Rule 25 `[R-ISO-SCOPE]`: nothing measured in one ISO is transferred to another; no ISO's cell
verdict moves.

Instrument: `scripts/probes/_caiso277_crossiso_hr.py`.
Output: `results/calibration/_caiso277_crossiso_hr.json`.

---

## §0 — THE RESULT, AND THE CORRECTION IT FORCES

caiso-276 refused the C3a-2022 arm and recommended the residual be pursued as a **program-level
object** in "a cross-ISO marginal-offer-formation charter". This session ran that measurement
first, as it should have been run before any charter was written. **The premise is false.**

Measured over **every registered keeper in every ISO — 288 ISO-months, 24 ISO-years, 7 ISOs**,
the implied-marginal-heat-rate bias `dHR = (price_model − price_actual) / gas`:

| | pooled |
|---|--:|
| ISO-months measured | **288** |
| dHR positive | **170 (59.0 %)** — barely above a coin flip |
| pooled mean dHR | **+0.037 MMBtu/MWh** — essentially **zero** |
| per-ISO mean range | **−0.717 (PJM) … +0.629 (CAISO)**, spread **1.346** |
| ISOs with a positive mean | **3 of 7** |

**There is no program-level bias.** Pooled across the program the effect vanishes. What exists is
**one ISO that runs high, two that run low, and four that are indistinguishable from zero.**

### The per-ISO test, on the COMMON WINDOW every ISO shares (2023–2025, 36 months each)

This is the apples-to-apples cut, and it is the one that matters: the full spans are unequal
(CAISO 48 months including its folded 2022 rung, ERCOT 60 including 2021–22, the other five 36),
and CAISO's 2022 is the most extreme year in the whole record — so a pooled comparison could
have been an artifact of *which* years each ISO contributes.

| ISO | n | dHR > 0 | dHR mean | sd | se | **t vs 0** | verdict |
|---|--:|--:|--:|--:|--:|--:|---|
| **CAISO** | 36 | **75.0 %** | **+0.534** | **0.794** | 0.132 | **+4.03** | **POSITIVE** |
| ERCOT | 36 | 36.1 % | −0.625 | 1.478 | 0.246 | **−2.54** | **NEGATIVE** |
| PJM | 36 | 38.9 % | −0.717 | 1.499 | 0.250 | **−2.87** | **NEGATIVE** |
| NYISO | 36 | 63.9 % | +0.299 | 2.173 | 0.362 | +0.83 | not distinguishable from 0 |
| MISO | 36 | 61.1 % | −0.002 | 1.395 | 0.232 | −0.01 | not distinguishable from 0 |
| NEISO | 36 | 61.1 % | −0.185 | 1.473 | 0.246 | −0.75 | not distinguishable from 0 |
| SPP | 36 | 58.3 % | −0.028 | 1.596 | 0.266 | −0.11 | not distinguishable from 0 |

**CAISO is the ONLY significantly positive ISO, and its positivity is not a 2022 artifact — it
survives the common window at t = +4.03.** Two ISOs run significantly in the *opposite*
direction. Four are noise.

**A second signature, and it is the more interesting one: CAISO's dHR standard deviation (0.794)
is the LOWEST of all seven** (every other ISO 1.40–2.17). CAISO carries a **small, highly
systematic** bias; the others carry **large noise around zero**. A consistent small offset in one
ISO and mean-zero scatter in six is the signature of a **structural mechanism specific to that
ISO**, not of a shared model-class defect in marginal-offer formation.

### Why ERCOT's own span is a warning about unequal windows

ERCOT reads **+0.052 (t = +0.17, indistinguishable from 0)** over its full five-year span but
**−0.625 (t = −2.54, NEGATIVE)** on 2023–2025. Its 2021 Uri year pulls the mean up and flips the
sign of the conclusion. **This is exactly the failure mode the common-window leg exists to catch**,
and it is why the §0 table is read on 2023–2025 rather than on the pooled spans.

---

## §1 — G-REPRO: the instrument reproduces the committed record exactly

| check | measured | expected |
|---|--:|--:|
| CAISO 2022 model load-weighted price | **94.069** | 94.069 (caiso-276 §1) |
| CAISO 2022 gated actual (`bench.avgLMP.rt_lw`) | **84.49** | 84.49 |
| **verdict** | **PASS** | |

Both sides are on the scorer's own basis: the model side is the demand-weighted zonal price from
each keeper's committed `hourly/system_<year>.parquet` (zero-demand import buses carry zero weight
and drop out exactly as in `score_price_mean`), and the actual side is the committed
`bench/<ISO>/<year>.json.gz` `rt_lw` / `rt_lw_mon`.

**The gas denominator is MEASURED, shared, and cheap.** caiso-270 and caiso-276 both took it from
the keeper's re-assembled fleet (`reconstruct_bundle_fleet`) — minutes per ISO-year, and hours
across 24. It is not the only admissible series, and it is not the best one. `dHR` needs **one gas
series per ISO-month applied to both sides** (caiso-270 §4's own discipline: "both sides at the
same delivered-gas series"), so this probe uses
`data.fuel.plant_prices.iso_monthly_gas_prices` — the **EIA-923 Schedule-5 volume-weighted
delivered gas cost across the ISO's own plants**. It is rule-14 `[R-ACCURATE]` preferable to a
model-internal array, it has **12/12 month coverage for every ISO-year in the record**, and it
reads in seconds. **No fleet rebuild ⇒ no shard ⇒ no LP** (rule 32 `[R-SHARD]` (a) keeps all of it
in the parent).

---

## §2 — WHERE EVERY KEEPER ACTUALLY STANDS ON C3a

Recomputed from committed artifacts, on the gated basis, for all 24 registered keeper-years:

| ISO | year | model lw | actual | gap $ | gap % | C3a ≤ ±10 % |
|---|--:|--:|--:|--:|--:|---|
| **CAISO** | **2022** | **94.07** | **84.49** | **+9.58** | **+11.34** | **FAIL** |
| CAISO | 2023 / 2024 / 2025 | 55.89 / 37.55 / 37.07 | 54.17 / 34.65 / 34.42 | +1.72 / +2.90 / +2.65 | +3.18 / +8.36 / +7.69 | PASS |
| ERCOT | 2021 … 2025 | 174.85 / 68.40 / 60.12 / 30.89 / 33.80 | 165.53 / 74.44 / 64.32 / 30.99 / 36.29 | +9.32 / −6.04 / −4.20 / −0.10 / −2.48 | +5.63 / −8.12 / −6.53 / −0.32 / −6.85 | PASS |
| MISO | 2023–2025 | 34.47 / 32.88 / 42.64 | 32.85 / 32.30 / 45.46 | +1.62 / +0.58 / −2.82 | +4.92 / +1.80 / −6.20 | PASS |
| NEISO | 2023–2025 | 37.59 / 42.42 / 69.69 | 38.10 / 41.68 / 70.23 | −0.51 / +0.74 / −0.54 | −1.34 / +1.77 / −0.77 | PASS |
| NYISO | 2023–2025 | 33.65 / 40.15 / 61.60 | 32.25 / 38.12 / 66.43 | +1.40 / +2.03 / −4.83 | +4.34 / +5.33 / −7.27 | PASS |
| PJM | 2023–2025 | 29.43 / 30.03 / 42.33 | 29.58 / 31.36 / 45.89 | −0.15 / −1.33 / −3.56 | −0.50 / −4.24 / −7.77 | PASS |
| SPP | 2023–2025 | 25.37 / 25.47 / 28.79 | 25.13 / 25.45 / 28.60 | +0.24 / +0.02 / +0.19 | +0.96 / +0.07 / +0.66 | PASS |

**CAISO-2022 is the single failing keeper-year in the entire program.** Three ISOs sit *below*
actual in their latest year (ERCOT −6.85 %, PJM −7.77 %, MISO −6.20 %, NYISO −7.27 %) — the
opposite sign to CAISO's miss. A lever that lowered marginal offers program-wide would push four
ISOs further out of band.

---

## §3 — THE POOLED GAS-BIN TABLE: no program-level gas-proportionality either

caiso-270 §4's own bins, pooled across all seven ISOs:

| gas $/MMBtu | n | HR model | HR actual | dHR | gap $ |
|---|--:|--:|--:|--:|--:|
| (0, 3] | 114 | 14.22 | 14.58 | **−0.363** | −1.02 |
| (3, 5] | 103 | 9.65 | 9.29 | +0.361 | +1.48 |
| (5, 8] | 47 | 8.76 | 8.58 | +0.178 | +1.01 |
| (8, 12] | 16 | 8.13 | 7.79 | +0.349 | +3.50 |
| (12, 20] | 5 | 6.48 | 6.51 | −0.031 | −0.77 |
| (20, 70] | 3 | 13.40 | 13.07 | +0.336 | −9.41 |

**dHR does not grow with the gas level and is not even consistently signed across bins.** The
gas-proportionality caiso-276 §3 measured is a **CAISO-within-2022** property, not a program
property. The `(0, 3]` bin — the largest, 114 months — is *negative*.

---

## §4 — WHAT IS CORRECTED, AND WHAT SURVIVES UNTOUCHED

### 4a — The misstatement, and where it came from

caiso-276 cited caiso-270 §4 as establishing the bias "in **40 of 48 ISO-months**", and read that
as a cross-ISO, program-level fact. **caiso-270 §4 says "all 48 months of 2022-2025" and it is
CAISO ONLY** — 4 years × 12 months of one ISO. It is 40 of 48 **CAISO** months. Nothing
cross-ISO was ever measured, in that session or any other, until now.

The phrase is corrected in place at every occurrence
(`FINDING-caiso276-…` §9.3 and §10.2, the caiso-276 entry in `docs/calibration-log/caiso.md`, and
the CAISO matrix shard's 2026-09-12 re-stamp). **The 40/48 measurement itself is not disputed** —
this session independently returns 39 of 48 positive CAISO months (81.2 %), on a measured rather
than model-internal gas series.

### 4b — caiso-276's REFUSAL stands in full; its SUCCESSOR RECOMMENDATION is WITHDRAWN

**Nothing in the refusal depended on the cross-ISO premise.** All four of its kills are
CAISO-internal measurements on CAISO's own committed solution:

1. the belly object carrying +0.250 of +9.579 (2.6 %) with the belly core unbiased (hod 14 −0.003);
2. 2022 being one object — December's dHR ranking 3 of 12, z = +0.51 vs the ex-December mean;
3. 647.7 MW of 22,354 MW idle-while-in-the-money, and the seam binding in zero hours;
4. the offer channel spent including CT_CHP, on the OASIS file's own provenance.

So **C3a-2022 remains refused and CAISO remains CALIBRATED.** What is withdrawn is caiso-276
§10.2's sentence that "the honest venue is a cross-ISO marginal-offer-formation charter, not a
CAISO held-out-year lane". **The venue is CAISO.** The measurement does not weaken the refusal; it
re-points the successor.

### 4c — And the re-pointing is a SHARPER lead than the one it replaces

Six other ISOs run the **same ISO-agnostic LP**, the same P0→P1 bid-cost pass, the same
`offer_curve_by_group` machinery, the same duals-as-prices rule — and **none of them carries this
bias**; two carry its opposite. So the carrier is something **CAISO has that the other six do
not**, and it is small and systematic rather than noisy (sd 0.794 against 1.40–2.17).

That is a much narrower search space than "marginal-offer formation across the program", and it is
enumerable from the keeper's own armed posture. **Named here as the open question, NOT proposed as
a lever** (rule 1 `[R-STRUCT]` — this session selects nothing): CAISO's distinctives include the
per-hub intertie with its two signed corridors, the **24.06 TWh of forced firm-import energy**
D-2 attributes in 2022 alone (versus 17.51 TWh of nuclear must-run), the four-tranche DSW
clean-depth family, the solar-belly scale, and `caiso_offer_surface_measured` /
`…_ungrounded`. Which of those — if any — carries a +0.5 MMBtu/MWh systematic offset is
**unmeasured**, and measuring it is the next charter's job.

---

## §5 — DISCLOSURES AGAINST INTEREST

1. **This session's headline is that MY OWN PRIOR SESSION'S recommendation was wrong.** caiso-276
   wrote a handoff charter on an unverified premise, and the first thing that charter's own
   measurement did was falsify it. The lesson is the charter should have been the measurement:
   a premise cited from another session's §-reference is not a measurement until it is re-read.
2. **The refusal it was attached to is unaffected** (§4b), and no determination, keeper, gate or
   registered number moves in any ISO.
3. **This is a KEEPER-POSTURE comparison, not a like-for-like model comparison.** Each ISO's
   keeper carries its own armed mechanism set, its own fleet representation (CAISO and ERCOT
   `plant_level_fleet` / `use_campd_bins`; others legacy bins), and its own measured-input
   inventory. So "CAISO is biased high and PJM low" is a statement about **the keepers as they
   stand**, not a controlled experiment isolating one mechanism. It is the right statement for
   deciding where to look next, and the wrong statement for attributing cause.
4. **The t-statistics assume the 36 monthly dHR values are independent**, which they are not
   (serial correlation within a year, and a common gas series). They are reported as a
   **magnitude-and-sign screen**, not as inference — which is all that is needed to separate
   "+4.03" from "−0.01", and is not enough to support a p-value. No conclusion here rests on a
   threshold near 2.0: CAISO is +4.03 and the four null ISOs are |t| ≤ 0.83.
5. **The CV-ratio "additive vs multiplicative" form test is uninformative where the mean is near
   zero** (CV = sd/|mean| explodes: MISO's raw CV is 929.7). It is therefore **gated on |t| ≥ 2**
   and reported as UNDETERMINED for the four null ISOs — the honest answer, not a reading. Only
   CAISO (multiplicative-on-gas) and PJM (multiplicative-on-gas) carry a determinable form.
6. **Unequal spans are a real limitation and the reason for §0's common-window leg.** ERCOT's sign
   flips between its full span and 2023–2025 (§0). The pooled 288-month numbers in §0 and the §3
   bin table are reported for completeness but the **common window is the load-bearing cut**.
7. **CAISO's 2022 row is a folded held-out rung**, from `caiso275_B_gascoupling_2022` rather than
   the span bundle. It is included so CAISO contributes the year caiso-276 was built on and so
   G-REPRO can check against a published number. It is **excluded from the common-window leg** by
   construction, and rule 30(c) `[R-TOUCHPOINT-FOLD]` still applies: it never downgrades the ISO.
8. **Rule 15 `[R-DASHBOARD]` raises no duty**: zero LP ⇒ no bundle ⇒ nothing to register.
9. **Rule 28(b) moves no cell.** This session tested no mechanism — it measured seven keepers'
   solved output. The only matrix edit is the §4a correction to the CAISO shard's own re-stamp
   prose.

---

## §6 — THE DECISION CARD (rule 1 `[R-STRUCT]`: measurement and options, no selection)

1. **Accept that the object is CAISO-specific**, and that caiso-276's cross-ISO successor
   recommendation is withdrawn. Nothing else in caiso-276 changes.
2. **The next charter, if you want one, is a CAISO ABLATION CENSUS, not a cross-ISO one**: take
   CAISO's armed distinctives (§4c) and ask which could produce a **+0.5 MMBtu/MWh systematic,
   low-variance** offset that six other ISOs do not carry. The zero-LP half is enumerable from the
   committed run configs and D-2 attribution; only the confirming A/B would need LP, and that A/B
   would be per-year shards under rule 32.
3. **Or stop.** CAISO is CALIBRATED on 2023–2025, every other ISO passes C3a in every registered
   year, and CAISO-2022 is a held-out rung that rule 30(c) says never downgrades the ISO. The
   program-wide C3a position is **23 of 24 keeper-years inside the band**. There is a defensible
   reading in which nothing here needs fixing at all, and this session does not argue against it.
4. **A caution to carry into any of the three**: four ISOs sit *below* actual in their latest year
   (ERCOT −6.85 %, PJM −7.77 %, NYISO −7.27 %, MISO −6.20 %). A mechanism that lowered marginal
   offers program-wide would push all four further out of band. Whatever is done must be
   CAISO-scoped, which rule 25 `[R-ISO-SCOPE]` requires anyway.

## §7 — RULE LEDGER

| rule | discharge |
|---|---|
| 1 `[R-STRUCT]` | No lever selected, no mechanism proposed. §4c names an open question; §6 hands options to the owner. |
| 14 `[R-ACCURATE]` | The gas denominator is the measured EIA-923 series in preference to a model-internal array. |
| 15 `[R-DASHBOARD]` | Zero LP ⇒ no bundle ⇒ no registration duty. |
| 25 `[R-ISO-SCOPE]` | Seven ISOs measured, zero verdicts transferred, no other ISO's keeper/log/shard touched. |
| 28(a) | Nothing re-tested: this measures solved output, it arms nothing. |
| 28(b) | No cell verdict moves (no mechanism tested); the CAISO shard's own prose correction is §4a. |
| 30(c) `[R-TOUCHPOINT-FOLD]` | CAISO's folded 2022 rung is reported and excluded from the common window; it downgrades nothing. |
| 31 `[R-RETAIN]` | Nothing deleted; no bundle produced. |
| 32 `[R-SHARD]` | **Zero LP and zero fleet rebuilds**, so there was nothing to shard — the measured gas series removed the only expensive compute (§1). |
