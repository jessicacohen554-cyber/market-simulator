# FINDING closeout-SOCO-2 — why the W0 keeper over-runs CC_REGULAR (zero LP)

Lane `claude/closeout-soco-2`, 2026-10-03. Keeper `2026-10-02-w0-soco-fix2`
(`results/calibration/w0_soco_span`, 2019–2025, owner ruling R-20). **No LP was
solved for this note.** Every number is from the keeper's committed sidecars on
`main` (`hourly/unit_marginal_<Y>.parquet`, `class_hourly`, `system`), EIA-923
(`_processed-legacy/eia923_monthly_generation.parquet`, `…fuel_costs.parquet`,
`coal-receipts`, `coal-stocks`), CAMPD hourly (`campd-unit-level`), and the
scorer's own functions (`scripts/calibration_verdict.py`). The keeper's
`dispatch/` and `unit_hourly` files are not on `main` and no shard branch survives;
`unit_marginal` (per-unit hourly `mw` / `cap_mw` / `mc` / `marginal`) carried
everything needed.

Probes: `scripts/probes/_closeout_soco2_{c1,a_avail,b_shape,b_price,greedy_nuc,c_exit}.py`.
Outputs: `docs/records/soco/r-soco/closeout-soco-2/`.

## 0. The target, exactly

C1 gates CC_REGULAR on two legs: volume within ±7.4–7.6 TWh, **and** share within
±3.0 pp. Volume passes every year; **share** is what fails.

| Year | Model TWh | EIA-923 TWh | Share pp | Status | Of which: model-vs-bench total-generation gap | CC cut that clears 3.0 pp |
|---|---|---|---|---|---|---|
| 2019 | 115.60 | 110.64 | **+3.64** | FAIL | +1.70 pp (model gen 245.6 vs 254.8 TWh) | **1.58 TWh** |
| 2020 | 115.66 | 113.98 | +2.57 | PASS | +1.87 pp | — |
| 2021 | 113.46 | 107.18 | **+3.58** | FAIL | +1.02 pp | **1.38 TWh** |
| 2022 | 108.36 | 111.56 | −0.43 | PASS | +0.85 pp | — |
| 2023 | 116.20 | 110.89 | +2.55 | PASS | +0.36 pp | — |
| 2024 | 114.22 | 110.31 | +2.49 | PASS | +0.96 pp | — |

About half of the 2019 miss is the denominator. Model demand is EIA-930 net
generation (2023: 239.63 vs 239.62 TWh), and it sits 1.8–9.2 TWh below the EIA-923
plant-sum bench. That is plan §3.8 step 3 (the pool-vs-BA benchmark-scope census),
not a CC question. The CC over-run itself is +2.5 to +2.6 pp of share in five of
seven years; 2019 and 2021 are just the two years where the denominator gap tips
it over.

## (a) Availability against demonstrated capability: not the driver

Per plant-month, the model's available energy (Σ `cap_mw`) is compared with
CAMPD-demonstrated capability. That capability is the month's p99.9 plant-hour
gross load, scaled to net by the plant's own EIA-923 net / CAMPD gross ratio,
times the hours in the month (`_closeout_soco2_a_avail.py`).

| Year | Model avail | Model MWh | EIA-923 | CAMPD-demonstrated | Σ(avail − demo)⁺ by plant-month |
|---|---|---|---|---|---|
| 2019 | 118.6 | 115.6 | 107.0 | 147.0 | **1.90 TWh** |
| 2020 | 120.5 | 115.7 | 109.6 | 144.1 | 1.45 |
| 2021 | 123.7 | 113.5 | 110.0 | 153.2 | **1.14** |
| 2023 | 121.2 | 116.2 | 109.8 | 150.9 | 0.70 |
| 2024 | 121.8 | 114.2 | 110.3 | 157.8 | 0.26 |

The model's E.1 seasonal capability sits **about 20 % below** what the plants
demonstrably delivered. The excess over demonstrated is confined to four plant
cases:
- **57037 Ratcliffe (Kemper)**: 0.46 / 0.93 / 0.66 TWh in 2019 / 2020 / 2021.
- **55440**: 0.72 TWh in 2019.
- **643 Lansing Smith**: 0.37 TWh in 2019.
- **55242**: 0.34 / 0.23 / 0.40 TWh.

