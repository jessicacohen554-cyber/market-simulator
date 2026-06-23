# PJM bituminous-marginal probe — REFUTED (2026-06)

**Date:** 2026-06-23. **Branch:** `claude/pjm-coal-bit-marginal-7pl7n7`.
**Status: negative result / diagnostic.** Making PJM bituminous a fully
dispatchable, full-delivered-cost marginal swing fuel — the literal thesis —
makes the model **dramatically less faithful** on both hourly shape and annual
volume. The keeper's must-run floor + sub-cost passthrough, which the thesis
called "PRB-style mistreatment", is what actually reproduces the measured
bituminous baseload behaviour. The frontier remains **price formation**, not
coal cost or contract structure (confirms `pjm-coal-overrun-decomp-2026-06.md`).

## What was tested (one-year 2024 diagnostic, cheapest-gas worst case)

`coal_bit_dispatchable` (new ScenarioConfig flag) + `coal_bit_passthrough_floor`
1.0 on the pjm_42_campdfix keeper recipe, PJM 2024:

1. **Full delivered-cost bid** (floor 0.76 → 1.0): above-must-run bituminous
   tranches carry full EIA-923 delivered cost (~$3.03/MMBtu × HR ~10.5 ⇒ SRMC
   ~$32) instead of the 0.76 cheap-gas discount.
2. **Fully dispatchable** (`coal_bit_dispatchable=True`): a bituminous-ranked
   plant's per-plant CAMPD must-run floor is **zeroed**, so all of its capacity
   enters the rising offer curve with Pmin=0 and can back down. PRB / lignite /
   waste keep their take-or-pay floors.

The bit must-run floors are already the CAMPD-observed P5-of-all-hours minimum
sustained level (Cardinal 60% / Kyger 48% / Gavin 48% / Amos 37%, from
`derive_thermal_tranches.py`), so "lowering the floors" was never the lever —
zeroing them (full dispatchability) is the only faithful way to express "it
backs down when uneconomic".

## Result — worse on every axis (2024, vs corrected per-plant CAMPD)

Bituminous fleet (CAMPD-GWh-weighted over 26 plants):

| metric | keeper (floor 0.76 + must-run) | marginal (floor 1.0 + dispatchable) | Δ |
|---|---|---|---|
| per-plant Pearson r (hourly shape) | **0.774** | 0.606 | **−0.167** |
| cf_emd (operating-level dist., lower better) | **0.088** | 0.229 | **+0.140** |
| cf_band_overlap (higher better) | **0.638** | 0.526 | **−0.113** |
| COAL_BIT annual TWh | **115.2** (CAMPD 107.7) | **55.1** | **−60.1** |

Every major plant collapses: Gavin 11.8→4.8, Amos 9.1→2.4, Cardinal 10.4→3.7,
Kyger 5.6→2.3 TWh. The fleet runs at **~half** its measured output.

### Where the 60.8 TWh of lost bituminous went (system fuel mix, 2024)

| | keeper | marginal | Δ |
|---|---|---|---|
| COAL_BIT | 113.0 | 52.2 | **−60.8** |
| CC_REGULAR (gas) | 337.6 | 354.0 | +16.4 |
| CT_PEAKER (gas) | 21.3 | 33.1 | **+11.8** |
| ST_GAS | 13.8 | 17.6 | +3.8 |
| net import (− = export) | −37.4 | −12.3 | +25.1 |

≈32 TWh **coal→gas relabel** (worsens the already-over gas fit, and pulls in
expensive CT peakers) + ≈25 TWh **collapsed exports** (net export 37→12 TWh,
now *under* the measured ~33). Load-weighted LMP rises $27.21 → $29.75 (actual
~$29.5) — but this is **coupled to the wrong volume collapse** (cheap coal
leaves, expensive peakers/gas set the margin more often), not a clean
price-formation fix.

## Reading — the thesis is empirically false for 2023–25 PJM bituminous

If PJM bituminous truly bid full delivered cost and backed down when gas is
cheap, it would have run **~50% less** than it actually did. CAMPD shows the
opposite: these plants ran as **baseload price-takers below full delivered
cost** — exactly what the keeper's 0.76 passthrough discount + CAMPD must-run
floor encode. Real reasons (take-or-pay tonnage, unit-commitment min-run /
hysteresis, capacity-obligation must-offer) keep bituminous up through cheap-gas
hours; a pure full-cost merit-order treatment does not. So the keeper's coal
structure is **not** an ERCOT-PRB mis-port — it is the faithful representation
of measured PJM bituminous behaviour, and removing it degrades the model.

The standing decomp conclusion holds: the residual coal/export over is
downstream of PJM's **suppressed model LMP** (a gas-marginal / missing
afternoon-scarcity price-formation problem). Only after price formation is lifted
toward actual would full-cost bituminous naturally hold near its observed
baseload — at which point marginal-bit could be revisited without the collapse.

## Disposition

- **Not a keeper; not registered.** Per CLAUDE.md #13 this is a single-year
  (2024, cheapest-gas worst case) throwaway diagnostic isolating the
  dispatchable-bit effect, not a dashboard run. The result is decisive and
  same-signed across years (dearer 2023/2025 gas → milder but identical-direction
  collapse), so the 3-year solve was not spent on a foregone-negative bundle.
- **`coal_bit_dispatchable` kept as a default-OFF diagnostic lever** (CLAUDE.md
  #11): it must never be enabled in a keeper. It exists so price-formation work
  can re-test marginal-bit once PJM's clearing price is lifted toward actual.
- **Keeper remains `pjm_42_campdfix`** ("pjm 42 campd-nan-fix"), unchanged.

### If a price-lever pairing is wanted next

The clean separation is **Option B**: keep the CAMPD must-run floor (preserves
the measured baseload volume + shape) but bid the bituminous must-run tranche at
full delivered cost instead of sunk-fuel VOM-only (no take-or-pay for spot
coal). That lifts the price the must-run base *sets* when marginal without
collapsing its volume — but it only bites once the broader afternoon-scarcity
price formation (`pjm-reserve-ordc` / `derive_dam_offer_hrmults`) is in place.

## Reproduce

```bash
# keeper baseline (one year; ~12 min, ~11 GB peak — ONE PJM per-plant solve at a time)
python scripts/probes/_pjm_retiree_run.py 2024 results/calibration/pjm_42_repro_y2024
# marginal-bit probe
python scripts/probes/_pjm_coalbit_marginal_run.py 2024 results/calibration/pjm_43_y2024
# per-plant bituminous CF-shape compare: reads dispatch/2024_P1.parquet + the
# campd shared input from each bundle, computes per-plant r / cf_emd /
# cf_band_overlap for bituminous plants.
python scripts/probes/_pjm_coalbit_shape_cmp.py \
    results/calibration/pjm_42_repro_y2024 results/calibration/pjm_43_y2024 2024
```
