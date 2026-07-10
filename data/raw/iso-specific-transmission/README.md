# iso-specific-transmission — raw transfer-limit / interchange sources

Immutable raw drops of per-ISO transmission data. Never modified in place.

## PJM (present)

- `PJM_<year>_transfer_limits_and_flows.csv` — PJM Data Miner 2
  `transfer_limits_and_flows` (hourly interface transfer limits & flows).
  Consumed by `scripts/curate_transfer_interface_limits.py` → the
  `transfer-interface-limits` clean datatype (measured hourly interface
  limits on the model clock; ten series incl. AP-South / Bedington-BlackOak
  pre+post-contingency, AEP/DOM, 50045005, Cleveland, and the Average
  Western/Central/Eastern envelopes). One row per series per UTC hour;
  spanning EPT midnight-to-midnight calendar years.
- `PJM_<year>_import_export_act_sch_interchange.csv` — Data Miner 2 actual +
  scheduled interchange by interface.

## ERCOT NP6-86 SCED binding-constraint archives (DATA NEEDED)

`DATA NEEDED:` the ERCOT **NP6-86-CD "SCED Shadow Prices and Binding
Transmission Constraints"** monthly archives for the backcast years
(2023, 2024, 2025), named `*SCEDBTCNP686*.zip`. Consumed by

- `scripts/curate_gtc_limits.py` → the `gtc-limits` clean datatype (measured
  hourly Generic Transmission Constraint limits on the model clock), and
- `scripts/derive_ttc_limits.py` (static limit-at-bind summary that seeded
  the `ttc_mw` values in `iso_configs._ercot_config`).

Expected layout, exactly as the ERCOT Data Portal bundles them: one zip per
month containing one inner zip per SCED execution (~5 min), each holding one
CSV with columns `SCEDTimeStamp, RepeatedHourFlag, ConstraintID,
ConstraintName, ContingencyName, ShadowPrice, MaxShadowPrice, Limit, Value,
ViolatedMW, FromStation, ToStation, FromStationkV, ToStationkV, CCTStatus`.
Loose per-interval `*SCEDBTCNP686*` zips/CSVs (the MIS current-window naming
`cdr.00012302.*.SCEDBTCNP686*.csv`) are also accepted.

Authoritative source: <https://data.ercot.com/data-product-archive/NP6-86-CD>
(EMIL NP6-86-CD, reportTypeId 12302). The live MIS listing
(`https://www.ercot.com/misapp/servlets/IceDocListJsonWS?reportTypeId=12302`)
retains only ~7 days; historical months require an ERCOT Data Portal sign-in,
so the archives must be supplied manually — they cannot be fetched
autonomously. A previous session's upload of the full 2023–2024 monthly set
(202,512 SCED intervals) has not been re-committed; this directory keeps only
what fits the repo.

The 5-minute GTC rows are identified by an **empty `FromStation`** (a GTC
caps a weighted flow sum across several elements, not one monitored line).

## 2026-07-10 holdout-year intake session (rule 22 authorized, CLAUDE.md §22)

Session scope: extend rows 35-40 of `docs/data-register-2026-07.md` (ERCOT
GTC, PJM interchange/transfer, CAISO WECC intertie LMP, MISO↔PJM border LMP,
EIA-930 BA-to-BA interchange, validation LMP) to 2018-2022 + H1-2026,
fetch/verify only (no solve, no scoring — rule 22 quarantine).

**ERCOT NP6-86 — still DATA NEEDED for 2018, 2019, and H1-2026.** Re-verified
2026-07-10: the ERCOT Data Portal (`data.ercot.com/data-product-archive/…`) is
a JS SPA behind Incapsula bot protection (confirms only a browser+login
session can reach the historical monthly archives); the public MIS JSON
listing (`IceDocListJsonWS?reportTypeId=12302`) still retains only the
rolling ~7-day current window (checked live: oldest entry ~2026-07-09), same
as reportTypeId 12302's normal retention. `api.ercot.com`'s public-reports
endpoint (subscription key present in `.env` as `ERCOT_API_KEY`) 302-redirects
to a B2C login — no username/password credential exists in this environment
to complete that OAuth flow. No autonomous path exists for any of 2018,
2019, or H1-2026; unchanged from the existing 2023-2025 gap above.

