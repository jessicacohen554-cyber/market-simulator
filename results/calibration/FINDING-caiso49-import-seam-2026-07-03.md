# CAISO 49/50 — the +40% mean-LMP root cause is the fitted flat import ladder; re-ground the WECC seam on the measured intertie hub prices

**Date:** 2026-07-03
**Branch:** `claude/caiso-calibration-2026-07-02-0zshir`
**Keeper at start:** `2026-07-01-caiso-42-atc-hydro` (NOT-YET; 7 criteria FAIL — the furthest ISO from calibrated)
**Bundles:** `results/calibration/caiso49_perhub_seam` (Arm A), `results/calibration/caiso50_perhub_bridge` (Arm B = A + UC startup bridge)

## 1. Root-cause decomposition (task order: no offer-curve touch until this exists)

### 1.1 What actually prices CAISO — the measured seam evidence

The measured WECC intertie LMPs (`data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet`,
OASIS Malin + Palo Verde scheduling points, energy+congestion+loss) track the actual CAISO hub price
almost month-for-month and hour-for-hour — the WEIM couples CAISO to the West and ~30% of supply
crosses this seam:

| 2024 monthly $/MWh | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| actual CAISO RT (hub mean) | 67.7 | 31.9 | 19.1 | 13.6 | 10.6 | 21.5 | 42.2 | 31.4 | 31.1 | 39.8 | 37.3 | 41.6 |
| measured Palo Verde | 64.4 | 33.0 | 16.6 | 11.8 | 11.6 | 25.9 | 50.2 | 38.2 | 37.7 | 37.6 | 33.7 | 38.8 |
| **keeper caiso-42 model** | **48.9** | **54.9** | **44.4** | **37.5** | **35.4** | **36.6** | **46.9** | **44.8** | **43.2** | **45.1** | **49.1** | **54.9** |

Hour-of-day 2024: actual midday (h10–14) $12–15, Palo Verde midday $8–11; actual overnight $37–41,
PV overnight $38–40; actual evening peak $52, PV evening $58–67. Annual PV mean **$33.3** ≈ the
actual CAISO RT mean **$32.4**. The same correspondence holds in 2023 and 2025.

### 1.2 What the keeper prices the seam with instead

The caiso-42 keeper prices this seam with the **static fitted ladder**
(`IMPORT_TRANCHES["CAISO"]`: $28/36/48/68/110/180, flat across all 8760 hours) plus $8/$0 export
sinks — the audit's C-6/L8 item ("historically re-fit against the model's own solved price").
Resolving the keeper's tri-state flags against `_calibration_config` confirms every measured-hub
path was OFF (`caiso_per_hub_intertie/bidir/import_hub_prices/reference_price_seam` = False), and —
contrary to the registered definition — the corridor-ATC-forward envelope was **inert** (the
`forward_atc` gate requires the per-hub corridor split, which the keeper never built; the caiso-47
byte-faithful HEAD replay confirms it reproduces the keeper without any envelope line in its log).

The flat ladder explains each failing criterion:

1. **C3a mean +36.9…+48.8% (over):** the ladder floors the seam at $28–48 in the ~4,000 hours/yr
   the real West clears at −$20…+$20 (spring/midday), so the model's marginal is either a $28–48
   import rung or a domestic CC at its ~$42–44 SRMC. Feb–Jun 2024 the model is +$20–25/month over.
2. **Jan 2024 −$19 (under):** the real winter hub ($64–78) never enters; the ladder caps winter
   import cost at $68 and domestic gas (monthly citygate) misses the daily spikes.
3. **C3b NRMSE 0.32–0.54:** model monthly range ~$35–55 vs actual ~$11–68 — the seasonal swing
   lives in the seam price the ladder flattens.
4. **C3c tail:** 2023's 107 h >$200 is generated 100% by the fitted 7,500 MW simultaneous cap
   (caiso-46/47 A/B: published MIC releases it → tail 0; actual 21 h), while 2024/25 collapse to
   0 h because the $180 scarcity rung + $5,000 VOLL is the only tail mechanism — the real tail
   (measured hub spikes to $551/$636 in 2024, $1,092/$1,244 in 2023) never enters.
