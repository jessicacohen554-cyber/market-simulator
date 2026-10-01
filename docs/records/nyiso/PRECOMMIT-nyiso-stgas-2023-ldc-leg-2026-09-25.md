# PRECOMMIT — NYISO-STGAS-2023: the 2023 ST_GAS over-dispatch, and the LDC generator delivery leg — 2026-09-25

**Session:** NYISO-STGAS-2023 (ORCHESTRATOR, rule 32 `[R-SHARD]` (a): this container runs no LP).
**Keeper (control, rule 29 (b) form 4):** `2026-09-24-nyiso-r-inputs-860vintage`, bundle
`results/calibration/rnyiso_span` (2022–2025, basis `e95436d5024fc14096eed558d6dd15a65128e524`),
determination **NOT-YET** on C1 (2023 ST_GAS +4.99 TWh / +4.1 pp) + C3c.
**2021 control:** the keeper recipe replayed on 2021 by R-NYISO-2021 (basis `24cf43280f3b…e9e`).
Its PR #6636 was **closed unmerged**. Its committed sidecars (branch head
`8671806374d1c08a945f497769b65783cc2fc70e`) are read here as the zero-LP 2021 control only, and
nothing from it is landed by this lane.
**Lane branch cut from:** `origin/main` = `c64e69ebeb2eb4c9e16106aa044b15285225393a`.
**Lever ruling:** the owner chose *"Intake NYC LDC leg"* on this session's lever question (§2),
after phase 0.

---

## 0. Headline, fixed before any solve

1. **The 2023 ST_GAS miss is not the reliability floor.** It is the economic dispatch of NYC steam
   on Transco Z6 hub gas. At plant grain (D-2) the floor forces 1.73 / 1.88 / 2.18 / 2.00 TWh of
   ST_GAS in 2022–2025 (2.25 TWh in 2021): flat across years, while the excess appears in 2023. The
   D-4 unit-conduct FAILs at 2480 and 8906 total 0.05 TWh.
2. **One lever, structural, zero free parameters:** `nyiso_ldc_generator_delivered_gas` (new,
   default off). Gas bought at the hub, grossed up by the LDC's **filed** loss allowance, plus the
   LDC's **filed** power-generation transportation charge, for generators EIA-860 records as
   LDC-served.
3. **The intake changed the answer's size.** The class that applies is Con Edison SC 9 **Rate D(2)**
   (≥ 50 MW generators): **1.92 ¢/therm + 0.5 % losses**, about +$0.20/MMBtu. It is not the
   ~$0.8/MMBtu off-peak firm rate, and not the ~$2.5 KEDNY non-firm rate nyiso-192 considered. The
   customer-specific Value Added Charge is not published, so the leg is a **lower bound**.
4. **All five years are solved, one shard each (rule 36), every year on the same config**
   (2021, 2022, 2023, 2024, 2025).
5. **No offer-curve band moves, no multiplier is tuned, and no gate is a stop condition.**
   Regressions are reported at full magnitude and routed. They are never recovered by tuning
   (rule 1 (c)).

## 1. Phase 0 (zero LP), committed evidence

Probes: `scripts/probes/nyiso_stgas2023_phase0.py` → `results/calibration/_nyiso_stgas2023_phase0.json`;
`scripts/probes/nyiso_stgas2023_offers.py` → `_nyiso_stgas2023_offers.json` (keeper posture) and
`_nyiso_stgas2023_offers_arm.json` (`--arm`); `scripts/probes/nyiso_stgas2023_ldc_footprint.py` →
`_nyiso_stgas2023_ldc_footprint.json`. Sources: the keeper payloads (per-plant hourly model CF),
the NYISO bench parts (per-plant CAMPD hourly + EIA-923), `hourly/class_band_hourly_<y>`,
`legitimacy_diagnostics.json` D-2/D-4, and fleet-only rebuilds through `replay_keeper.run_year_kwargs`.

### 1.1 ST_GAS by zone, model − EIA-923 (TWh)

