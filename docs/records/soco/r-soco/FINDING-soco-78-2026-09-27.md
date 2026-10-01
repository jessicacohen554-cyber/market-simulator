# FINDING — SOCO-78 (2026-09-27): the CT "ranking inversion" is a price-elasticity defect of the whole CT class, with no admissible measured carrier. The McDonough fall-back, as scoped, would miss McDonough and move NYISO. Zero LP, no solve.

**Lane** SOCO-78 · **DATA PROFILE** soco · **Model** Opus (rule 27).
**Keeper:** `2026-09-27-soco76-egrid-identity-hr`, unchanged. `origin/main` is at `9c9c59fb`, and PR #6783 is merged.
**Owner rulings:** there is no ruling in `docs/calibration-log/soco.md` on soco-75's two-sided coal mode, and none on soco-77's `tranche_startup_amortization` question. So the zero-LP identification task ran, and nothing was built.
**Legs:** the seven soco-76 legs, fetched at the RESULT-soco-76 §6 SHAs. All seven refs still resolved. The legs are gitignored and were not committed.
**Probe:** `scripts/probes/_soco78_ct_identification.py` (`attrs`, `rank`, `timing`).
**Outputs:** `soco78_ct_census.csv` (per CT plant-year) and `soco78_ct_entity_timing.csv`.

## 1. Headline

| question | answer |
|---|---|
| What drives the per-plant inversion? | **Merit order within the class.** The model ranks CTs by heat rate: log(model/923) against CEMS heat rate gives Spearman −0.60 (n = 110 plant-years). The cheapest CTs are the 7FA-class plants at 9.5–10.4 MMBtu/MWh. Most of them are IPP-sector (EIA-860 Sector 2) or Southern Power, so they absorb whatever the class over-runs. |
| Is it a per-plant cost the model has wrong? | **No, as far as the data can measure.** Heat rate is the plant's own CEMS figure (soco-76). Implied fuel is about $3.1–3.3/MMBtu at every plant. Oil share is ≈ 0 everywhere, apart from Calhoun 2023 (39 % of 0.03 TWh). No CT at either end has a window in SOCO's CAMPD outage extract. |
| What is the real object? | **The class's price elasticity.** Actual CT output is nearly flat at **3.3–4.7 TWh a year**; 2022 is the exception at 7.05. Modelled CT output swings **2.4 → 11.5 TWh** with gas price (table §2). In low-gas years (fuel ≤ $3.3/MMBtu: 2019, 2020, 2023, 2024) the class runs 2.0–2.6× actual, and 9,500–11,500 modelled entity-hours stand against 5,000–6,900 on CEMS. In high-gas 2021–22 it under-runs. |
| Where does the excess land? | **IPP CTs, because they are the cheapest.** In 2019 IPP CTs produce 4.90 TWh in the model against 0.71 actual. In reality 59–70 % of their energy falls in the top 10 % of load hours; the model puts 32–39 % there. Oglethorpe (OPC) CTs match in low-gas years (2.56 vs 2.48) and under-run 3–4× in 2021–22. **No entity is right in every year**, so this is not an ownership partition. |
| Is there an admissible carrier? | **None is registered.** Sector and operator are published per-plant fields (rule 18 compatible, like the `retirement_sector_gate` precedent), but the energy-side consequence is unmeasured: contract strike prices, tolling call rights, and IPP delivered gas, which EIA-923 Page 5 withholds for non-utility plants (`n_m` = NaN at every IPP). Any number put there would be a fitted adder (rules 1 and 13). **Refused.** |

## 2. The class-level object (soco76 legs; CT_PEAKER plants; EIA-923 plant boundary)

| year | model TWh | EIA-923 TWh | median implied fuel $/MMBtu | CT offer p50 $/MWh | price p50 / p90 |
|---|---|---|---|---|---|
| 2019 | **11.50** | 4.48 | 3.14 | 36.2 | 32.1 / 34.5 |
| 2020 | **9.18** | 3.53 | 2.66 | 30.6 | 25.9 / 29.9 |
| 2021 | 2.37 | 3.28 | 4.34 | 48.4 | 34.8 / 42.7 |
| 2022 | 5.18 | 7.05 | 7.89 | 86.5 | 65.3 / 82.6 |
| 2023 | **9.59** | 3.87 | 3.34 | 36.7 | 31.9 / 37.6 |
| 2024 | **8.01** | 3.99 | 3.11 | 34.0 | 27.7 / 34.4 |
| 2025 | 4.94 | 4.70 | 4.43 | 49.6 | 38.5 / 48.4 |

In every over-running year, the CT offer band sits at or just above the price p50 and inside the p90, so the class is marginal in a large share of hours. The same years carry the coal failures: 2019 COAL_BIT −4.16 pp and 2020 C4 0.301. This makes the CT level and the coal deficit one merit-order object, which soco-73 described from the coal side ($33–49 coal econ offers against a $26 price).

## 3. Entity split (CT-only plants; CEMS gross vs model; top-10 % = SOCO demand deciles)

