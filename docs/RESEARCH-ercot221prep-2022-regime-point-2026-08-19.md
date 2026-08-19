# RESEARCH — ercot-221 prep: the 2022 regime point, the trailing-expectation year-grain test, and what "use 2022" can and cannot mean

> Status: RECORD — read-only measurement session, 2026-08-19, branch
> `claude/ercot-lmp-miss-analysis-cde845`. **NO shorthand consumed** (the next
> free shorthand, ercot-221, is deliberately left for the Phase-0 the
> ercot-220b addendum recommends — this doc is supporting evidence FOR that
> charter, not the charter). No LP, no solve, no year scored, no run
> registered, no matrix cell touched, no mechanism built or armed.
> Probe: `scripts/probes/ercot221prep_2022_regime_phase0.py` →
> `results/calibration/ercot221prep_2022_regime.json` (committed).

**Keeper at measurement:** `2026-08-17-ercot215-arm-decontam` (unchanged).
**Rule-22 posture:** data-not-score. Out-of-training years enter as *measured
data* (inputs / identification anchors) only; no out-of-training year is
solved, scored or registered, and **2019 is left entirely untouched** — no
statistic in this session reads it — so the locked test keeps its full power
to surprise.

## 0. Context and the question

An owner Q&A session walked the full 2023 scarcity adjudication (slack vs
offer stack; the ECRS sequestration already armed and measured-faithful; the
ORDC adder legs of model and market agreeing at ~$1; every quantity-side and
re-slicing lever spent) and converged, independently, on the same object the
lane's record names: an **adaptive backward-looking expectation** behind the
2023 storage conduct offers. The owner then asked whether 2018–2022 can feed
that identification — "just do 2022?" This doc records the admissible answer
and the three measurements it enabled, all from committed/on-disk measured
data.

**The admissible sense of "do 2022":** intake and read its *measured market
data* as identification input (unrestricted — the score is held out, never
the data). **The closed sense:** solving/scoring/registering 2022 — the
`complete` block in `calibration-complete.json` is empty for every ISO, so no
validation-ladder year may be spent by anyone today.

## 1. M-1 — 2022 vs 2023: the regime axis measured as a two-point contrast

From ERCOT's own NP6-323 5-minute telemetry (hourly means at the actual
RT > $200 tail hours of each year):

| | 2022 tail (196 h) | 2023 tail (181 h) |
|---|---|---|
| PRC at tail, p50 | **3,768 MW** | 5,794 MW |
| λ at tail, p50 | $176 | $406 |
| λ-carried hours (λ > $200) | 83/196 | 122/181 |
| RTORPA at tail, p50 / p90 | **$34 / $493** | $0.72 / $55 |
| adder share of price, p50 | **15.3 %** | 0.5 % |

2022's scarcity is **administratively priced at real tightness** — PRC down
near the ORDC knee, the ORDC genuinely firing, a sixth of the tail price
being adder at the median. 2023's is **conduct-priced at comfortable PRC**
with the ORDC essentially silent. This is FINDING-ercot195's "a regime
series, not a tightness series" verdict rendered as a direct two-point
measurement, and it carries a practical implication: **2022 is a test of
physics the current model already has** (competitive λ + LOLP ORDC at true
tightness + the co-opt). When a `complete` marker ever authorizes the 2022
touchpoint, it will discriminate the model's *existing* scarcity mechanism —
unlike 2023, which tests the missing conduct layer. (A correction to the
in-chat version of this table: the 2022 adder share was first quoted as
1.1 % from a wrong denominator (PRC included); the probe's correct
λ+adder basis gives 15.3 %.)

## 2. M-2 — the trailing-expectation year-grain test

Question: does a backward-looking statistic of realized evening (HE17-22) RT
prices predict the measured storage offer level and its decay
(**$2,714 → $1,281 → $990** p50 at p98 tightness, ercot-210)? All six
candidates scanned are reported (windows end 1 June of the delivery year):

| statistic | →2023 | →2024 | →2025 | measured |
|---|---|---|---|---|
| 12mo p99 | 686 | 2,024 | 243 | |
| 24mo p99 | 423 | 1,180 | 1,123 | |
| 24mo p99.5 | 735 | 2,270 | 2,126 | |
| 36mo p99 | 805 | 919 | 961 | |
| 24mo mean top-50h | 905 | 2,414 | 2,319 | |
| **36mo mean top-100h** | **3,016** | **1,626** | 1,660 | 2,714 / 1,281 / 990 |

