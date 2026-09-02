# FINDING — capx D35: the FC-6 P2 gas leg re-scoped from a class label to the model's gas partition; neiso-t3's P2 row re-scored on committed artifacts

**Session:** D35 (capacity-expansion / Forecast Finalization track), branch
`claude/capx-d35-p2-scope-b5x2by`. **Date:** 2026-09-02. **HEAD at launch:** `07472e7c`
(origin/main). **Charter:** adjudicate what the gas-up driver leg (P2) SHOULD measure on a
25-year evolution pair whose combined-cycle class migrates to CCS, repair the checker so the
leg measures the model rather than its own construction, and re-score `neiso-t3`'s FC-6 P2
row artifact-only (zero solves), control-first, touching nothing beyond that row and the
FC-6 rollup it feeds.

---

## 0. PRE-STATEMENT — written and committed BEFORE the repaired checker ran

This section is frozen at its commit. §5 grades it.

### 0.1 The scope decision

**The P2 gas leg is re-scoped to TOTAL GAS-FIRED GENERATION — the sum over every class that
burns natural gas in the model's own fuel partition (`gas_cc`, `gas_ct`, `gas_cc_ccs`,
`gas_st`; `data/fuel/_shared.py::_GAS_FUEL_IDX`, the set of classes that pay the gas price).**
The per-class `gas_cc↓` key is retired from the gating list and kept only as a reported
control inside the row's evidence block. Reasons, in order of weight:

1. **It is the only candidate with a theorem behind it — even on the same-fleet pairs the
   leg was written for.** For a fixed feasible set, LP optimality of `x` under cost `c` and
   of `x'` under `c' = c + Δ` gives `Δ·(x' − x) ≤ 0`. A gas-price increase sets
   `Δ_g = hr_g × Δp_g ≥ 0` exactly on the gas-burning units and 0 elsewhere, so the
   heat-rate-weighted gas generation (gas fuel burn) weakly falls. Nothing in that inequality
   says anything about `gas_cc` alone: coal or imports displace the dearest gas MWh first
   (steam, CTs), and a per-class reading can move either way while the theorem holds.
   Total gas-fired MWh is the summary-visible proxy for burn (heat rates within the gas
   classes are close enough that a CT→CC reshuffle cannot invert it at the magnitudes the
   pair produces).
2. **The driver is a fuel-level input, so the response the leg is entitled to expect is
   fuel-level.** `gas_price_factor` scales the delivered gas price for every gas-burning
   unit. A CCS-retrofitted CC burns the same gas as its unabated host at a higher heat rate;
   labelling it a different "fuel" is a taxonomy convenience for the capacity ledger, not an
   economic boundary the gas price respects.
3. **On an evolution pair the class label is itself a response variable.** The CCS screen's
   fuel-cost penalty scales with the gas price, so the split of the CC family between
   `gas_cc` and `gas_cc_ccs` MOVES with the very driver the leg perturbs. Gating on one side
   of that split measures the retrofit screen's composition response — a legitimate model
   behaviour with no pre-registered sign — and reports it as a merit-order failure. That is
   the D23 family exactly: the instrument measuring its own construction.

