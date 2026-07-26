# PRE-COMMIT — ERCOT-113 Task B: per-zone wind SHAPE A/B

**Date** 2026-07-26 · **ISO** ERCOT · **Years** 2023–2025 (one invocation, years sequential) ·
**Gate** `ScenarioConfig.ercot_wind_zone_shape` (new, default **off**) ·
**Written and pushed BEFORE the treatment solve was launched** (rule 1).

Nothing below may be edited after the first treatment result is read. If a criterion turns out to
be unmeasurable, it is recorded as UNMEASURABLE — never redefined.

## 1. The arms

| arm | bundle | delta |
|---|---|---|
| **B** baseline | `results/calibration/ercot_netrev_margin` (keeper `2026-07-23-ercot100-netrev-margin-keeper`) | — |
| **T** treatment | `results/calibration/ercot113_wind_zone_shape` | `+ ercot_wind_zone_shape` |

The baseline is the committed keeper bundle, read from its `hourly/` sidecars (rule 15 — no
re-solve). The treatment is a single-delta replay of that same keeper:

```
python scripts/replay_keeper.py results/calibration/ercot_netrev_margin \
    --set ercot_wind_zone_shape=true \
    --out-dir results/calibration/ercot113_wind_zone_shape \
    --years 2023 2024 2025 \
    --note "ERCOT-113 Task B: per-zone MERRA-2 wind SHAPE (probe, default-off gate)"
```

## 2. What is being tested, and what is NOT

The mechanism gives each ERCOT zone its own MERRA-2 (NASA POWER WS50M) wind shape at that zone's
EIA-860 wind-plant locations instead of one ISO-wide hourly profile on every zone. The measured
night(00–06)/afternoon(12–18) ratio, stable across all three years, separates the nocturnal-jet
West (1.16/1.15/1.13), North (1.17/1.14/1.08) and Panhandle (1.04/1.13/1.06) from the
Gulf-sea-breeze South (0.89/0.84/0.84).

`renewables._redistribute_preserving_total` preserves the ISO aggregate **exactly in every hour**.
So the mechanism **cannot** change annual wind energy or the ISO-wide bound in any hour. It can
only change **which zone holds the wind**, hence when the West/Panhandle curtailment ceiling and
the zonal links bind.

**Therefore annual wind TWh is NOT a criterion here and will not be quoted as evidence either
way** — it measures zero by construction. Scoring is on the quintile tilt and the scarcity-hour
cheap-stack surplus, per the ERCOT-113 charter.

Baseline tilt to beat (model dispatch vs actual, by quintile of actual wind, from
`FINDING-ercot112-wind-prereqs-2026-07-25.md`):

| quintile | 2023 | 2024 | 2025 |
|---|---|---|---|
| Q1 (lowest wind) | +7.0 % | +5.5 % | +3.7 % |
| Q5 (highest wind) | −2.1 % | −1.4 % | +0.2 % |
| **tilt spread Q1−Q5** | **9.1 pp** | **6.9 pp** | **3.5 pp** |

## 3. Criteria (fixed now)

**W0 — arming proof (gate must fire).** Before any scoring, prove from the solve log and the
bundle that the per-zone shape fired: the run's `run_config.json` records
`ercot_wind_zone_shape=true` **and** the per-zone wind allocation differs from baseline in every
year. If the zonal split is identical to baseline in any year the run is **INERT**, no verdict is
readable, and it is registered as an inert probe. (The ERCOT-113 charter's silent-inertness trap:
an overlay that matches no generator runs clean through a full solve with no error.)

**W1 — aggregate-preservation invariant (falsifier).** Annual ISO-wide wind energy must be
unchanged vs baseline within **0.1 %** in every year. If it moves by more than that, the
redistribution is not preserving the aggregate the way the mechanism claims, the mechanism is
mis-specified, and the run **FAILS** regardless of what the tilt did.

**W2 — PRIMARY: the quintile tilt narrows.** Tilt spread = (model−actual)% at Q1 minus
(model−actual)% at Q5, per year, quintiles cut on **actual** wind. **PASS** iff the spread narrows
in **≥ 2 of 3 years** and **no year widens by more than 1.0 pp**.

**W3 — scarcity-hour cheap-stack surplus.** Mean (model wind − actual wind) MW over hours with
actual ERCOT RT ≥ $200/MWh. This is the quantity the charter cares about: the Q1 end over-supplies
the grid exactly when it is short. **PASS** iff it does not worsen (become more positive) by more
than **150 MW** in any year. Reported in every year whatever it does.

**W4 — scarcity price not degraded.** C3a within **2 pp** and C3c within **5 hours** of baseline
in every year, using the definitions pinned in `scripts/probes/ercot112_score_coal_arms.py`
(C3a = load-weighted `price + ordc_adder + rtordpa_overlay`; C3c = count ≥ $200/MWh).

**W5 — leave-one-year-out (rule 24).** The W2 direction must hold in ≥ 2 of 3 years with no year
degrading by more than 1.0 pp. In-sample gain with held-out degradation is overfitting, not skill.

## 4. Adjudication, fixed in advance

* **CANDIDATE (arm-worthy, recommend to owner)** — W0 and W1 hold, W2 PASSES, and neither W3 nor
  W4 fails.
* **REFUTED** — W0/W1 hold but W2 fails. Registered on the dashboard as a refuted probe with the
  numbers, and the gate stays default-off. A refuted tilt does **not** justify weakening or
  reverting the measured wind bound or the `ercot_wtx_curtailment_driver` (rules 1, 13, 14): the
  per-zone shape is a measured physical input, and if it does not move the tilt then the tilt's
  driver is elsewhere and that becomes the next charter.
* **INERT** — W0 fails. Registered as an inert probe; no verdict on the mechanism.

In **all three** outcomes the run is registered on the dashboard in this session (rule 15) and the
gate remains **default-off**; promotion is the owner's call, not this session's.

## 5. Standing constraints

* Years 2023–2025 only, one invocation, years sequential (rules 12, 16, 22).
* The gate is default-off and keeper-affecting; the keeper is **not** re-solved and **not**
  re-pointed by this session.
* No criterion above may be restated after a result is read.
