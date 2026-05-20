# Multi-ISO Data Acquisition Report

Status: **automation blocked by network policy** — no upstream data fetched.
Run date: 2026-05-20. Branch: `claude/data-scout-ez0qn`.

Role: data-acquisition scout for the multi-ISO backcast (doc 01 families 1, 4,
6 and doc 04 zonal load). This run attempted to programmatically gather regional
gas basis (Step 1) and directly-downloadable zonal hourly load (Step 2). Below
is exactly what was retrieved (nothing, this run) and, per item, the source URL
+ the manual steps + why automation failed.

---

## Step 0 — Connectivity result: BLOCKED (host allowlist)

The remote execution environment enforces an **outbound host allowlist**. Every
data-provider host returns `HTTP 403` with header `x-deny-reason: host_not_allowed`
and body `Host not in allowlist`. This is a proxy/network-policy block, not a
server-side error — the providers themselves were never reached.

Probed 2026-05-20:

| Host | Result |
|------|--------|
| `api.eia.gov` | **403 host_not_allowed** |
| `www.eia.gov` | **403 host_not_allowed** |
| `mis.nyiso.com` | **403 host_not_allowed** |
| `www.iso-ne.com` | **403 host_not_allowed** |
| `oasis.caiso.com` | **403 host_not_allowed** |
| `pypi.org` / `files.pythonhosted.org` | 200 (reachable) |
| `github.com` / `raw.githubusercontent.com` | 200 / 301 (reachable) |
| `api.anthropic.com` | 404 (reachable) |

