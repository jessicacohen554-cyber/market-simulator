# PREREG miso-172 (arm 1) — per-YEAR `online_frac` for the per-plant must-run window

**Written and committed BEFORE any arm result is read.** Session miso-172,
2026-08-20. Keeper `2026-08-19-miso-170-sitegrain` (bundle `miso170_layup_B2`),
determination NOT-YET on C3a-2025 + C8-2023. This prereg owns **C8-2023 only**;
the C3a-2025 scarcity lane is closed end-to-end (miso-163 owner ruling,
FINDING-miso171) and is not worked here.

Executes `RESULT-miso170b-sitegrain-execution-2026-08-19.md` §4's named
successor. The Ames (1122) p25 LEVEL basis is a **separate** mechanism under a
**separate** gate and its own prereg (rule 19 `[R-ONE-MECH]`):
`PREREG-miso172-p25-level-basis-2026-08-20.md`.

---

## 1. The defect

The committed thermal-tranche artifact publishes ONE `online_frac` per
`(plant_code, plant_group)`, measured over the **POOLED** derive window
(2023–2025 for MISO). The runtime consumes it as the **window of a SINGLE SOLVE
YEAR's** commitment floor — the top-`online_frac` fraction of *that year's*
hours, ranked by system load
(`data/fleet/arrays.py::_compose_min_gen_floors`).

The two grains do not match. A plant whose synchronization share **moves** across
the derive window is committed at its multi-year average in every year:
over-committed in its light years, under-committed in its heavy ones. This is
rule 17 `[R-FLOOR-WINDOW]` verbatim — a floor binding in hours its own driver
evidence says the unit is offline is a bug by definition, whatever it does to the
residual.

**The live case, MISO 1402 Little Gypsy** — the keeper's sole remaining D-4
conduct failure and MISO's sole C8 blocker:

| | 2023 | 2024 | 2025 | pooled |
|---|---|---|---|---|
| measured synchronization share | **0.251** | 0.615 | 0.658 | **0.508** |
| window the runtime uses today | 0.508 | 0.508 | 0.508 | |

A **~2.3× 2023 over-commitment**, and a ~19–23 % *under*-commitment in 2024–25.
The keeper's own D-4 row: 1402 is floored 0.3529 TWh across 2,567 binding hours
in 2023 while its meter reads **zero in 71.2 % of exactly those hours**.

**Scale, measured, not anecdotal:** 68 of MISO's 184 covered plants move ≥ 0.10
across the derive window.

## 2. The mechanism (GATED, default off)

`ScenarioConfig.mustrun_online_frac_per_year: bool = False`. When armed, the
window of **both** per-plant must-run seams (`cc_mustrun_per_plant` /
`st_gas_mustrun_per_plant`, the `st_gas_mustrun_p25_level` block included) is
sized by the **SOLVE YEAR's own** measured synchronization fraction.

* **Data:** `data/raw/_processed-legacy/thermal_tranches_online_frac_by_year_MISO.csv`,
  written by `scripts/data/derive_thermal_tranche_online_frac_by_year.py`.
* **Rule 23 `[R-FROZEN-DERIVE]` — the frozen deriver is NOT TOUCHED** (zero
  bytes) and its pooled artifact is **not regenerated**. The new script
  *imports* the frozen estimator (`_SYNC_MW_NAMEPLATE_FRAC`, `_THERMAL_GROUPS`,
  `_ONLINE_FRAC_GROUPS`, `_fleet_nameplate_and_group`, `_parasitic_factor_map`)
  so it is provably the same statistic, not a re-implementation. **Verified:
  summing the new file's counts over the pooled years reproduces the committed
  `online_frac` column on 178 of 178 rows, 0 mismatched** (`--verify-pooled`,
  in the build log). The 6 absent rows are `rarely_online` (no pooled fraction
  published). This is a reporting-GRAIN refinement, not a re-derivation of any
  value, and its trigger is a measured window/driver mismatch — never a residual.
* **Rule 21 `[R-DOF]` — ZERO new free parameters.** The values are the plants'
  own CEMS records at the grain the floor is applied at. `n_scalars` 0.