None of these plants runs at util 1.0. So the W0 rating is not what makes the
over-run. What E.1 did was **expose** the over-run, by giving the LP more cheap CC
to run.

## (b) Merit order: the over-run is a night phenomenon, and the offers are right

### Shape

CC_REGULAR, mean MW by system-demand decile, comparing model with CAMPD net-scaled
generation (`_closeout_soco2_b_shape.py`). Gap is model minus actual:

| Year | Decile 0 (lowest load) | Decile 2 | Decile 4 | Decile 6 | Decile 8 | Decile 9 (peak) |
|---|---|---|---|---|---|---|
| 2019 | **+1,901** | +1,292 | +1,125 | +891 | +138 | +62 |
| 2021 | **+1,316** | +712 | +507 | +363 | −291 | −599 |
| 2023 | **+1,237** | +1,052 | +731 | +738 | +207 | −28 |

COAL_BIT shows the mirror image, a flat deficit in every decile: −1.0 to −1.5 GW in
2019, −0.5 to −0.6 GW in 2021, −0.4 to −1.0 GW in 2023.

**What this means.** At peak, the model's CCs and the real ones produce about the
same. The over-run is the hours when real Southern backed its CCs down and kept
coal BIT (and gas steam) online. A capability defect would show up most at peak.
It does not, so the cause is commitment and merit order, not availability.

### Prices

Model offers are compared with fuel at each plant's measured heat rate. The heat
rate is CAMPD heat input divided by EIA-923 net generation. The fuel is the plant's
F923 delivered price and its Page-5 spot receipts. Source:
`_closeout_soco2_b_price.py`, medians over plant-months.

| Year | CC model offer | CC at F923 | Coal BIT model offer | Coal BIT at F923 | Coal BIT at spot receipts |
|---|---|---|---|---|---|
| 2019 | 22.2 | 19.7 | 36.7 | 35.2 | 38.9 |
| 2020 | 17.7 | 16.1 | 36.9 | 40.4 | — |
| 2021 | 29.9 | 28.5 | 39.7 | 37.8 | 35.6 |

Three conclusions follow:
- **The model reproduces Southern's own fuel books.** Offers sit within about
  $1–3/MWh of F923-delivered fuel at measured heat rate.
- **The SOCO gas basis does not put CC below coal artificially.** The model's
  implied CC gas price is $0.3–0.5/MMBtu *above* F923 delivered.
- **Coal at marginal replacement cost cannot close this.** At SOCO's BIT plants,
  spot receipts are *not* cheaper than the blended price in 2019 or 2021 (Barry:
  spot 3.46 vs blended 3.15 $/MMBtu in 2019). So `coal_marginal_replacement_pricing`
  (plan §3.8 row 2) raises or holds the coal BIT price in the CC-failing years. It
  is a 2022 lever only.

On F923 economics alone, real Southern ran **coal BIT ahead of $13–16/MWh-cheaper
CC capacity at night**. That is the 2019 self-commitment the plan already names
"not closable in class". The coal-cycler routes are adjudicated:
- `coal_takeorpay_committed`: G (soco-74).
- `coal_fuel_inventory_take_floor`: G (soco-80).
- A P0-seeded coal campaign floor: refused at soco-73.
- `tranche_startup_amortization`: G (soco-77/92).

## (b′) The admissible piece: nuclear availability 2019–2022 is an estimate

Nuclear under-runs by **−2.48 / −2.20 / −3.37 / −1.50 TWh** in 2019–2022, and by
only −0.14 to −0.24 TWh in 2023–2025.

The cause is that `constants.NUCLEAR_MONTHLY_CF_BY_YEAR["SOCO"]` carries only
2023–2025. SOCO-20 registered it when SOCO's span was 2023–25, and nobody extended
it when the span grew to 2019–2025. Every 2019–2022 leg therefore reads the
forecast fallback `NUCLEAR_MONTHLY_CF["SOCO"] × (1 − EFORD 0.03)`. That is a flat
fleet CF of 0.889, with Vogtle at 17.922 TWh and Hatch at 13.695 TWh **in every one
of the four years**.

