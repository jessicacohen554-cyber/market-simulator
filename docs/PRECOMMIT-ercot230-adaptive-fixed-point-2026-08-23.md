# PRECOMMIT — ercot-230: the SECOND ADAPTATION PASS (fixed-point iteration) on the armed adaptive-expectation storage floor — mechanism form, stopping rule, A/B and kill gates, pinned BEFORE any build and BEFORE any solve

> Status: PRECOMMIT, pushed and blob-verified before any code edit lands and
> before any LP is launched (dispatch requirement). Session ercot-230, branch
> `claude/ercot-2023-summer-scarcity-1nx4cl` (the dispatch named `-9lg3nm`,
> which the 226/227 hub consumed and the owner merged at PR #4210; this
> session's harness branch is the successor, cut from that merge's tip).
> Keeper at pin: **`2026-08-20-ercot223-arm-eventrelease`** (NOT-YET, fail
> set {C3a-2023 −39.7 %, C3b-2023 NRMSE 0.729}, C3c ledgered CAVEAT ×3;
> 2024/2025 clean at +0.4 %/0.131/22 h and −7.6 %/0.099/1 h).

## 0. THE OWNER CHARTER (verbatim, recorded per the X-1/X-2/B-1
signature-by-dispatch precedent)

The ercot-230 dispatch mandated: *"This session must NOT re-enter Door D on
its own authority — open by asking the owner whether W-1's fence lifts, and
what the lever is."* The session opened with exactly that question, presenting
three options (lift the fence onto the conduct object via the second
adaptation pass; keep the fence and sweep the non-AS tightness channel;
restore the Door-D rest posture). The owner selected, in session on
2026-08-23:

> **"2nd adaptation pass"** — the option pinned as: *"Lift the fence onto the
> conduct object. Card + build the fixed-point iteration on the ARMED adaptive
> mechanism: its ceiling is measured as bootstrap starvation (model 7 spike
> days ~30% of reality's 23; one pass recovered ~0.6pp of the ~24pp depth
> half). Precommit first (convergence/stopping rule identified ex ante, LOYO
> 2023-2025, full 226 gate battery), then solved A/B verdict."*

This constitutes the owner card for the family's first named successor —
FINDING-ercot221-adaptive-expectation-2026-08-19.md §4: *"The named successor
knobs — a second adaptation pass (fixed-point iteration), the cross-year
memory (…), a seasonal end-of-season term — each carry real DOF and need
their own identification; none is built here."* The cross-year member was
refuted at ercot-222 and stays refuted; the seasonal term is NOT chartered
here. W-1's fence is LIFTED for this object by the selection above; the
Door-D floor (2026 SOM anchors) remains the recorded fallback if this lane
fails.

Standing owner order carried forward from ercot-227: **every mechanism tested
gets a SOLVED verdict, not a paper kill.**

## 1. THE MECHANISM (pinned)

**What it completes.** The armed mechanism (`ercot_storage_adaptive_
expectation` + `ercot_adaptive_event_release`, the current keeper) computes
the storage fleet's spike expectation `P_hat` from the model's OWN price path
— but from the UNFLOORED pass-1 path, whose 7 spike days are ~30 % of
reality's 23 event days. Reality's conduct read reality's own realized path —
a path its own offers shaped, self-consistent by construction. The pass-1/
pass-2 split breaks that identity: the scored path's events are NOT the
events the offers were computed from (ercot-221 FINDING: "the bootstrap is
starved, not wrong"). The fixed-point iteration restores the identity: keep
re-deriving the floors from the latest solved path until the floors reproduce
themselves, so the scored pass's floors are computed from the scored pass's
own events.

**Form (pinned).** One new boolean `ScenarioConfig` field,
`ercot_adaptive_fixed_point` (default **False** → HEAD replays the keeper
byte-identically), read ONLY inside the existing `iso == "ERCOT"` armed
adaptive block (armed alone without the family: no-op, the
`ercot_adaptive_event_release` posture). When True, after the incumbent
pass-2 solve:

- **Iterate** additional adaptation passes k = 3, 4, …: recompute the
  IDENTICAL floor arithmetic the incumbent block runs — the Amendment-4
  settle basis (λ + the model's own decontaminated anchored scarcity-adder
  mirror) from the latest P1, daily-max events ≥ `ERCOT_ADAPTIVE_EVENT_USD`,
  `ercot_adaptive_expectation_daily` with the frozen constants, the h17–20
  window floor at `P_hat × ordc_voll`, and the event-release mask at hours
  the immediately-preceding pass's settle ≥ the event threshold (the natural
  generalization of "pass-1 settle" when the preceding pass is pass k−1; for
  pass 2 this is literally the incumbent construction) — then re-solve
  through the same `run_energy_solve(p1_storage_discharge_cost=…)` seam.
  P0 is untouched in every pass, exactly as today.
