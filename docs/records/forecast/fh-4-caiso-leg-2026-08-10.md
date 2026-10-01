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

## 2. Both arms solved clean at the pre-registered posture — I6 rider PASS on both

**Arm R** registered `caiso-2023-2025-t1ff-armr-fh4` (hindcast namespace,
`kind="full_forward"`), solved `[2023, 2024, 2025]`, bridged `[]`,
`leakage_violations: []`, freeze ACTIVE and read at launch, runtime
`cache_key=c407117093ad472e`. Meta records the shipped-defaults posture
exactly as pre-registered: `capacity_screen_unified_lookahead=False`,
`capacity_screen_scarcity_restoration=False`, `retirement_rule="pipeline"`,
`demand_growth_vintage=null`, `weather_posture="solve_year"`, shipped
capacity-clearing posture.

**Arm K** registered `caiso-2023-2025-t1ff-armk-fh4` (same namespace/kind),
solved `[2023, 2024, 2025]`, bridged `[]`, `leakage_violations: []`, freeze
ACTIVE, runtime `cache_key=9759385a44a5ad77`. Meta records the full as-known
posture: gas `hindcast_asknown_aeo2023`, `weather_posture="base_year"`,
`demand_growth_vintage: 2023` — **the CAISO vintage row's first armed solve**:
2024/2025 demand grown at the cited as-of-2023 CEC CEDU 2022 rate
1.30 %/yr instead of the live table's 2.8 %/yr.

*(The prereg §1.2/§1.3 cache keys `cdffce8d15657343` / `0419354e425baa41` are
the built-config keys measured before launch; the runtime keys above differ
because `run_scenario_iso` applies the ISO's default scenario overrides —
the same prereg-vs-runtime relation the protocol of record recorded.)*

