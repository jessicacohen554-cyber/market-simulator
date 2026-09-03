# PRE-REGISTRATION — nyiso-180: lift the per-generator-dispatch prerequisite, then adjudicate the nyiso-179 §6.1 candidates on it

**Session:** nyiso-180, NYISO backcast-calibration track, 2026-09-03.
**Committed BEFORE the first solve of this session.** Nothing below was written
after seeing a solved NYISO artifact.
**Keeper at entry: `2026-09-02-nyiso-177-vintage-matched`** (bundle
`results/calibration/nyiso177_vintage_B1p`), determination NOT-YET, fail set
{C1-2023 `ST_GAS` +3.86 TWh, C3a-2025 −11.2 %, C3c}.

---

## 0. The chartered object

nyiso-179 §6.1 handed forward a measured object it could not explain: against
the keeper's **own** P1 zonal prices the model dispatches only **0.767 / 0.522 /
0.740** of the `ST_GAS` its **own** offer puts in the money — **3.84 / 9.09 /
3.99 TWh a year** of steam that is in the money and does not run. Robust to a
strict-inequality sweep (R1), to reserve-family binding (R2), and to the P0/P1
bid-cost gap (R3, structurally zero for this class).

It named three candidate explanations and one prerequisite. The prerequisite is
this session's primary deliverable, because in a pure LP the object as stated is
**impossible**: a column whose objective coefficient is strictly below its own
row's dual, sitting strictly below its upper bound, has a strictly negative
reduced cost and violates optimality. So either the comparison is measuring two
different objects, or some **other row** is charging that column — and no
committed artifact could tell the two apart.

## 1. What this session builds (deliverable 1)

The `unit_hourly_<year>.parquet` sidecar (`_unit_hourly_frame`,
`hourly/`, already written by every solve and already carrying `mw` / `cap_mw`
per LP unit-hour) gains **two columns**, and `DispatchResult` gains the two
fields behind them:

* **`mc`** — `DispatchResult.gen_mc`, the `(n_gen, T)` marginal-cost array
  **this solve installed in its objective**. Not a reconstruction of the offer;
  the offer.
* **`red_cost`** — `DispatchResult.gen_reduced_cost`, the generation columns'
  HiGHS reduced cost, HiGHS-raw, float32. The exact twin of the already-retained
  `flow_dual` for the `P` block.

Joined to `hourly/system_<year>.parquet`'s zonal `price`, they close the
generation column's stationarity identity per unit-hour:

```
red_cost[g,t] = mc[g,t] − price[zone(g),t] + Σ_r a(r,g) · y_r
```

so **Ω[g,t] ≡ red_cost[g,t] − (mc[g,t] − price[zone(g),t])** is, exactly and
with zero free parameters, the net rent every **non-energy** row charges that
unit-hour; and `sign(red_cost)` says which bound the column sits at (`> 0`
lower, `< 0` upper, `≈ 0` interior/marginal).

**Grain: full per-unit × hour, unbounded.** Justified by measurement, not
assumption — the existing frame is **920 KB/yr for NYISO** (`.gitignore` §8, the
nyiso-116 correction), and the two new float32 columns are the same width as the
two already there. A bounded form (top-decile hours) was considered and
rejected: the object under study spans 5,144–7,911 hours a year, so a tail
slice would not contain it. **The measured post-change per-year size is reported
in the finding; if a year's frame exceeds 5 MB the layer is reported and NOT
committed, and the finding says so.**

**It is an OUTPUT artifact.** Proven, not asserted — see §4.

## 2. Candidates, predictions, falsifiers

Pre-declared before the solve. Every prediction is graded at full magnitude and
every miss is reported.

### 2.1 Candidates closed by CODE READING before any solve

These two were checked first and cheaply, as the brief directs. **Both close**,
and each carries a numerical prediction the solve can still falsify.

