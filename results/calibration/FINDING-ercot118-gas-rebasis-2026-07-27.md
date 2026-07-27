# FINDING — ERCOT-118: the EP rebasis closes ~40 % of the mid-merit elevation with the measured gas level KEPT; the peak band's per-year p50 is the wrong wall measurement; the committed band is blocked on destroyed data

**Date** 2026-07-27 · **ISO** ERCOT · **Years** 2023–2025 (one invocation, years sequential) ·
**Arm** `ercot118_ep_rebasis_joint` = the ercot115 keeper + `ercot_thermal_dam_availability_coal`
+ `ercot_offer_hrmult_ep_rebasis` (`replay_keeper`, two declared deltas) ·
**Run id** `2026-07-27-ercot118-gas-rebasis-joint` ·
**Pre-commit** `PRECOMMIT-ercot118-gas-rebasis-2026-07-26.md` (pushed at `a586dea` with the
mechanism, the per-year artifact and the scorer BEFORE any year was solved) ·
**Determination** NOT-YET (rejected probe — **ordinary G3 failure mode** per the pre-commit's
fixed decision rule; keeper unchanged: `2026-07-26-ercot115-coal-marginal-hr`)

## 1. What was built (Phase A, the measured fix)

The ERCOT-117-proven derivation⇄dispatch basis inconsistency is closed for the measurable part
of the CC band-multiplier family: `offer_curve_dam_hrmults_ep_yearly.json` re-derives
econ_low/econ_high/peak(B) **per delivery year** on the EP-anchored series
(`HH_daily + ercot_electric_power_gas_basis(year)`; basis vs HH−0.50: +0.50/+0.41/+0.04),
raw-direct from the slimmed disclosure parquets (9.26 M CC curve points). The mechanism
(`ercot_offer_hrmult_ep_rebasis`, default-off, ERCOT-scoped, cache-key-registered) replaces the
pooled overrides, re-applies the keeper's `offer_curve_deltas` unchanged, re-stamps the
conditional peak_ladder rungs, and threads each year's EP delivered mean
(2.5402/2.1067/3.0655 $/MMBtu) as the rebased classes' per-class margin anchor — the whole
markup decomposition on ONE basis (pre-commit §3's audit: the window anchor 2.2494 is verified
HH−0.50-based and stays for non-rebased classes).

**The committed band could not be rebased** (declared ex ante, pre-commit §2): its Min-Gen-Cost
instrument was dropped from the raws by the owner-ordered 2026-07-22 slimming, the parsed
intermediate was never committed, all 2023 publications are past the free MIS retention window,
and the credentialed archive was owner-declined. The CC LSL block therefore keeps pricing
~+$2.6–4.0 above its measured level in 2023/24 in the hours it prices.

## 2. G0 — armed and biting

`ERCOT DAM offer hr-mult EP rebasis` 3/3 years with the exact artifact+delta values;
`coal econ marginal-HR floor` 3/3; `COAL plant-grain redistribution` every year; the margin
line reports 337 tranches on per-class EP anchors; `run_config.json` records the flag and the
rebased curve. Environment parity held: `static TTC kept` 3/3 — the same fallback state as the
ercot115/116/117 baselines. Coal moved +1.2/+2.7/+10.2 TWh vs the keeper (BITE PASS).

## 3. Verdict against the pre-committed predictions

| prediction | result |
|---|---|
| **P1** 2023 AND 2024 [15,25) elevation ≤ $2.0 (from +5.18/+5.03) | **REFUTED**: +3.34/+2.79 — drops of −$1.84/−$2.24, ~half the full-surface ablation's (−$3.46/−$3.39) |
| **P2** 2025 improves ≥ $1.0, ≤$2.0 at risk | **CONFIRMED both halves**: +7.00 → +5.28 (−$1.72); line missed |
| **P3** G3 fails via C3a in the pre-declared mode, magnitude inside the ablation's | **HALF-CONFIRMED**: C3a −16.6→−26.6 / +1.3→−11.5 / +1.5→−5.6 (vs the ablation's −30.9/−16.1/−7.1), mid-merit legs −3.1/−6.6/−4.3 pp ALL toward actual — **but the tail legs are −6.9/−6.2/−2.9 pp, so the failure is NOT solely mid-merit** |
| **P4** C3c within ±5 h every year | **REFUTED**: 72→49 (2023), 13→3 (2024), 1→1 (2025) |
| **P5** BITE | PASS |
| **P6** G1/G2 pass all years, ≥ the envelope arm's own effect | **PASS**: excess −10.9/−6.2/−6.4 pp (envelope alone: −9.1/−5.7/−7.2); spread −0.200/−0.250/−0.075 |

