# FINDING — capx D37: the NEISO T1-H re-solved with the D40 Net ICR lever ARMED (owner ruling Q28), against a paired one-field control — THE POST-WAVE YEARS NOW SCORE: the armed positions land +0.37 / −3.26 / +0.14 points of the real FCA 14/15/16 where the control reads +21.13 / −1.44 / −5.34, superseding D40's own contaminated bound; and the lever's effect is INVISIBLE in the FC-3 band list it was routed through — retirements flip from +51 % over to −27 % under, storage stays at exactly 0.000 GW and refutes this lane's headline prediction by its own falsifier

**Lane:** capx D37 — the re-run three chains waited for (GOLDEN-2 routed it; D40 built the
lever and declared the post-wave years UNSCOREABLE until this run; owner ruling **Q28** armed
the lever FOR THIS MEASUREMENT ONLY). Branch `claude/capx-d37-neiso-t1h-armed-o98iy1`.
**Two solves, NEISO only**, years sequential within each invocation and the two invocations
concurrent (rule 12). **No `ScenarioConfig` field was added or moved and the SHIPPED DEFAULT
of `neiso_net_icr_requirement` STAYS `False`** — verified at HEAD (`scenarios.py:14043`) and
this branch touches nothing under `src/`. Rule 28 not triggered (D40 landed the lever's matrix
row and six cells). No keeper, shard or marker; the backcast namespace untouched.

**The frozen pre-declaration** (`PREDECL-capx-d37-neiso-t1h-armed-2026-09-02.md`, pushed
**before** the solve started, blob-verified 365 lines / sha256 `1d32c222…`) is graded at full
magnitude in §5, misses included. Its launch record is
`docs/handoffs/d37/ADDENDUM-launch-2026-09-02.md`.

## 0. Verdict (one paragraph)

**The lever works, and it does not work on the thing it was routed through.** On a fleet the
**armed screens themselves produced** — the measurement D40 §2 reading 3 said was the only
admissible one — the NEISO adequacy position lands **+0.37 / −3.26 / +0.14 points** of the
real FCA 14/15/16, against the paired control's **+21.13 / −1.44 / −5.34**. The +21-point
2023 denominator artifact D33 attributed is **gone**, and 2025 closes to a seventh of a point.
This **supersedes D40's own projection of the same rows** (−1.40 / −20.25 / −12.42): that
projection priced a fleet the OFF requirement produced, D40 labelled it a bound rather than a
forecast, and the re-solve shows the bound was **pessimistic by 17–12 points** in the
post-wave years — suppressing the wave lifts the fleet back to the requirement instead of
leaving it short. Capacity revenue moves from the control's **$0.00 / $54.11 / $143.83** to
**$17.27 / $89.17 / $29.52** against a real **$24.01 / $31.33 / $31.09**; **D40's expectation
that the arm would OVER-pay at the 2023 entry ($55.20) is refuted — it under-pays ($17.27)**,
for the mechanism this lane pre-stated (a fuller retained fleet sits longer on a steep curve),
though further than predicted. **But FC-3 does not move, and the determination does not
move.** Cumulative retirements go 7.566 → 3.645 GW against a 4.997 GW actual: **+51.4 % over
becomes −27.1 % under — still FAIL, sign flipped**, the same shape D27 measured in MISO for
the same structural reason (*a requirement repair RATIONS a channel, it does not AIM it*).
`false_retire` more than halves (0.583 → 0.263) and still fails; `unit_recall_gt300` is
**unchanged at 0.667**; oil (1.208 GW actual) and gas_ct (0.319) stay at **exactly 0.000 GW in
both arms**. The floor binds **only under the arm** (6 coal units / 682.8 MW in 2024, 13
gas_cc / 1,240.5 MW in 2025, against **zero in every control year**) — and the 2024 coal
retention is a **one-year delay, not a save**. Two mechanism findings the pre-declaration did
not anticipate: the arm **re-timed** the gas_st wave (2022 → 2023 + 2025) rather than
preventing it, leaving that fuel's total at **exactly 1.438 GW in both arms**; and **entry
FELL** rather than rose (gas_cc 2.0 → 1.0 GW, gas_ct 0.5 → 0.0). **This lane's headline
prediction is refuted by the falsifier written for it**: storage entry stays at **exactly
0.000 GW** against a 0.642 GW actual in both arms, so the storage channel is shut by something
other than capacity revenue — a **new identified object, routed, not tuned**. **Recommendation
(§7): do NOT flip the shipped default on this evidence; keep the lever ARMED for the NEISO
forecast lane's next measurement.** Determination **HOLD** on both arms, unchanged.

