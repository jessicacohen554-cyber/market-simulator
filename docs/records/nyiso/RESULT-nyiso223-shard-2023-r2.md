# RESULT — nyiso-223 shard `nyiso223-y2023-r2` (NYISO, 2023)

**Arm:** `nyiso_hub_gap_month_level=true` replayed over keeper `nyiso_fuelvintage_A`.
**Bundle:** `results/calibration/nyiso223_gapfill_2023/` (gitignored, local disk only — rule 31 `[R-RETAIN]`: **not deleted**).
**Supersedes:** `docs/RESULT-nyiso223-shard-2023.md` on branch `claude/nyiso223-y2023`, which is the
first 2023 shard's **STOPPED** report (blocked on an unbuilt `data/clean` tree, no solve artifact).
This relaunch carries the solve. Both docs are kept — that one records the blocker, this one the result.

**Base SHA:** `ce4779ecd62db3c732e0d0cd7b910b80bc23ed99` (verified; no pull/rebase).
**Control:** the committed keeper bundle `results/calibration/nyiso_fuelvintage_A/`, year 2023 (rule 29 `[R-SCREEN]` (b), G-CTRL form 4). No control solve spent.

## 0. Gates

**Hard stops** — all pass: HEAD SHA exact; `nyiso_fuelvintage_A/meta.json` `iso == NYISO`; `grep -c nyiso_hub_gap_month_level scenarios.py` = 4.

**Clean-tree build** — the two curations named in the setup were sufficient. The solve named **no third missing datatype**; the iterate-loop was not needed.

**Pre-solve gate** — exact match to expectation:

| quantity | off | on |
|---|---|---|
| annual mean hub gas ($/MMBtu) | 3.3566 | 3.3566 |
| Dec 22–31 mean | 3.919 | **3.683** |
| hours moved | — | **4416** |

Dec 22–31 moves **down**, i.e. against the price residual, as pre-registered.

**Post-solve signature** — exact match: `nyiso_hub_gap_month_level` **true**; `offer_curve_by_group.CC_REGULAR.peak` **2.25**, `.pct_peaking` **8.0**; `nyiso_gas_commitment_bridge` **true**; `nyiso_dynamic_reserve_requirements` **true**; `iso` NYISO; years `[2023]`. Solve exit 0.

**Not computed, by design:** the bundle carries no `metrics.json` / `calibration_attestation.json` — scoring needs the `lmp` clean partition, which is deliberately not curated here (its `regenerate_clean.py` leg fails on an unrelated CAISO `KeyError: 'MGHG'`). **C3a/C3b are therefore unavailable from this shard.** Scoring is the parent's job. `legitimacy_diagnostics.json` **is** present and is reported in full below.

---

## 1. Model annual mean LMP (5 load zones: Capital_Hudson, Long_Island, Lower_Hudson, NYC, Upstate_West)

| basis | keeper 2023 | **arm 2023** | Δ |
|---|---|---|---|
| **load-weighted, equal-hour mean of the hourly LW ISO price** | 32.3557 | **32.3600** | +0.0043 |
| equal-zone-weight, equal-hour mean | 34.1255 | **34.1307** | +0.0052 |
| fully energy-weighted (Σ p·q / Σ q) | 33.6503 | **33.6521** | +0.0018 |

Per zone (equal-hour mean $/MWh, arm), with the zone load used for the weighting:

| zone | keeper | **arm** | Δ | load TWh |
|---|---|---|---|---|
| Capital_Hudson | 35.6514 | **35.6580** | +0.0066 | 20.1088 |
| Long_Island | 37.6550 | **37.6647** | +0.0097 | 19.3840 |
| Lower_Hudson | 36.2548 | **36.2615** | +0.0067 | 8.0973 |
| NYC | 36.5828 | **36.5892** | +0.0064 | 48.2844 |
| Upstate_West | 24.4835 | **24.4800** | −0.0035 | 51.1744 |

Slack and dump are **0.0 MWh** in both runs.

**Price footprint:** 4,610 of 8,760 hours have a changed zonal price (>1e-6); max |zone price delta| **8.0559 $/MWh**; mean signed LW delta **+0.0043**. The 4,610 price hours sit just above the 4,416 fuel hours the gate moved — the extra ~194 come through commitment/storage coupling, i.e. the footprint is confined to the rows the mechanism claims.

