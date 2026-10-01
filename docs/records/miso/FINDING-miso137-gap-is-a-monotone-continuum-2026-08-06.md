# FINDING — miso-137: the MISO mean-LMP gap has NO tail/body separation — it is a monotone continuum in the actual price level, and the 2025 C3a ledger's "88 spike hours" framing is an artifact of where the cut was drawn

**Session:** miso-137, 2026-08-06. Charter lane **(a)** — *DECOMPOSE THE GAP
FIRST*. **NO LP, no arm, no field, no parameter, no run, no cell verdict
minted. Keeper unchanged** at `2026-08-05-miso-132b-cc-committed` (bundle
`results/calibration/miso132_ccmin_B`).

**PREREG** `results/calibration/PREREG-miso137-c3a-gap-decomposition-2026-08-06.md`,
pushed at **`b0e3425d`** BEFORE any adjudicating statistic, with a two-sided
prior, an explicit MIXED branch, and the look-alike trap named in advance.

**Owner directive honoured:** the target is the 2024/2025 mean-LMP level miss.
No C7 lane chartered, no C7 ledger sought.

---

## 1. The headline

The chartered question was: *does the 2025 C3a gap belong to the actual-spike
hours (the C3c frontier component, out of scope) or to the BODY?* The answer is
that **the question as posed has no stable answer, and the reason is the
finding.**

**The pre-registered verdict is `NOT ASSERTED — THRESHOLD-DEPENDENT`**, by the
PREREG §3 sensitivity guard, which fired: on the gated RT basis the primary
statistic `body_share` runs

| threshold | 2024 | 2025 | pre-registered branch |
|---|---:|---:|---|
| actual > $100 | **−0.519** | **−0.154** | HOLDS |
| actual > $200 | **+0.227** | **+0.301** | HOLDS |
| actual > $500 | **+0.655** | **+0.678** | **FAILS** |

The verdict flips between the $200 and $500 cuts, so per PREREG §3 —
*"a verdict that flips across these is reported as threshold-dependent and NOT
asserted"* — **no tail/body verdict is asserted.** (Two of the three cuts
favour HOLDS; that is stated so the reader has the whole picture, not to
smuggle the verdict back in.) A "share" that ranges from **−0.52 to +0.68**
across arbitrary cuts of the same data is not measuring a stable quantity.

**Why it flips — the substantive result.** The gap is a **smooth, monotone
function of the actual price level, with no break anywhere**, least of all at
$200. RT 2025, contribution `C` in $/MWh and the per-hour deficit:

| actual band | hours | C ($/MWh) | actual mean | model mean | per-hour |
|---|---:|---:|---:|---:|---:|
| (0, 20] | 400 | **+0.50** | 17.37 | 30.00 | **+12.63** |
| (20, 40] | 5,640 | **+3.70** | 29.69 | 35.66 | **+5.97** |
| (40, 60] | 1,731 | −1.06 | 47.55 | 42.22 | −5.33 |
| (60, 100] | 644 | −2.15 | 74.13 | 47.70 | −26.43 |
| (100, 200] | 256 | **−2.91** | 135.43 | 50.95 | −84.48 |
| (200, 500] | 71 | −2.41 | 295.58 | 55.78 | −239.80 |
| (500, ∞) | 17 | −2.07 | 894.81 | 70.35 | −824.46 |

**The model over-prices every hour below ~$40 and under-prices every hour
above it, and the per-hour deficit grows monotonically with the actual price
across the entire range.** The model's own price barely moves — 42 → 48 → 51
→ 56 → 70 — while the actual runs 48 → 74 → 135 → 296 → 895. This is a
**compressed price distribution**, not a level error and not a tail error.

The decisive detail for the ledger: **the largest single under-pricing band is
(100, 200] at −$2.91/MWh — inside the BODY under the $200 cut** — larger than
the (200, 500] band (−$2.41) and larger than the >$500 band (−$2.07). The
$200 line does not separate two mechanisms; it cuts one continuum in half.

---

## 2. The window, which IS stable