## 1. What ran, and the one-field A/B

| | ARM | CONTROL |
|---|---|---|
| run id | `neiso-2021-2025-realized-t1h-d37-armed` | `neiso-2021-2025-realized-t1h-d37-control` |
| cache key | `313ba0612435b963` | `5925e67c572a910f` |
| `neiso_net_icr_requirement` | **True** (run config only) | **False** |
| `entry_screen_diagnostics` | True | True |
| everything else | HEAD default | HEAD default |
| solved / bridged | [2021, 2023, 2024, 2025] / [2022] | identical |
| wall time | ~6 min | ~6 min |

Both `run_config.json` files record the arm (rule 24), verified. Both out-dirs were empty at
launch and `CACHE_ROOT` is redirected there, so no pre-existing bundle could be served at any
key; neither key collides with a committed NEISO bundle.

**Why the control was worth its compute, measured rather than asserted.** D27 declared its
confounds and ran one leg. Here HEAD had moved since the committed baseline
(`neiso-2021-2025-realized-mystic-rescore`, 2026-08-22), and the movement is **real and
material**: the control's own cumulative retirements are **7.566 GW where that committed
bundle scored 7.332**, and its 2024 wave is 4,769.4 MW where the committed bundle's was
5,891.9 MW. **Every attribution below is made ARM-vs-CONTROL, never arm-vs-committed.**

## 2. The result the three chains were waiting for — the post-wave years, scored

