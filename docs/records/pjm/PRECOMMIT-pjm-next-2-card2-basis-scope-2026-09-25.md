# PRECOMMIT — PJM-NEXT-2 card 2: C1 CC_REGULAR 2024 (−14.68 TWh) — the zonal gas basis is stacked on EIA-923 delivered prints

Session PJM-NEXT-2, 2026-09-25. Keeper `2026-09-25-pjm-next-c1`. Written and pushed **before any solve**. One gated
field, `pjm_zonal_gas_basis_skip_923_priced`, zero free parameters. Off-queue lever, stated reason: it is PJM's own
measurement of the rule-19 layering that PJM's matrix row `miso_zonal_gas_basis_skip_923_priced` names as "the same
rule-19 layering exists in kind … PJM's pjm_zonal_gas_basis included … enters this lane only as its own U candidate
with its own population measurement" — §2 is that measurement.

## 1. Where CC is displaced in 2024 (zero LP)

Model CC_REGULAR 320.9 vs EIA-923 335.6 TWh. By zone (model − 923, CC_REGULAR): **Dominion −10.1, SWMAAC −6.8,
EMAAC −5.0**; over-dispatch elsewhere: Central_PA CC +4.0 / coal +3.5, ComEd CT_PEAKER +6.2, West_APS CT +2.6.
The deficit is eastern and locational, concentrated in Feb-Apr / Oct-Nov and overnight-evening hours. Per plant:
Keys −3.24 (model CF 0.23 vs 0.68 actual), Brunswick −2.11, CPV St Charles −1.97, Greensville −1.71, Warren −1.59,
Wildcat Point −1.54, Doswell −1.47, Red Oak −1.27. Not the cause: CT-only CEMS reporters (Hunterstown, Ironwood,
Allegheny) are uncapped and run near their EIA-923 totals.

Also measured, **not in this arm** (reported for the lane): Montour (3149) is split into COAL_BIT 752 MW and ST_GAS
752 MW slices and the committed extract routes BOTH units' windows to ONE slice per year — 2023 to coal (gas slice
free: 3.21 vs 0.28 TWh), 2024 to gas (coal slice free at $13–23/MWh: 4.53 vs 0.42 TWh). A per-unit routing defect
(card-4 family), ~+2.2 TWh over-dispatch in Central_PA in 2024.

## 2. The cause measured: zonal basis on top of delivered prints

SWMAAC CCs are offered at a median ~$36/MWh in 2024 against Dominion's ~$24 (2023: $30 vs $38). Resolved gas:
SWMAAC 3.12 / 3.97 / 7.28 $/MMBtu (2023/24/25) while the western zones sit at 2.1-2.5 (2024).
The keeper arms `gas_plant_monthly_fuel_pricing` (EIA-923 per-plant prints + nearby pool) **and** the mean-zero
`pjm_zonal_gas_basis` (N3045<ST>3 state delivered-to-electric-power basis). The basis is added to print cells:

| plant (2024) | EIA-923 own print | model | model − print |
|---|---|---|---|
| Wildcat Point 59220 (MD, the only MD gas plant with public receipts) | 6.17 3.07 2.84 1.94 3.62 2.44 … | 6.95 3.84 3.60 2.74 4.36 3.24 … | **+0.78 every month** (2023: +0.53) |
| Brunswick 58260 (VA) | 5.27 2.77 2.36 3.22 … | 5.74 3.22 2.86 3.65 … | ≈ +0.45 |

Keys and CPV St Charles (no public receipts) inherit Wildcat's print + basis via the nearby pool. A delivered print
already embeds the regional delivered premium (the state series IS the aggregate of those receipts), so the premium
enters twice — the defect miso-213 measured and fixed for MISO. MISO's verdict does not transfer (rule 25); this is
PJM's own measurement.

## 3. The arm

`pjm_zonal_gas_basis_skip_923_priced`: the print-written-cell mask from `apply_plant_monthly_fuel_prices` is passed
to `basis/pjm.apply_pjm_zonal_gas_basis` (both fuel chains), which under the flag skips masked cells; the
capacity-weighted mean is still over all gas rows, so the spread values are unchanged. Zero-LP census (2024
fleet-only rebuild): **687 gas rows move, fuel only** — SWMAAC −0.78, Dominion −0.47, AEP_Ohio / ATSI +0.11
$/MMBtu (print-priced CC: Dominion 9,257 MW, AEP_Ohio 12,965, ATSI 2,594, SWMAAC 2,663); availability, min_gen and
every non-gas row byte-identical; flag off byte-identical. **Inert 2019-2021 by construction**
(`pjm_zonal_gas_hub.csv` has no rows before 2022 → the applier is a no-op), so those three years are **not
re-solved**: the composed arm carries the keeper's committed 2019-2021 legs (rule 34(c) exception, stated here).

G-DRIFT: as card 1 §5 — keeper recipe arrays byte-identical at `7f095384` and HEAD; form 4 valid.

## 4. Predictions (before the solve)

- CC_REGULAR rises in SWMAAC and Dominion and falls in AEP_Ohio / ATSI in 2022-2025. The sign of the ISO-total
  CC_REGULAR change is **not** predicted (east +, west −). If the ISO total barely moves, the arm is still a rule-19
  structural repair and is reported as such (rule 1: never selected on the residual).
- SWMAAC / Dominion zonal prices may fall slightly; C3a direction not predicted.

## 5. Execution

Four shards, 2022-2025: `replay_keeper.py results/calibration/pjmnext_c1_span --years <y>
--set pjm_zonal_gas_basis_skip_923_priced=true`, pinned SHA, full bundle to `claude/pjmnext2-c2-<y>`. Hard stops as
card 1 §7 except (b): the outage extract sha must be the keeper's `312a11b8` and (d) the arm flag true. The parent
composes 2019-2021 keeper legs + 2022-2025 arm legs, scores, attests, registers, asks.