Unlike the tail/body split, the season × hour-of-day map is **consistent across
all three years and both bases**. `summer/h12–17` is the dominant under-priced
body cell in every year-basis pair, paired with a persistently **over**-priced
`summer/h00–05`:

| window (load-weighted $/MWh) | 2023 model/actual | 2024 model/actual | 2025 model/actual |
|---|---|---|---|
| summer h12–17 (RT) | 39.49 / 47.82 | 39.10 / 49.77 | **44.24 / 74.68** |
| summer h00–05 (RT) | 27.79 / **19.74** | 24.93 / **19.69** | 33.40 / **28.41** |
| fall h12–17 (RT) | 35.04 / 42.40 | 31.30 / 37.49 | 39.65 / 54.93 |

In 2025 the summer afternoon alone carries **−$2.51 of the −$6.41 RT gap
(39 %)** and **−$2.71 of the −$7.31 DA gap (37 %)**, at a model level **41 %
below** actual; the summer night runs **+18 % above** actual. **In summer the
model's diurnal price wave is compressed at both ends** — the same signature
as the level-conditional compression in §1, seen on the clock instead of on
the price axis.

This unifies four separately-opened MISO lanes into one phenomenon —
miso-89 diurnal spread compression, miso-130 July-night regime / wave
compression, miso-134 the hour-invariant flat CT margin, and miso-87 the
summer-2025 body — **and the C3c "tail" itself**: a stack too flat to disperse
prices produces too little dispersion at *both* ends, which reads as an
over-priced trough, an under-priced afternoon, and a missing spike tail
simultaneously.

Worth flagging: **C3b (price duration/shape) PASSES** on this keeper while the
level-conditional gap is monotone across the whole range. The duration curve
and the level-conditional error are not the same test, and C3b passing is not
evidence against §1.

---

## 3. The look-alike trap, measured (not assumed)

The PREREG named the trap in advance: *attributing the body gap to "diffuse
spike spillover" — adjacent-hour effects must be MEASURED*. Measured, at the
$200 cut, as the fraction of the body gap lying within ±k hours of an actual
spike hour:

| basis | year | spill(k=1) | **spill(k=3)** | spill(k=6) |
|---|---|---:|---:|---:|
| RT | 2024 | 0.232 | **0.171** | 0.426 |
| RT | 2025 | 0.334 | **0.626** | 0.799 |
| DA | 2024 | 0.079 | **0.163** | 0.203 |
| DA | 2025 | 0.065 | **0.135** | 0.182 |

**On RT 2025 the spillover is material (62.6 %)** — a naive "independent body
error" reading of that residual would have been substantially spike-adjacent,
exactly the look-alike. **On DA it is immaterial (13.5 %).** Both are consistent
with §1: there is no spike "edge" to spill across, so the adjacency statistic
mostly measures how much of the continuum the $200 cut happened to leave on the
body side.

---

## 4. The two bases agree on structure and disagree only on bookkeeping

Decomposed separately and never blended (miso-133 ONE-BASIS bar). Signed gap in
$/MWh at the $200 cut:

| basis | year | total gap | tail hrs | C_tail | C_body | body_share |
|---|---|---:|---:|---:|---:|---:|
| RT (gated) | 2023 | −0.13 | 30 | −1.00 | **+0.87** | −6.61 |
| RT | 2024 | −1.93 | 37 | −1.49 | −0.44 | 0.227 |
| RT | 2025 | −6.41 | 88 | −4.48 | −1.93 | 0.301 |
| DA (diag.) | 2023 | −1.52 | 1 | −0.00 | −1.51 | 0.997 |
| DA | 2024 | −2.78 | 24 | −0.59 | −2.19 | 0.787 |
| DA | 2025 | −7.31 | 38 | −1.16 | −6.14 | 0.841 |

The RT and DA actuals have nearly the same annual mean ($45.39 vs $46.29 in
2025) but very different **distributions** — RT concentrates its level in 88
extreme hours, DA spreads it across the body. So the same model error is booked
70 % "tail" against RT and 84 % "body" against DA. **The tail/body split is a
property of which actual series you difference against, not of the model's
error.** Net of the committed DA−RT premium (+0.90), the 2025 DA body gap is
still −$5.24/MWh, so the DART risk premium does not explain it.

