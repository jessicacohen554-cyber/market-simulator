# FINDING — pjm-171: **PJM 2021's C3a +10.8 % is the already-adjudicated flat-offer-stack defect read WITHOUT its usual offset, and no admissible lever closes it**

**Session** pjm-171 · **ISO** PJM · **Date** 2026-09-07
**Branch** `claude/pjm-backcast-2021-lmp-l6i8fo`
**Keeper UNCHANGED** `2026-08-15-pjm-162-inputclock`. **Nothing is promoted, nothing is registered.**
**PJM headline UNCHANGED: CALIBRATED** (rule 30(c) — a held-out year never downgrades the ISO).
**ZERO LP SOLVED.** Every number below is measured on committed artifacts or on a
`run_year(fleet_only=True)` reconstruction (rule 29 `[R-SCREEN]` phase 0).

---

## 1. RESULT

> **2021 is not a 2021 defect.** PJM's model over-prices the off-peak trough and under-prices
> the peak in *every* year 2021–2025, tuned and held-out alike. The annual mean lands inside
> the ±10 % C3a band in the tuned years **because the two errors cancel**, not because either
> is small. 2021 is the only year in the span whose scarcity tail is ≈ absent, so nothing
> cancels the trough surplus and the defect is read at full magnitude: **C3a +10.8 %**.
>
> **Consequence for the session's charter.** There is no lever that lowers 2021 without
> breaking a year that currently passes — including a **training** year. The two mechanisms
> that would decompress the distribution are already adjudicated for PJM:
> `diurnal_price_amplitude` = **G** (owner-closed frontier, no admissible in-model route) and
> `measured_offer_surface` = **R** (pjm-123/126/127/132, the D-BIN resolution bound). This
> reproduces pjm-141's conclusion — *"the annual level being right is a cancellation, not a
> correct level"* — from a different direction, on three years pjm-141 never saw.
>
> **No arm is chartered and no LP was spent.** That is the honest outcome, not an unfinished one.

---

## 2. THE DECOMPOSITION — the whole finding in one table

Each year's C3a gap ($/MWh, system load-weighted, model − actual) split into a **trough leg**
(load deciles 1–8) and a **peak leg** (deciles 9–10), with the counterfactual C3a if either leg
alone were closed exactly to actual. Band is ±10 %.

| year | C3a | trough leg | peak leg | **if trough fixed** | **if peak fixed** |
|---|---|---|---|---|---|
| **2021** (holdout) | **+10.7 %** | **+3.56** | **+0.57** | **+1.5 %** ✅ | +9.2 % ✅ |
| **2022** (holdout) | −10.3 % | +4.24 | **−11.87** | **−16.0 %** ❌ | +5.7 % ✅ |
| **2023** (train) | +5.7 % | +3.42 | −1.72 | −5.8 % ✅ | **+11.5 %** ❌ |
| **2024** (train) | −1.4 % | +2.28 | −2.73 | −8.6 % ✅ | +7.2 % ✅ |
| **2025** (train) | −8.1 % | +0.82 | −4.54 | −9.8 % ✅ | +1.8 % ✅ |

Three facts, and each is load-bearing:

1. **The trough leg is positive in all five years** (+0.82 → +4.24 $/MWh) — it is *not* a
   held-out-year phenomenon. It is present, unfixed, in the three years the keeper is tuned on.
2. **The peak leg is the year-varying term** (+0.57 → −11.87) and it is what sets C3a's SIGN.
   2021's peak leg is ≈ 0 because 2021 had no scarcity: its decile-10 actual is $56.55/MWh,
   against $172.00 (2022), $48.28 (2023), $62.10 (2024), $92.67 (2025).
3. **Neither single-ended repair survives.** Closing the trough sends 2022 to −16.0 %; closing
   the peak sends **2023 — a training year — to +11.5 %**. Both are outside the commercial band.

**Robust to the split point.** At deciles 7/8/9 the trough-fixed 2022 reads −15.9 / −16.0 /
−14.1 % and the peak-fixed 2023 reads +10.5 / +11.5 / +11.1 %. No conclusion here depends on
where the cut is drawn.

