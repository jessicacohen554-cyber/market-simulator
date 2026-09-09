# PRECOMMIT — PJM: the measured monthly gas LEVEL + the 2019-2022 retiree window

**Session:** `pjm-fuelvintage-1`, 2026-09-09. **ISO scope: PJM only.**
**Branch:** `claude/pjm-fuelvintage-1`, off `origin/main` @ `87ad084b`.
**Arm:** `ScenarioConfig.gas_electric_power_monthly_level = True` (commit `7648daa0`), plus the
2019-2022 retiree window already on `main` (commit `7934e92c`, no flag).
**Control (declared posture, see §2):** the committed keeper bundle
`results/calibration/pjm_debugb_inputclock_A` = run `2026-08-15-pjm-162-inputclock`.

Written **before any LP**. Rule 29 `[R-SCREEN]` clause (0): an arm with a computable pre-solve
gate does not reach a solve until that gate passes.

---

## 0. STEP-0 verification (done)

| check | result |
|---|---|
| HEAD tree vs `origin/main` tree | **identical** (`580144d81299e55b241e2273f244c5d17dc80864`). Launch HEAD `b9fcb160` was merged to main as `87ad084b`; branched off `origin/main`. |
| `src/market_sim/data/fuel/electric_power.py` | present |
| `grep -c gas_electric_power_monthly_level scenarios.py` | **4** (expected 4) |
| retiree parquet | **1,094 rows, min `planned_retirement_year` 2019** (expected 1094 / 2019) |
| PJM keeper shard | `2026-08-15-pjm-162-inputclock` — **unchanged** by the 51 post-handoff commits |

## 0a. Keeper control baseline, re-scored at HEAD from committed artifacts only

`scripts/calibration_verdict.py --run-id 2026-08-15-pjm-162-inputclock` (no solve):
**CALIBRATED**, every criterion PASS, governance attested, zero caveats.

| criterion | 2023 | 2024 | 2025 |
|---|---|---|---|
| C3a mean LMP | **+6.2 %** (31.41 vs 29.58) | −0.8 % (31.11 vs 31.36) | **−7.7 %** (42.38 vs 45.89) |
| C3b NRMSE | 0.160 | 0.123 | 0.139 |
| C3c h>$200 | 4 vs 6 | 10 vs 18 | 32 vs 59 |
| C1 / C2 / C4 / C6 / C8 | PASS | PASS | PASS |

Band for C3a is **±10 %** (target and commercial). **2025 sits at −7.7 %, i.e. 2.3 pp of
headroom on the side this arm pushes.** That is recorded here, before the solve, as the arm's
single largest pre-registered gate risk — see §4.

---

## 1. ADDITION-0 items, checked rather than assumed

1. **`ercot-261`'s corroborated ERCOT monthly gas level** (`data/raw/ercot_gas_corroborator_monthly.csv`,
   `src/market_sim/data/fuel/basis/ercot.py`) is ERCOT-scoped, touches neither
   `gas_electric_power_monthly_level` nor PJM. Read as prior art; **no transfer** (rule 25
   `[R-ISO-SCOPE]`). Whether PJM's uniform cut wants a second independent corroborating source
   is a real question and is answered in §6 by the census, not by importing ERCOT's table.
2. **`partial_plant_exit_carry` double-count risk: NOT PRESENT in PJM.** The field's dataclass
   default is `False` (`scenarios.py:14173`), the PJM keeper's `run_config.json` does not set it,
   and the 2022/2021 touchpoint bundle records it explicitly `False`. The partial-plant channel
   is **off in every PJM run in scope**, so its `_PARTIAL_EXIT_WINDOW_START = 2019` cannot
   overlap the whole-plant retiree window here. Nothing further owed.
3. **`pjm-177` landed** (ST_GAS commitment shape). Its keeper is unchanged, so the designated
   keeper for this lane is still `2026-08-15-pjm-162-inputclock`.

---

## 2. G-DRIFT (rule 29(b)) — **THE AUDIT IS UNRUNNABLE, AND FORM 4 IS VOID**

