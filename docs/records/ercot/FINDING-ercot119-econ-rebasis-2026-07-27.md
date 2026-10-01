# FINDING — ERCOT-119: the leg-split refutes the peak-leg attribution — the ECON legs own both the mid-merit gain AND the C3c tail drain; the peak wall is nearly inert

**Date** 2026-07-27 · **ISO** ERCOT · **Years** 2023–2025 (one invocation, years sequential) ·
**Arm** `ercot119_econ_rebasis_joint` = the ercot115 keeper + `ercot_thermal_dam_availability_coal`
+ `ercot_offer_hrmult_ep_rebasis` scoped to `["econ_low","econ_high"]` (`replay_keeper`, three
declared `--set` deltas; single mechanism delta vs the ERCOT-118 arm) ·
**Run id** `2026-07-27-ercot119-econ-rebasis-joint` ·
**Pre-commit** `PRECOMMIT-ercot119-econ-rebasis-2026-07-27.md` (pushed at `aa80740` with the
band-scope mechanism BEFORE any year was solved) ·
**Determination** NOT-YET (rejected probe — **ordinary rejection** per the pre-commit's fixed
decision rule, gate (b) C3c breach; keeper unchanged: `2026-07-26-ercot115-coal-marginal-hr`,
per the pre-declared rule no promotion question arises)

## 1. What was built

