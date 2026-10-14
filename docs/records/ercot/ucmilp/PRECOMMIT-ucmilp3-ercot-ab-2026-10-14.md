# PRECOMMIT — UC-3-ERCOT: the UC A/B relaunched at the clean engine (uc-1.4), all seven ERCOT years, 2026-10-14

**Written and pushed before any shard of this lane exists.** Readings, bars, kills and budgets below are fixed here and do
not move after a number arrives (GATESPEC §7.1; rule 1(c) by analogy). Lane `UC-3-ERCOT` (Opus), chartered by UC-DESK
(`session_01WX9W5tgYMre3Z134LZoGF6`) on the owner's ruling of 2026-10-14, *"Go with your recommendations"* (desk decision 7:
relaunch every UC-2 ISO at uc-1.4). Branch `claude/ucmilp-3-ercot-ab`, cut fresh from `main` `580c4fbf`.
This file **inherits** `PRECOMMIT-ucmilp-ercot-ab-2026-10-10.md` (UC-2-ERCOT, Addenda A–D.3). Anything not restated here is
unchanged from that file. **Why this lane exists:** every UC-2 verdict was solved before uc-1.3, so each is confounded by
engine defect 6. Under that defect the cluster floor was split pro rata across offer tranches, which forced `_peak*` tranches
on: 5.81 TWh in ERCOT 2019. The UC-2 R is therefore not a structural rejection (rule 1, desk r08). This lane produces the
clean A/B.

## 0. A number that already exists, disclosed before launch

The uc-1.4 ERCOT 2019 repro (`FINDING-ucmilp-fix4-floor-merit-2026-10-10.md` §7) solved **this lane's arm on this lane's
engine** (§1). Its readings are therefore already public. Against the keeper they show:

| 2019 | control (keeper) | uc-1.4 repro | read under the inherited §3 rule |
|---|---|---|---|
| C3a mean LMP | +6.2 % PASS | **+18.8 % FAIL** | **PASS → FAIL: kill #3 fires on 2019** |
| C3b monthly NRMSE | 0.216 FAIL | 0.282 FAIL | wrong-sign on target T3 → R by §7.1 |
| C1 CC_REGULAR / COAL_PRB | +9.21 / −10.79 FAIL | +0.35 / −4.37 PASS | T4 met, both rows |

**Consequence, stated now.** Under the inherited verdict rule (§7.1: any kill ⇒ R), this lane's gate verdict is **R** whatever
the other six years show. The owner and desk ordered all seven years with that number in hand: *"All 7 keeper years this time
(no staging)"*. So the six new legs are not a test of whether the verdict can be K. They are the clean per-year evidence for
the question rule 1 leaves open. Is the UC's price move structural (fix the root cause) or a defect? And which hours and which
classes carry it? The RESULT reports the R first and the structural diagnosis beside it. Neither is allowed to soften the
other.

## 1. Pin, control, arm

