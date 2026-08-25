# FINDING — the forward-expectation entry signal, measured

_2026-08-25 · ENTRY-SIGNAL lane (charter: the rung named by
`docs/FINDING-entry-signal-disarm-2026-08.md` §6; root object
`docs/FINDING-entry-screen-t1h-2026-08.md` §6 D-8, §7 L-1/L-1b; predictions
pre-registered in
`docs/PRECOMMIT-entry-signal-forward-expectation-2026-08-25.md` **before the
solve**). **Two LP solves: the ERCOT treatment arm and a same-tree control.**
This rung adjudicates the new `entry_forward_expectation_signal` cell (ERCOT)
and closes the disarm's open trajectory question. **Nothing is armed as a
default anywhere; the verdict is mixed and is escalated to the owner as the
charter requires.**_

---

## 0. The one-paragraph answer

**The forward-expectation construction reproduces both of the disarm's
locational repairs exactly — and the terminal-RM overshoot survives it
unchanged, which closes the question the disarm left open: the overshoot
belongs to D-1's bang-bang volume rule, not to any signal construction.**
P1 and P2 confirm sharply (iron-air at exactly 3,000 MW in every step, wind
entering at 1,092.2 MW — the disarm's ledger rows, reproduced to the megawatt
on a different price object), while terminal RM lands at **40.38 %** against
the disarm's 40.24 and the control's 25.19 — above the pre-registered
35.2 % threshold, so the pre-registered fallback adjudicates: **the cobweb's
recovery overshoot is invariant across all three corners of the
signal-construction space now measured** (zone-flat + forward, zonal +
backward, zonal + forward), and no further signal-construction work should be
chartered against the trajectory. The lane also measured a defect of this
instantiation that no prediction anticipated: the additive re-level subtracts
`S_current`'s **pro-forma** ORDC tail from duals that carry only the
**realized** overlay — two different scarcity objects — so in the step after
a tight year the composed level goes unphysical (entering-2024 mean
**−$48.22/MWh**; solar capture −$185/MWh), flipping solar entry off (solar
|err| 7.09 → 13.09 GW, the one materially worse band). Cell verdict
**`O` (open)** under the precommit's direction-blind rule — not `R` (both
locational repairs confirmed on this construction's own evidence), not a
promotion (the composed-level defect and the owner's call on arming). The
scarcity-consistent delta basis is **named as the successor construction,
not run**.

---

## 1. Posture — verified, not asserted

| check | result |
|---|---|
| same-tree control (bare invocation) vs the committed registered posture | cache key **`28cef3500ec1fd9e` reproduced**; solved `[2021, 2023, 2024, 2025]`, bridged `[2022]` |
| treatment vs same-tree control | **exactly one** `run_config` field differs (`entry_forward_expectation_signal: False → True`), key `a2dc52ffebf14761` |
| holdout | no year outside the registered window solved, scored or registered; `--holdout-authorized` never needed or passed |
| probe gate | `entry_signal_fwd_expectation_compare.py` hard-fails unless all of the above hold; it passed |

**HEAD drift vs the committed brackets, reported and not chased** (the disarm
finding §5.2 discipline): the same-tree control's **fleet metrics are
identical to the committed control's** (additions, retirements, bands — and
its ledger RM path 8.54 / 14.65 / 25.19 % matches to the basis point), while
CO2 differs by **+22,360 / +419 / +5,807 t** (2023/2024/2025). Nine days of
`src/market_sim` commits intervene; ercot-234's EASTEX static GTC rating
(1,300 → 2,300 MW) is the leading dispatch-only candidate. Consequence: the
committed brackets remain fully valid anchors for every fleet-side
comparison in this document; only CO2 must be compared same-tree.

---

## 2. The pre-registered predictions, scored

Committed in the precommit §3 before the treatment bundle existed; executed
mechanically by the probe
(`results/calibration/entry_signal_fwd_expectation_ercot.json`).

