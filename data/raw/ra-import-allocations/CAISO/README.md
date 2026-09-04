# ra-import-allocations / CAISO — annual RA Import Capability Allocation results

Fetched 2026-09-04 from caiso.com (HTTP 200 through the session proxy; index
pages `https://www.caiso.com/library/{2023,2024,2025}-import-allocations`).
Session caiso-245 (`results/calibration/PRECOMMIT-caiso245-firm-import-allocation-split-2026-09-04.md`,
`FINDING-caiso245-firm-import-allocation-split-2026-09-04.md`).

CAISO's annual Import Capability Allocation process (tariff §40.4.6.2)
assigns each intertie branch group's published Maximum Import Capability
(MIC — already in `data/raw/capacity-deliverability/caiso/caiso.csv`) to
load-serving entities in numbered steps (Step 1–5 existing contracts / TORs /
pre-RA commitments / load-share allocation, Step 6 publication of
assigned/unassigned MW by branch group, Steps 8–13 bilateral transfers and
unassigned-capability rounds). Three document families per year:

| file | content | curated? |
|---|---|---|
| `<year>-holders-of-import-capability.xlsx` | LSE × BRANCHGROUP × ALLOCATION (MW) × START_DT/END_DT — the resulting HOLDINGS after every step and registered bilateral transfer (2023/2024 posted 2025-04-11; 2025 posted 2024-08-23) | **YES** → `ra-import-allocations` (`scripts/lib/ra_import_allocations/caiso.py`) |
| `<year>-import-capability-used-on-annual-resource-adequacy-plans.xlsx` | MONTH (May–Sep) × SCID/BG × USED_ALL_CAPABILITY (Yes/No) — whether the holder showed its full import capability on its annual RA plan | no — the single code column interleaves LSE IDs and branch-group codes with the flag on inconsistent rows (ambiguous grain). Read by the caiso-245 probe as a per-branch-group diagnostic only |
| `step6-<year>contractualdata.xlsx` / `step-6-2025-contractual-data.xlsx` | Step 6 contractual data: pre-RA import commitments, existing contracts and TORs with lock windows, by branch group and LSE | no — a subset of the holdings, kept for provenance |

Source URLs (`https://www.caiso.com/documents/<file>`):
- 2023: `2023-holders-of-import-capability.xlsx`, `2023-import-capability-used-on-annual-resource-adequacy-plans.xlsx`, `step6-2023contractualdata.xlsx`
- 2024: `2024-holders-of-import-capability.xlsx`, `2024-import-capability-used-on-annual-resource-adequacy-plans.xlsx`, `step6-2024contractualdata.xlsx`
- 2025: `2025-holders-of-import-capability.xlsx`, `2025-import-capability-used-on-annual-resource-adequacy-plans.xlsx`, `step-6-2025-contractual-data.xlsx`

Also published on the same pages and NOT committed (PDF, table cells
rasterized; the holdings workbook carries the same assignment at finer
grain): `step6-<year>assignedandunassignedraimportcapabilityonbranchgroups.pdf`
and the MIC PDFs (the latter already cited by the capacity-deliverability
corpus).

Branch-group codes carry the ISO's own suffix variants (`_ITC` / `_BG` /
`_ISL` / `_MSL`; 2023 uses `_BG` where 2024–25 use `_ITC` for the same
tie, and `PACI_MSL` (2023) is the Pacific AC Intertie the later files label
`MALIN500_ISL`). Consumers map the STEM, not the suffix.

Intake-only: no model mechanism reads this datatype. The pre-registered use
(re-key the firm import block's north/south split from the MIC capability
share to the held-allocation share) was stopped by its own rule — the held
north share (48.3 / 45.5 / 45.1 %) sits within 5 points of the MIC share
(46.2 / 46.2 / 46.4 %) in every year (`results/calibration/_caiso245_allocation_split.json`).

Rule 13: a published capability RIGHT on an annual cadence (regenerates each
July for the following RA year); never a fit target. Rule 14: an allocation
is neither a schedule nor an energy flow.

Immutable raw — never modified in place; `SHA256SUMS.txt` is the identity
record. DATA NEEDED: none for 2023–2025; add the 2026 workbooks when the
`2026-import-allocations` library page carries the holders file.
