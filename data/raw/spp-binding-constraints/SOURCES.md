# `spp-binding-constraints` — SOURCES

Every URL below was probed on **2026-09-06** by lane SPP-12. None returned data;
each is a manual-manifest row until a Marketplace credential exists. No value in
this directory or its README was taken from memory.

## Host

`portal.spp.org` (`marketplace.spp.org` 302-redirects to it — verified).

### `da-binding-constraints` — Binding Constraints (Day-Ahead)

- **Landing page:** <https://portal.spp.org/pages/da-binding-constraints>
- **Listing:** `GET https://portal.spp.org/file-browser-api/?fsName=da-binding-constraints&path=<path>&type=folder`
  (`path` percent-encoded; `path=` empty is the root; the trailing slash on
  `file-browser-api/` is part of the route)
- **Download:** `GET https://portal.spp.org/file-browser-api/download/da-binding-constraints?path=<path>`
- **Header required:** `X-SPP-UI-Token: <Marketplace UI token>` — **this repo has none**
- **Probed 2026-09-06:** listing HTTP **200** `[]` · download HTTP **404** · `isPublic` **true**

### `rtbm-binding-constraints` — Binding Constraints (Real-Time)

- **Landing page:** <https://portal.spp.org/pages/rtbm-binding-constraints>
- **Listing:** `GET https://portal.spp.org/file-browser-api/?fsName=rtbm-binding-constraints&path=<path>&type=folder`
  (`path` percent-encoded; `path=` empty is the root; the trailing slash on
  `file-browser-api/` is part of the route)
- **Download:** `GET https://portal.spp.org/file-browser-api/download/rtbm-binding-constraints?path=<path>`
- **Header required:** `X-SPP-UI-Token: <Marketplace UI token>` — **this repo has none**
- **Probed 2026-09-06:** listing HTTP **200** `[]` · download HTTP **404** · `isPublic` **true**

## Authoritative reference for the access route

- **SPP System Interfaces Stakeholder Reference Guide** —
  <https://www.spp.org/media/2598/spp-system-interfaces-stakeholder-reference-guide.pdf>
  (tracked at `data/raw/spp-planning/spp-system-interfaces-stakeholder-reference-guide.pdf`).
  Its **Public Data Specifications** section names the **"SPP Public Data Access"**
  guide — "Reference guide for accessing public data via the SPP Portal **and FTP**" —
  under Stakeholder Center > User Guides, APIs & Integrations > Technical Reference
  Documents > Public Data. The FTP route is **untried** and is the most promising
  unblocked path.

## Blocked / alternative hosts

| Host | Status 2026-09-06 | Note |
|---|---|---|
| `portal.spp.org` file-browser | listings `200 []`, downloads `404` | needs `X-SPP-UI-Token` |
| `marketplace.spp.org` | `302` to `portal.spp.org` | not a separate route |
| `oasis.oati.com/SWPP` | blocked (per plan §2.4) | login required |
| `www.spp.org` | **200, fully reachable** | planning PDFs — see `data/raw/spp-planning/` |

## Appended 2026-09-06 by lane SPP-13 — the FTP route

- **Reference:** `SPP Public Data Access` v3.0 (July 2023) — <https://www.spp.org/Documents/28853/SPP%20Public%20Data%20Access%2020230707.pdf>
  (tracked at `data/raw/spp-planning/SPP_Public_Data_Access_20230707.pdf`), p. 2: programmatic access is FTP, `ftp://pubftp.spp.org`.
