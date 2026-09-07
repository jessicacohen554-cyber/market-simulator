# FINDING — capx D84: the PJM THERMAL ELCC delivery-year vintage axis, BUILT and MEASURED

**Lane:** capx D84, executing `FINDING-capx-d75r-2026-09-06.md` §6 item 4 under **OWNER RULING Q60**
(2026-09-07, capx ledger §0bd.3(c) — *"D84 first, D83 after"*). Branch
`claude/capx-d84-thermal-elcc-vintage-cblmzl`. **DATA PROFILE: pjm.** MODEL: Opus. Ex-ante record:
`PRECOMMIT-capx-d84-pjm-thermal-elcc-vintage-2026-09-07.md`, **pushed before either solve**;
the gate analyzer `docs/handoffs/d84/gates.py` was committed **between the two legs**, so it could
not be written to fit the arm. Instruments: `docs/handoffs/d84/{thermal-elcc-vintage-phase0,
screen-gates,measurement}.json`.

**GATED DEFAULT-OFF. NOTHING ARMED, and no default was moved** — arming is an owner card, served in
§8 and not taken here.

---

## 0. The answer in one paragraph

Card §6-item-4's repair is **built, measured, and it does exactly what its own arithmetic says.**
Accrediting PJM's dispatchable classes at the delivery year's OWN published ELCC class ratings moves
accredited thermal **UP by +3,105.648 MW in DY 2025/2026** — the only window delivery year on the
ELCC axis at all — against the identity's predicted **+3,105.6475 MW**, i.e. **a gap of 0.00046 MW**,
and **exactly 0.000 MW in every other window year**, with all four earlier years **byte-identical**
across every ledger key compared. **All five pre-registered structural legs PASS.** The consequence
is real and large where the mechanism claims it: the D57 clearing regime **flips** from
`all_offers_clear_curve_sets_price` to `marginal_offer_sets_price`, 2,623.94 MW of coal stops
clearing, and the RTO price falls **$213.06 → $178.10 /MW-day**. And yet **every one of the 361
substantive scored records is byte-identical between arms** (only the score's UTC timestamp differs)
— **zero** band flips in either direction. §5 explains why, and the explanation is the most useful
thing this lane found: **100 % of the newly-uncleared MW is EIA-860 Sector 1**, which owner ruling
Q56's `retirement_sector_gate` partitions out of the exit decision — so the screen's *failing set*
moves while no *exit* can. Two published comparators move the **wrong** way in DY 2025/26 (§6) and
are reported at full magnitude rather than smoothed; under rule 14 `[R-ACCURATE]` that is a cost to
state, never a reason to restore a rating published for a different year.

---

## 1. What was built

| piece | where |
|---|---|
| registry | `THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO["PJM"]`, keyed by delivery-year label |
| gate | `ScenarioConfig.pjm_thermal_accreditation_vintage`, **default-OFF** |
| predicate | `retirements.thermal_accreditation_vintage_armed` |
| resolver | `resolve_thermal_vintage_rating`, at the **top** of `thermal_accreditation_fraction`'s `elcc_class_rating` branch |
| harness | `run_capacity_hindcast.py --pjm-thermal-accreditation-vintage` |
| tests | `tests/unit/data/test_thermal_elcc_vintage_ratings.py` — **14, all pass** |
| matrix | base row + a cell in **all seven** shards (rule 28 duty c) |

**A SUB-GATE INSIDE the D48 family, never a mechanism beside it.** The predicate requires the field
**AND** `pjm_accreditation_design_vintage` **AND** a registry entry for the ISO — D75-R's exact
composition, on the other axis of the same registry. The **rating** axis can therefore never be
devintaged while the **basis** axis is not (rule 19 `[R-ONE-MECH]`: a mixed accreditation vintage is
the failure D45 §2.2 measured). **Why a separate key**, since the charter asks it be said: D48's key
is ARMED for PJM through `iso_configs._pjm_config`, so keying off it alone would arm an untested
mechanism **by default** in every PJM forecast run and move the shipped `pjm-t1h` key — the same
argument that earned D75-R its own key.

**ZERO scalar fields, ZERO free parameters, and — unlike the VRE half — ZERO reconciliations.** PJM
rates each of the model's thermal classes with **exactly one** published class, so D75-R's
cross-vintage solar mix has no analogue here and none was introduced. Every rating reconciles
**byte-for-byte** to `data/raw/capacity-market/elcc/pjm/pjm.csv` by test. The class mapping is
**unchanged**; `biomass`, which PJM does not rate, keeps its UCAP fallback.

---

## 2. STEP (a) — the intake, confirmed independently

D75-R §6 item 4 said *"The intake now carries them"*; **it does.** The committed csv holds seven
`2025/2026 3IA (final for DY 2025/2026; posted 2025-03-12)` thermal rows, all `class_average`:
Nuclear 95, Coal 83, **Gas Combined Cycle 78**, **Gas Combustion Turbine 63**, Gas CT Dual Fuel 79,
**Diesel Utility 92**, **Steam 74** — against the wired 2026/27 set 95 / 83 / **74** / **60** / 78 /
**91** / **73**. No intake card was needed. Rows quoted verbatim in PRECOMMIT §2.

---

## 3. STEP (b) — the vintage and fall-through rules, fixed before any solve

Stated in full in PRECOMMIT §3 and unchanged since. In brief: **admissibility** is `class_average`
**and** official/FINAL-for-that-delivery-year, which admits exactly three PJM vintages (2025/2026
3IA, 2026/2027 BRA, 2027/2028 BRA) and excludes every preliminary/indicative *marginal* row — with
the test proving the marginal series is genuinely present, so the exclusion is not vacuous. **DY
2025/2026 is read at its FINAL (3IA) ratings**, the same posting D75-R's own 2025/2026 VRE row reads.
**The BRA-vintage alternative is NOT AVAILABLE** — the 2025/26 BRA (July 2024) report's tables are
images that do not extract (D75 §5 / D75-R §6 item 3), so a BRA-vintage rule cannot be sourced;
that is stated, not worked around. **No hold-last** at either edge, and pre-reform delivery years
never reach the registry at all (the D48 basis resolver has already returned `"ucap"`), so **the two
vintage axes compose rather than stack**. Neither rule is selectable by a result; both are locked
by test.

---

## 4. PHASE 0 (zero LP) — PASSED the charter's STOP gate

`docs/handoffs/d84/thermal-elcc-vintage-phase0-2026-09-07.json`, calling the shipped code path under
a control config and an armed one that differ in exactly one field.

**Exactly ONE delivery year in the 2021–2025 window sits on the ELCC axis at all** — DY 2025/2026,
because the D48 arm resolves `"ucap"` for 2021/22 through 2024/25. Predicted move on the nearest
available fleet: **+3,079.838516 MW**, sign **UP**; identity checked two independent ways (shipped
path vs registry difference), **gap 1.5 × 10⁻¹¹ MW**. Non-zero ⇒ **LIVE**, so the lane proceeded.

---

## 5. THE SCREEN (rule 29) — five legs, **all PASS** — and what it actually found

Rule 29's **year-scoped clause** applies: the mechanism's object exists in one window delivery year,
and that year is the window's **last**, so the screen and the full span are the same 2021–2025 solve.
Screen year **2025 / DY 2025/2026**, named in the PRECOMMIT before either leg ran, and named on the
mechanism's own **only** measured footprint — never on a residual.

**G-DRIFT earned the control, at an exact key rather than a heuristic** (PRECOMMIT §6): the newest
on-disk PJM bundle keys `bb6a60239d69508b`, which is **exactly `HEAD − Q55 − Q58`**, so two LIVE
hunks separate it from HEAD and rule 29(b) form 4 is void. **Both legs realized their DECLARED keys**
— control `f736025631d0d27e`, arm `b9fa47dedb6c3319` — and both HEAD guards passed clean.

### 5.1 The five pre-registered legs

| leg | result |
|---|---|
| **1. IDENTITY** (`Δ == Σ nameplate × Δrating`, < 0.01 MW) | **PASS** — predicted **3,105.647540**, measured **3,105.648000**, **gap 0.00046 MW** (the ledger's own 3-dp rounding) |
| **2. DIRECTION + ORDER OF MAGNITUDE** (positive, 10³ MW) | **PASS** — +3,105.648 MW |
| **3. CONFINEMENT** (2021–2024 byte-identical) | **PASS** — all four years identical across 13 scalars, 14 blocks and 12 clearing keys; **zero** differing keys |
| **4. CLASS CONFINEMENT** | **PASS** — `coal` / `nuclear` / `biomass` **exactly 0.000**; only `gas_cc` +2,282.838, `gas_ct` +773.732, `oil` +41.365, `gas_st` +7.712 |
| **5. NO NON-TARGET PASS → FAIL** | **PASS** — see 5.2; measured substantively, not vacuously |

The entering-2025 fleet is **shared between arms** (asserted, not assumed), which is what makes the
identity exact within the pair.

### 5.2 Leg 5, measured properly — and a defect of my own, fixed rather than hidden

`gates.py`'s leg-5 flattener returned **0 records**, i.e. it was **green and vacuous**. The cause:
`score.json` is written by `scripts/score_capacity_hindcast.py`, a **separate step** the solve does
not run. I ran the scorer on both bundles and diffed them properly:

> **362 leaf records compared. Exactly ONE differs: `generated_utc`** (`19:35:45Z` → `19:35:49Z`).
> **All 361 substantive records — including all 26 scored bands and both `retirements` /
> `retirements_is` blocks — are byte-identical.** Zero PASS → FAIL. Zero FAIL → PASS.

I report the vacuous first pass rather than only its repaired result, because a green-and-vacuous
guard is exactly what r#59 called out.

### 5.3 The substantive finding: a real regime change that no decision can absorb

In DY 2025/2026 the arm moves every consumer PRECOMMIT §5 said it would, and nothing it said it
could not:

| quantity | control | arm | Δ |
|---|---:|---:|---:|
| `screen_entering_firm_mw` | 146,449.630 | 149,555.278 | **+3,105.648** |
| `screen_reserve_position` | 1.013843 | 1.035343 | +0.021500 |
| `census_mw` | 146,165.127 | 149,270.775 | **+3,105.648** |
| `census_position` | 1.011874 | 1.033373 | +0.021499 |
| `offered_mw` | 126,530.744 | 129,636.392 | +3,105.648 |
| `cleared_mw` | 146,165.127 | 146,646.835 | **+481.708** |
| `cleared_position` | 1.011874 | 1.015208 | +0.003334 |
| `price_usd_per_mw_day` | 213.056369 | **178.095377** | **−34.961 (−16.4 %)** |
| `n_uncleared` | 0 | **14** | +14 |
| `how` | `all_offers_clear_curve_sets_price` | **`marginal_offer_sets_price`** | regime flip |
| `uncleared_mw_by_fuel` | `{}` | `{coal: 2,083.627}` | — |
| `screen_adequacy_requirement_mw` | 144,450.0 | 144,450.0 | **0** (D67's published operand) |
| `retirements` / `entry_decided_mw_by_tech` / `fleet_by_fuel_after` / `floor_retained` | — | — | **IDENTICAL** |

**The clearing arithmetic reconciles with nothing unaccounted:** `census − cleared = 2,623.940 MW` =
**2,083.626 MW fully uncleared** + **540.314 MW** of the marginal unit's own uncleared remainder;
and D57's identity I1 (`Q₀ + Σ A_g == census`) holds to **0.004 MW**.

### 5.4 WHY zero decisions moved — the answer, and it is a collision between two ARMED mechanisms

The newly-uncleared set is 14 tranches across **six plants**. Their EIA-860 `Sector`, looked up from
the same table the gate reads:

| plant | sector | tranches | accredited MW |
|---:|---:|---:|---:|
| 1040 (AEP Ohio) | **1** | 3 | 82.751 |
| 2936 (ATSI) | **1** | 4 | 27.389 |
| 3935 (AEP Ohio) — the marginal unit | **1** | 1 | 832.822 |
| 3954 (West APS) | **1** | 2 | 386.692 |
| 6166 (AEP Ohio) | **1** | 2 | 858.884 |
| 7213 (Dominion) | **1** | 3 | 727.910 |

**100.0 % of the newly-uncleared MW is Sector 1 — a regulated electric utility.** Under owner ruling
**Q56** (`retirement_sector_gate`, ARMED for PJM), a sector-1 unit still **offers** its accredited MW
into the D57 clearing at its net-ACR cap, but is **partitioned out of the step-3 economic exit
decision**. CLAUDE.md's D57 entry says *"the screen's failing set IS the auction's uncleared set"* —
and here the failing set moves from empty to 2,623.94 MW **while not one unit in it is eligible to
exit.** The coal offers themselves are **byte-identical** between arms (coal's rating does not move);
they fall out purely because the *stack* is 3,105.6 MW longer and the VRR curve intersects earlier.

That is a clean, structural explanation for "large census move, zero band move", and it is
**reported, not resolved**: nothing here adjudicates whether Q56's partition should extend to the
clearing's must-offer side. It does mean **a lane cannot currently learn anything about D84 from the
retirement bands in a PJM hindcast**, because the channel between them is closed by another armed
mechanism.

---

## 6. The published residual — REPORTED AT FULL MAGNITUDE, and NOT the reason for anything

Against PJM's own published DY 2025/2026 figures (read from the committed csvs; rule 13 — observables
compared against, never operands):

| comparator | published | control | arm | control gap | arm gap | direction |
|---|---:|---:|---:|---:|---:|---|
| RTO cleared MW, frame B (RPM + committed FRR) | 145,883.0 | 146,165.127 | 146,646.835 | +282.127 | **+763.835** | **AWAY** (+481.708) |
| RTO cleared MW, frame A (RPM only) | 135,684.0 | 146,165.127 | 146,646.835 | +10,481.127 | **+10,962.835** | **AWAY** (+481.708) |
| RTO BRA clearing price, $/MW-day | 269.92 | 213.056 | **178.095** | −56.864 | **−91.825** | **AWAY** (+34.961) |

**All three move the wrong way.** This is rule 14 `[R-ACCURATE]`'s *"treat the worse fit as a
discovered bug"* case, and it is stated as such: the 2026/27 table is **not** restored because it fit
better, and no vintage was selected by what it does to a criterion (rule 1 `[R-STRUCT]`). The
mechanism would have been built identically had the residual moved the other way, and the PRECOMMIT
said so before the number existed. What the residual **does** tell us is where the real defect is:
the model's cleared quantity already sat **above** frame B and its price **below** the published
before this lane touched anything, and more correctly-accredited supply necessarily worsens both.
That points at the supply-stack *level* and at the CT / ST / oil zero-E&AS operand D57 §4 already
named as the successor — not at the rating vintage.

---

## 7. Byte-identity and key evidence

- **0 of 224 committed `run_config.json` cache keys move** (pre/post census, zero errors), and that
  set **includes the PJM backcast keeper's own config** (`pjm_debugb_inputclock_A`,
  `9ca2c6052b4850ea`, unchanged).
- **The bare `pjm-t1h` control key is unmoved at `f736025631d0d27e`**; the arm keys distinctly at
  `b9fa47dedb6c3319`. Both realized as declared.
- The backcast keeper is untouched **by construction**, not merely by measurement: the field is
  coerced to its dataclass default whenever `mode == "backcast"`, and the registry is read only
  inside `capacity_evolution`, which a backcast never enters. (The charter's literal
  `git diff <keeper sha> HEAD` is **not executable** — the keeper records `git_sha = 457ae04`, dead
  after the 2026-08-16 history rewrite. Recorded, not worked around.)
- `check_cache_key_registration.py` passes; `check_mechanism_matrix.py` integrity clean (its 253
  anchor warnings are pre-existing — measured identical with the change stashed).
- Test baseline: the ten failures in `test_reserve_config` / `test_cache_solve_surface` /
  `test_export` / `test_capacity::TestGetRPSTarget` are **pre-existing on `main`** (measured stashed
  and unstashed, identical set). `tests/unit/results/test_cache_solve_surface.py` belongs to the
  concurrent **D86** lane and was not edited.

---

## 8. OWNER CARD — arm, or not arm. Both sides at equal strength.

**This lane does not take the decision and has moved no default.**

### The case FOR arming

1. **Rule 14 `[R-ACCURATE]` is dispositive on its own, and it is the whole case.** DY 2025/2026 is
   the FIRST delivery year of PJM's ELCC-class design, and the model accredits it at the **2026/2027**
   ratings — a set published for a different delivery year — while that year's OWN final ratings sit
   in the repository, already intaken. The rule requires preferring the published vintage
   **whatever it does to the fit**. This is the same sentence that carried D75-R to Q55.
2. **The mechanism is exact.** It lands on its pre-solve identity to **0.00046 MW**, is confined to
   the four classes and the one delivery year it claims, and leaves 2021–2024 **byte-identical**.
3. **Nothing regresses.** All 361 substantive scored records, all 26 bands, both retirement blocks:
   **byte-identical**. No criterion flips in either direction.
4. **Zero DOF cost** (rules 21/24): zero scalar fields, zero free parameters, and — unlike the VRE
   half — **zero reconciliations**. There is nothing here to fit and nothing was fitted.
5. **It closes the D48 family.** The basis axis (D48), the requirement axis (D48/D67) and the VRE
   rating axis (D75-R/Q55) are all devintaged; the thermal rating axis is the **last** half left on a
   single vintage. Leaving it is the mixed-vintage state rule 19 objects to.

### The case AGAINST arming

1. **Three published comparators move AWAY** in the one year it touches (§6): cleared MW +481.7 MW
   further above published on both frames, and the price $34.96/MW-day further below. An owner may
   reasonably want the level defect diagnosed **before** adding correctly-accredited supply on top
   of it.
2. **It buys no measurable improvement anywhere the model is scored.** Every band is byte-identical,
   so on the gate board this arm is invisible; its entire effect lands in a census and a clearing
   price that no scored criterion reads.
3. **Its real effect is currently absorbed by another armed mechanism** (§5.4). The regime flip and
   2,623.94 MW of uncleared coal produce **zero** exits because 100 % of that set is sector-1 and
   Q56 partitions it out. Arming now locks in a change whose only live consequence — the clearing
   price — moves the wrong way, while the consequence one would *want* (exit signal) is unreachable.
   An owner may prefer to settle the Q56-vs-D57 must-offer question **first**.
4. **One delivery year, at the window's edge.** The footprint is a single year, and it is the last
   one, so no subsequent hindcast year tests the fleet it produces. The evidence base is thinner
   than D75-R's three in-scope years.
5. **The 2025/26 BRA-vintage question is open** (§3). This lane wires the delivery year's FINAL (3IA)
   ratings because the BRA-vintage tables do not extract. If an owner judges that the *auction's own*
   ratings are the right operand, the correct answer for this year is not yet sourceable and arming
   now would wire the second-best one.

### If arming is granted — the honest posture

**The `iso_configs` `default_scenario_overrides` route, exactly as D57 / D67 / Q55 / Q56 all used for
PJM** — *not* a `(b′-1)` declared default flip. Add `"pjm_thermal_accreditation_vintage": True` to
`iso_configs.py::_pjm_config`, leaving the shared `ScenarioConfig` default `False`.

- **What re-keys:** PJM **forecast/hindcast** configs only. The bare `pjm-t1h` moves
  `f736025631d0d27e` → `b9fa47dedb6c3319` (this lane's own measured arm key, so the arm bundle IS
  the armed recipe).
- **What does not:** the shared default stays off, so **every other ISO and every backcast keeper is
  byte-identical**, and `--no-pjm-thermal-accreditation-vintage` reaches the pre-arm posture and
  keeps its key. The measured evidence for that is §7's 224-config census.
- **Registration** of the armed `pjm-t1h` on the forecast namespace would be owed by the executing
  lane, as Q55/Q56 were.

**What arming does NOT close, stated at the gate:** the model still clears **above** PJM's published
position and prices **below** it in DY 2025/2026, and this repair moves both further; the
`unit_recall_gt300` and `false_retire` bands stay FAIL, untouched; the Q56-vs-D57 must-offer
collision (§5.4) is **reported, not resolved**; and the 2025/26 BRA-vs-3IA vintage question (§3) is
carried forward, not answered.

---

## 9. What this lane ROUTES rather than absorbs

1. **The Q56 / D57 collision (§5.4).** A sector-1 unit must offer (Manual 18 §1.2 / §5.4.1) and is
   exempt from the economic exit — correct on both counts individually — but together they make the
   D57 clearing's *failing set* unable to produce an exit for any sector-1 unit, however deep it
   sits below the curve. Whether the auction's uncleared position should feed something else for
   those units (an IRP-shaped channel, or nothing at all) is a design card, not this lane's.
2. **`Gas Combustion Turbine Dual Fuel`**, published at 79 % for DY 2025/26 and 78 % for 2026/27, is
   not mapped: the model carries no dual-fuel CT class and the incumbent table never mapped to it.
   Re-mapping is a separate card and was deliberately not taken (rule 19).
3. **The 2025/26 BRA-vintage ratings** — images that do not extract. A lane with OCR or another
   primary source could close §3's open half.
4. **`Waste to Energy Steam`** (2027/28: 83 %) still has no 2026/27 rating, so model `biomass`
   remains on UCAP under both arms — unchanged from HEAD, and out of this card's scope.

---

## 10. Rules 29(c) / 31 `[R-RETAIN]` — THE BUNDLES ARE ON LOCAL DISK AND WILL NOT SURVIVE

- Both bundles are **gitignored** (`.gitignore`: `results/hindcast/pjm-2021-2025-realized-t1h-d84-*/`),
  which **discharges rule 29(c) in full** — they cannot reach `main` and the parity gate never sees
  them.
- **NOTHING WAS DELETED.** Rule 31 binds absolutely and this lane did not `rm` anything.
- **THE PROMOTION QUESTION IS ASKED EXPLICITLY, in §8, and it is open.** Both solved bundles
  (`…-d84-control` at `f736025631d0d27e`, `…-d84-thermalvintage` at `b9fa47dedb6c3319`, ~17 min of
  LP each, ~34 min total) sit **only** on this ephemeral container's local disk and **will not
  survive session reclamation**. Every number this document cites is carried here and in the three
  committed `d84/*.json` instruments, so the *record* survives; the *artifacts* do not. If the owner
  rules ARM, the executing lane must budget **~17 min** to re-solve the armed `pjm-t1h` for
  registration (the arm bundle here already carries the armed recipe's exact key, so a surviving
  copy would make that free).
