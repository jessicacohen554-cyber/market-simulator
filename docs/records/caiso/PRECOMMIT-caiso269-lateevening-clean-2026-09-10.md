# PRECOMMIT — caiso-269: the DSW clean-depth family does not tile the clock, and hod 22-23 is the gap

**Session caiso-269, 2026-09-10. Branch `claude/caiso269-lateevening-clean`.**
Keeper at HEAD: **`2026-09-09-caiso-fuelvintage-860-gas`**, DETERMINATION **CALIBRATED**, single ledgered C3c.
Arm: **`ScenarioConfig.caiso_dsw_lateevening_clean`**, default off, CAISO-only, ONE flag on the committed keeper
recipe via `--replay-bundle`. **Pushed before the first LP of any shard.**

---

## §0 — ZERO-LP PHASE 0 (rule 29 `[R-SCREEN]` clause 0). THREE CANDIDATE ARMS KILLED BEFORE A SOLVE

Every number below is computed from the keeper's own committed sidecars
(`results/calibration/caiso_fuelvintage_span/hourly/`), the committed `data/raw` measured series, and the
model's own loaders. No LP was run. This is reported first because it is the session's largest result.

### §0.1 — The belly/import object, re-measured

Model import minus EIA-930 CISO net interchange, mean MW by window (model - actual):

| year | belly h8-16 | evening h17-23 | overnight h0-6 | hod 22 | hod 23 | annual |
|---|--:|--:|--:|--:|--:|--:|
| 2023 | **+2,205** | -11 | +551 | **-1,063** | **-1,032** | +981 |
| 2024 | **+2,099** | -149 | +268 | **-1,290** | **-1,512** | +836 |
| 2025 | **+1,725** | -334 | -637 | **-1,454** | **-1,787** | +355 |

The belly over-import is real and confirmed. **So is a second, sharper object the charter did not name: a
consistent 1.0-1.8 GW import DEFICIT at hod 22-23, in every year, growing.**

### §0.2 — What binds in the belly (and why the funded route cannot reach it)

* The corridor ATC cap (`caiso_corridor_flow_limit`, p95 per month x hod) **binds within 50 MW in 39-46 % of
  belly hours** (2023/2024/2025), against 3.6-4.5 % of evening hours. The belly is cap-bound, not price-bound,
  in ~40 % of its hours. The cap's percentile is a free parameter and is **NOT swept** (rule 1 `[R-STRUCT]`).
* **ARM A KILLED — the funded G-26 / audit C-6 price-ladder closure is MEASURED NEARLY-INERT.** Reconstructing
  the firm + clean capability per hour and differencing it against the keeper's realized import shows the six
  static `IMPORT_TRANCHES["CAISO"]` rungs must clear in **2.9 % of hours / 0.181 TWh (2024)** and **1.1 % /
  0.022 TWh (2025)**. CAISO's import supply is, in 96-99 % of hours, entirely firm + clean tranches; the priced
  ladder is unreachable behind them. Re-pricing it — by Q-Q duration coupling or by the OASIS `PUB_DAM_GRP`
  public-bid limb — could not move the belly, and would barely move 2024/2025 at all. **The OASIS corpus was
  therefore NOT re-fetched** (its payload is untracked at tip; a re-fetch is ~1,096 requests at the 6 s AUP
  spacing, ~110 min and 422 MB, and `curate_dam_public_bids.py` OOMs on a full year per that corpus's own
  README). Cost avoided, and the reason is a measurement, not a schedule.
* **ARM B KILLED — shaping the clean depths by their own (month x hod) measured p95 is INERT.** Level-preserving
  caiso-73-form shaping of the three DSW clean depths binds on the keeper's realized import in **3.3 % of hours
  / 0.243 TWh (2024)** and **1.0 % / 0.023 TWh (2025)**: the clean depth already carries ~2.5 GW of belly slack,
  so the depth is not the binding object.
* **ARM C REFUSED, not tested — resizing or hour-scoping the fossil offer cut.** caiso-267 and caiso-268 are
  registered rejections the owner refused on rule 1 grounds. No third multiplier is proposed and the factor is
  not resized.

