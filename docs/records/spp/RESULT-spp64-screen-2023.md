# RESULT — SPP-64 SCREEN shard (2023). `st_gas_mustrun_per_plant` on SPP's ST_GAS fleet.

**Lane** SPP-64 SCREEN · **Branch** `claude/spp64-screen-2023b` ·
**Pin** `967db1ff63049b18d38d2de36838593054b6bed3` (verified at start; no fetch/pull/rebase before the
final push) · **Charter** `docs/handoffs/PRECOMMIT-spp-64-stgas-selfcommit-2026-09-10.md` §6 —
**no bar in it was re-cut by this shard.**

**VERDICT: PROCEED TO SPAN.** All six §6 STOP gates PASS. One material adverse finding that is **not**
a §6 gate is reported in §4 and belongs to the span's decision, not to this screen.

## 1. The solve

Exactly one LP, one year, as chartered:

```
python3 scripts/replay_keeper.py results/calibration/spp62_span \
  --years 2023 --out-dir results/calibration/spp64_screen_2023 \
  --set st_gas_mustrun_per_plant=true
```

P0 cold 85.076 s (76,749 simplex iters), P1 warm 42.029 s (15,494). Bundle
`results/calibration/spp64_screen_2023/` is **gitignored** (`.gitignore:1906`,
`results/calibration/spp64_*/`) and `git status` is clean of it. **Nothing was deleted**
(rule 31 `[R-RETAIN]`). Control = the keeper's **committed** bundle `results/calibration/spp62_span`,
**differenced, never re-solved** (rule 29(b) form 4).

## 2. §6 GATE TABLE — FILLED. Bar beside measured value.

| gate | STOP bar | measured | verdict |
|---|---|---|---|
| **G-1** config identity & liveness | any mismatch | `st_gas_mustrun_per_plant` **True**; `st_gas_mustrun_p25_level` **False**; **10** fossil classes at 0.93 on all four bands and `offer_curve_by_group` **byte-identical to the keeper**; `coal_supply_SPP.csv` **32** lines; `^6193,prb,` count **1** | **PASS** |
| **G-2** reach | ΔST_GAS outside **[+2.0, +7.5] TWh** | **+2.3314 TWh** (gross class series 7.0867 → 9.4181) | **PASS** |
| **G-3** allocation identity | **< 0.80** of the increase inside the floored-hour set | **1.0002** (inside +2.3319 of +2.3314 TWh; mean Δ **+279.23 MW** inside vs **−1.07 MW** outside) | **PASS** |
| **G-4** no new forcing | dump > 0, or any non-ST_GAS class gains min_gen, or slack **> 370.102 MWh** | dump **0.000 MWh**; slack **0.000 MWh**; min_gen gained by **ST_GAS only** (+3.8720 TWh) — every other class byte-identical | **PASS** |
| **G-5** no non-target regression | any **PASS → FAIL** | C3a **25.65 → 25.38** (−1.05 % vs keeper; error +2.1 % → **+1.0 %** vs actual, bar ±10 %); C3b **0.172 → 0.173** (bar ≤ 0.20); C2 **gas PASS→PASS, coal PASS→PASS**. **Zero PASS → FAIL** | **PASS** |
| **G-6** displacement | any in-band C1 class leaves the ±8.00 TWh band | **NONE.** All seven non-target C1 rows stay PASS; largest move CC_REGULAR −3.569 → **−4.127** TWh (headroom 3.87) | **PASS** |

### Instrument validation (done BEFORE either was trusted on the arm)

- **G-5**: `scripts/lib/spp63_g5.py` re-scored the **registered keeper** and reproduced the scorer
  exactly — 2023 **C3a 25.65 / C3b 0.172**, 2024 25.79 / 0.172, 2025 29.23 / 0.167.
