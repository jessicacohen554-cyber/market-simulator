# PRECOMMIT — C-1 joint wind charter: the dual-based signal object and the D11-R volume rule A/B'd TOGETHER (ERCOT T1-H), kill-gates fixed ex ante

**Authority.** Owner ruling **R-B**, 2026-08-31 director sitting: *"Joint
charter"* — on the Leg-B measurement
(`docs/FINDING-t1h-capacity-entry-phase0-2026-08-30.md` §4.1: the dual-based
signal object closes **8.87 %** of the 12.313 GW ERCOT wind entry miss, the
D11-R volume rule alone **4.91 %**, naively summing to ~13.8 % and read as
complementary) **promote nothing yet**; A/B the two mechanisms **together**
against the wind bands, kill-gates fixed ex ante. The joint arm is the only
untested combination.

**This precommit is pushed before any solve, any implementation commit, and
any registration.** Everything below is fixed now and scored against later;
nothing in it is derived from a residual (rules 13 `[R-MEASURED]` /
23 `[R-FROZEN-DERIVE]`).

Program: `docs/forecast-development-plan-2026-07.md` (T1-H). Parent charter:
`docs/PRECOMMIT-t1h-capacity-entry-2026-08-30.md` (Leg B was chartered there
as a **measurement** rung; R-B converts its measured record into this A/B).
Cited records: `docs/FINDING-t1h-capacity-entry-phase0-2026-08-30.md` (the
Leg-B measurement), `docs/FINDING-entry-signal-disarm-2026-08.md` (the C-1
verdict — `entry_lookahead_reprice` ERCOT cell **`K`** / **`fc O`**),
`docs/handoffs/FINDING-capx-d11r-entry-volume-rule-2026-08-30.md` (the volume
rule and its A/B), `docs/FINDING-t1h-capentry-phase1-ab-2026-08-30.md` (the
Leg-A A/B whose driver and posture discipline this lane reuses).

---

## 0. The base, and the control posture — stated explicitly, measured not assumed

