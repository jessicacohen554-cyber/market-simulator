# FH-4-ERCOT — step-0 gate re-probe + the ERCOT leg of the forward-skill battery

**Session.** FH-4-ERCOT `[FABLE]`, Wave FH Phase A (manager dispatch pack §0ad,
released §0ae). Branch `claude/fh-4-ercot-leg-kudnln`, off `origin/main`
`51d4e98`. The FH-4/FH-5 lift is **CONDITIONALLY GRANTED** (manager
determination, `ffr-owner-sitting-2026-08-02.md` Addendum AG.2, on the FFR-8B
re-based record); **the condition is the step-0 gate below passing.** A step-0
FAIL stops the lane and returns to the manager. No lift-adjacent claims beyond
the gate verdict; no arming beyond what the dispatch names; no keeper contact.

**Baseline epoch.** `docs/handoffs/ffr-9a-storage-vintage-seed-2026-08-09.md`
is THE current ERCOT hindcast baseline (its epoch statement supersedes FFR-8B
§2 as baseline; cache epoch 2026-08-09). Its UNGATED storage vintage-seed fix
and the FFR-3V renewable vintage-seed fix both ride automatically at this
head — nothing here arms them.

---

## 1. PRE-REGISTRATION

*Everything in §1 was written and committed BEFORE any solve was launched.
Nothing in §1 changes after. Sections §2+ are filled in order, as produced.
The one code change this lane lands — the Arm K `demand_growth_vintage`
wiring (§1.3) — is committed WITH this prereg, before any solve.*

### 1.1 The step-0 gate, as written

**Criterion (FH-1 §3.3 / handoff §7, applied AS WRITTEN).** The I6
over-retirement invariant of `scripts/check_forecast_invariants.py`:
single-year economically-retired capacity as a fraction of prior thermal MW,
cap **0.20** (`Thresholds.econ_retire_frac_cap`), measured per evolution year
from the run's own ledgers. The FAIL reference at the pre-fix posture is the
registered `ercot-2023-2025-t1ff-armr-fh1gate` sidecar: **2025: 26.8 % of
prior thermal economically retired in one year — I6 FAIL** (21.05 GW of
78.5 GW), with the full FC-1 signature I6 FAIL / I7 FAIL / I12 WARN.

**Verdict rule.** The gate **PASSES iff the re-probe's registered invariant
battery reads I6 = PASS** (no year's economic retirement exceeds 20 % of
prior thermal). I7 and I12 are reported alongside at full magnitude — they
are the FH-1 signature's other two legs, not the criterion. **FAIL → the
lane STOPS**: the probe is registered, the verdict + numbers are committed,
the record goes to the manager, and nothing further runs.

**Probe recipe (FH-1 §7 AS WRITTEN, at the determined posture).** ERCOT,
base 2023, vintage 2023, window 2023–2025 (3 solve-years), Arm R — with
`capacity_screen_unified_lookahead` + `capacity_screen_scarcity_restoration`
**ARMED BY INVOCATION** (the manager's arming determination, AG.2 ruling 1;
NOT a `ScenarioConfig` default flip — shipped defaults are untouched, and
every other field rides the shipped default, including `retirement_rule`
`"pipeline"` per D-1):

```
uv run python scripts/run_capacity_hindcast.py --iso ERCOT \
  --forward-from-base --arm realized --vintage 2023 \
  --start-year 2023 --end-year 2025 \
  --capacity-screen-unified-lookahead --capacity-screen-scarcity-restoration \
  --out-dir results/hindcast/ercot-2023-2025-t1ff-armr-fh4gate
```

**Expectation (to test, never a target).** PASS is expected: at this head the
same determined posture read **I6 PASS / I7 PASS** on both FFR-9A arms at
base 2021 (vintage 2020, 4 solve-years). Whether that holds at base
2023 / vintage 2023 — the FH-1 FAIL's own base — is exactly the probe's
question, and the criterion is applied as written whatever comes out.

### 1.2 The gate probe IS Arm R (declared before solving)

The FH-1 §3.3 recipe at the determined posture is **configurationally
identical** to FH-4's Arm R (same arm, window, vintage, arming; config cache
key `6378154a8d573597`, measured at prereg). One solve therefore serves both
roles, and no second identical 3-LP-year solve is burned:

* registered ONCE, id `ercot-2023-2025-t1ff-armr-fh4gate` (hindcast
  namespace, `meta.kind="full_forward"`), regardless of verdict;
* on gate **PASS**, its `crossover_score.json` is the **Arm R skill read**;
* on gate **FAIL**, its dispatch numbers are **GATE CONTEXT ONLY** (the FH-1
  §7(b) rule) and no skill is quoted.

### 1.3 Arm K invocation + the FH-2 §7 wiring landed here

**The wiring (this lane's one code change, committed with this prereg).**
FH-2 §7 assigned FH-4 the harness wiring *"`--arm asknown` should set
`demand_growth_vintage = base_year` alongside its gas path"*; FH-3 landed the
cited values. `run_capacity_hindcast.build_config` now sets
`demand_growth_vintage = start_year` for `--forward-from-base --arm asknown`
only — selected by the arm exactly like its gas path, no new flag, no
`ScenarioConfig` default touched, fail-closed on any base year without an
intaken vintage table. Arm R and both non-T1-FF modes pass `None` (the
registered cache-neutral default), so every existing posture's cache key is
unchanged — pinned by three new contract tests in
`tests/scoring/test_full_forward_hindcast.py` (43 pass). Recorded in
`meta.json` as `FromConfig` so the sidecar reads the solved posture.

**Arm K posture, resolved at this head** (base 2023): gas
`hindcast_asknown_aeo2023` (nominal 5.48 / 4.34 / 3.80 $/MMBtu vs realized
2.54 / 2.19 / 3.53 — **+116 % / +98 % / +7.6 %**, the ex-ante AEO2023 error
Arm K exists to measure); weather pinned to 2023 for every solve year;
demand growth as-of-2023 ERCOT LTLF **2.433 %/yr** (vs the live table's
8.5 %/yr the pre-wiring harness would have leaked). Config cache key
`cf5dac53df3c8414` at prereg.

```
uv run python scripts/run_capacity_hindcast.py --iso ERCOT \
  --forward-from-base --arm asknown --vintage 2023 \
  --start-year 2023 --end-year 2025 \
  --capacity-screen-unified-lookahead --capacity-screen-scarcity-restoration \
  --out-dir results/hindcast/ercot-2023-2025-t1ff-armk-fh4
```

Registered id `ercot-2023-2025-t1ff-armk-fh4`, hindcast namespace,
`meta.kind="full_forward"`, regardless of what the reads show. Runs ONLY on
gate PASS; sequential after the gate probe (this container is 15 GB / 4
cores — the FFR-9A rule-12 cap note; years sequential within each
invocation).

### 1.4 The skill reads (the §2.1b metric set), pre-registered

From `scripts/score_crossover.py` run verbatim per arm — no new metric, no
re-derivation: `dispatch_skill.metrics` = **fuelmix, price_mean, price_shape**
(+ `co2` reported) per scored year 2023–2025, each carrying `forecast_err`,
`keeper_backcast_err`, `input_gap = |forecast_err| / |keeper_backcast_err|`.
Keeper comparator: the CURRENT ERCOT keeper at this head,
**`2026-08-09-run181-position-tail`** (re-verified in
`frontend/data/backcast/keepers/ERCOT.json` — the dispatch's "at this
writing" id holds). The three-way read per metric-year (plan §2.1): keeper
err → Arm R err → Arm K err; the R-vs-keeper spread is the **overlay value**,
the K-vs-R spread the **driver-forecast error**. Both are the program's
deliverable, reported at full magnitude, never targets, never tuned toward.

**Pre-registered directions (to test, never targets):**

* **Arm R**: gaps expected materially below the FH-1 pre-fix probe's
  defect-dominated reads (price_mean input_gap 2.1 / **54.0** / 2.3, fuelmix
  9.8 / 13.6 / **28.1**) — those were adjudicated products of the retirement
  wave (2024 price from the pre-wave tight fleet, 2025 mix from the post-wave
  gutted one). No magnitude pre-registered.
* **Arm K vs Arm R**: price errors expected HIGHER in 2023–2024 (the +116 % /
  +98 % as-known gas vintage) and near-converged by 2025 (+7.6 %); fuel-mix
  expected to shift against gas in 2023–2024 (gas-coal switching under a
  2.2× gas price). Directions only; the measured spread IS the result.
* **Quoting rule (the AG.2 condition, restated).** These reads are quoted as
  T1-FF skill ONLY if the gate PASSED and the arm ran the determined posture.
  Otherwise they are gate context only.

### 1.5 The γ rider: instrument-date split of the window's actual exits

**Purpose (AG.2 γ rider).** The exit-side skill number must never be
mis-attributed: the T1-FF confirmed-exit channel is information-gated at
`confirmed_registry_as_of = date(vintage, 12-31)` = **2023-12-31**, so a
window exit whose enforceable instrument post-dates the cutoff is invisible
to that channel BY DESIGN — the information gate working, not a screen miss.

**Method (solve-independent; computed from committed artifacts only).** Take
the scorer's own target rows (`data/raw/_validation-source/
capacity_actuals_ercot.csv`, `kind="retirement"`) for the leg's window
2023–2025; match `(plant_id, unit/generator_id)` against the confirmed-exit
registry `data/raw/confirmed-retirements/ercot.csv`; split the actual MW
into instrument-dated **≤ 2023-12-31** vs **after / no instrument**. Also
reported for the 2021–2025 window — the referent of the dispatch's
"2.294 GW" figure (the FFR-8B window) — so the two windows' numbers are
never conflated. (Registry fact visible at prereg, stated for honesty: the
ERCOT registry carries exactly three rows — V H Braunig 1/2/3, instruments
dated 2024-03-13 / 2025-02-24 — all post-cutoff, so the ≤-cutoff share is
expected to be ~0. The split is still computed and reported from the
artifacts.)

### 1.6 Governance

* Holdout freeze read at launch by the harness (recorded in `meta.json`);
  solve years {2023, 2024, 2025} — training-tier only; no out-of-training
  backcast year solved/scored/registered; no measured H1-2026 contact
  anywhere; scoring never leaves 2023–2025 (the scorer refuses both bounds).
* Hindcast namespace ONLY — never the backcast registry, never
  `frontend/data/forecast/`. No keeper contact, no promotion, no shipped
  default flip, no matrix cell verdict beyond gate/measurement citations.
  Bar re-levels, signal scaling, tuning toward any residual: refused by name.
* ≤5 solve-years per invocation; years sequential within an invocation;
  invocations sequential in this container (15 GB / 4 cores).
* Registration commitment: every solved run registers REGARDLESS of verdict
  or reads. Commit order: prereg → gate verdict → results → handoff, as they
  exist.
* The five sibling ISO legs and FH-5 are NOT this session's (manager
  dispatches on a committed gate PASS); re-litigating the lift is refused
  (the determination is the manager's record).

---

*(Sections below this line are filled AFTER the pre-registered work runs, in
order, as produced.)*

## 2. STEP-0 GATE VERDICT — **PASS**

Probe run exactly as pre-registered (§1.1): registered
`ercot-2023-2025-t1ff-armr-fh4gate` (hindcast namespace,
`kind="full_forward"`), solved `[2023, 2024, 2025]`, bridged `[]`,
`leakage_violations: []`, holdout freeze ACTIVE and read at launch, runtime
`cache_key=e1714e3d41d0b979`, meta records the solved arming
(`capacity_screen_unified_lookahead=True`,
`capacity_screen_scarcity_restoration=True`, `retirement_rule="pipeline"` via
the shipped default, `demand_growth_vintage=null` — Arm R).

**The I6 criterion, applied as written — PASS in every year:**

| Year | Prior thermal | Econ retired | I6 fraction | FH-1 reference (pre-fix) |
|---|---|---|---|---|
| 2023 | 78.2 GW | 0.00 GW | **0.0 %** | 0.0 % |
| 2024 | 78.2 GW | 0.00 GW | **0.0 %** | 0.0 % |
| 2025 | 78.5 GW | 0.00 GW | **0.0 %** | **26.8 % — I6 FAIL** (21.05 GW) |

The registered invariant battery reads **I6 PASS** (cap 20 %, no year
exceeds it), and the wave is gone ENTIRELY, not reclassified: total
retirements of ANY reason are 0.00 GW in all three ledgers. **I7 PASS** (the
reliability floor held — the FH-1 signature's second FAIL leg also clears).
**I12 WARN remains**, now on the LOW side: reserve margin 2023 7.8 % and
2024 13.3 % sit under the scalar floor band [13.8 %, 28.7 %] (the FH-1 probe
was out on the high side, 2024 30.2 %); reported at full magnitude, not the
criterion. 14 checks: 0 FAIL, 1 WARN.

Screen context (ledger/log record, not tuned): the 2025 unified-lookahead
screen prices the thermal cohorts' net revenue far above their going-forward
bars (coal $514.0 vs $58.5/kW-yr bar; gas_cc $549.8 vs $30.0; gas_ct $463.0
vs $21.0; gas_st $390.2 vs $35.0), so the two-consecutive-loss counters never
mature — the s3/G-31 defect signature does not form at the determined
posture. In-window economic executions are 0 (the FFR-7C falsification bound
HOLDS).

**Consequence.** The AG.2 condition is met at base 2023 / vintage 2023 — the
posture the FH-1 FAIL was measured on. Phase A's ERCOT leg proceeds; per
§1.2 this probe IS Arm R, so its `crossover_score.json` is quotable as the
Arm R skill read (§4).

## 3. Arm K — solved clean at the pre-registered posture

Registered `ercot-2023-2025-t1ff-armk-fh4` (hindcast namespace,
`kind="full_forward"`), solved `[2023, 2024, 2025]`, bridged `[]`,
`leakage_violations: []`, freeze ACTIVE and read at launch, runtime
`cache_key=74323d2ef75551dd`. Meta records the full as-known posture: gas
`hindcast_asknown_aeo2023`, `weather_posture="base_year"`,
`demand_growth_vintage: 2023` (the §1.3 wiring's first armed solve — 2024/25
demand grown at the cited as-of-2023 LTLF 2.433 %/yr), both screen flags
armed, `retirement_rule="pipeline"` via the shipped default. The FFR-9A
vintage storage seed fired in both arms (`ERCOT 2023: 5 measured EIA-860
storage units (3814 MW incl. pumped storage)` — the vintage-2023 measured
fleet to the decimal).

Invariants: **I6 PASS** (2025 economic retirement 1.14 GW = **1.5 %** of
prior thermal — two orders under the cap). Two FAILs, reported at full
magnitude: **I7 FAIL** — the 2025 exit leaves thermal 77,382 MW, 1,145 MW
under the retirement-bounded floor 78,527 MW; the exit is an 11-tranche,
3-plant **gas_st** economic wave (1,144.4 MW: plants 56708 / 3628 / 4266 /
3507, South_Central + North) decided at the as-known 2024→2025 screen.
**I12 FAIL** — reserve margin below the scalar floor band in all three years
(7.8 / 11.2 / 7.2 % vs [13.8 %, 28.7 %]; the Arm R probe had two years out,
WARN). Neither is the gate criterion (the step-0 gate is Arm R's, §2);
both stand in the sidecar.

## 4. Skill reads — the three-way table

Scored by `score_crossover.py` verbatim against the committed bench and the
CURRENT keeper `2026-08-09-run181-position-tail`, per the prereg (§1.4).
Quotable as T1-FF skill: the gate PASSED and both arms ran the determined
posture. Errors at full magnitude; `gap` = input_gap = |arm err| / |keeper
err|. Keeper → Arm R spread = **overlay value**; Arm R → Arm K spread =
**driver-forecast error**.

**price_mean** (fraction of actual, signed = model − actual):

| Year | Keeper err | Arm R err (gap) | Arm K err (gap) |
|---|---|---|---|
| 2023 | 0.325 | **−0.651** (2.01) | **−0.292** (0.90) |
| 2024 | 0.025 | **−0.149** (6.00) | **+0.185** (7.47) |
| 2025 | 0.080 | **−0.136** (1.69) | **−0.092** (1.14) |

**price_shape** (monthly NRMSE): keeper 0.602 / 0.205 / 0.101; Arm R 1.137
(1.89) / 0.682 (3.33) / 0.162 (1.60); Arm K 0.948 (1.58) / 0.327 (1.60) /
0.155 (1.54).

**fuelmix** (TWh Σ|Δ| over scoreable classes): keeper 11.28 / 6.46 / 2.39;
Arm R 99.4 (8.8) / 115.3 (17.9) / 62.2 (26.0); Arm K 96.8 (8.6) / 90.5
(14.0) / 62.2 (26.0).

**co2** (fraction, reported — keeper record carries no comparable): Arm R
−35.2 / −27.6 / −35.4 %; Arm K −47.8 / −44.3 / −40.8 %.

**Reading, honestly:**

1. **The FH-1 defect artifacts are gone.** The pre-fix probe's 2024
   price_mean gap of 54.0 (pre-wave tight fleet) reads 6.00 at the
   determined posture; its 2025 mix was post-wave-gutted, this one is not.
   The pre-registered direction (gaps materially below the defect-dominated
   reads) held everywhere except the 2025 fuelmix gap, which is unchanged —
   see (2): it was never wave-driven.
2. **The dominant structural gap is COAL-ZERO, and it is the leg's headline
   overlay-value finding.** Both arms dispatch **0.0 TWh of coal in every
   year** against actuals of 60.4 / 61.5 / 62.2 TWh (COAL_PRB +
   COAL_LIGNITE) — the entire 2025 fuelmix error (62.2 TWh, identical
   across arms because the preliminary-vintage 2025 actuals leave only the
   coal classes scoreable) and most of 2023/2024's. The FH-1 probe showed
   the same property, so it is a standing T1-FF forward-stack behavior at
   base 2023, not an artifact of this arming: without the backcast's
   measured overlays and with the forward coal price flat at
   `COAL_PRB_BASE`-level (the FH-3 §6 DISCLOSE line — pre-2026 coal carries
   zero historic signal), the binned coal fleet never clears into merit.
   It also drives the CO2 undershoot (−28…−48 %). Root cause belongs to the
   coal-economics / fuel-trajectory lanes; nothing here was tuned (rule 1).
3. **Overlay value on price level (Arm R):** −65.1 % in 2023 vs the keeper's
   −32.4 % — the forward stack roughly doubles the keeper's known
   model-class 2023 undershoot (C3a-2023, the ledgered scarcity/conduct
   limitation) because it also loses the overlays' conduct content. In
   2024/2025 Arm R holds −14.9 / −13.6 % against keeper errs of 2.5 / 8.0 %.
4. **Driver-forecast error (Arm K vs Arm R) realized the pre-registered
   directions:** the +116 % as-known 2023 gas lifts the 2023 price from
   −65.1 % to −29.2 % — an error-compensation artifact (wrong driver
   masking missing conduct content), NOT skill, even though the 2023 gap
   prints 0.90 (< 1, nominally "better than the keeper"). 2024 flips to
   +18.5 % overshoot (+98 % gas vintage); 2025 nearly converges (−9.2 %,
   +7.6 % gas vintage). Fuel-mix moved WITH the gas error in 2024 (90.5 vs
   115.3 — expensive as-known gas pushes gas classes down toward their
   actuals) — the direction the prereg named for 2023–2024, realized in
   2024; in 2023 the mix is R-equal (96.8 vs 99.4) because coal-zero (2)
   caps what any gas-price change can move.
5. **Exit side (with §5's rider attached):** Arm R retires nothing
   (`total_gw` 0.0 vs the scorer's window-unfiltered 2.294 actual, the
   under-side FAIL FFR-8B/9A recorded); Arm K's as-known screen produces a
   1.14 GW gas_st econ wave (false-retire 0.256 GW vs the file's 0.888 GW
   gas_st actual). Zero MW of the actual exits were confirmed-knowable at
   the vintage cutoff (§5), so both arms' exit-side rows measure the
   economic/announced channel only.
6. **Entry side (reported, FFR-4/5 lanes' object):** decision-basis
   additions Arm R 26.4 GW / Arm K 17.4 GW vs 55.4 GW actual — the VRE
   build shortfall FFR-9B is chartered to diagnose persists in both arms
   (wind 5.0/1.7 vs 12.7 actual; solar 5.0/5.0 vs 25.1).

## 5. The γ rider — instrument-date split

Computed by `scripts/probes/fh4_instrument_date_split.py` from the committed
artifacts only (§1.5 method), solve-independent; the probe and its numbers
were committed before either arm ran.

**First, what the scorer's "2.294 GW actual" actually spans** — verified in
`score_capacity_hindcast.score_retirements`: the target set is the ENTIRE
committed `capacity_actuals_ercot.csv` (2021–2025, thermal + biomass =
2,293.9 MW), **never filtered to the bundle's window**. A 2023–2025 leg's
exit-side row (`sc.retirements.total_gw: model 0.0 vs actual 2.294, FAIL`)
therefore counts 2021–2022 exits its vintage-2023 fleet basis predates. The
leg's own window (2023–2025) holds 1,939.8 MW of actual exits, 1,772.6 MW
thermal (1,782.2 MW on the scorer's thermal+biomass family set).

**The instrument-date split at the vintage cutoff 2023-12-31:**

| Window | Actual exits (all) | Instrumented ≤ cutoff | Instrumented after | No instrument in registry |
|---|---|---|---|---|
| 2023–2025 (the leg's) | 1,939.8 MW | **0.0 MW** | 477.0 MW | 1,462.8 MW |
| 2021–2025 (the scorer's / the "2.294 GW" referent) | 2,680.3 MW | **0.0 MW** | 477.0 MW | 2,203.3 MW |

The 477 MW is V H Braunig 1/2 (gas_st, exited 2025), instrument dated
**2024-03-13** (ERCOT NSO suspension-retirement acceptance) — after the
cutoff. Every other window exit (Coleto Creek coal 1,008 MW included)
carries no enforceable instrument in the confirmed-exit registry at all.

**Attribution (the AG.2 γ rider's point).** ZERO MW of the window's actual
exits were knowable-as-confirmed at the vintage cutoff: the T1-FF
confirmed-exit channel (`confirmed_registry_as_of = 2023-12-31`) could not
carry ANY of them, by the information gate's own design. The exit-side FAIL
row on these arms is therefore an **economic/announced-channel miss measured
against exits that were not confirmed-knowable at the base date** — it must
not be read as the confirmed-exit mechanism failing, and equally must not be
excused: whether the economic screen *should* anticipate unconfirmed exits
of this kind is precisely the FFR retirement-lane question (FFR-8B §2.2
recorded the same 0.0-vs-actual under-side FAIL), untouched here.

## 6. Governance close-out

* **The AG.2 condition is DISCHARGED for the ERCOT leg**: the step-0 gate
  PASSED (§2) and both arms ran the determined posture, so the §4 reads are
  quotable as T1-FF skill. The five sibling ISO legs and FH-5 remain the
  manager's dispatches; nothing here re-litigates the lift.
* **Rule 22.** Solves were {2023, 2024, 2025} in both arms — training tier
  only; freeze ACTIVE and read at launch (recorded in both metas); no
  out-of-training year solved/scored/registered; no measured H1-2026
  contact; the scorer's bounds refused nothing because nothing out-of-bounds
  was asked.
* **Rules 1/13/14.** Nothing tuned toward any residual: the coal-zero
  finding, the I7/I12 FAILs on Arm K, the exit-side under-miss and the VRE
  entry shortfall are all reported at full magnitude and left standing. No
  bar re-level, no signal scaling, no default flip, no keeper contact.
* **Rule 28.** No new `ScenarioConfig` field (the wiring engages FH-2's
  registered field from the harness). Duty (b): the FH-4 measurement
  citations added to `capacity_screen_unified_lookahead`,
  `capacity_screen_scarcity_restoration` and `demand_growth_vintage`
  (fc-ERCOT U→O, measured-not-adjudicated); **no verdict cell moved** —
  both screen rows stay O with the adjudication the manager's.
* **Rule 27.** Fable; all edits local on-disk bytes; blob verification run
  after every push touching a ≥300-line file (all MATCH).
* **Registration.** Both runs registered regardless of reads:
  `ercot-2023-2025-t1ff-armr-fh4gate` + `ercot-2023-2025-t1ff-armk-fh4`,
  hindcast namespace only; the backcast registry and
  `frontend/data/forecast/` committed inputs are untouched.
* **Cost note for the sibling legs** (manager's planning): each 3-solve-year
  ERCOT arm ran ~8–10 min wall on a 15 GB / 4-core container (P0 ~140–190 s,
  P1 ~28–71 s per year), cold at the 2026-08-09 epoch.
