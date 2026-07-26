# PRE-COMMIT — ERCOT-117: the gas-basis causal probe on the coal-vs-gas mid-merit ranking bias

**Date** 2026-07-26 · **ISO** ERCOT · **Branch** `claude/ercot-117-coal-gas-bias-c7kekw` ·
**Base** the keeper `results/calibration/ercot115_coal_floor_only`
(`2026-07-26-ercot115-coal-marginal-hr`) · **Written and pushed BEFORE any ERCOT-117 solve**
(everything below rests on the no-LP measurements in
`scripts/probes/ercot117_coal_gas_ranking.py`, committed alongside this document).

## 1. What the no-LP measurements established (the probe script's A–F sections)

The ERCOT-116 charter asked which side of the $15–25 coal-vs-CC crossing is displaced.
Measured, before any mechanism:

1. **The model's coal supply curve is exonerated.** The real coal fleet's RT (SCED TPO)
   supply reaches 0.65–0.71 of telemetered HASL at ≤$20 and 0.91–0.92 at ≤$25, stable
   across 2024/2025 and across tail/control day families (probe §E; HASL ≈ 0.99 × HSL, so
   nothing is telemetered away). The model's coal supply sits at 0.66 of deliverable at
   ≤$20 and 0.91 at ≤$25 (2024, probe §B) — the same knee, the same top. The DAM
   disclosure's coal picture (committed supply saturating at ~5.4 GW, cleared share
   0.06–0.17 — probe §A and the cleared-share derive extended to CLLIG) reflects QSE
   self-supply bypassing DAM transaction, not withheld capability: the capability is
   offered in RT, at $20–25 for the bulk and $25–200 for the last ~8 %.
2. **The coal fuel-price basis is confirmed, not refuted** (the charter's named F923
   lead, probe §C): both F923-reporting PRB plants price within ±$0.06/MMBtu of the
   model's $1.75 reporter-proxy basis. San Miguel lignite measures $3.56 vs the model's
   $1.45, but it is 410 MW and its DAM offers sit at $19–20 — not the crossing's owner.
3. **The model's CC supply is displaced dear in the crossing band, every year** (probe
   §A vs §B): at ≤$15 the model carries 1.8 / 4.6 / 0.4 GW (2023/2024/2025 summer)
   against a measured committed DAM supply of 12.5 / 14.3 / 15.1 GW (offer curves floored
   at the committed LSL); the model's CC block arrives at $15–25 instead. In 2025 the
   model has essentially no CC supply below $17.5 (2.8 GW at ≤$17.5) while the real
   committed fleet stands at 16.1 GW there (14.2 GW price-taking LSL plus the offered
   ramp).
4. **The consequence is direct and visible in the keeper's own sidecars** (probe §F): in
   hours whose ACTUAL price is $15–25 (~3,000–3,700 h/yr — the mid-merit body), the
   keeper's load-weighted P1 price runs **+$4.4 (2023) / +$5.0 (2024) / +$7.0 (2025)
   above actual**, both seasons; in actual-$10–15 hours it runs +$7–11 high. In
   actual-$25–40 hours only +$1.3–3.3. The mid-merit clearing level is structurally
   elevated — so every correctly-priced coal tranche ≤$25 (0.91 of the envelope) clears
   in hours where reality cleared at $20 and dispatched 0.68 of coal. This is the
   season-invariant ranking bias of the ERCOT-116 signature: it expresses seasonally
   because summer holds the mid-merit hours.

## 2. The registered root-cause hypothesis

Every ERCOT gas offer-surface artifact (the DAM hr-mult overrides the keeper's
`offer_curve_overrides` come from, the mid-curve/cleared-share/conditional walls)
normalizes measured offers by **Henry Hub daily − 0.50** (`GAS_BASIS_DIFFERENTIAL`), while
the keeper prices dispatch gas at the **EP-anchored zonal level**
(`ercot_zonal_gas_basis`: HH + measured electric-power basis, **+0.50 / +0.41 / +0.04
$/MMBtu above the derivation basis in 2023 / 2024 / 2025**). A multiplier measured
against cheap gas, repriced on dear gas, reproduces the measured offer surface **+25 %
high in 2023/2024**. The 2025 leg of the displacement (basis gap ≈ 0) is carried by the
pooled-multiplier structure instead (the real fleet's offers scale sub-proportionally
with fuel: measured mid-curve s50 ≈ 6.8–7.1 HR-equiv in 2023/24 vs 5.4–6.1 in 2025) and
is **not** expected to respond to this probe — that asymmetry is the discriminator.

## 3. The arm (single solve, three years, one invocation)

`replay_keeper` on the ercot115 keeper with exactly two deltas:

