# `spp-lmp-alt` — SOURCES: the SPP-14 per-source sweep table

Every row was probed from this session on **2026-09-06**. No value is from
memory; no percentage is quoted without its formula. Licence text is quoted
verbatim where the source states one and is marked *none stated* where it does not.

## The per-source table

| # | Host | Product(s) offered | Span | Licence | Reachable | Reproduces SPP's own figures? |
|---|---|---|---|---|---|---|
| 1 | `api.gridstatus.io` | `spp_lmp_day_ahead_hourly`, SPP RT LMP 5-min/hourly, binding constraints, load by area, fuel mix, reserve MCPs | n/a — never returned data | see below | **partly**: `GET /v1/` -> `200 {"name":"Grid Status API","version":"1.3.0"}`; `openapi.json` -> `200` (168,774 B). **Every data endpoint -> `401 {"detail":"Missing API Key."}`** | **NOT TESTED** — no data could be retrieved |
| 2 | `docs.gridstatus.io`, `www.gridstatus.io` | licence / pricing / dataset pages | — | — | **NO — Cloudflare `403 "Attention Required!"`** to curl (any UA) and to the WebFetch tool | — |
| 3 | `files.pythonhosted.org` (`gridstatus` sdist 0.36.0) | *source code, not data* | — | **BSD-3-Clause** (`"Copyright 2022 James Max Kanter … Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met"`) | **YES** — 3,171,498 B | **n/a — but this is the row that mattered** (§ below) |
| 4 | `portal.spp.org` | LMP by settlement location (DA + RTBM), binding constraints, hourly load, gen mix, DA/RTBM MCP, permanent/temporary flowgates | 2013 -> current | **none stated** — SPP public data | **YES, ANONYMOUS** | **YES — exactly.** Gate table in FINDING-spp-14 §3: reconstructed system hub equals the committed `actual_lmp_hourly_SPP.parquet` to 0.0000 % on the annual RT mean in all three years, corr 1.000000 |
| 5 | `pricecontourmap.spp.org` | ArcGIS RTBM feature data (hubs, interfaces) — the one non-portal `spp.org` host the `gridstatus` client hits for prices | current interval only | none stated | reachable, but `MapServer/1/query` -> `200 {"error":{"code":404,"message":"Service not found"}}` — **the service the client names no longer exists** | no (real-time only; no archive) |
| 6 | `opsportal.spp.org` | generator interconnection queue (`/Studies/GenerateSummaryCSV`) | to 2026-09-04 | none stated | **YES** — `200`, 663,847 B `text/csv` | n/a — not an LMP/BC/load/genmix/MCP product (manifest row 14, not 5-9) |
| 7 | `www.energyonline.com` (LCG Consulting) | ERCOT, MISO, NYISO, PJM, CAISO prices and loads | — | — | **YES** — `200` | **NO SPP PRODUCT EXISTS.** Every one of the 21 dataset links on `/Data/` is ERCOT / MISO / NYISO / PJM / CAISO; SPP appears nowhere. `GenericData.aspx?DataId=15` -> `302` to `/Error.html` |
| 8 | `zenodo.org` record **17676746** | `price_spp.zip`, 7,775,776,701 B — SPP DA LMP daily `DA-LMP-SL-*.csv` + RT location zips, from `marketplace.spp.org/file-browser-api/download/da-lmp-by-location` (the uploader states the source URL) | central directory read by range request: members from **2013**; nested per-year `.zip.download` archives | **CC-BY-4.0** (`"license": {"id": "cc-by-4.0"}`) — redistribution permitted with attribution | **YES**, and it honours `Range` (`206`, `content-range: bytes 0-0/7775776701`) | **not needed** — kept as the documented fallback; the publisher's own route serves the same files |
| 9 | `www.spp.org` (SPP MMU) | Annual + **Quarterly** State of the Market (QSOM: Winter/Spring/Summer/Fall) | 2021-2025 | none stated | **YES** | **partly — and it cannot close P7.** See §"MMU" below |
| 10 | `api.eia.gov` v2 | — | — | — | **YES** | **NO SPP LMP OR FLOWGATE DATA.** The `electricity` route set is `retail-sales`, `electric-power-operational-data`, `rto`, `state-electricity-profiles`, `operating-generator-capacity`, `facility-fuel`; the `rto` sub-routes are `region-data`, `fuel-type-data`, `region-sub-ba-data`, `interchange-data` and their daily variants — **demand, generation and interchange only, no price and no flowgate** |
| 11 | `www.ferc.gov` / `eqrreportviewer.ferc.gov` | Electric Quarterly Reports | — | — | EQR viewer `200`; `www.ferc.gov` article pages `403` to curl | **NO SPP LMP OR FLOWGATE DATA.** EQR is bilateral contract-transaction reporting, not market LMP; FERC publishes no SPP flowgate archive |

