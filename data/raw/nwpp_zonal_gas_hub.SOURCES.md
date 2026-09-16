# `nwpp_zonal_gas_hub.csv` — SOURCES

Landed **2026-09-14** by lane **NWPP-33**
(`docs/multi-iso/nwpp-addition-plan-2026-09.md` §5 row NWPP-33; FINDING
`docs/handoffs/FINDING-nwpp-33-2026-09-14.md`). Schema is exactly the
MISO / PJM / CAISO / ERCOT / SPP one (`zone,year,basis_vs_hh_usd_mmbtu,hub,source`),
so `market_sim.data.fuel.basis.meanzero._load_zonal_gas_hub` reads it with no new
parsing code. Derived by `scripts/data/derive_nwpp_zonal_gas_hub.py`.

## 1. Why this footprint gets a per-zone table at all

NWPP-12 measured a **2.51× internal gas spread** — NorthWestern Montana burns gas
at 40 % of the price PacifiCorp East does (`data/raw/gas-prices/SOURCES_nwpp_gas.md`
§1). A single `NWPP` hub is not a simplification but an error the size of the fuel
cost itself.

## 2. Where the numbers come from — and why NOT a hub series

Every sibling table proxies its zones with a published **hub** or a per-**state**
EIA series. NWPP neither can nor needs to.

**Cannot.** NWPP-12 established, rather than assumed, that **Stanfield, Opal and
Kern River have no free public daily or monthly series reachable from this repo**:
EIA's Natural Gas Weekly Update spot table carries four points (Henry Hub, New
York, Chicago, Cal. Comp. Avg.) and a string search of the rendered page returns
zero hits for all three; EIA's dnav spot series is Henry Hub only; and
`eia.gov/naturalgas/xls/ice_natgas-2023final.xlsx` is 404. Only **Sumas** is
committed (`gas-prices/sumas_weekly.csv`), and it prices one of the five zones.
Synthesising the other three from a neighbouring hub is the substitution rule 13
`[R-MEASURED]` forbids and plan gate **G17** refuses by name.

**Does not need to.** The finest-grain measured input is already committed:
`data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet` (EIA-923 Schedule 2),
per plant per month, `price_per_mmbtu` and `quantity`. Under rule 14 `[R-ACCURATE]`
the delivered price the zone's own plants actually paid beats a state proxy for a
state that is 30 % of the zone — which is what `SPP-North` has to live with.

**Coverage is complete, which is why there is no fallback rule to document:**

| Zone | plants/yr (2023 / 2024 / 2025) | months covered | MMBtu 2023-2025 |
|---|---|---|---:|
| NWPP-NW | 7 / 7 / 5 | 12 / 12 / 12 | 232,604,506 |
| NWPP-OR | 5 / 5 / 4 | 12 / 12 / 12 | 220,225,562 |
| NWPP-INLAND | 3 / 4 / 4 | 12 / 12 / 12 | 83,899,124 |
| NWPP-EAST | 5 / 6 / 6 | 12 / 12 / 12 | 295,161,866 |
| NWPP-SNV | 10 / 10 / 11 | 12 / 12 / 12 | 481,342,696 |

