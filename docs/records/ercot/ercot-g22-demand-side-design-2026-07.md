# ERCOT G-22 demand-side scarcity design round — diagnosis + admissible mechanism space

**Date:** 2026-07-07
**Branch:** `claude/ercot-g22-demand-side-scarcity-om0881`
**Sanction:** owner-sanctioned design round for the reserve-demand side of G-22
(the round the ercot43 FILE-ONLY decision required). Tariff-cited ORDC curve
parameters (LOLP σ, VOLL, min-contingency) stay FROZEN — no sweeps, no offsets,
the deprecated ORDC offset stays deleted (rule 26). Sanctioned scope: a
structural representation of scarcity-year HELD reserve / deployment,
identified on measured MW quantities only.
**Baseline:** keeper `2026-07-07-ercot42-wtx-curtailment-driver` (verified at
HEAD); control bundle `2026-07-07-ercot43-extremeenv-off` (the keeper recipe
replayed at HEAD, registered). ERCOT is NOT-YET on exactly C3b (price shape)
and C3c (tail).
**Reads first:** `docs/handoffs/ercot-online-capacity-envelope-2026-07.md`
§7.3–7.4 (the failure signature this round starts from),
`docs/FINDING-ercot-priceshape-2026-07.md` §2–3 (the tail's settlement
decomposition), `docs/g20-scarcity-price-formation-diagnosis-2026-07.md` (the
cross-ISO wedge).

**Headline.**
1. **Thread A (demand-side scarcity formation): the admissible mechanism space
   is EMPTY — G-22's reserve-demand side is exhausted, on measured-quantity
   grounds, without a build.** The hour-level decomposition (§2) shows the real
   2023 tail formed on *energy offers at non-scarce reserve levels* (measured
   RTOLCAP p50 ≈ 8.0 GW in the missed hours, RTORPA p50 $0.7), and the keeper's
   adder channel already reproduces the measured adder's size and incidence.
   Every candidate that would make the reserve demand side price the missed
   hours either contradicts a measured series it must reproduce (§4, C-1), or
   removes real structure (C-2), or routes through the shared-headroom
   energy-vs-span coupling whose two regimes — slack (inert) and binding
   (over-fire) — are both already tested and rejected (C-3/C-6 = ercot41/43).
   With supply side and demand side both exhausted, the structural remainder of
   C3b/C3c-2023 is **scarcity-anticipating offer formation** (and, for C3c's
   DA-expressible basis, the DAM risk premium): §5.
2. **Thread B (2024/25 measured-HSL data vintage): root-caused at the data
   layer and FIXED.** The NP4-732/737 reports are stamped in Central
   *Prevailing* Time; `scripts/data/build_ercot_hsl.py` placed them on the model's
   fixed CST clock unconverted, so the entire mid-Mar–early-Nov wind/solar
   potential was **one hour late** (Jan best lag 0, Jul best lag +1 vs EIA-930,
   r = 1.0000 at both — the same series, shifted). That handed the dispatch
   3–5 GW of phantom post-sunset solar potential in exactly the scarcity
   window. Fixed (CPT→CST conversion with DSTFLAG disambiguation), parquets
   rebuilt, regression-tested; A/B at HEAD under the §6 pre-committed frame.
   The same defect class affects several sibling measured-series intakes
   (§7) — named rule-23 follow-ups, not silently churned here.

---

## 1. What the ercot43 failure signature asked

The envelope family (ercot41 base grain, ercot43 extreme-peak-resolved grain)
proved that no supply-side on-line-capability cap prices the 2023 tail
correctly while the co-opt demands energy + the full ~10.7 GW ORDC
total-reserve span inside it (`ercot-online-capacity-envelope-2026-07.md`
§7.4). The open questions this round had to answer on data:

* (Q1) why does the LP hold reserve up to the full span where ERCOT's real
  dispatch let PRC fall ~5 GW below it?
