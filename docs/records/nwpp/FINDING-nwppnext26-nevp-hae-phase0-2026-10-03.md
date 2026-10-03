# FINDING — NWPP-NEXT-26 phase 0: the CAISO_NEVP seam is priced before its path existed

Keeper `2026-10-03-nwpp-next-25-served` (bundle `results/calibration/nwppnext25_span`, legs at `d3965589`). Zero LP
throughout. Handoff task 1 (the NEVP seam, 2019–2022) found a lever; tasks 2 (CC supply side) and 3 (D-1) were not
reached and are routed to NEXT-27.

## A. The measured NEVP book

NEVP's own EIA-930 per-DIBA file (`data/raw/eia-930-interchange/NEVP interchange hourly.parquet`), TWh, export-positive:

| DIBA | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| CISO | −0.30 | 3.11 | 8.60 | 8.56 | 7.56 | 9.18 | 9.45 |
| LDWP | −5.05 | −6.85 | −8.60 | −9.19 | −8.66 | −9.34 | −7.50 |
| WALC | 1.71 | 0.39 | −2.60 | −2.52 | −3.14 | −2.82 | −2.58 |
| PACE | −1.75 | −1.65 | −2.79 | −2.46 | −0.79 | −0.61 | −1.99 |
| IPCO / BPAT | −0.94 | −1.54 | −1.14 | −1.08 | −0.34 | −0.29 | −0.56 |
| **NEVP net** | **−6.35** | **−6.55** | **−6.53** | **−6.69** | **−5.37** | **−3.87** | **−3.18** |

- NEVP is a steady ~6.5 TWh net importer in 2019–2022. Only the split moves.
- CAISO's own book shows the mirror image: CISO←LDWP falls 18.65 → 11.73 TWh from 2019 to 2021, while CISO←NEVP rises
  −0.31 → 8.60.

## B. The step is a transmission in-service date

NEVP→CISO hourly, MW:

| period | min | max | mean |
|---|---:|---:|---:|
| 2019 | −416 | 366 | −35 |
| 2020-01-01 … 2020-08-11 | −510 | 340 | — |
| 2020-08-12 | — | 1,029 | 95 |
| 2020-08-13 | — | 1,234 | 880 |
| 2021 | −254 | 1,780 | 982 |
| 2024 | −198 | 1,933 | 1,046 |

- The first hour above the pre-period maximum is 2020-08-12 18:00 local, at 459 MW. By the next day the leg runs
  ~900 MW mean, and it has stayed there every year since.
- **Cause.** The FERC filing ER20-1514 (CAISO, 2020-04-08) is Amendment No. 5 to the CAISO–NEVP Adjacent Balancing
  Authority Operating Agreement. It adds "the 500 KV transmission line from NEVP's Harry Allen Substation … to the
  Eldorado Substation, which creates a new intertie between NEVP's balancing authority area and the CAISO's". This is
  DesertLink's Harry Allen–Eldorado line. The filing gives an anticipated energization date of April 30, with the
  effective date "to coincide with the actual in-service date". The measured step dates it to 2020-08-12.
- The nine pre-existing interties in Schedule A are local-supply ties: Mohave–Laughlin 500 kV, which supplies the
  Laughlin load; the Eldorado 220 kV positions; Amargosa–Sandy Valley 138 kV; and so on. Before HAE, NEVP's
  California sales were scheduled on LDWP's book, the measured LDWP legs in §A.
- **The registered rating.** `CAISO_NEVP` is registered at 1,933 MW, "the measured NEVP->CISO hourly maximum"
  (`model/interchange/spec.py`). That is the 2024 maximum over the HAE intertie, and the rating applies to every year.

## C. What the keeper does with it

The keeper's P1 flows are from the NEXT-25 leg branches.

| | 2019 | 2020, Jan 1–Aug 11 | 2024 |
|---|---:|---:|---:|
| NEVP seam export, TWh | 10.47 | 7.17 (11.98 for the whole year) | 10.13 |
| above the pre-HAE envelope (> +366 MW), TWh | **8.94** | **5.86** | n/a |
| hours at the 1,933 MW limit | 4,829 | 3,151 | 5,596 |
| measured NEVP→CISO, TWh | −0.30 | — | 9.18 |

