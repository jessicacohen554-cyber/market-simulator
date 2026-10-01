# capx D61 — PJM State of the Market sources fetched (VALIDATION OBSERVABLES, rule 13 — nothing here enters the model)

Monitoring Analytics, *PJM State of the Market* annual reports, per-section PDFs at
`https://www.monitoringanalytics.com/reports/PJM_State_of_the_Market/<year>/<year>-som-pjm-sec<N>.pdf`,
fetched 2026-09-05 and parsed from the PDF text. Every figure quoted in
`FINDING-capx-d61-2026-09-05.md` is read from these files (table numbers cited in the finding).

| file | sha256 |
|---|---|
| 2021-som-pjm-sec7.pdf | 0c65725436bf5473e63aab32854afdf52333f219fbaa1dea2e81f5315c600aad |
| 2022-som-pjm-sec4.pdf | f8ad1b71882f312a795fce3932973b5f0e64c84943d59d5a984539266575f48a |
| 2022-som-pjm-sec5.pdf | 051a2793270b3363d213fb2e1be000631a3e1d8855ec3641f75d45e06706b614 |
| 2022-som-pjm-sec7.pdf | daeb78f6168f3de4e0812b19987c47fddf4e0b8e1ce35d5d5f66b346a3f83895 |
| 2022-som-pjm-sec10.pdf | 3b04608f5b2ed89e8f803799915a671ce10056ec6caa42a43770128db187eabd |
| 2023-som-pjm-sec4.pdf | 8948169a0ac96fff3d2f107240321e48331150886b17b0cc8a81bfde52de0b70 |
| 2023-som-pjm-sec5.pdf | 098beec520811d174a73102501864dd9001d55092808713bc86b91f03ed50e04 |
| 2023-som-pjm-sec7.pdf | ecbe23f5dc76ac8c56c2b6927aec726c3d3f899e2504dd4203487c5515170c5d |
| 2023-som-pjm-sec10.pdf | b33ef52e06fc63c592ecad294f6894a891f336e672350c770178d7cb6faa3c59 |
| 2024-som-pjm-sec4.pdf | 97249e337abfdb4153de7da4b4bbdae0c59615a2355aeff2227071f4006e6fdb |
| 2024-som-pjm-sec5.pdf | 45b31316e4633e4b5db2ca9f1adb3e79e7ff645714cb7de10cc047ecb74225d1 |
| 2024-som-pjm-sec7.pdf | e34e6a9950ac66a2d7304d2cf0e9bcb984d205ef6eeae1551f9757b7e530522f |
| 2024-som-pjm-sec10.pdf | cdc93469e3a7f22ff6b63b18b6a280895f7d1f7c987690ac39a9b6fcaec2a53b |

## Existing-unit net revenue by class — Table 7-36 (2021) / 7-40 (2022–2024), $/MW-yr

"Energy and ancillary service net revenue" = DA + balancing energy revenue − SRMC + DA/balancing
operating-reserve (uplift) credits + actual unit credits for regulation, synchronized reserve,
black start and reactive (the section text preceding each table). Median of the class; Q1/Q3 in
the finding where used. Capacity revenue = unit-specific RPM revenue net of performance penalties.

| class | 2021 E+AS med | 2021 cap med | 2022 E+AS med | 2022 cap med | 2023 E+AS med | 2023 cap med | 2024 E+AS med | 2024 cap med |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Combined cycle | 27,779 | 40,923 | 83,538 | 19,889 | 55,088 | 24,364 | 72,691 | 17,318 |
| CT – industrial frame | 2,192 | 40,591 | 18,273 | 24,668 | (all CT) 4,971 | 18,802 | (all CT) 8,157 | 12,677 |
| CT – aeroderivative | 6,946 | 57,412 | 22,224 | 26,399 | — | — | — | — |
| Coal | 27,209 | 38,549 | 31,458 | 17,639 | (7,937) | 15,304 | 11,257 | 11,313 |
| Oil or gas steam | (784) | 41,260 | 0 | 28,892 | 0 | 26,526 | 280 | 18,064 |
| Diesel | 10,590 | 41,446 | 36,190 | 34,963 | 0 | 27,276 | 6,721 | 25,431 |
| Nuclear | 272,263 | 63,272 | 518,160 | 43,895 | 213,144 | 17,580 | 213,144 | 17,580 |

ICAP in the tables: CT frame 21,441 / aero 6,086 (2021); CT 25,839 (2023), 25,291 (2024);
oil/gas steam 5,992 / 5,295 / 3,610 / 2,869; coal 38,816 / 35,864 / 30,111 / 25,760.

Median avoidable-cost recovery, E+AS only / all markets (Table 7-37 / 7-41): CT frame 6 % / 125 %
(2021), 31 / 69 (2022); CT 14 / 71 (2023), 27 / 71 (2024); oil/gas steam 0 / 182, 0 / 58, 0 / 73,
1 / 93; coal 56 / 125, 29 / 51, (7) / 4, 11 / 25.

## New-entrant net revenue, PJM row — Tables 7-9 (CT) / 7-11 (CC) / 7-13 (CP) energy, 7-6 capacity, 7-3 reactive, $/MW-yr

