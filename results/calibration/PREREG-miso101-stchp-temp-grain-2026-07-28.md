# PRE-REGISTRATION — miso-101 hour-grain diurnal temperature capability (single delta)

**Written and committed BEFORE either arm was solved.** No LP result existed
when this document was frozen. Gates below are final — a gate this document
does not contain cannot be quoted as a pass. Format follows
`PREREG-pjm135-star-node-net-position-cut-2026-07-28.md`, mirrored, not copied.

Chartered by `FINDING-miso100-stchp-diurnal-2026-07.md` §7 (owner pre-authorized
the arm lane). Keeper in force: **`2026-07-28-miso-99b-chp-power`**, bundle
`results/calibration/miso99_chp_hr_B`.

**Promotion is NOT pre-granted.** Owner rules 1 `[R-STRUCT]` and 14
`[R-ACCURATE]` apply in full: if structural fidelity improves but backcast gates
regress, the run may still be promoted, and an admissible physical input is
**never** reverted on fit alone. Regressions are reported plainly either way.

---

## §0 — what the derivation found, and how it reshaped the charter

The charter proposed deriving a **steam-cogen condenser** slope. The
measurements redirect that on two counts. Machine output:
`data/raw/_processed-legacy/campd_temp_derate_params_MISO.csv` (+ `_onset`,
`_phase` sidecars), from
`scripts/data/derive_campd_temp_derate_params.py --iso MISO`.

| test | result | verdict |
|---|---|---|
| **D1** what machine is actually metered | MISO's CEMS-visible cogen fleet is **gas-turbine-based, not boilers**: ExxonMobil Beaumont (50625) is **3 × combined-cycle** units (6.03 TWh/yr, the dominant plant); Portside (55096) is a 26 MW CT. R S Nelson (1393) — the other CEMS entry in the D-1 ST_CHP row — is a **tangentially-fired COAL** boiler whose ST_CHP slice is an EIA-923 monthly split off that coal meter, so it is DROPPED as a different machine | **the response is a GT air-density effect, not condenser back-pressure** |
| **D2** the slope, on MISO's own conduct | within-day plant-day fixed-effects regression of log CEMS gross load on the hour-grain dry-bulb, 6 identified cogens, 2023–25: per-plant **+0.0014 / +0.0040 / −0.0070 / +0.0008 / +0.0045 / +0.0006** per °C. Capacity-weighted p50 = **0.00141/°C** | **~5× BELOW the committed literature CC slope (0.0076/°C)** |
| **D3** is there a 15 °C onset? | **No.** At the dominant plant the within-day slope by day-mean-temperature bin is 0.0036 (5–10 °C, r −0.38), 0.0030 (10–15 °C, r −0.28), 0.0037 (15–20 °C), 0.0042 (20–25 °C), 0.0049 (25–40 °C). The response is **clearly present below 15 °C**, where the committed `max(0, T−15)` hinge is identically flat | **the committed hinge would erase the measured winter wave** |
| **D4** phase validation | re-fitting against hour-shifted copies of the proxy peaks at **lag 0 h** | **confirms the h05/h15 climatological anchors on MISO conduct** |
| **D5** is a "pin to the capability-limited plant" screen justified? | **No — refuted.** The premise would be that merchant dispatch contaminates the meter downward, so the most-pinned plants show the cleanest (largest) slope. MISO's most-pinned cogens (Primient cv 0.094, Portside cv 0.058) show the **smallest** slopes (+0.0006, +0.0008); Beaumont (cv 0.159) and Dearborn (cv 0.270) are indistinguishable on every a-priori pinnedness metric yet have opposite-signed slopes | **no screen is applied; the class-population statistic stands** |

**D5 is why the armed slope is 0.00141 and not Beaumont's own 0.00399.** No
principled a-priori screen separates the plants, and the hypothesis that would
have justified one is refuted by the data. The class parameter is therefore the
capacity-weighted p50 across all six identified plants — the same population
statistic `derive_campd_gas_commitment_params.py` uses for `min_load_frac`. This
is a deliberate **under-claim**: see prediction P4.

D2's result is MISO's own independent confirmation of **pjm-95** — literature
derate slopes do not transfer across ISOs (rule 25 `[R-ISO-SCOPE]`).

## §1 — the delta (ONE mechanism, ZERO free parameters)

Not a new floor and not a new mechanism (rule 19 `[R-ONE-MECH]`): an **input-grain
refinement** of the existing `temp_dependent_derate`. `MECH_CHP_STEAM` is already
clipped to `pmax × availability`, so a finer availability shape propagates to
every floored cogen with no second forcing channel.

**Arm B** = the miso-99b keeper recipe replayed at this session's HEAD **plus**:

```
scripts/replay_keeper.py results/calibration/miso99_chp_hr_B \
    --out-dir results/calibration/miso101_tempgrain_B \
    --years <Y> \
    --set temp_dependent_derate=true \
    --set temp_derate_hourly_grain=true \
    --set temp_derate_mean_anchored=true \
    --set temp_derate_classes='["ST_CHP","CT_CHP"]' \
    --set temp_derate_slope_st_chp=0.00141 \
    --set temp_derate_slope_ct_chp=0.00141
```

- **Arm A** `results/calibration/miso101_control_A` — keeper recipe, no delta,
  same HEAD, same container, same regenerated `clean` tree.
- Both arms: **2023 2024 2025**, one process per year into one bundle dir
  (rule 12), merged by `pjm119_merge_year_chain.py`, then `--rebuild-benchmark`
  **staged per arm** (the shared `bench/MISO/<year>.json.gz` trap). No
  `--reuse-solved`. P1-only.

**Every armed number is measured, none is free:**

