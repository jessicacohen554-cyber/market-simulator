# FINDING — D12: the entry screen's scarcity basis, adjudicated

_2026-08-30 · capacity-expansion (Forecast Finalization) track, lane D12
SCARCITY-CONSISTENT DELTA BASIS · chartered at director refresh #13 under the
r#8 owner-ratified sequencing (strictly after D11-R —
`docs/handoffs/FINDING-capx-d11r-entry-volume-rule-2026-08-30.md`), named as
the successor rung by `docs/FINDING-entry-signal-forward-expectation-2026-08-25.md`
§4. **This report is the INPUT to the owner's held Q8 arming decision**
(r#13 sitting: `entry_margin_exhaustion` arming HELD until this lane
adjudicates the scarcity basis). Branch `claude/capx-d12-scarcity-basis-xq50qu`.
**No LP was solved: the adjudication is exact arithmetic on committed objects,
and it is decisive. One default-OFF construction shipped
(`entry_forward_reserve_leg`); NO default changed; nothing armed.**_

---

## 0. The one-paragraph answer

**The screen's margin should carry ONE scarcity object — the entering year's
own expected-ORDC adder, the same instrument invocation that already prices
the energy leg — and the shipped realized-r reserve leg is a cross-year
phantom that fires exactly at the post-tight-year steps.** The committed
record proves both halves without a solve: at entering-2024 the registered
control's gas margins are **negative under the entering year's own
expectation on both offline bounds** (gas_cc −$10,730, gas_ct −$42,684
/MW-yr; committed dual-replay rows, reproduced here from the dumps to
$0.05), yet the shipped screen built 6 GW — the prior year's realized adder
alone flips both signs; the D11-R exhaustion arm's entering-2025 step
repeats the pattern on its own dumps (−$118.6k/−$111.4k under both bounds,
6 GW built) with an implied realized-leg annuity ≥ 4× the largest value the
consistent forward leg could possibly supply (Σadder = $26.6k). Everywhere
else the basis choice changes **nothing**: no committed row's sign moves
between r-none and the expected-adder leg in any step, and the
margin-exhaustion walk re-run on the committed dumps with the consistent leg
reproduces the committed r-none walk **tranche-for-tranche** (same builds,
same final adders, terminal 18.71/18.08 %). Consequences: under the
consistent basis the bang-bang ledger RM path is **unchanged** (the
2024-step gas lands COD 2026, outside the ledger window) while the scored
gas bands improve (gas_cc 9→6 GW, gas_ct 7.571→4.571; |err| 3.879→0.879 for
CT), and **the margin-exhaustion rule's gas half goes live** — the leg
reprices with the walk, and the D11-R within-walk closure
`r_walk = max(0, r + Δadder)` becomes the exact identity
`r_walk = adder_current` with zero new walk code. Shipped as the default-OFF
`ScenarioConfig.entry_forward_reserve_leg` (byte-identical off: default key
`603c2498bf71d21d` unmoved, both registered keys reconstruct). **Recommend:
adopt the forward leg as the screen's margin and arm it TOGETHER with
`entry_margin_exhaustion` — the owner decides (§7 card).**

---

## 1. The two scarcity objects, precisely

The ERCOT thermal ENTRY margin at the registered posture
(`28cef3500ec1fd9e`) is `Σ_t max(S_next(t) − vc, r(t)) − fixed`, where the
two terms come from different years AND different constructions:

- **Energy leg** `S_next` — the entering year's lookahead signal
  (`runner._lookahead_reprice_signal`): base merit price on the entering
  year's net load **plus the model's own expected-ORDC adder** (FFR-8A
  `capacity_screen_scarcity_restoration`, armed) — a forward, pro-forma
  object.
