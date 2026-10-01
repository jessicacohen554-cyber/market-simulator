# PRECOMMIT — capx D84: the PJM THERMAL ELCC delivery-year vintage axis

**Lane:** capx D84, executing `FINDING-capx-d75r-2026-09-06.md` §6 item 4 under **OWNER RULING Q60**
(2026-09-07, capx ledger §0bd.3(c) — *"D84 first, D83 after"*). Branch
`claude/capx-d84-thermal-elcc-vintage-cblmzl`. **DATA PROFILE: pjm.** MODEL: Opus.

**Pushed BEFORE the first solve.** Everything below — the object, the vintage rule, the
fall-through rule, the per-class per-delivery-year prediction, the consumer enumeration, the
G-DRIFT audit, the named screen year and the pre-registered gate legs — is fixed here and is not
re-writable against a result.

**GATED DEFAULT-OFF. NOTHING IS ARMED, and this charter does not authorize an arm** — arming is an
owner card this lane SERVES, never an act it takes.

---

## 0. The object, exactly

`constants.THERMAL_ELCC_CLASS_RATING_BY_ISO["PJM"]` (`src/market_sim/config/capacity_market.py`)
is a **SINGLE-VINTAGE** table — its own comment says so: *"the 2026/2027 BRA official/final
class-average rating"*. But `THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO["PJM"] ==
"2025/2026"`, so **DY 2025/2026 is the FIRST delivery year accredited on the ELCC-class design at
all** — and it has its own published final class ratings, which differ:

| model fuel | PJM published class | 2026/27 (wired) | 2025/26 3IA (published for that DY) | Δ |
|---|---|---|---|---|
| `nuclear` | Nuclear | 0.95 | 0.95 | **0.00** |
| `coal` | Coal | 0.83 | 0.83 | **0.00** |
| `gas_cc` | Gas Combined Cycle | 0.74 | **0.78** | **+0.04** |
| `gas_ct` | Gas Combustion Turbine | 0.60 | **0.63** | **+0.03** |
| `gas_st` | Steam | 0.73 | **0.74** | **+0.01** |
| `oil` | Diesel Utility | 0.91 | **0.92** | **+0.01** |
| `biomass` | *(none published)* | UCAP | UCAP | **0.00** |

One post-reform rating table is therefore applied to a delivery year that settled under a different
published rating set. **This is the thermal transpose of D75-R** (owner ruling Q55, ARMED at r#55),
which fixed the identical defect on the VRE axis, and it follows that lane's shape without
inventing a third form.

**THE BASIS IS RULE 14 `[R-ACCURATE]`, NEVER THE RESIDUAL.** The delivery year's own published
rating is preferred over a rating published for a different year. If the repair makes a scored band
worse, that is rule 14's *"treat the worse fit as a discovered bug"* case and it is reported at full
magnitude; the 2026/27 table is not restored because it fits better, and no vintage is selected by
what it does to a criterion (rule 1 `[R-STRUCT]`).

---

## 1. What is BUILT (all default-off, nothing armed)

| piece | where |
|---|---|
| registry | `THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO["PJM"]`, keyed by delivery-year label |
| gate | `ScenarioConfig.pjm_thermal_accreditation_vintage`, **default-OFF** |
| predicate | `retirements.thermal_accreditation_vintage_armed` |
| resolver | `resolve_thermal_vintage_rating`, at the TOP of `thermal_accreditation_fraction`'s `elcc_class_rating` branch |
| harness | `run_capacity_hindcast.py --pjm-thermal-accreditation-vintage` |
| tests | `tests/unit/data/test_thermal_elcc_vintage_ratings.py` (14, all pass) |
| matrix | base row in `mechanism-matrix.js` + a cell in **all seven** shards (rule 28 duty c) |

**The predicate requires THREE conditions** — the field, **`pjm_accreditation_design_vintage`
(D48's own gate)**, and a registry entry for the ISO. So this is a **sub-gate inside the D48
family**, never a mechanism beside it: the RATING axis can never be devintaged while the BASIS axis
is not (rule 19 `[R-ONE-MECH]` — a mixed accreditation vintage is the failure D45 §2.2 measured).
**Why a separate key** rather than reusing D48's: D48 is ARMED for PJM through
`iso_configs._pjm_config`, so keying off it alone would arm an untested mechanism **by default** in
every PJM forecast run and move the shipped `pjm-t1h` key — the same argument that earned D75-R its
own key.

---

## 2. (a) THE INTAKE IS ALREADY THERE — confirmed, with the rows quoted

D75-R §6 item 4 states *"The intake now carries them"*. **Confirmed independently.**
`data/raw/capacity-market/elcc/pjm/pjm.csv` (258 lines, committed) carries seven
`2025/2026 3IA (final for DY 2025/2026; posted 2025-03-12)` rows, all `elcc_type=class_average`:

```
PJM,Nuclear,                         2025/2026 3IA (...posted 2025-03-12),elcc_pct=95,class_average
PJM,Coal,                            2025/2026 3IA (...posted 2025-03-12),elcc_pct=83,class_average
PJM,Gas Combined Cycle,              2025/2026 3IA (...posted 2025-03-12),elcc_pct=78,class_average
PJM,Gas Combustion Turbine,          2025/2026 3IA (...posted 2025-03-12),elcc_pct=63,class_average
PJM,Gas Combustion Turbine Dual Fuel,2025/2026 3IA (...posted 2025-03-12),elcc_pct=79,class_average
PJM,Diesel Utility,                  2025/2026 3IA (...posted 2025-03-12),elcc_pct=92,class_average
PJM,Steam,                           2025/2026 3IA (...posted 2025-03-12),elcc_pct=74,class_average
```

alongside the `2026/2027 BRA (official/final)` set (95 / 83 / 74 / 60 / 78 / 91 / 73) and the
`2027/2028 BRA (official/final)` set (95 / 83 / 74 / 61 / 77 / 92 / 72). **No intake card is
needed.**

**ZERO SCALAR FIELDS** — the D67 / D75-R standard, met: every rating is digitized from those
committed rows and reconciled against them **by test**, never typed
(`test_every_rating_rederives_from_the_committed_rows`). And, unlike D75-R, there is **not even one
reconciliation to declare**: PJM rates each of the model's thermal classes with exactly ONE
published class, so the cross-vintage solar mix has no analogue here and none is introduced
(rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`).

