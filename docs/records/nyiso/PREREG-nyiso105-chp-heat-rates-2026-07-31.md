# PREREG — nyiso-105: `measured_chp_heat_rates` on the nyiso-100 keeper

**Written and pushed BEFORE either arm solved** (caiso-146 / nyiso-98 / nyiso-99
precedent). Keeper under test: `2026-07-30-nyiso-100-silretire`
(`results/calibration/nyiso100_silretire`), determination
CALIBRATED-WITH-CAVEATS, 0 FAILs, 1 ledgered caveat (C3c price tail).

Rules in force: 1 `[R-STRUCT]`, 5 `[R-NO-MAGIC]`, 12 `[R-PARALLEL]`,
13 `[R-MEASURED]`, 14 `[R-ACCURATE]`, 15 `[R-DASHBOARD]`, 16 `[R-ALLYEARS]`,
17 `[R-FLOOR-WINDOW]`, 19 `[R-ONE-MECH]`, 21 `[R-DOF]`, 22 `[R-HOLDOUT]`,
24 `[R-REGISTRY]`, 25 `[R-ISO-SCOPE]`, 27 `[R-PUSH]`, 28 `[R-MECH-MATRIX]`.

---

## 1. What survived the no-solve stage, and why only ONE arm solves

The session opened with two candidate levers and two no-solve items. Three of the
four closed on measurement alone. **Only `measured_chp_heat_rates` solves.**

| scoped item | outcome | solves? |
|---|---|---|
| Lever 1 `st_gas_mustrun_p25_level` | **INERT / REFUSED ex ante** (§2) | no |
| Lever 2 `measured_chp_heat_rates` | **LIVE — the arm below** | **yes** |
| Item A P1 export-sink seam | **exposure CONFIRMED and LIVE; reported, not armed** | no |
| Item B `dual_fuel_oil_reattribution` | **zero dispatch delta PROVED; recording-basis delta is NOT zero** | no |

---

## 2. Lever 1 is withdrawn before it solves — four independent measured blockers

Recorded here so the arm list is auditable, not to re-litigate it. Evidence:
`scripts/probes/_nyiso105_seam_recipe_stgas.py` §C.

1. **The single flag is a no-op by construction.** `data/fleet/arrays.py:1750-1753`
   gates the p25 block on `st_gas_mustrun_p25_level` **AND**
   `st_gas_mustrun_per_plant`. The keeper carries `st_gas_mustrun_per_plant=False`,
   so the `--set st_gas_mustrun_p25_level=true` arm would have solved a
   bit-identical control. **The arm is therefore the pair, not the flag** — which
   answers the scope's pre-registration question.
2. **The pair is a no-op on today's artifact.**
   `thermal_tranche_online_frac("NYISO")` returns **0 rows**:
   `thermal_tranches_NYISO.csv` has no `online_frac` column at all (MISO's has it
   on 16/16 ST_GAS rows; PJM/CAISO have the column but 0 populated ST_GAS rows).
   The runtime requires `level > 0 AND online_frac > 0` per plant, so **0 of 11**
   NYISO ST_GAS plants are armable and the floor places nothing.
3. **Making it fire is a fleet-wide re-basing, not a single delta.** Re-deriving
   the artifact at HEAD (`derive_thermal_tranches.py --iso NYISO --years 2023 2024
   2025`, `--chp-floors-from` the committed file) adds `online_frac` — and also
   moves columns the whole NYISO offer curve consumes: `p25_cf` identical on only
   **46/78** rows (max |Δ| 83.6 pts), `committed_pct` **42/78** (max 27.2),
   `median_cf` **41/78** (max 72.1), `online_hours` **32/78**, `peaking_pct`
   **70/78**; plus 3 new columns and 1 new row. It also emits **`p25_cf > 100 %`**
   on two ST_GAS plants (S A Carlson 142.2, Astoria 101.7) against a
   `thermal_tranche_p25_level` accessor that applies **no upper clamp** — so the
   swap would ask for a floor above nameplate. Refreshing the artifact needs its
   own charter (rule 23 `[R-FROZEN-DERIVE]`); it is not this lever.