- **Stopping rule (parameter-free, pinned ex ante).** After each solved pass
  k, compute the floor vector the NEXT pass would run under, `floor_{k+1}`:
  - `floor_{k+1} == floor_k` elementwise (the floor the just-solved pass ran
    under) ⇒ **CONVERGED**: pass k+1 would solve the identical LP, so pass k
    IS the fixed point — it is THE scored pass; no further solve. The
    comparison is exact float equality, meaningful because the floor is a
    deterministic function of the discrete state (daily event set + in-window
    release set): identical state ⇒ bitwise-identical floors.
  - `floor_{k+1}` equal to the floor of an EARLIER, non-adjacent pass ⇒
    **CYCLE** (the release-mask flip-flop this design anticipates: a
    floor-carried hour crosses the event threshold, is released next pass,
    falls back, is re-floored): stop, score the last solved pass, record the
    cycle. The scored object is then a well-defined N-pass adaptive path —
    one epistemic level deeper than the keeper's, disclosed as non-converged.
  - `ERCOT_ADAPTIVE_MAX_PASSES = 8` additional passes reached ⇒ stop, score
    the last solved pass, record CAP-HIT. The cap is an OPERATIONAL bound of
    the conventions class (like the 120-day trail window), pre-registered
    here, bounding worst-case runtime (~8 extra P0+P1 chains); it shapes no
    converged answer — a converged run never reaches it, and a capped run is
    disclosed as non-converged.
- **Audit trail.** The `hourly/adaptive_<year>.parquet` sidecar keeps its
  exact schema (year/hour/s_model_day/p_hat_day/floor_usd) and carries the
  state of THE SCORED PASS: the event/P_hat series its floors were derived
  from and the floors it ran under (at convergence these are the scored
  path's own events — the self-consistency made visible). A new small
  `hourly/adaptive_iteration_<year>.json` records the trajectory: per-pass
  spike-day counts, floored/released window-hour counts, floor-vector
  hashes, and the stop reason. Absent (no file) on every flag-off run.

**What is UNTOUCHED (pinned):** the two rule-23 frozen constants (half-life
30.0 d, β 3.0077), the conventions ($1,000 event threshold; 120-day trail;
h17–20 CST window; per-solve-year reset — the ercot-222 refuted cross-year
seed stays refuted), the Amendment-4 event basis, the event-release guard's
threshold and semantics, the P0 pass, the mutual exclusion with
`ercot_storage_reservation_offer`, and the CAISO leg (rule 25: a CAISO
fixed point would be its own card in its own lane).

## 2. IDENTIFICATION (why this carries ZERO new identified constants)

The ercot-221 Phase-0 identified `(half-life, β)` by fitting the measured
2023 daily evening offer surface against the trailing state of the MEASURED
realized path — reality's own path, which is self-consistent (its offers
shaped it). The constants are therefore identified FOR a self-consistent
path; applying them to the pass-1 unfloored path under-supplies the state
they were fit against — that is precisely the measured starvation (implied
floors $899–1,850 vs measured asks $3,400–5,000; 7 events vs 23). The
iteration is not a new behavioural claim and fits nothing: it supplies the
constants the path-consistency their identification assumed. Free
parameters added: **none.** DOF ledger delta: ONE boolean + ONE
pre-registered operational cap (8) in the conventions class;
`n_residual` unchanged.

