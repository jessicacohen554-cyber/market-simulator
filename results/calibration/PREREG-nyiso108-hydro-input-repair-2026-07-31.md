# PREREG — nyiso-108: arm the NYISO hydro input repair (`--hydro-backfill-year 2024` + `--hydro-eia930-monthly`)

**Written and pushed BEFORE either arm solves.** Everything below — the
construction choice, the gates, the tautology declaration, the all-three-years
declaration, and the REPORTED/KILL split — is fixed in advance. The A/B scorer
`scripts/probes/_nyiso108_hydro_input_repair_ab.py` scores **only** the gates in
§4 and reports **only** the quantities in §5.

**Session:** nyiso-108. **Scope item:** A (the named successor chartered by
nyiso-107 §E). **Keeper under test:** `2026-07-31-nyiso105-chp-heat-rates`
(bundle `results/calibration/nyiso105_chpheatrate_B`, CALIBRATED-WITH-CAVEATS,
0 FAILs, 1 ledgered caveat C3c).
**Pre-solve evidence:** `scripts/probes/_nyiso108_hydro_construction_audit.py`
→ `results/calibration/_nyiso108_hydro_construction_audit.json`.

---

## §1 — What this is: a rule-14 input repair, NOT a tuning lever

nyiso-107 established, and this session independently reproduced from the
committed data, that the NYISO keeper is **fed a truncated EIA-923 hydro vintage
and scored against a repaired benchmark**. The keeper carries
`hydro_backfill_year=None` and `hydro_eia930_monthly=False`, so its 2025 LP hydro
fleet is **3 units / 21.0482 TWh** against 147 / 27.8750 the year before — a
**2.0 % plant retention** — while the scorer's 2025 benchmark is already repaired
to EIA-930's 24.1039 TWh.

**NYISO is the only material-hydro ISO running unrepaired.** Four of six keepers
arm the repair (CAISO/PJM/MISO/NEISO); the only other holdout is ERCOT, whose
hydro is 0.017–0.463 TWh/yr and immaterial. NYISO's hydro is ~26.5 TWh/yr, about
18 % of its generation.

This is therefore a **rule 14 [R-ACCURATE]** correction — swapping an estimate
for measured data — not a mechanism being tested for fit. It adds **no
`ScenarioConfig` field, no new mechanism and zero fitted parameters**: both flags
already exist, are already registered in `run_config`/`meta`, and are already
armed on four other keepers.

Independent reproduction of the nyiso-107 fleet numbers, at the keeper's exact
remaining hydro settings (`hydro_min_flow_floor=True`, `hydro_ror_split=False`,
`hydro_budget_nameplate_aware=False`):

| construction | 2023 units / TWh | 2024 units / TWh | 2025 units / TWh |
|---|---|---|---|
| `bare` (KEEPER) | 154 / 28.4033 | 147 / 27.8750 | **3 / 21.0482** |
| `backfill` — option (ii) | 155 / 28.4060 | 147 / 27.8750 | 147 / 25.9944 |
| `pinned` — option (i) | 155 / 26.8365 | 147 / 26.7463 | 147 / 24.0625 |

---

## §2 — Construction choice: **option (i), backfill + EIA-930 level pin** (the CAISO/NEISO posture)

The three options the scope required to be adjudicated in advance, and why (i)
wins on the evidence measured **before** any solve.

### 2.1 The tie-breaker instrument is NYISO's own P-63, not either EIA series

nyiso-107 established NYISO MIS **P-63 Real-Time Fuel Mix** (`Hydro` category)
as an EIA-independent instrument on the level. It is the one series that is
**neither the model's input nor the scorer's benchmark**, so it can adjudicate
between candidate inputs without circularity. Each candidate LP budget against
P-63:

| year | P-63 (TWh) | `bare` | `backfill` (ii) | `pinned` (i) |
|---|---|---|---|---|
| 2023 | 27.1845 | +4.48 % | +4.49 % | **−1.28 %** |
| 2024 | 26.9763 | +3.33 % | +3.33 % | **−0.85 %** |
| 2025 | 24.2489 | −13.20 % | +7.20 % | **−0.77 %** |

**The 930-pinned input is closest to NYISO's own telemetry in every year**, and
its residual is small, consistent in sign and stable in magnitude (−1.28 /
−0.85 / −0.77 %) — the signature of a small fixed metering-basis offset between
930 and P-63, not of a modelling error. Rule 14 is decisive on this table alone.

### 2.2 Option (ii), backfill-only, is REFUSED — and not merely on level

Two independent reasons, both measured pre-solve:

1. **Level.** It leaves 2025 at 25.9944 TWh, **+7.20 % above P-63** and +7.84 %
   above the benchmark, because it carries 2024's water year forward onto 144
   non-reporting plants. Rule 14 forbids preferring an estimate when the accurate
   value is available and not misaligned.