4. **The premise is false for NYISO, and rule 19 forbids the stack.** The queue
   entry says "measured levels **instead of fitted fractions**" — that describes
   MISO's incumbent (`committed_pct` = P5-of-online LSL). NYISO's surviving
   ST_GAS limbs are **already measured p25**: `NYC:ST_GAS:tmax` 0.1750 and
   `Long_Island:ST_GAS:tmax` 0.2620 are both documented *"persistent 24h base:
   base_24h (when-available cool-day CF p25)"*. And ST_GAS already carries **two**
   mechanisms in the keeper's own D-2 — `reliability_floor` 24.2/27.8/19.4 % of
   class and `nyiso_gas_commitment_bridge` 1.8/2.8/2.5 % — with D-2 already
   flagging **2024 ST_GAS at 30.6 % > 30 %**. A third floor is a rule-19 stack.

**Verdict: matrix cell `st_gas_mustrun_p25` NYISO `U → I`** (inert as shipped),
with the deriver-refresh path named as a separate charter, not a queue item.

---

## 3. The arm

Single boolean delta on the keeper recipe, both arms at the SAME frozen HEAD.

```
control  results/calibration/nyiso105_control_A       (zero-delta replay)
arm B    results/calibration/nyiso105_chpheatrate_B   --set measured_chp_heat_rates=true
```

Both `--year 2023 2024 2025` in ONE invocation, years sequential inside it
(rules 12/16). Scored against the **control**, never the committed keeper
(neiso-69 drift precedent; standing instruction `docs/calibration-log/caiso.md:1165`).
Control-vs-committed-keeper drift is reported separately as its own finding.

### 3.1 The measured input (rules 13/14, zero fitted parameters)

`scripts/data/derive_chp_power_only_heat_rates.py --iso NYISO` →
`data/raw/_processed-legacy/chp_power_only_heat_rates_NYISO.csv`, 31 (plant,
class) rows, **18 applied** (`flag == "ok"`). It undoes eGRID's own published CHP
allocation on eGRID's own net denominator:
`heat_rate = (PLHTIAN + CHPCHTI) / PLNGENAN`. No gross-to-net factor, no fitted
scalar, same source/vintage/denominator as the incumbent.

| class | applied | of class MW | model HR | measured HR | understated |
|---|---|---|---|---|---|
| CC_CHP | 11 / 17 plants | 2,984 / 4,309 MW (69.3 %) | 6.82 | 8.50 | −19.8 % |
| CT_CHP | 7 / 14 plants | 384 / 446 MW (86.2 %) | 7.46 | 11.68 | −36.2 % |

CEMS validation: `(PLHTIAN + CHPCHTI)` reproduces independently metered CAMPD
heat input within 1 % on **16/18** covered plants, median ratio 1.00000.
Flag census: ok 18, not_unfired_topping 8, no_egrid_row 2, no_chp_credit 1,
above_physical_band 1, basis_mismatch 1.

Largest repricings are in-city: Linden Cogeneration 915 MW 5.74 → 9.23,
East River 306 MW (CT_CHP) 7.42 → 11.80, Brooklyn Navy Yard 260 MW 5.38 → 8.75.

**Rule 25 `[R-ISO-SCOPE]`:** NYISO derives its own artifact; no MISO/CAISO
parameter crosses the boundary. **Rule 21 `[R-DOF]`:** zero free parameters — the
arm introduces no tunable, and the DOF ledger is unchanged.

**NYISO is NOT in `CHP_STEAM_CREDIT_HR_CORRECTION_ISOS`** (`{CAISO, PJM}`), so
unlike caiso-147 the incumbent here is eGRID's raw credited `PLHTRT` — the MISO
shape. The caiso-147 hand-factor basis-gate defect **cannot** apply, and this arm
retires no hand number; it is a pure rule-14 accuracy swap.

### 3.2 Rules 17/19 — why no window or one-mechanism question arises

This is an **offer-curve input**, not a floor: it changes `heat_rate` on 18
plants and nothing else. It declares no window, forces no energy, and stamps no
D-2 mechanism id, so rule 17 `[R-FLOOR-WINDOW]` and rule 19 `[R-ONE-MECH]` are
not engaged. Forward story (rule 13 admissibility): the artifact re-derives from
each new eGRID vintage for any forward year and responds to changed conditions —
the same standing the MISO and CAISO keepers were promoted on.

