# `spp-lmp-alt` — the SPP alternative-source sweep (lane SPP-14)

Opened **2026-09-06** by lane **SPP-14** under owner ruling **P12 r#4**
(*"Try to find the data somewhere else"*), charter
`docs/multi-iso/spp-addition-plan-2026-09.md` §5 row SPP-14.

## THIS DIRECTORY CARRIES NO PAYLOAD, AND THAT IS THE RESULT

The sweep was chartered to find a third-party HTTPS host for SPP's LMP archive
after SPP-12 read the portal as credential-walled and SPP-13 found SPP's own
documented FTP route blocked by the session egress. **It found something better
than a third party: SPP's own portal is not walled.** Both
`portal.spp.org/file-browser-api` calls answer anonymously over plain HTTPS, with
no token and no cookie, and `Range` requests are honoured. The full route
correction, with the measured before/after, is in the `SOURCES.md` beside this
file and repeated in each served directory's own `SOURCES.md`.

So no alternative source was landed, because **no alternative source is needed**,
and rule 13 `[R-MEASURED]` prefers the publisher's own series over any copy of it:
a third-party mirror is admissible only as SPP's own published series faithfully
reproduced, and once SPP serves it directly the mirror adds provenance risk and
nothing else.

**Where the data actually landed:**

| Manifest row | Product | Directory |
|---|---|---|
| 5 | per-hub `SPPNORTH_HUB` / `SPPSOUTH_HUB` DA+RT hourly 2023-2025 | `data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet` |
| 6 | hourly load by area 2023-2024 | `data/raw/spp-hourly-load/` |
| 7 | generation mix 2023-2025 (complete) | `data/raw/spp-genmix/` |
| 8 | flowgate registries (+ the measured BC archive, pulled not committed) | `data/raw/spp-binding-constraints/` |
| 9 | DA operating-reserve MCP 2023-2024 | `data/raw/spp-or-mcp/` |

## The candidate list, and what each one turned out to be

The full per-source table — host, product, span, licence quoted, reachable,
reproduces SPP's own figures — is `SOURCES.md` beside this file and
`docs/handoffs/FINDING-spp-14-2026-09-06.md` §2. In one line each:

- **gridstatus.io hosted API** — reachable, but **every data endpoint requires an
  API key**; there is no key-free tier. Not usable here.
- **`gridstatus` open-source Python package** — not a data source, but **the
  decisive evidence**: its SPP client reads `portal.spp.org` with a bare
  `pandas.read_csv(url)` and carries no credential at all, which is what prompted
  the re-probe that opened the route.
- **LCG Consulting EnergyOnline** — reachable; **publishes no SPP data at all**
  (ERCOT, MISO, NYISO, PJM, CAISO only).
- **Zenodo record 17676746** — a real CC-BY-4.0 mirror of SPP DA LMP taken from
  this same portal endpoint. Kept as a documented fallback, not landed.
- **SPP MMU** — publishes hub spreads annually, not at monthly-or-finer grain in
  a form that substitutes for the hourly series; and never a p90.
- **EIA / FERC** — neither publishes SPP LMP or flowgate data. One line each in
  `SOURCES.md`.

## Retention

Nothing here is a data contract. If a future session finds the portal route
closed again, read `SOURCES.md` first: it records the exact call grammar, the
two path-shape traps that made SPP-12 read it as walled, and the Zenodo fallback.
