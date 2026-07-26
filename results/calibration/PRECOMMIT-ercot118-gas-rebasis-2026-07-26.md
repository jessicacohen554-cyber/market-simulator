# PRE-COMMIT — ERCOT-118: re-ground the ERCOT CC gas offer band multipliers on the EP dispatch basis (Phase A, joint arm)

**Date** 2026-07-26 · **ISO** ERCOT · **Branch** `claude/ercot-118-gas-offer-rebasis-ymxdan` ·
**Base** the keeper `results/calibration/ercot115_coal_floor_only`
(`2026-07-26-ercot115-coal-marginal-hr`) · **Slug** `ercot118-gas-rebasis` ·
**Written and pushed BEFORE any ERCOT-118 solve**, with the mechanism commit, the committed
per-year artifact `data/raw/_validation-source/offer_curve_dam_hrmults_ep_yearly.json`, and the
scorer `scripts/probes/ercot118_gas_rebasis_score.py`.

## 1. What this arm changes (Phase A — the measured fix, single mechanism delta)

ERCOT-117 proved causally (P1/P4 confirmed, run `2026-07-26-ercot117-gas-basis-probe`) that the
keeper's mid-merit +$5.0/+$5.2/+$7.0 crossing-band elevation is owned by the derivation⇄dispatch
gas-basis inconsistency of the measured CC DAM band multipliers: derived at **HH_daily − 0.50
pooled 2023-25**, repriced at the **EP-anchored zonal level** (+0.50/+0.41/+0.04 $/MMBtu above
that basis; verified this session: `ercot_electric_power_gas_basis` = +0.0045/−0.0858/−0.4634 vs
HH). Per rules 13/14 the fix keeps the EP level and re-derives the multipliers on it.

The new mechanism (`ScenarioConfig.ercot_offer_hrmult_ep_rebasis`, default-off, ERCOT-scoped,
cache-key-registered, tri-state solve kwarg + None CLI default — both ercot-115 seam lessons)
replaces the keeper's CC_REGULAR/CC_CHP override bands with the committed PER-YEAR EP-basis
artifact and re-applies the keeper's `offer_curve_deltas` **unchanged** on the rebased base
(composition preserved; attribution requires the rebasis to be the only offer delta). The
conditional-surface peak_ladder rungs are re-stamped at the rebased peak; the walls
(midcurve/cleared-share/conditional/lowcurve) and the phys_* keys are untouched (in-scope family
only — they are internally consistent HH−0.50 pairs).

Measured per-year values (raw-direct derive, 9,260,346 CC curve points, delivery
2023-01-01→2025-12-31; peak mode B, the cconly lineage):

| year | econ_low | econ_high | peak(B) | anchor ($/MMBtu, EP delivered mean) |
|---|---|---|---|---|
| 2023 | 0.812 | 1.235 | 2.546 | 2.5402 |
| 2024 | 0.792 | 1.265 | 3.501 | 2.1067 |
| 2025 | 0.850 | 1.332 | 2.629 | 3.0655 |

(Keeper pooled registered: econ_low 0.963 / econ_high 1.454 / peak 4.326 at HH−0.50.) Implied
resolved econ_high repricing at year-mean fuel under the armed margin mechanism:
**−$3.5/−$3.5/−$0.5 per MWh** (2023/24/25, CC base HR) — matching the ablation's proven
crossing-band drops on the two basis-gap years, with 2025 carried mostly by the pooling leg.

## 2. The COMMITTED band — declared limitation, ex ante

The committed (Min-Gen-Cost) band **cannot be re-derived per-year on any basis in this
session**, and is therefore **absent from the artifact — it keeps the keeper's resolved value**
(CC_REGULAR 0.998, CC_CHP 1.029):