**Fresh base:** `origin/main` @ **`54ca19ae0782871bd4adbcb482bc531a66618402`**
(`54ca19a`, the #4428 merge), fetched at the top of this session. Ruling R-A
is arming Leg A's two mechanisms in a parallel lane; **at this base nothing
from R-A has landed** — read from the source tree at the base sha, not
inferred:

| field | default at the base | consequence for the control |
|---|---|---|
| `entry_lookahead_reprice` | **`True`** (`scenarios.py:3893`, owner-approved default-ON, FF-2A) | the control consumes the **repriced zone-flat** signal |
| `entry_margin_exhaustion` | `False` (`scenarios.py:4221`) | the control allocates **bang-bang** |
| `storage_entry_availability_gate` | `False` (`scenarios.py:4311`) | **R-A NOT landed at this base** |
| `storage_entry_cost_normalized_rank` | `False` (`scenarios.py:4341`) | **R-A NOT landed at this base** |
| `entry_forward_reserve_leg` | `False` (`scenarios.py:4260`) | D12 leg unarmed |
| `entry_forward_expectation_signal` | `False` (`scenarios.py:4175`) | unarmed |

**THE CONTROL ARM IS THE REGISTERED T1-H POSTURE**, produced by the *bare*
invocation of `run_capacity_hindcast.py --iso ERCOT --start-year 2021
--end-year 2025` (the D11-R §7 / Leg-A byte precedent), i.e. the recipe the
registered bundle `ercot-2021-2025-realized-t1h-refresh` carries in its
committed `run_config.json`: `entry_lookahead_reprice=True`,
`capacity_screen_unified_lookahead=True`,
`capacity_screen_scarcity_restoration=True`,
`entry_pipeline_aware_signal=True`, `screen_reserve_value_enabled=True`,
`entry_price_signal_alpha=1.0`, `mode="forecast"`, `hindcast=True`; every
gated entry mechanism above at its default-OFF. **Expected control cache key
`28cef3500ec1fd9e`** — the key the registered refresh, the C-1 control, the
D11-R control, the D12-C control and the Leg-A control all reproduce.

**If R-A lands between this precommit and the solves, the control does NOT
move.** Two reasons, fixed here: (a) the control must be the posture the
*joint arm* differs from in exactly the two chartered fields, and an R-A
arming would introduce two more; (b) both arms are solved by this session on
**one tree**, so the A/B is internally valid regardless of what main does
meanwhile. Any drift between that tree and `origin/main` at push time is
**measured and recorded** in the finding (the v13 C-1 drift discipline), never
assumed away.

---

## 1. The joint arm — and the constructibility finding that must be stated ex ante

### 1.1 What the two objects are

- **The dual-based signal object** = `entry_lookahead_reprice=False`. The
  disarm arm *is* that object (Phase-0 §4.1): with the reprice disarmed every
  capacity screen reads `econ_prices` — the run's **own prior-year hourly
  zonal LP duals**, locational and real-shaped, but backward-looking (naive
  cobweb expectations). Wind 0.350 → **1.442 GW**.
- **The D11-R volume rule** = `entry_margin_exhaustion=True`. It replaces the
  allocators' bang-bang volume rule with a tranche walk that stops when the
  screen's **own repriced margin** is exhausted, bounded by the same caps.
  Wind 0.350 → **0.954 GW**.

**The joint arm is `entry_lookahead_reprice=False` + `entry_margin_exhaustion=True`,
and NOTHING else differing from the control.**

### 1.2 The finding: at the base, that posture is REFUSED — and would be INERT if the refusal alone were lifted

Measured at the base sha, from committed code, before any solve:

| check | measured at `54ca19a` |
|---|---|
| `ScenarioConfig(iso="ERCOT", mode="forecast", entry_lookahead_reprice=False, entry_margin_exhaustion=True)` | **raises `ValueError`** — `scenarios.py:13738` |
| the refusal's stated reason | *"with the reprice disarmed there is no repricing instrument and the walk would silently reproduce the bang-bang allocation"* (the FFR-8A refuse-rather-than-inert pattern) |
| where the walk is constructed | `runner.py:3902`, **inside** the block gated at `runner.py:3506-3511` on `config.entry_lookahead_reprice and mode=="forecast" and lookahead_next_ok` |
| what the allocators do with no walk | `new_entry.py:1569` / `storage.py:1976` — `if entry_reprice is not None:`; `None` ⇒ the untouched bang-bang path |
| default forecast cache key at the base | `603c2498bf71d21d` (matches the D11-R citation) |

So, stated at full strength and **before** any measurement: **lifting the
config refusal ALONE would produce an arm byte-identical to the pure disarm
arm** — `entry_walks` would stay empty, `entry_walks.get(year)` would return
`None`, and both allocators would take the bang-bang branch. That is not the
joint object the ruling asks for; it is the signal leg wearing a second flag.
**The refusal is a correct description of the shipped WIRING, and is exactly
what must be narrowed to execute R-B.**

### 1.3 Why the joint object nevertheless exists, and what the enabling change is

The walk is **delta-only** by construction. `_EntryRepriceWalk.signal()`
(`runner.py:976`) returns

```
consumed + alpha x (S(state) - S(0))
```

where `consumed` is whatever price array the screens were handed (2-D zonal
handled explicitly at `runner.py:979-981`) and `S` is the lookahead
instrument re-invoked at the walk's additions. **The walk never supplies the
signal LEVEL; it supplies a within-year capacity-response DELTA.** The
instrument `_lookahead_reprice_signal` (`runner.py:604`) exists and is
callable independently of whether its output level is consumed. Therefore the
joint object — *locational level from the duals, capacity-response delta from
the instrument* — is well defined, and `S(state) - S(0)` is not identically
zero, so exhaustion **can** bind. The refusal's "could never bind" is a
statement about the wiring, not about the arithmetic.

**The enabling change, fixed here and scoped to exactly this:**

1. `scenarios.py` — narrow the `entry_margin_exhaustion` ⇒
   `entry_lookahead_reprice` refusal so the pair is constructible. (The
   `entry_forward_expectation_signal` and `entry_forward_reserve_leg`
   refusals on the same field are **untouched**.)
2. `runner.py` — widen the seam's availability gate to
   `(entry_lookahead_reprice or entry_margin_exhaustion)` and **guard the
   CONSUMPTION**, so that with the reprice disarmed the seam runs for its
   walk (and its diagnostic dump) only: `price_signal` stays `econ_prices`
   and `unified_signals` stays empty. Both `_screen_signal_for` calls (the
   `next_year` one and the bridge-adjacent one) stay unconditional inside the
   widened gate, so the joint arm gets a walk for **every** entering year the
   reprice-armed arm gets one for — no bridge asymmetry.
3. Unit tests asserting (a) the pair now constructs, (b) the walk object is
   live in the disarmed-consumption posture, (c) the consumed signal in that
   posture is `econ_prices` and not the repriced level, (d) byte-identity of
   every other posture.

**This is NOT a new mechanism and introduces NO new degree of freedom
(rules 19 `[R-ONE-MECH]`, 21 `[R-DOF]`, 24 `[R-REGISTRY]`):** no new
`ScenarioConfig` field, no new constant, no new coefficient. The joint
posture is fully determined by **two already-registered fields**, both
already carried in `run_config.json` and both already cache-key terms. Rule
26 `[R-MECH-MATRIX]` duty (c) does not fire (no `ScenarioConfig` field is
added); duty (b) fires and is discharged in this session on the two tested
ERCOT cells.

### 1.4 Declared bounds of the joint object (recorded ex ante, not discovered later)

- **The delta stays zone-flat.** The instrument returns a system row, so in
  the joint arm a **locational level** is walked by a **flat delta**. The
  joint object is therefore *not* a zonally-resolved volume rule; D-8's
  zone-flatness survives in the response surface even though it is gone from
  the level. Any result must be read with that bound.
- **The reserve leg keeps the shipped realized-`r` basis.** `screen_reserve_value_enabled`
  is on in both arms; `entry_forward_reserve_leg` stays OFF (its own refusal
  is untouched). The D11-R structural finding — that the realized-adder
  reserve leg is an inexhaustible within-year floor that keeps *gas*
  cap-bound — therefore applies to the joint arm too, and is **predicted, not
  discovered**, below.
- **The joint arm will emit `screen_signal_diag_*.npz` dumps** (the seam
  runs), where the pure disarm arm emits **0** (Phase-0 §4.2, verified by
  file count). This is output-only — it changes no dispatch or entry outcome
  — and is recorded as a side benefit: it makes the joint posture's signal
  object offline-diagnosable, which the disarm posture is not.

---

## 2. The two-arm design

| | control | joint arm |
|---|---|---|
| bundle | `results/hindcast/ercot-2021-2025-realized-t1h-c1joint-control` | `results/hindcast/ercot-2021-2025-realized-t1h-c1joint-arm` |
| invocation | bare (registered posture) | `--no-entry-lookahead-reprice --entry-margin-exhaustion` |
| `entry_lookahead_reprice` | `True` | **`False`** |
| `entry_margin_exhaustion` | `False` | **`True`** |
| every other field | identical | identical |
| expected cache key | **`28cef3500ec1fd9e`** | distinct (recorded when measured) |

Window: `--iso ERCOT --start-year 2021 --end-year 2025` — solved
[2021, 2023, 2024, 2025], bridged [2022], i.e. **the registered window
only**. `--holdout-authorized` is **never** passed; no out-of-training year is
solved, scored or registered (rule 22 `[R-HOLDOUT]`).

**Both arms are solved by this session on one tree, sequentially** — control
first, then the arm. Rule 12 `[R-PARALLEL]` governs LP solves and years stay
sequential within each invocation; the two *invocations* are also sequential
because the container's memcg (~15 GiB total) is shared and two concurrent
ERCOT T1-H invocations swap-thrash rather than parallelize — the same
container-scoped decision the Leg-A A/B recorded (`FINDING-t1h-capentry-phase1-ab`
§1).

---

## 3. Kill-gates — FIXED EX ANTE, applied mechanically by the driver

Both are evaluated on the **addition-metric bands** from each bundle's
`score.json` (decision basis 2023–2025 vs RD-5 actuals), over the five scored
techs `{wind, solar, gas_cc, gas_ct, storage}`, on `|err_frac|`, at **full
magnitude in both directions with no netting** (rule 1 `[R-STRUCT]`).

- **K1 — REJECTED.** Fires if **any** addition-metric band moves **away** from
  actuals by more than the **sum of the improvements on the others**.
  Formally, with `d_t = |err_frac_arm(t)| - |err_frac_control(t)|`,
  `I = Σ_{t : d_t < 0} (-d_t)` and `W = { t : d_t > 0 }`: K1 fires iff
  `∃ t ∈ W with d_t > I`. Every `d_t` is reported whatever the verdict.
- **K2 — INERT.** Fires if the arm is **indistinguishable from the control**:
  no `model_gw` differs by more than 1e-9 on any of the five techs **and**
  every per-step entry/storage decision row is equal. An inert arm takes cell
  **`I`**.

**A fired kill-gate is a REJECTION and is recorded as one** — matrix cells go
`R` (K1) or `I` (K2), and the finding says so in its title. Nothing is
withheld or re-run to avoid a fire, and no gate is re-defined after the
numbers are seen.

**K1 is expected to be in genuine jeopardy here, and that is deliberate.**
The two single arms pull in opposite directions on the bands: the **disarm**
improves four of five (wind 0.350 → 1.442, solar 17.987 → 19.987, gas_ct
7.571 → 5.571, storage 5.000 → 18.000 — |err| 8.691 → 4.309 GW — against
actuals 12.663 / 25.080 / 3.692 / 13.691; gas_cc unchanged at 9.000 — all
five still FAIL), while the
**D11-R** arm worsens **four of five** (solar 17.987 → 7.687, gas_cc
9.000 → 12.000, gas_ct 7.571 → 10.571, storage 5.000 → 3.000; only wind
improves). A joint arm that inherits the D11-R exhaustion's band pattern is a
plausible K1 fire. Per rule 1, K1 is a gate
on *this A/B's* claim, **not** a licence to withdraw a structurally-argued
mechanism; the finding will say which of the two it is.

### 3.1 The complementarity read (REPORTED, not a gate)

The ruling's object is whether the two legs are complementary. That question
is **reported**, never gated — adding a third kill-gate would exceed the
ruling. Pre-registered as required reporting, from committed artifacts plus
this session's two bundles:

| arm | source | wind model GW | share of the 12.313 GW miss closed |
|---|---|--:|--:|
| control (registered posture) | this session + committed refresh | 0.350 | — |
| signal alone (`t1h-disarm`, key `2eab21467a4214c7`) | **committed** | 1.442 | 8.87 % |
| volume alone (`t1h-d11r-exhaustion`, key `cc7bbe1170db65c2`) | **committed** | 0.954 | 4.91 % |
| **joint (this A/B)** | this session | *measured* | *measured* |
| naive sum of the singles | arithmetic, **not a prediction** | 2.396 | 13.78 % |

Read as: **SUPER-ADDITIVE** (> 13.78 %), **ADDITIVE** (≈ 13.78 %),
**SUB-ADDITIVE but complementary** (> max single, 8.87 %),
**NON-COMPLEMENTARY** (≤ max single), or **WIRING-INERT** (identical to the
disarm arm — which would mean the enabling change did not make the walk live,
and would be reported as an implementation failure of this lane, not as a
property of the mechanisms).

---

## 4. Pre-registered directions — scored against later, in the finding

Fixed now, before any solve. Rule 1: these are *predictions*, and a miss is
reported as a miss, not quietly dropped.

1. **Not additive.** The two legs share one queue budget and one shared ISO
   cap ladder, so the joint wind build will **not** reach the naive 2.396 GW
   sum. Predicted joint wind ∈ **(0.350, 2.396) GW**, and predicted **>
   0.954 GW** (the volume-alone value) since the level leg is the larger
   single effect.
2. **Gas stays cap-bound.** The D11-R structural finding — the realized-`r`
   reserve leg is an inexhaustible within-year floor — is basis-unchanged in
   the joint arm, so gas is predicted to build to its caps in every clearing
   year, and the exhaustion damping to land on **VRE and storage**.
3. **Storage stays long-duration and li-ion-free.** Neither chartered
   mechanism touches the tech pool or the ranking object (Phase-0 §1.1:
   D-2/D-3 are not closed by either), and R-A is not in this posture, so
   li-ion is predicted to build **0 MW** in both arms.
4. **The overshoot worsens.** Disarm's terminal RM is 40.24 % vs the
   control's 25.19 %; the volume rule damps to 22.02 %. The joint arm's
   terminal RM is predicted **above the control's 25.19 %** and **below the
   disarm's 40.24 %** — the volume rule damping a level object that
   over-builds.
5. **B-2 survives.** The cobweb's sign pattern (down-up-up across the ledger
   swings) is predicted to persist in the joint arm, as it has in every arm
   measured so far. Its death would be the notable result.

