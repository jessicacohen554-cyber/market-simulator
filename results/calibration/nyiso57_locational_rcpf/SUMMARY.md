# nyiso 57 locational-rcpf — SOM primary-source grounding of NYISO_RCPF_LOCATIONAL

**Run id:** `2026-07-07-nyiso-57-locational-rcpf` · **PROBE / keeper-quality
grounding** (C6 unattested). Years 2023/2024/2025. Single-delta replay of the
`nyiso-56-measured-zonal` recipe (measured U3 zonal shares + LI-TSL + v2 CO2
rates + downstate CT gas) — the **only** change is the primary-source-corrected
`NYISO_RCPF_LOCATIONAL` in the live `energy_reserve_coopt` path.

## The change (rule 12/13 grounding)

From the NYISO State-of-the-Market report, in-repo (`data/raw/NYISO/NYISO-
{2023,2024,2025}-SOM-*.pdf`), identical across all three years (2024 p.297):

| Product | placeholder | **SOM (primary)** |
|---|---|---|
| East | 30-min, 1,200 MW, $500 | **10-min, 1,200 MW, $775** |
| SENY | 1,100 MW, $500 | **≥1,300 MW**, $500 |
| NYC 30-/10-min | $500 | **$25** |

Closes the `TODO(SENY-MW)` main left open and fixes three wrong entries. The
10-min East now draws only quick-start {gas_ct, oil} headroom (the downstate F–K
peaker fleet). Live in the co-opt: 7 families, **4** quick-start, ORDC $3–$775.

## A/B vs nyiso-56-measured-zonal (official DA-expressible scorer)

| criterion | nyiso-56 | **nyiso-57** |
|---|---|---|
| price_mean | CAVEAT (2023 $31.59) | CAVEAT (2023 **$30.76**, closer to $30.29) |
| price_shape | CAVEAT (2024 0.20) | FAIL (2024 0.20 — boundary flip) |
| price_tail | FAIL (2023 21 h vs 1 DA) | FAIL (2023 **15 h**, less over) |
| determination | NOT-YET | NOT-YET |

RT basis: 2023 C3a **−4.2%** (mean $29.0 vs $30.3), 2023 tail 8 h vs actual 10,
2025 7 h vs 42. The placeholder $500 NYC penalty was over-firing (baseline 2023
21 h); the SOM $25 pulls it toward actual. The deep 2025 tail is the **#1344**
condition-varying-requirement residual (Ask-B, data-blocked) for both.

## Disposition

Grounding, not a scorecard win — the values are now the published truth, not
placeholders. Determination NOT-YET (governance unattested; price_shape/tail the
standing NYISO frontier). Keeper `nyiso-56-measured-zonal` unchanged pending owner
adjudication on faithfulness (rule 1). Reproduce:
`scripts/replay_keeper.py results/calibration/nyiso56_measuredshares --out-dir <dir>`
at this HEAD (SOM-corrected `NYISO_RCPF_LOCATIONAL`).
