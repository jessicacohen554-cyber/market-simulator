# PRECOMMIT — miso-271: root cause of the R-MISO CC_REGULAR shortfall, and ONE structural fix (retire the statistical forced-outage term the measured windows now carry)

```
LANE    : miso-271 (off-queue, owner charter: "root-cause the 2021-2023 CC_REGULAR shortfall, then fix it structurally")
BASE    : main 7c778943 (+ this lane's probes cc555329)
KEEPER  : 2026-09-24-rmiso-arm-b-mid (results/calibration/rmiso_b_span, 2019-2025), git_sha bef12b51
ARM     : keeper recipe + wefor_residual=0.0, wefor_residual_groups=[CC_REGULAR, ST_CHP, ST_GAS]
CONTROL : keeper recipe at THIS SHA, 2019-2024 (G-DRIFT found LIVE hunks, §3); 2025 = keeper bundle (form 4)
SHARDS  : 7 arm (2019-2025) + 6 control (2019-2024), one year each (rule 36), pinned to this document's SHA
DATA    : DATA PROFILE: miso
DOF     : +0. No multiplier moves (offer_curve_by_group byte-identical, sha c5ab11d9b26d2abf).
```

## 1. Year set (rules 34(c) / 35(b))

Registered MISO runs at HEAD: one, the keeper, years **{2019 … 2025}**; nothing stamped to it. This lane solves
all seven.

## 2. Phase 0 — the root cause (zero LP)

Probes: `scripts/probes/_miso271_cc_decomp.py` (fleet-only rebuilds of the keeper recipe toggling one family at a
time), `scripts/probes/_miso271_wefor_ident.py` (the identification). Record:
`results/calibration/_miso271_wefor_ident.json`.

### 2.1 Where the class dispatch moved (committed hourly sidecars)

Keeper miso-268 → rmiso_b_span, CC_REGULAR P1 by offer band: every band falls by roughly the same share
(2023: committed −0.75, econc00…05 −0.43…−0.20 TWh; 2021 committed −2.13, econ −0.55…−0.42). A merit-order shift
would move the top bands and leave the committed band alone. A uniform fall across all bands is the signature of
**lost capability**, which matches CT_PEAKER and imports rising to replace it (RESULT §2).

### 2.2 Decomposition of available CC_REGULAR energy (`Σ pmax × availability`, TWh)

| year | keeper posture (K) | rmiso_b (B) | Δ | vintage (B − noV) | short-gas (B − noG) | measured HR (B − noH) |
|---|---:|---:|---:|---:|---:|---:|
| 2021 | 147.93 | 138.76 | −9.17 | **−4.80** | **−4.62** | 0.00 |
| 2022 | 171.46 | 162.37 | −9.09 | **−4.66** | **−4.52** | 0.00 |
| 2023 | 179.46 | 171.48 | −7.98 | **−4.35** | **−3.75** | 0.00 |

The measured heat rates move no MW. They make CC **cheaper** (capacity-weighted 9.28 → 9.07 in 2021, 9.00 → 8.88
in 2023), so they push dispatch the other way.

### 2.3 (a)/(c) Per plant, the vintage part (2023: −1,357.8 MW, −4.35 TWh)

| plant | Δ MW | Δ avail TWh | what it is |
|---|---:|---:|---|
| 67005 Magnolia Power | −678.7 | **0.000** | First EIA-923 generation is **Dec 2025** (0.10 TWh CS/NG). The canonical snapshot carried it at **zero availability** (COD ramp), so the membership delta is cosmetic. The vintage is right (rule 14). |
| 1004 Edwardsport | −481.2 | **−3.920** | §2.4 |
| 55358 Cottonwood | −7.8 | −0.567 (2021: −1.096) | Year-matched summer ratings and OP status (canonical marks 4 of 8 units OA). This is the vintage being right, and it is small. |
| 8031, others | ±8 | ±0.06 | |

### 2.4 (d) Edwardsport (1004) — IGCC, the classification disagrees across sources, and the keeper carried a phantom

* **EIA-860, every vintage 2019–2024:** CT1/CT2 (240.6 MW nameplate each) `Energy Source 1 = SGC`, `2 = NG`;
  **no summer rating on either CT**. The CA steam row carries **555 MW summer (595 in 2019–2022) against its own
  331.5 MW nameplate**. That is the whole block's net rating, reported on one row per EIA's IGCC convention.
  **Canonical (latest) 860 alone** lists the CTs as `NG` primary.