So `pip install` works, but **no data source is reachable**. Per the task's
Step 0 ("if blocked, skip fetching and write the report listing every source URL
and the exact manual steps"), nothing was downloaded and no data values were
computed or invented.

**An EIA API key IS present** (`.env` → `EIA_API_KEY=…`, also readable as
`EIA_API_KEY`). It was validated only insofar as the host is blocked; the key
itself was not exercised. Once `api.eia.gov` is allowlisted, the Step 1 EIA
pulls below become fully automatable with this key.

### To enable automation in a future run

Add these hosts to the environment's outbound allowlist, then re-run this scout:

```
api.eia.gov          # Step 1 gas basis (key already in .env) — covers most of it
www.eia.gov          # Step 1 fallback (dnav HTML/CSV bulk downloads)
mis.nyiso.com        # Step 2 NYISO zonal actual load (fully public, no auth)
oasis.caiso.com      # Step 2 CAISO OASIS load (public API, no auth)
www.iso-ne.com       # Step 2 ISO-NE load (some reports need a free account)
```

Network policies are chosen at environment-creation time; see
https://code.claude.com/docs/en/claude-code-on-the-web for how to pick a more
permissive policy or add allowlist entries.

---

## Step 1 — Regional gas basis  →  `inputs/raw-data/gas_basis_by_iso_month.csv`

**GOT:** nothing this run. The target CSV was created as a **header-only
template** (schema locked, zero data rows) so a manual/automated fill-in drops
straight in:

```
iso,year,month,hub,basis_usd_mmbtu,source
```

`basis_usd_mmbtu` = (monthly hub price) − (monthly Henry Hub), in $/MMBtu.

**MISSING — sources & manual steps.**

### 1a. Henry Hub (the subtrahend) — EIA, free

- dnav (daily, HTML→download CSV): https://www.eia.gov/dnav/ng/hist/rngwhhdD.htm
- EIA API v2 (daily spot, series `RNGWHHD`):
  `https://api.eia.gov/v2/natural-gas/pri/fut/data/?api_key=$EIA_API_KEY&frequency=daily&data[0]=value&facets[series][]=RNGWHHD&start=2021-01-01`
- Aggregate the daily series to a **monthly mean** to subtract from each hub.
  (EIA does not publish a Henry Hub monthly *spot* directly; derive it from the
  daily series, or use the Henry Hub citygate `N3050US3` as a cross-check.)
- *Verify the exact route/series facet against the live API once unblocked — the
  daily Henry Hub spot has historically lived under both `pri/fut` and `pri/spt`.*

### 1b. Citygate by state (monthly) — EIA, free

- dnav: https://www.eia.gov/dnav/ng/ng_pri_sum_dcu_nus_m.htm
- EIA API v2 route: `https://api.eia.gov/v2/natural-gas/pri/sum/data/?api_key=$EIA_API_KEY&frequency=monthly&data[0]=value&facets[process][]=PG2&start=2021-01`
  (citygate price, monthly, per-state series of the form `N3050<ST>3`, e.g.
  `N3050CA3` California, `N3050NY3` New York, `N3050MA3` Massachusetts,
  `N3050IL3` Illinois, `N3050PA3` Pennsylvania). *Confirm facet codes live.*

### 1c. ISO hub → series mapping, and the paywall problem

The task's representative hubs are **named pipeline trading points**. EIA does
**not** publish daily/monthly prices for these specific points — they are
**ICE / S&P Global Platts (Gas Daily / Inside FERC) products, paywalled.**
What EIA gives for free is Henry Hub + **state citygate** averages, which are
usable *proxies* for some ISOs but not exact for the Northeast (where the
winter basis blowout — the single most important calibration item per doc 01
§4 — happens precisely at AGT / Transco Z6 NY and is understated by a state
citygate average).

| ISO | Task's representative hub(s) | Exact source | Free EIA proxy (citygate) | Note for `source` column |
|-----|------------------------------|--------------|---------------------------|--------------------------|
| PJM | TETCO M3, Transco Z6 (non-NY), Dominion South | **ICE/Platts** | PA / NJ citygate | exact hubs paywalled; proxy only |
| NYISO | Transco Z6 NY | **ICE/Platts** | NY citygate (`N3050NY3`) | proxy understates winter spike |
| ISO-NE | Algonquin Citygate (AGT) | **ICE/Platts** | MA citygate (`N3050MA3`) | proxy understates winter spike |
| MISO | Chicago Citygate | **ICE/Platts** | IL citygate (`N3050IL3`) | good proxy (Chicago≈IL citygate) |
| SPP | Panhandle Eastern | **ICE/Platts** | OK/KS citygate | proxy only |
| CAISO | PG&E Citygate, SoCal Border | **ICE/Platts** | CA citygate (`N3050CA3`) | good proxy |

**Manual procedure (free, EIA-only proxy basis):**
1. Pull Henry Hub daily (1a) → monthly mean `hh[year,month]`.
2. Pull state citygate monthly (1b) for CA, NY, MA, IL, PA/NJ, OK/KS.
3. For each ISO row: `basis = citygate[state,year,month] − hh[year,month]`,
   `hub` = the proxy name (e.g. "CA citygate (EIA N3050CA3)"),
   `source` = `"EIA citygate proxy"`.
4. Write rows to `inputs/raw-data/gas_basis_by_iso_month.csv` for 2021–2025.

**Manual procedure (exact hubs, paywalled — only if a license exists):**
- Source AGT, Transco Z6 NY, TETCO M3, Dominion South, Chicago Citygate,
  Panhandle Eastern, PG&E/SoCal monthly indices from **ICE** or **Platts Gas
  Daily / Inside FERC Bidweek**. Compute `basis = hub − Henry Hub` monthly.
  Set `source` = `"ICE"` or `"Platts Inside FERC"`. These cannot be automated
  from a free endpoint and require account/credentials the repo does not hold.

**Why automation failed this run:** `api.eia.gov` and `www.eia.gov` are both
blocked by the host allowlist (Step 0). The free EIA proxy path is otherwise
fully scriptable with the in-repo `EIA_API_KEY`; the exact-hub path is
paywalled regardless of network access.

---

## Step 2 — Zonal hourly load  →  `inputs/raw-data/zonal-load/<ISO>/`

**GOT:** nothing this run. The `zonal-load/<ISO>/` directories were not created
because there is no content to put in them (git does not track empty dirs);
create them at fill-in time.

### NYISO — fully public, no auth  **MISSING (host blocked)**

- Index: http://mis.nyiso.com/public/csv/pal/
- "Real-Time Actual Load" (zonal, zones A–K). File patterns:
  - Daily CSV: `http://mis.nyiso.com/public/csv/pal/YYYYMMDDpal.csv`
  - Monthly ZIP of dailies: `http://mis.nyiso.com/public/csv/pal/YYYYMM01pal_csv.zip`
- **Manual steps:** loop months 2021-01 … 2025-12, download each `…pal_csv.zip`,
  unzip, concatenate. Columns: timestamp, zone name (CAPITL, CENTRL, DUNWOD,
  GENESE, HUD VL, LONGIL, MHK VL, MILLWD, N.Y.C., NORTH, WEST), Load (MW).
  Save to `inputs/raw-data/zonal-load/NYISO/`. Be polite (small delay per file).
- **Why automation failed:** `mis.nyiso.com` blocked (host allowlist). No auth
  needed — this one is purely a network-policy issue and will work the moment
  the host is allowlisted.

### CAISO — public OASIS API, no auth  **MISSING (host blocked)**

- OASIS SingleZip API base: `http://oasis.caiso.com/oasisapi/SingleZip`
- Actual/forecast system load report: `queryname=SLD_FCST` (forecast incl.
  actuals) with `market_run_id=ACTUAL`, `version=1`, and
  `startdatetime`/`enddatetime` in `YYYYMMDDThh:mm-0000`. Max ~31-day window
  per call → loop monthly. Returns a zipped CSV; load is by **TAC area**
  (PGE-TAC, SCE-TAC, SDGE-TAC, CA ISO-TAC). Map TAC areas → the doc-04 target
  zones (NP15/ZP26/SP15) at processing time.
- Docs: http://www.caiso.com/Documents/OASIS-InterfaceSpecification.pdf
- **Manual steps:** loop monthly 2021–2025, `curl` each SingleZip URL, unzip,
  concat → `inputs/raw-data/zonal-load/CAISO/`. OASIS throttles aggressively —
  keep ≥5 s between calls.
- **Why automation failed:** `oasis.caiso.com` blocked (host allowlist).

### ISO-NE — mostly public, some reports need a free account  **MISSING (host blocked)**

- Reports page: https://www.iso-ne.com/isoexpress/web/reports/load-and-demand
- Zonal hourly metered load (8 zones: ME, NH, VT, CT, RI, SEMA, WCMA, NEMA/Boston).
  Bulk historical "Zonal Information" hourly load is downloadable as CSV/XLS per
  year; the **Web Services API** (`https://webservices.iso-ne.com/api/v1.1/`)
  serves `…/hourlyloadzonal/…` but requires a **free registered account**
  (HTTP Basic auth).
- **Manual steps:** either (a) download the per-year zonal load CSVs from the
  reports page, or (b) register for a Web Services account and pull
  `hourlyloadzonal` per day/zone. Save to `inputs/raw-data/zonal-load/ISO-NE/`.
- **Why automation failed:** `www.iso-ne.com` blocked (host allowlist); the API
  path additionally needs credentials not present in the repo.

### PJM — Data Miner 2, needs API key  **MISSING (auth + host)**

- Portal: https://dataminer2.pjm.com/  ·  API: `https://api.pjm.com/api/v1/`
- Zonal metered load feed: `hrl_load_metered` (hourly load by zone/area).
  Requires header `Ocp-Apim-Subscription-Key: <key>` from a free Data Miner 2
  account. No such key is in the repo (`.env` holds only `EIA_API_KEY`).
- **Manual steps:** register at dataminer2.pjm.com, copy the subscription key,
  then `GET https://api.pjm.com/api/v1/hrl_load_metered?startRow=1&rowCount=50000&datetime_beginning_ept=…`
  paginated over 2021–2025; or use the browser "Download CSV" per zone. Save to
  `inputs/raw-data/zonal-load/PJM/`. Also the source for the doc-04 load-share
  refresh (replace the 0.37/0.28/0.20/0.15 placeholders).
- **Why automation failed:** no PJM subscription key available, and `api.pjm.com`
  would also need allowlisting. Recorded the exact feed instead of guessing.

### MISO — Market Reports, public files  **MISSING (host blocked)**

- Market reports: https://www.misoenergy.org/markets-and-operations/real-time--market-data/market-reports/
- Regional (North / Central / South) actual + forecast load: daily files
  `YYYYMMDD_rf_al.xls` (Regional Forecast and Actual Load), served from MISO's
  public docs/`api.misoenergy.org` document store.
- **Manual steps:** loop dates 2021–2025, download each `…_rf_al.xls`, parse the
  actual-load columns by region → `inputs/raw-data/zonal-load/MISO/`. (The
  daily-file URL pattern shifts periodically; confirm the current path on the
  reports page first.)
- **Why automation failed:** MISO hosts blocked by allowlist; URL pattern also
  needs live confirmation, so no values were guessed.

### SPP — Marketplace / Portal, needs auth  **MISSING (auth + host)**

- Marketplace: https://marketplace.spp.org/  ·  public file browser:
  https://portal.spp.org/pages/hourly-load (and the SPP "Integrated Marketplace"
  data portal).
