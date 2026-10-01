# DIAGNOSIS — ERCOT-135 Phase 1: the coal-vs-gas merit bias is a curve-SHAPE defect, sized at 3.2–4.2 GW. The model offers 61–69 % of its coal capacity below the price the real fleet actually submits, and only 37–39 pp of that is min-load

**Date** 2026-07-28 · **ISO** ERCOT · **Lane** ercot135-coal-merit-order ·
**Keeper** `2026-07-28-ercot116-regate-base` (bundle
`results/calibration/ercot116_regate_base`) — **unchanged by this document** ·
**Method** Phase 1 — **no LP, no solve, no registered run.** Every model-side
number is captured at the exact seam the LP consumes it; every measured number
is read on an already-accepted convention. Default
`ScenarioConfig().cache_key()` verified `603c2498bf71d21d` at session start
(after the §7 repair) and end. ·
**Reproduction** `scripts/probes/ercot135_coal_merit_order.py` (committed with
this document); artifact `results/calibration/ercot135_coal_merit_order.json`.

This is the successor lane `DIAGNOSIS-ercot134` §10 chartered: **the coal-vs-gas
merit-order lane on the un-pinned fleet.** ERCOT-134 established the target —
on the un-pinned fleet coal runs **+6 to +18 pp hotter than the real fleet at
matched RT price in EVERY band of EVERY year** (G1 1/21), over-running
+6.5/+9.6/+11.4 TWh, displaced ~1:1 from gas. This document measures *why*,
and sizes it.

---

## 0. The result in one line

The model's coal supply curve is **bimodal** — ~30 % of capacity at
**$4.50/MWh**, the rest at $19–30 — while the real ERCOT coal fleet's
**submitted** DAM curve is a nearly **flat step at ~$20.5/MWh**. Netting off
the part of the cheap block that min-load legitimately explains leaves
**3,255 / 4,163 / 3,171 MW** (23.3 / 29.8 / 22.7 pp of coal capacity) offered
below the measured price with **no min-load justification**. That block clears
ahead of gas in every hour priced above its bid — which is every band — and
that is the band-uniform signature ERCOT-134 measured.

## 1. The model's coal supply curve vs the real fleet's submitted curve

Model side captured at the LP seam (after `apply_coal_tranches` applies the
take-or-pay discount — the last thing that touches a coal bid). Measured side
is the 60-Day DAM disclosure, `Resource Type == CLLIG`, the submitted
incremental energy curve, capacity(HSL)-weighted.

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| model bid p10 / p25 | **4.50 / 4.50** | **4.50 / 4.50** | **4.50 / 4.50** |
| model bid p50 | 21.55 | 19.26 | 22.20 |
| model bid p90 | 28.88 | 25.15 | 29.50 |
| model bid top | 52.24 | 48.65 | 56.09 |
| model cap-wtd **mean** | 18.78 | 16.88 | 19.42 |
| **measured DAM top offer (cap-wtd p50)** | **20.46** | **20.49** | **21.50** |
| measured submit share | 0.391 | 0.387 | 0.278 |

Two facts, both stable across all three years:

**(a) The real submitted curve is FLAT.** At most plants the bottom and top of
the submitted curve are the *same price* — Martin Lake 19.58/19.58 (2023),
21.51/21.51 (2024); Coleto Creek 21.29/21.29, 19.69/19.69. The real fleet
submits essentially one block at one price. Only Fayette and J K Spruce
submit a genuinely rising curve.

**(b) The model's curve is steep, and cheap where it matters.** Its bottom two
quartiles sit at **$4.50/MWh** — the tranche-1 take-or-pay band bidding VOM-only
(`coal_tranche_1_fuel_passthrough = 0.00`). No real ERCOT coal resource submits
at that price in any year of the corpus.

