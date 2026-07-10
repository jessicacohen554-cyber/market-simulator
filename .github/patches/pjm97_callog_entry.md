
## 2026-07-10 — PJM — KEEPER SWAP pjm-94 -> pjm-97 (owner decision, rule 1) — G-20 Phase-2 measured internal interface limits + data-intake

**Owner decision (2026-07-10).** pjm-97 (`2026-07-10-pjm-97-measured-interfaces`)
is the new PJM keeper, superseding pjm-94: the measured seam ladder + measured
hourly internal interface limits replace the residual-seeded static estimates the
pjm-94 lineage carried, and per rule 1 the build proceeds from the most
structurally faithful base — explicitly NOT from the best-fitting one. The fit
record is mixed and recorded honestly below and in the keeper sidecar.

**What this session built (channel (b) of the pjm-94 eastern-slack diagnosis).**
- **New clean datatype `transfer-interface-limits`** (schema-first, per-ISO
  registry `scripts/lib/transfer_interface_limits/`, PJM first): the three PJM
  Data Miner 2 `transfer_limits_and_flows` CSVs (2023-2025, ten series incl.
  pre/post-contingency kept separate) curated onto the fixed non-leap 8760 model
  clock — UTC→EPT, Feb 29 dropped, DST fall-back merged, the one spring-forward
  hour filled and flagged (`n_source_rows=0`). Dense; the measured `transfers`
  column is diagnostic-only. tmp-CLEAN_DIR tests; `regenerate_clean` registered.
- **Crosswalk** (`constants.PJM_INTERFACE_LINK_MAP`, rule-14 misalignments
  documented): 50045005 → ComEd→AEP; AEP/DOM → AEP→Dominion; AP-South →
  West_APS→SWMAAC ONLY (parallel-path split — West_APS→Dominion keeps its
  static so the flowgate is never double-applied); Bedington-BlackOak →
  West_APS→Central_PA; the Average West/Central/East envelopes → the links they
  seeded. Cleveland deliberately ABSENT (sub-pocket boundary, the N_TO_H
  pattern). Measured-flow direction sanity: ≥98.5% one-directional west→east on
  the named flowgates.
- **Gated overlay `ScenarioConfig.pjm_measured_interface_limits`** (default OFF,
  `--pjm-measured-interface-limits`, meta round-trip): hourly measured forward
  caps (min of pre/post; non-positive limits clamp to 0), static rating on the
  reverse direction — the ercot_gtc_limits_measured `ttc`/`ttc_import` seam
  reused. Supersedes `PJM_MEASURED_INTERNAL_TTC` medians on mapped links (rule
  19). Forecast keeps the static seeds (two-track). DOF ledger: mapped links
  flip static-estimate → measured-physical under the flag.

**Keeper `pjm-97` / `2026-07-10-pjm-97-measured-interfaces`** (bundle
`results/calibration/pjm97_measured_interfaces`): pjm-94 recipe + seam ladder +
interface overlay + `pjm_reserve_pergen` + `measured_ramp_capability` (pjm-81
owner recommendation). Full span 2023-2025, sequential years (rules 12/16).
Zero-forcing ablation twin solved and registered
(`2026-07-10-pjm-97-measured-interfaces-ablation`, rule 21); governance
attestation + DOF ledger in `calibration_attestation.json`. The mechanism flip
carries zero fitted scalars, so the rule-22 LOO clause for tuned changes is
vacuous (noted in the attestation).

**Honest fit record (vs pjm-94).** C1 15/16 (free 11/12) vs 14/16 (free 10/12);
C2 PASS→CAVEAT (+3.0% 2025 gas); C3a -14.9→-15.6% (2025 FAIL); C3b 1-of-3→3-of-3
FAIL (0.232/0.219/0.249 — the regression enters with the seam ladder; the
interface limits are neutral on top); C3c unchanged (0/6, 0/18, 0/59 h). The
measured caps BIND (AEP→Dominion ~94% of hours at its hourly limit); the ComEd
corridor over-run is cut (CT 2024 +73→+35%, 2025 +111→+85%) while the eastern
under-run persists and CT per-plant capture falls (2023 median r 0.301→0.246).
pjm-96 (seam ladder alone, solved by the parallel session) is registered as a
rejected probe alongside.

**Open root cause handed to G-20 (the build-from-here agenda).** With both
transmission channels measured end-to-end, Dominion is a through-corridor
(imports at cap, re-exports at cap into SWMAAC 5,193-6,703 h/yr), no cut binds
around the MAD zones, and 2025 net export overshoots (27.1 vs 18.0 TWh): the
eastern CC/CT fleet is priced/committed out by seam-plus-west supply. The
residual work is the Phase-1 commitment posture of eastern CC/CT (pjm-81
attribution) and the Dominion seam-inflow structure — offer/commitment, not
transmission.

**Bookkeeping.** `keepers.json` PJM → `2026-07-10-pjm-97-measured-interfaces`;
`status.js` rebuilt; pjm-83 and pjm-86 pruned (top-15, twins exempt); pjm-94
remains registered as the prior keeper (the meaningful comparison, per
retention). Registered server-side (`register-pjm97.yml` promotion edition —
run payloads exceed the session push path; the runner re-solves
deterministically, registers, and commits).
