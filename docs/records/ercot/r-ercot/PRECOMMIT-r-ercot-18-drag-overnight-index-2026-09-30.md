# PRECOMMIT — R-ERCOT-18: prior-year overnight-commitment allocation of the ST_GAS drag

Date 2026-09-30. Keeper `2026-09-29-r-17-south-texas` (bundle `results/calibration/r_ercot17_span`, 2019–2025, ISO NOT-YET). DATA PROFILE: ercot. Written before any solve.

## 1. The object

2022 went CALIBRATED → NOT-YET at R-ERCOT-17 on C8 alone: ST_GAS forced share 30.4 % against a 30 % cap. The above-cap escape (rule 21: D-4 window + D-1 shape) fails on one row, the D-4 per-unit conduct FAIL of `st_netload_drag` at plant 3452 (Lake Hubbard, 927.5 MW). The floor binds 4,662 h and 0.43 TWh, while the plant's own meter reads zero in 76 % of those hours. The defect is pre-existing and was the same in the prior keeper.

## 2. Phase 0 — characterization (zero LP)

**Which rows carry the defect.** Keeper `legitimacy_diagnostics.json`, D-4 unit-conduct rows for `st_netload_drag`: 9 FAILs in 62 rows.

| Plant | FAIL years |
|---|---|
| 3452 Lake Hubbard | 2019, 2020, 2021, 2022, 2023 |
| 3628 R W Miller | 2019, 2020 |
| 3491 Handley | 2024, 2025 |

Only 2022 is rubric-visible, because only 2022 sits above the C8 cap.

**Why the floor reaches 3452.** It is ST_GAS and not on `ST_GAS_PEAKER_PLANTS`. That registry's own pooled duty test puts Lake Hubbard at 36.9 %, just above the cut (the cut lies in the registry's empty gap, 34.7–36.9 %). Moving the cut would be a threshold sweep, so membership is not the lever. Unit physics (8 h min-run/down) does not separate it from the other boilers either (rule 18).

**What 3452 actually does.** It is neither a mothball nor a seasonal lay-up. It is a **two-shift cycler**:

- 2022 units ran 25 % / 28 % of hours, and the median off-run was 12–13 h.
- 51–62 % of its off-hours sit in sub-5-day stops, which the lay-up mask cannot see.
- 2022 meter-on share by hour of day is ≈0 over 23–02h and ≈0.5 over 09–20h.
- The pro-rata floor, by contrast, binds 55–65 % of every hour of the day.

**The driver says so directly.** The drag's driver is the fleet's CAMPD **overnight (23–05h)** capacity factor (`docs/ercot-st-gas-netload-drag-2026-06.md`). 3452's own overnight CF was near zero until 2023:

| Year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| 3452 overnight CF | 0.008 | 0.001 | 0.000 | 0.012 | 0.050 | 0.132 | 0.186 |

The pro-rata applier nonetheless assigns it the fleet's ~0.15. Per rule 17 that is a bug by definition: the floor binds in hours its own driver evidence says the unit is off.

**Prior repairs and why they did not close it.**

| Repair | Lane | Outcome |
|---|---|---|
| Lay-up mask | ercot-256 (armed) | Blind to sub-5-day stops |
| Merit allocation | ercot-259/260 | 3452 stayed convicted (median 0 MW); 2023 C8 13.5 → 17.8 % |
| Sub-5-day grain instrument | — | Refused as pinning |
| Class-level LP row | — | Refused (makes C8 blind) |
| Static pooled ordering | — | Refuted, not year-stable (3452 went 0.00 → 0.19 overnight CF across the span) |

## 3. The construction (owner decision card 2026-09-30: "Build prior-year index (Recommended)")

New default-off flag `netload_drag_prior_year_commitment_index`. It is an allocation-only swap in `fleet.floors.apply_netload_reliability_floor`:

- The curve, membership, window and mech id are unchanged. It adds no floor (rule 19).
- Each metered plant's fraction becomes `floor_frac × k_p`, with `k_p = (E_p/B_p)/(ΣE/ΣB)`.
  - `E_p` is the plant's **Y−1** measured overnight net MWh.
  - `B_p` is the floor's own pmax basis.
  - So the nominal mandate is preserved over the metered plants.
- Unmetered plants keep k = 1.
- Artifact: `scripts/data/derive_ercot_stgas_overnight_commitment.py` → `data/raw/_validation-source/ercot_stgas_overnight_commitment.csv` (sha256 `285c74f1…`). It uses the curve derive's own fleet, unit routing and window, and is frozen under rule 23.
- **Fail-closed:** where there is no Y−1 vintage, allocation stays pro-rata. That covers 2019, because TX 2018 CAMPD is off disk.
- **Backcast-only** (rule 13), refused in forecast mode by `_BACKCAST_ONLY_OVERLAY_FIELDS` and gated again in the loader.
- Zero free parameters (rule 21).
- Matrix: registered as a sub-gate in the `netload_drag_floors` row, the same as the three sibling sub-gates.
- Tests: `tests/unit/data/test_drag_prior_year_index.py` (11 tests).