### Row 1 — gridstatus.io licence terms, and why they are recorded as UNOBTAINED

The charter asks for the licence terms **verbatim**. They could not be obtained:
`docs.gridstatus.io` and `www.gridstatus.io` (including `/terms` and `/pricing`)
return Cloudflare `403 "Attention Required!"` to every request from this session,
with a browser User-Agent and through the WebFetch tool alike, and
`api.gridstatus.io/openapi.json` declares **no** `securitySchemes` and carries no
licence field. **No licence text is quoted here because none was retrieved** —
quoting one from memory is exactly what this table forbids. The operative fact for
the sweep needs no licence anyway: **there is no key-free tier**. `GET /v1/datasets`,
`/v1/pricing_locations` and `/v1/datasets/spp_lmp_day_ahead_hourly/query` all return
`401 {"detail":"Missing API Key."}`, with and without an empty `api_key=` parameter.

### Row 3 — the row that opened the route

`gridstatus/spp.py` (v0.36.0) defines `FILE_BROWSER_DOWNLOAD_URL =
"https://portal.spp.org/file-browser-api/download"` and reads every SPP product
from it with a bare `pd.read_csv(url)`. It has **no** token, header or cookie on
that path — its only session helper (`_get_marketplace_session`) is used elsewhere.
A widely-used open-source client fetching SPP anonymously is incompatible with
"the portal requires `X-SPP-UI-Token`", so the portal was re-probed, and the wall
turned out to be two path-shape artifacts:

| Call | What SPP-12 sent | What SPP-14 sent | Result |
|---|---|---|---|
| download | a folder path, or a path absent from that product's layout | the exact **file** path | `404` -> **`200`, real CSV** |
| listing | `path=` (empty) — the SPA's own first call | `path=%2F` (the root) or a real folder | `200 []` -> **`200`, real JSON array** |

Both are correct server behaviour, not authorization. `Accept-Ranges: bytes` is
advertised and `206` responses are served, which is what lets an archived
`<year>/<year>.zip` be read member-by-member — the technique
`scripts/data/build_spp_lmp_reference.py` already implements, and which therefore
**runs unmodified** against this route.

### Row 9 — the MMU, and the p90 it cannot supply

SPP's MMU publishes **quarterly** State of the Market reports as well as the annual
ones SPP-12 transcribed (`spp mmu qsom winter 2024`, `spring 2024`, `summer 2024`,
`fall 2024` at `www.spp.org/documents/{71500,72043,72602,73090}/`), and the Fall
2024 edition tabulates hub prices by hour of day. **A monthly or quarterly N/S
spread series is a partial substitute for P7's hourly mean, and it is NOT a
substitute for the p90 at all** — a p90 is a statement about the tail of an hourly
distribution, and no aggregate of monthly means can recover it. This is recorded
because the charter asked the question; it is **moot in the event**, because the
hourly series itself landed (FINDING-spp-14 §3) and the mean and p90 are computed
from it directly.

## Provenance of every landed byte

Every file lane SPP-14 landed came from `portal.spp.org/file-browser-api/download/`
over anonymous HTTPS on 2026-09-06, written byte-for-byte unmodified. sha256 sums
are in each destination directory's `SOURCES.md` section and in FINDING-spp-14 §7.
No third-party copy was landed anywhere.

---

## Re-probe by SPP-30 (2026-09-12) — row 4 re-verified and EXTENDED BACK TO 2019

Lane SPP-30 needed SPP's out-of-training price years and took **row 4** (the publisher's
own portal) without re-running SPP-14's third-party sweep, which is a DO-NOT-REDO. Row 4's
span claim ("2013 -> current") is **re-verified at the archive-zip level for 2019-2023**,
still **anonymous**, still **none stated** on licence, `Range` still honoured (`206` on
every probe). Zenodo record 17676746 was **not** touched: the publisher's own route served
every byte, which is the rule 13 `[R-MEASURED]` preference.

