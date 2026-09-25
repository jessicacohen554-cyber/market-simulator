# RESULT — R-SOCO: SOCO re-solved on the corrected backcast inputs (F1 + F2)

Charter: `docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md` §5.3.8.
PRECOMMIT: [`PRECOMMIT-r-soco-2026-09-24.md`](PRECOMMIT-r-soco-2026-09-24.md), pinned
`455e002177738e8291a84da08f76123336b7dabc`. The parent spent no LP. Three year-isolated shards ran
8–10 min each.

**Run: `2026-09-24-r-soco-corrected-inputs`**, bundle `results/calibration/rsoco_corrected_inputs_span`.
It is registered and **not promoted**; the promotion question is in §6.

## 1. Headline

- **Determination unchanged:** `PHYSICALLY-CALIBRATED (PRICE UNSCORED)`, the same as the keeper
  `2026-09-24-soco61-dark-unit`. This scorer literal certifies no price, as before.
- **No status moved.** C1 is 14/14 (free 10/10). C2, C4, C6 and C8 PASS. C3a/b/c are UNSCORABLE
  (SOCO has no price reference). Grade is 5/5/0 and DOF `n_residual` is 1.
- **Years: 2023–2025 only.** 2019–2022 cannot be solved: SOCO has no EIA-930, FERC-714,
  interchange/seam, gas-hub, solar-shape or renewable-capacity inputs before 2023 (PRECOMMIT §2).
  This is routed in §5.
- The recipe is the keeper plus the owner-mandated input corrections: the year-matched EIA-860 vintage,
  plant heat rates including CHP, and the CAMPD short-coal, short-gas and partial outage families. **The
  offer-curve multipliers are unchanged.**

## 2. Per year, keeper → re-solve (C1 grid-delivered TWh; share error in pp)

| year | class | actual | keeper | re-solve |
|---|---|---:|---:|---:|
| 2023 | CC_REGULAR | 110.89 | 113.19 (+1.31) | 113.75 (+1.54) |
| 2023 | COAL_PRB | 23.66 | 22.03 (−0.61) | 21.70 (−0.74) |
| 2023 | COAL_BIT | 13.79 | 11.67 (−0.84) | 11.57 (−0.88) |
| 2023 | ST_GAS | 9.29 | 3.80 (−2.26) | 4.14 (−2.12) |
| 2023 | CT_PEAKER | 4.33 | 9.56 (+2.19) | 9.41 (+2.13) |
| 2023 | CC_CHP | 1.86 | 2.28 (+0.18) | 2.00 (+0.06) |
| 2024 | CC_REGULAR | 110.31 | 113.45 (+2.19) | **110.69 (+1.09)** |
| 2024 | COAL_PRB | 26.91 | 22.73 (−1.45) | 23.67 (−1.07) |
| 2024 | COAL_BIT | 13.36 | 11.50 (−0.63) | 11.32 (−0.70) |
| 2024 | ST_GAS | 7.62 | 2.92 (−1.81) | 3.17 (−1.71) |
| 2024 | CT_PEAKER | 4.41 | 6.76 (+0.98) | **8.93 (+1.85)** |
| 2024 | CC_CHP | 1.82 | 2.29 (+0.20) | 1.98 (+0.08) |
| 2025* | CC_REGULAR | 110.51 | 109.84 (−0.60) | 108.22 (−1.25) |
| 2025* | COAL_PRB | 28.35 | 31.65 (+1.22) | 32.21 (+1.44) |
| 2025* | CT_PEAKER | 4.71 | 5.07 (+0.13) | 6.23 (+0.59) |

\*2025 C1 rows are SKIPPED by the scorer in both runs; this is pre-existing.

| metric | 2023 | 2024 | 2025 |
|---|---|---|---|
| C4 gas r / NRMSE | 0.958/0.087 → 0.961/0.087 | 0.952/0.111 → 0.956/0.103 | 0.947/0.090 → 0.949/0.090 |
| C4 coal r / NRMSE | 0.904/0.210 → 0.910/0.215 | 0.843/0.235 → 0.841/0.224 | 0.882/0.200 → 0.888/0.201 |
| C8 ST_GAS forced share | 15.9 → 14.3 % | 16.1 → 16.4 % | 18.3 → **20.2 %** (under the 30 % cap) |
| unserved MWh | 0 → 0 | 0 → 0 | **267.4 → 813.8** |
| model mean LMP (UNVERIFIED, no reference) | $30.90 → $30.98 | $27.98 → $28.93 | $53.16 → $54.25 |

**Better:** 2024 CC_REGULAR (+2.19 → +1.09 pp); CHP now tracks EIA-923 in every year; ST_GAS is
closer everywhere; 2024 COAL_PRB is closer. **Worse, reported at full magnitude:** 2024 CT_PEAKER
(+0.98 → +1.85 pp, +2.17 TWh). It replaces the CC energy the short-gas / partial windows remove,
the same substitution SOCO-61 saw. 2025 unserved triples (the added outage windows tighten the
scarcity hours). The 2025 ST_GAS forced share rises to 20.2 %. D-1 2023 COAL_BIT diurnal profile_r
0.38 → 0.0 is still the one D-1 FAIL, pre-existing and not gating (C8 is under budget).

Pre-registered expectations (PRECOMMIT §6): **E1** held (2023/24 coal within ±1.5 TWh:
−0.43 / +0.76). **E2** held (CC_CHP −0.28 / −0.31 / −0.29 TWh). **E3** held in 2023 (+0.56) and
failed in 2024. In 2024 CC fell by 2.76 TWh, more than the < 2 TWh I expected, which means CC
*is* availability-bound in 2024 hours. **E4** held.

