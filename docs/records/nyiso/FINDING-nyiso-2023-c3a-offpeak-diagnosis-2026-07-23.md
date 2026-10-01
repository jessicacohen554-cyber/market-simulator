# FINDING — NYISO C3a 2023 residual is an OFF-PEAK downstate-thermal price-formation floor, NOT gas-basis / offer-markup / reserve (2026-07-23)

**Status: DIAGNOSTIC ONLY. Keeper stays `nyiso-70`
(`2026-07-22-nyiso-70-scr-edrp`); no keeper change, no registration.** This
session picked up the nyiso-70 handoff task — close the 2023 C3a mean-LMP
residual (+15.9%, RT load-weighted) — and instead **conclusively re-scoped it**.
The handoff's two named hypotheses (offer-surface markup, Transco Z6 / Iroquois
gas basis) and three further structural levers are each **empirically refuted**
by a 2023-only diagnostic A/B: every one either moves the residual by ~0 or makes
it **worse**. The residual is a broad OFF-PEAK over-pricing whose price-setter is
a mid-efficiency downstate combined-cycle unit, dispatched at full SRMC while the
efficient CC fleet is outage-exhausted. No single mechanism in the current model
closes it.

All A/Bs are `scripts/replay_keeper.py … --years 2023 --set <flag>` off the
committed keeper bundle `results/calibration/nyiso70_scr_edrp_reserve`, scored on
the committed hourly sidecars vs `actual_lmp_hourly_NYISO.parquet` (2023 is a
train year — rule 22 compliant). Probe scripts: `scripts/probes/_nyiso_2023_*.py`.

## 1. The residual is OFF-PEAK, not broadband

Load-weighted RT mean LMP, shoulder months (May/Jun/Aug), keeper nyiso-70:

| window | actual RT | model (keeper) | error |
|---|--:|--:|--:|
| shoulder **off-peak** (hod 0–6) | **19.62** | **30.02** | **+53%** |
| shoulder on-peak (hod 14–19) | 32.12 | 39.70 | +24% |
| full year | 30.28 | 36.02 | +19% |

The +15.9% C3a is dominated by the overnight/shoulder trough: the model floors
NYISO off-peak at ~$29–30 statewide (uniform across all five zones — **no
congestion signal**) where the real market troughs to ~$16–20. On-peak is closer.

## 2. Five refutations (this is the finding's core)