The rule-29(b) audit requires `git diff <keeper git_sha> HEAD`. **It cannot be run:**

| sha | source | resolves at HEAD? |
|---|---|---|
| `457ae04` | keeper bundle `run_config.json` `git.sha` | **NO** — `git cat-file` fails |
| `c447199c9009…` | same bundle, `git.basis_sha` | **NO** |
| `f36cee6e` | `pjm169_tp2022_2021_f2arm` (2026-09-07 touchpoint) | **NO** |
| `a269fb77b4a0…` | same bundle, `basis_sha` | **NO** |

Neither carries an entry in `docs/governance/citation-commit-map.txt`. The keeper's shas predate
the 2026-08-16 history rewrite; the **touchpoint's do not**, and they still fail — these are
feature-branch tip shas that squash-merge discarded. **So the failure is not only the rewrite:
no PJM bundle's recorded `git_sha` is resolvable from `origin/main` at all.** Recorded here as a
finding in its own right, because rule 29(b) makes that sha the sole input to the audit it
mandates.

`PRECOMMIT-pjm177-…-2026-09-09.md` §4 reached the same conclusion independently for `457ae04`
and additionally named **two LIVE hunks** on the PJM backcast path since the keeper:
`f923_gas_price_plausibility_screen` (default `True`, and absent from the keeper's recorded
config) and `EGRID_CT_HR_PHYSICAL_FLOOR`. Either one alone voids form 4.

**Declared control posture, therefore:**

- **A same-HEAD control solve is EARNED for the screen year (2023) but is spent CONDITIONALLY,
  and only on a failure.** Rule 29(b)'s LIVE-hunk case licenses a control "only for the years the
  screen needs", and on inspection the screen does not need one *up front*: **G-4's bar is a
  PASS → FAIL flip, and PASS/FAIL is scored absolutely against actuals**, not against a control.
  The committed keeper is all-PASS in 2023 (§0a), so an arm that comes back all-PASS clears G-4
  with no control in existence. A control is needed only to **attribute** a failure — to separate
  this arm from the two LIVE hunks §2 names. So: **run the arm; spend the 2023 control if and
  only if a load-bearing criterion fails.** Declared here, before the solve, so it cannot be read
  as a post-hoc economy.
- **For the full span (2023-2025) and the touchpoints (2020-2022) no control is solved.** Those
  runs are scored **absolutely against actuals** by `calibration_verdict.py`; a determination
  needs no control. The committed keeper's numbers in §0a are quoted alongside them as
  **context, explicitly contaminated by HEAD drift**, never as a clean A/B attribution. The
  screen's control−arm pair at 2023 is what carries the attribution claim.

`data/raw/reference/iso-gas-capacity-state-weights.csv` is NEW and is **LIVE only when the flag
is armed** (read exclusively by `electric_power._load_iso_weights`). The retiree parquet is
**LIVE for 2019-2022** and asserted INERT for 2023-2025 — **that second half is PROVEN, not
asserted, in §5 gate G-6**, not taken on the construction's word.

---

## 3. SCREEN YEAR, NAMED BEFORE THE SCREEN RUNS: **2023**

Named on the **mechanism's own measured footprint**, never on a residual: FINDING §3 gives PJM
2023 the largest measured level gap of any PJM year — annual **−0.770 $/MMBtu**, `mae` **0.775**,
and **all twelve months lower** (−0.31 to −1.42). Reproduced independently here from
`iso_electric_power_monthly_level('PJM', y)`:

| year | basket cov. | measured annual $/MMBtu | monthly min / max |
|---|---|---|---|
| 2020 | 0.781 | 1.937 | 1.638 / 2.689 |
| 2021 | 0.721 | 3.588 | 2.427 / 5.095 |
| 2022 | 0.975 | 6.469 | 4.640 / 8.361 |
| **2023** | **0.975** | **2.490** | 1.942 / 3.862 |
| 2024 | 0.975 | 2.380 | 1.776 / 5.074 |
| 2025 | 0.912 | 3.745 | 2.331 / 8.511 |