**This reconciles ERCOT-112 §6 and localises it.** That finding's "$28 model vs
~$21 real" is reproduced here from the code rather than quoted — on the
well-observed plants (submit ≥ 0.5) the model's **top** is $7–18/MWh above the
measured top in every year (2023 Martin Lake +12.88, Coleto +12.51, Fayette
+14.44, J K Spruce +14.87; 2025 Fayette +18.47, J K Spruce +18.11). But the
model's **mean** is *below* the measured offer. The curve is not shifted — it is
**too wide in both directions**, and it is the cheap end that sets dispatch.

## 2. Why the level lever was inert, and why band-local levers are refuted

Both prior refutations follow directly from §1 and need no re-testing:

* **ERCOT-132 leg B (LEVEL, CLOSED).** Moving 6.4 GW of coal offer level changed
  coal energy by ≤ 0.19 TWh on a ~60 TWh class. A translation of a curve whose
  bottom two quartiles sit at $4.50 does not change what clears first — the
  cheap block is still cheapest.
* **ERCOT-134 (band-uniform, G1 1/21).** A block priced below *every* band's
  clearing price over-runs in *every* band. The uniformity is not evidence of a
  mysterious fleet-wide mispricing; it is the arithmetic signature of a cheap
  block sitting under the whole price distribution.

## 3. The F923 delivered-fuel lead is CLOSED as a price question

ERCOT-112 §6 named this "an F923 delivered-fuel-price question, its own charter
with receipts". The receipts are largely **not there**:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| plants with an EIA-923 coal cost receipt | **3 / 10** | 3 / 10 | 3 / 10 |
| share of ERCOT coal **MW** with a receipt | **25.7 %** | 25.7 % | 25.7 % |

Only **Fayette, San Miguel and J K Spruce** report a delivered coal cost, in
every year 2018–2026 — the other seven plants (Limestone, W A Parish, Martin
Lake, Coleto Creek, Oak Grove, Major Oak, Sandy Creek) have **zero** rows in the
EIA-923 fuel-cost extract for any year. This is not an extract artifact; it is
ERCOT's merchant structure. The codebase already knew it —
`data/fuel/coal.py:73` states *"the merchant fleet's receipts are
confidential"* — and this section quantifies it.

**Where a receipt exists, the model already uses it, essentially exactly**
(`coal_plant_monthly_pricing=True`): 2023 deltas Fayette **+0.001**, J K Spruce
**+0.009**, San Miguel **−0.036** $/MMBtu. The remaining 74.3 % of coal MW price
off the coal-supply trajectories (2023 fallback levels $1.450 and $1.823/MMBtu;
2025 $1.450 and $1.614), with the PRB monthly shape itself derived from the two
reporters as a measured proxy.

**Consequence:** the A-vs-B gap in §1 **cannot** be a delivered-fuel-price
error, because the fuel price is either the plant's own receipt or a measured
proxy for a plant that publishes none. The defect is in the **offer
construction** — heat rate × passthrough × tranche geometry — not the fuel
price. There is no receipts-based correction available to buy, and chasing one
would be inventing a price for fuel whose cost is not published (rule 13
`[R-MEASURED]`). **This lead is closed; do not re-open it as a price question.**

## 4. The take-or-pay / committed share (ERCOT-127 §E convention, verbatim)

Measured on the 60-Day DAM CLLIG corpus, committed = `HSL > 0`, reproducing the
ERCOT-62 derive's construction (imported from the ERCOT-127 probe, not
re-implemented):

| | 2023 | 2024 | 2025 | pooled |
|---|---|---|---|---|
| cap-wtd p50 `LSL/HSL` | 0.3500 | 0.3729 | 0.3705 | 0.3636 |
| fleet aggregate `ΣLSL/ΣHSL` | 0.3742 | 0.3926 | 0.3856 | 0.3844 |
| **model `coal_tranche_1_frac`** | **0.30** | 0.30 | 0.30 | 0.30 |

