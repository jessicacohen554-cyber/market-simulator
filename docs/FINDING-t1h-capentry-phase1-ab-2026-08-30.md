# FINDING — T1-H capacity-entry Phase-1 Leg A: the storage-entry D-2 + D-3 joint repair A/B'd — both kill-gates PASS, the arm reproduces the pre-registered li-ion signature exactly, arming open

_2026-08-30 · T1-H capacity-entry repair lane, **Phase-1 Leg A** (storage) ·
charter `docs/PRECOMMIT-t1h-capacity-entry-2026-08-30.md` §Phase-1 (owner
ruling 2026-08-30, director sitting, decision card 2) · Phase-0 record
`docs/FINDING-t1h-capacity-entry-phase0-2026-08-30.md` (its pre-registrations
stand and are scored against below) · implementation merged at PR #4386
(`storage_entry_availability_gate` + `storage_entry_cost_normalized_rank`,
both `ScenarioConfig`-registered, GATED default-OFF) · driver
`scripts/probes/storage_entry_repair_compare.py`, artifact
`results/calibration/storage_entry_repair_ab_ercot.json`._

**Both arms solved by THIS session on one HEAD** (`bd97c6e`, the #4399 merge;
`origin/main` advanced to `edd8990` during the session with **zero solve-path
changes** — `git diff bd97c6e..edd8990 -- src/ scripts/run_*.py
scripts/score_*.py` is empty — so the arms are solve-path-current at the merge
base too). Registered on the FORECAST namespace only (rule 15):
`ercot-2021-2025-realized-t1h-capentry-{control,repair}`. The backcast
registry, every keeper shard, `calibration-complete.json`,
`holdout-freeze.json` and `program-status.json` are untouched. **Neither
default is flipped: ARMING IS AN OWNER DECISION on this record, not this
lane's** (charter Phase-1; dispatch hard line).

---

## 0. The one-paragraph answer

**Both kill-gates PASS, and the joint repair does exactly one thing:** it
changes *which* storage technologies the 2023 decision year builds — from
`iron_air` 3,000 + `flow_battery` 2,000 MW (cap-weighted **64.0 h**, li-ion
**0 %**) to **`li_ion_4hr` 3,000 + `li_ion_8hr` 2,000 MW (5.6 h, li-ion
100 %)** — which is **byte-exact the Phase-0 §3.3 pre-registered signature**,
the mix the cost-normalized metric picks on either candidate pool, and the
1.6-hour-class technology ERCOT actually built (measured 2023–2025 vintage
1.60 h cap-weighted, 13,659 MW li-ion operable vs 0.0 MW flow/metal-air).
**Every addition-metric band is IDENTICAL between arms** — model GW and
err_frac unchanged to the digit on all five techs — so K1 (some band moves
away by more than the others improve) had *nothing to fire on*: in the
shipped default posture the storage **volume** is set by the annual budget +
share cap (defect D-1, capx's, out of scope here), and all admitted li-ion
techs clear by 10–20×, so both slots fill in both arms. K2 (inert) does not
fire because the storage-mix rows differ. The two measured couplings, at full
magnitude: the ledger **reserve-margin path shifts down** (2023 8.54 → 6.98,
2024 14.65 → 13.10, 2025 25.19 → 23.61 % — the 5.6 h fleet accredits less
firm capacity than 64 h iron-air/flow) **without flipping any downstream
decision** (thermal/VRE entry identical every step, zero retirements both
arms, zero backstop fires), and **co2** (REPORTED-ONLY stream) moves
−0.49 Mt (2023), −0.52 Mt (2024), **+0.34 Mt (2025)**. Verdict: **the
candidate stands** — both ERCOT matrix cells go `U → O` (measured, ARMING
OPEN) with this A/B as the citation.

---

## 1. Posture — verified mechanically, not asserted

The driver hard-fails unless the arms differ in exactly the two chartered
fields; it did not fail. From the committed `run_config.json` of each arm:

| check | measured |
|---|---|
| `scenario_config` field diff, control vs arm | **exactly** `{storage_entry_availability_gate: False→True, storage_entry_cost_normalized_rank: False→True}` — no third field |
| control cache key | **`28cef3500ec1fd9e`** — the registered `…-t1h-refresh` key REPRODUCED (the two new fields are cache-key-optional at their registered default, so the bare invocation keeps the registered key) |
| arm cache key | `dcbd3b9567b2fe26` |
| solve/bridge span, both arms | solved [2021, 2023, 2024, 2025], bridged [2022] — identical to the registered bundle; no out-of-training year touched |
| `leakage_violations`, both arms | `[]` |
| invocation | the D11-R §7 byte-precedent: bare `run_capacity_hindcast.py --iso ERCOT --start-year 2021 --end-year 2025` (control); + `--storage-entry-availability-gate --storage-entry-cost-normalized-rank` (arm) |

Arms ran **sequentially** (control, then arm): the container memcg
(~13.3 GiB) is shared, so two concurrent ERCOT T1-H invocations would
swap-thrash rather than parallelize — the dispatch's default posture for this
container, taking precedence over rule 12's separate-invocation concurrency
here. Years sequential within each invocation (rule 12).

## 2. Control-vs-registered drift record (the v13 C-1 precedent: measured, never assumed)

| check | measured |
|---|---|
| cache key reproduced | **yes** — `28cef3500ec1fd9e` |
| additions rows vs registered `score.json` | **identical on all five techs** — model GW and err_frac to the digit (wind 0.350 / solar 17.987 / gas_cc 9.000 / gas_ct 7.571 / storage 5.000) |
| RM path vs registered ledger | 19.00 / 8.54 / 14.65 / 25.19 — verbatim |
| storage mix vs registered ledger | `iron_air` 3,000 + `flow_battery` 2,000 in 2023, nothing elsewhere — verbatim |

**Zero source-tree drift at HEAD.** Every committed bracket of the registered
T1-H posture remains a valid anchor for this A/B.

## 3. The A/B record

### 3.1 Addition bands at FULL MAGNITUDE in both directions (the K1 object)

From each bundle's `score.json` (decision basis 2023–2025 additions vs RD-5
actuals), Δ|err| > 0 = away from actuals, < 0 = toward:

| tech | actual GW | control GW | arm GW | control err_frac | arm err_frac | Δ\|err\| | band |
|---|--:|--:|--:|--:|--:|--:|---|
| wind | 12.663 | 0.350 | 0.350 | −0.9720 | −0.9720 | **0.0000** | FAIL → FAIL |
| solar | 25.080 | 17.987 | 17.987 | −0.2830 | −0.2830 | **0.0000** | FAIL → FAIL |
| gas_cc | 0.244 | 9.000 | 9.000 | +35.8850 | +35.8850 | **0.0000** | FAIL → FAIL |
| gas_ct | 3.692 | 7.571 | 7.571 | +1.0500 | +1.0500 | **0.0000** | FAIL → FAIL |
| storage | 13.691 | 5.000 | 5.000 | −0.6350 | −0.6350 | **0.0000** | FAIL → FAIL |

Stated in both directions with no netting: **no band improves, and no band
worsens** — sum of improvements 0.0, worsenings {}. K1 does not fire.

**Why the bands cannot move in this posture, stated as the mechanism.** The
storage volume is `min(budget, caps)`: `STORAGE_ANNUAL_BUILD_CAP_MW["ERCOT"]`
5,000 with the 0.6 share cap giving 3,000 + 2,000 slots — that is defect
**D-1 (bang-bang volume), which is capx's (D11-R) and explicitly out of scope
here** (charter dedup gate). Since every admitted li-ion tech clears its
margin by 10–20× (Phase-0 §3), both slots fill in both arms and the scored
GW is unchanged; thermal/VRE entry never sees the storage mix. The joint
repair is a **mix-only lever in the shipped default posture** — exactly what
the charter's pre-registration anticipated the object under test to be.

**The Phase-0 §2.2 item 5 pre-registration, scored.** It pre-registered that
"D-2 **alone** can only make the storage band worse (5,000 → 0 MW if no
admitted tech clears in 2023, or → a li-ion mix per §3)". Measured: the
second branch is what obtains **jointly** — admitted techs (li-ion from 2012,
flow_battery from 2017) clear in 2023, so the volume never drops and the
worse-band direction never materializes. K1 was read against that
pre-registration as the charter requires, and adjudicated on the measured
table above: zero movement, no fire.

### 3.2 The storage mix — the object under test, vs its pre-registered signature

