# CAISO 2021 Q2 price intake — the GroupZip boundary, what it costs 2021, and the backfill scoping

**Session:** caiso-264, 2026-09-07. Branch `claude/caiso-2021-april-june-fetch-njpk1c`.
**Scope:** DATA + DOCS ONLY. No LP solved, no default changed, no run registered, no
keeper touched, no scoring. Rule 22 `[R-HOLDOUT]`: this is **intake**, which needs no
marker — only solving/scoring/registering an out-of-training year is the spend, and none
is done here.

**Headline.** The owner asked for CAISO 2021 April → end of June. **April 1–26 is
permanently unobtainable**: OASIS GroupZip has its own retention boundary, measured this
session at **2021-04-27**, and it moves with the calendar. Fetched 2021-04-27..06-30 on
every axis, plus the FULL Apr 1 – Jun 30 quarter on the non-LMP reports, whose retention is
deeper. **A 2021 CAISO price basis is now capped at 5,976 h against a 6,500 h guard**, and
the cap tightens by 24 h/day.

---

## 1. The boundary — measured, not assumed

Binary-searched against the live endpoint, `DAM_LMP_GRP` v12, 2026-09-07:

| trade date | result |
|---|---|
| 2021-03-31 · 04-01 · 04-02 · 04-15 · 04-22 · 04-26 | `No data returned for the specified selection` (error envelope, XML members only) |
| **2021-04-27** | **9.85 MB, four component CSVs** |
| 2021-04-28 · 04-30 · 05-01 · 05-15 · 06-01 · 06-30 | OK, 9.86–10.24 MB |

`RTM_LMP_GRP` v3 tracks the same boundary exactly: 2021-04-26 HE01 → no data;
2021-04-27 HE01 → 6.94 MB; 2021-04-27 HE19 and 2021-06-30 HE13 → OK.

