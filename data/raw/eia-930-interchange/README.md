# eia-930-interchange — raw

`CISO interchange hourly.parquet`, `MISO interchange hourly.parquet`,
`ISNE interchange hourly.parquet`, `PJM interchange hourly.parquet` — the
EIA-930 BA-to-BA net interchange product (`TI` interchange family), long form
per directly-interconnected balancing authority (DIBA): columns
`diba, mw, local_time`. EIA sign convention: positive = the named BA exports
to the DIBA. `local_time` is the hour-ending timestamp on the BA's local
clock, spanning the covered local calendar years — 2023-2025 for MISO/ISNE;
**2019 - H1-2026 for PJM and CISO**, both extended 2026-07-31 under the
rule-22 intake authorizations logged in `calibration-complete.json`.

**The 2018 floor is the product's, not ours.** Two independent probes on
2026-07-31 found the EIA API v2 `interchange-data` route returns **no rows at
all for 2018** — `total: 0` for PJM month-by-month (2018-01/04/07/08/09/10/12,
first rows 2019-01) and for CISO on any 2018 window. That is a publication
floor for this product, so 2018 is absent rather than padded. Each file's
handful of stray local-2018 rows is just the local tail of the first UTC-2019
hours, exactly as the committed years carry theirs.

**PJM span.** 2026 is capped at hour-ending **2026-07-01 00:00**, the H1
authorization boundary, not the API's own horizon. Per-year DIBA-hour
coverage: 2019 99.7% · 2020 99.4% · 2021 **95.5%** · 2022 99.5% · 2023 99.4% ·
2024 99.4% · 2025 97.0% · H1-2026 95.1%. The 2021 dip is a hole in EIA's own
submission — CPLE is complete (8,759 h) while the other six DIBAs are each cut
to 8,303 h by the same ~457-hour gap — the same class of incompleteness the
committed 2025 block already carries, not a fetch artifact.

**CISO holdout back-fill.** Extended with the same committed producer under
`--merge`, which drops every fetched hour the file already carries and leaves
the committed rows untouched (verified: all 289,344 pre-existing rows survive
with their exact values and multiplicities). It now holds 721,892 rows —
8,759 distinct local hours × 11 DIBAs for 2019-2022, identical to the
in-sample years' grain, plus 4,317 h of H1-2026 through 2026-06-30.

**`SWPP interchange hourly.parquet`** (added 2026-09-06, lane SPP-11 —
`docs/handoffs/FINDING-spp-11-2026-09-06.md`; plan `docs/multi-iso/spp-addition-plan-2026-09.md`
§6 row 3). 268,177 rows, 2023-01-01 01:00 .. 2026-01-01 00:00 on
`America/Chicago`, fetched with the committed producer on its **keyless**
`--source bulk` route (this environment carries no `EIA_API_KEY`):

    python scripts/data/fetch_eia930_interchange.py --ba SWPP --source bulk \
        --years 2023 2024 2025

Eleven DIBAs: `AECI`, `EPE`, `ERCO`, `MISO`, `PNM`, `PSCO`, `SIKE`, `SPA`,
`SPC`, `WACM`, `WAUW`. Every DIBA except `SIKE` carries the full 8,759 /
8,784 / 8,760 hour grain (the three absent hours are the DST spring-forward
02:00 local, correctly so); `SIKE` first appears 2025-06-01. Per-hour value
coverage is EIA's: 97 (2023) / 361 (2024) / 936 (2025) hours are NaN for
*every* DIBA at once — a submission gap, not a fetch artifact. `PNM` is
identically 0 through 2025 after 2024.

**Three impossible prints, carried unmodified** (data/raw is immutable; any
repair is a consumer's decision, and none is applied here): `SPC` (SaskPower,
a ~150 MW DC tie) reads **+9,967 MW** at 2024-07-19 00:00 and **−57,499 MW**
at 2025-11-19 15:00; `WACM` reads **+32,974 MW** at 2025-06-21 05:00. The
`MISO` **−5,377 MW** print at 2024-01-14 08:00 is *not* in this class — it is
Winter Storm Heather, and the seam really did carry it.