`ScenarioConfig.ercot_offer_hrmult_ep_rebasis_bands` (default None = all artifact bands,
cache-key-registered, neutral at default — the pinned-key drift check confirms the default key
unchanged) restricts the ERCOT-118 per-year EP rebasis to the named artifact bands. Armed at
`["econ_low","econ_high"]`: the CC econ bands take their per-year EP-basis values (+ the
keeper's own deltas) while the peak standing wall, its conditional-surface ladder rungs, and
the committed band keep the keeper's resolved values (CC_REGULAR peak 4.576, CC_CHP 3.748).
Anchor threading became band-scoped (`margin_anchor_<band>` keys, resolved per tranche by the
new `offer_curves.band_margin_anchor`): the rebased econ markups price at the year's EP
identification anchor, the un-rebased peak/committed markups stay on the window anchor 2.2494.
`bands=None` reproduces ERCOT-118 byte-identically (test-pinned).

## 2. G0 — armed and biting, exactly as pre-committed

`ERCOT DAM offer hr-mult EP rebasis` 3/3 with `scope=econ_low,econ_high` and EXACTLY 4 band
replacements per year at the precomputed values; `coal econ marginal-HR floor` 3/3; `COAL
plant-grain redistribution` every year; margin lines report **192/192/190 tranches on
per-class EP anchors** (< ERCOT-118's 337 — the peak rungs back on the window anchor, the
pre-registered signature); `run_config.json`/`meta.json` record the flag, the scope (both
`--set` channels agreed; only the known keeper-lineage `ercot_wtx_curtailment_driver` stomp
WARNING appeared, prb value True active as in every baseline), and the scoped curve.
Environment parity held: `static TTC kept` 3/3, highspy 1.14.0 — the same fallback state as
the ercot115/116/117/118 baselines. BITE PASS: coal 59.34→60.55 / 57.32→60.05 / 60.29→70.52
TWh vs the keeper.

## 3. Verdict against the pre-registered gates

| gate | result |
|---|---|
| **(a)** crossing-band [15,25) retention ≥ 80 % of the ERCOT-118 drop (≤ +3.71/+3.24/+5.62) | **PASS**: +3.34/+2.79/+5.27 — 100 % retention, identical to ERCOT-118 to the cent |
| **(b)** C3c within ±5 h of keeper EVERY year | **FAIL**: 72→49 (2023), 13→3 (2024), 1→1 (2025) — the IDENTICAL drain ERCOT-118 produced with the peak rebased |
| **(c)** C1 16/16 · free 12/12 | **PASS** (calibration_verdict D-10) |
| **(d)** G1/G2 | **PASS**: excess −10.90/−6.24/−6.45 pp; spread −0.199/−0.250/−0.076 |

Registered expectations: **P1 CONFIRMED** (mid-merit ΔC3a legs −3.10/−6.63/−4.31 pp, all
TOWARD actual, matching ERCOT-118's −3.1/−6.6/−4.3); **P2 REFUTED** — the tail legs did NOT
shrink (−7.03/−6.16/−2.92 pp vs ERCOT-118's −6.9/−6.2/−2.9): restoring the peak wall removed
essentially none of the tail-band price reduction; **P3 CONFIRMED** (2023/24 elevation stays
+3.34/+2.79, the committed-band residual as declared). G3 fails via C3a AND C3c → **not** the
pre-declared escalate-to-owner mode → **ordinary rejection** as fixed ex ante. Rubric:
C2/C4/C5a/C7/C8 PASS, C3a/C3b/C3c FAIL (C3a is the keeper's ledgered exposure, deepened as
designed), C6 UNATTESTED (owner lane, like-for-like with the keeper).

## 4. What ERCOT-119 establishes

1. **The ERCOT-118 §4.2 peak-leg attribution is REFUTED by the controlled single-delta
   experiment.** With the pooled standing wall fully restored (peak 4.576 vs the rebased
   2.796, its ladder rungs and window anchor intact — ~$60/MWh of offer-wall level), the arm
   reproduces ERCOT-118 almost byte-for-byte: crossing elevations equal to the cent
   (+3.34/+2.79/+5.27 vs +3.34/+2.79/+5.28), C3a legs within 0.13 pp, **C3c identical to the
   hour** (49/3/1 in both). The whole peak-leg footprint is mean |Δprice| $0.07/$0.02/$0.04
   per hour (max $13.4, mostly re-shuffled mid-hours). The per-year peak p50 deflation did
   not own the C3c breach — the peak band is nearly inert in this configuration.
2. **The econ legs own BOTH the mid-merit gain and the tail drain — they are one mechanism,
   not two separable legs.** The measured per-year CC econ repricing produces the −$1.8/−$2.2
   crossing-band improvement AND the 23/10-hour C3c loss together. The D-2 bridge attribution
   shows the dispatch channel: the gas commitment bridge's binding forced energy collapses
   identically in both arms (keeper 0.77/1.41/0.97 TWh → 0.20/0.46/0.30) — the cheaper econ
   bands put the CC fleet in merit through hours the keeper had to force, shifting the
   supply surface under the near-tail hours; the model's sub-$200-adjacent price formation
   sits on the CC econ/markup surface, so repricing it drains the ≥$200 count.
3. **The frontier moves back to scarcity formation, away from offer measurement.** The real
   market's 2023/24 tail did not soften when its own (measured, cheap) CC offers stood —
   because the real tail is made by ORDC/reserve scarcity, not by the CC energy-offer level.
   A model whose ≥$200 count responds this strongly to a measured mid-merit repricing is
   telling us its near-tail hours are priced on the offer surface where the real market's
   are priced on scarcity machinery (the ERCOT-94/99 ledgered frontier). Consequence: no
   offer-band leg-split can clear C3c while keeping the measured econ fix — the C3c residual
   is owned by scarcity formation, and the rebasis lane is CLOSED as a C3c fix.
4. **Phase 2 (per-year peak quantile ladders) loses its motivation** and is de-prioritized:
   the controlled experiment shows the peak band's level barely reaches the tail at all, so
   re-expressing its dispersion cannot recover the drained hours.
5. **The band-scope mechanism is keeper-grade plumbing and stays, default-off.**
   Byte-identical for every existing config (test-pinned, default cache key unmoved); the
   artifact untouched (rule 23 — no source change); the pooled artifacts stay frozen.

## 5. Successor lanes (in priority order)

1. **ERCOT-120 — tail-hour mechanism decomposition (diagnostic, committed sidecars only, no
   solve):** for the 23 lost 2023 hours and 10 lost 2024 hours, identify from the keeper and
   arm `hourly/` sidecars what prices each hour in each bundle (marginal class, ORDC/co-opt
   adder share, energy dual level) — the concrete question this finding poses: which
   mechanism SHOULD be carrying those hours to ≥$200 when the mid-merit surface is measured
   and cheap. Its answer routes the scarcity-formation lane (ORDC/co-opt reach at high net
   load, ERCOT-94/99), not another offer probe.
2. **The committed-band data decision (owner, unchanged):** credentialed archive vs partial
   2024/25 Min-Gen-Cost intake vs accept the residual ~+$2.8–3.3 (2023/24) — P3 confirmed
   the residual stands.
3. **The measured coal envelope re-arming** remains gated on a shape-clean arm (its own
   gates G1/G2/BITE passed again here — third consecutive confirmation the envelope leg is
   healthy; what fails is the econ-leg tail interaction).

## 6. Declared-not-counted, honoured

No price-MAE argument in either direction; the C3a deepening was the designed exposure (P1)
and is not evidence against the rebasis direction; the C3c breach is reported as coded with
no post-hoc gate edit and adjudicated by the pre-commit's fixed rule (ordinary rejection); no
keeper change is recommended (the owner's conditional promote-if-candidate instruction is
answered NO by the pre-declared rule); the measured coal envelope stays default-off; the
holdout years were not touched (span exactly {2023, 2024, 2025}). Dashboard registration:
`2026-07-27-ercot119-econ-rebasis-joint` (NOT-YET), one auto-prune as expected
(`2026-07-24-ercot105-keeper-recovered-2023`, beyond top-15 ERCOT retention).
