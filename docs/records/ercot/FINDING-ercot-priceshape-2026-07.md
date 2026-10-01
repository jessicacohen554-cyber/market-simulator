# FINDING — ERCOT price shape (C3b) and scarcity tail (C3c): month×hour and mechanism attribution

**Date:** 2026-07-05
**Basis:** the ercot32 keeper (`results/calibration/ercot_ordc_total_rtolcap_v1`,
run id `2026-07-03-ercot32-ordc-total-rtolcap`), scored on the extended rubric
(C1–C8). Standing fails this finding decomposes: **C3b** monthly-shape NRMSE
2023 = 0.393 and 2024 = 0.235 (gate ≤ 0.15), **C3c** tail 2023 = 77 h model vs
181 h actual (0.43×) and 2025 = 10 h vs 31 h (0.32×; gate [0.7×, 1.5×]).
**Method:** the actual 2023 >$200 hour list (hub-average RT, the C3c basis) is
classified hour-by-hour against ERCOT's own published price-formation
decomposition (NP6-323 SCED system lambda + RTORPA + RTORDPA, PRC/RTOLCAP
reserve levels, zonal hub spreads) and against the model's state in the SAME
hours (byte-faithful keeper replay: hourly zonal duals, ORDC-family adder,
reserve prices, slack). Attribution, not guesswork.

---

## 1. C3b decomposes into two separable phenomena

Monthly load-weighted model-vs-actual RT price (committed keeper payload vs
`actual_lmp.json`), the months that carry each year's NRMSE:

| year | NRMSE | dominant months (model − actual, $/MWh) |
|---|---|---|
| 2023 | 0.393 | **Aug −62.4**, Jun −13.5, Jul −8.4, Jan +7.9 — the scarcity summer |
| 2024 | 0.234 | **Jan +18.2, May +9.4** (over), Nov −6.1 — the DAM-AS overlay's DA-boundary premium months |
| 2025 | 0.087 | none > ±6 — passes |

C3b-2023 **is** C3c-2023: the same underpriced scarcity hours (Aug/Jun/Jul
evenings) carry both the monthly-shape RMSE and the missing tail count. Fixing
the tail's root cause fixes 2023 shape; there is no separate 2023 "shape"
problem. C3b-2024 is the opposite sign and a different mechanism — the
measured DAM-AS overlay adds the day-ahead AS scarcity premium (realized DA
$599/$511 on the Jan/May acute days) onto an RT-scored benchmark (RT $205/$316)
— the keeper's documented MODEL MISS (calibration log 2026-07-03, root cause 4).

## 2. The actual 2023 tail is ENERGY-OFFER scarcity, not adder scarcity

Decomposing each of the 181 actual >$200 hours by ERCOT's own settlement
identity (RTSPP ≈ SCED system lambda + RTORPA + RTORDPA):

- **175 of 181 hours: SCED system lambda itself > $200.** The marginal *energy
  offer* set the price. Only ~3–6 hours are adder-carried (lambda ≤ $200 lifted
  over by RTORPA/RTORDPA). RTORPA exceeded $50/MWh in just 35 of the 181 hours.
- **Reserves were NOT at the ORDC knee**: PRC in the tail hours p10/p50/p90 =
  4.7/5.6/6.2 GW — well above the ~3 GW LOLP knee, which is exactly why the
  measured RTORPA stayed small (monthly means $0–134 in tail hours).
- **Same signature in 2024 and 2025**: 2024 actual tail 53 h, 50 lambda-carried
  (mean lambda $601, mean RTORPA $29); 2025 tail 31 h, 25 lambda-carried
  (mean lambda $431, mean RTORPA $2).
- **Where/when:** 2023: Aug 100 h, Sep 32, Jun 14, Jul 11, rest scattered;
  hour-of-day 14–20 dominates (173/181 between HOD 13 and 20). Net load in the
  tail hours: 143/181 at ≥ p95 of the year, 57/181 at ≥ p99.

Mechanism classification of the actual tail against the four candidates:

| candidate mechanism | verdict | evidence |
|---|---|---|
| (a) reserve/ORDC scarcity the co-opt underprices | **exonerated (≤6 h/yr)** | actual adders carried ~3–6 of 181 hours; PRC sat 4.7–6.2 GW, above the knee; the model's lumped-ORDC family on measured RTOLCAP supply already reproduces the *adder's* small size |
| (b) congestion/GTC hours the zonal topology can't see | **exonerated at the hub level (~3 h)** | the C3c metric is the hub-average RT; only 3–6 hours have lambda ≤ $200 with the hub average lifted over $200 by zonal spread. (Zonal spread > $50 exists in 121/181 hours but rides ON TOP of a > $200 systemwide lambda — it moves West/Houston basis, not the hub-average tail count.) |
| (c) outage-driven tightness the statistical WEFOR smooths away | **co-primary as *online-capability* tightness, quantified in §3** | this is a backcast with the CAMPD ≥2-day overlay already on, so what remains is not WEFOR smoothing but the *online-capability wedge*: in the missed hours the model holds ~3.2 GW of spare dispatchable sub-$200 capacity beyond even the measured RTOLCAP — the P1 perfect-commitment assumption plus the sub-2-day forced-outage/heat-derate tail. ~1.7–2 GW of that wedge is the mispriced peak band itself (fixable by (d)); the remainder is genuine commitment/short-outage structure the LP lacks — filed, not tuned |
| (d) net-load extremes mispriced by the offer stack | **INDICTED — the primary fixable mechanism** | 143/181 hours at net-load ≥ p95; actual lambda formed on QSE offers that steepen toward the $5,000 cap (HCAP) as PRC tightens; the model's offer stack tops out at ~$84–150 (class-median peak multipliers). In the 76 hours the model catches, the co-opt's shortage pricing carries it; in the 105 it misses, the spare capacity that keeps the dual at $45 is mostly peak-band MW the disclosure says is really offered at $266–$2,700+ |

## 3. The model in the same 181 hours (byte-faithful keeper replay)

Replay of the keeper's own `meta.json` (`scripts/replay_keeper.py`, scratch
out-dir, not registered), hourly per-zone duals + overlay columns, joined
DST-aware (the model's 8760 clock is local **standard** time; the ERCOT actual
series are local **prevailing**, so summer hours shift by one — verified by
cross-correlation, model-vs-hub best at lag −1 in Jun–Sep, 0 in winter).

- **Model tail composition is now offer/co-opt-carried, not overlay-carried**:
  of the model's 2023 >$200 hours, ~90/93 have the LP energy dual itself
  > $200 (the co-opt's VOLL-anchored reserve-shortage penalties propagating
  into the energy dual in genuinely tight hours, plus 4 VOLL-slack hours);
  only ~3 are overlay/adder-carried. 2024 is different: 56 of 78 model tail
  hours are `dam_as_overlay`-carried (the measured DA MCPC), only 22 from the
  LP dual — the 2024 tail PASS is mostly the measured overlay, not formed
  price. 2025: 6 LP + 4 overlay = 10 h vs actual 31.
- **The model catches 76 of the 181 actual 2023 tail hours** (it prices those
  deep — sometimes deeper than actual; note the un-clamped energy+adder sum
  can exceed the $5,000 RTSPP cap, max $7,221). **In the 105 missed hours the
  model is not even near its stack top: LP dual p50 = $43, p90 = $51** — the
  marginal unit is mid-merit CC econ, with GWs of cheap headroom to spare.
  60 of the 105 missed hours are August; 47 had actual RT > $500.
- **The wedge is supply-state, measured**: in the missed hours the model's
  available-thermal headroom (available capacity − dispatch) averages
  **10.9 GW**, while ERCOT's *measured* real-time online-responsive capability
  (RTOLCAP) in the same hours averages **7.7 GW** (actual PRC 5.7 GW). Even
  after the co-opt holds the full measured reserve supply, the model retains
  **~3.2 GW of spare sub-$200 energy capacity** the real system did not have
  online — so its dual sits at $45 where SCED's sat at $600+. In the 76 hit
  hours that spare is only ~1.3 GW, and the co-opt prices scarcity correctly.
  The wedge is the P1 LP's perfect-commitment assumption (every available MW
  can serve energy instantly; ERCOT's real online fleet was thinner) plus the
  sub-2-day forced-outage/heat-derate tail the ≥2-day CAMPD detector misses.