Sum-of-legs vs the BA-level `Total interchange` column of
`../eia-930-hourly/SWPP hourly.parquet`: 4.59 / 2.01 / 1.89 TWh against
3.91 / 1.66 / 2.36 TWh for 2023 / 2024 / 2025 — the usual gap between the
per-seam legs and EIA's imbalance-adjusted BA total, plus the NaN hours.

**WIDENED to 2019-2025 on 2026-09-06 by lane SPP-15** (`docs/handoffs/
FINDING-spp-15-2026-09-06.md`; plan §8 SPP-15, r#4 am.1; §6 row 15), through
the producer's own `--merge` path, which keeps every already-committed
`(local_time, diba)` row and adds only hours the file did not carry:

    python scripts/data/fetch_eia930_interchange.py --ba SWPP --source bulk \
        --years 2019 2020 2021 2022 --merge

**Byte-identity of the committed window, proven either side of the merge:**
the 2023-01-01 01:00 .. 2026-01-01 00:00 slice is **268,177 rows** before and
after, and the sha256 of its canonical `(local_time, diba, mw)` serialization
is `243889469b96680815f64b8499d957ed4388630b36207dce8547ba26f7c75a3d` on both
sides. The file itself is rewritten (whole-file parquet: 268,177 -> 618,817
rows, sha256 `2d06a21c…` -> `807056bb…`), which is the merge doing its job;
no in-sample value moved. **Rule 22 `[R-HOLDOUT]`: data prep, not a spend** —
nothing solved, scored or registered, and SPP holds no tier marker.

The back years add **350,640 rows** = 10 DIBAs x 35,064 hours,
2019-01-01 01:00 .. 2023-01-01 00:00. `SIKE` is absent (it first appears
2025-06-01); the other ten run the full grain in all four years. Two things a
seam consumer must handle:

* **Value coverage is far worse in the early years.** Hours that are NaN for
  *every* DIBA at once: **2,040 (2019) / 2,256 (2020) / 503 (2021) / 313
  (2022)** — 23 % and 26 % of 2019 and 2020, against 97 / 361 / 936 in
  2023-2025. They are not scattered: 103 contiguous blocks, ~50 % of them
  Saturday and ~49 % Friday local (the largest are Thanksgiving 2019 and the
  Nov/Dec 2020 holiday weekends, 96 h each). This is EIA's own submission
  history for SWPP interchange, not a fetch artifact, and it is carried as
  absence. **Routed to SPP-33:** a seam calibration on 2019 or 2020 is fitting
  ~three quarters of the hours, with the missing quarter concentrated on
  weekends — a systematically non-random hole.
* **Two impossible `AECI` prints, carried unmodified** (the §4.3 class of the
  2023-2025 window): **−5,360,453 MW** at 2020-03-17 14:00 and
  **−5,380,676 MW** at 2020-03-17 15:00, on a tie whose rest-of-series lives
  in ±1,500 MW. They are five orders of magnitude out and they dominate every
  aggregate that includes them: SWPP's 2020 system net reads **−9.77 TWh**
  with them and **+0.97 TWh** without, and `AECI`'s own 2020 net **−10.37 TWh**
  vs **+0.37 TWh**. No repair is applied here (data/raw is immutable; the
  repair is a consumer's decision). The `MISO` **−5,340 MW** print at
  2021-02-15 09:00 is *not* in this class — it is Winter Storm Uri, and the
  seam really did carry it; do not filter it with the other two.

System net, excluding the two impossible prints: **+1.98 / +0.97 / +2.62 /
+6.16 TWh** for 2019 / 2020 / 2021 / 2022 — SWPP is a net exporter in every
back year, as it is in 2023-2025.

**`SOCO interchange hourly.parquet`** (added 2026-09-13, lane SOCO-11 —
`docs/handoffs/FINDING-soco-11-2026-09-13.md`; plan
`docs/multi-iso/soco-addition-plan-2026-09.md` §6 row 3). 236,736 rows,
2023-01-01 01:00 .. 2026-01-01 00:00 on **`America/Chicago`**, fetched with
the committed producer on its **keyless** `--source bulk` route (this
environment carries no `EIA_API_KEY`, as the charter container did not):

    python scripts/data/fetch_eia930_interchange.py --ba SOCO --source bulk \
        --years 2023 2024 2025

Nine DIBAs: `DUK`, `FPC`, `FPL`, `MISO`, `SC`, `SCEG`, `SEPA`, `TAL`, `TVA`.
**`AEC` (PowerSouth) is not among them** although its territory is embedded in
Southern's — EIA does not book it as a SOCO seam in this product.

**This is the cleanest interchange book in the corpus.** Every DIBA carries
the full grain in every year — 8,759 / 8,784 / 8,760 hours, the three absent
hours being the DST spring-forward 02:00 local, correctly so — and there are
**zero NaN hours**, against SWPP's 97 / 361 / 936 all-DIBA-NaN hours over the
same window. No impossible print was found: the extreme values are
`TVA` −3,150 MW and `FPL` +2,843 MW, both inside the plausible range for
those ties.

**Sum-of-legs against the BA-level `Total interchange` column of
`../eia-930-hourly/SOCO hourly.parquet`: 10.155 / 10.832 / 13.038 TWh vs
10.156 / 10.831 / 13.021** for 2023 / 2024 / 2025 — agreement to 0.001 /
0.001 / 0.017 TWh, far tighter than the usual gap between per-seam legs and
EIA's imbalance-adjusted BA total (SWPP's is 0.4-0.7 TWh). Hour by hour on the
local clock, 24,100 of 26,294 joined hours are **exactly** equal (r = 0.9986);
every ±1 h shift collapses that to ~50, which is what fixes the two files on
the same clock.

**Clock, measured not assumed.** The `local_time` stamps imply UTC-minus-local
offsets of 5 h on 17,133 rows and 6 h on 9,161 — CDT/CST, i.e.
`America/Chicago` — reproducing the committed `SOCO hourly.parquet` split
(17,133 / 9,171) to the DST-dedupe rows. Georgia Power's operating clock is
Eastern; the BA reports on Central. Hence the `"SOCO": "America/Chicago"` key
added to `fetch_eia930_hourly.BA_TIMEZONE` in the same commit.

**SOCO is a net EXPORTER in all three years — +10.155 / +10.832 / +13.038 TWh**
(EIA sign convention: positive = SOCO exports to the DIBA), confirming the
charter's measured 10.2 / 10.8 / 13.0. Per-counterparty net, TWh:

| DIBA | 2023 | 2024 | 2025 | direction |
|---|---:|---:|---:|---|
| `SCEG` | +7.119 | +8.845 | +9.779 | export, ~100 % of hours |
| `SC` | +4.055 | +4.588 | +4.834 | export, 96-100 % of hours |
| `MISO` | +4.388 | +4.494 | +4.725 | export, 91-95 % of hours |
| `FPL` | +2.903 | +2.770 | +2.911 | export, 77-85 % of hours |
| `TAL` | +0.706 | +0.672 | +0.556 | export, 89-95 % of hours |
| `FPC` | +0.082 | −0.024 | −0.419 | balanced, drifting to import |
| `SEPA` | −1.949 | −2.580 | −2.311 | import, 97-100 % of hours (federal hydro) |
| `TVA` | −3.456 | −4.075 | −2.878 | import on net, but two-way: ±2,500-3,150 MW |
| `DUK` | −3.692 | −3.859 | −4.159 | import, 88-94 % of hours |

`SEPA` and `DUK` are near-unidirectional and `SCEG`/`SC` almost perfectly so;
`TVA` is the only genuinely two-way seam (27 / 18 / 28 % of hours exporting).
Full per-DIBA per-year duration curves (min, p1, p5, p25, p50, p75, p95, p99,
max) are in the FINDING.

ISNE's DIBAs are its three external seams: `HQT` (Hydro-Québec TransÉnergie —
the Phase II + Highgate ties), `NBSO` (New Brunswick) and `NYIS` (New York).