* **EIA-923 2023:** 3.27 TWh total, of which 1.18 TWh on NG (CT 0.76 + CA 0.42) and 2.09 TWh on SGC/BIT. The NG
  share is 19–36 % in 2019–2023 and 49 % in 2024–2025. The benchmark books the NG rows as **CC_REGULAR**
  (1.08–1.69 TWh/yr).
* **Keeper miso-268 (canonical snapshot):** 481.2 MW `CC_REGULAR` priced on **gas at 8.17 MMBtu/MWh** **plus**
  555 MW `COAL_BIT`, 1,036 MW in total for a ~555–618 MW machine. **The keeper's CC_REGULAR level therefore rode
  on 481 MW of phantom gas CC**, applied retroactively from the latest filing to every year.
* **rmiso_b (vintage):** 1,036 MW `COAL_BIT` at the measured 10.5 heat rate. The fuel classification is now
  year-true, but the **481 MW phantom is still carried, now as coal**.

**Verdict on (c)/(d):** the vintage is right on membership and fuel (rule 14). Part of the 2023 "regression" is
the keeper losing a phantom, not the model getting worse. **Routed, not fixed here** (§7): the block-capacity
phantom (481 MW coal, every year) and the NG share of a dual-fuel IGCC that the model cannot produce.

### 2.5 The defect this lane fixes: the short-gas arm STACKED on the statistical forced-outage term (rule 19)

In MISO's historic backcast, CC_REGULAR / CC_CHP / ST_GAS / ST_CHP carry the **full statistical WEFOR**
(`THERMAL_AVAILABILITY` base + age escalation; `wefor_residual` is `None`). Multiplied onto it are the measured
CAMPD windows: ≥ 5 d (`-unitroute`), maxgen, and since R-MISO the **1–4.9-day gas windows (`-shortgas`)**. The
field `wefor_residual` exists precisely for this: *"the CAMPD historic overlay … already carr[ies] every ≥ 5-day
outage … so the full statistical WEFOR double-counts them … capped at this short-outage residual — the < 5-day
events below the overlay's detector floor"* (`scenarios.py`, `wefor_residual`). When R-MISO armed the short-gas
family, **that residual became measured too**, and nothing retired the statistical term.
`unit_outage_short_windows_gas`'s own docstring claims it *"REPLACES a discard rather than stacking on anything"*.
That claim checks disjointness from the ≥ 5-day overlay only; it never checks the statistical term.

**What the statistical term still removes in the keeper (TWh/yr, fleet-only `noW − B`):**

| year | CC_REGULAR | CC_CHP | ST_GAS | ST_CHP |
|---|---:|---:|---:|---:|
| 2019 | 7.57 | 1.52 | 10.74 | 0.55 |
| 2021 | 7.96 | 1.56 | 9.39 | 0.58 |
| 2023 | 9.97 | 1.69 | 8.71 | 0.70 |
| 2025 | 9.74 | 1.58 | 9.97 | 0.54 |

**Identification — the frozen caiso-187 formula, on MISO's own fleet** (rule 25: CAISO's formula, not its values):
`residual_c = max(0, W_c − X_c)`. `W_c` is the statistical term's capacity-hour removal (`noW − B`). `X_c` is the
removal the LP's overlay block applies (`noO − B`, `outage_source = statistical`), which is the gating reading.
The direct count over the extracts is reported as a cross-check.