**Candidates rejected, and why** (the charter's list, adjudicated rather than assumed):

- *The whole `gas_cc` family including CCS-converted units.* A label fix, not a claim fix:
  it still omits `gas_ct`/`gas_st`, it has no theorem behind it, and it inherits the same
  confound the moment a CT or steam unit's share moves. Subsumed by the all-gas scope.
- *The last year both worlds hold unabated CC.* A year search keyed on the outcome of the
  confound. On this pair that year is 2039, where the arm holds 4,000 MW of unabated CC to
  the base's 3,000 and the per-class key STILL reads a violation — so it rescues nothing,
  and as an instrument it lets the comparison year drift with the fleet rather than being
  fixed by the pair. Rejected.
- *A capacity-migration-aware construction* (per-MW utilisation of the unabated class, or a
  class-capacity-normalised comparison). Undefined whenever a class is absent in one world
  (this pair at 2050), and it compares the utilisation of DIFFERENT marginal units across
  worlds, which has no sign expectation. Migration-awareness belongs in the EVIDENCE — the
  row now reports the class split in both worlds and whether the legacy key would have been
  confounded — not in the gate.

**What stays exactly as it was:** the comparison year (the last common solved year), the
`coal↑` sub-check (scored only where the base holds coal at that year, as before), `price↑`,
`objective↑` (where the objective is available), the FAIL-on-sign rule, and the row's
ident/name (`P2` / `merit-order sign`).

**Meaningfulness on fleets that do NOT migrate (charter criterion b):** on a same-fleet pair
the all-gas sum is `gas_cc + gas_ct + gas_st`, the theorem above applies verbatim, and the
sign is BETTER founded than the old per-class key was. Nothing is lost; a class-level
response is still visible in the evidence block.

### 0.2 The artifact-only path

The committed golden-2 FC-6 arms carry `full_horizon_summary.json` + `run_config.json` only
(no per-year parquets, no caches — session-local, gitignored). The summary's
`generation_by_fuel_mwh` (D29 grain) is computed by `run_full_horizon.py` calling the
checker's OWN `_fuel_gen_mwh` and rounding to 0.1 MWh, so a summary-backed P2 is the
cache-backed P2 by construction for generation and load-weighted price. The one sub-check
the summary cannot carry is `objective↑` (no objective in the summary). In summary mode the
row reports it as not available at that grain and excludes it from the gating list — it is
NOT carried as a PASS from the committed row. (The committed row's own detail lists every
failing sub-check and names only `gas_cc↓`, so the committed cache-scored objective↑ was a
PASS; that is recorded here as a fact about the committed row, not scored.)

### 0.3 The pre-stated expectation

- **Control 1 (unmodified scorer, committed inputs):** reproduces the committed
  `forecast_verdict.json` with zero non-provenance diffs. Expected: exact.
- **Control 2 (legacy per-class key computed on the committed summaries):** reproduces the
  committed P2 detail `year 2050: wrong: gas_cc↓` exactly. Expected: exact (same function,
  same rounding).
- **The repaired leg on the committed pair, expected verdict: P2 PASS.** From the numbers
  already in golden-2 §7.1: total gas-fired generation at 2050 is 36.53 TWh (base) vs
  35.36 TWh (gas ×1.5) — falls; load-weighted price 79.16 → 93.95 $/MWh — rises; the base
  holds no coal at 2050 so `coal↑` auto-skips; `objective↑` is not available at summary
  grain. The class-migration evidence is expected to show the base at 0 MW / 0 TWh of
  unabated CC against the arm's 6,000 MW / 23.2 TWh, i.e. the legacy key flagged
  confounded.
- **Consequence for FC-6, expected:** the P2 row FAIL → PASS; the FC-6 category
  FAIL → CAVEAT (the surviving CAVEAT is T16-A's battery row, all-constant series
  [1.0, 1.0], untouched); `reasons` drops `FC-6 driver response FAIL`; `caveats` gains
  `FC-6 driver response`; determination stays **HOLD** on FC-1/2/3/4. Nothing else moves;
  if the recursive diff shows anything beyond those leaves the lane STOPS and routes.

Honesty note on the pre-statement: the charter itself quoted the all-gas 2050 numbers, and
this lane printed the arms' per-year class table while establishing the artifact-only path
(§0.2) before writing this section. The pre-statement's value is therefore NOT that the
outcome was unknown — it is that the scope was chosen on the theorem in §0.1, which would
have been the choice whatever the numbers said. Either outcome of the repaired leg was and
is valid: a surviving FAIL would have measured the model.

---

## 1. Charter discipline

Zero solves. No model parameter, threshold, band, expectation, keeper, shard, marker, or
backcast-namespace file touched. No `ScenarioConfig` field (rule 28 `[R-MECH-MATRIX]` duty
(c) does not fire; `check_mechanism_matrix.py` passes: integrity OK, 0 unresolvable anchors
beyond the ratchet, keeper stamps matched). No mechanism tested, so no matrix cell moves and
no `ev` stamp is minted — the NEISO shard is untouched. No workflow. The only solve-affecting
code in the repo that this lane touches is none: `check_forecast_invariants.py` is an
instrument (rule 27 `[R-PUSH]` applies — it is a core script ≥300 lines, edited locally and
pushed as on-disk bytes, blob-verified after push, §7). The committed golden-2 arm bundles,
attestation, DOF ledger, FC-5 disposition table and T16-A battery record are read, never
written. Everything below is measured from committed artifacts at HEAD `07472e7c` + this
branch.

## 2. The controls — both exact

| control | what it proves | result |
|---|---|---|
| **C1** — unmodified `forecast_verdict.py` at HEAD, on exactly the committed inputs (summary, invariants, T16-A battery, committed `paired_invariants.json`, hindcast, crossover, corridor + benchmark corridor, run_config, DOF ledger, attestation) | the scorer reproduces the committed `forecast_verdict.json` | **0 non-provenance diffs** (only `scored_at_sha` / `scored_at_date`; `cache_epoch` `706e7ba8e6582d42` unchanged) |
| **C2** — the retired per-class key (`coal↑` where base coal > 0, `gas_cc↓`, `price↑`), computed by the repaired module's own summary-evidence builder on the committed base and gasup150 summaries | the summary grain IS the cache grain the committed row was scored on | detail string **`year 2050: wrong: gas_cc↓` — byte-equal** to the committed row (pinned as `test_p2_legacy_key_on_committed_golden2_summaries_reproduces_the_committed_row`) |

C2 is the load-bearing one: it shows that switching the evidence source from the
session-local caches to the committed summaries changes NOTHING about what the legacy
instrument sees at 2050 (unabated `gas_cc` 0.0 MWh in base vs 23,186,992.2 MWh in the arm;
LW price 79.162 vs 93.951). Whatever the repaired leg then says is attributable to the
scope change alone.

## 3. The repair (what changed in the instrument)

`scripts/check_forecast_invariants.py`:

- **`GAS_FIRED_FUELS = {gas_cc, gas_ct, gas_cc_ccs, gas_st}`** — a literal mirror of
  `data/fuel/_shared.py::_GAS_FUEL_IDX` (the model's own "pays the gas price" partition,
  through `data/fleet/models.py::FUEL_TYPE_MAP`), kept literal for the same reason as
  `THERMAL_FUELS`, and pinned to the model's set by
  `test_p2_gas_scope_is_the_models_gas_partition` so drift fails loudly.
- **`check_p2_merit_sign_evidence(base_ev, up_ev)`** — P2 on pre-extracted evidence: at the
  last common year, `coal↑` (only where the base holds coal that year, unchanged), **`gas↓`
  on the gas-fired TOTAL** (replaces `gas_cc↓`), `price↑`, `objective↑` where both objectives
  exist. A sub-check whose inputs the grain lacks is listed in `data.not_scored` and named
  in the detail — never a PASS. The row's `data` block carries the 2050 per-class split in
  both worlds, the per-year gas-fired series over every common year, the scored /
  not-scored lists, and **`legacy_gas_cc_key`** (base/up MWh, `would_fail`,
  `disagrees_with_gas_fired_total`) — the retired key as a reported control, gating nothing.
- **`p2_evidence_from_run` / `p2_evidence_from_summary`** — the same evidence from a loaded
  cache or from a committed `full_horizon_summary.json`. The summary route is exact for
  generation and price by construction (`run_full_horizon.py` writes the energy block by
  calling this module's `_fuel_gen_mwh`); it carries no objective. Pre-D29 summaries (no
  energy block) contribute no year, so such a pair SKIPs rather than scoring on nothing.
- **`check_p2_merit_sign(base, gas_up)`** keeps its signature and delegates — every existing
  caller and test is unchanged.
- **`--paired-summaries BASE OTHER --pair-kind gas_up`** — the artifact-only CLI mode. P1
  (needs each arm's resolved config for the premise row) and P3 (needs the evolution
  ledgers) stay on `--paired` cache directories and the new mode refuses them with the
  reason.

`forecast_verdict.py` is **not changed**: `score_fc6` reads a paired row's status and detail
only, so the evidence block never gates
(`test_paired_p2_row_with_evidence_block_scores_on_status_only`).

## 4. The repaired leg on the committed pair — measured, full magnitude

**Row (from `--paired-summaries … --pair-kind gas_up --json`):**

> `P2 merit-order sign PASS — year 2050: all signs correct; gas-fired 36.53→35.36 TWh,
> LW price 79.16→93.95 $/MWh [not scored at this grain: objective↑]`

The 2050 gas-fired split, both worlds (TWh; base = golden-2 `706e7ba8`, up = gasup150
`65662ca1`):

| class | base | gas ×1.5 | Δ |
|---|---:|---:|---:|
| `gas_cc` (unabated) | 0.00 | 23.19 | +23.19 |
| `gas_cc_ccs` | 35.08 | 10.83 | −24.24 |
| `gas_ct` | 1.22 | 1.00 | −0.23 |
| `gas_st` | 0.23 | 0.35 | +0.12 |
| **gas-fired total** | **36.53** | **35.36** | **−1.16** |

The retired key reads +23.19 TWh on a class the base does not hold at all
(`legacy_gas_cc_key.would_fail = true`, `disagrees_with_gas_fired_total = true`); the fuel
it is a label for falls by 1.16 TWh. **The per-year series holds the sign in every one of
the 25 common years** — gas-fired base vs up, TWh: 2026 42.47→36.11 (the same-fleet dispatch
era, the largest response), 2030 36.17→35.80, 2035 31.90→31.36, 2040 31.96→30.61,
2045 33.31→31.82, 2050 36.53→35.36; the narrowest gap is 2032 (34.25→34.03, when both
worlds sit at ≈0.1 TWh of unabated CC and the split is nearly identical). Figure:
`docs/handoffs/figures/capx-d35-p2-gas-fired.svg` (the per-year totals and the 2050 class
split, both worlds).

`coal↑` auto-skipped (no base coal at 2050); `price↑` PASS; `objective↑` not scored at
summary grain — the committed cache-scored row listed only `gas_cc↓` as failing, so its
objective sub-check was a PASS there, recorded as a fact about that row and not scored here.

## 5. The pre-statement, graded

| §0.3 line | outcome |
|---|---|
| C1 exact | **held** (0 diffs) |
| C2 exact | **held** (byte-equal string) |
| repaired P2 = PASS on gas↓ / price↑, coal skipped, objective n/a | **held**, every sub-outcome as stated |
| legacy key flagged confounded (0 vs 6,000 MW / 23.2 TWh) | **held** (0.0 vs 23.19 TWh; `would_fail`) |
| FC-6 FAIL → CAVEAT via the P2 row; reasons/caveats move; HOLD unchanged; nothing else | **held** — the recursive diff is exactly five leaves (§6) |

No miss. The one thing the pre-statement did not predict in detail — that the sign would
hold in ALL 25 years rather than only at the comparison year — is reported as measured;
it was not a scored expectation, and the leg does not gate on it (the per-year series is
evidence, not a new gate).

## 6. The FC-6 re-score and the cross-lane re-grade audit

`paired_invariants.json` replaced in place (the D21/D26 precedent) as
`[P1, P1.premise, P2, P3]` with **P1, P1.premise and P3 carried byte-verbatim** (asserted
against the committed record before the write) and P2 the repaired row above. The scorer
then re-run on the same committed inputs as C1 with the new paired record. Recursive diff
against the committed verdict, provenance excluded — **five leaves, all FC-6 P2 or its
rollup**:

```
.categories.FC-6.rows[2].status   FAIL → PASS
.categories.FC-6.rows[2].detail   "P2 merit-order sign: year 2050: wrong: gas_cc↓"
                                → "P2 merit-order sign: year 2050: all signs correct; gas-fired
                                   36.53→35.36 TWh, LW price 79.16→93.95 $/MWh [not scored at
                                   this grain: objective↑]"
.categories.FC-6.status           FAIL → CAVEAT
.reasons                          drops "FC-6 driver response FAIL"
.caveats                          gains "FC-6 driver response"
```

| | committed (golden-2 + T16-A) | **D35 re-score** |
|---|---|---|
| FC-6 battery gate rows | CAVEAT (all-constant series [1.0, 1.0]) | **CAVEAT — untouched, byte-identical** |
| FC-6 paired P1 / P1.premise | PASS / PASS | PASS / PASS (carried verbatim) |
| FC-6 paired **P2** | **FAIL** (`gas_cc↓`) | **PASS** (gas-fired total ↓, price ↑) |
| FC-6 paired P3 | PASS | PASS (carried verbatim) |
| **FC-6 category** | **FAIL** | **CAVEAT** (the surviving caveat is T16-A's battery row) |
| determination | HOLD on FC-1/2/3/4/6 | **HOLD on FC-1/2/3/4** |

Every other category, row, reason, caveat and note is byte-identical. The STOP rule was not
triggered; the result publishes.

**Published (preserve-then-overwrite):** `results/ff-t3-neiso-golden/bau/forecast_verdict.json`
re-scored; `frontend/data/forecast/ff-verdicts.json` — the prior live `neiso-t3` preserved
byte-equal at **`neiso-t3-pre-p2scope`** (asserted), bare `neiso-t3` overwritten with the
re-score and the golden-2/T16-A `session_note` preserved verbatim and extended; 56 → 57
keys, exactly one moved and one added (asserted). `program-status.json` — NEISO `golden`
note appended and a top-level `d35_fc6_p2_scope` stamp (no provenance field names, so the
staleness checker cannot read it as a scoring event); every other block byte-identical
(asserted); `t3_determination` stays HOLD. The run-explorer sidecar
`neiso-2026-2050-t3-golden2-bau` carries I1–I14 only and is untouched; the preserved
verdict chain (`-pre-fc5`, `-pre-fc6`, `-pre-fc6repair`, `-prera-2026-08-31`) and the
pre-R-A bundle's own `paired_invariants.json` are frozen records and are not re-scored.
Backcast namespace untouched (plan §7.5).

## 7. What this changes for the other five ISOs' future FC-6 runs

**The leg is cross-ISO instrument code, and the repair applies to every ISO's next paired
gas-up run; it re-scores nothing today.** No ISO other than NEISO holds a committed P2 row
(the only `paired P2` rows in `ff-verdicts.json` are `neiso-t3` and its preserved
snapshots), so no other verdict moves. Going forward:

- **Non-migrating fleets** (a pair whose CC class never retrofits — every ISO's pair until
  its CCS screen clears): the gas-fired total is `gas_cc + gas_ct + gas_st`, and the sign
  is the LP comparative-statics inequality applied to exactly the units the driver
  touches. That is a STRONGER claim than the retired key — `gas_cc↓` alone was never
  guaranteed even on a same-fleet pair (coal or imports displace the dearest gas MWh
  first, which are steam and CTs, not CCs). A FAIL there is a real finding.
- **Coal-bearing ISOs** (ERCOT, PJM, MISO): `coal↑` still scores as before wherever the
  base holds coal at the comparison year; nothing about it moved.
- **Migrating fleets** (any ISO whose pair crosses a CCS conversion — CAISO/NYISO/PJM are
  the likely next cases given their carbon signals): the class split is reported in the
  evidence block and cannot confound the gate.
- **Rule 25 `[R-ISO-SCOPE]`** governs verdicts, not the checker: no NEISO-derived number
  enters the instrument (the scope is a set membership from the model's fuel partition, not
  a tuned quantity), so nothing crosses an ISO boundary.
- The summary-backed mode means any ISO's FC-6 P2 can be re-scored from its committed arm
  summaries without the session-local caches — the artifact-only path is now standing
  instrument capability, not a one-off.

Not changed and not this lane's: the P2 pairing itself (`gas_price_factor=1.5` vs the
validation program's "+$1/MMBtu" text — a pre-existing D21 construction, unaffected by the
scope), P1/P3, and the `objective` field's absence from the summary (a one-field producer
addition in `run_full_horizon.py` if a future lane wants objective↑ scoreable artifact-only;
routed, not done — it would change the committed summary shape).

