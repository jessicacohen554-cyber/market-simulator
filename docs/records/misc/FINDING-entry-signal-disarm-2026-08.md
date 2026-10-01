# FINDING — the entry-signal DISARM probe adjudicated; CAISO L-1 measured

_2026-08-24 · ENTRY SIGNAL lane (charter: `docs/FINDING-entry-signal-l1-2026-08.md`
§4 item 2 / §5 — "the named next rung"; parent `docs/FINDING-entry-screen-t1h-2026-08.md`
§7–§8) · **Four LP solves: the ERCOT disarm probe, a same-tree ERCOT control, the
CAISO dump-production run, and a same-tree CAISO control.** This rung ADJUDICATES
one mechanism cell (`entry_lookahead_reprice`, ERCOT `fc` column) and MEASURES
CAISO's L-1. **Nothing is armed as a default anywhere** — arming the disarm is the
owner's promotion decision, stated as such in the charter._

---

## 0. The one-paragraph answer

**The disarm does what L-1 predicted to the megawatt on storage, and fails L-1's
gas prediction in the direction that proves the stand-in bound was real.** Replacing
the zone-flat MC-step entry signal with the run's own prior-year LP duals turns
ERCOT storage entry from a one-shot 5.0 GW spike into **iron-air at exactly 3,000 MW
in every step**, flips the second storage slot flow_battery → compressed_air exactly
as L-1 §2.3 predicted, and lets wind enter economically at all for the first time —
while the entering-2024 gas margins move the *opposite* way from L-1's keeper-duals
replay (gas_ct falls from its 3,000 MW cap to 1,000 MW), measuring the
fleet/run-identity residual L-1 §1.1 declared but could not size. Four of five
addition metrics improve and every one still FAILs its band; the cobweb survives and
its recovery **overshoot gets worse** (terminal RM 25.19 → 40.24 %). The verdict is
therefore `fc K → O`, not a promotion and not a rejection: the disarm trades a
forward-looking-but-structurally-wrong object for a structurally-right-but-backward-looking
one, and neither is the developer pro-forma. On CAISO, the L-5 gate works and the
`--entry-screen-diagnostics` flag is **proven inert by a control arm** (the apparent
byte-identity failure is source-tree drift, not the flag); CAISO's own L-1 shows the
signal replacement closes **63–85 %** of the iron-air arbitrage requirement and still
does not build storage — a rule-25 divergence from ERCOT, where the same replacement
flipped iron-air positive.

---

## 1. The probe, and why its posture is measured rather than asserted

The charter required the disarm to run at *exactly* the registered t1h-refresh
posture with one flag changed. That is verified, not claimed:

| check | result |
|---|---|
| registered `run_config.json` → `ScenarioConfig` at HEAD | **zero field diffs**, cache key `28cef3500ec1fd9e` reproduced |
| the CLI invocation that produces it | **bare** — `--iso ERCOT --start-year 2021 --end-year 2025`; the registered leg inherited only shipped defaults |
| disarm arm | **exactly one** field differs (`entry_lookahead_reprice: True → False`), key `2eab21467a4214c7` |
| solve / bridge span | identical both arms: solved `[2021, 2023, 2024, 2025]`, bridged `[2022]` |
| holdout | no year outside the training window is solved, scored or registered; `--holdout-authorized` never needed or passed |

Four `ScenarioConfig` fields exist at HEAD that the 2026-08-22 config predates
(`ercot_adaptive_fixed_point`, `ercot_tie_zonal_interchange`,
`miso_offer_spread_anchored`, `nyiso_gas_bridge_reserve_duty_exclusions`); all four
are default-`False` and the cache key is unmoved, so the reconstruction is exact.

**No plumbing was added.** `--no-entry-lookahead-reprice` already existed
(`run_capacity_hindcast.py:1239`, `BooleanOptionalAction`).

**The two lookahead-internal gates needed no disarm, and config validation did not
refuse the combination.** Verified at HEAD rather than inherited from the charter:
the entire unified/scarcity block — `unified_signals`, `_screen_signal_for`, and the
`scarcity_sigma_r` consumer — sits inside `if config.entry_lookahead_reprice and …`
(`runner.py:3281`). With the reprice off it never runs, `unified_signals` stays `{}`,
and at the shipped `entry_price_signal_alpha = 1.0` the blend is a pass-through, so
every screen reads `econ_prices` — the run's own prior-year hourly zonal LP duals —
unchanged.