- **Credential:** `SPP Markets Public Data Guide v35` (tracked as `data/raw/spp-planning/SPP_Markets_Public_Data_Guide_v35.docx`), "FTP Site Access": user `anonymous`, password = an email address.
- **Folders:** `ftp://pubftp.spp.org/Markets/RTBM/BINDING_CONSTRAINTS/` · `ftp://pubftp.spp.org/Markets/DA/BINDING_CONSTRAINTS/` · `ftp://pubftp.spp.org/Markets/DA/Congestion-Constraint`
- **Probed 2026-09-06:** `CONNECT pubftp.spp.org:21` through the session egress → tunnel opens, **no FTP banner within 36 s**, relay closes; identical for control hosts `ftp.gnu.org:21` and `ftp.debian.org:21` → **egress policy blocks FTP**, not SPP. Ports 443/990 reset after ClientHello. `WebFetch`: "Unsupported protocol ftp:".
- **Schema source:** sample files inside <https://www.spp.org/Documents/75871/SPP%20Markets%20Public%20Data%20Guide%20and%20Samples%20v35.zip> (82.6 MB, not tracked; sha256 in `data/raw/spp-planning/SHA256SUMS.txt`).


## Appended 2026-09-06 by lane SPP-14 — THE PORTAL ROUTE IS OPEN, ANONYMOUS, OVER HTTPS

**This supersedes the "Blocked / alternative hosts" row above for `portal.spp.org`.**
Lane SPP-14 re-probed the portal while sweeping third-party sources and found both
file-browser calls answering anonymously over plain HTTPS — no `X-SPP-UI-Token`, no
cookie, no FTP. The two corrections, each measured 2026-09-06:

| Call | SPP-12 read | SPP-14 measured |
|---|---|---|
| `GET /file-browser-api/download/<fs>?path=<FILE path>` | `404`, zero bytes | **HTTP 200, `text/csv`**, the real file. The 404s were path-shaped: the route serves *files*, so a folder path — or a path that does not exist in that product's archive layout — 404s correctly |
| `GET /file-browser-api/?fsName=<fs>&path=%2F&type=folder` | `200 []` at "every path/type form" | **HTTP 200 with the real JSON directory array.** The literal `[]` reproduces only for `path=` **empty**, which is the SPA's own first call — an empty-path artifact, not authorization |
| `Range:` requests | not tried | **honoured** (`Accept-Ranges: bytes`, `206`), so an archived `<year>/<year>.zip` is read member-by-member without downloading the body |

Corroborating witness: the open-source `gridstatus` package's SPP client reads these
same URLs with a bare `pandas.read_csv(url)` and carries no credential at all
(`gridstatus/spp.py` v0.36.0, sdist read 2026-09-06 from `files.pythonhosted.org`).

