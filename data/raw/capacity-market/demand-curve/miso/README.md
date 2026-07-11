# MISO capacity-market-demand-curve (seasonal PRA reliability-based demand curve)

Drop the retrieved unified CSV here as **`miso.csv`**. MISO's demand curve is
seasonal from Planning Year 2025-26 onward (summer/fall/winter/spring) — the
only ISO in this registry whose `season` column is populated. Note the season
for each row's curve in `source_page` if the CSV's own `season` column isn't
present.

- **metric:** `net_cone` (native alias `cone` — MISO calls it Cost of New
  Entry), `curve_point` (native alias `rbdc_point` — Reliability-Based Demand
  Curve).
- **delivery_year:** MISO Planning Year label, e.g. "2025-2026".
- **area:** Local Resource Zone (LRZ 1-10) if MISO publishes zonal curves,
  else blank for a MISO-wide row.
- **y_unit:** MISO publishes PRA prices in $/MW-day.

## Authoritative sources

- MISO Resource Adequacy hub: https://www.misoenergy.org/planning/resource-adequacy/
- MISO Planning Resource Auction results/parameters: search "MISO Planning
  Resource Auction results [planning year]" on misoenergy.org
- FERC eLibrary docket for MISO's reliability-based demand curve filing:
  https://elibrary.ferc.gov (search "MISO demand curve")

**STATUS:** `miso.csv` committed — gross CONE (Annual) by LRZ 1-10 + ERZs,
regional Net CONE (North/Central + South), seasonal CONE by System/subregion ×
4 seasons, the 8 labeled RBDC clearing-intersection points (subregion ×
season), and Planning Reserve Margin (%) by season for PY2023-24 through
PY2025-26 — all from the PY2025-26 PRA Results Posting + the RASC Net-CONE
update. MISO's reliability-based demand curve (RBDC) began PY2025-26; the full
continuous curve (beyond the one labeled clearing point per chart) is not
published as a data table, only as chart images — the labeled intersection is
the only exact point available. A more granular per-zone-per-season PRMR (MW)
breakdown exists in the source but was not transcribed at this pass (season-
level % IRM was kept instead). See
`docs/handoffs/capacity-market-intake-2026-07.md`.
