# NYISO downstate LDC non-firm transportation delivery rates — sources

`nyiso_downstate_ldc_transport_monthly.csv` — the measured monthly LDC non-firm
transportation delivery charge ($/therm and $/MMBtu) a downstate NYISO
electric-generation gas peaker pays to move its own gas from the city gate to the
plant, over the Transco Zone 6 NY pipeline-hub commodity the model already
prices. This is the correct delivered-fuel boundary for these interruptible,
no-firm-capacity peakers (transportation customers), and supersedes the statewide
EIA-N3050NY3 firm-citygate stand-in (`nyiso_downstate_ct_gas_basis_monthly.csv`)
for the daily downstate re-grounding (gap register G-13; CLAUDE.md rules #11/#12/#13).

## Rate class (why SC-19 / SC-22, Tier 1)

National Grid's downstate gas tariff (PSC No. 1 KEDLI / PSC No. 12 KEDNY) serves
merchant electric-generation peakers as **non-firm transportation** customers:

- **KEDLI** (KeySpan Gas East, Long Island — zone K): **SC-19 Non-Firm Demand
  Response Transportation** (the successor to SC-7 Interruptible Transportation,
  Rate Code 469 "Non-Core Transportation Service for Electric Generators",
  renamed effective 2019 per Case 16-G-0058).
- **KEDNY** (Brooklyn Union Gas, NYC — zone J): **SC-22 C&G Non-Firm
  Transportation** (published on the same non-firm statement as SC-18–22).

Both publish the delivery rate **every month** in the *Statement of Non-Firm
Demand Response Sales and Transportation Rates* (`statnfdr` PDFs). We take the
**Tier 1** rate — customers with fully automatic dual-fuel switchover equipment,
which is what a grid-reliability merchant peaker runs (Tier 2 is semi-automatic /
manual, within ~$0.03/therm). The published **"Total Monthly SC-19/SC-22 Tier 1
Transportation Service"** figure already includes that month's delivery-rate
adjustment clauses (Earnings Adjustment Mechanism, Demand Capacity Surcharge, Net
Utility Plant Tracker, Rate Adjustment Clause, …), so it is the complete delivered
transport charge — no separate Transportation Adjustment Charge (TAC) statement is
required. The base volumetric rate steps at rate cases (KEDLI: 0.16080 →
0.22310 eff 2024-09 → 0.28530 eff 2025-04 $/therm; KEDNY steps similarly), which
is the forward-native driver that regenerates the series for a forecast year.

## Provenance

- Source: `https://www.nationalgridus.com` "Gas Rate Statements" archive.
  - KEDLI: `.../gas-rates/nyl/[<year>/]statnfdr-<n>-eff-<mm>-01-<yy>-for-kedli.pdf`
  - KEDNY: `.../gas-rates/nym/[<year>/]statnfdr-<n>-eff-<mm>-01-<yy>-for-kedny.pdf`
  - Statement numbers increment one per month; separator style, year
    subdirectory, and effective day (some months post `mm-02-yy`) vary, so the
    fetcher tries a compact template set per month and validates the effective
    date printed inside each PDF. The `source_statement` column records the exact
    PDF each row was parsed from.
- Rate class confirmed against the consolidated KEDLI PSC No. 1 effective tariff
  (schedule of service classifications, SC-7/SC-19 Rate Code 469; Case 17-G-0011
  order 2025-10-17) and the KEDLI GTOP manual (electric-generation = non-core
  transportation).
- Regenerate: `python scripts/fetch_nyiso_downstate_ldc_transport.py`
  (requires network + `pdfminer.six`/`pypdf`). The committed CSV is the durable
  artifact.

## Quarantine

2023–2025 only. 2022 and H1-2026 are holdout-quarantined (CLAUDE.md rule 22); the
fetcher never requests them.

## Level summary ($/MMBtu = $/therm × 10)

| LDC (zone) | 2023 | 2024 | 2025 |
|---|---|---|---|
| KEDLI (Long_Island) | ~1.70 | ~1.66–2.27 | ~2.27–2.89 |
| KEDNY (NYC)         | ~2.48–2.62 | ~2.49–2.97 | ~2.97–3.45 |
