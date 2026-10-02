# RESULT: closeout W0 denominator fix, part 2 — the live roster (desk ruling D-1), 2026-10-02

Lane `closeout-W0-denominator-fix-2`, chartered by the Backcast close-out desk. **Zero LP.** Base `origin/main`
837556d2 (PR #7047 merged). Evidence for this note is in `W0-denominator-fix-2/`.

## 1. Defect and ruling

With `unit_outage_dispatched_bin_denominator` on, a dated exit cohort that retired BEFORE the solve year stays on
the LP roster at zero availability (the COD ramp masks every month), and its `pmax` stayed in the bin's outage
denominator all year, diluting the survivors' measured derate. #7047 fixed the in-year case only (RESULT part 1 §2).
Desk ruling: under the companion the denominator is the LIVE roster, `D_k(t) = Σ pmax_i · online_i(month t)`;
fold the default-off NWPP-NEXT-15 sub-gate `unit_outage_dispatched_bin_live_denominator` into the companion and
delete it (rules 19 / 26), keeping #7047's monthly mechanics and its zero-month fallback.

## 2. Fix (no new field; zero free parameters)

- `outages.lp_bin_capacity_index(live_year=)` reads each row's `(12,)` online mask off
  `cod_ramp.generator_online_mask` (`outages._roster_online_masks`) — **the COD ramp's own resolver, with the same
  inputs** `fleet.arrays` applies it with, clipped at 1.0. So the denominator IS the capacity the LP carries online.
  - A row offline every month is skipped (dead exit cohorts: Scherer 6257 2023-25, Centralia 3845, Colstrip 6076,
    Schahfer 6085, Petersburg 994, Dallman 963, ...).
  - A bin held below its `pmax` in some month gets #7047's monthly entry and divides hour by hour; a month whose
    live roster is 0 keeps the full-year value (no divide-by-zero, no over-derate of an all-exit key).
  - A bin fully online all year gets no monthly entry: its roster is byte-identical.
- One accessor, `outages.dispatched_bin_live_year` (companion on, `mode == "backcast"`, `cod_ramp_enabled` —
  exactly when the COD ramp runs). `dispatched_bin_exit_year` and the `exit_year=` parameter are folded into it.
- Every roster site threads it: `fleet/arrays.py` (overlay roster, mustrun lay-up, miso-273 screened-coal share),
  `fleet/floors.py` (drag lay-up), `scripts/run_calibration.py` (reliability-floor lay-up, which now takes the LP
  generators so it can read their COD dates; a row-count mismatch raises).
- **Deleted (rule 26):** the field, its `_CACHE_KEY_OPTIONAL_FIELDS` / defaults entries (registered optional at
  False, so no retired-field entry is owed and no default key moves), both runners' kwargs and recorded keys, the
  `--[no-]unit-outage-dispatched-bin-live-denominator` flag pair, its matrix row and its cell in all nine shards.
  `replay_keeper._RULE26_DELETED_UNCONDITIONAL` maps the key `("NWPP", (True, None))`; every keeper meta records
  None.
- **The sub-gate's second limb** (screened-coal-first relief order) now belongs to
  `wefor_residual_short_screened_coal`. It changes output only where `wefor_residual_groups` names a coal class;
  MISO's keeper, the only one arming the relief, names none, so the limb is inert there
  (`TestScreenedCoalFirst::test_coal_blend_independent_of_the_groups`).

**Wider than "dead cohorts", by the ruling's own formula.** Keying on the exit-cohort unit-id tag alone (the
NWPP-NEXT-15 construction) missed rows whose COD-ramp mask is below 1 without being a dated cohort: a plant-level
bin whose EIA-860 constituents are only partly in service (SOCO 2023 Barry 3 CC_REGULAR: 1,845 MW on the roster,
1,071 MW online all year, −1.00 TWh) and mid-year builds (MISO 2019 56104 CC_REGULAR −0.25; PJM 2019 55524
CC_REGULAR −0.20, 2021 60356 −0.34, 2023 62949 −0.27). Reading the COD ramp's own mask covers every case by
construction, and it is what reproduces the census's SOCO 2023 figure (−2.83; the tag-only build gives −1.83). If
the desk wants the narrower dead-cohort-only reading, it is a one-function change.

## 3. Zero-LP before/after (`probe_live_sweep.py` → `W0-denominator-fix-2/sweep/`)

Each build is the keeper recipe at W0 posture (`build_fleet_census.rebuild_fleet`), three code trees on the same
data: **after** = this branch, **main** = 837556d2, **pre-#7047** = eec4eb5c. PJM runs with `pjm_da_virtual_bids`
off (input not in this checkout; downstream of the fleet). Hashes cover `availability`, `pmax`, `pmin`, `min_gen`.
"Rows offline all year" counts LP rows the COD ramp masks every month (they carry no energy either way).