- **What 2019 shows.** The LP sells SNV's surplus CC energy to CAISO at CISO's net-load price for 4,829 hours, through
  a path that did not exist. This is the "SNV's freed capacity leaves through the NEVP seam" of RESULT-nwppnext25.
- **Against the over-runs.** 8.9 TWh is 70 % of the 2019 CC_REGULAR over-run (+12.73). In 2020 the gap is 5.9 TWh
  against +7.51.
- **2021–2025.** The seam rating is the real one. 2024 exports 10.13 TWh against 9.18 measured, so this is not the
  2024 over-run, which sits at COI (+6.8) and BC (+3.9).

## D. The lever: `nwpp_seam_in_service_vintage` (owner card 2026-10-03, "Serve pre-HAE")

- **How it works.**
  - `constants.NWPP_SEAM_IN_SERVICE_UTC = {"CAISO_NEVP": "2020-08-12 07:00:00"}`. That is local midnight PDT, as UTC
    hour-ending.
  - `envelopes.nwpp_seam_priced_hours` returns one hourly mask.
  - Before the in-service instant, the seam's measured CISO leg stays in the served schedule
    (`nwpp_unpriced_residual_interchange`), and NEXT-25's attribution places it at SNV.
  - In those same hours, `run_calibration.run_year` caps the seam's net flow at zero with an aggregate interface group
    (`build_seam_limit_groups`).
  - After the instant, the cap is the registered 1,933 MW, which the bands already sum to.
- **Rule 19.** One mask partitions the year, so each hour is either priced or served, never both. This is the
  anchored-years construction (`WECC_CAN` before 2023) applied by the hour.
- **Rules 13 and 14.** The in-service date of a physical element is a measured input. The served leg is the keeper's
  existing served-schedule construction, so no new flow is pinned. The arm adds no number.
- **Forward story.** Every forecast hour is after the date. The runner refuses the key, because only `run_year` builds
  the cap.
- **Zero-LP construction.**

  | | 2019 | 2020 | 2021–2025 |
  |---|---|---|---|
  | NEVP priced hours | 0 | 3,409 | 8,760 |
  | served residual, TWh | −1.96 → −2.27 | 4.27 → 4.04 | unchanged |
  | SNV demand, TWh | −0.30 | −0.23 | unchanged |

  - In 2019–2020 the other zones are unchanged to ±0.01 TWh.
  - In 2021–2025 demand and caps are identical to the keeper, so those five shards are byte-identity controls.
- **The rejected alternative.** The other option was to cap the seam at the pre-HAE measured extremes (+366 / −510 MW).
  It keeps two flow-derived numbers and still leaves up to 3.2 TWh/yr of priced export.

## E. Expected direction (ex ante; PRECOMMIT)

- **SNV.** In 2019 SNV loses up to 10.8 TWh of exports: the model's 10.47 export against the measured 0.30 import. The
  share that re-routes is bounded by NW/OR's COI headroom and the 600 MW and 300 MW internal SNV links. The SNV CCs
  (Harry Allen, Clark, Silverhawk, Chuck Lenzie) fall, and SNV gas moves toward NEVP EIA-930 (2019: 29.58 model,
  22.2 measured).
- **Predictions.**
  - CC_REGULAR 2019 falls by 4–9 TWh (+12.73 → +4…+9), and 2020 falls by 2–5 TWh.
  - C4 gas 2019 r is likely to rise.
  - Price 2019–2022 is unscored (R-9).
- **Risks.**
  - COI exports rise in 2019 if NW/SNV surplus finds that path.
  - CT_PEAKER and ST_GAS in SNV may change.
  - D-1 diurnal shapes in SNV.
  - Every regression is reported at full magnitude.

## F. Not reached (routed to NEXT-27)

- **The 2024 over-run (+12.77).** 2024 exports at COI run 8.97 TWh against 2.15 measured, and at BC 11.36 against
  7.51. Remaining questions: the COI/BC level, CC availability (CAMPD outages), heat rates and per-plant delivered gas
  basis. The CLOSED list in the HANDOFFs applies. In particular, `wefor_residual` is O, and no CC-specific availability
  lever has been adjudicated.
- **D-1 13 → 16** (2019 COAL_BIT, 2022 CT_PEAKER, 2022 ST_GAS). Not read this session.
