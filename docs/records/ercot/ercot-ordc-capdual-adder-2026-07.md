# ERCOT ORDC additive-adder double-count fix + C3a scoring-frame finding (2026-07-09)

**Shorthand:** ercot52. **Bundles:** `results/calibration/ercot52_ordc_capdual`
(candidate) / `ercot52_ordc_capdual_ablation` (zero-forcing twin). **Config =
the ercot51 coal-net-summer-derate config + `ercot_ordc_cap_dual_adder`** (one
delta; the derate stays ON per the owner's 2026-07-09 disposition). Offer-curve
band multipliers are UNCHANGED from the ercot46 keeper — the assigned "offer
re-tune" turned out not to be an offer problem (§2, §4).

## 1. The task and what the diagnosis actually found

Handed off: ercot51 (coal derate) overshoots C3a (2023 +9.3%→+42.7%) in the
shoulder-summer; re-tune the gas offer stack / co-opt to bring C3a back to
keeper level while keeping the C3c tail (104→162 h). The no-solve decomposition
of the committed ercot51 2023 hours (energy dual vs `ordc_adder` vs
`rtordpa_overlay` columns) found the overshoot is NOT the gas offer stack:

* **The energy-only price surface is already right.** The model's energy-dual
  price-duration curve matches the measured RT settlement tail almost exactly
  (top-100 hours contribute 19.60 model vs 20.00 actual $/MWh of the annual
  mean; top-200: 23.41 vs 23.67), and the tail's hour-of-day / demand-percentile
  timing matches the measured 2023 distribution. On the matched
  demand-weighted zonal basis the full-year energy-only mean is 62.5 vs 65.2
  actual — the co-opt already reproduces 2023 price formation.
* **The additive ORDC adder is a double-count.** 100% of hours with
  `ordc_adder` > $10 have energy duals already > $200 (median $1,957 in
  adder>$50 hours, +$254 median adder on top → totals ~$3,000 vs measured deep
  hours ~$1,200–1,800). The adder contributes +5.5 $/MWh (demand-weighted) of
  the 2023 C3a error and ZERO C3c hours (tail count is 162 h with or without
  it).

## 2. Root cause: the additive construction's premise inverted under the derate

The additive RTORPA construction (`_system_frame`) added the **total-family
balance dual** to the energy price, justified by "a pure reserve cap prices
reserve WITHOUT lifting the energy LMP (energy cancels out of a ΣR cap)". That
premise holds only while the RTOLCAP **supply-cap row** is the binding reserve
constraint. When the **physical shared headroom** binds instead, the balance
dual passes into the energy LMP through the headroom coupling — the repo's own
unit test documents it
(`tests/test_reserve_coopt.py::test_total_shortfall_prices_and_lifts_lmp`:
LMP = MC + total-reserve step) — so re-adding it double-prices the hour.

The coal net-summer derate moved the binding constraint. Pre-derate, summer
fleet headroom sat ABOVE measured RTOLCAP → the cap row bound → adder correct.
Post-derate the physical headroom binds first in every 2023 scarcity hour (the
solved cap-row dual is zero in all 8760 hours), so the whole adder was
double-count. This is why a CEMS-correct ~0.7 GW coal cut moved C3a ~30 pp:
each new shortage hour was priced twice.

**Fix** (`ercot_ordc_cap_dual_adder`, ScenarioConfig-recorded solve kwarg,
default off = keeper-reproducing): source the additive adder from the
**supply-cap rows' own duals** (summed across headroom tiers), which are the
exactly-uninternalized component in BOTH regimes — LP duality: a supplying
reserve column prices λ_balance = λ_cap + μ_headroom, and only μ passes into
the energy dual. When the cap binds, λ_cap carries the full ORDC step (old and
new construction agree); when headroom binds, λ_cap = 0 (energy already
carries it). `DispatchResult.reserve_supply_cap_dual` (n_tiers, T) exposes the
series; three unit tests pin both regimes and the None case. No new parameter,
no price fit, dispatch/duals byte-identical.

## 3. 2023 single-delta A/B (throwaway probes, coal derate ON in every arm)

| arm | C3a | C3b | C3c >$200 (DA 311) |
|---|---|---|---|
| ercot51 baseline (balance-dual adder) | +42.7% | 0.435 | 162 h |
| **+ cap-dual adder (the fix)** | **+31.3%** | **0.260** | **162 h** |
| + cap-dual + G-22 §8 offer surface ON | +35.2% | 0.316 | 166 h |

The surface arm re-confirms ercot50: even with the derate, 2023's missed tail
hours are econ-band-marginal (online-capability wedge) — the measured peak-band
wall adds 4 h of breadth for +3.9 pp C3a / +0.056 C3b. Surface stays
default-off; the wedge (structural conclusion #2) remains the forward path for
the remaining 162→311 C3c gap, whose shape is a missing $100–300 SHOULDER
(model rank-200 price $69 vs actual $191, rank-400 $48 vs $101), not missing
depth.

## 4. The C3a scoring-frame finding (owner decision needed — rubric territory)

With the double-count removed, the remaining "+31.3%" is dominated by a
**basis mismatch in the C3a metric itself**, invisible until a run had a real
scarcity tail:

* Model side (`score_price_mean`): per-zone **hourly-demand-weighted** annual
  mean, zone-demand-weighted across zones.
* Actual side (bench `avgLMP.rt`): **HB_HUBAVG equal-hour mean**
  (`derive_actual_lmp.py`) — no demand weighting, hub not load zone.

2023 actual prices covary strongly with demand (the August tail sits on the
year's top-demand hours), so the two bases diverge by ~+35% in a scarcity
year: **feeding the actual 2023 LZ settlement prices through the scorer's own
formula scores +33.5% "error" against the scorer's own benchmark** (64.55 vs
48.36). The ercot52 candidate (63.48) scores BELOW the perfect-model
construction. On a like-for-like equal-hour system-mean basis the candidate is
**+4.7%** vs the hub bench — the single-digit target of this thread, reached
with zero offer-curve movement.

Implications (not acted on here — rubric v2.x is owner-versioned):
1. Every keeper's historical single-digit C3a (incl. ercot46's +9.3%) was
   partly a cancellation: a too-shallow tail offsets the demand-weighting
   wedge. C3a and C3c are structurally in tension under the current bases —
   the metric penalizes exactly the tail realism the derate added.
2. Candidate fix: score C3a like-for-like (model equal-hour system mean vs
   HB_HUBAVG, or build a demand-weighted actual bench from the committed LZ
   archives). Either is scorer-only (no re-solve); all ISOs should be checked
   for the same asymmetry before any rubric change.
3. Until the rubric decision, ercot52's C3a/C3b rows must be read against the
   +33.5% perfect-model floor recorded here.

## 5. Residual (pre-existing, out of scope here)

The Jan/Feb/Apr winter-shoulder body overshoot (Jan +50%, Feb +34%, Apr +36%
on the demand-weighted monthly basis; CC_REGULAR econ_high marginal at ~$26–31
vs actual clearing ~$22–25) predates the derate — it is byte-identical in the
ercot46 keeper's non-summer months and was previously cancelled by the August
undershoot the derate fixed. It is the main C3b residual. No admissible driver
identified this session; flagged as an open root-cause item (candidate
suspects: winter delivered-gas shape, wind dispatch, CC econ band seasonality).
Do NOT close it with a band trim — the same bands are already slightly UNDER
in the summer body (Jul −2.1, Aug −6.8 $/MWh), so a global trim just moves the
error across seasons (rule 13).

## 6. Settled context (do not relitigate)

Coal derate stays ON (owner 2026-07-09; CEMS-flat Jun–Sep, rule 15). Surface
stays in code default-off (ercot50 + §3 here). Temp-derate CLOSED. The
balance-dual additive construction is retained behind the default-off flag for
keeper reproduction only; any new ERCOT candidate should carry
`ercot_ordc_cap_dual_adder`.
