# FINDING — nyiso-232: NYISO's C3a residual is **TWO separable objects**, and a zero-LP tail-removal test separates them cleanly — the extreme-event tail, and a gas-monotone tilt that **survives removing it**

**Session** nyiso-232 · **ISO** NYISO · **Date** 2026-09-13 · **ZERO LP**
(every number is read from the designated keeper's **committed** `hourly/` sidecars —
`results/calibration/nyiso231_anchor_span` — and `data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet`.)

The nyiso-232 handoff ranked this object #2 and set the method: *"Do NOT assume a second
anchor-family mechanism; re-derive the regression on the NEW keeper's own hourlies first … and see
what shape is left before proposing anything."*

**A correction to this document's own first draft, kept visible rather than quietly fixed.** On the
monthly regression alone (§2) I first concluded that the leftover slope "is not a gas object" and
recommended spending nothing further on it. **The tail-removal test in §5 falsified that**, and the
recommendation is reversed. The monthly r² was real but I read it wrong: a *year-constant* regressor
cannot explain more than the *between-year* share of a monthly residual, and within-year scatter here
is 4× the between-year spread — so a low monthly r² was never evidence that the year-level tilt is
not gas. §5 is the test that actually separates them, and it is the load-bearing section.

---

## 1. THE ANNUAL RELATIONSHIP SURVIVES — AND IT IS FOUR POINTS

Reconstructed from the keeper's own sidecars (load-weighted over all zones):

| year | model $/MWh | actual $/MWh | residual | gas anchor $/MMBtu |
|---|---:|---:|---:|---:|
| 2022 | 73.13 | 80.37 | **−9.01 %** | 8.4431 |
| 2023 | 32.44 | 32.05 | **+1.23 %** | 3.3566 |
| 2024 | 38.52 | 38.13 | **+1.02 %** | 2.7969 |
| 2025 | 62.49 | 66.35 | **−5.82 %** | 5.5602 |

Annual spread **10.23 pp**; residual vs anchor **r = −0.970, r² = 0.941, slope −1.93 pp per
$/MMBtu** — still monotone, still tight, exactly as the handoff said.

*(Basis note: this reconstruction is a plain all-zone load-weighted mean and lands within ~0.9 pp of
`calibration_verdict.py`'s scored C3a — −9.9 / +0.6 / +1.1 / −5.9 %. It is used here for SHAPE, not
as the scored number, and nothing below turns on the difference.)*

## 2. AT THE GRAIN WHERE THE ERROR ACTUALLY LIVES, THE GAS RELATIONSHIP LARGELY EVAPORATES

Re-measured at **monthly** grain, n = 48, against the year's gas anchor and against the load level —
so the answer was free to come back "not gas":

| regressor | r | r² |
|---|---:|---:|
| year gas anchor | −0.354 | **0.125** |
| load level (GW) | −0.253 | 0.064 |
| both jointly | — | **0.175** |

**Gas explains 12.5 % of the MONTHLY residual variance** — but read that carefully, because the
first draft of this document read it wrong. The gas anchor is **constant within a year**, so it can
never explain more than the *between-year* share of a monthly series, and §2's own next table shows
within-year scatter is 4× the between-year spread. A low monthly r² is therefore evidence that the
**monthly** error is dominated by something month-scale — not evidence that the **year-level** tilt
is not gas. §5 tests that properly.

**And the something larger is 4× the slope itself:**

| | measured |
|---|---:|
| WITHIN-year monthly residual spread | **42.4 / 39.0 / 48.5 / 42.1 pp** (2022/23/24/25) |
| ACROSS-year annual residual spread — the whole "slope" | **10.2 pp** |

A 10 pp year-to-year tilt is being read off a series whose month-to-month scatter inside a single
year is 39–48 pp. The tilt is real; it is a small residue riding on a much bigger error the annual
average hides.

## 3. THE BIG ERROR IS NOT DIFFUSE — IT IS A HANDFUL OF DAYS

