# uranium-marketing — raw

Source root for the `uranium-marketing-price` clean datatype
(`data/dictionary/schema/uranium-marketing-price.schema.yaml`), curated by
`scripts/curate_uranium_marketing_price.py`, which reads
`eia_umar_uranium_price.csv` in this directory and writes schema-valid
Parquet to `data/clean/uranium-marketing-price/uranium-marketing-price.parquet`.

## Why this exists

D2 in the forecast-driver audit: `fuel.py:113-115` prices nuclear as a
non-fuel-burning unit at `$0/MMBtu`, alongside wind/solar/hydro. Nuclear
plants do burn fuel — it's just never had a real-data-cited cost. This lands
the EIA-published front-end-fuel-cycle price components a `$/MMBtu` nuclear
fuel cost would be built from.

## No machine-readable route — PDF-only source (verified)

Checked before transcribing: the EIA Open Data API v2 has no `uranium`
route (`/v2/` route list: coal, crude-oil-imports, electricity,
international, natural-gas, **nuclear-outages** (physical reactor outages,
not price/quantity market data), petroleum, seds, steo, densified-biomass,
total-energy, aeo, ieo, co2-emissions — no uranium marketing route). The
Uranium Marketing Annual Report's own page
(`eia.gov/uranium/marketing/`) links only PDFs (no `.xls`/`.csv` — confirmed
by listing every download link on the page). This is a genuinely PDF-only
EIA publication, unlike the AEO/coal-price data this session also intakes.

## Extraction method

Downloaded `https://www.eia.gov/uranium/marketing/pdf/2024%20UMAR.pdf`
(EIA's 2024 Uranium Marketing Annual Report, released September 2025) and
extracted text with `pdfminer.six` (the sandboxed environment has no
`poppler-utils`/`pdftoppm`, so the Read tool's normal PDF-page-image path was
unavailable; `pdfminer.six` gives pure-Python text extraction instead). Every
value below was cross-checked against the report's own narrative summary
text (e.g. "$52.71 per pound U3O8e" for 2024, "$43.80... for 2023" — matches
Table S1b exactly) before being transcribed — not OCR'd or guessed.

## Expected file

`eia_umar_uranium_price.csv` — one row per (metric, delivery_year), columns:

```
metric,delivery_year,value,unit,source_doc,source_page
```

- `metric`: `total_purchased_quantity` (Table S1a "Total purchased", million
  lb U3O8e) | `total_purchased_price` (Table S1b "Total purchased
  (weighted-average price)", $/lb U3O8e) | `enrichment_services_price`
  (Table S2 "Average price (US$ per SWU)").
- Prices are **nominal** (not inflation-adjusted) — the source report's own
  footnote: "Weighted-average prices are not adjusted for inflation." Do not
  mix directly with the real-2024$ `eia-aeo-fuel-prices` series without
  deflating.

## Authoritative source

EIA, *2024 Uranium Marketing Annual Report* (released September 2025):
<https://www.eia.gov/uranium/marketing/pdf/2024%20UMAR.pdf>

| Table | Content | Years |
|---|---|---|
| S1a | Uranium purchased (quantity, million lb U3O8e) | 2002-2024 |
| S1b | Uranium purchased (weighted-average price, $/lb U3O8e) | 2002-2024 |
| S2 | Enrichment services average price ($/SWU) | 2006-2024 (2002-2005 marked "not available" in the source — not transcribed as zero) |

## DATA (landed)

- [x] `eia_umar_uranium_price.csv` — 65 rows (23 years x 2 uranium metrics +
      19 years x 1 enrichment metric).

## What this doesn't cover

- **$/MMBtu conversion.** EIA does not publish nuclear fuel cost in $/MMBtu
  directly. Building it from this data needs: a conversion-services cost
  component (EIA's UMAR does not carry a time series for this — historically
  a smaller share of front-end cost than U3O8 + enrichment), a fabrication
  cost (not EIA-published as a time series either), and a burnup/thermal-
  efficiency assumption to translate $/kg-enriched-uranium into $/MMBtu of
  heat delivered. None of that is guessed here (CLAUDE.md: no value
  guessing) — landing the two dominant, real, EIA-published cost components
  (U3O8 price, enrichment price) is this session's job; the $/MMBtu
  build-up, cited to this data change, is P-1D's (CLAUDE.md rule 23).
- **Per-reactor or per-utility detail.** The report has much finer
  breakdowns (by supplier type, contract type, origin country); only the
  "Total purchased" aggregate columns are landed, since that's what a
  single national nuclear-fuel-cost series needs. Revisit if a future
  session wants foreign- vs. domestic-origin cost differentiation.

## Consumer

None yet (intake only this session). Future consumer: a `$/MMBtu` nuclear
fuel cost series in `constants.py`/`fuel.py`, replacing the `$0` placeholder
(P-1D, cited to this data per CLAUDE.md rule 23).
