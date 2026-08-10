# FH-4-CAISO — the CAISO leg of the FH-4 forward-skill battery

**Session.** FH-4-CAISO `[FABLE]`, Wave FH Phase A sibling leg (manager dispatch
pack §0ag). Branch `claude/fh-4-caiso-leg-rk5ste`, off `origin/main` `aa61791e`.
The FH-4 lift is **UNCONDITIONAL** (Addendum AI.1: the ERCOT step-0 gate PASSED
at 0.0 % vs the 26.8 % reference, discharging the AG.2 condition; the five
sibling legs are released per §0ag). This leg therefore has **no step-0 gate**;
the **I6 rider** applies to both arms (§1.7). Protocol of record:
`docs/handoffs/fh-4-ercot-leg-2026-08-09.md`, executed for CAISO at **SHIPPED
DEFAULTS** — no keeper contact, no arming, no tuning.

---

## 1. PRE-REGISTRATION

*Everything in §1 was written and committed BEFORE any solve was launched.
Nothing in §1 changes after. Sections §2+ are filled in order, as produced.
The one code change this lane lands — the `score_crossover` missing-target
degrade (§1.6, scoring-only, solve-untouched) — is committed WITH this prereg,
before any solve.*

### 1.1 Posture: SHIPPED DEFAULTS, measured at prereg

Both arms run the shipped `ScenarioConfig` defaults through the T1-FF
`--forward-from-base` surface. Measured from the built configs at prereg
(nothing asserted from memory):

* `capacity_screen_unified_lookahead = False`, `capacity_screen_scarcity_restoration
  = False` — the shipped defaults; **nothing is armed by invocation** (the §0ag
  shared protocol: the ERCOT-only scarcity restoration *cannot and does not*
  arm here — its validator is ERCOT-only, rule 25 structural).
* `retirement_rule = "pipeline"` via the shipped default (D-1).
* The CAISO **keeper-recipe** flags are NOT armed, per the dispatch:
  `unit_outage_lp_capacity_basis = False`, `capacity_deliverability_limits =
  False` (and no hour-grain outage envelope). The keeper is the skill
  **COMPARATOR only** — its recipe never touches these arms.
* Capacity-price posture: the harness default = the SHIPPED production posture,
  `capacity_market_clearing_by_iso = {PJM, MISO, CAISO, NEISO: True}` — CAISO
  clears its RA position on its published curve, the configuration the
  forecast actually runs (FFR-2E).
* Gas basis: the T1-FF forward stack prices CAISO gas at the trajectory Henry
  Hub + the scalar `GAS_BASIS_DIFFERENTIAL["CAISO"] = +1.20` (SoCal Citygate
  seed). The measured hub-month overlay (`gas_hub_basis_overlay`) is armed only
  by the BACKCAST config assembly (`pipeline/backcast_config.py`) and stays
  OFF here — the forward stack carries no measured overlay, by construction.

### 1.2 Arm R invocation (declared before solving)

```
uv run python scripts/run_capacity_hindcast.py --iso CAISO \
  --forward-from-base --arm realized --vintage 2023 \
  --start-year 2023 --end-year 2025 \
  --out-dir results/hindcast/caiso-2023-2025-t1ff-armr-fh4
```

Config cache key **`cdffce8d15657343`**, measured at prereg. Gas
`hindcast_realized` (HH annual 2.54 / 2.19 / 3.53 $/MMBtu), per-solve-year
weather (`weather_posture="solve_year"`), `demand_growth_vintage = null` (the
registered cache-neutral default; Arm R's growth spans are zero-year by
construction). Registered id `caiso-2023-2025-t1ff-armr-fh4`, hindcast
namespace, `meta.kind="full_forward"`, regardless of what the reads show.

### 1.3 Arm K invocation (declared before solving)

```
uv run python scripts/run_capacity_hindcast.py --iso CAISO \
  --forward-from-base --arm asknown --vintage 2023 \
  --start-year 2023 --end-year 2025 \
  --out-dir results/hindcast/caiso-2023-2025-t1ff-armk-fh4
```

Config cache key **`0419354e425baa41`**, measured at prereg. The as-known
posture at base 2023, all resolved by the arm (the FH-2 §7 wiring landed at
FH-4-ERCOT — **no code change needed here**, the harness already selects it):

