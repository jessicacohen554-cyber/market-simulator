# PREREG — MISO T1-X crossover, the one unmeasured leg of the FFR-3A battery

**Written and committed BEFORE the bundle exists.** No `results/ffr3a4/t1x/`
directory has been created at the time of this commit; the leg has not been
launched. This file exists so the reading of the result cannot be authored after
the result (forecast-determination rubric §4, and the discipline FFR-3A-2 and
FFR-3A-3 both applied to their own instruments).

Base sha: `292f577e`. Author: FFR-3A-4.

---

## 1. What is being measured, and why it is the last leg

FFR-3A-2 ran a 14-leg T1 battery, then recorded a **provenance ceiling** on its
own results: the rebase brought in FFR-3F's G3 cap-grain fix (`2adfb49`), which
is **unconditional** and changes the *admitted exit set* of the economic
retirement screen. FFR-3A-3 re-measured six of the seven affected legs at the
post-fix HEAD `941f4983`. **MISO T1-X was launched twice and killed twice by
OOM** — the second time by that session's own concurrent git activity — and was
correctly reported as NOT MEASURED with a null board cell rather than a carried
stale value (FFR-3A-3 §6.1).

This leg closes that gap. Invocation, with all six solve-affecting flags
**omitted** so every one inherits its shipped default:

```
uv run python scripts/run_capacity_hindcast.py --iso MISO --crossover --vintage 2023 \
  --start-year 2023 --end-year 2027 --out-dir results/ffr3a4/t1x/miso-2023-2027-crossover-ffr3a4
```

Nothing is tuned and nothing is promoted. Owner Addendum D.1 (*HOLD PROMOTION,
FIND ROOT CAUSE*; D-1 and D-2 both stay armed) and Addendum G.1 (D-8
`exit_rate_limits` ships default-OFF) are honoured, and will be verified in the
**resolved** config read out of the run log, not in the request.

## 2. The comparator — a real pre/post pair, not a first measurement

MISO T1-X *was* measured pre-fix by FFR-3A-2 and is registered as
`miso-2023-2027-crossover-ffr3a2`. Its committed metrics, extracted from the
sidecar **before this leg was launched**, are the baseline this PREREG is
scored against (`forecast_abs_err_frac`):

| metric | 2023 | 2024 | 2025 |
|---|---|---|---|
| price | 0.1360 | 0.1385 | 0.2743 |
| co2 | 0.6333 | 0.5887 | 0.7546 |
| gas_twh | 0.0950 | 0.1510 | uncovered |
| coal_twh | 0.0099 | 0.0158 | uncovered |

Both 2025 volume metrics are **uncovered** (preliminary EIA-923 vintage —
incomplete class actuals, reported but not banded), and that is expected to
persist; it is a property of the actuals, not of the solve.

## 3. THE PREDICTION

**Primary (falsifiable): every metric above reproduces to 3 decimal places, and
the determination stays HOLD.**

Grounds — mechanism, not extrapolation:

1. **Both other T1-X legs were completely unmoved by the G3 fix.** FFR-3A-3 §4:
   ERCOT and PJM reproduce *every* metric identically to FFR-3A-2 post-fix.
2. **FFR-3L established WHY, and the reason is structural.** In the ERCOT T1-X
   crossover, all four arms of its 2×2 execute **zero economic retirements in
   2023–2025** — the scored window — with the mass exit landing in 2026, a year
   that is *solved but never scored* (rule 22). A fix to the *admission* set of
   a screen that executes nothing inside the scored window cannot move a scored
   metric. The same structure applies to MISO's 2023–2027 crossover.
3. PJM is the direct precedent for the two halves diverging: **PJM's T1-X is
   unmoved while PJM's T1-H moved 3.55 GW under the same fix**, because T1-X
   seeds from the 2023 vintage over 2023–2027 while T1-H seeds from 2020 over
   2021–2025 — a different decision set on a different fleet.

**This prediction is NOT free, and here is exactly why.** MISO is the ISO whose
T1-H moved **most** of the four: `retire.total_gw` 13.734 PASS → 12.716 FAIL,
coal 12.95 → 11.932 GW. Its economic-retirement screen fires harder than any
other leg's, and the G3 fix moves a leg *in proportion to how hard that screen
fires* (FFR-3A-3 §2.1). If MISO's crossover — unlike ERCOT's and PJM's —
**executes** economic retirements inside 2023–2025, the fix can and should move
the scored metrics, and this prediction is refuted.

## 4. The discriminator, fixed in advance

The score alone cannot distinguish "the fix is inert here" from "the fix moved
something that happened to cancel". So the mechanism check below is committed
**now**, and will be read regardless of which way the metrics come out:

> Read the evolution ledgers at `<out-dir>/MISO/<resolved cache_key>/` (the
> resolved on-disk key, **not** a request-side `reference_config(...).cache_key()`
> — FFR-3A-2 §1.2) and count **executed economic retirements in 2023, 2024 and
> 2025**, keyed on `mw`, not `capacity_mw`.

- **Zero executed economic exits in 2023–2025** ⇒ the null is *structural*, the
  FFR-3L reading transfers to MISO on MISO's own evidence, and an unchanged
  score is explained rather than merely observed.
- **Non-zero executed economic exits in 2023–2025** ⇒ the FFR-3L structural
  story does **not** cover MISO, and an unchanged score would then be a
  cancellation that needs its own explanation before anything is claimed.

## 5. What this leg will NOT establish, stated in advance

1. **No control arm.** One arm at shipped defaults. Any pre/post difference is
   *convergence or divergence*, never attribution — the same limit FFR-3A-3 put
   on its own §3 finding.
2. **No verdict is minted for D-1 or D-2** from this leg. A crossover whose
   scored window executes no exits is a null by construction (the FFR-3C §3.2
   pattern), and per rule 25 nothing transfers to or from another ISO.
3. **FC-7 will be scored WITHOUT `--run-config`**, like every other leg in this
   battery. Passing it lifts FC-7 FAIL → CAVEAT purely because the scorer
   accepts the hindcast runner's YAML, which would show a false improvement on
   every leg (FFR-3A-3 §6.3). The like-for-like invocation is chosen
   deliberately.
4. **Nothing here bears on the depth residuals.** PJM over-retires and MISO
   under-retires; those are the chartered G-31 lane's (owner Addendum F.1), not
   a tuning target.
5. **No out-of-training year is touched in any measured-actuals mode.** The
   2023–2027 window is legal only via the enumerated carve-out in
   `scripts/lib/holdout_policy.py`, re-read at this head: `HINDCAST_SOLVE_YEARS
   = {2021, 2023, 2024, 2025}`, `HINDCAST_BRIDGE_YEARS = {2022, 2026}`, scoring
   bounded to 2023–2025, and 2026/2027 solved as forecast-mode years reading no
   measured actuals. The holdout spend freeze is ACTIVE and is neither spent nor
   worked around.
