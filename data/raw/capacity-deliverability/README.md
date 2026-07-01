# capacity-deliverability (raw)

Locational capacity requirements and import/export transfer limits per capacity
area, per delivery period, for every ISO with a capacity-deliverability
construct. PJM's **CETO** (Capacity Emergency Transfer *Objective* — the
locational requirement) and **CETL** (Capacity Emergency Transfer *Limit* — the
import transfer limit) are the reference pair; the other ISOs' native quantities
map onto the same canonical metrics (see the schema header and
`docs/adding-new-data-types.md`).

## Layout

One subdirectory per ISO; each holds a single **unified CSV** named `<iso>.csv`
with exactly the canonical columns:

```
iso,delivery_year,season,area,area_type,metric,value_mw,value_pu,source_doc,source_page
```

The retrieval prompts (see the session prompt pack) produce these CSVs directly.
`scripts/curate_capacity_deliverability.py` reads each subdir and writes the
clean partition `data/clean/capacity-deliverability/<ISO>/…parquet`.

- `metric` ∈ {requirement, local_clearing_requirement, import_limit,
  export_limit, import_ability, system_requirement} (`requirement` = CETO
  analog, `import_limit` = CETL analog).
- `season` ∈ {annual, summer, fall, winter, spring} — only MISO uses seasons.
- `delivery_year` is a label: "2025/2026" for planning-year ISOs, "2025" for
  CAISO (calendar study year).
- Leave a value cell blank rather than guess an unpublished number; blank-valued
  rows are dropped at intake.

## Per-ISO status & sources

| ISO | subdir | area unit | requirement (CETO) | import limit (CETL) | status |
|-----|--------|-----------|--------------------|--------------------|--------|
| PJM | `pjm/` | LDA | CETO | CETL | reference impl (parser registered) |
| MISO | `miso/` | LRZ 1–10 × season | LRR (+ LCR, ZIA) | CIL (+ CEL) | DATA NEEDED |
| NYISO | `nyiso/` | locality (J/K/G-J) | ICAP req + LCR% | Bulk Power Transmission Limit | DATA NEEDED |
| ISO-NE | `isone/` | capacity zone | LSR (+ MCL) | interface import limit | DATA NEEDED |
| CAISO | `caiso/` | local area / branch group | LCR "Capacity Needed" | Maximum Import Capability | DATA NEEDED |
| ERCOT | — | — | — | — | **excluded** (energy-only, no LDAs/analog) |

Authoritative source URLs for each ISO are listed in that ISO's `README.md`.