| year | CT energy | CC energy | CP energy | capacity | CT reactive | CT levelized cost | CT % recovered |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 44,583 | 82,983 | 33,463 | 50,695 | 3,734 | 134,297 | 74 |
| 2022 | 106,814 | 165,402 | 59,112 | 39,442 | 2,917 | 149,470 | 100 |
| 2023 | 60,290 | 90,055 | 19,527 | 20,155 | 2,601 | 163,333 | 51 |
| 2024 | 73,049 | 98,094 | 32,548 | 15,030 | 2,403 | 185,198 | 49 |

New-entrant CT: 9,241 Btu/kWh, CF 42 / 40 / 60 / 60 %, SRMC $37.73 / 69.94 / 25.29 / 26.19 per MWh
(Tables 7-4, 7-5). The SOM publishes NO per-service split (sync / non-sync / regulation / black
start) for the new entrant; new-entrant total = energy + capacity + reactive.

MMU "avoidable costs by technology" (Table 7-39, $/MW-day; first published in the 2022 report):
coal 296.96 / 311.91 / 305.01; CC 91.17 / 99.81 / 125.46; CT 162.43 / 180.29 / 279.28; diesel
105.25 / 114.90 / 121.30 (2022 / 2023 / 2024). These are the MMU's own competitive-offer view and
are NOT the Manual 18 default gross ACR (Section 5 publishes no default-ACR dollar table).

## Ancillary services — Section 10

| item | 2022 | 2023 | 2024 |
|---|---:|---:|---:|
| Regulation total charges, $M | 296.2 | 134.0 | 183.2 |
| Synchronized reserve credits, $M | Jan–Sep tier-2 54.4 + LOC 16.3; Oct–Dec (2.3 / 3.5 / −8.4) | 73.0 | 74.1 |
| Non-synchronized reserve credits, $M | ≈15.4 Jan–Sep; Oct–Dec 0.12 / 0.40 / −23.8 (Elliott buy-backs) | 9.0 | 10.2 |
| Secondary (30-min) reserve credits, $M | 0.06 / 0.01 / 0.67 (Oct–Dec) | 1.2 (all LOC) | 2.3 (all LOC) |
| Black start total charges, $M | 68.6 | 67.3 | 73.8 |
| Reactive total, $M | 385.5 (2024 restatement 386.5) | 389.1 | 380.7 |
| Regulation weighted-average cost, $/MW | 65.10 | 29.32 | 40.08 |
| Sync reserve RTO price, $/MWh | tier-2 Jan–Sep 16.16; Oct–Dec RT 11.21 | RT 1.83 / DA 3.14 | RT 3.41 / DA 3.04 |
| Non-sync reserve RTO price, $/MWh | Jan–Sep 0.25; Oct–Dec RT 1.74 / DA 3.31 | RT 0.60 / DA 1.03 | RT 1.54 / DA 1.32 |
| Regulation demand, MW | 525 / 800 (ramp hours) | same | same |
| Sync reserve requirement RTO / MAD, MW | 1,676 / 1,676 (Jan–Sep); 1,819 / 1,819 | 2,133 / 1,766 | 2,346 / 1,773 |

ORDC as implemented: two steps, $850/MWh at the reliability requirement and $300/MWh on the
+190 MW extension; no $2,000 penalty factor appears in any of the three reports (the 2019
filing's figure was reversed on remand 2021-12-22). From 2023-05-19 PJM raised the synchronized
reserve reliability requirement 30 % (Table 10-7), which the MMU grades "Flawed" / "Not
Competitive"; sync-reserve credits rose from $1.6 M/month (Jan–Apr 2023) to $8.3 M/month.
The 2024 report (sec 10) states reactive is counted in the capacity demand-curve E&AS offset
at **$2,199 per MW-year**.

## Energy uplift (operating reserve credits) — Section 4, Table 4-1 / 4-4, $M

| unit type | 2021 | 2022 | 2023 | 2024 |
|---|---:|---:|---:|---:|
| Combustion turbine | 153.5 | 174.5 | 92.8 | 119.9 |
| Combined cycle | 5.9 | 33.7 | 5.3 | 11.8 |
| Steam – coal | 13.5 | 35.2 | 36.1 | 61.1 |
| Steam – other (oil / gas) | 3.3 | 39.8 | 19.8 | 71.1 |
| Diesel | 1.6 | 3.1 | — | — |
| Total uplift credits | 178.4 | 289.9 | 158.7 | 269.9 |

CTs received 75–86 % of balancing credits and 82–85 % of lost-opportunity-cost credits in every
year; steam units received most day-ahead credits.

## Capacity market — Section 5

E&AS offset: the tariff's backward-looking three-year average was restored by FERC's
2021-12-22 Order on Voluntary Remand (the forward-looking offset applied only to the 2022/23 BRA);
the MMU argues for a forward-looking offset. Share of generation resources electing the
**default**-ACR offer cap (Table 5-14 / 5-16): 2023/24 BRA 612 resources (61.0 %); 2024/25 715
(74.2 %); 2025/26 729 (65.1 %).