One correction to the charter's description, immaterial to the result: the charter
names `prior_results["prices"]` (runner.py:1787-1789) as the armed fallback. In fact
`price_signal` is still *set* (to `econ_prices`) and passed, so line 1787 reads it
rather than falling through to `prices`. Both are the same duals object; the
mechanism is as chartered.

### 1.1 Why there is a control arm

The registered bundle commits **no evolution ledgers** — repo policy, stated in
`.gitignore` §9: "bundle internals are reproducible from the recorded config". That
is exactly why L-1b had to *reconstruct* the shipped per-step split (its footnote 1).
Rather than compare a measured treatment against a reconstruction, this lane
re-solved the shipped posture from the same tree.

**The control validates the reconstruction, and establishes determinism** — the
second result matters because a later section depends on it:

| | control (measured) | L-1b / finding (reconstructed) |
|---|--:|--:|
| RM, ledger 2023 | **8.54 %** | 8.5 % |
| RM, ledger 2024 | **14.65 %** | 14.7 % |
| RM, ledger 2025 | **25.19 %** | 25.2 % |
| CO2 vs registered `score.json` | **delta 0.0 t, all three scored years** | — |
| the four `screen_signal_diag_*.npz` | **byte-identical to the committed dumps** | — |

Re-solving this pipeline at the same cache key is **bit-reproducible**.

Per repo policy the ledgers stay uncommitted; the ledger-derived evidence is
committed instead as `results/calibration/entry_signal_disarm_ledger_ercot.json`
(probe `scripts/probes/entry_signal_disarm_ledger_compare.py`), the established
probe-artifact pattern, so the next session reads the per-step decisions without
replaying a solve.

---

## 2. The pre-registered predictions, scored

L-1's predictions were committed in
`results/calibration/entry_signal_l1_dual_replay_ercot.json` and tabulated in that
finding §1.2–§1.4 **before this solve existed**. Scored against the ledger:

| # | L-1 prediction | ledger outcome | verdict |
|---|---|---|:--|
| 1 | steady ~3 GW/yr of the longest-duration tech instead of the one-shot 5 GW | control: storage **only** in 2023 (iron_air 3,000 + flow_battery 2,000 = 5.0 GW). Disarm: **iron_air exactly 3,000 MW in every step 2022/2023/2024/2025** | **CONFIRMED** |
| 2 | the second storage slot flips flow_battery → compressed_air (§2.3) | control 2023 `flow_battery 2,000`; disarm 2023 `compressed_air 2,000` | **CONFIRMED** |
| 3 | wind at capture parity ⇒ wind stops being anti-selected | control: wind absent from every step (0.350 GW scored = procured only). Disarm: **wind 1,092.2 MW enters in 2022**, scored 1.442 GW | **CONFIRMED in kind** (entry appears; level still −89 % vs actual) |
| 4 | the entering-2024 gas margins turn **positive** (gas_cc −10,730 → +22,583; gas_ct −42,684 → +350) | disarm entering-2024: gas_cc unchanged at the 3,000 MW cap, **gas_ct falls 3,000 → 1,000 MW** | **NOT CONFIRMED — the informative miss** |

### 2.1 What prediction 4's failure measures

L-1 §1.1 declared its own bound in writing: the dual arm used the **backcast
keeper's** hourly duals as a stand-in, so its delta measured "signal construction
**plus a fleet/run-identity residual**", and the exact object — the T1-H run's own
prior-year duals at its own evolved fleet — was only obtainable from this solve.

Prediction 4 is where that residual bites. On the keeper's backcast duals (real
ERCOT prices, actual fleet) entering-2024 gas looked profitable. On the disarm run's
**own** forecast-lane duals — priced on a fleet the model has already over-built with
9 GW of gas_cc and 12 GW of storage — gas_ct is worth *less*, not more, and the
screen buys 2 GW less of it. The stand-in over-predicted gas value; the disarm
removes the bound and sizes the residual as **material for gas and immaterial for
storage** (predictions 1 and 2 held exactly).

