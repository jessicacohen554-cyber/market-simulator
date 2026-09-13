# NWPP gas basis — which hub prices which zone, and what is actually reachable

Landed **2026-09-13** by lane **NWPP-12**
(`docs/multi-iso/nwpp-addition-plan-2026-09.md` §5 row NWPP-12, item 6; FINDING
`docs/handoffs/FINDING-nwpp-12-2026-09-13.md`).

**This lane landed NO new price file.** It establishes (a) that a single hub
cannot price this footprint, with the spread measured; (b) which hub each card
N5 zone prices against; (c) which of those hubs has a free public series
reachable from this session and which do not; and (d) what is already committed
in this directory and elsewhere that covers the gap. A consumer wiring
`NWPP` fuel should read this before adding a series.

## 1. The finding that decides the design: this footprint has a 2.5× internal gas spread

Measured this session off the committed
`data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet` (EIA-923
Schedule 2, per-plant monthly delivered fuel price and quantity), restricted to
plants whose EIA-860 balancing authority is one of the 17 footprint BAs, over
**2023–2025** (1,524 rows, 38 plants), quantity-weighted:

| Card N5 zone | Natural gas, $/MMBtu | MMBtu burned |
|---|---:|---:|
| **NWPP-INLAND** | **3.400** | 83,899,124 |
| **NWPP-OR** | **3.267** | 220,225,562 |
| **NWPP-NW** | **4.092** | 232,604,506 |
| **NWPP-SNV** | **4.513** | 481,342,696 |
| **NWPP-EAST** | **4.564** | 295,161,866 |

and, per balancing authority — which is where the spread really shows:

| BA | Zone | $/MMBtu | MMBtu |
|---|---|---:|---:|
| **NWMT** | INLAND | **1.815** | 20,214,617 |
| PGE | OR | 3.267 | 220,225,562 |
| PSEI | NW | 3.749 | 107,215,945 |
| IPCO | INLAND | 3.903 | 63,684,507 |
| BPAT | NW | 4.386 | 125,388,561 |
| NEVP | SNV | 4.513 | 481,342,696 |
| PACE | EAST | 4.564 | 295,161,866 |

**NorthWestern Montana burns gas at 40 % of the price PacifiCorp East does — a
2.51× spread inside one model footprint.** A single `NWPP` gas hub is therefore
not a simplification, it is an error of the size of the fuel cost itself, and
card N5's five zones are the minimum granularity a gas price can be attached at.
Note also that `NWPP-INLAND`'s zone average (3.400) sits between its two
members' values (NWMT 1.815, IPCO 3.903) and describes neither.

*(Rule 13 `[R-MEASURED]` posture: these are measured **input** prices — delivered
fuel cost, a physical/market input that regenerates for a forward year from
forward drivers — not a measured outcome and not a calibration target. They are
reported here as evidence for a design choice, not written into any config.)*

## 2. The hub for each zone, and what is reachable

The four candidate hubs the charter named, against the zones they price:

| Hub | Prices which card N5 zone(s) | Free public series reachable from this session? |
|---|---|---|
| **Sumas** (Northwest Pipeline at the BC border) | **NWPP-NW** — *"the main pricing point for natural gas in the Pacific Northwest"* in EIA's own words | **YES — already committed.** `sumas_weekly.csv` in this directory (124 rows, 2023→), scraped from the EIA Natural Gas Weekly Update narrative by `scripts/data/fetch_sumas_weekly.py` |
| **Stanfield** (Northwest Pipeline / GTN interconnect, eastern Oregon) | **NWPP-OR**, and the GTN-served part of **NWPP-INLAND** (AVA, NWMT) | **NO** — see §3 |
| **Opal** (Wyoming; Kern River / Northwest Pipeline) | **NWPP-EAST** and the Williams-served part of **NWPP-INLAND** (IPCO) | **NO** — see §3 |
| **Kern River** delivered | **NWPP-SNV** | **NO** — see §3 |

> **The zone→hub column above is a physical-geography reading, not a quotation
> from a source in this repo.** It is offered to NWPP-33 (which owns the zonal
> gas hub) as a starting hypothesis, and it is **testable against §1**: the
> measured ordering (INLAND/OR cheapest, EAST/SNV dearest, NWMT far cheapest of
> all) is consistent with it, but consistency is not proof. NWPP-33 should treat
> §1 as the evidence and this column as the hypothesis.