**Candidate (b) — a post-solve transform between the LP dual and `system`'s
`price`.** `model.py` sets `prices = row_dual[: n_zones*T].reshape(T, n_zones).T`
— the raw energy-balance dual, no negation, no scaling. `_system_frame` adds
`total_overlay` to it, and every contributing term (`ercot_rtordpa_overlay`,
`ercot_dam_as_overlay`, the three ORDC-adder limbs) is inside `if iso ==
"ERCOT"`. For NYISO `total_overlay` is identically zero.
→ **CLOSED. Prediction P-b:** over `ST_GAS` unit-hours that are **interior**
(`|red_cost| ≤ $0.01/MWh`, i.e. the LP itself says the column is marginal), the
median of `mc − price` is `0` to within `$0.01/MWh`, and the mean is not
systematically signed.
→ **FALSIFIED IF** that median is displaced from zero by more than $0.01/MWh, or
`|mean|` exceeds $0.05/MWh: a marginal unit prices at the dual by definition, so
a systematic offset would be exactly the transform this candidate posits.

**Candidate (a) — the armed `nyiso_zonal_loss_surface` delivery factors.** The
loss fraction is applied in `rows.py::build_constraints` as a sparse correction
that scales the **receiving-end incidence entry of each lossy one-way LINK
column** from `+1` to `1 − link_loss[l,t]`. Generation columns are untouched:
generator `g` enters its own zone's balance row with coefficient exactly `+1`.
So the in-the-money test `mc ≤ price[zone(g)]` is already the correct test and
there is no delivery-factor wedge on injections to apply.
→ **CLOSED. Prediction P-a:** identical to P-b (the same interior-unit residual
detects any injection-side factor of any origin), **plus** the brief's own
bound holds: NYISO marginal-loss deviations are a few percent, so even the
counterfactual `δ_z × price_z` test moves the unrun fraction `R` by a few
percent — never the measured 25–48 %.
→ **FALSIFIED IF** P-b's residual fails, or if recomputing `R` against
`δ_z·price_z` moves it by more than 5 percentage points in any year.

### 2.2 Candidate (c) — a capacity-basis mismatch (adjudicated on the sidecar)

nyiso-179 reconstructed `pmax × availability` **outside** the solve; the sidecar
carries the LP's own `mw` next to that same `cap_mw`, and `red_cost < 0` is the
unambiguous signature of a column at an **upper** bound.
→ **Prediction P-c:** the mismatch is **not** the carrier. Specifically, of the
`ST_GAS` MW that are in the money at the model's own price and not dispatched,
the share sitting at an upper bound (`red_cost < −$0.01/MWh`) is **< 10 %**; and
`max(mw − cap_mw) ≤ 1e-3 MW` (the reconstruction never under-states the LP).
→ **FALSIFIED IF** that share is ≥ 10 %, or any unit-hour has `mw > cap_mw +
1e-3` — either says the two capacity bases are different objects and the
reconstruction, not the LP, was wrong.

### 2.3 The two candidates nyiso-179's list does NOT contain, named here before the measurement

The §6.1 list is not exhaustive, and pre-declaring the alternatives is what
stops this session from discovering one after the fact. The keeper arms both of
the LP mechanisms that can hold an in-the-money column at its **lower** bound:

* **`energy_reserve_coopt = True`** — the shared-headroom row `P[g,t] + R[g,t] ≤
  pmax·availability` lets cleared reserve occupy a unit's energy headroom.
  **nyiso-179's R2 cannot see this**: R2 tested whether a reserve family's
  *balance-row dual* was positive, and reserve can be **held** (physically
  occupying headroom, capping energy) while that dual is ~0.
* **`ramp_limits = True`** — an inter-temporal row. A unit in the money this
  hour but ramp-bound from last hour's dispatch is exactly a column at a lower
  bound with a positive reduced cost, and nothing in nyiso-179's instrument
  looks at `t−1`.

