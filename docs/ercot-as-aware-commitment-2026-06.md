# ERCOT AS-aware commitment — the phantom-headroom fix (PARTIAL / rejected probe)

**Date:** 2026-06-26
**Branch:** `claude/ercot-as-aware-commitment-e3j9c2`
**Status:** lever BUILT, tested, default-off, ERCOT-gated; greenlight gate **NOT
met** — the broad-May month **over-fires to VOLL**, so this is a **rejected
probe**, not a keeper. The measured DAM-AS overlay (run157) **stays** the ERCOT
keeper / pre-RTC+B backcast bridge.
**Reads first:** `docs/ercot-multiproduct-as-coopt-2026-06.md` (the run159 partial
that motivated this build) and
`docs/ercot-reserve-supply-scarcity-handoff-2026-06.md` (the rejected-approach
log + the measured RTOLCAP reserve-supply target).

---

## What this build is

The forward analogue of the measured DAM-AS overlay needs the multi-product co-opt
to form the **broad** May-2024 elevation endogenously, not only the acute days.
run159 showed the gap is **phantom headroom**: the perfect-foresight P1 LP leaves
cold slow-start units idle yet counts their full capacity as reserve, so most May
hours are not reserve-thin and the co-opt only binds on the genuinely tight acute
days ($40 acute vs $21 broad month).

This build adds **AS-aware commitment** — a P2 commitment screen that values a
unit's *AS* revenue (not energy margin alone) when deciding which units stay
online, so the units a tight month keeps online for AS are committed and the P2
co-opt's shared-headroom RHS reflects **realistic online headroom** (the idle
slow-start capacity that earns neither energy nor AS is decommitted out of it).

### Components (all default-off, ERCOT-gated, legacy byte-identical)

1. **`config.ercot_as_aware_commitment`** (+ `ercot_as_adequacy_frac`, default 1.0)
   — flags; CLI `--ercot-as-aware-commitment`. Triggers a P2 pass even with the
   energy-only commitment screen off; requires `energy_reserve_coopt` +
   `ercot_multiproduct_as_coopt`.
2. **`scarcity.ercot_as_aware_unit_value`** — `as_value[g,t] = reserve_price ×
   headroom`, the per-unit AS revenue estimate from the model's **own P1
   balance-row dual** (`reserve_price_by_family`), never the measured MCPC — no
   fit. Cascade-aware (fast units price every product; quick-start peakers only
   Non-Spin).
3. **`commitment.compute_commitment(as_value=…)`** — AS revenue joins the in-merit
   mask and the startup hurdle, with a **temporal-locality** filter: an AS-only
   run (no energy-in-merit hour) is dropped, so a unit running for energy in one
   window (summer peak) is not held online for AS in a different idle window (May
   midday) the LP leaves it cold. That cold idle capacity is the phantom headroom
   the screen removes.