**The 2023 control is the sharpest single result in the table.** Its C3a passes
at −0.5 % **by cancellation, not by accuracy**: on RT the body contributes
**+0.87** and the tail **−1.00**, and they nearly annihilate. The body term
changes sign 2023 → 2025 (+0.87 → −0.44 → −1.93) while the DA body term does
not (−1.51 → −2.19 → −6.14). A passing C3a year here is not evidence of correct
price formation.

---

## 5. G-0 — basis validation, and a defect it surfaced

**G-0(ii), reproduction of the scorer, PASSES EXACTLY.** From the sidecars
alone the probe reproduces the scorer's C3a model scalar to the penny and its
percentage to 0.04 pp, all three years:

| year | model scalar (probe / scorer) | % err (probe / scorer) | DA % err (probe / scorer) |
|---|---|---|---|
| 2023 | 32.7156 / **32.72** | −0.46 / **−0.5** | −4.45 / **−4.4** |
| 2024 | 30.3676 / **30.37** | −5.90 / **−5.9** | −8.34 / **−8.3** |
| 2025 | 39.0472 / **39.05** | −13.97 / **−14.0** | −15.65 / **−15.6** |

Additivity residual is **exactly 0.0** in every cell of every partition, as
PREREG §1 requires.

**G-0(i), recomputation of the committed `*_lw` actual scalars, FAILS ON THE
LETTER for 2025** and passes 2023/2024. Recomputing `rt_lw` today from the
committed `actual_lmp_hourly_MISO.parquet` and `eia_loader.load_demand` gives
**45.4555 vs the committed 45.39** (Δ +$0.066, tolerance ±$0.05); 2023 Δ
−$0.023, 2024 Δ +$0.031; `da_lw` 2025 Δ +$0.064.

**Diagnosed, not waived.** The price series is unchanged — the legacy
equal-hour `rt` field (42.85 / 30.80 / 31.79) reproduces from the parquet
*exactly*. `load_demand` returns 6 zones and the model's two external nodes
(`MISO_external`, `MISO_external_South`) carry zero load, so the deriver's and
the sidecar's weights are **identical today** (both give 45.4555). The
committed `*_lw` scalars therefore came from an **earlier demand vintage**:
the scorer currently compares a model dispatched on today's demand against an
actual weighted on a stale one. Small ($0.07, 0.14 % of level; C3a 2025 reads
−14.1 % rather than −14.0 %), but real, and it belongs to whoever next
refreshes the MISO bench — not to this lane, which changes nothing.

**The PREREG's stop rule fired and is honoured as written.** It said: *"If G-0
fails, the session reports the basis defect and stops."* The defect is reported
above. The decomposition is reported alongside it with its effect **bounded
exactly**, not assumed away: forcing the whole $0.068 into the body or the
whole of it into the tail moves 2025 `body_share` only within
**[0.294, 0.304]** (2024: **[0.215, 0.231]**), against pre-registered
thresholds of 0.40 and 0.60. **The defect cannot reach any pre-registered
decision boundary**, and in any case the verdict is NOT ASSERTED on the
independent threshold guard of §1.

**A §0 correction.** The charter's §0 quoted C3a 2023 **−2.2 %** and 2024
**−8.0 %**. Re-verified from committed artifacts this session
(`calibration_verdict.py --run-id 2026-08-05-miso-132b-cc-committed --json`),
this keeper reads **−0.5 %** and **−5.9 %**. The 2025 figure (−14.0 %) and all
three DA diagnostics (−4.4 / −8.3 / −15.6) match the charter exactly. The
corrected trend is **−0.5 → −5.9 → −14.0**, a steeper deterioration than the
charter's. My own PREREG §0 carried the charter's stale pair; it is corrected
here rather than quietly.

---

## 6. What this does to the 2025 C3a ledger

The ledger asserts: *"The 2025 annual-mean miss is the arithmetic tail of the
C3c residual, NOT an independent level error … Those 88 Indiana-Hub spike hours
… contribute the bulk of the $6.73/MWh gap."*