| parameter | value | source |
|---|---|---|
| `temp_derate_slope_st_chp` / `_ct_chp` | 0.00141 /°C | D2, capacity-weighted p50, MISO CAMPD 2023–25 |
| onset | none (mean-anchored) | D3 — no hinge measurable |
| diurnal phase anchors | h05 / h15 LST | `constants.DIURNAL_TMIN_HOUR/TMAX_HOUR`, Parton & Logan (1981); validated at lag 0 by D4 |
| class scope | ST_CHP + CT_CHP | the classes the CEMS meter spans (D1) |

**`temp_derate_mean_anchored` is the level-neutrality guarantee.** The curve is
`1 − slope × (T − T̄_zone)`, annual mean exactly 1.0, composed **on top of** the
existing level treatment rather than replacing it. The estimator behind the
slope is a within-day fixed-effects regression that differences every level term
away, so the arm claims **only** shape and claims **nothing** about class level.

## §2 — SCOPE, stated explicitly before solving (task item 3)

**Armed: `ST_CHP` and `CT_CHP` only.** Both are tranches of the same physical
cogen facilities, and the CEMS meter spans both — they identify jointly and must
move together, or one half of a single plant would breathe while the other
stayed flat.

**NOT armed: `ST_GAS`, `COAL`, `CC_REGULAR`, `CC_CHP`, `CT_PEAKER`.** No MISO
identification exists for them, and pjm-95 makes the committed literature slopes
non-transferable. Any spillover into these classes is a **defect**, not a result
— see gate G3.

## §3 — PRE-REGISTERED PREDICTIONS

**P1 — the floored cogen wave flips into phase.** Beaumont's ST_CHP grid slice
goes from byte-flat to a wave troughing **h14–h16** and peaking **h05–h08**,
matching the measured phase.
*Verified pre-solve, no LP* (`full_run_year_kwargs` reconstruction of the keeper
fleet, 2024): BASE flat at 36.17 MW, amplitude 0.000; ARM **argmin h15, argmax
h05**, amplitude 0.563 MW. Recorded here so the solve cannot re-litigate it.

**P2 — the class `profile_r` may STAY NEGATIVE in 2024–25, and that is NOT a
failure.** The D-1 ST_CHP statistic composites three channels and the lever owns
only one: Beaumont's floored slice. R S Nelson's anti-phase merchant afternoon
hump (1.6/3.7/6.3 MW, `profile_r` −0.795/−0.751/−0.740 *by itself*) and the flat
report-side BTM add-back are **separate channels the lever does not touch**. A
`profile_r` that stays negative is expected and is **not** grounds to widen the
lever, retune the slope, or revert (rule 1: a structurally-correct mechanism is
not judged by the residual).

**P3 — out-of-scope classes do not move at all.**
*Verified pre-solve:* ST_GAS / COAL / CC_REGULAR availability change **0.000 %**
with hour-of-day range unchanged.

**P4 — the amplitude deliberately UNDER-claims.** The armed class slope
(0.00141) is 35 % of Beaumont's own (0.00399), so the modelled wave is ~1.5 %
of level against a measured ~3.7 % (2024). Predicted, accepted, and **not** to
be closed by raising the slope — closing it would require either a per-plant
slope (no basis: D5) or Beaumont's own value as a class parameter (cherry-pick).

**P5 — system metrics barely move.** ST_CHP is 0.6–0.8 % of MISO load and the
arm is level-neutral, so price MAE / class energy should be near-unchanged. A
**large** headline move is a signal to investigate the plumbing, not a win.

**P6 — D-1 `cv_ratio` for ST_CHP rises**, from a model that had ~zero within-day
variance (0.004/0.010/0.012 model offpeak CV) toward the actual.

## §4 — GATES (final; a gate not listed here cannot be quoted as a pass)

**Structural gates — these decide the mechanism.**

- **G1 (phase).** Beaumont ST_CHP slice model profile troughs in h14–h16.
  *Already met pre-solve.* A solved profile that does **not** is a FAIL.
- **G2 (level neutrality).** ST_CHP and CT_CHP annual **energy** move < 1.0 %
  vs Arm A. Larger is level leakage ⇒ the mean-anchoring is broken ⇒ FAIL.
- **G3 (scope containment).** ST_GAS / COAL / CC_* annual energy move < 0.1 %.
  Any material move is out-of-scope spillover ⇒ FAIL.
- **G4 (direction).** Beaumont-level correlation against its measured hour-of-day
  profile improves. A per-plant correlation that gets **worse** falsifies the
  mechanism ⇒ FAIL.

**Reported, NOT gates** (rules 1/14 — these may regress without triggering a
revert): system price MAE/RMSE, all C-series gates, class `profile_r`, the
all-class D-1/D-2 board. Any regression is reported plainly in the FINDING.

**DO-NOT-REDO carried in:** `gt_ambient_derate` in MISO (inert, miso-90);
arming `temp_dependent_derate` as-is (day-flat input + 15 °C hinge — cannot
produce the wave, and D3 now measures why); any ST_CHP heat-rate add-back
(miso-99 §1.3, back-pressure); the host-load-following premise (refuted,
FINDING-miso100 §8).

## §5 — what this session will NOT do

- Not widen the lever to ST_GAS/COAL to chase `profile_r` (§2).
- Not re-tune the slope after seeing a gate (rule 23 `[R-FROZEN-DERIVE]`: the
  derive script re-runs only when its source data updates).
- Not touch R S Nelson's slice conduct or the fleet-classification question —
  FINDING-miso100 §7 explicitly separates it as its own decision.
- Not solve or score any year outside 2023–2025 (rule 22; MISO freeze active,
  no calibration-complete marker).
