# PRECOMMIT — ercot-213 (RESERVE-BASIS-2, card X item X-3 second increment): the anchoring-correct successor to the ercot-212 net-credits arm (`ercot_ordc_adder_published_anchor`), armed A/B on the keeper recipe

**Session ercot-213, 2026-08-16, branch `claude/ercot-reserve-anchoring-fix-p6c55p`.
PUSHED BEFORE ANY SOLVE.** Keeper resolved fresh from
`frontend/data/backcast/keepers/ERCOT.json`:
**`2026-08-15-ercot204-rule26-delete`**, determination NOT-YET, fail set
{C3a-2023, C3b-2023}, C3c the single ledgered CAVEAT ×3. **The keeper cannot
change in-session** — the outcome is a promotion RECOMMENDATION at most (X-3).

This is the successor NAMED by
`docs/FINDING-ercot212-reserve-basis-phase0-2026-08-16.md` §5, entered on its
terms: the net-credits identification is VALIDATED, the arm was REJECTED on a
diagnosed structural mis-anchoring, and the 28a cell note forbids re-running
the bare netting without the anchoring fix. Nothing here re-tests the bare
netting.

## §1 The delta — the keeper recipe + the netting flag + ONE anchoring repair

Two flags on the keeper recipe, and they are one object: the netting is the
validated half being carried forward, the anchor is the repair.

1. **`ercot_reserve_supply_cap_net_credits=true`** (the ercot-212 field,
   unchanged, still default-off) — net the armed LR + storage-AS credit series
   off the measured reserve-supply caps, `cap' = max(cap − lr − sas, 0)`, so
   the same MW is not credited on the demand side while riding a supply cap
   whose telemetry already contains it. Identification VALIDATED at ercot-212:
   realized `ordc_adder` incidence 184/38/7 h ≥ $1 against a 175/45/5
   prediction, nonzero 564/178/67 against a 571/190/67 upper bound.
2. **`ercot_ordc_adder_published_anchor=true`** (NEW, default **False** —
   keeper-reproducing) — the repair. Inside the already-armed cap-additive
   branch of `run_calibration_full._system_frame`, and nowhere else:

```
lambda(t)  = demand-weighted system energy dual        (the LP's own price)
head(t)    = max(VOLL - lambda(t), 0)                  (VOLL = ordc_voll, registered)
adder(t)   = min( gamma_all(t) * head(t) / VOLL , head(t) )
```

where `gamma_all` is the **ALL-tier** (total-reserve, `RTOLCAP + RTOFFCAP`)
reserve-supply-cap row dual — a SINGLE counterpart, never the two-tier sum.

**What it repairs, both halves structural** (finding §5):

* **(a) Anchor.** The in-LP ORDC demand curve is **VOLL-anchored**
  (`scarcity.ercot_ordc_demand_steps` — an LP objective coefficient must be a
  constant, and λ is endogenous). That is the co-optimization-correct form,
  where the dual lifts the LMP and λ is already carried there. The **published
  additive** formula this channel emulates is
  `RTORPA = 0.5 (VOLL − λ)(LOLP_full + LOLP_half)`, capped so `λ + adders ≤ VOLL`
  (`results/scarcity.py::ordc_adder`). Writing the VOLL-anchored dual verbatim
  into an ADDITIVE channel over-prices every hour by exactly the missing λ
  subtraction.
* **(b) Counterpart.** Summing BOTH headroom tiers' cap duals adds two ORDC
  prices for one ORDC. Measured consequence on the ercot-212 arm: a maximum
  written adder of **$10,000/MWh = 2 × VOLL**, a price the published protocol
  cap makes unreachable. The additive channel prices the ORDC **total**-reserve
  family, whose supply bound is the all tier; that row is its counterpart.

**Why the rescale IS the published formula, exactly** (and why this is an
anchor change, not a curve, level or basis change): at the marginal reserve
level the LP step price is `gamma = 0.5·VOLL·(LOLP_f + LOLP_h)` at that same
level, so `gamma·(VOLL − λ)/VOLL = 0.5·(VOLL − λ)·(LOLP_f + LOLP_h)` — the
published adder, at the level the LP actually cleared. Pinned as a test
(`tests/unit/pipeline/test_ordc_published_anchor.py::
test_reproduces_the_published_ordc_adder_at_the_same_level`).

**Identification (rules 5/13/20/23): ZERO fitted scalars.** VOLL is the
registered `ScenarioConfig.ordc_voll`, read through the prb_overrides-first
channel (the caiso-80 defect class) so a scenario override cannot be silently
dropped; λ is the LP's own demand-weighted system energy dual (the model
analogue documented in `results/scarcity.py`); `gamma_all` is an LP dual. The
flag is a boolean. `ordc_voll=None` under the armed flag is a loud `ValueError`,
never a magic default (rule 5).

