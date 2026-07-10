# NYISO per-interface hourly flows + limits (Ask D1, `nyiso-data-asks-2026-07.md`)

Hourly aggregation of the NYISO MIS public 5-minute "Interface Limits and
Flows" posting (P-32, `mis.nyiso.com/public/csv/ExternalLimitsFlows/`),
2018-01 through 2026-06 (H1-2026 cap), one CSV.GZ per year:

    NYISO_interface_flows_hourly_<year>.csv.gz

Built by `scripts/fetch_nyiso_interface_flows.py` (download + documented
5-min→hourly aggregation: mean flow, most-binding limits per hour; the raw
5-minute zips are ~95 MB/year and are not committed — the script's cache
regenerates them from the MIS archive). Interior source gaps (1–3 hours/year
system-wide) are filled from the adjacent actual observation and marked
`n_intervals = 0` (owner instruction 2026-07-10); hours before an interface
enters service (CHPE 2026) are never invented. Curated into the
`nyiso-interface-flows` clean datatype by
`scripts/curate_nyiso_interface_flows.py` (which also nulls the ±9,999 MW
"unbounded" sentinel limits).

Interfaces covered (18; 19 from 2026 when CHPE enters): internal transfer
interfaces CENTRAL EAST - VC, TOTAL EAST, UPNY CONED, MOSES SOUTH, DYSINGER
EAST, WEST CENTRAL, SPR/DUN-SOUTH; external schedules SCH - HQ - NY /
HQ_CEDARS / HQ_IMPORT_EXPORT / NE - NY / NPX_1385 / NPX_CSC / OH - NY /
PJ - NY / PJM_HTP / PJM_NEPTUNE / PJM_VFT.

Note the posting carries UPNY CONED (not a separate UPNY-SENY row); the
UPNY-SENY boundary of the D1 ask is spanned by TOTAL EAST / UPNY CONED plus
the SENY-side schedules — document any crosswalk at the consumer, not here.

Years 2018–2022 and 2026 are out-of-training intake under the session-logged
owner authorization of 2026-07-10 (CLAUDE.md rule 22; itemized in
`docs/out-of-sample-results-2026-07.md` §1.2). Admissibility: measured
physical flows and posted ratings are rule-13 inputs (they regenerate from
forward drivers); they are diagnosis/validation series for the interchange
wedge, never a dispatch answer to pin.
