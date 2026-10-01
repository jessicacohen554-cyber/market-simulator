# FINDING — C-1 joint wind A/B: both kill-gates PASS, and the joint posture is **NON-COMPLEMENTARY on wind** — it closes exactly the signal leg's 8.87 %, adding nothing; the volume rule's only live effect on the dual level is to exhaust one solar decision

_2026-08-31 · C-1 joint wind charter lane, executing owner ruling **R-B**
(2026-08-31 director sitting) · charter
`docs/PRECOMMIT-c1-joint-wind-2026-08-31.md` (+ its pre-solve **Amendment 1**),
merged as PR #4430 before any solve · Leg-B measurement
`docs/FINDING-t1h-capacity-entry-phase0-2026-08-30.md` §4.1 · driver
`scripts/probes/joint_wind_entry_compare.py`, artifact
`results/calibration/joint_wind_entry_ab_ercot.json`._

**Both arms solved by THIS session on one tree** (`bdb698c`, rebased onto
`origin/main` @ `e52b90a`). Registered on the FORECAST namespace only
(rule 15 `[R-DASHBOARD]`): `ercot-2021-2025-realized-t1h-c1joint-{control,arm}`.
The backcast registry, every keeper shard, `calibration-complete.json`,
`holdout-freeze.json` and `program-status.json` are untouched. **Neither
default is flipped: ARMING IS AN OWNER DECISION on this record, not this
lane's.**

---

## 0. The one-paragraph answer

**The joint arm builds 1.442 GW of wind — to the megawatt the same as the
committed signal-alone (disarm) arm — so it closes 8.87 % of the 12.313 GW
ERCOT wind entry miss and the volume rule contributes exactly ZERO wind on
top of the dual-based level.** Against the naive sum of the two singles
(13.77 %) and the best single (8.87 %), the pre-registered read is
**NON_COMPLEMENTARY**. It is **not** wiring-inert: the walk is live and does
one thing in the whole 2021–2025 window — it **fully exhausts the
entering-2023 solar decision, 5,550 MW → 0** — and that single decision is
the *only* difference between the joint arm and the pure disarm arm, in any
step, for any technology. Both chartered kill-gates **PASS**: K1 does not fire
(the one worsening band, solar at Δ|err| **+0.1410**, is far below the
**0.9470** of improvements on wind/gas_ct/storage), and K2 does not fire (the
arm differs from the control on four of five addition metrics). Four of the
five pre-registered directions are confirmed — including the terminal reserve
margin landing at **38.84 %**, inside the pre-registered (25.19, 40.24) band,
and B-2's cobweb surviving with the predicted down-up-up sign pattern — and
one, "the joint arm builds more wind than the volume rule alone", is confirmed
only in the trivial sense that it inherits the signal leg's number and adds
nothing of its own. **Verdict: the two mechanisms are NOT complementary on
wind; the wind miss is a signal-object question, and 91.1 % of it stays open
under both mechanisms together.**

---

## 1. Posture — verified mechanically, not asserted

The driver hard-fails unless the arms differ in exactly the two chartered
fields; it did not fail. From each arm's committed `run_config.json`:

| check | measured |
|---|---|
| `scenario_config` field diff, control vs arm | **exactly** `{entry_lookahead_reprice: True→False, entry_margin_exhaustion: False→True}` — no third field |
| control cache key | **`28cef3500ec1fd9e`** — the registered T1-H key, REPRODUCED |
| arm cache key | `0490af522537a67c` — the key Amendment 1 predicted ex ante |
| solve/bridge span, both arms | solved [2021, 2023, 2024, 2025], bridged [2022] — the registered window; no out-of-training year touched |
| `leakage_violations`, both arms | `[]` |
| control invocation | `--no-entry-margin-exhaustion --no-entry-forward-reserve-leg` (Amendment 1: the bare invocation now resolves to the Q15-armed default `f061b2646bfaac8b`) |
| arm invocation | `--no-entry-lookahead-reprice --entry-margin-exhaustion --no-entry-forward-reserve-leg` |

