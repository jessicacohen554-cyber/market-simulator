# CAISO capacity-market-loads-resources (Summer Loads and Resources Assessment)

CAISO's **published class-level resource-adequacy ledger** — the Summer Loads and
Resources Assessment Technical Appendix, whose Table 1.1 reports every fuel
type's Net Dependable Capacity (NDC) and Net Qualifying Capacity (NQC) split by
deliverability status.

This is a **third instrument**, distinct from the two already committed under
`../../`:

| instrument | grain | what it is |
|---|---|---|
| `../../nqc/caiso/` (NQC report) | per-resource, monthly | the adopted per-resource accreditation and the published per-technology monthly factors |
| `../../elcc/caiso/` (E3/Astrapé study) | marginal tranche | *incremental* ELCC conditioned on an IRP portfolio |
| **here** (SLRA Table 1.1) | **per class, whole-fleet** | the **realized class totals** CAISO's own RA ledger counts, with the deliverability split |

Table 1.1 is the only one of the three that publishes a **realized whole-class
ratio**, which is what a class whose accreditation CAISO does *not* publish a
technology factor for needs. Storage is exactly that class: the NQC report's
`2026 Tech Factors` tab has **no battery row**, because batteries are
*dispatchable* and are accredited at demonstrated capability. The appendix says
so in terms (§1.1.1): *"For dispatchable resources like battery and natural gas
plants, the NQC value is typically near its NDC or installed capacity."*

## Files

| file | what it is |
|---|---|
| `2026-summer-loads-and-resources-assessment-technical-appendix.pdf` | **Immutable source download.** CAISO, "2026 Summer Loads and Resources Assessment — Technical Appendix", May 2026. sha256 `609e77b53dcbb65901dc93c6adbe0be16ebe57f7bebf916476e1b909a5654be3`. |
| `caiso_slra_class_accreditation.csv` | **DERIVED, reviewable.** Table 1.1 digitized first-party by `scripts/data/derive_caiso_slra_class_accreditation.py`. Regenerate with that script; never hand-edit. |

Contract: raw-only, matching the sibling `../../nqc/caiso/` intake — an immutable
source plus a reviewable derived CSV that registry literals cite and tests
reconcile against. There is no `data/clean/` schema because nothing here is a
per-ISO time series the model reads at solve time; the numbers enter as cited
registry constants.

## What the table's own footnotes say (load-bearing provenance)

* Existing-resource data is sourced from the **March 2026 NQC list** and accounts
  for known 2026 retirements.
* **September NQC values** are used; **NDC is calculated as of April 1, 2026**
  from the CAISO Master File.
* The table **excludes** tie-generators, pseudo-tie and dynamic import resources
  outside the CAISO BAA (~9,200 MW), SRR gas units, participating loads and
  demand-response resources.

## Closure checks (run by the deriver, on every re-derivation)

* The NQC column's fuel rows sum **exactly** to the published Total, 59,069 MW.
* The NDC column's rows sum to 83,923 against a published Total of 83,922 — a
  **1 MW per-row rounding artifact in CAISO's own table**, not a parse defect.
  The deriver tolerates ±2 MW and logs any nonzero drift.

## Source

- CAISO Library → Summer Loads and Resources Assessment:
  https://www.caiso.com/library/summer-loads-and-resources-assessment
- Direct:
  https://www.caiso.com/documents/2026-summer-loads-and-resources-assessment-technical-appendix.pdf
- Methodology: CPUC adopted Qualifying Capacity Methodology, D.10-06-036 App. B
  (as amended); CPUC Resource Adequacy proceeding R.21-10-002 / R.23-10-011.

## Vintage

CY2026, matching the model's forecast base year and the same vintage the other
near-term CAISO adequacy anchors are read at (the committed CY2026 NQC report).

## Rule 23 [R-FROZEN-DERIVE]

Re-derive **only** when CAISO publishes a new assessment and that PDF is intaken
here. Never because a model residual moved. A re-derivation commit cites the data
change.