This is the cleanest possible vindication of L-1's decision to state the bound
rather than bury it.

### 2.2 Per-step ledger, both arms

Entry decisions in MW, by ledger year (2022 is the bridge; it carries decisions but
no reserve margin):

| ledger year | arm | thermal + VRE decided | storage decided | RM % |
|---|---|---|---|--:|
| 2021 | control | — | — | 19.00 |
| | **disarm** | — | — | **19.00** |
| 2022 (bridge) | control | gas_cc 3,000 · gas_ct 1,571 · solar 4,946.6 | — | — |
| | **disarm** | gas_cc 3,000 · gas_ct 1,571 · solar 4,946.6 · **wind 1,092.2** | **iron_air 3,000 · CAES 2,000** | — |
| 2023 | control | gas_cc 3,000 · gas_ct 3,000 · solar 5,550 | iron_air 3,000 · flow 2,000 | 8.54 |
| | **disarm** | gas_cc 3,000 · gas_ct 3,000 · solar 5,550 | **iron_air 3,000 · CAES 2,000** | **14.00** |
| 2024 | control | gas_cc 3,000 · gas_ct 3,000 · solar 6,000 | — | 14.65 |
| | **disarm** | gas_cc 3,000 · **gas_ct 1,000** · **solar 8,000** | **iron_air 3,000 · CAES 2,000** | **25.92** |
| 2025 | control | — | — | 25.19 |
| | **disarm** | — | **iron_air 3,000** | **40.24** |

---

## 3. Bands and trajectory — attached evidence, never the verdict (rule 1)

Rule 1 `[R-STRUCT]` cuts both ways here and is honoured in both directions: the cell
is **not** flipped because bands improved, and **not** held because one worsened.

### 3.1 Additions (scored 2023–2025, decision basis)

| tech | actual GW | control/registered | disarm | \|err\| control → disarm |
|---|--:|--:|--:|:--|
| wind | 12.663 | 0.350 | **1.442** | 12.313 → **11.221** |
| solar | 25.080 | 17.987 | **19.987** | 7.093 → **5.093** |
| gas_cc | 0.244 | 9.000 | 9.000 | 8.756 → 8.756 (cap-bound both arms) |
| gas_ct | 3.692 | 7.571 | **5.571** | 3.879 → **1.879** |
| storage | 13.691 | 5.000 | **18.000** | 8.691 → **4.309** |
| retirements | 2.294 | 0.000 | 0.000 | unchanged |

**Four of five improve; every band still reads FAIL, and retirements are untouched
at 0.000 GW.** The disarm is not close to a passing posture and is not offered as one.

### 3.2 The cobweb survives, and the overshoot worsens

| | control (= registered) | disarm |
|---|--:|--:|
| RM path (ledger 2021 → 2025) | 19.00 → 8.54 → 14.65 → 25.19 | 19.00 → 14.00 → 25.92 → **40.24** |
| swings (pp) | −10.46 / +6.11 / +10.54 | **−5.00 / +11.92 / +14.32** |

B-2 is confirmed real for the third time: the oscillation is a property of a
one-pass, no-foresight entry loop, not of the signal. What the disarm changes is its
*shape* — it damps the down-swing (−10.46 → −5.00 pp) and **amplifies the rebound**,
ending 15 pp higher, driven by ~12 GW of decided storage against the control's 5.
That is a real cost and it is reported at full magnitude.

### 3.3 A structural cost that is not in any band