(Every year admitted; the annuals reproduce FINDING §3 to ≤0.010 $/MMBtu, the residue being an
unweighted-vs-weighted annual-mean convention.) **The basket's composition varies BETWEEN years**
(2021 drops IL/MD/MI, 2020 drops IL/IN) and is constant **within** each year, which is exactly
what the module's admission rule requires — noted so a cross-year level comparison is read with
that in mind.

---

## 4. PRE-REGISTERED PREDICTIONS (rule 1: reported at full magnitude, gating nothing)

**Direction, from §3 and FINDING §5b:** the measured delivered level is **BELOW** the keeper's
level in every month of every PJM year ⇒ **gas cheaper ⇒ coal displaced UP, gas CC down, LMP
DOWN.** PJM is the largest and most uniform fuel move in the program.

**Magnitude, as an upper bound.** A Δgas of −0.770 (2023) / −0.469 (2024) / −0.189 (2025)
$/MMBtu at a 7.5 MMBtu/MWh CC heat rate is **−5.8 / −3.5 / −1.4 $/MWh** of marginal-cost move,
~1.4× that in a CT-marginal hour. **Passed through in full** to the load-weighted mean, that is
**−18.4 / −11.3 / −3.3 %** of the keeper's model mean. The realised move will be smaller by the
non-gas-marginal hour share **and, decisively, by whatever fraction of PJM gas capacity-hours the
F923 print path already owns** (§6). Both legs are unknown before the census; the bound is stated
so the screen cannot be read as confirming a number it never predicted.

**Per-criterion, pre-registered:**

| criterion | 2023 | 2024 | 2025 |
|---|---|---|---|
| **C3a** | +6.2 % moves **down**. Improves, then overshoots. PASS unless the pass-through exceeds ~16 pp | −0.8 % moves down. **Risk of leaving the −10 % band if pass-through > 9 pp** | **−7.7 % moves down. THE TIGHTEST CELL IN THE RUN: only 2.3 pp of headroom; a full-pass-through −3.3 pp puts 2025 at ≈ −11 % ⇒ FAIL** |
| **C3b** | ±0.03 of 0.160 | ±0.03 of 0.123 | ±0.03 of 0.139 |
| **C1 / C2** | coal UP, gas CC DOWN; both should stay in band | same | same |
| **C3c** | may rise slightly (cheaper gas ⇒ lower prices ⇒ *fewer* >$200 h, if anything) | same | same |

**Why PJM is the program's highest C3b risk, in my own words, before I see a number.** C3b is a
*monthly-shape* NRMSE, and this seam is the only mechanism in the program that rewrites the gas
level **month by month with a different number in each month**. Every other PJM monthly gas
mechanism in the recipe is mean-preserving by construction — `gas_daily_shape` normalises within
each month, and `gas_hh_monthly_shape` normalises to the annual — so none of them can move C3b's
own axis. This one can, and it does so with no hub overlay above it to supersede the change and
no measured constrained-hub index to keep it anchored: PJM is the only in-scope ISO where the
seam reaches the operative level in 12/12 months of 7/7 years. That is the whole exposure. What
makes it survivable, and why I do not predict an ercot-254 repeat: ercot-254 broke because a
**single 49.5 $/MMBtu Uri month** was smeared flat across 672 hours; PJM's largest single-month
gap in any year is **1.72 $/MMBtu** (Jan-2025), 29× smaller, and `gas_daily_shape` — armed in
this keeper, and *not* armed in ercot-254's arm — already redistributes each month's cost across
its days by the real commodity swing. The failure mode scales with the outlier, and PJM has no
outlier.

**Card A (2019-2022 fleet), pre-registered:** PJM gains 205 units / 13,294.9 MW net summer,
coal-dominated (10,649.9 MW) — per solve year **2020 +8,094.5 MW, 2021 +5,687.1, 2022 +4,535.9,
and ZERO in 2023-2025**. Prediction: **coal generation UP and prices DOWN in all three touchpoint
years, 2020 the largest**. Both fixes are carried together in the touchpoint shards per the owner
instruction (no attribution arms), so the touchpoint deltas are **joint** and will be reported as
joint.