| year | NYC | Long Island | Capital/Hudson | Upstate West | **total (C1)** |
|---|---|---|---|---|---|
| 2021 | **+4.77** | −2.99 | −0.80 | −0.42 | +0.57 |
| 2022 | **+2.55** | −1.61 | −1.30 | −0.49 | −0.86 |
| 2023 | **+8.15** | −1.79 | −0.85 | −0.52 | **+4.99** |
| 2024 | **+3.14** | −1.62 | −0.77 | −0.28 | +0.48 |
| 2025 | **+1.29** | −1.78 | −1.36 | −0.15 | −1.99 |

**Correction to the lane brief:** 2021 is not a clean control. It carries the same zonal object,
netted to +0.57.

**2023 by plant:**

| plant | model TWh | EIA-923 TWh | Δ | notes |
|---|---|---|---|---|
| Ravenswood 2500 | 6.10 | 0.79 | **+5.31** | model on 8,736 h at 697 MW vs CEMS on 5,485 h at 155 MW |
| Arthur Kill 2490 | 2.60 | 1.04 | +1.55 | |
| Astoria 8906 | 2.01 | 0.73 | +1.29 | |
| Northport 2516 | 1.49 | 2.39 | −0.90 | |
| Bowline 2625 | 0.16 | 0.94 | −0.78 | |

**Seasonality:** Ravenswood's measured 2023 energy is almost all Jul/Sep/Oct. The model runs
280–864 GWh in every month.

### 1.2 Floor-forced vs economic

- **Plant grain (D-2) reliability-floor energy:** 2.25 / 1.73 / 1.88 / 2.20 / 2.01 TWh
  (2021–2025). The gas bridge adds ≤ 0.016 TWh. Class bands in 2023: committed 2.75, econ 9.89,
  peak 0.70 TWh.
- **Unit grain:** the NYC persistent-base limb places **1.62 TWh** on Ravenswood in 2023 (1.72 /
  0.33 / 0.57 / 0.29 in 2021 / 2022 / 2024 / 2025). The limb is pro-rata on available capacity, so
  it scales with the availability the merit-order guard hands back (0.64 / 0.68 in 2023 / 2021 vs
  0.12–0.23 otherwise). D-2 nets this away at plant grain, as nyiso-181 recorded.
- **Split of Ravenswood's 2023 +5.31 TWh:** about **1.6 TWh is floor**, which by itself already
  exceeds Ravenswood's measured 0.79. About **3.7 TWh is economic**.
- **Reserves are not the driver:** every NYC / SENY / LI reserve family's dual is ≈ 0 in every
  year.

### 1.3 The offer anatomy (the carrier)

2023, keeper posture, mean over hours:
- **Ravenswood:** econ tranche **$31.84/MWh** (measured HR 11.315 × Transco Z6 gas). The model NYC
  price mean is $33.95, and its cheapest tranche sits below that price in **5,485 h**.
- **LI / Hudson steam at nearly the same heat rate:** Northport $46.13, Barrett $45.46, Bowline
  $44.10, Roseton $45.48. In merit 240–870 h.
- **The whole gap is gas.** NYC is priced at Transco Z6 NY ($1.94 / MMBtu SOM annual 2023), LI and
  Hudson at Iroquois Z2 ($3.28).
- **The NYC price is not the carrier:** model NYC 2023 = $34.76 vs RT actual $33.47 (+$1.29).
  Monthly, it tracks actual to within a few dollars.