PJM's DIBAs are `CPLE`, `CPLW`, `DUK`, `LGEE`, `MISO`, `NYIS`, `TVA`.
**Boundary caveat:** PJM's 930 submission disagrees materially with both
PJM's own settlement-grade tie-line file
(`data/raw/iso-specific-transmission/PJM_{year}_import_export_act_sch_interchange.csv`)
and the counterparty meters on the MISO seam (2023: 56.6 TWh exported per
this product vs 35.3 TWh in the tie file vs 33.5 TWh in MISO's own 930 book
— pseudo-tie / dynamic-schedule attribution differences between
submissions). The PJM seam-ladder derivation
(`scripts/derive_pjm_seam_ladders.py`) therefore uses the tie-line file as
its flow source and keeps this parquet as the printed cross-check.

**Source:** EIA-930 (Hourly Electric Grid Monitor), public domain — see
`docs/data-licensing.md` §1.

**Regeneration:** `scripts/fetch_eia930_interchange.py` (EIA API v2
`electricity/rto/interchange-data` route, same pagination/key pattern as
`scripts/fetch_eia930_long.py`):

    EIA_API_KEY=... python scripts/data/fetch_eia930_interchange.py --ba ISNE \
        --years 2023 2024 2025

The CISO/MISO files predate the script (manual pulls of the same product);
the ISNE file was fetched with it (2026-07-06), the PJM file likewise
(2026-07-10; extended to 2019 - H1-2026 on 2026-07-31, with the committed
2023-01-01 01:00 .. 2026-01-01 00:00 block asserted content-identical across
the merge). Raw data is immutable — the script refuses to overwrite an
existing file without `--force`.

