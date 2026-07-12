## 11. LANE EXECUTED (2026-07-12 — miso-57 rdt-congestion): §10 pointer 1 built —
bypass severed + published derate/TCDC; transmission lane now structurally
faithful; 2025 separation re-attributed to lane 2 (mid-merit split)

Registered `2026-07-12-miso-57-rdt-congestion` + twin (NOT-YET; FAIL set
{fuelmix, sysvol, price_mean, price_tail} — co2 leaves the set on today's
basis for both 56 and 57). Two changes on the miso-56 replay:
`miso_south_seam_split` (severs the free 3 GW South→external→Midwest wheel the
2025 diagnostic measured at 1,255 MW summer mean — the reason the RDT link sat
at 54 MW) and `miso_rdt_tcdc` (92% default derate + $40/$500 TCDC priced
tiers; constants.MISO_RDT_*, zero fitted scalars).

Verification against measured: RDT S→N mean 1,139/1,035 MW 2023/24 (measured
917/1,108), binding ≈25% of hours at the derated 2,300 MW (IMM 2024: >25% of
RT intervals), first model DA >$200 hours (Aug-26-2024 HE15/17/18, South
decoupled below). Score flat-to-marginally-better everywhere vs same-basis
miso-56; C3a-2025 −13.3% flat. The 2025 model RDT direction is INVERTED vs
measured (N→S-dominant vs S→N-dominant; Jun-Aug separation +$0.02 vs $9.31):
with the transmission structure now correct, the July-2025 gap is pinned on
the COAL_BIT/CC mid-merit split + import under-run (§10 pointer 2), which the
severed bypass now exposes at full size. RPE ($200 published demand value) is
the lane's one remaining admissible increment — deliberately not built here.
Data adjudication: no public hourly operative-RDT-limit series exists
(endpoint deprecated, no archive); the pbc binding-record reports
(da_pbc/rt_pbc daily CSVs 2023–2025) are the measured validation series for
this lane. Recommendation: miso-57 supersedes miso-56 on structural grounding
at flat-to-better score (miso-55→56 pattern); owner decision pending;
keepers.json untouched. Full record: calibration-log 2026-07-12 entry.
