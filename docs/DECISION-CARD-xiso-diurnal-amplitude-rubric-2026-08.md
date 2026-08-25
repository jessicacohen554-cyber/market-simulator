# DECISION CARD — should the rubric gain a DIURNAL PRICE-AMPLITUDE criterion?

> **RULED 2026-08-25 (session `xiso-amplitude-rubric-card`): OPTION B — ADDED AS
> REPORTED-ONLY, AND BAND-FREE.** The owner selected (B), the recommendation
> below. **Rubric v3.5** adds **D-A** (`calibration_verdict.score_diurnal_amplitude`,
> rubric §D-A): the hour-of-day amplitude ratio, phase check and profile
> correlation are published on every run and contribute **no status and no
> caveat budget**. Band-free per §5(B): no external comparable exists to anchor
> a threshold, so the number is published without a verdict. **`CRITERIA`,
> `LEDGERABLE_CRITERIA` (`{price_tail}`) and `MAX_LEDGERED_CAVEATS` (1) are
> UNCHANGED, and no determination moved** — verified by re-scoring all 55
> registered runs before and after (zero diffs; 161 D-A records, 0 skipped),
> pinned by `test_IT_CANNOT_GATE`. Scorer-only: every already-registered run
> scores in place, no solve and no bundle regeneration.
>
> **Two things the ruling deliberately does NOT do**, both established below and
> unchanged by it: **§6 stands — NEISO's PS lane is NOT unblocked** (the
> DO-NOT-REDO is a mechanism finding; a criterion changes no dispatch), and the
> open act there remains a charter for the neiso-76 stack-traversal route. And
> **the defect itself is not closed** — (B) is a disclosure, so nothing is
> obliged to close it; §5(C)'s cost is mitigated, not paid.
>
> Carried in the same amendment, found while implementing and reported rather
> than buried: `REPORTED_ONLY` records were **computed and silently dropped**
> since v2.9 (so C5a `co2` reported nothing) — now surfaced in a `reported`
> block; and `lmpDeltaHr`'s `-32768` NaN sentinel, unmasked, inflates MISO 2025's
> amplitude from 20.8 % to 186.9 % — masked here, and **filed for other lanes:
> at least seven committed probes decode that field directly.**

**Raised by session `xiso-amplitude-rubric-card`, 2026-08-25.** The call was
filed first by **neiso-74** (2026-08-01) and re-filed by **xiso-1** (2026-08-01);
it has never been answered. **THE CARD ITSELF DECIDED NOTHING** — the ruling
above was taken by the owner on the analysis below, which is preserved verbatim
as the basis for it.

**No solve was spent.** Every number is measured on committed artifacts
(`scripts/probes/_xiso6_amplitude_criterion_band_probe.py`, transcript
`results/calibration/PROBE-xiso6-amplitude-criterion-bands-2026-08-25.txt`;
amplitude re-taken by
`results/calibration/PROBE-xiso1-diurnal-amplitude-audit-RETAKE-2026-08-25.txt`).
**The scorer was NOT changed** — `scripts/calibration_verdict.py`,
`rubric-consts.js`, `CRITERIA`, `LEDGERABLE_CRITERIA` and `MAX_LEDGERED_CAVEATS`
are untouched; the hypothetical aggregation is replayed inside the probe. No
keeper moved, no determination was re-written, no dashboard status regenerated,
no matrix cell verdict moved (rule 26 `[R-MECH-MATRIX]`: no mechanism was
tested). Rule 22 `[R-HOLDOUT]`: 2023–2025 only, nothing spent.

---

## 0. THE ASK, in one line

xiso-1 measured a defect present in **36 of 36** ISO × year × benchmark cells
that **no criterion sees**. Decide whether the rubric gains a criterion that
sees it — and if so, at what tier and what band.

## 1. THE ONE-PARAGRAPH ANSWER