---

## 5. Scoring artifacts — fixed here

| artifact | path |
|---|---|
| both bundles | `results/hindcast/ercot-2021-2025-realized-t1h-c1joint-{control,arm}` |
| per-arm scores | `score_capacity_hindcast.py --bundle <each>` → each bundle's `score.json` |
| **posture-gated compare driver** | `scripts/probes/joint_wind_entry_compare.py` (new; modelled on `storage_entry_repair_compare.py`) |
| A/B record | `results/calibration/joint_wind_entry_ab_ercot.json` |
| registration | `scripts/register_forecast_run.py` **only**, ids `ercot-2021-2025-realized-t1h-c1joint-{control,arm}` |
| finding | `docs/FINDING-c1-joint-wind-ab-2026-08-31.md` |
| matrix | `docs/codebase-site/data/mechanism-matrix/ERCOT.js` — **ERCOT shard only** |

**The driver HARD-FAILS unless the arms differ in exactly the two chartered
fields** (`entry_lookahead_reprice` True→False, `entry_margin_exhaustion`
False→True) — a third differing field aborts the comparison rather than
being explained afterwards. It also records the control-vs-committed drift
check against the registered bundle (cache key + all five addition rows), the
per-step decision rows, the storage mix, the RM path, the full-magnitude band
table, the K1/K2 verdicts, and the §3.1 complementarity read against the two
committed single arms.