The model's cheap band is **smaller** than the measured min-load share, not
bigger. **That matters for what this diagnosis does NOT claim:** the *existence*
and *size* of a price-independent coal block is measured-consistent with the
model's. The defect is not that the model has a cheap block — it is **where that
block is priced** ($4.50 vs a submitted ~$20.5) and how much *additional*
capacity sits under the measured price.

## 5. Sizing the bias (the number this lane contributes)

Netting the min-load-justified share off the cheap share:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| model coal MW offered below the measured DAM price | 60.7 % | 69.1 % | 61.3 % |
| measured min-load share (`ΣLSL/ΣHSL`) | 37.4 % | 39.3 % | 38.6 % |
| **excess cheap, no min-load justification** | **23.3 pp** | **29.8 pp** | **22.7 pp** |
| **= MW** | **3,255** | **4,163** | **3,171** |

Cross-check against ERCOT-134's over-run (+6.5/+9.6/+11.4 TWh): 3.2–4.2 GW
running some 1,900–2,900 extra hours reproduces that energy, and 2024 — the
largest excess (4,163 MW) — is also the year with the largest per-band G1
over-loading. The sizing is consistent with the target it was built to explain.

**This is a sizing statistic, not a mechanism** (§6).

## 6. What this licenses — and what it explicitly does NOT

**Licensed:** the defect is now *located* (offer construction, not fuel price,
not level, not availability) and *sized* (3.2–4.2 GW). The successor is a
**curve-SHAPE** question — the width of the model's coal offer curve against a
measured-flat submitted curve — which is a different object from the LEVEL
lever ERCOT-132 leg B refuted and from the availability envelope ERCOT-126
closed.