**A gating criterion is not available at any band, and the reason is not
squeamishness about the verdicts — it is that the criterion has no anchored band
and no single object to measure.** Across ten candidate bands it is either
**vacuous** (amplitude floor ≤ 20 % of measured: every keeper passes, 0 of 3
`CALIBRATED` determinations move — a gate that certifies a model reproducing a
fifth of the measured daily price swing) or **universal** (floor ≥ 45 %: five or
six of six ISOs `FAIL`, all 3 `CALIBRATED` determinations lost). The entire
dynamic range sits between floors of **20 % and 45 %**, a window inside which any
choice is a number picked to produce a desired verdict — and the rubric has no
external comparable to anchor it, which is the *exact* ground on which the owner
**retired C7 diurnal shape outright** five days after xiso-1 filed this question
(rubric v3.1, 2026-08-06). Worse for the "one criterion" premise: the four ISOs
that have since decomposed their own cell **disagree about what the statistic is
measuring**, in two cases with opposite sign. **Recommendation: option (B),
REPORTED-ONLY and band-free** — which is precisely what v3.1 did to diurnal
*dispatch* shape (gate deleted, D-1 measurement kept). The claim that any of this
unblocks NEISO's PS lane is **withdrawn**, on evidence, in both directions.

---

## 2. PHASE 0.1 — the measurement re-taken at HEAD

All six keepers have promoted since xiso-1 measured, so every cell is re-taken,
not carried forward. **The finding reproduces.**

| ISO | keeper at HEAD | 2023 | 2024 | 2025 | worst |
|---|---|---:|---:|---:|---:|
| ERCOT | `2026-08-25-234-eastex-identity` | 41.0 % | 77.3 % | 49.0 % | 41.0 % |
| PJM | `2026-08-15-pjm-162-inputclock` | 31.2 % | 29.5 % | 32.0 % | 29.5 % |
| CAISO | `2026-08-17-caiso-200-h1-memberpanel` | 67.0 % | 73.3 % | 89.2 % | 67.0 % |
| NYISO | `2026-08-22-nyiso-152-duty-complete` | 58.5 % | 46.5 % | 38.7 % | 38.7 % |
| NEISO | `2026-08-17-neiso-99-joint-p1` | 27.1 % | 22.9 % | 33.2 % | 22.9 % |
| MISO | `2026-08-22-miso-177-rho-measured` | 36.3 % | 32.0 % | 20.8 % | 20.8 % |

Hour-of-day mean range, model ÷ measured, **vs RT** — the basis C3a gates on
(`score_price_mean`: RT is the honest benchmark, DA only a fallback). Mean
**44.8 %** vs RT and **41.5 %** vs DA, against xiso-1's 43.9 % / 40.5 %. Daily
MAX under-priced and daily MIN over-priced in 36/36 cells; phase right in 34/36.
**No cell is stale and none is missing** — every keeper ships the sidecars.

One cell moved materially: **ERCOT 2024, 38.2 → 72.0 % (DA)**, on the ercot234
keeper. It is the only ISO-year in which the defect has visibly improved, and it
does not change the picture at any other ISO.

*Reported against interest:* the scorer emits **STALE BENCHMARK** alarms for
PJM, CAISO and NEISO parts. Those bear on C1's metered actuals, not on the
amplitude statistic (which reads keeper hourly sidecars and the committed actual
LMP directly), but they sit on the transcript rather than filtered out of it.

## 3. PHASE 0.2 — THE DECISIVE MEASUREMENT: band × ISO → determination

Base determinations at HEAD, from the unmodified scorer: **PJM, NYISO, NEISO
`CALIBRATED`**; ERCOT, CAISO, MISO `NOT-YET` (C3a and/or C3b fails they carry
independently of this question).

Criterion form: two-band on `|amplitude_ratio − 1|`, worst-year aggregation —
the shape every magnitude criterion in the rubric already uses (`_band_result`,
`_agg_status`). Cell = criterion status / resulting determination. **vs RT, at
LOAD-BEARING tier** (the supporting-tier table is **identical** — see §4a):