`entry_forward_reserve_leg` is pinned **OFF in both arms**, so it is not part
of the delta. The pin is forced, not chosen: that field's own refusal is
untouched by this lane, and a reprice-disarmed ERCOT leg carrying it does not
construct at all (Amendment 1, verified).

Arms ran **sequentially** (control, then arm): the container memcg (~15 GiB)
is shared, so two concurrent ERCOT T1-H invocations would swap-thrash rather
than parallelize. Years sequential within each invocation (rule 12
`[R-PARALLEL]`).

## 2. Control-vs-registered drift record (the v13 C-1 precedent: measured, never assumed)

| check | measured |
|---|---|
| cache key reproduced | **yes** — `28cef3500ec1fd9e` |
| additions rows vs the registered `…-t1h-refresh` `score.json` | **identical on all five techs**, model GW and `err_frac` to the digit (wind 0.350 / solar 17.987 / gas_cc 9.000 / gas_ct 7.571 / storage 5.000) |
| RM path vs the registered ledger | 19.00 / 8.54 / 14.65 / 25.19 — verbatim |
| storage mix vs the registered ledger | `iron_air` 3,000 + `flow_battery` 2,000 in 2023, nothing elsewhere — verbatim |

**Zero fleet-side drift at this HEAD**, despite the Q15 arming landing in
between — because the control pins both Q15 fields off. Every committed
bracket of the registered T1-H posture remains a valid anchor.

## 3. The A/B record

### 3.1 Addition bands at FULL MAGNITUDE in both directions (the K1 object)

Decision basis 2023–2025 additions vs RD-5 actuals. `Δ|err|` > 0 = moved
**away** from actuals, < 0 = moved **toward**. No netting.

| tech | actual GW | control GW | arm GW | control err_frac | arm err_frac | **Δ\|err\|** | band |
|---|--:|--:|--:|--:|--:|--:|---|
| wind | 12.663 | 0.350 | **1.442** | −0.9720 | −0.8860 | **−0.0860** | FAIL → FAIL |
| solar | 25.080 | 17.987 | **14.437** | −0.2830 | −0.4240 | **+0.1410** | FAIL → FAIL |
| gas_cc | 0.244 | 9.000 | 9.000 | +35.8850 | +35.8850 | **0.0000** | FAIL → FAIL |
| gas_ct | 3.692 | 7.571 | **5.571** | +1.0500 | +0.5090 | **−0.5410** | FAIL → FAIL |
| storage | 13.691 | 5.000 | **18.000** | −0.6350 | +0.3150 | **−0.3200** | FAIL → FAIL |

Stated in both directions: **three bands improve** (wind, gas_ct, storage;
sum of improvements **0.9470**), **one worsens** (solar, **+0.1410**), one is
unchanged. **Every band still FAILs in both arms** — the arm is not close to
any actual, and nothing here is a claim of skill. Note the storage row's sign
flip: the arm overshoots (18.000 vs 13.691 actual) where the control
undershoots (5.000); its `|err|` is smaller, which is what the gate measures,
but the model is now wrong in the other direction.

### 3.2 The kill-gates, applied mechanically by the driver

| gate | charter definition | measured | fires? |
|---|---|---|---|
| **K1 REJECTED** | some addition band moves AWAY from actuals by more (in \|err_frac\|) than the SUM of the improvements on the others | one worsening: solar **+0.1410** vs **0.9470** of improvements elsewhere ⇒ `0.1410 > 0.9470` is **false** | **NO** |
| **K2 INERT** | indistinguishable from control on every addition metric AND every per-step decision row | four of five `model_gw` differ; per-step rows differ in 2022/2023/2024/2025 | **NO** |

### 3.3 The complementarity read (charter §3.1 — REPORTED, never gated)

Wind, 2023–2025 decision basis, each arm's share of the 12.313 GW miss
computed as `(model_arm − 0.350) / (12.663 − 0.350)`:

| arm | source | wind model GW | **share of the miss closed** |
|---|---|--:|--:|
| control (registered posture) | this session | 0.350 | — |
| signal alone (`…-t1h-disarm`, key `2eab21467a4214c7`) | **committed** | 1.442 | **8.87 %** |
| volume alone (`…-t1h-d11r-exhaustion`, key `cc7bbe1170db65c2`) | **committed** | 0.954 | **4.91 %** |
| **JOINT (this A/B)** | this session | **1.442** | **8.87 %** |
| naive sum of the singles | arithmetic, never a prediction | 2.396 | 13.77 % |

**Verdict: `NON_COMPLEMENTARY`** — the joint share does not exceed the best
single share (8.87 % vs 8.87 %, a difference of exactly 0.00 pp), let alone
approach the naive 13.77 %. **The volume rule adds ZERO wind on top of the
dual-based signal.** The ruling's premise — that the Leg-B measurement's two
partial closures looked complementary — is **not borne out**: measured
together, they are not additive, not partially additive, and not even
marginally so on this metric.

**It is NOT wiring-inert.** The pre-registered failure mode (charter §6 stop
rule 3: a joint arm byte-identical to the committed disarm arm, meaning the
enabling change never made the walk live) is checked mechanically on all five
addition metrics and reads **false** — solar differs (14.437 vs the disarm's
19.987). The walk is live; it simply does not act on wind.

### 3.4 What the walk actually did — the joint arm against BOTH singles, per step

The decisive table. Joint-arm ledger rows against the committed disarm ledger
(`results/calibration/entry_signal_disarm_ledger_ercot.json`) and this
session's control:

| step | control (registered) | signal alone (committed disarm) | **JOINT (this A/B)** |
|---|---|---|---|
| 2021 | — | — | — |
| 2022 (bridge) | gas_cc 3,000 · gas_ct 1,571 · solar 4,946.6 | + **wind 1,092.2**; storage CAES 2,000 + iron_air 3,000 | **identical to disarm** |
| 2023 | gas_cc 3,000 · gas_ct 3,000 · solar 5,550; storage flow 2,000 + iron_air 3,000 | gas_cc 3,000 · gas_ct 3,000 · **solar 5,550**; storage CAES 2,000 + iron_air 3,000 | gas_cc 3,000 · gas_ct 3,000 · **solar 0**; storage CAES 2,000 + iron_air 3,000 |
| 2024 | gas_cc 3,000 · gas_ct 3,000 · solar 6,000 | gas_cc 3,000 · **gas_ct 1,000** · solar 8,000; storage CAES 2,000 + iron_air 3,000 | **identical to disarm** |
| 2025 | — | storage iron_air 3,000 | **identical to disarm** |
| RM path % | 19.00 / 8.54 / 14.65 / **25.19** | 19.00 / 14.00 / 25.92 / **40.24** | 19.00 / 14.00 / 25.92 / **38.84** |

**The margin-exhaustion walk changes EXACTLY ONE DECISION in the entire
window: entering-2023 solar, 5,550 MW → 0, fully exhausted.** Every other
entry decision, every storage decision, every technology, every step is
byte-identical to the pure disarm arm — including the wind that enters in the
2022 bridge step, which is where all of the joint arm's wind comes from and
which the walk leaves at exactly 1,092.2 MW.

**Why the volume rule's own wind gain does not transfer — the mechanism,
stated.** Under the *shipped repriced* signal (D11-R §3.4), the exhaustion
rule produced wind by an indirect route: solar exhausted **below its cap**
(4,946.6 → 1,250 in 2022; 5,550 → 4,946.6 in 2023), which freed headroom in
the **shared queue budget** that bang-bang solar had consumed at a
manufactured margin, and wind cleared into it. On the **dual-based** level
that route is closed at both ends: (a) in the 2022 step wind already clears on
its own merit — the disarm arm builds 1,092.2 MW there without any volume
rule — so there is no budget headroom left for the walk to hand it; and (b) in
the 2023 step the walk exhausts solar **all the way to zero** rather than
partially, and no wind clears in its place. Exhausting a competitor to zero
does not produce an entrant when the entrant's own repriced margin never
clears. The two legs therefore act on **the same 5,550 MW of 2023 solar** from
opposite sides, and their wind effects do not compose.