- Hourly load by SPP area/zone. Most CSV downloads sit behind an authenticated
  Marketplace session; some aggregate hourly-load files are public via the
  portal file browser.
- **Manual steps:** sign in to SPP Marketplace (or use the public hourly-load
  browser if the needed granularity is there), download hourly load by area for
  2021–2025 → `inputs/raw-data/zonal-load/SPP/`.
- **Why automation failed:** SPP hosts blocked by allowlist and the richer feeds
  need a Marketplace login the repo does not hold.

---

## Summary table

| Item | Status | Path / Source | Blocker |
|------|--------|---------------|---------|
| Gas basis CSV (schema) | **template only** | `inputs/raw-data/gas_basis_by_iso_month.csv` | created header, 0 rows |
| Gas basis — EIA proxy | MISSING | api.eia.gov / dnav | host allowlist (key present) |
| Gas basis — exact hubs | MISSING | ICE / Platts | paywalled (no license) |
| NYISO zonal load | MISSING | mis.nyiso.com/public/csv/pal/ | host allowlist (no auth needed) |
| CAISO zonal load | MISSING | oasis.caiso.com OASIS API | host allowlist (no auth needed) |
| ISO-NE zonal load | MISSING | iso-ne.com reports / web services | host allowlist (+ free acct for API) |
| PJM zonal load | MISSING | api.pjm.com Data Miner 2 | API key + host |
| MISO regional load | MISSING | misoenergy.org market reports | host allowlist (+ confirm URL) |
| SPP area load | MISSING | marketplace.spp.org | login + host |

**Bottom line:** with `api.eia.gov`, `mis.nyiso.com`, and `oasis.caiso.com`
added to the allowlist, Step 1 (EIA proxy basis) and the NYISO + CAISO halves of
Step 2 are immediately and fully automatable from this repo (EIA key already
present, no other credentials needed). ISO-NE/PJM/MISO/SPP additionally need
free-account credentials and/or a live URL confirmation, so they were recorded
as exact manual steps rather than guessed. No data values were fabricated.