## 3. Census deltas (phase 0; PRECOMMIT §3)

The EIA-860 source goes from canonical to `vintage_2023` / `vintage_2024` (2025 stays canonical).
3,647 MW of coal that the canonical snapshot carried fully dark leaves the fleet, and availability
energy removed falls by an equal 31.4 / 31.5 TWh. CC_CHP heat rate goes 5.85 → 8.1 and CT_CHP
5.58 → 6.85. CC availability removed rises by 5.8–6.5 TWh/yr. The residual class-table heat rate
is 1,045 MW (Dahlberg 7709, Hartwell 54538), an EPA↔EIA facility-ID crosswalk defect (routed, §5).
The benchmark is unchanged: the EIA-923 / EIA-930 shared-input hashes equal the keeper's. The CAMPD
frame hash moves because it keys on fleet plants.

## 4. Governance

- **Attestation** `calibration-attestation/v1`, `exceptions []`. `gen_rsoco_attestation.py` sits on
  top of `gen_soco60b_attestation.py`. The inherited checks are re-verified by execution.
  `gen_soco60b` gains an explicit `--declared-inert-moved` flag for the one new solve-surface key,
  `RGGI_MEMBER_STATES_BY_YEAR`: pjm-h22 added its 2020/2022 rows, and it is INERT for SOCO because
  no SOCO state is a RGGI member. This extends the G-DRIFT of PRECOMMIT §4. The outage inputs are
  sha256-verified and equal the files at the pinned SHA: std `-perunitdark-` `ae0912a9…`, short
  `3f9c371c…`, short-gas `13cee3d9…`, partial `dde155f9…`.
- **DOF**: 17 entries, `n_residual` 1 (unchanged). The four new entries are categorical measured
  switches with `n_scalars` 0. No `authorized_price_tuning`; every band is 1.0.
- **Matrix (rule 28(b))**: in the SOCO shard, `eia860_vintage_tracks_solve_year`,
  `measured_chp_heat_rates`, `unit_outage_short_windows` (which carries the partial family) and
  `unit_outage_short_windows_gas` move U → **O** (tested, promotion owner-pending).
- **Parity gate**: RED locally only on the three gitignored per-year legs (rule 31's documented
  local-RED case); CI sees committed files only.

## 5. Routed, not done here

1. **SOCO 2019–2022 intake** (the addition plan's manifest row 9). The EIA-930 part is derivable from
   the committed `EIA930_BALANCE_2019…2022` parquet. FERC-714 (PUDL), interchange (needs an EIA API
   key or the Grid Monitor CSV), delivered gas, the gas hub, and the seam / solar-shape / zonal-share /
   renewable-capacity builders all need to run for 2019–2022. When that lands, a successor solves
   2019–2022 one shard per year on this recipe and folds them into the keeper.
2. **EPA↔EIA facility-ID crosswalk** for the measured heat-rate and outage derives. It is cross-ISO
   and an F1 residual. SOCO case: Dahlberg 7709↔CAMD 7765 and Hartwell 54538↔70454, 1,045 MW of CT at
   class-table 10.5 / 11.5 against a measured ≈12.0.

## 6. Where the bytes are; promotion

- **On `main` once this PR merges**: the composite bundle (17 files, rule-15 shape), its sidecar,
  its run payload and the SOCO bench parts. **A promotion from that state costs zero re-solves.**
- **Per-year legs**: gitignored and on this container only. Provenance SHAs (not a recovery route):
  2023 `bf7309eed7866f0b8d7080f81ac808a2beb40930`, 2024 `4734ccb3d39c1c0a6f910f56fd07cad1b20bd2ad`,
  2025 `17d33d1a60f593cae9d8cb1861ccf1f3b6964365`. Recovering them would mean re-solving, about
  10 min per year.
- **Leftover shard branches for the owner to remove** (a session cannot delete refs):
  `claude/rsoco-2023`, `claude/rsoco-2024`, `claude/rsoco-2025`.
- **Recommendation: PROMOTE.** PRECOMMIT §6 fixed the rule before the solve: this is an owner-mandated
  input correction, all three years solved cleanly with the posture verified, and no status
  regressed. Rule 14 forbids keeping the inaccurate inputs because of the 2024 CT_PEAKER / 2025
  unserved moves; those two are root-cause leads.
  If promoted, the rule-35 prune removes `2026-09-24-soco61-dark-unit` and the long-unruled
  `2026-09-20-soco53g-prb-own-iso`. The year union {2023, 2024, 2025} is covered.

## Addendum — rebase onto `main` @ `3321109c` (G-DRIFT, rule 29(b))

The lane was rebased onto `main` for merge. Between the pinned SHA `455e0021` and `3321109c`, one
lane (R-NEISO, `c265c1c3`) touched the solve path. Every hunk is INERT for this run:

| hunk | class | reason |
|---|---|---|
| `data/outages.py` + `fleet/arrays.py`: gas sub-5-day scope armable without the coal scope (`coal_scope`) | INERT | both flags are armed here, so the call is byte-identical (`coal_scope` defaults True) |
| `fleet/eia860.py` `_mid_vintage_exit_rows_from_window` | INERT | only reached under `mid_vintage_exit_carry`, which is `False` in this run's resolved config |
| `results/cache.py` epoch note | INERT | prose only, no `SolveEpoch` |

The registered run therefore stands at the rebased head with no re-solve. The only conflict was the
append-only `docs/calibration-log/soco.md`; both sides' entries were kept.