**The I6 rider, applied as written — PASS on BOTH registered batteries** (no
year's economic retirement approaches the 20 % cap: total retirements are
0.03 GW in 2024 and 1.12 GW in 2025 against ~50 GW fleets, and none exceed
the cap's fraction). The non-criterion legs stand in both sidecars at full
magnitude:

* **I7 FAIL (both arms)** — accredited firm short of the requirement in
  2023 (49,076 < 50,608 MW) and 2024 (Arm R: 50,377 < 54,707; Arm K:
  50,377 < 51,266 — the as-known demand vintage lowers the requirement).
* **I9 FAIL (both arms)** — simultaneous charge+discharge 0.15–0.27 % of
  storage throughput.
* **I12 WARN (both arms)** — reserve margin under the [15 %, 30 %] band:
  Arm R 11.5 % / **5.9 %** (2023/2024), Arm K 11.5 % / 13.0 %; both recover
  to 15.0 % in 2025 via the reserve backstop (Arm R builds 1.4 + 1.2 GW
  gas_ct in 2024/2025; Arm K 1.4 + 2.8 GW).

Wall clock: ~12.1 min (Arm R) and ~11.3 min (Arm K) on this 15 GB / 4-core
container, cold at the 2026-08-10 epoch (per-year P0 ~100–110 s, P1
~30–60 s) — the sibling-leg cost note for the manager.

## 3. Skill reads — the three-way table

Scored by `score_crossover.py` verbatim against the committed bench and the
CURRENT keeper **`2026-08-09-caiso-188-d1-micseam`**, per the prereg (§1.4).
Quotable as T1-FF skill: the lift is unconditional, both arms ran the
pre-registered shipped-defaults posture, and the I6 rider PASSED on both.
Errors at full magnitude, signed = model − actual; `gap` = input_gap =
|arm err| / |keeper err|. Keeper → Arm R spread = **overlay value**;
Arm R → Arm K spread = **driver-forecast error**.

**price_mean** (fraction of actual):

| Year | Keeper err | Arm R err (gap) | Arm K err (gap) |
|---|---|---|---|
| 2023 | +0.034 | **−0.177** (5.16) | **+0.222** (6.49) |
| 2024 | +0.105 | **+0.237** (2.27) | **+0.686** (6.56) |
| 2025 | +0.129 | **+0.556** (4.30) | **+0.634** (4.90) |

**price_shape** (monthly NRMSE): keeper 0.075 / 0.145 / 0.164; Arm R 0.477
(6.36) / 0.423 (2.92) / 0.585 (3.57); Arm K 0.460 (6.13) / 0.778 (5.37) /
0.662 (4.04).

**fuelmix** (TWh Σ|Δ| over scoreable classes): keeper 7.81 / 5.80 / n/a;
Arm R 27.38 (3.50) / 37.20 (6.41) / n/a; Arm K 18.66 (2.39) / 28.99 (5.00) /
n/a. 2025 is unscoreable in BOTH arms: the preliminary EIA-923 vintage
leaves **no** complete CAISO class actual (unlike ERCOT, where the coal
classes remained) — reported, never banded, in both sidecars.

**co2** (fraction, signed; reported — the keeper record carries no
comparable): Arm R +16.6 / +44.5 / +63.5 %; Arm K +4.6 / +25.6 / +62.8 %.

**Reading, honestly:**

1. **The dominant structural finding is the ENTRY-SIDE UNDER-BUILD, and in
   CAISO it inverts the error sign relative to ERCOT.** Both arms land
   essentially ZERO renewable/storage MW inside the window — the 2024
   decision round decides 6.7 GW of VRE but every COD falls ≥ 2026, so the
   only capacity that actually arrives is the reserve backstop's gas_ct
   (Arm R 2.6 GW, Arm K 4.2 GW across 2024–2025) — against CAISO's actual
   2023–2025 solar/storage build. The fleet tightens (Arm R 2024 reserve
   margin 5.9 %), gas CCs fill the missing VRE energy (2024: model CC
   classes 88.0 TWh vs 52.8 actual in Arm R), and prices overshoot,
   GROWING with distance from base (+23.7 % → +55.6 % in Arm R). Where
   ERCOT's T1-FF signature was coal-zero + price UNDERSHOOT, CAISO's is
   VRE-zero + gas-over + price OVERSHOOT — the FFR-9B VRE-entry shortfall
   extended to CAISO in a more extreme form. Root cause belongs to the
   entry lanes (the FFR-9C menu); nothing here was tuned (rule 1).
2. **2023 (the vintage-true year) realized the pre-registered undershoot
   direction:** Arm R −17.7 % vs the keeper's +3.4 %. The magnitude is far
   smaller than the lost crisis-gas basis alone implies (+$7.06 measured →
   +$1.20 scalar, ~2.6× marginal-fuel understatement): the missing fuel
   cost (−) nets against the same over-tight/over-gas dynamic that
   overshoots 2024/2025 (+) — two opposite-signed structural errors inside
   one signed number. Stated as observed; the decomposition is the lanes'
   work, not this leg's.
3. **Arm K realized all three pre-registered directions**: 2023 higher than
   Arm R (crossing sign: −17.7 % → +22.2 %); 2024 far above (+68.6 % vs
   +23.7 %, the +98 % gas vintage); 2025 near-converged in spread (+7.8 pp
   on the +7.6 % vintage remnant). The K−R spread — the driver-forecast
   error — is **+39.9 / +44.9 / +7.8 pp**, tracking the AEO2023 gas error
   almost one-for-one. Unlike ERCOT (where expensive as-known gas partially
   MASKED a conduct undershoot and printed a deceptively low 2023 gap),
   in CAISO the as-known gas error COMPOUNDS the standing overshoot —
   Arm K is worse than Arm R on price in every year, and no
   error-compensation reading is available on the price level.
4. **Fuel-mix prints Arm K better than Arm R** (18.7 vs 27.4 TWh in 2023,
   29.0 vs 37.2 in 2024) — this IS the error-compensation artifact here:
   the 2.2× as-known gas price suppresses exactly the CC over-dispatch the
   under-built fleet causes. The protocol §4(4) lens applies: an artifact
   of one error masking another, NOT driver skill.
5. **Overlay value (keeper → Arm R):** gaps 2.3–6.4 across price level,
   shape and mix. Two things are bundled in that spread and this leg cannot
   split them: the keeper's measured overlays (monthly delivered gas
   including the 2023 crisis basis, CAMPD outage windows, same-year CEMS
   rates, measured demand) AND the keeper's measured fleet — the backcast
   dispatches the fleet that actually existed, while T1-FF dispatches what
   its own evolution built from the 2023 vintage. The forward-stack price
   of losing both is what the table measures.