---

## 3. (b) THE VINTAGE RULE and THE FALL-THROUGH RULE — fixed HERE, before any solve

**ADMISSIBILITY.** A published rating enters the registry **iff** it is (i) `elcc_type ==
"class_average"` — the construct the accredited-UCAP census is built from, so every `marginal`
indicative row is excluded — **and** (ii) an **official/FINAL** posting *for that delivery year*, so
every *"preliminary, non-binding, indicative"* row is excluded. Applied to the committed csv this
admits **exactly three** PJM vintages: **2025/2026 3IA** (final for DY 2025/2026, posted
2025-03-12), **2026/2027 BRA** (official/final), **2027/2028 BRA** (official/final). Asserted
against the csv by test, not assumed — and the test also proves the marginal series is genuinely
present, so the exclusion is not vacuous.

**WHICH PUBLISHED TABLE GOVERNS WHICH DELIVERY YEAR.** Each delivery year is read at **its own
FINAL published ratings**. For DY 2025/2026 that is the **3IA posting of 2025-03-12** — the same
posting D75-R's own 2025/2026 VRE row reads, and the same *"what did this delivery year actually
settle on"* question its 2024/2025 row answers with the December-2023 final study rather than the
December-2021 preliminary set.

**THE KNOWN TRAP, and why the alternative is NOT AVAILABLE (D75-R §6 item 3).** The 2025/26 BRA was
held in July 2024 and cleared on the ratings current then; **that report's tables are IMAGES THAT
DO NOT EXTRACT**. A BRA-vintage rule cannot be sourced, so it is not available to this lane. The
rule actually used is stated here rather than left implicit, and **neither rule is selectable by a
result**.

**THE PRE-REFORM RULE — the two axes COMPOSE, they do not STACK.** A delivery year strictly before
`THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO["PJM"]` is **UCAP `1 − EFORd`** under
`pjm_accreditation_design_vintage`, and it **never reaches this registry at all**:
`resolve_thermal_accreditation_basis` has already returned `"ucap"`, so the `elcc_class_rating`
branch — the registry's only reader — is not taken. Locked by
`test_pre_reform_years_never_reach_the_registry`.