- **Reserve leg** `r` — the **prior solved year's realized post-solve ORDC
  adder** (`screen_reserve_value_enabled` with
  `ercot_thermal_as_endogenous=False`: runner threads `overlay_adder` into
  both tiers of `prior_results.reserve_price_signal{,_slow}`) — a backward,
  realized object. After a bridge it is TWO years stale (entering-2023
  reads the 2021 solve's adder).

The FFR-9B diagnosis noted the timing asymmetry in passing ("energy-leg
lookahead into Y+1 vs reserve-leg realized year Y, noted") and established
the offline method: the true realized leg is **not recoverable offline**
(hourly fleet availability is not persisted), so committed replays bracket
it with two bounds — `r_none` (no leg) and `r_dump_adder` (the entering
year's own expected adder). That second bound **is** the consistent basis
this lane adjudicates. The RETIREMENT screens are a different case and are
untouched: their energy leg is the realized year's prices too, so realized-r
there is an internally consistent backward pair (rule 19).

## 2. The candidate bases (charter task 1)

| basis | construction | a developer's pro-forma reading | forward regeneration (rule 13) |
|---|---|---|---|
| **A (shipped)** | energy on S_next (forward), r = prior-year realized adder | no pro-forma does this: forward energy curve, but AS revenue floored at last year's realized RTORPA outturn — an accounting hybrid with no market story | regenerates (model-produced), but prices the WRONG year's scarcity: the vintage year's outturn as the delivery year's floor |
| **B (scarcity-consistent forward)** | r = the entering year's OWN expected adder from the SAME instrument invocation; hourly value ≡ `adder(t) + max(base(t) − vc, 0)` | the textbook expected-ORDC pro-forma: every MW earns the expected reserve price every hour (in merit through the energy adder, out of merit as RTORPA/RTOFFPA — Nodal Protocols §6.5.7.5 pays the delivery year's reserve state), plus energy rents | fully forward: the adder is a function of the entering-year fleet/demand state and responds to changed conditions (measured: control vs arm entering-2024 adder means $6.66 vs $45.95 — same year, different fleets) |
| **C (r-none)** | no reserve leg (the L-1b offline walk's construction) | under-counts a real revenue stream (ERCOT pays reserves) | bracket, not a candidate for the screen |
| **D (fully realized / disarm)** | energy AND reserve both from the prior year's realized surface | "last year's outturn as the forecast" — naive-expectations entry, the textbook cobweb; a real behavioural theory, already measured live (terminal 40.24) | regenerates; a coherent backward pair, but a different whole-surface theory, not a repair of A |
| **D′ (composition repair)** | the fwd-expectation §4 named successor: composed signal with a tail-free delta | same principle as B (one scarcity object per construction) applied to the SIGNAL side; orthogonal — the composition is unarmed at the registered posture | exact arithmetic on existing objects; remains the successor IF the composition lane reopens |
| **A+Δ (D11-R within-walk closure)** | r_walk = max(0, r_realized + Δadder) | within-year-only repair; deliberately does not answer the cross-year question (D11-R §1.2 item 4) | under B this closure is not stacked or discarded — it becomes **exact** (§5.3) |

## 3. Pre-declared expectations vs outcomes (the honesty test)

Recorded in-session **before** the corresponding numbers were extracted —
committed verbatim, with its timing notes, as
`docs/handoffs/PREDECL-capx-d12-scarcity-basis-2026-08-30.md` (S-4
discipline). Scored:

| # | pre-declaration | outcome |
|---|---|---|
| P-D1 | entering-2022/2023 gas margins positive under BOTH bounds; basis choice changes nothing pre-tight | **CONFIRMED** (+45.9k/+5.8k and +3.15M/+3.11M; no sign moves) |
| P-D2 | entering-2025 negative under both bounds (control built nothing) | **CONFIRMED** (−136.3k/−122.6k) |
| P-D3 | basis-B bang-bang changes ONLY the 2024 decision (6 GW gas → 0); terminal ledger RM drops toward ~21–22 % | **HALF-CONFIRMED, HALF-WRONG, owned in-session**: the decision half is confirmed; the RM half was wrong — thermal COD lag is 2, so a 2024-step decision lands 2026, OUTSIDE the ledger window, and the ledger path is IDENTICAL (25.19 terminal). Corrected in a dated addendum BEFORE any dump computation |
| P-D4 | under B the exhaustion walk's gas half is live; 2024 gas never starts; 2022 gas_ct may damp | **CONFIRMED on the live half; detail misses reported**: on the L-1b cross-year walk state gas_cc builds 3 GW at 2024 (the walk's prior years built less, so its 2024 state is genuinely tighter — a different object than the committed-state bang-bang, which decides NO gas); at 2022 the walk stops gas_cc at 1 GW and gas_ct at 0 — identical to the committed r-none walk |
| P-D5 | gas-inertness per basis: A inert (measured), B live at exactly the post-tight step, C ≈ B at 2024/2025, D measured | **CONFIRMED** |
| P-D6 | Σadder(entering-2024) ~$5k so B ≈ C where A diverges most | **structural claim CONFIRMED, magnitude WRONG**: control Σadder(2024) = $58.4k (the ~$5k guess came from the treatment arm's tail table — different fleet); the margin increment is still ≈ 0 (gas_cc +$0.0, gas_ct +$14.2) because the adder is already in S for in-merit hours |
| P-D7 | (recorded before opening the arm's dumps) the arm's 2025 6 GW gas build shrinks or vanishes under B — expected at least partly realized-r-carried | **CONFIRMED sharply**: −$118.6k/−$111.4k under r-none, −$117.4k/−$101.5k under B — entirely realized-r-carried; under B it never starts |

## 4. Exact arithmetic on committed objects (charter task 2)

**Provenance and verification.** Dumps: the four committed
`screen_signal_diag_*.npz` of the registered t1h-refresh bundle (key
`28cef3500ec1fd9e`; the d11r-control bundle's dumps are **byte-identical**,
max abs diff 0.0 on every array — verified) and the exhaustion arm's own
dumps (`cc7bbe1170db65c2`). Var-costs from the screen's own construction at
the committed step gas prices (3.41/2.04/1.69/3.03 $/mmBtu — the
dual-replay artifact's recorded values); fixed costs from
`resolve_new_entry_costs` (cc $147,155.5, ct $128,111.6 /MW-yr). Every
recomputed margin cross-checks the committed
`entry_signal_l1_dual_replay_ercot.json` shipped-signal rows to **≤ $0.05
/MW-yr** (that artifact's own machinery is validated against the FFR-9B
replay identities), and the decomposition identity
`max(S−vc, adder) = adder + max(base−vc, 0)` holds to 1e-10 on every step.

### 4.1 The registered posture: per-year, per-candidate screen margins ($/MW-yr)

| entering | tech | vc $/MWh | energy leg E (r-none) | margin, C (r-none) | margin, **B** (r = entering-year adder) | margin, A (shipped) → decision |
|---|---|--:|--:|--:|--:|---|
| 2022 | gas_cc | 23.483 | 193,086 | **+45,931** | **+45,931** | >0 → 3,000 MW (cap) |
| 2022 | gas_ct | 34.190 | 133,885 | **+5,774** | **+8,643** | >0 → 1,571 MW (ladder) |
| 2023 | gas_cc | 14.852 | 3,294,737 | **+3,147,581** | **+3,147,581** | >0 → 3,000 MW |
| 2023 | gas_ct | 21.860 | 3,233,347 | **+3,105,235** | **+3,105,235** | >0 → 3,000 MW |
| **2024** | gas_cc | 12.647 | 136,425 | **−10,730** | **−10,730** | **>0 → 3,000 MW — the flip is the realized leg's** |
| **2024** | gas_ct | 18.710 | 85,428 | **−42,684** | **−42,670** | **>0 → 3,000 MW — same** |
| 2025 | gas_cc | 21.089 | 10,855 | −136,300 | −135,210 | <0 → none |
| 2025 | gas_ct | 30.770 | 5,528 | −122,584 | −117,875 | <0 → none |

Σadder (the largest annuity the consistent forward leg could possibly add,
$/MW-yr): **124,033 (2022) · 3,045,919 (2023) · 58,370 (2024) · 10,236
(2025)**; adder means $14.16 / $347.71 / $6.66 / $1.17. The realized leg is
not persisted offline (FFR-9B protocol note), but its sign-flip
contribution is bounded from the decisions: at entering-2024 it supplied
**≥ $10,730 (cc) and ≥ $42,684 (ct)** per MW-yr. Basis A ≠ basis B in
exactly one registered step — the one immediately after the modeled tight
year — and the entering-2023 leg is doubly anachronistic (the 2021 solve's
adder, across the 2022 bridge).

### 4.2 The exhaustion arm's own dumps — the second phantom, and the response test

| entering (arm state) | Σadder | tech | margin C (r-none) | margin **B** | live arm decision (A) |
|---|--:|---|--:|--:|---|
| 2024 (thinner fleet: solar 1,250 & storage 3,000 upstream) | 402,522 | gas_cc | **+343,590** | **+343,590** | 3,000 MW — genuinely expectation-carried |
| | | gas_ct | +310,691 | +310,717 | 3,000 MW |
| **2025** (after its tight 2024) | **26,632** | gas_cc | **−118,613** | **−117,372** | **3,000 MW — realized-r-carried entirely** |
| | | gas_ct | −111,433 | −101,479 | **3,000 MW — same** |

Two things measured at once. **(i) The forward leg responds to conditions**
(rule 13's test, passed by construction and now by measurement): the same
entering year, 2024, carries adder mean $6.66 on the control fleet and
$45.95 on the arm's thinner fleet — the expectation moves with the state.
**(ii) The arm's entering-2025 build is the phantom at full magnitude**: the
implied realized-leg annuity (≥ $111–119k) exceeds the **entire** possible
consistent-forward annuity (Σadder $26.6k) by ≥ 4×. This is the D11-R §4
"inexhaustible floor" measured from the margin side: the walk's Δadder
closure could only move the leg by within-walk deltas of a $1–3-mean adder,
so the realized level, booked from the arm's own tight 2024, carried 6 GW of
gas the arm's own forward view priced ~$110k/MW-yr under water.

### 4.3 Basis D, where committed (dual-replay `dual_prior_solve` rows)

Entering-2024: gas_cc +22,583 / gas_ct +350 (r-none; +73,177 / +52,192 with
the adder leg) — the realized 2023 duals carry the real 2023 scarcity, which
is why the disarm arm also built 2024 gas. Entering-2025: −68,049/−79,791 —
nothing builds. (2022/2023 blocked: no committed 2021 hourly duals.) Basis D
is a coherent backward theory measured live (terminal 40.24); it is not a
repair of A and is not re-adjudicated here.

## 5. Walks and anchors (charter task 2's second deliverable)

### 5.1 The B-walk on the committed dumps ≡ the committed C-walk, exactly

The L-1b probe's own machinery (StepState, cross-year deltas, caps, RM
accounting — imported, not re-implemented) re-run with the thermal margin
`Σ max(sig − vc, adder_current) − fixed` (basis B, the leg walked):
**identical builds tranche-for-tranche** to the committed
`entry_signal_l1b_allocator_ercot.json` r-none arms at both VRE-budget
sweeps — 2022 gas_cc 1,000; 2023 gas 3,000/1,500 (1,000 at 8 GW) + iron_air
3,000 + CAES 2,000; 2024 gas_cc 3,000; 2025 nothing; same tranche counts,
same final adder means, same RM trajectory (**terminal 18.71 / 18.08 %**).
The consistent leg is small and well-behaved everywhere; **every difference
between bases anywhere in the committed record is the phantom.**

### 5.2 Open-loop anchors and bands

| construction | terminal ledger RM % | scored gas bands (cc / ct, GW; actual 0.244 / 3.692) |
|---|--:|---|
| shipped bang-bang (A, committed) | 25.19 | 9.000 / 7.571 |
| **B + bang-bang (open-loop)** | **25.19 — IDENTICAL** (the 2024-step 6 GW lands COD 2026, outside the ledger window; nothing else changes — VRE/storage screens carry no reserve leg, so solar 6,000 stays and no other 2024 candidate clears) | **6.000 / 4.571** (|err| 8.756→5.756, **3.879→0.879**) |
| disarm raw duals (D, committed) | 40.24 | 9.000 / 5.571 |
| forward-expectation (committed) | 40.38 | 9.000 / 7.571 |
| exhaustion live under A (D11-R) | 22.02 | 12.000 / 10.571 |
| **B + exhaustion (open-loop walk, committed dumps)** | **18.71 / 18.08** (≡ the committed L-1b C-walk) | arm's 2025-step 6 GW never starts (§4.2) → 9.000 / 7.571 open-loop |
| L-1b offline walk (C, committed) | 18.71 / 18.08 | — |

The post-window consequence of B + bang-bang is real but outside the ledger:
2026 enters with 6 GW less gas (≈ −7 pp of RM at the ~80 GW 2025-step peak).
Open-loop honesty: the closed-loop B trajectory (feedback through the
2025/2026 solves) is not reconstructed here; D11-R §3.3 measured the
direction of such feedback (thinner fleet → more later entry support).

### 5.3 The rule-19 statement: nothing stacks, and the D11-R closure becomes exact

Under B the walk seeds the leg at the zero-additions adder, so the EXISTING
new_entry closure `r_walk = max(0, r + Δadder)` evaluates to
`max(0, adder₀ + (adder_now − adder₀)) = adder_now` — the within-walk shift
is no longer a cross-basis approximation but the identity. **No walk code
changed; nothing is stacked; one leg, walked.** The D11-R within-year
closure is thereby subsumed-when-armed, not contradicted: unarmed (basis A)
it keeps exactly its D11-R semantics.

## 6. Adjudication

**Basis B is the screen's margin.** The grounds, in rule-1 order — market
structure, never the bands (the band improvements in §5.2 are attached
evidence, not the reason):

1. **One scarcity object per construction** (rule 19, and the same principle
   the fwd-expectation finding §4 applied to the signal side): the shipped
   margin's max() crosses both years and objects; B closes it with an object
   the same instrument invocation already computes.
2. **Market fidelity**: ERCOT pays RTORPA/RTOFFPA on the **delivery year's**
   real-time reserve state; a pro-forma projects AS revenue off the same
   forward view as its energy curve. The hybrid A has no market story —
   backward-looking entry as a behavioural theory is basis D, whole-surface,
   already measured and separately adjudicated.
3. **Rule 13**: both A and B are model-produced and regenerate forward, so
   admissibility does not discriminate; B additionally passes the
   responds-to-changed-conditions test by measurement (§4.2.i).
4. **Zero DOF** (rule 21): no new construction, no coefficient — the swap is
   which committed object two arguments read.

**No live A/B was run, deliberately** (charter step 3's "if, and only if"):
the offline arithmetic recomputes the screens' own margins exactly (the
replay machinery is identity-validated), the only decision it cannot
close — the closed-loop trajectory — is precisely the posture whose arming
the owner has HELD, and D11-R already supplies the live exhaustion A/B under
basis A. Running the armed pair now would front-run Q8 and spend the shared
heavy-solve budget (a MISO heavy solve was running at charter).

**Out of scope, flagged**: the retirement screens' backward pair is
internally consistent and untouched, but it is a *naive-expectations* pair;
whether the retirement margin should also go forward is a separate,
unchartered question — it should not ride this arming.

## 7. The Q8 decision card (the owner decides; this lane only recommends)

**The question re-opened**: arm `entry_margin_exhaustion`, and on which
margin?

| option | what it does | what it re-opens / costs |
|---|---|---|
| **(a) RECOMMENDED: arm `entry_margin_exhaustion` + `entry_forward_reserve_leg` together** (one T1-H confirmation pair first if the owner wants the closed loop measured before arming — a single arm-vs-control at the registered posture with the TWO fields as the single logical delta) | the D11-R volume rule with its gas half live on a one-object margin; the walk leg reprices via the exact identity (§5.3) | the closed-loop trajectory is open-loop-predicted here, not measured; if the owner wants it measured first, that pair is the one remaining solve this rung needs |
| (b) arm `entry_margin_exhaustion` alone (basis A) | the honest description D11-R §5 gave: margin-exhaustion for VRE/storage, bang-bang for gas — the gas half stays decided by a leg this finding adjudicates as a phantom | bakes the phantom into the armed posture; the arm's own record shows it manufacturing 6 GW of 2025 gas against a −$110k forward margin |
| (c) arm `entry_forward_reserve_leg` alone | repairs the bang-bang screen's margin (2024-step 6 GW gas gone; CT band |err| 0.879); allocator stays bang-bang | leaves D-1's measured overshoot ownership unaddressed; the volume rule waits |
| (d) hold both | status quo | the two-scarcity-objects defect stays live in every T1-H/forecast leg; D-1 stays bang-bang |
| (e) reject the forward leg | — | rejects the only construction under which the exhaustion rule's gas half can bind; a rejection on trajectory/band grounds would be rule-1-inadmissible — the case here is structural |

**Recommendation: (a).** The structural case for each half is
construction-independent (D11-R §5 for the volume rule; §6 here for the
basis), the composition is exact with zero new code, and the two halves were
held apart only by this adjudication. Evidence: §4 (the two phantom flips,
committed), §4.2.i (the forward leg responds), §5.1 (the consistent leg
changes nothing that was right), §5.3 (no stacking). Both fields are
default-OFF and cache-key-registered; arming is one `run_config` posture
plus the ISOConfig/default route the owner prefers, and per rule 26 the
verdicts are ERCOT's — the five sister cells enter as `U`.

## 8. What shipped (all default-OFF; no default changed; byte-identity proven)

| piece | where |
|---|---|
| field | `ScenarioConfig.entry_forward_reserve_leg = False` (scenarios.py; cache-key-registered at default per the nyiso-119 discipline; `__post_init__` refuses without `entry_lookahead_reprice` and without `screen_reserve_value_enabled`; coerced off in backcast) |
| capture | `runner._screen_signal_for`: per-entering-year adder captured into `entry_reserve_adders` (armed only; the npz dump keeps its ORIGINAL gate — arming alone emits no dumps) |
| threading | `PriorYearResults.entry_reserve_price_signal`, set per entering year and rebound at the top-of-iteration seam exactly like `entry_reprice` |
| consumption | `evolve.evolve_fleet`: the NEW-ENTRY call's two reserve tiers read the adder when armed-and-captured (both tiers, mirroring the shipped one-overlay wiring); retirement legs untouched; degrade-to-shipped when an entering year has no captured adder |
| CLI / record | `scripts/run_capacity_hindcast.py` `--entry-forward-reserve-leg` / `--no-…`; `FromConfig(cast=bool)` in the hindcast meta (FFR-3R) |
| tests | `tests/unit/model/test_entry_forward_reserve_leg.py` — 10 tests: registration / both refusals / coercion / cache-key at default and armed; the expected-ORDC revenue identity; the walk-closure identity; evolve routing (armed swaps entry legs only; unarmed and uncaptured byte-identical) |
| byte-identity | default key `603c2498bf71d21d` unmoved; registered keys `28cef3500ec1fd9e` (control) and `cc7bbe1170db65c2` (arm) reconstruct from their committed `run_config.json`; armed hashes `1eda234b96a95fee` |
| regression | 313 entry/capacity + 607 config + 204 pipeline tests pass; `check_mechanism_matrix.py` clean (anchor digits repaired via its own `--fix-anchors`) |
| repair (pre-existing, reported) | `tests/unit/pipeline/test_pipeline_prior.py::test_all_cross_year_keys_present` was ALREADY FAILING on main — D11-R added `entry_reprice` to `PriorYearResults` without extending the contract set. Repaired here for both fields, labeled in the test |
| matrix (rule 28) | base row `entry_forward_reserve_leg` + a cell line in EVERY shard (ERCOT `O`/`fc O` with this finding; five sisters `U`); the ERCOT `entry_margin_exhaustion` cell carries a dated D12 stamp pointing Q8 at this card |

## 9. Rule compliance

- **Rule 1 `[R-STRUCT]`** — adjudicated on which object is real (§6); the
  band improvements are reported as attached evidence and are not the
  grounds; option (e) records that a trajectory-grounds rejection would
  itself be inadmissible.
- **Rule 13 `[R-MEASURED]`** — no measured outcome enters any path; both
  candidate legs are model-produced; the direction of every result was
  pre-declared before computation (§3), including two owned misses.
- **Rule 19 `[R-ONE-MECH]`** — the leg is swapped, never stacked; the
  D11-R walk closure becomes the identity rather than a second mechanism;
  the field refuses postures where it would be a second mechanism.
- **Rule 21 `[R-DOF]`** — zero coefficients; the shipped construction reads
  two existing committed objects.
- **Rule 22 `[R-HOLDOUT]`** — no year solved, scored or registered anywhere
  (no LP ran at all); freeze untouched; no backcast file touched.
- **Rule 24/26/28** — the field serializes into `run_config.json` and the
  hindcast meta; every measured number is ERCOT's, sisters enter `U`; the
  matrix row + all-shard cells landed with the mechanism in this branch.
- **Rule 27 `[R-PUSH]`** — every ≥300-line file edited locally and pushed as
  on-disk bytes with post-push blob verification; no CI workflow added; no
  work offloaded to CI.
- **Rule 12 `[R-PARALLEL]`** — no solve launched; the shared ≤2-heavy cap
  was left to the running MISO leg. Deconfliction: `ercot-241` backcast
  branch checked at session start; no backcast surface touched.

## 10. Reproduction

```
# the entire adjudication (no solve): recompute §4 from the committed dumps
uv run python - <<'PY'
# see the finding's §4 provenance: dumps under
#   results/hindcast/ercot-2021-2025-realized-t1h-refresh/ERCOT/28cef3500ec1fd9e/
#   results/hindcast/ercot-2021-2025-realized-t1h-d11r-exhaustion/ERCOT/cc7bbe1170db65c2/
# margins: E = sum(max(base+adder-vc, 0)); basis B = sum(max(base+adder-vc, adder));
# vc from HEAT_RATE_BINS/VOM at gas 3.41/2.04/1.69/3.03; fixed from resolve_new_entry_costs.
PY

# committed cross-checks
uv run python -m pytest tests/unit/model/test_entry_forward_reserve_leg.py -q
uv run python scripts/check_mechanism_matrix.py

# the arms the arithmetic reads (already committed; listed for provenance)
#   results/calibration/entry_signal_l1_dual_replay_ercot.json   (margins, both bounds)
#   results/calibration/entry_signal_l1b_allocator_ercot.json    (the C-walk the B-walk reproduces)
#   results/calibration/entry_volume_rule_ab_ercot.json          (the live A/B under basis A)
#   docs/handoffs/ffr-9b/entry-screen-replay.json                (replay-machinery validation)
```
