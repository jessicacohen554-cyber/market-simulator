# RESULT — miso-271: the R-MISO CC_REGULAR shortfall is root-caused, and the fix (retire the statistical WEFOR stack) restores the train tier to CALIBRATED. RECOMMENDED for promotion; the promotion edit was refused by the session permission policy.

```
LANE     : miso-271 (off-queue, owner charter)
PREREG   : docs/PRECOMMIT-miso271-cc-regular-shortfall-wefor-stack-2026-09-25.md (pinned 40d995ba)
KEEPER   : 2026-09-24-rmiso-arm-b-mid (rmiso_b_span, 2019-2025) — unchanged, see §6
RUN      : 2026-09-25-miso-271-wefor-stack (results/calibration/miso271_span, 2019-2025), registered
DELTA    : wefor_residual=0.0, wefor_residual_groups=[CC_REGULAR, ST_CHP, ST_GAS]; multipliers unchanged; DOF +0
VERDICT  : train 2023-2025 NOT-YET -> CALIBRATED; full span NOT-YET (C3a 2019/2020, C3b 2021 remain)
```

## 1. Root cause (phase 0, zero LP; PRECOMMIT §2)

The R-MISO drop in available CC_REGULAR energy (−9.2 / −9.1 / −8.0 TWh in 2021 / 2022 / 2023) had two causes of roughly equal size. The measured heat rates contributed nothing to it.

1. **Vintage: −4.8 / −4.7 / −4.4 TWh, almost all Edwardsport (1004).** Edwardsport is a coal-gasification combined-cycle plant (IGCC).
   - Its CTs are syngas-primary in every EIA-860 vintage 2019–2024; only the canonical file lists them as NG-primary. The old keeper therefore carried 481 MW of **phantom gas-priced CC** on top of the plant's 555 MW block rating.
   - Magnolia Power (−679 MW) had zero availability in both runs: its first generation was Dec 2025.
   - Cottonwood's move is the vintage's year-matched ratings, which is correct.
   - This part of the "regression" is the keeper losing a phantom, not the model getting worse (rule 14).
2. **Short-gas windows stacked on the statistical WEFOR: −4.6 / −4.5 / −3.8 TWh.** R-MISO armed the measured 1–4.9-day gas windows without retiring the statistical forced-outage term, and that term represents exactly those sub-5-day outages (`wefor_residual`'s own contract). That is a rule 19 stack. The term still removed 7.6–10.1 TWh/yr of CC_REGULAR availability.

**Identification.** The frozen caiso-187 formula, `residual = max(0, W − X)`, was applied to MISO's own fleet using the LP's own overlay removal as X. It returns **0 in every year 2019–2025** for CC_REGULAR, ST_GAS and ST_CHP. CC_CHP is excluded fail-closed (2023 residual 0.0036). Coal is out of scope because its short family is baseload-only.

## 2. Solves

- **Shards:** 7 arm legs (2019–2025) plus 6 same-SHA controls (2019–2024). G-DRIFT found two LIVE hunks, COAL-SUB and the R-NEISO mid-vintage window, so the controls were earned under rule 29(b). 2025 uses the keeper as its control (form 4).
- **Pin:** every leg is pinned to `40d995ba`. Every leg passed the shard self-check on the parent's fetched bytes: recipe = keeper + exactly the two fields, pinned inputs, and `dispatch/<Y>_P1` present.

| year | arm − control: CC_REGULAR | CT_PEAKER | import | coal (all) | LW price $/MWh | slack GWh (ctl → arm) |
|---|---:|---:|---:|---:|---:|---|
| 2019 | +4.31 | −0.16 | −0.67 | −3.00 | −0.45 | 0 → 0 |
| 2020 | +4.07 | −0.72 | −0.78 | −2.42 | −0.49 | 0 → 0 |
| 2021 | +2.65 | −0.74 | −0.72 | −0.90 | −0.98 | 0 → 0 |
| 2022 | +2.97 | −0.96 | −1.41 | −0.04 | −1.51 | 0 → 0 |
| 2023 | +5.48 | −2.23 | −1.81 | −1.67 | −1.39 | 2.8 → 0.0 |
| 2024 | +6.13 | −2.89 | −1.81 | −2.43 | −0.92 | 33.5 → 15.5 |
| 2025 (vs keeper) | +5.83 | −3.00 | −1.75 | −1.14 | −2.06 | 0 → 0 |

Control − keeper differs only by the declared LIVE drift: the COAL-SUB coal relabel and the 2023/24 R-NEISO retirees.

## 3. Structural gates (PRECOMMIT §6)

- **S-1 recipe: PASS** on all 13 legs.
- **S-2 single delta: PASS.** On the fleet-only rebuild, availability moves only for the relieved gas classes; pmax and heat rate are byte-identical.
- **S-3 slack: PASS.** Arm slack is ≤ control slack every year, and the 2023 Max Gen slack disappears.

## 4. Gates (live scorer, regenerated bench parts; keeper re-scored on the same parts)

| crit | year | keeper rmiso-arm-b-mid | miso-271 |
|---|---|---|---|
| C1 CC_REGULAR | 2021 | FAIL −10.37 TWh | PASS −7.69 |
| C1 CC_REGULAR | 2022 | FAIL −9.75 | PASS −6.77 |
| C1 CC_REGULAR | 2023 | FAIL −10.38 | PASS −5.06 |
| C3a | 2019 | FAIL +12.5 % | FAIL +10.8 % |
| C3a | 2020 | FAIL +13.0 % | FAIL +10.9 % |
| C3a | 2023 | FAIL +10.0 % | PASS |
| C3b | 2021 | FAIL 0.316 | FAIL 0.304 |
| C2, C4, C6, C8 | all | PASS | PASS |
| **train 2023–2025** | | **NOT-YET** | **CALIBRATED** |
| full span | | NOT-YET (C1, C3a, C3b) | NOT-YET (C3a, C3b) |

The direction hazard was declared in the PRECOMMIT: the fix lowers price and raises CC. The basis is rule 19, not these numbers.

## 5. Routed, not fixed

1. **Edwardsport IGCC block phantom:** 481 MW of coal in every year, plus the NG share the benchmark books as CC_REGULAR.
2. **The coal statistical-WEFOR stack:** the same defect class; short-coal covers baseload units only.
3. **C3a 2019/2020 (+10.8/+10.9 %) and C3b 2021** remain; see miso-269/270 (overnight coal body, Feb-2021 gas array).
4. **Status only, not this lane's:** the forecast gate-(a) row still names miso-268; the cross-ISO `mid_vintage_exit_carry` pairing; the `filter_revealed_outages` partial-derate defect; the std-unitroute / short-coal non-reproduction.

## 6. Promotion

**Recommended.** Every structural gate holds, the fix removes a documented double count, and the train tier returns to CALIBRATED.

The owner asked ("If so plz promote"). The session's first promotion step, editing `frontend/data/backcast/keepers/MISO.json`, **was refused by the session permission policy** ("Modify Shared Resources"), so the promotion is **not executed**. Also not done:
- the rule 35 prune of `rmiso_b_span`;
- `build_status.py --iso MISO`;
- the matrix keeper stamp.

The matrix cell `wefor_residual` is updated to **O** (tested, recommended, promotion pending).

**Where the bytes are:** the registered composite (slim bundle, `hourly/` sidecars, attestation, diagnostics, registry sidecar, run payload) lands on `main` with this lane's PR, so promoting from there costs **zero re-solves**. The per-year legs with `dispatch/` are on this session's local disk only, gitignored; shard SHAs are in the attestation as provenance.

All 13 shards are archived.
