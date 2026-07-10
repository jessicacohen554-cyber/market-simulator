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
| `lrr_wayback_20201029.pdf` | in force 2020-10-29 (Wayback) | SENY 30-min flat 1,300 MW; NYC 500/1,000; TSA zeroes SENY only |
| `lrr_wayback_20211204.pdf` | 2021-12-04 → ≥2026-02-14 (Wayback, byte-identical snapshots) | SENY 30-min hourly steps 1,300/1,550/1,800; NYC 500/1,000; TSA zeroes NYC 10T/30T + SENY 30T |
| `lrr_retrieved_20260710.pdf` | retrieved 2026-07-10 | NYC raised to 625/1,250; SENY steps unchanged |

Source URL (current): <https://www.nyiso.com/documents/20142/3694424/Locational-Reserves-Requirements.pdf>
Wayback snapshots: `web.archive.org/web/20201029110250` and `20211204105606`
of the same document path (see the CSV's `source_doc` column). Regenerate the
PDFs with `python scripts/fetch_nyiso_lrr_pdfs.py` (md5-verified).

Effective-date caveats (bounds, not pinned dates):
- The SENY hourly-step regime appears between 2020-10-29 and 2021-12-04 —
  plausibly with the July 2021 operating-reserve procurement enhancements
  (FERC accepted 2021-06-23, effective 2021-07-13), **unverified**.
- The NYC 625/1,250 MW raise appears between 2026-02-14 and 2026-07-10 —
  plausibly the 2026-05-01 capability year, **unverified**. Training years
  2023–2025 are fully inside the v2021 regime either way.
- The LI 270/540 on/off-peak hour boundary is not defined in the posting
  itself (`DATA NEEDED`: the defining Ancillary Services Manual /
  Transmission & Dispatch Operations Manual section).

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
