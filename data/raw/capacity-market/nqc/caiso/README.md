# CAISO capacity-market-nqc (Net Qualifying Capacity report)

CAISO's / the CPUC's **adopted resource-adequacy accreditation** for the
compliance year: the per-resource monthly Net Qualifying Capacity (NQC) list
plus the published per-technology monthly **technology factors** those NQC
values are computed from.

This is a **different instrument** from the incremental-ELCC study already
committed under `../../elcc/caiso/caiso.csv`. That study (E3/Astrapé, filed in
the IRP/LTPP proceeding) publishes *marginal-tranche* ELCCs conditioned on an
IRP portfolio; this report publishes the *class-average* accreditation CAISO's
RA ledger actually counts. The registry comment on
`RENEWABLE_ELCC_CURVES_BY_ISO` records why the marginal study could not be used
as a whole-fleet ledger credit (rule 14's misalignment exception); this intake
is the class-average source that note said was pending.

## Files

| file | what it is |
|---|---|
| `net-qualifying-capacity-report-cy2026.xlsx` | **Immutable source download.** CAISO, "Net Qualifying Capacity Report for Compliance Year 2026". sha256 `f77bff4dd6961fd988d15dcf128437a59e48ea557649a4937036ce2d1724ac28`. Tabs: `2026 NQC List` (per-resource monthly NQC MW, dispatchability flag, Path 26 designation, deliverability status), `2026 Other`, `2026 Tech Factors` (the published monthly technology factors). |
| `caiso_nqc_class_factors.csv` | **DERIVED, reviewable.** Fleet-weighted monthly accreditation factor for the model's `solar` and `wind` classes, produced by `scripts/data/derive_caiso_nqc_class_factors.py` from the workbook above. Regenerate with that script; never hand-edit. |

## Source

- CAISO Library → Net Qualifying Capacity (NQC) and Effective Flexible Capacity:
  https://www.caiso.com/library/net-qualifying-capacity-nqc-and-effective-flexible-capacity-efc
- Direct: https://www.caiso.com/documents/net-qualifying-capacity-report-for-compliance-year-2026.xlsx
- Methodology: CPUC adopted Qualifying Capacity Methodology, D.10-06-036 App. B
  (as amended); CPUC Resource Adequacy proceeding R.21-10-002 / R.23-10-011.

## Vintage

CY2026 is the compliance year matching the model's forecast base year, and the
same vintage the other near-term CAISO adequacy anchors are read at. Adjacent
vintages retrieved and checked for stability while deriving (**not committed** —
the anchor vintage is the one the registry cites):

- CY2025 — `final-net-qualifying-capacity-report-for-compliance-year-2025.xlsx`,
  the vintage `HYDRO_ACCREDITATION_CREDIT_BY_ISO["CAISO"]` currently cites.
- CY2027 (draft final) —
  `draft-final-net-qualifying-capacity-report-for-compliance-year-2027.xlsx`.

Vintage sensitivity is recorded in
`docs/handoffs/ffr-3p-caiso-accreditation-2026-08-04.md` §3.3 — the August solar
factors move materially between CY2026 and the CY2027 draft, which is why the
registry states its vintage explicitly.

## Rule 23 [R-FROZEN-DERIVE]

Re-derive **only** when CAISO publishes a new compliance-year report and that
workbook is intaken here. Never because a model residual moved. A re-derivation
commit cites the data change.