Reading, stated with its caveat:

- **Uri-inclusion is load-bearing for the 2023 level.** Every window that
  excludes Feb-2021 misses 2023 by 4–6×; the one Uri-inclusive statistic
  lands 2023 within ~11 % and gets the 2023→2024 direction right. This is
  the post-Uri risk-premium story of RESEARCH-ercot218b, measured at year
  grain.
- **Price memory alone flattens by 2025** (1,660 predicted vs 990 measured)
  while the measured level keeps falling — the residual decay matches the
  **competitive-state driver** (storage offered volume 8.4×, ercot-210), not
  memory. A memory × competitive-state two-driver form is the natural
  Phase-0 candidate.
- **Selection caveat, stated plainly:** six statistics were scanned post hoc
  in one session. This scan spends selection freedom; the ercot-221 Phase-0
  must PRE-REGISTER its statistic, grain and gates before evaluating
  anything further (the ercot-210 precommit pattern, T1–T5 + LOYO + the
  2024→2025 within-regime control the 220b addendum names as decisive).

## 3. M-3 — the trigger half is already well-posed on the keeper

Ranking 2023 hours by the keeper's own P1 `ercot_ordc_total` held-MW margin
(committed sidecar) and sweeping a binding-count threshold N against the 181
actual tail hours:

| N tightest model hours | hits /181 | false positives | actual RT p50 in false hours |
|---|---|---|---|
| 100 | 91 | 9 | $152 |
| **181** | **136** | 45 | $126 |
| 500 | 171 | 329 | $78 |

The actual tail sits at the model's **1st–2nd percentile** of margin
(p25/p50/p75 = 0.01/0.01/0.02). Two implications: (a) the *selection*
instrument for a conduct mechanism already exists inside the model (the
margin embeds the armed ECRS sequestration — consistent with ercot-219's
not-refuted stage-2 exhaustion signature); (b) the open object is purely the
**price function** on the selected hours — which is M-2's territory, and
exactly where ercot-220b's month-grain evidence points.

Note the instrument distinction from FINDING-ercot210's "tightest hours are
not the scarcity hours": that finding ranked hours by *measured actual PRC*;
this one ranks by the *model's own* P1 margin, which embeds the AS carve-out
and the model's weather/outage state — and selects far better. The two are
not in tension; they measure different instruments.

## 4. Data availability: what "do 2022" runs into

- **2022 offer surface (60-day SCED disclosure): NOT HELD.** The corpus
  spans publications 2023-03..2026-03 (deliveries ≳ Jan-2023); 2022
  deliveries published 2022-03..2023-02, before the corpus starts. MIS
  recoverability is an **open check** — `fetch_ercot_sced_corpus_shards.py`
  exists, but the fresh-MIS route decays (corpus README). This is the
  single most valuable missing measurement: a measured 2022 storage offer
  level is the **discriminator** between the memory and competitive-state
  drivers (trailing-2022 memory has Uri at 12–18 months AND a tiny fleet →
  both stories predict high 2022 offers, but with different magnitudes and
  different 2022-internal decay).
- **2022 NP6-323 telemetry: held** (`data/raw/ercot/…_2022.parquet`) — M-1
  used it.
- **Hourly actual RT/DA: held 2018–2026** (`_validation-source`).

## 5. What this does and does not license

1. **Supports** the ercot-220b recommendation to charter ercot-221 Phase-0
   (adaptive-rule identification), adding: the year-grain two-driver signal
   (§2), the trigger-half result (§3), the 2022 regime contrast (§1), and
   the 2022-offer-corpus recoverability check as a named data task.
2. **Licenses nothing to be armed.** No mechanism, field or wiring changed;
   the adjacent matrix verdicts (`ercot_artificial_shortage_pricing` R, the
   conduct-transfer NOT-TRANSFERABLE, Door D as the recorded floor) all
   stand. Any solve-bearing follow-up runs through an owner-signed charter
   with a pushed precommit.
3. **Rule-22 discipline for the follow-up:** identification may read
   2020–2022 measured data (documented in the DOF ledger, so any later
   touchpoint result on those years is not quoted as independent
   confirmation); **2019 stays out of every fitting set**; no
   out-of-training year is solved or scored without its tier marker, which
   today no ISO holds.