Positions are on the FCA's own raw convention (R-B), computed from each run's own ledgers via
the identity `firm = peak × (1 + reserve_margin)` — verified at source to be exactly the
`accredited_firm_capacity_mw` that enters the position (`runner.py:4186, 4250`), so the
numerator is the model's own, not a reconstruction. Prices are HEAD's committed vintage
curves, which the instrument **self-checks** by reproducing the real FCA clearing prices to
the cent at the real positions (D33 §2's cross-validation).

| yr (FCA) | firm CTL | firm ARM | req CTL | req ARM | pos CTL | pos ARM | **real** | gap CTL | **gap ARM** | $ CTL | $ ARM | **$ real** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 (14) | 30,935.1 | 31,221.0 | 24,146.5 | 29,636.0 | 1.2564 | 1.0488 | 1.0451 | **+21.13** | **+0.37** | 0.00 | 17.27 | 24.01 |
| 2024 (15) | 25,665.9 | 30,612.5 | 24,948.9 | 30,347.5 | 1.0262 | 1.0080 | 1.0406 | −1.44 | **−3.26** | 54.11 | 89.17 | 31.33 |
| 2025 (16) | 26,153.7 | 30,075.0 | 26,638.9 | 28,865.2 | 0.9834 | 1.0382 | 1.0368 | −5.34 | **+0.14** | 143.83 | 29.52 | 31.09 |

Readings, each measured:

1. **The denominator artifact is gone on an armed-produced fleet.** 2023 goes +21.13 → +0.37
   points. This is the D33 attribution confirmed by the only instrument that could confirm it.
2. **2025 is the row that could not be projected, and it closes.** D40's contaminated bound
   read **−12.42** points; measured, it is **+0.14**. The reason is structural and was the
   open question: suppressing the 2024 wave leaves a fleet that the floor holds **at** the
   requirement, so the post-wave position recovers instead of collapsing. **D40's caveat was
   right to refuse to forecast these rows, and the bound it published was pessimistic.**
3. **2024 is now the WEAKEST armed year (−3.26 pts), and it was the strongest control year
   (−1.44).** The arm makes this row worse. Its mechanism is visible in the trajectory: the
   control's 2024 fleet had already collapsed (reserve margin 0.058) so it happened to sit
   near the real position for the wrong reason — two errors cancelling, the same pattern D40
   §3 identified in its failing LOYO fold.
4. **Capacity revenue: better in aggregate, and D40's over-payment expectation is refuted.**
   The control's $0.00 (2023) and $143.83 (2025) readings are gone. At the 2023 entry the arm
   pays **$17.27 against a real $24.01** — an **under**-payment, where D40 projected $55.20
   over. This lane pre-stated the correction's direction and mechanism ("a fuller fleet, a
   longer position, and ISO-NE's MRI curve is steep there") but bracketed it at $20–55 and
   still called it an over-payment; **the direction of the correction is a hit and the
   absolute call is a miss** (§5, P7). 2025 lands $29.52 vs $31.09 — within $1.57.

## 3. What the lever did to the FC-3 bands — the failure is RELOCATED, not closed

| band | CONTROL | ARM | actual | movement |
|---|---|---|---|---|
| `retire.total_gw` | **FAIL** 7.566 (+51.4 %) | **FAIL** 3.645 (−27.1 %) | 4.997 | sign **FLIPPED** |
| `retire.false_retire` | **FAIL** 0.583 | **FAIL** 0.263 | band 0.15 | halved, still fails |
| `retire.unit_recall_gt300` | **FAIL** 0.667 | **FAIL** 0.667 | band 0.70 | **unchanged** |
| `add.by_tech.storage` | **FAIL** 0.000 | **FAIL** 0.000 | 0.642 | **unchanged at zero** |
| `add.by_tech.gas_ct` | **FAIL** 0.500 | **FAIL** 0.000 | 0.162 | fell |
| `add.by_tech.gas_cc` | SKIP 2.000 | SKIP 1.000 | 0.000 | fell |
| `add.by_tech.wind` | **FAIL** 2.000 | **FAIL** 2.000 | 0.225 | unchanged |
| `add.by_tech.solar` | **PASS** 2.056 | **PASS** 2.056 | 1.947 | unchanged |
| `add.shares.gas_ct` | **PASS** | **FAIL** | 0.054 | **the ONE band the arm makes worse** |

FC-3 fails **10** bands in the control and **11** under the arm. Per-fuel retirements (GW):

| fuel | actual | CTL | ARM | reading |
|---|---:|---:|---:|---|
| gas_cc | 1.884 | **5.335** (+183 %) | **1.414** (−25 %) | the arm's real repair |
| gas_st | 0.480 | 1.438 | **1.438** | **identical — RE-TIMED, not prevented** |
| coal | 0.846 | 0.791 | 0.791 | unchanged, near actual |
| **oil** | **1.208** | **0.000** | **0.000** | channel shut in both arms |
| **gas_ct** | **0.319** | **0.000** | **0.000** | channel shut in both arms |
| biomass | 0.262 | 0.002 | 0.002 | unchanged |

**Mechanism 1 — the exits were RE-TIMED, and the gas_st total is the proof.** The control
exits 1,438.2 MW of gas_st in the 2022 bridge year. Under the arm that wave is inadmissible
(the published resolver needs no peak, so it binds in a bridged year — the pre-declaration's
P2 falsifier tested exactly this and did not fire), and 2022 falls to **1.8 MW**. But the same
fuel then exits **1,152.2 MW in 2023 and 285.9 MW in 2025 — totalling 1,438.1 MW, the control's
figure to within 0.1 MW.** The lever moved *when*, not *whether*.

**Mechanism 2 — the floor binds only under the arm, and its 2024 retention is a one-year
delay.** `floor_retained` is empty in **every control year**. Under the arm it holds **6 coal
units / 682.8 MW in 2024** and **13 gas_cc / 1,240.5 MW in 2025**. The 2024 coal retention is
not a save: **the same 682.8 MW of coal exits in 2025.** Terminal reserve margin
0.009873 → 0.161288.

**Mechanism 3 — entry FELL.** gas_cc 2.0 → 1.0 GW and gas_ct 0.5 → 0.0 GW; wind and solar are
identical. The pre-declaration reasoned that higher capacity revenue would pull entry forward;
the opposite happened, because the arm **retains** a fuller fleet rather than rebuilding one,
so the later positions are long and entry is not called. This also refutes D40 §4's pre-stated
"entry EARLIER" half (its "retirements HARDER" half is confirmed).

## 4. The storage prediction, refuted by its own falsifier

The pre-declaration's §3 P5 called storage **"the interesting one"**: storage entry is a value
stack including RA capacity value, NEISO has a capacity market, and the arm takes the capacity
price from $0.00 to ~$42/kW-yr — so storage entry should become **strictly positive, 0.1–1.5
GW**. It wrote its own falsifier: *"storage stays exactly 0.000 GW ⇒ the storage channel is
shut by something other than capacity revenue, which is a new identified object."*

**Measured: storage entry is exactly 0.000 GW in BOTH arms** (`storage_firm_mw` 1726.95 and
`storage_power_mw` 1924.2, identical in every year of both runs, zero `storage_additions`),
against a **0.642 GW actual**. The falsifier fires. The capacity price at the 2023 position did
rise from $0.00 to $17.27/kW-yr, so the revenue term moved and the channel did not.

**This is the lane's headline miss and it is a real finding: NEISO's storage-entry channel is
insensitive to the capacity-revenue term.** It is ROUTED to the director as a new identified
object, not tuned. It is the NEISO analogue of D27's MISO result — the requirement-side lever
cannot open a channel whose gate is elsewhere — and the run's committed
`entry_screen_diagnostics` rows (5 per evolved year in both arms, the D36/D39 precondition's
payoff) are the instrument for attributing it to a term.

## 5. The frozen pre-declaration, graded at full magnitude

| # | prediction | measured | grade |
|---|---|---|---|
| **P1** | 2024 wave collapses; 0.2–1.5 GW, central 0.6; falsifier > 4.0 GW | **108.7 MW** | **HIT direction, MISS magnitude** (below bracket); falsifier silent |
| **P2** | 2022 bridged wave shrinks, 0.0–1.31 GW; falsifier = unchanged 1,440.0 | **1.8 MW** | **HIT** (in bracket, at its floor); falsifier silent ⇒ **the resolver DOES bind in a bridged year**, as claimed |
| **P3** | `retire.total_gw` 1.0–3.5 GW, central 2.0; band FAIL with sign flipped | **3.645 GW**, FAIL, **sign flipped** | **HIT** on band + sign + direction; **MISS on magnitude** by 0.145 GW (4 % outside) |
| **P4a** | `false_retire` 0.3–1.2 GW / ~40 %, still FAIL | **0.959 GW / 26.3 %**, FAIL | **HIT** (GW in bracket; fraction better than predicted) |
| **P4b** | `unit_recall_gt300` FALLS to 0.17–0.50, FAIL | **0.667, unchanged**, FAIL | **MISS on movement**, hit on band |
| **P4c** | oil and gas_ct stay exactly 0.000 GW | **both 0.000** | **HIT**; falsifier silent |
| **P5a** | **storage strictly positive, 0.1–1.5 GW**; falsifier = stays 0.000 | **exactly 0.000** | **REFUTED — falsifier fired** (§4) |
| **P5b** | gas_ct entry UP or flat, 0.4–1.5 GW, stays FAIL | **0.000 GW**, FAIL | **MISS on direction**, hit on band |
| **P5c** | gas_cc entry UP, 2.0–4.0 GW, band SKIP | **1.0 GW**, SKIP | **MISS on direction**, hit on band |
| **P5d** | wind unchanged 1.5–2.5, FAIL; solar 1.7–2.4, PASS | **2.000 FAIL; 2.056 PASS** | **HIT** (both) |
| **P6a** | `floor_retained` non-empty in ≥1 armed year, likely 2022 and/or 2024 | **2024 (6 units) + 2025 (13)**, zero in control | **HIT** |
| **P6b** | diagnostics rows present in every evolved year of both arms | **5 rows/year, both arms** | **HIT** |
| **P6c** | terminal reserve margin rises to 0.10–0.30 | **0.161288** | **HIT** |
| **P7** | 2023 pays $20–55, central $35, **over**-paying vs $24.01 | **$17.27 — UNDER-pays** | **MISS** on magnitude and sign; the *correction vs D40's $55.20* was called correctly |
| **P8** | FC-3 stays FAIL; FC-7 FAIL→CAVEAT; FC-1/8 SKIPPED; **HOLD**; nothing outside `neiso-t1h` moves | all as stated | **HIT** (all five) |
| **P9** | evidence will NOT support flipping the default; flip needs total_gw **and** false_retire in band **and** clean LOYO | none of the three met | **HIT** (§7) |

**Scoreboard: 9 hits, 5 partial (band/direction right, magnitude or movement wrong), 1
outright refutation.** The refutation (P5a) was the lane's own headline and is reported as
such. The pre-declaration's honest note also held: D40's clean-entry figure did not determine
the post-wave years — but it erred **pessimistic**, which the note allowed for and no
prediction claimed.

## 6. The CCS axis (handoff-requested) — a structural no-op, reported as one

`ccs_retrofit_available_year = 2028` at HEAD and this window ends **2025**, so the CCS retrofit
screen is unreachable in every year of both arms. Measured: `ccs_retrofits` is an **empty list
in all five years of both runs**, as it is in the committed baseline. D41's repaired constants
are live and verified at HEAD (`fixed_om_gas_cc_ccs = 65.0`, `ccs_retrofit_capex_kw = 1521.4`)
and this is the **first NEISO capacity bundle solved on them** — but on this axis the bundle is
a **structural no-op, not a measurement**, and it must not be cited as evidence about the
repair. D41's first real NEISO exposure is the T3 golden (2026–2050). One consequence worth
recording: D41 advanced the pinned cache key, which is part of why the bare-HEAD NEISO T1-H key
today (`b0fcad25a90a6449`) differs from the committed baseline's — a key move for a cause that
cannot bind in this window.

## 7. The arming recommendation — the owner decides; this lane recommends on the evidence

**Recommend: do NOT flip the shipped default. Keep the lever ARMED for the NEISO forecast
lane's next measurement.**

*The pre-stated flip condition, which cannot be traded after the fact* (pre-declaration P9):
`retire.total_gw` in band **AND** `false_retire` in band **AND** a clean LOYO, *"any two of
three is not enough."* Measured: `retire.total_gw` is **−27.1 %** against a ±10 % band
(**fails**); `false_retire` is **0.263** against 0.15 (**fails**); and the scorer's own LOYO
recall leg holds for **neither** arm (armed folds 4/6, 1/4, 2/4 — all FAIL; control 4/6, 0/4,
3/4). **Nought of three.** The condition is not met and the default does not move.

*What nevertheless argues for keeping it armed, stated at full strength because it is stronger
than this lane predicted:*

- **The structural case is unchanged and rule 1 governs it.** A published per-CCP requirement
  series is the more faithful market structure than a single-vintage composite, for the same
  reason PJM's FPR path exists. Rule 1 forbids rejecting it because a residual moved.
- **The position evidence is now measured, not projected, and it is strong.** +0.37 / −3.26 /
  +0.14 points on an armed-produced fleet, against +21.13 / −1.44 / −5.34. This is the
  certifying instrument D40 §3 said did not yet exist, and it certifies the lever's own object.
- **The FC-3 miss is a DIFFERENT object.** The bands that still fail — the missing oil/gas_ct
  exit channel (1.527 GW of real exits the screen produces at exactly zero, in **both** arms)
  and the shut storage-entry channel (§4) — are **unmoved by the lever in either direction**.
  Failing them is not evidence against the requirement repair; it is evidence about the
  selection key and the entry gate, which is D27's measured MISO result reproduced on NEISO's
  own evidence (rule 25 clean — nothing imported).

*Routed onward, not tuned here (rule 21):*

1. **The storage-entry channel's insensitivity to capacity revenue** (§4) — new object, this
   lane's refuted headline, with the committed `entry_screen_diagnostics` rows as its instrument.
2. **The oil / gas_ct exit channel at exactly 0.000 GW** — the NEISO analogue of D27's
   floor-retention-key finding; a requirement-side lever provably cannot open it.
3. **The 2024 armed row (−3.26 pts), the one year the arm makes worse**, and the gas_st
   **re-timing** (§3 mechanism 1) — the lever moves *when* an exit lands, and nothing here
   identifies *when* it should.
4. **`add.shares.gas_ct` PASS → FAIL**, the single band the arm degrades, via the gas_ct entry
   collapse.

## 8. Governance attestation

- **Rule 12:** two separate invocations run concurrently; years strictly sequential within each
  (solved [2021, 2023, 2024, 2025], bridged [2022] in both). ~6 min / 2 arms on a 15 GB host.
- **Rule 13/14:** no measured outcome was fed back; the lever's identification is D40's
  committed published Net ICR series; the sign of every movement was pre-stated in a pushed
  document before the solve, and the misses are reported at full magnitude rather than renarrated.
- **Rule 21/24:** **no parameter moved** — no FOM constant, threshold, execution lag, margin
  adder or screen parameter. The arm is a `ScenarioConfig` field recorded in both
  `run_config.json` files; the shipped default stays `False` (verified at HEAD) and this branch
  changes nothing under `src/`.
- **Rule 22:** solve years are the training window plus the never-scored 2021 seed; scoring is
  bounded to 2023–2025; the holdout freeze was ACTIVE at launch and is untouched; **no
  out-of-training year was solved, scored or registered.**
- **Rule 25:** NEISO only; the lever's registry holds one ISO and its predicate requires an entry.
- **Rule 27:** local edits, exact on-disk bytes pushed; **every pushed file ≥300 lines was
  blob-verified** against the remote (both `run_config.json` 853 lines, `register_forecast_run.py`
  842, both hindcast sidecars 655/659, and the pre-declaration 365) — all byte-identical.
- **Rule 28: NOT triggered** — no field added; D40 landed the lever's matrix row and six cells,
  and this lane writes no matrix cell.
- **STOP condition (handoff, binding): NOT triggered.** The `ff-verdicts.json` diff is a **pure
  insertion — 203 added lines, 1 removed** — touching exactly `neiso-t1h`,
  `neiso-t1h-pre-d37` and `neiso-t1h-d37-control`, with a programmatic assertion that **every
  other key is byte-equal** and that the preserved record is the old one verbatim but for its
  added marker note. The board edit is NEISO's `t1h_provenance` + one new `t1h_net_icr_arm`
  field + one new top-level block; no gate leg, no determination, no marker, no other ISO.
- **Collision:** D42 (MISO) and D43 (CAISO) share no files; nothing else touched `neiso-t1h` or
  the NEISO board in this window.
- **A correction this lane owes its own pre-declaration** (recorded in the launch addendum
  before any result was read): the pre-solve cache-key table hashed `build_config()` alone,
  where the runner hashes after `apply_iso_scenario_defaults()`. Adding that layer reproduces
  both realized keys exactly, so it was an instrument error in this lane's arithmetic, not a
  mismatch between the intended and resolved config; every relationship the posture depended on
  survives re-measurement at the correct layer.
- **A claim this lane was asked to verify and found HALF WRONG.** The D36/D39
  `entry_screen_diagnostics` precondition is *"output-only, no cache-key term"*. **Output-only
  is TRUE** (verified at source: the `screen_ledger` sink is write-only, every diagnostic write
  is guarded by `_diag`, and nothing reads it back into a decision — the fleet outcome is
  byte-identical). **"No cache-key term" is FALSE:** the field is **not** a member of
  `_CACHE_KEY_OPTIONAL_FIELDS` — precisely the set dropped from the hash at default — so it is
  hashed at every value (measured: `b0fcad25a90a6449` → `5925e67c572a910f`). It is zero-cost in
  *correctness* and a **full re-solve** in *compute*. **Proposed, not done here** (a cache-key
  registry edit is outside a measurement lane's scope): register it at `"False"`, which would
  make the claim true as written.

## 9. Handoff

**The post-wave years score, so D40's blocker is discharged and the three waiting chains can
proceed on measured rows** (§2). **The default flip is refused on this lane's own pre-stated
condition** (§7) and remains an owner decision. **Four objects are routed** (§7) — the storage
channel, the oil/gas_ct exit channel, the 2024 row and gas_st re-timing, and the degraded
`add.shares.gas_ct` band. **Do not tune this lever to any of them** (D40 §6, verbatim).