| year | CC_REGULAR W / X | CC_CHP W / X | ST_GAS W / X | ST_CHP W / X |
|---|---|---|---|---|
| 2019 | 0.0382 / 0.2392 | 0.0473 / 0.0487 | 0.0985 / 0.2369 | 0.1034 / 0.1682 |
| 2020 | 0.0363 / 0.2707 | 0.0487 / 0.0498 | 0.0938 / 0.2749 | 0.1036 / 0.1710 |
| 2021 | 0.0367 / 0.2768 | 0.0490 / 0.0626 | 0.0908 / 0.2880 | 0.1061 / 0.1791 |
| 2022 | 0.0403 / 0.1960 | 0.0505 / 0.0598 | 0.0966 / 0.2656 | 0.1081 / 0.1526 |
| 2023 | 0.0424 / 0.1861 | 0.0511 / **0.0475** | 0.0874 / 0.3240 | 0.1110 / 0.1420 |
| 2024 | 0.0426 / 0.1973 | 0.0491 / 0.0500 | 0.0931 / 0.3073 | 0.1128 / 0.1337 |
| 2025 | 0.0398 / 0.2157 | 0.0497 / 0.0694 | 0.0926 / 0.2366 | 0.0860 / 0.2770 |
| **residual = 0 all years?** | **yes** | **no (2023: 0.0036)** | **yes** | **yes** |

**Scope rule (fixed by the formula, not by any gate):** relieve exactly the short-gas classes whose residual is 0
in **every** year. That is **{CC_REGULAR, ST_GAS, ST_CHP}**, at `wefor_residual = 0.0`. **CC_CHP stays on the full
statistical model**, fail-closed: its measured record barely covers W in 2019, 2020 and 2024 and does not cover it
in 2023, consistent with CEMS-exempt cogeneration being unseen by CAMPD (caiso-197 excluded CC_CHP for the same
reason). **Coal is out of scope:** its short family is guarded to baseload units (CF ≥ 0.55), so coal's sub-5-day
residual is only partly measured. The coal stack is the same defect class and is routed (§7).

**Why this is new evidence for an `I` cell (rule 28(a)).** miso-149 marked `wefor_residual` MISO `I` on 2023–2025,
when `sfac` was **coal-only by construction** (its own §4, "all 987 rows … COAL"), so no gas sub-5-day record
existed and the statistical term was the only carrier of short gas outages. Since R-MISO (2026-09-24) that
premise is false. miso-149 also read `X ≥ W` as "immaterial". The formula it cited returns a **cap of 0**, and
the measured removal of a zero cap is 7.6–10.1 TWh/yr of CC_REGULAR availability. That is material by any bar.
caiso-197 later armed the identical construction (0.0, `{CC_REGULAR}`) as `K` in CAISO. That is not evidence
here (rule 28(d)), and it is cited only for the construction.

**Direction hazard, declared:** this adds gas capability, so price falls and CC dispatch rises. Both flatter MISO's
open gates (C3a +10–13 % high; C1 CC_REGULAR −10 TWh). The basis is rule 19 and nothing else. The arm stays in
whether it helps or hurts, and is reported at full magnitude.

## 3. G-DRIFT (rule 29(b)) — keeper `bef12b51` vs this SHA

`git diff bef12b51 <this SHA> -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference`: 57 files. Audited hunk by hunk (bef12b51 is **not**
an ancestor of main; R-MISO was rebased; its own branch changes are byte-identical at HEAD):

| hunk group | class | reason |
|---|---|---|
| R-NEISO `c265c1c3`: `_mid_vintage_exit_rows_from_window` (`eia860.py`) | **LIVE 2023, 2024** | `vintage_2023/2024` have no Retired-and-Canceled sheet. At bef12b51 the carry returned `None`; now it injects that year's whole-plant retirees from the canonical window parquet: **2023 +15 units / 958.9 MW** (Lansing 4, Baxter Wilson 1, Taconite Harbor, …), **2024 +39 units / 2,298.5 MW** (Rush Island 1,178, Grand Tower 511, LaO 384, …), each COD-ramped to its retirement month. The commit's "inert for every registered run" claim is false for this keeper. |
| COAL-SUB `8eaf34b5` / `05437cc0` (`coal.py`, `eia860.py`, `offer_curves.py`) | **LIVE 2019–2024** (unresolved-rank coal only) | Unresolved-rank coal now takes its EIA-860 fuel code's subclass (SUB → COAL_PRB curve 1.309/1.628, LIG → COAL_LIGNITE) instead of the `COAL` curve (= COAL_BIT). MW: 2,139.8 / 2,055.8 / 1,862.7 / 1,361.2 / 266.6 / 19.6 / 0 (2019→2025). The family folds (`artifact_class`) are equivalent by static review. |
| COAL-SUB scoring (`run_calibration_full.py`, `scripts/lib/benchmark_semantics.py`, `rubric_consts.py`) | SCORING-ONLY | Moves MISO C1 coal-class books for the unresolved plants in 2019–2024. The keeper is re-scored on the same code, so the comparison stays like-for-like. |
| R-SOCO-B BA membership; R-ERCOT bin HRs; CAISO 2019–21 intake; PJM RGGI; soco/nwpp reference data; `custom-bin-assignments.csv` (ERCOT rows) | INERT | other ISO's gate / data |
| R-NEISO `coal_scope` short-gas param; COAL-SUB config refusal / other-ISO tables; `fleet_only` return; `cache.py` docstring | INERT | byte-inert at this recipe's flag state / prose |