**A disarmed run emits no `screen_signal_diag_*.npz` at all** (0 vs the control's 4):
the dump is written inside `_screen_signal_for`, which lives inside the reprice gate.
So the L-5 offline-diagnosis route — landed one rung ago precisely to make screens
diagnosable — **does not survive the disarm**. The signal is not lost, it is
relocated: it becomes `econ_prices`, recoverable from the run's own hourly outputs.
Any future promotion of the disarm should carry that relocation deliberately rather
than discover it.

---

## 4. The adjudication — `entry_lookahead_reprice`, ERCOT `fc`: **K → O**

The question rule 1 poses is not which arm scores better. It is **which signal
construction is the real developer pro-forma.** Both arms fail it, in opposite ways:

- **The shipped reprice has the right *intent* and the wrong *object*.** A developer's
  pro-forma is forward-looking, and the reprice is the only construction here that
  looks forward at all — it re-prices the entering year's net load against the
  current stack. But the object it produces is **zone-flat by construction** (measured
  in both ISOs below: `zonal_mean_range` and `hourly_cross_zone_spread` are exactly
  0.0), and ~90 % of its dispersion is the ORDC adder (D-8) — a summer-afternoon
  artifact, not a price any generator is paid. No developer prices a project off a
  system-wide scalar that ignores their interconnection node.
- **The duals fallback has the right *object* and the wrong *expectation model*.** The
  LP dual at the node, over the hours the unit runs, *is* the price a generator
  receives — locational, with real intraday shape, and it makes the storage screen's
  per-window best-zone selection live for the first time. But reading **last year's**
  realized duals as next year's expectation is naive-expectations — the textbook
  cobweb — which no developer pro-forma uses either.

So the disarm is not a structural upgrade; it is a **trade of one structural defect
for another**, with measured repairs (locational dispersion, steady long-duration
storage, wind entering) and a measured cost (terminal RM +15 pp, dumps gone).

Verdict **`fc: K → O`** — measured, not adjudicated to a keeper or a rejection:

- **Not `R`.** The disarm demonstrably repairs defects L-1 attributed to this
  mechanism, on this mechanism's own evidence. Rejecting it would bury a real finding.
- **Not `K` for the disarm, and no promotion.** Arming it as the lane default is the
  owner's decision, stated explicitly in the charter, and the RM cost plus the dump
  loss are exactly what such a decision must weigh.
- **`cell` (backcast) is untouched** — this lane tested the forecast lane only.

`scripts/check_mechanism_matrix.py` passes; the ERCOT shard cell carries the full
evidence string (rule 26 duty b, discharged in this session).

---

## 5. CAISO — dump production, and a stop-the-line that resolved the other way

### 5.1 The L-5 gate works

The CAISO 2021–2025 realized hindcast re-ran at exactly its registered posture
(`run_config` rebuilds to `408f9199a82f5814` at HEAD, **zero field diffs**) plus
`--entry-screen-diagnostics`, and emitted screen-signal dumps for the first time —
defect **D-7 cleared**.

It emits **two** dumps (`2023_for_2024`, `2024_for_2025`), and that is the right
number, not a shortfall. CAISO ships `capacity_screen_unified_lookahead=False`, so
`lookahead_next_ok` suppresses the lookahead whenever the entering year is a bridge
year; ERCOT's unified-ON refresh priced all four steps. The probe now **asserts** its
step map against the dumps on disk rather than assuming it.

### 5.2 The byte-identity check, and the control that settled it

Against the committed registered `score.json` the dump run showed **every fleet
metric identical** but a CO2 difference: **+68.4 / −49,190.1 / −44,077.4 t** across
2023/2024/2025. That is the charter's stop-the-line signature, and it was treated as
one — nothing was pushed on this item until it was resolved.

A control arm resolves it decisively. Re-solving the registered CAISO posture with
**no flag at all**, at the registered cache key:

| comparison | result |
|---|---|
| control (no flag) vs dump run (flag on), **all fields of `score.json`** | **IDENTICAL** |
| control (no flag) vs committed registered bundle | differs by **exactly** +68.4 / −49,190.1 / −44,077.4 t |

**The flag is inert and its documented contract holds.** The difference is
**source-tree drift** between the registered solve (2026-08-22, sha `e2a333f`) and
HEAD — and the ERCOT control proves re-solving is otherwise bit-reproducible, so the
drift is real and CAISO-specific.

This inverts what the naive check implied, and it is why the control existed: without
it, the honest reading of the raw comparison would have been "the flag is not
output-only", which is false.

**Reported, not chased:** nine `src/market_sim` commits intervene, of which
`caiso-217`'s measured CAISO generator-hub-membership crosswalk intake (`f0dd328`) is
the most likely dispatch-affecting candidate. It is **not asserted as the cause** —
isolating it needs a bisection this lane did not run. It moves dispatch only:
additions, retirements and every band are unchanged. **The consequence worth acting
on is that the committed CAISO registered bundle's `score.json` no longer reproduces
at HEAD**, so any lane treating it as a reproduction baseline should re-solve first.
ERCOT's does reproduce.

No dashboard registration was made — this is dump production for an
already-registered run.

### 5.3 CAISO L-1, measured offline

The probe was extended by ISO rather than duplicated
(`scripts/probes/entry_signal_l1_dual_replay.py --iso CAISO`); the committed ERCOT
artifact reproduces **identically** after the refactor, with only a `zone_names`
provenance key added.

**The WECC import node, handled explicitly.** It is a real topology difference
between the two lanes, not a naming mismatch: the forecast lane's `ISOConfig` carries
one seam node (`WECC_import`), while the backcast keeper `caiso200_h1_memberpanel`
resolves the same seam as **two** external hub nodes (`WECC_DSW`, `WECC_PNW`). The
five in-state zones (NP15, ZP26, LA_BASIN, SDGE, SP15_rest) match exactly and are the
only zones an entry candidate can build in — `get_renewable_zone` returns an in-state
zone, and a seam node's dual is an external hub price, not a CAISO clearing price a
new CAISO unit would earn. Aggregating the two hub rows into a synthetic
`WECC_import` row would invent a price the model never formed, so the node is
**dropped from both arms**, keeping the cross-arm delta like-for-like.

**Validation gate: PASSED.** CAISO's phase-0 artifact carries no `decision_years`
(it predates the L-5 gate — D-7), so `break_even` is the only committed overlap. It
is a real gate: its two columns are exactly the price-independent legs of this
probe's storage stack, and the replay reproduces **6/6 techs on both annual cost and
RA capacity value**.

**(i) Margin signs** ($/MW-yr, energy leg):

| step | tech | shipped | duals | flip |
|---|---|--:|--:|:--|
| 2024 | gas_cc | −82,715 | **+66,594** | **− → +** |
| | gas_ct | −127,009 | −11,181 | no (−91 %) |
| | solar (per-MWh) | −6.18 | **+2.92** | **− → +** |
| | wind (per-MWh) | +7.39 | +19.25 | no (both +) |
| 2025 | gas_cc | −145,229 | −111,874 | no |
| | gas_ct | −128,112 | −118,945 | no |

**(ii) Storage ranking and allocation — the decisive CAISO result.** The ranking is
**identical in both arms** (iron_air, compressed_air, li_ion_4hr, li_ion_8hr,
flow_battery, li_ion_12hr) and the allocator is **empty in both**: every tech is
negative on the shipped signal *and* on the duals. Signal replacement moves the level
a long way and still does not cross zero:

| step | arm | iron-air arbitrage $/MW-yr | iron-air margin $/MW-yr |
|---|---|--:|--:|
| 2024 | shipped | **0.0** | −61,248 |
| | duals | **32,018** | −29,230 |
| 2025 | shipped | 1,964 | −59,285 |
| | duals | **43,040** | −18,208 |

**(iii) Capture ratios** (build-zone row): wind 0.9894 → 0.9347, solar 0.9002 →
0.8193 (2024); wind 0.9879 → 0.9225, solar 0.8433 → 0.7880 (2025). **CAISO shows no
B-3-type inversion** — its shipped signal is already near wind parity, and the duals
move both techs slightly *down*. That is the expected consequence of CAISO running
`scarcity_price_overlay = False`: with no ORDC adder there is no summer-afternoon
shape to manufacture the ERCOT anti-correlation. Rule 25 in action — the same
mechanism, a different market, a different answer.

### 5.4 §8 item 1's named question, answered with a measurement

> *Is CAISO's base-merit daily spread below the \$14.36/MWh iron-air nine-day
> threshold?*

**Yes — and the sharper measurement is worse than the spread proxy suggests.**

| screen | shipped daily top4/bot4 spread | duals |
|---|--:|--:|
| entering-2024 | **\$12.71** | \$35.46 |
| entering-2025 | **\$14.36** | \$29.97 |

Against iron-air's \$14.36/MWh *gross* requirement, the shipped base-merit spread is
below it in 2024 and exactly at it in 2025. *(The 2025 figure coinciding with the
threshold to the cent is a genuine coincidence — the two are unrelated computations,
one a price-shape statistic and the other cost ÷ (windows × duration) + degradation.
Flagged so it is not read as constructed.)*

The binding measurement is the model's own arbitrage estimator over iron-air's 40
nine-day windows (4,000 MWh/MW-yr), against a **\$12.69/MWh net** requirement:

| screen | shipped | duals |
|---|--:|--:|
| entering-2024 | **\$0.00/MWh — 0.0 %** of requirement | **\$8.00/MWh — 63.1 %** |
| entering-2025 | \$0.49/MWh — 3.9 % | **\$10.76/MWh — 84.8 %** |

So CAISO's shipped MC-step object delivers **essentially zero** exploitable arbitrage
for a 100-hour device — D-8 measured from the storage side — and the model's own LP
duals close **63–85 %** of the gap but **still fall short in both years**.

**The CAISO conclusion, and it differs from ERCOT's (rule 25):** signal replacement
alone would **not** restore CAISO storage entry. In ERCOT the duals flipped iron-air
positive; in CAISO they do not. CAISO's 0-MW-vs-15,147-actual storage miss is
therefore **larger than the signal defect** — the residual sits in the value stack
(the RA credit at \$77,611/MW-yr against a \$138,859/MW-yr cost, i.e. D-9's missing
AS credit) or in the cost basis, not only in the price shape. **CAISO L-1 is
measurement only: no CAISO cell verdict moves**, and a CAISO disarm solve remains a
later rung.

---

## 6. The next rung, named with its adjudicating measurement

**Next rung: the forward-expectation object — price the entering year on the model's
own duals *re-priced against the entering year's stack*, i.e. the one construction
neither arm here tested.** This lane measured the two corners (forward-looking +
zone-flat; locational + backward-looking); the untested cell is locational **and**
forward-looking, which is what a developer pro-forma actually is. It is a
**replacement** for the signal's construction, not a shape correction stacked on it,
so it satisfies rule 19 `[R-ONE-MECH]` by the same argument the disarm did.

**The adjudicating measurement:** an ERCOT T1-H arm that keeps
`entry_lookahead_reprice=True` but re-prices on the **zonal** dual surface rather
than the zone-flat MC step — scored against *this* finding's two arms as the
bracketing pair, with the pre-registered prediction that it reproduces the disarm's
storage and wind repairs **without** the +15 pp terminal-RM overshoot (because it
keeps the forward view that damps the rebound). If it does not, the overshoot is not
the expectation model's and D-1's bang-bang volume rule owns it — which L-1b already
measured as the zero-DOF candidate.

Sequenced before any CAISO signal lever: **CAISO's storage miss is not signal-bound**
(§5.4), so the CAISO queue's next rung is the **value stack** — D-9's missing AS
credit — not a CAISO disarm.

**Inherited as constraints, not re-tested:** signal replacement does not restore
li-ion (L-1 measured it; this solve did not disturb it), and B-2's cobweb is real in
every arm run so far.

**Named and NOT chased** (rule 21 `[R-DOF]`): the terminal-RM overshoot tempts an
elasticity or damping coefficient. There is none in this lane and there should be
none — it is an **open root-cause issue**, owned by D-1's volume rule.

---

## 7. Rule compliance

- **Rule 1 `[R-STRUCT]`** — the cell verdict is argued from which object is the real
  pro-forma, not from bands; bands are reported at full magnitude in both directions
  (four improve, terminal RM worsens 15 pp) and are explicitly labelled attached
  evidence. No number is reached through an unreal mechanism.
- **Rule 13 `[R-MEASURED]`** — no measured outcome enters any model path; the keeper
  duals appear only inside evidence artifacts, as a measurement instrument.
- **Rule 19 `[R-ONE-MECH]`** — the object under test is the **replacement** (the
  disarm), never a shape correction stacked on the shipped signal; exactly one
  reserve-price mechanism remains in play, unchanged.
- **Rule 21 `[R-DOF]`** — no elasticity, damping or scaling coefficient exists in any
  probe here; the trajectory gap is named as an open root-cause issue (§6).
- **Rule 22 `[R-HOLDOUT]`** — every solve spans the registered window
  (2021 seed + 2023–2025 training, 2022 bridged). No out-of-training year is solved,
  scored or registered; no marker is spent; the freeze stayed ACTIVE throughout.
- **Rule 25 `[R-ISO-SCOPE]`** — CAISO derives its own step map, its own validation
  gate, its own zone handling and its own numbers; the ERCOT verdict transfers
  nothing, and CAISO's answer is measured to *differ* from ERCOT's (§5.3–§5.4).
- **Rule 26 `[R-MECH-MATRIX]`** — the tested cell (`entry_lookahead_reprice`, ERCOT
  `fc`) is updated in this session with its evidence citation; no new
  `ScenarioConfig` field was added, so duty (c) does not fire; the two standing
  adjudications (`ercot_adaptive_fixed_point`, `miso_offer_level_dispersion`) were
  not re-opened.
- **Rule 27 `[R-PUSH]`** — every file ≥300 lines was edited locally and blob-verified
  after push (`entry_signal_l1_dual_replay.py` 538 → 674 lines; remote blob sha, line
  count and sha256 all matched local; nothing shrank). `git push` on a freshly-fetched
  base throughout.
- **Repo policy honoured over the charter's wording on one point:** the charter listed
  evolution ledgers among the "slim files" to commit, but `.gitignore` §9 deliberately
  excludes them as reproducible from the recorded config. The ledgers are therefore
  **not** force-added; their evidence is committed as a probe artifact instead, which
  serves the charter's intent (the next session reads the decisions without a replay)
  without overriding a documented repo decision.
- **Out of scope, untouched:** keeper shards, `calibration-complete.json`,
  `holdout-freeze.json`, the backcast registry, L-2/L-3/L-4/L-6, the
  `STORAGE_TECH_BUILD_SHARE_CAP` citation defect, the li-ion technology split, and
  `.github/workflows/`. All four solves ran in-session; no CI job was created.

---

## 8. Reproduction

```
# the two ERCOT arms (bare invocation = the registered posture; one flag differs)
uv run python scripts/run_capacity_hindcast.py --iso ERCOT --start-year 2021 --end-year 2025 \
    --out-dir results/hindcast/ercot-2021-2025-realized-t1h-control
uv run python scripts/run_capacity_hindcast.py --iso ERCOT --start-year 2021 --end-year 2025 \
    --no-entry-lookahead-reprice \
    --out-dir results/hindcast/ercot-2021-2025-realized-t1h-disarm

# the two CAISO arms (flag-on dump production, and the no-flag control that exonerates it)
uv run python scripts/run_capacity_hindcast.py --iso CAISO --start-year 2021 --end-year 2025 \
    --entry-screen-diagnostics --out-dir results/hindcast/caiso-2021-2025-realized-dumps
uv run python scripts/run_capacity_hindcast.py --iso CAISO --start-year 2021 --end-year 2025 \
    --out-dir results/hindcast/caiso-2021-2025-realized-control

# score each, then the two probes
uv run python scripts/score_capacity_hindcast.py --bundle <each bundle>
uv run python scripts/probes/entry_signal_disarm_ledger_compare.py \
    --disarm results/hindcast/ercot-2021-2025-realized-t1h-disarm \
    --control results/hindcast/ercot-2021-2025-realized-t1h-control \
    --registered results/hindcast/ercot-2021-2025-realized-t1h-refresh \
    --out results/calibration/entry_signal_disarm_ledger_ercot.json
uv run python scripts/probes/entry_signal_l1_dual_replay.py --iso CAISO \
    --bundle results/hindcast/caiso-2021-2025-realized-dumps \
    --duals-bundle results/calibration/caiso200_h1_memberpanel \
    --out results/calibration/entry_signal_l1_dual_replay_caiso.json
```

`data/clean` is derived and gitignored, so a fresh container must run
`PYTHONPATH=. uv run python scripts/regenerate_clean.py` before any solve (48/51
datatypes succeed on the ercot+caiso profiles; the three failures are MISO/NYISO/PJM
raw mirrors absent from those profiles and irrelevant here).

Both probes hard-fail rather than report if their gates do not reproduce: the ERCOT
comparison refuses unless the control reproduces the registered key, the disarm
differs in exactly one field, and the solve spans match; the CAISO replay refuses
unless the phase-0 `break_even` rows reproduce and the step map matches the dumps on
disk.
