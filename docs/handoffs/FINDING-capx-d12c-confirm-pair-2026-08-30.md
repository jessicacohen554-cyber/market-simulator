# FINDING — D12-C: the arming confirmation pair, measured closed-loop

_2026-08-30 · capacity-expansion (Forecast Finalization) track, lane D12-C
ARMING CONFIRMATION PAIR · chartered by the owner's Q10 ruling (r#15 sitting,
2026-08-30, `docs/handoffs/capx-director-ledger-2026-08.md` §0l.2/§3):
**"CONFIRM-PAIR, THEN ARM. Lane D12-C chartered: ONE arm-vs-control A/B on the
ERCOT T1-H leg at the registered posture with the TWO fields
(`entry_margin_exhaustion` + `entry_forward_reserve_leg`) as the single
logical delta, measuring the closed loop D12 open-loop-predicted. Arming
auto-executes on a confirming record (both flip to ERCOT forecast defaults,
honestly described); a contradiction does NOT arm and comes back to the owner
at full magnitude."** Branch `claude/capx-d12c-confirm-pair-oji8wv`.
Predecessors: `FINDING-capx-d12-scarcity-basis-2026-08-30.md` (+ its PREDECL)
and `FINDING-capx-d11r-entry-volume-rule-2026-08-30.md` §3 (the A/B protocol
repeated here and the committed control bracket)._

---

## 1. Pre-declared expectations and tolerances (§1 COMMITTED BEFORE EITHER SOLVE COMPLETED)