- **The peak band sits inside that wedge**: available peak-tranche capacity
  (CC/CT/ST gas) in the missed hours averages 4.2 GW with only 0.4 GW
  dispatched. Repricing its measured upper rungs (≥p70 ≈ 1.7 GW to
  $266–$850+, ≥p90 ≈ 0.8 GW to $2,700+) converts most of the phantom
  sub-$200 spare into correctly-priced scarcity supply — the model's
  effective cheap headroom in the missed hours drops to roughly the hit-hour
  level, which is what lets the co-opt + offer stack price those hours. The
  ladder's lower rungs (p10/p30) stay above the econ band at every rung
  (CC 1.57 > econ_high 1.454; CT 2.03 > 1.413; ST 2.44 > 2.043), so the
  supply curve remains rising and the class's median offer is unchanged.

## 4. The structural gap: the measured offer distribution's upper half is collapsed to its median

The keeper's gas offer heights are already *measured* — the 60-Day DAM
disclosure capacity-weighted **p50** per band
(`data/raw/_validation-source/offer_curve_dam_hrmults.json`, mode B,
`docs/ercot-dam-offer-hrmults-2026-06.md`). But representing every plant's
peak band at the class **median** discards the across-resource dispersion the
same measurement produced, and that upper half is exactly the real market's
scarcity wall (measured, pooled 2023–2025 delivery, capacity-weighted
quantiles of each resource's top-of-curve multiplier, incl. near-cap bids):

| output group | p10 | p30 | p50 (current model) | p70 | p90 | $ at $2.5/MMBtu gas (p70 / p90) |
|---|---|---|---|---|---|---|
| CC_REGULAR | 1.57 | 2.57 | **4.33** | 43.9 | 144.2 | $850 / $2,790 |
| CC_CHP | 1.54 | 2.52 | **4.25** | 43.1 | 141.6 | $850 / $2,790 |
| CT_PEAKER | 2.03 | 3.45 | **5.39** | 9.8 | 124.6 | $266 / $3,397 |
| ST_GAS | 2.44 | 3.06 | **4.10** | 22.8 | 194.2 | $638 / $5,429 |

The aggregate MW the disclosure shows offered at scarcity prices is *condition
-responsive*: hours-average ~240 MW ≥ $200 across the gas classes, but
**~1,320 MW mean (p90 2,690 MW) in the Aug-2023 HE17–20 hours** — QSEs
re-offer the wall wider when tightness is anticipated. A static
across-resource quantile ladder reproduces the right order of magnitude
(~1.5–3 GW of >$200 offer capacity across CC+CT+ST peak bands) and is
self-gating: those MW only price when the model's own demand digs into them.

**Why the current single-price peak band physically cannot produce the tail:**
with every CC peak MW at $84 and every CT peak MW at ~$150, the model's
highest energy offer is ~$150–200; its duals top out there, and the entire
modeled tail must then come from the ORDC-family adder — which the measured
RTORPA says was small in these hours. The keeper's model tail (77 h) is
adder-carried; the actual tail (181 h) is offer-carried. The C3c ratio 0.43×
masks that the tail *composition* is wrong even where the count overlaps.

## 5. What this finding does and does not license (rules 1, 13, 26)

- **Licensed — represent the measured peak-band offer DISTRIBUTION's upper
  half instead of collapsing it to the median**: split each gas plant's peak
  tranche into equal-capacity rungs at the capacity-weighted
  p10/p30/p50/p70/p90 of the same measured distribution the current p50 came
  from, **each rung clamped from below at the class p50**. Same source data
  (`ercot_dam_offers.parquet`, already the offer-height grounding), same
  derivation method (mode B, per-resource top-of-curve, capacity-weighted),
  zero residual input — the change is *not throwing away* measurement the
  pipeline already made. Forward story: re-derive from any year's disclosure;
  multiplier form scales with fuel price; the wall's existence is market
  design (energy offers may reach the published HCAP = $5,000, 16 TAC
  §25.505(g)(6)(B)) and its size is measured QSE behaviour, the same
  admissibility class as CAMPD-derived emission rates (rule 13).
  *Why the below-median clamp is structural, not a fit:* an unclamped
  first-probe (2023, single delta) let the sub-p50 rungs re-price 40% of
  every plant's scarcity band below the class median — MW that belongs to
  resources whose *entire* curve is cheap and which the model already prices
  through those plants' cheaper committed/econ bands. The result was the
  documented CT↔ST coupling crater (CT_PEAKER +5.3 TWh, ST_GAS −8.0 TWh vs
  CAMPD-measured volumes) with **no tail gain** (91 vs 90 raw-dual hours) —
  the cheap rungs re-added exactly the spare sub-$200 capacity the expensive
  rungs removed. The clamp (a plant's scarcity band never bids below its
  class's measured median top-of-curve) makes the ladder a pure upward
  widening: the sub-$200 stack is byte-identical to the keeper's and only
  the measured wall (p70/p90 rungs, ~40% of band capacity) is added.
- **NOT licensed — sweeping the ORDC parameters** (tariff-cited, rule 26
  killed the re-armable offset), **any adder/haircut on the residual**, or
  gating the wall by *realized* prices/outcomes.
- **Structural remainder, filed not tuned**: (i) the sub-2-day forced-outage
  tail during heat events (CAMPD ≥2-day detector floor) — needs
  weather-correlated short-outage structure, not a bigger wall; (ii) the
  DAM-AS overlay's DA-boundary premium on 2024 Jan/May (an RT-scored
  benchmark vs a DA-priced overlay — a scoring-boundary mismatch, kept as
  documented MODEL MISS unless the wall lets the RT co-opt form those days
  endogenously, in which case one-event-one-channel (rule 19) requires
  re-examining the overlay); (iii) nodal/intra-zone congestion basis (C1
  exception thread, unchanged — exonerated for C3c).

## 6. Probe results (ercot33 offer wall) and verdict — REJECTED PROBE, keeper stays ercot32

Two probe arms were solved this session (3 years, one invocation each, single
delta vs the ercot32 keeper config):

1. **Unclamped ladder** (p10/p30/p50/p70/p90 as-measured; diagnostic, deleted
   after the same-session clamped re-run superseded it): 2023 raw-dual tail
   91 vs keeper-replay 90 — **no tail gain** — while CT_PEAKER +5.3 TWh /
   ST_GAS −8.0 TWh vs the CAMPD-measured volumes. The sub-median rungs
   re-added exactly the cheap spare the wall rungs removed (§5).
2. **p50-clamped ladder** (`results/calibration/ercot_offer_wall_v1`,
   registered): the price side moves the right way in the scarcity year —
   2023 C3a −6.7 → −2.9%, C3b NRMSE 0.375 → 0.336, >$500 deep-tail 64 → 75 h
   (actual 104), D-2 forced-energy PASSes (keeper FAILs) — but the mild years
   lift broadly (2024 C3a +2.3 → +6.6%, 2025 +3.8 → +7.7% on the same
   in-container replay basis; 2025 would flip its official C3a PASS), the
   >$200 tail count barely moves (93 → 94 in 2023: the wall deepens hours the
   co-opt already priced, it does not flip the 105 missed mid-merit hours),
   and — decisively — **the CT↔ST mid-merit knife edge flips**: ST_GAS
   committed/econ −7.5 TWh, CT_PEAKER committed/econ +5.9 TWh (2023: model
   CT 10.4 vs measured ~6.4, ST 6.3 vs ~16.8 TWh). The peak rungs themselves
   dispatch almost nothing — the swap runs through the P0→P1 startup
   amortization: repricing 40% of the peak bands perturbs P0 run lengths,
   which re-amortize startup into the P1 committed bids, and the documented
   −0.25 CT↔ST offer coupling does the rest.

**Verdict (rule #1 applied in both directions):** the *mechanism* — a
measured, always-posted scarcity wall in the energy offer stack — is real
market structure the keeper lacks, and the attribution stands. But the
*static* representation is not faithful either (the measured wall is
condition-responsive: ~240 MW ≥$200 in an average hour vs ~1.3–2.7 GW in
anticipated-tight hours — a static 1.7 GW over-withholds every mild day), and
its side effect through the startup-amortization coupling produces class
volumes the measured CAMPD dispatch contradicts. A probe that improves the
price residual while moving 8 TWh of mid-merit energy off the measured
allocation is **not structurally superior**; promoting it would be exactly
the fit-first mistake rule #1 forbids. The keeper stays
`2026-07-03-ercot32-ordc-total-rtolcap`.

**Filed structural conclusions (the honest C3b/C3c answer):**

1. **Condition-responsive offer surface** — the disclosure supports deriving
   the ladder *per anticipated-tightness state* (bin delivery-days by their
   net-load percentile; the model selects the curve by its own day state —
   forward-derivable, condition-responsive, rule-13-admissible). This is the
   right form of the wall; the static ladder machinery built this session
   (`peak_ladder` band, `derive_dam_offer_hrmults --peak-ladder`, opt-in
   artifact `offer_curve_dam_hrmults_ladder.json`) is its substrate and
   stays, inert by default.
2. **Online-capability structure** — §3's measured wedge (model spare
   sub-$200 headroom ~3.2 GW beyond RTOLCAP in the missed hours): the P1
   perfect-commitment assumption plus sub-2-day forced outages. No offer
   height fixes this; it needs commitment thinness (the shelved P2 family)
   and/or weather-correlated short-outage structure.
3. **CT↔ST startup-amortization fragility** — an ~8 TWh mid-merit allocation
   flips on a 1.7 GW top-of-stack perturbation (and the keeper itself is not
   container-reproducible: a byte-faithful replay on current main lands
   CC_REGULAR at 145.4 TWh vs the committed bundle's 133.2, ST_GAS 15.1 vs
   16.8, 2024 C3a +2.3% vs the committed +9.1% — code/data drift on main
   since 2026-07-03, GTC ruled out in-container). Both belong in the D-8
   coefficient-stability thread; a class allocation this sensitive cannot
   carry calibration weight.

**§6.3 addendum (2026-07-06, G-12 attribution complete — L-12 wave 3).** The
"not container-reproducible" reading above is now root-caused and is NOT
knife-edge sensitivity or code/data drift in the solve path. Three named
movers, in order of size:

1. **A replay-contract gap (dominant).** The keeper solved with
   `ercot_zonal_gas_basis=True`, `ercot_west_netload_gas_shape=True`,
   `ercot_west_gas_delivered_floor=0.4` and `oil_primary_bin_fuel=True` —
   proven by the committed bundle's resolved `run_config.json` — but
   `solve_and_persist`'s `meta.json` writer does not persist these four
   fields, and their `ScenarioConfig` defaults are False/null. Every
   "byte-faithful" `replay_keeper.py` replay (this finding's §3/§6.3 replay,
   `2026-07-03-32-head-regate`, the ercot33 ex-overlay baseline, the ercot40
   WS-A probe) therefore silently solved WITHOUT the ERCOT zonal/West-Waha
   delivered-gas geography — a different merit order for all 963 ERCOT gas
   units. Re-adding the four flags via `--set` restores the keeper's class
   allocation (the ercot34/ercot35 A/B pair on the dashboard quantifies the
   arm-to-arm movement). Same disease class as the pjm-77 `ct_netload_drag`
   meta-gap fix; the CAISO post-07-03 drift (#1346) should be checked for
   the same mechanism (its keeper also carries CLI-only config). Fix owner:
   the meta writer is `run_calibration_full.py` (orchestrator-unification
   lane), outside L-12 file ownership.
2. **Coal max-CF re-derive** (`f5543232`, 2026-07-03T20:10Z, ~50 min after
   the keeper's solve): dropped the year-pinned hand ceilings for
   CAMPD-derived flat physics ceilings (Limestone 298 0.82/0.86/0.87 →
   0.95; Fayette 6179 0.99; J K Spruce 7097 0.95; Oak Grove 6180 uncapped)
   — a rule-23-compliant re-derive with its own registered probe; explains
   the year-constant coal `cap_mw` signature in the replay diff.
3. **fleet.py curated-bin-drift reconciliation** (#1451's identified
   contributor, ~450 MW reclassified): predominantly LABEL movement —
   CC_CHP −4.3 and CT_CHP −2.2 TWh/yr move between class totals while the
   underlying plants' dispatch is nearly unchanged (CC_CHP plant-grain
   −0.36/−0.25/−0.37 TWh by year).

Consequence for the D-8 thread: the 10–18 TWh/yr CC_REGULAR replay swing was
a *config divergence*, not coefficient instability; the CT↔ST coupling
fragility observed IN-container (the offer-wall probe, same config both arms)
stands on its own evidence and remains the open D-8 item.