**Rule 15 `[R-DASHBOARD]`:** both arms are forecast-family runs and go on the
**forecast** dashboard through `register_forecast_run.py` alone. The backcast
registry, every keeper shard, `calibration-complete.json`,
`holdout-freeze.json` and `program-status.json` are **untouched**.

---

## 6. Stop rule

1. **Enabling not posture-gated ⇒ STOP before the arm solve.** The default
   forecast cache key must stay **`603c2498bf71d21d`** and the control must
   reproduce **`28cef3500ec1fd9e`**. If the enabling change moves either, it
   is not posture-gated; the lane stops, reports, and registers nothing.
2. **Third field differs ⇒ STOP.** The driver's posture gate is the check;
   no A/B is reported on a contaminated posture.
3. **Wiring-inert ⇒ REPORT, do not patch around.** If the joint arm comes
   back byte-identical to the committed disarm arm, the lane reports that as
   an implementation failure and stops; it does **not** invent a second
   instrument to make the walk bite.
4. **Overtaken ⇒ close with the citation.** If a lane lands the same enabling
   before this one solves, this lane drops its enabling commit, re-verifies
   the posture, and proceeds with the A/B unchanged.
5. **No re-definition after the fact.** K1, K2, the §4 predictions and the
   §3.1 read are fixed by this document; the finding scores against them
   verbatim.