**Conclusion carried to the RESULT whatever this arm does: the belly over-import has no groundable lever
available to this session.** Its two live objects are a percentile this session may not sweep and a delivery
basis whose measured evidence currently supports the model's construction. That is stated now, before the
solve, so it cannot be read as a post-hoc excuse.

### §0.3 — The object this arm DOES address, measured

The three DSW clean-depth constructions **do not tile the clock**: caiso-93 runs hod 0-5, caiso-94 runs hod
6-21, and caiso-87's surplus trigger is coverage-STARVED at hod 22-23 (ON in 0.3/0.8 % of 2024 and 1.6/1.9 % of
2025 hod 22/23 — **caiso-253's own G-WINDOW leg**, which closed the question with *"22-23 are
OVERNIGHT-construction hours and no future session need re-measure it"*).

Armed clean capability on the keeper, mean MW by hod, across the hod 21 -> 22 boundary:

| year | hod 21 | hod 22 | hod 23 | measured WECC_DSW corridor net import p50, hod 21/22/23 |
|---|--:|--:|--:|---|
| 2023 | 2,673 | **123** | 347 | 4,911 / 4,947 / 4,835 |
| 2024 | 3,117 | **9** | 26 | 4,540 / 4,814 / 4,824 |
| 2025 | 3,420 | **33** | 42 | 4,642 / 4,911 / 4,875 |

**A ~100x capability discontinuity across one hour boundary, in hours whose measured corridor depth RISES
across the same boundary.** That is a construction artifact of two windows that do not meet, and it sits
exactly on top of the 1.0-1.8 GW measured import deficit of §0.1.

## §1 — THE LEVER, AND ITS EXTERNAL DRIVER NAMED BEFORE ANY NUMBER

**Driver:** the WEIM/EDAM clean-transfer capability at the CAISO-desert-SW boundary — the same physical,
published market structure the caiso-87 / caiso-93 / caiso-94 family already carries. **Window:** the
complement those three leave, fixed by the tiling and by caiso-253's own G-WINDOW finding — **never by a
residual** (rule 17 `[R-FLOOR-WINDOW]`). **Forward story:** depth and gate are pooled climatologies that
regenerate from any year's measured record exactly as the sibling legs do (rule 13 `[R-MEASURED]`).

**Construction** — `inject_caiso_dsw_lateevening_clean`, one tranche:

    cap[t] = admissible[t] x max(0, depth_year - firm_south[t] - surplus[t] - overnight[t] - daytime[t])

