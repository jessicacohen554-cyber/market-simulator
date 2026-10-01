# RESEARCH — why ERCOT's 2023 prices were actually so high (owner-directed, ercot-218 session addendum)

**Owner directive (verbatim, mid-session 2026-08-18):** *"research why ERCOT
2023 prices were so high actually."* This memo answers from primary sources —
the IMM's 2023 State of the Market report (re-fetched this session and
sha256-verified byte-exact against `data/raw/ERCOT/SHA256SUMS.txt`:
`4abda7d7…`), ERCOT's own published real-time telemetry as committed in this
repo (NP6-905 reserves/λ/RTORPA/PRC; hub RT/DA hourly), the committed 60-day
disclosure censuses, and independent market analyses. Read-only: no LP, no
solve, no criterion scored; every number below is measured or quoted, with its
basis stated.

## 0. THE ANSWER, IN ONE PARAGRAPH

Record heat created an unusually large number of tight late-afternoon hours —
but the grid was **not** short: ERCOT carried 4–5.5 GW of physical responsive
reserve through almost every high-priced hour, and the official scarcity
mechanism (the ORDC) contributed only **~$1/MWh across all of 2023 (~2 % of
the average price — less than in 2022)**. What made prices extreme was the
**June 10, 2023 introduction of ECRS**: ERCOT began procuring ~2.1 GW of a
new 10-minute reserve **on top of** undiminished RRS — roughly doubling
10-minute reserves to ~5 GW (August: ECRS 2,127 + RRS 2,566 + RegUp 389 MW ≈
5.1 GW) — **sequestered that capacity out of the real-time dispatch, and
almost never released it**. Capacity that in prior summers would have
self-committed into the energy market at tight hours instead sat in reserve,
so SCED repeatedly "ran out of available resources" while the system held
ample physical reserves — the IMM's *"artificial shortage pricing as high as
$5,000 per MWh when the system was not actually short of reserves."* At those
artificially-thinned margins the price was set by the **energy offers of the
then-small battery fleet** (4.7 GW installed, mostly 1–2 h duration), which
priced its scarce state-of-charge at expected evening-scarcity value —
$3,400–5,000/MWh medians in the summer months. The IMM re-ran the real-time
dispatch with 75 % of the sequestered capacity released and found the ECRS
effect **doubled average real-time prices from June through December 2023 and
added more than $12 billion of real-time market costs through November**.
Both halves of that mechanism are now gone: ERCOT implemented an ECRS
deployment trigger in August 2024, the battery fleet has roughly tripled
(compressing those scarcity offers ~2.7×), and RTC+B (Dec 2025) removed the
sequestration design entirely. 2023 was one summer's interaction of a design
defect with a young, concentrated storage margin — priced through energy
offers, not through the scarcity adder.

## 1. THE PRICE ANATOMY, MEASURED (committed telemetry; hub RT hourly vs NP6-905)

2023 had **181 hub hours above $200/MWh** (100 of them in August; 86 % between
13:00 and 19:00). Decomposing every one of them against ERCOT's own published
real-time series:

| population | n | SCED λ p10/p50/p90 | RTORPA p50 (max) | PRC p10/p50 | λ ≥ 0.8×RT | RTORPA > $100 | PRC < 3,000 MW |
|---|---:|---|---|---|---:|---:|---:|
| RT > $200 | 181 | 242 / 620 / 2,608 | $4.51 ($650.80) | 4,728 / 5,619 MW | **162** | 17 | 1 |
| RT > $1,000 | 61 | 1,121 / 2,065 / 4,139 | $22.38 | 4,155 / 5,342 MW | 57 | 10 | 1 |
| RT > $4,000 | 7 | 4,066 / 4,714 / 4,902 | $30.92 | 3,045 / 3,873 MW | **7** | 1 | 1 |

Three facts follow directly:

1. **The 2023 tail was made by the SCED energy price λ, not by scarcity
   adders.** 162 of 181 tail hours (and all 7 hours above $4,000) had λ
   carrying ≥ 80 % of the settled price. RTORPA — the ORDC's real-time
   scarcity adder — never exceeded $651 all year and sat at a median of
   **$4.51** across the tail.