* (Q2) does the co-opt's energy-dual coupling over-transfer vs the settlement
  construction (post-SCED adder) — and is "adder at the PRC point" the right
  settlement analogue?
* (Q3) what hour-level room/PRC distribution does the keeper produce vs
  measured in 2023's tight hours?

## 2. The 2023 hour-level decomposition (control bundle, measured series)

Basis: byte-faithful replay of the ercot43 control (= keeper recipe) at HEAD
(`results/calibration/_diag_g22_control`, scratch, NOT registered; tail count
reproduces the registered 103 h exactly). Measured series joined on the model
CST clock with the +1 h prevailing-placement defect (§7) undone. "Room" =
thermal available − dispatch (+ storage power where noted); model energy dual
= zonal demand-weighted price minus the system-wide ORDC-adder and RTORDPA
overlay columns.

**Top-25 % net-load hours of 2023 (n = 2,190), p10/p50/p90:**

| series | p10 | p50 | p90 |
|---|---|---|---|
| model energy dual (dw) | $27 | $35 | $53 |
| model ORDC adder | 0 | 0 | 0 |
| measured SCED λ | $24 | $35 | $137 |
| measured RTORPA | 0 | 0 | $0.5 |
| actual RT hub | $23 | $34 | $134 |
| actual DA hub | $25 | $42 | $274 |
| model thermal room | 6.6 GW | 13.1 GW | 21.8 GW |
| measured RTOLCAP | 7.5 GW | 10.4 GW | 15.1 GW |
| measured PRC | 5.4 GW | 6.3 GW | 7.5 GW |
| measured AS plan (procured) | 6.8 GW | 7.9 GW | 8.8 GW |

**The model 2023 tail is 103 h settled > $200: 101 dual-carried, 2
adder-carried.** Against actual RT (181 h) the split is:

| p10/p50/p90 | HIT (n = 81) | MISS (n = 100) |
|---|---|---|
| model energy dual | $502 / $943 / $2,500 | $37 / **$53** / $75 |
| model ORDC adder | $4.7 / $43 / $540 | 0 / $0.1 / $2.5 |
| measured λ | $283 / $1,247 / $3,728 | $223 / **$443** / $1,408 |
| measured RTORPA | $1 / $19 / $134 | $0 / **$0.7** / $28 |
| model thermal room | 2.2 / 3.7 / 4.9 GW | 5.1 / 6.4 / 11.0 GW |
| measured RTOLCAP | 4.9 / 6.7 / 8.0 GW | 6.2 / **8.0** / 9.0 GW |
| measured PRC | 4.5 / 5.5 / 5.9 GW | 5.1 / 5.8 / 6.3 GW |
| model (room+storage) − RTOLCAP | −0.9 / **+0.01** / +0.9 GW | −0.1 / **+1.7** / +5.8 GW |

Answers:

* **(Q3)** In the **hit** hours the keeper's room already collapses to the
  measured RTOLCAP (median gap +0.01 GW) and the co-opt prices deep — adder
  live, dual $943. In the **missed** hours the residual wedge is +1.7 GW at
  the median (down from the 3.2 GW of the ercot32-era FINDING — the ercot42
  recipe closed roughly half of it), and the marginal unit is mid-merit at
  $53.
* **(Q1) The premise inverts: the real market did not "hold less" in any
  sense the LP can exploit.** The measured *procured* reserve (the AS plan,
  7.9 GW mean in the top-25 %) is what the co-opt's product families already
  demand; realized PRC (6.4 GW mean) fell *below* the procurement in tight
  hours through deployments — but PRC is the frequency-responsive subset, not
  the ORDC's pricing input. The span the total-reserve family demands
  (10.7 GW) is a *pricing* span: the published curve values the residual
  online capability, and in the keeper (headroom slack) holding it is free —
  the family clears against the RTOLCAP-capped supply and its dual IS the
  small measured adder. Nothing in the measured quantities says the market
  "operated 5 GW below the span" in a way the LP mis-represents: RTOLCAP in
  the missed hours was **8.0 GW — above the ORDC knee — and the measured
  adder was $0.7.** The span-vs-PRC gap is real but priced-correct.