1. The owner-ordered 2026-07-22 raw slimming (`slim_ercot_dam_disclosure.py`) dropped
   `Min Gen Cost` / `Start Up *` from every raw disclosure parquet (re-fetch instruction noted
   in that script's registry).
2. The parsed intermediate `ercot_dam_offers.parquet` was never committed and is not
   rebuildable from the slimmed raws (`parse_ercot_dam_offers.py` hard-requires the dropped
   columns).
3. The free MIS path retains only ~2.3 years of publications — **all 2023 deliveries are
   permanently unreachable**, and the credentialed data.ercot.com archive was owner-declined
   (`docs/handoffs/ercot-as-coopt-plan-2026-07.md` §WS-E).

Consequence, stated before solving: the CC committed (LSL-block) tranche keeps pricing
~+$2.6–4.0 above its measured level in 2023/24 in the hours it prices (its markup leg is inert
either way — resolved 0.998 < phys 1.006 clips to 0), so part of the ERCOT-117 §A ≤$15
committed-supply displacement (measured 12.5–15.1 GW vs model 1.8–4.6 GW) **will remain**. Any
committed-band rebasis is an owner decision: re-authorize the credentialed archive, or accept a
2024/25-only partial intake. This is a declared possible cause of a partial primary-yardstick
result, **not** grounds to tune anything else around it (rule 14).

Reconstruction transparency: the identical band construction run at pooled HH−0.50 on TODAY's
raw corpus gives CC_REGULAR 0.956/1.412/4.313 vs the frozen artifact's 0.963/1.454/4.326 —
corpus growth since the 2026-07-22/23 derivation (~−0.7 % to −2.9 %), small against the ~+25 %
basis effect. The pooled artifacts stay frozen (rule 23); the per-year artifact is derived from
the committed raw corpus of record.

## 3. The margin-anchor audit (charter mandate)

`GAS_OFFER_MARGIN_ANCHOR_BY_ISO["ERCOT"] = 2.2494` is **verified computed on the HH−0.50
series**: it is the 2023–25 mean of the model's own delivered annual means
(2.0394/1.6895/3.0192 = HH annual − 0.50 to the cent; `derive_gas_offer_margin_anchor.py`, the
ercot99-overlay series). The keeper's markup decomposition was therefore internally consistent
in its markup leg (pooled HH−0.50 mult − phys, priced at the HH−0.50 window mean); the
inconsistency the rebasis fixes enters through the phys×EP-fuel leg and the mult level.

Under the rebasis, each per-year multiplier is identified at that year's own EP delivered mean,
so the artifact's `anchor_usd_mmbtu` (2.5402/2.1067/3.0655) is threaded onto the REBASED
classes as a per-class `margin_anchor` (per-tranche override inside `apply_gas_offer_margin`,
bit-identical when absent): **every rebased band's (mult, anchor) pair sits on the EP series;
every untouched band keeps its original identification pair** (CT_PEAKER/ST_GAS/CT_CHP mults
are calibrated values, not members of the measured band family — moving their anchor would be
an out-of-scope second delta, rule 25/attribution). One declared residual mismatch remains: the
untouched committed band (HH−0.50-derived mult × EP fuel), covered by §2.

## 4. The arm (single solve, three years, one invocation — R-ALLYEARS)

`replay_keeper` on the ercot115 keeper with exactly two deltas (the ERCOT-116 joint-arm gate
protocol — the measured coal envelope is ARMED, never re-tuned around):

- `ercot_thermal_dam_availability_coal=true` — the measured coal DAM envelope.
- `ercot_offer_hrmult_ep_rebasis=true` — Phase A, this charter.

Out dir `results/calibration/ercot118_ep_rebasis_joint`; years 2023 2024 2025, sequential in
the one invocation (rule 12). Keeper `offer_curve_deltas` and every other keeper flag
unchanged.

**G0 (armed and biting), checked before scoring:** solve log carries `coal econ marginal-HR
floor` 3/3, `COAL plant-grain redistribution` 3/3, `ERCOT DAM offer hr-mult EP rebasis` 3/3
(the new mechanism's own line — a silently-inert mechanism voids the arm, the ercot112 trap),
and the margin line's `tranches on per-class EP anchors` suffix; `run_config.json` records
`ercot_offer_hrmult_ep_rebasis: true` with the rebased `offer_curve_by_group`.

**Environment parity:** fresh container; the gtc-limits clean partition is absent so the solver
falls back to `static TTC kept` — the SAME fallback state the ercot115 keeper, the ercot116
envelope arm and the ercot117 probe were solved under (like-for-like); highspy pinned 1.14.0
per the family setup. Comparisons to all three baselines are therefore state-matched.

## 5. Scoring — fixed before the solve

1. `scripts/probes/ercot116_seasonal_shape.py` **VERBATIM** (keeper =
   `ercot115_coal_floor_only`, arm = this bundle) — G1/G2/G3/BITE as coded.
2. The same metrics vs `ercot116_coal_avail_on_keeper` AND vs `ercot117_gas_basis_probe`
   (both on disk — no extra solves) to isolate the rebasis's own contribution under the
   identical envelope and against the full-surface ablation.
3. `scripts/probes/ercot118_gas_rebasis_score.py` (committed with this doc; validated by
   reproducing the ercot117 published crossing drops −$3.46/−$3.39/−$2.03 from the on-disk
   bundles): the PRIMARY yardstick and the G3-trap decomposition.

**PRIMARY YARDSTICK (pre-registered, the charter's):** the probe-§F crossing-band elevation —
model-minus-actual in actual-$[15,25) hours falls to **≤ $2.0 in EVERY year** (keeper:
+5.18/+5.03/+7.00), with **C3c within ±5 h of the keeper** in every year and **C1 not
degraded** (16/16 · free 12/12).

**THE G3 TRAP, adjudicated in advance:** G3 is run exactly as coded and reported. If it fails
**solely** via C3a moving toward actual in the $10–40 bands — the
`ercot118_gas_rebasis_score.py` decomposition splits each year's ΔC3a into the actual-$[10,40)
mid-merit leg vs the tail leg, and prints whether the band moved TOWARD actual — that outcome
is **pre-declared ESCALATE-TO-OWNER** with the decomposition: not a revert signal, not grounds
to edit the gate, not self-promotion. **Any other G3 failure mode** (C3c breach, or a C3a move
away from actual, or a tail-carried delta) **is an ordinary rejection.**

## 6. Registered predictions (falsifiable, written before any year solved)

- **P1.** 2023 AND 2024 [15,25) elevation falls to ≤ $2.0 (from +5.18/+5.03) — the basis-gap
  years, where the rebased econ_high repricing (−$3.5) matches the ablation's proven drop.
- **P2.** 2025 improves by ≥ $1.0 but the ≤ $2.0 line is **at risk** (the un-rebased committed
  band, §2, plus the 2025 residual being pooling-carried; the full-surface ablation itself only
  reached +4.97). A 2025 miss with 2023/24 clearing means the charter's success criterion is
  not met in full: outcome NOT-YET, residual owners named (committed-band data gap; Phase B).
- **P3.** G3-as-coded fails via C3a in the pre-declared mode (mid-merit leg toward actual),
  with magnitude well inside the ablation's (−14/−17/−9 pp there; only the CC bands move here).
- **P4.** C3c stays within ±5 h of the keeper every year (unlike the ablation's 72→48: the
  ≥$200 set is ORDC/co-opt-owned and the walls are untouched; the CC peak rebasis moves
  sub-$200 loose-hour rungs).
- **P5.** BITE — coal moves > 0.5 TWh vs the keeper in at least one year.
- **P6.** G1/G2 (the envelope shape gates) PASS all years, ≥ the ercot116 envelope arm's own
  effect (−5.7/−7.2 pp excess drops).

## 7. Decision rule (fixed now)

- All gates pass, or G3 fails **only** in the pre-declared C3a-toward-actual mode → write the
  FINDING, **recommend re-arming the measured coal envelope** (the ERCOT-116 exit criterion)
  and **STOP for owner sign-off**. `frontend/data/backcast/keepers/ERCOT.json` is never touched
  without that sign-off (the ercot-115 process-breach lesson).
- The primary yardstick misses on a leg attributed ex ante (§2 committed band / P2's 2025
  pooling residual) with P1 confirmed → NOT-YET finding; the committed-band data decision and
  Phase B (delta re-fit on the re-grounded base, its own pre-commit and solve budget) are the
  named successors. **No delta re-fit happens in this session without its own pre-commit**
  (Phase B is not entered on top of this arm's result sheet).
- Any other failure mode → ordinary rejection, finding records it, keeper unchanged.
- Register the completed solve on the dashboard the same session whatever the outcome
  (rule 15), slim-bundle per the ercot116/117 precedent.

## 8. Declared-not-counted

No price-MAE argument in either direction; the ercot116/117 §F keeper elevations quoted here
(+5.18/+5.03/+7.00) supersede the finding texts' rounded +$4.4–7.0 (same construction, exact
values from the committed sidecars); the pooled HH−0.50 artifacts stay frozen as the record of
the old basis; the committed band is escalated, never patched around; the ercot-115 CLI seam
fix (`--coal-econ-marginal-hr-bound` default False→None in the hand-written parser, which was
silently scrubbing the promoted floor on direct CLI runs) rides this branch as an
infrastructure correction and touches no solve in this lane (replay_keeper bypasses the CLI).