**THE FALL-THROUGH RULE — NO HOLD-LAST, deliberately**, the same choice D75-R made and for the same
reason. A delivery year past the last tabulated one (2028/2029 onward) falls straight through to the
incumbent single-vintage `THERMAL_ELCC_CLASS_RATING_BY_ISO`, which **IS** the 2026/27 set and is the
right basis wherever no other final rating is published (2028/29+ carries only preliminary marginal
ratings, which admissibility excludes). Carrying a rating forward past its own posting would rebuild
the very mixed-vintage error the registry removes. Locked by
`test_no_hold_last_past_the_last_tabulated_delivery_year`.

**THE CLASS MAPPING IS UNCHANGED.** The axis moves the VINTAGE only; it reuses the incumbent table's
model-fuel → PJM-class mapping exactly (`gas_ct` → *Gas Combustion Turbine*, **not** Dual Fuel;
`oil` → *Diesel Utility*; `gas_st` → *Steam*), and `biomass`, which PJM does not rate, stays absent
and keeps UCAP. Re-mapping a class would be a second mechanism on the same phenomenon (rule 19).

---

## 4. (c) THE PREDICTION — per fuel class, per delivery year, in accredited MW

Instrument: `docs/handoffs/d84/thermal-elcc-vintage-phase0-2026-09-07.py` → `.json` (**zero LP**;
it calls the SHIPPED code path — `thermal_accreditation_fraction` /
`resolve_thermal_accreditation_basis` / `thermal_accreditation_vintage_armed` — under a control
config and an armed one that differ in exactly one field).

**IN-TABLE vs FALL-THROUGH, over the 2021–2025 window.** Under the D48 arm (which `_pjm_config`
ships for PJM), **exactly ONE window delivery year sits on the ELCC axis at all**:

| DY | model year | basis (both arms) | on this axis? |
|---|---|---|---|
| 2021/2022 | 2021 | `ucap` | no — pre-reform |
| 2022/2023 | 2022 | `ucap` | no — pre-reform |
| 2023/2024 | 2023 | `ucap` | no — pre-reform |
| 2024/2025 | 2024 | `ucap` | no — pre-reform |
| **2025/2026** | **2025** | `elcc_class_rating` | **YES — in-table (3IA)** |

Delivery years 2026/2027 and 2027/2028 are in-table but **outside the window**; 2026/2027 is an
exact **no-op** against the incumbent by construction (asserted by test), and 2028/2029 onward
**falls through**.

**THE POINT PREDICTION, DY 2025/2026** — on the entering fleet of the nearest available PJM bundle
(`pjm-2021-2025-realized-t1h-d78-sectorgate`, key `bb6a60239d69508b`):

| fuel | entering nameplate MW | Δ rating | **Δ accredited MW** |
|---|---:|---:|---:|
| `gas_cc` | 56,425.7354 | +0.04 | **+2,257.0294** |
| `gas_ct` | 25,791.0700 | +0.03 | **+773.7321** |
| `oil` | 4,136.5000 | +0.01 | **+41.3650** |
| `gas_st` | 771.2000 | +0.01 | **+7.7120** |
| `coal` | 40,652.3960 | 0.00 | **0.0000** |
| `nuclear` | 32,672.1000 | 0.00 | **0.0000** |
| `biomass` | 1,999.4000 | 0.00 (UCAP) | **0.0000** |
| **total** | | | **+3,079.838516** |

Every other window delivery year: **exactly 0.000 MW**. Window total **+3,079.838516 MW**, **sign
UP**. Reference-bundle screen position 1.011564 → predicted **≈1.032886** (requirement 144,450.0 MW,
which D67's published operand makes independent of the model's peak, so it does not move).

**THE IDENTITY THIS LANE IS GRADED ON — and why the point value above is an ANCHOR, not the number.**
Thermal accreditation is `pmax × fraction` with the fraction uniform inside a fuel class, so

> **Δ accredited(DY 2025/26) = Σ_fuel  nameplate_entering_2025,fuel × Δrating_fuel**

exactly. Phase 0 checks it two independent ways — the shipped code path against the direct registry
difference — and it **holds to 1.5 × 10⁻¹¹ MW**. The reference bundle is **NOT at HEAD posture**
(§6), so its fleet is a magnitude anchor; the graded prediction is the identity, evaluated on the
**control run's own entering fleet**. That is exact within the pair, because years 2021–2024 are
byte-identical between arms by construction (the gate is inert pre-2025/26), so the arm's
entering-2025 fleet **equals** the control's.