5. **C4 gas r→0.42, C1 CC_REGULAR +9.21 TWh, C2 2025 gas +12.3%, C5a CO2 +7/+13%:** with imports
   mispriced flat, in-state CC runs midday hours where cheap western surplus should serve (and the
   model under-imports), and misses hours where the seam is genuinely expensive — wrong volume and
   wrong timing, CO2 follows.

### 1.3 Hydro (audited, kept)

`hydro_eia930_monthly=True` pins monthly energy budgets to the measured EIA-930 total (2024:
22.68 TWh); hydro prices endogenously at the LP's monthly-budget shadow price (opportunity cost).
Structurally correct; no change. The 2025 hydro gap was already fixed by caiso-42.

### 1.4 Why the prior arms failed to move the mean

- **caiso-35/36 (forward reference seam):** annual-anchored formula — right level, no measured
  shape; 2023 body blew out; rejected.
- **caiso-44/45/48 (startup bridge + bidir hub-priced tie):** fixed Jan (49→61) and improved
  spring, but the bidir node (a) averages Malin+Palo Verde into one export hub that FLOORS the
  price when exporting (summer regressed +$4–7), (b) kept the fitted 7,500 MW cap (2023 tail
  161 h), and (c) had no export-direction envelope, so unbounded 3.5 GW flat export raised CC
  infra-marginality (C1 CC_REGULAR widened to +11.1 TWh).

## 2. The fix (all measured/structural; no fitted values added, several removed from the binding path)

**Arm A (caiso-49):** every caiso-42 keeper lever, plus
1. **`caiso_per_hub_intertie` + measured hub pricing** — the two real corridors (COI/Path-66 →
   NP15 at Malin; Path-46/WOR → SP15 at Palo Verde), each a single signed flow, import leg =
   own hub + OATT wheel + per-tranche CARB border carbon, export leg = own hub − ε,
   arbitrage-free per corridor-hour. Measured data replaces the fitted ladder in the binding path
   (rule #14); forward analogue exists (`caiso_reference_price_seam` / per-hub reference formula).
2. **`caiso_corridor_flow_limit`** — measured p95 deliverability envelopes per (month × hour-of-day),
   BOTH directions: import tightens midday (the neighbors are themselves long), export collapses
   to ~0 in evening-ramp buckets (no wheel-out; the caiso-45/48 C1 widening guard).
3. **`capacity_deliverability_limits` (Part A)** — the published branch-group MIC sum
   (16,055/16,452/16,148 MW for 2023/24/25) replaces the hand-tightened 7,500 MW scalar
   (audit C-5). New first-class CLI flag (`--capacity-deliverability-limits`) replacing the
   caiso-46 probe's JSON side-channel. Part B (capacity-payment collapse) is unreachable in a
   backcast (no capacity evolution).
4. **2023 hub-series hybrid gap-fill** (`eia_loader.measured_import_hub_prices`): the ~1.4k-hour
   Jan–Feb 2023 OASIS retention gap is filled with the corridor's forward reference price
   (bounded ≤25% of the year; a mostly-missing series still falls back). The filled hours are the
   same hours absent from the actual-LMP benchmark, so C3 never reads a filled value; ten measured
   months stop being discarded wholesale (the caiso-48 2023 regression).

**Arm B (caiso-50):** Arm A + `caiso_ra_startup_bridge` + `caiso_ra_bridge_decommit` — the
caiso-44/48 UC restart-economics mechanism (hold a committed CC at min-load across a gap when
startup cost exceeds the net hold cost; DA-horizon-bounded, RUC-order decommit). Real UC physics,
forward-derivable; scored as its own arm so the seam fix and the commitment fix attribute cleanly.

**Not touched (deliberately):** offer curves (the caiso-39 CAMPD econ_high 1.21→~1.06 measured
correction stays deferred until the seam fix lands and its CC-volume effect is re-measured);
hydro; the CT drag / reliability floor / RA min-load levers (carried as-is).

## 3. Results

(filled in after the 3-year solves; see the dashboard entries `caiso 49 perhub seam` /
`caiso 50 perhub bridge` and the verdicts below)