---

## 5. SCREEN GATES — pre-registered, **STOP-ONLY**, none of them the target residual

A screen **may kill this arm; it may never promote it** (rule 29). None of C1/C2/C3a/C3b/C3c is a
gate *in the improving direction*: G-4 fires only on a PASS → FAIL flip, which is a stop, never a
promotion.

| gate | claim it tests | bar |
|---|---|---|
| **G-1 direction & magnitude** | the delivered gas array moves the way the pre-solve arithmetic says | armed − control monthly mean gas price over gas rows is **negative in all 12 months of 2023**, and its capacity-weighted annual mean is within **±25 %** of the census-predicted move of §6 |
| **G-2 confinement** | only gas moves | `max|Δ|` over **coal, oil, biomass, nuclear, hydrogen** rows of `fuel_prices` = **exactly 0.0** |
| **G-3 rule 19 — replaced, not blended** | the seam supersedes rather than stacks | on the rows the seam actually reaches, the armed monthly level equals `iso_electric_power_monthly_level('PJM', 2023)` **exactly** (≤1e-9 $/MMBtu) before `gas_daily_shape`'s mean-preserving multiplier |
| **G-4 no non-target regression** | no load-bearing criterion breaks | none of **C1, C2, C3a, C3b** flips **PASS → FAIL** in 2023. **If it does, THE ARM DIES HERE**, the remaining years are never spent, and that is reported as a successful screen |
| **G-5 feasibility** | the LP is not being rescued by slack | `slack` and `dump` **= 0.0** |
| **G-6 Card-A inertness in-window** | the retiree window really is 2019-2022 only | `max |class-hour delta|` between the armed 2023 fleet and the keeper's committed `class_hourly_2023.parquet` attributable to the fleet = **0.000000 MW**; proven by a `fleet_only` array comparison, **not asserted from the parquet's own construction** |

G-4's own baseline is the **same-HEAD control** of §2, not the committed keeper — that is what the
control solve is spent on.

---

## 6. PHASE-0 CENSUS (ADDITION 1) — the gate that can kill the arm at zero LP cost

**The question.** The PJM keeper carries `gas_plant_monthly_fuel_pricing = True`.
`apply_plant_monthly_fuel_prices` runs **after** the new seam (`resolve.py:152` seam →
`resolve.py:~225` overlay) and overwrites each gas plant's price with that plant's own F923
monthly print where one exists. The seam may therefore reach only (a) the gas cells the print
path does **not** write and (b) the ISO-level `_gas_series` that keys the coal passthrough
sigmoid. **If the print path owns ~all of PJM's gas capacity-hours, the arm is inert on gas
offers and the screen must not be spent.**

Note this is sharper than the FINDING's own table: FINDING §3's "model level" column is the
monthly mean of the ISO-level `_gas_series`, which is **not** what a PJM gas plant pays under this
keeper's recipe.

**Method (zero LP).** Two on-recipe `run_calibration.run_year(..., fleet_only=True)` rebuilds off
`results/calibration/pjm_debugb_inputclock_A/meta.json`, differing **only** in
`gas_electric_power_monthly_level`, routed through the generic `prb_overrides` channel — which is
byte-identical to what `replay_keeper.py --set gas_electric_power_monthly_level=true` does, since
the field is a `ScenarioConfig` field and **not** a `solve_and_persist` parameter, so `--set`
routes it through `prb_overrides` and nothing else (`replay_keeper.py:905-914`). The payload's
`fuel_prices` is the fully-resolved array **after every overlay**, so the armed−control delta over
gas rows IS the answer, and the print-cell mask returned by `apply_plant_monthly_fuel_prices` is
reported alongside it as the mechanism.