## 8. Test and guard controls

| check | unmodified `origin/main` (`07472e7c`) | this branch | verdict |
|---|---|---|---|
| `tests/regression/test_forecast_invariants.py` | 56 passed / 1 skipped | **64 passed** / 1 skipped (8 added) | green |
| `tests/scoring/test_forecast_verdict.py` | 90 passed | **91 passed** (1 added) | green |
| `tests/scoring`, FULL | 6 failed / 1197 passed / 3 skipped / 1 xfailed | 6 failed / 1197 passed / 3 skipped / 1 xfailed | **identical set** |
| the 6 failing names | `test_ff_readiness_battery::{test_walk_inputs_trivial_single_year, test_resolve_report_no_hard_fail_full_horizon, test_ercot_confirmed_horizon_is_reported_not_failed, test_marker_state_reflects_committed_markers, test_build_registration_scorecard_no_iso_gate_open}`, `test_forecast_parity::test_all_six_keepers_resolve` | same six | **pre-existing, name-for-name** |
| `ruff check` + `ruff format --check` on every edited `.py` | — | clean | pass |
| `check_mechanism_matrix.py` | integrity OK | integrity OK, 0 unresolvable anchors beyond the ratchet, keeper stamps matched | pass |

The six reds were measured on the stashed (unmodified) tree of this same checkout, not
inferred; T16-A disclosed four of them on 2026-09-02 and two more `test_ff_readiness_battery`
rows have since gone red on `main` (they read the live board / keeper resolution, not
anything this lane writes — the board file this lane edits was stashed for that run and
they fail without it). **This lane introduces no new test failure and fixes none.**

