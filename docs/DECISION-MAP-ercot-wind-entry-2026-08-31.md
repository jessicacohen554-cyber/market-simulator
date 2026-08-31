# DECISION MAP — the ERCOT wind entry miss: TERMINAL REST at this representation grain

**Filed:** 2026-08-31, executing owner ruling **R-D** of the 2026-08-31 director
REFRESH sitting, on `docs/FINDING-c1-joint-wind-ab-2026-08-31.md`. **Pattern:**
the caiso-222 §1(c) **option 3 — TERMINAL REST + MAP** (owner ruling R-3,
2026-08-30; `docs/calibration-log/caiso.md`, the caiso-222 entry). **Zero solve;
this document changes no keeper, shard, marker, determination, default or matrix
cell verdict.** Its only companion edits are the R-D ruling stamps appended to
the two ERCOT matrix cells' evidence strings, and the log entries that record
the ruling.

> **What TERMINAL REST means here, stated first so it cannot be misread.**
> Further pursuit of the ERCOT wind entry miss **at this representation grain**
> is designated **NOT THE ROUTE**. It does **not** mean the miss is closed,
> small, or acceptable: **91.1 % of it stays open and is published at full
> magnitude below.** It does not make any ERCOT band pass — every addition band
> FAILs in both arms of the deciding A/B. It does not arm anything: **the ERCOT
> entry screen keeps its shipped posture**, verified at this document's pin
> (`ScenarioConfig.entry_lookahead_reprice: bool = True`,
> `src/market_sim/config/scenarios.py:3919`). What it rules is that the next
> honest move is **not another lever at hub grain** — it is a new measured
> driver or an owner-chartered change to what the model can *see*.

---

## 1. The object

ERCOT's capacity-entry screen builds **0.350 GW** of wind over the 2023–2025
decision basis against **12.663 GW** actually built (RD-5 actuals) — a
**12.313 GW** miss, `err_frac` **−0.9720**. It is the single largest addition
band error in the T1-H ERCOT lane, and it has been the standing open question
on this program's owner queue since v16 (item 2, "the C-1 wind signal-object
call").

## 2. The attribution — a zone-flat, ORDC-dominated signal at hub grain

The miss is **not** a wind-cost, wind-CF or queue-budget defect. It is a
property of the **signal object** the entry screen prices against, and that
object was characterized before any of the A/Bs below were run:

- **The shipped signal is zone-flat BY CONSTRUCTION.** `entry_lookahead_reprice`
  re-prices the entering year's net load against the current stack and produces
  a system-wide MC step: measured `zonal_mean_range` and
  `hourly_cross_zone_spread` are **exactly 0.0** in both ISOs tested
  (`docs/FINDING-entry-signal-disarm-2026-08.md` §, the L-1 characterization).
  ERCOT's seven model zones see one number.
- **~90 % of what dispersion it does carry is the ORDC adder** — a
  summer-afternoon artifact, not a price any generator is paid
  (`FINDING-entry-signal-disarm-2026-08.md`; D-8 attribution).
- **That shape inverts wind's value at hub grain.** Against each arm's own mean,
  the build-zone (West) capture ratio reads **0.494 / 0.805 / 0.927** on the
  shipped signal versus **0.988 / 0.988 / 1.055** on the model's own hourly
  zonal LP duals (`docs/FINDING-entry-signal-l1-2026-08.md` §1, entering
  2023/2024/2025). **Wind is at capture parity on the duals and below parity on
  the shipped object**, and the B-3 inversion the parent finding chased (wind
  anti-correlated, solar 2.6×-correlated) is **manufactured by the ORDC adder's
  summer-afternoon shape**, not by wind's market value.

So: a developer's pro-forma prices a project at its interconnection node. The
shipped object is a system-wide scalar whose only structure is a scarcity
artifact. **At hub grain the model cannot see the thing that makes an ERCOT wind
project bankable**, and that is where the 12.313 GW lives.

## 3. What was MEASURED, and what it CLOSED

Three registered A/Bs, all on the ERCOT T1-H `2021-2025-realized` leg, each
against a same-tree control that **reproduces the registered T1-H cache key
`28cef3500ec1fd9e`** with its additions table and reserve-margin path verbatim
(zero fleet-side HEAD drift, measured in every one of the three).