| Year | Fallback mean CF | Measured (frozen derive) | Ratio |
|---|---|---|---|
| 2019 | 0.8888 | 0.9272 | 1.043 |
| 2020 | 0.8885 | 0.9244 | 1.040 |
| 2021 | 0.8888 | 0.9498 | 1.069 |
| 2022 | 0.8888 | 0.9186 | 1.034 |

The measured rows come from `scripts/data/derive_nuclear_monthly_cf.py --isos SOCO
--years 2019 … 2025`. The 2023–25 rows reproduce byte-for-byte under `--check`.
This is a **rule-14 defect**: measured data was on disk and an estimate was used
instead. Extending the table is an initial derivation for years it never carried,
which follows the ercot-253 precedent for ERCOT 2021/2022. It is not a
re-derivation (rule 23). It replaces the fallback rather than stacking on it
(rule 19). Under rule 13 it is the same admitted input the 2023–25 legs already
read.

### Greedy (`_closeout_soco2_greedy_nuc.py`)

How the greedy works:
- The new monthly CF is applied hour by hour on the keeper's `unit_marginal`.
- The extra nuclear MW displaces **in-merit** units only (mc ≤ the unit's zone
  price), from the highest offer down. Floor-bound units are never displaced.
- A shortfall is filled cheapest-first.
- The price moves only when the in-merit setter is exhausted.
- C1 is re-scored with `score_fuelmix` on the edited payload.

| Year | ΔNuc | ΔCC | ΔCT | ΔPRB | CC share pp | C1 CC | C3a (vs λ) |
|---|---|---|---|---|---|---|---|
| 2019 | +1.96 | −0.57 | −0.55 | −0.42 | 3.64 → **3.41** | FAIL → FAIL | +11.9 → +10.8 % |
| 2020 | +1.83 | −0.65 | −0.54 | −0.33 | 2.57 → 2.29 | PASS | +12.0 → +11.2 % |
| 2021 | +3.13 | −1.92 | −0.47 | −0.31 | 3.58 → **2.78** | **FAIL → PASS** | −4.3 → −6.5 % |
| 2022 | +1.53 | −1.01 | −0.34 | 0.00 | −0.43 → −0.85 | PASS | −14.3 → −14.6 % |

After the change, model nuclear is 47.2 / 47.2 / 48.7 / 47.1 TWh against EIA-923's
47.7 / 47.6 / 48.9 / 47.1. No other class changes status in any year. 2023–25 are
untouched.

## (c) The retiring-plant last-year over-run (cross-ISO)

Source: `_closeout_soco2_c_exit.py`, over the 30 EXIT-CARRY rows of
`carry_audit_w0_2026-10-02.csv`.

**Scale.** The model exceeds EIA-923 in 20 of 28 rows that have a leg, by +10.0 TWh
in total.

**There are two measured signatures, both visible in EIA-923 monthly data:**
- **A dark tail.** 17 of 30 rows have one or more terminal months at about zero
  generation before the EIA-860 retirement month. Examples: St Clair 7 months,
  Trenton Channel 6, Braunig 9, Duane Arnold 3 (the derecho), Hammond 4,
  McIntosh-1 5.
- **Wind-down.** 16 of 30 rows run at under 0.8 × the year-on-year change of the
  same ISO's non-exit fleet over the same months. Examples: Bruce Mansfield 0.30,
  Meramec 0.19, Oklaunion 0.53, Coffeen 0.68.

Same-year monthly generation is the answer key (rule 13), so neither signature can
be imposed directly.

**The admissible, forward-reproducible form for coal is the R-3 overlay** (owner
ruling R-3: receipts plus the stock envelope as a take ceiling). Applied at its
loosest (stock minimum = 0, receipts over the online months plus December Y−1
stock), across the 20 coal rows with a leg:
- the over-run falls from **+7.54 to +0.97 TWh**;
- it under-runs by 2.62 TWh, of which 1.5 is St Clair, whose receipts land on its
  shared-yard sibling (Belle River).

That is the existing `coal_fuel_inventory` family: MISO K, SOCO U. The non-coal
rows (+2.49 TWh: Duane Arnold, LaO, Meramec ST, Decker Creek) are outage or
conduct, and no fuel ceiling reaches them.

**SOCO's three rows** (they are not wind-down):