---

## 3. THE TROUGH LEG HAS A YEAR-INVARIANT STRUCTURAL SIGNATURE

Implied market heat rate — price ÷ **the model's own delivered gas series** (`_gas_series`,
`gas_monthly_actuals` on, the identical series the merit order prices gas at) — in the bottom
load decile:

| year | gas $/MMBtu | model $ | **model IHR** | actual $ | **actual IHR** | Δ IHR |
|---|---|---|---|---|---|---|
| 2021 | 3.85 | 32.59 | 8.46 | 25.21 | 6.55 | **+1.92** |
| 2022 | 6.68 | 52.91 | 7.92 | 39.21 | 5.87 | **+2.05** |
| 2023 | 2.94 | 25.64 | 8.71 | 17.72 | 6.02 | **+2.69** |
| 2024 | 2.52 | 23.34 | 9.28 | 15.98 | 6.35 | **+2.92** |
| 2025 | 3.43 | 31.49 | 9.17 | 24.06 | 7.01 | **+2.17** |

The model's overnight marginal offer sits at an implied heat rate of **7.9–9.3 in every year**
— a gas CC at about its rated heat rate, always. PJM's own overnight clearing sits at
**5.9–7.0**, i.e. *below any CC's full-load heat rate*. The market's trough is set by conduct
the model's offer stack does not represent; the model's is set by the merit order alone.

This is the same object pjm-141 measured on the diurnal axis (*"every one of the 2,034–2,044
thermal LP rows posts the SAME offer in every hour of a calendar day — within-day σ =
$0.000000"*), reproduced here on the load axis and extended to 2021, 2022 and 2025. pjm-141's
T1/T4 already established the overnight **tranche** and the overnight **requirement** are
correct, so this is not a commitment or a floor defect — it is the absence of hour-varying
offer conduct, which is precisely the cell the owner closed.

---

## 4. A SEPARATE, NEW DOF OBSERVATION — the coal sigmoid's identification support

Measured with the keeper's own parameters (`floor` 0.65 / `ceil` 1.32 / `gas_mid` 3.40 /
`gas_slope` 2.5) against the model's own `_gas_series`, the **realized annual-mean bituminous
passthrough** is:

| year | 2024 | 2023 | 2025 | **2021** | **2022** |
|---|---|---|---|---|---|
| model-seen gas $/MMBtu | 2.86 | 3.26 | 3.93 | 4.11 | 7.12 |
| realized passthrough | **0.81** | **0.92** | 1.06 | **1.12** | **1.32** (saturated, 12/12 months) |

**The training window exercises only the sigmoid's lower limb.** 2023 and 2024 sit at 0.81–0.92,
near the 0.65 floor; the two held-out years sit at 1.12 and 1.32, the latter pinned to the
ceiling in every month of the year. The `ceil` and `gas_mid` that set 2021's and 2022's coal
offers are therefore **effectively unidentified by the years they were tuned against** — a
rule 21 `[R-DOF]` observation about the family, not about any one arm.

It is recorded because it explains *why* pjm-170's ceiling screen read as it did (2022 is the
one year where `ceil` is the entire operand), and because it bears on any future coal-curve
card. **It is not a lever here**: pjm-170 measured that removing the full 32 % markup moves
2022's annual mean by only **−$0.17/MWh**, so the curve has ~no leverage on the C3a level, and
the `ceil`-alone cell is adjudicated **R** (DO-NOT-REDO, rule 32).

---

## 5. WHAT THIS SESSION DID **NOT** DO, and why

- **It did not tune anything to 2021.** 2021 is a rule 22 validation-tier touchpoint. The
  touchpoint loop identifies parameters on 2023–2025 only; a value chosen to make 2021 land
  inside a band is the fitted-mechanism selection rules 1 `[R-STRUCT]` and 29 `[R-SCREEN]`
  exist to forbid. Every measurement above was taken on the object (offer level, implied heat
  rate, passthrough), never on the residual.