**Arming.** Whatever the verdict, **arming the joint posture in the T1-H
default lane is an OWNER decision on this A/B record — never this lane's.**
Both fields stay at their shipped defaults; no default is flipped.

---

## 7. Rule compliance

- **Rule 1 `[R-STRUCT]`** — the joint object is argued from the two
  mechanisms' structural claims (a locational price level; a margin-bounded
  volume), not from the residual; §4 pre-registers directions including ones
  that make bands worse, and every band is reported at full magnitude in both
  directions whatever the verdict.
- **Rule 12 `[R-PARALLEL]`** — years sequential within each invocation; the
  two invocations sequential for container-memcg reasons (§2).
- **Rule 13 `[R-MEASURED]` / 23 `[R-FROZEN-DERIVE]`** — no measured outcome
  enters any model path; no parameter is identified against any residual; the
  enabling change introduces no parameter at all.
- **Rule 15 `[R-DASHBOARD]`** — forecast namespace only, via
  `register_forecast_run.py`; backcast registry untouched (§5).
- **Rule 19 `[R-ONE-MECH]`** — nothing is stacked: the walk is the *same* one
  mechanism, re-used on a different consumed level; §1.2 enumerates what
  already governs entry volume and the signal object before anything changes.
- **Rule 21 `[R-DOF]`** — zero new free parameters (§1.3).
- **Rule 22 `[R-HOLDOUT]`** — the registered 2021–2025 window only;
  `--holdout-authorized` never passed; freeze untouched.
- **Rule 24 `[R-REGISTRY]`** — the joint posture is two already-registered
  `ScenarioConfig` fields, serialized into each arm's `run_config.json`; no
  env-var or off-registry channel.
- **Rule 25 `[R-ISO-SCOPE]`** — ERCOT only; no verdict transfers to another
  ISO's cell; only the ERCOT shard is edited.
- **Rule 26 `[R-MECH-MATRIX]`** — duty (a): the cells were checked before
  chartering (`entry_lookahead_reprice` ERCOT `K`/`fc O`;
  `entry_margin_exhaustion` `O`/`fc O`; neither is `R`/`I`/`G`, so nothing
  adjudicated is re-tested). Duty (b) is discharged in this session on both
  cells, rejection included if a gate fires. Duty (c) does not fire — no
  `ScenarioConfig` field is added.
- **Rule 27 `[R-PUSH]`** — every edit made locally and pushed as on-disk
  bytes; any push touching a ≥300-line file is followed by blob verification;
  no CI workflow is added (the solves run in this session).