| Row | Fuel / receipts | CF vs a year earlier | Model GWh | R-3 ceiling GWh | EIA-923 GWh |
|---|---|---|---|---|---|
| Hammond 2019 | Received no coal in 2019; the model priced it on the nearby fallback (implied $2.14/MMBtu) | about 2 % CF, as in 2018 | 573 | 83 | 111 |
| McIntosh-1 2019 | — | about 2 % CF, as in 2018 | 140 | 0 | 16 |
| Wansley 2022 | — | — | 1,250 | 1,147 | 884 |

**The R-3 lever pushes SOCO CC up, not down.** The capped coal energy is refilled
at the margin by CC, so it cannot serve the CC bar. It is a separate SOCO lane: R-3
for SOCO coal, which also reaches Scherer 2022.

**Cross-ISO note for the desk.** `NUCLEAR_MONTHLY_CF_BY_YEAR` lacks 2019–2022 for
MISO, SPP, PJM and NWPP, and lacks 2019–2020 for ERCOT, where each keeper carries
those years. Each is the same fallback defect, and it is invisible wherever an NRC
`nuclear_unit_availability` overlay covers the dates. It is each lane's to measure
(rule 25).

## Verdict

The CC_REGULAR over-run has four parts:
1. **The scorer's denominator.** Bench scope accounts for 1.0–1.9 pp of share.
2. **A rule-14 nuclear availability defect in 2019–2022.** It is measured, and the
   fix is admissible. It clears 2021 at zero LP.
3. **Real Southern's night conduct, which is the dominant residual.** At night it
   kept coal BIT and gas steam committed ahead of CC that its own F923 fuel books
   price $13–16/MWh cheaper. Every existing route to that conduct is adjudicated
   G/R. This residual is the mirror of the ledgered 2019 COAL_BIT row.
4. **A small E.1 excess** of 1.1–1.9 TWh, at four plants only.

**Lever:** the nuclear 2019–2022 coverage repair. It is not a new field, and there
is no new matrix row (it is a `constants.py` table, not a `ScenarioConfig` field).
SolveEpoch 2026-10-03b (legs stamped 2026-10-03a; renamed at merge) re-keys backcast SOCO.

## (d) Cross-ISO: years that read the nuclear forecast fallback (desk item 1, zero LP)

Probe: `scripts/probes/_closeout_soco2_nuc_coverage.py`; output in
`r-soco/closeout-soco-2/nuc_coverage.csv`.

**How the table is built.**
- One row per (ISO, year) of each current keeper with **no**
  `NUCLEAR_MONTHLY_CF_BY_YEAR` row at the keeper's SHA. Those years read
  `NUCLEAR_MONTHLY_CF[ISO]` (× 1 − EFORD) as the base table.
- Model nuclear is the keeper payload's `gmModel` value; EIA-923 is the bench part's
  `classFull`.
- The NRC column records whether the keeper arms the daily `nuclear_unit_availability`
  overlay, read from the keeper `run_config.json`.

**How to read the NRC column.** Where it reads "yes", the overlay replaces the
fallback on every NRC-covered date, so the fallback reaches only uncovered dates
(for example the uprate-season months the deriver drops). Those gaps are not purely
the fallback's.

Every year not listed has a table row: CAISO, NEISO and NYISO in full, plus
ERCOT 2021–25, MISO/NWPP/PJM/SPP 2023–25 and SOCO 2023–25.

| ISO | Year | NRC overlay | Model nuclear TWh | EIA-923 TWh | Gap TWh |
|---|---|---|---|---|---|
| ERCOT | 2019 | yes | 40.56 | 41.30 | −0.74 |
| ERCOT | 2020 | yes | 40.75 | 41.44 | −0.69 |
| MISO | 2019 | yes | 97.58 | 97.03 | +0.55 |
| MISO | 2020 | yes | 97.57 | 92.20 | +5.37 |
| MISO | 2021 | yes | 93.61 | 95.69 | −2.09 |
| MISO | 2022 | yes | 89.94 | 91.35 | −1.41 |
| NWPP | 2019 | no | 8.53 | 8.87 | −0.34 |
| NWPP | 2020 | no | 8.44 | 9.43 | −0.99 |
| NWPP | 2021 | no | 8.44 | 8.51 | −0.07 |
| NWPP | 2022 | no | 8.44 | 9.85 | −1.41 |
| PJM | 2019 | no | 276.99 | 277.92 | −0.93 |
| PJM | 2020 | no | 272.05 | 275.75 | −3.70 |
| PJM | 2021 | no | 271.90 | 271.69 | +0.20 |
| PJM | 2022 | no | 271.90 | 270.59 | +1.31 |
| SOCO | 2019 | no | 45.25 | 47.73 | −2.48 |
| SOCO | 2020 | no | 45.40 | 47.60 | −2.20 |
| SOCO | 2021 | no | 45.56 | 48.93 | −3.37 |
| SOCO | 2022 | no | 45.56 | 47.06 | −1.50 |
| SPP | 2019 | no | 15.80 | 16.20 | −0.40 |
| SPP | 2020 | no | 15.80 | 16.77 | −0.97 |
| SPP | 2021 | no | 15.80 | 15.46 | +0.35 |
| SPP | 2022 | no | 15.80 | 14.60 | +1.20 |

