# PRECOMMIT — nyiso-227: measure the ONE criterion nyiso-226 could not, and decide the NYC persistent-base re-basing

**Session:** nyiso-227 (parent / orchestrator) · **ISO:** NYISO · **Date:** 2026-09-11
**Keeper / control:** `2026-09-09-nyiso-221-fuelvintage-span`
(`results/calibration/nyiso_fuelvintage_A`, `git_sha da2e7076`), **UNCHANGED at this writing.**
**Chain:** `ADDENDUM-nyiso226-not-promoted-and-main-reverted-2026-09-10.md` §4 → this document.

---

## 0. What this session is, in one paragraph

nyiso-226 measured the NYC `ST_GAS` persistent-base re-basing
(`reliability_floor_coeffs_NYISO.csv` line 6, `floor_pct` **0.175 → 0.16629202320362052`) on
C1, C2, C3a and C8 across 2023–2025 and it passed everywhere. **C3b — the tightest-margin
load-bearing criterion, 2024 at 0.179 against a 0.20 ceiling — was never measured**, after five
independently blocked retrieval routes, and the span bundle died with its container. The arm is
therefore **UNDECIDED, not rejected**. This session measures C3b and decides it.

**Nothing about the arm is re-opened.** Its value, its derivation, its confinement and its
screen gates are nyiso-226's and are carried verbatim. This session adds one measurement.

## 1. The gap nyiso-226 hit is CLOSED AT ZERO LP, before any solve is launched

The blocker was never the criterion — it was that `calibration_verdict.py` reads the dashboard
payload, which only *registration* writes, and rule 32 `[R-SHARD]` (c)(6) forbids a shard to
register. **`scripts/score_bundle_price_shape.py` (added by this session, additive, no existing
file touched) removes the dependency.** It does not re-implement C3b. It rebuilds the single
payload block C3b reads — `lmp[zone] = {"pMon", "dMon"}` — from the bundle's own
`hourly/system_<year>.parquet` using `render_calibration_html.py`'s arithmetic (its rounding
included, because the rounding is part of the scored quantity), then calls
`calibration_verdict.score_price_shape` **itself**. Band, load-weighted-actual ladder,
partial-month coverage mask and NRMSE are the scorer's, unmodified, and the benchmark is the
committed `bench/NYISO/<year>.json.gz` — the same part the registered control was scored against.

**Validated against the designated keeper, and it is EXACT, not approximate:**

| year | registered verdict | `score_bundle_price_shape.py` |
|---|---|---|
| 2023 | 0.122 | **0.122** |
| 2024 | 0.179 | **0.179** |
| 2025 | 0.160 | **0.160** |

This supersedes nyiso-226's hand reconstruction, which was good to ±0.002 — itself 10 % of
2024's 0.021 headroom, and the reason that lane would not have been able to conclude from it.

**Consequence for the shard design:** the shard can print a decision-grade C3b in its final
message with no registration, no artifact hand-back and no permission-classifier dependency.
That is the primary deliverable, and it is independent of whether the bundle survives.

## 2. The arm (carried verbatim from nyiso-226; NOT re-derived)

One cell of `data/raw/reference/reliability_floor_coeffs_NYISO.csv`, line 6
(`NYISO,NYC,ST_GAS,tmax,-50.0`): `floor_pct` **0.175 → 0.16629202320362052**.
Rule 14 `[R-ACCURATE]` construction repair — a fleet-aggregate DAILY-MEAN cool-day when-available
CF p25 was being applied per unit-HOUR; the arm is the basis-matched per-unit-hour statistic.
Zero new `ScenarioConfig` fields, zero cache-key delta, zero free parameters swept.
Pre-edit file: 47 lines, `sha256 81502c83…5df07`. **The edit is made in BINARY mode** — the file
is CRLF and a text-mode write silently rewrites all 47 line endings (nyiso-226 SHARDREPORT §1).
`git diff --stat` must read exactly `1 insertion(+), 1 deletion(-)`.

## 3. Rule 29(b) G-CTRL form 4 + G-DRIFT — NO CONTROL SOLVE IS SPENT

`git diff da2e7076 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/replay_keeper.py scripts/lib data/raw/_validation-source data/raw/reference`.
nyiso-226 §5 audited `da2e7076 → ec3374d2` and classified every hunk INERT. This session audits
the remainder, `ec3374d2 → HEAD (d2082b26)` — **four files**:

| file | change | verdict |
|---|---|---|
| `src/market_sim/config/scenarios.py` | +3 fields, **0 deletions**: `mustrun_window_commitment_grain`, `unit_outage_short_windows_gas`, `mustrun_chp_btm_holdout`, all `bool = False` | **INERT** — default-off and absent from the keeper recipe |
| `src/market_sim/data/fleet/arrays.py` | spp-27 day-grain must-run window + pjm-d4-4 gas short-outage scope, both behind the above gates | **INERT** — `_day_grain`/`gas_scope` resolve False |
| `src/market_sim/data/outages.py` | new `unit_outage_short_gas_csv_for_iso` + `_SHORT_GAS_GROUPS`, read only under `unit_outage_short_windows_gas` | **INERT** — gate off; no NYISO artifact exists |
| `scripts/run_calibration_full.py` | threads `mustrun_chp_btm_holdout` through `_eia923_frame` / `_must_run_profiles` / `_benchmark_eia923_frame` / `run_replay_bundle`, plus the archived P2 path | **INERT** — every new branch is `if mustrun_chp_btm_holdout:`; the module's own docstring states byte-identical off |

**BENCH DRIFT SEPARATELY CHECKED, because it would invalidate the control even though it cannot
change the solve:** `data/raw/_validation-source/{actual_lmp,calibration_reference}.json` both
changed since `da2e7076`, but the diff contains **zero NYISO tokens**, and re-running
`calibration_verdict.py --run-id 2026-09-09-nyiso-221-fuelvintage-span` at HEAD reproduces
`CALIBRATED` with C3b 0.122 / 0.179 / 0.160. **The registered control is HEAD-current.**

**ALL HUNKS INERT ⇒ form 4 valid, the keeper's committed bundle IS the control, no control
solve.**

## 4. The pre-registered decision rule and prediction — fixed BEFORE the solve

**DECISION RULE (owner's, carried into this document): PROMOTE iff no year's arm C3b exceeds
0.20.** `_band_result` is `PASS iff NRMSE ≤ 0.20` with target == commercial, so there is no
caveat band: ≤ 0.20 PASS, > 0.20 FAIL. The comparison is on the UNROUNDED NRMSE, so the shard
reports the unrounded value too. Any other criterion flipping PASS → FAIL is also a stop.

**PREDICTION, registered here so it can be wrong.** C3a moved **+0.026 / +0.028 / +0.025 $/MWh**
on annual means of 33.65 / 40.15 / 61.60. C3b is a monthly NRMSE normalised by the actual's mean
(~33 / ~38 / ~60), so a shift of that size can move NRMSE by at most ≈ 0.0008 if it were uniform
across months; a non-uniform distribution widens that, but reaching 2024's 0.021 of headroom
would need some months to move ~30× the annual mean with offsetting signs elsewhere. **Predicted
|ΔC3b| ≤ 0.005 in every year — i.e. 2024 lands ≤ 0.184.** If the measured move is materially
larger than that, the prediction is wrong and that is itself the finding, reported at full
magnitude whichever way the verdict goes.

**This is a measurement, not a fitting step (rule 1 `[R-STRUCT]`).** The coefficient is fixed;
nothing is swept; the arm's two-sidedness (2023 C1 ST_GAS better, 2024 worse) already establishes
it cannot have been chosen against a residual. `authorized_price_tuning` = **NONE**.

## 5. Execution (rule 32 `[R-SHARD]`)

- **The parent runs no LP.** Phase 0, this PRECOMMIT, the SHA pin, then scoring, registration
  (rule 32(d)), the matrix shard and the promotion question.
- **ONE shard, three years, one bundle** (rule 16 `[R-ALLYEARS]`):
  `replay_keeper.py results/calibration/nyiso_fuelvintage_A --years 2023 2024 2025
  --out-dir results/calibration/nyiso227_rebasis_span`, coefficient edited before the solve.
  nyiso-226's identical span ran **18 m 20 s, exit 0** — inside the 20-minute unit with 1 m 40 s
  of margin. The shard is given an explicit overrun rule: at 19 minutes it commits what exists
  and reports rather than running long.
- **THE BUNDLE IS NOT GITIGNORED.** This is the single change from nyiso-226, and it is the one
  that mattered: that lane added `results/calibration/nyiso226_*/` to `.gitignore` under rule
  29(c), which forced `git add -f`, which the shard's permission classifier refused, which
  stranded the bundle. Rule 29(c) governs **screen** bundles; this is a full-span candidate,
  which rule 15 `[R-DASHBOARD]` requires to be registered and committed. `git check-ignore`
  confirms `results/calibration/nyiso227_rebasis_span/{meta.json,hourly/system_2023.parquet}`
  are **not** ignored, so a plain `git add` of the slim bundle works — the path caiso-270/-271
  and spp-27 shards take routinely.
- **The shard does NOT register** (rule 32(c)(6)). Registration, scoring and the determination
  are the parent's, once, at the end (rule 32(d)). The shard's deliverables are **numbers in its
  final message** plus its own committed slim bundle — never an artifact hand-back.
- **Rule 31 `[R-RETAIN]`:** the ~18-minute cost is stated here, before the LP is spent, and the
  owner is asked before it is spent. Nothing is deleted by this session.

## 6. Governance

- **Rule 1 `[R-STRUCT]`** — the arm is fixed ex ante; this session measures, it does not tune.
- **Rule 13/14 `[R-MEASURED]`/`[R-ACCURATE]`** — measured basis, forward-regenerable, no outcome pinned.
- **Rule 15 `[R-DASHBOARD]`** — the span is registered by the parent whatever the verdict.
- **Rule 16 `[R-ALLYEARS]`** — one invocation, one bundle, 2023–2025.
- **Rule 21 `[R-DOF]`** — the coefficient remains a ledgered free parameter; count unchanged.
- **Rule 23 `[R-FROZEN-DERIVE]`** — no source-data trigger, and none is claimed. This is the
  open admissibility question nyiso-203 refused to answer alone and nyiso-226 put to the owner;
  it is named here as an open governance item, not silently resolved.
- **Rule 29 `[R-SCREEN]`** — the screen is spent (nyiso-226, 2023, survived); this is clause (2),
  the full span.
- **Rule 30 `[R-MECH-MATRIX]`** — the NYISO shard is updated in this session, whichever way it goes.
- **Rule 32 `[R-SHARD]`** — parent solves nothing; one shard, one commit, ≤ 20 min.
