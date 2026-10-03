# FINDING — NWPP-NEXT-25 phase 0 (CC pivot): the served schedule lands in the wrong zones

Owner card 2026-10-03 "Pivot to CC/C4 gas": the C3a tail-day lane closed with no lever
(FINDING-nwppnext25-scarcity-phase0). This file is the zero-LP phase 0 for handoff task 2: the CC_REGULAR
2019/2024 over-run and C4 gas. Probes: `scripts/probes/_nwppnext25_served_schedule_phase0.py` and this
session's scratch decomposition, reproduced in §A. Keeper: `2026-10-03-nwpp-next-24-head`.

## A. Where the over-run sits (keeper, model vs measured)

- **By plant (EIA-923 CC prime movers, same plant set).** In 2024 the model runs 71.81 TWh against 62.49 measured.
  - The long plants are all in SNV and EAST: SNV +8.31 TWh, EAST +3.13 (2024).
    - SNV: Harry Allen 55322 +1.88, 55687 +1.29, 55514 +1.18, Clark 2322 +1.14, 55841 +1.05, 2336 +0.81, 7082 +0.51.
    - EAST: Lake Side 56237 +2.07, Currant Creek 56102 +1.09.
  - NW runs short (−2.35). 2019 and 2025 show the same pattern: SNV +7.76 / +5.29, EAST +2.00 / +2.79.
- **By BA (EIA-930 NG:NG).** Model zonal gas is SNV 31.3 / 32.3 TWh against NEVP 22.2 / 21.7, and EAST 10.6 / 15.4 against
  PACE 9.7 / 11.7 (2019 / 2024). The SNV excess runs Jun–Oct at +1.3–1.6 TWh/month.
- **The exports (TWh).** COI is 10.42 model against 2.15 measured and BC 13.25 against 7.51 (2024). NEVP is 9.50 against −0.30
  (2019). The sum of the excess matches the CC excess.
- **Units run flat out.** CC sits at 0.87–0.91 of available capacity at night, with mc $16–22 under a $29 price.

## B. The defect

Under the priced seams (NEXT-20, owner card "Schedule as residual") every unpriced counterparty is served at its
measured flow: `envelopes.nwpp_unpriced_residual_interchange`. That covers LDWP via PDCI and NEVP, WALC, AZPS, WACM,
PNM, SRP, BANC, AESO, GWA/WWA and SWPP.

`load_demand` then spreads that scalar over the five zones **by load share**. Physically each leg lands at the
member BA that reports it on its own EIA-930 per-DIBA file:

- NEVP imports 9–10 TWh/yr from LDWP and WALC, which is SNV;
- PACE imports from WACM and AZPS, which is EAST;
- BPAT exports over PDCI to LDWP and to BANC, which is NW;
- GRID exports to PNM, SRP and WALC, which is OR.

The spread hands SNV and EAST almost none of their imports. Their own CCs fill the gap. NW and OR are relieved of
exports they really carry, and their surplus leaves through COI and BC.

The same placement is already made for ERCOT (`ercot_tie_zonal_interchange`) and PJM (`pjm_zonal_interchange`).
NWPP was the one region whose served schedule had no zonal attribution.

## C. Zero-LP shift in each zone's local generation need

Measured legs at the member's zone minus the load-share spread. The remainder keeps the spread; column sums are
unchanged.

| year | NW | OR | INLAND | EAST | SNV |
|---|---:|---:|---:|---:|---:|
| 2019 | +14.20 | −2.34 | −2.66 | −3.53 | −5.67 |
| 2020 | +14.17 | −1.73 | −2.28 | −1.70 | −8.46 |
| 2021 | +11.94 | +4.83 | −1.66 | −2.89 | −12.23 |
| 2022 | +13.54 | +5.16 | −1.42 | −4.41 | −12.87 |
| 2023 | +9.56 | +8.02 | +0.19 | −6.64 | −11.14 |
| 2024 | +8.58 | +10.10 | −0.87 | −5.80 | −12.02 |
| 2025 | +6.68 | +9.25 | −2.27 | −2.75 | −10.91 |

- **2019–2022.** BC (`WECC_CAN`) is unpriced before its 2023 anchor, so BPAT's BCHA leg is a served leg placed at NW.
  The 2019–2022 legs of NEVP, PACE, NWMT and WAUW come from this session's keyless back-fill
  (`data/raw/eia-930-interchange/SOURCES-NWPP.md`). The Mountain members are read on their own clock: PACE→NEVP
  mirrors −(NEVP→PACE) at 0.0 MW at +1 h.
- **SNV.** The shift (−10.9 to −12.9 TWh, 2021–2025) has the sign and size of SNV's gas excess against NEVP EIA-930
  (+6.6 to +10.6).
- **EAST.** 2021–2022 already sit below PACE (6.5 / 2.7 against 10.7 / 11.3 TWh). The shift pushes EAST's need further
  down in those years. The LP decides what fills it, and the result reports it at full magnitude.

## D. Admissibility

- **Rules 13 and 14.** No new flow is pinned. The keeper already serves this schedule. The key only stops spreading a
  measured quantity away from where its ties land. The measured per-counterparty legs replace a spread that ignores
  location.
- **Free parameters.** Zero: the zone of each member is `zone_assignment._NWPP_BA_ZONES` and the clock is measured.
- **Rule 19.** A priced seam's legs are skipped in their priced years, so each counterparty is priced or scheduled,
  never both.
- **Forward story.** That of the priced seams: a forecast year has no served schedule, and the key raises outside the
  priced-seam path.

## E. Expected direction

- SNV and EAST CC fall, and NW/OR serve the PDCI, BANC and SW exports locally. COI and BC exports fall by the NW
  surplus the spread was creating.
- Footprint CC_REGULAR should fall where the SNV and EAST cuts exceed the NW increase. NW's increase is met first
  from fewer exports and from hydro shaping.
- Risks: EAST 2021–2022 short; NW CC up; the C4 gas shape. All reported at full magnitude.
