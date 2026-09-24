# NYISO reserve requirements & operating events (Ask B, `nyiso-data-asks-2026-07.md`)

Raw sources for the `nyiso-reserve-requirements` and `nyiso-operating-events`
datatypes — the measured inputs from which the condition-varying downstate
reserve requirement (issue #1344) is reconstructed. NYISO does **not** publish
the as-enforced locational reserve requirement as a continuous historical
series (confirmed 2026-07-10: no MIS/OASIS posting exists; the Dynamic
Reserves market design will post condition-varying requirements forward, but
it is not deployed for the backcast window). What NYISO does publish, and
what lives here:

## `locational-reserve-requirements/` + `nyiso_locational_reserve_requirements.csv`

Dated versions of NYISO's published "Locational Reserve Requirements" posting
(the static/hour-shaped requirement table by product × region), plus a
hand-transcribed CSV of every printed cell (source of the
`nyiso-reserve-requirements` clean datatype; curated by
`scripts/curate_nyiso_reserve_requirements.py`).

| file | evidence window | key values |
|---|---|---|
| `lrr_nyiso_v1.1_20160817.pdf` | nyiso.com doc version 1.1, created 2016-08-17 → in force until 2019-06-26 | no NYC region; SENY 30-min flat 1,300 MW (TSA → 0); NYCA/EAST/LI as v2020 |
| `lrr_nyiso_v1.2_20190624.pdf` | nyiso.com doc version 1.2, created 2019-06-24 → in force 2019-06-26 … | NYC region added 500/1,000 (no TSA footnote); every value identical to v1.3 |
| `lrr_wayback_20201029.pdf` | in force 2020-10-29 (Wayback) | SENY 30-min flat 1,300 MW; NYC 500/1,000; TSA zeroes SENY only |
| `lrr_wayback_20211204.pdf` | 2021-12-04 → ≥2026-02-14 (Wayback, byte-identical snapshots) | SENY 30-min hourly steps 1,300/1,550/1,800; NYC 500/1,000; TSA zeroes NYC 10T/30T + SENY 30T |
| `lrr_retrieved_20260710.pdf` | retrieved 2026-07-10 | NYC raised to 625/1,250; SENY steps unchanged |

Source URL (current): <https://www.nyiso.com/documents/20142/3694424/Locational-Reserves-Requirements.pdf>
Wayback snapshots: `web.archive.org/web/20201029110250` and `20211204105606`
of the same document path (see the CSV's `source_doc` column). Regenerate the
PDFs with `python scripts/fetch_nyiso_lrr_pdfs.py` (md5-verified).

**Version history (2026-09-24, session I-NYISO).** nyiso.com serves the
posting's own Liferay version history (`…/Locational-Reserves-Requirements.pdf?version=N`):
v1.1 (PDF CreationDate 2016-08-17), v1.2 (2019-06-24), v1.3 (2020-08-06 —
byte-identical to `lrr_wayback_20201029.pdf`), v1.4 (2021-06-17 — byte-identical
to `lrr_wayback_20211204.pdf`), v2.0/v2.1 (2026-05-13 — byte-identical to
`lrr_retrieved_20260710.pdf`) and v3.0 (2026-09-09, **not yet transcribed** —
2026 only, outside the 2019-2025 backcast span). v1.1 and v1.2 are the new
sources behind transcription versions `v2016` / `v2019`.

**Sourced effective dates** (`effective_start` / `effective_source` columns —
what the hourly derive switches versions on):
- `v2019` **2019-06-26** — the NYC locational reserve region was activated in
  the DAM and RT markets on Wednesday 2019-06-26 (S&P Global, 2019-06-24,
  republished on nyiso.com: "plans to activate Wednesday a new locational
  reserve region for New York City"). Before it the posting has no NYC region,
  so NYC 10/30-min requirements are 0 MW for 2019-01-01..2019-06-25.
- `v2020` **2020-08-06** — v1.3 CreationDate. Every requirement value is
  identical to v1.2 (wording-only revision), so this boundary moves no number.
- `v2021` **2021-06-17** — FERC docket ER21-625 ("SENY reserve enhancements"):
  -001 noticed 2021-06-08, -002 delayed to 2021-06-10, **-003 (filed
  2021-06-08, 86 FR 2021-12370) delayed to 2021-06-17**, the last notice in
  the docket; the v1.4 posting is created the same day (2021-06-17 12:41 ET).
  This supersedes the earlier "plausibly 2021-07-13" guess, which was the
  unrelated ORDC compliance date. v1.4 also introduces the NYC TSA-zeroing
  footnotes; they are dated with the same version.

Effective-date caveats (bounds, not pinned dates):
- *(Resolved 2026-09-24 — see above.)* The SENY hourly-step regime appears
  between 2020-10-29 and 2021-12-04 — plausibly with the July 2021
  operating-reserve procurement enhancements (FERC accepted 2021-06-23,
  effective 2021-07-13), **unverified**.
- The NYC 625/1,250 MW raise appears between 2026-02-14 and 2026-07-10 —
  plausibly the 2026-05-01 capability year, **unverified**. Training years
  2023–2025 are fully inside the v2021 regime either way.
- The LI 270/540 on/off-peak hour boundary is not defined in the posting
  itself. **RESOLVED 2026-07-26 (nyiso-83)** — it is defined in neither the
  Ancillary Services Manual nor the Transmission & Dispatch Operations Manual
  (both searched in full), but it *is* defined in the tariff: **MST §2.15
  Definitions-O** (effective 10/31/2025, Docket ER26-1265-000) —
  *"On-Peak: The hours between 7 a.m. and 11 p.m. inclusive, prevailing
  Eastern Time, Monday through Friday, except for NERC-defined holidays, or as
  otherwise decided by the ISO"*; Off-Peak is the stated complement (11 p.m.–
  7 a.m. Mon–Fri, all day Sat/Sun, and NERC holidays). Hour-beginning 7–22
  inclusive. Implemented as `model.reserves.spec.nyiso_onpeak_mask` /
  `nerc_holidays`; a published calendar rule, so it regenerates for any
  forward year (rule 13 admissible).
- LI demand-curve values (needed to build the family's ORDC steps) are
  **Ancillary Services Manual §6.8 items 10 and 15**: the Long Island
  10-minute and 30-minute reserves demand curves are both **$25/MW** — the
  same locational tier the published NYC products carry. LI also nests inside
  the $775 (E/SENY/NYC/LI) and $500/$40 (SENY/NYC/LI) tiers, and providers on
  Long Island settle as if providing reserves in SENY (ASM §6.5.2).

## `realtime-events/`, `oper-messages/`

Per-year re-serializations of the NYISO MIS public message logs (fetched by
`scripts/fetch_nyiso_operating_events.py`; source of the
`nyiso-operating-events` clean datatype):

- `realtime-events/NYISO_realtime_events_<year>.csv` — P-35 Real-Time Events
  (`mis.nyiso.com/public/csv/RealTimeEvents/`): Thunderstorm Alert start/end
  and start-of-day state, system state changes (normal/alert/major
  emergency), reserve pick-up initiation/termination, emergency capacity
  requests to proxy buses.
- `oper-messages/NYISO_oper_messages_<year>.csv` — P-25 Operational
  Announcements (`mis.nyiso.com/public/csv/OperMessages/`): out-of-merit
  reliability commitments (incl. explicit "FOR TSA" commits), emergency
  energy transactions, price-correction notices (noise for our purpose but
  preserved — raw is unfiltered). Upstream CSVs are malformed (doubled
  quotes, embedded newlines); the fetch script re-serializes valid CSV with
  message text preserved.

Timestamps in both feeds are Eastern prevailing wall-clock with no EDT/EST
marker (resolved to UTC at curation). Coverage: 2018-01 through 2026-06.
**Years 2018–2022 and 2026 are out-of-training intake under the
session-logged owner authorization of 2026-07-10** (CLAUDE.md rule 22;
itemized in `docs/out-of-sample-results-2026-07.md` §1.2). Nothing past
2026-06-30 exists here; the fetch script hard-caps at H1-2026.

Admissibility (rule 13): requirements, alert windows and reliability
commitment events are measured physical/market **inputs** that regenerate
for a forward year from forward drivers (published rules + weather/
contingency conditions). The measured reserve **prices** one directory up
(`data/raw/NYISO-AS/*.csv`) remain the validation target and must never
become an input.

DATA NEEDED (still open after this intake):
- B1 continuous as-enforced requirement series as scheduled into RTD/RTC —
  only available via a NYISO Market Operations data request.
- The LI on/off-peak boundary + EDRP/SCR-activation 30-min adder history
  (MST Rate Schedule 4 §15.4.6.2) if the requirement builder needs them.

## `NYISO_reserve_requirements_<year>.csv` (DERIVED — the loader-contract series)

Hourly measured requirement series consumed by
`src/market_sim/data/nyiso_reserve_requirements.py` when
`ScenarioConfig.nyiso_dynamic_reserve_requirements` is on. DERIVED, not a
download: reconstructed by `scripts/derive_nyiso_reserve_requirements_hourly.py`
from the two committed sources above —

    requirement(region, product, hour) =
        published LRR base (v-version covering the year; SENY 30-min hourly
        steps included) x (1 - TSA-window fraction of the hour) for the rows
        the version flags TSA-reduced-to-zero, else the base unchanged.

TSA windows come from the message logs with two documented repairs (both
itemized in the derive run log, never silent): an explicit "no longer
operating in thunderstorm alert" message always closes a window (genuine
overnight TSAs exist whose spanned midnight carries no start-of-day ACTIVE
attestation, e.g. 2025-03-31 -> 2025-04-01); a start whose end message is
missing from the log closes at its first midnight NOT attested by a
"Start of day thunderstorm alert state is ACTIVE" row (e.g. 2025-06-19,
2025-07-31 — conservative upper bound, the true end time that day is
unknown). Clock: naive Eastern wall-clock hour-beginning, Feb 29 dropped
(the model's non-leap 8760 clock; `process_nyiso_as.py` convention).

This is a documented LOWER BOUND on the as-enforced requirement in non-TSA
hours: the condition-varying RTD/RTC increments (forecast-uncertainty
adders, largest-single-contingency changes) are the still-open B1 data
request. Rule 24: re-derive only when the source data above updates —
never against a residual. Years 2019-2025 are committed (2019-2021 added 2026-09-24; 2022-2025
re-derived byte-identically by the version-stitching derive). 2019 and 2021
each switch LRR version mid-year at the sourced `effective_start` above; a
year whose boundary is unsourced is refused by the derive.
