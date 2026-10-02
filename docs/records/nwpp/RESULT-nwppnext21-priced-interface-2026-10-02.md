# RESULT — NWPP-NEXT-21: the priced interface (NWPP-56) on keeper #20, 2019–2025

PRECOMMIT: `PRECOMMIT-nwppnext21-priced-interface-2019-2025-2026-10-02.md`. The run was scored as probe
`2026-10-02-nwpp-next-21-priced`, on bundle `results/calibration/nwppnext21_span`, composed locally from the seven shard legs.

**Owner card 2026-10-02: "Hold #20, fix seam headroom".** Keeper #20 stays. The probe registration is withdrawn
(rule 15). The span was never committed, and the leg SHAs below are its provenance (rule 33).

## Legs

All seven legs are parented on pin `86b73d6f910d4b3a179f6158727b5e31b5f8c265`. The replay is keeper #20's own leg
with `--set reference_price_interface=true --set priced_interchange=true`.

| year | leg SHA | demand frame TWh (native + residual) |
|---|---|---:|
| 2019 | `4d6cb87ed4af3961caf6cef03db27c5bd62bf143` | 272.855 |
| 2020 | `7cdb53da881b400ee9f3406d610fefa181a5bed4` | 274.573 |
| 2021 | `542733eaef5b5232e3d02a5c9a83197a6ddef473` | 268.646 |
| 2022 | `876d4faa32cf580848b4fa763ea51b319ad96932` | 277.900 |
| 2023 | `3f52175627fcda2c1cf1c3b093ea96929413319c` | 262.091 |
| 2024 | `8ffeaed04b7bdf5a1c79b794f6f9121574ab772c` | 271.477 |
| 2025 | `3d36a7b093469538892363af1a7d0ce2d6f8fbf1` | 287.331 |

Every hard stop passed in every leg, and the parent re-verified each one:

- The `scenario_config` diff is exactly `reference_price_interface`, and `meta.json` records `priced_interchange` and
  `reference_price_interface` both True.
- There are three external zones, with 32 rows in 2019–22 and 48 in 2023–25.
- The residual equals the PRECOMMIT table, and demand is exact.
- There is no slack or dump in any external zone. The dangling 2019–22 `NWPP_ext_BC` link carries 0.

The 2023 solve took 29 min, with a 5.06 GiB peak.

## Gate (a), structural STOP: PASS

Net flows in TWh, export-positive, model / measured; r is the hourly correlation with the measured leg.

| seam | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| COI net | 19.55 / 7.03 | 23.99 / 15.26 | 24.98 / 12.11 | 24.65 / 12.50 | 4.69 / 1.13 | 17.38 / 2.15 | 10.25 / 3.03 |
| COI r | 0.675 | 0.576 | 0.575 | 0.645 | 0.438 | 0.543 | 0.567 |
| NEVP net | 8.13 / −0.30 † | 9.35 / 3.11 | 10.26 / 8.60 | 8.00 / 8.56 | 3.06 / 7.56 | 8.43 / 9.08 | 4.86 / 9.40 |
| NEVP r | 0.125 | 0.117 | 0.443 | 0.449 | 0.186 | 0.311 | 0.432 |
| BC net | unpriced (0) | unpriced (0) | unpriced (0) | unpriced (0) | 22.48 / 9.48 | 10.97 / 7.51 | 2.00 / 2.77 |
| BC r | | | | | 0.129 | 0.355 | 0.443 |

† NEVP 2019 is the near-zero leg the PRECOMMIT exempted from the sign test. Every other priced (seam, year) has the
measured sign, and every r is > 0.

**Magnitude, the real finding.** The priced seams export 27.7 / 33.3 / 35.2 / 32.7 / 30.2 / 36.8 / 17.1 TWh against
6.7 / 18.4 / 20.7 / 21.1 / 18.2 / 18.7 / 15.2 measured. Examples: COI 2024 runs 8×, and BC 2023 exports 8,700 h at the
limit.

## Gate (d): the BC↔CA wheel

Hours with COI importing and BC exporting at the same time: 3,034 h (6.04 TWh) in 2023, 1,691 h (2.51 TWh) in 2024,
and 2,113 h (2.54 TWh) in 2025. In 2019–22 BC is unpriced, so there are 0.

## Gate (b): verdict diff against keeper #20, per (criterion, year, key)

Both runs are scored under today's rubric. R-9 landed after NEXT-20, so keeper #20 now scores price in 2023–25
against the WEIM ELAP benchmark. **Both runs are NOT-YET**, with fuelmix, price_mean, price_shape and dispatch_corr
failing.