### 3.5 Everything else that moved, at full magnitude (rule 1: no netting)

**Reserve-margin path (ledger; a sanity object, not a scored band):**

| step | control % | joint arm % | Δ pp | disarm % (committed, for reference) |
|---|--:|--:|--:|--:|
| 2021 | 19.00 | 19.00 | 0.00 | 19.00 |
| 2023 | 8.54 | **14.00** | **+5.46** | 14.00 |
| 2024 | 14.65 | **25.92** | **+11.27** | 25.92 |
| 2025 | 25.19 | **38.84** | **+13.65** | 40.24 |

The arm's terminal overshoot is **13.65 pp worse than the control** — the
adequacy cost of the dual-based level, reported at full magnitude and not
netted against the band improvements above. Against the signal leg alone the
walk damps the terminal RM by **−1.40 pp** (40.24 → 38.84), which is the
entire measurable adequacy contribution of the volume rule in this posture.
Swings: control **−10.46 / +6.11 / +10.54**, arm **−5.00 / +11.92 / +12.92**.

**Storage mix** (neither chartered mechanism touches the tech pool or the
ranking object, and R-A is not in this posture):

| | by tech | total MW | cap-wtd duration | li-ion share |
|---|---|--:|--:|--:|
| control | `flow_battery` 2,000 + `iron_air` 3,000 | 5,000 | 64.0 h | **0 %** |
| joint arm | `compressed_air` 6,000 + `iron_air` 12,000 | 18,000 | **69.3 h** | **0 %** |

**Zero retirements in every step of both arms**; the reserve-margin build
backstop (default off) never fires.

**Diagnostic side effect, pre-registered in charter §1.4 and confirmed:** the
joint arm emits **4** `screen_signal_diag_*.npz` dumps where the pure disarm
arm emits **0** (Phase-0 §4.2, verified by file count). The seam runs for its
walk, so the joint posture's signal object is offline-diagnosable where the
disarm posture's is not — output-only, no dispatch or entry effect (the
control's byte-exact reproduction of the registered key and rows is the
proof).

### 3.6 Invariant blocks (the FR-24 ledger duty, discharged in the registration commit)

The **control** carries **I3 FAIL** at *2023 slack 0.01 % of load* — the
standing **FR-6** ERCOT energy-only scarcity-slack cause, identical in
magnitude to the capentry control that reproduces the same key, and not
anything this lane introduced. The **joint arm carries NO FAIL**: its 2023
step builds no solar and reaches a 14.0 % reserve margin against the control's
8.5 %, leaving no scarcity slack at all. Only the control is declared in
`frontend/data/hindcast/invariant-failures.json` (`c1joint_note`) — a stale
declaration fails the checker, so the arm is deliberately not declared.
Declaration is not absolution: FR-6 stays the open root cause. Both arms carry
WARNs (reserve-margin band: control 2023 8.5 %, arm 2025 38.8 %, both outside
[13.8 %, 28.7 %]; control price sanity 2023; **arm cobweb detector `wind(3)`**)
— reported, not acted on.

## 4. The pre-registered directions, scored verbatim (charter §4)

| # | pre-registered | measured | verdict |
|---|---|---|---|
| 1 | not additive; joint wind ∈ (0.350, 2.396) GW and **> 0.954** | **1.442 GW** — in range, above 0.954 | **CONFIRMED**, but trivially: it equals the signal leg exactly and the volume rule adds 0.000 GW. The prediction was right for the wrong reason — it anticipated a partial composition, and what obtains is no composition at all |
| 2 | gas stays cap-bound; damping lands on VRE and storage | gas_cc 3,000 at cap in every clearing step of both arms; the walk's one effect is on **solar**; storage untouched by the walk | **CONFIRMED** on gas and on "damping lands on VRE"; the storage half is vacuous here (the walk changed no storage decision) |
| 3 | storage stays long-duration and li-ion-free; li-ion builds 0 MW in both arms | li-ion share **0 %** in both; arm 69.3 h cap-weighted | **CONFIRMED** |
| 4 | terminal RM above the control's 25.19 % and below the disarm's 40.24 % | **38.84 %** | **CONFIRMED** |
| 5 | B-2 survives — the cobweb's down-up-up sign pattern persists | arm swings **−5.00 / +11.92 / +12.92** | **CONFIRMED** |

