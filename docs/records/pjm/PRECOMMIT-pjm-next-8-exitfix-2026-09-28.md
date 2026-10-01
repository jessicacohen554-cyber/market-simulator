# PRECOMMIT — PJM-NEXT-8 card 2: exit-cohort repair of the CAMPD outage layer (2026-09-28)

- **Owner approval.** Decision card 2026-09-28, card 2: *"Build + solve"*. Basis: `docs/FINDING-pjm-next-7-coal-phase0-2026-09-28.md` §3–§5 (rule 14 `[R-ACCURATE]`).
- **Keeper and control.** Keeper `2026-09-28-pjm-next-7-virtual` (`results/calibration/pjmnext7_vs_span`, solved at `f2850356`). The control is the keeper's committed bundle plus G-DRIFT (§4); no control solve (rule 29(b)).
- Written and pushed **before any solve**.

## 1. Arm (single delta, zero free parameters)

`replay_keeper.py results/calibration/pjmnext7_vs_span --years <y> --out-dir results/calibration/pjmnext8_xf_<y> --set unit_outage_exit_cohort_repair=true`, one shard per year 2019–2025 (rule 36), pinned to this commit.

`unit_outage_exit_cohort_repair` selects `data/raw/campd-unit-outages-rederive-peakerkeep-exitfix-unitfuel-PJM.csv` (14,113 rows, sha256 `02d565cd382fc69692b7c04ca38985b21b5e66a7f229d44548145bd30f0e40ff`), built by `scripts/probes/_pjmnext8_build_exitfix_companion.py`: the keeper's own construction plus the deriver's new `--exit-cohort-repair`:

| part | what | example |
|---|---|---|
| (a) | unit capacity from the derive year's **own** EIA-860 vintage (year-end operable + retired-during-year), prime-mover disambiguation of multi-hit digit matches | Chalk Point 1571 coal `1`/`2`: 16/35 MW (GT1/GT2) → 364 MW (ST1/ST2) |
| (a′) | a unit whose matched generator's prime mover cannot belong to its routed bin gets no window there | Possum Point 3804 unit 5 (882 MW oil ST) no longer derates the CC bin |
| (b) | at a plant split into dated exit bins, a row derates **its own** dated bin over that bin's share (`exit_ym` key) | Mansfield 6094 unit 3 bin: 0.639 → 0 in its windows |
| (c) | one full-year window for a unit dark every hour of the year that the year's vintage carries and retires that year or next, a peer running | Mansfield 1–2, Sammis 1–2 (2019) |

**Control check (done):** the construction without the switch reproduces the keeper's committed companion **byte-for-byte** (sha256 `5171a5fb…`), and the new code's off path re-derives the identical raw extract (sha256 `49e9678a…` both ways). Unit tests: `tests/unit/data/test_unit_outage_exit_cohort_repair.py` (8 pass). The 28 failures in `tests/unit/data/test_outages.py` / `test_unit_outage_*` / `test_campd*` are identical on `origin/main` (non-PJM data not hydrated).

## 2. Zero-LP footprint (`scripts/probes/_pjmnext8_exitfix_avail_delta.py`, fleet_only off vs on)

| year | Δ available COAL_BIT (TWh) | keeper model energy above repaired availability (TWh) | plants |
|---|---|---|---|
| 2019 | −16.6 | **10.4** | Mansfield 3.9, Sammis 3.0, Conesville 1.7, Chalk Point 1.7 |
| 2020 | −4.9 | 0.9 | Chalk Point 0.9 |
| 2021 | 0.0 | ≤ 0.1 | Sammis 0.1 |
| 2022 | −0.6 | ≤ 0.15 | Sammis, Homer City |
| 2023 | −0.7 | ≤ 0.17 | Sammis 5–7 (2023 exit) |
| 2024 / 2025 | **0.0 (no array moves)** | 0 | — |

CC_REGULAR availability moves < 0.2 TWh in any year (Lackawanna 60357 re-sized CS 499.5 → 555 MW per its vintage).

## 3. Predictions (C1, model − actual TWh; band ±8)

Net = gross × 40–70 % (other synced coal backfills, as FINDING §5 assumed).

| row | keeper | predicted | verdict |
|---|---|---|---|
| COAL_BIT 2019 | +17.81 | **+10.5 to +13.6** | still FAIL |
| COAL_BIT 2020 | (pass) | −0.4 to −0.6 | PASS |
| COAL_BIT 2021 | +17.16 | +17.1 ± 0.1 | still FAIL |
| COAL_BIT 2022 / 2023 | pass | Δ within ±0.15 | PASS |
| every row 2024, 2025 | — | **byte-identical** | unchanged |
| CC_REGULAR 2019–2020 | | +1 to +4 (backfill) | 2020 stays FAIL |

**Falsifiers:** (i) any 2024/2025 class-hour moves (the arrays are identical and years are isolated); (ii) |ΔCOAL_BIT 2023| > 0.3; (iii) ΔCOAL_BIT 2019 outside −3 to −9. **Expected determination:** run-level still NOT-YET; training span unchanged (CC_REGULAR 2023 +8.40, the zonal defect in `docs/FINDING-pjm-next-8-cc2023-phase0-2026-09-28.md`). Promotion is the owner's, on structure (rules 1, 31).

## 4. G-DRIFT (keeper `f2850356` → this pin)

Every hunk on the backcast path in `git diff f2850356 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference` is INERT for PJM:
- `caiso_tac_shares_standard_time` (scenarios, eia930 demand/zonal shares, both runners): CAISO-gated, default off, absent from the recipe.
- `campd.CAMPD_UNIT_PLANT_REMAP` (SPP-98): facilities 1416 / 3006 / 762 / 63628, all SPP-area, none in PJM's fleet or CAMPD states.
- `ferc714.py` system lambda: SOCO, reported-only, not an LP input.
- `pipeline/commitment.py`: inside the SOCO gas-steam campaign commitment function, SOCO-gated.
- `scripts/lib/seam_neighbour_price/*`: new files, imported by no solve-path module.
- This lane's own changes: default-off field; `arrays.py` computes dated shares only when armed; `outages.py` adds default-off parameters with `key = tgt` otherwise.

**All INERT → form 4 valid; the keeper bundle is the control.**
