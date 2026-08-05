# NYISO NY-NJ PAR data — P-33 `outSched` + P-34 `ParFlows`

Curated by `scripts/data/fetch_nyiso_par_data.py`. Intaken 2026-08-05 (nyiso-127)
under the owner authorization of that date, for the eastern-seam attribution
identified at nyiso-126 and amended at nyiso-127.

## What this is for

NYISO's posting *"NY-NJ PAR Interchange Percentages, Operational Base Flow (OBF),
and other MW Offsets"*
(<https://www.nyiso.com/documents/20142/2268509/NY-NJ_PAR_Interchange_and_OBF.pdf>,
percentages effective 5/1/2017; OBF identically 0 MW since 11/1/2019) directs a
published percentage of the PJM-AC interchange over eight named PARs:

| interface | PARs | share each | interface total | NY zone |
|---|---|---:|---:|---|
| Hopatcong–Ramapo | 3500, 4500 | 16 % | 32 % | G |
| JK | E, F, O (Waldwick) | 5 % | 15 % | G |
| ABC | A (Goethals), B, C (Farragut) | 7 % | 21 % | J |
| — residual | free-flowing western AC ties | — | 32 % | A |

and closes the rule: *"If a PAR is out of service, interchange normally
distributed over that PAR will be modeled over the free-flowing western AC tie
lines between NYISO and PJM."* **The split is therefore a function of PAR
availability, not a constant.**

## Files

* **`NYISO_par_outages.csv`** — 66 deduplicated published outage windows for the
  eight PARs, 2023-2025. Columns: `ptid, equipment_name, outage_start,
  outage_end, par, interface, published_share`. Source: MIS P-33 `outSched`.
  This is BOTH the PAR ↔ PTID identity (`equipment_name` matches the posting's
  PAR names exactly) and the in-service state.
* **`NYISO_par_flows_hourly_<year>.csv.gz`** — hourly mean measured flow for the
  same eight PARs. Source: MIS P-34 `ParFlows` (5-minute, 63 PTIDs; curated to
  the eight the posting names). Keyed by LOCAL wall-clock. Used as INDEPENDENT
  CORROBORATION of the outage state, not as the state itself — `ParFlows`
  carries a bare numeric `Point ID` and no facility name, so it cannot identify
  which PAR a PTID is.

## The measured state, 2023-2025

**ABC-B and ABC-C (Farragut TR11 / TR12) have been out of service since
2018-01-15 and are out for 100 % of every hour of 2023-2025** — a single window
whose `Scheduled In` is rolled forward (2023-01-31 → … → 2026-02-01), matching the
Operating Study's note that the Marion–Farragut 345 kV B and C cables are
"expected to remain open". Corroborated exactly: both measure **0.00 MW in every
five-minute interval** while the in-service PARs carry ±200-570 MW.

Resulting availability-conditioned split of the PJM-AC interchange:

| year | Capital_Hudson (G) | NYC (J) | Upstate_West (A) |
|---|---:|---:|---:|
| 2023 | 45.7 % | 7.0 % | 47.3 % |
| 2024 | 46.8 % | 6.8 % | 46.4 % |
| 2025 | 46.4 % | 6.8 % | 46.8 % |

not the flat 47 / 21 / 32 the nameplate percentages imply.

## Provenance / rules

* Rule 13 `[R-MEASURED]`: an INPUT (published percentages × published
  availability), regenerable for a forward year, never an outcome pinned to a
  residual.
* Rule 22 `[R-HOLDOUT]`: 2023-2025 only. Extending to any out-of-training year
  needs its own session-logged owner authorization.
* Evidence:
  `results/calibration/PREREG-nyiso126-eastern-seam-attribution-2026-08-04.md`,
  `results/calibration/PREREG-nyiso127-addendum-eastern-seam-availability-source-2026-08-05.md`.