- **It did not re-test an adjudicated cell.** `diurnal_price_amplitude` **G**,
  `measured_offer_surface` **R**, `ordc_scarcity_overlay` **G**, `coal_passthrough_sigmoids`
  `ceil`-alone **R** — all barred by the DO-NOT-REDO discipline absent new evidence, and this
  session's evidence corroborates rather than overturns them.
- **It did not spend a screen.** Phase 0 killed the candidate before a solve: the only
  single-ended repairs available regress a year that currently passes (§2), and the coal curve
  has no measured leverage on the level (§4). Rule 29's phase 0 doing its job.
- **It did not register a run.** No bundle was produced (rule 15 governs *completed runs*;
  there is none). The 2021/2022 numbers quoted are the already-registered
  `2026-09-07-pjm-2022-2021-touchpoints`, re-scored at HEAD without a solve.

---

## 6. STATED LIMITS

1. **Basis.** §2/§3 compare the model's hourly system load-weighted price against the committed
   RT hourly actual (`data/raw/_validation-source/actual_lmp_hourly_PJM.parquet`), while the
   scorer's C3a uses the committed `rt_lw` bench field. The two differ by ≤0.5 pp
   (2021 +10.7 vs +10.8; 2022 −10.3 vs −9.9; 2023 +5.7 vs +6.2; 2024 −1.4 vs −0.8;
   2025 −8.1 vs −7.7). Every conclusion here has margin far larger than that offset, and the
   §2 counterfactuals are outside the band on either basis.
2. **The counterfactuals are arithmetic, not solves.** "If trough fixed" sets that leg's hours
   to the measured actual and re-weights; it does not model how a real mechanism would
   redistribute dispatch. They bound the *sign and rough size* of a single-ended repair, which
   is all §2 claims.
3. **HEAD drift.** The 2023–2025 columns are the keeper's committed hourlies solved at its own
   HEAD; 2021/2022 are the touchpoint's, at a later HEAD. PJM's G-DRIFT baseline is
   unrecoverable (pjm-167, replicated by pjm-166 at 11,640 commits). This affects
   cross-*column* comparison, not the within-year trough/peak split, which is internal to one
   bundle-year.

---

## 7. WHAT THE SUCCESSOR SHOULD DO

**Do not open a card to close 2021.** Rule 30(c) already holds PJM's headline at CALIBRATED,
rule 22 already forbids quoting 2021 as a skill number, and §2 shows the miss has no admissible
single-ended repair. Re-running the touchpoint on a level lever would spend LP to move a number
the rules forbid using, and would break 2022 or 2023 doing it.

**The live card is unchanged and is pjm-170 §7 item 2**, now with a second face and a sharper
statement: PJM's price *distribution* is compressed at both ends — the trough by ~2.35 MMBtu/MWh
of implied heat rate (§3), the peak by the C3c tail the rubric already accepts as a model-class
limitation. The two ends are one defect, they cancel in the annual mean, and **the cancellation
is load-bearing in the training window** (§2, the 2023 column). Any repair must move both ends
or it regresses the keeper.

**Owner-facing, not decided here.** Both ends sit behind adjudicated cells (§5). Re-opening
either is an owner decision on rule 1 `[R-STRUCT]` structural grounds, never on the fit. What
this session adds to that decision is the measurement that the current pass is a cancellation
in the *tuned* years too — which pjm-141 asserted on 2023–2025 and this session now shows
across the full 2021–2025 span.

---

## 8. ARTIFACTS

Scratch measurement scripts are session-local and not committed (rule 29(c) discipline: this
document carries every number this session will ever cite). The inputs are all committed:
`results/calibration/pjm169_tp2022_2021_f2arm/hourly/`,
`results/calibration/pjm_debugb_inputclock_A/hourly/`,
`data/raw/_validation-source/actual_lmp_hourly_PJM.parquet`,
`frontend/data/backcast/bench/PJM/<year>.json.gz`, and
`src/market_sim/data/fuel/trajectories.py::_gas_series` / `_sigmoid_passthrough`.