| lever A/B'd (2023, vs keeper) | off-peak $ | Δ | verdict |
|---|--:|--:|---|
| `energy_reserve_coopt=false` | 30.02 | **0.00** | reserve NOT the driver (confirms the handoff's 1.6%-of-mean note; the dispatch-reshuffle effect is also ~0) |
| `cc_intermediate_split=true` | 30.41 | **+0.39** | **WORSE.** NYISO's `CC_REGULAR` curve is already `econ_high=1.0` (flatter than the MISO `CC_INTERMEDIATE` fix at 1.08); routing to it *steepens* the ramp |
| `gas_plant_monthly_fuel_pricing=false` | 30.02 | **0.00** | per-plant F923 delivered gas NOT the driver |
| `nyiso_zonal_gas_basis=false` | 33.59 | **+3.57** | **WORSE.** The zonal basis is net price-*lowering*; removing it raises the trough |
| `reliability_floor=false` | 31.81 | **+1.79** | **WORSE.** The downstate ST/CT reliability floors supply *cheap* forced local energy; removing them raises the trough |

And from the P0-vs-P1 decomposition (`_nyiso_2023_markup_decomp.py`): the P1
startup-amortization **markup adds only +$0.55/MWh** system-wide (+$0.67 off-peak).
P0 base-cost is already +14.3% — **so it is NOT an offer-markup problem** (the
handoff's first hypothesis). The gas basis is grounded and already minimized (§2
rows 3–4). Neither of the handoff's two named hypotheses survives.

## 3. What the off-peak price-setter actually is

Marginal-unit identification at true availability (`pmax × availability`,
`_nyiso_2023_avail_stack.py` / `_nyiso_2023_mc_decomp.py`):

- Off-peak the price-setter is a **downstate CC_REGULAR at mc ≈ $29.2**
  (`hr 8.24`, gas ≈ ISO-month+zonal, VOM $2, RGGI carbon $6.07). Reliability-
  floored **ST_GAS** (HR 11.5) runs at ~52% util 100% of hours but sits **above**
  the clearing price (forced, made-whole-in-reality, not the LP price-taker here).
- **Efficient CC (tranche HR < 7.5) is outage-exhausted:** 4,493 MW available
  after the (CEMS-verified, settled) outage overlay, **90% utilized** off-peak
  (443 MW headroom). The off-peak CC load (~5,003 MW) therefore spills onto the
  **mid-efficiency CC band (HR 7.5–9)** — that is the $29 marginal.
- The naïve merit stack (sort by mc, ignore constraints) clears ~$21.5, but it is
  **unreachable**: every floor removed *raises* the price (§2), so the floors are
  net-lowering and the $29 is already the constrained optimum given the measured
  fleet.

Imports are not the gap either: the model already imports **more** off-peak
(2,909 MW) than the measured schedule (2,324 MW) and still floors at $30; reality
troughed to $19.6 on **less** import. So reality's *domestic* off-peak marginal
was genuinely cheaper than the model's mid-CC.

## 4. Why it does not close — the surviving structural interpretation

Given measured/grounded demand, imports (EIA-930-reconciled), nuclear, hydro,
renewables, gas (ISO-month + measured zonal basis), RGGI ($13.49), and
CEMS-verified outages — **and** an efficient-CC fleet legitimately exhausted
off-peak — the model's full-SRMC dispatch produces a $29 mid-CC trough. Reality
troughs ~$10 lower. NYISO CCs are baseload-duty (median CF 79–86%), so their
EIA-923 heat rates are **not** cycling-inflated; the mid-CC is priced correctly
on its own SRMC. The residual is therefore most consistent with a
**price-formation gap the pure-LP full-SRMC model cannot represent**: real
overnight LBMP is depressed by committed units bidding **below SRMC** (down to
their avoid-shutdown / no-load-recovery floor, sometimes negative) to stay online
through the trough, whereas the LP prices every online unit at its full marginal
energy cost. This is the same class as the startup-cost treatment — a commitment
economics effect on the *offer*, not a missing supply resource.

The only other non-refuted contributor is the residual **efficient-CC
availability** itself (the outage overlay removes Ravenswood ~1,030 MW / Athens
~759 MW etc. through the shoulder). Those windows are CEMS-verified and the
outage source is **settled** (`docs/handoffs/nyiso-outage-source-determination-2026-07.md`,
rule 11) — not to be re-litigated.

## 5. Recommendation

- **Keeper unchanged: `nyiso-70` remains, NOT-YET on 2023 C3a/C3c/C7.** Nothing
  tested this session improves C3a; several candidate levers make it worse.
- **Do NOT pursue** for C3a 2023: reserve, the CC econ-ramp / `cc_intermediate`,
  per-plant or zonal gas basis, or the reliability floor. All refuted above.
- The **only** structurally-honest forward lever is a **below-SRMC overnight
  commitment-bid mechanism** (committed thermal offering into the trough below
  full marginal cost to avoid shutdown), which is a **cross-ISO price-formation
  methodology change** — not a NYISO calibration knob — and must be validated
  model-wide (it would move every ISO's overnight trough) before any keeper use.
  Absent that, the 2023 off-peak residual is a **structural limit** of the
  full-SRMC LP on the measured, outage-thinned downstate fleet, and nyiso-70
  should be held as the most structurally-faithful NOT-YET keeper (rule 1).
- The C7 ST_GAS off-peak-shape miss shares this root: the flat overnight
  reliability floor + the forced-ST_GAS trough both flatten off-peak dispatch.
  A below-SRMC trough mechanism would address C3a and C7 together, as the handoff
  anticipated — but via commitment bidding, not the levers it named.

## Reproduction

```
# keeper bundle + hourly sidecars already committed:
#   results/calibration/nyiso70_scr_edrp_reserve/hourly/{system,class_hourly}_2023.parquet
# each A/B (≈4 min, 2023-only, throwaway --out-dir):
python scripts/replay_keeper.py results/calibration/nyiso70_scr_edrp_reserve \
  --out-dir /tmp/ab --years 2023 --set <flag>=<value> --note "diag"
# analysis probes (read the committed sidecar / a captured decomposition npz):
python scripts/probes/_nyiso_2023_avail_stack.py      # marginal unit @ true availability
python scripts/probes/_nyiso_2023_mc_decomp.py        # full mc decomposition
```