| # | prediction | outcome | verdict |
|---|---|---|:--|
| P1 | storage decided in ≥3 of 4 steps, long-duration leading, no one-shot recurrence | storage in **all 4 steps**, iron_air leading every step (3,000 MW each), one-shot pattern absent | **CONFIRMED** |
| P2 | decided wind > 0 MW in ≥1 step | **wind 1,092.2 MW enters in 2022** (scored 1.442 GW vs the control's 0.350) | **CONFIRMED** |
| P3 | terminal ledger-2025 RM ≤ 30.2 % (no overshoot) | terminal RM **40.38 %** ≥ the 35.2 % survives-threshold | **OVERSHOOT SURVIVES** |

### 2.1 Per-step ledger, treatment vs the brackets

| ledger year | committed control | committed disarm | **fwd-expectation** |
|---|---|---|---|
| 2022 (bridge) | gas_cc 3,000 · gas_ct 1,571 · solar 4,946.6 | + wind 1,092.2 · iron_air 3,000 · CAES 2,000 | **identical to the disarm row** |
| 2023 | gas 3,000/3,000 · solar 5,550 · iron_air 3,000 · flow 2,000 | same, but CAES 2,000 for flow | gas 3,000/3,000 · solar 5,550 · **iron_air 3,000 · flow 2,000** |
| 2024 | gas 3,000/3,000 · solar 6,000 | gas_cc 3,000 · gas_ct **1,000** · solar 8,000 · iron_air 3,000 · CAES 2,000 | gas 3,000/3,000 · **no solar** · iron_air 3,000 · CAES 2,000 |
| 2025 | — | iron_air 3,000 | **iron_air 3,000** |
| RM path (2021→2025) | 19.00 → 8.54 → 14.65 → 25.19 | 19.00 → 14.00 → 25.92 → 40.24 | **19.00 → 14.15 → 26.06 → 40.38** |

---

## 3. The headline structural result: the trajectory is the allocator's, not the signal's

Three constructions have now produced three very different margin surfaces
and **one trajectory shape**:

| construction | entering-2024 signal mean | terminal RM |
|---|--:|--:|
| zone-flat MC step + pro-forma tail (shipped) | $28.22 | 25.19 % |
| raw zonal duals (disarm) | ~$156 (its own 2023 duals+overlay) | 40.24 % |
| duals re-leveled forward (this arm) | **−$48.22** | **40.38 %** |

Once the locational object lets storage and wind clear at all, the volumes
are set by `QUEUE_CAP_PER_TECH_GW` / `STORAGE_ANNUAL_BUILD_CAP_MW` and the
top-2 share split — a technology clearing by $1 builds its full cap
(`new_entry.py:1441`, `storage.py:1897`) — so the RM path is nearly bitwise
across a ~$200/MWh swing in the mean signal. **This is L-1b's separation,
measured rather than reconstructed, and on the strongest possible
instrument:** the forward view was the last candidate owner for the
overshoot, and it does not move it. Per the precommit's fallback (rule 21
`[R-DOF]`, in those words): the only admissible closure is an equilibrium
condition the model already contains — build until the screen's own repriced
margin is exhausted — **never a tuned elasticity or damping coefficient.**
D-1 owns the trajectory; the signal lane should not be re-chartered against
it.

---

## 4. The measured defect of this instantiation: two scarcity objects, one subtraction

The composition assumes `S_current` is an unbiased stand-in for the level
the duals carry. It is not, and the four dumps measure the miss directly
(zone-mean $/MWh; `fwd_curr_*` keys are the `S_current` internals):

