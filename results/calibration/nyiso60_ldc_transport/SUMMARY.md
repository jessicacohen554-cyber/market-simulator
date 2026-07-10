# NYISO 60 — G-13 fold-in: per-zone daily LDC-transport delivered gas (keeper combination) — KEEPER CANDIDATE

The `2026-07-10-nyiso-59-dynamic-rr` keeper recipe VERBATIM with exactly one
change, a **measured-data** swap (rules 12/13, zero new free parameters): the
downstate CT-peaker delivered-gas index moves from the v1 monthly statewide
citygate premium (`nyiso_downstate_ct_gas_basis`: EIA N3050NY3 − Transco Z6 NY,
floored 0) to the **measured per-zone DAILY LDC-transport delivered index**
(`nyiso_downstate_ct_gas_daily`; the `nyiso-downstate-gas` curated datatype v2):

```
delivered_gas[zone][day] = Transco Z6 NY daily spot + LDC monthly non-firm transport rate[zone]
```

- **NYC** → KEDNY SC-22 C&G Non-Firm Transportation, Tier 1 (published statnfdr)
- **Long_Island** → KEDLI SC-19 Non-Firm Demand Response Transportation, Tier 1

This is nyiso-55's G-13 mechanism folded into the keeper line: the
interruptible LM6000 peakers are **transport** customers (commodity at the
market hub + a published tariff delivery charge), not firm-sales citygate
customers, and the LI gas island vs the NYC system carry materially different
delivery costs. The daily hub leg prices the cold-snap blowouts (Jan-2024
$23.90; **2025-01-17 $97.90**) on the exact days the peakers run — the monthly
mean smears them away. One mechanism per phenomenon (rule 19): v1 OFF, v2 ON —
superseded, not stacked. Engagement: 105 downstate CT_PEAKER units repriced per
year; delivered ranges 2.45–30.84 (2023), 2.76–26.52 (2024), 4.18–100.87
(2025) $/MMBtu.

## Result (vs the nyiso-59 keeper, v2.4 lw price basis)

Metrics a **wash-to-slightly-better**; the 2025 monthly shape crosses INTO the
band (one ledgered caveat drops); the scarcity tail is unchanged:

| metric | keeper nyiso-59 | nyiso-60 | actual |
|---|---|---|---|
| C3a 2023 / 2024 / 2025 | −4.8% pass / −13.2% / −15.7% | −4.8% pass / −13.2% / **−13.7%** | ±10% band |
| C3b NRMSE 2023 / 2024 / 2025 | pass / 0.221 / 0.215 (ledgered) | 0.163 / 0.223 / **0.199 PASS** | ≤0.20 band |
| C3c >$300 h 2023 / 2024 / 2025 | 23 / 1 / 25 | 23 / 1 / 25 (identical) | RT 10 / 12 / 42 (DA 1 / 0 / 12) |
| C5a CO2 2023 / 2024 / 2025 | — / clears / +8.6% | +3.3% / +2.5% / +8.1% (commercial) | ±7% target / ±10% commercial |

C1 fuel-mix **14/14 PASS** all years (free 10/10), C2 PASS, C4 PASS, C7 PASS
(ST_GAS D-1 r 0.950–0.957, cv_ratio 0.681–0.902), **C8 clean PASS** via the
v2.2 grounded-above-budget escalation (ST_GAS `reliability_floor`
32.1/44.0/36.0% forced — all inside the declared D-4 window, off-window 0.0%;
keeper read 30.3/44.5/38.0%). The C3a-2025 2.0 pp improvement and the
C3b-2025 band entry are the daily index pricing the Jan/Feb-2025 arctic-blast
months the monthly premium could not.

**Determination: CALIBRATED-WITH-CAVEATS** (same as keeper; 3 ledgered price
criteria — C3a 2024/2025, C3b 2024, C3c 2023/2025 — plus the C5a-2025
commercial-band auto-caveat). Rule 1: kept and promoted on its measured basis
(per-zone daily measured delivered index > monthly statewide stand-in — the
exact promotion logic of nyiso-56's measured load shares and nyiso-59's
measured hourly requirements), not on residual movement. Zero-forcing ablation
twin registered alongside (`2026-07-10-nyiso-60-ldc-transport-ablation`;
floors-off prices sit HIGHER — simple means 32.20 vs 29.05 (2023), 35.07 vs
31.96 (2024), 60.09 vs 54.08 (2025) — and the 2023 tail max ($2,000) is
present in both arms: the floors force cheap steam-base energy, they do not
manufacture the level or the tail; the tail is the measured requirement's
reserve duals plus the measured daily delivered gas).

## Reproduce

CI replay of this recipe OOMs GitHub-hosted runners in `regenerate_clean`
(nyiso-59 lineage, 4 attempts 2026-07-10); solve locally with ≥15 GB + swap:

```
python scripts/regenerate_clean.py
python scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso60_ldc_transport \
  --iso NYISO   # in-place re-solve; add --zero-forcing-ablation + --out-dir .../nyiso60_ldc_transport-ablation for the twin
```
