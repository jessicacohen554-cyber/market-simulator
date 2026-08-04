# RESULT — MISO T1-X, scored against the PREREG

Companion to `PREREG-miso-t1x-2026-08-04.md`, which was committed **before** this
bundle existed (commit `00b0637c`, merged to main as PR #3494). Nothing here was
authored before the prediction; nothing in the prediction was edited after the
result.

Run `miso-2023-2027-crossover-ffr3a4` · cache key `46954f417b6e18e2` ·
solved `[2023, 2024, 2025, 2026, 2027]`, bridged `[]`.

---

## 1. Posture — verified in the RESOLVED config, not the request

All six solve-affecting flags were **omitted** from the invocation. Note that
`run_config.json` records the CLI *request* (every one reads `None` = "flag not
passed"), which is **not** the resolved posture — the same request-vs-resolved
distinction FFR-3A-2 §1.2 recorded for cache keys. Read two independent ways
(`run_config.yaml`, and the runner's own startup log line), they agree:

```
retirement_rule = pipeline        entry_rate_limits        = True
entry_lookahead_reprice = True    entry_commissioning_lag  = True
correlated_forced_outage = True   exit_rate_limits         = False
```

`exit_rate_limits=False` is owner Addendum G.1 honoured. Nothing was tuned,
nothing promoted, no default moved.

**Rule 22, re-read at this head rather than inherited:**
`HINDCAST_SOLVE_YEARS = {2021, 2023, 2024, 2025}`,
`HINDCAST_BRIDGE_YEARS = {2022, 2026}`, scoring bounded to 2023–2025. The
runner emitted its governance line; the holdout spend freeze is **ACTIVE** and
was neither spent nor worked around. 2026/2027 are solved as forecast-mode
years reading no measured actuals.

## 2. THE PREDICTION HELD — every banded metric reproduces at +0.0000

`forecast_abs_err_frac`, post-fix vs the pre-fix comparator
`miso-2023-2027-crossover-ffr3a2`:

| metric | year | pre-fix | **post-fix** | delta |
|---|---|---|---|---|
| price | 2023 | 0.1360 | **0.1360** | +0.0000 |
| price | 2024 | 0.1385 | **0.1385** | +0.0000 |
| price | 2025 | 0.2743 | **0.2743** | +0.0000 |
| co2 | 2023 | 0.6333 | **0.6333** | +0.0000 |
| co2 | 2024 | 0.5887 | **0.5887** | +0.0000 |
| co2 | 2025 | 0.7546 | **0.7546** | +0.0000 |
| gas_twh | 2023 | 0.0950 | **0.0950** | +0.0000 |
| gas_twh | 2024 | 0.1510 | **0.1510** | +0.0000 |
| coal_twh | 2023 | 0.0099 | **0.0099** | +0.0000 |
| coal_twh | 2024 | 0.0158 | **0.0158** | +0.0000 |

2025 gas/coal remain **uncovered** (preliminary EIA-923 vintage, incomplete
class actuals — reported, not banded), exactly as the PREREG anticipated; that
is a property of the actuals, not the solve.

**MISO joins ERCOT and PJM: all three T1-X legs are completely unmoved by the G3
cap-grain fix `2adfb49`.** The battery's T1-X half is now fully measured.

## 3. The discriminator — read BEFORE the score, and it answers cleanly

PREREG §4 fixed this check in advance precisely so an unchanged score could be
told apart from a cancellation. Executed retirements from the evolution ledgers
at `<out-dir>/MISO/46954f417b6e18e2/` (keyed on `mw`):

| year | retirements | economic | econ MW |
|---|---|---|---|
| 2023 | 0 | 0 | 0.0 |
| 2024 | 0 | 0 | 0.0 |
| 2025 | 0 | 0 | 0.0 |
| **2026** | 3 | **3** | **432.8** |
| 2027 | 4 | 0 (`announced`) | 0.0 |

**Zero executed economic retirements anywhere in the scored window; the exits
land in 2026 — solved but never scored (rule 22).** So the G3 fix, which changes
the *admission* set of the economic-retirement screen, has nothing to act on
inside 2023–2025. This is the PREREG's first branch: the null is **structural**,
not a coincidence of cancelling errors.

This independently reproduces, in MISO, the pattern FFR-3L established for
ERCOT's crossover — and it does so on **MISO's own evidence**, so rule 25 is
satisfied and nothing is imported. It also explains why MISO's T1-H moved most
of the four legs while its T1-X does not move at all: T1-H seeds from 2020 over
2021–2025 and executes exits inside its scored window; T1-X seeds from the 2023
vintage over 2023–2027 and does not. Same fix, different decision set, different
fleet — the PJM precedent exactly.

## 4. Determination — HOLD

`forecast_verdict.py --tier t1x`, scored **without** `--run-config`
(like-for-like; passing it lifts FC-7 FAIL → CAVEAT purely because the scorer
accepts the hindcast runner's YAML, which would show a false improvement on
every leg — FFR-3A-3 §6.3):

```
FC-4 crossover dispatch skill   FAIL   K_iso=3.0
    price   2023 13.6% / 2024 13.9% / 2025 27.4%   all CAVEAT
    co2     2023 63.3% / 2024 58.9% / 2025 75.5%   all FAIL
    gas_twh 2023  9.5% CAVEAT / 2024 15.1%         FAIL
FC-7 provenance & DOF           FAIL   run_config.json absent; DOF ledger absent
FC-1 / FC-2 / FC-3 / FC-5 / FC-8       SKIPPED
```

**HOLD** — the same category pattern (FC-4 FAIL, FC-7 FAIL) as every other leg
in the battery. **No determination moved anywhere**, and the §2.1b gate stays
closed for all six ISOs on criterion (b).

## 5. What this leg does NOT establish

Restated from PREREG §5, all of which survived contact with the result:

1. **No control arm.** One arm at shipped defaults. The reproduction is
   *convergence*, never attribution.
2. **No verdict minted for D-1 or D-2.** A crossover whose scored window
   executes no exits is a null by construction (the FFR-3C §3.2 pattern). The
   matrix cells are unchanged; only evidence citations were added.
3. **Nothing bears on the depth residuals.** PJM over-retires and MISO
   under-retires; those remain the chartered G-31 lane's (Addendum F.1).
4. **FC-7 fails by construction** on every leg — FFR-3A-2 blocker 5, unchanged.
5. **Nothing promoted, nothing tuned**, no band widened, no damper unarmed.