2. **Seasonal shape — it is actively WORSE than the keeper.** Against P-63 (an
   instrument independent of both input and benchmark), backfill-only *degrades*
   the 2025 monthly shape and puts the annual peak in the **wrong month**:

   | construction | 2023 r | 2024 r | **2025 r** | 2025 share MAE | 2025 peak mo (P-63: **5**) |
   |---|---|---|---|---|---|
   | `bare` | 0.9931 | 0.9938 | 0.9251 | 0.00342 | 5 ✓ |
   | `backfill` (ii) | 0.9930 | 0.9938 | **0.8265** | 0.00391 | **3 ✗** |
   | `pinned` (i) | 0.9882 | 0.9915 | **0.9943** | **0.00079** | 5 ✓ |

   Carrying 2024's shape forward imports 2024's March freshet into a 2025 that
   actually peaked in May. Option (ii) would repair the plant census while
   corrupting the seasonality.

   The PJM/MISO precedent does **not** transfer: those two take backfill without
   the pin because their `NG: WAT` folds pumped storage in gross and the pin is
   *internally refused* for them. NYISO carries **no such fold** — re-confirmed
   independently at nyiso-107 (`NG: WAT`/923-`HY` = 0.9448 / 0.9606, *below* 923
   HY, the opposite of the MISO/PJM signature; NYIS `PS` net **negative**
   −0.372 / −0.410 / −0.490 TWh). NYISO's surface condition is CAISO's and
   NEISO's, and the probe asserts NYISO's absence from
   `EIA930_PS_FOLDED_INTO_WAT` at run time so this cannot silently drift.

### 2.3 Option (iii), a basis-consistent input+benchmark design, is OUT OF SCOPE for this lane

Making input and benchmark share one basis requires changing the **benchmark**
side — `_backfill_renewables_eia930`'s 0.90-completeness swap. That is a
cross-ISO scorer change of exactly the family the owner **DEFERRED** at
nyiso-107 (matrix §5.5 item 11b), and it would move CAISO and NEISO benchmarks
too. It is not available from a NYISO lane without its own charter. Recorded
here as adjudicated, not forgotten.

### 2.4 A third, unbudgeted argument for the pin: physical attainability

Counting plant-months whose energy budget exceeds the plant's own
`nameplate × hours` ceiling — i.e. budget the LP physically cannot deliver and
must silently clip:

| construction | 2023 | 2024 | 2025 |
|---|---|---|---|
| `bare` | 34 | 34 | 0 |
| `backfill` (ii) | 34 | 34 | 33 |
| `pinned` (i) | **14** | **20** | **10** |

The pin more than halves the physically-unattainable plant-months in every year.
Reported as a construction fact, not a gate.

---

## §3 — The two declarations the scope requires IN ADVANCE

### 3.1 The pair moves ALL THREE YEARS, not just 2025 — declared

The flags are passed verbatim to every year in the invocation, so 2023 and 2024
take the 930 level too. Measured budget deltas vs the keeper:

| year | keeper TWh | armed TWh | **Δ TWh** | vs as-scored benchmark |
|---|---|---|---|---|
| 2023 | 28.4033 | 26.8365 | **−1.5668** | +1.33 % → **−4.26 %** |
| 2024 | 27.8750 | 26.7463 | **−1.1287** | +1.49 % → **−2.62 %** |
| 2025 | 21.0482 | 24.0625 | **+3.0143** | −12.68 % → **−0.17 %** |

So the scored 2023/2024 hydro volume error gets **worse** while 2025's collapses.
This is expected and it is **not** a degradation to be fixed by reverting: in
2023/2024 the *benchmark* is raw EIA-923, which sits **+3.11 % / +1.81 % above
NYISO's own P-63 telemetry**, while the armed input sits −1.28 % / −0.85 % below
it. Most of the new 2023/24 "miss" is the benchmark's own basis, measured in
advance. Rule 14 is explicit that the accurate input stays and the root cause is
named rather than buried — the root cause here is the benchmark-side basis
asymmetry already chartered as matrix §5.5 item 11b.

### 3.2 The 2025 hydro VOLUME statistic becomes near-tautological — declared as plumbing

With the budget pinned to the same EIA-930 `NG: WAT` series the 2025 benchmark
uses, the 2025 hydro volume error is **−0.17 % BY CONSTRUCTION**. Budget and
benchmark become the same series.

**This is declared plumbing and is NEVER banked as an improvement.** It is
admissible under rule 13 [R-MEASURED] because a monthly hydro budget is an
inflow/water-availability input — a physical availability limit, the same family
as an outage window — and it regenerates for a forward year through
`forecast_monthly_hydro`'s normal-water-year climatology, responding to changed
conditions via the `hydro_year` wet/dry lever. It passes the rule-13 forward
test; it does not constitute evidence of skill.

**Consequently: the hydro volume error in ANY year is REPORTED, never scored,
and never quoted as an improvement.** Any skill claim must live in quantities the
LP is free to choose — dispatch **shape** (C7 diurnal, hourly r) and the
system-level response (prices, other classes) — and in the pre-solve P-63
comparisons of §2, which are input-accuracy evidence rather than model skill.