## 2. Model monthly means — load-weighted ISO price ($/MWh)

| month | keeper | **arm** | Δ |
|---|---|---|---|
| Jan | 39.8617 | **39.8773** | +0.0156 |
| Feb | 37.0009 | **37.0009** | +0.0000 |
| Mar | 34.1182 | **34.1166** | −0.0016 |
| Apr | 29.0149 | **29.0794** | +0.0645 |
| May | 19.4376 | **19.4376** | +0.0000 |
| Jun | 29.9590 | **29.9587** | −0.0003 |
| Jul | 40.1536 | **40.0470** | −0.1066 |
| Aug | 30.4048 | **30.4029** | −0.0019 |
| Sep | 33.8680 | **33.9061** | +0.0381 |
| Oct | 27.3391 | **27.3496** | +0.0105 |
| Nov | 32.0992 | **32.0971** | −0.0021 |
| Dec | 35.3167 | **35.3543** | +0.0376 |

Feb and May are byte-identical — the gap fill has no unpriced days to fill in those months.

## 3. C3c (model side only — no actuals available in this shard)

| quantity | keeper 2023 | **arm 2023** |
|---|---|---|
| hours load-weighted ISO price > $300 | 0 | **0** |
| hours **any zone** > $300 | 2 | **2** |
| **model maximum zonal price** | 326.4235 (Long_Island) | **326.4235 (Long_Island)** |
| max load-weighted ISO price | 213.8595 | **213.3737** |
| hours LW ISO price > $100 | 30 | **30** |
| hours any zone > $1000 | 0 | **0** |

Reference from the prompt: keeper 2023 = 2 h, max $326.4, **actual 10 h**. The arm reproduces the keeper exactly on both — the tail is untouched, so C3c does not move.

## 4. C1 per-class TWh — TWO BASES, reported separately

**CRITICAL:** the two bases differ materially and are **not** interchangeable. Difference like against like.

### 4a. Basis A — `hourly/class_hourly_2023.parquet`, `pass == P1` (P1 grid-delivered)

| class | keeper | **arm** | Δ |
|---|---|---|---|
| CC_REGULAR | 33.79867 | **33.80822** | +0.00956 |
| nuclear | 27.48714 | **27.48714** | 0.00000 |
| hydro | 26.61577 | **26.61577** | 0.00000 |
| import | 23.33567 | **23.33255** | −0.00312 |
| CC_CHP | 15.90567 | **15.90444** | −0.00124 |
| ST_GAS | 9.80968 | **9.79686** | −0.01282 |
| wind | 4.59072 | **4.59072** | 0.00000 |
| OTHER | 2.19733 | **2.19733** | 0.00000 |
| CT_CHP | 1.53500 | **1.53571** | +0.00071 |
| ST_CHP | 1.36862 | **1.37322** | +0.00460 |
| biomass | 0.83953 | **0.83953** | 0.00000 |
| CT_PEAKER | 0.39666 | **0.39731** | +0.00065 |
| solar | 0.27982 | **0.27982** | 0.00000 |
| oil | 0.14973 | **0.14973** | 0.00000 |
| COAL_BIT | 0.00000 | **0.00000** | 0.00000 |
| COAL_PRB | 0.00000 | **0.00000** | 0.00000 |
| **total** | **148.3100** | **148.3083** | −0.0017 |

### 4b. Basis B — D-2 `class_total_twh` (from `legitimacy_diagnostics.json`)

This is the column the D-2/C8 forced shares are computed against. **It is a different basis** — the sibling shard's ~1 TWh CC_REGULAR observation is confirmed and is in fact larger:

| class | basis A (class_hourly) | **basis B (D-2 `class_total_twh`)** | B − A |
|---|---|---|---|
| CC_REGULAR | 33.80822 | **31.9380** | **−1.8702** |
| hydro | 26.61577 | **26.6158** | +0.0000 |
| CC_CHP | 15.90444 | **15.9315** | +0.0271 |
| ST_GAS | 9.79686 | **11.8377** | **+2.0408** |
| CT_CHP | 1.53571 | **2.8480** | **+1.3123** |
| ST_CHP | 1.37322 | **0.0679** | **−1.3053** |
| CT_PEAKER | 0.39731 | **0.3419** | −0.0554 |