- **Pin = `580c4fbf80b8bf970bc19acf14f614728de9d401`** (`main`: uc-1.3 #7237 merit-order floor fill + uc-1.4 #7238 P1 floor =
  `mlf·p̄·a·u` + pass-2 schedule reuse; desk r08 records). Shards pin this lane branch's head, which carries this file and no
  other change (`source_revision` = its full 40-char SHA; the `src/`/`scripts/` tree equals `580c4fbf`'s).
- **Control (rule 29(b), no control solve):** keeper `2026-10-02-closeout-l1-coal-fuel`, bundle
  `results/calibration/closeout_ercot_l1_span`, 2019–2025, unchanged since the prior lane (same bundle bytes, same rubric 3.20
  records quoted in the inherited §3).
- **Arm (unchanged, one logical delta):** `replay_keeper.py results/calibration/closeout_ercot_l1_span --years <y> --set
  unit_commitment_milp=true --set ercot_gas_commitment_bridge=false`. `uc_*` at declared defaults (inherited §1 table +
  `uc_slim_window=true`). Every other floor is kept: `ercot_coal_min_config_floor`, `gas_st_netload_drag`,
  `coal_mustrun_per_plant`, `reliability_floor`, the CC committed tranche and `chp_steam`. Offer bands are **not** touched
  (rule 1; ERCOT bands are a separate lane, desk decision 8).

### 1.1 G-DRIFT, zero LP

**Prior pin `eab17188` → `580c4fbf`.** Outside `docs/`, `tests/` and `results/{bench,phase0}` records, six paths change:

| file | hunk | control (gate off) | arm |
|---|---|---|---|
| `model/uc/schedule.py`, `model/uc/uplift.py`, `pipeline/uc.py` | uc-1.3 merit-order cluster-floor fill; uplift priced in-process at `mc_base` (`uplift_from_bundle` deleted); pass-2 schedule reuse keyed by input digest; uc-1.4 P1 floor = `mlf·p̄·a·u` | **INERT**: `pipeline.uc` is imported only under `if getattr(config, "unit_commitment_milp", False)` (`pipeline/solve.py:676`, `runner.py:4175`, `run_calibration_full.py:7481`); no other importer of `model/uc` on the solve path (grep at the pin) | LIVE (intended: the release) |
| `scripts/probes/_ucmilp_compose_span.py` | uplift is no longer recomputed from the bundle | not on the solve path | composer only |
| `.gitignore` | negations for other lanes' bundles | — | — |

No `constants.py`, `iso_configs.py`, `config/scenarios.py`, `model/lp/*`, `data/*` or orchestrator hunk. **Control INERT**:
the keeper bundle remains the control. Since the prior lane's instrument-3 identity probe, the LP inputs have changed only
inside the gated stage.

**2019 leg reuse: `f998cf47` → `580c4fbf`.** `git diff --name-only f998cf47 580c4fbf` outside `docs/` and `tests/` is
**empty**: engine, orchestrators and scripts are byte-identical. The repro leg `claude/ucmilp-fix5-ercot-2019` @
`f832aa5261f60c61b3905b5ce1b0c92b3d12a0db` (parent `f998cf47`; 21 files incl. `dispatch/2019_P1.parquet`,
`uc_schedule`, `uc_uplift`, `uc_solve_log_2019.json`, `unit_marginal_2019`) records `run_config.json`
`git.basis_sha = f998cf47…`, `dirty = false`, `unit_commitment_milp = true`, `ercot_gas_commitment_bridge = false`,
`ercot_commitment_posture = false`, and every `uc_*` at its declared default. **It is this lane's 2019 leg.** The scratch
composer's recipe assertion (§4) re-checks it field by field against the keeper's 2019 recipe. If that assertion fails, the
lane re-solves 2019 at the pin under §4's budget.

## 2. Readings (inherited; restated by reference)

- **Targets T1–T6:** inherited §2, same bars. T4 (coal) is read as before: the eleven yard-pinned coal clusters carry no
  integer (ruling (a)), so coal rows move only through the merit order.
- **Control readings / kill rows:** inherited §3, unchanged (every registered year, every criterion and class row; the
  tight rows named there; attestation artefacts per inherited §8 are not flips).
- **Structure S1–S5, cost W1–W5:** inherited §§4–5. W1's ratio uses the same declared proxy: total ÷ the shard's own
  `solve_p0 + solve_p1`.
- **Added by the charter, per year, control → arm:** C1, C3a, C3b, C3c, C4, C8 (as scored, and with MECH 28 removed = R4);
  unserved MWh; uplift % (Σ `uplift_usd` ÷ Σ λ·load); CC_REGULAR / ST_GAS / coal starts vs CEMS; **forced peak-tranche TWh**
  (`unit_marginal` rows on `_peak*` tranches at their UC floor; expected ≈ 0 at uc-1.4; any year > 0.1 TWh is reported as a
  defect-6 recurrence to UC-DESK); wall ÷ (P0+P1); integer clusters / gate set; time-limit hits.
- **Price-move diagnosis (zero LP, from the bundles; reported, never tuned on).** For every year where |ΔC3a| > 2 pp or
  |ΔC3b| > 0.02, control → arm:
  1. Δ mean LMP split by **hour class**: actual-price terciles; hours with actual ≤ $15; the top-100 actual-price hours;
     and on-peak (HE07–22 weekdays) vs off-peak.
  2. In each class, the **marginal class mix**: P1 `unit_marginal` `marginal == 1` rows, by plant class and offer tranche
     (`committed` / `econ_low` / `econ_high` / `peak`), arm vs control.
  3. The UC's **online-capacity delta** in the same hours: Σ online MW from `uc_schedule`, against the control's online MW
     on the 1 %-of-cap convention.
  4. The sign of each piece, so the move is attributed to one of three things: (i) price set by a higher-tranche unit after
     decommitment (the scarcity wall); (ii) a lost near-min-load body (fewer online MW in the trough); (iii) a reserve-dual
     change. The attribution is descriptive. It does not create a parameter (rule 21).

## 3. Kills and verdict (inherited §7, §7.1; staging dropped by charter)

1. **Kill #1, an infeasible window or "no incumbent":** that leg stops. Its window index, hours and traceback go to UC-DESK
   as an engine defect, with a repro. The lane patches no `src/`. The other legs run on.
2. **Kill #2, the P1 LP infeasible after the UC:** same handling as kill #1.
3. **Kill #3, a control flip:** 2019 has already fired it (§0). **Per the charter, it does not stop the other legs.** It
   fixes the verdict at R. All seven years are scored and reported, and every further flip is listed.
4. **Non-determinism:** exercised only if a relaunched leg and its predecessor both complete (inherited).
- **Verdict:** K-candidate / R / I per inherited §7.1. Expected **R** (§0). The RESULT's D-6 card text names the rule-1
  reading separately: is the remaining price gap engine, calibration (bands, a separate lane) or structural?

## 4. Solve plan

| year | leg | budget | basis for the budget |
|---|---|---|---|
| 2019 | **reused**: `claude/ucmilp-fix5-ercot-2019` @ `f832aa52` (§1.1) | — | measured 8,030 s total |
| 2020, 2024, 2025 | new shard | **720 min** | uc-1.2 single-pass UC 6,500–8,500 s; pass-2 reuse at uc-1.3 removes the second pass |
| 2021, 2022, 2023 | new shard | **720 min** (charter cap) | inherited Addendum B.3: the 2022 MILP was projected at ≈ 28,000 s with 72 integers. 61 integers here can only shorten it. A leg that reaches 720 min with no bundle stops and reports its last window (a cost finding, not a kill) |

- Six shards, one year each (rules 16, 36): prompts from `scripts/shard_prompt.py --iso ERCOT --year <y> --sha <branch
  head> --lane ucmilp3-ercot --bundle results/calibration/closeout_ercot_l1_span --set unit_commitment_milp=true --set
  ercot_gas_commitment_bridge=false --budget 720`, plus the inherited Addendum D lane addenda (the solve runs detached and
  the session stays active; `unit_hourly` is unstaged; five UC artefacts are required; kill handling). New: **any file over
  100 MB is split into ≤ 95 MB parts** before commit (`split -b 95M`). Its sha256 and the part sha256s go in
  `<out-dir>/SPLIT_SHA256SUMS`, and the unsplit original is unstaged. Out-dirs `results/calibration/ucmilp3_ercot_<y>`,
  branches `claude/ucmilp3-ercot-<y>`. Prompts are committed as `shard-prompts-ucmilp3-ercot.txt`.
- **Each leg:** fetch; `git ls-tree -r <sha> -- <out-dir>` non-empty; check out; verify `dispatch/<y>_P1.parquet` and the
  four UC/marginal files; then archive (rule 33).
- **Compose and score in the parent, zero LP.** Use the prior lane's scratch composer
  (`data/ucmilp_ercot_span/readings/compose_ercot.py`): `PER_YEAR_FIELDS` ∪ the keeper's per-year fields, the recipe
  assertion, and `_respan_shared_inputs`. The output is `results/calibration/ucmilp3_ercot_span`. Then
  `calibration_verdict.py --json`, regenerated `legitimacy_diagnostics.json`, `screen_year` M1–M4, the flip diff, R4 and the
  §2 diagnosis. Local scoring only: no dashboard registration (E13), no promotion, nothing deleted (rule 31).
- **Deliver:** a RESULT beside this file, a slim span under `docs/records/ercot/ucmilp/data/ucmilp3_ercot_span/`, the
  `unit_commitment_milp` cell in `mechanism-matrix/ERCOT.js`, one PR to `main` (UC-DESK merges), and a message to UC-DESK.

## 5. DO NOT REDO

Inherited §9: no posture, no `online_capacity_envelope`, no `uc_*` value other than the defaults, no third `--set`, no
control solve, no offer-band change, no registration, no promotion.

## Addendum A (2026-10-14 08:49Z) — launched

Six shards were launched at the lane head `36b5c3f3a44d54791fc5cdddfaf158f135a88b69` (this file's first commit, with code
equal to `580c4fbf`). Model Opus, tag `ucmilp:UC-3-ERCOT-shard`, 720 min each, prompts in `shard-prompts-ucmilp3-ercot.txt`:

| year | session | branch |
|---|---|---|
| 2020 | `session_01VhB8cLCd2bB9bsQCAxQTbr` | `claude/ucmilp3-ercot-2020` |
| 2021 | `session_01NeHxoYbmZLgJpKWzZSv4yw` | `claude/ucmilp3-ercot-2021` |
| 2022 | `session_01R8MdgJEWNkgRrHrY7S3iuM` | `claude/ucmilp3-ercot-2022` |
| 2023 | `session_01H9eBzn6ycpWjnMP6aAX6Ze` | `claude/ucmilp3-ercot-2023` |
| 2024 | `session_01AfFUGJNKzacAk8xMP1jDSi` | `claude/ucmilp3-ercot-2024` |
| 2025 | `session_01L9fKwrsVqGz2VQoLcMGgvX` | `claude/ucmilp3-ercot-2025` |

The 2019 leg is reused from `f832aa52` (§1.1).

## Addendum B (2026-10-14 12:40Z) — engine defect 7; the verdict moves to uc-1.5

**UC-DESK (12:37Z, verbatim):** *"engine defect 7 is confirmed: the UC double-counted no-load on integer clusters
(ERCOT 2019: $148M CC, $18M ST). The fix (uc-1.5, PR #7246) merges shortly. Plan for you: let the shards already running at
580c4fbf finish; they're kept as uc-1.4 evidence, so don't kill them. Don't launch any new uc-1.4 legs. When I send the uc-1.5
full SHA, add a PRECOMMIT addendum with G-DRIFT to it and run all 7 years at uc-1.5. The RESULT reports uc-1.4 and uc-1.5 side
by side; the verdict is read at uc-1.5."*

Fixed now, before any uc-1.5 number exists:

1. **The uc-1.4 legs are evidence and are not scored for the verdict.** Five are in hand: 2019 `f832aa52`, 2020 `2f6b9e1d`,
   2023 `090b2a35`, 2024 `bbe10707` and 2025 `9a0665e8`. 2021 and 2022 run to completion. The RESULT shows their gate rows
   beside the uc-1.5 rows.
2. **uc-1.5 span.** Seven new shards, 2019–2025; the 2019 repro is not reused, because its engine is uc-1.4. Each shard pins
   this lane branch's head after Addendum C. Addendum C records the uc-1.5 merge SHA and the G-DRIFT `580c4fbf` → uc-1.5, and
   only a UC-stage hunk (gated) may be LIVE. Same arm, same two `--set` fields, 720 min per shard. Out-dirs
   `results/calibration/ucmilp3b_ercot_<y>`, branches `claude/ucmilp3b-ercot-<y>`.
3. **Verdict at uc-1.5.** The readings, bars, kills and verdict rule do not move. §0's 2019 pre-known flip is a uc-1.4 number,
   so it no longer fixes the verdict: the uc-1.5 2019 leg is read fresh under the inherited §3 rule.
4. Defect 7 inflates the UC's cost of keeping integer clusters online, so it biases the schedule toward decommitment. That is
   the direction of every uc-1.4 price move in this lane (§2 diagnosis: −4 GW CC online, +$4–6/MWh). The uc-1.4 → uc-1.5 delta
   is therefore reported per year as a direct measure of how much of the price move was the defect.
