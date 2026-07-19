# NYISO demand response — SCR & EDRP enrollment

`nyiso_scr_edrp_enrollment.csv` — registered demand-response capability by NYISO
zone (A–K), capability period (summer / winter) and program, transcribed from
the **NYISO Gold Book (Load & Capacity Data Report)** projection-of-enrollment
table for each year:

| Gold Book year | Table | Page |
|----------------|-------|------|
| 2023 | I-17 | 67 |
| 2024 | I-18 | 71 |
| 2025 | I-17 | 69 |

Two programs, both dispatched by NYISO only during declared reliability events
(reserve pickup / EEA), which in practice fall on summer heat-driven peaks:

* **SCR — Special Case Resources.** ICAP demand-response resources obligated to
  curtail when activated. The large program (~1.23–1.49 GW NYCA summer),
  concentrated downstate (Zone J / NYC ≈ 420–480 MW).
* **EDRP — Emergency Demand Response Program.** Voluntary emergency curtailment.
  Small (≤ 13 MW NYCA), also J-heavy.

Schema (`enrolled_mw` is the projected registered MW for that Gold Book's own
capability year; source columns cite the exact table/page):

```
gold_book_year, nyiso_zone, program, season, enrolled_mw, source_doc, source_table, source_page
```

## Provenance / reproduction

The immutable source is the committed Gold Book PDF
(`data/raw/NYISO/{year}-Gold-Book-Public.pdf`), from whose cited enrollment
table (see the table/page map above) the per-zone values are transcribed.
`scripts/data/build_nyiso_scr_edrp.py` encodes that transcription and re-emits
this CSV deterministically (byte-identical), so the enrollment input is
reproducible and diff-reviewable. It is a measured published input (CLAUDE.md
rule 13/23 — it regenerates for a forward year from the next Gold Book and
responds to changed enrollment; re-derive ONLY when a new Gold Book is
published, never against a price residual). To add a year: read the new Gold
Book's SCR/EDRP projection table, add its rows to `_ENROLLMENT` and its citation
to `_SOURCES` in the build script, and re-run it.

Consumed by `src/market_sim/data/nyiso_demand_response.py`, which aggregates the
A–K rows onto the five NYISO model zones (Upstate_West = A–E, Capital_Hudson =
F–G, Lower_Hudson = H–I, NYC = J, Long_Island = K) and builds the DR pseudo-gen
supply blocks used when `ScenarioConfig.nyiso_scr_edrp` is on.