**RESULT — the arm is NOT inert. THE GATE PASSES and the screen is justified.**

PJM 2023, `fuel_prices` after every overlay, capacity-weighted over the 1,744 gas rows
(3,789 LP rows total, 8,760 h):

| quantity | value |
|---|---|
| **F923 print path owns (cap-weighted gas capacity-hours)** | **51.794 %** |
| **the seam reaches** | **48.206 %** |
| moved **and** print-written | **0.0000 %** |
| moved **nor** print-written | **0.0000 %** |
| delta on the cells the seam reaches | mean **−0.7721**, min −1.5954, max −0.3001 $/MMBtu, **100 % negative** |
| delta cap-weighted over **all** gas cells | **−0.3721 $/MMBtu** |
| **max \|Δ\| over coal / oil / biomass / nuclear / hydrogen rows** | **exactly 0.0000000000** |

Three things this settles at zero LP cost:

1. **The partition is EXACT.** `moved ∧ print-written` and `¬moved ∧ ¬print-written` are both
   **0.0000 %**: the seam reaches precisely the complement of the print path's written-cell mask,
   with no cell double-written and no cell left unpriced. That is rule 19 `[R-ONE-MECH]` holding
   by measurement rather than by assertion.
2. **On the cells it owns, the seam REPLACES rather than blends.** The mean delta there,
   **−0.7721 $/MMBtu**, reproduces FINDING §3's PJM-2023 annual **−0.770** to three decimals —
   i.e. the reached cells land on `iso_electric_power_monthly_level('PJM', 2023)` itself. **G-3 is
   effectively satisfied pre-solve**; the screen re-checks it against the solved array.
3. **G-2 is satisfied pre-solve**: every non-gas row moves **exactly** 0.0.

Monthly, the reach is a two-step function of F923 coverage — **46.62 %** Jan–Sep, **52.93 %**
Oct–Dec — and the cap-weighted delta over all gas cells runs −0.144 (Jul) to −0.660 (Feb):

| month | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cw Δ $/MMBtu | −0.519 | −0.660 | −0.397 | −0.409 | −0.395 | −0.240 | −0.144 | −0.156 | −0.252 | −0.356 | −0.480 | −0.482 |
| cw moved % | 46.6 | 46.6 | 46.6 | 46.6 | 46.6 | 46.6 | 46.6 | 46.6 | 46.6 | 52.9 | 52.9 | 52.9 |

**§4's magnitude prediction is therefore SHARPENED before the solve, not after.** The effective
gas move is **48.2 %** of the headline, so the full-pass-through bound becomes **−2.79 $/MWh**
(2023), and — carrying the same reach forward as the only estimate available pre-solve —
**−1.69** (2024) and **−0.68** (2025) $/MWh. Against the keeper's model means that is
**−8.9 % / −5.4 % / −1.6 %**, giving pre-registered C3a landing points of roughly
**−2.7 % / −6.2 % / −9.3 %**. **2025 remains the tight cell** — ≈0.7 pp inside the ±10 % band on
this arithmetic — and its basket coverage (0.912) differs from 2023's (0.975), so its reach is
the one number in this table that is extrapolated rather than measured. Reported at full
magnitude either way; **none of it gates anything** (rule 1 `[R-STRUCT]`).

**A rule-19 observation this census surfaced, recorded not absorbed.** The F923 plausibility
screen (`f923_gas_price_plausibility_screen`, default `True` — one of the two LIVE hunks §2
names) already reads **the same EIA `N3045<ST>3` series** this seam blends, as the out-of-band
fallback reference: for PJM 2023 it moved **24 plant-months across 9 plants** onto that
reference. So a small, bounded part of the print path's 51.8 % is *already* N3045-priced, by a
different route. That is a **different quantity** — a per-plant, per-state reference used as an
implausibility backstop, versus a footprint-blended ISO-level replacement — and the two do not
stack on any cell (the partition above is exact). Recorded here so the interaction is on the
record before the solve rather than discovered in the residual.

---