| ISO | Year | Δ vs main (TWh) | Δ vs pre-#7047 (TWh) | ≥ 0.1 vs main | byte-identical vs main | changed arrays | rows offline all year | largest movers vs main (plant/group, TWh) |
|---|---|---|---|---|---|---|---|---|
| MISO | 2019 | -0.253 | -0.253 | **yes** | no | availability | 1 | 56104/CC_REGULAR -0.253 |
| MISO | 2020 | +0.000 | -0.033 |  | yes |  | 50 |  |
| MISO | 2021 | -0.370 | -0.913 | **yes** | no | availability | 69 | 963/COAL_BIT -0.310; 976/COAL_BIT -0.061 |
| MISO | 2022 | -1.390 | -1.390 | **yes** | no | availability, min_gen | 126 | 6085/COAL_BIT -1.173; 994/COAL_BIT -0.142; 963/COAL_BIT -0.063 |
| MISO | 2023 | -1.051 | -1.203 | **yes** | no | availability, min_gen | 157 | 6085/COAL_BIT -0.686; 994/COAL_BIT -0.293; 963/COAL_BIT -0.114 |
| MISO | 2024 | -3.146 | -4.410 | **yes** | no | availability, min_gen | 189 | 6085/COAL_BIT -1.094; 994/COAL_BIT -0.983; 6090/COAL_PRB -0.957 |
| MISO | 2025 | -4.267 | -4.267 | **yes** | no | availability, min_gen | 214 | 6085/COAL_BIT -1.751; 6090/COAL_PRB -1.000; 4041/COAL_PRB -0.666 |
| NWPP | 2019 | +0.000 | +0.000 |  | yes |  | 0 |  |
| NWPP | 2020 | +0.000 | -0.199 |  | yes |  | 0 |  |
| NWPP | 2021 | -1.600 | -1.600 | **yes** | no | availability | 10 | 3845/COAL_BIT -0.934; 6076/COAL_PRB -0.666 |
| NWPP | 2022 | -1.173 | -1.173 | **yes** | no | availability | 10 | 3845/COAL_BIT -0.766; 6076/COAL_PRB -0.406 |
| NWPP | 2023 | -0.962 | -0.962 | **yes** | no | availability | 11 | 3845/COAL_BIT -0.585; 6076/COAL_PRB -0.377 |
| NWPP | 2024 | -1.701 | -1.701 | **yes** | no | availability | 17 | 3845/COAL_BIT -0.953; 6076/COAL_PRB -0.748 |
| NWPP | 2025 | -1.611 | -1.611 | **yes** | no | availability | 23 | 3845/COAL_BIT -0.841; 6076/COAL_PRB -0.770 |
| PJM | 2019 | -0.195 | -0.195 | **yes** | no | availability, min_gen | 0 | 55524/CC_REGULAR -0.195 |
| PJM | 2020 | -0.001 | -0.097 |  | no | availability | 15 | 3149/COAL_BIT -0.001 |
| PJM | 2021 | -1.920 | -1.920 | **yes** | no | availability, min_gen | 31 | 2866/COAL_BIT -1.575; 60356/CC_REGULAR -0.338; 3149/COAL_BIT -0.007 |
| PJM | 2022 | -1.539 | -1.539 | **yes** | no | availability | 39 | 2866/COAL_BIT -1.536; 3149/COAL_BIT -0.004 |
| PJM | 2023 | -0.266 | -0.266 | **yes** | no | availability, min_gen | 38 | 62949/CC_REGULAR -0.266 |
| PJM | 2024 | +0.000 | +0.000 |  | yes |  | 53 |  |
| PJM | 2025 | +0.000 | +0.000 |  | yes |  | 54 |  |
| SOCO | 2019 | +0.000 | +0.000 |  | yes |  | 0 |  |
| SOCO | 2020 | +0.000 | +0.000 |  | yes |  | 5 |  |
| SOCO | 2021 | +0.000 | +0.000 |  | yes |  | 5 |  |
| SOCO | 2022 | +0.000 | -2.009 |  | yes |  | 5 |  |
| SOCO | 2023 | -2.828 | -2.828 | **yes** | no | availability | 14 | 6257/COAL_PRB -1.828; 3/CC_REGULAR -1.001 |
| SOCO | 2024 | -1.143 | -1.143 | **yes** | no | availability | 18 | 6257/COAL_PRB -1.143 |
| SOCO | 2025 | -1.620 | -1.620 | **yes** | no | availability | 18 | 6257/COAL_PRB -1.620 |
| NEISO | 2019 | +0.000 | +0.000 |  | yes |  | 0 |  |
| NEISO | 2020 | +0.000 | +0.000 |  | yes |  | 0 |  |
| NEISO | 2021 | +0.000 | +0.000 |  | yes |  | 8 |  |
| NEISO | 2022 | +0.000 | +0.000 |  | yes |  | 20 |  |
| NEISO | 2023 | +0.000 | +0.000 |  | yes |  | 20 |  |
| NEISO | 2024 | +0.000 | +0.000 |  | yes |  | 20 |  |
| NEISO | 2025 | +0.000 | +0.000 |  | yes |  | 20 |  |

