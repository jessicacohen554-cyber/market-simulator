# new-build-cost-benchmarks — cross-source new-build capital-cost benchmark set

Raw reference datatype backing the **new-build cost grounding / literature-envelope**
methodology (`docs/new-build-cost-methodology-2026-07.md`, capacity-cost-grounding
session 2026-07-19). One curated table (`benchmarks_2026.csv`) transcribing the
published overnight-capital-cost and fixed-O&M figures of the respected third-party
sources the model's `NEW_ENTRY_COSTS` / `TECH_COST_MULTIPLIERS` / `STORAGE_TECHS` /
emerging-tech cost constants are validated against, plus markdown conversions of the
source documents (`md/`) for QA/QC and grep-ability if source URLs rot.

**Consumed by** `scripts/data/derive_cost_benchmark_envelope.py`, which normalizes
every row to the model's constant-2026-USD basis (`constants.INFLATION_RATE`
convention, same deflator rule as `derive_entry_costs_from_atb.py`) and emits the
per-technology literature envelope + the `TECH_COST_MULTIPLIERS` low/high capex
ratios. `tests/test_cost_benchmark_envelope.py` asserts the committed constants
equal that derivation (CLAUDE.md rule 23).

## Sources (retrieved & QA'd 2026-07-19)

| id | document | edition | $-year | file QA'd | sha256 (source PDF) |
|---|---|---|---|---|---|
| sl2024 | Sargent & Lundy for EIA, *Capital Cost and Performance Characteristics for Utility-Scale Electric Power Generating Technologies* (basis of AEO2025) | Jan 2024 | 2023 | full 183-p conversion; committed extract `md/sargent-lundy-capital-cost-aeo2025-extract.md` | `ad9127130fece93d3c2d9e203fc0176fcfc5e4d4dccc61d6576107f2d2df96ec` |
| aeo2026 | EIA, *Assumptions to the Annual Energy Outlook 2026: Electricity Market Module* (Table 3 cost & performance; Table 4 regional overnight costs) | Apr 2026 | 2025 | full conversion committed `md/emm-assumptions-aeo2026.md` | `ae21fcea7110c6efac978fa9bf28670998392e72959077f7a07d5aa3045e00bb` |
| aeo2025lcoe | EIA, *Levelized Costs of New Generation Resources in the Annual Energy Outlook 2025* | Jul 2025 | 2024 | full conversion committed `md/aeo2025-lcoe-report.md` | `4a5651e1b1392541ffc648364d4afbbdef0e0049eed164b87b1bdacc3c51e68c` |
| lazard2025 | Lazard, *Levelized Cost of Energy+ (LCOE+)* v18.0 (incl. LCOS v10.0) | Jun 2025 | 2025 | full conversion committed `md/lazard-lcoeplus-june-2025.md` | `63a3376ad437bb2311be3384f568a8be6d3f4790c26771584b29e2e561376360` |
| brattle2025 | The Brattle Group + Sargent & Lundy, *Brattle 2025 CONE Report for PJM* (revised, MIC 2025-04-11) | Apr 2025 | nominal for 6/2028 online | full 112-p conversion; committed extract `md/brattle-pjm-cone-2025-extract.md` | `cf0e1805f81aa0691cef9fba8db7f7b0c082e090b21e3a77b3b34f4d02725588` |
| atb2024 | NREL ATB 2024 v3.0.0 (the model's pinned primary anchor; **final ATB edition** — no 2025/2026 ATB exists, verified against the renamed lab's site and OEDI 2026-07-19) | Jun 2024 | 2022 | committed extract `data/raw/nrel-atb/` (EGS classes added this session, part11+) | see `data/raw/nrel-atb/README.md` |
| doe-liftoff / pnnl | DOE Liftoff (next-gen geothermal; LDES) and PNNL 2022 storage assessment | 2023–2025 | various | **NOT re-fetched** — `liftoff.energy.gov` DNS-unreachable and `pnnl.gov` PDF endpoint bot-walled from this environment; rows carry `verified=0` and are excluded from the enforced envelope unless corroborated | n/a |

PDFs themselves are NOT committed (binary, several MB); they re-download via
`scripts/data/fetch_cost_benchmark_sources.py`, which pins the sha256 values above
and can regenerate the full markdown conversions (`--to-markdown`).

## `benchmarks_2026.csv` columns

- `source_id`, `source`, `edition` — provenance; `source_ref` the exact table/page.
- `dollar_year` — the dollar basis of the published number; the derive script
  normalizes with `(1 + INFLATION_RATE) ** (2026 − dollar_year)`. The Brattle rows
  are nominal-for-June-2028-online overnight costs → `dollar_year=2028` deflates
  them back to 2026$.
- `model_tech` — this model's technology key (`wind`, `solar`, `gas_cc`, `gas_ct`,
  `gas_cc_ccs`, `nuclear_large`, `nuclear_smr`, `hydrogen_ct`,
  `offshore_wind_fixed`, `geothermal_egs`, `geothermal_conventional`,
  `storage_li_ion_4hr`, …).
- `capex_per_kw_{low,mid,high}` / `fom_per_kw_yr_{low,mid,high}` — as published:
  point estimates fill `mid`; ranges fill `low`/`high`.
- `in_envelope` — 1 = participates in the enforced literature envelope for its
  `model_tech`; 0 = documentation-only (e.g. aeroderivative CTs vs the model's
  frame-CT concept, conventional hydrothermal geothermal vs EGS, 2-hr BESS).
- `verified` — 1 = number transcribed from a document downloaded and converted to
  markdown in the intake session (QA'd against the conversion); 0 = recorded from
  a source this environment could not re-fetch (kept out of the enforced envelope;
  flagged for browser re-verification).

## QA/QC performed at intake (2026-07-19)

1. Every PDF downloaded from its canonical URL, page-converted to markdown via
   pdfplumber, and the transcribed figures read back from the conversion (not from
   memory or secondary coverage). Conversions committed under `md/` (full text for
   EMM/Lazard/LCOE-report; key-table extracts for the 183-p S&L and 112-p Brattle,
   whose full conversions regenerate via the fetch script).
2. Cross-footing checks: AEO2026 Table 3 totals = base × technological-optimism
   factor (e.g. CC-CCS 2567×1.10=2824; SMR 8937×1.10=9831); S&L Table 1-2 BESS
   $1,744/kW = $436/kWh × 4 h (150 MW/600 MWh config confirmed in the Case 19
   chapter); Lazard 4-hr BESS $/kW computed from its published $/kWh DC+EPC and
   $/kW AC components (formula in the row note).
3. Dollar-year bases read from each document itself (S&L "2023 price levels";
   EMM "2025$/kW"; Lazard June-2025 current; Brattle "Nominal$ for 2028 Online").
4. The `verified=0` rows (DOE Liftoff EGS/LDES, PNNL storage) are recorded with
   their unreachable-primary caveat — same convention as the FF-1E §4.2
   45Y/48E manual-download flag.

Raw files are immutable (CLAUDE.md); corrections happen by superseding rows in a
new intake commit, never by silent edits.