| step | duals+realized overlay | S_next (tail) | S_curr (tail; h>$1000) | delta mean | composed mean |
|---|--:|--:|--:|--:|--:|
| 2021→2022 | 111.05 | 45.52 (14.16) | 66.24 (34.51; 81 h) | −20.72 | 90.33 |
| 2021→2023 | 111.05 | 390.96 (347.71) | 66.24 (34.51; 81 h) | +324.72 | 435.77 |
| **2023→2024** | **40.33** | 20.74 (0.59) | **109.29 (88.09; 220 h)** | **−88.54** | **−48.22** |
| 2024→2025 | 17.81 | 16.31 (0.02) | 19.66 (2.83; 8 h) | −3.36 | 14.46 |

The duals carry the **realized** post-solve overlay (2023: mean ≈ $5 on the
treatment's 14 %-RM fleet). `S_current` carries the **pro-forma FFR-8A tail
on the same year's own demand** (2023: mean $88.09, 220 hours above $1,000).
Subtracting the latter from the former injects their difference as a phantom
level move: after a tight year the composed signal averages **−$48/MWh**,
with last year's pro-forma scarcity hours — summer afternoons — becoming
deep negative troughs (delta min −$4,926). Measured consequence on the
entering-2024 screens (zone-mean basis, vs the control's zone-flat object):
gas_cc energy margin 55.6 → 4.0 $k/MW-yr, **solar capture +$38.92 →
−$185.12/MWh**, wind capture +22.71 → −4.08. That is why the 2024 step
decides **no solar** where both brackets decided 6–8 GW: the D-8
anti-correlation returns inverted — solar is now anti-selected because its
hours were *last* year's pro-forma-scarce hours. (Gas still builds at its
caps in that step — margin-sign robustness under the reserve-price leg and
the cap-bound allocator; the per-candidate decomposition is recoverable
without a re-solve via `--entry-screen-diagnostics` if the owner wants it.)

**The named successor construction (zero-DOF; NOT run here):** evaluate the
delta on a scarcity-consistent basis — both `S` evaluations tail-free, so
the duals + realized overlay carry all scarcity and the delta carries only
the merit-stack move; or, equivalently symmetric, both sides on the
pro-forma object. Either is exact arithmetic on existing objects. It was not
run because the precommit fixed this construction before the solve, and a
post-hoc second delta in the same session would be exactly the kind of
unregistered iteration the precommit exists to prevent.

---

## 5. Bands and trajectory — attached evidence, never the verdict (rule 1)

Additions, scored 2023–2025 decision basis, all four arms:

| tech | actual GW | committed control | committed disarm | fwd-expectation | \|err\| control → fwd |
|---|--:|--:|--:|--:|:--|
| wind | 12.663 | 0.350 | 1.442 | **1.442** | 12.313 → **11.221** |
| solar | 25.080 | 17.987 | 19.987 | **11.987** | 7.093 → **13.093** |
| gas_cc | 0.244 | 9.000 | 9.000 | 9.000 | 8.756 → 8.756 (cap-bound) |
| gas_ct | 3.692 | 7.571 | 5.571 | **7.571** | 3.879 → 3.879 |
| storage | 13.691 | 5.000 | 18.000 | **18.000** | 8.691 → **4.309** |
| retirements | 2.294 | 0.000 | 0.000 | 0.000 | unchanged |

Storage and wind improve exactly as the disarm did; solar worsens (§4);
gas_ct loses the disarm's 2 GW improvement (the forward level restores its
2024 cap-clear). Every band still FAILs; nothing here is offered as a
passing posture, and no cell verdict rests on any of it.

---

## 6. The L-5 relocation, carried

The disarm killed the screen-signal dumps (its §3.3); this construction
keeps `entry_lookahead_reprice=True`, so the treatment emits **all 4 dumps**
— and each now additionally records `signal_zonal_usd_mwh` (the composed
object the screens actually consumed), `fwd_delta_usd_mwh`, and the
`fwd_curr_*` S_current internals. Every number in §4 was read from the
committed dumps offline; no replay is needed to re-derive them.

---

## 7. Adjudication — `entry_forward_expectation_signal`, ERCOT: **stays `O`, escalated to the owner**

