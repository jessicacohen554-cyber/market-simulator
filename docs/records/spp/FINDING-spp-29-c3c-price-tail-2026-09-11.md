# FINDING — SPP-29: R-bd is REFUSED AT PHASE 0. SPP's missing price tail is NOT congestion, and it is not reachable by any hourly quantity mechanism — rule 22 `[R-C3C]`'s model-class limitation is now MEASURED rather than asserted.

**Lane** SPP-29 · **Base** `762cc766b2b9734fc34bd68bb1a02418a4d11efd` · **Keeper UNCHANGED**
`2026-09-10-spp-27-commitment-grain`, bundle `results/calibration/spp27_span` (read, never
written) · **Predecessor** `docs/handoffs/FINDING-spp-64-2026-09-10.md`, whose §9 chartered card
**R-bd** · **LP SPENT: ZERO.** Rule 29 `[R-SCREEN]` clause 0 — the chartered arm has a computable
pre-solve gate and it fails it, twice, on independent evidence. No shard was launched, no screen
solved, nothing registered, no verdict minted, no keeper touched.

**RESULT IN ONE LINE.** R-bd's premise — *"the missing upper tail is CONGESTION RENT"* — is
**false**, and the measurement that falsifies it is SPP's own: hourly congestion rent from SPP's
published RTBM archive has a rank correlation of **+0.019** with the RT hub price, and SPP's own
**day-ahead** market — a security-constrained hourly optimization carrying every one of those
~730 constraints at full nodal resolution — cleared above $200 in **0 of 42** and **0 of 68** of
the 2023 and 2025 RT tail hours. What remains, measured three ways, is **offer markup over
marginal cost in real time**: give the keeper's own fleet SPP's **metered** demand, wind and solar
and price it with perfect foresight, and it still produces **7 / 29 / 0** hours above $200 against
**42 / 59 / 68** actual — **FAIL in all three years on the scorer's own band** — while the real
market charged a median **$241 / $208 / $254 above** the marginal unit's cost, or **9.5× / 7.3× /
9.4×** it. **SPP is unchanged: `CALIBRATED`, grade 7 of 8, 0 fails, 1 ledgered C3c caveat.**

Every number below is re-derived in this session from the committed artifacts and the scorer,
including the numbers the handoff supplied. The instrument is
`scripts/probes/_spp29_c3c_phase0.py` (committed with this document); `--report` reproduces every
table.

---

## 0. What is being scored, stated precisely — because the asymmetry matters

`calibration_verdict.score_price_tail` gates the **model's max zonal dual** above `$200`
(`TAIL_THRESHOLD["SPP"]`, owner ruling P6) against the committed RT actual in
`frontend/data/backcast/tail/actual_tail.json`, band `[0.5×, 2.0×]`, small-count rule
`|Δ| ≤ 10` below 10 actual hours. SPP has **no published reserve overlay**, so `h["overlay"]` is
absent and the gated model quantity is the **energy-only LP dual**.

The actual benchmark is derived by `scripts/data/derive_actual_tail.py` from
`actual_lmp_hourly_SPP.parquet` — the **hub-average** RT series. Verified here: that series and
the two-hub mean of `actual_lmp_hourly_zonal_SPP.parquet` agree to **6.1 × 10⁻⁵ $/MWh**.

So the comparison is **model MAX over zones** against **actual MEAN over hubs**. That asymmetry is
*generous to the model* — and the model still reads 0 / 5 / 0. Re-derived from the keeper's
committed `hourly/system_<year>.parquet`, matching the registered payload's `ordc.hoursGt200`
**exactly**:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| model hours, max zonal dual > $200 | **0** | **5** | **0** |
| keeper LP max zonal price | $59.3126 | $2,000.0000 | $73.7731 |
| committed RT actual (`rt_gt`) | 42 | 59 | 68 |

## 1. R-bd'S PREMISE IS FALSE — the tail is not a congestion object, on three independent readings

### 1a. The scored quantity is a hub AVERAGE, and in 113 of 169 tail hours BOTH hubs are above $200

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| tail hours (hub average > $200) | 42 | 59 | 68 |
| **BOTH hubs > $200 simultaneously** | **32** | **31** | **50** |
| median of the LOWER hub, in tail hours | **$230.80** | **$211.28** | **$259.38** |

