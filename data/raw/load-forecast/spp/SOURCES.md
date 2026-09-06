# `load-forecast/spp` — SOURCES

Opened **2026-09-06** by lane **SPP-12** (plan §6 manifest row 13, flagged there as
a **W2 precondition**). Fetched from `www.spp.org`, which is fully reachable.

## What landed, and what did not

`spp.csv` carries **four `annual_peak_mw` rows** (2026, 2029, 2034, 2044) from the
**2025 ITP Assessment Report v1.0**. That satisfies the manifest row's stated bar
— *"a real edition + vintage ≥ 2020"* — with edition `2025 ITP`, vintage `2025`.

It does **not** carry `energy_gwh`, and it is **not** a dedicated long-term load
forecast publication of the kind MISO's `2026-LTLF-Results-Summary.pdf` is. SPP
does not appear to publish a standalone LTLF document on `spp.org`; its
forward load view is embedded in the ITP assessment cycle. Consequences to state
plainly:

- Only **four study years** exist, not an annual series. `scripts/lib/load_forecast/spp.py`
  (SPP-20's file, not this lane's) will have to interpolate between them, and that
  interpolation is a modelling choice that should be declared where it is made.
- There is **no energy forecast**, so any SPP load-growth constant derived from
  this file is a peak-growth constant. Implied CAGR on the peak series is ~1.2 %/yr
  (2026→2044); this is a **derivation from the four rows**, not a published figure,
  and it is deliberately not written into `spp.csv`.
- The four rows are **Base Reliability** model peaks. The same report carries
  separate **resiliency** peaks (Figures 2.48/2.49, printed pp. 82–83) that run
  higher — summer +5.09 %, winter +3.7 % over the previous five-year ITP average,
  by SPP's own statement on p. 82. Those are a different published case and are not
  mixed into these rows.

## Source

- **2025 ITP Assessment Report v1.0** —
  <https://www.spp.org/Documents/75483/2025%20ITP%20Report%20v1.0.pdf>
  (14.3 MB, sha256 `e9b494a820a2691d2dee41d3d04b4c65148dee25d4215c4afc2c9c40d3446616`)
- Found via: SPP.org > Engineering > Transmission Planning.
- **The PDF payload is not tracked here** — at 14.3 MB it is seven times the
  largest source file in this datatype (MISO's 2.0 MB). It follows the repo's
  corpus convention instead: full text transcription at
  `data/raw/spp-planning/transcriptions/2025_ITP_Report_v1.0.txt`, checksum in
  `data/raw/spp-planning/SHA256SUMS.txt`, and **re-fetch from the URL above** as
  the recovery route. This departs from the six sibling directories, which do
  track their source PDF; the reason is size, and it is recorded here rather than
  left for a reader to infer.

## The chart-read caveat — read this before trusting the values

Figure 2.1 is a **bar chart with data labels**, not a table. `pdfminer` recovers
the labels and the axis categories but **not their pairing**: the raw extracted
token order is

```
SPP Peak Load by Model Year
76.4   66.5   69.8   61.7        <- data labels, chart-render order
...(y-axis 80.0 ... 50.0)...
2026   2029   2034   2044        <- category axis, left to right
```

The values were paired to years by the only assignment consistent with a load
**growth** forecast — ascending years to ascending values:

| Study year | Coincident peak |
|---|---|
| 2026 | 61.7 GW |
| 2029 | 66.5 GW |
| 2034 | 69.8 GW |
| 2044 | 76.4 GW |

Two independent checks support it and are worth recording, because the pairing is
the one inference in this file:

1. The report's own §3 narrative (printed pp. 88–92) is about **load growth** —
   *"seven of 11 SPP states … show[ing]"* growth, and *"forecasts in 2026 ITP are
   of much larger magnitude"*. A non-monotonic peak series would contradict it.
2. The 2025 resiliency figures on printed p. 82 bracket the same range
   (summer base/resiliency coincident peaks 65,698–82,996 MW across Y5/Y10 and
   two futures), consistent with a 2026 base near 61.7 GW rising through 76.4 GW
   by 2044.

This is the same class of read MISO's rows already carry (`"chart vector read"` in
`miso.csv`'s `source_page`), so the datatype has precedent for it — but it is a
**read**, and a session that gains access to the ITP's underlying model data
should replace these four rows with tabulated values rather than re-deriving the
same chart.

## Follow-ups for whoever needs more than four peak years

In descending order of likely payoff, all on the reachable `www.spp.org`:

| Candidate | Where |
|---|---|
| ITP Manual v3.3 — defines how the ITP load forecast is built | `/Documents/77209/ITP Manual Version 3.3.pdf` |
| 2022 20-Year Assessment Report — longer horizon, may tabulate load | `/Documents/69814/2022 20-Year Assessment Report v1.0.pdf` |
| 20-Year Assessment Manual | `/Documents/59716/20_Year_Assessment_Manual.pdf` |
| ITP Postings folder (models, data requests) | `/spp-documents-filings/?id=31491` |
| Annual Engineering Data Request Schedule | `/spp-documents-filings/?id=462845` |

The 2023 and 2024 ITP Assessment Reports also exist
(`/Documents/70584/`, `/Documents/73086/`) and would give earlier **vintages** of
the same peak series — useful if a hindcast ever needs the forecast as it stood at
an information cutoff, which is exactly the vintage-gating rule 13 `[R-MEASURED]`
asks of a forward-regenerable input.
