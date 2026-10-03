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
SolveEpoch 2026-10-03a re-keys backcast SOCO.