## 4. Phase 0 — fleet delta through the real code path (zero LP)

Probe: `scripts/probes/_r_ercot18_drag_index_delta.py` → `docs/records/ercot/r-ercot/r_ercot18_drag_index_delta.json`. It rebuilds each year fleet-only through `replay_keeper`'s recipe, with the flag off vs on. Checks: pmax, availability, mc and every non-drag min_gen are byte-identical; the row sets are identical.

Nominal drag floor energy, TWh (off → on):

| Year | Total | 3452 | 3491 | 3628 | 3460 |
|---|---|---|---|---|---|
| 2019 | 5.672 → 5.672 (**byte-identical**) | 0.410 | 0.600 | 0.365 | 0.980 |
| 2020 | 4.668 → 4.813 | 0.458 → 0.093 | 0.568 → 0.298 | 0.178 → 0.101 | 0.761 → 1.127 |
| 2021 | 5.492 → 5.672 | 0.442 → 0.018 | 0.814 → 0.469 | 0.264 → 0.084 | 0.940 → 1.871 |
| 2022 | 6.686 → 6.702 | **0.692 → 0.004** | 0.919 → 0.524 | 0.306 → 0.178 | 1.070 → 2.124 |
| 2023 | 6.725 → 6.783 | 0.702 → 0.113 | 1.003 → 0.484 | 0.326 → 0.200 | 1.214 → 2.340 |
| 2024 | 6.723 → 6.921 | 0.689 → 0.355 | 0.835 → 0.640 | 0.381 → 0.231 | 1.185 → 1.811 |
| 2025 | 5.450 → 5.377 | 0.766 → 0.817 | **0.874 → 0.161** | 0.425 → 0.265 | 0.756 → 1.003 |

The delivered total moves −1.3 % to +3.9 %. The cause is the availability clip: moving MW onto plants with headroom delivers more of the nominal mandate. This is stated, not hidden; the nominal mandate is preserved by construction. In 2025, 3452 rises slightly (its 2024 overnight CF of 0.13 is at the fleet mean), consistent with its meter (2025 D-4 already passes, median 55.6 MW).

## 5. G-DRIFT (rule 29(b)) — keeper legs `4aaa1a1f` → base `2202f60a`

Exactly one file changed on the backcast path: `scripts/lib/forecast_parity_registry.py`. It adds a declaration row, is imported by no solve-path module, and is **INERT**. The keeper's committed legs are the control (form 4), so there is no control solve.

## 6. Arm

Seven shards (rule 36), one per year. Each runs `replay_keeper.py results/calibration/r_ercot17_span --years <Y> --set netload_drag_prior_year_commitment_index=true`. Prompts are in `docs/records/ercot/r-ercot/SHARD-PROMPTS-r-ercot-18.md`. 2019 is solved as a byte-identity check of the fail-closed path.

## 7. Predictions (written before solving)

| Year | C8 ST_GAS (keeper → arm) | D-4 st_netload_drag FAIL rows | C3a move | Determination |
|---|---|---|---|---|
| 2019 | 18.1 % → identical | 2 → 2 | 0 | NOT-YET (unch.) |
| 2020 | 21.9 % → 19–24 % | 2 → 0 | < 0.5 pp | NOT-YET (unch.) |
| 2021 | 22.4 % → 20–25 % | 1 → 0 | < 0.5 pp | CALIBRATED (unch.) |
| 2022 | **30.4 % → 26–33 %** | **1 → 0** | < 0.5 pp | **NOT-YET → CALIBRATED** — via C8 < 30 %, or via the escape if the D-1 shape holds |
| 2023 | 18.5 % → 16–22 % | 1 → 0 | < 0.5 pp | NOT-YET (hold) |
| 2024 | 15.4 % → 14–19 % | 1 → 0 or 1 (3491 still floored 0.64) | < 0.5 pp | NOT-YET (unch.) |
| 2025 | 22.8 % → 18–24 % | 1 → 0 | < 0.5 pp (2025 C3a is at −9.9 %, edge) | CALIBRATED — **at risk only via the C3a edge** |

- **Direction risk, stated.** Concentrating the mandate onto efficient plants (3460 Cedar Bayou doubles) can *raise* the realized forced share, because a bigger block binds where a thin smear did not. That is what merit allocation did in 2023. My central expectation for 2022 is ~29 %, with real uncertainty either side. The escape needs D-4 clean plus the D-1 shape, and I expect D-4 to be clean.
- ST_GAS class energy: up 0–0.3 TWh per year (the delivered mandate rises).
- LW price: ±0.3 $/MWh.
- Slack: unchanged.

## 8. Decision rule

- **Promote** under the standing instruction ("Is it an improvement? Then promote") if:
  - no year's determination flips worse, and
  - the D-4 `st_netload_drag` FAIL count falls.
- The construction's basis is rules 17/14 (the floor contradicted its own driver evidence), not the residual.
- **Decision card, not self-promotion, with every bundle kept (rule 31)** if any of:
  - any year flips worse (2025's C3a edge is the live risk);
  - 2022 stays NOT-YET *and* C8 rises in two or more years.
- DOF ledger: unchanged (zero added).