**NOT licensed, and this is the constraint on any successor:** §1's measured
curve covers only the **27.8–39.1 %** of committed coal resource-hours that
submit any curve at all. `DIAGNOSIS-ercot122` §4 measured the same thing from
the headroom side (coal exposes 0.161–0.184 of online headroom to DAM merit vs
CC's 0.594–0.677; the model offers ~100 %) and its caution is unchanged and
binding: **the unoffered ~60–72 % may be withheld, self-scheduled (price-taking)
or telemetered down, and those imply opposite corrections.** If it is
self-scheduled, a price-taking block is exactly what a $4.50 bid represents and
the model's cheap band is structurally right. Choosing a price for that block
without the evidence would be a fitted wall (rule 13 `[R-MEASURED]`) and a
second mechanism stacked on one phenomenon (rule 19 `[R-ONE-MECH]`).

**Therefore this session builds no mechanism and recommends no keeper.** The
instrument that can settle it is unchanged from `DIAGNOSIS-ercot122` §5.4 and
`FINDING-ercot132-legB` §7: the **SCED TPO instrument** (`FINDING-ercot117` §E)
— measure what the unoffered block does in real time, *then* design. ERCOT-135
adds one constraint to that successor and one asset: the defect is **shape, not
level or price**, and it is **3.2–4.2 GW**, so any candidate mechanism has a
pre-registered magnitude to hit.

## 7. Incidental repairs and findings

1. **Cache-key regression fixed (blocking).** `ScenarioConfig().cache_key()` had
   moved `603c2498bf71d21d → 25aa0d236dd6a574`: pjm-136 (PR #3093) landed
   `pjm_zonal_loss_surface` without registering it in
   `_CACHE_KEY_OPTIONAL_FIELDS`, so it entered the hash at its default and
   orphaned every on-disk cache, against its own declaration's promise
   ("byte-identical off"). Registered (commit on this branch); key restored,
   armed runs still hash distinct, pinned tests 40/40. **Fifth instance** of
   this exact one-line remedy already documented in that registry.
2. **The plant-grain water-fill saturates at model `pmax` (ERCOT-134 §2
   prediction-4 partial, now decomposed).** Under the measured envelope each
   plant's landing relative to its own COP declaration equals its
   `pmax`/declared-max ratio, to three decimals, at every plant:

   | plant | ARM/declared | pmax/declared-max |
   |---|---|---|
   | **Martin Lake** | **1.451** | **1.451** |
   | J K Spruce | 1.128 | 1.128 |
   | Major Oak | 1.126 | 1.127 |
   | Limestone | 1.096 | 1.096 |
   | Oak Grove | 1.050 | 1.050 |
   | Sandy Creek | 1.003 | 1.003 |
   | Coleto Creek | 0.950 | 0.950 |

   So the redistribution pins the class-hour mean and water-fills each plant up
   to its **model** `pmax`, tracking the declaration's *shape* but not its
   *level*. Martin Lake's 1.45 is therefore not a redistribution bug in
   general — it is that its model `pmax` (2,380 MW) stands ~45 % above its own
   declared maximum, because unit 1 was destroyed and is carried by the
   retained `BIN_FORCED_DERATE_BY_YEAR` `N_COAL4 {2025: 0.67}` entry
   (2,380 × 0.67 ≈ 1,595 ≈ the declared max). **The water-fill can lift a plant
   back above a forced derate that models a physically destroyed unit.**
   Recorded for the ERCOT-116 adoption decision — it is a reason the ARM's
   envelope is not simply adoptable as-is — and NOT acted on here (rule 19).

## 8. Owner decision — surfaced, NOT decided (the entry gate)

**ERCOT-116 adoption remains un-ruled**, and this lane's charter makes it
blocking: the successor's gate requires the ERCOT-116 metrics scored with the
**measured envelope ARMED** (rule 14 `[R-ACCURATE]` — the compensator must not
be re-tuned around the estimate). With no ruling, no solve was run and no arm
was built; Phase 1 is complete and stops here by design.

The pre-registered Phase 2 A/B — written **before** any solve, per the charter —
is `docs/PRECOMMIT-ercot135-coal-offer-width-2026-07-28.md`. §7 item 2 above is
new input to the adoption decision.

## 9. Scope, closed items honoured

No LP was solved and no run was registered; no `ScenarioConfig` field was added
or changed (the §7.1 repair is a cache-key registration, not a mechanism); no
keeper file was touched; holdout years (2022 / 2019 / ≤2021 / H1-2026)
untouched, span exactly {2023, 2024, 2025} and the probe hard-fails any other
`--year` (rule 22 `[R-HOLDOUT]`). Every CLOSED lane stays closed: coal offer
LEVEL (ercot132 leg B), pooled `econ_high` 2.856 (ercot122 §5.2), coal ramp
trajectory (ercot127 §1 / ercot132 leg A), the availability ENVELOPE layer
(ercot126 §§2–3), min-config upper bound / cap-off (ercot130), plant-grain
fractional min-load floor (ercot127 §3), unit-grain commitment STATE
(ercot128), availability-SCALED floor (ercot128 P3–P4), age/temp derates
(ercot121 §1a), the EP-rebasis C3c lane (ercot119), `ercot_zonal_gas_basis`,
and the West/Panhandle topology split. **§3 CLOSES the F923 delivered-coal-price
lead** as a price question.

**Process note, on the record:** the first capture attempt patched
`market_sim.runner.apply_coal_tranches`, which is a dead copy — the live call is
the one imported into `scripts.run_calibration` (the identical trap
`ercot130_capoff_phase1` records for the fleet-array constructor). That replay
therefore solved 2025 in full instead of aborting at the seam. It was a training
year, the output was scratch, it was deleted unregistered, and the probe now
patches the live copy and documents the trap.

## 10. Environment parity

Fresh container, ercot115–134 baseline matched: no gtc-limits clean partition
("static TTC kept"), `hydro-plant-modes` WARNING, benign
`ercot_wtx_curtailment_driver` prb-stomp WARNING, no confirmed-retirements
partition. `ScenarioConfig().cache_key()` `603c2498bf71d21d` at session start
(post-§7.1) and end.