**The signature of the fallback** is model nuclear that is *identical across years*:
- NWPP 8.44 in 2020–22;
- PJM 271.90 in 2021–22;
- SPP 15.80 in all four years;
- SOCO 45.56 in 2021–22.

The gaps run both ways (−3.70 to +1.31 TWh), because a fixed seasonal pattern misses
each year's real refuelling cadence. The lanes that most need the same rule-14 repair
(rows from `derive_nuclear_monthly_cf.py --isos <ISO> --years 2019 … 2022`, existing
rows reproduced under `--check`) are:
- **PJM 2020** (−3.70);
- **SOCO 2019–22**, done in this lane;
- **NWPP 2020/2022**;
- **SPP 2020/2022**.

**MISO 2020 (+5.37) and the ERCOT gaps** sit under an armed NRC overlay. They are the
overlay's question (for example Duane Arnold's derecho-damaged months), not the base
table's. For reference, the rows that do have a table show the same pattern under a
measured base: NEISO 2019 +1.99 and NYISO 2021 +2.94 (NRC armed) are those lanes'
questions too. Each lane measures its own (rule 25).

## (e) Cross-ISO: exit-carry R-3 envelope, per row (desk item 2, zero LP)

Probe: `scripts/probes/_closeout_soco2_c_exit.py`; outputs `c_exit.csv` and
`c_exit_ctl.csv`.

**Envelope definition.** The loosest R-3 form: Page-5 receipts over the online months,
plus the December Y−1 stock, at S_min = 0. MMBtu is converted to MWh at the plant's
Y−1 coal heat rate (EIA-923 annual fuel / net generation).

**The other columns:**
- **Model GWh** is the W0 leg's per-plant MWh from `carry_audit_w0_2026-10-02.csv`.
- **Dark tail** is the number of terminal online months with ≤ 0.5 GWh of EIA-923
  generation.
- **Rel. CF** is the plant's EIA-923 change versus a year earlier over its online
  months, divided by the same ratio for its ISO's non-exit fleet of the same family.
- **Capped** is min(model, envelope).
- **Residual** is capped minus EIA-923.

