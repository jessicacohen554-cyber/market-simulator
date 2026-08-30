# FINDING — D12-A: the arming execution (Q15) — both entry-pair fields are ERCOT forecast defaults

_2026-08-30 · capacity-expansion (Forecast Finalization) track, lane D12-A
ARMING EXECUTION · ZERO SOLVES · chartered by owner ruling **Q15** (r#18
sitting, 2026-08-30, `docs/handoffs/capx-director-ledger-2026-08.md` §3 /
§0o.7). Branch `claude/capx-d12a-arming-0ibtzh`, fresh off `origin/main` @
`d1407e4`. Predecessors: `FINDING-capx-d12c-confirm-pair-2026-08-30.md` (the
measured pair whose §1.4 execution list this lane runs, under Q15 instead of
a confirming record) and `FINDING-capx-d12-scarcity-basis-2026-08-30.md` §5–§6
(the mechanism)._

---

## 0. The one-paragraph answer

`entry_margin_exhaustion` and `entry_forward_reserve_leg` are now the **ERCOT
forecast defaults**, armed as ONE unit through ERCOT's
`ISOConfig.default_scenario_overrides` (the FFR-9C stage-B seam), executing
owner ruling Q15 on the D12-C record the owner judged confirming-in-substance
per that finding's own §4.3 clause. Verified zero-solve: the bare ERCOT T1-H
construction now resolves **bit-equal to the registered armed bundle's
committed key `f061b2646bfaac8b`** (`ercot-2021-2025-realized-t1h-d12c-armed`
IS the record of the new default posture — no re-solve, no re-registration),
and the pair-off reconstruction still lands on the control's
`28cef3500ec1fd9e`. The global pin, both `ScenarioConfig` field defaults,
every backcast key and every sister-ISO resolution are unmoved. The V-2 miss
is carried at full magnitude in every citation (§3). ERCOT matrix shard cells
moved `fc` O → K on the registered pair's evidence + Q15; sister-ISO cells
stay U.

## 1. The rulings executed (verbatim)