* **Rule 13 `[R-MEASURED]` — BACKCAST ONLY**, gated twice (the
  `_BACKCAST_ONLY_OVERLAY_FIELDS` construction guard and a `mode == "backcast"`
  engine gate). **Forward story:** a forecast year has no same-year meter, so it
  keeps the **POOLED multi-year fraction** — which is the same estimator's own
  forward form, re-derived from the most recent CEMS history as each year lands
  and responsive to changed conditions through it. Nothing is pinned to an
  outcome: the window is a commitment-hours count, not a price or volume target,
  and dispatch above the floor stays free.
* **Rule 19 `[R-ONE-MECH]` — the window VINTAGE is replaced, never stacked**, and
  **MEMBERSHIP is unchanged**: a plant qualifies on the pooled artifact exactly as
  today. The single membership consequence is deliberate — a per-year fraction of
  **zero** means the plant's own meter says it never synchronized that year, so it
  carries no floor that year.
* **1402 is NEVER added to the lay-up census** (rules 1/14; the line has held
  three times). It is a cycler; its floor is right in kind, wrong in WINDOW.

## 3. THE HONEST PREDICTION — this arm does NOT clear C8-2023

Measured **before the solve**, from committed artifacts only (the keeper's own
`hourly/system_<year>.parquet` demand, the committed bench per-plant meter, and
the new per-year artifact), 1402's metered **zero-share over the top-k
system-load hours**:

| 2023 window | k | metered zero-share | conduct rider |
|---|---|---|---|
| pooled 0.508 (today) | 4,450 | 72.9 % | FAIL (observed 71.2 % over binding hours) |
| **per-year 0.251 (this arm)** | **2,199** | **64.1 %** | **still FAIL — predicted** |

The rider fails when the metered median over binding hours is ≤ 0, i.e. when the
zero-share is ≥ 50 %. **The largest 2023 window that could clear it is 247 hours
(2.8 %)** — no admissible `online_frac` reaches it. 1402's 2023 conduct is **not
load-ranked at all**: its monthly online share runs 0.00 / 0.02 / 0.34 / **0.49**
/ 0.36 / 0.31 / 0.38 / 0.76 / 0.15 / 0.10 / 0.03 / 0.06, i.e. April (a shoulder
month) exceeds June and July, and the zero-share is already 54 % in the top
1,000 ISO-wide load hours. **2024 and 2025 clear the rider at EVERY k.**

So this arm is pre-registered as a **structural repair that fixes the window's
VINTAGE and leaves a different object — the window's SHAPE/season — standing**.
Under rule 1 `[R-STRUCT]` that is not a reason to withhold it: the pooled window
applied per year is a plain grain error, the fix is zero-DOF measured data, and a
structurally-correct mechanism is not judged by whether the residual moves.
**§6 names the successor with its evidence.**

## 4. Pre-registered gates (scored by `scripts/probes/_miso172_window_ab.py`, committed before either result is read)

Control `miso172_control` = same-recipe `replay_keeper` of the keeper at this
HEAD with both new flags OFF. Arm `miso172_peryear` = the control `--set
mustrun_online_frac_per_year=true`. Both `--year 2023 2024 2025`, sequential in
ONE invocation (rules 12/16).

| gate | pass condition |
|---|---|
| **K-0** control inertness | every scored sidecar of every year `max\|diff\| = 0.0` vs the committed keeper, non-numeric equal. **Verified BEFORE any arm output is read.** A K-0 failure stops the session. |
| **K-1** window exactness | in the arm, every floored plant's binding-hour count ≤ `round(per-year frac × 8760)`, and no live plant's window is sized by the pooled value. Read at unit grain from the arm's own `floors/<year>_P1.npz`. |
| **K-2** liveness | the mechanism's D-2 forced energy lands inside the §5 bands, **all 21 plant-years**, with the 1402 direction sign-correct in every year (2023 DOWN, 2024 UP, 2025 UP). |
| **K-3** conduct failures | **ZERO NEW** D-4 conduct failures and zero new off-window binding, in any year. 1402-2023 is **pre-named as an expected surviving failure** (§3). |
| **K-4** C8 | 2024 and 2025 must NOT regress from the control. **2023 is pre-registered to FAIL.** |
| **K-5** no gated flip | zero record-grain PASS→FAIL flips over the full scorer output. A flip is reported and **blocks promotion on this arm alone** — the structure-vs-gates question then goes to the owner, as at miso-170 K-1; the session does not self-absolve. |
| **K-6** ST_GAS shape | D-1 `profile_r ≥ 0.80` and `cv_ratio ≥ 0.5` in all three years (the live gates), and `profile_r` no more than 0.05 below the control in any year. |