* **Depth** = p95 of measured WECC_DSW corridor net import over the SAME hod 22-23 window the capability arms
  (the sibling derives' window-match rule), producer
  `scripts/data/derive_caiso_lateevening_clean_depth.py`: **6,120 / 6,429 / 6,697 MW** (2023/2024/2025),
  2022 **6,726 MW**, pooled static **6,415 MW**. FROZEN caiso-81/86/87/88 gates: **CV 0.037** (<= 0.20 PASS),
  **LOYO worst 6.8 %** (<= 25 % PASS) — tighter than the caiso-93 overnight depth's 0.041 / 8.1 %.
* **Admissibility gate = caiso-253's OWN REFUSAL, adopted unchanged.** caiso-253 refused extending raw-hub
  pricing to hod 22-23 because its **pre-registered** [-2, +4] $/MWh raw-hub discriminator FAILED in 2023
  (DA block median -3.98/-2.56 at hod 22/23) while PASSING in 2024 (-0.73/+0.11) and 2025 (-0.19/+0.06). An
  hour arms **only** where the measured (month x hod) median DA CAISO-PaloVerde spread lies inside that band.
  This session's instrument **reproduces caiso-253's published block medians exactly (-3.21 / -0.36 / -0.03)**,
  which is what pins the gate to that session's refusal rather than to a re-derivation. Admissible buckets:
  **2022 12/24, 2023 4/20** (the 2023 Jan-Feb OASIS hub gap leaves 10 covered months), **2024 18/24,
  2025 19/24** — the gate keeps 2023 dark, which is the point.
* **EF 0 and the no-wheel WEIM basis are MEASURED for these two hours, not inherited**: caiso-253's G-WEDGE leg
  tested hod 22-23 explicitly and PASSED everywhere (delivered median -5.2 to -14.2 against a +4 gate;
  wedge-consistent share 0.0-4.7 % against a 6 % gate).
* **Zero new free parameters and zero new thresholds** (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`): the statistic,
  the percentile, the DA basis, the window and the band are all prior sessions'. The DOF ledger gains **no**
  row.
* **Rule 19 `[R-ONE-MECH]`**: netted per hour against the shaped firm block and all three siblings; it
  **fills** their gap rather than stacking on any of them.
* **Byte-identical off**: the tranche row is only BUILT when the flag is on, so the LP column set is unchanged
  (verified: with the flag off the per-hub fleet's unit-id list is identical).

## §2 — SCREEN YEAR, NAMED BEFORE THE SCREEN RUNS (rule 29 clause d)

**2025** — the year the mechanism's OWN measured footprint is largest: armed capability **2.270 TWh** (2025) vs
1.971 (2024), 1.487 (2022), 0.512 (2023). **Not** the year with the biggest residual. The owner has instructed
all years be solved, so the full span runs regardless; the screen year is named so the gate reading is not
chosen after the fact.

## §3 — PRE-SOLVE FOOTPRINT AND PREDICTIONS

Armed capability, computed pre-solve (`verify_arm`), mean MW at hod 22 / 23 and annual TWh:

| year | hod 22 | hod 23 | armed TWh | armed hours | capability outside hod 22-23 |
|---|--:|--:|--:|--:|--:|
| 2022 | 1,331 | 2,742 | 1.487 | 362 | **0.000000 MW** |
| 2023 | 703 | 700 | **0.512** | 122 | **0.000000 MW** |
| 2024 | 2,399 | 3,000 | 1.971 | 546 | **0.000000 MW** |
| 2025 | 3,606 | 2,612 | 2.270 | 578 | **0.000000 MW** |

**P1.** Import RISES at hod 22-23, by less than the armed capability (it is a capability, the LP clears below
it, and the p95 corridor ATC cap still bounds delivered flow), in the direction of the §0.1 measured deficit.
**P2.** Gas FALLS at hod 22-23. These are high-price hours, so **C3a falls** in 2022/2024/2025 and moves little
in 2023 (the gate keeps 2023 dark).
**P3.** 2023 is near-inert by construction — if 2023 moves materially, the gate is not doing what §1 says and
that is a finding against this arm.
**P4 — C4-2025 IS THE EXPOSURE, STATED IN ADVANCE.** C4-2025 gas NRMSE sits at **0.298 against <= 0.300** —
0.002 of headroom, and it is what killed both ×0.92 arms. This arm pushes gas DOWN at hod 22-23, where the
model over-produces gas (+766 MW mean across h17-23), so the *sign* is favourable — unlike the ×0.92 arms,
which pushed gas UP everywhere. **But 0.002 is 0.7 % of headroom and any dispatch change can cross it.** If
C4-2025 fails, this arm is not promoted, and that is pre-registered here.
**P5.** C3c may move: removing gas from hod 22-23 can shorten the model's price tail. C3c is exempt from
G-NOFLIP (rubric v3.6) and is reported at full magnitude either way.

## §4 — GATES. ALL STOP-ONLY. NONE READS THE TARGET RESIDUAL

| gate | pre-registered condition |
|---|---|
| **G-IDENT** | demand / renewables / hydro / outages / fleet byte-identical to the keeper; the ONLY differing `scenario_config` field is `caiso_dsw_lateevening_clean` |
| **G-FOOT** | the dispatch response is confined to hod 22-23 and to the import + gas rows; armed capability is **exactly 0.000000 MW** outside hod 22-23 (already verified pre-solve, re-verified on the bundle) |
| **G-DIR** | import at hod 22-23 **RISES**, by **more than 0 and less than the armed capability**, in every year the gate admits buckets; and 2023's move is the smallest of the four |
| **G-NOFLIP** | no non-target load-bearing criterion (C1, C2, C3b, C6, C8) flips PASS -> FAIL. C3c exempt (rubric v3.6). **C4 is supporting tier and is deliberately NOT a stop** — it is measured, reported at full magnitude and carried to the owner as the promotion question, exactly as caiso-268 did |
| **G-CTRL** | **form 4** — the committed keeper bundle `results/calibration/caiso_fuelvintage_span` is the control. **NO CONTROL SOLVE.** Earned by G-DRIFT below |

A gate may KILL this arm; none may promote it.

## §5 — G-DRIFT (rule 29(b)). ALL HUNKS INERT ⇒ G-CTRL FORM 4 IS VALID

`git diff 873f7564 origin/main -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference` — 8 files, every hunk classified:

| file | change | verdict |
|---|---|---|
| `data/raw/_validation-source/actual_lmp.json` | adds `rt_lw`/`da_lw` blocks; **10 changed leaves, ALL under `/ERCOT/2021` and `/ERCOT/2022`, ZERO CAISO leaves** (verified by leaf diff, not by eye) | **INERT** — another ISO's benchmark |
| `scripts/lib/holdout_policy.py`, `scripts/run_calibration.py`, `scripts/run_calibration_full.py` | the `[R-HOLDOUT]` removal (2026-09-09): gate/marker/flag deletions only | **INERT** — no dispatch path |
| `src/market_sim/config/constants.py` | **0 non-comment lines** (verified mechanically) | **INERT** |
| `src/market_sim/config/scenarios.py` | one new field `ercot_ep_gas_basis_receipts_fallback`, default `False`, absent from the CAISO keeper recipe | **INERT** — ERCOT-gated, default off |
| `src/market_sim/config/solve_surface_declared.py` | one NYISO-scoped declaration (`HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT: {"NYISO": ...}`) | **INERT** — another ISO |
| `src/market_sim/data/fuel/basis/ercot.py` | ERCOT-only, entirely gated on the default-off field above | **INERT** |

**All hunks INERT ⇒ form 4 valid, the keeper's committed bundle is the control, and no control solve is
spent.** (Noted in passing, not repaired here: `scripts/run_calibration_full.py --help` raises
`ValueError: unsupported format character` **on `origin/main` before this branch's changes** — a pre-existing
`scripts/` defect, verified by stashing this branch's diff.)

## §6 — SHARD PLAN (rule 32 `[R-SHARD]`). THE PARENT NEVER SOLVES

Four shards, ONE YEAR EACH, each <= 20 min, all pinned to this PRECOMMIT commit's full 40-char SHA:

| shard | year | branch | out-dir |
|---|---|---|---|
| Y2022 | 2022 | `claude/caiso269-2022` | `results/calibration/caiso269_lateevening_2022/` |
| Y2023 | 2023 | `claude/caiso269-2023` | `results/calibration/caiso269_lateevening_2023/` |
| Y2024 | 2024 | `claude/caiso269-2024` | `results/calibration/caiso269_lateevening_2024/` |
| Y2025 | 2025 | `claude/caiso269-2025` | `results/calibration/caiso269_lateevening_2025/` |

Each solves the **committed keeper recipe plus ONE flag**, via
`--replay-bundle results/calibration/caiso_fuelvintage_span --caiso-dsw-lateevening-clean`, so the arm is
provably the keeper recipe plus this one value and no recipe is rebuilt by parameter name.

**Rule 22 note, corrected against HEAD:** `[R-HOLDOUT]` was **REMOVED on 2026-09-09**; `holdout-freeze.json`
does not exist at HEAD and the `--holdout-authorized` flag **no longer exists** (its only two remaining
occurrences in `run_calibration_full.py` are stale comments). 2022 therefore needs **no authorization and no
flag**, and passing one would be a hard CLI error. 2019 and H1-2026 are not solved, scored or registered.
2020 and 2021 remain **blocked on DATA** (`data/raw/reference/caiso-supply-consistent-demand/` and
`frontend/data/backcast/bench/CAISO/` both start at 2022) — an unrestricted intake task for a separate session.

## §7 — WHAT IS NOT DONE HERE

No offer-curve multiplier of any size (rules 1/13 carve-out **not** exercised; no `authorized_price_tuning`
block). No adder, offset, haircut or load proxy. No pin to actuals. No re-sweep of the corridor ATC percentile.
No re-opening of the CT_PEAKER volume residual (owner ruling caiso-261, DO-NOT-REDO). No other ISO's keeper
shard, matrix shard, status part or calibration log is touched (rule 25 `[R-ISO-SCOPE]`); the six non-CAISO
matrix shards receive only the `.` n/a cell rule 28(c) requires of a new field.