| arm | mechanism delta | key | wind model GW | **share of the 12.313 GW miss closed** |
|---|---|---|--:|--:|
| control (registered posture) | — | `28cef3500ec1fd9e` | 0.350 | — |
| **signal alone** (`…-t1h-disarm`) | `entry_lookahead_reprice` **off** ⇒ dual-based level | `2eab21467a4214c7` | **1.442** | **8.87 %** |
| **volume alone** (`…-t1h-d11r-exhaustion`) | `entry_margin_exhaustion` **on**, shipped signal | `cc7bbe1170db65c2` | 0.954 | **4.91 %** |
| **JOINT** (`…-t1h-c1joint-arm`) | **both**, the only untested combination | `0490af522537a67c` | **1.442** | **8.87 %** |
| *naive sum of the singles* | arithmetic, never a prediction | — | *2.396* | *13.77 %* |

**Verdict `NON_COMPLEMENTARY`.** The joint share does not exceed the best single
share — 8.87 % vs 8.87 %, a difference of exactly **0.00 pp**. **The volume rule
adds ZERO wind on top of the dual-based signal.** Both charter kill-gates PASS
(K1: the lone worsening band, solar at Δ|err| **+0.1410**, against **0.9470** of
improvements elsewhere, so `0.1410 > 0.9470` is false; K2 inert: four of five
addition metrics differ). The joint arm is **not** wiring-inert — the walk runs
and is live.

**The joint posture therefore closes exactly the signal leg's 8.87 %, and
91.1 % of the ERCOT wind entry miss stays open under both mechanisms together.**

### 3.1 Why the volume rule's own wind gain does not transfer — the mechanism

The margin-exhaustion walk changes **exactly one decision** in the whole
2021–2025 window on a dual-based level: **entering-2023 solar, 5,550 MW → 0,
fully exhausted.** Every other entry decision, every storage decision, every
technology, every step is **byte-identical to the pure disarm arm** — including
the 1,092.2 MW of wind that enters in the 2022 bridge step, which is the entire
source of the joint arm's wind.

Under the *shipped* signal the rule produced wind by an indirect route: solar
exhausted **below** its cap (4,946.6 → 1,250 in 2022; 5,550 → 4,946.6 in 2023),
freeing shared queue budget that bang-bang solar had consumed at a manufactured
margin, and wind cleared into it. On the dual level that route is closed at both
ends — wind already clears on its own merit in the 2022 step (so there is no
headroom left to hand it), and the 2023 walk exhausts solar **all the way to
zero** with no wind replacing it. **The 4.91 % is identified as a
shipped-signal artifact**: evidence about the shipped object's manufactured
solar margin, not about the volume rule.

## 4. The couplings, at FULL magnitude, in both directions (rule 1 `[R-STRUCT]`)

Nothing here is netted, and nothing here is a claim of skill: **every addition
band FAILs in both arms.**

| tech | actual GW | control GW | joint arm GW | control err_frac | arm err_frac | **Δ\|err\|** |
|---|--:|--:|--:|--:|--:|--:|
| wind | 12.663 | 0.350 | 1.442 | −0.9720 | −0.8860 | **−0.0860** |
| solar | 25.080 | 17.987 | 14.437 | −0.2830 | −0.4240 | **+0.1410** |
| gas_cc | 0.244 | 9.000 | 9.000 | +35.8850 | +35.8850 | 0.0000 |
| gas_ct | 3.692 | 7.571 | 5.571 | +1.0500 | +0.5090 | **−0.5410** |
| storage | 13.691 | 5.000 | 18.000 | −0.6350 | +0.3150 | **−0.3200** |

- **Adequacy is the posture's real cost, and it is large.** Terminal reserve
  margin **25.19 → 38.84 %**, **+13.65 pp** against the control, on a
  [13.8 %, 28.7 %] band. The RM path runs 19.00 / 14.00 / 25.92 / **38.84** %
  against the control's 19.00 / 8.54 / 14.65 / **25.19** %. The volume rule's
  entire measurable adequacy contribution is **−1.40 pp** off the signal leg's
  own 40.24 % overshoot. **This posture over-builds**, whatever the band
  arithmetic says.