- **Q10** (r#15 sitting, 2026-08-30): *"CONFIRM-PAIR, THEN ARM. Lane D12-C
  chartered: ONE arm-vs-control A/B on the ERCOT T1-H leg at the registered
  posture with the TWO fields (`entry_margin_exhaustion` +
  `entry_forward_reserve_leg`) as the single logical delta, measuring the
  closed loop D12 open-loop-predicted. Arming auto-executes on a confirming
  record (both flip to ERCOT forecast defaults, honestly described); a
  contradiction does NOT arm and comes back to the owner at full magnitude."*
- The D12-C record was **CONTRADICTING on exactly one of five pre-declared
  verdict criteria** (V-2), so its protocol armed nothing and escalated.
- **Q15** (r#18 sitting, 2026-08-30): *"ARM BOTH FIELDS
  (`entry_margin_exhaustion` + `entry_forward_reserve_leg` → ERCOT forecast
  defaults), the owner judging the record confirming-in-substance per the
  finding's own §4.3 clause. The V-2 miss is described honestly in the arming
  citation; matrix cells O → K-forecast-armed on the registered pair's
  evidence; sister-ISO cells stay U (rule 26). Execution = lane D12-A
  (zero-solve; prompt in the pack)."*

This lane executed exactly the D12-C §1.4 confirmation list, under Q15
instead of a confirming record. Zero parameters, zero solves: two booleans
flipped, two rulings cited.

## 2. The edit

| piece | where |
|---|---|
| the flip | `src/market_sim/config/iso_configs.py` — ERCOT `default_scenario_overrides` gains `entry_margin_exhaustion: True` + `entry_forward_reserve_leg: True` (one unit), with a D12-A citation block quoting Q10 and Q15 verbatim, the honest posture incl. the V-2 miss, the measured epoch keys, the control-arm expressibility and the dependency wall |
| field comments | `scenarios.py` — both field comments note the ERCOT ISO-default arming (field defaults stay `False`; rule 25 noted) |
| epoch probe | **NEW** `scripts/probes/_d12a_arming_cache_epoch.py` (modeled on `_ffr9c_stageb_cache_epoch.py`) — the declaration's measured half: global pin, both epoch poles, the bare-T1-H ↔ registered-bundle key identities, sister-ISO immobility. ALL READS PASS |
| FFR-9C probe repair | `_ffr9c_stageb_cache_epoch.py` now strips post-D-30 armings (`POST_D30_ARMINGS`) before evaluating the D-30 poles, so the D-30 declaration stays live-verifiable — it would otherwise falsely report its epoch broken on every later arming. Re-run: ALL EPOCH READS PASS |
| pins | `tests/unit/config/test_ercot_stageb_arming.py` — new `TestD12AArming` (pair-as-one-unit, sister ISOs clean, seam-not-field-defaults + `_CACHE_KEY_OPTIONAL_FIELDS` membership, both epoch poles as literals, control-arm expressibility, the dependency wall) + the backcast-lane tests extended to the pair (including a new coercion-through-the-seam pin); the D-30 epoch test now reconstructs its poles with the pair stripped (same `dataclasses.replace` discipline, one layer later) |
| pins | `tests/unit/config/test_iso_override_precedence.py` — `ERCOT_ARMED_KEY` moves to the live pole `68a207068509f2b0` with the genealogy comment |
| matrix | ERCOT shard `docs/codebase-site/data/mechanism-matrix/ERCOT.js`: both cells `fc` **O → K** with the Q15/D12-A record appended to `ev`, `updated` → 2026-08-30, tail re-stamp block appended. Base `mechanism-matrix.js`: the two rows' stale "NOT ARMED ANYWHERE" note tails replaced with the Q15 arming record (+ `--fix-anchors` for the +8-line scenarios.py comment shift). **No new row** — both fields exist (rule 28(c) not triggered). Sister shards untouched |
| test repair | `tests/unit/pipeline/test_runner.py::TestPriceSignalByteIdentity` — pins the pair off alongside `entry_lookahead_reprice=False` (the dependency wall now refuses a reprice-only disarm for ERCOT; same treatment the FF-2A flip gave this test). The assertion is unchanged — nothing weakened |

**NOT touched, by design:** no solve; no registration (both D12-C bundles are
already registered — the armed one is the record of the new posture); no
board edit (the director stamps `program-status.json` on its refresh); no
backcast surface (below); no sister-ISO shard; no new `ScenarioConfig` field;
the retirement screens' internally-consistent backward pair (the D12 finding's
own scope line); the director ledger (the director's).

## 3. The honest posture (the Q10 "honestly described" clause)

Armed, **ERCOT forecast entry is exhaustion-bounded on the entering year's own
expected-ORDC surface for every candidate class**: both entry allocators build
in repriced 250 MW tranches until the screen's one-object forward margin —
energy leg plus the SAME `_lookahead_reprice_signal` invocation's
expected-ORDC reserve adder, never the prior year's realized post-solve
adder — is exhausted, bounded by the same caps as bang-bang.

**The V-2 miss, at full magnitude:** the D12-C pair's entering-2022 gas_cc
build was **0 MW, outside the pre-declared [750, 1,250] MW window** (the
offline B-walk's 1,000 ± 1 tranche). It is not a construction defect — the
armed run's start margin was bit-identical to the committed +$45,930.9/MW-yr —
but a **pre-declaration derivation error**: the window was derived from the
offline walk's RESTRICTED candidate set (VRE held at shipped), while the live
walk fields every candidate class, so solar won the early tranches and
exhausted cc's margin before any tranche cleared. Direction conservative
(MORE exhaustion by the same mechanism on the same one-object margin); every
other criterion and every structural claim confirmed (V-1/V-3/V-4/V-5 and
both gates exactly; terminal RM 15.84 % inside the ex-ante [15.0, 21.0]
band); **the tolerance was never widened after the record** (rule 21) — the
pair adjudicated CONTRADICTING as written, and the owner, not a revised
tolerance, made this arming.

## 4. Zero-solve verification (measured this session, probe-reproducible)

`scripts/probes/_d12a_arming_cache_epoch.py` — ALL READS PASS:

| read | value | meaning |
|---|---|---|
| bare T1-H construction, resolved | **`f061b2646bfaac8b`** | = the registered armed bundle's committed `run_config.json` key, bit-equal — a bare `run_capacity_hindcast.py --iso ERCOT --start-year 2021 --end-year 2025` now solves exactly the D12-C armed posture, so that bundle IS the record of the default (no re-solve, no re-registration) |
| bare T1-H, pair replaced to field defaults | `28cef3500ec1fd9e` | = the registered control bundle — the explicit `--no-entry-margin-exhaustion --no-entry-forward-reserve-leg` control arm stays expressible (OVERRIDE-FIX precedence) and lands on the committed control key |
| ERCOT forecast resolved default | `8d9ef77edb3e44cb` → **`68a207068509f2b0`** | the declared D12-A cache epoch, ERCOT forecast lane only — every pre-D12-A ERCOT forecast/hindcast sidecar is historical record, never a post-epoch baseline; nothing is silently re-used (both armed values enter the digest) |
| global pin | `603c2498bf71d21d` | UNMOVED (field defaults stay `False`; both fields are `_CACHE_KEY_OPTIONAL_FIELDS` members) |
| ERCOT backcast (2024 builder key `e29ebfc9813c3eb1`) | UNMOVED | backcast untouched **by construction twice over**: the calibration lane never applies ISO overrides, and `__post_init__` backcast-coerces both fields off even through the seam (new pin `test_a_backcast_resolution_coerces_the_pair_off`); `tests/regression/test_persisted_identity.py` 13/13 |
| sister ISOs (CAISO/MISO/NYISO/NEISO/PJM) | pair (False, False), keys unmoved | rule 25 |

Baseline sanity, measured BEFORE the flip: the same constructions reproduced
`28cef3500ec1fd9e` (bare) and `f061b2646bfaac8b` (+2 flags via `replace`) at
HEAD — the reconstruction instrument is exact on both poles.

## 5. Fast checks (all run in-session)

- `tests/unit/config` — **618 passed**, 13 skipped (the pre-existing
  bool-field skip pattern in the precedence module; my two rows join
  `PROMOTED` parametrically and pass), 18 subtests.
- `tests/unit/pipeline` — **205 passed** after the one documented repair
  (§2 test-repair row; the failure was the dependency wall refusing the
  reprice-only disarm, i.e. the arming working as pinned).
- entry/capacity model lane (11 modules incl. both field suites) —
  **435 passed**; `test_scarcity.py` 34 passed.
- `tests/regression/test_persisted_identity.py` — 13 passed (global pin +
  backcast keys byte-stable).
- `scripts/check_mechanism_matrix.py` — clean (anchor digits repaired via its
  own `--fix-anchors` after the scenarios.py comment shift).
- Both epoch probes — ALL READS PASS. `ruff check` + `ruff format --check`
  clean on every touched file.
- `tests/scoring` + provenance/warmstart — **1148 passed**, 3 skipped,
  1 xfailed, 98 subtests; **6 failures PRE-EXISTING on unmodified `main`**
  (verified by `git stash` re-run at `d1407e4`: identical 6). They are not
  this lane's: 5× `test_ff_readiness_battery` (marker/board state) and
  `test_forecast_parity.py::test_all_six_keepers_resolve` — the ERCOT keeper
  arms `ercot_adaptive_event_release` + `ercot_storage_adaptive_expectation`
  with no forecast-orchestrator consumer or
  `scripts/lib/forecast_parity_registry.py` declaration (an ercot-221/223-era
  gap). **Flagged to the director** — it predates this arming and is a
  backcast-keeper/forecast-parity seam question, not an entry-pair one.

## 6. CROSS-TRACK FLAG (carry to the audit track's T1-H capacity-entry lane)

This arming moves the ERCOT forecast defaults **under the audit track's T1-H
capacity-entry lane**. Their registered-posture control bundles are
unaffected — committed `run_config.json`s pin their solved values — but **any
FUTURE bare ERCOT T1-H/forecast invocation lands on the armed defaults**
(and, per the dependency wall, an ERCOT leg that disarms
`entry_lookahead_reprice` or `screen_reserve_value_enabled` must now disarm
this pair WITH it or construction raises). The pre-D12-A "bare" posture is
reachable as the explicit `--no-entry-margin-exhaustion
--no-entry-forward-reserve-leg` control arm, which reproduces the committed
control key exactly (§4). Their next session should treat
`28cef3500ec1fd9e`-keyed bare invocations as pre-epoch history. No audit
surface was touched by this lane.

## 7. Rule compliance

- **Rule 1 `[R-STRUCT]` / 13 `[R-MEASURED]`** — the arming ships the
  structurally-adjudicated mechanism (D12 §6) on the owner's judgment of the
  measured closed-loop record; the pair moves as one unit because the
  measured evidence covers exactly the two-field delta; no measured outcome
  enters any model path (both fields backcast-coerced; T1-H is forecast
  machinery).
- **Rule 21 `[R-DOF]`** — zero parameters: two booleans, two rulings cited;
  the D12-C tolerance was not revised (the CONTRADICTING adjudication
  stands in the record and in every citation).
- **Rule 22 `[R-HOLDOUT]`** — zero solves; no out-of-training year touched in
  any tier; the tier-scoped freeze untouched.
- **Rule 24 `[R-REGISTRY]`** — the arming lives on the registered
  `ISOConfig.default_scenario_overrides` seam and in `run_config.json` at
  solve time; the control arm is expressible through the same registered
  path.
- **Rule 25/26 `[R-ISO-SCOPE]`** — ERCOT only; sister ISOs resolve unmoved
  (probe read 4) and their matrix cells stay U.
- **Rule 27 `[R-PUSH]`** — Opus/Fable session; all edits local (Edit tool);
  push carries on-disk bytes with post-push blob verification on every
  ≥300-line file.
- **Rule 28(b) `[R-MECH-MATRIX]`** — both tested cells re-stamped in the
  ERCOT shard by this session with the pair + Q15 as evidence; (c) not
  triggered (no new field).

## 8. Reproduction (zero-solve)

```
# the epoch declaration (global pin, both poles, T1-H key identities, sister ISOs)
uv run python scripts/probes/_d12a_arming_cache_epoch.py

# the D-30 declaration, still live post-D12-A
uv run python scripts/probes/_ffr9c_stageb_cache_epoch.py

# the pins
uv run pytest tests/unit/config/test_ercot_stageb_arming.py \
    tests/unit/config/test_iso_override_precedence.py -q
```
