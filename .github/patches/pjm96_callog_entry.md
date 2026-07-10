
## 2026-07-10 — PJM keeper DEMOTED: pjm-95 → pjm-94 (rule-24 own-fleet validation REFUTES the temp-derate slopes on PJM CAMPD); measured PJM seam ladder derived + wired (`pjm_seam_measured_ladder`, C-6 closure for PJM's priced seam)

**Demotion (the pre-agreed exit).** The pjm-95 promotion carried an
`open_validation` debt: port the ERCOT temp-derate closure test to PJM's own
fleet, and "if PJM's fleet refutes the slopes the same way, this mechanism
exits the keeper the same way ERCOT's did." It does.
`scripts/probes/_pjm_temp_capability_envelope.py` (PJM CAMPD unit gross load
× zone TMAX, class/zone map from the model's own PJM fleet build,
dominant-group ≥90% purity guard; 2023+2024+2025):

- **Envelope**: p98 output/reference is FLAT — 0.98–1.11× in every TMAX bin
  up to 36–40 °C for CC_REGULAR (160 units), CT_PEAKER (240–246), ST_GAS
  (22), CC_CHP (16–17), all three years, where the raw literature curves
  predict 0.84–0.95.
- **Lower bound** (production ≤ capability, no at-max assumption):
  CC_REGULAR median max-output/net-summer = 1.00 at TMAX ≥34 °C with 78–89%
  of capacity proven ≥0.95× — the fleet demonstrates its rating on the exact
  hours the derate cuts it.
- **Max-incentive scarcity-hour slopes** (RT>$200: 5,147 plant-hours;
  RT>$100 companion: 25,093): CC_REGULAR −0.10/−0.15 %/°C vs model −0.76;
  CT_PEAKER +0.16/+0.27 vs −1.26; CC_CHP +0.58 vs −0.76. Only ST_GAS reads
  near-model (−0.67 vs −0.54 at $100) — a <2%-of-load class whose envelope
  is nonetheless flat.

The pjm-95 C3b-2025 PASS and C3c 0h→19h tail gain were therefore bought by
deleting capability the fleet measurably has (rule 1: right number, unreal
mechanism). Keeper reverts to `2026-07-09-pjm-94-stgas-netload` (twin
`2026-07-09-pjm-94-stgas-drag`); the pjm-95/pjm-94 sidecars, the pjm-95
attestation (`open_validation` RESOLVED), keepers.json (both maps) and
status.js all record it. Honest re-opened state: C3b-2025 NRMSE 0.217 FAIL,
C3c-2025 0h/51h — the G-20 Phase-2 scarcity-structure gap, not a derate.
ERCOT precedent note: PJM was the second fleet to refute the same
literature slopes; the mechanism now has no keeper user (MISO's
`miso-49-tempderate` keeper predates both refutations — flagged for its own
rule-24 own-fleet check as follow-up).

**Measured PJM seam ladder (C1 root-cause lead, audit C-6 closure for the
priced seam).** The pjm-95 C1 CC_REGULAR miss (2023 −14.1 / 2024 +10.25 TWh)
traces to the seam: the model imports in 46% of 2023 hours where the
measured record imports in ~2% (diurnal corr −0.50) — phantom imports
displacing CC dispatch. Root cause is structural: the measured PJM
interchange is direction-structural (exports to MISO/NYISO in ~97–100% of
ALL hours, imports from Carolinas/TVA/LGEE in 77–97% — firm PTP schedules
revealed only statistically), which the hurdle-gated spot-spread reference
seam inverts. Fix is the MISO/NEISO measured-ladder pattern applied to PJM:
`scripts/derive_pjm_seam_ladders.py` Q-Q duration-couples PJM's
settlement-grade tie-line flows (`PJM_{year}_import_export_act_sch_
interchange.csv`, pooled onto the five priced seams by the new
`interchange_config.PJM_SEAM_TIE`) with the measured PJM DA system LMP →
`PJM_SEAM_LADDER_BY_YEAR` (2023/2024/2025 + pooled forward story), applied
under the new `ScenarioConfig.pjm_seam_measured_ladder`
(`--pjm-seam-measured-ladder`) by `transmission.inject_pjm_seam_ladder_
prices`; it DISPLACES the firm scheduled-export floor on ladder years
(rule 19). Offline P9: every seam's simulated volume within ±0.06 TWh of
measured, import-hour shares 0–2% vs measured 0–2% (MISO/NYISO seams),
duration RMSE 40–275 MW. Boundary note (rule 14): PJM's EIA-930 submission
disagrees with both the tie-line meter and the counterparty meters on the
MISO seam (2023: 56.6 vs 35.3 vs MISO's own 33.5 TWh) — the tie-line file
(the model's canonical boundary, behind `pjm_net_interchange` and the seam
envelopes) is the flow source; the fetched `PJM interchange hourly.parquet`
(new raw intake, `fetch_eia930_interchange.py --ba PJM`) is the printed
cross-check. DOF ledger: PJM seam bands flip residual → measured-physical
under the flag (`build_dof_ledger.py`). Tests: `tests/test_pjm_seam_ladder
.py` (registry shape/ordering/no-wash, injection, firm-floor displacement).

**Next.** pjm-96 = pjm-94 recipe + `pjm_seam_measured_ladder` (temp derate
OUT per the demotion), full 2023–2025 one bundle, targeting C1.

**Holdouts.** No solve, score, or intake outside 2023–2025 (rule 22): the
probe reads 2023–2025 CAMPD/weather only; the seam intake covers 2023–2025.
No offer-curve or sigmoid touched (rules 13/21/23); the ladder is
measured-behaviour with a frozen formula (rule 23), zero fitted parameters.
