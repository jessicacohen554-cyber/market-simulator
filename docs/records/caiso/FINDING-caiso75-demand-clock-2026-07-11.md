# FINDING — CAISO demand-basis adjudication: the 930 `Demand` basis is CORRECT (it IS the SLD actual); the real defect is a +1 h Demand-clock window covering Jan–Oct 2023; the "missing 1.5 GW afternoon load" is a supply-side balance artifact (2026-07-11)

**Rule-14 data adjudication** (no solve; the probe on the resulting fix is
caiso-75). Adjudicates the CAISO backcast demand basis between the three
published measurements that disagree by ~1.5 GW in the h14-17 CT-ramp window
(`FINDING-caiso72-step0-evening-displacement-2026-07-10.md` §3, open question
of the 2026-07-07 W3a log entry): EIA-930 `Demand` (the model input), the
OASIS SLD TAC-area actual, and the supply-implied load (930
`net_gen − interchange`). Reproduce every number:
`scripts/validate_caiso_demand_clock.py` (the window guard) and the analysis
blocks quoted below run off `data/raw/eia-930-hourly/CISO hourly.parquet` and
`data/raw/zone-specific-demand/CAISO/CAISO_tac_load_hourly_{2023,2024,2025}.csv`
alone.

## 1. The three-way disagreement is two separate artifacts, not one basis question

**(a) 930 `Demand` and the OASIS SLD TAC actual are the SAME measurement.**
Once per-file stamp conventions are removed, 2024 full-year corr is
**0.9994** (MAE ~180 MW on a 25.5 GW mean), residual a smooth ~250 MW midday
dip with near-zero evening bias — a small definitional boundary, not a
conflicting measurement. (The TAC files' stamps sit at a constant per-file
offset vs the extract's wall-true generation frame: +1 h in the hand-pulled
Jan-2023 file, +2 h in the scripted 2024/2025 files — same artifact family as
the documented per-DIBA interchange lag constants. Follow-up filed in §4.)

**(b) The `Demand` column's clock is broken for Jan–Oct 2023 only.**
Monthly best lag of `Demand` against the extract's own balance identity
(`net_gen − interchange`, on the astronomy-verified generation frame):

| window | best lag | r |
|---|---|---|
| 2023-01 .. 2023-10 | **−1 (Demand +1 h late)** | 0.984–0.997 (near-identity) |
| 2023-11 | mixed (transition month) | 0.68 |
| 2023-12 .. 2025-12 | 0 (aligned) | 0.88–0.99 |

Daily scan pins the flip at **2023-11-01**. This closes the seam-tz FINDING's
"open ±1 h Demand-vs-SLD question" (§2): the Jan-2023 SLD comparison (0.9953
at lag −1) was detecting exactly this window; the upstream submission
convention changed on Nov 1 2023 and EIA never restated the prior months.
The model's 2023 demand input therefore rides 1 h late against its own
wall-true renewables — the evening ramp lands after sunset, artificially
deepening the 2023 net-load peak (a live suspect for the spurious 2023
system tail: 480 h > $200 modeled vs 21 actual, open since caiso-49).

**(c) The supply-implied series is the outlier, and its afternoon excess is
a supply-side artifact.** With 2024/25 internally aligned (lag 0), the 930
balance residual `R = net_gen − interchange − Demand` is a zero-daily-mean
diurnal see-saw: **−1.1 to −1.8 GW overnight (deepest h8), +0.9 to +1.8 GW
h15-19** (summer 2024/25; annual mean −138/−201 MW). Both independent demand
measurements (930 `Demand`, TAC SLD) sit together on one side of it, so the
see-saw lives in the 930 *generation/interchange* columns, not in unmeasured
load (partial solar-linked structure: corr(R, NG:SUN) ≈ 0.43). The STEP-0
"model demand runs 1.4–1.7 GW below supply-implied at h14-17" is therefore
NOT missing demand in 2024/25 — treating supply-implied as the load basis
would inject a fictitious afternoon ramp the ISO's own metering contradicts.

## 2. The rule-14 decision

1. **Demand basis: KEEP EIA-930 `Demand`.** It is corroborated byte-for-byte
   (0.9994) by CAISO's own SLD actual; the supply-implied alternative is
   refuted by both. No basis swap; no level change of any kind.
2. **Fix the measured clock defect**: realign the Jan–Oct 2023 `Demand`
   window −1 h onto the wall-true frame
   (`ScenarioConfig.caiso_demand_clock_realign`, GATED default off;
   `eia_loader._CAISO_DEMAND_CLOCK_LAG_H` / `_CAISO_DEMAND_CLOCK_REALIGN_END`,
   derivation frozen against residuals per rule 23 and guarded by
   `scripts/validate_caiso_demand_clock.py`, which fails loudly if EIA ever
   restates the series). Annual energy is conserved to +0.1 MW on the mean;
   the 2023 summer evening ramp moves 1 h earlier (h15 29.5→31.0 GW,
   h21 31.7→29.7 GW); one seam hour at the Oct-31/Nov-1 boundary duplicates
   the first aligned value (documented approximation, ~3 a.m. load).
3. **This is a clock reconciliation, not a tune**: derived entirely from the
   source series' internal identity + the ISO's own load measurement, with a
   forward story by construction (2024+ needs no correction; the constants
   re-derive only from the guard scan when the source data changes).

## 3. Probe caiso-75 (pre-registered before solving)

Single delta on the session's best line: `caiso_demand_clock_realign=True`.
Directions, called before the solve:

- **2023 only** — 2024/2025 are byte-identical by construction (the window
  ends 2023-11-01).
- 2023 evening net-load peak SOFTENS (demand ramp re-overlaps the last solar
  hours): the spurious 2023 system tail (480 h > $200 zonal-max vs 21 RT
  actual) falls; C3a-2023 (+23.5 %) eases.
- 2023 CT/CC afternoon dispatch shifts ~1 h earlier with the ramp; CT_PEAKER
  2023 direction ambiguous in volume (disclosed), shape (D-1 profile) should
  improve or hold.
- C5a-2023 CO2 (+7.1 % CAVEAT) direction follows gas volume — ambiguous,
  disclosed.
- DISCLOSED RISK: the 2023 tail may not close fully (other drivers open since
  caiso-49); a partial move is still the honest input (rule 14 — the fix
  stays in regardless of the residual).

## 4. Follow-ups filed (not this probe)

- **TAC-file stamp offsets → zonal-share weights**: the hourly zonal shares
  (`curate_zonal_shares.parse_caiso_shares`) consume the TAC stamps as-is, so
  the share *weights* ride +1/+2 h off the model frame (level ratios are
  slow-moving; second-order). Fix alongside the next zonal-shares re-derive,
  with its own A/B.
- **The 930 supply-side see-saw** (±1.5 GW diurnal, zero-mean): affects any
  diagnostic that trusts 930 `net_gen` hour-by-hour (e.g. STEP-0 tables);
  benchmark C-gates are unaffected (they score CAMPD/EIA-923/LMP actuals).
  Flagged for the data-provider question list.
- 2025-12 shows one indecisive month (r = 0.78 at lag 0) in the guard scan —
  winter identity noise, no lag flip; watch on the next 930 refresh.