New tests: `test_p2_gas_scope_is_the_models_gas_partition` (the literal mirrors
`_GAS_FUEL_IDX`), `test_p2_migration_pair_scores_the_gas_total_not_the_class_label` (the
golden-2 shape in miniature: PASS, legacy key confounded, objective named unscored),
`test_p2_fails_when_total_gas_fired_generation_rises` (the two constructions disagree the
other way too and the total wins — a FAIL path, so the leg is not one-directional),
`test_p2_same_fleet_pair_keeps_every_legacy_subcheck`,
`test_p2_scores_the_last_common_year_and_carries_the_series`,
`test_p2_summary_evidence_matches_run_evidence` (summary grain = cache grain; pre-D29
summary yields no year), `test_p2_summaries_cli_scores_gas_up_only`, and the C2 control
pinned against the committed golden-2 summaries; scorer side
`test_paired_p2_row_with_evidence_block_scores_on_status_only`.

## 9. What was written

| artifact | change |
|---|---|
| `scripts/check_forecast_invariants.py` | `GAS_FIRED_FUELS`; `_gas_fired_mwh`, `_p2_year_evidence`, `p2_evidence_from_run`, `p2_evidence_from_summary`, `check_p2_merit_sign_evidence`; `check_p2_merit_sign` delegates; `run_paired_summaries` + `--paired-summaries`; module docstring usage line (rule 27: edited locally, pushed as on-disk bytes, blob-verified) |
| `tests/regression/test_forecast_invariants.py`, `tests/scoring/test_forecast_verdict.py` | the tests above |
| `results/ff-t3-neiso-golden/bau/fc6/paired_invariants.json` | P2 row replaced; P1 / P1.premise / P3 byte-verbatim (asserted) |
| `results/ff-t3-neiso-golden/bau/forecast_verdict.json` | re-scored (five FC-6 leaves + provenance) |
| `frontend/data/forecast/ff-verdicts.json` | `neiso-t3` re-scored, `session_note` extended; prior preserved byte-equal at `neiso-t3-pre-p2scope`; 56 → 57 keys, one moved + one added (asserted) |
| `frontend/data/forecast/program-status.json` | top-level `d35_fc6_p2_scope` stamp + NEISO `golden` note appended; every other block byte-identical (asserted) |
| `docs/handoffs/forecast-validation-program-2026-07.md` | the P2 row of the paired-invariant table amended (dated) |
| `CHANGELOG.md` | entry |
| `docs/handoffs/figures/capx-d35-p2-gas-fired.svg` | the per-year gas-fired totals and the 2050 class split, both worlds |
| this finding | — |