* gas `hindcast_asknown_aeo2023` — nominal 5.48 / 4.34 / 3.80 $/MMBtu vs
  realized 2.54 / 2.19 / 3.53: **+116 % / +98 % / +7.6 %**, the ex-ante
  AEO2023 error Arm K exists to measure;
* weather pinned to 2023 for every solve year (`weather_posture="base_year"`);
* demand growth as-of-2023: `demand_growth_vintage = 2023` resolves the CAISO
  row of `DEMAND_GROWTH_RATES_VINTAGES[2023]` — **1.30 %/yr** (CEC CEDU 2022
  "California Energy Demand Forecast 2022–2035", January 2023, statewide
  planning-area proxy; FH-3 intake) vs the live table's 2.8 %/yr near rate.
  The fail-closed wiring is satisfied: the vintage row exists, verified at
  prereg by building the config.

Registered id `caiso-2023-2025-t1ff-armk-fh4`, hindcast namespace,
`meta.kind="full_forward"`, regardless of reads. Runs SEQUENTIALLY after Arm R
(this container is 15 GB / 4 cores — the rule-12 cap note; years sequential
within each invocation).

### 1.4 The skill reads (the §2.1b metric set), pre-registered

From `scripts/score_crossover.py` run verbatim per arm — no new metric, no
re-derivation: `dispatch_skill.metrics` = **fuelmix, price_mean, price_shape**
(+ `co2` reported) per scored year 2023–2025, each carrying `forecast_err`,
`keeper_backcast_err`, `input_gap = |forecast_err| / |keeper_backcast_err|`.

**Keeper comparator: the CURRENT CAISO keeper at this head,
`2026-08-09-caiso-188-d1-micseam`** — RE-VERIFIED in
`frontend/data/backcast/keepers/CAISO.json` at `aa61791e`. The dispatch's
"at this writing" id (`2026-08-09-caiso-184-c1-lpbasis`) did NOT hold: CAISO
moved again after dispatch (the caiso-188 MIC-seam promotion, commit
`e30cacbc`, PR #3825), exactly as the dispatch's RE-VERIFY warning
anticipated. The scorer resolves the keeper from the sharded store itself, so
the read and this prereg agree by construction. Comparator context, quoted
from its shard for reading the three-way honestly (never a target): caiso-188
carries **C3a mean-LMP FAIL 2024 +10.4 % / 2025 +12.9 % (model OVER actual),
2023 C3a PASS**, C3c the single ledgered caveat, determination NOT-YET — the
comparator's price errs are *overshoots* on a structurally-promoted keeper.

The three-way read per metric-year (plan §2.1): keeper err → Arm R err →
Arm K err; the keeper→R spread is the **overlay value**, the R→K spread the
**driver-forecast error**. Both are the program's deliverable, reported at
full magnitude, never targets, never tuned toward.

**Pre-registered directions (to test, never targets):**

* **Arm R 2023 price_mean: a material UNDERSHOOT, gap > 1 expected.** The
  keeper prices 2023 CAISO gas on the measured hub overlay, which carries the
  Dec-22/Jan-23 western gas crisis — measured annual delivered basis **+$7.06**
  over HH (fuel_trajectories.py, EIA-923 Schedule-5 measured check; Jan-2023
  delivered $38.7/MMBtu vs HH $3.27). The forward stack prices the same year
  at HH 2.54 + the +1.20 scalar — roughly **2.6× understated marginal fuel
  cost** at the 2023 gas margin. Losing that overlay is the single largest
  overlay-value term this leg can measure.
* **Arm R 2024/2025: smaller price gaps than 2023.** Measured basis +2.26 /
  +1.12 vs the +1.20 scalar — near-parity, with 2025's scalar slightly ABOVE
  measured, so the fuel-cost error is small and can sit either side.
* **Arm K vs Arm R, 2023:** as-known HH (+116 %) is expected to lift the 2023
  price toward actual — if Arm K's 2023 gap prints below Arm R's, that is the
  ERCOT leg's §4(4) **error-compensation artifact** (wrong driver masking lost
  overlay content), NOT skill, and will be read as such. 2024: Arm K expected
  ABOVE Arm R (+98 % vintage); 2025 near-converged (+7.6 %).
* **Fuel mix:** Arm R's under-priced 2023 gas is expected to push in-CAISO gas
  dispatch UP against actual; Arm K's expensive 2023–2024 gas pushes gas back
  down toward/below actual. Directions only; the measured spread IS the result.
