# NYISO LDC power-generation transportation rates — sources

`nyiso_ldc_generator_transport_monthly.csv` — the filed delivery charge an **LDC-served**
electric generator pays its local distribution company to carry its own gas (bought at the
pipeline hub the model already prices) from the city gate to the plant. Consumed by
`market_sim.data.fuel.apply_nyiso_ldc_generator_delivered_gas`
(`ScenarioConfig.nyiso_ldc_generator_delivered_gas`, NYISO-STGAS-2023, 2026-09-25).

Columns: `ldc_eia860_name` (exactly as EIA-860 Schedule 2 `Natural Gas LDC Name` spells it —
the join key; which plants an LDC serves is read from EIA-860, never listed here),
`year`, `month`, `transport_usd_per_mmbtu`, `loss_factor` (multiplier on the commodity),
`min_plant_mw` (the class's filed facility-rating threshold), `service_class`, `source`.

## Consolidated Edison (PSC No. 9 — Gas), 2021-01 .. 2025-12

**Class: Service Classification No. 9, Transportation, Rate (D)(2) "Rate for Power Generation
Transportation Customers"** — Leaf 277 Revision 5 (initial effective 2014-03-01, Case
13-G-0031; cancelled by Revision 7 effective 2026-02-01) and Leaf 277.1 Revision 2 (effective
2006-06-15, Case 98-G-0122; cancelled 2026-02-01). Verbatim applicability: *"applicable to the
transportation of gas used to fuel an electric generation facility having a rated capacity of
50 Megawatts or greater"*. In force unchanged for every month 2021-2025.

| component | filed value | here |
|---|---|---|
| System Cost Component | 1.0 ¢/therm | |
| Marginal Cost Component | 0.92 ¢/therm | 1.92 ¢/therm = **0.192 $/MMBtu** |
| Loss allowance | 0.5 % | **loss_factor 1.005** |
| Value Added Charge | individual customer, filed annually with the PSC (5 % of the positive monthly spark-spread difference vs the 1999-2000 base year, by heat-rate tier) | **omitted** — not published (no VAC statement type in the PSC ETS for PSC 9) |

Because the VAC is omitted, the leg is a **lower bound** on the filed delivery charge.

Retrieval: NY DPS Electronic Tariff System, cancelled leaves for Con Ed PSC 9 Gas
(`https://ets.dps.ny.gov/ets_web/search/searchShortcutCancelledLeaf.cfm?service_desc=GAS&company_id=3569014&psc_num=9`),
fetched 2026-09-25. Committed copies: `coned-psc9-gas/coned_leaf277_rev5.pdf`
(sha256 `832b4a5f…265df7a`), `coned-psc9-gas/coned_leaf277.1_rev2.pdf` (sha256 `0e2c80a2…dfc6ca8`).

### The class NOT used, and why

The monthly SC 9 **ITR** statements (Nos. 271-331, 2021-01..2025-12, same ETS) carry an
**Off-Peak Firm** contract rate of 8.75 / 7.75 ¢/therm (constant) and a line-loss factor of
1.0245 / 1.0288 / 1.0340 / 1.0338 / 1.0443 (2021-2025). That is the general transportation class;
Rate (D)(2) is the tariff's own class for ≥ 50 MW generators, and the tariff's non-firm revenue
credit (GI VII(B)(1)(d)) names divested third-party power generation facilities as served under
Rate D(1)/D(2) or negotiated contracts. The ITR series is recorded in
`docs/PRECOMMIT-nyiso-stgas-2023-ldc-leg-2026-09-25.md` as the refuted alternative, not committed as
an input.

## LDCs not intaken (stated scope limit)

EIA-860 also records Central Hudson (Danskammer 2480, Roseton 8006), NYSEG (Greenidge 2527),
KeySpan/National Grid NY (Brooklyn Navy Yard, Gowanus, Narrows …) and Niagara Mohawk
(Sithe, Castleton, …) as generator LDCs. Their generator classes are not intaken; those plants
stay on the hub. Brooklyn Union (KEDNY) has an SC 20 "Interruptible Transportation for Electric
Generators" class whose first public statement (ITEG No. 1) is effective 2026-01-01 only.