| ISO | Year | Plant | Family | Dark tail (mo) | Rel. CF | EIA-923 GWh | Model GWh | R-3 envelope GWh | Capped GWh | Residual GWh |
|---|---|---|---|---|---|---|---|---|---|---|
| CAISO | 2023 | AES Redondo Beach | ST_GAS | 0 | 1.18 | 256 | 0 | — | — | — |
| ERCOT | 2020 | Oklaunion | COAL | 0 | 0.53 | 1,101 | 1,036 | 1,165 | 1,036 | −65 |
| ERCOT | 2022 | Decker Creek | ST_GAS | 0 | 0.63 | 73 | 195 | — | — | — |
| ERCOT | 2025 | Sandy Creek | COAL | 8 | 0.21 | 719 | 612 | 1,441 | 612 | −107 |
| ERCOT | 2025 | V H Braunig | ST_GAS | 9 | 0.22 | 387 | 414 | — | — | — |
| MISO | 2019 | Coffeen | COAL | 1 | 0.68 | 2,677 | 3,697 | 2,783 | 2,783 | +106 |
| MISO | 2019 | Havana | COAL | 1 | 0.78 | 1,469 | 1,698 | 1,477 | 1,477 | +8 |
| MISO | 2019 | Duck Creek | COAL | 0 | 1.15 | 2,237 | 1,941 | 1,861 | 1,861 | −376 |
| MISO | 2019 | Hennepin | COAL | 1 | 0.72 | 921 | 1,182 | 819 | 819 | −102 |
| MISO | 2020 | NRG Sterlington | CT | 12 | 0.74 | 2 | 40 | — | — | — |
| MISO | 2020 | Duane Arnold | NUCLEAR | 3 | 0.63 | 2,905 | 4,135 | — | — | — |
| MISO | 2021 | Dolet Hills | COAL | 1 | 1.21 | 943 | — | 1,017 | — | — |
| MISO | 2022 | St Clair | COAL | 7 | 0.55 | 1,602 | 4,278 | 107 | 107 | −1,495 |
| MISO | 2022 | E D Edwards | COAL | 0 | 1.09 | 2,695 | 2,993 | 2,629 | 2,629 | −66 |
| MISO | 2022 | Meramec | COAL | 0 | 0.19 | 86 | 465 | 247 | 247 | +162 |
| MISO | 2022 | Trenton Channel | COAL | 6 | 0.57 | 571 | 1,186 | 507 | 507 | −64 |
| MISO | 2022 | Erickson | COAL | 0 | 1.26 | 783 | 630 | 772 | 630 | −152 |
| MISO | 2022 | Meramec | ST_GAS | 0 | 2.04 | 128 | 465 | — | — | — |
| MISO | 2023 | A B Brown | COAL | 0 | 0.83 | 1,719 | 2,156 | 1,986 | 1,986 | +266 |
| MISO | 2024 | Rush Island | COAL | 1 | 0.78 | 508 | 612 | 865 | 612 | +104 |
| MISO | 2024 | LaO Energy Systems | CC | 0 | 0.80 | 1,441 | 2,180 | — | — | — |
| NWPP | 2020 | Boardman | COAL | 0 | 1.03 | 1,630 | 1,909 | 1,589 | 1,589 | −41 |
| PJM | 2019 | Bruce Mansfield | COAL | 2 | 0.30 | 647 | 942 | 711 | 711 | +64 |
| PJM | 2019 | Three Mile Island | NUCLEAR | 0 | 0.97 | 5,214 | 5,005 | — | — | — |
| PJM | 2020 | Dickerson | COAL | 1 | 4.22 | 179 | 169 | 171 | 169 | −10 |
| PJM | 2023 | Joliet 29 | ST_GAS | 1 | 1.15 | 708 | — | — | — | — |
| SOCO | 2019 | Hammond | COAL | 4 | 1.24 | 111 | 573 | 83 | 83 | −28 |
| SOCO | 2019 | McIntosh-1 | COAL | 5 | 1.26 | 16 | 140 | 0 | 0 | −16 |
| SOCO | 2022 | Wansley | COAL | 1 | 0.89 | 884 | 1,250 | 1,147 | 1,147 | +263 |
| SPP | 2020 | Oklaunion | COAL | 0 | 0.56 | 1,101 | 1,007 | 1,165 | 1,007 | −94 |

**Totals over the 20 coal rows with a leg.** The over-run falls from **+7.54 to +0.97
TWh**, and the capped rows under-run by **−2.62 TWh**. Of that under-run, −1.50 is St
Clair (MISO 2022): its receipts are recorded on its shared-yard sibling Belle River,
so a per-plant envelope reads 107 GWh against 1,602 burned. A yard-grain join (the
MISO construction) removes it, leaving about −1.1 TWh, mostly Duck Creek's
envelope-below-burn.

**Non-coal rows** (+2.49 TWh over: Duane Arnold, LaO, Meramec ST, Decker Creek,
Sterlington) are outside any fuel ceiling. They are outage or conduct questions.

**Routing.** This is the existing `coal_fuel_inventory` family (rule 19: no new
mechanism). Cell states: MISO K (its ceiling census is in
FINDING-closeout-miso-wave1), SOCO / PJM / NWPP / ERCOT U, SPP R (SPP-44). Each lane
arms it on its own footprint (rule 25). The dark-tail and wind-down profiles
themselves are same-year generation, the answer key under rule 13, and are not
admissible as an input.
