# FINDING — NYISO C3a 2023 off-peak trough: the ISO-neutral gas commitment bridge (ERCOT-63) is NEAR-INERT here; the "only forward lever" is BUILT, TESTED, and does not close it (2026-07-24)

**Status: DIAGNOSTIC ONLY. Keeper stays `nyiso-72`
(`2026-07-23-nyiso-72-netrev-margin`, NOT-YET); no keeper change, no
registration, no residual tuning (rule 1).** This session picked up the
`claude/nyiso-backcast-c3a-2023` handoff — close the dominant open miss, the
2023 C3a OFF-PEAK trough (+53–59%, the model floors overnight LBMP at ~$31 where
the real market troughs to ~$19.6) — and resolves the one open question the two
prior 2026-07-23 findings left: they named a **below-SRMC overnight commitment
mechanism** as the sole structurally-honest forward lever but framed it as an
**unbuilt cross-ISO price-formation methodology change**. That mechanism EXISTS
(`ercot_gas_commitment_bridge`, ERCOT-63, ISO-neutral internals). This session
routed it onto NYISO and measured it: **it fires but is near-inert on the C3a
trough, and marginally compresses the daily spread** — the same refutation
signature ERCOT's price-side markdown showed. The lever is now empirically
closed for NYISO.

## 1. Independent verification of the miss on nyiso-72

Committed keeper hourlies (`nyiso72_netrev_margin/hourly/`) vs
`actual_lmp_hourly_NYISO.parquet`, load-weighted RT, shoulder (May/Jun/Aug):

| window | actual RT | keeper nyiso-72 | error |
|---|--:|--:|--:|
| **off-peak (hod 0–6)** | **19.62** | **31.12** | **+58.7%** |
| on-peak (hod 14–19) | 32.12 | 41.03 | +27.8% |
| full year | 30.28 | 36.78 | +21.4% |

The miss is OFF-PEAK-specific and wider on nyiso-72 than on nyiso-70 (the
net-revenue margin form made 2023 marginally worse, as logged). Off-peak
marginal = CC_REGULAR (gas_cc); evening marginal shifts to CT_PEAKER (17→650 MW)
+ hydro (1752→4124 MW). Structural note: because a flat input (gas basis, HR,
offer level, import price) shifts every hour ~symmetrically, **no hour-symmetric
input can produce an off-peak-SPECIFIC gap** — the +58.7%/+27.8% split is itself
evidence the driver is a commitment/price-formation effect (which manifests only
off-peak, when units would otherwise shut down), not a level input. This
sharpens the prior findings' refutation of the handoff's named levers
(gas-basis, CC offer surface, imports) from *empirical* to *structural*.

## 2. The lever the prior findings called "unbuilt" is built: ERCOT-63

The 2026-07-23 findings' recommendation was a below-SRMC overnight
commitment-bid mechanism, "a cross-ISO price-formation methodology change… not a
NYISO knob." The ERCOT trough campaign
(`docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md`) built exactly this:

* **The price-side form** (`ercot_offer_surface_lowcurve`, the measured LSL /
  below-SRMC bid) moves the trough LEVEL toward reality but is **REFUTED** — it
  reprices the committed tranche that is ALSO the evening marginal, so it
  compresses the daily spread the wrong way (rule 1: right number, wrong
  mechanism). The floor-scoped variant is provably inert.
* **The state-side form** (`ercot_gas_commitment_bridge`, ERCOT-63): the CAISO
  RA must-offer bridge internals (`caiso_ra_mustoffer_min_gen` — min-down +
  startup-restart economics detected from the model's OWN P0 run pattern,
  physics-gated per rule 18, forward-native) scoped to merchant gas-CC, with
  `min_load_frac` = the MEASURED committed-CC LSL/HSL p50. On ERCOT the STATE
  bridge closed the trough LEVEL (C3a +3.9% → +0.3%) and *deepened* the trough.
  The detector body (`_ercot_gas_bridge_floor`) is ISO-neutral; only the two
  wrapper gates pin ERCOT.

## 3. The probe: the ISO-neutral bridge on NYISO 2023

`scripts/probes/_nyiso73_gas_bridge_probe.py` (rule-16 throwaway, NEVER
registered): monkeypatches `build_ercot_gas_bridge_p1_preps` so the ISO-neutral
detector fires on NYISO gas-CC, keeper nyiso-72 recipe otherwise byte-faithful
(`build_kwargs(meta)`). `min_load_frac` = 0.574 (ERCOT-measured LSL/HSL p50, used
as a physical CC min-stable proxy — the floored VOLUME the detector finds is
~independent of the exact fraction, and the efficacy result below is
fraction-independent because the marginal price-setter is unchanged, §5).

**The bridge fires — NYISO CC does cycle off overnight.** 6,492 unit-hours
floored, **0.573 TWh** floor volume, 895 bridged gaps (221 <4h, 299 4–8h, 301
8–16h, 74 16–24h) — the overnight-between-run-days pattern, NOT a null. The
applicability premise (baseload CC never idles) is **disproved**: enough NYISO
CC cycles overnight to bridge a comparable volume to ERCOT's.