Congestion between North and South moves one hub up and the other down around the energy
component; it does not move their mean. In two thirds of the tail the *cheaper* hub is already
above $200. This is a **system-wide energy-price event**, and the model's two-zone reduction is
not what is hiding it.

### 1b. SPP's published congestion does not select the tail hours — ρ = +0.019

From `data/raw/spp-binding-constraints/RTBM-BC-YEARLY-2024.csv.zip`, 5-minute shadow prices
aggregated to the hour (SPP stamps intervals interval-ending, so 00:05 is hour 0). SPP-64's
census is reproduced — **8,546 / 8,760 = 97.6 %** of 2024 hours carry ≥ 1 binding constraint —
and then asked the question SPP-64 did not:

| 2024 statistic | tail-hour percentile (median) | overlap of its top-59 hours with the 59 tail hours | spearman vs RT hub price |
|---|---|---|---|
| binding constraint-intervals | **53.2** | — | — |
| distinct monitored facilities | **54.2** | **1 / 59** | — |
| total congestion rent | 86.7 | 10 / 59 | **+0.019** |
| max shadow price | 83.3 | 14 / 59 | **+0.079** |

**The number of constraints binding in a tail hour is at the 53rd percentile — statistically
indistinguishable from an ordinary hour.** Rent and max shadow price are mildly elevated, but
their own top-59 hours overlap the tail by 10 and 14 of 59, and the rank correlation with price is
**+0.019** — zero. Congestion is not what is happening in those hours; it is what is happening in
*every* hour.

### 1c. SPP's OWN hourly market, which HAS all 730 constraints, produces no tail either

This is the decisive control and it costs nothing: SPP's day-ahead market is an hourly,
security-constrained unit-commitment optimization over the same fleet, the same offers and the
**full nodal network**. If the tail were hourly congestion, DA would show it.

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| RT hours > $200 (hub avg) | 42 | 59 | 68 |
| **DA hours > $200** | **6** | 35 | **0** |
| **DA annual maximum** | $240.55 | $563.55 | **$176.62** |
| RT tail hours in which DA also cleared > $200 | **0 / 42** | 14 / 59 | **0 / 68** |
| RT tail hours in which **DA cleared below $100** | **40 / 42** | 32 / 59 | **66 / 68** |
| median RT − DA wedge, in tail hours | **+$227.48** | +$181.67 | **+$244.04** |
| median RT − DA wedge, all hours | −$4.39 | −$4.07 | −$5.60 |
| share of tail hours with RT > DA | **100 %** | 86 % | **100 %** |

**In 2025 SPP's own hourly market never touched $200 all year while real time did so 68 times.**
The entire tail is the **RT − DA wedge**: +$227 / +$182 / +$244 in tail hours against roughly
−$4 to −$6 in an ordinary hour. That wedge is the 5-minute balancing market's departure from the
hourly commitment — ramp, deployment, forced outage and forecast divergence — and it is exactly
what an 8760 perfect-foresight hourly LP is out of representation to price.

**Consequence for the chartered card:** R-bd is refused. It is *not* refused on a governance
technicality or on cost; it is refused because the object it names does not produce the
phenomenon it was chartered to explain.

## 2. NOR IS IT A QUANTITY ERROR — the model's tail hours are already right, to within 1.4 % of net load

The natural fallback is that the model simply does not see how tight those hours were — R-bc's
phantom wind, or under-modelled outages. It is measured here against EIA-930 and refused.

Alignment is measured, not assumed: the 930 series (interval-ending UTC) converted to fixed UTC-6
and shifted one hour back correlates with the model's own demand array at **0.98369**, against
0.97547 unshifted and 0.94076 the other way.

| model − metered, in the tail hours (GW) | 2023 | 2024 | 2025 |
|---|---|---|---|
| demand | −0.34 | −1.44 | −0.13 |
| **wind** | **+0.18** | **−1.20** | **+0.31** |
| **NET LOAD** | **−0.52** | **−0.25** | **−0.44** |
| *net load, all hours (for contrast)* | *−0.81* | *−1.14* | *−1.08* |

**The phantom wind is not in the tail hours.** The keeper over-delivers +0.85 / +1.33 / +1.35 GW
of wind on an annual average, but in the tail hours it is +0.18 / −1.20 / +0.31 GW — in 2024 the
model carries *less* wind than SPP metered. Net load in the tail hours is right to
**0.25–0.52 GW**, i.e. **1.4 % or better**.