2. **The grid was never in deep reserve scarcity by its own telemetry.** PRC
   stayed above the ORDC's 3,000 MW knee in 180 of the 181 tail hours and
   never touched the 2,300 MW EEA-1 trigger; even the $4,000+ hours carried a
   median 3,873 MW of physical responsive capability.
3. **The market priced this in advance, not just in real time.** 133 of the
   181 tail hours also cleared above $200 **day-ahead**, and August's DA
   monthly mean ($261) exceeded its RT mean ($192): the scarcity premium was
   the market's *expectation*, embedded in forward offers — exactly where a
   thin storage margin prices its state of charge.

The only hours with any material reserve-price component (17 hours,
RTORPA $108–651) fall on **Aug 17–30 and Sep 6–8** plus a few spring
evenings — the handful of genuinely tight events inside a sea of
artificially-thinned ones.

## 2. THE DRIVERS, QUANTIFIED

### 2.1 Record heat and load — necessary, not sufficient

ERCOT broke its all-time peak demand record **49 times** in summer 2023
(85.7 GW on Aug 10); the summer averaged 85.3 °F, cooling degree days up to
+8.5 %, West-zone load +15.5 % y/y (2023 SOM). But supply kept pace — 10.5 GW
of new capacity entered in 2023, including 5.8 GW of solar the IMM calls
"particularly valuable for helping satisfy the peak summer demands" — and the
IMM found **"no material risks of load shedding during the summer months"**.
Heat produced many tight-ish evening net-peak hours; it did not produce an
adequacy emergency. (2011 and 2019 were hotter relative to their fleets and
produced nothing like $12 B of scarcity rent.)

### 2.2 The ECRS artificial-shortage mechanism — the IMM's principal finding

The 2023 SOM's own words (Executive Summary, §II):

> "The implementation of ECRS almost doubled the amount of 10-minute reserves
> procured by ERCOT … ECRS resources, like responsive reserves, are withheld
> from the real-time energy market dispatch until manually deployed, which
> can cause the market to falsely perceive a shortage; and ERCOT generally
> did not deploy the ECRS resources … **Prior to ECRS, many of these
> resources would have been self-committed by their owners under these
> conditions.** … This resulted in artificial shortage pricing as high as
> $5,000 per MWh when the system was not actually short of reserves."

> "ERCOT generally avoided deploying the resources even when the real-time
> dispatch model **ran out of available resources** and prices rose as high
> as $5,000 per MWh."

Quantities (measured ASPLANNP433, committed;
`results/calibration/ercot217_regime_phase0.json`): ECRS 2,041–2,127 MW
Jun–Sep 2023, RRS 2,566–2,676 MW, RegUp ~380–410 MW — **≈ 5.1 GW of
10-minute-class capability carved out of SCED's dispatchable range in
August**, with *"no offsetting reduction in responsive reserve
procurements"*. The IMM's counterfactual — re-running the actual real-time
dispatch with 75 % of the sequestered capacity available — is the headline:
**ECRS doubled average real-time prices June–December 2023 and added
> $12 billion of real-time market costs through November.** Its reliability
value was ~nil: LOLP addressed 0–0.2 %, marginal value ≈ 0 at the procured
quantity, total reliability value **$12 M against > $600 M of procurement
cost** ("50 times higher").

And the converse: the ORDC — the *designed* scarcity-pricing mechanism —
contributed *"just over $1 per MWh or roughly 2 % of the annual average
real-time energy price, significantly less than in 2022 ($6.41)"*; *"most of
the price spikes that occurred in June, August, and September 2023 did not
reflect true shortages."* 2023's prices were not the scarcity design working;
they were the sequestration working through the energy offer stack.

### 2.3 Who set λ at the thinned margin: the young storage fleet's offers

With ~5 GW held out, the marginal resource at the spike hours was
overwhelmingly storage, and its offers were near the cap:

- **0.91 of the 1.10 GW offered at ≥ $500/MWh at the top-100 gap hours was
  storage** (ercot-161 census, committed 60-day SCED disclosures).