---

## 4. Construction gates (K) — these can KILL

| gate | test | kill condition |
|---|---|---|
| **K1 flag fidelity** | arm B `run_config.scenario_config.measured_chp_heat_rates == true`, control `false`; all 18 applied artifact rows carry `flag == "ok"` | any mismatch |
| **K2 control integrity** | control reproduces the committed keeper's **scorecard** basis — same determination, same per-criterion statuses. The stricter **byte** basis (class-hour < 1e-6 MW) is computed and REPORTED; a byte miss is drift, a separately-reported finding, **not** a failed gate (caiso-146 K2 precedent) | scorecard basis differs |
| **K3 mechanism is LIVE** | `max |Δ CC_CHP MW| > 50` **or** `max |Δ CT_CHP MW| > 50` on a class-hour in ≥1 year | fail ⇒ verdict `I` (inert), **not** `R` |
| **K4 single delta** | the two `run_config` scenario blocks differ in exactly one boolean | >1 field differs |
| **K5 year span** | both bundles carry exactly `[2023, 2024, 2025]` | any other year (rule 22 / D-6; the holdout spend freeze is ACTIVE) |
| **K6 pin sensitivity** | C1 recomputed with the D-10 pinned classes excluded, both arms — the verdict must not rest only on classes D-10 discounts | verdict hinges solely on pinned classes |

**Pre-registered liveness risk (scope's own flag).** NYISO's D-10 block lists
`CC_CHP`/`ST_CHP` in `excluded_from_free` and
`CC_CHP`/`CT_CHP`/`ST_CHP`/`hydro`/`imports`/`nuclear`/`solar`/`wind` in
`pinned_classes`. D-10 is a **reporting** diagnostic with no gate, so C1 still
scores CC_CHP/CT_CHP all-class; the real risk is that the whole improvement lands
in classes D-10 discounts. K6 makes that visible either way. `ST_CHP` is **not**
repriced by this artifact (a boiler-first back-pressure cogen's fuel is process
fuel — out of the mechanism's scope by turbine physics), so its pin is inert here.

---

## 5. What is REPORTED and can never kill

Per rule 1 `[R-STRUCT]` both directions, and rule 14 `[R-ACCURATE]`: **a measured
input that makes the backcast worse stays in, and the real root cause is opened
as a bug.** nyiso-100 was itself promoted on structural integrity while its
reported diagnostics moved the other way.

Reported, never a kill: every C1 class TWh vs actual; C2 system volume; C3a mean
λ; C3b duration/shape; C3c tail hours >$300; C4 hourly r; C7 diurnal shape;
C8/D-2 forced shares; slack/dump; the per-zone λ profile.

**Explicit prediction, recorded now so it can be scored WRONG** (the nyiso-100
prereg's C3c prediction is on the record as wrong, and that is the point): making
in-city CHP ~20–36 % more expensive should push CC_CHP down and CC_REGULAR up,
raising downstate λ. **C3c is NOT this arm's target and no C3c movement is
required, claimed, or sufficient** — the C3c queue is closed and this lever is
not in it.

---

## 6. Promotion rule, fixed in advance

Arm B is promoted to keeper **iff** K1/K2/K4/K5 pass, K3 shows the mechanism is
live, and no criterion moves PASS → FAIL. If a criterion regresses to CAVEAT or a
class-energy residual widens while the input is strictly more accurate, that is
reported and the arm is **still** a keeper candidate on rule 14 — the caveat
budget (3 ledgered / 1 protective, 1 used by C3c) is **not** spent by this arm,
and the C3c caveat stays exactly as ledgered.

If K3 fails ⇒ cell `I`. If a criterion goes PASS → FAIL ⇒ cell `R`, reported with
the trade on the record.

---

## 7. Out of scope (restated so no arm drifts into it)

`nyiso_iroquois_winter_spread` re-arm; `hydro_ror_split`; anything targeting C3c;
any year outside 2023/2024/2025 (the **holdout spend freeze is ACTIVE** and
outranks NYISO's `complete` marker; NYISO is absent from `final`); arming the
CAISO `caiso_p1_export_sink_seam` mechanism (Item A is an infrastructure-defect
audit only).