* **co2** is reported (the keeper record carries no comparable), on the same
  full-plant basis the keeper's C5a used.
* **Quoting rule.** The lift being unconditional, these reads are quotable as
  T1-FF skill iff both arms ran the pre-registered shipped-defaults posture
  AND the I6 rider (§1.7) PASSES on both arms.

### 1.5 The γ rider: NOT APPLICABLE for CAISO — stated with the evidence

The exit-target instrument-date split (protocol §1.5) requires the ISO's
scored exit target, `data/raw/_validation-source/capacity_actuals_<iso>.csv`.
**No such file exists for CAISO** — the directory carries
`capacity_actuals_{ercot,miso,neiso,nyiso,pjm}.csv` only; the CAISO file was
never built, and building it is a data intake this dispatch does not order.
There is therefore **no scored exit target in this window to split**, and no
exit/addition skill row can be computed at all (see §1.6 for how the scorer
records that absence). The confirmed-exit registry
`data/raw/confirmed-retirements/caiso.csv` DOES exist and rides the runs as
the step-0 confirmed-exit channel input, but with no actual-exit target there
is nothing to attribute against. Per the dispatch: "exit-target
instrument-date split if applicable, else state so" — **stated: not
applicable.**

### 1.6 The one code change: the missing-capacity-target degrade (scoring-only)

`score_crossover.score_capacity_events` called `CH.load_actuals(iso)`
unguarded, which `SystemExit`s for an ISO with no capacity-actuals target —
taking the entire crossover score (including the dispatch-skill three-way
table, this leg's deliverable) down with it. Every prior full-forward leg was
ERCOT/MISO-side, where the file exists; CAISO is the first leg to hit the
absence. Landed with this prereg, before any solve:

* `score_capacity_events` degrades exactly like `score_dispatch_skill`'s
  missing-keeper path: it records the absence in `capacity_events_note`,
  carries `None` for `retirements` / `additions` / `additions_cod_basis` /
  `additions_basis` (never a fabricated table), and keeps the `co2` block —
  its actual comes from the bench, not the capacity target.
* `write_report` renders the note instead of the (b) tables;
  `register_hindcast.py`'s forecast-validation page branches the same way
  (`forecast_verdict._collect_hindcast_bands` already isinstance-guards, so
  `None` blocks are safe there — verified at prereg).
* Two contract tests pin the degrade
  (`tests/scoring/test_score_crossover.py`). **No `ScenarioConfig` field, no
  solve-affecting change, no cache-key contact** — the change is entirely on
  the scoring/reporting side.

### 1.7 The I6 rider (the §0ag verdict rule for every sibling leg)

Both arms' registered invariant batteries must read **I6 = PASS**
(`check_forecast_invariants.py`: single-year economically-retired capacity ≤
20 % of prior thermal MW, `Thresholds.econ_retire_frac_cap = 0.20`, measured
per evolution year from the run's own ledgers). **An I6 FAIL on either arm is
a stop-the-line report to the manager — the run is still registered, the
verdict + numbers committed, and NO skill numbers are quoted from a
failed-I6 leg.** All other invariants are reported alongside at full
magnitude; they are not the criterion.

### 1.8 Governance

* Holdout freeze read at launch by the harness (recorded in `meta.json`);
  solve years {2023, 2024, 2025} — training-tier only; no out-of-training
  backcast year solved/scored/registered; no measured H1-2026 contact
  anywhere; scoring never leaves 2023–2025 (the scorer refuses both bounds).
  CAISO holds NO `complete` marker (withdrawn 2026-08-06 at caiso-178) — and
  needs none: this leg never leaves the training window.
* Hindcast namespace ONLY — never the backcast registry, never
  `frontend/data/forecast/`. No keeper contact, no promotion, no shipped
  default flip, no matrix cell verdict beyond measurement citations.
  Bar re-levels, signal scaling, tuning toward any residual: refused by name.
* 3 solve-years per invocation; years sequential within an invocation;
  invocations sequential in this container (15 GB / 4 cores).
* Registration commitment: every solved run registers REGARDLESS of verdict
  or reads. Commit order: prereg → results → handoff, as they exist.
* The other sibling ISO legs and FH-5 are NOT this session's; re-litigating
  the lift is refused (the determination is the manager's record).

---

*(Sections below this line are filled AFTER the pre-registered work runs, in
order, as produced.)*