No prediction was withdrawn, redefined or added after the numbers were seen.
The charter's §3 expectation that **K1 was in genuine jeopardy** did not
materialize: the joint arm inherits the *disarm's* band pattern (four of five
improving), not the D11-R exhaustion arm's (four of five worsening), because
the walk's only live decision is one the band table barely registers.

## 5. What this record says, and what it does not

Recorded for the owner, not recommended:

1. **The wind entry miss is a SIGNAL-OBJECT question, not a volume question.**
   Both mechanisms together close **8.87 %** and leave **91.1 %** open. The
   volume rule contributes nothing to it once the level is locational, and the
   R-B premise of complementarity is measured false.
2. **The volume rule's measured wind gain was a shipped-signal artifact.**
   Its 4.91 % came from solar exhausting *below its cap* and freeing shared
   queue budget for wind — a route that exists only because the shipped
   zone-flat signal manufactures a solar margin that bang-bang then spends in
   full. On the dual level, wind already takes what it can clear on merit in
   the 2022 step, and the walk exhausts 2023 solar to zero without wind
   replacing it. This is evidence about the **shipped signal's solar margin**,
   not about the volume rule.
3. **The joint posture's cost is adequacy, and it is large.** Terminal RM
   **+13.65 pp** against the control (38.84 % vs 25.19 %), against a
   [13.8 %, 28.7 %] band. The walk damps only **−1.40 pp** of the signal leg's
   overshoot. Whatever the band arithmetic says, this posture over-builds.
4. **The one live thing the walk does on a dual level is exhaust solar to
   zero in 2023**, and the solar band is the one band that worsens
   (Δ|err| +0.1410, model 17.987 → 14.437 against a 25.080 actual — the model
   was already short of solar and the walk makes it shorter). K1 does not fire
   because three other bands improve by more, but the mechanism's own
   signature in this posture is a worsening one.
5. **A governance fact this lane records but does not adjudicate.** R-B
   chartered this A/B to measure the volume rule's joint value and ruled
   *"promote nothing yet"*. While the lane was implementing, ruling **Q15**
   (`76c3395`) armed `entry_margin_exhaustion` — one of the two mechanisms
   under test — together with `entry_forward_reserve_leg` as **ERCOT forecast
   defaults**, on the separate D12-C record. This verdict therefore speaks to
   a mechanism that is **already armed in the default lane**. The two rulings
   are the owner's to reconcile; nothing here is acted on, and this lane flips
   no default.
6. **What is NOT covered.** The Q15-armed posture itself (exhaustion **with**
   the D12 forward reserve leg, on either signal level) is unsolved here — the
   D12 leg is pinned off in both arms because it cannot construct with the
   reprice disarmed. A joint arm carrying it would need that field's own
   refusal revisited, which is out of this charter.

No repair ideas beyond the chartered pair surfaced; no proposals are added.

## 6. Rule compliance

- **Rule 1 `[R-STRUCT]`** — the joint object was argued from the two
  mechanisms' structural claims before any measurement; every band is reported
  at full magnitude in both directions (§3.1, §3.5), including the storage
  row's sign flip and the +13.65 pp adequacy cost that no band captures; the
  NON_COMPLEMENTARY result is reported as the measured fact it is, and no gate
  or prediction was redefined after the numbers were seen.
- **Rule 12 `[R-PARALLEL]`** — years sequential within each invocation; the
  two invocations sequential for container-memcg reasons (§1).
- **Rule 13 `[R-MEASURED]` / 23 `[R-FROZEN-DERIVE]`** — no measured outcome
  enters any model path; no parameter is identified against any residual; the
  enabling change introduces no parameter at all.
- **Rule 15 `[R-DASHBOARD]`** — both arms registered via
  `register_forecast_run.py` on the forecast namespace only; the backcast
  registry and its CI gates never touched.