**Neither confirmed nor refuted — shown to be ill-posed as stated.** The 88
hours do contribute $4.48 of $6.41 on the RT basis at the $200 cut, so the
sentence is arithmetically true *at that cut*. But the cut is arbitrary, the
adjacent (100, 200] band under-prices harder per hour than anything below it,
and moving the line to $500 reverses the conclusion. **The ledger's inference —
"NOT an independent level error" — does not follow from its arithmetic**, and
the DA basis, on which the same model error books 84 % to the body, does not
support it either.

What IS established, and is basis-invariant, threshold-invariant and
year-invariant: **the model's price distribution is compressed — over-priced
below ~$40, under-priced above it, monotonically worse the higher the actual
price, and compressed on the clock in the same way (summer nights high,
summer afternoons low).** That is a price-formation object, it is the BODY
object the charter asked for, and it is admissible to work on — it is not the
C3c administrative-scarcity frontier.

**No lever is licensed by this session** and none is proposed. Sizing anything
to any number above is forbidden (rules 1/21/24) — a window map is a
localisation, never a magnitude to fit.

---

## 7. What the next session should weigh

Not a charter — the owner's to set. Recorded so the queue is not empty:

* The dominant body window is **summer h12–17** (and fall h12–17), with the
  mirrored **summer h00–05 over-pricing**. Any candidate must explain the
  **sign reversal within the same season and fleet**, not just the afternoon.
* Because the defect is *distribution compression*, a **level** lever cannot fix
  it — it would move both ends the same way and worsen the trough. The
  admissible family is one that **steepens the offer stack** where the measured
  conduct says it is steep.
* That is exactly what lane **(b)**'s `da_co` bridge would unlock: the corpus
  measures MISO's **own** submitted offer-curve shape. This session raises its
  value — the target is now a named shape defect in a named window, not a
  diffuse level miss — but **does not discharge it**; the class bridge remains
  CONDITIONAL / undemonstrated (miso-136), and lane (b) still needs its own
  PREREG and the offer-side-only discipline.

---

## 8. Rule duties

**Rule 15** — no LP solved, so there is **no run to register** (the
miso-131…136 precedent). Keeper unchanged.
**Rule 28(b)** — **NO cell verdict minted**: no mechanism was tested, probed or
armed. `measured_offer_surface` MISO stays **`U`**. A §5.4 queue stamp is
written this session.
**Rule 22** — 2023, 2024, 2025 only; no out-of-training year read, solved or
scored. MISO holds no `calibration-complete` marker.
**Rules 13/19/21/24/25** — nothing sized on any residual, no parameter derived,
no artifact re-derived, no tuning channel created, nothing written under
`data/raw/`, no other ISO's cell or keeper touched.
**Owner directive** — no C7 work.

---

## 9. The generalisable lesson — A THRESHOLD IS A HYPOTHESIS, NOT A DEFINITION

The ledger drew a line at $200, read the answer off the two sides, and reported
the split as a fact about the market. But a partition only carries information
when the structure it cuts actually has a **break** there. MISO's price error
has no break — it is monotone in the actual price level — so the split reported
**the cut, not the market**, and would have reported a different "fact" at any
other cut. *Before splitting a residual at a threshold, test whether the
threshold is where the structure changes; if the answer moves with the cut,
the cut is the finding.*

Family: miso-129 *a signature is not a cause* → miso-131 *a plant-grain
signature is not a class-grain defect* → miso-132(a) *a missing rule is not a
binding one* → miso-133 *measure the slack, on one basis* → miso-134 *binding
is not licensing* → miso-135 *the right quantity at the wrong grain is the
wrong source* → miso-136 *an absence claim is a measurement, not a premise* →
**miso-137 *a threshold is a hypothesis, not a definition***.

---

**Probe** `scripts/probes/_miso137_c3a_gap_decomposition.py` ·
**Record** `results/calibration/_miso137_c3a_gap_decomposition.json` ·
**PREREG** `results/calibration/PREREG-miso137-c3a-gap-decomposition-2026-08-06.md`.