The §2.1/§2.2 P-63 tables are **monthly** and therefore also set by the input
under the pin; they are evidence about **which input is more accurate**
(rule 14's question), not about model skill, and are labelled as such throughout.

---

## §4 — Construction gates (these, and only these, can invalidate the experiment)

* **K1 flag fidelity.** Arm B's `meta.json`/`run_config` records
  `hydro_backfill_year == 2024` and `hydro_eia930_monthly == true`; the control
  records `null` / `false`. Arm B's 2025 LP hydro fleet is **147 units**, not 3.
* **K2 control integrity — TWO BASES, only the first is a gate.** The
  **scorecard** basis (control reproduces the committed keeper's determination
  and every per-criterion status) is the pre-registered gate. The stricter
  **byte** basis (class-hour for class-hour, < 1e-6 MW) is computed and
  **REPORTED**; a byte miss is same-HEAD drift — its own finding, not a failed
  gate (caiso-146 / neiso-69 precedent, and the reason a same-HEAD control is
  solved at all).
* **K3 mechanism is LIVE.** `max |Δ hydro class MW|` on a class-hour **> 50 MW**
  in **every** year, and annual hydro dispatch differs by **> 0.5 TWh** in every
  year. Failing K3 is verdict `I` (inert), not `R`.
* **K4 single delta.** The two arms' `run_config` scenario blocks differ in
  **exactly** the two hydro keys and nothing else. Additionally verified
  pre-solve: the armed `hydro_min_flow_floor` level is **identical** across all
  three constructions (18.8423 / 18.9829 / 15.1784 TWh in 2023/24/25) and
  `minflow_infeasible_plant_months == 0` everywhere, so the pin is not smuggling
  a second mechanism change or creating an infeasible two-sided hydro row.
* **K5 year span.** Both bundles carry exactly `[2023, 2024, 2025]` (rule 16
  [R-ALLYEARS]; rule 22 [R-HOLDOUT] D-6 quarantine — the holdout spend freeze is
  ACTIVE and NYISO is absent from `final`).
* **K6 pin sensitivity.** C1 recomputed with the D-10 pinned classes excluded,
  so a verdict resting only on classes D-10 discounts is visible. Additionally,
  C1 recomputed with **hydro itself excluded**, since §3.2 makes hydro's own
  volume term plumbing — a C1 movement that is only the hydro term must be
  visible as such.

## §5 — REPORTED, never a kill condition

Per rules 1 [R-STRUCT] and 14 [R-ACCURATE], a worse backcast on a strictly more
accurate measured input is a **discovered bug to be root-caused**, never grounds
to revert the input:

* Hydro volume error, every year, both directions (§3.2 — plumbing in 2025,
  benchmark-basis in 2023/24).
* Per-class TWh vs actual for every other class; mean λ; price MAE/RMSE.
* Tail hours, slack/dump, congestion, reserve prices.
* **C3c movement in either direction.** C3c is a ledgered, DIAGNOSED, UNCLOSED
  structural limitation with a CLOSED and EMPTY queue. This session does not
  target it, does not claim it, and will not spend a caveat slot on it.
* The barred statistics — 2025 `solar`, `OTHER`, `ST_CHP`, and hydro itself —
  which are not used to size or judge anything (nyiso-106/107).

## §6 — What CAN change the outcome

The **input's admissibility does not depend on the solve**: it rests on rule 14
plus the pre-solve P-63 evidence of §2, all of which is already measured. What
the solve decides is **promotion**.

* **Experiment invalid** → K1, K2 (scorecard basis), K4 or K5 fails. No verdict;
  fix and re-solve.
* **Verdict `I`** → K3 fails (the pair is inert). Recorded, not promoted.
* **Verdict `K`, PROMOTE** → gates pass, and the arm introduces **no new C-gate
  FAIL** relative to the control.
* **Verdict `K`, NOT-YET (no promotion)** → gates pass but the arm introduces a
  **new FAIL**. Per rule 14 the accurate input still stays correct and is **not**
  reverted; the new FAIL is a **discovered root cause** that opens its own item
  and is named in the finding. Promotion waits on that item, not on the input.

## §7 — Promotion requirements (rule 15 / rule 28 duties, in this session)

Both sidecars a replay does not write, before any promotion:

1. `scripts/legitimacy_diagnostics.py --bundle <arm> --iso NYISO --years 2023 2024 2025 --json-out <arm>/legitimacy_diagnostics.json` — else C7/C8 score SKIPPED.
2. `scripts/gen_nyiso108_attestation.py`, modelled on `gen_nyiso105_attestation.py` — else governance scores UNATTESTED and the determination is NOT-YET regardless of result.

Every completed bundle — control and arm, keeper or rejected — is registered on
the dashboard with a real `definition`, the matrix cells and NYISO header are
re-stamped, and `docs/calibration-log/nyiso.md` and `docs/mechanism-testing-matrix.md`
§5.5 are updated in **this** session.

**DOF ledger:** zero free parameters added. Both flags are pre-existing,
registered, measured-data switches already armed on four other keepers; the level
they pin to is a measured EIA-930 series, and the backfill year (2024) is the
prior complete EIA-923 vintage, not a choice fitted to any residual.
