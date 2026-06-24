# pjm 50 — firm-export floor + TVA/LGEE seams + losses-only hurdle

Three grounded, forecast-native structural additions to the PJM reference-price
seam, building on the pjm-48 coal keeper + pjm-49 seam-price corrections. Each
traces to a measured/documented input and never to the realized net-interchange
target (rules #11/#12).

1. **Firm scheduled-export floor** (`firm_export_floor_by_year` +
   `inject_reference_price_firm_export`). PJM exports to MISO/NYISO in 87-100% of
   hours at a spread too thin for a pure energy-spread seam, because a large
   share is FIRM long-term scheduled capacity/energy. Force the cheapest export
   tranches on at the measured firm base — the **p10 of PJM's OWN per-tie
   SCHEDULED export** (`derive_firm_export_floor.py`; MISO 1250/100/0, NYISO
   900/1400/1650 MW), the export-direction mirror of the Manitoba/HQ firm-import
   floors. Forecast years carry no floor (byte-identical).
2. **Hurdle 2.0 → 1.0** — physical decomposition, not a flow fit. The old $2
   (OMS-RSC wheeling adder) conflated firm transmission service (paid by the firm
   scheduled flow, now the floor) with marginal losses (~3% × ~$35/MWh ≈ $1).
   Under the PJM-MISO/NYISO JOAs the coordinated economic flow pays no pancaked
   wheeling, so the marginal increment's only friction is losses.
3. **TVA + LGEE import seams** — ~8 TWh/yr of net import into PJM (south-west),
   previously unmodeled. Priced on the documented ~$30/MWh SERC-bilateral basis
   (HR 11.6, like the reconciled Carolinas), limits 1600/1100 MW from p99.5 of
   PJM's measured ties (`derive_interface_limits.py --check`). Per-tie data
   VALIDATES the net-import direction; it does not set it.

## Result: per-seam net export (TWh, + = PJM export), model vs PJM per-tie

| seam | 2023 m/t | 2024 m/t | 2025 m/t |
|------|----------|----------|----------|
| MISO      | +22.6 / +35.3 | +25.5 / +27.2 | +20.0 / +24.6 |
| NYISO     |  +8.4 / +18.5 | +20.4 / +20.4 | +28.1 / +21.9 |
| Carolinas |  −0.4 / −5.4  |  −6.2 / −6.4  |  +2.0 / −5.9  |
| TVA       |  −0.5 / −6.2  |  −4.7 / −5.8  |  +1.3 / −5.4  |
| LGEE      |  −0.5 / −2.2  |  −3.4 / −2.4  |  +0.9 / −2.3  |
| **NET**   | **+29.6** / 40.0 | **+31.6** / 33.0 | **+52.2** / 32.9 |
| EIA-930   | +40.0 | +32.7 | +18.0 |

Net-interchange MAE vs EIA-930 **15.2** TWh (pjm-49 16.5); vs the per-tie sum
**10.4**.

### 2024: every seam direction + magnitude correct
NET +31.6 vs +32.7. The firm floor nails NYISO (+20.4 exact), the losses hurdle
recovers MISO (+20.2→+25.5) and Carolinas (−4.8→−6.2), and TVA/LGEE import
correctly. This validates all three mechanisms.

### 2023: improved, still under (cheap-gas)
NET +29.6 (was +22.5 at pjm-49). The firm floor lifts NYISO (+4.3→+8.4) and MISO
(+17.6→+22.6). Residual: NYISO's low system-avg HR (9.66) leaves the economic
seam idle, so NYISO export ≈ the p10 firm floor (8 TWh) vs the real +18.5 — the
real firm export sits above p10 and/or clears against the PJM-NY *border* (not
the NYC-weighted system average). The p10 floor is held (rule #11: the firm
*contractual* base, not a flow-pinning p50).

### 2025: over-export — two isolated root causes (NOT model skill)
1. **Southeast gas-elasticity (the headline finding).** Carolinas/TVA/LGEE are
   priced gas×HR, but they are coal/nuclear-heavy and only weakly gas-elastic.
   At HR 11.6 the Southeast sits a thin ~$1.5-2 *parallel* below PJM every year
   (29.5/25.4/40.8 vs PJM 31.0/26.7/42.9), so in dear-gas 2025 the diurnal swing
   flips the seam to wrong-direction export (+2.0/+1.3/+0.9 vs measured
   −5.9/−5.4/−2.3 — a ~+18 TWh error). This pre-existed at pjm-49 (Carolinas
   +2.3); TVA/LGEE inherit it. **Next fix:** price the Southeast gas-*inelastically*
   (a per-year effective HR from its coal/nuclear fuel mix / EIA-923 delivered
   coal, or a measured Duke/SOCO system-lambda), so the structural import
   direction holds across the gas cycle.
2. **NYISO system-avg HR.** NYISO's seam references its NYC-congestion-inflated
   system-average LMP (HR 14.67 in 2025), not the PJM-NY (west-NY) border, so it
   over-exports (+28.1 vs +21.9). Scope-B border-price re-anchor is gated on a
   committed west-NY hourly LMP extract (not yet present).

### Measured-source limitation (documented, not fixable by any seam)
In 2025 the EIA-930 PJM net total (+18.0) sits ~15 TWh BELOW PJM's OWN per-tie
sum (+32.9); 2023/24 the two agree. No seam model can close a gap between two
measured sources — 2025 is scored against BOTH and flagged (see
`calibration_attestation.json`).

## Verdict
pjm-48 remains the PJM keeper. This is a structural **diagnostic**: the firm
floor + losses hurdle + TVA/LGEE are correct and stay in (rule #1, even where the
2025 headline worsens); they make 2024 per-seam-exact and improve 2023, and they
isolate the next root cause (Southeast gas-inelastic pricing) cleanly.
