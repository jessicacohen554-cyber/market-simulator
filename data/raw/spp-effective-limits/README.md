# `spp-effective-limits` — SPP RTBM effective limits (2022-04-14 onward)

Opened **2026-10-22** by lane **UC-SPP-CORRIDOR** (owner ruling R30). Finding:
`docs/records/spp/FINDING-uc-spp-corridor-2026-10-22.md`.

## What this is

SPP's own published operating limits for every Real-Time Balancing Market
constraint-interval that was ACTIVATED, BINDING or BREACHED: `Source Limit`
(the FAC-011 system operating limit), `Realtime Effective Limit` (the value
enforced in RTBM, TOP-001) and `Initial Effective Limit`.

It is a **separate portal product** from `rtbm-binding-constraints`
(`../spp-binding-constraints/`). That archive gained limit columns only on
2026-03-17 (`FINDING-spp-53` §3.1), which is why SPP-53 had to build the N↔S
link from 2026 limits. This product carries them from **2022-04-14**. Lanes
SPP-12/13/14/53 searched only the binding-constraint product; this one was
found in the portal menu (`GET https://portal.spp.org/api/menu/`, slug
`effective-limits`).

## Source

| item | value |
|---|---|
| landing page | <https://portal.spp.org/pages/effective-limits> |
| listing | `GET https://portal.spp.org/file-browser-api/?fsName=effective-limits&path=%2F<YYYY>%2F<MM>%2FBy_Day&type=folder` |
| download | `GET https://portal.spp.org/file-browser-api/download/effective-limits?path=%2F<YYYY>%2F<MM>%2FBy_Day%2FRTBM-EFFLIMIT-<YYYYMMDD>.csv` |
| access | anonymous HTTPS (same route as `fetch_spp_alt_portal.py`) |
| SPP's description | "Provides effective limit information associated with binding constraints." Column definitions quoted from `GET /api/pageConfig/by-slug/effective-limits` (`fs_html`), read 2026-10-22 |
| coverage | 2022-04-14 → present, one file per operating day; nothing before 2022-04-14 is served |
| licence | SPP public market data; no restriction stated (as `../spp-binding-constraints/SOURCES.md`) |

Header (verbatim; note the leading spaces on the last three names):

```
Interval,GMTIntervalEnd,Constraint Name,Constraint Type,NERCID,TLR Level,State,Shadow Price,Monitored Facility,Contingent Facility, Source Limit, Realtime Effective Limit, Initial Effective Limit
```

`Interval` / `GMTIntervalEnd` are interval-**ending** stamps (Central / UTC),
`MM/DD/YYYY HH:MM:SS`.

## Layout

| path | committed | content |
|---|---|---|
| `by_day/<YYYY>/RTBM-EFFLIMIT-<YYYYMMDD>.csv` | **no** (gitignored, ~3 GB for 2022–2025) | the day files, byte-for-byte |
| `SHA256SUMS.txt` | yes | `<sha256> <bytes> <file>` for every day file pulled |
| `rtbm_efflimit_bound_<YYYY>.csv.gz` | yes | the BINDING + BREACHED lines of that year's day files, verbatim, one header; ACTIVATED rows (~90 %) dropped |
| `Temp_Flowgate_Archive.csv` | yes | SPP `archive-temporary-flowgates` (`GET .../download/archive-temporary-flowgates?path=%2FTemp_Flowgate_Archive.csv`, portal-stamped 10/21/2026), byte-for-byte: every temporary SWPP flowgate since 2014 with static Norm/Emer limits and create/remove times. Ratings, not effective limits |

Rebuild: `python scripts/data/fetch_spp_effective_limits.py --years 2022 2023 2024 2025`
then `... --reduce`. Curated to `data/clean/flowgate-limits-at-bind/SPP/rt/`
by `python -m scripts.data.curate_flowgate_limits_at_bind`.

## Use and limits (rules 13 / 14)

- A limit here is an **element-under-contingency** rating, not an interface
  transfer capability. Converting it into one needs a transfer sensitivity
  (SPP-53's ψ); that conversion is where the uncertainty lives.
- The limits are admissible inputs. **When** a constraint binds is a dispatch
  outcome; the binding hours are evidence, never a target.

DATA NEEDED: none for 2022-04-14 → 2025. **2019 – 2022-04-13 have no
effective-limit series on the portal**; the only in-window limit evidence for
those years is the static `NormLimit`/`EmerLimit` in SPP's
`archive-temporary-flowgates` (`Temp_Flowgate_Archive.csv`) and the seasonal
ratings in `permanent-flowgates`.