**LIVE ⇒ a control solve is earned for 2019–2024** (the rule's only trigger). 2025 has no LIVE hunk, so form 4
holds and the keeper bundle is its control. The control is also the promotion-safe comparator: the arm is
differenced against **same-SHA control legs**, never against the keeper, wherever a LIVE hunk exists.

Pinned inputs: `scripts/probes/_miso271_shard_check.py::INPUT_SHA` (all 11 re-verified byte-identical to R-MISO's
pins at this SHA).

## 4. The arm (exactly two fields; both are existing, registered `ScenarioConfig` fields — no code change)

```
python scripts/replay_keeper.py results/calibration/rmiso_b_span --years <Y> \
  --set wefor_residual=0.0 --set 'wefor_residual_groups=["CC_REGULAR","ST_CHP","ST_GAS"]' \
  --out-dir results/calibration/miso271_arm_<Y> --note "miso-271 arm <Y>: wefor stack retired"
```

Control (2019–2024): the same command with no `--set`, `--out-dir results/calibration/miso271_ctl_<Y>`.
The shard check is `_miso271_shard_check.py --groups CC_REGULAR ST_CHP ST_GAS` (arm) or `--control`.

## 5. Predictions (fixed before any shard; directions only)

* CC_REGULAR available energy +3.6–4.3 % every year; **CC_REGULAR TWh up**. CT_PEAKER and imports down, and ST_GAS
  up, in the years where the fleet is short (2021–2024).
* Load-weighted price **down** in every year, largest in high-load months. C3a moves toward the band in
  2019/2020/2023, and may overshoot negative in 2022 (−7.7 %) and 2024/2025.
* **C1 2023 CC_REGULAR:** direction toward the band. **Closing it is not predicted**: the 2.4 TWh needed is
  roughly the size of the CC dispatch response, and the Edwardsport NG share (~1.2 TWh) stays out of reach.
* Slack: the Max Gen hours (2023 h5654–5656, 2024 h5700–5706) should fall or vanish.
* 2025: smallest move (its stack is present, but its C1 is SKIPPED and the price already sits in band).

## 6. Decision rule (fixed now)

Recommend promotion iff every structural gate holds:

* **S-1 recipe:** every arm leg is keeper + exactly §4's two fields; every control leg is keeper + nothing;
  pinned inputs; hydro classifier; mechanism log lines.
* **S-2 single delta:** arm − control (2019–2024; 2025 vs keeper) is confined to the availability of
  {CC_REGULAR, ST_GAS, ST_CHP}. Checked zero-LP by a fleet-only rebuild: every other generator's availability is
  byte-identical.
* **S-3 slack:** no arm year has more slack than its control.

Gates C1–C8 are reported per year at full magnitude, both ways, and decide nothing (owner standard). The promotion
decision is the owner's (rule 31).

## 7. Routed, not fixed here

1. **Edwardsport IGCC block phantom:** 481 MW in every year (coal now, gas CC in the old keeper), plus the NG
   share the benchmark books as CC_REGULAR. A block-capacity reconciliation (CA-row summer = block net when the CT
   rows carry none) and a syngas/NG fuel choice, both MISO-lane.
2. **The coal statistical stack:** the same rule-19 defect, but short-coal covers baseload units only.
3. **The R-NEISO mid-vintage window injection (2023/2024)** changes MISO's keeper at HEAD. It is measured by this
   lane's controls and reported.
4. The out-of-lane items the charter lists (forecast gate-(a) row; the cross-ISO `mid_vintage_exit_carry` pairing;
   the `filter_revealed_outages` partial defect; the std-unitroute / short-coal non-reproduction). Status only.
