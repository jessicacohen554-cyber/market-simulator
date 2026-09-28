# `seam-neighbour-price/` — hourly prices at both ends of NYISO's external seams

Intake for NYISO-NEXT-10 (2026-09-28). NEXT-7
(`docs/FINDING-nyiso-next7-star-node-2026-09-27.md` §3(c)) refused a
per-neighbour NYISO seam construction because the repo held no price on the
**neighbour** side of any NY tie. This tree holds, 2021–2025, the NY-side price
at every proxy bus and zone and each neighbour's own price at the node facing
New York. Curated to the `seam-neighbour-price` clean datatype
(`scripts/data/curate_seam_neighbour_price.py`, schema
`data/dictionary/schema/seam-neighbour-price.schema.yaml`).

| dir | publisher | nodes | markets | coverage | committed? | fetcher |
|---|---|---|---|---|---|---|
| `nyiso/` | NYISO MIS `damlbmp` zone + gen zips | 11 zones; AC proxies `H Q`, `O H`, `PJM`, `NPX`; proxy buses `HQ_GEN_CEDARS_PROXY`, `HQ_GEN_IMPORT`, `PJM_GEN_KEYSTONE`, `PJM_GEN_{HTP,VFT,NEPTUNE}_PROXY`, `NPX_GEN_CSC`, `NPX_GEN_1385_PROXY` | DA | 2021-01-01 → 2025-12-31, every hour of all 23 points | yes (`.csv.gz`, ~12 MB) | `fetch_seam_neighbour_price_nyiso.py` |
| `pjm/` | PJM DataMiner2 `da_hrl_lmps` / `rt_hrl_lmps`, `type=INTERFACE` | `NYIS` (5413134), `HUDSONTP` (1124361945), `LINDENVFT` (81436855), `NEPTUNE` (56958967) | DA, RT | 2021-01-01 → 2025-12-31 | **no** — gitignored (`docs/data-licensing.md` §4); re-fetch | `fetch_seam_neighbour_price_pjm.py` |
| `neiso/` | ISO-NE static `histRpts` hourly LMP (DA, RT final) | `.I.ROSETON 345 1` (4011, NY AC), `.I.SHOREHAM138 99` (4014, CSC), `.I.NRTHPORT138 5` (4017, 1385), `.H.INTERNAL_HUB` (4000) | DA, RT | 2021-01-01 → 2025-12-31, all 1,826 days | yes (~9 MB) | `fetch_seam_neighbour_price_neiso.py` |
| `ieso/` | IESO reports-public `PriceHOEPPredispOR`, `RealtimeMktPriceYear`; Bank of Canada Valet `FXUSDCAD` | HOEP; hourly mean of the 5-min MCP for `Ontario` and the `New-York` intertie zone | RT (IESO had no DA market pre-2025-05) | 2021-01-01 → **2025-04-30** | yes (~1.4 MB) | `fetch_seam_neighbour_price_ieso.py` |

## Clocks

- NYISO and ISO-NE files are hour-beginning / hour-ending in Eastern **prevailing**
  time; each (day, node) row carries its publication position `seq`, which is
  what resolves the 23- and 25-hour DST days.
- PJM rows carry PJM's own `datetime_beginning_utc`.
- IESO hours are **EST all year** (no DST): hour-ending `h` begins `(h-1):00` EST.
- IESO prices are **CAD**; the curation converts at the Bank of Canada daily
  USD/CAD for the operating date, carried over non-business days.

## DATA NEEDED — IESO May–December 2025

The IESO Market Renewal Program went live **2025-05-01**. HOEP and the MCP
ceased; their successors (Ontario Zonal Price, intertie LMPs:
`DAHourlyOntarioZonalPrice`, `DAHourlyIntertieLMP`, `RealTimeIntertieLMP`) are
published only as daily/hourly XML on a **rolling ~90-day** archive. Checked
2026-09-28: the oldest file on reports-public (and its sandbox) is 2026-06-28/29;
the IESO Data Directory and the Wayback Machine hold no 2025 copy. May–Dec 2025
Ontario prices are therefore **not obtainable from a public source today**; a
consumer must treat IESO 2025 as Jan–Apr only. A future session could archive
the rolling XML forward from now, but that never reaches back to 2025.

## Recovery

`SHA256SUMS.txt` records every payload, including the gitignored PJM CSVs. All
four fetchers are idempotent and deterministic (the NYISO gzip is written with
`mtime=0`).
