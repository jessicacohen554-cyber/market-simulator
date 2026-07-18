# PJM outage re-gate — net-load-filtered outages (2026-06)

> **Update 2026-06-22 (`claude/cross-iso-outage-local-band-yhyu1f`): LOCAL
> (seasonal) net-load band — new keeper `results/calibration/pjm_39` (dashboard
> `pjm 39 local-band outage`), supersedes pjm 38.** The annual band below
> over-cut genuine multi-week shoulder CCGT maintenance; `high_load_mask` now
> measures the high-load percentile over a centered rolling ±30-day window
> (commit `152bb99`; see `docs/ercot-outage-sensitivity-middle-ground-2026-06.md`).
> The pjm-38 config was re-solved **byte-faithfully** (same probe scripts,
> `retiree_cems_cap=True`) on the regenerated local-band PJM outages — **only the
> outage input changed**. Recovering shoulder outages puts MORE coal/CC offline
> in shoulder months, so the local band partially UNWINDS the annual band's
> over-availability: it is a **strict improvement over pjm 38 on every axis.**
>
> | metric (model vs actual RT) | 2023 | 2024 | 2025 |
> |---|---|---|---|
> | LMP demand-wtd mean: pjm38 → **pjm39** (actual) | 28.12 → **28.29** (28.44) | 26.17 → **26.12** (29.53) | 34.63 → **35.01** (42.89) |
> | hourly hub MAE: pjm38 → **pjm39** | 8.12 → **7.94** | 10.49 → **9.75** | 15.82 → **13.37** |
> | coal-tot resid: pjm38 → **pjm39** | +17.3% → **+11.4%** | +13.9% → **+3.0%** | +22.8% → **+11.1%** |
> | net-export resid: pjm38 → **pjm39** | +69% → **+31%** | +65% → **+17.5%** | +204% → **+93%** |
> | hrs >$200 (model / actual) | 0 / 6 | 0 / 18 | 0 / 59 |
> | in-tolerance fails: pjm38 → **pjm39** | **11 → 7** | | |
>
> Tail unchanged (model still does not fire PJM's scarcity tail — the documented
> separate coal-cost/offer issue, neither collapsed nor re-inflated); summer not
> under-fired (2023 Jul/Aug model 29.1 vs actual 31.8). The residual coal
> over-run + over-export is PJM's forecast-native coal issue
> (`pjm-coal-mustrun-floor.md`), here made **less** visible than the annual band,
> not newly introduced — still the next frontier (offer-curve / coal-cost
> retune), not chased in the outage step. Reproduce: identical to the pjm 38
> commands below (the local-band outages are the committed state of
> `data/raw/campd-*-PJM.csv`); merged into `results/calibration/pjm_39`.

**Status (annual band — superseded 2026-06-22, see above):** done. **Keeper was
`results/calibration/pjm_38`** (dashboard label
`pjm 38 outage-regate`), promoted from the prior keeper
`pjm_37` / `pjm-36-retiree-cems`.
**Trigger:** commit `b0c41cb` (branch `claude/ercot-scarcity-tuning-handoff-nl1y3m`),
the cross-ISO revealed-availability (high-net-load) outage filter — see
`docs/multi-iso/cross-iso-outage-regate-handoff-2026-06.md`.

## What was done

The pjm-36 keeper config (`retiree_cems_cap=True`, the per-unit retiree COD fix +
within-window retiree CEMS cap) was re-solved **byte-faithfully** from
`results/calibration/pjm_37/run_config.json` (driver
`scripts/probes/_pjm_retiree_run.py`, one year per solve, merged with
`_pjm_aswh_merge.py`), changing **only** the outage input — both regenerated PJM
files (`data/raw/campd-outages-PJM.csv` facility + `campd-unit-outages-PJM.csv`
unit) are picked up automatically from `data/raw/`. No offers/curves/flags were
re-tuned in this step (the methodology rule: isolate the outage effect).

The net-load filter cut PJM capacity-weighted outage GW-days ~46%
(37,889→20,304), concentrated in shoulder months (Apr/Oct), with summer binding
outages preserved (Jul −728 outage-hrs).

For the comparison the old keeper was reproduced faithfully on the **pre-filter**
outages (`git show b0c41cb^:…`), confirming the published pjm-36 numbers to 2
decimals (load-wtd LMP 30.09/28.06/37.81, coal-tot 129.2/119.8/149.4); the
pre-filter outages were then restored to the committed (filtered) state.

## Result — the gate is NOT clean; accepted as forecast-native

| metric (resid vs actual) | 2023 | 2024 | 2025 |
|---|---|---|---|
| coal-tot: old → new | +6.8% → **+17.3%** | −2.2% → **+13.9%** | +2.4% → **+22.8%** |
| gas: old → new | +1.8% → +4.9% | +3.9% → +5.7% (FAIL) | +3.0% → +3.7% |
| net-export: old → new | +11.6% → **+69%** | −11.8% → **+65%** | +28% → **+204%** |
| in-tolerance fails | **3 → 11** | | |
| LMP load-wtd mean: old → new | 30.09 → 28.12 | 28.06 → 26.17 | 37.81 → 34.63 |
| LMP load-wtd MAE: old → new | 8.30 → 8.12 | 10.46 → 10.49 | 15.06 → **15.82** |
| actual RT (load-wtd) | 29.64 | 31.24 | 46.02 |
| hrs >$200 (model, full yr) | 0 → 0 | 0 → 0 | 0 → 0 |

**Diagnosis.** Fewer shoulder/winter outages → more available coal/CC → PJM's
**cost-based LP runs the freed cheap take-or-pay coal** (and CC) and exports the
surplus. This *amplifies* PJM's already-documented, forecast-native coal
over-run + over-export (`docs/multi-iso/pjm-coal-mustrun-floor.md`): the old
(higher) outages were partly **masking** the over-run by forcing shoulder coal
offline. Prices cool as the cross-ISO handoff predicted, but because PJM is
already *under* on LMP in 2024/25, the cooling moves **away** from actuals
(MAE flat-to-worse) rather than helping.

**Decision (user, right-structure-first).** The net-load filter is the
forecast-defensible **exogenous** outage input (keys on net load, not the price
residual), so it is adopted as the keeper input despite the worse fuel-mix /
export / LMP gates — those are the **forecast-native** coal-over/over-export the
project already treats as a settled, separate issue, here made more visible
rather than newly introduced. Right structure (the correct input) first; the
coal-over/export is the **next** frontier (offer-curve / coal-cost retune), not
chased in the outage step.

## Reproduction

```bash
# keeper = pjm_38 (uses the committed net-load-filtered outages in data/raw/)
python scripts/probes/_pjm_retiree_run.py 2023 results/calibration/pjm_38_y2023
python scripts/probes/_pjm_retiree_run.py 2024 results/calibration/pjm_38_y2024
python scripts/probes/_pjm_retiree_run.py 2025 results/calibration/pjm_38_y2025
python scripts/probes/_pjm_aswh_merge.py results/calibration/pjm_38 \
    results/calibration/pjm_38_y202{3,4,5}
python scripts/probes/_pjm_score.py pjm_38
python scripts/archive/analyze_lmp_residual.py results/calibration/pjm_38

# old-keeper baseline: restore pre-filter outages first
#   git show b0c41cb^:data/raw/campd-outages-PJM.csv > data/raw/campd-outages-PJM.csv
#   git show b0c41cb^:data/raw/campd-unit-outages-PJM.csv > data/raw/campd-unit-outages-PJM.csv
#   …solve as above… then restore: git checkout data/raw/campd-*-PJM.csv
```