- At matched tightness (each year's tightest 2 %), storage's MW-weighted
  median above-LSL offer was **$2,714/MWh in 2023** — monthly
  **$3,361–5,000 Jun–Sep** — versus **$1,281 in 2024 and $990 in 2025**,
  while storage offered volume at those hours grew 3.0 → 8.4 → 25.3 GW
  (ercot-210 §4 / ercot-218, committed).
- The fleet was small and short: 4.7 GW installed (1.9 GW added during
  2023), predominantly 1–2 h duration — scarce state-of-charge priced at the
  expected value of the evening net-peak, by a margin thin enough to carry
  scarcity rents. Independent revenue data corroborate the concentration:
  **51 % of Jan–Aug 2023 ERCOT battery revenue was earned in 10 days**, and
  August alone paid ~15× the average month, with ECRS itself ~29 % of
  battery revenue through August (Modo Energy).

This is why the DA market was high too (§1): the *expectation* of thin
evening margins was general, and offers — storage foremost — priced it. It
is also why the 2023 offer level does not transfer from 2024/25 data
(measured three ways: ercot-210/211 proxy drivers, ercot-218 true AS-state
drivers, both NOT-TRANSFERABLE; the within-regime 2024→2025 control fails
0/6): the level was the scarcity rent of a fleet configuration that existed
for one summer. By 2025 competition had compressed it 2.7×.

### 2.4 The genuine emergencies were few — and the worst was transmission-made

Prices reached the $5,000 system-wide offer cap for **more than four hours
total in 2023, mainly on August 17 and September 6** (SOM Appendix A8). The
September 6 EEA-2 — the year's only declared emergency — was
**transmission-driven**: a severe constraint violation prompted ERCOT to
manually curtail **1,500 MW of generation (1,300 MW of it wind) into a
rising evening ramp**, frequency fell below 59.91 Hz for 15 consecutive
minutes, and EEA-2 was declared (SOM §I; the IMM's re-simulation with a
$15,000 shadow-price cap finds the violation avoidable with no manual
curtailment). Small contributors, for completeness: the RUC/conservative-ops
reliability adder was non-zero mainly in Aug–Sep (~$0.84/MWh annual per the
SOM; the model's measured overlay carries $0.75 demand-weighted), and NSPIN
procurement was actually *reduced* May→Aug (5,052 → 2,206 MW) — easing, not
tightening.

## 3. WHY 2023 WAS SUI GENERIS — both halves of the mechanism are gone

1. **The design half was repaired.** The PUCT rejected NPRR1224's $750/MWh
   release floor at its 2024-07-25 open meeting, but ERCOT implemented the
   deployment process anyway from **2024-08-01**: ECRS now releases in
   500 MW increments on a sustained power-balance violation, at resources'
   own offers (IMM 2024 SOM recap, carried in the model as
   `ERCOT_ECRS_RELEASE_REFORM_HOUR`). Post-reform 2024 carries no
   ECRS-artificial-shortage tail (2024: 53 h > $200; 2025: 31 h). **RTC+B
   (2025-12-05) removed the sequestration architecture entirely** — AS and
   energy co-optimized in real time, per-product demand curves, storage
   selling AS directly into RT.
2. **The competitive half eroded.** The storage fleet roughly tripled
   2023→2025; at identical measured tightness its median scarcity-hour offer
   fell $2,714 → $990. The 2023 rent required both the thinned stack *and*
   the thin storage margin; neither exists now.

## 4. WHAT THE MODEL CARRIES, AND WHERE THE MISS ACTUALLY LIVES

| real driver (2023) | model status |
|---|---|
| Record heat / load | CARRIED — backcast uses the weather-year's measured load |
| ECRS + RRS sequestration (~5.1 GW out of dispatch) | CARRIED + ARMED — `ercot_ecrs_conservative_deployment` (rigid whole-2023 → 2024-07-31), `ercot_nonreleasable_as_withholding`, the measured hourly per-product AS plan |
| ORDC scarcity pricing (small in reality) | CARRIED — co-optimized reserve duals + the decontaminated published-anchor adder (ercot-215); faithful to the published magnitudes |
| RUC / conservative ops (~$0.84) | CARRIED — measured RTORDPA overlay ($0.75 dw) |
| ECRS release reform / RTC+B boundaries | CARRIED — date-gated to the published instruments |
| **SCED's residual stack actually exhausting** | **NOT REPRODUCED** — the model retains more cheap dispatchable headroom than real SCED had at those hours (the ~2.7 GW capability wedge; its per-unit identification twice failed its licence — item 11, L1 0.3857 vs 0.90, Q-B) |
| **The marginal offer level at the thinned margin** (storage pricing SOC at expected scarcity) | **NOT REPRESENTED** — model storage bids ~ε and is an inframarginal price-taker under perfect foresight; reality's storage was the marginal price-MAKER at $1,000–5,000. Same MW (±8 % fuel-by-fuel at the missed hours, ercot-216 §3), opposite merit-order position |

The two rows in bold are one phenomenon seen from two sides: reality's stack
ran out ~$300–400/MWh *below* where the model's does, and the resources that
then set the price offered at scarcity expectation rather than cost. The
model dispatches the same megawatts at those hours and clears at $70–97
where SCED cleared at $272–457 — the gap is entirely *which unit is
marginal, and at what offer*. A perfect-foresight LP cannot price a battery
at "expected evening scarcity" above its own equilibrium price level — an
endogenous opportunity-cost offer reproduces the model's own (too-low)
expectation by construction, a measured 2023 offer level fed back in is the
rule-13 forbidden form, and a fitted level was measured non-transferable
three ways (ercot-210/211/218). A structural representation of the
artificial-shortage channel itself — e.g., pricing the sequestration-induced
stack exhaustion — would require the model's stack to exhaust where SCED's
did, which is the twice-unlicensed capability wedge. That chain of closures
is why the residual is adjudicated model-class; this memo's contribution is
that the *cause* is now fully named and quantified, not mysterious: **a
one-summer design defect monetized by a young storage fleet, priced through
energy offers with the official scarcity mechanism nearly silent.**
(A supporting model-class fact, measured at ercot-216 §4: 17 % of 2023's
actual tail hours clear $200 on only a minority of their 15-minute
intervals — structurally invisible to an hourly LP.)

## 5. CAN THIS BE MODELED? (owner follow-up, same session: "Is there no way to model this??")

**In principle yes — the mechanism is now understood well enough to specify a
fully structural model of it. In practice every buildable version chains
through one keystone that today's data cannot license.** The assessment, with
a new measurement:

**The new measurement — August 2023's offer level was rational expectation.**
The realized daily probability of a ≥ $1,000 spike-hour, by month, against
the measured storage offer at the tightest hours (implied P = offer / $5,000
cap):

| | realized P(≥$1,000 day) | P × $5,000 | measured storage `p50` | implied P |
|---|---:|---:|---:|---:|
| Jun 2023 | 0.03 | $167 | $5,000 | 1.00 |
| Jul 2023 | 0.06 | $323 | $5,000 | 1.00 |
| **Aug 2023** | **0.52** | **$2,581** | **$3,361** | **0.67** |
| Sep 2023 | 0.13 | $667 | $4,052 | 0.81 |
| 2024 (yr) | 0.014 | $68 | $1,281 | 0.26 |
| 2025 (yr) | 0.008 | $41 | $990 | 0.20 |

In the month that carries the object (August, with September = 96.2 % of the
C3b-2023 residual), the offer level matches the realized event base rate to
~30 % — the "conduct" was a calibrated bet on the artificial-shortage event
frequency. June/July sit at the cap regardless (park-at-the-cap in an unknown
new regime), September looks backward-priced off August's experience, and
2024/25 offers exceed realized frequency severalfold as events vanish —
consistent with adaptive/lagged expectations, and with why no *static*
function of same-hour telemetry fits the surface (the T5 irreducibility).

**The structural architecture this implies** (three stages, each with a real
market analogue, zero fitted scalars in principle):

1. **Stack exhaustion** — the model's SCED-equivalent dispatchable stack must
   run out where the real one did (the sequestration is already carried; the
   model's residual headroom is ~2.7 GW too fat — the item-11 capability
   wedge).
2. **Expectation** — the probability of an exhaustion event in the evening
   peak, computed from the model's own state (load, net-load ramp, available
   capability net of the sequestered MW). In 2023 this is large *because of*
   ECRS; in 2024/25 it collapses; in a forecast year it regenerates.
3. **The offer** — storage prices its scarce SOC at that expectation × the
   cap (the textbook reservation price of stored energy), becoming the
   marginal price-setter at exactly the hours reality's batteries were.

None of this is the refuted material: it fits nothing to a residual (Door A
closed *fitted* conduct functions), feeds no measured surface (ercot-162's R),
and reads no price as an input. It is a NEW mechanism family and would need
its own owner card, matrix row, precommit and kill gates.

**The keystone, and why it is currently blocked: stage 1.** Without real
exhaustion events, stage 2's in-model probability is ~zero (the model's
August-2023 λ sits at ~$97 with headroom to spare), and anchoring the
expectation on *reality's* event frequency instead is a measured-outcome
input — the rule-13 forbidden form. The three known ways to close the wedge
are each adjudicated on today's data: the per-hour telemetered capability cap
(aggregate or per-unit) pins the backcast to realized commitment — rule-13
forbidden (ERCOT-159/163, cell `R`); the reproducible per-unit
SCED-train↔model-unit capability model failed its pre-registered licence
twice (L1 0.5111/0.3375 then 0.3857 vs a 0.90 bar — item 11, Q-B); the
commitment-state route was refuted (ercot-163). And capability is *already*
measured-informed (the DAM availability rescale), so a stacked physics
derate would double-count a phenomenon that overlay owns (rule 19).

**The three honest options for the owner:**

- **(A) Hold the current posture.** 2023's level stands as the priced
  residue of a one-summer design defect; the forecast never needs the
  mechanism (the ECRS trigger since Aug-2024 and RTC+B removed the channel);
  Door D's 2026 SOM anchors arrive ~mid-2027. Cost: C3a/C3b-2023 stay
  failed; C3c stays a ledgered caveat.
- **(B) Sign a scoped rule amendment.** Authorize, as an explicit owner
  decision, a backcast-2023-only capability reconciliation to the published
  aggregate telemetry (rule 14's "reconciled version of real data" clause,
  extended by your signature to cover what rule 13 currently scores as
  pinning), then build stages 2–3 structurally on top. The record would mark
  those hours measured-capability-anchored; the forecast lane is untouched.
- **(C) Fund the data route.** The wedge is at bottom a data-quality
  problem — a resource-name↔model-unit mapping that cannot be licensed from
  the committed disclosures alone. A better crosswalk intake (EIA↔ERCOT
  registry / settlement-ID based) could pass the existing 0.90 licence bar,
  and then the whole architecture is buildable with zero fitted scalars and
  no rule change. Unknown cost until scoped; it is the only route that
  closes the gap *within* the current rules.

Nothing is built or armed here; this section exists so the choice is the
owner's, on the record.

## 6. SOURCES

**Primary:** Potomac Economics, *2023 State of the Market Report for the
ERCOT Electricity Markets* (June 2024) — Executive Summary (ECRS mechanism,
doubling, > $12 B, ORDC ~$1/MWh, ECRS value $12 M vs $600 M, records,
Sept 6, Appendix A8 high-price duration); re-fetched from
<https://www.potomaceconomics.com/wp-content/uploads/2024/05/2023-State-of-the-Market-Report_Final_060624.pdf>
and sha256-verified against the committed manifest. Committed measured
series: hub RT/DA hourly (`data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet`),
NP6-905 reserves/λ/adders (`data/raw/ercot/ercot_2023_ordc_reserves_hourly.parquet`),
ASPLANNP433 monthly plan (`results/calibration/ercot217_regime_phase0.json`),
60-day disclosure censuses (ercot-161/210/218 artifacts). **Independent
corroboration:** Modo Energy research on ERCOT battery revenues and offers
(<https://modoenergy.com/research/ercot-battery-energy-storage-system-august-2023-revenues-ancillary-services-ecrs-arbitrage>,
<https://modoenergy.com/research/ercot-battery-energy-storage-systems-annual-revenues-2023-bess-index-ancillary-services-arbitrage-ecrs>);
Ascend Analytics on ECRS pricing dynamics
(<https://www.ascendanalytics.com/blog/understanding-the-ercot-contingency-reserve-service-ecrs-from-pricing-dynamics-to-storage-dispatch-behavior>).

*Session ercot-218 addendum, branch `claude/ercot-218-direct-driver-5ckiur`.
No LP, no solve, no criterion scored, nothing fitted, keeper untouched
(`2026-08-17-ercot215-arm-decontam`). The SOM PDF payload remains gitignored
per the corpus posture; the values above carry their citations here.*
