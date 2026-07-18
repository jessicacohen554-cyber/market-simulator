# NEISO (ISO-NE) Data Audit — Stage E / P0 (2026-06-11)

Status: **complete.** Wave-0 data audit from the NEISO prompt pack (doc 08,
prompt P0), run per playbook §1–2. Records what is in the repo today, what the
calibration reference now carries for NEISO, the fleet sanity check against
ISO-NE CELT/RSP, CEMS state coverage, and the open items mapped to the doc-08
upload manifest (U1–U7). Done together with the NYISO audit
(`nyiso-data-audit.md`) in one pass — both ISOs share
`scripts/data/build_calibration_reference.py` + `calibration_reference.json`.

---

## 1. Calibration reference — extended for NEISO 2023–2025

`scripts/data/build_calibration_reference.py` now derives NEISO (and NYISO)
alongside ERCOT/PJM/CAISO. NEISO uses a per-ISO year override
(`CALIBRATION_YEARS_BY_ISO["NEISO"] = (2023, 2024, 2025)`) with BA code `ISNE`
— NEISO has the most complete CEMS coverage of the new ISOs, so all three years
are first-class.

Written artifacts:

- `data/raw/_validation-source/calibration_reference.json` — NEISO blocks for
  2023/2024/2025: EIA-930 demand stats (`data/eia_hourly/ISNE hourly.parquet`),
  measured Henry Hub, EIA-923 by-fuel `generation_twh` (now including **hydro**
  and the **oil** columns — ISO-NE burns real oil in winter — see §1a), EIA-860
  wind/solar December totals + 4-zone shares + monthly ramps, and the eGRID
  2023 `BACODE=ISNE` generation/emissions benchmark.
- `data/raw/_validation-source/NEISO_{2023,2024,2025}_renewable_capacity.csv` —
  per-zone, per-month EIA-860 operable wind/solar capacity.

Headline reference values:

| Year | Demand (TWh) | Peak (MW) | HH ($/MMBtu) | Wind Dec (MW) | Solar Dec (MW) | EIA-923 gas cc/ct/st (TWh) | Nuclear (TWh) | Hydro (TWh) | **Oil (TWh)** |
|---|---|---|---|---|---|---|---|---|---|
| 2023 | 112.0 | 23,475 | 2.54 | 1,536 | 2,924 | 54.3 / 1.9 / 0.4 | 23.2 | 8.5 | **0.39** |
| 2024 | 114.4 | 24,255 | 2.19 | 1,536 | 3,354 | 58.6 / 2.1 / 0.3 | 26.5 | 6.7 | **0.31** |
| 2025 | 115.3 | 25,898 | 3.52 | 1,721 | 3,618 | 51.3 / 0.8 / 0.3 | 27.6 | 0.1 | **0.91** |

eGRID 2023 ISNE benchmark (headline): gas_cc 53.1 TWh / gas_ct 4.3 TWh
(eGRID heat-rate CC/CT split; 923's prime-mover split is the more reliable
class benchmark), hydro 8.2 TWh, nuclear 23.2 TWh, oil 0.18 TWh, coal 0.16 TWh,
biomass 5.53 TWh; CO2 totals gas_cc 20.10 + gas_ct 1.89 + biomass 2.67 +
oil 0.18 + coal 0.17 ≈ **25.1 Mt**.

### 1a. Hydro + oil added to the EIA-923 benchmark (code change this session)

