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

## 2. STEP-0 GATE VERDICT

*(pending — nothing below §1 was written before the probe ran)*

## 3. Arm K

*(pending)*

## 4. Skill reads — the three-way table

*(pending)*

## 5. The γ rider — instrument-date split

*(pending)*

## 6. Governance close-out

*(pending)*