Share of each year's total load-weighted price gap carried by its worst days:

| year | annual gap | worst 5 days | worst 10 days | the worst three days |
|---|---:|---:|---:|---|
| **2022** | **−$1,105.5 M** | **58.4 %** | **78.5 %** | 2022-12-24, 2022-12-23, 2022-01-16 |
| **2025** | **−$585.7 M** | **76.5 %** | **108.4 %** | 2025-06-24, 2025-06-23, 2025-07-01 |
| 2023 | +$57.7 M | *n/m* | *n/m* | 2023-02-04, 2023-09-05, 2023-02-03 |
| 2024 | +$58.7 M | *n/m* | *n/m* | 2024-12-22, 2024-06-17, 2024-12-21 |

**2023 and 2024 are marked *n/m* deliberately and their concentration shares are NOT quoted.** Their
annual gaps are ~$58 M against a ~$2.5 bn base — the near-perfect cancellation of large offsetting
days — so the share statistic divides by approximately zero and returns meaningless values
(−353 %, −288 %). Reporting them as if they meant something would be the defect this finding is
about. What IS meaningful about those two years is §2: their monthly spreads are 39.0 and 48.5 pp,
the largest of the four, while their annual residuals are +1.2 % and +1.0 %.

**Winter Storm Elliott, priced day by day.** Dec-2022, daily load-weighted:

| date | model | actual | gap |
|---|---:|---:|---:|
| 2022-12-23 | **$70.2** | **$383.0** | −81.7 % |
| 2022-12-24 | **$79.9** | **$747.8** | −89.3 % |
| 2022-12-25 | $74.9 | $166.8 | −55.1 % |
| 2022-12-26 | $75.7 | $218.4 | −65.3 % |
| 2022-12-27 | $77.1 | $138.3 | −44.3 % |

The model sits essentially **flat at $70–80** straight through a five-day event in which the real
market cleared a daily average of up to **$748/MWh**. That is not an offer-level error of any size;
it is the absence of a scarcity price-formation mechanism.

**2025's worst days are June 23–24 and July 1 — a HEAT event, not a cold one.** So the object is
*extreme events*, not *winter*, and a seasonal or winter-fuel mechanism would be the wrong shape.

## 4. WHY A GAS CORRELATION EXISTS AT ALL — AND WHY IT IS NOT A LEVER

The two years with a material extreme-event miss (2022, 2025) are **also the two high-gas years**.
In a four-point sample, delivered gas and extreme-weather scarcity are collinear. nyiso-231's phase 0
disclosed exactly this caveat before its own span — *"gas and price level are collinear, so
correlation alone cannot separate this from generic variance compression"* — and its span was the
decisive test: the anchor gate closed **the part that really was gas level** (spread 19.9 → 11.0 pp).
What it could not close is the part that was never gas.

**So the r² = 0.9955 regression nyiso-231 inherited was real, and it was mostly two objects wearing
one coat.** One has been closed. The other is the tail.

## 5. THE TEST THAT SEPARATES THEM — and the tilt SURVIVES

The two candidate objects are collinear in an annual average, so the question is put directly:
**progressively remove each year's highest-ACTUAL-price hours and watch what happens to the tilt.**
If the tilt is an artifact of the tail it must collapse; if it is a separate object it must not.
Zero LP, on committed sidecars, with the excluded set chosen on the **actual** series so the model's
own behaviour cannot select it.

| hours excluded (per year) | 2022 | 2023 | 2024 | 2025 | **spread** | r vs gas | r² |
|---|---:|---:|---:|---:|---:|---:|---:|
| none (all 8760 h) | −9.01 | +1.23 | +1.02 | −5.82 | **10.23** | −0.970 | 0.941 |
| worst 25 h (0.29 %) | −5.19 | +4.87 | +4.69 | −1.06 | **10.06** | −0.987 | 0.974 |
| worst 50 h (0.57 %) | −3.88 | +6.55 | +5.89 | +0.34 | **10.43** | −0.982 | 0.965 |
| worst 100 h (1.14 %) | −1.92 | +8.88 | +7.45 | +1.64 | **10.80** | −0.962 | 0.926 |
| worst 200 h (2.28 %) | +0.46 | +11.22 | +9.31 | +3.36 | **10.76** | −0.942 | 0.888 |
| worst 438 h (5.00 %) | +4.12 | +14.21 | +11.91 | +6.14 | **10.09** | −0.915 | 0.837 |

