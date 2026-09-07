# PRECOMMIT — SPP-48: the per-zone wind LEVEL rule (SPP-54 R-21), the shared-builder repair

**Lane** SPP-48 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-07 ·
**Branch** `claude/spp-48-wind-level-rule-dn2l1r` · **Base** `5de0319b` (`origin/main` at launch) ·
**Data profile** `spp` (+ MISO's EIA-860 rows, which the same committed `data/raw/eia-860` carries) ·
**LP: NONE.** Zero-LP by charter — a construction repair, its identity proofs, and two arithmetic deltas.

**Pushed before any repaired shape was built and before any delta, identity residual or window margin was
read.** Everything below — the rule, the properties it is graded on, the h8509 protocol and the
re-baseline decision rule — is declared here so it cannot be selected by its own result
(rules 1 `[R-STRUCT]`, 23 `[R-FROZEN-DERIVE]`, 29 `[R-SCREEN]`).

---

## 0. Scope, and what is closed before this lane starts

Owner ruling **P17** (2026-09-07, SPP desk r#12) closed the scope question: **shared builder repair; each
ISO re-derives its own numbers (rule 25 `[R-ISO-SCOPE]`).** This lane does not re-litigate that. What it
must establish is that the repair is **correct** — that is the deliverable, not the fact that it changes
a number.

**Landing posture, declared now (SPP-54 §5's pattern, copied deliberately).** The repaired **builders**
and this lane's instruments land on the branch. **No wind-shape parquet on the solve path is regenerated
or committed** — `data/raw/spp-wind-shape/`, `data/raw/miso-wind-shape/` and `data/raw/ercot-wind-shape/`
keep `origin/main`'s bytes. SPP-46 is solving against keeper-3 in parallel and a changed wind input would
invalidate its control mid-flight (rule 29(b)). Every repaired shape this lane builds is written to a
throwaway directory outside the solve path and is never committed. Landing the re-baseline is the desk's
call, sequenced on this lane's item-4 answer.

---

## 1. The defect, stated as arithmetic (SPP-54 §4.2 C-4 is the baseline measurement)

`renewables._redistribute_preserving_total` allocates the measured system wind MW `M(t)` across zones in
proportion to `cap_z · ramp_z(t) · SHAPE_z(t)`. Zone *z*'s share is therefore

```
s_z(t) = cap_z ramp_z SHAPE_z(t) / Σ_k cap_k ramp_k SHAPE_k(t)
```

which is invariant to a **common** rescaling of every zone's shape (`SHAPE → λ·SHAPE` leaves `s`
unchanged) but **not** to a **per-zone** one (`SHAPE_z → λ_z·SHAPE_z` moves the split). What the builder
owes downstream is therefore not "a shape up to an arbitrary per-zone constant" but an estimator of the
zone's true fleet capacity factor **on one common absolute scale**. Both builders' own docstrings assert
the opposite — *"The absolute CF level this script prints is a diagnostic only — nothing downstream reads
it"* — and that assertion is **false per zone**. It is true only of a global constant.

The estimator both builders actually ship is

```
SHAPE_z(t) = Σ_{i ∈ top-6 of z} cap_i cf_i(t) / Σ_{i ∈ top-6 of z} cap_i          (_SAMPLES_PER_ZONE = 6)
```

— the capacity-weighted mean CF over a **non-random, size-selected subsample** of the zone's fleet. Its
level carries a per-zone bias `λ_z = E[SHAPE_z] / cf̄_z ≠ 1`: the six largest plants cover a small and
unequal fraction of each zone's capacity, they are sited on the zone's best resource rather than
representatively, and they are newer, hence taller-hubbed, which lifts their CF through the shear law.
`λ_z` is identified by nothing measured. It is an **undeclared per-zone free parameter that multiplies
the split** (rules 21 `[R-DOF]`, 24 `[R-REGISTRY]`).

Its sharpest symptom is that the estimator is **not partition-consistent**: `top-6(A) ∪ top-6(B) ≠
top-6(A ∪ B)`, so re-cutting one zone's boundary moves **every other zone's** weight at an identical
system total. SPP-54 measured exactly that (§4.2 C-4): splitting the old SPP-South into Oklahoma + the
SPS pocket moved the **North's** annual potential **+1.382 / +1.475 / +1.913 TWh** (2023 / 2024 / 2025),
of which **+1.943 / +2.021 / +2.650 TWh** is the residual South's own sample changing and
**−0.561 / −0.546 / −0.738 TWh** the pocket's shape — and h8509 (2025-12-21 13:00) flipped from a
**+440 MW** feasible regional margin to **−545 MW** infeasible. That is the measurement this lane's
repair must answer, and it is the baseline every number below is differenced against.

---

## 2. The repair — R-LEVEL, declared

**For model zone `z` and year `Y`:**

```
SHAPE_z(t) = Σ_{i ∈ F_z(Y)} cap_i · cf_i(t) / Σ_{i ∈ F_z(Y)} cap_i
```

where **`F_z(Y)` is EVERY EIA-860 operable wind plant assigned to zone `z` and online by year `Y`** — the
same filter both builders already apply *before* they take the six largest — `cap_i` is the plant-summed
nameplate, and `cf_i(t)` is the plant's hourly capacity factor from NASA POWER `WS50M` at the plant's own
coordinates, lifted to the plant's own EIA-860 hub height by the **unchanged** 1/7-power-law shear
profile and passed through the **unchanged** generic IEC-class onshore power curve.

The code change is one line — `nlargest(_SAMPLES_PER_ZONE, "cap")` becomes the whole zone — and one
deletion. **`_SAMPLES_PER_ZONE` is DELETED, not raised** (rule 26 `[R-DELETE]`): a retained sample-count
knob, or a `--samples-per-zone` flag, is a re-armable answer key for precisely the channel this repair
closes.

**The shared rule is expressed ONCE** (rule 25, and the charter's item 1): the ISO-agnostic construction
— physics constants, power curve, shear law, the reanalysis fetch, the per-zone fleet load, the zone-shape
assembly and the per-year frame — moves into `scripts/lib/wind_shape.py`, which both builders import.
Each builder keeps only what is genuinely its ISO's: its docstring and provenance, its clock, its parquet
metadata, and (SPP) the GenMix reconciliation leg. **No number crosses an ISO boundary** — the shared
module contains no ISO name, no per-ISO constant and no ISO branch; each ISO's zone set, plant set,
capacities, hub heights and clock come from its own registry entry and its own EIA-860 rows. This is a
partial fold and does **not** pre-empt the full builder consolidation SPP-54 §8 routed to the desk.

**Not changed by this repair, and stated so a reviewer can check it:** `_SHEAR_EXPONENT`,
`_REANALYSIS_HEIGHT_M`, `_DEFAULT_HUB_HEIGHT_M`, the cut-in / rated / cut-out speeds, the model clock,
the parquet schema and column names, `renewables._redistribute_preserving_total`, `_distribute_by_eia860`,
`_wind_zone_reanalysis_shapes`, `_WIND_ZONE_SHAPE_ISOS`, `_WIND_ZONE_SHAPE_GATES`, and **every**
`ScenarioConfig` field. No gate moves; no default flips; the solve surface must not move.

### 2.1 A cache is added, and it is not a knob

All-fleet sampling raises the reanalysis fetch from 6 points/zone to every plant (SPP 230 plants, MISO
360, per year), so the shared module memoises each `(lat, lon, year)` speed series under `data/clean/`
(DERIVED, disposable, gitignored — the repo's own home for derived artifacts). The cache is content-free
policy: it changes no value, and a cold run and a warm run must produce byte-identical parquets. That is
a declared test, not an assertion.

---

## 3. The properties this repair is graded on — declared BEFORE any of them is measured

A failure of any of these is a defect in the repair, to be fixed or reported as a stop; **none of them is
a residual, and no parameter moves on any of their values.**

| # | property | gate |
|---|---|---|
| **P1** | **Definitional identity.** `SHAPE_z` *is* the zone's capacity-weighted fleet CF, so the per-zone level bias `λ_z ≡ 1` for every zone by construction — no subsample, no size selection, nothing left to identify | argued + tested (a zone's built shape equals the direct capacity-weighted mean over its plants) |
| **P2** | **Partition consistency — the property the defect violates.** For zones `A`, `B` partitioning an old zone `C` over the same plant set, in **every** hour: `C_A·SHAPE_A(t) + C_B·SHAPE_B(t) = C_C·SHAPE_C(t)`, with `C_z = Σ_{i∈z} cap_i`. Re-cutting a boundary therefore cannot move any **other** zone's redistribution weight | max relative violation ≤ **1e-12**; unit test |
| **P3** | **System identity** (charter item 2) — `Σ_z cap_z·cf_z(t) = M(t)`, the system total the builder is handed, on **both** ISOs and **every** year, plus no capacity overflow lost in the water-filling | max rel ≤ **1e-9**; lost-overflow hours = **0** |
| **P4** | **Zero DOF** (rules 21 / 24) — the repair adds no constant and deletes one: net **−1** free parameter | ledger line in the FINDING |
| **P5** | **Forward test** (rule 13 `[R-MEASURED]`) — could this same quantity be produced for a forward year from forward drivers, and would it respond to changed conditions? | answered in writing, §5 |
| **P6** | **No solve-surface move** — `solve_surface_register --diff origin/main HEAD` | **0 moved** |
| **P7** | **Cold/warm cache identity** — the memo changes no value | byte-identical parquet |

### 3.1 An ex-ante PREDICTION, recorded before the measurement

P2 has a consequence for SPP-54's C-3 that is worth pinning **now**, because it is the whole point of the
repair and it would be worthless as a post-hoc observation:

> Under R-LEVEL, the three-zone `South + SPS` regional wind potential must equal the two-zone `South`
> potential **hour for hour**, so the C-3 regional margin delta between the two splits collapses to
> **zero** and h8509 cannot be made infeasible by re-cutting the zone.

This is exact only where the model's per-zone online-MW weight is proportional to the builder's own
per-zone capacity sum. Two things break strict proportionality and are measured rather than assumed:
(a) the **vintage capacity ramp** — `cap_z·ramp_z(t)` tracks *monthly* operable capacity while `SHAPE_z`
is built on the year-end operable plant set, so a mid-year addition inside one side of the cut makes the
two weights non-proportional in the months before it lands (in **December**, where h8509 sits, the ramp
is ~1 on both sides by construction, so the identity should be essentially exact there); and (b) the
**water-filling headroom**, which is per zone, so a three-zone cut can bind a per-zone ceiling that the
undivided zone did not. **Both residuals are measured and reported at full magnitude, whatever they are.**

---

## 4. The measurements, and their protocols — declared before they run

All are arithmetic over committed inputs plus the repaired shapes. **No LP. No holdout year** (rule 22 —
every year touched is 2023 / 2024 / 2025, and nothing is solved at all).

**(M1) Identity legs, both ISOs, all three years** (charter item 2 → P3). SPP-54's committed
`docs/handoffs/spp54/wind_reconcile.py` is the instrument for the identity legs; this lane's copy runs the
same C-1 / C-2 arithmetic through the real path
(`_eia860_monthly_capacity → _forecast_uncurtailed_cf → _wind_zone_reanalysis_shapes →
_distribute_by_eia860`) for SPP two-zone and for MISO, before and after. Reported: max relative
`|Σ_z cap_z cf_z − M|`, hours with lost overflow, max per-zone CF.

**(M2) The h8509 test** (charter item 3). SPP-54's committed `docs/handoffs/spp54/dec21_window_2025.csv`
carries, for every hour of the 2025-12-21 window, the three-zone demand (N / S / SPS), the thermal + hydro
capability **net of keeper-3's own availability arrays**, and the regional solar — all from
`run_year(fleet_only=True)` on keeper-3's recipe at design commit `8d427adc`. This lane **replaces only
the wind terms** with the repaired build and recomputes SPP-54's own margin:

```
region margin = th_S + th_SPS + w_S + w_SPS + solar + 3,400 − (d_S + d_SPS)
```

Three margins are reported for h8509 and for the whole window, because the repair moves both sides of
SPP-54's comparison: **(a)** repaired three-zone, **(b)** repaired two-zone, **(c)** the incumbent
(unrepaired) two-zone — keeper-3's actual current input — so the change is legible against both the old
comparator and the new one. The verdict leg is SPP-54's: **is any window hour infeasible under the
repaired three-zone inputs that was feasible under the two-zone inputs?**

**Declared now:** the answer is reported **either way**. A repair that is correct and does **not** unblock
the pocket is still the right repair; it is the desk's problem and it is **not** a reason to touch the
construction (rule 1 `[R-STRUCT]` — a structurally-correct mechanism is never judged by whether the
residual moved).

**(M3) The two-zone delta** (charter item 4). Per-zone annual wind potential (TWh) for SPP's **current
two-zone** map, 2023 / 2024 / 2025, before and after, plus the implied change to the LP's wind upper bound
`cap_z·cf_z(t)` — annual, mean |Δ|, p1/p99 and max — and the December-window hours specifically. Verdict:
plainly whether keeper-3 needs a re-baseline.

**Re-baseline decision rule, declared before the number is seen** — so it is a rule, not a reading. A
re-baseline is **owed** if the repaired two-zone build changes the LP's per-zone wind upper bound at all
beyond floating-point noise (> 1 MW in any hour), because keeper-3's calibration was identified against
the unrepaired input and a changed physical input is a changed model (rule 14 `[R-ACCURATE]`). Magnitude
decides **urgency and sequencing**, never whether the repair is right. This lane recommends; the desk
sequences.

**(M4) The MISO delta** (charter item 5), measured exactly as (M3) over MISO's six zones for
2023 / 2024 / 2025 — the years MISO calibrates on — with a stated note that MISO's committed set also
carries 2018–2022 and that those would move too. Routed to MISO's desk as a number. **No MISO file other
than the shared-rule half of `build_miso_wind_shape.py` is touched**; MISO's log, shard, keeper and status
are out of scope by charter.

---

## 5. The forward test (rule 13), answered here rather than after the fact

**Question:** could this same quantity be produced for a forward year from forward drivers, and would it
respond to changed conditions?

**Yes, and more strongly than the construction it replaces.** R-LEVEL is *"every operable wind plant in
the zone at the run's information vintage, at its own coordinates and its own hub height, through a fixed
physical shear law and a fixed generic power curve, driven by a chosen weather year."* For a forecast year
the plant set is the model's own evolved fleet (or EIA-860's proposed pipeline at the vintage cutoff), the
weather is the chosen weather year, and nothing in the rule reads an outcome. It responds to changed
conditions in the ways that matter: new capacity sited in a windier part of a zone raises that zone's
level and shifts its diurnal shape; taller hubs raise it through the shear law; a retirement removes its
plant's weight. The six-site rule responds to **none** of these unless the new or retired plant happens to
fall inside the six largest — which is itself the arbitrariness being removed. No measured outcome enters
in either mode, so the input is identical in backcast and forecast (rule 13's forward-vs-backcast line),
and it is not an overlay.

---

## 6. What this lane will not do

- No solve of any kind, no registration, no keeper change, no `keepers/*.json`, no bench part, no registry
  sidecar, no `frontend/data/forecast/`.
- No regenerated or committed wind-shape parquet on the solve path, for any ISO (§0).
- No `ScenarioConfig` field, default or gate moved; no ERCOT parquet rebuilt (ERCOT's shapes are built by
  `build_miso_wind_shape.py --iso ERCOT` and its arming gate `ercot_wind_zone_shape` is default-off — the
  repair reaches ERCOT's **regeneration command** and therefore its future rebuild, which is a routed note
  to ERCOT's desk, not an edit here).
- No shared record touched (plan §8.0 collision rules r#11): not the plan, the ledger,
  `docs/calibration-log/spp.md`, `CHANGELOG.md`, `docs/mechanism-testing-matrix.md`, MISO's log / shard /
  status, or any keeper/gates stamp. This lane's record is its PRECOMMIT, its FINDING and
  `docs/handoffs/spp48/`.
- No change to the construction after any number is read (rule 23) — the rule above is frozen at this
  commit.