The rule-10 note, confronted: `[R-ONE-PASS]`'s letter governs CAPACITY
EVOLUTION ("one-pass capacity evolution, no within-year convergence
iteration") and is untouched — capacity evolution stays one-pass. The
ercot-221 card additionally pinned "exactly ONE adaptation pass (no
fixed-point iteration — rule 10 spirit)" for THIS mechanism as its own
conservatism; its FINDING then named the second pass as the family's first
successor needing its own card. This precommit, under the §0 owner charter,
is that card: the one-pass pin is AMENDED for the adaptive P1 offer pass
only. Nothing else inherits a licence to iterate.

## 3. A/B DESIGN (the ercot-226/227 discipline verbatim)

- **Control** = the keeper recipe (`results/calibration/ercot223_release_arm`
  meta) replayed at HEAD on THIS box via `scripts/replay_keeper.py … --years
  2023 --out-dir results/calibration/ercot230_ctl2023`. **G-REPRO is verified
  BEFORE the arm is read**: numeric identity vs the keeper's committed 2023
  sidecars (max|Δ| = 0.0 per numeric column of system/reserve_family/storage/
  adaptive; sha may differ on parquet layout across environments — the
  ercot-226/229 contract), plus `scripts/probes/ercot226_official_score.py
  --validate-keeper` printing exactly −39.7 % / 0.729 / 74 h (2023),
  +0.4 % / 0.131 / 22 h (2024), −7.6 % / 0.099 / 1 h (2025) from the
  committed bundle.
- **Arm** = the identical replay plus the single delta
  `--set ercot_adaptive_fixed_point=true`, 2023-only, into
  `results/calibration/ercot230_arm2023`. (2023-only probes are authorized
  and NOT dashboard-registered — waiver W-2 of the ercot-226 dispatch,
  carried forward by the ercot-230 dispatch. Probe bundles stay local; the
  committed record is the probe JSON + the FINDING.)
- Env pins verified before the control replay (highspy 1.15.1 / pandas 3.0.5 /
  pyarrow 25.0.1); solves in-session, strictly sequential, 6G swapfile +
  `MALLOC_ARENA_MAX=2` (the armed LP is UNCHANGED in size — the iteration
  adds passes, not rows — but the box ships with zero swap and the keeper
  chain peaks ~12.7–14 GB).

## 4. MEASUREMENTS AND GATES (per probe; scored by the frozen tooling)

`scripts/probes/ercot226_official_score.py` (official basis) +
`scripts/probes/ercot226_gates.py` (imports the frozen ercot221_gates
constructions; G-CAP, G-SHED, G-SPUR banded + lidless report-only, G-BAT,
G-D2, G-SHORTFALL, the summer miss-split / window-concentration /
calm-fortnight / channel-attribution block, per-family reserve diagnostics)
— run control → arm, 2023. Plus this card's own blocks:

- **Iteration trajectory**: per-pass spike days S_k, floored/released
  window hours, stop reason, n passes — from the solve log and
  `adaptive_iteration_2023.json`. Reported whatever the verdict.
- **The 226 §5.2 summer block**, with special attention to
  `d_price_at_miss` — the statistic every AS-procurement factor left at
  exactly 0.0. A conduct-depth lever moving it (or converting missed hours)
  is the first channel-consistent movement of the 114-hour miss set.

### Adoption criteria (official basis; the 226 §5.5 bars verbatim)

- C3a-2023 improves ≥ **1.5 pp** toward zero vs keeper −39.7 %;
- C3b-2023 ≤ keeper 0.729 + **0.005**;
- improvement window-concentrated and calm-fortnight clean (bias not worse
  than keeper 15.44 % by more than +2 pp);