### Against the census (it measured against pre-#7047 main)

| ISO | Census (TWh) | This build vs pre-#7047 (TWh) | |
|---|---|---|---|
| SOCO | 2022 −2.01, 2023 −2.83, 2024 −1.14, 2025 −1.62 | −2.009, −2.828, −1.143, −1.620 | exact |
| MISO | 2021 −0.88, 2022 −1.39, 2023 −1.17, 2024 −4.41, 2025 −4.27 | −0.913, −1.390, −1.203, −4.410, −4.267 | 2022/24/25 exact; 2021/23 within 0.04 |
| NWPP | 2020–25 −1.0 to −1.7 | 2020 −0.199; 2021–25 −1.600 / −1.173 / −0.962 / −1.701 / −1.611 | 2021–25 match |
| PJM | 2019 −1.47, 2020 −0.94, 2021 −1.92, 2022 −1.54, 2023 −0.27 | −0.195, −0.097, −1.920, −1.539, −0.266 | 2021–23 exact; **2019/20 do not reproduce** |
| NEISO | 0 | 0, all seven years byte-identical | exact |

**Open discrepancies (for the desk):**
- **NWPP 2020.** No cohort is dead in 2020: Centralia BW21 (`_r202012`) is online all year, and Colstrip 1–2
  (`_r202001`) are online in January, the #7047 in-year case (−0.199). So no live-roster move is owed in 2020; the
  census range reads as a span over 2021–25.
- **PJM 2019/2020.** This build has no row offline all year in PJM 2019. The only 2019 mover is 55524
  CC_REGULAR (−0.195, a mid-year build). In 2020 the offline-all-year bins 3149 and 3809 move −0.001 TWh, because
  almost no outage rows reach them. Without the census script I cannot tell what produced −1.47 / −0.94. Every
  2021–23 PJM figure reproduces exactly from the same build.
- MISO 2021/2023 differ by 0.03 TWh, consistent with the partly-in-service / mid-year-build rows the tag-only census
  would not see.

## 4. Byte-inertness

- **Byte-identical vs main** (all four arrays): NEISO 2019–2025, NWPP 2019–2020, SOCO 2019–2022, MISO 2020, PJM
  2024–2025.
- **Every ISO-year with no row offline all year and no partly-online bin that an outage reaches is byte-identical**:
  NEISO 2019–2020, NWPP 2019–2020, SOCO 2019. NEISO 2021–25 and SOCO 2020–22 carry rows offline all year
  (whole-plant retirees the LP keeps at zero), but no measured outage row is routed to their bins, so nothing moves.
- **NWPP 2019/2020 were NOT byte-identical before the 1.0 clip.** `cod_ramp.bin_online_fraction` returned
  `1 + 1 ulp` for 10761 CC_REGULAR, which emitted a monthly entry for a fully online bin (3e-16 per hour). The clip
  restores identity; `test_one_ulp_over_one_is_fully_online` pins it.
- `min_gen` moves in MISO 2022–25 and PJM 2019/2021/2023 are the zonal floor allocation following the moved
  availability, as in part 1 §4.
- Every move lowers available energy, as expected: the fix only ever shrinks a denominator.

## 5. Cache key

`SolveEpoch` **2026-10-02d**, `modes=("backcast",)`, `isos=("MISO", "NWPP", "PJM", "SOCO")` — the ISOs the sweep
moves. NEISO is excluded: its keeper recipe is byte-identical in all seven years. It is ledgered in
`results/cache.py`. Forecast and the default key do not move; ERCOT / CAISO / NYISO / SPP are untouched (companion
off or yielded).

## 6. Tests and checks

- `tests/unit/data/test_unit_outage_dispatched_bin_live_roster.py` (39; replaces the exit-year and live-sub-gate
  files). Trivial first: one plant, survivors A (600 MW) + cohort B (400 MW), 300 MW of A out all year.
  - A dead B is excluded all year (0.5 every hour, identical to no-B), with and without per-unit clip.
  - An in-year B is unchanged from #7047 (Jan 0.7, Feb–Dec equal to no-B, MW removed = MW out every hour).
  - An all-exit key gets 0.25 every hour, never an over-derate or a divide by 0.
  - Also covered: a mid-year new build, a future build, a fractional plant-level bin, the 1-ulp clip, the mask
    being the COD ramp's own, the accessor's gates, and the deleted field raising `TypeError`.
- `test_solve_surface.py`: epoch scope.
- Fast tier: 11,282 passed, 62 skipped, 3 xfailed. ruff clean.
- `check_mechanism_matrix.py --base origin/main` passes; the anchors this PR staled are repaired.
