# PRECOMMIT caiso-293 — the `chp_steam` floor binds in hours the meter says the plant is OFF

**Lane:** caiso-293 · **Date:** 2026-09-20 · **Keeper:** `2026-09-20-caiso-290-leftedge`
(bundle `xiso8_leftedge_span`, 2022–2025, DETERMINATION CALIBRATED with a single ledgered C3c).
**Phase 0 LP spent: ZERO** (rule 32 `[R-SHARD]` (a) — the parent never solves).
**This document is written and pushed BEFORE any code change and BEFORE any solve.** Every
number below is measured from committed artifacts at zero LP; every gate and band in §6 is
declared here and is never swept (rule 1 `[R-STRUCT]`).

---

## 0. The answer in one paragraph

The `chp_steam` floor level is an **energy-equivalent annual average applied as an every-hour
never-below floor**. `derive_thermal_tranches.py` computes
`steam_level_cf = on_freq × p50(loading-when-on)` and **multiplies the on-frequency in**;
`fleet/arrays.py:2875` then applies that product flat across all 8,760 hours
(`min_gen[g, :] = pmin_mw`). The two objects are the same only when `on_freq ≈ 1`. For a plant
online 2–13 % of hours the construction converts a cycler into a 24/7 trickle: same annual
energy, entirely wrong hourly conduct. **Five of the thirteen metered floored plants are forced
to deliver more energy than their meter recorded for the whole year** (Kingsburg 5.16×,
McKittrick 2.22×, Badger Creek 1.84×, Gilroy 1.56×, King City 1.01×, 2025). This is not a
membership error and not an availability error — it is the statistic's semantics. The repair
uses the on-frequency the way **every other per-plant must-run floor in this repo already uses
it** — to size a window that the loading-when-on level then fills — and it needs **no derive
change and no new free parameter**, because `on_frac = steam_level_cf / median_cf` is an exact
identity over two already-committed columns.

---

## 1. What phase 0 measured (all zero-LP, all from committed artifacts)

Probes, both committed with this document:
`scripts/probes/caiso293_chp_steam_floor_census.py`,
`scripts/probes/caiso293_window_placement.py`.
Artifacts: `results/calibration/_caiso293_chp_floor_census.json`,
`_caiso293_window_placement.json`, `_caiso293_window_pooled.json`,
`_caiso293_window_netload.json`.

### 1.1 The mechanism is 20× bigger than its D-4 failure

The keeper's committed `legitimacy_diagnostics.json` fails D-4 on 28 rows / 7 plants /
0.570 TWh. That is the visible tip. The whole `MECH_CHP_STEAM` floor, rebuilt through the
SANCTIONED `bundle_fleet.reconstruct_bundle_fleet` (carrying
`replay_keeper.DERIVED_RUN_YEAR_INPUTS`, caiso-292):