- channel attribution clean: no improvement carried by manufactured reserve
  shortfall — **G-SHORTFALL subset form** (arm shortfall hour-set ⊆
  control's, per rigid family; Amendment-1 posture);
- G-CAP / G-SHED (2023 shed set ⊆ control's ∅) / G-BAT / G-D2 clean;
  G-SPUR banded ≤ +5 (lidless reported both forms, gate files untouched —
  the ercot-225 card stays unsigned);
- convergence is REPORTED, not gated: a converged fixed point is the design
  outcome; a cycle/cap stop is a disclosed limitation the owner weighs.

2023 official numbers remain side-effect reporting at full magnitude under
Q-B FINAL / R-A; the adoption criteria above are this card's owner-chartered
use of them (the 226 posture, §0).

### Promotion stage (ONLY if adoption passes; the dispatch's deliverables
clause authorizes promotion in-session)

Full 3-year armed bundle (rule 16 `[R-ALLYEARS]`: 2023 2024 2025, one
invocation, sequential), then:

- **G-OWNER retention**: official C3a-2024, C3a-2025, C3b-2024/2025 all
  remain PASS on the registered rubric bands;
- **G-SHED**: shed sets ⊆ {∅, {3067}, ∅};
- **G-BAT**: storage net discharge at actual-tail hours within ±25 % of
  EIA-930 BAT (2024/2025);
- **2025 invariance-by-construction, verified numerically**: the keeper's
  2025 path has zero spike days ⇒ P_hat ≡ 0 ⇒ the first recomputed floor
  equals the pass-2 floor (all-vom) ⇒ immediate convergence with ZERO
  additional solves; the 2025 sidecars must be numerically identical to the
  keeper's. 2024 (3 pass-1 spike days) MAY move; G-OWNER is its gate. This
  is the declared cross-year falsifier (G-SAFE analogue); LOYO on fitted
  constants is structurally N/A — zero new identified constants (the
  ercot-221/223 posture, stated ex ante).
- **Registration + promotion duties**: rule 15 in full (bundle slim files +
  registry sidecar + run payload over `git push` + bench + hourly sidecars
  incl. `reserve_family_<y>.parquet`); the keeper-shard X-2 prose rewrite
  (`standing_note`/`promotion_note`/`site_retention_note` re-written with
  THIS keeper's numbers); the ercot-216 C3c OPEN-RESIDUAL-LANE re-wording;
  the matrix §5.1 keeper + `gates:` re-stamp; `calibration-keeper-auditor`
  run --iso ERCOT. ERCOT holds no `complete` marker — no
  `calibration-complete.json` re-key arises.

**Verdict rule (mechanical):** adoption criteria all clear on the 2023 A/B ⇒
proceed to the promotion stage; its gates all clear ⇒ promoted this session.
Any adoption/promotion gate FAIL ⇒ REJECTED-AS-ARMED (or the stage's named
failure), recorded unrewritten at full magnitude, keeper unchanged, the
matrix cell stamped with the evidence — and the handback states which gate
failed, verbatim (the §5.8 else-branch form). Borderline mechanical verdicts
escalate in the handback per the owner's standing structural standard —
never self-rejected, never silently promoted.

## 5. PRIORS (pre-registered expected branches, recorded for honesty)

- **P-1 (convergence):** 2023 converges in ≤ 5 additional passes with
  spike days growing 7 → S* somewhere in [10, 30]; β = 3.0077 amplifies a
  trailing frequency of ⅓ to P_hat = 1, so the Aug–Sep window floors
  approach VOLL as the summer event set fills in. Official C3a-2023
  improvement is honestly UNKNOWN — the single-pass yield was ~+0.7 pp and
  compounding is superlinear until the clip; the depth-half ceiling
  (−13.4 % probe basis at perfect execution) stands, and the 117-hour count
  half remains out of scope by construction EXCEPT where an
  in-window floored hour itself crosses $200 (missed→caught conversion the
  AS program could never produce — report the miss-split movement).
- **P-2 (cycle):** the release-mask flip-flop can 2-cycle at floor-carried
  marginal event days (floored → realized → released → collapses →
  re-floored). The cycle rule scores the last pass and discloses.
- **P-3 (shed):** deeper floors at more hours re-create the h3066 defect
  class in 2023 at hours just UNDER the release threshold (floor-driven
  withhold with settle < $1,000, so the guard does not release). G-SHED
  2023 ⊆ ∅ is the direction-blind kill; a FAIL is recorded, not argued.
- **P-4 (G-BAT / re-timing):** iterated floors re-time storage discharge
  across the tail; the whole-day-floor failure mode (ercot-219 ratio 0.41)
  is window-fenced, but a within-window pile-up remains possible.
- **P-5 (2024, promotion stage):** 2024's 3 events amplify; expected
  movement +0.4 % → somewhere positive but in band; G-OWNER decides
  mechanically.
- **P-6 (the honest failure shape):** if the fixed point converges with
  spike days still ≪ 23 and C3a-2023 short of the 1.5 pp bar, the verdict
  is MEASURED-INSUFFICIENT — the within-year fixed point cannot supply
  reality's event experience from the model's own path, which would be the
  measured statement that the remaining depth needs the cross-year /
  seasonal structure the record has separately fenced (ercot-222 R; the
  unchartered seasonal term), and the lane returns to the owner with that
  measurement.

## 6. FENCES

Rule 22 ({2023} probe; {2023, 2024, 2025} promotion stage only; ERCOT holds
no marker — no other year, not even diagnostic). Rule 25 (ERCOT-gated field
inside the ERCOT block; CAISO leg and every other ISO's shards/curves
untouched). Rule 27 (edit locally, push exact on-disk bytes, blob-verify
every pushed file ≥ 300 lines; `git fetch origin main` + rebase before every
push; HTTP/1.1 retry before any pack-size conclusion; after any merge,
re-verify this session's edits survived). Rule 28 (the new field lands in
the `ercot_storage_adaptive_expectation` family row's `def:` string in
`mechanism-matrix.js` in the build commit — same family, no new mechanism
row, the ercot-223 precedent; the ERCOT cell verdict is stamped THIS session
whatever the outcome; `scripts/check_mechanism_matrix.py` exit 0 before
every push). Rules 5/23/24 (the boolean + cap registered:
`_CACHE_KEY_OPTIONAL_FIELDS` at its default with the nyiso-119
same-commit discipline, defaults table, `TIER_TAGS`; the cap a cited
constant in `results/scarcity.py`; no env-var knob). Rule 12 (years
sequential within an invocation; one solve at a time on this box). No CI
solves, no new workflows, no cron, no PR — push-and-stop on the designated
branch. W-2 (probe bundles local and unregistered; committed record = probe
JSON + FINDING + matrix stamp + log entry). DO-NOT-REDO honoured: Door A
static conduct ×3, item 11 / Q-B FINAL, mid-band, regime lanes, the
ercot-219 aggregate, B-2 (UNSIGNED, untouched), the ercot-222 cross-year
seed (R), F2/F3/F1-family (R/I), item 8 (closed) — all untouched; the
G-SPUR band-top card (ercot-225) and B-2 card stay unsigned, their gate
files untouched.

## 7. PROBE JSON SCHEMA

`results/calibration/ercot230_probe_fixedpoint.json` — the ercot-226 §5.9
schema verbatim (probe/factor/charter/session/branch_sha/env/control{grepro}/
arm/official/probe_basis/gates/family_diagnostics/summer/adaptive/verdict)
plus one block:
`iteration {n_adapt_passes, stop_reason ("converged"|"cycle"|"cap"),
spike_days_by_pass[], floored_window_hours_by_pass[],
released_window_hours_by_pass[], floor_sha_by_pass[]}`.