**The spread does not move. At all.** 10.23 → 10.06 → 10.43 → 10.80 → 10.76 → 10.09 pp while 5 % of
hours are removed, and the gas correlation stays between −0.92 and −0.99 throughout. **The tilt is
invariant to the tail.**

**This is the separation nyiso-231 said correlation alone could not perform.** Its phase 0 disclosed
the confound honestly — *"gas and price level are collinear, so correlation alone cannot separate
this from generic variance compression"* — and its span separated the first half by solving. This
separates the second half at zero LP: whatever the tail is doing, it is not producing the tilt.

**So there are two objects, and they decompose cleanly:**

* **OBJECT A — a LEVEL error carried by the extreme tail.** Removing 5 % of hours lifts *every*
  year's residual by **≈ +13 pp**, and the sign flips: with the tail gone the model is **over**-priced
  by **+4.1 to +14.2 %** in every one of the four years. That is the whole story of §3 and §4, and it
  says something sharper than "the model misses scarcity": **the model compensates for the tail it
  cannot form by pricing ordinary hours too high.** The two errors partly cancel in the annual mean,
  which is why C3a passes in 2023/2024 while both components are large. This is C3c / issue #1344.
* **OBJECT B — a gas-monotone TILT of ≈ 10.1–10.8 pp**, present at every cut, r² 0.84–0.97. This is a
  real, separate, gas-level object and the anchor gate closed only part of it (19.9 → 11.0 pp).

**Recommendation, reversed from this document's first draft: object B IS worth a mechanism**, and it
is the better-posed of the two because it is now demonstrably not a tail artifact. The handoff's
instruction stands, though — *do not assume a second anchor-family mechanism*. What the evidence
licenses is that a gas-level object survives; it does not say the next mechanism is another anchor.
Object A is the larger number and the harder problem, and it remains issue #1344.

**A caution that belongs with object A, from the same table.** Any mechanism that raises ordinary-hour
prices to close the headline C3a will make object A's over-pricing worse, because with the tail removed
the model is *already* +4 to +14 % over. The headline residual is a difference of two large errors of
opposite sign, and it should not be optimised directly.

## 6. AGAINST THIS SESSION'S OWN LEVER, STATED PLAINLY

This session's ST_GAS econ de-leak (`nyiso_st_gas_econ_bands_deleaked`,
`PRECOMMIT-nyiso232-st-gas-deleak.md`) makes the model **cheaper in every hour**. On the finding
above it therefore makes this residual **worse**, not better — most in 2022, the year whose gap is
58 % five days. That is consistent with what the PRECOMMIT pre-registered (a C3a-2022 stop is the
expected screen outcome) and it is the reason the de-leak is argued as a **legitimacy** repair under
rules 25/26 and never as a price lever. Nothing in this finding supports it; it is recorded because
it is true.

## 7. RULES

1 `[R-STRUCT]` — the object is identified by what the mechanism would have to be, not by what would
move the residual; a finding that argues against this session's own arm is reported at full
magnitude. 13 `[R-MEASURED]` — every number is a measurement on committed artifacts; nothing is
fitted. 19 `[R-ONE-MECH]` — C3a's residual slope and C3c are shown to be one phenomenon, so they are
not chased twice. 28 `[R-MECH-MATRIX]` — no cell verdict rests on this; it constrains NYISO's lever
queue rather than adjudicating a mechanism. 32 `[R-SHARD]` — zero LP.