**Not touched:** any `ScenarioConfig` field or default (rule 28 duty (c) does not fire; no
matrix row, no shard cell, no `ev` stamp — no mechanism was tested); the golden's solved
bundle, attestation, DOF ledger, FC-5 dispositions, T16-A battery record; the D26 P1
construction; the preserved verdict chain; the run-explorer sidecar; the pre-R-A bundle's
`paired_invariants.json`; `forecast_verdict.py`; the rubric (`forecast-determination-rubric.md`
FC-6 row 3 already says "P1 or P2 FAIL ⇒ FAIL" and names no per-class key, so it needed no
edit); anything in the backcast namespace; any workflow.

## 10. Reproduction record

```
# instruments at this branch, committed artifacts only, zero solves
B=results/ff-t3-neiso-golden/bau

# C1 — control: unmodified scorer (git stash) reproduces the committed verdict
PYTHONPATH=src .venv/bin/python scripts/forecast_verdict.py --tier t3 \
  --summary $B/full_horizon_summary.json --invariants $B/full_horizon_summary.json \
  --paired-invariants $B/fc6/paired_invariants.json \
  --driver-battery $B/fc6/driver-battery-neiso-2026-09-02.json \
  --hindcast-score results/hindcast/neiso-2021-2025-curve/NEISO/2ba529574d4982ea/score.json \
  --crossover-score results/hindcast/neiso-2023-2027-crossover-capxd14/NEISO/07e416f3f8072e7c/crossover_score.json \
  --corridor results/ff-corridor/dispositions/neiso-t3.json \
  --benchmark-corridor results/ff-corridor/benchmark-corridor-anchors.json \
  --run-config $B/run_config.json --dof-ledger $B/dof_ledger.json \
  --attestation $B/forecast_attestation.json --json-out <control>.json
# (recursive diff vs $B/forecast_verdict.json, provenance excluded: 0 leaves)

# C2 — the retired key at summary grain reproduces "year 2050: wrong: gas_cc↓"
PYTHONPATH=src .venv/bin/python -m pytest tests/regression/test_forecast_invariants.py \
  -k legacy_key_on_committed_golden2 -q

# the repaired leg
PYTHONPATH=src .venv/bin/python scripts/check_forecast_invariants.py \
  --paired-summaries $B/fc6/arms/base/full_horizon_summary.json \
                     $B/fc6/arms/gasup150/full_horizon_summary.json \
  --pair-kind gas_up --json          # → the P2 row now in $B/fc6/paired_invariants.json
# paired_invariants.json = [P1, P1.premise (verbatim), P2 (above), P3 (verbatim)]
# then the scorer command above with the new paired record → $B/forecast_verdict.json
# (recursive diff vs the committed verdict: exactly the five FC-6 leaves of §6)
```