**Licence.** SPP states no licence or redistribution restriction on these public
market files; they are published as SPP's public data (guide: `SPP Public Data
Access` v3.0, tracked in `data/raw/spp-planning/`). Landed byte-for-byte, unmodified.

**Producer:** `scripts/data/fetch_spp_alt_portal.py` (rows 6-9);
`scripts/data/build_spp_lmp_reference.py` **runs unmodified** against this route (row 5).

### Route OPEN, archive measured, payload deliberately NOT landed (row 8)

The RTBM binding-constraint archive is reachable anonymously and is **small**:

| Year | Portal path (`fsName=rtbm-binding-constraints`) | Bytes | Yearly rollup inside |
|---|---|---|---|
| 2023 | `/2023/2023.zip` | 58,684,654 | `2023/RTBM-BC-YEARLY-2023.csv.zip` -> 484,341,150 B CSV |
| 2024 | `/2024/2024.zip` | 70,104,073 | `2024/RTBM-BC-YEARLY-2024.csv.zip` -> 539,367,345 B CSV |
| 2025 | `/2025/RTBM-BC-YEARLY-2025.csv.zip` | 24,985,891 | `RTBM-BC-YEARLY-2025.csv` -> 659,007,717 B CSV |

All three were pulled and parsed in-session by SPP-14. **The payload is not committed**:
the SPP-14 charter scopes the four-group table to the FINDING, and 154 MB of zips (1.7 GB
inflated) is not a pack this lane pushes for a table that is already written down. Git
history is the record (rule 15 `[R-DASHBOARD]`); the pull is one command against the route
above. The four-group binding-share table, the derived group membership and the flowgate
registries it rests on are in `docs/handoffs/FINDING-spp-14-2026-09-06.md` sections 4-5.

**SCHEMA CORRECTION — this changes what SPP-53 can measure.** `FINDING-spp-13` section 3
recorded a **14-column** schema with `Source Limit` / **`Real Time Effective Limit`** /
`Initial Effective Limit` / `Interconnect`, read from the v35 zip's
`RTBM-DAILY-BC-20260128.csv` sample. The archive SPP **serves** carries only the first
**10** columns for every file up to and including 2026-03-24, and the four extra columns
appear from 2026-04-01 (measured: 2026-03-23 and 2026-03-24 are 10 columns; 2026-04-01,
-04-08, -04-15, -05-01, -06-01, -07-01, -08-01 and -09-01 are 14 — the same
2026-03-24 format break the `gridstatus` client records for hourly load). The 2023-2025
files carry **no effective-limit column at all**, so **the RTBM binding-constraint
archive cannot supply SPP-53's measured N<->S limit for the calibration span.** It can
from 2026-04 forward. SPP-53 stays on the rule-14 Tier-3 reconciled estimate that P11
ruled for SPP-20; the permanent-flowgate registry's seasonal `Normal`/`Emergency` MW
ratings (below) are the better measured substitute.

### Flowgate registries — landed by SPP-14 (the group-membership basis)

| File | Portal path | Rows | What it carries |
|---|---|---|---|
| `Flowgates.csv` | `fsName=permanent-flowgates`, `/Flowgates.csv` | 823 | permanent flowgates: `Flowgate`, `From Area`/`To Area` control-area codes, `Voltage`, seasonal `Normal`/`Emergency` MW ratings, `IROLLimit`, `Interconnect` |
| `Temp_Flowgate.csv` | `fsName=temporary-flowgates`, `/Temp_Flowgate.csv` | 3,298 | temporary constraints (the `TMP*`/`TEMP*` names that carry most SPP binding): same area codes plus `NormLimit`/`EmerLimit`, `CreatedTime`, `TOP` |

These are what makes the four-group membership **measured rather than asserted**: every
flowgate carries SPP's own `From Area` / `To Area`. **The four groups themselves are
unchanged** — they were fixed in this README before any data existed (rule 1
`[R-STRUCT]`), and SPP-14 changed no group, no definition and no ranking test. What this
README always reserved to "the session with the data" — *"the actual membership has to be
derived from the delivered flowgate names, which is a judgement the session with the data
makes and records"* — is recorded in FINDING-spp-14 section 4.1, area code by area code.
## Appended 2026-09-06 by lane SPP-14 — the portal route is OPEN; the RTBM 2023–2025 roll-ups landed

- `https://portal.spp.org/file-browser-api/download/rtbm-binding-constraints?path=%2F2023%2F2023.zip` (58,684,654 B) and `…%2F2024%2F2024.zip` (70,104,073 B): only the `RTBM-BC-YEARLY-<yr>.csv.zip` member landed (18,955,353 / 20,916,813 B).
- `https://portal.spp.org/file-browser-api/download/rtbm-binding-constraints?path=%2F2025%2F<mm>%2FRTBM-BC-MONTHLY-2025<mm>.csv.zip` ×12 (1.9–2.6 MB each).
- Schema-change bracket: `…?path=%2F2026%2F01%2FBy_Day%2FRTBM-DAILY-BC-20260127.csv` is 10-column; `…20260128.csv` (SPP-13's sample) is 14-column.
- The DA binding-constraint product (`da-binding-constraints`, `DA-BC-YEARLY-<yr>.zip`) and `Markets/DA/Congestion-Constraint` were listed but NOT landed (the RT table is what card P1 asks for).
- Producer: `scripts/data/fetch_spp_alt_portal.py --only binding-constraints`. Checksums: `SHA256SUMS.txt` (new).

## Appended 2026-09-07 by lane SPP-53 — the 2026 daily RTBM BC files (pulled, NOT landed) and the reduced corridor sidecar (landed)

- `https://portal.spp.org/file-browser-api/download/rtbm-binding-constraints?path=%2F2026%2F<mm>%2FBy_Day%2FRTBM-DAILY-BC-<yyyymmdd>.csv`, every day 2026-01-28 → 2026-09-05 (221 files, 1.9–3.3 MB each, ~550 MB; listed via `?fsName=rtbm-binding-constraints&path=%2F2026%2F<mm>%2FBy_Day&type=folder`). Anonymous HTTPS, byte-for-byte as served, to the session scratchpad only. **Schema-break correction**: 14-column rows begin 2026-03-17 (one day), recur on 2026-03-25 from 10:25 local under a 10-column header, and are continuous from 2026-04-01; the served `20260128.csv` is 10-column.
- `rtbm_bc_corridor_limits_2026.parquet` — DERIVED from those files by `docs/handoffs/spp53/extract_2026.py` (the `n_s_corridor` rows under `docs/handoffs/spp14/groups.py`'s unchanged rules, `State ∈ {BINDING, BREACHED, ACTIVATED}`, 563,450 rows, 2026-03-17 → 2026-09-06 UTC). sha256 `b5756023cef5da66ed23bf86a54a09e88d5a072a54ff8c027877c7b067a4626f`. Licence as above (SPP Terms & Conditions).

## Appended 2026-09-07 by lane SPP-57 — the reduced Oklahoma-set sidecar (landed)

- **Route:** the same anonymous HTTPS daily files as the SPP-53 row above
  (`rtbm-binding-constraints`, `/2026/<mm>/By_Day/RTBM-DAILY-BC-YYYYMMDD.csv`, 2026-01-28 →
  2026-09-05, 221 files, 0 failures; pulled by `docs/handoffs/spp53/pull_daily.py`, scratch only).
- **`rtbm_bc_oklahoma_limits_2026.parquet`** — producer `docs/handoffs/spp57/extract_2026.py`;
  rows = `State ∈ {BINDING, BREACHED, ACTIVATED}` × 14-column days × group ∈ {`oklahoma_internal`,
  `sps_tie`, `other`/"other areas: CSWS"}; 1,083,301 rows, 2026-03-17 05:05 → 2026-09-06 05:00 UTC;
  sha256 in `SHA256SUMS.txt`. Licence: SPP Terms & Conditions as quoted above.

## Appended 2026-09-25 by lane SPP-80 — the RTBM 2019–2022 yearly roll-ups (landed)

- `https://portal.spp.org/file-browser-api/download/rtbm-binding-constraints?path=%2F<yr>%2F<yr>.zip`
  for 2019 (161,777,119 B), 2020 (139,132,459 B), 2021 (126,077,359 B), 2022 (65,660,974 B).
  Only the yearly roll-up member was range-read out of each archive (central directory over
  `Range:`, never the body), exactly as SPP-14 did for 2023–2024:
  `2019/RTBM-BC-YEARLY-2019.csv.zip` (13,068,192 B), `2020/RTBM-BC-YEARLY-2020.csv.zip`
  (10,882,285 B), `2021/RTBM-BC-YEARLY-2021.csv.zip` (17,249,564 B), and
  **`2022/RTBM-BC-YEARLY-2022.zip`** (20,481,650 B) — SPP names the 2022 member without the
  `.csv` infix and nests the CSV one folder deep (`RTBM-BC-YEARLY-2022/RTBM-BC-YEARLY-2022.csv`);
  landed under SPP's own name, unmodified.
- Schema: the same 10 columns as 2023–2024 (`Interval, GMTIntervalEnd, Constraint Name,
  Constraint Type, NERCID, TLR Level, State, Shadow Price, Monitored Facility, Contingent
  Facility`), verified on the first row of every year. No effective-limit column, as for 2023–25.
- Producer: `fetch_spp_alt_portal.central_directory` / `read_member` (unmodified) driven for
  2019–2022. Checksums appended to `SHA256SUMS.txt`. Use: the SPP-80 FINDING
  (`docs/handoffs/FINDING-spp-80-upper-tercile-premium-2026-09-25.md`).