The pattern is a **class-mapping difference, not a metering one**: CT_CHP/ST_CHP trade +1.3123/−1.3053 (near-exact offset) and CC_REGULAR/ST_GAS trade −1.8702/+2.0408. Basis B comes from the D-2 `run_year(fleet_only=True)` floor reconstruction; basis A is the LP's own dispatch sidecar. **Any C1 comparison the parent makes must state which basis it used**, and must not mix the two across ISOs or years.

D-2 also carries an un-classed pair keyed to a 35.3716 TWh pool: `nuclear_mustrun` 27.4871 (0.7771) and `firm_import` 7.8840 (0.2229).

## 5. C8 — forced share by class, with the per-mechanism breakdown (arm, 2023)

D-2 summary verdicts (`d2_merchant_max_share` 0.30, `d2_peaker_max_share` 0.15):

| class | forced TWh | class_total TWh | forced share | limit | verdict |
|---|---|---|---|---|---|
| CC_REGULAR | 0.3588 | 31.9380 | **0.0112** | 0.30 | pass |
| CT_PEAKER | 0.0000 | 0.3419 | **0.0000** | 0.15 | pass |
| ST_GAS | 1.9116 | 11.8377 | **0.1615** | 0.30 | pass |
| hydro | 0.0000 | 26.6158 | **0.0000** | 0.30 | pass |

**No class is over budget.** All four rows are flagged `lower_bound: true` (the P2 RA must-offer bridge floor is not included in the `fleet_only` reconstruction), `immaterial: false`.

Mechanism breakdown (D-2 rows, arm vs keeper forced TWh):

| class | mechanism | arm forced TWh | share of class | keeper forced TWh |
|---|---|---|---|---|
| — (pool 35.3716) | nuclear_mustrun | 27.4871 | 0.7771 | 27.4871 |
| — (pool 35.3716) | firm_import | 7.8840 | 0.2229 | 7.8840 |
| CC_CHP | chp_steam | 0.0137 | 0.0009 | 0.0136 |
| **CC_REGULAR** | **nyiso_gas_commitment_bridge** | **0.3588** | **0.0112** | 0.3549 |
| CT_CHP | chp_steam | 0.0003 | 0.0001 | 0.0002 |
| ST_CHP | chp_steam | 0.0073 | 0.1081 | 0.0078 |
| **ST_GAS** | **reliability_floor** | **1.9044** | **0.1609** | 1.9019 |
| ST_GAS | nyiso_gas_commitment_bridge | 0.0073 | 0.0006 | 0.0070 |
| hydro | hydro_min_flow | 7.7254 | 0.2903 | 7.7305 |

Exempt classes (`d2_exempt_classes`): CC_CHP, CT_CHP, ST_CHP, nuclear.

## 6. December equal-hour mean model price — split

Load-weighted ISO price, equal-hour mean over the sub-period:

| window | keeper | **arm** | Δ |
|---|---|---|---|
| **Dec 1–21** | 35.1934 | **35.7358** | **+0.5424** |
| **Dec 22–31** | 35.5754 | **34.5531** | **−1.0223** |
| Dec full month | 35.3167 | **35.3543** | +0.0376 |

Equal-zone-weight basis: Dec 1–21 35.6641 → **36.2071**; Dec 22–31 35.9609 → **34.9152**.

Per zone, equal-hour mean (keeper → arm):

| zone | Dec 1–21 | Dec 22–31 |
|---|---|---|
| Capital_Hudson | 35.5344 → **36.0668** | 35.7783 → **34.7222** |
| Long_Island | 37.0846 → **37.6460** | 37.2100 → **36.1129** |
| Lower_Hudson | 36.0540 → **36.5941** | 36.3014 → **35.2299** |
| NYC | 36.2546 → **36.7980** | 36.5050 → **35.4268** |
| Upstate_West | 33.3931 → **33.9308** | 34.0096 → **33.0843** |

Keeper 2023 has no published Dec split; both windows are reported raw. The direction is uniform across all five zones in both windows, and matches the fuel-side gate: Dec 22–31 gas fell 3.919 → 3.683 and Dec 22–31 price fell in every zone.

## 7. Legitimacy diagnostics gate