**PHASE 0 STOP GATE: PASSES — LIVE.** The predicted per-class move is non-zero in DY 2025/2026, so
the lane does not end here.

---

## 5. (d) CONSUMERS of the accreditation census — what this moves, and what it cannot

Enumerated the way D76 §4.2 did, from the call graph of `thermal_accreditation_fraction` /
`_thermal_firm_mw` (the ONE thermal accreditation resolver, rule 19). **All of these move only in
DY 2025/2026, and only in a run where the gate is armed.**

**MOVED:**
1. **`accredited_firm_capacity_mw`** (`adequacy.py`) — and therefore the **CR-1 reserve position**,
   the ledger's `capacity_reserve_position` / `screen_reserve_position`, and
   `screen_entering_firm_mw`.
2. **The retirement reliability floor** — both its threshold test (via #1) and its per-unit
   retention increments; and **`_floor_retention_merit`** key 1, which is
   *going-forward cost per firm MW* and reads the same fraction, so the retention ORDER can move
   within a class boundary as well as the quantity.
3. **The reserve-margin build backstop** — same requirement/position pair as #1.
4. **The D57 capacity-market clearing half** — `offer_g = max(0, GFC_g − E&AS_g) / (A_g × 365)`
   uses the unit's accredited MW, so a **higher** `A_g` **lowers** each affected unit's $/MW-day
   offer while **raising** the MW it offers; and the price-taking block `Q_0` is the whole
   accredited ledger. So `offered_mw`, `price_takers_mw`, `cleared_mw`, `census_mw`,
   `census_position` and the **clearing price** can all move. **This is the largest consumer.**
5. **`capacity_revenue_per_mw_yr`** — the per-unit capacity payment is `price × accredited`, so the
   economic screen's net revenue moves for every affected unit, in both the retirement and entry
   screens, and the D57 clearing price feeds it.
6. **Downstream fleet propagation** — anything #2/#4/#5 changes in 2025's decisions changes
   `fleet_by_fuel_after` and every 2026+ year of a longer horizon.

**NOT MOVED (and why):**
7. **The D67 published adequacy requirement** — it is the **requirement**, digitized from PJM's own
   published Reliability Requirement MW; it is independent of the model's supply census *and* of the
   model's peak (`∂R/∂peak = 0` in every in-table delivery year). The requirement is a fixed
   denominator here.
8. **The D76 measured screen peak** — a **peak** operand, upstream of accreditation entirely.
9. **VRE / hydro / storage / firm-import / DR accreditation** — `_renewable_credit`,
   `resolve_renewable_capacity_credit` (incl. D75-R's rung 0), `_hydro_firm_mw`, `storage_firm_mw`,
   `_firm_import_mw` and `resolve_demand_response_supply_mw` are untouched. This axis reaches
   **thermal fuel classes only**.
10. **The internal-supply accounting ratio** — PJM has no entry in
    `ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO`, so it resolves the neutral 1.0 and neither
    scales nor masks the delta.
11. **Every LP / dispatch quantity, every price band, every emissions stream** — accreditation is a
    capacity-screen operand; it enters no LP column, row or cost.
12. **Every pre-2025 window year, every other ISO, and every backcast** — §6.

---

## 6. (e) G-DRIFT (rule 29(b)) — and why a control solve IS earned here

**The backcast keeper is untouched — proven at code and key level, with NO LP.** The charter's
literal audit (`git diff <keeper git_sha> HEAD`) is **not executable**: the PJM keeper
`2026-08-15-pjm-162-inputclock` records `git_sha = 457ae04`, which is a **dead object** after the
2026-08-16 history rewrite (`git cat-file -t 457ae04` → *not a valid object name*), exactly as
CLAUDE.md warns of every pre-rewrite sha citation. Recorded, not worked around. The substantive
answer is **stronger than a drift audit**, because it is a construction argument plus a measurement:

- (i) `pjm_thermal_accreditation_vintage` is **coerced to its dataclass default whenever
  `mode == "backcast"`** (`__post_init__`, the D48/D75-R pattern) — asserted by
  `test_a_plain_backcast_coerces_the_gate_off`.
- (ii) The registry is read **only** inside `thermal_accreditation_fraction`, which lives in
  `capacity_evolution` — a module a `mode="backcast"` run never enters (a backcast runs no capacity
  evolution).
- (iii) **MEASURED: 0 of 224 committed `run_config.json` cache keys move** (pre/post census over
  `results/**`, zero errors), and that set **includes the PJM keeper's own config**
  (`results/calibration/pjm_debugb_inputclock_A/run_config.json`, `9ca2c6052b4850ea` → unchanged).
  `check_cache_key_registration.py` passes (278 registered fields, 300 solve-surface names, all
  declared).

**The HINDCAST control is a different question, and form 4 is VOID for it — established by an exact
key identification, not a "files changed" heuristic.** No on-disk or committed PJM hindcast bundle
carries HEAD's posture:

| posture | cache key |
|---|---|
| **HEAD bare `pjm-t1h`** | **`f736025631d0d27e`** |
| HEAD − Q55 (VRE vintage off) | `f577130c7aa36742` |
| HEAD − Q58 (measured peak off) | `fb16fda2ddb0a94a` |
| HEAD − Q55 − Q58 | **`bb6a60239d69508b`** ← the newest on-disk PJM bundle (`…-d78-sectorgate`) |
| HEAD − Q55 − Q56 − Q58 | `a9c66d8ea25acb9d` |

The newest bundle on disk is **exactly `HEAD − Q55 − Q58`**: it carries Q56 (sector gate) but
**neither Q55** (`pjm_vre_accreditation_vintage`, owner ruling Q55) **nor Q58**
(`capacity_screen_peak_measured_hindcast`, owner ruling Q58). Both are **LIVE hunks** on this ISO's
forecast path — Q55 changes DY 2025/26's VRE credit, which sits in the same census this lane moves,
and Q58 changes the screen peak operand. Two LIVE hunks, named at the line, at zero LP cost. Rule
29(b) provides for exactly this: **a LIVE hunk earns a control solve.** The `…-d75rarm` bundle
registered at `fb16fda2ddb0a94a` is still `HEAD − Q58` and is in any case **not on disk**.

**So: a HEAD control at `f736025631d0d27e` and an arm at `b9fa47dedb6c3319`.** Both keys are
declared here, before either runs, and each script HEAD-guards itself (exit 90 if the sha moves).

---

## 7. THE SCREEN — named BEFORE it runs

**Rule 29 `[R-SCREEN]`'s year-scoped clause applies, and the screen IS the full span.** The rule's
own exception: *"a year-scoped mechanism whose object only exists in one year, which is the screen
and the full span at once."* This mechanism's object exists in **one** window delivery year — DY
2025/2026, model year **2025** — and that year is the window's **last**, so a hindcast cannot reach
it without solving 2021→2025 anyway (year Y's fleet is year Y−1's output). **The screen year is
therefore model year 2025 / DY 2025/2026**, named here, and it is named on the **mechanism's own
largest measured footprint** from §4 — it is the *only* year with any footprint at all — and never
on the biggest residual.

**Legs, both 2021–2025, one `--start-year 2021 --end-year 2025` invocation each:**

| leg | posture | declared key |
|---|---|---|
| control | bare `pjm-t1h` at HEAD (D48 ×2 + Q55 + Q56 + Q58 + clearing armed by `_pjm_config`; thermal vintage OFF) | **`f736025631d0d27e`** |
| **arm** | + `--pjm-thermal-accreditation-vintage` | **`b9fa47dedb6c3319`** |

Scripts, committed before the solve: `docs/handoffs/d84/run_ctl.sh`, `docs/handoffs/d84/run_arm.sh`.

### 7.1 The pre-registered gate legs — STRUCTURAL and STOP-ONLY

Rule 29: the gate may **kill** the arm; it may **never promote** one, it contributes to no
determination, and **not one leg is read against the target residual**.

1. **IDENTITY.** In DY 2025/2026, measured
   `Δ accredited_firm_capacity_mw == Σ_fuel nameplate_entering_2025,fuel × Δrating_fuel`
   to **< 0.01 MW**, with the per-class split matching §4's Δ-rating column exactly. A miss is a
   threading defect between the resolver and the screen.
2. **DIRECTION AND ORDER OF MAGNITUDE.** The DY 2025/2026 move is **positive** and of order
   **10³ MW** (the anchor is +3,079.84 MW on a neighbouring fleet; the *identity* is what binds, the
   level is expected within a few percent of it since the entering thermal fleet moves little).
3. **CONFINEMENT.** Years 2021–2024 are **byte-identical** between arms — same
   `fleet_by_fuel_before/after`, same `retirements`, same `capacity_clearing`, same
   `screen_entering_firm_mw`. The gate claims no pre-reform row and must touch none. A difference
   there is a leak.
4. **CLASS CONFINEMENT.** Within DY 2025/2026, `coal`, `nuclear` and `biomass` accredited MW are
   **unchanged**; only `gas_cc`, `gas_ct`, `gas_st`, `oil` move, in the ratio §4 states.
5. **NON-TARGET LOAD-BEARING CRITERIA.** No non-target load-bearing scored criterion flips
   **PASS → FAIL**. (A criterion that flips FAIL → PASS is *reported*, never a promotion — rule 29.)

**A leg that fails KILLS the arm** and is reported as the session's result.

### 7.2 Pre-declared expected direction, stated so it cannot be written after the fact

Accredited thermal **UP** in DY 2025/2026 and **exactly zero** in every other window year, so the
**census position RISES** there. The reference bundle already clears every offer at a position of
1.0096 with **zero uncleared MW**, so the most likely consequences are (i) a **higher** cleared and
census position, (ii) a **lower** clearing price, since each affected unit's offer is divided by a
larger `A_g` on a curve that is steep at this position, and (iii) **fewer** economic exits in 2025,
since capacity revenue per unit rises. **Whether the position moves toward or away from PJM's
published cleared position is a DIAGNOSTIC, not a gate** — §0's rule-14 basis is the reason for the
change, and this lane would build it identically had the sign been the other way.

---

## 8. Rules 29(c) / 31 `[R-RETAIN]` — what happens to the bundles

- **`.gitignore` carries `results/hindcast/pjm-2021-2025-realized-t1h-d84-*` from the moment it is
  written**, so neither bundle can reach `main` and the parity gate never sees them. That
  **discharges rule 29(c) in full** — the duty is about the repository, not the working tree
  (the ercot-255 amendment).
- **NOTHING IS `rm`-ed.** Rule 31 binds absolutely: no solved bundle is deleted until the owner has
  ruled on promotion. The FINDING will carry every number this lane will ever cite, **and** will
  state explicitly that the bundles sit on local disk in an ephemeral container and will not survive
  the session — with the promotion question asked, not implied.

---

## 9. Rule 28 `[R-MECH-MATRIX]` and the guards

Duty (c) discharged **in this PR**: base row `pjm_thermal_accreditation_vintage` in
`docs/codebase-site/data/mechanism-matrix.js` plus a cell line in **all seven** shards (SPP
included). `scripts/check_mechanism_matrix.py` integrity: clean (the 253 anchor warnings are
**pre-existing and unchanged** — measured identical with the change stashed). Duty (b) — the cell
verdict stamp on the measurement — lands with the FINDING.

`ruff check` clean; `ruff format` clean. Test baseline: the ten failures in
`test_reserve_config` / `test_cache_solve_surface` / `test_export` / `test_capacity::TestGetRPSTarget`
are **pre-existing on `main`** (measured stashed and unstashed, identical set) and are untouched by
this lane — `tests/unit/results/test_cache_solve_surface.py` in particular belongs to the concurrent
**D86** lane and was not edited.

---

## 10. What this PRECOMMIT does NOT claim

- It does **not** propose an arm. Arming is an owner card the FINDING serves.
- It does **not** close the 2025/26 **BRA**-vintage question — that posting's tables are images and
  do not extract; this lane reads the delivery year's FINAL (3IA) ratings and says so (§3).
- It does **not** touch the `Gas Combustion Turbine Dual Fuel` class (published at 79 % for DY
  2025/26), because the model carries no dual-fuel CT class and the incumbent table does not map to
  it. Re-mapping is a separate card.
- It does **not** address the wider PJM census residual (D66 card B's remaining half), the
  `unit_recall_gt300` gap, or the CT / ST / oil zero-E&AS operand D57 §4 named as the successor for
  the retirement bands.