| target/comm | amp floor | ERCOT | PJM | CAISO | NYISO | NEISO | MISO | CAL lost |
|---|---|---|---|---|---|---|---|---|
| ±0.20/±0.35 | ≥80 % / ≥65 % | FAIL/NOT-YET | FAIL/NOT-YET | CAV/NOT-YET | FAIL/NOT-YET | FAIL/NOT-YET | FAIL/NOT-YET | **3/3** |
| ±0.30/±0.45 | ≥70 % / ≥55 % | FAIL/NOT-YET | FAIL/NOT-YET | CAV/NOT-YET | FAIL/NOT-YET | FAIL/NOT-YET | FAIL/NOT-YET | **3/3** |
| ±0.40/±0.55 | ≥60 % / ≥45 % | FAIL/NOT-YET | FAIL/NOT-YET | PASS/NOT-YET | FAIL/NOT-YET | FAIL/NOT-YET | FAIL/NOT-YET | **3/3** |
| ±0.50/±0.65 | ≥50 % / ≥35 % | CAV/NOT-YET | FAIL/NOT-YET | PASS/NOT-YET | CAV/**CWC** | FAIL/NOT-YET | FAIL/NOT-YET | **3/3** |
| ±0.55/±0.70 | ≥45 % / ≥30 % | CAV/NOT-YET | FAIL/NOT-YET | PASS/NOT-YET | CAV/**CWC** | FAIL/NOT-YET | FAIL/NOT-YET | **3/3** |
| ±0.60/±0.75 | ≥40 % / ≥25 % | PASS/NOT-YET | CAV/**CWC** | PASS/NOT-YET | CAV/**CWC** | FAIL/NOT-YET | FAIL/NOT-YET | **3/3** |
| ±0.65/±0.80 | ≥35 % / ≥20 % | PASS/NOT-YET | CAV/**CWC** | PASS/NOT-YET | PASS/CAL | CAV/**CWC** | CAV/NOT-YET | **2/3** |
| ±0.70/±0.85 | ≥30 % / ≥15 % | PASS/NOT-YET | CAV/**CWC** | PASS/NOT-YET | PASS/CAL | CAV/**CWC** | CAV/NOT-YET | **2/3** |
| ±0.75/±0.90 | ≥25 % / ≥10 % | PASS/NOT-YET | PASS/CAL | PASS/NOT-YET | PASS/CAL | CAV/**CWC** | CAV/NOT-YET | **1/3** |
| ±0.80/±0.90 | ≥20 % / ≥10 % | PASS/NOT-YET | PASS/CAL | PASS/NOT-YET | PASS/CAL | PASS/CAL | PASS/NOT-YET | **0/3** |

*(CWC = `CALIBRATED-WITH-CAVEATS`. "CAL lost" = how many of the three
currently-`CALIBRATED` ISOs stop being `CALIBRATED`. The DA table is in the
transcript; it is uniformly harsher — at floor ≥70 % **all six** ISOs FAIL.)*

**Stated plainly, as the charter asks.** At every band from ≥40 % upward, **all
three** currently-`CALIBRATED` ISOs (PJM, NYISO, NEISO) stop being `CALIBRATED`.
At ≥35 % and ≥30 %, **two of three** stop (PJM and NEISO drop to
`CALIBRATED-WITH-CAVEATS`; NYISO survives). At ≥25 %, **one of three** (NEISO).
At ≥20 %, **none** — and at ≥20 % the criterion certifies MISO's 20.8 % as
acceptable, which is the definition of a gate that does not gate.

**The three findings that come out of this table:**

1. **There is no band that both bites and discriminates on anything meaningful.**
   The whole dynamic range is floors 20–45 %. Below 25 % the criterion is
   vacuous; at 45 % and above it is universal. The 25–40 % window discriminates
   only in the sense that it sorts ISOs by a number for which **no external
   anchor exists** (§4a).
2. **The ISOs it would separate are not separated by model quality.** At floor
   ≥35 % it passes ERCOT (41.0 %) — an ISO at `NOT-YET` with C3a **and** C3b
   failing — while caveating PJM (29.5 %), whose keeper passes 8/8 criteria. A
   criterion that grades a two-FAIL model above a clean one is measuring
   something other than calibration quality.
3. **A `FAIL` forces `NOT-YET` at every tier**, so the tier choice cannot soften
   the tight bands; and the tiers that could soften the middle bands cannot be
   reached (§4a).

### 3a. Option (B) measured: REPORTED-ONLY changes nothing, at every band

A `REPORTED_ONLY` criterion is scored and published but is not aggregated into
the determination and consumes no caveat budget — the posture C5a `co2` already
holds. By construction, and verified in the probe: **every determination is the
base determination, at all ten bands and all three tiers.** ERCOT `NOT-YET`, PJM
`CALIBRATED`, CAISO `NOT-YET`, NYISO `CALIBRATED`, NEISO `CALIBRATED`, MISO
`NOT-YET` — unchanged.

---

## 4. THE THREE QUESTIONS THE CARD TURNS ON

### (a) TIER — and the finding that load-bearing and supporting are the SAME

**Load-bearing and supporting tier produce byte-identical determination tables**
(both benchmarks, all ten bands). That is not an accident and it is the central
constraint on option (A):

* A **`FAIL`** forces `NOT-YET` on **any** tier — the v1 rule `CRITERIA` still
  carries verbatim ("Any FAIL on ANY tier still forces NOT-YET").
* A **commercial-band `CAVEAT`** downgrades to `CALIBRATED-WITH-CAVEATS`
  identically at load-bearing and supporting tier.
* **Protective tier is strictly harsher**, not softer: `MAX_PROTECTIVE_CAVEATS`
  is **0**, so a protective caveat is immediately `NOT-YET`. At floor ≥35 % that
  costs NEISO and PJM a further step down, from CWC to `NOT-YET`.

So the *only* thing the supporting tier buys is **eligibility to be ledgered**
like C3c — the v3.0 guard admits `model-class` ledgering for supporting-tier
criteria alone. **That route is closed twice over:**

1. **`LEDGERABLE_CRITERIA` is `{price_tail}`** (rubric v3.1) — C3c is the only
   ledgerable criterion at all. Admitting a second is itself an owner amendment,
   and v3.1's stated purpose was to *narrow* this set.
2. **The single ledger slot is already occupied at five of six ISOs.**
   `MAX_LEDGERED_CAVEATS` is **1**, deliberately hardened ("the v1/v2 budget of 1
   let one…"). ERCOT, CAISO, NYISO, NEISO and MISO each already carry a ledgered
   C3c caveat consuming that slot. **PJM is the only ISO with a free slot** — and
   PJM is the ISO with the *worst* amplitude of the three CALIBRATED ones. A
   ledgerable amplitude criterion would therefore push five of six ISOs to
   `NOT-YET` on **budget exceeded**, without any of them getting the ledger.

**Answer to (a):** if adopted as a gate it would have to be **supporting** tier
(load-bearing is identical in effect and strictly stronger in claim; protective
is harsher and reserved for the anti-gaming gates C6/C8, which enforce CLAUDE.md
rules rather than claim accuracy). But supporting tier delivers no relief unless
the owner *also* raises `MAX_LEDGERED_CAVEATS` to 2 and widens
`LEDGERABLE_CRITERIA` — two further amendments, both loosening the
anti-self-deception tier, to accommodate one criterion. **That price is the
argument against (A), not a detail of it.**

**The anchor problem, which is prior to all of this.** Every graded criterion in
this rubric is two-band scored against a *published comparable*: C3a's ±10 % is
the SEM/Ireland regulator criterion for its official PLEXOS model (ECA,
SEM-20-004); C3b's 0.20 NRMSE is the outer edge of SEM's regulator-accepted
backcast. **There is no published counterpart for diurnal price amplitude.** The
rubric says so about this exact class of object, in §8's comparables row, and it
is the evidence C7 was retired on at **v3.1 (2026-08-06)**:

> *"beyond commercial practice" means **no external anchor exists** … C6 and C8
> keep their places anyway — they enforce CLAUDE.md rules 13/20 rather than claim
> accuracy against a comparable — but **a diurnal-shape ACCURACY gate with no
> published counterpart was doing neither**.*

A diurnal price-amplitude gate is that object exactly. Adopting it would reverse,
for prices, a decision the owner made for dispatch **five days after xiso-1 filed
this question** — and the band table shows there is no anchored number to adopt
it *at*.

### (b) RULE 19 `[R-ONE-MECH]` — one phenomenon, or several?

**This has changed materially since the charter was written, and the change runs
against the single-criterion premise.** The charter states that only NYISO has
decomposed its cell and "THE OTHER FIVE LANES HAVE NOT ANSWERED THIS PER-ISO
DECOMPOSITION QUESTION." That was true on 2026-08-01. **Four ISOs have since
decomposed their own cell, and they do not agree** (rule 25 `[R-ISO-SCOPE]`:
each number below is that ISO's own, and none transfers):

| ISO | cell | its own decomposition | what the statistic is measuring there |
|---|---|---|---|
| **NYISO** | `G` | nyiso-110: the measured spin-reserve differential covers **97–131 %** of the missing RT swing, passthrough slope ≈ 1; once reserve content is stripped the model **over-prices BOTH ends** and its energy-only swing is **117 / 97 / 107 %** of the reserve-stripped actual | **a missing PRODUCT** (reserve-price formation). On the energy basis NYISO has essentially **no amplitude defect at all** |
| **NEISO** | `O` | neiso-76 §(b), in terms: **"NEISO's amplitude does NOT decompose like NYISO's"** — reserve owns only **33 / 43 / 32 %** of the missing RT swing, RT reserve price is **$0.00 at the median hour**, and ISO-NE cleared **no day-ahead reserve product at all** before 2025-03-01. Energy-basis restatement puts the model's **peak right to ±$3** with the **overnight trough $7.6–9.9 too dear** | **an energy-side TROUGH defect** |
| **MISO** | `G` | miso-114 + miso-130: the compression is **two-sided** — night **+$7.0–8.7 flat overshoot** in all three years, July wave 20.2 vs 109.3 $/MWh (2025) — with the freeze statistic being PRB econ capacity priced below the model's own July night floor | **a night-floor / coal-offer regime** |
| **CAISO** | `U` | caiso-202 §B (year-invariant compression by actual-price bucket) + caiso-215 (per-zone): **south-concentrated**, hod 10–15 carries 64/45/35 % of the south's gap-$, and **NP15's $40–60 bucket is already UNDER-priced** | **a locational/bucket effect, of OPPOSITE sign between zones** |
| **PJM** | `G` | owner-closed frontier, empty lever queue; the flat-stack representation boundary | closed — no admissible in-model route |
| **ERCOT** | `U` | no ISO-local finding | unmeasured |

**Answer to (b): it is one STATISTIC, not one OBJECT.** xiso-1 was right that a
single construction reproduces the number everywhere and that the pre-existing
PJM/MISO/NYISO/NEISO diagnoses must not be re-derived — that reconciliation
stands. But "the same number falls out" is not "the same phenomenon". Two of the
four decompositions are flatly incompatible: NYISO's face is dominated by a
missing product whose energy side is already *correct*, while NEISO's face is
majority energy-side and lives in the trough, with its lane saying so explicitly
and in NYISO's own terms. CAISO's carries **opposite signs in different zones**.
A single cross-ISO criterion would be one gate over at least four different
objects — the criterion-side analogue of exactly what rule 19 forbids on the
mechanism side, and it would mark NYISO down for a defect its own energy basis
does not have.

**What is still not known, stated rather than papered over:** ERCOT has no
ISO-local decomposition at all (cell `U`, xiso-1's audit row is its only
evidence), and CAISO's cell is `U` — its evidence is a C3a-overrun decomposition
that was not framed as an amplitude decomposition. So the count is **four
decomposed, two not**, and the four that exist already disagree. Nothing here
licenses transferring any of them (rule 25).

### (c) THE CANCELLATION TRAP — what an amplitude repair does to C3a

**Measured for the first time here.** Accounting decomposition, not a mechanism:
the hour-of-day profile is split into the 12 hours the *measured* profile ranks
highest and the 12 it ranks lowest; "peak-only" repairs the peak half to measured
and leaves the trough, "trough-only" is the mirror. Any successor that closes
amplitude lands **between** these two level errors (or outside, if it overshoots).
C3a passes iff |level err| ≤ 10 % — target and commercial bands are **coincident**
for C3a, so it is PASS or FAIL with no caveat available.

| ISO | yr | level err | peak half | trough half | peak-only → C3a | trough-only → C3a |
|---|---|---:|---:|---:|---|---|
| ERCOT | 2023 | −30.1 % | −41.7 % | +13.0 % | +2.8 % PASS | −32.8 % FAIL |
| ERCOT | 2024 | +8.3 % | +0.4 % | +23.6 % | +8.1 % PASS | +0.2 % PASS |
| ERCOT | 2025 | +0.3 % | −8.7 % | +15.7 % | +5.8 % PASS | −5.5 % PASS |
| PJM | 2023 | +8.7 % | −2.5 % | +24.7 % | **+10.2 % FAIL** | −1.4 % PASS |
| PJM | 2024 | +1.9 % | −10.1 % | +20.4 % | +8.1 % PASS | −6.1 % PASS |
| PJM | 2025 | −4.9 % | −15.3 % | +10.2 % | +4.1 % PASS | −9.1 % PASS |
| CAISO | 2023 | +4.7 % | −1.8 % | +15.1 % | +5.8 % PASS | −1.1 % PASS |
| CAISO | 2024 | +12.9 % | +3.8 % | +30.4 % | **+10.5 % FAIL** | +2.5 % PASS |
| CAISO | 2025 | +13.7 % | +6.9 % | +25.9 % | +9.3 % PASS | +4.4 % PASS |
| NYISO | 2023 | +8.4 % | +2.6 % | +16.0 % | +6.9 % PASS | +1.5 % PASS |
| NYISO | 2024 | −0.7 % | −6.9 % | +7.5 % | +3.2 % PASS | −3.9 % PASS |
| NYISO | 2025 | −4.3 % | −11.6 % | +5.6 % | +2.4 % PASS | −6.7 % PASS |
| NEISO | 2023 | +7.6 % | −1.0 % | +18.7 % | +8.1 % PASS | −0.6 % PASS |
| NEISO | 2024 | +10.5 % | +0.7 % | +23.3 % | **+10.1 % FAIL** | +0.4 % PASS |
| NEISO | 2025 | +5.2 % | −2.8 % | +15.5 % | +6.7 % PASS | −1.6 % PASS |
| MISO | 2023 | +2.9 % | −5.2 % | +13.9 % | +5.9 % PASS | −3.0 % PASS |
| MISO | 2024 | −2.2 % | −11.8 % | +11.5 % | +4.7 % PASS | −6.9 % PASS |
| MISO | 2025 | −8.4 % | −18.1 % | +5.5 % | +2.3 % PASS | **−10.7 % FAIL** |

**Answer to (c), and it is the sharpest coupling on the card.** The trough half
is over-priced in **18 of 18** ISO-years (+5.5 % … +30.4 %) against a peak half
running −41.7 % … +6.9 %. The cancellation xiso-1 inferred from annual means is
confirmed hour-by-hour and is universal.

The consequence for adoption: **a peak-only repair — the natural direction for
every scarcity, reserve-formation and offer-surface successor on the queues —
moves the C3a level error UP by 3 to 13 pp and flips C3a from PASS to FAIL at PJM
2023, CAISO 2024 and NEISO 2024.** Two of those three (PJM, NEISO) are
currently-`CALIBRATED` ISOs, and C3a is **load-bearing and not ledgerable**. So a
successor that satisfies a new amplitude criterion by lifting the peak would buy
the amplitude PASS by breaking a load-bearing criterion at two of the three
models that are currently clean. The only repair that leaves C3a whole is a
**two-sided** one that lowers the trough as it lifts the peak — which is
precisely the direction NEISO's own decomposition points (trough $7.6–9.9 too
dear) and NYISO's does not (reserve-stripped energy already over-prices both
ends, so at NYISO the two-sided repair is a *level cut*, not a stretch).

The trap in one sentence: **the level is currently right for the wrong reason,
and adding a criterion that rewards closing the amplitude creates a standing
incentive to trade a load-bearing C3a PASS for a supporting-tier amplitude PASS.**

---

## 5. THE OPTIONS

### (A) ADD IT AS A GATING CRITERION, at a stated tier and band

**Effect on all six determinations: §3's table, at whatever band is chosen.** The
honest summary is that there is no band worth choosing:

* floor ≥ 45 % → 5 of 6 ISOs FAIL, **3 of 3** `CALIBRATED` lost;
* floor 30–40 % → **2–3 of 3** lost, and the criterion ranks a two-FAIL ERCOT
  above a clean PJM;
* floor ≤ 25 % → **0–1 of 3** lost, and the gate certifies 20.8 % amplitude.

**Costs, beyond the verdicts:** it needs an unanchored self-set band (§4a),
against the reasoning the owner used to retire C7 at v3.1; at supporting tier it
delivers no relief unless `MAX_LEDGERED_CAVEATS` goes 1 → 2 **and**
`LEDGERABLE_CRITERIA` widens, both loosenings of the anti-self-deception tier;
and it would gate at least four different objects with one number (§4b),
marking NYISO down for a defect its energy basis does not have.

**The NEISO unblock is NOT a consequence of this option** — see §6. Delete that
line from the case for (A).

### (B) ADD IT AS REPORTED-ONLY — measured, published, no status, no budget

**Effect on all six determinations: NONE, at every band and every tier**
(measured, §3a). It would join C5a `co2` in `REPORTED_ONLY`: `score_*` runs, the
number reaches the payload, the JSON detail and every dashboard run page, and it
contributes no status and consumes no caveat budget.

**Recommended in a band-free form.** Because no external anchor exists, a
reported-only amplitude criterion should carry **no threshold at all** — publish
the ratio, the daily MAX/MIN errors and the phase check as a measurement, not a
graded band. That removes the §4a objection entirely: there is no self-set number
to defend, and nothing to silently re-arm as a gate.

**Cost, stated:** it is not free — it needs a `score_diurnal_amplitude` in the
scorer and a `REPORTED_ONLY` entry, an owner act this session is fenced from.
And it is a *disclosure*, not a gate: nothing is obliged to close the defect.

**Does it unblock NEISO? No.** See §6.

### (C) DO NOT ADD IT

**Cost, in full, as the charter requires.** A defect present in **36/36** cells —
daily peaks under-priced by up to 61 %, troughs over-priced by up to 146 %,
amplitude at a mean 45 % of measured — stays **permanently invisible to the
model's own quality gate**. C3a is a level test that this defect passes *by
cancellation* (§4c, 18/18 rows); C3b is a 12-month load-weighted NRMSE
structurally blind to hour-of-day for every ISO; C3c is a tail count; **and C7,
the one criterion that ever scored a diurnal shape, was retired outright at
v3.1** — so the rubric today sees *less* hour-of-day structure than it did when
xiso-1 filed. A model can be certified `CALIBRATED` on 8/8 criteria while
reproducing 29.5 % of the measured daily price swing, which is PJM's keeper
today. Anyone reading a `CALIBRATED` determination as a statement about intraday
price formation is being misled, and nothing in the rubric corrects them.

NEISO's storage lane stays blocked — but it stays blocked under **(A)** and
**(B)** too, for reasons that have nothing to do with the rubric (§6).

---

## 6. THE NEISO PS UNBLOCK — the claim is WITHDRAWN, on evidence

The charter names NEISO's unblock as a consequence of (A) and asks honestly
whether (B) delivers it. **Neither does, and neither could.** Reading the block
itself (`docs/mechanism-testing-matrix.md` §5.6 item 8, neiso-74):

> **DO-NOT-REDO** any storage-side PS lever at NEISO until the diurnal amplitude
> defect **closes**.

The block exists because neiso-74's screen found **the storage block is already
optimal for the price signal it is shown** — a perfect-foresight LP on NEISO's
own storage physics discharges 4.301 TWh on measured DA prices against the
keeper's endogenous 0.400/0.363/0.497 TWh, and the same LP *on the model's own
duals* returns 0.370/0.339/0.612, bracketing the keeper. Every storage-side knob
is wrong-signed or cross-ISO shared. The constraining object is upstream, in
price formation.

**A rubric criterion changes no dispatch and closes no defect.** The block lifts
when a price-formation mechanism lands, not when a criterion is written. NEISO's
own named successor is not a rubric change either: item 1's DA-bid
offer-formation charter was **refuted on both limbs at neiso-76**, which named a
new **stack-traversal** route and said in terms that it "needs ITS OWN CHARTER,
not opened."

**So the real NEISO ask is a different owner act than this card's question:**
charter the neiso-76 traversal route. That is worth putting to the owner
alongside this card, and it is not blocked by whichever option is chosen here.

---

## 7. RECOMMENDATION — **(B), REPORTED-ONLY and BAND-FREE**

**Reasoning, in the order that decides it:**

1. **(A) is not available at any band.** Not because the verdicts are
   uncomfortable, but because the criterion is vacuous below 25 % and universal
   above 45 %, and every number in between is self-set. The rubric grades every
   other criterion against a published comparable; there is none for this.
2. **The owner has already ruled on this class of object, for dispatch.** v3.1
   retired C7 outright on exactly this ground — *"a diurnal-shape ACCURACY gate
   with no published counterpart"* — while **explicitly keeping the D-1
   measurement**. Option (B) is that same disposition applied to prices:
   **keep the measurement, do not gate on it.** Choosing (A) would reverse a
   five-day-old amendment; choosing (B) extends it consistently.
3. **(A) would gate four different objects with one number.** NYISO's face is a
   missing reserve product whose energy side is already correct; NEISO's is an
   energy-side trough; MISO's is a night floor; CAISO's changes sign between
   zones. Marking NYISO down on a statistic its own decomposition explains away
   is a false negative, and the rubric would have no way to tell.
4. **(A) creates a perverse incentive that (B) does not.** §4c shows the natural
   peak-only repair flips **load-bearing, non-ledgerable** C3a to FAIL at PJM
   2023, CAISO 2024 and NEISO 2024. A gate that rewards closing amplitude while
   C3a passes by cancellation prices a real criterion against a synthetic one.
5. **(C) is refused on its stated cost, which is real.** A 36/36 defect invisible
   to the quality gate is exactly the self-deception the protective tier exists
   to prevent, and the C7 retirement made the rubric *blinder* to hour-of-day
   than it was when the question was filed. (B) closes that gap at zero cost to
   any determination — the disclosure without the unanchored gate.

**What (B) should look like concretely** (for the owner's drafting, not built
here): report per ISO-year, on the RT basis with DA alongside — the amplitude
ratio, daily MAX and MIN errors, the peak/trough phase check and the hod
correlation; no band, no status, `REPORTED_ONLY` membership so it can never
contribute to a determination or be silently re-armed as a gate. The statistic is
already computed and costs zero LP (`_xiso1_diurnal_amplitude_audit.py`).

**What the owner should decide separately, and what this card does not decide:**
whether to charter NEISO's neiso-76 stack-traversal route (§6). That is the act
that would actually move NEISO's PS lane, and it is independent of this question.

---

## 8. GOVERNANCE

No LP solved, no config changed, no bundle produced, **no dashboard
registration** (rule 15 `[R-DASHBOARD]` binds bundles; this card produces none).
**Scorer untouched** — `calibration_verdict.py`, `rubric-consts.js`, `CRITERIA`,
`LEDGERABLE_CRITERIA`, `MAX_LEDGERED_CAVEATS` all unchanged; xiso-1's "the scorer
was NOT changed" posture holds until the owner signs. No keeper moved, no
determination re-written, no `keepers/<ISO>.json`, `calibration-complete.json` or
`holdout-freeze.json` touched. Rule 22 `[R-HOLDOUT]`: 2023–2025 only, committed
artifacts only, nothing spent — the freeze is ACTIVE and irrelevant because this
lane spends nothing. Rule 25 `[R-ISO-SCOPE]`: every per-ISO decomposition in §4b
stays its own ISO's; none is transferred. Rule 26 `[R-MECH-MATRIX]`: **no
mechanism was tested, so no cell verdict moves** — evidence is appended to the
`diurnal_price_amplitude` row only.

**DO-NOT-REDO:** do not re-measure cross-ISO diurnal amplitude, and do not
re-derive the band × ISO × determination table. Re-run
`scripts/probes/_xiso6_amplitude_criterion_band_probe.py`; it reads the live
keeper store and the unmodified scorer, so it re-reports against whatever the
keepers and the rubric are, at zero LP cost.