**Named limitation, stated up front, not discovered later.** Where the LP's
marginal step is an OBDRR048 **floor** step rather than an LOLP step, the
rescale under-states the published floor by `λ/VOLL` — conservative, and
measured negligible: at the floor's ≤ 7,000 MW reserve levels the LOLP price on
the armed μ=924/σ=1,348 curve is ~$200+, an order of magnitude above the
$10/$20 floor, so the floor never sets the step. **The route through the
post-solve `ordc_adder()` construction was considered and REJECTED on a
structural argument, not on convenience:** it would re-price the WHOLE curve
value at the realized level, including the `mu_headroom` component the co-opt
has already folded into the energy LMP — re-introducing exactly the ercot52
double-count the cap-dual branch exists to prevent. The rescale preserves the
LP's own `λ_balance = λ_cap + μ_headroom` decomposition and touches only the
anchor. `ordc_adder()`'s protocol cap and OBDRR048 date gate are therefore
re-derived here rather than inherited: the cap is the explicit `min(·, head)`
above, and the floor's date gate is immaterial because the floor never binds
(measured post-solve, reported either way).

**Increment (c) is NOT in this A/B.** The published **two-basis** form
(half-hour LOLP term at the online tier, floor keyed to online) is a
family-splitting construction and is separately gated: it is built ONLY if this
increment lands clean, under its own precommit amendment, as a third registered
member. Building it now would confound the two.

**Scope / registry (rules 24/25).** The flag is a `solve_and_persist` kwarg
recorded in the bundle's `meta.json`, exactly like its sibling
`ercot_ordc_cap_dual_adder`, with a matching `--ercot-ordc-adder-published-anchor`
CLI flag — the additive-writer family's registered channel. It is reachable
only inside `iso == "ERCOT"` + `ercot_reserve_supply_cap` + the ORDC regime +
`ercot_ordc_cap_dual_adder`; armed alone it is provably inert (test
`test_flag_is_inert_without_the_cap_dual_branch`). No env-var knob, no
`getattr` literal, no per-plant dict.

## §2 Predictions, stated ex ante