**Consumers:**
- `scripts/derive_manitoba_firm_import.py` — filters MISO's file to the
  MHEB (Manitoba Hydro) DIBA for the firm-import floor.
- `scripts/derive_firm_import_floor.py` — same file.
- `scripts/derive_caiso_export_cap.py` — uses CISO's file as the realized
  ATC proxy for the export-cap derivation (a true OASIS export-ATC pull is
  an open follow-up, noted in that script).
- `scripts/derive_neiso_import_tranches.py` — uses ISNE's file (per-seam
  flow duration curves) to derive the measured NEISO import/export tranche
  ladders (`interchange_config.IMPORT_TRANCHES["NEISO"]` /
  `EXPORT_TRANCHES[_BY_YEAR]["NEISO"]`, audit C-6 closure).
- `scripts/derive_pjm_seam_ladders.py` — prints PJM's file as the boundary
  CROSS-CHECK only (the ladder derivation's flow source is PJM's tie-line
  file; see the boundary caveat above).

## The 17 NWPP balancing authorities (2026-09-13, NWPP-11)

`BPAT PACE PACW PGE PSEI AVA IPCO NWMT CHPD DOPD GCPD SCL TPWR AVRN GRID WAUW
NEVP`, 2023-2025, fetched through the unmodified
`scripts/data/fetch_eia930_interchange.py --source bulk` (the **key-free** Grid
Monitor route — `EIA_API_KEY` was unset in that container). Provenance, the
sign convention and the route's equivalence record: **`SOURCES-NWPP.md`** in
this directory. Analysis: `docs/handoffs/FINDING-nwpp-11-2026-09-13.md` §4.

2,278,882 rows over 30 distinct counterparties, 13 of them outside the
footprint: `CISO BCHA WACM SRP LDWP PNM BANC AZPS WALC WWA GWA SWPP AESO`.