* **(Q2) The settlement construction is already faithful, and "adder at the
  PRC point" is refuted by the tariff's own series.** RTORPA is the curve at
  RTOLCAP (online capability), not PRC: in the 181 actual tail hours,
  curve(PRC) p50 = **$253/MWh** while curve(RTOLCAP) p50 = $14 and measured
  RTORPA p50 = **$4.5**. An adder-at-PRC construction would fire a ~$250
  median adder the measured settlement flatly contradicts. The keeper's
  additive construction (total-family dual added post-solve, energy dual
  untouched while headroom is slack) reproduces the measured adder's size
  (2023 mean $1.84 vs measured $0.9) and incidence. The *over*-transfer only
  appears when a capacity cap makes energy and the span compete (the
  envelope arms) — and that regime is the tested, rejected ercot41/43.

**What actually carries the real 2023 tail:** measured λ > $200 in 175 of 181
RT tail hours with RTORPA small — energy offers, with ~8 GW of online
capability still on the system. At those reserve levels no published reserve
demand curve prices scarcity — correctly. The model's $53-vs-$443 miss is the
offer stack (QSEs' scarcity-anticipating wall, measured at p70/p90 =
$266–$2,700+ in the 60-Day disclosure), not reserve demand.

## 3. C3c's DA-expressible basis sharpens the same conclusion

The rubric's C3c-2023 basis is DA actual (311 h > $200) vs the model's 103 h
(0.33×, FAIL). Against **RT** actual (181 h) the same 103 h is **0.57× — inside
the [0.5×, 2.0×] band.** The ~130 h DA–RT wedge is day-ahead scarcity *risk
premium* — hours the DAM priced above $200 on expectation that real-time never
realized. That is the DAM's co-optimized AS/energy expectation channel (the
keeper's measured `dam_as_overlay` carries it for 2024+ but is off for 2023,
and no endogenous DA construction exists), i.e. the same
scarcity-*anticipation* phenomenon as the offer wall, expressed at the DA
boundary. No reserve-demand mechanism in the RT co-opt can close a
DA-expectation gap; it belongs to the offer-formation / DA-boundary thread
(§5).

## 4. The admissible mechanism space, enumerated (rules 13/17/19/26)

Each candidate states its driver/window/forward story and its identification
gate; a candidate dies when a measured series it must reproduce contradicts
it, when it duplicates an existing mechanism's phenomenon (rule 19: reconcile
with `ercot_ordc_total_reserve`, `ercot_reserve_supply_cap`/`_forward`, the
LR/storage credits — never stack), or when its only identification is the
price residual (rule 13/26).

* **C-1 — settle the adder at the PRC point** (re-anchor the ORDC evaluation
  from RTOLCAP to PRC). Driver: measured PRC. Window: tight hours. Forward
  story: PRC-analogue from the co-opt's responsive subset. **REFUTED at the
  identification gate:** the tariff evaluates RTOLCAP; curve(PRC) in the
  actual tail hours is ~$253 median where measured RTORPA is $4.5 — the
  candidate fails to reproduce the *measured adder*, the one quantity it is
  about. Building it would be re-shaping the frozen ORDC family's input to
  manufacture a fire (rule 26 territory). DEAD.