| population class | plants | floor MW | forced TWh/yr (2022→2025) |
|---|--:|--:|--:|
| **A** D-4-failing cyclers | 7 | 48.463 | 0.148 / 0.145 / 0.198 / 0.137 |
| **B** cyclers the D-4 rider SKIPS (CT-only CEMS flag) | 3 | 5.256 | 0.043 / 0.043 / 0.043 / 0.042 |
| **C** flat steam hosts (the mechanism's own cited evidence) | 3 | 714.988 | 5.119 / 4.763 / 3.835 / 4.019 |
| **D** `eia923_cf` lens, no CAMPD meter at all | 28 | 493.172 | 3.913 / 3.915 / 3.915 / 3.899 |
| **total** | **41** | **1261.879** | **9.223 / 8.866 / 7.992 / 8.096** |

The repair's entire reach is **A + B = 53.719 MW, 0.179–0.241 TWh/yr** — 4.3 % of the
mechanism's floor MW. **Class C is untouched by construction** and **class D cannot be reached
at all** (§3.3).

### 1.2 It is NOT a membership error — that candidate is falsified

All seven class-A plants are EIA-860 `Status = OP`,
`Associated with Combined Heat and Power System = Y`, `Sector Name = IPP CHP`,
`Topping or Bottoming = T`. None is retired, mothballed or mis-flagged. The lane instruction's
"is one of these seven a retired/mothballed steam host still carrying a floor?" answers **no**.

### 1.3 The two populations are physically different machines, and the meter says so

CAMPD hourly, plant-summed, on the gap-free clock:

| | on-frac 2025 | hod max/min | median run | runs/yr | longest OFF |
|---|--:|--:|--:|--:|--:|
| **C** Elk Hills / Los Medanos / Salinas River | 0.96 / 0.68 / 0.96 | **1.00–1.04** | 387–3,300 h | 3–22 | 249–2,389 h |
| **A** the seven | 0.018–0.127 | **12.4–35.0** | **4–11 h** | 18–158 | 943–3,693 h |

The `D4_WINDOWS` comment justifies its all-24-hour window by measurement — *"CEMS net flat
0.65-0.76 GW across every hour-of-day, hod max/min 1.16"*. **That evidence is corroborated for
class C and falsified for class A.** Bear Mountain's own hour-of-day on-frequency is 0.02–0.04
overnight and midday rising to **0.31 at h16–h20**: the CAISO evening net-load ramp, not a
steam host. McKittrick 2025 is off for one continuous stretch of **3,693 hours** (5 months)
while its floor binds 8,741 hours.

### 1.4 The derive's "self-targeting" claim is measurably false

`derive_thermal_tranches.py:135` and `campd_bins.thermal_tranche_chp_steam_level`'s docstring
both assert the statistic self-targets: *"a rarely-online cycler's on-frequency collapses its
level toward 0 and it carries no operating-level floor (cyclers keep only their p2/923-CF
never-below base)."* Every clause of that is checkable and it fails:

* **All seven have `chp_pmin_cf = 0.0`** — the p2 never-below base IS zero, so
  `assembly.py:900`'s `if _level > (pmin_cf or 0.0)` fires on every one of them and the swap
  *creates* the entire floor rather than superseding a smaller one.
* *Toward* 0 is not *to* 0. McKittrick's level collapses to 4.9 % of nameplate — and 4.9 % of
  nameplate held for 8,760 h is **12.8 GWh against 5.8 GWh metered**.
* The claim is also false for class C's own p2: Los Medanos, Elk Hills and Salinas River all
  carry `chp_pmin_cf = 0.0` too, because a p2 of an all-hours distribution is 0 for anything
  that ever stops. **Disarming the level swap is therefore not a repair** — it would delete the
  715 MW class-C floor that WP-3 armed the swap to create (FINDING-caiso95 §5).

These two comments are corrected in this lane as falsified statements of fact, independent of
whether the mechanism change below is promoted.

---

## 2. The repair, declared ex ante

**`ScenarioConfig.chp_steam_duty_window: bool = False`** — the on-frequency sizes a WINDOW; the
loading-when-on level fills it.

```
today :  floor = on_frac × L  held in ALL 8760 hours
repair:  floor = L            held in the top (on_frac × live-hours) hours of the SHARED
                              commitment-floor window driver (arrays.py `_window_src`)
```

Annual forced energy is **conserved by construction** (`on_frac × L × H = L × on_frac × H`);
what moves is only *which hours carry it*.

### 2.1 Why this is the repo's own existing pattern, not an invention

`derive_thermal_tranches.py:993`'s `online_frac` comment says of the sibling floors
(`cc_mustrun_per_plant` / `st_gas_mustrun_per_plant`): *"it sizes the committed window — the
top-online_frac system-load hours the plant's committed tranche is held on."* **The CHP steam
floor is the only per-plant must-run floor in the repo that multiplies its on-frequency into
the level instead of using it to size a window**, and the same file blanks the `online_frac`
column for CHP groups on the stated ground that *"their floor is the steam host"* — the exact
premise §1.3 falsifies for class A.

### 2.2 ZERO derive change — the factors are already committed

`median_cf = 100 × p50(on_cat)` and `steam_level_cf = 100 × on_freq × p50(on_cat)` are taken at
the **same percentile over the same sample** (`_CHP_STEAM_LEVEL_ON_PCTILE = 50`), so

> **`on_frac ≡ steam_level_cf / median_cf`**, exactly, from two already-committed columns.

Verified on the committed CAISO artifact: `online_hours / on_frac` lands at **26,264–26,950 h**
for 9 of 13 `ok` rows — i.e. it independently reconstructs the derive's own 3-year 2023–2025
CAMPD sample (26,304 h). Rule 23 `[R-FROZEN-DERIVE]` is therefore **not engaged at all**: no
derive re-runs, no artifact byte moves, no measured parameter is re-identified.

### 2.3 It self-scopes to the metered lens with no membership rule

**0 of 73 `eia923_cf` rows carry `median_cf`.** The identity is undefined there, so class D
keeps today's construction automatically — "the rider never fails a mechanism for a missing
meter" (`legitimacy_diagnostics.py`), enforced by arithmetic rather than by a written exclusion.

### 2.4 Rule compliance, stated rather than assumed

* **Rule 21 `[R-DOF]` — zero new free parameters.** No threshold, no cut, no scalar. Both
  factors are already-derived measured quantities; nothing here can be tuned against a residual.
* **Rule 19 `[R-ONE-MECH]`** — no new floor, no membership change, no second level source. The
  existing floor's *hour-eligibility* is set by the same statistic family that sets its *level*
  — the composition `mustrun_layup_window_mask` already names (membership / size /
  hour-eligibility of the ONE floor).
* **Rule 13 `[R-MEASURED]`** — pooled multi-year CEMS, regenerates from the next vintage,
  responds to changed conditions. **Forward-valid, not backcast-only** (unlike the lay-up mask).
  No outcome is pinned: dispatch above the floor stays free and the window is placed by the
  model's own load, never by the plant's measured on-hours.
* **Rule 17 `[R-FLOOR-WINDOW]`** — (a) driver: the plant's own measured synchronization
  fraction, the same driver the sibling floors use; (b) hours: the top-`on_frac` hours of the
  shared window driver; (c) forward story: both factors re-derive from the next CEMS vintage
  with no model input.
* **Rule 25 `[R-ISO-SCOPE]`** — the artifact is per-ISO; no number crosses an ISO boundary.
* **Rule 1 `[R-STRUCT]`** — selected on §1.3's driver evidence and §3's ex-ante placement
  measurement. **Not selected on any residual, and it will not be reverted because a residual
  moves the wrong way.**

---

## 3. The window driver was ADJUDICATED before the repair was chosen

Three placements scored at zero LP, same window size, `lift = precision / on_frac`
(lift 1.0 = no better than flat forcing):

| placement | class A mean lift | class C mean lift | class A rider-passes |
|---|--:|--:|--:|
| **gross load** (`_window_src` default) | **5.29** | **0.999** | **8 / 28** |
| net load (`commitment_floor_window_netload`, SPP-66) | 4.55 | 0.999 | 3 / 28 |
| plant's own leave-one-year-out (month × hod) duty surface | 3.69 | 1.008 | — |

**Gross load wins, so the repair stays on the existing default and arms no second gate.** Net
load losing is itself informative: these plants follow total system load, not the solar-net
residual.

**The class-C control lands at lift 0.999 with min precision 0.663** — the repair is a measured
no-op on the three plants whose flat conduct is the mechanism's own cited justification.

---

## 4. PRE-REGISTERED GATES — declared here, never swept

| id | gate | bar | STOP? |
|---|---|---|---|
| **G-1** | Identity: for every `status=="ok"` CHP row of **every** ISO artifact, `\|on_frac × median_cf − steam_level_cf\| ≤ 0.05` (the 1-dp rounding envelope) | all rows | **yes** |
| **G-2** | Off-inert: gate OFF ⇒ rebuilt `chp_grid_pmin_mw` and composed `min_gen` / `min_gen_mech` **bit-identical** to HEAD, all four years | exact | **yes** |
| **G-3** | Control inertness: gate ON ⇒ class-C forced energy moves **< 2 %** per year | < 2 % | **yes** |
| **G-4** | Energy conservation: class A+B forced energy moves **< 10 %** per year (redistribution, not removal) | < 10 % | **yes** |
| **G-5** | The point: D-4 `chp_steam` failing rows fall from 28 | see §5 | no |
| **G-6** | C1 `CC_CHP` / `CT_CHP` volumes, C3a, belly | **reported at full magnitude** | no |

G-1 through G-4 are **zero-LP** and are run before any shard is launched.

---

## 5. THE PREDICTION, INCLUDING WHAT THIS REPAIR DOES **NOT** FIX

Scored on the committed placement artifact under the **pooled** `on_frac` the design actually
uses (not the more flattering per-year variant):

> **D-4 `chp_steam` failing rows: 28 → 20 predicted. The repair does NOT clear D-4.**
> The 8 class-A plant-years predicted to clear the conduct rider are exactly
> `10649-{2022,2023,2024,2025}`, `10650-{2022,2024}`, `54768-{2022,2025}`.

Stated before the solve rather than discovered after it. Two named reasons, neither absorbed:

1. **Window-size vintage.** `on_frac` is pooled over 2023–2025 while these plants' on-frequency
   **collapsed across the window** (Gilroy 0.110 → 0.035; McKittrick 0.039 → 0.018; Goal Line
   0.037 → 0.024), so one pooled window is too large in the later years and too small in 2022.
   The repo already names this gate family — `mustrun_online_frac_per_year`, "window SIZE
   vintage". It is the **identified successor** and is deliberately NOT bundled in here.
2. **A load-ranked window can never reach precision 1.0** unless the plant dispatches purely on
   system load. The residual gap is unit-specific economics — which is what the LP is for, and
   which is the honest argument that the *end state* for class A is commitment-conditional
   forcing, or no floor at all. Both are larger objects than this lane.

Under rule 1 `[R-STRUCT]`, a structurally-correct mechanism stays in whatever the gate does; and
D-4 is **not** currently gating this keeper's determination (it reads CALIBRATED with D-4 FAIL
pre-existing). The case for the repair is §1.3, not §5.