- **Storage flips sign rather than improving.** Control undershoots (5.000 GW),
  arm overshoots (18.000 GW) against 13.691 actual; |err| is smaller and the
  model is now wrong in the other direction. Mix: control `flow_battery` 2,000 +
  `iron_air` 3,000 (5,000 MW, 64.0 h, **0 % li-ion**) → arm `compressed_air`
  6,000 + `iron_air` 12,000 (18,000 MW, 69.3 h, **0 % li-ion**).
- **The one live thing the walk does is a WORSENING one.** It exhausts 2023
  solar to zero, and solar is the band that moves away from actuals (17.987 →
  14.437 against 25.080 — the model was already short of solar and the walk
  makes it shorter). K1 does not fire only because three other bands improve by
  more.
- **Zero retirements in every step of both arms**; the reserve-margin build
  backstop never fires. co2 is reported-only. The arm carries a cobweb-detector
  `wind(3)` WARN; both arms carry reserve-margin band WARNs (control 2023 8.5 %,
  arm 2025 38.8 %). The control carries the standing **FR-6** ERCOT energy-only
  scarcity-slack **I3 FAIL** at 2023 slack 0.01 % of load — not introduced by
  this lane, and declared in `frontend/data/hindcast/invariant-failures.json`.

## 5. THE RULING — terminal rest at this grain

**Owner ruling R-D, 2026-08-31 refresh sitting.** On the kill-gates-pass,
`NON_COMPLEMENTARY` record above: **TERMINAL REST at this representation
grain, with this map attached** — the caiso-222 §1(c) option-3 pattern.

What that settles, and what it does not:

- **The wind entry miss is a SIGNAL-OBJECT question, not a volume question.**
  That is now measured rather than argued: the only untested combination was
  tested and the volume leg contributes 0.000 GW of wind on a locational level.
- **Nothing is armed.** The ERCOT entry screen keeps its shipped posture;
  `entry_lookahead_reprice` stays default-ON. No `ScenarioConfig` field moved,
  no DOF was added by any arm in this program (rule 21 `[R-DOF]`: the joint
  posture is two already-registered fields, zero new parameters).
- **Nothing is rejected.** The dual-based object is **not** `R`. It repairs
  measured defects on its own evidence (locational dispersion where the shipped
  object is flat by construction; steady long-duration storage; wind entering at
  all) and trades them for a backward-looking naive-expectations object at a
  +13.65 pp adequacy cost. Neither object is the developer pro-forma. Both
  matrix cells stay where they were: `entry_lookahead_reprice` **cell K / fc O**,
  `entry_margin_exhaustion` **cell O / fc K** — **measured, rested unadopted.**
- **The 91.1 % is published, not retired.** It stands as the honest open
  residual of the ERCOT T1-H addition bands, at full magnitude, and it is
  reported as such wherever those bands are quoted.
- **This is not a determination act.** No ERCOT backcast determination, keeper,
  marker or frontier is touched by this ruling; the T1-H lane is the forecast
  namespace and the backcast CI gates stay blind to it (rule 15
  `[R-DASHBOARD]`).

## 6. RE-OPEN CONDITIONS — the only two, and they are narrow

Exhaustively, the ways this rest re-opens:

1. **A NEW MEASURED DRIVER.** A measured input that reaches the signal object
   and is admissible under rule 13 `[R-MEASURED]` — it must be producible for a
   forward year from forward drivers and respond to changed conditions. A
   residual-fitted adder, a tuned capture factor, a wind-build target, or any
   quantity backed out of the 12.313 GW gap is **not** such a driver and is
   forbidden by rules 1 `[R-STRUCT]`, 13 `[R-MEASURED]` and 21 `[R-DOF]`. The
   published entry-screen constants are not knobs.
2. **AN OWNER-CHARTERED REPRESENTATION-GRAIN CHANGE.** A change to what the
   entry screen can *see* — nodal or sub-zonal price formation for the entry
   signal, a locational capture object at the interconnection node, or a
   forward-expectation construction that is neither the zone-flat MC step nor
   last year's realized duals. This is the caiso-223 class: **a
   representation-grain program, not a lever**, and it earns its arming
   separately with its own precommit. It is an owner act, not a lane's.

**Neither route may be opened by re-running a lever at hub grain.** Both
mechanisms in the deciding A/B are adjudicated; re-testing either cell without
new evidence is a rule 26 `[R-MECH-MATRIX]` DO-NOT-REDO violation.

## 7. WATCH ITEM — the armed-combination measurement gap (NOT a re-open condition)