Under the precommit §4 direction-blind rule:

- **Not `R`.** P1 and P2 confirm on this construction's own evidence; the
  deltas are bounded and finite. Rejecting the row would bury both the
  trajectory-invariance result and the reproduced repairs.
- **Not a promotion, and not self-adjudicated further.** The verdict is
  mixed — two confirmations, one pre-registered fallback fired, one measured
  composed-level defect — which is precisely the charter's escalation
  condition. **The owner decides** among: (a) charter the scarcity-consistent
  delta basis (§4's named successor) as the next single-delta rung; (b) rest
  the signal lane and charter D-1's volume rule (the trajectory owner, §3);
  (c) reject the composed form outright. This lane recommends **(b) first**
  — §3 is the strongest result here and it is construction-independent —
  with (a) as the successor rung if the signal lane continues.
- `entry_lookahead_reprice`'s own cell (`K`/`fc O` after the disarm) is
  untouched: this lane tested the new row, not that one.

---

## 8. Rule compliance

- **Rule 1 `[R-STRUCT]`** — the verdict is argued from which objects are
  real (realized vs pro-forma scarcity; the allocator vs the signal), never
  from bands; the solar regression is reported at full magnitude.
- **Rule 12 `[R-PARALLEL]`** — the two invocations ran concurrently; years
  sequential within each.
- **Rule 13 `[R-MEASURED]`** — no measured outcome enters any model path;
  every input to the construction is a model-produced object.
- **Rule 19 `[R-ONE-MECH]`** — the construction replaces the zone-flat
  object; the shipped reprice and the composition never stack.
- **Rule 21 `[R-DOF]`** — zero coefficients anywhere; the overshoot is
  named as D-1's open root-cause issue, in those words, and no damping
  parameter was introduced or proposed.
- **Rule 22 `[R-HOLDOUT]`** — registered window only (2021 seed +
  2023–2025, 2022 bridged); freeze untouched.
- **Rule 26 `[R-MECH-MATRIX]`** — the row landed with the mechanism (duty
  c, prior commit); the ERCOT cell is updated in this session with this
  evidence (duty b); no other ISO's cell moves (rule 25 — CAISO enters only
  as `U`, and its own composition remains a separate later rung per the
  charter).
- **Rule 27 `[R-PUSH]`** — every ≥300-line file was edited locally and
  blob-verified after push; all solves ran in-session; no CI workflow was
  added.

---

## 9. Reproduction

```
# the two arms (bare invocation = the registered posture; one flag differs)
uv run python scripts/run_capacity_hindcast.py --iso ERCOT --start-year 2021 --end-year 2025 \
    --out-dir results/hindcast/ercot-2021-2025-realized-t1h-fwdexp-control
uv run python scripts/run_capacity_hindcast.py --iso ERCOT --start-year 2021 --end-year 2025 \
    --entry-forward-expectation-signal \
    --out-dir results/hindcast/ercot-2021-2025-realized-t1h-fwdexp

# score each, then the probe (posture-gated; executes the precommit thresholds)
uv run python scripts/score_capacity_hindcast.py --bundle <each bundle>
uv run python scripts/probes/entry_signal_fwd_expectation_compare.py \
    --treatment results/hindcast/ercot-2021-2025-realized-t1h-fwdexp \
    --control results/hindcast/ercot-2021-2025-realized-t1h-fwdexp-control \
    --out results/calibration/entry_signal_fwd_expectation_ercot.json
```

`data/clean` is derived and gitignored: run
`PYTHONPATH=. uv run python scripts/regenerate_clean.py` first (50/51
datatypes succeed on this tree; the one failure is a MISO raw mirror absent
from the profile and irrelevant here). Evolution ledgers stay uncommitted
per repo policy; the probe artifact carries both arms' per-step rows, and
the committed dumps carry every §4 number.