## 6a. THE OFFER-LEVEL FOOTPRINT — and a pre-registered prediction I am REVISING, before the solve

The §6 census measures `fuel_prices`. The LP solves on `mc_base`. Measuring the second (same two
`fleet_only` builds, PJM 2023) found a second live channel the FINDING's tables do not carry, and
it **contradicts one of my own §4 predictions**. Revised here, on the mechanism's own arithmetic,
**before any LP** — never on a residual.

| fuel | rows | cells moved | max \|Δ\| $/MWh | cap-weighted mean Δ $/MWh |
|---|---|---|---|---|
| gas | 1,744 | 50.13 % | 65.612 | **−3.2588** |
| **coal** | **553** | **71.07 %** | **61.278** | **−3.0571** |
| oil | 507 | 0.00 % | **0.00000** | 0.00000 |
| biomass | 672 | 0.00 % | **0.00000** | 0.00000 |
| nuclear | 32 | 0.00 % | **0.00000** | 0.00000 |
| other (hydro / storage / renewable rows) | 281 | 0.00 % | **0.00000** | 0.00000 |

**Coal offers move almost as much as gas offers do, and in the same direction.** The route is the
keeper's own coal passthrough sigmoids (`coal_prb_passthrough_sigmoid` and
`coal_bit_passthrough_sigmoid`, both `True`), which are keyed on the ISO-level `_gas_series` —
the series this seam replaces. Cheaper gas ⇒ a lower passthrough ⇒ coal discounts to hold its
place in merit. **That is a real market behaviour and it is structurally correct** (rule 1
`[R-STRUCT]`: a structurally-correct mechanism is never judged by the residual), and it is *not*
a G-2 violation — G-2 is stated over **fuel prices**, where coal moves exactly 0.0; this is the
**offer** layer, one step downstream, and it is the sigmoid doing exactly its declared job.

Monthly, cap-weighted:

| month | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gas Δ $/MWh | −4.55 | −5.78 | −3.48 | −3.58 | −3.46 | −2.11 | −1.26 | −1.36 | −2.20 | −3.12 | −4.20 | −4.22 |
| coal Δ $/MWh | −2.88 | −6.50 | −5.53 | −3.62 | −2.19 | −0.79 | −0.66 | −0.45 | −1.19 | −1.87 | −6.25 | −5.06 |

**What I am revising.** §4 predicted "**coal displaced UP, gas CC down**", inherited from FINDING
§5b. On this measurement that prediction is **wrong in its mechanism and probably wrong in its
sign**: coal's offer falls by −3.06 $/MWh against gas's −3.26, so the coal-vs-gas **spread** moves
only ~0.20 $/MWh on the annual cap-weighted mean, and in **five of twelve months (Feb, Mar, Apr,
Nov, Dec) coal falls by MORE than gas**, which pushes coal *down* the merit order relative to gas,
not up. **Revised prediction: the coal/gas substitution is second-order and its sign is
month-dependent; C1/C2 should move much less than FINDING §5b implies, and a large coal-up move
would now be the surprise.**

**What this does to the C3a risk — it raises it.** The price effect is no longer a gas-only
channel. Roughly **85 %** of PJM's thermal rows (gas + coal) see a **−3.1 to −3.3 $/MWh** offer
cut, so a marginal hour is cheaper whichever of the two sets it. Against the keeper's 2023 model
mean of $31.41 that is up to **−10.4 %** at full marginal pass-through, versus the −8.9 % §6
projected from the gas leg alone. **The §4 landing points are therefore soft on the low side, and
2025 — at −7.7 % with 2.3 pp of headroom — remains the cell that can fail.** Stated at full
magnitude and gating nothing.

**A consequence for gate G-2, made explicit so the screen cannot be mis-scored:** G-2's bar is
`max|Δ|` over non-gas rows of **`fuel_prices`** = exactly 0.0 — measured, satisfied. It is **not**
a bar on `mc_base`, where coal is *expected* to move. A screen that reported the coal offer move
as a confinement failure would be reading the wrong array.