| year | entity | model TWh | 923 TWh | model top-10 % share | CEMS top-10 % share | hourly r |
|---|---|---|---|---|---|---|
| 2019 | IPP | 4.90 | 0.71 | 0.32 | 0.59 | 0.52 |
| 2019 | OPC | 2.56 | 2.48 | 0.45 | 0.56 | 0.76 |
| 2021 | IPP | 0.98 | 0.58 | 0.61 | 0.43 | 0.67 |
| 2021 | OPC | 0.43 | 1.80 | 0.57 | 0.49 | 0.73 |
| 2022 | OPC | 0.85 | 3.02 | 0.58 | 0.47 | 0.74 |
| 2023 | IPP | 4.50 | 0.49 | 0.34 | 0.70 | 0.49 |
| 2023 | OPC | 2.05 | 1.99 | 0.47 | 0.56 | 0.78 |

The full table for 2019–2025 is in `soco78_ct_entity_timing.csv`. The SO-utility and muni/coop groups are excluded here because their CEMS includes the non-CT units at mixed plants.

## 4. Candidates checked (soco-77 §2 list)

| candidate | measured | verdict |
|---|---|---|
| Heat rate as measured vs as modelled | own CEMS HR in the offer; implied fuel is flat across plants | not the cause |
| Firm vs interruptible gas / delivered price | IPP receipts withheld on EIA-923 Page 5. Utility and OPC receipts are $2.1–2.8 in 2019, cheaper than the model's ~$3.1 | no measured number exists that would make IPPs dearer |
| Dual-fuel or oil-only | 860 multifuel says dual-capable; 923 oil share ≈ 0 | not the cause |
| Availability / outages | no CT window for any of the 10 plants in `campd-unit-outages-SOCO.csv`; CEMS on-hours are ordinary | cannot discriminate |
| Exports out of the SOCO BA | EIA-930 interchange is BA-level only | not identifiable per plant |
| Offtake / tolling / dispatch rights | Sector and operator partition the over-run in low-gas years only | the energy consequence is unmeasured, so refused (§1) |

**What this points to** (not built, no field): a CT class whose real energy is load-driven (peak / reliability) rather than fuel-merit-driven. The soco-77 start cost moves in that direction. It cuts modelled on-hours and brings the class level in (§4 there), and it is the only registered carrier with this reach. **It remains the owner's open question.** This lane adds one piece of evidence: the error is the class's elasticity to fuel price, not a per-plant ranking error. A start cost is price-level-neutral across gas years, so the soco-77 greedy should be read against 2021–22 as well. There it pushed CT_PEAKER further under (−0.54 → −1.17 and −0.98 → −1.57 pp; both still PASS).

## 5. Secondary census: McDonough 710 CTs on the plant CC blend (soco-76 §2b)

- **Where the blend actually comes from.** In 2019–2022 the four 1971 CTs are CAMPD-binned `CT_PEAKER` tranches at the plant blend: offer $18.7–52.4, 0.45–0.50 TWh a year against ≈ 0 actual. In 2023–2025 they are separate units (`710_3A/3B`) at $147–155 and dispatch 0. The family mechanism is **not involved in any year**. `egrid_family_heat_rates` applies only `APPLIED_VINTAGE = 2023` (`scripts/data/derive_egrid_family_heat_rates.py:117`), and in the 2023 vintage McDonough has no live GT family. Its out-of-window GT rows (46.5 / 35.0 / 40.5) exist only in the record-only `_vintages.csv` for 2019 / 2022 / 2024.
- **So the scoped fix ("fall back to class default for an `out_of_window` family inside `egrid_family_heat_rates`") would not reach McDonough.** Census over every committed artifact at the applied vintage:

| ISO | keeper arms the flag? | `out_of_window` rows at the applied vintage | effect of the scoped fix |
|---|---|---|---|
| CAISO | yes (`rcaiso5_XE_span`) | 0 | byte-identical |
| NYISO | yes (`nyisonext3_span`) | **Northport 2516 GT** | **moves the NYISO keeper**, so it needs a per-ISO gate |
| SOCO | yes (soco76) | 0 | **inert**, so it misses its target |
| other ISOs | no artifact | — | byte-identical |

- **The real seam** is that the plant-grain eGRID join has been year-matched since F1 (`data/egrid.py`, `egrid_vintage_for_year`), while the family artifact stayed pinned to 2023. A McDonough repair would therefore mean applying the family rate from the join's own vintage, which is exactly what the derive docstring says it does. That is a shared-code change: it moves CAISO (36 vintage rows against 8 applied) and NYISO (96 against 15) as well as SOCO. It needs either its own gate or a per-ISO census at fleet grain (a `fleet_only` rebuild per keeper). **Not built.** Reach is bounded at ≤ 0.50 TWh a year of SOCO CT, 2019–2022 only.

## 6. Owner questions (carried; none new)

1. soco-75: a two-sided `coal_econ_marginal_hr_bound` for must-run-floored plants.
2. soco-77: arm `tranche_startup_amortization` for SOCO as the objective start. This lane's §2–§4 is added evidence for the level, not for a ranking fix.
3. (Scoping, not a ruling) Should the eGRID family mechanism follow the join's year-matched vintage (§5)? It is shared code that moves three ISOs.

## 7. Retrievability (rule 34(e))

No solve, so there is nothing to retrieve. The soco-76 legs are costed as a re-solve (~5–25 min of LP per year) if their refs go.