- **Heat rate is not the carrier either** (nyiso-183's object is closed): measured CAMPD raises
  Ravenswood from the old 9.50 hand value to 11.315.

**NYC steam over-run vs the gap between measured NY delivered-to-generators gas and the Z6 hub**
(EIA N3045NY3 minus the SOM Z6 NY annual, $/MMBtu):

| year | NYC steam model − 923 (TWh) | N3045NY3 − Z6 hub |
|---|---|---|
| 2021 | +4.77 | +0.55 |
| 2022 | +2.55 | +0.28 |
| 2023 | +8.15 | +1.15 |
| 2024 | +3.14 | +0.61 |
| 2025 | +1.29 | −0.11 |

## 2. The lever and its identification

### 2.1 The object

The model prices every NYISO gas unit at its zone's **pipeline hub**, which is the commodity. The
three NYC steam plants are **not on the pipeline**. EIA-860 Schedule 2 (`Natural Gas LDC Name`,
identical in the 2021–2024 vintage plant files and the canonical 2025 file) records Ravenswood,
Astoria **and Arthur Kill** as served by **Consolidated Edison**. That corrects nyiso-192's "Arthur
Kill is KEDNY".

The Long Island and Bowline steam plants are instead recorded as **pipeline-connected** (Iroquois,
Transco, Columbia). That is consistent with nyiso-145: their EIA-923 delivered cost tracks their
hub within about ±10 %.

An LDC-served generator pays the LDC's filed transportation charge on top of the commodity. The
model omits it (rule 14 `[R-ACCURATE]`).

### 2.2 The class (the intake)

Retrieved from the NY DPS Electronic Tariff System, cancelled leaves of Con Ed PSC No. 9 Gas:
- **Leaf 277 Rev 5** (effective 2014-03-01, cancelled 2026-02-01).
- **Leaf 277.1 Rev 2.**

Committed to `data/raw/gas-prices/coned-psc9-gas/`, with sources in
`data/raw/gas-prices/SOURCES_nyiso_ldc_generator_transport.md`.

**SC 9 Rate (D)(2), "Rate for Power Generation Transportation Customers":** *"applicable to the
transportation of gas used to fuel an electric generation facility having a rated capacity of 50
Megawatts or greater"*.

| component | filed | used |
|---|---|---|
| System Cost Component | 1.0 ¢/therm | |
| Marginal Cost Component | 0.92 ¢/therm | **0.192 $/MMBtu** |
| Loss allowance | 0.5 % | **× 1.005** |
| Value Added Charge | individual customer, filed annually, unpublished | **omitted → lower bound** |

It is in force unchanged for every month of 2021–2025. The tariff's own gas-cost reference is
Transco Z6 NY, the model's commodity hub, which confirms the leg is additive to that hub.

**Refuted alternative, recorded so it is not re-proposed:** SC 9 Off-Peak Firm from the monthly
ITR statements (Nos. 271–331):
- 8.75 / 7.75 ¢/therm, constant 2021–2025.
- Line-loss factor 1.0245 / 1.0288 / 1.0340 / 1.0338 / 1.0443.

That is the general transportation class; Rate D(2) is the tariff's class for ≥ 50 MW generators.
The KEDNY SC-22 non-firm Tier 1 rate (~$2.5) is the wrong LDC for all three plants.

### 2.3 The mechanism (`nyiso_ldc_generator_delivered_gas`, default off)

`data/fuel/basis/nyiso.py::apply_nyiso_ldc_generator_delivered_gas`, called from
`run_calibration.run_year` after `apply_nyiso_downstate_ct_gas_daily` and before the dual-fuel
oil-parity min. It sets

    delivered[h] = hub[h] × loss_factor[month] + transport[month]

for every gas row that meets all three conditions:
- the row is **not** `CT_PEAKER` (the CT daily leg already sets those; rule 19);
- its plant's active-vintage EIA-860 LDC has a filed rate in
  `data/raw/gas-prices/nyiso_ldc_generator_transport_monthly.csv`;
- its plant capacity meets the class's filed threshold (`min_plant_mw` = 50).

- **Population:** by the unit's published LDC and the tariff's own size criterion, never by a class
  list (the rule 18 discipline). That is why the NYC CCs on Con Ed (Astoria Energy I/II, NYPA
  Astoria, Ravenswood CC) are included. Rate D(2) is a generator tariff, not a steam tariff.
- **Free parameters:** zero. Rules 21 / 24 hold: every value is a filed tariff number or an EIA-860
  field, and there is no plant list in code.
- **Rule 13:** the tariff publishes forward and steps at rate cases, and EIA-860 is annual.
- **Stated scope limits:**
  - LDCs whose generator class is not intaken stay on the hub: Central Hudson (Danskammer,
    Roseton), NYSEG (Greenidge), National Grid NY (Brooklyn Navy Yard …), Niagara Mohawk (Sithe …).
  - The VAC is omitted.
  - The CT daily leg's own class choice (KEDNY SC-22 for every NYC CT, Con Ed-served CTs included)
    is not changed here. It is a named successor.

## 3. G-DRIFT (rule 29 (b))

- `e95436d5 → 7c778943`: audited INERT in `docs/PRECOMMIT-r-nyiso-2021-2026-09-25.md` §3.
- `7c778943 → 5c6e7ab8`: audited this session, over the solve path (`src/market_sim`,
  `run_calibration{,_full}.py`, `replay_keeper.py`, `scripts/lib`, `_validation-source`,
  `reference`, `NYISO-AS`, `_processed-legacy`) plus the fleet loader's `eia-860`. **No LIVE hunk:**
  - new SOCO / PSEI registries (other BAs);
  - `fleet_zone_vintage_coords` and `ercot_partial_outage_day_guard` (default off, absent from the
    recipe);
  - NWPP-pool EIA-930 fills;
  - CAISO CC heat rates;
  - an additive two-row `vintage_2022` EIA-860 change (Santa Rosa, FPL);
  - `isos.NYISO` in `calibration_reference.json` is equal at both revisions.
- `5c6e7ab8 → c64e69eb`: two new default-off fields, `cc_block_summer_rating` and
  `unit_outage_precod_clip`, both absent from both NYISO recipes. The rest is PJM/NWPP scoring
  declarations and SPP data. **No LIVE hunk.**
- **This lane's own diff:** the new field is default off, and its consumer returns before touching
  `fuel_prices` when it is off (byte-inert, unit-tested). The cache key is unchanged at the default
  (`_CACHE_KEY_OPTIONAL_FIELDS` drop `"False"`; `check_cache_key_registration` OK).

**Form 4 stands.** The keeper's committed 2022–2025 bundle, and the committed 2021 sidecars, are
the controls, so no control solve is spent.

## 4. G-FOOTPRINT (zero LP, measured, `_nyiso_stgas2023_ldc_footprint.json`)

Arming the flag on the keeper recipe moves **exactly 42 unit rows at 6 plants in every year**:
- 2490, 2500 and 8906 (NYC `ST_GAS`, 3,510–3,538 MW);
- 55375, 56196 and 57664 plus 2500's CC rows (NYC `CC_REGULAR`, 2,057–2,089 MW).

Every other fuel price, and every `pmax / pmin / heat_rate / availability / vom / zone` array, is
**byte-identical**. The fuel delta is +0.200 to +0.226 $/MMBtu. The `mc_base` delta is +$1.9 to
+$10.5/MWh on ST tranches (the peak tranche carries its 4.2× HR) and +$1.3 to +$3.7/MWh on CC
tranches.

**Economic in-merit hours** (cheapest tranche below the keeper's own hourly zonal price), keeper →
armed:

| year | Ravenswood | Astoria | Arthur Kill |
|---|---|---|---|
| 2021 | 2,245 → 1,008 | 5,575 → 4,610 | 3,613 → 1,392 |
| 2022 | 4,310 → 3,581 | 6,154 → 5,654 | 3,829 → 3,364 |
| 2023 | **5,485 → 3,065** | **7,156 → 4,649** | **4,217 → 2,470** |
| 2024 | 5,652 → 4,033 | 5,039 → 3,757 | 3,601 → 2,587 |
| 2025 | 6,059 → 4,913 | 6,288 → 5,464 | 5,178 → 4,395 |

## 5. Pre-registered expectations (fixed now, so they cannot be written to fit)

- **Direction in every year:** NYC ST_GAS ↓ and NYC CC_REGULAR slightly ↓. Some of that energy
  moves to LI / Hudson steam and CCs, CT and imports. NYC and downstate prices move up by less than
  the offer shift.
- **Magnitude:** NYC ST_GAS −1.0 to −3.5 TWh in 2023. The economic 3.7 TWh at Ravenswood is scaled
  by its in-merit loss, and the zonal price response gives some back. Smaller in 2022 and 2025
  (low guard availability, expensive gas), in between for 2021 and 2024. Floor energy (unit grain
  ~1.6 TWh at Ravenswood in 2023) is **untouched by construction**.
- **C1-2023 ST_GAS** moves from +4.99 toward the band. Whether it crosses ±3.89 TWh / ±3 pp is
  **not predicted** and **not a criterion**.
- **C8 ST_GAS forced share rises** in every year: the numerator is unchanged and the denominator
  shrinks.
- **2025 ST_GAS** (−1.99, C1 SKIPPED) moves further down.
- **C3a** moves up slightly, from −3.4 % (2023) and −9.8 % (2025).
- **Protective gates:** C6 unchanged (one new zero-DOF measured field, entered in the DOF ledger as
  a measured input). **C8 is the one to watch.**

## 6. The recipe: five shards, one per year (rule 36), pinned to this document's commit SHA

```
uv run python scripts/replay_keeper.py results/calibration/rnyiso_span --years <Y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_coal_heat_rates=true \
  --set measured_st_heat_rates=true --set measured_cc_heat_rates=true \
  --set nyiso_ldc_generator_delivered_gas=true \
  --out-dir results/calibration/nyisostg_<Y>
```

`<Y>` ∈ {2021, 2022, 2023, 2024, 2025}; 2021 reads `NYISO_reserve_requirements_2021.csv` exactly as
R-NYISO-2021 did.

## 7. Leg acceptance (the parent refuses a leg that fails any check)

- **S0 pin:** `run_config.json` `git.basis_sha` equals the pinned SHA, and `dirty` is false.
- **S1 config:** the F1 flags, `hydro_ror_split` and `nyiso_dynamic_reserve_requirements` are true;
  the outage-window flags are false; **`nyiso_ldc_generator_delivered_gas` is true**. The
  offer-curve block equals the keeper's after the bare-`COAL` fold.
- **S2 inputs:** `campd_unit_outages` and `thermal_tranches` sha256 equal the keeper's.
- **S3 fleet:** zero coal-class MWh.
- **S4 hydro:** 94 run-of-river / 70 reservoir.
- **S5 armed footprint:** the solve log carries the `NYISO LDC generator delivery leg (<Y>): 42 gas
  unit rows at plants [2490, 2500, 8906, 55375, 56196, 57664]` line.

## 8. Reporting and promotion

- **Report, per year, at full magnitude:**
  - C1–C8;
  - ST_GAS TWh vs EIA-923, by zone and by plant;
  - hourly load-weighted price bias / MAE vs RT;
  - D-2 / D-4 changes.

  Each is differenced against the controls.
- **Promotion rule, fixed now.** The arm is **structurally more faithful by construction**: it adds
  a filed cost that is really paid, and moves nothing else. It is promoted unless:
  - a leg fails acceptance; or
  - a protective criterion (C6 / C8) newly fails without passing C8's provenance + shape
    escalation (rule 21).

  A regression elsewhere is reported, not a bar (owner guidance: a structurally more faithful run
  may be a keeper even if some gates regress). It is never promoted on MAE alone.
- **If promoted (rule 35):**
  1. enumerate the year set first;
  2. register 2022–2025 composed as the keeper;
  3. register 2021 stamped to it (`--holdout-year 2021`);
  4. run `audit_keepers`;
  5. prune the outgoing keeper.
- **Rule 28 (b):** the NYISO cell `nyiso_ldc_generator_delivered_gas` moves O → K / R with this
  evidence.
