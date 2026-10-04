# PRECOMMIT — NWPP-NEXT-27: Path 76 served at its measured bilateral leg, 2019–2025

- **Phase 0:** `FINDING-nwppnext27-cc-conduct-path76-phase0-2026-10-03.md`.
- **Owner card:** 2026-10-03, "Path 76 served".
- **Control:** keeper `2026-10-03-nwpp-next-26-nevp`, read from its committed bundle `results/calibration/nwppnext26_span`
  (rule 29b: no control solve).
- **Arm:** the keeper recipe plus two keys, `nwpp_path76_served_schedule=true` and `nwpp_path76_alturas_link=false`.
  They replace one mechanism with one (rule 19). Both keys are set on the replay.
- **Free parameters added:** zero.
- **Shards:** seven, one per year (rules 16 and 36). No year is an exact control, because the leg is non-zero in every
  year.

## G-DRIFT (HEAD against the NEXT-26 pin `30c0e017`)

- `model/loss_demand.py` and `pipeline/solve.py`: they add `zonal_loss_demand_reconciliation`, which is gated, default
  off and not armed by NWPP. INERT, as NEXT-26 already recorded.
- `scripts/calibration_verdict.py`: scoring only (rubric v3.20, the C3c ordering). It does not touch the solve.
- `scripts/run_calibration_full.py`: threads the loss-demand flag. INERT when off.
- Probes: none on the solve path.
- Verdict: no LIVE hunk, so no control solve.

## Ex-ante predictions (fixed before any solve)

1. **P1 zonal demand.** It matches the FINDING §E table to ±0.10 TWh. OR, INLAND and EAST match the keeper, and so do
   the footprint totals.
2. **Path 76 is gone.** The leg log line reads `NWPP <Y> Path 76 served: NEVP -> BPAT <leg> TWh`. No
   `NWPP Path 76 (Alturas)` line appears, and no flows row exists between NWPP-NW and NWPP-SNV.
3. **SNV gas falls** toward NEVP EIA-930. The fall is −1.0 … −2.4 TWh in 2019, 2023, 2024 and 2025, and within
   ±0.6 TWh in 2020–2022.
4. **Footprint CC_REGULAR falls** by −0.3 … −2.0 TWh in 2019, 2023, 2024 and 2025. NW must replace about 2 TWh of import,
   partly from its own CC and hydro shaping and partly from fewer COI/BC exports. CC_REGULAR 2024 stays a FAIL. The
   arm alone does not close the +12.77 TWh gap, and it is not expected to.
5. **COI + BC exports fall** by 0 … 2 TWh in 2019, 2023 and 2024.
6. **Risks.**
   - SNV adequacy: unserved energy without the priced link was 15–119 GWh in NEXT-6 arm A. The served leg keeps the
     measured imports in their hours, so SNV unserved is expected under 50 GWh/yr.
   - The SNV price rises in peak hours.
   - NW CC rises.
   - C4 gas in SNV and NW.
   - D-1.
   Every regression will be reported at full magnitude.

## Decision rule

- **Promotion candidate** (owner standing ruling) when both hold:
  - each hard stop holds;
  - no gate flips PASS→FAIL without a new FAIL being closed.
- The promotion goes on ONE owner card in either case, with the full verdict diff against the keeper.