**Belly disclosure, declared in advance (rule 1).** The repair moves 0.18–0.24 TWh/yr of forced
energy out of the midday and overnight hours into the top-load hours, so it necessarily removes
must-run MW from the CAISO solar belly — the region an adjacent open object concerns. **The
repair is not selected for that effect and will not be kept or dropped on it.**

---

## 6. G-DRIFT (rule 29 `[R-SCREEN]` (b)) — the keeper's committed bundle IS the control

No control solve. caiso-292 audited `e7091f56..HEAD` and classified every solve-path hunk
**INERT for CAISO** (SPP-66 `commitment_floor_window_netload` default-off OFF-branch identical;
soco-55 `gas_basis_differential_measured_by_year` table carries only `{"SOCO": …}`; nwpp-44
take-or-pay gated `iso in ("MISO","NWPP")`; nyiso-245/246). **This lane extends that audit from
caiso-292's HEAD to this lane's own base and re-states it in the RESULT; it does not re-do it.**

---

## 7. What gets solved, and what it costs

Rules 32 / 34 / 36: **one year per shard, own container, `--years <single year>`, full 40-char
`source_revision`, each shard pushes its WHOLE bundle including `dispatch/<year>_P1.parquet`
via a `.gitignore` negation and a PLAIN `git add`.** Four shards — 2022, 2023, 2024, 2025 —
the full year set the keeper carries (rule 34 `[R-SHARD-PROMOTABLE]` (c); the registry carries
no other CAISO year). The parent composes, scores and registers once.

---

## 8. Known blocker, declared rather than walked into

**A keeper does not re-score in place today** (caiso-292 RESULT §1.6 item 3): regenerating
`legitimacy_diagnostics.json` from the committed keeper bundle differs in 697 of 1,396 leaves
because the committed run scored on `dispatch/<y>_P1.parquet` and a regeneration falls back to
the run payload (D-2 24 → 20, D-4 52 → 37). **Every D-4 number in this document is read from the
COMMITTED artifact, never from a regeneration**, and the arm's D-4 will be read from the arm's
own solve-time artifact. No cross-comparison of a regenerated figure against a committed one is
made anywhere in this lane.
