# PRECOMMIT closeout-SOCO-w3p: SOCO measured running parasitic factors (rule 14), 7 legs, structure vs gates

Lane closeout-SOCO-w3, 2026-10-05.

- **Desk direction (2026-10-05):** take the parasitic-load gap as its own structural lane. Use measured data even
  though the sign hurts the fit, declare the expected CC worsening ex ante, solve all 7 years and report structure
  vs gates.
- **Desk ruling B (same day):** use the running-slope form, the rule-14 reconciled form.
- **Timing:** written and pushed before any shard launches.
- **Evidence:** `FINDING-closeout-soco-w3-cc-offer-phase0c-2026-10-05.md` §4; census `parasitic_census_all_iso.csv`.

## 1. The defect and the correction

- **The gap.** `parasitic_load_factors.parquet` carries no SOCO plant. Two families of consumers therefore fall back
  to different estimates:
  - The measured-HR derives (coal, CC, CT, ST) convert CEMS gross to net on a class default: coal 0.93, CC 0.975,
    CT 0.99, ST 0.95.
  - The tranche-family derives (`thermal_tranches`, the OOM level, the coal metered floor) and the benchmark's
    CEMS→net conversion fall back to **1.0** (`campd.plant_group_hourly_net`: `factors.get(code, 1.0)`). They treat
    gross as net.
- **Why not the annual ratio.** The existing construction (annual EIA-923 net ÷ CAMPD gross) charges OFFLINE station
  service to the running output. For low-CF units this is a boundary misalignment: SOCO peakers read 0.83–0.94 and
  Wansley coal 0.817.
- **The reconciled form** (`derive_parasitic_load.py --running-slope`, source `measured_running`): the OLS slope of
  monthly EIA-923 combustion net on monthly CAMPD gross. It is written only where all of these hold:
  - the plant is a single-family COAL, CC or ST plant;
  - the slope lies inside the construction's own band [0.80, 1.00];
  - the intercept is ≤ 0.

  CT and mixed-family plants are not identified and keep their consumers' defaults. No threshold is added.
- **Result:** 14 SOCO plants.

| Plant | Running factor | Was (HR derive / tranche derive) |
|---|---|---|
| Bowen 703 (coal) | 0.930 | 0.93 / 1.0 |
| Miller 6002 (coal) | 0.946 | 0.93 / 1.0 |
| Scherer 6257 (coal) | 0.910 | 0.93 / 1.0 |
| Wansley 6052 (coal) | 0.901 | 0.93 / 1.0 |
| Yates 728 (ST) | 0.962 | 0.95 / 1.0 |
| CC 643, 7710, 7897, 7917, 55241, 55242, 55271, 56150, 57037 | 0.969–0.998 | 0.975 / 1.0 |

## 2. What changes at the pin (branch-only data; never on main before the owner rules)

| Artifact | How | Move |
|---|---|---|
| `parasitic_load_factors.{parquet,csv}` | `derive_parasitic_load.py --iso SOCO --years 2019..2025 --merge --fleet-scope --measured-only --running-slope --no-registry` | +14 pooled rows; the existing 2,712 rows are byte-identical; no plant of another ISO is written |
| `campd_coal_heat_rates_SOCO.csv` | `rebase_measured_hr_parasitic.py` (net = gross ÷ factor on the committed rows) | Scherer +0.25, Wansley +0.35, Miller −0.19 MMBtu/MWh net; Bowen 0 |
| `campd_cc_heat_rates_SOCO.csv` | same | 9 plants −0.00 to −0.18 (CC slightly cheaper) |
| `campd_st_heat_rates_SOCO.csv` | same | Yates −0.13 |
| `campd_ct_heat_rates_SOCO.csv` | — | none (no CT plant identified) |
| `thermal_tranches_oom_level_mw_SOCO.csv` | re-derived (the control re-derive reproduced the committed bytes) | Yates 120.0 → 115.4 MW |
| `thermal_tranches_SOCO.csv` | arm/control ratio of two HEAD re-derives applied to the committed rows (`_closeout_socow3p_tranche_transplant.py`; the derive does not reproduce at HEAD) | gross → net for the 14 plants (below) |

Tranche changes:

- Must-run share: Bowen 60.0 → 59.3 %, Miller 43.2 → 40.9 %, Scherer 34.9 → 31.8 %. Wansley's must-run share is
  0 in the committed artifact; its online must-run share moves 20.1 → 18.1 %.