Scorer gates (`ercot116_seasonal_shape.py` verbatim): G1 **PASS**, G2 **PASS**, G3 **FAIL**
(C3a and C3c both breach), BITE **PASS**. Rubric: C1 **16/16 · free 12/12 held**, C2/C4/C5/C7/
C8 PASS, C3a/b/c FAIL (as the keeper), C6 UNATTESTED. **Because C3c breaches alongside C3a,
this is the pre-declared ORDINARY REJECTION, not the escalate-to-owner C3a-only mode.**

## 4. What ERCOT-118 establishes

1. **The rebasis's own mid-merit contribution is real and directional with the measured gas
   level kept.** Under the identical measured envelope, the crossing-band elevation falls
   −$1.3/−$1.4/−$0.7 vs the envelope arm (+4.65/+4.17/+5.98 → +3.34/+2.79/+5.28) and the
   $[10,40) model price moves toward actual in every year — the C3a mid-merit legs are
   −3.1/−6.6/−4.3 pp. C1 16/16 · free 12/12 and every shape gate hold. This is roughly **half**
   of what the ERCOT-117 full-surface ablation achieved, consistent with the two legs the
   scoped rebasis deliberately does not touch: the un-rebasable committed band (the ≤$15
   committed-supply displacement, ERCOT-117 §A) and the CT/ST/coal-passthrough surfaces.
2. **The per-year peak(B) p50 is the wrong wall measurement — the C3c breach's owner.** The
   pooled peak 4.326 is the p50 of each resource's top-of-curve over THREE years; per-year it
   collapses to 2.546/3.501/2.629 because a within-year max is structurally smaller than a
   pooled max and different resources post their wall in different years. Rebasing the peak to
   the per-year p50 deflates the sub-$200 standing scarcity wall (the
   `FINDING-ercot-priceshape` "always-posted wall" the p50-collapse lesson already warned
   about), draining C3c 72→49 / 13→3 and carrying tail legs of −6.9/−6.2 pp — the gate breach
   that rejects the arm. The peak band needs its per-year rebasis expressed as the measured
   QUANTILE LADDER (the dispersion, not the p50) or must stay on the pooled wall while only
   the econ bands go per-year.
3. **The committed band is a data-availability blocker, not a modelling one.** The remaining
   +$2.8–3.3 (2023/24) mid-merit elevation is consistent with the declared un-rebased
   committed block; closing it needs an owner decision — re-authorize the credentialed ERCOT
   archive, or accept a 2024/25-only partial committed intake (2023 is gone on the free path).
4. **The mechanism, artifact and per-class anchor plumbing are keeper-grade and stay,
   default-off.** Byte-identical for every existing config; the pooled artifacts stay frozen
   as the old-basis record.

## 5. Successor lanes (in priority order)

1. **ERCOT-119 — leg-split rebasis (`ercot119-econ-rebasis` candidate):** per-year EP rebasis
   of the ECON bands only, peak kept at the pooled standing wall (or moved to per-year
   quantile ladders); single delta vs this arm, expected to keep the mid-merit gains
   (−$1.3–1.4 crossing-band vs envelope) while clearing C3c. Its pre-commit should also
   pre-register the committed-band residual explicitly.
2. **The committed-band data decision (owner):** credentialed archive vs partial 2024/25
   intake vs accepting the residual.
3. **Phase B (delta re-fit on the re-grounded base)** stays gated behind a shape-clean
   Phase A variant; the summer price-flat coal utilization offset and the coal price-taking
   base remain open per ERCOT-117 §5.

## 6. Declared-not-counted, honoured

No price-MAE argument in either direction; the C3a deepening was predicted (P3) and is
reported as the designed exposure of the keeper's netted scarcity-LOW error, not evidence
against the rebasis direction; the C3c breach is reported as coded with no post-hoc gate edit
and adjudicated by the pre-commit's fixed rule (ordinary rejection); no keeper change is
recommended; the measured coal envelope stays default-off (its re-arming recommendation
required this arm to pass, which it did not).
