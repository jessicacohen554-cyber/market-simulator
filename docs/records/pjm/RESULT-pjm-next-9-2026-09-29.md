# RESULT — PJM-NEXT-9: the east→south boundary identified and recorded as a model-class limit (zero LP), 2026-09-29

**Keeper unchanged:** `2026-09-28-pjm-next8-exitfix` (bundle `results/calibration/pjmnext8_xf_span`). **No LP solved, no shard launched, nothing registered or promoted.**

## Card 1 — CC_REGULAR 2023 (the only training-span failure)

Detail: `docs/records/pjm/FINDING-pjm-next-9-east-south-boundary-2026-09-28.md`.
- **Method.** PJM's DA binding-constraint record for 2019–2025 (re-fetched, gitignored) regressed onto DA hub congestion spreads. R² is 0.90–0.98.
- **Result.** The missing boundary is the **Peach Bottom / Conastone corridor** (PECO/PPL → BGE): Nottingham 230 kV 2-3, Graceton–Safe Harbor and Conastone–Northwest.
  - It carries **35–91 % of NJ–Western congestion in every year**.
  - 2023: 91 %, with Nottingham binding 5,341 h.
- **Same object in other years.** It explains CC_REGULAR 2019 / 2020 / 2022 / 2023 (EMAAC / Central_PA over, Dominion / SWMAAC under).
- **Not buildable.** PJM publishes no MW limit for this corridor: it is a single 230 kV facility, and BC/PEPCO is not posted. Sizing a cut from binding frequency or prices is refused under rules 1 and 13.
- **Owner card:** *"Record as limit; go card 3"*. Matrix cell `internal_congestion_split` PJM `.` → `G`.

## Card 2 — 2019 CC_REGULAR +10.86 / C3a +11.8 %

This is the same zonal signature as 2023: EMAAC +11.2, Central_PA +7.8, Dominion −8.4, SWMAAC −3.7 TWh. Card 1 covers it, and it is not a 2019-specific input.

## Card 3 — COAL_BIT / CT_PEAKER (zero-LP phase 0 only)

Monthly model − EIA-923 on bench plants (TWh):

| | COAL_BIT | CT_PEAKER |
|---|---|---|
| 2019 | +19.0 | −4.0 |
| 2021 | +15.4 | −9.1 |
| 2022 | +8.5 | −6.9 |
| 2023 | +0.3 | −2.3 |
| 2025 | +13.0 | +3.8 |

- **The coal over-run is a flat level offset:** +0.6 to +3.0 TWh in nearly every month, not seasonal. It is loading within synced capacity (FINDING-pjm-next-7 §2), in AEP_Ohio and West_APS.
- **It is not monotone in the gas price** (2022, the highest-gas year, is smaller).
- **Where it leads:** the coal offer-band basis lineage (pjm-h5 → h9c: `committed_band_measured_basis` `R`; the mustrun band named in pjm-h8 as the unexamined band, 4× further from the PJM offer basis).
- **No measured operand identified this session**, and no card was put to the owner because nothing solvable was found. It is handed on.

## Retrievability (rule 34(e))

Nothing was solved. Probe `scripts/probes/_pjmnext9_congestion_boundary.py` and output `results/phase0/pjm/_pjmnext9_congestion_boundary.json` are on `main` via this lane's PR.

## Next (PJM-NEXT-10)

1. **COAL_BIT level offset** (2019 / 2021, plus the 2025 +11.3 that sits inside its band). Zero-LP phase 0: per-plant loading vs CAMPD by year, and the mustrun band's basis vs PJM's own offers (pjm-h8 named successor). Present a design card before any solve. Do NOT re-test `committed_band_measured_basis` (`R`).
2. **CT_PEAKER 2021 −9.6.**
3. **C3a 2020 / 2022, C3b 2022.**
4. **Every-year fossil surplus** (+5 to +13 TWh net, 2019–2025 except 2024): check net interchange vs actual.