## 4. A/B result — near-inert on the trough, marginally spread-compressing

nyiso-72 keeper base vs the bridge arm, 2023, shoulder, load-weighted:

| metric | actual | base | bridge | Δ (bridge−base) |
|---|--:|--:|--:|--:|
| off-peak trough (hod 0–6) | 19.62 | 31.12 | 30.92 | **−0.20** |
| on-peak (hod 14–19) | 32.12 | 41.03 | 40.26 | −0.78 |
| full year | 30.28 | 36.78 | 36.34 | −0.44 |
| median daily spread | 26.39 | 8.72 | 8.08 | **−0.63 (worse)** |

C1 fuel-mix unchanged (CC_REGULAR +0.23 TWh, CC_CHP −0.11, ST_GAS −0.07, imports
0.00 annual — all PASS-band); C7 ST_GAS shape inert (ST_GAS Δ −0.07 TWh). **The
off-peak trough moves −0.20 $/MWh against an $11.5 gap — it is not closed
(+57.6% remains) — and the daily spread compresses −0.63 (away from reality's
26.39), the SAME signature that refuted ERCOT's price-side markdown.**

## 5. Why it is near-inert here but worked on ERCOT (the structural difference)

In the bridged shoulder off-peak hours the floor raises CC_REGULAR 3527→3642 MW
(+115) and **displaces imports** 2896→2754 MW (−142) — not a more-expensive
domestic unit. Imports are already repriced to neighbor DA LMPs sitting near the
CC band, so swapping ~140 MW of import for CC-at-LSL happens at essentially the
same price, and **the marginal domestic price-setter stays a mid-efficiency
CC_REGULAR at ~$29–31.** The trough LMP therefore holds.

This is the decisive contrast with ERCOT. On ERCOT the bridge's floored CC-at-LSL
displaced a *more-expensive* overnight marginal, so the trough deepened. On NYISO
the overnight marginal is ALREADY a CC and the bridged units ARE CCs, so flooring
them exposes nothing cheaper — the whole downstate CC fleet prices in the high
$20s and the efficient band is already ~90% utilized (the prior finding). **A
STATE mechanism (more units online at min-load) cannot fix a PRICE gap** (the
model's cheapest available marginal is genuinely dearer than reality's, whose
overnight marginal bids below SRMC). And the price-side (below-SRMC bid) that
*would* reach reality is cross-ISO REFUTED (spread compression), a signature this
NYISO probe reproduces even at the bridge's small magnitude. The near-inertness
is fraction-independent: 0.35 TWh of non-CC was displaced yet the marginal held,
so a larger `min_load_frac` only displaces more non-CC (toward oversupply), never
lowering the CC-band marginal.

## 6. Verdict & recommendation

- **Keeper unchanged: `nyiso-72` holds, NOT-YET.** The dominant miss (C3a 2023
  off-peak trough) is a **price-formation limit of the full-SRMC LP**, confirmed
  now on both sides: the STATE bridge (this session) is near-inert and mildly
  spread-compressing; the PRICE markdown is cross-ISO refuted. Every measured
  NYISO-contained input is grounded and every commitment-state lever is exhausted.
- **The lever the prior findings named is CLOSED, not merely "unbuilt."** The
  below-SRMC commitment mechanism exists (ERCOT-63) and, tested on NYISO, does
  not close C3a. The residual is an instance of the **cross-ISO overnight-trough
  price-formation frontier problem** (ERCOT's own trough is still open at
  frontier), whose only non-refuted-non-inert closer would be a below-SRMC
  *offer* form that lowers the marginal bid WITHOUT compressing the spread —
  unfound across ERCOT (markdown refuted, floor-scoped inert, bridge deepens) and
  now NYISO (bridge inert). This is a methodology-lane item, not a NYISO
  calibration task; anything validated there must be validated model-wide.
- **Do NOT** promote the bridge for NYISO (near-inert + spread-compressing;
  promoting it would be adding a real-but-unhelpful mechanism that mildly worsens
  the one price-shape target it touches — not keeper-justified), **do NOT**
  re-chase the handoff's named levers (gas-basis / CC offer surface / imports —
  structurally refuted §1), **do NOT** raise a floor or tune an offer to the
  residual (rules 11/23).
- The separate ST_GAS under-generation / C7 half remains a **data-intake
  blocker** (a published NYISO NYC Zone-J / Long-Island Zone-K minimum in-city
  generation requirement), per
  `FINDING-nyiso-stgas-underrun-diagnosis-2026-07-23.md` — unchanged.

## Reproduction

```
# committed keeper hourlies: results/calibration/nyiso72_netrev_margin/hourly/
python scripts/probes/_nyiso73_gas_bridge_probe.py nyiso73_gas_bridge_2023 --years 2023
# -> logs "[nyiso73-bridge] floored unit-hours 6492, floor volume 0.573 TWh"
# A/B vs the committed nyiso-72 base: off-peak trough Δ -0.20, spread Δ -0.63.
```