- `ercot_thermal_dam_availability_coal=true` — the measured coal envelope ARMED, per the
  ERCOT-116 gate protocol (the compensator is never re-tuned around the estimate).
- `ercot_zonal_gas_basis=false` — the **diagnostic ablation**: delivered gas reverts to
  the flat HH−0.50 series every offer multiplier was derived against, restoring
  derivation⇄dispatch basis consistency for 2023/24 and changing ~nothing in 2025
  (EP−(HH−0.50) = +0.04). Side effects accepted and declared: the West/Panhandle
  two-regime shape (`ercot_west_netload_gas_shape`) soft-gates off with it, and the coal
  passthrough sigmoid re-keys to the cheaper series (passthrough −0.06 in 2023/24 ⇒ coal
  ~$1.1/MWh cheaper — this works AGAINST the predicted coal stand-down, so the measured
  effect is a conservative lower bound on the pure CC-side effect).

**This arm is a rule-13 diagnostic probe by construction, never a keeper candidate in any
outcome**: it disarms a measured input (the EP-anchored gas level) and rule 14 forbids
reverting measured data because a residual moved. If the probe confirms causality, the
forward fix is the opposite composition — **keep** the EP-anchored gas level and
**re-derive the offer surface on that same series** (the ERCOT-118 program, §6).

## 4. Scoring — fixed before the solve

`scripts/probes/ercot116_seasonal_shape.py` **verbatim** (the charter's fixed gate;
keeper = `ercot115_coal_floor_only`, arm = this bundle), plus the same metrics computed
arm-vs-`ercot116_coal_avail_on_keeper` (the envelope-armed probe already on disk) to
isolate the basis-flip's own contribution under an identical envelope — no extra solve.
G3's coded form (|ΔC3a| ≤ 2.0 pp, |ΔC3c| ≤ 5 h vs keeper, two-sided) is run as coded.

## 5. Registered predictions (falsifiable, written before any year solved)

- **P1 (the causal claim).** Matched-band excess vs the ercot116 envelope-armed arm falls
  by ≥ 4 pp in 2023 AND 2024 (10.04 → < 6.0, 12.87 → < 8.9); **2025 stays within ±1.5 pp
  of 13.38** (the null-control leg). If 2023/24 do not move, the basis attribution is
  refuted; if 2025 moves as much as 2023/24, the pooling attribution is refuted.
- **P2.** G1-as-coded (vs keeper, drop ≥ 5 pp every year) passes all three years — 2025
  via the envelope's own −7.2 pp shape effect (ERCOT-116), 2023/24 by more.
- **P3.** G3 **fails via C3a**: repricing the CC mid-curve down lowers the mid-merit
  clearing level, and the keeper's annual C3a nets a mid-merit-high error against a
  scarcity-low error, so removing the first exposes the second (2023 −16.6 pp goes more
  negative; 2024/25 +1.3/+1.5 go negative past −0.7/−0.5). The expected overall verdict
  is therefore **REJECTED PROBE** — rejection with P1 confirmed is the successful
  outcome (causality proven), not a failure of the lane.
- **P4.** The probe-§F crossing-band elevation (+$5.0 / +$4.4 / +$7.0 in $15–25) drops by
  ≥ $2.5 in 2023 and 2024 and by < $1 in 2025.
- **P5.** BITE passes (coal moves > 0.5 TWh vs keeper in at least one year).

## 6. Decision rule (fixed now)

**No keeper change in any branch; no promotion is possible from this probe.**

- P1 + P4 confirmed → write the FINDING; charter **ERCOT-118**: re-derive the ERCOT gas
  offer-surface artifacts (hr-mult overrides + walls) normalized on the SAME EP-anchored
  delivered-gas series the model dispatches on, with per-year tables replacing the pooled
  p50s (the 2025 leg), and re-fit the keeper's offer deltas on the re-grounded base —
  the full re-grounding program this probe's causality result justifies.
- P1 refuted → the basis attribution is dead; the displacement lives in the pooled
  multiplier / margin structure alone; charter the re-derivation without the basis claim.
- Mixed → report per-leg against the predictions above; no post-hoc gate edits.

## 7. Verification lines (G0 — armed and biting, checked before scoring)

- `coal econ marginal-HR floor` — expect 3/3 years (keeper mechanism intact).
- `COAL plant-grain redistribution` — expect 3/3 years (envelope armed).
- `ERCOT zonal gas basis` log line **ABSENT** all years (ablation armed) and
  `run_config.json` records `ercot_zonal_gas_basis: false`.
- Registration: dashboard-registered as a **probe** (rule 15), honouring top-15 pruning.