6. **co2 overshoots in both arms** (gas-over signature), opposite in sign to
   ERCOT's coal-zero-driven undershoot; Arm K's 2023 +4.6 % is the same
   compensation artifact as (4), not accuracy.
7. **Harness observation (reported for the FH lane, not repaired here):**
   the hydro budget loads the 2023 weather base in EVERY solve year of both
   arms (`data.hydro` log: "CAISO 2023 hydro budget pinned … 17.89 TWh" at
   each year's LP build) — Arm R's "solve-year weather" posture is
   therefore PARTIAL for hydro. Shared by both arms, so the R→K spread is
   unaffected; it does sit inside the keeper→R overlay-value spread.

## 4. The γ rider — not applicable, restated from the artifact record

As pre-registered (§1.5): CAISO has **no scored exit target** —
`data/raw/_validation-source/` carries no `capacity_actuals_caiso.csv`, so
there is no window exit set to split by instrument date, and the exit/
addition skill rows are unscorable for CAISO altogether. The registered
sidecars record that absence explicitly
(`capacity_events_note: "capacity events not scored — no committed
exit/addition target exists for CAISO …"`) via the §1.6 degrade — reported
as absent, never fabricated. The confirmed-exit registry
(`data/raw/confirmed-retirements/caiso.csv`) rode both solves as the step-0
channel input, unaffected by this. **Per the dispatch: stated — not
applicable.**

## 5. Governance close-out

* **Rule 22.** Solves were {2023, 2024, 2025} in both arms — training tier
  only; freeze ACTIVE and read at launch (recorded in both metas); no
  out-of-training year solved/scored/registered; no measured H1-2026
  contact; the scorer's bounds refused nothing because nothing
  out-of-bounds was asked. CAISO's absent `complete` marker was never
  needed — the leg never leaves the training window.
* **Rules 1/13/14.** Nothing tuned toward any residual: the entry-side
  under-build, the growing price overshoot, the I7/I9 FAILs and I12 WARNs,
  the co2 overshoot and the partial-hydro observation are all reported at
  full magnitude and left standing. No bar re-level, no signal scaling, no
  default flip, no keeper contact — the keeper was the comparator only,
  and its recipe flags stayed OFF in both arms as the dispatch ordered.
* **Rule 28 duty (b).** The FH-4-CAISO measurement citation added to the
  `demand_growth_vintage` matrix row (fc-CAISO U→O, measured in the Arm-K
  instrument, not adjudicated); **no verdict cell moved**. The screen-flag
  rows are untouched — this leg never armed them.
* **Rule 27.** Fable; all edits local on-disk bytes; blob verification run
  after every push touching a ≥300-line file (all MATCH).
* **Registration.** Both runs registered regardless of reads:
  `caiso-2023-2025-t1ff-armr-fh4` + `caiso-2023-2025-t1ff-armk-fh4`,
  hindcast namespace only; the backcast registry and the committed
  `frontend/data/forecast/` inputs are untouched.
* **The §1.6 degrade in production:** exercised end-to-end by both scores;
  one seam gap found and fixed in the same session (the driver's selective
  merge initially dropped `capacity_events_note` from the top level —
  caught on the first real scoring run, fixed before Arm K scored, both
  committed sidecars carry the note).