The shared `_eia923_generation` masks previously emitted only
coal/gas_cc/gas_ct/gas_st/nuclear/wind/solar. For NEISO the **oil** column is
first-order (ISO-NE's winter dual-fuel burn, doc-08 design decisions 1–2) and
hydro is worth tracking. Two scoped additions:

- **hydro** = EIA-923 fuel code `WAT` + prime mover `HY` (conventional hydro
  only; pumped storage `WAT`/`PS`, which nets negative, is excluded — it is
  storage, not energy, per doc-08 design decision 5).
- **oil** = fuel codes `DFO`/`RFO`/`JF`/`KER`/`WO`/`PC`, any prime mover.

Gated through `_EIA923_EXTRA_FUELS_BY_ISO = {NYISO, NEISO}`, so the
already-calibrated ERCOT/PJM/CAISO `generation_twh` blocks are untouched. eGRID
already mapped `HYDRO`/`OIL` generically, so the benchmark needed no change
beyond the new `NYIS`/`ISNE` BACODE entries.

### 1b. Regression guard — verified, with the known ERCOT/PJM drift finding

The merged `calibration_reference.json` was diffed against the committed
version: **every ERCOT/PJM/CAISO block and all top-level fields are
byte-identical** (zero removed/changed lines; only the NYISO/NEISO `isos` and
`egrid_benchmark` entries are added). The committed ERCOT/PJM/CAISO
renewable-capacity CSVs were left untouched.

**Finding (backlog, ERCOT/PJM-owned — same item as caiso-data-audit §1b):**
re-running the script at HEAD *would* shift the committed ERCOT/PJM blocks,
because the ERCOT topology gained a `Northeast` zone (committed ERCOT CSVs carry
6 zones, current `iso_configs` has 7) and the EIA-860 parquets were rebuilt,
both *after* the ERCOT/PJM reference was last generated (2026-06-10). To honor
the byte-identical guard this session **preserved** the committed
ERCOT/PJM/CAISO blocks verbatim (load committed JSON → insert only NYISO/NEISO →
re-dump) and restored the ERCOT/PJM CSVs from HEAD. Re-baselining ERCOT/PJM
belongs to an ERCOT/PJM calibration session. CAISO (regenerated 2026-06-11)
reproduces byte-identically.

### 1c. Known caveats on the NEISO blocks

- **2025 `generation_twh` is a lower bound.** The `f923_2025` zip is the
  early-release M-file; annual-only respondents are absent. ISNE shows it
  starkly: only **322 reporting rows** vs ~1,700 in the final 2023/2024 files,
  with just **6 hydro rows** (vs ~170) → 2025 hydro reads 0.09 TWh (vs 8.5 in
  2023) and solar 1.02 TWh (vs 4.53 in 2024). All 12 months are present — this
  is respondent coverage, not a partial year. Demand (EIA-930) is complete;
  only the 923 by-fuel mix is preliminary. **P11/P12 must treat the 2025
  fuel-mix targets (especially hydro/solar/oil) as preliminary** and re-run the
  script when the final 2025 EIA-923 lands. (ERCOT/PJM/CAISO/NYISO 2025 carry
  the same national caveat; ISNE is hit hardest because its early-release skews
  hard to the large gas/nuclear monthly reporters.)
- **Demand is net load** (playbook §8.1): EIA-930 ISNE demand is net of MA/CT's
  material BTM PV wedge. Backcasts model front-of-meter resources only.

## 2. Fleet sanity — `get_iso_config("NEISO")` + ISNE BA filter

`load_fleet_from_csv("NEISO", get_iso_config("NEISO"))` (the per-plant EIA-860
path; wind/solar/hydro/storage load via their own machinery and are excluded
here):

- **431 LP generators, 199 distinct plants, 24,588 MW** fossil + nuclear:

| Class | MW | Units |
|---|---|---|
| gas_cc | 13,264 | 97 |
| **oil** | **5,182** | **135** |
| nuclear | 3,355 | 3 |
| gas_ct | 1,631 | 127 |
| biomass | 1,047 | 68 |
| coal | 108 | 1 |

- **Oil is the second-largest class (5,182 MW)** — the largest oil fleet of any
  ISO in the model, the defining ISO-NE winter feature. **Dual-fuel: 6,367 MW
  across 42 plants** carry an EIA-860 oil/gas switch flag — the gas→oil
  switching machinery P13 activates (doc-08 design decision 2).
- **Coal is essentially gone:** a single ~108 MW unit (Merrimack retired);
  confirms the doc-08 "no coal must-run layer" premise. (The
  `campd-unit-outages-NEISO.csv` carries a `COAL` group for this lone unit.)
- **Zone distribution (MW):** North 6,105 / Central 6,042 / Boston 3,770 /
  Connecticut 8,672 / HQ_import 0 (the import node, no in-area plants —
  correct). **No unassigned plants** (zero fallback-zone warnings).
- **States:** CT 8,669 MW (74 plants), MA 7,937 (64), NH 3,259 (20), ME 2,648
  (19), RI 1,875 (11), VT 197 (10), **NY 2 MW (1)** — Fishers Island (ORIS
  57600, a 2 MW island diesel off the CT coast, electrically ISO-NE; correct).
- **Pilgrim confirmed ABSENT** (retired 2019). The 3 nuclear units are
  Millstone 2 (863 MW) & 3 (1,245) in CT and Seabrook (1,247) in NH — ~3.4 GW,
  matching doc-08 design decision 6.

### 2a. Comparison vs published totals (ISO-NE CELT / FCM)

The fleet loader covers fossil + nuclear only; renewables, hydro, and storage
load through their own machinery (P4/P5/P6). Reconstructed nameplate:
fossil+nuclear 24.6 GW + wind 1.5 + solar 2.9 + hydro (~2 GW nameplate, ME/NH/VT
run-of-river) + Northfield Mountain + Bear Swamp PS (~1.7 GW) ≈ **~33 GW
nameplate**, consistent with the published ISO-NE fleet.

| Class | Model | Published benchmark | Verdict |
|---|---|---|---|
| Fossil + nuclear | 24,588 MW | ISO-NE FCM: ~28.5 GW generation cleared (FCA for 2027/28); ~31–34 GW total nameplate incl. hydro/VRE/storage | reconciles once companion fleets applied |
| Nuclear | 3,355 MW (3 units) | Millstone 2&3 + Seabrook, ~3.4 GW | ✓ Pilgrim retired |
| Wind | 1,536 MW (Dec-2023) | eGRID 2023 ISNE: 1,536 MW (923 CF cross-check 3.34 TWh) | ✓ |
| Solar | 2,924 MW (Dec-2023) | utility-scale only; large MA/CT BTM PV excluded (net-load) | ✓ direction |

Source: [ISO-NE CELT Reports](https://www.iso-ne.com/system-planning/system-plans-studies/celt);
[ISO-NE Key Grid and Market Stats](https://www.iso-ne.com/about/key-stats);
[ISO-NE Forward Capacity Auction (2027/28) results](https://isonewswire.com/2024/02/09/new-englands-forward-capacity-auction-closes-with-adequate-power-system-resources-for-2027-2028/)
(~28,478 MW generation cleared). Note: iso-ne.com returns 403 from this
environment (EIA/ISO hosts blocked, playbook §2), so the CELT per-state
capacity table could not be pulled directly; the headline FCM figure is from
the public ISO Newswire release, and the in-repo eGRID 2023 workbook
(`BACODE=ISNE`) serves as the EPA fleet benchmark.

### 2b. P13 dual-fuel / oil winter switching — activation & validation

The national dual-fuel machinery (`fleet.py::dual_fuel_plant_groups`, the `oil`
fuel type + `OIL` offer band, `fuel.py::apply_dual_fuel_pricing`) is **activated
and validated** for NEISO this session; no source change was needed beyond the
gating already in place (`dual_fuel_switching` on for the PJM + NE/NY winter
cluster, off for ERCOT/CAISO/MISO/SPP — `run_calibration._calibration_config`).

**1. Detection (EIA-860 Multifuel schedule).** `dual_fuel_plant_groups()`
flags every NG-primary unit with "Switch Between Oil and Natural Gas? = Y";
intersected with the loaded NEISO fleet this is **107 gas tranches / 6,367 MW
across 42 plants** — including Middletown and Montville Station (the doc-08
named CT/ST switchers). Oil-**primary** steam (Energy Source 1 = `RFO`/`DFO`)
is correctly *excluded* from the switch set and instead carried as `oil` fuel
type: **135 oil units / 5,182 MW**, led by William F Wyman (ME, 846 MW), Canal
(MA, ~1.45 GW RFO steam + DFO GT), New Haven Steam, Montville and Newington.
Note: **Mystic is retired** in the 2025 EIA-860 vintage (only a 1 MW PV site
remains under "BWC Mystic River") — it is correctly absent, not a detection
miss.

**2. The switch consumes the P7 overlay.** In `resolve_fuel_prices` the order is
`apply_hub_basis_overlay` → `apply_dual_fuel_pricing`, so a dual-fuel unit caps
the AGT-blown winter hub gas at delivered oil parity, i.e. `min(hub_gas, oil)`
× gas heat rate. Covered by `tests/test_fuel.py::
test_neiso_hub_overlay_drives_dual_fuel_switch` (a Jan AGT spike past parity
trips the dual-fuel unit to oil while a gas-only unit eats the full hub spike;
the shoulder month leaves both on gas).

### 2c. AGT-basis wiring bug + daily refinement (2026-06-16)

Two coupled fixes this session turned the AGT basis from documented-but-inert
into the dominant correct price driver it was always meant to be.

**A. The hub-basis overlay was never applied in the calibration dispatch.**
`resolve_fuel_prices` runs `apply_hub_basis_overlay` only inside its
`apply_monthly=True` branch, but `run_calibration.run_year` resolves fuel prices
with `apply_monthly=False` (so the coal-supply base lands before the per-plant
EIA-923 overwrite) and then re-applied *only* `apply_plant_monthly_fuel_prices`
and `apply_dual_fuel_pricing` — **never the hub overlay.** So every NEISO keeper
through P12/P14 priced gas at the EIA-923 ISO-month series (Jan-2025 gas
**$5.30/MMBtu**, not the AGT hub **$16.92**), and the dual-fuel switch capped
against that wrong gas — i.e. the AGT overlay and the §2b switch were dead code
in the calibration path. Because NEISO's ISO-month 923 series rests on only two
(partly LNG-priced) reporters, it was *over-priced* in most months and
*under-priced* in winter, so the dead overlay mis-set the price level in **both
directions**. Fix: `run_year` now calls `apply_hub_basis_overlay` between the
plant-monthly and dual-fuel passes, mirroring the `apply_monthly=True` order
(the overlay is idempotent and no-ops for non-NEISO, so ERCOT/PJM/CAISO/NYISO
stay byte-identical). Effect on the load-weighted hub price level (vs ISO-NE
.H.INTERNAL_HUB DA avg):

| year | prior keeper | overlay wired (keeper) | actual DA |
|------|-------------:|-----------------------:|----------:|
| 2023 | $53.61 (+46%) | **$34.41** | $36.82 |
| 2024 | $55.72 (+34%) | **$39.84** | $41.47 |
| 2025 | $54.31 (−20%) | **$68.52** | $67.86 |

Gas TWh also tightened to near-exact (within −1.3% of EIA-930 all years). This
supersedes the "level is at sign-off" finding in doc-08 — the prior price level
was wrong because the measured AGT data was being ignored.

The **keeper** (`neiso_agt_3yr`, one 2023–2025 bundle, neiso 13) rests on this
monthly overlay alone — no fitted parameter — with hydro 930-pinned uniformly
across years: gas within −1.3% of EIA-930, hydro 8.70/7.33/5.11 vs 930
8.77/7.39/5.12, load-weighted hub $34.4/$39.8/$68.5 vs actual DA
$36.8/$41.5/$67.9.

**B. Daily AGT basis — now real measured data, promoted into the keeper
(2026-06-24, neiso-27).** The ICE/Platts daily AGT spot is paywalled, but EIA
quotes the real Algonquin Citygate spot in the *prose* of every Natural Gas
Weekly Update ("…the price went up $9.31 from $4.04/MMBtu last Wednesday to
$13.35/MMBtu yesterday…"). `scripts/data/fetch_algonquin_daily_spot.py` harvests these
into `data/raw/gas-prices/algonquin_citygate_daily.csv` — **123 hard-dated real
AGT prints 2023–2025**, two Wednesdays per weekly page plus winter high/low days,
densest in the cold weeks that set the tail (max $28.36 on 2023-02-02). The
`gas_hub_basis_daily` path (`fuel.iso_hub_daily_gas_prices`) now anchors the
within-month AGT basis to these real prints (interpolated on their true calendar
days) and mean-preserves to the measured monthly basis; sparse-print months
borrow the measured Transco Z6 NY daily-basis within-month shape (AGT≈Transco
basis, measured slope ~0.95, corr ~0.79), capped at AGT's own measured price
ceiling so NY's more extreme vortex spikes (Transco $97.9 in Jan-2025) don't
over-amplify Boston. Gas-vs-gas validation (no electricity): MAE
$0.71/$0.74/$2.08, corr 0.98/0.96/0.65.

This **retires `AGT_DAILY_BASIS_CONVEXITY` (=7.0) and the `_neiso_daily_demand`
driver**, which redistributed the monthly basis by NEISO demand raised to an
exponent *chosen to reproduce the measured oil/>$200 counts* — a within-month
shape fitted to the answer it predicts (CLAUDE.md #12 violation), which is why it
could never be a keeper. The replacement is real, free, EIA-sourced,
forward-applicable gas-market data with no electricity/oil tuning, so the daily
overlay is now **on in the keeper** (`--gas-hub-basis-daily`). A/B vs the
monthly-basis control on current code (identical monthly mean): winter hours
>$200 **0/0/80 → 55/20/191** (measured ~44/11/160), oil burn **0.00/0.00/0.16 →
0.28/0.20/1.66 TWh** (EIA-930 0.32/0.37/1.24), pumped-storage discharge
**0.24/0.31/1.08 → 0.36/0.49/1.14 TWh**, system mean LMP preserved. The residual
>$300 scarcity tail (model 0h vs actual 15/8/20h) stays open — it is capped by
dual-fuel switching at oil parity, an offer-side structural item (single-fuel gas
at AGT spot; ORDC reserve scarcity), explicitly **not** to be closed by
re-tuning the now-measured gas input (run neiso-27 attestation exceptions ledger).

**3. Monthly-granularity limitation (documented, accepted in the keeper).** The
committed `gas_basis_by_iso_month.csv` is *monthly*, and monthly AGT averages
never reach distillate parity (~$18/MMBtu): max **Feb-2023 $8.1, Dec-2024 $9.1,
Jan-2025 $16.9** — all below oil, so on the flat monthly plateau the dual-fuel
CT/ST switch never binds (guarded by
`test_neiso_monthly_agt_basis_stays_below_distillate_parity`) and modeled winter
oil stays near zero. The keeper accepts this as the honest limit of
monthly-granularity data; only the opt-in daily proxy (2c-B) lifts the coldest
days past parity (264 gas-hours > $18 in Jan-2025).

### 2d. Oil generation re-attribution (off-by-default diagnostic, 2026-06-16)

The §2b dual-fuel switch is *objective-only*: a dual-fuel CC/CT that switches to
oil prices at `min(gas, oil)` but the LP still dispatches it on the gas
heat-rate and counts its MWh as **gas**, so the keeper's modeled oil sits near
zero (2023 0.00 / 2024 0.00 / 2025 0.06 TWh) below the EIA-930 `NG: OIL` column
(0.32 / 0.37 / 1.24) — the documented monthly-granularity limit (§2c-3). An
opt-in **re-attribution** (`dual_fuel_oil_reattribution`, rides
`--gas-hub-basis-daily`) relabels switched unit-hours as oil:
`fuel.dual_fuel_switch_mask` marks the generator-hours where the pre-cap gas
price exceeds oil parity (the counterpart of the `min` the switch writes),
threaded through `p2_state` into `_dispatch_frame`. It is LMP-neutral (a
generation relabel, not new energy) and **off in the keeper** — it only bites
with the daily overlay, and is gated NEISO-only regardless (PJM/NYISO dual-fuel
units also cross oil parity on their own winter gas — mask sums 10,416 / 4,104
gen-hours in 2024 — so enabling it there would move their gas/oil split and
break the ERCOT/PJM/CAISO byte-identical guard).

With the diagnostic on (daily overlay + re-attribution), modeled oil rises to
the right **order of magnitude** (from ~0):

| year | oil keeper | oil (diagnostic) | EIA-930 |
|------|-----------:|-----------------:|--------:|
| 2023 | 0.00 | **0.09** | 0.32 |
| 2024 | 0.00 | **0.15** | 0.37 |
| 2025 | 0.06 | **2.12** | 1.24 |

The cross-year fit is imperfect — 2023/24 under, 2025 over — because the
price-parity switch assumes a unit burns oil in *every* hour its delivered gas
exceeds oil, with no representation of **firm vs interruptible gas** (a
dual-fuel CC on a firm pipeline contract keeps burning gas even when AGT spot
tops oil) or **on-site oil inventory / air-permit limits** (which cap real
winter oil hours). The daily-basis proxy (§2c-B) also over-amplifies the
highest-basis year (2025), so its parity-hour count runs long. The
re-attribution conserves total thermal generation (gas+oil), so it is a relabel,
not new energy; CO2 still rides the gas characterization in `compute_emissions`
(static per-generator rates) — the oil-vs-gas delta on ~1–2 TWh of switched burn
is small (~1–2% of NEISO CO2) and is the documented residual. Precise oil
matching needs firm-gas-share / oil-inventory data (a new upload).

**4. Validation vs the EIA-923 oil column (2023 smoke,
`run_calibration --iso NEISO --year 2023 --hours 8760`):**

| Class | Model TWh | EIA-923 TWh | diff |
|---|---|---|---|
| **oil** | **0.24** | **0.39** | **−37%** |
| gas_ct | 1.67 | 1.89 | −12% |
| gas_st | 0.28 | 0.40 | −31% |

Modeled oil is **same order of magnitude** and **not near-zero** — the doc-08
red-flag test passes. It sits ~37% under the EIA target partly because gas_cc
over-runs in this pre-calibration smoke (69.3 vs 54.3 TWh; cheap gas displaces
oil at the margin), so oil should rise toward 0.39 TWh once the offer-curve /
import / gas-basis knobs are tuned in P11/P12. Citation target: the per-year
EIA-923 oil column in `data/raw/_validation-source/calibration_reference.json`
(`isos.NEISO.<year>.generation_twh.oil` = 0.39 / 0.31 / 0.91 TWh for
2023/24/25).

### 2e. Merrimack coal rank (COAL_BIT) + CC_REGULAR Jacobian re-derivation (2026-06-17)

**Merrimack classified bituminous (COAL_BIT), data-driven.** The lone NEISO coal
unit (ORIS 2364, Bow NH; Granite Shore Power) previously carried `supply = ''`
(unclassified) and fell to the generic `COAL` default for both delivered fuel
cost and offer-curve key. `scripts/data/derive_coal_supply.py --iso NEISO` — the same
EIA-923 Schedule-5 receipts machinery already used for PJM — sums the plant's
coal receipts (54,050 tons 2023-2025) and finds them **100 % bituminous**,
writing `data/raw/_processed-legacy/coal_supply_NEISO.csv` (`2364,bituminous,receipts`).
`fleet.coal_supply_class(2364)` now returns `bituminous`, so the dispatch class,
`offer_curve_by_group` key, and `_coal_supply_class` scorecard label all resolve
to **`COAL_BIT`**; the delivered cost stays `COAL_PRICE_BASE["NEISO"]` = 3.0 (the
bituminous-by-rail blend, already correct). EIA-860 confirms the
retirement/availability window: generator 1 (113.6 MW nameplate / 108 MW net
summer, `BIT`, status `OP`, planned retirement 2027) operates across all three
backcast years and generator 2 (345.6 MW, `BIT`, status `OS`) is out of service,
so the ~108 MW unit 1 produces the EIA-930 ISNE coal column (**0.18 / 0.24 / 0.28
TWh**) as a low-CF winter-peaking run — confirming coal is *not* zero. The
classification is **dispatch-neutral** (the `COAL_BIT` and generic `COAL` offer
curves are byte-identical and the delivered cost is unchanged): the keeper
`neiso_cc_coalbit_3yr` reproduces `neiso_agt_3yr` to the TWh (coal 0.0145 / 0.00 /
0.237, well inside the size-aware ±1 TWh band), only now scored against the
bituminous benchmark.

**CC_REGULAR offer-curve Jacobian, re-seeded on the wired structure.** The prior
Jacobian/dead-knob panel was derived **before** the AGT overlay was wired into the
dispatch (§2c), so it is stale: its anchor (CC_REGULAR 55.31 / CT_PEAKER 0.336)
differs from the wired keeper (56.56 / 0.014). Fresh ±0.05 single-knob probes
(`results/calibration/neiso_probe_v2_*`, base reproduces the keeper exactly) give
the corrected sensitivity (2024, P2, ΔTWh): econ_high ±0.05 → ∓0.061/+0.070
CC_REGULAR; econ_low +0.05 → −0.048; committed +0.05 → −0.012. The **live**
CC_REGULAR bands are econ_high > econ_low > committed, but **every one
redistributes only within the CC family (CC_REGULAR ↔ CC_CHP) and to the measured
import schedule — none reaches CT_PEAKER, ST_GAS, or oil** (ST_GAS is dead to its
own committed knob). The cause is structural: CC base HR ≈ 7.0 vs CT/ST ≈ 10.4, so
CT_PEAKER's cheapest tranche (committed 1.55 × 10.4 ≈ 16.1 eff-HR) sits above
CC_REGULAR's whole economic curve including the duct-fire fold (peak 2.25 × 7.0 ≈
15.8). The "CC over-cheap" symptom is therefore correct behaviour (CC genuinely is
the cheapest gas, ~95 % of the EIA-923 prime-mover split); the CT_PEAKER (~2 TWh)
/ ST_GAS (~0.3) gap is reserve / AS / load-pocket deployment the energy-only
4-zone LP does not reproduce, recoverable only by the off-by-default
`ct_deployment` overlay (NEISO wedge ≈ 0.05 TWh, §`Cross-ISO` in calibration-log),
**not** offer-curve tunable. The CC_REGULAR curve is held at the keeper values.

**CT_PEAKER reserve recovered via the ct_deployment overlay (keeper neiso 16).**
The one sanctioned lever for the CT gap — the targeted `ct_deployment` overlay
(`scripts/data/derive_ct_deployment.py --iso NEISO` →
`data/raw/_validation-source/ct_deployment_floor_NEISO.parquet`, wedge 0.08/0.04/0.05 TWh)
— floored CT correctly in P1 but was **stripped by the P2 commitment screen**
because `commitment.apply_commitment_with_coal_pin` rebuilt the P2 fleet without
`min_gen`. Fixed by carrying `min_gen` through P2 under a `preserve_min_gen` gate
that is active **only** when a deployment overlay is set (default-off; the
forecast runner and every non-overlay keeper stay byte-identical, verified on
NEISO base 2024). With `--ct-deployment` the keeper `neiso_ctdeploy_3yr`
(neiso 16) lifts CT_PEAKER 0.014/0.014/0.038 → **0.084/0.052/0.079 TWh** with the
gas total and price level unchanged (the CT energy displaces CC within gas, not
coal/imports). The residual CT (~2 TWh) / ST_GAS (~0.3) / oil gap is the
documented non-offer-recoverable reserve / winter-monthly-data limit. See
calibration-log 2026-06-17.

## 3. CEMS coverage

Distinct states of NEISO-fleet **fossil** plants and the diff against
`data/raw/campd-unit-level/<ST>_<year>.parquet`:

| State | Plants | MW | CEMS present | Missing |
|---|---|---|---|---|
| CT | 67 | 6,421 | 2023, 2024, 2025 | — |
| MA | 53 | 7,675 | 2023, 2024, 2025 | — |
| ME | 8 | 2,305 | 2023, 2024, 2025 | — |
| NH | 9 | 1,830 | 2023, 2024 | **2025 (upload U1)** |
| RI | 8 | 1,835 | 2023, 2024, 2025 | — |
| VT | 6 | 118 | 2023, 2024, 2025 | — |
| NY | 1 | 2 | 2023, 2025 | 2024 (Fishers Island, 2 MW — immaterial) |

- **Expected gap confirmed: `NH_2025`** is the one missing extract (doc-08
  U1) — the only 2025 CEMS gap. NH 2025 (1,830 MW, ~7% of fossil) runs on
  statistical availability until it lands; CT/MA/ME/RI/VT 2025 are complete.
- `campd.ISO_STATES["NEISO"] = ("ME","NH","MA","CT","RI","VT")` — the 2 MW
  NY/Fishers Island unit is outside the scope and immaterial.
- Unit-outage windows `campd-unit-outages-NEISO.csv` are already derived and
  **complete for all three years** (start-year counts: 2023 = 431, 2024 = 452,
  2025 = 422; 34 facilities; groups CC_REGULAR/CC_CHP/CT_CHP/ST_GAS + the lone
  COAL unit). P1 verifies; a `--iso NEISO` rerun folds NH 2025 in once U1 lands.

## 4. Upload manifest status (doc-08 U1–U7)

| # | Item | Destination | Status |
|---|------|-------------|--------|
| U1 | CAMPD unit-level `NH_2025.parquet` | `data/raw/campd-unit-level/` | **missing** — the only 2025 CEMS gap; CT/MA/ME/RI/VT 2025 + all 2023/2024 present |
| U2 | DA+RT hourly Hub + zonal LMP (NEMA/Boston, CT, SEMA, ME) 2023–2025 | `data/raw/lmp-data/NEISO/` | **missing** — needed by P10; price calibration is level-only without it |
| U3 | Zonal hourly load (8 ISO-NE zones) 2023–2025 | `data/raw/zone-specific-demand/NEISO/` | **missing** — zonal load stays on static RSP shares (0.20/0.30/0.21/0.29) until landed (P8) |
| U4 | Algonquin Citygate (AGT) delivered gas basis 2023–2025 | cite into `constants.py` / gas path | **partial (done as available)** — per doc-08 §P7, the ISO-NE MA gas index satisfies 35/36 months 2023–2025 in `data/raw/gas_basis_by_iso_month.csv` (Aug-2025 missing upstream, falls back to 923/shaped). The single most important NEISO upload — drives winter spikes + the dual-fuel switch (P13) |
| U5 | RGGI allowance prices 2023–2025 (optional) | cite into `STATE_CARBON_PRICE_BY_ISO` | **satisfied (web-search)** — done by P7: `STATE_CARBON_PRICE_BY_ISO["NEISO"]` active default-on |
| U6 | North–South / Boston-Import / CT-Import interface flows + limits (optional) | `data/raw/iso-specific-transmission/NEISO/` | **missing** — TTCs stay on Tier-3 RSP seeds (P10 validation) |
| U7 | HQ Phase II HVDC + Highgate + Cross-Sound scheduled flows (optional) | `data/raw/iso-specific-transmission/NEISO/` | **missing** — EIA-930 carries net interchange; priced-node refinement only (P9) |

U2 unblocks price calibration; U4 (largely landed) + P13 are the winter
make-or-break. The Stage-E reference and fleet/CEMS audit are complete now.

### Already done by earlier NEISO packs (for reference)

- **P7 (2026-06-11, doc-08):** `GAS_BASIS_DIFFERENTIAL["NEISO"]` (+1.10 seed),
  RGGI in marginal cost (`STATE_CARBON_PRICE_BY_ISO["NEISO"]`, 2023–2025,
  default-on), Algonquin winter basis via `gas_hub_basis_overlay` (35/36
  months), `gas_monthly_actuals` default-on.
- **P13 (2026-06-11, doc-08):** dual-fuel/oil winter switching activated and
  validated for NEISO — `dual_fuel_switching` default-on, the switch consumes
  the P7 AGT overlay (`apply_hub_basis_overlay` runs before
  `apply_dual_fuel_pricing` in `resolve_fuel_prices`, so the dual-fuel cap sees
  the blown-out hub gas). See §2b for the validation finding.
- **Outage windows (P1 scope):** `campd-unit-outages-NEISO.csv` complete for
  2023–2025 (§3); `ISO_STATES["NEISO"]` set.

## 5. Present and verified (do not re-acquire)

- `data/eia_hourly/ISNE hourly.parquet` (demand/fuel/interchange); neighbor
  `NYIS` parquet for the seam.
- CAMPD unit-level CT/MA/ME/RI/VT 2023–2025 + NH 2023–2024; derived
  `campd-unit-outages-NEISO.csv` (2023–2025 complete).
- EIA-860 (incl. multifuel/storage tables), EIA-923 zips 2023/2024/2025,
  eGRID 2023 workbook, Henry Hub series — all national, in-repo.
- Topology/config: `_neiso_config()` (4 zones + HQ_import node + interface
  links), FIPS state→zone assignment, `MarketDesign("NEISO",
  capacity_market=True, net_cone=95)` (FCM), `voll=2000`,
  `FLEET_AVAILABILITY["NEISO"]=0.85`, generalized import-node machinery, and
  the P7 gas/RGGI/AGT-basis wiring above.
- Calibration reference + NEISO 2023/2024/2025 renewable CSVs (this session).

## 6. Out-of-scope observations for the backlog

- ERCOT/PJM calibration-reference staleness vs the new `Northeast` zone +
  EIA-860 vintage (§1b) — ERCOT/PJM-owned re-baseline.
- 2025 EIA-923 early-release respondent coverage (§1c) — national; ISNE hit
  hardest. Re-run on the final file.
- `tests/test_eia_loader.py::test_caiso_zonal_shares_fall_back_without_file`
  and `::test_caiso_zone_rows_are_static_share_split` fail on a clean checkout
  (CAISO zonal-share float tolerance) — pre-existing, unrelated to this change
  (941 other tests pass).