**Independently corroborated.** Session caiso-263 bisected the same date from a different
lane and landed it in `data/raw/lmp-data/CAISO/README.md` (commit `12648526`, *"bound the
OASIS GroupZip retention window — 2021-04-27, not unlimited"*), including the finding that
it is a property of the **report**, not the version or market, and that it **moves**. Two
independent measurements agreeing on the day is the strongest form this claim can take.
**Never hardcode it — re-measure.**

## 2. What was fetched (this session)

| dataset | route | window | result |
|---|---|---|---|
| DAM LMP | `fetch_caiso_oasis_grp.py --market dam` | 2021-04-27..06-30 | **65/65 dates, 0 missing, 0 partial**; 0.653 GB transferred, 580 s |
| RTM LMP | `fetch_caiso_oasis_grp.py --market rtm` | 2021-04-27..06-30 | **65/65 dates, 0 missing, 0 partial**; 1,560 requests, 10.969 GB, 13,690 s (3.8 h) |
| `asprc_{ru,rd,sr,nr}`, `asresults`, `load` | `fetch_caiso_oasis.py` | **2021-04-01..06-30 (full quarter)** | deeper retention — covers the LMP gap |

DAM verification: 62,400 rows, 4 components (LMP/MCC/MCE/MCL), **1,560 distinct hours =
exactly 65 × 24, dense, no gaps**, and the node set is **identical** to the one
`CAISO_dam_hourly_2022.csv` carries (3 hubs + 4 DLAPs + CAPTJACK / MALIN / PALOVRDE). Same
publisher, reports, components and downstream chain as 2022–2025, so **rule-14 alignment is
exact and no reconciliation is engaged** — the same conclusion the 2022 charter reached.

RTM verification: 936,000 rows, 5 components (LMP/MCC/MCE/MCL/MGHG), **18,720 five-minute
intervals = exactly 65 × 288**, 10 nodes, 0 zips left behind (extract-and-discard held).

Hub means, 2021-04-27..06-30 DAM: **NP15 $42.67, SP15 $38.37, ZP26 $36.78/MWh** (vs 2022
full-year NP15 $89.03 / SP15 $84.80 / ZP26 $82.12). A drought-year shoulder quarter below a
gas-spike year is the expected ordering; this is a plausibility note, not a calibration
claim. RTM over the same window is **NP15 $36.32, SP15 $32.04, ZP26 $29.81/MWh** — below DA
at every hub, the ordinary CAISO spring DA premium.

Intertie parquet (`wecc_intertie_lmp_hourly_CAISO.parquet`, built from the DAM windows
BEFORE postprocess stages them out — see §5): 70,080 → 87,600 rows; 2021 carries **exactly
1,560 finite hours per hub** on the dense 8,760 calendar (MALIN $41.25, PALOVRDE
$37.92/MWh), the rest NaN by construction. The pre-existing rows are untouched — 2022 MALIN
$86.39 / PALOVRDE $82.95 reproduce caiso-261's recorded figures exactly.

**The non-LMP reports are the important half.** 2021 previously carried `asreq` only (16
full-year windows); `asprc_*`, `asresults` and `load` were absent — exactly the sparse state
2020 was in before caiso-263 filled it. Those reports outlive `PRC_LMP`, which is *why*
caiso-263's Q2-2020 lane could fetch AS and load for a quarter with no obtainable LMP at
all. So **the Apr 1–26 gap is a price-only gap**; every other axis covers the full quarter.

## 3. What the boundary costs 2021 — the part that needs a decision

```
boundary today (2026-09-07)      2021-04-27
max obtainable 2021 span         2021-04-27 .. 12-31  = 249 d = 5,976 h
derive_actual_lmp.py floor       6,500 h   (CAISO_MIN_HOURS)
shortfall even if ALL fetched      524 h
```

`CAISO_PARTIAL_YEARS` is `frozenset({2026})` — 2021 is not in it, so 2021 must clear the
full 6,500 h and **cannot, ever**. Consequences:

1. A 2021 CAISO price basis requires an **explicit, declared** `CAISO_PARTIAL_YEARS`
   amendment adding 2021. That is a deliberate code change with a stated floor, not
   something to slip in beside a data commit — and it is **not done here**.
2. Of the 5,976 h ceiling, **1,560 h are now in hand** and **4,416 h (Jul 1 – Dec 31) are
   still obtainable today**.
3. **The ceiling drops by 24 h for every day of delay.** Jan–Apr 2021, all of 2020 and all
   of 2019 are already gone from OASIS by any endpoint.

## 4. Third-party backfill scoping (owner card, 2026-09-07)

Asked: can Apr 1–26 2021 CAISO hub LMPs be obtained from a non-OASIS source? Every row was
probed from this environment on 2026-09-07.

| # | candidate | evidence | verdict |
|---|---|---|---|
| 1 | **`gridstatus` package** (PyPI 0.36.0, BSD-3, sdist `gridstatus-0.36.0.tar.gz`) | Read `gridstatus/caiso/caiso_constants.py`: its LMP route is `queryname: PRC_LMP` against **OASIS** — the *per-node* endpoint, whose ~39-month retention is **shallower** than the GroupZip route we already use | **REJECTED — strictly worse than the primary route held.** No new bytes exist behind it |
| 2 | **`gridstatus.io` hosted API** | `401 {"detail":"Missing API Key."}`; site + docs behind Cloudflare (403 to this environment), so **licence terms cannot be read verbatim** | **REFUSED** — same verdict as the 2022 charter §3 and `FINDING-spp-14-2026-09-06-session-b.md` row 1. Key-gated, terms unreadable |
| 3 | **CAISO Today's Outlook history** (`www.caiso.com/outlook/history/{yyyymmdd}/{stem}.csv?_=<cb>`) — a **different host** from OASIS with its own retention | Enumerated the served stems on a known-good date: `fuelsource`, `demand`, `netdemand`, `co2` return 200; `prices`, `lmp`, `curtailment`, `batteries`, `emissions` all 404 | **DEAD END for price.** Genuinely useful for demand/fuel-mix/CO2, and worth remembering as a non-OASIS retention pool — but it publishes no LMP |
| 4 | **CAISO Open Data portals** (`odp.` / `catalog.` / `opendata.caiso.com`) | Gateway 502 on CONNECT — **cannot distinguish policy denial from a nonexistent host**. `www.caiso.com` and `oasis.caiso.com` both resolve normally from here, so a blanket caiso.com block is unlikely and "these hosts do not exist" is the more probable reading | **UNRESOLVED, low prospect.** Stated as unresolved rather than refuted |
| 5 | **`isodart.io`** | Gateway 502 on CONNECT, same ambiguity as #4 | **UNRESOLVED** |
| 6 | **EIA / ICE daily indices** | EIA publishes no hourly nodal or hub LMP; ICE indices are **daily** | **REJECTED on basis**, as the 2022 charter §3 already ruled — a daily index is not the hourly RT hub series C3a/C3b/C3c score |
| 7 | **CAISO DMM quarterly / annual reports** | Publish **monthly average** hub prices | **Not a basis.** Usable only as a level cross-check, never as a scored series |

**Scoping conclusion.** No source tested supplies hourly CAISO hub LMPs for 2021-04-01..26.
The one route that would have been rule-14 clean (a second primary CAISO publication with
deeper retention) is Today's Outlook, and it carries no price file. **caiso-263's README
statement stands as written and is now independently tested from a second direction:** a
price basis for 2019, 2020 and Jan–Apr 2021 needs a different source adjudicated under
rule 14, and this session did not find one. Rows 4–5 are the only unexhausted leads and both
are low-prospect.

## 5. Two defects found in the intake path (both closed here)

**(a) The DST head window.** `fetch_caiso_oasis.UTC_OFFSET_HOURS = 8` is PST, so in a PDT
month a range's first request instant lands at 01:00 local: **2021-04-01 came back HE2–HE24**,
and the range spilled into 2021-04-26 HE1. Verified in-data before the fix, then closed with
the `--start-date 2021-03-31 --end-date 2021-04-01` head window. Caught only because
caiso-263 wrote the note up in `data/raw/CAISO-AS/README.md` after hitting it on Q2-2020 —
it is silent otherwise, and it bites the START of every new range. All six datasets are now
**2,184/2,184 (day, hour) pairs** for Apr 1 – Jun 30.

**(b) The MWD-TAC seam — the one that would have done real damage.** `CAISO_TACS` gained
`MWD-TAC` on 2026-08-05 (caiso-175, rule 14: a measured area replacing a pro-rata
re-apportionment of it), but the committed `CAISO_tac_load_hourly_{2020,2021}.csv` predate
that change and carry five areas. Re-folding **one quarter** adds MWD for that quarter only —
2,208 h against the other areas' 8,760 — and `load_zonal_shares` NORMALISES component TACs to
1.0, so a ragged sixth area is not a missing column but a **within-year discontinuity in the
zonal shares**, an artifact of intake vintage rather than of load. Closed by re-fetching
full-year load for both years with `--force` (required: the coverage check reads one
reference series, so a newly-kept series can never be back-filled without it). Both
aggregates are now uniform six-area full-year, and the change is a **pure addition** — every
pre-existing row byte-identical, 0 mismatches, 0 dropped, verified against `HEAD`.

**(c) Left for the owner, deliberately not resolved here.** `postprocess_oasis_downloads.py
--stage-dir` stages raw `load_*.csv` windows OUT by design, but the Q2-2020 intake
**committed** its five `load_ALL_2020*.csv` windows — so a postprocess run in any lane now
surfaces them as deletions of tracked files. They were **restored**, not deleted in this
lane's diff. Either those windows are committed for every year or for none; `asprc_*` /
`asresults_*` are a different case (no aggregate) and are correctly committed.

## 6. What is owed / recommended

* **Not done here, deliberately:** no `derive_actual_lmp.py` / `derive_actual_tail.py` run
  (2021 fails the 6,500 h guard, by construction — §3), no `CAISO_PARTIAL_YEARS` amendment,
  no solve, no score, no registration. The owner's card was *fold + push, then stop*.
* **Time-critical, owner's call:** crawl **2021-07-01..12-31** (DAM ~30 min; RTM 4,416
  requests ≈ 11–13 h) while it is still served. It is the difference between a 5,976 h and a
  1,560 h ceiling for 2021, and the window shrinks 24 h/day. Deferring it is a real,
  irreversible cost — unlike most deferrals in this program.
* **Standing:** the boundary MOVES. Any future lane touching pre-2023 CAISO prices
  re-measures it first and never hardcodes the date.
