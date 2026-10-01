# PRECOMMIT — pjm-h20: Card C, the CC/CT pair — CC econ rungs at PJM's own offer (LEVEL form) + CT_FAST measured max()-seam, all six PJM years (2026-09-24)

Card C of `docs/FINDING-pjm-h18-price-object-localised-2026-09-23.md` §5, chartered as a **pair**.
Written and pushed **before any solve**; the six shards are pinned to this commit's full SHA.

**Keeper (control):** `2026-09-23-pjm-h19-dbs-span` (2023–25, CALIBRATED 8/8) + folded
`2026-09-23-pjm-h19-dbs-touchpoint` (2020–22, NOT-YET). Bundles
`results/calibration/pjm_h19_dbs_{span,touchpoint}`, every leg solved at `2d57aa20`.
**Rules:** 1 `[R-STRUCT]`, 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`, 16/34(c) all years, 19 `[R-ONE-MECH]`,
21 `[R-DOF]`, 28 `[R-MECH-MATRIX]`, 29(b) G-DRIFT, 31 `[R-RETAIN]`, 32/34/36 shards.
**Phase 0 (zero LP):** `scripts/probes/pjm_h20_cardc_phase0.py` → `results/calibration/_pjm_h20_cardc_phase0.json`.

## 1. The arm — two existing default-off switches, zero new code, zero new parameters

| leg | switch | what it does |
|---|---|---|
| CC | `pjm_offer_midcurve_level_segments = ["CC_LIKE"]` | The keeper already prices CC_REGULAR econ rungs off PJM's published offer corpus, but in **floor** form (raise-only). LEVEL form makes the bid **equal** PJM's offer at the rung's own capacity share, so a fitted rung sitting above it comes down. |
| CT | `pjm_ct_measured_max_reprice = true` | CT_PEAKER econ/peak rungs bid `max(full P1 bid, PJM's own CT offer)`. Applied after the startup amortization, so the two never add together (rule 19; pjm-123 K3). |

Everything else is the keeper recipe, byte for byte. `offer_curve_by_group` is untouched, so the
rule-1 authorized price-tuning channel is **not used** (`authorized_price_tuning.used = false`).

## 2. Phase 0 — the CC half has a measured cause (it is not a level knob)

Method: `fleet_only` rebuild of the keeper recipe (the same `mc_base` the LP solved on), with pjm-h18's
marginal-band classification on the keeper's committed hourlies. Both switches are built with the
model's own builders in a local config copy.

| year | CC-marg. hours: model / actual $ | keeper marginal CC bid | **PJM's own offer at that rung** | CC econ MWh where fitted > PJM | reachable* |
|---|---|---|---|---|---|
| 2020 | 23.6 / 20.0 | 23.6 | **17.8** | 93 % | 91 % |
| 2021 | 35.7 / 34.7 | 35.9 | **30.2** | 91 % | 91 % |
| 2022 | 56.4 / 51.5 | 57.8 | **50.8** | 64 % | 92 % |
| 2023 | 28.0 / 24.4 | 28.5 | **22.6** | 82 % | 93 % |
| 2024 | 27.1 / 23.4 | 28.0 | **23.1** | 82 % | 92 % |
| 2025 | 39.3 / 37.4 | 40.0 | **33.1** | 75 % | 89 % |

\* share of CC-marginal hours whose marginal band is an `econ*` rung (the rows the switch reaches).

**The cause, named:** in the hours where CC sets the price, the keeper's CC offer is set by the fitted
`econ_low`/`econ_high` band multipliers, and those sit **$4.9–6.9/MWh above PJM's own published CC offer**
at the same rung in every year. The armed floor can never pull them down. That is a rule-14 measured
identification. The source is the committed PJM energy-offer corpus
(`derive_pjm_offer_midcurve.py`, frozen, rule 20), and the same surface has a pooled table for
forward years. **No new parameter, no residual fit.**

The CT half (pjm-h17 §5, re-measured on this keeper):

| year | CT MW priced | capacity-weighted `mc_base` | PJM's own CT offer | MWh where PJM > `mc_base` |
|---|---|---|---|---|
| 2020 | 22,831 | 42.7 | 37.4 | 63 % |
| 2021 | 22,822 | 64.6 | 64.3 | 68 % |
| 2022 | 22,822 | 99.5 | 138.4 | 85 % |
| 2023 | 22,829 | 51.4 | 86.2 | 91 % |
| 2024 | 22,836 | 48.9 | 79.3 | 91 % |
| 2025 | 22,835 | 63.4 | 127.5 | 94 % |

The CT lift is an **upper bound**: the max() is taken against the full P1 bid, which already carries
the startup amortization (not observable without an LP).

**Where the CC leg lands (static, marginal band only, $/MWh contribution to the annual mean):**

| year | bottom 50 % | p50–p95 | top 5 % | sum |
|---|---|---|---|---|
| 2020 | −1.26 | −1.79 | −0.14 | −3.19 |
| 2021 | −1.52 | −1.52 | −0.16 | −3.20 |
| 2022 | −2.37 | −0.96 | −0.03 | −3.36 |
| 2023 | −1.66 | −0.99 | −0.05 | −2.70 |
| 2024 | −1.30 | −0.68 | −0.01 | −1.99 |
| 2025 | −1.26 | −1.29 | −0.05 | −2.60 |

It lands where pjm-h18 put the error (bottom half +$2.6 to +$4.8) and not in the top tail. Static =
no redispatch, so these are the **largest** plausible moves, not predictions.

## 3. Rule 28(a) — why this re-tests adjudicated cells

- **Level CC_LIKE** was refuted in pjm-121 §5 **as the C3a-2025 dispersion lever** (it narrows the
  within-bin CC offer spread). The object here is different: a CC-marginal level error present in
  every year (pjm-h18 §3, new evidence), located in §2 to fitted rungs above measured.
- **CT max()-seam** was refuted in pjm-123 as part of the three-leg **dispersion composite**
  (K1 gradient wrong-signed). It has **never been solved**. New evidence: pjm-h17 §4–5 (the idle
  22.8 GW shelf in the missed hours) and pjm-h18 (CT/ST-marginal hours low in every year but 2020).
- **Risk carried over, stated:** pjm-123 found PJM's measured CT and CC surfaces are cheapest in
  the tightest net-load bin. The pair corrects the level **by marginal family**, not the within-bin
  slope, so C3b and the top tail may not improve. That is a prediction, not a reason to stop.

## 4. G-DRIFT `2d57aa20` → pin (rule 29(b)) — zero LP

| file | change | PJM |
|---|---|---|
| `src/market_sim/config/constants.py` | `ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE = {"SOCO": True}` | INERT: SOCO-keyed; `.get("PJM", False)` |
| `src/market_sim/config/solve_surface_declared.py` | declares the above, `{"SOCO": …}` | INERT: per-ISO hash, PJM's key unchanged |
| `scripts/run_calibration_full.py` | `_eia860_current_ba_recoded`, gated on the constant | INERT: never read for PJM |
| `scripts/lib/benchmark_semantics.py` | `EIA930_GAS_FOLD_REFUTED = {"SOCO"}` | INERT: benchmark-only, SOCO-only |

**All hunks INERT ⇒ form 4 valid; the committed keeper bundles are the LP control.** Both switches
touch every year, so no year is a free same-HEAD control this time. `--rebuild-benchmark` is run on
the arm, and the keeper is re-scored on the same benchmark (carried correction 4). Benchmark drift is
measured by diffing `status/PJM.js`.

## 5. Population the pair CANNOT reach — named before the solve

1. **CC committed-band marginal hours:** 7–11 % of CC-marginal hours. Level form touches `econ*` only.
2. **ST_GAS- and coal-marginal hours.** LONG_RUN stays floor form. 2022's ST term (−7.30) is untouched.
3. **CC_CHP / CT_CHP:** not mapped to the surface.
4. **CT rows where PJM's offer is below the model bid:** 2020 (37 % of CT MWh) and 2021 (32 %). The
   max() only raises, so 2020/2021 CT barely move.
5. **Scarcity above ~$200:** Winter Storm Elliott (Card B), reserve/LP tightness (G-20b).
6. Hours with no measured surface coverage (NaN target) stay unpriced.

## 6. Gates and predictions — declared before any solve

Decided on structure (rule 1). A failed gate does not kill the arm; a passed gate does not promote it.

- **G1 liveness** (sidecars vs control, with the control's hour classification):
  (a) load-weighted price in the control's CC-econ-marginal hours **falls by ≥ $1.50 in every year**;
  (b) CT_PEAKER P1 TWh **does not rise** in any year and **falls** in 2022–2025.
  (c) Shard self-check before the solve: the §2 census reproduces for its year (±0.01 share, ±$0.1).
- **G2 targeted — predictions:**
  - CC-marginal-hour error (control's classification) **shrinks in every year**. It may cross zero:
    the static floor of the move puts it between −13 % and −1 %.
  - The bottom-50 % error term (+2.6…+4.8) **falls by ≥ $1.0 in every year**.
  - **C3a, stated plainly: the in-sample C3a may move EITHER way.** The CC leg alone lowers every year
    (static −2.0 to −3.4 $/MWh). The CT leg raises it by an amount I cannot measure without an LP.
    - 2020: +14.5 % → **between −1 % and +12 %** (likely nearer PASS).
    - 2023 (+0.6 %) and 2024 (−3.0 %): move negative. CC-only static −8.5 / −6.3 points.
    - **2025 (−6.8 %) may breach −10 %**: CC-only static is ≈ −12.4 %, and it stays inside the bar
      only if the CT leg lifts the mean by ≥ ~$1.3.
    - 2022 (−10.4 %) may get worse (the CC leg lowers its bottom half) unless the CT leg offsets.
      Elliott is untouched.
    - **Under rule 1 a C3a regression is not grounds to reject the pair**: it would mean the
      in-sample pass was cancellation (pjm-h18 §0), which is what this card exists to expose.
  - **C1 direction:** CC cheaper ⇒ CC_REGULAR up, COAL_BIT down. That helps 2020/2021 COAL_BIT
    (over by 25.5/19.2 TWh) and hurts 2022 CC_REGULAR (over by 11.1). The CT max() ⇒ CT_PEAKER down,
    which hurts 2021 (12.8 vs 21.5) and risks 2023 (20.4 vs 21.7).
  - Determination: span may leave CALIBRATED; touchpoint stays NOT-YET (Elliott).
- **G3 no silent breakage:** full rubric C1–C8, every year, at full magnitude vs the control on the
  same benchmark. D-1/D-2/D-4 run once per bundle, sequentially.

## 7. DOF (rule 21)

Zero new free parameters: both switches are scopes on the frozen, committed offer corpus. Where the
surface has coverage, the level form **retires** the CC_REGULAR `econ_low`/`econ_high` multipliers'
effect on the econ rungs. The multipliers still order tranches, which sets each row's share. That
removes fitted influence; it adds none.

**Rule 13:** `pjm_ct_measured_max_reprice` is registered in `_BACKCAST_ONLY_OVERLAY_FIELDS`. Like the
keeper's own `gas_monthly_actuals`, it is admissible in backcast and is never the forecast method.
The level form is not on that list (pooled forward table). No forecast config moves.

## 8. Shards (rules 32 / 34 / 36)

Six, one per year, each pinned to this commit's full SHA. Out-dir `results/calibration/pjm_h20_cardc_<y>`,
branch `claude/pjm-h20-cardc-<y>`.

1. `git rev-parse HEAD` must equal the pinned SHA, else STOP.
2. `uv sync`. Use `.venv/bin/python` if `python3 -c "import numpy"` fails.
3. `hydrate_data.py --profile pjm`, then `regenerate_clean.py` (full; `emissions-unit-annual` OOM is harmless).
4. `scripts/data/fetch_pjm_da_virtuals.py --years <y> --feeds hrl_da_incs_decs`.
5. `scripts/data/curate_hydro_plant_modes.py --iso PJM` must report **57 run-of-river-class of 82**, else STOP.
6. Self-check (G1c): `scripts/probes/pjm_h20_cardc_phase0.py <y>` must reproduce §2 for that year, else STOP.
7. `scripts/replay_keeper.py <control> --years <y> --set 'pjm_offer_midcurve_level_segments=["CC_LIKE"]'
   --set pjm_ct_measured_max_reprice=true --out-dir results/calibration/pjm_h20_cardc_<y>
   --note "pjm-h20 Card C pair, <y>"`.
8. Commit the full bundle, `dispatch/<y>_P1.parquet` included, via a `.gitignore` negation and a plain `git add`. Push.

| year | control bundle |
|---|---|
| 2020, 2021, 2022 | `results/calibration/pjm_h19_dbs_touchpoint` |
| 2023, 2024, 2025 | `results/calibration/pjm_h19_dbs_span` |

**Retrievability (rule 34(e)):** the parent fetches every leg, composes, and lands the registered
bundles on `main` before this lane's PR merges. Shard SHAs are provenance only.

## 9. Not in this lane

Card B (Elliott) awaits the owner. The D-4 coal conduct FAILs (1384/2023, 7213/2021–23) and SPP-71's
`coal_sync_ensemble_level` (fresh U) stay open. `measured_offer_surface` (R) is not re-opened.
