# `gas-ofo-events` — gas pipeline Operational Flow Order declarations

Immutable source snapshots of declaring gas utilities' public **Operational
Flow Order (OFO)** event ledgers. An OFO is a utility's tariff instrument for
forcing shippers' daily deliveries into balance with their burn when the
pipeline/storage system cannot absorb the imbalance: a **physical gas-system
availability event**, declared per gas day, with a published escalation stage
and imbalance tolerance band.

- **LOW OFO** — under-delivery penalized, tolerance printed **negative**. This
  is the winter gas-*deliverability* instrument: the one that binds when a cold
  snap strands gas-fired generation.
- **HIGH OFO** — over-delivery penalized, tolerance printed **positive**. The
  converse linepack-surplus instrument.
- **EFO** — an *Emergency* Flow Order, a distinct Rule 23 instrument the
  utility prints in the same ledger. Carried as `stage = "EFO"` and
  deliberately left unranked.

Curated to the tidy `gas-ofo-events` clean datatype
(`data/dictionary/schema/gas-ofo-events.schema.yaml`), one row per
`(iso, utility, gas_day, side)`.

## Layout

```
gas-ofo-events/
  README.md                          <- this file
  caiso/
    socalgas_low_ofo_events.html     <- verbatim ENVOY response, low ledger
    socalgas_high_ofo_events.html    <- verbatim ENVOY response, high ledger
    _snapshot.json                   <- per-file url / retrieved_utc / bytes / sha256
```

Files here are **never modified in place**. Re-retrieval overwrites a whole
snapshot and rewrites `_snapshot.json`; the SHA-256 in that manifest is the
identity record, and it rides into the clean file's parquet footer.

## Sources

### CAISO — Southern California Gas Company (SoCalGas)

SoCalGas ENVOY public site, **no authentication**
(`https://www.socalgas-envoy.com`):

| ledger | endpoint | published span |
|---|---|---|
| Low OFO / EFO | `/Public/ViewExternalLowOFO.getLowOFOEvent` | 2015 – present |
| High OFO | `/Public/ViewExternalOFO.getOFOEvent` | 1997 – present |

Both pages return the **entire** history in one response as a single HTML table
whose `<th>` header cells are years (newest first) and whose body cells hold
one event each as free text (`"January 3, Stage 3.1, -5%"`). A cell's *column
position* supplies the year, so a row is only reconstructable from
(header year, cell text) together. There is no date-range paging and no
retention cliff observed.

Retrieved by `scripts/data/fetch_socalgas_ofo_events.py`; parsed by
`scripts/lib/gas_ofo_events/caiso.py` through the package's
`envoy_year_column_table` reader.

Two further SoCalGas routes exist and are **not** used, because the two ledgers
above already carry the full event record at the grain the schema declares:

- **Per-gas-day cycle detail** — `/Public/ViewExternalOFO.getOFO` and
  `/Public/ViewExternalLowOFO.getLowOFO` accept a historical `gasFlowDate`
  (mm/dd/yyyy) and export CSV/PDF with the intraday nomination-cycle
  calculation behind one day's order. Verified reachable for 2024-01-15
  (caiso-225 §A3). Intake it only if a mechanism needs *within-day* cycle
  detail; the event-day grain does not.
- **Critical Notices** — OFO declarations also post to the searchable public
  notice ledger under Tariff Rule 30. A redundant route to the same events.

## `DATA NEEDED`

- **PG&E OFO record (CAISO / NP15).** Pacific Gas & Electric declares its own
  OFOs for the northern half of the CAISO footprint, on a different portal with
  a different layout. **Not yet retrieved.** The `caiso-131` §5 ask names
  "SoCalGas / PG&E"; this intake (caiso-226) landed the SoCalGas half only.
  Adding PG&E is one more `OfoSource` in `scripts/lib/gas_ofo_events/caiso.py`
  plus a reader in `scripts/lib/gas_ofo_events.READERS` — no shared-code
  change. Note the asymmetry when consuming the CAISO partition today: it
  describes SP15 gas deliverability, not the whole ISO.
- **Other ISOs.** NEISO (Algonquin/Tennessee), NYISO (Transco/Iroquois) and PJM
  (TETCO/Transco) have OFO-analogue instruments on their interstate pipelines.
  None is retrieved. Each is a new `scripts/lib/gas_ofo_events/<iso>.py` plus a
  reader; the shared code needs no edit.

## Status: intake-only

**No mechanism consumes this datatype.** It was retrieved under caiso-226 as
the funded `caiso-131` A3 ask, so that a future gas-deliverability trigger can
be keyed to the *source event* rather than to a price threshold tuned against a
residual (rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]` / 24 `[R-DOF]`).

- Rule-13 adjudication and the forward-analogue story:
  `results/calibration/FINDING-caiso226-ofo-intake-2026-08-31.md` §4–§5.
- Pre-registered, falsifiable design for the future arm:
  `results/calibration/PRECOMMIT-caiso227-ofo-arm-2026-08-31.md`.
