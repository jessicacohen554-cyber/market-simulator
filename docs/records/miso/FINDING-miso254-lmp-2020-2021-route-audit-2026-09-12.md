# FINDING — miso-254: MISO 2020/2021 LMP. The block is now EXHAUSTIVE, the substitute route is DEAD too, and the unblock chain is verified end-to-end

```
SESSION : miso-254
ISO     : MISO
ASK     : "Collect miso data on 2020 and 2021 LMP to populate the keeper report with
           those LMP years so we know how far off the miss is"
RESULT  : NOT COLLECTED. Every public route re-tested today and five NEW ones tested for
           the first time; all closed. The one unblocker is unchanged and is a credential.
DELIVERED: (1) an exhaustive route audit that closes the follow-up routes miso-252 left open,
           (2) a verified one-command unblock chain (no re-solve), (3) a staging-integrity
           fix + tests for a trap the documented command would otherwise have sprung.
```

## 1. The ask, and why it is not satisfiable here

`frontend/data/backcast/bench/MISO/{2020,2021}.json.gz` carry no `avgLMP` block, so the two
folded validation rungs (`2026-09-10-miso-251-tp2020`, `…-tp2021`) read **C3a / C3b / C3c =
SKIPPED**. That is the "miss" the ask wants sized. Populating it needs a measured hourly MISO
LMP series for 2020 and 2021. There is none on disk
(`actual_lmp_hourly_MISO.parquet` covers 2022–2026) and none obtainable from this session.

## 2. Route audit — every route, measured today (2026-09-12), not inherited

miso-252 (2026-09-10) tested seven routes. All seven were re-measured today and all give the
same answer. **Five further routes were tested for the first time**; they are the rows this
finding adds, and they are the ones a next session would otherwise have tried.