| diagnostic | arm | keeper |
|---|---|---|
| D-1 diurnal shape | **PASS** | PASS |
| D-2 forced-energy attribution | **PASS** | PASS |
| **D-4 off-window binding** | **FAIL** | **FAIL** |
| D-5 forecast/backcast parity | **PASS** | PASS |
| D-9 overlay quarantine | **PASS** | PASS |
| D-10 free-class-only rescore | **PASS** | PASS |

Gates: `d1_min_profile_r` 0.8, `d1_min_cv_ratio` 0.5, `d1_offpeak_last_hour` 14, `d1_gated_classes` [CT_PEAKER, ST_GAS, COAL*], `d2_peaker_max_share` 0.15, `d2_merchant_max_share` 0.30, `d4_max_offwindow_share` 0.05.

### D-4 failing rows (arm, 2023) — **both are pre-existing in the keeper, neither is induced by the arm**

| floor | plant | floored TWh | binding hours | measured median MW | measured zero share | verdict |
|---|---|---|---|---|---|---|
| reliability_floor × ST_GAS | **2480** | 0.0015 | 157 | 0.000 | 1.000 | **FAIL** |
| reliability_floor × ST_GAS | **8906** | 0.2404 | 5,562 | 0.000 | 0.5097 | **FAIL** |

Keeper 2023, same two plants: 2480 — 0.0015 TWh / 157 h / median 0.000 / zero-share 1.000; 8906 — 0.2397 TWh / 5,551 h / median 0.000 / zero-share 0.5102. The arm moves 8906 by +0.0007 TWh and +11 binding hours. **The arm introduces no new D-4 failure and clears none.** (The keeper's other three D-4 failures are 2024 rows and out of this shard's scope.)

Both are per-unit **conduct-rider** failures, not window failures: every `check == "window"` row passes at `offwindow_share` 0.0000 — chp_steam, firm_import, reliability_floor × ST_GAS, and nyiso_gas_commitment_bridge × CC_REGULAR all bind entirely inside their declared `h0-23` window.

D-1 rows (arm, 2023), gated classes bolded:

| class | profile_r | model offpeak cv | actual offpeak cv | cv_ratio | gated | verdict |
|---|---|---|---|---|---|---|
| CC_CHP | 0.954 | 0.088 | 0.114 | 0.77 | no | pass |
| CC_REGULAR | 0.962 | 0.070 | 0.073 | 0.96 | no | pass |
| CT_CHP | 0.338 | 0.395 | 0.065 | 6.039 | no | pass |
| **CT_PEAKER** | 0.962 | 1.249 | 0.688 | 1.816 | **yes** | pass |
| ST_CHP | 0.404 | 0.235 | 0.106 | 2.230 | no | pass |
| **ST_GAS** | 0.963 | 0.247 | 0.200 | 1.231 | **yes** | pass |

## 8. Did class energy move materially vs the keeper?

**No.** Every class delta is ≤ 0.013 TWh on basis A, against a 148.31 TWh total — the largest is ST_GAS at **−0.0128 TWh (−0.13 % of that class, −0.0086 % of ISO load)**, followed by CC_REGULAR **+0.0096 TWh (+0.028 %)**. Total P1 grid-delivered energy moves −0.0017 TWh (−0.001 %). Six classes (nuclear, hydro, wind, OTHER, biomass, solar, oil, COAL_*) are byte-identical.

The signed pattern is the one the mechanism's arithmetic implies: gas gets cheaper on the filled unpriced days in some months and dearer in others, so **ST_GAS gives up 0.0128 TWh to CC_REGULAR (+0.0096) plus small CHP/peaker pickups**, and imports fall 0.0031 TWh. Direction and order of magnitude are consistent with a fuel-price re-shuffle inside the merit order, not a level shift: the **annual** mean price moves +0.0043 $/MWh (+0.013 %) while individual hours move up to 8.06 $/MWh.

**Summary for the parent:** the arm is a **within-year redistribution**, essentially neutral on the annual price and on class energy, with its only material signature in the December split (Dec 22–31 −1.02, Dec 1–21 +0.54 $/MWh). The C3c tail is unchanged (2 h > $300, max $326.4235 — identical to the keeper). The D-4 failure set is unchanged.

---

*Shard `nyiso223-y2023-r2` for session nyiso-223. No `src/` or `scripts/` edit, no registration, no result deleted, no PR.*
