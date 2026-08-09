# CAISO capacity-market-demand-curve (documented fixed proxy — no curve)

Drop the retrieved unified CSV here as **`caiso.csv`**. CAISO has no
centralized capacity auction or sloped demand curve (bilateral Resource
Adequacy). Only two scalar metrics apply:

- **metric:** `soft_offer_cap` (CAISO's Capacity Procurement Mechanism (CPM)
  price cap — tariff-published), `ra_report_price` (CPUC's annual Resource
  Adequacy Report observed bilateral price, where published), `ra_mpb` (CPUC's
  PCIA Resource Adequacy Market Price Benchmark — see "The three metrics are
  three different objects" below).
- No `curve_point` rows — there is no curve; `point_index`/`x_value`/`x_unit`
  stay blank for every row.
- **delivery_year:** calendar year.
- **y_unit:** likely `usd_per_kw_month` or `usd_per_kw_yr` — record whichever
  the source actually publishes, do not convert.

## Authoritative sources

- CAISO Tariff / Business Practice Manual for Reliability Requirements (CPM
  soft offer cap): https://www.caiso.com/documents/ (search "Capacity
  Procurement Mechanism soft offer cap")
- CPUC Resource Adequacy Report: https://www.cpuc.ca.gov/industries-and-topics/electrical-energy/electric-power-procurement/long-term-procurement-planning/resource-adequacy-homepage

**STATUS:** `caiso.csv` committed — CPM soft-offer cap for 2023-2025
($6.31/kW-month through 2024-05-31, $7.34/kW-month from 2024-06-01 per FERC
Docket ER24-1225-000) and CPUC RA Report bilateral prices for 2023-2025 (system
weighted-average plus the 2023 product breakdown: all-RA/local/flexible/
system-incl-import), from the CPUC 2023 Resource Adequacy Report (published
2025-08, the most current comprehensive CPUC RA report as of this intake).
Monthly-granularity RA prices (e.g. the Sept 2023 seasonal-peak spike to
$24.07/kW-month) were fetched but not transcribed — this schema's grain is
annual; see `docs/handoffs/capacity-market-intake-2026-07.md` if the monthly
series is wanted later.

**STATUS 2026-08-09 (FFR-4F):** `ra_mpb` rows added for delivery years 2025
(Final, $11.21/kW-month) and 2026 (Forecast, $11.53/kW-month), from the CPUC
Energy Division "Market Price Benchmark Calculations 2025" (issued 2025-10-01),
committed alongside as `cpuc-market-price-benchmarks-2025.pdf` so the numbers
are re-derivable without a re-fetch (this closes, for this datatype, the
FFR-4D D-7 "source PDF not committed" weakness).

## The three metrics are three DIFFERENT objects — never interchangeable

This is the load-bearing distinction for anything that prices CAISO capacity,
and getting it wrong is what FFR-3W §2.3 measured:

| metric | what it actually is | contains capex? | who is paid it |
|---|---|---|---|
| `soft_offer_cap` | administrative **CEILING** on what a CPM-designated resource may **offer** into CAISO's backstop procurement. Derived as the **going-forward fixed cost of a 550 MW existing COMBINED-CYCLE reference unit × 1.20** (FERC ER24-1225). Resources may offer *above* it only by cost-justifying to FERC **on their own going-forward fixed costs, using the same cost categories** | **No** — going-forward cost is FOM + sustaining capital by construction | nobody, in the ordinary market; it bounds a rarely-used backstop (5 designations ≈ 256 MW in all of 2023, every one clearing *at* the cap — see `../../auction-price/caiso/`) |
| `ra_report_price` | CPUC RA Report **retrospective** transacted weighted average, split by RA product (system / local / flexible / all) | n/a — a transacted price | every RA seller, for a **past** compliance year |
| `ra_mpb` | CPUC PCIA **Market Price Benchmark**: volume-weighted average of **all** IOU/CCA/ESP RA transactions for a stated **delivery** year; unified to a single RA value by D.25-06-049; issued each October under D.22-01-023 | n/a — a transacted price | every RA seller, for the stated delivery year (incl. **forward** years) |

**CAISO publishes no net-CONE and no new-entry capacity price.** It runs no
centralized capacity auction and no sloped demand curve, so there is no
net-CONE by technology to intake — the `net_cone` metric is structurally
absent for this ISO, not merely un-fetched. Any model term that needs "the
price CAISO capacity is paid" must come from `ra_mpb` (forward) or
`ra_report_price` (retrospective); `soft_offer_cap` answers a different
question and must not be used for it.

### Deliberately NOT transcribed

The same source page carries **legacy** per-product, per-IOU RA MPBs under the
methodology D.25-06-049 superseded (2024 Final System $28.65 / Flexible $12.89
/ Local $12.22–17.21; 2025 Forecast System $42.54 / Flexible $14.16 / Local
$9.99–13.29). They are **not** transcribed, for two reasons: they are
superseded by the unified methodology, and their per-IOU column alignment is
not unambiguous in the source's merged-cell table layout. Recording them would
be a guess about which column a spanning cell belongs to — rule 5. The PDF is
committed, so a later session that needs them can read the layout directly.
