# PRECHECK / PREREG — caiso-163: CAISO asymmetric WECC path ratings

**Session** caiso-163 · **Date** 2026-08-03 · **Branch**
`claude/caiso-asymmetric-path-ratings-3qnzoh` · **Base** `98ad9c1` (main, with
caiso-162 PR #3375 merged at `02230f8`)

**Mechanism** `ScenarioConfig.caiso_asymmetric_path_ratings` · matrix row
`measured_interface_limits`, CAISO cell `K` (the caiso-161 census registered this
leg on that row as **default-off and UNTESTED — no A/B, no probe, no log entry
anywhere in the record**) · **Incumbent keeper**
`2026-08-03-caiso162-per-year-import`
(`results/calibration/caiso162_peryear_import_caps_v2`), determination
CALIBRATED-WITH-CAVEATS, 2 of 3 non-protective ledger slots spent, 0 FAILs.

This document is written and pushed **before any LP is solved**. Every number in
§1–§5 is measured from committed artifacts, published data, or a no-LP structural
probe — no solve.

---

## 1. The arm

Single delta on the caiso162 keeper recipe, applied through
`scripts/replay_keeper.py --set caiso_asymmetric_path_ratings=<bool>`. The replay
driver reconstructs the keeper's `meta.json` kwargs exactly, so the config delta
is **structurally** one field rather than an asserted one. Both arms are solved at
**this session's HEAD**; the committed keeper is *not* used as the baseline
(caiso-162 measured HEAD drift alone moving C3a-2025 by 0.1 pp, comparable to the
effect under test).

| arm | bundle | flag |
|---|---|---|
| A (control) | `results/calibration/caiso163_control_A` | `caiso_asymmetric_path_ratings=false` |
| B (treatment) | `results/calibration/caiso163_asym_path_ratings` | `caiso_asymmetric_path_ratings=true` |

`iso_configs.py:369-378` ships CAISO's two internal north–south paths with
**symmetric** TTCs:

```
TransferLink(from_zone="NP15", to_zone="ZP26",       ttc_mw=5400.0)  # Path 15
TransferLink(from_zone="ZP26", to_zone="SP15_rest",  ttc_mw=4000.0)  # Path 26
```

Each of those numbers is only **one direction's** WECC rating. The published
directional ratings (WECC Path Rating Catalog;
`interchange/caiso.py:1850-1857` `CAISO_PATH_DIRECTIONAL_RATINGS`):

| path | N→S | S→N | shipped symmetric TTC | loosest direction's error |
|---|---:|---:|---:|---|
| Path 15 (Midway–Los Banos) | **3,265** | **5,400** | 5,400 | N→S runs **+65.4 %** too loose |
| Path 26 (Midway–Vincent) | **4,000** | **3,000** | 4,000 | S→N runs **+33.3 %** too loose |

So the LP is today free to move up to 5,400 MW north→south across a path WECC
rates at 3,265 MW, and up to 4,000 MW south→north across a path WECC rates at
3,000 MW. This is a rule-14 `[R-ACCURATE]` measured-over-estimate swap: published
directional ratings replacing a symmetric estimate.

### 1a. NO-TUNING CLAUSE

**Zero free parameters.** All four numbers are the published WECC Path Rating
Catalog directional ratings, already committed in
`CAISO_PATH_DIRECTIONAL_RATINGS` before this session opened; this session neither
adds, edits nor derives any of them. **Nothing is swept, blended, interpolated,
rounded, or adjusted, and no residual is consulted in choosing any value** —
there is no knob in this arm to sweep. The DOF ledger gains **no** entry
(rule 21 `[R-DOF]`): it is carried verbatim at the incumbent's 11 entries /
9 residual and the attestation generator will **assert** that, not assume it.
No new `ScenarioConfig` surface is created (rule 24 `[R-REGISTRY]`) — the field
already exists.

### 1b. Wiring status — checked BEFORE solving (the caiso-162 lesson)

caiso-162 lost a solve to a mechanism that had **no call site on the backcast
lane at all**, and would have written a false `I` (a DO-NOT-REDO code) had it
been read on prices. That check was run first here.

`apply_caiso_asymmetric_path_limits` is invoked from
`interchange/spec.py:1988` inside `apply_interchange_topology`, which **is**
called on the calibration lane at `scripts/run_calibration.py:2037` (inside the
`priced_interchange` branch). The keeper runs `priced_interchange=true`,
`caiso_per_hub_intertie=true`, `caiso_endogenous_wecc_node=false`, so that branch
is the one it takes. **The call site exists on the lane being solved** — verified
by a no-LP structural probe that ran the full backcast topology sequence
(`apply_iso_year_ttc` → `apply_caiso_local_import_limits` →
`apply_interchange_topology`) for each solve year and resolved the result through
`build_interface_groups`:

```
2023/2024/2025 OFF: internal N–S links [(NP15,ZP26,5400),(ZP26,SP15_rest,4000)]
                    | directional limits = 0 | resolved-to-LP-groups = 0
2023/2024/2025 ON : internal N–S links [(NP15,ZP26,5400),(ZP26,SP15_rest,4000)]
                    | directional limits = 2 | resolved-to-LP-groups = 2
                      CAISO_path_directional_NP15_ZP26       cap=3265.0 rev=5400.0
                      CAISO_path_directional_ZP26_SP15_rest  cap=4000.0 rev=3000.0
```

Both limits survive the per-hub corridor split (it re-homes only the *import*
links) and both resolve to non-empty LP flow-column groups, so the LP sees them.
`InterfaceLimit.reverse_cap_mw` bounds the signed group sum in
`[-reverse_cap_mw, cap_mw]`, overriding `bidirectional`
(`iso_configs.py:69-80`, `interchange/core.py:98`); the listed orientation of
each limit is the N→S direction, so `cap_mw` is the N→S bound and
`reverse_cap_mw` the S→N bound. The per-link symmetric `ttc_mw` is left untouched
(it already equals the looser direction), so the effective bounds become the
published ratings.

**What WAS missing, and is fixed in this session's first commit:** the flag had
no CLI/kwarg channel into the calibration lane — it could only be reached through
the generic `prb_overrides` dict. Seven sites wired:
`run_calibration_full.py` (`solve_and_persist` signature, the `recorded_cfg`
`with_overrides` block, the `run_year` call, the `meta` dict, the argparse
`--caiso-asymmetric-path-ratings`, and the `main()` call) plus
`run_calibration.py` (`run_year` signature and its `with_overrides` block).

### 1c. The structural no-op check that stands in for a zero-delta year

This mechanism has **no built-in no-op year** — unlike caiso-162, whose published
2023 LCT row equalled the static bake and gave a free zero-delta control. The
published ratings are year-invariant, so **every** solve year is a live year and
there is no free zero-delta arm. It is replaced by a **pre-solve structural
assertion**, already run and passing:

```
A. flag-off returns SAME OBJECT: True      # apply_...(cfg, config) is cfg
B. flag-on  returns a NEW object: True
```

Identity (`is`), not equality — the off path cannot perturb the topology even by
reconstruction. This is what licenses arm A as a clean control.

---

## 2. Why this lane, stated as the defect (no-LP evidence)

Measured from the committed keeper's own hourly sidecars against the published
CAISO DAM hub LMPs (`data/raw/lmp-data/CAISO/CAISO_dam_hourly_<y>.csv`,
`TH_{NP15,ZP26,SP15}_GEN-APND`):

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **hours NP15 ≠ ZP26, MODEL (keeper)** | 3 (0.034 %) | **0 (0.000 %)** | 1 (0.011 %) |
| **hours NP15 ≠ ZP26, ACTUAL** | **99.5 %** | **99.9 %** | **100.0 %** |
| mean NP15 − ZP26, MODEL | +0.00 | +0.00 | +0.00 |
| mean NP15 − ZP26, ACTUAL | **+5.95** | **+8.58** | **+5.73** |
| mean NP15 − SP15, MODEL | **−1.17** | **−0.91** | **−0.77** |
| mean NP15 − SP15, ACTUAL | **+2.34** | **+7.99** | **+6.01** |

Two structural facts, both independent of any residual:

1. **Path 15 is functionally absent from the model.** It separates NP15 from
   ZP26 in ~0.02 % of model hours against ~100 % of real hours; the model's
   NP15 and ZP26 are byte-identical in all 8,760 hours of 2024. A modelled
   transmission path that never binds is not modelling the path.
2. **The NP15-over-SP15 basis has the wrong sign in all three years.** The real
   north trades $2.3–8.0/MWh *above* the south; the model puts it $0.8–1.2/MWh
   *below*.

*(Correction to the handoff's framing, recorded rather than buried: NP15 ≡ ZP26
is byte-identical only in **2024**. In 2023 and 2025 they differ in 3 and 1 hours
respectively, max |Δ| 1.14 and 4.29 $/MWh. The defect is real and the direction
of the claim is unchanged — Path 15 essentially never binds — but "byte-identical
in all years" overstates it, and the gates in §3 are written against the measured
0.034 % / 0 % / 0.011 % rather than against zero.)*

---

## 3. SIGN IS AMBIGUOUS — what this arm does NOT claim

This is a **structural-faithfulness arm, not a C3a arm.** It is *not* pitched as
closing C3a-2025 and must not be reported as such.

The two legs push the ISO mean in opposite directions and the net is not
predictable from committed artifacts:

- Tightening **Path 15 N→S** (5,400 → 3,265) traps cheap northern energy in
  NP15: NP15 falls, ZP26/SP15 rise. That moves NP15 − ZP26 **further negative** —
  *away* from the measured +5.7…+8.6.
- Tightening **Path 26 S→N** (4,000 → 3,000) confines the south's midday solar
  surplus: SP15 falls, ZP26/NP15 rise. That moves NP15 − SP15 **toward** the
  measured positive sign.

Which dominates depends on the realised hourly flow direction and is exactly
what the solve measures. **No prediction of the ISO-mean sign is registered
here**, and no post-hoc rationalisation of whichever sign appears will be
offered as evidence for the mechanism.

---

## 4. Gates, registered before the solve

### 4.1 LIVENESS — verified on FLOWS, never on prices (blocking)

Read from each arm's persisted link-flow array, not from `run_config.json` and
not from prices. Prices alone read a never-executed mechanism as a clean INERT
verdict and would write a **false matrix `I`**.

- **L1 (control is loose).** In arm A, `max` Path-15 N→S flow **> 3,265 MW**
  in at least one solve year, and/or `max` Path-26 S→N flow **> 3,000 MW** in at
  least one solve year. If neither is exceeded, the mechanism has nothing to bite
  on and the arm is reported **INERT with the flow evidence**, not as a null
  price result.
- **L2 (treatment is clipped).** In arm B, **every hour of every year**:
  Path-15 N→S ≤ 3,265 MW + 1e-6 and Path-26 S→N ≤ 3,000 MW + 1e-6.
- **L3 (it actually binds).** In arm B, the count of hours at each cap
  (within 1e-6) is reported per path per year.

**L2 failing is a stop-the-line bug, not a result.** L1 and L3 are what
distinguish a live-but-slack mechanism from an unexecuted one.

### 4.2 PRIMARY structural gates (the claim under test)

Reported for both arms, all three years:

- **S1** hours with |NP15 − ZP26| > $0.01, model — does Path 15 bind at all?
  Control baseline 0.034 % / 0.000 % / 0.011 %; actual ~100 %.
- **S2** does NP15 ≡ ZP26 stop being byte-identical in 2024 (the one year it is)?
- **S3** mean NP15 − ZP26 vs the measured +5.95 / +8.58 / +5.73.
- **S4** mean NP15 − SP15_rest vs the measured +2.34 / +7.99 / +6.01 — does the
  basis move **toward the measured sign**?

S3/S4 are **reported, not pass/fail**: per §3 the sign is ambiguous a priori, and
per rule 1 `[R-STRUCT]` a structurally-correct mechanism is never judged by
whether it improves the residual.

### 4.3 GUARD gates — no flip (the promotion condition)

Re-scored with `scripts/calibration_verdict.py` on both arms. The incumbent's
verdicts (rubric 2.9, `determination = CALIBRATED-WITH-CAVEATS`, 9 scored,
target grade 7, 2 ledgered, **0 FAILs**):

| id | criterion | tier | incumbent |
|---|---|---|---|
| C1 | fuel-mix by class (grid-delivered) | load-bearing | PASS |
| C2 | system volume (gas/coal families) | load-bearing | PASS |
| C3a | mean LMP | load-bearing | CAVEAT (ledgered) |
| C3b | price duration/shape | load-bearing | PASS |
| C3c | price tail / scarcity (RT hourly) | supporting | CAVEAT (ledgered) |
| C4 | fleet hourly dispatch correlation | supporting | PASS |
| C6 | governance gate | protective | PASS |
| C7 | diurnal shape (D-1) | protective | PASS |
| C8 | forced-energy share (D-2) | protective | PASS |

**No criterion may flip to FAIL**, and no new caveat slot may be spent (the
ledger budget is 3 non-protective / 1 protective; 2 non-protective are already
spent by the owner's act of 2026-07-30 at caiso-145). A **protective** flip
(C6/C7/C8) is disqualifying for promotion in its own right.

### 4.4 RULE 14 DISPOSITION — stated BEFORE the result

**The published WECC directional ratings STAY IN even if the fit worsens.** They
are the measured limit; the symmetric TTC is an estimate. Per rule 14
`[R-ACCURATE]` and rule 1 `[R-STRUCT]`:

- A **worse** backcast under the published ratings is a **DISCOVERED BUG** —
  evidence that something else in the model was silently compensating for the
  loose reverse directions — and opens a root-cause investigation. It is
  **never** a reason to revert to the symmetric estimate, and the estimate is
  never restored to recover a number.
- A **better** backcast is not the reason the mechanism is right either; the
  reason is that the ratings are published and directional and the shipped TTCs
  are not.
- This disposition is fixed here, before any arm has solved, precisely so that
  it cannot be chosen after seeing the sign.

### 4.5 Promotion condition

Promotion is in scope under the owner's standing rule ("if structural integrity
improves but gates regress that may still be a keeper"). Concretely: promote iff
**L2 holds**, **L1/L3 show the mechanism live**, structural integrity improves
(S1/S2 — Path 15 becomes a path that binds), and **no criterion flips to FAIL
and no protective criterion flips at all**. If the mechanism proves INERT on
flows (L1 fails), it is registered as **INERT with flow evidence** and the matrix
cell records that, with no promotion.

---

## 5. Inherited owner-decision default flips — disclosed, not absorbed

Runs solved at current main carry, relative to the incumbent's original solve
basis: `retirement_rule` `legacy → pipeline` (owner decision D-1),
`entry_rate_limits` and `entry_commissioning_lag` armed (D-2),
`net_cone_forward_escalation → reindex_gross` (D-3a). These are **merged owner
decisions, not this session's choices and not tuning.**

Admissible on two grounds, both of which the attestation generator will
**ASSERT** rather than assume (modelled on `scripts/gen_caiso162_attestation.py`):

1. Every one is capacity-evolution / forward-entry machinery gated behind a hard
   `config.mode == "forecast"` check, and both bundles are `mode="backcast"`, so
   none can reach the dispatch LP.
2. Each holds the **same value in arm A and arm B**, so none can confound the
   A/B.

The generator fails if either condition breaks or any **undeclared** config delta
appears between the arms.

---

## 6. Discipline

- **Rule 16** `[R-ALLYEARS]`: `--year 2023 2024 2025`, one invocation per arm,
  one bundle per arm. Years sequential within a run (rule 12).
- **Rule 22** `[R-HOLDOUT]`: the holdout spend freeze
  (`frontend/data/backcast/holdout-freeze.json`) is ACTIVE and outranks every
  marker. No year outside 2023–2025 is solved, scored or registered, for any
  reason. CAISO holds **no** `complete` marker, so there is no
  `calibration-complete` re-key (D-5(b) applies to `complete` ISOs only) and this
  session writes no marker.
- **Rule 15** `[R-DASHBOARD]`: **both** arms are registered, keeper or not.
- **Rule 28(b)** `[R-MECH-MATRIX]`: the `measured_interface_limits` CAISO cell is
  updated with its tested verdict + evidence citation in **this** session, the
  header re-stamped, and §5.2 + `docs/calibration-log/caiso.md` updated.
- **CI**: solves run **in-session only** — never on a GitHub Actions runner
  (private repo, billed minutes).

---

## 7. What would falsify the arm

- **L2 violated** — a flow above a published cap in arm B: the limit is not
  reaching the LP as intended. Stop-the-line.
- **L1 not exceeded in arm A** — the symmetric TTCs were never the binding
  constraint anyway; the mechanism is INERT and the matrix records `I` **on flow
  evidence**, with the counts published.
- **Arm B byte-identical to arm A** with L1 exceeded — the same contradiction
  caiso-162 hit; would mean the limits are constructed but dropped downstream of
  `build_interface_groups`. Stop-the-line, not an INERT verdict.
- **A protective criterion (C6/C7/C8) flipping** — disqualifies promotion
  regardless of what S1–S4 do.