| | slot 1 (3,000 MW) | slot 2 (2,000 MW) | cap-wtd duration | li-ion share |
|---|---|---|--:|--:|
| control (= registered ledger) | `iron_air` | `flow_battery` | 64.0 h | 0 % |
| **arm (joint D-2 + D-3)** | **`li_ion_4hr`** | **`li_ion_8hr`** | **5.6 h** | **100 %** |
| Phase-0 §3.3 pre-registered joint counterfactual | `li_ion_4hr` | `li_ion_8hr` | — | 100 % |
| measured ERCOT 2023–2025 vintage (Phase-0 §2.2) | — | — | 1.60 h (max 4.0) | 13,659.3 of 13,909.3 MW operable |

**EXACT MATCH to the pre-registered signature** — the live joint mechanism
reproduces the Phase-0 arithmetic replay's `li_ion_4hr` 3,000 + `li_ion_8hr`
2,000, the pool-invariant answer of the cost-normalized metric. The
mechanism decomposition, confirmed live against the Phase-0 replay:

- **The gate (D-2)** excludes `iron_air` in the 2023 decision year (first US
  operating year 2024 > 2023) and `compressed_air` (fail-closed `None` — the
  modeled non-cavern adiabatic class has zero national base ever), while
  admitting all li-ion (2012) and `flow_battery` (2017).
- **The rank (D-3)** demotes admitted `flow_battery` from 2nd-of-pool
  (absolute $/MW-yr) to last (margin per $/kW) and orders `li_ion_4hr` >
  `li_ion_8hr` > `li_ion_12hr` — so the slots go to the 4 h + 8 h classes.
- **Neither alone produces this mix** (Phase-0 §3.2–3.3: D-3 alone flips only
  slot 2 to `compressed_air`; D-2 alone on the absolute metric hands slot 1
  to `flow_battery`, then `li_ion_12hr` — duration still wrong). Only the
  pair is pool-invariant li-ion 4hr+8hr. Confirmed here by the single live
  A/B of the pair; the singles were not solved (the charter charters the
  joint repair as the object under test).
- **The gate is not a permanent iron-air ban:** from the 2024 decision year
  `iron_air` is admissible (2024 ≥ its first operating year) and builds
  **0 MW in both arms** — no storage tech clears any later decision year
  (the 2023 build collapses the arbitrage margins). Its exclusion is
  anachronism-scoped, exactly as designed.

### 3.3 Everything else that moved, at full magnitude (rule 1: no netting)

A recursive diff of the two `score.json`s finds **exactly one moving stream**
(plus timestamps); the per-step ledgers add the RM path. Both reported whole:

**Reserve-margin path (ledger; a sanity object, not a scored band):**

| year | control % | arm % | Δ pp |
|---|--:|--:|--:|
| 2021 | 19.00 | 19.00 | 0.00 |
| 2023 | 8.54 | **6.98** | **−1.56** |
| 2024 | 14.65 | **13.10** | **−1.55** |
| 2025 | 25.19 | **23.61** | **−1.58** |

The 5.6 h li-ion fleet accredits less firm capacity than the control's 64 h
iron-air/flow build — a real, duration-driven ELCC effect and the one live
coupling of the mix into the rest of the model. Measured consequence:
**no downstream decision flips** — thermal/VRE entry decisions are identical
in every step (2022 bridge included), retirements are zero in every step of
both arms, and the reserve-margin build backstop (default off) never fires.
Stated in both directions: the arm's RM path is lower everywhere it differs;
nothing moves toward or away from any scored actual because RM is not a
scored band in this harness.

**co2 (REPORTED-ONLY stream — demoted from the determination at rubric v2.9;
reported because it moved):**

| year | control t | arm t | Δ t |
|---|--:|--:|--:|
| 2023 | 167,539,465 | 167,049,288 | **−490,178** |
| 2024 | 155,434,859 | 154,913,728 | **−521,130** |
| 2025 | 188,208,785 | 188,546,149 | **+337,364** |

Two years move down, one moves **up** — dispatch-level effects of a 5.6 h
fleet cycling differently than a 64 h fleet. No netting: the 2025 worsening
is +0.34 Mt whatever the 2023/2024 improvements are.

**Everything else in `score.json` is byte-identical** — retirement rows and
bands, recall, additions (above), every other stream.

### 3.4 The kill-gates, applied mechanically by the driver

