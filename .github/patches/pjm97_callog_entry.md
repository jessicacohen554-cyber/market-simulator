
## 2026-07-10 — PJM — G-20 Phase-2 measured internal interface limits (pjm 97 measured-interfaces): PROBE, keeper stays pjm-94

**Goal (G-20 Phase-2 support; channel (b) of the pjm-94 eastern-slack diagnosis).**
The pjm-94 volErr zoneMon decomposition attributed the MAD-side phantom supply to two
channels: (a) the external seams (closed structurally by `pjm_seam_measured_ladder`,
tested as pjm-96 — hypothesis refuted, see its registry definition) and (b) the
internal interfaces, whose 11 static `ttc_mw` constants were Tier-3 estimates seeded
from 2024 means of measured data the repo already held. This session closed channel
(b) with measured data end-to-end (rules 13/14; the ERCOT gtc-limits precedent):

- **New clean datatype `transfer-interface-limits`** (schema-first, per-ISO registry
  `scripts/lib/transfer_interface_limits/`, PJM first): the three PJM Data Miner 2
  `transfer_limits_and_flows` CSVs (2023-2025, ten series incl. pre/post-contingency
  kept separate) curated onto the fixed non-leap 8760 model clock — UTC→EPT, Feb 29
  dropped, DST fall-back merged, the one spring-forward hour filled and flagged
  (`n_source_rows=0`). Dense; the measured `transfers` column is carried for
  crosswalk diagnostics only. tmp-CLEAN_DIR tests; `regenerate_clean` registered.
- **Crosswalk** (`constants.PJM_INTERFACE_LINK_MAP`, misalignments documented per the
  rule-14 exception clause): 50045005 → ComEd→AEP (the config's own comment names the
  link "the 5004/5005 interface"; measured mean ~2,900-3,100 vs the loose 6,000
  static), AEP/DOM → AEP→Dominion, AP-South → West_APS→SWMAAC ONLY (parallel-path
  split of the reduced mesh; West_APS→Dominion keeps its static so the flowgate is
  never double-applied), Bedington-BlackOak → West_APS→Central_PA, the Average
  West/Central/East envelopes → the links they seeded. Cleveland deliberately ABSENT
  (ATSI-Cleveland sub-pocket ≠ the PJM_ATSI zone boundary — the N_TO_H pattern).
  Direction sanity: AP-South/BB/AEP-DOM measured flows ≥98.5% one-directional
  west→east; binding (≥90% util) up to 6.5% of hours.
- **Gated overlay `ScenarioConfig.pjm_measured_interface_limits`** (tier-3, default
  OFF, `--pjm-measured-interface-limits`, meta.json round-trip): hourly measured
  forward caps (elementwise min of pre/post — both are simultaneously-enforced
  security limits; non-positive limits clamp to 0), static rating kept on the reverse
  direction and as the fallback fill — the ercot_gtc_limits_measured seam
  (`ttc`/`ttc_import`) reused unchanged. Supersedes `PJM_MEASURED_INTERNAL_TTC`'s
  pooled medians on mapped links (same feed, hourly — rule 19). Forecast years keep
  the static seeds (two-track; the statics ARE the forward story). DOF ledger: a
  measured-physical row under the flag (mapped links flip static-estimate →
  measured-physical). Docs/dictionary updated; iso_configs Tier-3 comment now points
  at the overlay.

**Probe `pjm-97` / dashboard `2026-07-10-pjm-97-measured-interfaces`** (bundle
`results/calibration/pjm97_measured_interfaces`): pjm-96 recipe + the overlay +
`pjm_reserve_pergen` + `measured_ramp_capability` (pjm-81 owner recommendation;
measured ramp intake thins the deliverable pool 48.2 → 37.8 GW). Full span
2023-2025, single invocation, sequential years (rules 12/16).

**Result (honest): the caps bind, the hypothesis does not survive.** AEP→Dominion
runs at its measured hourly limit ~94% of hours; West_APS→Dominion and ComEd→AEP
bind thousands of hours — and the eastern under-run still does not recover
(Dominion CC 2023 −78→−81%, Dominion CT 2025 −72→−80%, EMAAC CT −80→−83%, SWMAAC CC
2025 −88→−93%). The one clear win is the ComEd corridor over-run, cut by the
measured 50045005 cap (ComEd CT 2024 +73→+35%, 2025 +111→+85%). CT per-plant capture
FELL (2023 median r 0.301→0.246) and C3c is unchanged at 0 h >$200 (0/6, 0/18, 0/59;
the per-gen MAD reserve family never binds). C1 15/16 (free 11/12) vs pjm-94's 14/16
— the 2023 CC_REGULAR system cell clears, carried by the seam ladder as in pjm-96;
C3b stays at the pjm-96 3-of-3 FAIL level (0.232/0.219/0.249). NOT-YET (probe,
unattested).

**Attribution (rule 14).** With channel (b) physically capped, Dominion becomes a
through-corridor — importing at the measured caps from AEP/West_APS and re-exporting
at cap into SWMAAC 5,193-6,703 h/yr — and no cut binds around the MAD zones because
the Carolinas/TVA/LGEE seam supply (right-sized UPWARD by the measured ladder)
replaces what the west can no longer push; zonal LMPs barely separate and 2025 net
export overshoots (27.1 vs 18.0 TWh). Both structural transmission channels are now
measured and neither closes the eastern skew: the remaining root cause is the
**Phase-1 commitment posture of the eastern CC/CT fleet** (the pjm-81 attribution)
plus the seam-inflow structure at Dominion — an offer/commitment problem, not a
transmission-representation problem. Per rule 14 the measured limits STAY (default-off
overlay); the worse CT capture under truer physics is the discovered-bug signal, and
reverting to the static estimates would bury it.

**Bookkeeping.** pjm-96 (solved and scored by the parallel 2026-07-10 session;
hypothesis refuted, its registry definition carries the finding) and pjm-97 both
registered server-side (`register-pjm96-v2.yml` / `register-pjm97.yml` — the run
payloads exceed the session push path; the workflows re-solve deterministically on
the runner, register, and commit). Retention: pjm-83 and pjm-86 pruned (top-15).
Keeper remains `2026-07-09-pjm-94-stgas-netload`; no keeper flip, so no LOO scoring
was triggered (rule 22) and no attestation/ablation twin was drafted (rule 21 applies
at promotion).