---

## 7. Markers, read authoritatively (ADDITION 4)

`scripts/lib/holdout_policy.registration_refusals(years, 'PJM', marker_doc, freeze_doc)` at HEAD:

| years | refusals |
|---|---|
| 2023, 2024, 2025 | **none** (train tier) |
| 2020, 2021 | **none** — PJM holds `complete` (declared 2026-07-31, keyed to this keeper) |
| 2022 | **none** |
| **2019** | **REFUSED** — locked-test tier, under an ACTIVE tier-scoped freeze (`frozen_tiers = {'locked_test'}`), and PJM is absent from `final` (`final` holds only `_note`) |

2019 is **not attempted, not requested, and not designed around.** Validation numbers are
iterable model-selection evidence, never a certified out-of-sample skill number (rule 22), and
**no parameter is identified against 2020/2021/2022** — structurally guaranteed, since both
changes have **zero free parameters**: the seam is a frozen blend of a published series over a
rule-23 frozen weight table, and the retiree window is an EIA-860 fact.

Rule 30(c) `[R-TOUCHPOINT-FOLD]`: a held-out year **never downgrades PJM's determination**. PJM's
headline is the 2023-2025 train-tier verdict and nothing else.

---

## 8. ENVIRONMENT FINDINGS — this container could not have solved PJM as handed over

Recorded because they are the session's first real result and they bind every PJM shard.

1. **`data/clean/` was EMPTY.** It is gitignored (derived, disposable) and must be rebuilt with
   `scripts/regenerate_clean.py` before any solve. The PJM fleet build hard-fails — by design,
   "the mechanism never silently no-ops" — on each missing partition in turn:
   `transfer-interface-limits`, then `ramp-capability`, …
2. **Six PJM-relevant `data/raw` corpora are payload-less** (the corpus-conversion class of
   `docs/bloat-removal-plan-2026-08.md` §4 — README + `SHA256SUMS.txt` tracked, payload
   gitignored, and stripped from history by the 2026-08-16 rewrite, so **re-fetch is the only
   recovery route**): `pjm-da-virtuals`, `pjm-energy-offers`, `pjm-zonal-lmp`,
   `pjm-binding-constraints`, `pjm-ehv-lmp`, `lmp-components`.
   **`pjm-da-virtuals` is REQUIRED by the keeper recipe** (`pjm_da_virtual_bids = True` in both
   the keeper's and the touchpoint bundle's `run_config.json`) and is being re-fetched here from
   PJM DataMiner2 for 2020-2025.
3. **Consequence for the shard plan (ADDITION 2):** every child session gets a fresh container
   and therefore inherits an empty `data/clean` and the same payload-less corpora. Each child's
   launch prompt must carry the clean rebuild and the DataMiner re-fetch, or it will fail the
   same way ~4 minutes into its first fleet build.

---

## 9. Governance

- **Rule 31 `[R-RETAIN]`** — no solve output is deleted before the owner rules on promotion. The
  bundle families are **gitignored**, not `rm`'d; they live on local disk and **will not survive
  this session's container**. The promotion question is asked explicitly in the final report.
- **Rule 15 `[R-DASHBOARD]`** — every completed run is registered in this session, keeper or
  rejected probe. Screen and control bundles are **throwaway probes**: never registered, never
  committed, gitignored (rule 29(c) as amended 2026-09-07 — `.gitignore`, not `rm`).
- **Rule 16 `[R-ALLYEARS]` + ADDITION 3** — sharding the SOLVE is not registering FRAGMENTS. T1
  (2023, 2024) and T2 (2025) compose into **one** bundle covering 2023-2025 before registration.
- **Rules 1 / 14** — these land because they are **correct**. A worse fit is a root-cause
  investigation, never a revert to the estimate. No gate reads the target residual.
- **Rule 28 `[R-MECH-MATRIX]`** — only `docs/codebase-site/data/mechanism-matrix/PJM.js`, cell
  `gas_electric_power_monthly_level` (currently `O`), is edited.