Against that, what reaching $200 would cost:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| model headroom above the marginal unit, in tail hours (median) | 11,669 MW | 7,604 MW | 12,467 MW |
| **MW that must vanish to reach $200** | **10,096** | **5,758** | **11,094** |
| **as a share of that hour's net load** | **43.6 %** | **15.2 %** | **39.6 %** |

A 0.25–0.52 GW quantity error cannot be closed into a 5.8–11.1 GW one. **No quantity mechanism —
congestion, curtailment, outage, demand — reaches this at the scale required.**

Nor is it the offer ceiling, which SPP-64 read as a $74-to-VOLL void. The keeper's stack does
carry an upper region: **1,788 / 2,319 / 1,809 MW with MC > $200** and a **maximum unit MC of
$725.99 / $649.91 / $538.57**. The tail is absent because the LP never climbs that far, not
because there is nothing there to climb.

## 3. THE POSITIVE IDENTIFICATION — a perfect-quantity hourly LP still fails C3c in all three years

The counterfactual that settles it. Take the keeper's **own** reconstructed fleet, availability and
marginal costs, and price them with a merit-order screen against SPP's **metered** net load —
perfect demand, perfect wind, perfect solar, perfect foresight. This is the best an 8760 hourly
marginal-cost model can be.

**The screen is validated against the LP it approximates** (`--report` prints it): given the
*model's* net load it returns **spearman 0.981 / 0.984 / 0.951** against the keeper's max zonal
dual, percentiles within $1–3 through p99, and the scored `hours > $200` count **exactly**:
0 / 5 / 0, matching the LP. It omits the network, commitment floors, the hydro budget and storage
discharge, which makes it *tighter* than the LP — so its counterfactual is an **upper bound** on
what a perfect-quantity hourly LP could reach.

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| keeper LP hours > $200 | 0 | 5 | 0 |
| **perfect-net-load screen, hours > $200** | **7** | **29** *(6 of them literal infeasibility)* | **0** |
| perfect-net-load screen, annual max | $361.73 | $507.50 | **$166.50** |
| actual RT | 42 | 59 | 68 |
| **C3c band `[0.5×, 2.0×]` on perfect quantities** | 0.1667× **FAIL** | 0.4915× **FAIL** | 0.0000× **FAIL** |
| median markup the real market charged over the marginal unit's cost | **+$241.04** | **+$207.82** | **+$254.20** |
| as a multiple of that cost | **9.5×** | **7.3×** | **9.4×** |

**Read the 2025 row.** Hand the model the market's own metered quantities and it prices the whole
year with a maximum of **$166.50**. It cannot reach $200 *once*, in a year the market did so 68
times. The residual is not information the model lacks; it is a price the market charges that a
marginal-cost LP does not contain.

**2024 misses the band by 0.0085** (0.4915 against a 0.5 floor) — the closest any year comes, and
it is the one year whose tail is partly an hourly event (median actual-net-load percentile 95.0,
34 of 59 tail hours in the top decile, DA reaching $563.55). Recorded as the honest edge of this
finding, not smoothed over: **2024 is the year where an hourly mechanism has the most left to
reach**, and §5 routes it.

## 4. WHAT THIS MEANS FOR RULE 22 `[R-C3C]` — the classification is earned, and this is the first SPP measurement of it

Rule 22 absorbs a lone C3c failure as an `ACCEPTED MODEL-CLASS LIMITATION`. Until now that was a
**classification**; for SPP it is now a **measurement**:

1. The tail is the **RT − DA wedge** (+$227 / +$182 / +$244 against −$4 to −$6 ordinary), and the
   hourly market on the other side of that wedge — SPP's own, fully nodal — produces
   **0 / 14 / 0** of those hours itself.
2. It is **not congestion** (ρ = +0.019; tail hours at the 53rd percentile of constraint count).
3. It is **not a quantity error** (net load right to ≤ 1.4 %; $200 needs 15–44 % of net load
   removed).
4. It is **not an offer-ceiling artifact** (1.8–2.3 GW of stack above $200; max unit MC $538–726).
5. A **perfect-quantity, perfect-foresight hourly LP still FAILS the band in all three years**,
   and in 2025 cannot exceed $166.50.

