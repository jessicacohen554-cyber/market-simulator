# ERCOT G-22 §8 heterogeneity-preserving condition-responsive offer surface — build + A/B (2026-07-09)

**Shorthand:** ercot50. **Bundles:** `results/calibration/ercot50_offer_surface_cond`
(candidate, surface ON) / `ercot50_offer_surface_control` (A/B control, surface OFF
= keeper reproduction). **Keeper stays `2026-07-08-ercot46-clock-steamgas`.**
**Recommendation: REJECT for promotion; KEEP the mechanism in code, default-off.**

## What was built (the filed ercot37 §8 / G-22 §5.1 path)

The measured DAM offer *distribution* posted **condition-responsively** and
**P1-only**, the successor to the two rejected predecessors:

- the flat `ercot_ct_offer_surface` (ercot37) posted one p50 level on every CT
  econ/peak row above a hinge → collapsed offer heterogeneity, removed ~3.2 GW of
  spare in one step, over-corrected the level (calibration-log 2026-07-06);
- the **static** `peak_ladder` wall (ercot33) posted the measured ladder in all 8760
  hours → perturbed P0 run lengths and swapped ~8 TWh CT↔ST through the startup-
  amortization coupling (`FINDING-ercot-priceshape-2026-07.md` §6).

The new mechanism (`ScenarioConfig.ercot_offer_surface_conditional`, default off,
ERCOT-gated) fixes both failure modes structurally:

1. **Distribution / heterogeneity.** The gas peak band (CC_REGULAR, CC_CHP,
   CT_PEAKER, ST_GAS) is split equal-capacity into 5 rungs at the class's resolved
   peak height (a pure structural no-op — 5 equal sub-bands at one MC == one flat
   band). At solve time the upper rungs (p70/p90) are repriced to the measured wall
   while the lower rungs stay at the resolved peak. The measured wall is the 60-Day
   DAM disclosure per-resource top-of-curve quantile ladder
   (`scripts/data/derive_dam_offer_hrmults.py --condition-binned` →
   `offer_curve_dam_hrmults_condbinned.json`).
2. **Condition.** The ladder is derived and applied **per net-load-percentile bin**
   (edges 0.80/0.90/0.97 → 4 bins on the year's own net-load distribution, forward-
   native). The tightest bin binds ~263/8760 h (≈3%).
3. **P1-only, clamped ≥ 1.** The wall is an additive markup on the P1 clearing
   objective ONLY (`pipeline/solve.py::run_energy_solve` `mc_bid_adjust`), so P0 run
   lengths and the CT↔ST coupling are byte-identical to the keeper. The ratio is
   clamped ≥ 1 (no bin lowers an offer below the keeper peak) and the repriced offer
   is capped below VOLL (`ercot_offer_surface_price_cap_frac` = 0.95).

All knobs are in `ScenarioConfig`/`run_config.json` (rule 23), ERCOT-only (rule 24),
derived from source data only (rule 21), rule-13-admissible (net-load driver +
measured QSE quantiles both forward-reproducible). New unit tests:
`tests/test_ercot_offer_surface_conditional.py` (flag-off no-op, only upper rungs
move, condition-responsive, VOLL cap, edge-mismatch guard).

## A/B result (full 2023–2025, single delta = the surface flag)

| year | C3a OFF→ON | C3b OFF→ON | C3c >$200 OFF→ON | DA / RT actual |
|---|---|---|---|---|
| 2023 | +9.3% → **+11.6%** | 0.251 → 0.236 | 104 → **104** | 311 / 181 |
| 2024 | +6.5% → **+11.2%** | 0.185 → **0.265** | 29 → 35 | 68 / 53 |
| 2025 | +4.9% → +6.7% | 0.080 → 0.093 | 4 → **19** | 23 / 31 |

Tail depth (RT, hours): 2023 >$500 95→97 / >$1000 43→46 / >$3000 11→13; 2024
>$1000 11→14; 2025 breadth 4→19. Max price stays ≤ VOLL from the surface (the 7244
in 2023 is a pre-existing VOLL-slack artifact, unchanged).

Candidate determination (rubric v2.2): **C3a FAIL, C3b FAIL, C3c FAIL**; C1/C4/C5a
PASS, C2 CAVEAT-commercial, C7/C8 unchanged from the keeper (the surface is P1-only
and touches no forcing floor). Control determination reproduces the keeper (C3a
PASS-commercial, C3b FAIL-2023-only, C3c FAIL).

## Why REJECT — and what it proves (rule 1 in both directions)

The surface **adds real tail breadth where the peak band is marginal** (2025 +15
toward 23/31; 2024 +6 toward 68/53) — confirming the measured always-posted
scarcity wall is a genuine price-formation mechanism the keeper lacks. **But:**

- **It adds ZERO breadth in 2023** — the acute year, the C3c target. 2023's missed
  tail hours have the model's marginal unit in the *economic* band at ~$43 (below
  the peak band), so repricing the peak band cannot lift the dual there. This is the
  **online-capability wedge** (`FINDING` §3 / structural conclusion #2): the model
  holds ~3.2 GW more cheap econ capacity online than ERCOT's measured RTOLCAP in
  those hours. The measured data itself proves offers are not the gap — the measured
  econ offer is ~$43, matching the model; the gap is *how much capacity was online*.
  No faithful offer lever closes it (making econ_high expensive above its measured
  ~1.45–1.58× would be the rejected ercot37 overshoot). The peak-band wall
  **deepens** hours the co-opt already priced but **cannot flip** the econ-marginal
  missed hours — exactly the ercot33 §6 finding, now re-confirmed P1-only.
- **It over-corrects the level (C3a) in every year**, flipping 2024 PASS→FAIL and
  pushing 2023 past ±10% (the §6.1 pre-committed rejection: a mechanism that hurts
  the current-design years 2024/2025 is rejected). When the wall *is* reached (mild
  years), it lifts the annual mean past the band. 2024 C3b also regresses past its
  0.20 gate.

The pattern is **consistent across all three years** (LOYO within 2023–2025): the
on/off effect is not a one-year artifact — over-correction of C3a in every fold,
breadth gain only where the peak band is already marginal, zero gain in the
wedge-dominated acute year. So the reject holds leave-one-year-out.

Per rule 1 the mechanism is faithful market structure and **stays in the code
default-off** — it is the price-formation layer that will PAIR with the real fix:
once commitment-thinness (structural conclusion #2, the shelved P2/posture family +
weather-correlated sub-2-day outage structure) removes the econ-band spare in the
acute hours, the peak band becomes marginal there and this measured wall sets the
scarcity price. It is necessary-but-not-sufficient; enabling it before the wedge is
closed only over-prices the mean.

## Scoring-frame note (owner)

The surface lands **neither** the RT (181) nor DA (311) 2023 breadth basis — it stays
at 104. The RT/DA gap (~130 h) is the DA scarcity-risk premium the RT model cannot
form (`G-22` §3/§5.2); it is not addressable by any RT-mode mechanism. The 2023 tail
target is dominated by the online-capability wedge, not the offer stack or the
scoring frame.

## Settled context (do not relitigate)

Physical scarcity (temp-derate) is CLOSED (owner 2026-07-09). Reserve-demand space is
DEAD (G-22 thread A). Static offer wall REJECTED (ercot33). Flat CT surface REJECTED
(ercot37). This heterogeneity-preserving, condition-responsive, P1-only variant is
the last sanctioned offer-side remedy — and it confirms the acute-year tail is not an
offer problem. Forward path: commitment thinness (conclusion #2).