The committed builder `scripts/data/build_spp_lmp_reference.py` **runs unmodified** on
these years — its own `_remote_size` / `_central_directory` / `_read_member` were driven
against the archived `<year>/<year>.zip` and found all 12 `MONTHLY-SL` members in every
year, for both products:

| `fsName` | Year | Archive bytes | Total zip members | `MONTHLY-SL` months found |
|---|---|---|---|---|
| `da-lmp-by-settlement-location` | 2019 | 228,667,478 | 402 | 1-12 |
| `da-lmp-by-settlement-location` | 2020 | 232,711,485 | 403 | 1-12 |
| `da-lmp-by-settlement-location` | 2021 | 261,793,877 | 595 | 1-12 |
| `da-lmp-by-settlement-location` | 2022 | 280,525,231 | 402 | 1-12 |
| `da-lmp-by-settlement-location` | 2023 | 286,071,592 | 402 | 1-12 |
| `rtbm-lmp-by-location` | 2019 | 4,027,796,207 | 107,066 | 1-12 |
| `rtbm-lmp-by-location` | 2020 | 4,167,267,200 | 107,213 | 1-12 |
| `rtbm-lmp-by-location` | 2021 | 4,616,074,817 | 107,726 | 1-12 |
| `rtbm-lmp-by-location` | 2022 | 5,024,338,629 | 108,334 | 1-12 |
| `rtbm-lmp-by-location` | 2023 | 4,986,546,038 | 104,748 | 1-12 |

**The range-read design is what makes this affordable.** The RTBM archives are 4-5 GB
each; only the 12 monthly members are pulled out of them, which for 2019-2022 is
**578.1 MB compressed in total** (DA 64.6 / 65.5 / 74.3 / 82.5 MB; RTBM 65.1 / 66.2 /
75.8 / 84.1 MB) instead of ~18 GB of whole zips. Measured from the central directories
before any payload was fetched, so the cost was known before it was spent.

Also re-probed on the same route and landed for 2019-2022 (see each directory's own
`SOURCES.md` for byte counts and sha256): `fsName=hourly-load`
(`/<year>/<year>.zip`) and `fsName=generation-mix-historical` (`/GenMix_<year>.csv`).
The **listing** endpoint is `file-browser-api/?fsName=<fs>&path=<p>&type=folder` — NOT
the `download/` path — and `hourly-load` lists years from **2011**, confirming row 4's
span claim independently of the LMP products.

**One charter item was declined on evidence, not fetched:** `lmp-data/DAMLZHBSPP_<year>.zip`
is **ERCOT** data, not SPP — `DAMLZHBSPP` is *DAM Load Zone and Hub Settlement Point
Prices*, where the trailing "SPP" means *Settlement Point Prices*. The zip member is
`rpt.00013060.0000000000000000.DAMLZHBSPP_2023.xlsx`, an ERCOT MIS report id, and
`scripts/hydrate_data.py:186-191` warns that a bare `spp` token "would also claim ERCOT's
settlement-point zips". It is not on this route and was never part of this corpus.

## Appended 2026-09-25 by lane SPP-80 — the hub price COMPONENTS (MCC / MLC) from the same files

The monthly wide settlement-location files this route serves (`{DA-LMP,RTBM-LMP}-MONTHLY-SL-YYYYMM.csv`,
live per-month for the current window, range-read out of `/<yr>/<yr>.zip` for archived years) carry three
`Price Type` rows per settlement location — `LMP`, `MCC`, `MLC` (measured 2026-09-25 on
`rtbm-lmp-by-location` `/2025/07/RTBM-LMP-MONTHLY-SL-202507.csv`). The committed hub sidecars kept only
`LMP`. `scripts/data/fetch_spp_hub_lmp_components.py` re-reads the same files for 2019–2025 through the
builder's own functions and keeps all three for the two hubs, landing
`data/raw/_validation-source/actual_lmp_components_hourly_zonal_SPP.parquet` (row and checksum in that
directory's README). Its `lmp` column reproduces the committed zonal file bit-exactly.