**PJM — new fetch script, DataMiner2 confirmed back to 2011/2014.**
`scripts/fetch_pjm_transmission.py` (added this session) fetches
`act_sch_interchange` (firstAvailable 2014-01-01), `transfer_limits_and_flows`
(firstAvailable 2011-01-01), and merged `da_hrl_lmps`+`rt_hrl_lmps`
(`type=HUB`, firstAvailable 2000/1998) — all indefinite retention, verified
live against 2019 archived rows with no `API_1044` restriction. A full
2018-2022 + H1-2026 pull for all three feeds was run and verified against
real PJM data during this session (spot-checked row counts and schemas
against the existing 2023-2025 files) but the resulting raw CSVs
(11-140 MB/year, matching the existing 2023-2025 file sizes above) exceed the
push_files commit path's practical size ceiling — see "commit-size
constraint" below. Re-run the script locally to regenerate the raw drops;
only a much coarser (~weekly-mean) illustrative slice could be committed this
session.

**CAISO WECC intertie LMP — 2018-2022 source-side blocked, H1-2026 fetchable.**
`scripts/fetch_caiso_intertie_lmp.py --years 2020` returns OASIS
`ERR_CODE 1000` ("no data returned for the specified selection") — confirmed
live 2026-07-10 against a 2020-06-01 PRC_LMP DAM query. This matches the
~39-month rolling retention `fetch_caiso_oasis.py` already documents: OASIS
has aged out everything before roughly 2023-03. **2018-2022 CAISO WECC
intertie LMP (and, for the same reason, any other CAISO OASIS PRC_LMP-sourced
holdout series, including the CAISO validation LMP hub source) is not
recoverable from OASIS at all** — this is a source-retention exhaustion, not
a script or auth limitation. H1-2026 fetched cleanly (`--years 2026`; MALIN
and CAPTJACK nodes both resolve for the full Jan-Jul window).

**MISO↔PJM border / MISO validation LMP — fetchable via the Pricing API
fallback, but slow.** `scripts/fetch_miso_hub_lmp.py --years 2018 2019 2020
2021` uses the `MISO_PRICING_API_KEY` fallback (the static daily CSVs have
aged off retention for all of 2018-2021, confirmed same ~3.5yr rolling
window as the 2022 boundary the script's docstring already documents). The
fallback works (verified against a live 2020-06-01 call) but costs 8 API
calls/hub-day and is rate-limited to 90/min, so a full 4-year backfill is a
multi-hour run; this session started it in the background and made partial
progress (see the calibration-log / handoff note for the exact day range
reached).

**Commit-size constraint discovered this session (applies repo-wide, not just
this datatype).** The `mcp__github__push_files` commit path silently
corrupts non-UTF-8 binary content passed directly as `content` (confirmed via
a byte-identity round-trip test: a raw Latin-1-decoded binary probe came back
mangled, while the same bytes base64-encoded as ASCII text round-tripped
byte-identical). Base64-as-text is therefore the only reliable way to commit
binary (zip/parquet) through this path, but at the cost of ~1.33x size
inflation, and every byte of `content` a session commits this way has to be
reproduced verbatim by the model in a tool call — which is only practical up
to roughly the same tens-of-KB/file ceiling `fetch_miso_hub_lmp.py`'s
docstring already independently discovered for its own plain-CSV chunking
(2026-07-09). Full-fidelity hourly multi-entity raw drops at the scale of the
existing PJM/NYISO/MISO 2023-2025 files (11-140 MB/year) are **not**
committable through this path in a single session; they were evidently
committed in an earlier era when `git push` (not the API) was still viable
for this repo. Until a bulk-upload path exists, holdout-year extensions of
these bulky raw datatypes should either land via a session that restores
`git push`, or accept a materially coarser (weekly/monthly-mean) companion
series clearly labeled as such alongside the full-fidelity file it summarizes.