(The MMBtu column reproduces NWPP-12's §1 table exactly — an independent
re-derivation of that lane's measurement from the same committed bytes.)

## 3. The construction — one rule, no per-zone and no per-year choices

```
price_z,m = Σ_p price_{p,m} · quantity_{p,m} / Σ_p quantity_{p,m}
basis_z,y = mean over the 12 months m of ( price_z,m − HenryHub_m )
```

Quantity-weighting **within** a month is what the zone actually paid that month;
averaging the twelve monthly *basis* values **equally** is the month-balanced
convention every sibling table uses, so a heavy-burn winter cannot pull the annual
level toward the winter basis. Henry Hub is the committed
`gas-prices/henry_hub_monthly.csv`. Plants reach zones through
`zone_assignment.build_zone_lookup("NWPP")` — the ruled BA-keyed map (owner ruling
N5), the same key the fleet and the renewable capacity use.

## 4. The table, and what actually reaches a solve

| Zone | 2023 | 2024 | 2025 | Hub |
|---|---:|---:|---:|---|
| NWPP-NW | 2.682 | 0.847 | −0.282 | Sumas / Northwest Pipeline |
| NWPP-OR | 2.454 | −0.240 | −1.301 | Stanfield / GTN |
| NWPP-INLAND | 2.143 | 0.223 | −0.952 | **MIXED** — see §6 |
| NWPP-EAST | 5.272 | 0.774 | −0.173 | Opal / Rockies |
| NWPP-SNV | 4.654 | 0.734 | −0.091 | Kern River |

The **level never reaches a solve**: the mean-zero applier re-centres to a
gas-capacity-weighted mean of zero (the PJM / MISO / CAISO / ERCOT convention), so
only the cross-zonal spread can move dispatch. Equal-weight re-centred spread:

| Year | min .. max | range |
|---|---|---:|
| 2023 | −1.298 .. +1.831 | 3.129 $/MMBtu |
| 2024 | −0.708 .. +0.379 | 1.087 |
| 2025 | −0.741 .. +0.469 | 1.210 |

## 5. STATED LIMITATION: the 2023 row is a one-month-dominated annual mean

The **western winter 2022-23 gas event** puts January 2023 far above every other
month of the span, against a $3.27 Henry Hub:

| Zone | Jan 2023 $/MMBtu | full-year basis | **January-excluded basis** |
|---|---:|---:|---:|
| NWPP-EAST | 39.66 | 5.272 | 2.443 |
| NWPP-SNV | 34.61 | 4.654 | 2.229 |
| NWPP-OR | 21.38 | 2.454 | 1.031 |
| NWPP-NW | 18.30 | 2.682 | 1.559 |
| NWPP-INLAND | 15.41 | 2.143 | 1.234 |

**The month is real and it is not removed.** It is a documented physical market
event, and dropping a month because it is inconvenient is exactly the
residual-driven selection rules 1 `[R-STRUCT]` and 13 forbid. The
January-excluded column is printed here so the distortion is **visible rather
than buried**, and it is carried in each 2023 row's own `source` string — it is
not an alternative value and must not be substituted for one.

**The event does not merely scale the spread — it re-ranks part of it**, which is
worth stating because it is the reason the caveat is a caveat and not a footnote.
The two dear zones stay dear and in the same order either way (EAST then SNV), but
`NWPP-OR` and `NWPP-INLAND` **swap for cheapest zone**: on the full-year 2023
basis INLAND is cheapest (2.143 against OR's 2.454), on the January-excluded one
OR is (1.031 against INLAND's 1.234). A consumer that cares about the bottom of
the 2023 merit order should read this row knowing that.

## 6. STATED LIMITATION: `NWPP-INLAND` is genuinely MIXED and is labelled so

| Member | $/MMBtu 2023-2025 | MMBtu | Pipeline |
|---|---:|---:|---|
| NWMT | **1.815** | 20,214,617 | GTN + NorthWestern's own LDC |
| IPCO | **3.903** | 63,684,507 | Northwest Pipeline (Williams / Rockies) |

**2.15×, inside one zone.** The zone's own average describes neither member. The
`hub` column therefore reads `MIXED: …` and names both halves rather than
resolving to the larger one — picking the larger half silently is precisely what
this lane was chartered not to do. Splitting the zone is a **zoning** change, which
is owner-ruled territory (card N5, and gate G18 bars any zone finer than a whole-BA
group anyway), so the caveat is declared, not fixed. It is the same class of
limitation `SPP-North` carries on its 30 % Kansas proxy, and it is larger.

## 7. `NWPP-EAST`'s attribution is NO LONGER PROVISIONAL

`nwpp-data-audit.md` §7.2 flagged 1,174.1 MW of PACE gas filed as *"Other — please
explain in pipeline notes below"* and asked a follow-up to read those notes. This
lane read them off the committed `eia860_plant.parquet`:

| Plant | MW | `Pipeline Notes`, verbatim |
|---|---:|---|
| Jim Bridger | 1,164.1 | *"Jim Bridger Units 1 and 2 recieve their gas supply from Williams Gas Supply. The units are owned by PacifiCorp and Idaho Power."* |
| Hurricane City Power | 10.0 | *"Enbridge (formerly Dominion Energy)"* — i.e. Questar's successor |

With Questar's own 152.4 MW and Colorado Interstate's 2.2 MW that is **1,328.7 of
1,695.3 named MW (78.4 %) on the Rockies complex**, against Kern River 217.0 and
Northwest Pipeline 144.0. **Opal / Rockies is confirmed for `NWPP-EAST`.**

The separate gap the audit names stays open and is not this table's: **5,518.0 MW
(23.7 %) of footprint gas names no pipeline at all** in EIA-860. That is an
attribution gap in the *hub label*, not in the *prices* — every row above is a
delivered price the plants actually paid.

## 8. NO APPLIER IS ARMED FOR NWPP

This is a registered path and a measured table, not a mechanism. Registering the
path constant (`meanzero.NWPP_ZONAL_GAS_HUB_PATH`) and any applier lives under
`src/`, outside lane NWPP-33's boundary, so **no `ScenarioConfig` field was added,
nothing reads this yet, and no keeper's `cache_key` moves** (plan §7 gate G8) —
the same posture SPP-32 landed its own table in. Arming is routed to NWPP-DESK;
see FINDING §5.

## 9. Regeneration

`python scripts/data/derive_nwpp_zonal_gas_hub.py` (`--dry-run` to report only).
Both inputs are committed, so this regenerates offline with no fetch and no API key.
