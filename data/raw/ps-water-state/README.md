# ps-water-state — measured hourly pumped-storage plant operations

Hourly pumped-storage generation/pumping energy, powerhouse water flows, and
upper/lower reservoir elevation/storage, from the **operator's own published
plant records**. Schema (the contract):
`data/dictionary/schema/ps-water-state.schema.yaml`. Curated by
`scripts/data/curate_ps_water_state.py` through the `write_clean` seam; per-ISO
parsing registers in `scripts/lib/ps_water_state/<iso>.py`.

## Why this datatype exists

CAISO's hourly split of pumped-storage operation from conventional hydro is
**non-public at fleet coverage**: EIA-930 nets PS inside the CISO `WAT` cell
(the 2024-H2 schema adds explicit Pumped Storage columns but CISO files nulls
in them — re-verified live 2026-08-31), CAISO's Today's Outlook hydro is the
same PS-net feed, the Outlook storage feed is battery-only, EIA-923 is monthly,
and CDEC instruments only the DWR share (39.7 %). The wall record:
`FINDING-caiso141` §A/§B, re-verified `docs/handoffs/caiso-186-owner-sitting-2026-08-09.md`
§a.1 and again by caiso-227. The owner funded this intake in the caiso-227
charter (the caiso-201 Q2(a) object).

**The public breach**: the Helms Pumped Storage Project (FERC P-2735) filed its
measured hourly operations record as a PUBLIC appendix of its Final License
Application on FERC eLibrary.

## caiso/ — Helms (FERC P-2735)

| file | source |
|---|---|
| `helms_fla_appb1_hydrology.xlsx` | FERC eLibrary accession **20240418-5301** (PG&E Helms FLA, 2024-04-18), transmittal file `02_Helms FLA_P-2735_PUBLIC_Vol I_App B1 Hydrology.xlsx`, fileId `CFF7C81B-5BBF-CE68-8A75-8EF75D300000` |
| `_snapshot.json` | retrieval manifest: endpoint, request body, timestamp, byte count, SHA-256 |

Retrieval route (public, no authentication): `POST
https://elibrary.ferc.gov/eLibrarywebapi/api/File/DownloadP8File` with body
`{"fileidLst": ["<fileId>"], "Islegacy": false}` —
`scripts/data/fetch_helms_ps_water_state.py` re-runs it. The browser-facing
`filedownload` route serves the SPA shell, not the file; the fileId comes from
the eLibrary `Search/AdvancedSearch` API (search text "Helms Final License
Application", accession 20240418-5301).

Workbook layout (asserted at parse time; a change fails loudly):

* `Hourly PG&E Data` — **the parsed sheet**: HEC-DSS export, 8 series ×
  190,632 hourly rows, 2001-01-01 HE01 → 2022-09-30 HE24: Courtright
  (upper) elevation/storage, Wishon (lower) elevation/storage, Helms PH
  flow-generation/generation, flow-pumping/pumping. Units FT / AF / CFS / MWH;
  data types INST-VAL (reservoirs) and PER-AVER/PER-CUM (flows/energy).
* `Daily PG&E Data`, `Daily USGS Data` — daily aggregates and USGS gauge
  series (1978→2022); present in the snapshot, **not parsed** (the funded
  object is the hourly split; the daily sheets are derivable/auxiliary).

Clock: hour-ending, **fixed-offset local standard time** — the span is exactly
7,943 days × 24 h = 190,632 gap-free rows, so the record carries no DST
insertions/deletions. Later vintages stamp hours with sub-second HEC-DSS float
drift (`04:59:59.97` ≈ HE05); curation rounds to the nearest hour and asserts
gap-freeness. Missing-value sentinels `-901` ("missing") and `-902` ("no
record") become nulls; any other negative physical value fails curation.

**SPAN LIMITATION (stated honestly):** the record ends **2022-09-30** — the
relicensing study cut-off. It does NOT cover the 2023–2025 training years, so
it cannot directly overlay the backcast PS water state there; what it grounds
is the measured multi-year hourly *conduct* of the plant (rule-13-admissible
the same way multi-year CAMPD history grounds forecast emission rates). Any
derived parameter re-derives from this source only (rule 23) and is never
tuned to a residual (rules 13/24).

## DATA NEEDED

* **Helms 2022-10-01 → present** — PG&E holds it (the relicensing operations
  records end at the study cut-off); no public filing located that carries it.
  A future FERC compliance filing or a CEII/owner-level request are the known
  routes (the latter DECLINED by the owner, caiso-222 §9 route (ii)).
* **Eastwood (SCE, ~200 MW)** — no public hourly operations record located.
* **DWR facilities (San Luis/Gianelli, Hyatt-Thermalito; 39.7 % of the model
  fleet)** — CDEC hourly telemetry exists in AF/flow grain (stations SNL, ORO,
  TAB per `FINDING-caiso141` §C); needs its own `PsSource` + reader and an
  AF→MWh derivation with cited head/efficiency parameters.
* Other ISOs' PS fleets — none intaken; each is one
  `scripts/lib/ps_water_state/<iso>.py` module away.

## NOT YET CONSUMED

No model mechanism reads this datatype (intake-only as of caiso-227). Arming
anything on it is a separately chartered session with its own PRECOMMIT; the
caiso-186 §a.3 bound (its most favourable C3a reach: 62.1 % of 2024's required
move, 10.4 % of 2025's) travels with any such charter.