## 3. What is NOT reachable, established rather than assumed

**Stanfield, Opal and Kern River have no free public daily or monthly series
reachable from this session.** Checked 2026-09-13:

- **EIA's Natural Gas Weekly Update** (`https://www.eia.gov/naturalgas/weekly/`,
  200, 115,146 B) carries a compact spot-price table of **four** points only —
  Henry Hub, New York, Chicago and "Cal. Comp. Avg." (itself *"Avg. of NGI's
  reported prices for: Malin, PG&E Citygate, and Southern California Border
  Avg."*). A string search of the rendered page for `Sumas`, `Opal`,
  `Kern River`, `Stanfield`, `Rockies`, `Cheyenne` and `Northwest` returns
  **zero hits in the table**; Sumas appears only in the weekly *narrative*, which
  is exactly why `fetch_sumas_weekly.py` parses prose rather than a table.
- **EIA's dnav natural-gas spot series** publishes Henry Hub only.
- `https://www.eia.gov/naturalgas/xls/ice_natgas-2023final.xlsx` — **404**.
  (The electricity counterpart, `electricity/wholesale/xls/archive/
  ice_electric-2023final.xlsx`, is 200 and is the plan §2.6 Mid-C source; there
  is no natural-gas twin at that path.)

Stanfield, Opal and Kern River are quoted by **NGI** and **Platts**, both
proprietary. Note the licensing caveat this directory's `README.md` already
carries: the NGI-derived series EIA merely *displays* (`algonquin_citygate_daily`,
`caiso_citygate_daily`, `miso_citygate_daily`, `transco_z6_*`) are flagged for
owner review in `docs/data-licensing.md` §5 — `sumas_weekly.csv` comes from the
same EIA narrative and inherits the same open question. **This lane does not
resolve that finding and does not add to the class.**

## 4. What is already committed and covers the gap — use this, not a guess

Two series already in the tree cover every NWPP state and plant, and under
rule 14 `[R-ACCURATE]` they are the *accurate* input a hub proxy would be
standing in for:

1. **`eia_delivered_gas_electric_power_by_state_monthly_2018-2026.csv`** (this
   directory) — EIA `N3045<ST>3`, delivered-to-electric-power price, $/Mcf,
   monthly, **all 50 states**, 2018-01 … 2026-06. Covers **WA, OR, ID, UT, WY,
   MT, NV**. Provenance and consumer caveats:
   `SOURCES_eia_delivered_gas_electric_power_by_state.md`.
   **Coverage warning that bites here specifically:** that file's own coverage
   note lists **OR and WA among the states whose 2025 is thin**, so an NWPP
   2025 backcast month may fall back to `N3045US3`. Check before relying on it.
2. **`data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`** — the
   per-plant monthly delivered price used for §1 above
   (`year, month, plant_id, state, fuel_group, price_per_mmbtu, quantity`). This
   is the finest grain available and it is already how `data/fuel/plant_prices.py`
   prices gas plants under `gas_plant_monthly_fuel_pricing`.

**Recommendation to NWPP-33 (recommend, do not decide):** price NWPP gas from
the **per-plant EIA-923 series**, with the per-state `N3045` table as the
documented fallback where a plant-month is missing, and carry **Sumas** only as
the NW zone's published hub for shape. Do **not** synthesise a Stanfield, Opal
or Kern River series from a neighbouring hub — that is the load-proxy
substitution rule 13 forbids and plan §2.6 gate **G17** refuses by name for
prices; the same logic applies to fuel.

## 5. One number for the seam, from a participant's own filing

PacifiCorp's 2025 IRP models a **Wyoming market hub** for gas-adjacent reasons
and states its own limiting assumption (Vol. 1 printed p. 189, footnote 8):
*"In light of the restrictions on the types of market products that can count
toward WRAP capacity requirements, PacifiCorp's modeling does not count any
short-term market products toward WRAP compliance and has limited market
purchases at all points during the highest load conditions in each month, to
represent potential market liquidity limits."* Recorded because a lane reading
the same hub structure should know the operator treats its liquidity as bounded.