The residual is an **offer markup of 7.3–9.5× marginal cost in real time**. Closing it inside this
model would require an adder on the offer stack sized to the tail — which is precisely the fitted
mechanism rules 1 `[R-STRUCT]` and 13 `[R-MEASURED]` forbid, and which the rule-1 carve-out does
not reach (the authorized `offer_curve_by_group` band multipliers are year-invariant, declared
ex ante and **never swept against a gate**; selecting one because C3c passes is condition (c)'s
named prohibition).

**This lane therefore recommends no change to C3c's standing for SPP, and proposes no rubric
change.** One governance hazard is named rather than left implicit: the rubric already carries a
**DA row as a reported-only diagnostic**, and on that basis SPP's model would read **PASS / FAIL /
PASS** (`|0−6| ≤ 10`, 5/35 = 0.143×, `|0−0| ≤ 10`). **That is reported here as a measurement of the
limitation's size and must not be read as a proposal.** Moving a criterion to the basis on which it
passes is gate-shopping, it is the owner's call and nobody else's, and this lane does not ask for
it.

## 5. THE SUCCESSOR CARDS

> **R-bd is CLOSED as chartered.** Its premise (congestion rent) is falsified in §1 on SPP's own
> published archive and on SPP's own day-ahead market. It should **not** be re-opened as a
> congestion object without new evidence meeting rule 28(a)'s re-test condition.

> **R-bc SURVIVES, and this lane SHARPENS its success criterion.** SPP-64's card is unchanged in
> substance: the model owes the ~11.8 TWh of curtailment under rule 14 `[R-ACCURATE]`, and the
> `spp_curtailment_ceiling` channel (a CF upper bound) cannot deliver the price half, so a
> price-forming curtailment must **replace** it. **What this lane adds is a boundary condition:
> R-bc must be chartered against the NEGATIVE tail and the wind volume ONLY.** §2 shows the
> over-delivered wind is absent from the tail hours (+0.18 / −1.20 / +0.31 GW) and §3 shows the
> upper tail survives perfect quantities — so **a lane that charters R-bc against C3c will fail,
> and it will fail for reasons that have nothing to do with R-bc's merits.** SPP-64 §9's success
> test ("negative hours up toward 1,018, congestion rent up, C3b down") is right; the words
> "and the upper tail" must never be added to it.

> **R-bf (NEW) — the 2024 hourly remnant, and it is the only reachable tail work left.**
> 2024 alone misses the perfect-quantity band by 0.0085 and is the only year whose tail is an
> hourly net-load event (34 of 59 tail hours in the top actual-net-load decile; SPP's own DA
> market reached $563.55 and 35 hours > $200). The model produces 5 hours there, and **all 5 are
> `ISOConfig.voll` infeasibility cliffs, not a scarcity curve** — the keeper's 2024 LP max is
> exactly $2,000.00. The card is: *does the model's supply availability in 2024's 35 DA-tail hours
> match what SPP actually had?* In those hours the model holds a median **8,233 MW** above its
> $74.80 marginal unit. This is a **rule-14 `[R-ACCURATE]` availability question** (winter forced
> outage, fuel interruption, derate — Winter Storm Heather is in this window), it is
> forecast-admissible, it is answerable at **zero LP** against CAMPD, and it is **not** a price
> adder. It is worth one lane. It is **not** worth a topology change.

> **R-ba (unchanged).** SPP-64's bound holds: the merit-order inversion re-ranks classes inside a
> narrow band and cannot by itself produce a price distribution spanning $1,130.

**Explicitly NOT routed: a topology change.** SPP-64 §8 measured 2024 congestion rent across 444
monitored facilities — 23 for half, **115 for 90 %** — and this lane adds that congestion does not
select the tail at all (§1b). A sub-zonal split would cost a data intake, a crosswalk, a topology
build and a full re-calibration of every SPP gate, and §1c says SPP's own fully-nodal hourly market
would not produce the tail even if the build were perfect. **`internal_congestion_split` stays `U`
and this lane recommends against opening it for C3c.**

## 6. GOVERNANCE

- **Rule 29 `[R-SCREEN]` clause 0 — ZERO LP.** The chartered arm was refused on a computable
  pre-solve gate. No shard launched, no screen solved, no span spent, no bundle written. Every
  candidate's kill is a measurement, not a cost argument.
- **Rule 32 `[R-SHARD]`** — satisfied trivially: this session ran no LP in its own container and
  had nothing to hand a shard. The zero-LP work (census, reconstruction, screening, scoring) is
  the parent's by the rule's own clause (a).