- **Rule 19 `[R-ONE-MECH]`** — nothing stacked: the same one walk, re-used on
  a different consumed level; the charter enumerated what already governs
  entry volume and the signal object before anything changed.
- **Rule 21 `[R-DOF]`** — **zero new free parameters**: no new
  `ScenarioConfig` field, no new constant, no new coefficient. The joint
  posture is two already-registered fields.
- **Rule 22 `[R-HOLDOUT]`** — solves span the registered window only (2021
  enumerated seed + 2023–2025 training, 2022 bridged); `--holdout-authorized`
  never passed; the freeze untouched; both governance banners clean and
  `leakage_violations` empty in both metas.
- **Rule 24 `[R-REGISTRY]`** — both fields are `ScenarioConfig` fields
  serialized into each arm's committed `run_config.json`; the CLI flags are
  tri-state.
- **Rule 25 `[R-ISO-SCOPE]`** — every number is ERCOT's; no verdict transfers;
  only the ERCOT matrix shard is edited.
- **Rule 26 `[R-MECH-MATRIX]`** — duty (a) discharged at charter time (both
  cells checked; neither was `R`/`I`/`G`). Duty (b) discharged in this session
  on both tested ERCOT cells with this finding as the citation. Duty (c) does
  not fire — no `ScenarioConfig` field was added.
- **Rule 27 `[R-PUSH]`** — every edit made locally and pushed as on-disk
  bytes; every push touching a ≥300-line file followed by blob verification
  (line count + hash); no existing large file rewritten from response content;
  no CI workflow added — both solves ran in this session.

## 7. Reproduction

```
# environment: pip install --ignore-installed PyYAML -r requirements.txt
#              pip install -e . --no-deps
#              python3 scripts/regenerate_clean.py        (51 datatypes)
# arms (sequential; the control is PINNED, not bare -- charter Amendment 1)
python3 scripts/run_capacity_hindcast.py --iso ERCOT --start-year 2021 --end-year 2025 \
    --no-entry-margin-exhaustion --no-entry-forward-reserve-leg \
    --out-dir results/hindcast/ercot-2021-2025-realized-t1h-c1joint-control
python3 scripts/run_capacity_hindcast.py --iso ERCOT --start-year 2021 --end-year 2025 \
    --no-entry-lookahead-reprice --entry-margin-exhaustion --no-entry-forward-reserve-leg \
    --out-dir results/hindcast/ercot-2021-2025-realized-t1h-c1joint-arm

python3 scripts/score_capacity_hindcast.py --bundle results/hindcast/ercot-2021-2025-realized-t1h-c1joint-control
python3 scripts/score_capacity_hindcast.py --bundle results/hindcast/ercot-2021-2025-realized-t1h-c1joint-arm

# posture-gated A/B driver (hard-fails on a third differing field)
python3 scripts/probes/joint_wind_entry_compare.py \
    --arm results/hindcast/ercot-2021-2025-realized-t1h-c1joint-arm \
    --control results/hindcast/ercot-2021-2025-realized-t1h-c1joint-control \
    --out results/calibration/joint_wind_entry_ab_ercot.json

# registration (forecast namespace only)
python3 scripts/register_forecast_run.py --bundle results/hindcast/ercot-2021-2025-realized-t1h-c1joint-control
python3 scripts/register_forecast_run.py --bundle results/hindcast/ercot-2021-2025-realized-t1h-c1joint-arm

# mechanism tests
python3 -m pytest tests/unit/pipeline/test_runner.py::TestJointSignalVolumePosture \
                 tests/unit/model/test_entry_margin_exhaustion.py -q
```

The evolution ledgers the driver reads are gitignored bundle internals — the
probe must run in the session that solved the bundles (it did); the committed
artifact `results/calibration/joint_wind_entry_ab_ercot.json` carries both
arms' per-step rows, the posture record, the drift record, the storage mix,
the RM paths, the full-magnitude band table, the K1/K2 verdicts and the
complementarity read in full.