| # | route | result today | new? |
|---|---|---|---|
| 1 | `docs.misoenergy.org/marketreports/YYYYMMDD_{da_expost_lmp,rt_lmp_final}.csv` | **404** for 2020-06-15 and 2021-06-15, both markets. Floor re-measured: **2022-12-31 → 404, 2023-01-01 → 200** — a FIXED floor, not a rolling window (unchanged since 2026-07-09 and 2026-09-10) | re-test |
| 2 | archive shapes for the daily report (`.zip`, `.xls`, `archive/…`, `YYYY/…`, `marketreportsarchives/…`, `202006…`, `2020-06…`) | **404**, 13 shapes | re-test + widened |
| 3 | `apim.misoenergy.org/pricing/v1` keyless | **401** *"Access denied due to missing subscription key"* | re-test |
| 4 | `MISO_PRICING_API_KEY` in env or repo `.env` | **absent** (no `.env` exists; `.env.example` names the key only) | re-test |
| 5 | `www.misoenergy.org` Market Report Archives page | **403 Cloudflare interstitial** ("Just a moment…") to curl, to a browser UA, and to WebFetch | re-test |
| 6 | anything in `data/raw` carrying MISO 2020/2021 prices | **none** | re-test |
| 7 | **the annual `*_HIST` archive family** — 144-URL sweep over `{2020,2024} × {da_expost_lmp, rt_lmp_final, da_lmp, rt_lmp, DA_LMP, RT_LMP, lmp, LMP, 5MIN_LMP} × {_HIST, _HIST_csv, _hist, ""} × {.zip,.csv} × {YYYY, YYYY12}` | **0 hits.** The sweep is worth recording because the family is REAL and its retention is LONGER than the daily floor: `202012_dfal_HIST_xls.zip` and `201912_dfal_HIST_xls.zip` both **200** (load), while `2023_da_bc_HIST.csv` and `2024_da_bc_HIST.csv` are **200** and `2021_da_bc_HIST.csv` is **404**. So MISO does keep pre-2023 annual archives — **just not for LMP.** This is now measured, not assumed | **NEW** |
| 8 | monthly `YYYYMMDD_mom.xlsx` (Markets & Operations Monthly, which carries monthly average prices) | **404** for 2020-03/04 and 2021-03; **200** for 2024-03 and 2025-03. Same 2023 floor | **NEW** |
| 9 | Azure blob container listing on `docs.misoenergy.org` (`?restype=container&comp=list`) | **404 `ResourceNotFound`** — listing is disabled, so the retained set cannot be enumerated, only probed | **NEW** |
| 10 | `cdn.misoenergy.org` (hosts the Market Reports Directory xlsx and the SOM appendices) | **403** to curl and to WebFetch | **NEW** |
| 11 | `web.archive.org` snapshot of the Market Report Archives page (would reveal the archive URLs behind route 5's Cloudflare wall) | **blocked by this session's egress policy** — `archive.org`'s availability API answers and reports a 2026-02-12 snapshot exists, but `web.archive.org` itself is refused ("Blocked by egress policy"). Reported, not routed around | **NEW** |
| 12 | **the MMU's published monthly series** — the 2020 SOM *Analytical Appendix* Figures A26–A31 are per-hub monthly average day-ahead and real-time prices, i.e. exactly the series a C3b bench needs | **DEAD END, and this kills the obvious follow-up to miso-252 §2.** The appendix was downloaded (10.0 MB) and text-extracted in full: the figures are **raster images with no text layer** — only their titles and captions extract. No monthly number is recoverable from any SOM volume; the whole-dollar annual sentence miso-252 quoted is the only machine-readable figure in them | **NEW** |

**Conclusion.** The static archive is closed at 2023-01-01 for every LMP-bearing report family,
the one family that predates it does not carry LMP, the archive index is unreachable behind
Cloudflare and the Wayback mirror is egress-blocked, and the only published substitute is a
rounded annual scalar in a PDF. `MISO_PRICING_API_KEY` remains the single unblocker, exactly as
miso-252 §6 said — this finding removes the remaining "but did anyone try…" routes.

## 3. What the key buys, and the one thing still unverified about it

The Data Exchange developer portal's own metadata was read today
(`data-exchange.misoenergy.org/developer/apis?api-version=2022-04-01-preview`, the APIM content
API behind the SPA — the browsable pages themselves are a JS app):

* `pricing-api` exists, `subscriptionRequired: true`, and its `GET /v1/{day-ahead,real-time}/{date}/lmp-expost`
  operations are documented as **"Historical … locational marginal prices … by CPNode in hourly
  intervals"**, with a documented `404 Date not found` response.
* **No earliest-date is documented anywhere in the portal metadata or the FAQ.** So it is
  *plausible but UNVERIFIED* that the API serves 2020/2021. The first thing to do with a key is
  a single-day probe (`/v1/day-ahead/2020-06-15/lmp-expost?node=INDIANA.HUB`) before spending a
  year's worth of calls: a 404 there would mean the API carries the same floor as the static
  reports and **the rungs cannot be priced at all** from MISO's public surface.
* Anyone with a MISO public-website profile can create a Data Exchange account and subscribe
  (`https://data-exchange.misoenergy.org`); the subscription key is what the fetch script reads.
* Unrelated but worth recording, from the same metadata: the RT ex-post **5-minute** interval
  labels were re-based on 2026-05-06 (they now carry period START). **Hourly is explicitly
  unchanged**, and `fetch_miso_hub_lmp._hub_rows_api` reads hourly records, so the repo's API
  path is unaffected.

## 4. The unblock chain, verified end-to-end (no re-solve)

Every script in the chain was read today and **none hardcodes a year that would exclude 2020/2021**
(`derive_miso_hub_lmp.py` and `build_miso_lmp_reference.py` both take `--years` and merge on
year; `render_calibration_html.py:1865` copies the `actual_lmp.json` record straight into the
bench part as `avgLMP`; `calibration_verdict.py` reads `avgLMP` for C3a/C3b/C3c). The bundles
for both rungs are committed, so **nothing needs re-solving** — this is a bench build and a
re-score.

```bash
# 0. PROBE FIRST (one call) — does the API serve the year at all?
curl -H "Ocp-Apim-Subscription-Key: $MISO_PRICING_API_KEY" \
  "https://apim.misoenergy.org/pricing/v1/day-ahead/2020-06-15/lmp-expost?node=INDIANA.HUB"

# 1. stage the eight hubs (8 calls/day/market under a 90/min limiter: ~2.7 h/year/market)
MISO_PRICING_API_KEY=... python scripts/data/fetch_miso_hub_lmp.py --years 2020 2021 --markets da rt

# 2. reduce to the zonal + system validation parquets
python scripts/data/derive_miso_hub_lmp.py --years 2020 2021

# 3. write the MISO blocks of actual_lmp.json (annual + monthly + percentiles + zones)
python scripts/data/build_miso_lmp_reference.py --years 2020 2021

# 4. add the load-weighted basis the v2.4 rubric gates on (rt_lw/da_lw)
python scripts/data/derive_actual_lmp.py --lw-retrofit --years 2020 2021 --isos MISO

# 5. refresh the bench parts and re-score the folded rungs; then rule 15 registration
```

Step 4 needs measured MISO demand for both years, which is on disk (subba demand 2019–2021).

## 5. A trap in the documented command, found and fixed here

`stage_year` drops a day that fails every retry rather than aborting the year — deliberate, and
right, since one lost day is cheap to re-fetch. But a year in which **every** day fails still
wrote its full set of chunk files: ~53 per market, header-only, 0 rows, named exactly like a
real staging, and `derive_miso_hub_lmp.py` reads them without complaint. Running the documented
`--years 2020 2021` command **without** the key — the single most likely next action by a
session that has not read this file — would have littered `data/raw/lmp-data/MISO/` with 106
empty CSVs that look like staged years.

Fixed in `scripts/data/fetch_miso_hub_lmp.py`:

* a year with **0 staged days raises** and writes nothing, naming both causes (the 2023-01-01
  floor and the missing key);
* a chunk window with no staged day **is not written at all**, which also makes the on-disk
  convention true to what 2022 already records — a short tail shows as *absent* chunks
  (`p01..p49`), never as empty ones.

Covered by `tests/curation/test_fetch_miso_hub_lmp_staging.py` (2 tests, no network).
`tests/curation/test_derive_miso_hub_lmp.py` still passes (4).

## 6. What the rungs currently say about the miss, and what may NOT be done about it

miso-252 §3 stands unchanged and is the only sizing available: against the MMU's published
annual real-time energy price, with the hub-vs-system basis band carried explicitly,
**2021 is inconclusive (−2.7 % to +12.5 %, straddling the in-sample −0.5 %…+8.4 % range) and
2020 is high by +26.9 % to +46.8 %**. The band (16 pp on a single anchor year) is wider than
the model's own in-sample error, which is precisely why that number **must not be fed to the
C3a scorer**: it is not the same quantity as the hub-mean bench the criterion is defined on.
C3a/C3b/C3c therefore stay **SKIPPED** on both rungs rather than being scored against a
non-like-for-like actual. Rule 14 `[R-ACCURATE]`'s misalignment exception is not a licence to
substitute a different statistic for a missing one.

Rule 30(c) is unaffected either way: these are held-out years, they cannot certify or decertify
MISO, and the ISO's determination stays the train-tier `CALIBRATED`.

## 7. Owner action

**Supply `MISO_PRICING_API_KEY`** (or create the free Data Exchange subscription at
`https://data-exchange.misoenergy.org` and hand the key over). Step 0 above then answers, in one
call, whether MISO's own API retains 2020 — and if it does, §4 prices both rungs with no LP spent.