* **C-2 — drop/shrink the ORDC total-reserve family to the AS plan** ("the
  market only held the plan"). Driver: measured ASPLAN. **DEAD under rules
  1/19:** the total family is the structural RTORPA analogue — its dual is
  the validated small adder (and the acute >$1000 tail incidence). Removing
  it deletes real, published market structure to no gain (the adder is not
  what misses).
* **C-3 — represent deployment/ECRS-withholding so "held" reserve tightens
  SCED-dispatchable supply.** The conservative-deployment design is already
  built and on (`ercot_ecrs_conservative_deployment`: pre-2024-08-01 ECRS is
  a rigid VOLL-anchored carve-out; date-gated by the published reform). Its
  LP effect routes through the shared-headroom row, which is **slack** in
  the missed hours (+1.7 GW median beyond measured RTOLCAP, +5.8 GW p90) —
  withholding 2 GW that is free to withhold moves no dual. Making the
  headroom scarce so the carve-out bites IS the on-line-capacity envelope —
  tested at two grains, rejected (ercot41/43), explicitly out of this
  round's sanction ("do not rebuild"). DEAD by reduction to a rejected probe.
* **C-4 — load-resource behaviour.** The LR RRS-UFR credit is already a
  measured, mode-aware supply credit (G4); PRC's load-side component is
  inside it. No measured series licenses a second LR mechanism (rule 19).
  DEAD.
* **C-5 — deployment-depletion of PRC as a reserve-demand reduction** (model
  the scarcity-hour conversion of reserve to energy). The LP already
  co-optimizes exactly that margin; a forced depletion is either a no-op
  (slack headroom) or a fitted year-shape (rule 13's year-pinning bar —
  2023's depletion is the scarcity outcome itself, so a depletion series
  derived from 2023 tight-hour outcomes is feeding the answer back in,
  rule 13's forbidden branch). DEAD.
* **C-6 — pricing-only span (decouple the total family from the headroom
  competition) + an on-line-capability envelope on energy + AS plan only**
  (the "SCED-dispatchable = online HSL − AS responsibility" construction).
  The most structurally attractive form — it reproduces real HASL mechanics
  and removes the ercot43 over-transfer channel. **DEAD at identification,
  twice over:** (a) it inherits the envelope's substrate, whose extreme-tail
  identification is provably year-asymmetric (ercot43 ledger −23 % / −2 % /
  +18 % — unfixable without year-pinning, rule 13); (b) with the span no
  longer graduating the price, an energy+plan envelope binding under
  inelastic demand jumps from the ~$150 offer top straight to VOLL slack —
  a worse intensity profile than the graded steps ercot43 already rejected.
  And the missed hours' measured RTOLCAP (8.0 GW median) says the binding
  frequency needed to price them is *higher than the real system's* — the
  envelope would have to bind in hours the measured capability says it was
  not binding. DEAD.

**Conclusion (thread A): no rule-13-admissible candidate reaches a passing
identification gate; Phase 2 is correctly NOT built.** The reserve-demand
side joins the offer surface (ercot33/37) and the on-line-capability envelope
(ercot41/43) as exhausted G-22 remedies. This closes the mechanism space the
ercot43 §7.4 filing pointed at: the co-opt's energy-vs-span competition is
not mis-designed — it is inert exactly where reality's adder was ~$0, and the
tail lives in offer formation.

## 5. What owns the residual (filed, outside this sanction)

1. **Heterogeneity-preserving, condition-responsive offer surface** — the
   ercot37 §8 filed next step (post the measured offer *distribution* across
   tranches, not the p50 on all rows). The only remedy class the 2023
   decomposition still licenses: the missed hours' λ formed on offers at
   non-scarce reserve levels. Needs its own sanction; the static and
   flat-p50 forms are already rejected probes.
2. **DA-boundary scarcity expectation** (C3c's DA-expressible basis, §3): an
   endogenous or measured-DA construction for 2023 analogous to the 2024+
   `dam_as_overlay`, or a scoring-frame decision that C3c-2023's DA basis
   double-counts a premium the RT model is not supposed to form. Owner-level
   framing question, not a mechanism this round can build.
3. **The residual +1.7 GW online-capability wedge** — what remains of
   commitment thinness after ercot42; any further capability structure needs
   a year-symmetric identification the ercot43 ledger shows does not exist
   in the pooled data (rule 13).

## 6. Thread B — the 2024/25 measured-HSL data vintage: root cause and fix

### 6.1 The defect (found, cited, fixed)

`scripts/data/build_ercot_hsl.py::_parse_report` placed NP4-732/737 report labels
(`DELIVERY_DATE` + `HOUR_ENDING`, Central **Prevailing** Time) on the model's
fixed CST clock without the CPT→CST conversion. Evidence:

* Cross-correlation of the parquet's own delivered column vs EIA-930 (the
  demand clock): **Jan best lag 0, Jul best lag +1, r = 1.0000 at both** —
  identically zero measurement disagreement, pure placement (2024 and 2025;
  2023's UMass source aggregates positionally and is aligned).
* Solstice anchor (2024/2025-06-21): the parquet's solar column equals
  EIA-930 shifted one hour late; EIA-930 matches physical sunrise/sunset on
  CST; the parquet showed 0.7–1.4 GW solar in the 20:00–21:00 CST
  hour — after sunset.
* The source's own DST structure (HE 3 absent on spring-forward day, HE 2
  doubled with `DSTFLAG=Y` on fall-back day) proves the labels prevailing.

**Scarcity-window impact of the defect (measured HSL vs the G7 gross-up it
replaced, mean MW):** 2025 top-1 % net-load solar potential **+4,959 MW**
(6,286 claimed vs 1,244 delivered — phantom post-sunset solar), 2025 DA>$200
hours **+5,226 MW**, 2024 DA>$200 hours **+3,208 MW**; wind shifted −0.6 to
−1.2 GW at the Aug evening peak. After the fix these deltas collapse to
+410 / +466 / −182 MW — the residual being genuine measurement (the
corrected 2024 series says the extreme peak had *more* wind and *less* solar
potential than the gross-up assumed). This is the mechanism behind the
ercot42-attributed "data-vintage effect": C3b-2024 ablation 0.225 (Aug-2024
+13.2 of +16.4), C3c-2025 collapse to 1 h vs DA 23 h, C2-2025 gas −6.4 % —
phantom evening solar suppressing exactly the evening tightness those
criteria score.

**Fix (this branch):** `_prevailing_to_standard()` in
`scripts/data/build_ercot_hsl.py` — tz-localize to US/Central with the reports'
`DSTFLAG` disambiguating the fall-back repeat, convert to fixed UTC-6, drop
tz; both report families (hourly HE and 5-minute stamps) converted; the CST
clock is covered gapless through both DST transitions (regression tests in
`tests/test_ercot_hsl.py`: winter identity, June −1 h, spring/fall coverage).
2024/2025 parquets rebuilt; annual totals unchanged (level was never the
issue); post-rebuild lags 0 everywhere and the solstice rows match EIA-930
byte-for-byte. **Rule-23 citation: the re-derive responds to a placement
defect in this repo's intake of the unchanged ERCOT source reports — not to
any residual.** Under rule 14 the corrected data is the standing input
regardless of what it does to any score.

### 6.2 Pre-committed evaluation frame for the ercot44 A/B (committed BEFORE the treatment readout)

* **Arms:** control = registered `2026-07-07-ercot43-extremeenv-off` (keeper
  recipe at HEAD, pre-fix parquets; reproduced in-container: 2023 tail 103 h
  exact). Treatment = `ercot44_hsl_clock_fix`: identical recipe at HEAD,
  single delta = the rebuilt 2024/2025 HSL parquets. 2023 must be
  **byte-identical** across arms (its parquet is untouched) — a failed
  identity is a replay-contract bug, not a result.
* **Score:** the official rubric (`calibration_verdict.py`) on the ercot43
  acceptance frame — C3a/C3b/C3c per year + C1/C2 volumes + D-8
  class-volume neutrality (2023 must not move; 2024/25 moves must be the
  renewable-shape effect, reported per class) + measured-quantity
  reproduction ([3e] curtailment vs reported).
* **Decision rule:** the data fix is kept unconditionally (rule 14) — the
  A/B decides the *keeper*, not the fix. If the treatment's verdict is
  equal-or-better it is the keeper-candidate (owner decision, rule 21
  artifacts required). If it *worsens* a current-design year, that is a
  discovered compensation elsewhere (rule 14): register the arm, open the
  root-cause item, keeper stays. No coefficient may move in response
  (rules 20/23) — specifically the WTX depth pair and the WS-A
  shares/deliverability stay frozen even though their derivations consumed
  net-load built on the defective clock; their re-derives are §7 follow-ups.
* Both arms live on the dashboard whatever the outcome (rule 15); all three
  years in one bundle (rule 16); holdouts untouched (rule 22).

## 7. Systemic follow-ups the same defect class opens (named, NOT churned here)

The naive place-prevailing-labels-on-the-CST-clock pattern is shared by other
ERCOT measured-series intakes. Verified by the same Jan/Jul lag test:

| series | consumer | Jul lag | consequence | action |
|---|---|---|---|---|
| `ercot_<yr>_ordc_reserves_hourly.parquet` (`fetch_ercot_ordc_reserves.py`) — RTOLCAP/RTOFFCAP/PRC/RTORPA/RTORDPA/λ | measured reserve-supply cap (in-LP when `ercot_reserve_supply_forward` is off), RTORDPA overlay (in the keeper's settled price), WS-A/envelope derives + validation gates, every G-22 diagnosis join | **+1 (all 3 years)** | evening RTOLCAP one hour late = supply cap too loose in the falling-into-peak hours; RTORDPA overlay lands an hour off; derive conditioning (net-load decile × the shifted series) blurred | own round: fix fetch script, rebuild, re-run the WS-A + envelope identification gates (rule 23 — same placement-defect citation); re-gate the keeper |
| `ercot-AS` series (`build_ercot_as_withholding.py` family): AS plan requirements, storage-AS award credit, LR RRS-UFR credit | multiproduct co-opt requirements + credits (in-LP) | defect confirmed at the builder (same naive HE−1 placement, spring-gap interpolation tell); lag test inconclusive — DAM plan series are too smooth to phase-detect | requirements/credits one hour late in the DST window; impact bounded by the series' smoothness | fold into the same fetch-fix round |
| `ercot-wtx-congestion` (NP6-86 SCED binding, `curate_ercot_wtx_congestion.py`) | the KEEPER's curtailment-share table (hour axis of SHAPE) | expected same (SCED stamps prevailing) | summer binding-frequency hour cells shifted one hour | rule-23 re-derive of the share table + LOYO re-check before any keeper re-gate |
| `actual_lmp_hourly_ERCOT.parquet` (+ DA) | **validation only** (never an input) | documented (FINDING §3: model-vs-hub best at lag −1 Jun–Sep) | monthly/count metrics ~insensitive; hour-matched diagnostics must keep shifting | scorer-side note; align when the reserves fetch is fixed so all measured joins share one convention |

These are each a one-line-diagnosis but a keeper-identification-touching
rebuild (the WS-A deliverability coefficients, the envelope share tables, the
WTX share table and the ECRS reform-hour window all condition on the affected
clocks), so per rules 20/23 each gets its own cited re-derive + re-gate round
rather than a silent batch fix under this sanction.

## 8. Register / deliverables

* Thread A: **no build** (§4) — G-22's register row should record the
  demand side as exhausted-with-evidence; residual ownership per §5.
* Thread B: builder fix + rebuilt 2024/25 parquets + tests (this branch),
  ercot44 A/B solved and registered per §6.2, rule-23 citation in §6.1.
* Follow-up register items per §7 (reserves-parquet clock fix round; AS
  series verification; WTX share-table re-derive; scorer clock note).