| record | keeper #20 | NEXT-21 | |
|---|---|---|---|
| C4 coal 2023 | r 0.669 / NRMSE 0.313 FAIL | **0.781 / 0.288 PASS** | gain |
| C3a price mean 2023 | −21.4 % FAIL | **−0.3 % PASS** | gain |
| C3b price shape 2023 | NRMSE 0.303 FAIL | **0.182 PASS** | gain |
| C1 CC_REGULAR 2025 | +9.60 TWh FAIL | +7.50 TWh PASS | gain |
| C4 gas 2019 | 0.731 / 0.232 PASS | **0.621 / 0.392 FAIL** | regression |
| C4 gas 2020 | 0.813 / 0.181 PASS | **0.754 / 0.365 FAIL** | regression |
| C4 gas 2022 | 0.864 / 0.184 PASS | **0.705 / 0.350 FAIL** | regression |
| C4 gas 2023 | 0.781 / 0.181 PASS | **0.465 / 0.417 FAIL** | regression |
| C4 gas 2024 | 0.894 / 0.125 PASS | **0.739 / 0.386 FAIL** | regression |
| C1 CC_REGULAR 2019 | +1.10 TWh PASS | **+10.92 TWh FAIL** | regression |
| C1 CC_REGULAR 2020 | +1.67 TWh PASS | **+9.67 TWh FAIL** | regression |
| C1 CC_REGULAR 2024 | +6.60 TWh PASS | **+12.47 TWh FAIL** | regression |
| C3a price mean 2024 | −27.7 % FAIL | −20.8 % FAIL | |
| C3b price shape 2024 | NRMSE 0.676 FAIL | **0.787 FAIL** | worse |
| C3a 2025 | +2.6 % PASS | +5.9 % PASS | |

The CT_PEAKER forced-share records for 2019, 2020 and 2022 move from SKIPPED (immaterial) to PASS at 0 % forced,
because CT is now material.

**Root cause, stated (gate (b)).** Every regression is gas filling the excess seam export.

- Each seam offers its full path rating (COI 4,800, NEVP 1,933, BC 3,150 MW) as merchant capacity against a measured
  counterparty price. The measured exchange uses a fraction of that.
- CC_REGULAR (keeper → arm / actual, TWh): 51.1 → 60.9 / 50.0 (2019); 63.5 → 69.4 / 56.9 (2024).
- CT_PEAKER: 0.98 → 6.88 / 2.87 (2019); 4.50 → 11.65 / 7.39 (2024). That is 1.5–2.4× actual in every year.
- Gas hourly fit falls because NW gas now follows the CAISO net-load price shape on the seam.
- Coal barely moves in volume. The coal 2023 clear is hourly shape: the NW price now has within-day structure.
- ST_GAS moves toward actual (2024: 0.89 → 4.25 / 4.62).

## Gate (c): rule 20 and legitimacy

- D-2 forced energy PASS in both runs, and C6 governance PASS.
- D-1 diurnal failures fall from 22 (keeper #20) to 14. The remainder are coal-class rows, mostly COAL_WC, which is
  immaterial at 0.4 TWh.
- CT_PEAKER volume is as stated above. The NEXT-19 §3 expectation of 2–2.7× was met.

## Headroom evidence for the next lever (zero LP, read this session)

CAISO OASIS `TRNS_USAGE` DAM (`data/raw/caiso-trns-usage/`, 2023–25, already curated into the
`transfer-interface-limits` clean datatype) gives CAISO's own scheduling limits. Annual means:

| tie (import into CAISO) | seasonal TTC | hourly OTC | DAM net schedule |
|---|---:|---:|---:|
| MALIN500_ISL (COI, CAISO share) | 3,007 / 3,129 / 3,351 | 2,737 / 2,732 / 2,717 | 713 / 823 / 864 |
| COTPISO_ITC | 87 / 128 / 161 | 81 / 116 / 133 | 17 / 52 / 33 |
| NOB_ITC (PDCI; not in CAISO_COI) | 1,622 | 1,337 / 1,438 / 1,414 | 370 / 397 / 412 |

The registered CAISO_COI limit (4,800 MW) is Path 66's full rating. CAISO's market sees about 2,730 MW of it after
derates. The rest is COTP / TANC capacity scheduled outside CAISO's market, which bears on N4.

A measured hourly OTC is an operating-condition input of the same kind as an outage window. That makes it admissible
under rule 13, as a backcast overlay with a forward analogue (the seasonal TTC). It is not a fit to flow.

## Reading and ruling

The mechanism forms price the right way:

- the 2023 price level and shape clear;
- the coal 2023 shape clears;
- the seam signs and hourly correlations hold.

But the seam volume is 2–8× measured, because the limit is the full path rating, not what the market actually has.
The gas regressions are that construction, not the mechanism. **Owner card: hold keeper #20 and fix the seam headroom
first** (matrix cells `reference_price_interface` / `priced_interchange` = **O**: open, in play, no verdict yet). NEXT-22 starts at zero LP from the
OTC evidence above.
