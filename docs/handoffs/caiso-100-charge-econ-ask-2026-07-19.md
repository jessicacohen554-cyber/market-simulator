# OWNER-ASK (CAISO-100): arm the battery cycling-degradation cost for CAISO — `battery_dispatch_adder` 0.0 → the DERIVED $14.25/MWh (re-opens the caiso-76 no-change ruling on moved evidence)

**Status: PENDING owner ruling. No knob change, no new-mechanism solve, nothing
registered under this ask.** The CAISO-100 charter is derive-first +
owner-gated and its carrier carried no execution ruling, so this session
measured, pre-registered, and filed. Full evidence:
`results/calibration/FINDING-caiso100-charge-economics-2026-07-19.md`
(pre-registered bands + gates in its §6, binding on the build session).

## 1. What would change (one registered scalar, one B-leg)

`ScenarioConfig.battery_dispatch_adder` (existing registered knob; enters the
backcast battery objective as $/MWh discharged via `load_eia860_storage` →
`StorageUnit.vom`) goes 0.0 → **14.25** for the CAISO backcast recipe — the
DERIVED cycling-degradation cost
(`storage._degradation_cost_per_mwh` construction: NREL ATB 2024 capex
$285/kWh × 1000 ÷ 5,000 LFP warranty cycles × 0.25 replacement fraction,
`constants.py:4128-4136` — the identical formula the storage entry screen
already prices and ERCOT's cycling lane quoted). NOT a tuned value: no sweep,
no residual fit (rule 25); ERCOT's tuned $10 does not cross the ISO boundary
(rule 25) — CAISO takes the physics-derived number.

Single-delta A/B per FINDING §6: fresh same-machine `caiso100_repro_A`
(caiso-99 keeper recipe) vs + `battery_dispatch_adder=14.25`, 2023-2025 one
bundle (rule 16), sequential, registered whatever the result (rule 15),
promotion only on no-status-regression, prune CAISO retention to top-15 at
registration.

## 2. Why (the two-line case)

The caiso-99 keeper still over-prices the belly +7.7/+7.6/+6.3 because the
zero-cycling-cost LP charges at the p95 envelope cap in ~every economic hour
at a marginal spread of just the efficiency-loss floor (~$3-4/MWh). The
measured fleet's charge distribution reveals a conduct cost of **$15-20/MWh at
its 5-10 % margin** (FINDING §3) — bracketing the derived **$14.25** physical
cycling cost — and CAISO's own DEB design prices exactly this term (DMM 2024
Eq 2.11.1 ρ; MSC Nov-2024: degradation terms "appropriate to include").
The model's current $0 is the estimate; the derived cost is the measured
replacement (rule 14).

## 3. Why this re-opens caiso-76's "no-change" honestly (both grounds moved)

The 2026-07-11 caiso-76 session resolved this knob NO-CHANGE on two grounds:

- *"RDT `STORAGE_VARIABLE_COST` defaults to $0"* — the RDT default is the
  fallback, not the design: the DEB ρ term exists to carry resource-specific
  validated cycling costs, and the fleet's revealed conduct shows a positive
  one in force.
- *"The zero-adder LP already UNDER-cycles CAISO"* (then: model discharge
  5.33/7.60/10.48 vs LESR RTD 5.67/10.04/12.06 TWh) — measured on the
  caiso-65-era model. The caiso-99 keeper stack now **OVER-charges** on the
  NG:OTH basis (6.06/10.20/13.76 vs measured 4.07/8.71/13.02 TWh); the
  failure mode the adder addresses is now present. FINDING §6 carries a
  two-sided throughput guard so the B-leg cannot trade the belly fix for a
  new under-cycling defect on either measured basis.

## 4. What was measured-refuted and is NOT proposed

The charter's alternative (b) — a DA-spread day-level charging threshold — is
refuted by the measurement (FINDING §2): the mature fleet charges on ~every
day (skip-share ~2 % in 2024/25, weak spread correlation); there is no
day-gate in the data for a threshold to anchor to. It is closed, not deferred.

## 5. The ask

**Owner: do you authorize the CAISO-100 B-leg — `battery_dispatch_adder` 0.0 →
the derived 14.25 for the CAISO backcast recipe, single-delta A/B under
FINDING §6's pre-registered bands and gates?** Until ruled, the knob stays
0.0 and no B-leg is solved. If ruled OUT, the residual belly re-charters to
the remaining conduct channels (DA-award allocation, AS-deployment variance),
both currently unmeasured at the needed grain.