- **G-6**: the C1 instrument (`apply_other_fossil_scoring` on the arm's own dispatch frame → the
  scorer's own `score_fuelmix`) reproduced the keeper's six known 2023 deltas to three decimals —
  CC_REGULAR **−3.569**, CT_PEAKER **+2.407**, COAL_PRB **+1.598**, COAL_LIGNITE **−2.103**,
  CC_CHP **+0.116**, ST_CHP **−0.230** — against the keeper's committed run payload.
  The OTHER_FOSSIL split is conservative (Σ gmModel − Σ raw = −0.0001 TWh) and the arm's raw
  dispatch frame equals its `class_hourly` sidecar class-for-class.
- **G-4**: the control's min_gen came from a **zero-LP** `run_year(fleet_only=True)` rebuild of the
  keeper's own 2023 recipe (`scripts/lib/bundle_fleet.py`), not from prose.

### G-1, the three non-target config fields that differ

`nyiso_total_east_cutset_ttc` `None→False`, `spp_curtailment_ceiling` `None→False`,
`spp_curtail_depth_wind` `None→0.288137`. These are fields **added since the keeper was solved**,
materializing at their declared defaults — exactly PRECOMMIT §7's G-DRIFT INERT hunks. Re-verified
here at the read site: `runner.py:3232` gates the depth read behind
`if iso == "SPP" and getattr(config, "spp_curtailment_ceiling", False)`, which is **False**.
`st_gas_mustrun_per_plant` is the **only** live field that moves.

## 3. FULL CLASS-DELTA TABLE vs the keeper

**(a) Gross class series** (`hourly/class_hourly_2023.parquet`, P1, TWh):

| class | keeper | ARM | Δ |
|---|---|---|---|
| **ST_GAS** | **7.0867** | **9.4181** | **+2.3314** |
| CC_REGULAR | 42.4877 | 41.9243 | −0.5633 |
| CT_PEAKER | 16.2967 | 15.7407 | −0.5560 |
| COAL_PRB | 66.8769 | 65.8052 | −1.0717 |
| COAL_LIGNITE | 7.2935 | 7.1926 | −0.1009 |
| CC_CHP | 1.8535 | 1.8477 | −0.0058 |
| CT_CHP | 1.2108 | 1.2034 | −0.0075 |
| ST_CHP | 0.3027 | 0.2926 | −0.0101 |
| wind | 113.7572 | 113.7422 | −0.0150 |
| solar | 0.5876 | 0.5875 | −0.0001 |
| hydro | 8.3441 | 8.3441 | 0.0000 |
| nuclear | 16.9270 | 16.9270 | 0.0000 |
| biomass | 1.1014 | 1.1014 | 0.0000 |
| OTHER | 0.5072 | 0.5072 | 0.0000 |
| oil | 0.0000 | 0.0000 | 0.0000 |
| **TOTAL** | **284.6329** | **284.6338** | **+0.0009** |

The 2.3314 TWh is paid for almost entirely by COAL_PRB (−1.07), CC_REGULAR (−0.56) and CT_PEAKER
(−0.56) — **not** by curtailing renewables (wind −0.0150 TWh, 0.013 %).

**(b) Scored C1 basis** (grid-delivered `gmModel`, the scorer's own `score_fuelmix`, band ±8.00 TWh
& ±3 pp):

| class | actual | keeper model | keeper Δ | keeper | ARM model | ARM Δ | ARM |
|---|---|---|---|---|---|---|---|
| **ST_GAS** *(target)* | 15.020 | 6.640 | **−8.380** | FAIL | 8.986 | **−6.034** | PASS |
| CC_REGULAR | 45.694 | 42.125 | −3.569 | PASS | 41.567 | −4.127 | PASS |
| CT_PEAKER | 13.214 | 15.621 | +2.407 | PASS | 15.095 | +1.881 | PASS |
| COAL_PRB | 65.279 | 66.877 | +1.598 | PASS | 65.805 | +0.526 | PASS |
| COAL_LIGNITE | 9.396 | 7.293 | −2.103 | PASS | 7.193 | −2.203 | PASS |
| CC_CHP | 1.737 | 1.853 | +0.116 | PASS | 1.848 | +0.111 | PASS |
| ST_CHP | 0.533 | 0.303 | −0.230 | PASS | 0.293 | −0.240 | PASS |
| COAL_BIT | 0.035 | 0.000 | −0.035 | PASS | 0.000 | −0.035 | PASS |

**The target row is reported at full magnitude and is NOT a gate in either direction** (charter §6).
ST_GAS **−8.380 → −6.034 TWh**, share_pp −2.94 → −2.12, crossing FAIL → PASS. That crossing did not
enter any gate above and did not decide this verdict; the verdict rests on G-1…G-6, none of which
reads it.

## 4. REPORTED, NON-GATING — and this is the screen's most important adverse finding

**D-4 unit-conduct rider: 4 FAILs, and the keeper had none.** The arm's own committed
`legitimacy_diagnostics.json` turns `D4.passed` **True → False**, which is why the run prints
"legitimacy diagnostics gate FAIL". The rows:

| plant | floored TWh | share of forced energy | binding hours | measured median MW in those hours | share of them at zero |
|---|---|---|---|---|---|
| 1230 | 0.0108 | 0.46 % | 1,251 | 0.000 | 70.2 % |
| 1235 | 0.0112 | 0.48 % | 1,106 | 0.000 | 62.3 % |
| 1271 | 0.0048 | 0.21 % | 830 | 0.000 | 69.8 % |
| 3008 | 0.0327 | 1.41 % | 2,016 | 0.000 | 53.6 % |
| **total** | **0.0595** | **2.56 %** | | | |

15 of the 19 ST_GAS unit-conduct rows pass. But on these four plants the meter says the unit was
**offline in the majority of the hours the floor asserts it must be online** — which is the
rule 17 `[R-FLOOR-WINDOW]` signature ("a floor binding in hours its own driver evidence says the
class is offline is a bug by definition"), at the per-unit grain. It is **not** a §6 gate and this
shard will not fail the arm on a bar the charter did not pre-register; it is handed to the span.

**Everything else in the legitimacy artifact moved the other way, and two of the three risks the
PRECOMMIT pre-declared did NOT materialise in 2023:**

- **D-2 forced share (rule 20 `[R-FORCED-BUDGET]`, PRECOMMIT's "KNOWN OPEN RISK")**:
  `st_gas_mustrun_per_plant × ST_GAS` forces **2.3238 TWh = 0.1962** of the class total —
  **under** the `d2_merchant_max_share` **0.30** cap. `D2.passed = True`. The budget question the
  charter routed to the span does not bind in 2023.
- **D-1 diurnal shape (PRECOMMIT's "genuinely uncertain leg")**: ST_GAS `profile_r`
  **0.996 → 0.997** (bar ≥ 0.80), `cv_ratio` **2.161 → 2.117** (bar ≥ 0.50). Passes, and barely
  moves. `D1.passed = True`.
- **D-4 window leg**: `offwindow_share` **0.0000** — self-windowing at h0-23 exactly as predicted.

**C3c is untouched**, as the charter said it would be: **0 system-hours above $200** in both keeper
and arm, against 42 actual in 2023.

## 5. Prices, slack, dump

| | keeper | ARM | Δ |
|---|---|---|---|
| load-weighted level | 25.653 $/MWh | 25.382 $/MWh | −0.271 |
| C3a (scorer) vs actual 25.13 | 25.65 (+2.1 %) | 25.38 (**+1.0 %**) | error halves |
| C3b monthly NRMSE | 0.172 | 0.173 | +0.001 |
| zone-hours < $0 (of 17,520) | 423 (2.41 %) | 433 (2.47 %) | +10 |
| system-hours < $0 (of 8,760) | 229 | 234 | +5 |
| zone-hours > $200 | 0 | 0 | 0 |
| **system-hours > $200** | **0** | **0** | **0** |
| system price max / min | 55.45 / −26.00 | 55.45 / −26.00 | 0 |
| system p99 | 40.56 | 40.34 | −0.22 |
| **slack** | **0.000 MWh** | **0.000 MWh** | 0 |
| **dump** | **0.000 MWh** | **0.000 MWh** | 0 |

## 6. Honest limits of this screen

- **G-3's floored-hour set is wide.** The union of 21 plants' own top-`online_frac` windows covers
  **8,351 of 8,760 hours (95.33 %)**, so passing at 1.0002 is a weak discriminator by construction.
  Two sharper statistics, **reported and not substituted for the chartered bar**: `corr(Δ_t, floor_t
  − control_t) = 0.8506`; and the mechanism's **own** D-2 forced energy **2.3238 TWh** against the
  realised class increase **2.3314 TWh** — a ratio of **0.9967**, i.e. essentially all of the class
  increase is the mechanism's own forced energy, measured at the mechanism's grain rather than the
  class's.
- **G-2 lands near its lower bound** (+2.3314 against a floor of +2.0). The pre-solve arithmetic
  (PRECOMMIT §3's 3.8701 TWh of min_gen; §5's 4.894 TWh forced increment) over-predicts because the
  floor is clipped to `pmax × availability` and the model already dispatched some ST_GAS. The npz
  stamp confirms the floor placed **3.8720 TWh** — reproducing §3 to 0.05 % — of which 2.3238 TWh
  actually binds. **The bar was not re-cut.**
- This is a **screen**: it may kill an arm, never promote one. Nothing here is a determination, a
  keeper claim, or a skill claim. `[R-HOLDOUT]` was removed 2026-09-09, so 2023 is a year that has
  been iterated against; these are model-**selection** numbers.

## 7. VERDICT

**PROCEED TO SPAN** — six of six §6 STOP gates PASS, and no gate was re-cut. The span
(`--years 2023 2024 2025`, `results/calibration/spp64_span`) must adjudicate, per PRECOMMIT §6 and
§10: (i) the **D-4 unit-conduct rider** above, which the keeper did not carry; (ii) rule 20's
forced-budget across all three years (2023 clears it at 0.1962); (iii) D-1 across all three years.