- **Rule 31 `[R-RETAIN]` — nothing was created and nothing was deleted. NO `rm` WAS ISSUED.**
  No bundle exists, so **there is no promotion question to put**: this lane has nothing promotable
  on local disk and nothing that will be lost when the container is reclaimed. The keeper's
  committed bundle was read, never written.
- **Rule 15 `[R-DASHBOARD]` — nothing to register.** A run is what gets registered; this lane
  produced none. This document is the record (rule 29(c)).
- **Rule 28 `[R-MECH-MATRIX]` — NO VERDICT MINTED, deliberately.** This lane tested no mechanism;
  it measured the keeper, the actuals and SPP's published archives. `internal_congestion_split`
  and `ordc_scarcity_overlay` stay **`U`**, `energy_reserve_coopt` and `negative_renewable_offers`
  stay **`I`**, `spp_curtailment_ceiling` stays **`O`**. Three cells receive **annotations without
  a cell move**, the precedent SPP-55 and SPP-64 both set.
- **Rule 28(a) DO-NOT-REDO honoured.** `energy_reserve_coopt` is **`I`** on SPP-55's measurement
  (1 / 0 / 0 hours of C3c overlap) and **was not re-tested**. It is independently corroborated
  here from a new direction — the tail's **RT − DA character** (§1c). SPP's reserve shortage is a
  5-minute object, and an overlay adds price **in the hours it is short**; SPP-55 measured those
  hours as 1 / 0 / 0 of the C3c tail, and §1c independently shows the tail is a real-time wedge
  spread across all twelve months and most hours of the day rather than a concentrated shortage
  event. *(No arithmetic bound is offered from the offer caps: SPP's Contingency Reserve Demand
  Curve steps are $275 / $550 / $1,100 per MW — 0.25/0.5/1.0 × the $1,000 Safety-Net Energy Offer
  Cap plus the $100 Contingency Reserve Offer Cap, Protocols v119 §4.1.5.2 — so a shortage step
  is far above the $200 threshold and the kill rests entirely on the measured non-overlap, not on
  the level.)* `spp_curtailment_ceiling` and `negative_renewable_offers` were likewise not
  re-tested.
- **Rule 1 `[R-STRUCT]` / 13 `[R-MEASURED]` — no tuning channel was touched.** The
  `offer_curve_by_group` multipliers stay at the keeper's uniform 0.93 and were not re-cut,
  swept or examined against C3c. No adder, offset, haircut, proxy or rescaled input was proposed.
  The one basis change §4 measures is explicitly **not** proposed.
- **Rule 21 `[R-DOF]`** — ledger unchanged (n_entries 3 / n_residual 2). No mechanism, no free
  parameter.
- **G-DRIFT** — not required: no control differencing was performed and no LP was spent.
- **`[R-HOLDOUT]` was removed 2026-09-09.** No year is protected from being iterated against.
  Every number here is model-**SELECTION** evidence read off a committed keeper, SPP's committed
  published series and the scorer — **not a certified out-of-sample skill claim**, and
  `CALIBRATED` remains a rubric determination rather than one.
- **No `complete` marker and no `frontier` declaration is added, requested or implied.** SPP holds
  neither and this lane changes that in no way.

## 7. WHAT THIS DOES NOT ESTABLISH

- It does **not** prove no mechanism can ever close C3c in SPP. It proves that **no hourly
  quantity mechanism** can, and that the residual is an offer markup of 7.3–9.5× marginal cost.
  A sub-hourly model, or a published markup series admissible under rule 13, is outside what was
  tested — and outside what this codebase represents.
- The §3 counterfactual is a **merit-order screen, not an LP**. It is validated against the keeper
  LP (spearman 0.951–0.984, exact agreement on the scored tail count) and it is deliberately
  tighter than the LP, so it bounds the conclusion in the safe direction — but it is not a solve
  and is not quoted as one.
- It does **not** adjudicate `spp_curtailment_ceiling` (stays `O` on SPP-63's evidence), and it
  does **not** rank card P1's SPP-54 against SPP-57 — fixing flowgate membership while reading
  the shares is the residual-driven selection rule 1 forbids, and §5 recommends against opening
  that lever for C3c at all.
- It does **not** re-read SPP-55's or SPP-63's spent gates.
- **The keeper is untouched and SPP's determination is unchanged: `CALIBRATED`, grade 7 of 8,
  0 fails, 1 ledgered C3c caveat.**
