# NEISO (ISO-NE) Day-Ahead Energy Market SUBMITTED demand bids + cleared demand

Two ISO Express reports (both need the report page's `isox_token` cookie):

**Submitted book** — *Day-Ahead Energy Market Demand Historical Demand Bid
Report*, one operating day per file (~2.3 MB):

    https://www.iso-ne.com/transform/csv/hbdayaheaddemandbid?start=YYYYMMDD

Per (hour, masked participant, masked location, Bid ID): Location Type
(LOAD ZONE / NETWORK NODE / HUB / DRR AGGREGATION ZONE), **Bid Type** and up
to **50 (price, MW) segments**:

| Bid Type | what it is | price axis |
|---|---|---|
| `FIXED` | price-insensitive physical demand | none (MW only) |
| `PRICE` | price-sensitive physical demand | yes |
| `DEC`   | virtual load (decrement bid) | yes |
| `INC`   | virtual supply (increment offer) | yes |

This is the **submitted** curve, not a cleared one — the nyiso-94 blocker that
killed NYISO's DA-depth lane does **not** bind at NEISO (neiso-76 K3(i);
measured on 2023 / 2024 / 2025 days, all four bid types present in every
sampled day, 165-219 GWh/day of priced segment MW). The report carries **no
cleared-MW column**, so the ladder semantics (incremental vs cumulative MW)
cannot be identified the way MISO's file allowed; the companion cleared
series below is what a successor must identify against.

**Cleared quantity** — *Day-Ahead Energy Market Hourly Demand Report*
(hourly DA cleared demand MWh; a bare `?start=` 500s — pass a range):

    https://www.iso-ne.com/transform/csv/hourlydayaheaddemand?start=YYYYMMDD&end=YYYYMMDD

## Layout

    hbdayaheaddemandbid_<YYYYMMDD>.csv      # submitted book, one per day
    cleared_<start>_<end>.csv               # cleared demand, one per month

Both are **gitignored** (the NYISO-archive push-limit precedent). Regenerate
with the committed probe — which pulls the neiso-76 Phase-0 sample (the 15th
of every month 2023-2025 plus the five 2025 C3c event days, 41 days):

    python scripts/probes/_neiso76_demand_limb.py --fetch

Known source gaps: the endpoint returns an empty report for a subset of days,
the same publication pattern the sibling `da-energy-offers/` README documents.

Rule 13: prices here are a measured market input on the bid side and the
validation target on the cleared side; nothing derived from them is armed in
any solve. Coverage policy: train years 2023-2025 only (CLAUDE.md rule 22).

DATA NEEDED: none beyond the public reports.