From the ercot-212 out-of-LP construction (finding §5, "expected landing
zone") and the arithmetic of the repair:

* **Incidence barely moves from the ercot-212 arm; LEVELS fall, and fall most
  where λ is largest.** The rescale factor is `(VOLL − λ)/VOLL` — 0.99 in a
  $30/MWh hour, 0.4 in a $3,000/MWh hour — so the deep tail is cut hardest
  while the broad-shallow region is nearly untouched. Dropping the fast tier
  removes its contribution outright wherever both cap rows bound.
* **Landing zone (the dispatch's stated band): 2023 deep tail ~20–37 h > $100
  against 17 published settled; 2024 ~45–48 h > $1 against 78** — between the
  control's silence (3/0/0 h `ordc_adder` > $1) and the ercot-212 arm's
  overshoot.
* **No written adder may exceed `VOLL − λ`**; the arm's $10,000/h maximum
  becomes ≤ $5,000 − λ by construction. Reported as a measured post-solve
  check, not assumed.
* **2023 moves and is side-effect-reported at full magnitude under Q-B/R-A
  phrasing, never a basis, never a gate** (X-3). Direction expected: the
  ercot-212 arm read C3a-2023 **+13.3 %** (from the control's −33.2 %); a
  strictly smaller adder lands somewhere BELOW that, and where it lands
  between −33.2 % and +13.3 % is not a promotion criterion and is not consulted
  by §4.
* Dispatch effects: unchanged in kind from ercot-212 — the netting frees
  reserve into energy in newly cap-bound hours (2023 shed 4 → 0 expected to
  reproduce). The anchor is post-solve and moves NO volume, so all volume
  effects are the netting's.
* 2025 stays under-produced vs published on counts — the parameter-keyed
  residual ercot-206 B0 assigned to the 2025-vintage LOLP table; NOT chased
  here (no table arming).

## §3 Kill gates — direction-blind, inherited from ercot-212 §3 AS AMENDED

Measured on the armed member vs the control replay; **ANY kill ⇒
REJECTED-AS-ARMED**, verdict standing regardless of residual direction.

| gate | rule |
|---|---|
| **G-REPRO′** | Inherited from ercot-212 Amendment 1 and adopted FROM THE START: the keeper is **not byte-reproducible at HEAD** (upstream main drift, `c447199c9..HEAD`, measured on both environments). So (a) the A/B is measured **control-vs-armed**, both at the same HEAD on the pinned true solve environment, isolating exactly the delta; (b) off-path inertness is carried by construction + the design tests, not by vs-keeper bytes; (c) the control-vs-keeper drift is REPORTED at full magnitude alongside the control's own scored values. |
| **G-SHED** | shed (slack) hours must not INCREASE in any year (control basis). Decreases and hour-list changes are reported, not gated. |
| **G-C3c** | the model price tail must not move AWAY from actual in any year (2023 actual 181, 2024 53, 2025 31). Movement toward actual is reported, never a promotion basis. |
| **G-SPUR** | spurious mid-band hours (model ∈ [150, 500] & actual < $150) must not increase by more than **5** in any year. *(This is the gate that killed ercot-212: 9 → 16 in 2023.)* |
| **G-SPAN** | max per-class annual energy delta ≤ 2.0 % of ISO load in every year. |
| **G-COAL148** | coal-above-ceiling rise ≤ 0.5 TWh in every year. |
| **G-OWNER** | C3a-2024, C3a-2025, C3b-2024 must remain PASS on the armed member's own scorecard. |
| **G-DOF** | zero new tuned scalars: ledger `n_residual` stays 6; both new flags are booleans carrying no numeric value. |
| **G-D2** | no NEW D-4 off-window-binding failure row (the pre-existing `reliability_floor × CT_PEAKER` rows carry). |

**One ADDED gate, structural and pre-registered because it is the whole point
of this increment:**

| gate | rule |
|---|---|
| **G-CAP** | **no written `ordc_adder(t)` may exceed `VOLL − λ(t)`** in any hour of any year (the published protocol cap, `λ + adders ≤ VOLL`). A violation means the repair did not repair. Measured on the armed member's committed `system_<year>.parquet`. |

**LOYO:** parameter-free rule (no fitted value exists to identify), so
structurally N/A, with per-year deltas reported in its place (ercot-173/188
precedent).

## §4 Decision rule (direction-blind)

Reads ONLY the §3 gates. All live gates PASS ⇒ register both + **RECOMMEND
promotion** (the keeper does not change in-session) + evaluate whether to build
increment (c) under an amendment. Any kill gate FAILS ⇒ **REJECTED-AS-ARMED**,
register both, prune per §5, cell verdict `R`, and increment (c) is NOT built.
Residual direction — 2023 included — is never consulted by this rule; all
residual moves are reported at full magnitude under the Q-B/R-A phrasing.

## §5 Roster effects, named ex ante (the retention directive replaces top-15)

ERCOT's registry currently holds ONE run (the keeper, protected) — the
ercot-212 A/B pair was registered then pruned in-session per the roster duty. A
live A/B registers normally → 3 runs, no eviction. If the adjudication is
REJECTED-WHOLESALE, the pair is pruned in this same session with
`scripts/prune_iso_runs.py`; the finding, the matrix cell and the log entry
remain the durable record either way.

## §6 Execution

* **Solve environment PINNED BEFORE THE CONTROL** to the keeper's TRUE solve
  env — **highspy 1.15.1 / pandas 3.0.5 / pyarrow 25.0.1** — not the lockfile
  env its `run_config.json` `environment` block records (highspy 1.14.0 /
  pandas 3.0.3 / pyarrow 24.0.0; the ercot-204 §B.2 trap, re-measured at
  ercot-212 Amendment 1). `./.venv/bin/python` invoked directly, never
  `uv run`.
* `data/clean/gtc-limits` regenerated from `data/raw` before any replay (the
  keeper arms `ercot_gtc_limits_measured`; the partition is gitignored).
  Regenerated 2026-08-16: 7 year files, 2023/2024/2025 = 13,452 / 15,273 /
  21,864 (gtc, hour) rows.
* Control: `scripts/replay_keeper.py results/calibration/ercot204_rule26_delete
  --out-dir results/calibration/ercot213_control_A` — full span
  `2023 2024 2025` in ONE invocation, years sequential (rule 12).
* Armed: same + `--set ercot_reserve_supply_cap_net_credits=true`
  `--set ercot_ordc_adder_published_anchor=true`,
  `--out-dir results/calibration/ercot213_anchor_B`.
* The two invocations run **sequentially, not concurrently**: rule 12 caps
  per-plant multi-zone concurrency at ~2, but this box has 15 GB RAM against a
  measured ~12.7 GB peak RSS for this keeper's LP (ercot-188 G-COST), so two
  at once would OOM.
* Both runs register on the BACKCAST registry with payloads (rules 15/16; run
  payloads over `git push`, HTTP/1.1 fallback on a hung push), matrix 28b cell
  verdict on the `ercot_multiproduct_as` row + the 28c leg in the same landing,
  calibration-log entry under **ercot-213** (ercot-199 remains unclaimed).

## §7 Fences

Rule 22: {2023, 2024, 2025} only, no marker sought, no out-of-training year
solved or scored. Rule 25: ERCOT only — both flags gate on the ERCOT
multiproduct design alone; no parameter crosses an ISO boundary. Rule 27: edits
local, exact on-disk bytes pushed, ≥300-line pushed files blob-verified. Rules
5/24: both fields registered, recorded in `meta.json`, no off-registry channel.
No new workflows, no cron, solves run in-session.
`scripts/check_mechanism_matrix.py` exit 0 before landing. No PR
(push-and-stop; the owner merges).

**Standing rulings cited, never re-litigated.** Q-B FINAL + R-A: any
C3a/C3b-2023 movement is side-effect-reported at full magnitude, never a gate,
never a basis (the ercot-212 §5 report is the phrasing precedent). ercot-206
B0: no blanket LOLP-table arming — the published NP6-576-ER table is not armed
here in any form. ercot-211: Door A closed, no conduct work. V0/ercot-201
DO-NOT-REDO: no tightness-conditioned identification, no E1 term; RTOLCAP is
telemetry read against the ALREADY-armed cap construction (FFR-8B §4), never a
fitted input. 28a: the bare net-credits arm is adjudicated `R` and is NOT
re-tested — it appears here only WITH the anchoring fix.
