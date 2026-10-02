# FINDING — NYISO-NEXT-31 phase 0: the bridge D-4 rows have no parameter-level repair — 2026-10-01

Zero LP. Keeper `2026-10-01-nyisonext21-astoria-hr-span` + stamped `-2021`, untouched. Open item 4 (LEAD B).

Probe `scripts/probes/nyisonext31_bridge_d4_legs.py --legs-dir <git archive of claude/nyisonext21-<y>>`
→ `results/phase0/nyiso/_nyisonext31_bridge_d4_legs.json`. It reads each leg's P1 floor
(`floors/<y>_P1.npz`, mechanism 20) and P1 unit dispatch (`unit_hourly_<y>.parquet`), and the CAMPD bench meter.

**Validation:** the probe's binding hours/GWh reproduce the keeper's D-4 rows exactly
(Saranac 54574: 2021 25 h / 0.7 GWh, 2024 142 h / 4.65 GWh; Athens 55405: 2025 3 h / 0.51 GWh).

## 1. Leg attribution

Saranac (measured per-plant min-run 14 h) and Athens (10 h) are outside the state-floor cohort (≥ 100 h),
so their floor comes only from the min-run extension or the gap legs, and every floored hour was P0-OFF.
P0 dispatch is not in the bundle, so each floored block is classified from its P1 neighbours (proxy).

| row | binding h | meter-zero h | min-run | gap | other | unanchored | in measured off > 24 h | anchor run never metered on | meter > 0 but < floor |
|---|---|---|---|---|---|---|---|---|---|
| Saranac 2021 | 25 | 25 | 12 | 0 | 0 | 13 | 7 | 0 | 0 |
| Saranac 2024 | 142 | 81 | 5 | 3 | 27 | 46 | 31 | 12 | 12 |
| Athens 2025 | 3 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |

Fleet, all bridge plants with a trusted meter (D-4's CT-only skips excluded), meter-zero binding:

| year | bridge-floored energy | meter-zero binding | min-run | gap | other | unanchored |
|---|---|---|---|---|---|---|
| 2021 | 6.4 TWh | 17.4 GWh / 282 h | 19 | 88 | 31 | 137 |
| 2022 | 6.7 TWh | 7.0 GWh / 216 h | 43 | 85 | 22 | 59 |
| 2023 | 7.1 TWh | 1.8 GWh / 32 h | 3 | 15 | 0 | 15 |
| 2024 | 6.8 TWh | 10.4 GWh / 232 h | 21 | 69 | 37 | 104 |
| 2025 | 7.4 TWh | 11.0 GWh / 270 h | 43 | 136 | 38 | 54 |

## 2. Answers to the three questions

- **(i) Min-run leg: a minor share.** It is half of Saranac 2021 (12 of 25 h), and 3–43 h a year fleet-wide.
  Per-plant min-run is `R` (nyiso-146), so it is not re-tested. The class 21 h is a measured CAMPD value (rule 23).
- **(ii) Min-load share: not the defect.** The rider fails on a ZERO meter, not a low one.
  Hours with the meter above zero but below the floor are 0–12 on these rows. Changing 0.523 changes GWh, not the verdict.
- **(iii) Detection / the P0→P1 seam: the largest share.**
  - The biggest bucket is `unanchored`: the floored block abuts no P1 run. P1 bid-cost dispatch moved the run that P0 detected, so the floor sits next to a run P1 never made.
  - The largest bucket that can be attributed is the economic gap leg (≤ DA horizon), across gaps the real unit cycled through.
  - 12 of Saranac 2024's meter-zero hours anchor on a run the unit never metered.

## 3. No parameter-level repair

- **Gap leg:** its driver is the class startup cost (NREL table) against the P0 margin. Moving it class-wide to clear meter-zero hours would be tuning to a residual (rules 1, 13).
- **Seam:** re-detecting on P1 is an architectural change: a second detection pass, which is a P1 iteration. It is not a parameter.
- **Per-plant levers** (min-run, exclusion) are `R` or would be per-plant knobs (rule 18).

**Materiality:**
- The keeper's three bridge FAIL rows total 5.9 GWh over five years.
- Fleet-wide meter-zero binding is ≤ 0.3 % of bridge-floored energy.
- NEXT-26 arm B reads CALIBRATED with these rows present. They do not move the determination.

**No PRECOMMIT.** Open item 4 is closed at phase 0. Proposed owner card 6: ledger the bridge D-4 rows as a P0-anchored-detection seam limitation. Re-open only with an admissible P1-native commitment detector, or on new evidence moving a row above materiality.

The `nyiso_gas_commitment_bridge` cell verdict is unchanged; append this FINDING as evidence.