**Candidate rule.** The arm is a keeper candidate iff K-0, K-1, K-3, K-5 and K-6
pass and K-2 lands in band — i.e. all kills silent — with K-4-2023 failing
exactly as pre-registered. C8-2023 remaining red is **not** a rejection of this
arm; it is this prereg's own stated prediction.

## 5. K-2 bands, computed from committed artifacts BEFORE the solve

Instrument: per plant-year, `predicted = observed_control × (est_arm / est_pool)`
where `est(k, level) = Σ_{top-k load hours} min(level, nameplate × availability)`
— the ratio carries the window change and the calibration factor cancels the
plant's own at-floor rate. Band **± 50 %** on the *change*, the miso-170 K-2
precedent. Mechanism totals (`st_gas_mustrun_per_plant` forced TWh):

| year | control | predicted | Δ | band on Δ |
|---|---|---|---|---|
| 2023 | 7.2596 | **7.1511** | −0.109 | [−0.163, −0.054] |
| 2024 | 7.3357 | **7.3046** | −0.031 | [−0.047, −0.016] |
| 2025 | 9.3428 | **9.5311** | +0.188 | [+0.094, +0.283] |

The lever is deliberately **plant-targeted, not fleet-wide** — 1402 carries
almost all of it:

| plant | year | control TWh | predicted TWh | Δ |
|---|---|---|---|---|
| **1402** | 2023 | 0.3529 | **0.1432** | **−59 %** |
| **1402** | 2024 | 0.4618 | **0.5590** | **+21 %** |
| **1402** | 2025 | 0.4819 | **0.6181** | **+28 %** |
| 3457 | 2023 | 0.4948 | 0.4612 | −7 % |
| 6035 | 2023 | 0.0781 | 0.0684 | −12 % |
| 3459 / 1403 / 990 / 1122 | all | — | within ±5 % | small pooled-vs-year spreads |

That the correction moves 1402 **down in 2023 and up in 2024–25** is the point:
a vintage error is directional, and a lever that only ever removed forcing would
be a haircut, not a repair.

## 6. The named successor, identified pre-solve (NOT worked here — rule 19)

The 2023 residual is an **availability/seasonal-lay-up** object, not a window
object, and it is measured:

> 1402's outage-extract availability in 2023 is **0.541 in January and February
> and ~0.95–1.00 in November–December**, while its meter reads **0.000 / 0.015**
> online in Jan/Feb and **0.033 / 0.058** in Nov/Dec. The model believes half to
> all of a 916 MW steamer is available in exactly the months the meter says it
> never ran.

This is the same "laid up but reads ~available in the outage extract" family the
miso-170 census repaired — at **part-year** grain, which the census (which
requires all 18 pooled (year, 4-hour-block) cells at zero) cannot see. The
successor is a **seasonal availability/commitment-window** object with its own
identification, its own A/B and its own DOF answer. It is **not** an exclusion
and **not** a census membership change (rules 1/14).

## 7. Governance

Rule 22 `[R-HOLDOUT]` fail-closed: MISO holds neither `complete` nor `final`,
the spend freeze is ACTIVE, **2023–2025 only** under every result here. Rule 28
`[R-MECH-MATRIX]`: the mechanism's base row plus a cell line in **every** ISO
shard land in the same PR; MISO's cell is stamped with this arm's verdict in
this session, and no other ISO's shard is touched (rule 25). Rule 15: both runs
are registered on the dashboard in this session, keeper or not.
