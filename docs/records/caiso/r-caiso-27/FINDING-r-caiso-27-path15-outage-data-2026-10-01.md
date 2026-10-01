# FINDING — R-CAISO-27: a Path-15 / Gates–Midway outage or derate record. SCOPING ONLY. Zero LP.

Keeper `2026-09-30-caiso-r20-overnight` (bundle `rcaiso20_A_span`, 2022–25), unchanged. No shard, no cell moved.
Probe: `scripts/probes/_rcaiso27_path15_outage.py` (CAISO OASIS `TRNS_OUTAGE`, fetched live, nothing committed).

## 0. The question

`caiso_fsno_subzonal_topology` is **R** (caiso-224): the static DMM element caps were falsified (F1 over-trap,
F2 year-ordered split vector vs reality's non-monotone 1,310 / 1,691 / 1,347 h). Its one data re-arm route is a
measured, backcast-admissible **outage / derate record for the Path-15 / Gates–Midway elements, 2022–25**.
Rule 13 test: a physical availability quantity (element out of service, derated rating), never a constraint
shadow price, congestion rent or curtailment outcome.

## 1. Answer: no public series exists

| Candidate | Public? | Path-15 internal elements? | Granularity | 2022–25 retrievable today? | Rule 13 |
|---|---|---|---|---|---|
| OASIS `TRNS_OUTAGE` (`CURTAILED_OTC_MW`) | Yes | **No** — intertie/ISL only since 2019-01-16 | Interface × direction, hourly window | Yes (verified live) | Admissible, **intertie-scoped** |
| OASIS `TRNS_USAGE` (R-CAISO-26) | Yes | No — interties only | Hourly OTC | Mid-2023+ | Admissible, intertie-scoped |
| OMS Transmission Outage Report (TOR) | **No** — CAISO certificate | Yes, element level | Hourly (7 d) / daily (1,000 d) | **No** — posted 3 calendar days, no archive | Would be admissible; no history |
| CRR Full Network Model outage set | **No** — NDA + certificate | Yes, >200 kV planned outages | Monthly snapshot | Not public; history unverified | Planning snapshot, not measured availability |
| CAISO Operating Procedures 6310 / 6310A (Path 15 OTC, Los Banos–Midway outage) | **No** — non-public | Yes | Static rules, no series | No | No series |
| WECC Path Rating Catalog | Yes | Path 15 aggregate | Static rating | Yes | Already used (`measured_interface_limits` K); static class falsified (caiso-218) |
| OASIS `PRC_NOMOGRAM` | Yes | Constraint names | Hourly / 15-min | Yes | **No** — price only, **no limit MW**, binding rows only (an outcome) |
| DMM quarterly / annual reports | Yes (PDF) | Narrative (e.g. Gates–Midway #2 congested 4 % of Q2-2023 hours) | Event narrative | Yes | No — congestion outcome, no dated outage windows |
| FERC 715 / NERC TADS / EIA | CEII / confidential / none | — | — | — | No |

Sources: OASIS interface spec v5.1.2; CAISO notice "OASIS transmission-related reports — transmission interface
identifiers" (intertie-only from 2019-01-16); OMS TOR FAQ (3-day retention); operating-procedures index (6310 /
6310A / 6320 non-public); CRR BPM v28 §3.5 (FNM via NDA); CAISO notice retiring selected Path-15 nomograms
(2019-10-17); DMM Q2-2023 report.

## 2. Verified live: `TRNS_OUTAGE` is intertie-scoped

Three sample months (Jun 2022, Nov 2023, Jun 2024; 4,389 / 5,009 / 8,571 rows) carry **50 distinct `TI_ID`s, every
one an intertie, ISL or intertie branch group** (`COTPISO_ITC`, `MALIN500_ISL`, `TRACY500_ITC`, `PATH_WOR`, …).
No Path 15, Path 26, Gates or Midway interface.

Path-15 elements appear **only as the cause text** of an intertie curtailment: Jun 2024, `OMS 15901361 …
Los Banos-500 LINE` curtails `COTPISO_ITC` (≤ 427 MW), `MALIN500_ISL` (≤ 3,050), `TRACY500_ITC`, `TRCYTEA_ITC` —
34 rows. Nov 2023: 0 rows. The Jun-2022 hits are a 2017 legacy row naming Midway–Vincent (Path 26).

That is not an availability series for the element: it records a Path-15 outage only when, and only to the
extent that, it happens to derate an intertie. Selected on an intertie consequence, it cannot say what the
Gates–Midway limit was in the hours the N–S split sets (local-curtailment hours, R-CAISO-23 §2).

## 3. What it means

- **No admissible public series exists.** The element-level truth lives in the OMS TOR (certificate, 3-day
  retention) and the CRR FNM (NDA). Neither is reconstructable from public history.
- `caiso_fsno_subzonal_topology` **stays R**. Its data re-arm route is closed for public data. The only remaining
  routes are a restricted-data request (CEII / NDA, owner action; feasibility and terms unknown) or caiso-222
  W-2 / W-3.
- A forward-recording workaround (archive the TOR daily from now) is not available without a CAISO certificate,
  and would not reach 2022–25 anyway.
- caiso-218 §F fences hold: no re-tune of static caps, no shadow-price or curtailment input.
- No matrix cell moves. CAISO shard gates stamp updated.

## 4. Owner card (2026-10-01)

Selected: **close link 9 → link 10 (R-CAISO-28)**. Not selected: a restricted-data (CEII / NDA) request, and
formally retiring the data re-arm route. fsno stays R; the restricted-data route is noted, not queued.
