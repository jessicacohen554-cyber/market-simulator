# FINDING — PJM ST_GAS volume driver (#1483): net-load reliability commitment, not RMR

**Date:** 2026-07-07 (G-20b path-B lane). **Status:** investigation finding +
derived candidate mechanism, NOT applied to any run. Keeper unaffected.
**Issue:** #1483 (G-21 re-grounding relocated the C1 miss onto an unmodeled
ST_GAS volume driver). **Scripts:** `scripts/derive_pjm_st_gas_netload_drag.py`
(new, this finding's evidence generator).

## 1. The question

After the G-21 SRMC re-grounding (keeper `pjm-83-srmc-reground`), PJM ST_GAS
clears 3.4–5.8 TWh/yr against ~8.6/12.4/14.3 TWh (2023/24/25) EIA-923 actual —
the efficiency merit order (ST_GAS AHR ~10.6 vs CC ~7) sends the marginal
energy to CC_REGULAR. Issue #1483 lists three candidate drivers: (1) RMR /
must-run contracts, (2) local-deliverability pockets, (3) per-plant heat-rate
error. Rule 17 requires any fix to carry a window, a cited driver, and a
forward story; rule 14 forbids re-lowering the offers below the Manual-15
SRMC floor.

## 2. Measured decomposition — who actually runs (CAMPD, plant-level)

CAMPD facility-level gross TWh for the model's ST_GAS plant set:

| plant (zone) | 2023 | 2024 | 2025 |
|---|---|---|---|
| Brunner Island (Central_PA) | 2.98 | 3.67 | 4.49 |
| Montour (Central_PA) | 0.64 | 3.12 | 4.94 |
| Martins Creek (Central_PA/EMAAC seam) | 0.62 | 2.70 | 2.37 |
| Shawville (Central_PA) | 1.73 | 1.67 | 1.18 |
| Chalk Point (SWMAAC) | 0.78 | 1.02 | 1.87 |
| New Castle (ATSI/west PA) | 0.96 | 0.74 | 0.74 |
| Edge Moor (EMAAC) | 0.27 | 0.38 | 0.45 |
| **H.A. Wagner (SWMAAC, RMR)** | **0.09** | **0.17** | **0.21** |
| **Eddystone (EMAAC, DOE 202(c))** | **0.03** | **0.07** | **0.05** |

### Candidate (1) RMR — FALSIFIED as the volume driver

The RMR/202(c) steamers carry ~0.1–0.3 TWh/yr combined — under 3 % of the
class actual. Wagner 3–4 (oil/gas steam, FERC-approved RMR settlement through
2029-05-31, BGE-zone voltage support) and Eddystone 3–4 (DOE §202(c) order
2025-05-30 → 2026) are real, cited instruments — already in
`data/raw/confirmed-retirements/pjm.csv` — but they are *retention*
instruments for low-CF units, not the energy. An RMR floor would close <0.3 of
the ~9 TWh gap.

### Candidate (2) local deliverability — NOT the primary story

The volume carriers are the Marcellus-belt coal-to-gas conversions (Brunner
Island, Montour, Martins Creek, Shawville — all Central-PA, the export-heavy
gas belt, not import-constrained pockets). Chalk Point (SWMAAC, ~1–1.9 TWh)
has a plausible local component but is second-order.

### Candidate (3) heat-rate error — FALSIFIED

Measured plant heat rates (CAMPD heatInput/grossLoad, running hours): Brunner
Island 9.4–10.1, Montour 9.2–9.8, Martins Creek 10.7–10.8, Shawville 10.3,
Chalk Point 10.6, New Castle 10.5 — at/near the model's ~10.6 class AHR.
Montour is ~1 MMBtu/MWh better than class but that alone cannot flip the
CC-vs-ST merit order.

## 3. The actual driver — multi-day reliability commitment on high net-load

The measured operating signature (printed by the derive script):

* **Flat diurnal profile** — hour-of-day fleet output varies only ~1.6× across
  the day (2024: 1.1–1.8 GW). When these boilers run, they run around the
  clock — NREL gas-steam min-run 24–48 h (`ST_GAS_COMMITMENT_PARAMS`), a
  stop-start costs more than idling at min load.
* **Strongly seasonal** — Jul 2024 alone 2.7 TWh; winter peaks; shoulder
  months near zero. Commitment follows system tightness, not calendar.
* **Monotonic in net-load** — pooled overnight (23–05h, the low-price hours
  where hour-by-hour dispatch is non-economic, so output = held commitment)
  CF rises 0.05 → 0.48 over the 60→111 GW net-load range; Spearman ρ
  overnight 0.32/0.38/0.52, all-hours 0.51/0.60 (2023/24/25).

This is the same phenomenon the ERCOT keeper's ST_GAS drag models
(`docs/ercot-st-gas-netload-drag-2026-06.md`): RUC-style reliability
commitment of big steam capacity in tight periods, held online through the
trough. The hourly energy-only LP, free to de-commit each hour, never sees it.
Rule 17 triple: **window** = all-hours conditional on the net-load hinge (the
measured diurnal blocks are flat — unlike the CT drag's [15,22) ramp
concentration); **driver** = PJM reliability commitment of long-min-run steam
capacity, keyed to system net-load (the RUC tightness proxy); **forward
story** = net-load regenerates from a load forecast + VRE build and the floor
responds to it.

## 4. Derived PJM curve (rule 25 — the ERCOT hinge cannot cross ISOs)

`scripts/derive_pjm_st_gas_netload_drag.py` (CAMPD 2023–2025 pooled overnight
CF vs EIA-930 PJM net-load, hinge fit, 9 pure-play plants, 7.71 GW nameplate):

```
gas_st_drag_slope_per_gw = 0.01029
gas_st_drag_intercept    = -0.7263      (zero below ~70.6 GW net-load)
gas_st_drag_cap          = 0.39
```

Energy cross-check (all-hours floor vs measured class total): 2024 86 %,
2025 83 % — a floor the LP exceeds economically, correct direction — but
**2023 overshoots at 122 %** (floor 9.9 vs measured 8.1 TWh).

### Disclosed caveat — the 2023 overshoot is a fleet-vintage artifact

Montour's coal→gas conversion completed across 2023–24: its 2023 gas-steam
output was 0.64 TWh while the model's (2024-vintage EIA-860) fleet classes its
full ~1.5 GW as ST_GAS in 2023 too. The pooled curve therefore over-floors the
2023 class. Before this mechanism can be enabled in a probe, one of:
(a) vintage-aware nameplate in the derivation AND application (exclude
not-yet-converted capacity from the 2023 floor — cited conversion dates), or
(b) accept and disclose the 2023 +1.3 TWh overshoot risk. Option (a) is the
honest fix; it needs the conversion dates intaken as data, not hand-coded.

## 5. Disposition

* RMR is real but tiny — keep the instruments in `confirmed-retirements`
  (retention channel); do NOT build an RMR energy floor (it would be a floor
  without a volume to explain — rule 19).
* The candidate mechanism is `gas_st_netload_drag` (already plumbed:
  `ScenarioConfig.gas_st_netload_drag` + `gas_st_drag_overrides`,
  `fleet.apply_gas_st_netload_drag_floor`, `MECH_ST_NETLOAD_DRAG` D-2
  attribution) with the PJM-derived coefficients above — pending the §4
  vintage fix, then its own single-delta probe cycle (full span, rule 16),
  with a D4 all-hours window declaration for `(MECH_ST_NETLOAD_DRAG, None)`
  documented against the flat measured diurnal blocks.
* Do NOT stack this into the G-20b path-B probe (pjm-85) — one mechanism per
  probe; the reserve-supply scoping and the ST_GAS commitment drag are
  different phenomena (rule 19).