- Committed share: Bowen 64.0 → 59.5 %, Miller 43.2 → 40.9, Scherer 34.9 → 31.8, Wansley 20.1 → 18.1.
- CC committed shares fall by 0.4–1.0 pp.
- The benchmark's CEMS→net conversion moves for the same 14 plants (C4 only). Scoring rebuilds the bench at the pin.

Not changed (outside this lane, recorded):

- the remaining 31 SOCO plants stay on the tranche-family 1.0 fallback and the HR class default;
- the `factors.get(code, 1.0)` fallback itself (every ISO);
- other ISOs (census to the desk; a separate backfill lane, session_011WyJzKvry8qxcvVH5EgPfU).

## 3. Recipe, pin, control

- **Recipe.** Keeper `closeout_soco_3_span` replayed with `--set mustrun_chp_btm_holdout=true` (the holdout recipe)
  at the pin. No new ScenarioConfig field: the correction is source data (rule 23, cited in the data commit).
- **Pin.** Branch `claude/closeout-soco-w3p`, HEAD after this PRECOMMIT commit (full SHA in the shard prompts and
  the RESULT).
- **Control.** The holdout probe `closeout_soco_w3_span` (pin 487bfdb8; payload on `claude/closeout-soco-w3-reg`).
- **G-DRIFT.**
  - 487bfdb8 → 6cfad57b: `GDRIFT-closeout-soco-w3-keeper-to-pin-2026-10-04.md` plus the diagnostic lane's own
    default-off field.
  - 6cfad57b → pin: every code hunk is INERT for SOCO. `coal_perplant_cliff_split` is ERCOT-gated and off; the MISO
    seam full span is MISO-gated and off; the `unit_commitment_milp` stage and its sidecars are gated off and armed
    by no ISO. The `MECH_DIAG_COAL_METERED_ONLINE` renumbering is a label only.
  - The only data change on the backcast path is this lane's 8 files.
  - The derive and rebase scripts are not on the solve path.

## 4. Expected effect, declared ex ante (the desk asked for the worsening up front)

**Direction:**

- Coal floors and committed bands shrink at Bowen, Miller, Scherer and Wansley (gross → net). That is about −190 to
  −230 MW of must-run per year: Miller −64, Scherer −107, Bowen −22, and Wansley's online must-run −35 in
  2019–2022.
- Scherer and Wansley offers rise; Miller's falls.
- CC offers fall slightly.

**Expected, per year, against the control:**

- COAL_BIT + COAL_PRB −0.5 to −2.0 TWh;
- CC_REGULAR +0.3 to +1.5 TWh.

**Expected record outcomes:**

- CC 2021 / 2023 stay FAIL and deepen.
- A new CC FAIL is possible in 2019 or 2024 (control +6.23 / +6.48 TWh).
- COAL_BIT 2019 deepens (control −7.47).
- C3a/C3b move by about ±1 % / ±0.01.
- C4 coal moves with the bench rebuild.

**This is a structure-vs-gates card.** Measured data replaces two estimates (a class default and gross-as-net). Per
rule 14, a worse fit is a discovered bug elsewhere: SOCO-F1 conduct. The lane does not promote; the owner rules.

## 5. Kills (structural only) and reading

**Kills:**

- unserved energy or dump > 0;
- a leg whose `run_config` lacks `mustrun_chp_btm_holdout=true`;
- a leg not solved at the pin;
- a leg whose `parasitic_load_factors.parquet` sha256 differs from the pin's.

**Reading:** report every record's status change against the control, the class deltas, and the forced share (C8),
with the zero-LP expectation beside the realised values.

## 6. Shards and disposition

- **Shards:** 7 shards, one per year (rule 36), in env env_016R8xUY4maDbppZ6TEns5V8.
  - Out dirs: `results/calibration/closeout_soco_w3p_<Y>`.
  - Branches: `claude/closeout-soco-w3p-<Y>`.
  - Each pushes its full bundle (rule 34) and is archived after verification (rule 33).
- **Composed span:** `closeout_soco_w3p_span`.
- **Scoring:** local scoring registration only (E13).
- **Main receives:** the derive and rebase code, the RESULT and the SOCO matrix note.
- **Branch-only:** the data and the bundle, until the owner rules on promotion.