4. **`commitment.as_adequacy_commit`** — the anti-over-fire floor (the
   `reserve_adequacy_commit` analogue): after the screen decommits, re-commit
   cheapest eligible units until each co-opt headroom row's committed capacity
   covers the **total responsive P1 energy + that row's MEASURED ASPLANNP433
   requirement**. Tier-aware (fast row covered from the fast set, not peakers).
   The target is the measured AS procurement, never a price fit; `frac` is a
   coverage multiple (CLAUDE.md #12).

The reserve dual still forms **from the LP** end-to-end; nothing reads the
measured MCPC. The honesty gate holds.

---

## Greenlight gate — NOT met (broad May over-fires to VOLL)

2024, overlay OFF, AS-aware commitment ON (`scripts/archive/run_160.py`; evaluated with
`scripts/probes/_eval_may_gate.py`, demand-weighted vs actual RTSPP):

| configuration | 2024 annual | May month | May acute (8/24/26) | Aug month |
|---|---|---|---|---|
| target / actual | ~26.8 | **~46.7** | **~45** | ~38.6 |
| run159 (no commitment) | 22.4 | 21.3 | 40.0 | ~29 |
| AS-aware, no floor | 84.9 | 245 | 165 | 42.3 |
| AS-aware + floor frac=1.0 (net-hr) | 75.4 | 235.6 | 47.7 | 40.6 |
| **AS-aware + floor (total-energy)** | **61.8** | **187.8** | **47.3** | 32.5 |

**What works:** the lever is **directionally correct and forms the scarcity** the
co-opt could not. The **acute days lift to ~$47 (≈ the ~$45 target) with the
adequacy floor**, and the over-fire is **concentrated in the low-load shoulder
months** (Aug holds at $32–43), so the screen correctly *targets* the months the
overlay lifts.

**Why it fails the gate:** the **broad May month over-fires to VOLL** — 132 May
hours with the per-product reserve dual > $1000, demand-weighted May ≈ $188 vs the
$46.7 target.

### Root cause (P2-actual headroom diagnostic)

Decomposing the P2 solve's **actual** reserve headroom vs the AS requirement (not
the floor's P1 estimate):

```
P2-ACTUAL row0 (fast: RegUp/RRS/ECRS, on CC/ST/coal/nuclear):
  May hrs short = 335/744,  min cov 1732 MW,  req ~5068 MW,  mean cov 5653
P2-ACTUAL row1 (all four products, + quick-start peakers):
  May hrs short = 493/744,  min cov 2797 MW,  req ~8771 MW,  mean cov 7465
```

The adequacy floor commits enough **capacity**, but that capacity does **not**
translate to **headroom** at solve time: in the May **evening-ramp** hours the
committed fast (CC) fleet runs near full **for energy** — because the screen
decommitted the cheaper peakers/slow units that would otherwise carry that
energy — so fast headroom collapses 3+ GW **below** the fast requirement → the
VOLL-anchored shortfall curve prices the deficit at VOLL, not the intended modest
shared-headroom opportunity cost.

The mechanism is **bimodal with no grounded middle**:
- **Idle-only removal** (gentle screen) → fast headroom stays abundant in low-load
  May → no shortfall → back to the run159 **under-fire** ($21).
- **Aggressive removal** (energy-margin screen) → the committed fast fleet must
  back-fill the decommitted units' energy → evening fast headroom collapses →
  **VOLL over-fire** ($188+).

Threading the ~$46.7 opportunity-cost target between these would require tuning
the screen aggressiveness (or `frac`) **to the price** — a forbidden fit
(CLAUDE.md #1/#11). So the lever is left structurally complete but **off**, and
the run is registered as a **rejected probe**.

---

## Ruled out this session (adds to the handoff's rejected-approach log)

- **Valuing AS via the P1 reserve *price*** is partly circular: P1's broad-May
  reserve price is ~$0 (the phantom-headroom under-fire we are trying to fix), so
  the `as_value` cannot protect the very units a tight May keeps online — the
  screen decommits them on energy margin alone. The adequacy floor (requirement-
  based, not price-based) is the necessary complement, but it floors **capacity**,
  which the P2 redispatch converts back to energy rather than headroom.
- **AS-adequacy floor on net headroom / per-row energy / total-responsive energy**
  — each tightens the acute days correctly but none prevents the evening fast-
  headroom collapse, because the floor cannot force a *committed* unit to *withhold*
  energy for reserve; the co-opt does that only when the reserve price exceeds the
  energy value, and by then headroom is already gone.

## The promising next track (not built)

The real signal is in `docs/ercot-reserve-supply-scarcity-handoff-2026-06.md`
Session 2: the **measured RTOLCAP** (online responsive capability, ~16.7 GW 2024,
tightening to ~8–12 GW in the P90–P99 band) is the exogenous physical target the
reserve **supply** should track — a single grounded series, not the bimodal
commitment screen. A reserve-supply re-scope that makes the co-opt headroom RHS
track measured RTOLCAP (rather than full fleet headroom *or* an over-decommitted
screen) is the better-grounded path to the broad-month band, and it sidesteps the
energy-vs-headroom redispatch problem entirely because it shapes the **supply
definition**, not the commitment. The AS-aware screen built here remains available
(and correctly forms the acute days) but is not the broad-month mechanism.

## Files

- `src/market_sim/config/scenarios.py` — `ercot_as_aware_commitment`,
  `ercot_as_adequacy_frac`.
- `src/market_sim/results/scarcity.py` — `ercot_as_aware_unit_value`.
- `src/market_sim/model/commitment.py` — `compute_commitment(as_value=…)`,
  `as_adequacy_commit`.
- `scripts/run_calibration.py` — `_commitment_pass` AS-aware wiring; `run_year`
  P2 trigger.
- `src/market_sim/runner.py` — forecast-path wiring (mirror of the calibration
  path).
- `scripts/archive/run_160.py` — the 3-year overlay-off AS-aware run driver.
- tests: `tests/test_commitment.py`, `tests/test_ercot_multiproduct_coopt.py`.