→ **Prediction P-d (the session's ranked prior, stated so it can be wrong):**
the dominant attribution is `red_cost > 0` — units at their **LOWER** bound with
`Ω > 0`, i.e. some non-energy row charging them — accounting for **≥ 70 %** of
the in-the-money-unrun MW; and within that, the largest single attributable
signature is the **reserve shared-headroom** occupancy rather than ramp.
→ **FALSIFIED IF** the lower-bound share is < 70 %, or if ramp saturation
attributes more MW than headroom occupancy. **Both legs are reported at full
magnitude whichever way they land, and P-d is the prediction most likely to be
wrong** — it is a prior on which armed row dominates, not a derivation.

### 2.4 The one outcome that would mean the instrument is wrong

If a material population of `ST_GAS` unit-hours shows `mc < price − $1/MWh`,
`mw` strictly between its bounds, **and** `|red_cost| ≤ $0.01` with `Ω ≈ 0`,
then the identity does not close and the sidecar is measuring something other
than the LP that priced. That is a **STOP**: no candidate is adjudicated, and the
finding reports the instrument as failed rather than reporting a verdict.

## 3. Attribution resolution — declared in advance, so the limit is not a surprise

`Ω` is a **sum over rows**. This session can measure it exactly and can test
individual signatures (upper-bound sign; ramp-rate saturation against `t−1`;
reserve-family held MW from the committed `reserve_family_<year>.parquet`), but
it cannot decompose `Ω` into per-row terms without persisting each row family's
dual, which it is not building. **Any unattributed remainder is reported at full
magnitude as unattributed** — never assigned to the leading candidate by
elimination.

## 4. Inertness — the proof, run BEFORE this document was pushed

The change must not touch the LP, the offer path, or any cache key.

1. **Cache key.** No `ScenarioConfig` field is added. Measured at HEAD+change:
   default `4c6b03ae098b6e3e`, bare backcast `8211c72bb1960adc` — identical to
   the two pinned keys the capx-D44 note carries.
2. **Byte-identity control replay.** A real multi-zone LP (40 generators, 3
   zones, storage, renewables, 168 h) solved on the **pre-change** tree and the
   **post-change** tree, digesting `dispatch`, `wind_dispatched`,
   `solar_dispatched`, `slack`, `dump`, `prices`, `storage_charge`,
   `storage_discharge`, `storage_soc`, `flows`, `flow_dual`, `reserve_price` and
   the objective. Run in **two** configurations — **with links** (the branch that
   already converted `col_dual`) and **without links** (the branch that did
   **not**, and now does, which is the only behavioural change in the
   extraction). **Both configurations: BYTE-IDENTICAL.**
3. **Suite.** `tests/unit/model/test_dispatch.py`,
   `tests/unit/model/test_p1_floor_inplace.py`, `tests/unit/pipeline` —
   **314 passed**.

## 5. Stop conditions

* **S1** — if §2.4 fires (the identity does not close), no candidate is
  adjudicated and the finding reports a failed instrument.
* **S2** — if the 3-year solve cannot complete in this session's budget, the
  sidecar lands with its inertness proof and the adjudication is handed forward
  **unmade**; nothing is inferred from a partial year, and no single-year bundle
  is registered as a keeper (rule 16).
* **S3** — **zero free parameters, zero swept bands, zero new mechanisms.** This
  is an instrument lane. If the adjudication points at a lever, the lever is
  **named and handed forward**, never armed here.

## 6. Governance

* **Rule 1 `[R-STRUCT]`** — no residual is consulted in choosing what to measure;
  no mechanism is adopted or rejected on whether it moves a fit.
* **Rule 13 `[R-MEASURED]`** — nothing is pinned to actuals; the run is a replay
  of the keeper's own recipe.
* **Rule 15** — whatever solve completes is registered on the backcast dashboard
  in this session, keeper or rejected probe.
* **Rule 16 `[R-ALLYEARS]`** — one invocation, `--year 2023 2024 2025`, years
  sequential (rule 12).
* **Rule 21 `[R-DOF]`** — no free parameter is introduced; the sidecar carries no
  tunable.
* **Rule 22 `[R-HOLDOUT]`** — training window only. No year outside {2023, 2024,
  2025} is solved, scored or registered. The holdout freeze is untouched and no
  marker is requested.
* **Rule 24 `[R-REGISTRY]`** — no new `ScenarioConfig` field, no env-var knob, no
  gate. The columns are written unconditionally because a write-only output
  cannot change a solve (§4).
* **Rule 25 `[R-ISO-SCOPE]`** — the sidecar change is ISO-agnostic by
  construction (it is the LP's own output, in the shared writer); only the NYISO
  matrix shard is edited.
* **Rule 27 `[R-PUSH]`** — the three touched files are all ≥ 300 lines; each is
  edited locally and pushed as its exact on-disk bytes, with a blob verification
  after the push.
* **Rule 28 `[R-MECH-MATRIX]`** — `unit_network_layer_sidecar` is the matrix row
  this touches; its NYISO cell is re-stamped in this session.