| gate | charter definition | measured | fires? |
|---|---|---|---|
| **K1 REJECTED** | some addition-metric band moves AWAY from actuals by more (in \|err_frac\|) than the sum of the improvements on the others | every Δ\|err\| = 0.0000; worsenings {} | **NO** |
| **K2 INERT** | indistinguishable from control on every addition metric AND every storage-mix row | addition metrics indistinguishable, but the storage mix differs in every row (tech set, duration, li-ion share) | **NO** |

### 3.5 Invariant blocks (declared post-registration; the FR-24 ledger duty)

Both sidecars carry **I3 FAIL** — the standing **FR-6** ERCOT energy-only
scarcity-slack cause (`invariant-failures.json` `dominant_open_causes`), the
same ident the registered `…-t1h-refresh` sidecar carries. Detail strings at
full magnitude: control **2023 slack 0.01 % of load**, repair **2023 slack
0.04 % of load** (refresh: 0.02 %). The repair's larger 2023 slack is the
same physics as its RM-path shift (§3.3): the 5.6 h li-ion fleet covers
fewer 2023 scarcity hours than the control's 64 h build — reported here as
the third full-magnitude coupling. Sub-band diagnostic magnitudes; no scored
metric moves (§3.1). Both runs are declared in
`frontend/data/hindcast/invariant-failures.json` (`capentry_note`) per that
ledger's `how_to_update` contract — one commit after the registration,
because the registration PR was merged before this ledger duty was executed.
Declaration is not absolution: FR-6 stays the open root cause. Observed and
recorded, not acted on (out of this lane's scope): ten other committed
sidecars carry undeclared FAILs of the same family pattern (`t1h-refresh`,
the capx `t1h-d11r-*`/`t1h-d12c-*` pairs on I3; caiso/neiso/pjm rows on
I6/I7/I9), which keep the `forecast-invariant-artifacts` CI job red on main
until their owning lanes declare them.

## 4. Verdict, and what is recorded for the owner

**Both kill-gates pass → the candidate verdict is recorded with ARMING OPEN**
(dispatch item 7). Both ERCOT matrix cells move `U → O` in this session
(rule 26 duty (b)) with this finding + the A/B artifact as the citation.
Nothing is armed: `storage_entry_availability_gate` and
`storage_entry_cost_normalized_rank` remain GATED default-OFF, the T1-H
default lane is untouched, and the arming decision is the owner's on this
record.

Findings the arming decision would weigh — recorded, not recommended:

1. **In the shipped posture the repair is mix-fidelity at zero band cost.**
   The measured mix moves from 100 % never-deployed-in-ERCOT technology
   classes at 40× the measured duration to the measured fleet's own 4 h/8 h
   li-ion classes, while every scored addition band is unchanged to the
   digit. The rule-1 rationale is the deployment record (Phase-0 §2.2), not
   the residual — and the residual indeed did not move.
2. **The armed-D11-R interaction is not covered by this A/B.** Under
   `entry_margin_exhaustion` the second storage slot exhausts (that arm
   builds `iron_air` 3,000 only), so the joint repair's measurable effect
   there is smaller and different in kind. This A/B ran at the shipped
   (unarmed) default **by design** (Phase-0 §5 item 4 sequencing note). If
   the owner arms both mechanisms together, the combined posture has not
   been solved; the walk consumes the same `_storage_entry_candidates` /
   `_storage_entry_rank_score` seams (rule 19), so the mechanism composes,
   but its numbers are unmeasured.
3. **The RM-path coupling (−1.6 pp) is the one live side effect.** Inert
   downstream in this window (no decision flips; backstop off), but any
   RM-adjacent consumer armed in a future posture would see it.
4. **Sequencing note inherited from Phase-0 §5 item 4:** the parent
   finding's L-6 (storage cost/life specification) makes long-duration
   storage *cheaper* and must not land before D-2.

No repair ideas beyond the chartered pair surfaced — no proposals are added.

## 5. Rule compliance

- **Rule 1 `[R-STRUCT]`** — the mechanism is argued from the deployment
  record; every band is reported at full magnitude in both directions
  (§3.1, §3.3); the zero-band-movement result is reported as the measured
  fact, never as the mechanism's justification.
- **Rule 12 `[R-PARALLEL]`** — years sequential within each invocation; the
  two invocations sequential for container-memcg reasons (§1).
- **Rule 13 `[R-MEASURED]`** — no measured outcome enters any model path.
  `STORAGE_TECH_AVAILABLE_YEAR` is a reproducible physical/market input
  (a technology class's first US operating year), the storage analogue of
  the thermal path's cited availability years; it regenerates for forward
  years and responds to changed conditions (a class crossing into
  availability enters the pool, as iron-air does in 2024).
- **Rule 15 `[R-DASHBOARD]`** — both arms registered via
  `register_forecast_run.py` on the forecast namespace only; the backcast
  registry and its CI gates never touched.
- **Rule 19 `[R-ONE-MECH]`** — one gate helper + one rank helper, each
  consumed by BOTH storage allocation rules; nothing stacked on the
  bang-bang paths.
- **Rule 21 `[R-DOF]`** — zero new free parameters: the gate years are
  measured constants with citations (`capacity_market.py`), the rank is a
  ratio of two quantities the screen already holds.
- **Rule 22 `[R-HOLDOUT]`** — solves span the registered window only (2021
  enumerated seed + 2023–2025 training, 2022 bridged); `--holdout-authorized`
  never passed; the freeze untouched; both governance banners clean and
  `leakage_violations` empty in both metas.
- **Rule 24 `[R-REGISTRY]`** — both mechanisms are `ScenarioConfig` fields
  serialized into each arm's committed `run_config.json`; the CLI flags are
  tri-state (omit = shipped default).
- **Rule 25 `[R-ISO-SCOPE]`** — every number is ERCOT's; no verdict
  transfers; the CAISO/other shard cells stay `U`.
- **Rule 26 `[R-MECH-MATRIX]`** — duty (a) discharged at dispatch (cells
  verified `U`, no adjudicated cell re-tested); duty (b) discharged in this
  session: both ERCOT cells adjudicated `U → O` with citations; duty (c) was
  the implementation PR's (#4386, rows + all-shard cell lines landed there).
- **Rule 27 `[R-PUSH]`** — no existing ≥300-line file rewritten; all new
  files pushed as on-disk bytes over `git push` (small packs, fresh fetch of
  main first) with post-push blob verification of every ≥300-line file.

## 6. Reproduction

```
# environment: pip install -r requirements.txt && pip install -e . --no-deps
#              python3 scripts/regenerate_clean.py   (50/51 expected)
# arms (sequential; control = bare registered posture)
python3 scripts/run_capacity_hindcast.py --iso ERCOT --start-year 2021 --end-year 2025 \
    --out-dir results/hindcast/ercot-2021-2025-realized-t1h-capentry-control
python3 scripts/run_capacity_hindcast.py --iso ERCOT --start-year 2021 --end-year 2025 \
    --storage-entry-availability-gate --storage-entry-cost-normalized-rank \
    --out-dir results/hindcast/ercot-2021-2025-realized-t1h-capentry-repair

# score each, then the A/B driver (posture-gated: exactly the two fields may differ)
python3 scripts/score_capacity_hindcast.py --bundle results/hindcast/ercot-2021-2025-realized-t1h-capentry-control
python3 scripts/score_capacity_hindcast.py --bundle results/hindcast/ercot-2021-2025-realized-t1h-capentry-repair
python3 scripts/probes/storage_entry_repair_compare.py \
    --arm results/hindcast/ercot-2021-2025-realized-t1h-capentry-repair \
    --control results/hindcast/ercot-2021-2025-realized-t1h-capentry-control \
    --out results/calibration/storage_entry_repair_ab_ercot.json

# registration (forecast namespace only)
python3 scripts/register_forecast_run.py --bundle results/hindcast/ercot-2021-2025-realized-t1h-capentry-control
python3 scripts/register_forecast_run.py --bundle results/hindcast/ercot-2021-2025-realized-t1h-capentry-repair

# mechanism unit tests
python3 -m pytest tests/unit/model/test_storage_entry_gates.py -q   # 21 passed
```

The evolution ledgers the driver reads are gitignored bundle internals — the
probe must run in the session that solved the bundles (it did); the committed
artifact `results/calibration/storage_entry_repair_ab_ercot.json` carries
both arms' per-step rows, the posture record, the drift record, the band
table and the gate verdicts in full.