**Timing note (the S-4 discipline, as in D12's PREDECL):** everything in this
§1 was written and committed BEFORE the control or arm invocation was
launched. Seen at write time: the two predecessor findings and their committed
artifacts (`entry_signal_l1_dual_replay_ercot.json`,
`entry_signal_l1b_allocator_ercot.json`, `entry_volume_rule_ab_ercot.json`),
the committed d11r bundle sidecars, and the code seams. NOT seen: any output
of the D12-C invocations (none existed). The expected arm cache key below was
computed ex ante from the committed control `run_config.json` plus the two
flags via `ScenarioConfig.cache_key()` — an arithmetic derivation, not a
solve.

**The pair.** ERCOT `ercot-2021-2025-realized` T1-H leg at the registered
posture, same HEAD (`origin/main` @ `9c3f221` + this lane's probe-extension
commit), both invocations solved by this session, concurrently (rule 12),
years sequential within each:

- CONTROL — bare `run_capacity_hindcast.py --iso ERCOT --start-year 2021
  --end-year 2025`, out-dir `…-t1h-d12c-control`.
- ARM — same plus `--entry-margin-exhaustion --entry-forward-reserve-leg`,
  out-dir `…-t1h-d12c-armed`.
- Probe: `scripts/probes/entry_volume_rule_compare.py` extended with
  `--expect-delta entry_margin_exhaustion,entry_forward_reserve_leg` (the
  two-field delta gate; hard-fails on anything else). Artifact:
  `results/calibration/entry_confirm_pair_d12c_ercot.json`.

### 1.1 Gates (stop-the-line, before any verdict is read)

- **G-1 control integrity.** The control reproduces the committed registered
  bracket EXACTLY: cache key `28cef3500ec1fd9e`; RM path
  19.00 → 8.54 → 14.65 → 25.19 at the reported 2 dp; the additions table
  verbatim (wind 0.350 / solar 17.987 / gas_cc 9.000 / gas_ct 7.571 / storage
  5.000 GW); per-step decisions equal to the committed
  `entry_volume_rule_ab_ercot.json` control block row-for-row. Any drift is a
  stop-the-line finding (HEAD drift on the fleet side), NOT a baseline — no
  A/B verdict is read on a drifted control.
- **G-2 posture.** `run_config` delta exactly
  {`entry_margin_exhaustion`: False→True, `entry_forward_reserve_leg`:
  False→True} (probe-gated); expected arm cache key **`f061b2646bfaac8b`**
  (computed ex ante as above; D12 §8's `1eda234b96a95fee` is the
  pinned-GLOBAL-default + leg hash, a different posture — verified ex ante
  against `ScenarioConfig()` before declaring). A different arm key with a
  clean two-field delta is posture drift: stop the line.

### 1.2 Verdict criteria (ALL must land inside tolerance for a CONFIRMING record)

The record CONFIRMS iff V-1 … V-5 all hold. A miss on any single one is a
CONTRADICTION: nothing arms, the divergence is decomposed at full magnitude,
and the owner re-decides. Margin recomputation tolerance wherever a margin is
quoted: **$0.05/MW-yr** (D12 §4's own reproduction error against the
dual-replay rows — declared here, ex ante, as the numeric basis; every
committed margin this pair tests sits ≥ $5.7k from zero, so $0.05 flips no
sign and maps to < 1 tranche of walk arithmetic).

- **V-1 — the phantom step builds nothing.** The arm's entering-2025 step
  builds ZERO gas (gas_cc = 0 AND gas_ct = 0). Every committed open-loop
  estimate agrees the one-object margin is negative there on both measured
  states (walk state: "2025 nothing"; the D11-R arm's thinner state:
  −$117.4k / −$101.5k under B). Exact, no tolerance.
- **V-2 — the gas half of the exhaustion rule is LIVE at the state-clean
  step.** Entering-2022 is the one step where the live closed-loop state ≡
  the walk state (first decision off the common 2021 seed), so the walk's
  arithmetic must reproduce nearly exactly: gas_cc ∈ **[750, 1,250] MW**
  (walk: 1,000, ± 1 tranche of 250 MW) and gas_ct ≤ **250 MW** (walk: 0,
  + 1 tranche) — both strictly below their caps (3,000 / 1,571). This is the
  first live record of ERCOT gas entry stopping on its own exhausted margin.
- **V-3 — nothing that was right changes.** Entering-2023 gas_cc = 3,000
  (cap; B margins +$3.1M — no repricing can exhaust them) and entering-2024
  gas_cc ∈ **[2,500, 3,000]** (the walk caps it at 3,000 with the last
  tranche still +$19.9k and declining ≈ $13k/tranche, so a modestly fatter
  live state may stop 1–2 tranches short; both measured open-loop states
  agree cc is carried at 2024 — walk +$46k → +$19.9k, D11-R-arm state
  +$343.6k).
- **V-4 — terminal ledger RM.** Expected at the walk bracket
  **[18.08, 18.71] %**; CONFIRMING band **[15.0, 21.0] %**. Derivation, ex
  ante: the walk's RM accounting rides the registered trajectory with
  thermal/storage firm deltas ONLY (`entry_signal_l1b_allocator_ercot.json`
  `rm_trajectory` — VRE deltas excluded by construction, its "ELCC deltas
  cancel" note), so the live closed loop adds two effects the bracket cannot
  carry: (i) live VRE/storage exhaustion feedback, whose measured magnitude
  under the D11-R live arm was **−3.17 pp** (its entire terminal delta vs
  control — in-window gas was identical); (ii) a richer entering-2023 state
  (the live 2022 solar cut lands COD 2023) that can carry gas_ct past the
  walk's 1,500 MW stop toward its 3,000 cap, worth ≤ **+1.8 pp** in-window.
  Band = bracket − 3.2 / + 2.3, i.e. [14.9, 21.0], rounded to [15.0, 21.0]
  with the top held ≥ 1.0 pp below the nearest committed alternative anchor.
  Both committed alternatives lie OUTSIDE the band: 22.02 (exhaustion under
  basis A, live) and 25.19 (shipped bang-bang) — the tolerance cannot absorb
  a phantom (one 3 GW cap-slam ≈ 3.6 pp in-window) or a dead gas half.
- **V-5 — the reason matches the arithmetic.** Recomputed from the arm's own
  emitted `screen_signal_diag` dumps with D12 §4's exact method (energy leg
  `Σ max(base+adder−vc, 0)`, basis-B leg `Σ max(base+adder−vc, adder)`, fixed
  costs from `resolve_new_entry_costs`), the arm's entering-2025 gas margins
  are NEGATIVE for both techs at walk start (± $0.05) — the step builds
  nothing FOR D12's reason, not coincidentally.

### 1.3 Reported expectations (recorded ex ante; NOT verdict criteria)

- **R-1 gas bands** (attached evidence, never the verdict — rule 1
  [R-STRUCT]; the charter's own framing): both scored gas band errors shrink
  vs the shipped control (|err| gas_cc < 8.756, gas_ct < 3.879 GW; actuals
  0.244 / 3.692). Committed anchors, all quoted ex ante: B+bang-bang
  open-loop 6.000 / 4.571 (err 5.756 / 0.879); B+exhaustion walk-state
  totals 7.000 / 1.500 (err 6.756 / 2.192); shipped control 9.000 / 7.571
  (err 8.756 / 3.879); D11-R live exhaustion arm 12.000 / 10.571. The closed
  loop decides where in that fan it lands.
- **R-2 the B-2 cobweb**, re-measured and reported whatever it shows.
  Expected ex ante: the −/+/+ sign pattern survives; first swing near the
  D11-R arm's −12.65 pp (the 2022 VRE/storage exhaustion carries over,
  possibly damped — fewer 2022 gas tranches leave solar exhausting later);
  middle swing SHRINKS from the arm's +5.20 pp toward the offline walk's
  +1.59 pp (the 2022 gas cut lands COD 2024); expected RM path shape
  ≈ 19.00 → 6.3–8.5 → 7–11 → V-4's band.
- **R-3 entering-2024 gas_ct**: state-dependent and admissible either way —
  the walk (fatter, VRE-held state) builds 0; the D11-R arm's thinner state
  priced ct at +$310.7k (would build). Reported with its own dump-recomputed
  margins; only cc is gated (V-3).
- **R-4 entering-2023 gas_ct**: walk says 1,500 (1,000 at the 8 GW sweep);
  the live richer state can carry it up to the 3,000 cap. Reported, with the
  in-window RM consequence already inside V-4's band arithmetic.
- **R-5 storage/wind**: expected qualitatively as the D11-R arm behaved
  (iron_air-only second slot or exhaustion below 5,000; wind entry > 0 in
  2023 plausible); li-ion still never builds (L-3/D-3 territory, not this
  lane's). Reported.

### 1.4 What confirmation triggers (pre-authorized by Q10 — no further ask)

On a CONFIRMING record, IN THIS SESSION: both fields flip to ERCOT forecast
defaults via the ISOConfig `default_scenario_overrides` route (the FFR-9C
stage-B pattern), with the Q10 ruling cited verbatim in the citation block;
the ERCOT matrix shard cells move (`entry_margin_exhaustion` O →
K-forecast-armed; `entry_forward_reserve_leg` ERCOT cell likewise) with this
pair as evidence; sister-ISO cells stay U (rule 26); both bundles register on
the FORECAST namespace (`ercot-2021-2025-realized-t1h-d12c-{control,armed}`)
with `run_config.json` committed. The armed posture is recorded honestly: the
margin-exhaustion volume rule with its gas half live on a one-object forward
margin — i.e., ERCOT forecast entry becomes exhaustion-bounded on the
entering year's own expected-ORDC surface for every candidate class. On a
CONTRADICTING record: nothing arms, cells stay O, this finding reports the
divergence decomposed at full magnitude, and the owner re-decides.

---

## 2. Control gate (measured) — G-1 and G-2 PASS EXACTLY

Both invocations solved by this session at one HEAD (`origin/main` @
`e65bbba` + the §1 pre-declaration commit `bf5e08f`; no solve-path file
differs from the §1 commit), concurrently, years sequential within each;
both solved [2021, 2023, 2024, 2025], bridged [2022], zero leakage
violations.

- **G-1**: the control reproduces the committed registered bracket EXACTLY —
  cache key `28cef3500ec1fd9e`; RM path 19.00 → 8.54 → 14.65 → 25.19 to the
  basis point; per-step decisions row-for-row (2022: gas 3,000/1,571 + solar
  4,946.6; 2023: gas 3,000/3,000 + solar 5,550 + iron_air 3,000 + flow
  2,000; 2024: gas 3,000/3,000 + solar 6,000; 2025: nothing); scored
  additions verbatim (0.350 / 17.987 / 9.000 / 7.571 / 5.000 GW). Zero HEAD
  drift on the fleet side — every committed bracket is a valid anchor.
  Deeper still: the control bundle's own dumps reproduce the committed
  dual-replay basis-B margins to the cent on every step (+45,930.9 /
  +8,642.8 / +3,147,581.4 / +3,105,235.2 / −10,730.3 / −42,669.7 /
  −135,210.3 / −117,875.4 $/MW-yr) — the whole margin machinery is
  byte-stable at this HEAD.
- **G-2**: the probe (`--expect-delta` two-field gate) verifies the delta is
  exactly {`entry_margin_exhaustion`, `entry_forward_reserve_leg`}, each
  False→True; the armed cache key is **`f061b2646bfaac8b`** — the ex-ante
  §1.1 prediction, bit-equal. Artifact:
  `results/calibration/entry_confirm_pair_d12c_ercot.json`.

## 3. The armed record (measured)

Ledger (armed): 2022 bridge — solar 4,946.6, **NO gas**; 2023 — gas_cc
3,000 (cap) + gas_ct 1,571 (its ladder cap at zero prior ct build) + solar
6,979 + iron_air 2,750; 2024 — gas_cc 3,000 (cap) + gas_ct 500 (exhausted
sub-cap) + solar 3,250; 2025 — **nothing**. RM path **19.00 → 6.05 → 6.79 →
15.84**; swings **−12.95 / +0.74 / +9.05** (B-2 SURVIVES: −/+/+ with
amplitude, the probe's own test). Scored decision-basis additions: wind
0.350 / solar 16.666 / **gas_cc 6.000** / **gas_ct 2.071** / storage 2.75
GW.

Dump-recomputed one-object margins at walk start (the §1.2 method,
validated on the control to ≤ $0.05):

| entering (armed state) | Σadder | gas_cc B | gas_ct B | decision |
|---|--:|--:|--:|---|
| 2022 (≡ seed state) | 124,033 | **+45,930.9** (bit-equal to committed) | +8,642.8 | **0 / 0** — walked out by solar competition (§4.2) |
| 2023 | 3,045,919 | +3,147,581 | +3,105,235 | 3,000 (cap) / 1,571 (ladder cap) |
| 2024 (thin state) | 685,833 | +637,248 | +603,754 | 3,000 (cap) / 500 (exhausted) — expectation-carried |
| 2025 | 106,927 | **−34,524** | **−20,898** | **nothing — V-5's prediction, exactly** |

## 4. Adjudication — the record CONTRADICTS on ONE pre-declared window; NOTHING ARMS

### 4.1 The scorecard

| check | declared (§1, ex ante) | measured | verdict |
|---|---|---|---|
| G-1 control | exact bracket | exact, to the cent | **PASS** |
| G-2 posture | two-field delta; key `f061b2646bfaac8b` | exact | **PASS** |
| V-1 2025-step gas | 0 / 0, exact | 0 / 0 | **PASS** |
| V-2 2022-step gas | cc ∈ [750, 1,250]; ct ≤ 250; both sub-cap | ct 0 ✓; **cc 0 — OUTSIDE [750, 1,250]** | **FAIL (cc window)** |
| V-3 2023/2024 cc | 3,000; [2,500, 3,000] | 3,000; 3,000 | **PASS** |
| V-4 terminal RM | [15.0, 21.0] | 15.84 | **PASS** |
| V-5 2025 margins negative | both, ±$0.05 method | −34,524 / −20,898 | **PASS** |
| R-1 gas bands improve (non-gating) | cc err < 8.756; ct err < 3.879 | cc 5.756 (6.000 GW — exactly the charter's anchor); ct 1.621 (2.071 GW) | confirmed |
| R-2 B-2 (non-gating, report) | −/+/+ survives; middle shrinks toward +1.59 | −12.95 / +0.74 / +9.05 | confirmed |
| R-3/R-4/R-5 (report) | state-dependent | 2024 ct 500 on +603.8k start; 2023 ct ladder-capped 1,571; iron_air-only 2,750; wind 0.350; no li-ion | reported |

**Verdict: CONTRADICTING**, mechanically, per §1.2's own rule ("a miss on
any single one is a CONTRADICTION"). Q10's auto-arm executes only on a
fully confirming record; this is not one. **Nothing arms. Both fields stay
default-OFF. The ERCOT matrix cells stay `O`. The owner re-decides.**

### 4.2 The one divergence, decomposed at full magnitude

The miss is the entering-2022 gas_cc build: **0 MW vs the declared window
[750, 1,250]** (the offline B-walk's 1,000 ± 1 tranche). What it is and is
not:

1. **Not a construction defect.** The armed run's entering-2022 start margin
   is **bit-identical to the committed control-state value (+$45,930.9)** —
   same seed state, same instrument, same arithmetic. The screen priced cc
   exactly as D12's committed reconstruction says it should.
2. **Not the phantom, and not a regression toward either committed
   alternative.** V-1/V-5 hold exactly (the post-tight step builds nothing,
   for D12's reason, at the declared tolerance); terminal 15.84 is 6.2 pp
   below the A-exhaustion arm (22.02) and 9.4 below shipped (25.19).
3. **What it is: the live walk competes candidates the offline walk never
   fielded.** The L-1b machinery — the source of the "cc 1,000" prediction —
   held VRE at shipped and walked ONLY {gas_cc, gas_ct} + storage (its
   declared offline-harness artifact). The LIVE walk fields every candidate
   class (D11-R §1.2 item 5). At 2022, solar wins the early tranches and
   builds to its full 4,946.6 (in the D11-R basis-A arm, 4,571 MW of
   reserve-carried gas went first and solar exhausted at 1,250; here the
   order inverts), repricing the signal so cc's +45.9k margin is exhausted
   before any cc tranche clears. **Direction: MORE exhaustion by the same
   mechanism on the same one-object margin.** §1 named this exact artifact
   for V-4's RM derivation ("VRE held at shipped offline while the live
   pair exhausts VRE") and failed to carry it into V-2's window — a
   pre-declaration calibration error of the same class as D12's owned
   P-D3, except discovered after the arm ran, so it stands as a miss and
   the contradiction branch executes. The tolerance is not widened after
   the fact (rule 21): that discipline is worth more than this arming.

### 4.3 What the record establishes for the owner's re-decision (evidence, not a recommendation to bypass the protocol)

Every expectation **the Q10 charter itself pre-declared** is confirmed on
the closed loop: the exhaustion walk on the consistent leg lands where
D12's reconstruction pointed (terminal 15.84 = the walk bracket carried
down by exactly the pre-named live-VRE feedback, inside the ex-ante band);
**no phantom gas** at the entering-2024/2025 steps (2024's 3.5 GW is
expectation-carried at +$603–637k start margins on its own thin state —
D12 §4.2's case, live; 2025 builds nothing on negative margins); the
scored gas bands improve with **gas_cc landing exactly on the charter's
6 GW anchor** and gas_ct |err| 3.879 → 1.621; B-2 re-measured and
surviving. The gas half of the exhaustion rule is LIVE — 2024 ct stops at
500 MW sub-cap on a repriced margin, and 2022 gas is margin-bounded
(harder than predicted). The sole divergence from the pre-declared record
is one window whose derivation imported the offline walk's restricted
candidate set. The owner may judge that confirming-in-substance and direct
the arming, or hold; **this lane executes the protocol as written and arms
nothing.**

## 5. Rule compliance

- **Rule 1 `[R-STRUCT]`** — the verdict is the pre-declared protocol's,
  not the bands' (which improved and are reported as attached evidence
  only); the contradiction is declared even though every structural claim
  of D12 is supported, because the declared tolerance is the adjudicator.
- **Rule 12 `[R-PARALLEL]`** — the two invocations ran concurrently, years
  sequential within each; `git ls-remote` deconfliction at session start
  (no other capx branch); nothing larger launched.
- **Rule 13 `[R-MEASURED]`** — no measured outcome enters any model path;
  both runs are forecast-machinery T1-H on the registered training window.
- **Rule 21 `[R-DOF]`** — zero parameters anywhere; the confirmation
  tolerance was committed and PUSHED (bf5e08f) before either solve
  launched, and is not revised after the record.
- **Rule 22 `[R-HOLDOUT]`** — solves span 2021 seed + 2023–2025 (2022
  bridged) only; the freeze's tier scope untouched; `--holdout-authorized`
  never passed; harness governance banner verified on both logs.
- **Rule 15/24** — both bundles registered on the FORECAST namespace with
  `run_config.json` committed
  (`ercot-2021-2025-realized-t1h-d12c-{control,armed}`); backcast registry,
  keeper shards, `calibration-complete.json`, offer curves, commitment
  bridges untouched.
- **Rule 25/26** — every number is ERCOT's; no sister-ISO cell moves.
- **Rule 28(b)** — both tested cells' evidence updated in this session with
  the pair's citation; **status stays `O`** per the contradiction branch.
- **Rule 27 `[R-PUSH]`** — all edits local; pushes carry on-disk bytes with
  post-push blob verification on every ≥300-line file; no CI workflows
  added; all solves ran in-session.

## 5b. Session-observed operational notes (not findings)

- The first launch attempt deadlocked: two background launcher shells each
  waited on `pgrep -f regenerate_clean.py`, which matched the OTHER
  launcher's own command line (both embedded the string). Killed and
  relaunched directly; the solves themselves were unaffected.
- `git push` through the session's egress proxy failed 5× mid-upload
  (connection reset / HTTP 500, tiny pack, HTTP/1.1 included) until the
  remote branch existed, then succeeded first-try. Recorded for the next
  lane's expectations; not a pack-size issue.

## 6. Reproduction

```
# the two arms (bare invocation = the registered posture; TWO flags differ)
uv run python scripts/run_capacity_hindcast.py --iso ERCOT --start-year 2021 --end-year 2025 \
    --out-dir results/hindcast/ercot-2021-2025-realized-t1h-d12c-control
uv run python scripts/run_capacity_hindcast.py --iso ERCOT --start-year 2021 --end-year 2025 \
    --entry-margin-exhaustion --entry-forward-reserve-leg \
    --out-dir results/hindcast/ercot-2021-2025-realized-t1h-d12c-armed

# score each, then the A/B probe (posture-gated: exactly the two fields may differ)
uv run python scripts/score_capacity_hindcast.py --bundle <each bundle>
uv run python scripts/probes/entry_volume_rule_compare.py \
    --arm results/hindcast/ercot-2021-2025-realized-t1h-d12c-armed \
    --control results/hindcast/ercot-2021-2025-realized-t1h-d12c-control \
    --expect-delta entry_margin_exhaustion,entry_forward_reserve_leg \
    --out results/calibration/entry_confirm_pair_d12c_ercot.json
```