Recorded so it is not lost, and explicitly **not** a trigger for re-opening §6:

**No registered bundle sits at the posture a bare ERCOT T1-H run now
constructs.** As of this document's pin, that bare run resolves **five**
solve-affecting entry-screen fields to ON simultaneously — the shipped signal
plus **four fields armed by two owner rulings** (each ruling arming its pair as
one unit):

| field | live state | armed as | by |
|---|---|---|---|
| `entry_lookahead_reprice` | ON | `ScenarioConfig` default `True` | shipped posture (not a ruling) |
| `entry_margin_exhaustion` | ON | ERCOT `default_scenario_overrides` | D12-A, owner ruling Q15 |
| `entry_forward_reserve_leg` | ON | ERCOT `default_scenario_overrides` | D12-A, owner ruling Q15 (one unit with the above) |
| `storage_entry_availability_gate` | ON | `ScenarioConfig` default `True` | **owner ruling R-A**, 2026-08-31 |
| `storage_entry_cost_normalized_rank` | ON | `ScenarioConfig` default `True` | **owner ruling R-A**, 2026-08-31 |

Every registered A/B measured a **strict subset**: the R-A repair arm ran at the
*unarmed* walk by design; the D12-C armed pair ran at the *pre-R-A* storage
defaults; the C-1 joint arm pinned `entry_forward_reserve_leg` **off in both
arms** (a reprice-disarmed leg carrying it does not construct at all). **The
full combination is composed-by-construction and UNMEASURED.**

Two sharp consequences, both already on the record and restated here because
this is where a reader will look:

- **A silent same-key collision.** The R-A arming declared a cache epoch
  (`src/market_sim/results/cache.py`, "Epoch 2026-08-31") in which the forecast
  default key **`603c2498bf71d21d` does not move** — both storage fields are
  `_CACHE_KEY_OPTIONAL_FIELDS` members, so a **pre-flip unarmed bundle and a
  post-flip armed config are the same key** and an armed run will silently serve
  the unarmed bundle. Named concretely in the epoch: the C-1 and capentry
  control arms are such bundles. **Purge or re-solve before quoting an armed
  run.** An explicit `=False` remains non-default and hashes distinctly, so
  disarmed controls stay separable.
- **Anything measured at the combined posture is new evidence about the
  COMBINATION, not about either mechanism's cell** — and not, by itself, a new
  measured driver under §6 clause 1.

Closing this gap is a T1-H re-baseline, which is the forecast program's
charter, not a calibration lane's and not this map's.

## 8. Evidence

- `docs/FINDING-c1-joint-wind-ab-2026-08-31.md` — the deciding A/B (charter
  `docs/PRECOMMIT-c1-joint-wind-2026-08-31.md` + its pre-solve Amendment 1,
  merged **before** any solve); artifact
  `results/calibration/joint_wind_entry_ab_ercot.json`; driver
  `scripts/probes/joint_wind_entry_compare.py` (hard-gates the exactly-two-field
  posture); registered `ercot-2021-2025-realized-t1h-c1joint-{control,arm}`
  (forecast namespace only).
- `docs/FINDING-entry-signal-l1-2026-08.md` — the L-1 signal characterization
  (capture ratios, dispersion, the B-3 attribution).
- `docs/FINDING-entry-signal-disarm-2026-08.md` — the single-flag disarm
  (zone-flatness measured at 0.0; the ~90 % ORDC dispersion attribution; the
  `fc K → O` verdict and its "trade of one structural defect for another"
  reasoning).
- `docs/handoffs/FINDING-capx-d11r-entry-volume-rule-2026-08-30.md` — the volume
  rule's own A/B (the 4.91 %, here identified as a shipped-signal artifact).
- `docs/FINDING-t1h-capacity-entry-phase0-2026-08-30.md` §4.1 — the Leg-B
  measurement that produced the 8.87 %.
- `docs/FINDING-t1h-capentry-phase1-ab-2026-08-30.md` — Leg A, armed by R-A;
  `src/market_sim/results/cache.py` epoch 2026-08-31.
- `docs/codebase-site/data/mechanism-matrix/ERCOT.js` — the two cells' R-D
  ruling stamps.
- Precedent for this document's form: the caiso-222 Q1 ruling
  (`docs/calibration-log/caiso.md`, 2026-08-30 entry, packet §1(c) option 3).
