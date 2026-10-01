# PREREG nyiso-140 — arm the Long_Island ST_GAS floor's per-plant membership correction (exclude the laid-up Port Jefferson)

**Written BEFORE any solve.** Identification:
`results/calibration/FINDING-nyiso140-li-st-floor-membership-2026-08-16.md`.
Owner decision 2026-08-16: **standalone arm first, then Zone-K** — the transfer
bound and this floor are not one phenomenon (nyiso-139b §4), so folding them
together would confound a rule-17 bug fix with an untested lever.

---

## 1. The object

The one live `Long_Island × ST_GAS` limb (`tmax`, threshold −50 °C ⇒ binds all
8,760 h, `floor_pct` 0.262, `distribution=pro_rata`) is **identified** on a
fleet-aggregate when-available capacity factor but **applied** per unit. Port
Jefferson (2517, 385 MW) is economically laid up — median when-available CF
exactly **0.000** in every hour block of every year, 73 % of cool hours at zero —
yet carries ~100 % model availability, because the 2026-07-26 guard fix
(`6a8f285`) correctly un-booked lay-up from the outage extract. The limb
therefore holds it at 26.2 % of nameplate in all 8,760 h, manufacturing
**1.87 TWh over three years — 72.6 % of everything the limb forces, on 7.2 % of
the fleet's observed output**.

The **window is not the defect and is not being changed**: Barrett (2511) and
Northport (2516) run a genuine persistent baseline (cool-day median CF
0.254 / 0.313 at h00-05, zero in 4–5 % of cool hours) and the floor adds only
4–6 % to their own output.

## 2. The lever, and its rule status

`ScenarioConfig.reliability_floor_plant_exclusions` (new, default **off**) arms
each limb's `exclude_plant_codes`, a new optional column of
`reliability_floor_coeffs_<ISO>.csv`. NYISO's CSV carries exactly one entry:
`2517` on the always-on LI base.

* **Rule 17 `[R-FLOOR-WINDOW]`** — this is the rule the current limb violates;
  the arm is the repair, not a new floor.
* **Rule 23 `[R-FROZEN-DERIVE]`** — a **source-data** trigger (the plant's own
  CAMPD conduct), not a residual. No price or volume residual was consulted in
  the identification, and none may be consulted to size it.
* **Rule 21 `[R-DOF]`** — **zero new free parameters.** `floor_pct` is
  UNCHANGED at 0.262: correcting both cancelling basis errors (a daily-mean
  statistic applied hourly; a fleet aggregate applied per unit) gives 0.2666,
  which rounds onto the frozen value. The arm adds a boolean gate and a
  membership list read from measured conduct — no fitted scalar.
* **Rule 25 `[R-ISO-SCOPE]`** — no other ISO's CSV carries an exclusion
  (unit-tested); the mechanism enters every other shard as `U`.

## 3. Ex-ante prediction — stated before the solve, and deliberately unflattering

Port Jefferson's floored energy is ~0.62 TWh/yr. Removing it lowers LI ST_GAS
output by up to that much, less whatever the LP replaces in-class.

Model vs actual ST_GAS (grid-delivered, `bench.classFull`):

| year | model | actual | model − actual | effect of the arm on C1 |
|---|---:|---:|---:|---|
| 2023 | 11.383 | 8.704 | **+2.679** | **improves** |
| 2024 | 10.476 | 11.071 | −0.595 | **worsens** |
| 2025 | 12.625 | 16.003 | −3.378 | **worsens** |

**So the arm is predicted to make two of three years' ST_GAS volume WORSE.** It
is registered anyway, because rule 1 `[R-STRUCT]` decides this: the floor is
forcing a laid-up plant, that is wrong whatever it does to the residual, and a
mechanism is never kept because it is compensating for something else.

**Rule 14 `[R-ACCURATE]` governs the adverse case.** If the fit degrades, the
correct reading is that the manufactured 1.87 TWh was silently compensating for
a real under-production elsewhere in NYISO's downstate stack (2025 ST_GAS is
already −21 %). The disposition is then to **keep the correction and open a
root-cause lane** — never to bury the error back inside the floor.

## 4. Kill gates — pre-registered, evaluated before any promotion claim

| gate | condition | disposition if it fires |
|---|---|---|
| **K1** config isolation | exactly ONE differing `scenario_config` field between arms (`reliability_floor_plant_exclusions`) | comparison void, re-run |
| **K2** feasibility | zero slack and zero dump, both arms, all three years | comparison void |
| **K3** liveness | the arm's D-2 `reliability_floor × ST_GAS` forced TWh FALLS by ≥ 0.3 TWh/yr vs control — the exclusion demonstrably reaches the LP | mechanism not wired, void |
| **K4** scope | no non-NYISO input moves; no limb other than `Long_Island:ST_GAS:tmax` changes its floored row set | edit leaked, void |
| **K5** gated-criterion regression | any of C1/C2/C3a/C3b/C4/C6/C8 goes PASS → FAIL | **NOT PROMOTED** — see below |
| **K6′** forcing provenance + shape | a D-2 mechanism's forced share rises **and** either (a) a binding mechanism binds outside its driver-justified window (D-4), or (b) the class's D-1 `profile_r`/`cv_ratio` misses | **NOT PROMOTED** |

**K6′ is the owner-adopted successor to K6** (decision 2026-08-16, finding §5). A
bare forced-share rise is **not** a kill: this arm lowers both `forced_twh` and
`class_total_twh`, so the *share* of the surviving `nyiso_gas_commitment_bridge`
mechanism can rise mechanically while it does strictly less work. The gate fires
only on a provenance or shape miss. The energy-normalised diagnostic
`Δforced = forced_arm − forced_ctrl × (class_energy_arm / class_energy_ctrl)` is
**reported, not gated**.

**K5's disposition is deliberately "not promoted", not "rejected as armed".**
The identification in the finding is not contingent on the solve: the floor
forces a plant its own driver evidence says is idle. If a gated criterion flips,
this configuration does not become the keeper, **and the correction is not
reverted** — a root-cause lane opens for whatever the manufactured energy was
masking (rule 14).

**What is NOT a kill:** any ST_GAS volume degradation predicted in §3, in any
year; any move in a report-only band. Per rule 1 the arm is judged on whether
the mechanism is more faithful, not on whether the residual improved.

## 5. Registration duties

* **Rule 15** — control AND arm both registered on the backcast dashboard in
  this session, keeper or rejected probe.
* **Rule 16** — `--year 2023 2024 2025` in ONE bundle per arm, sequential.
* **Rule 28** — the `reliability_floor_plant_exclusions` row was added to
  `mechanism-matrix.js` with the field, plus a cell in all six shards (NYISO `O`,
  the other five `U` per rule 28(d)). Only the NYISO shard carries a verdict.
* **Rule 22 D-5(b)** — promotion is the **owner's call**; the keeper shard, the
  `complete` marker and the matrix keeper stamp stay untouched pending it.
* **Holdout** — 2023–2025 only. The freeze on 2019/2020/2021/2022/H1-2026 is
  untouched; nothing outside the training window is solved, scored or registered.
