# PJM coal data-fidelity — heat-input MWh proxy + coal-cogen CHP/BTM holdout (2026-06)

**Date:** 2026-06-22. **Branch:** `claude/pjm-coal-fidelity-pjbyal`.
**Baseline:** `results/calibration/pjm_39` (dashboard *pjm 39 local-band*).
**Scope:** PJM only. **Status:** structurally-faithful CORRECTNESS fix,
measured-anchored, MAE-neutral. Not the +16 TWh over-run fix (that is PJM's
own price-formation / coal-cost issue — see `pjm-coal-overrun-decomp-2026-06.md`).

## The defect

CAMPD's `grossLoad` column is NaN for circulating-fluidized-bed, waste-coal
(culm) and industrial-cogen coal units — Virginia City (56808), Seward (3130),
the PA culm fleet (Scrubgrass 50974, Panther Creek 50776, Grant Town 10151,
John B Rich/Gilberton 10113, St Nicholas 54634, …), Eastman (50481). They report
`heatInput` + `steamLoad` instead. Two consequences:

1. **Invisible to any grossLoad-based CAMPD series** (the per-plant net series,
   `campd_active`): they look offline all year (~7–8 TWh to the PJM grid in 2024).
2. **The chp=Y coal subset is dispatched as cheap economic COAL_BIT/WC** — the LP
   follows LMP with coal that should follow a host STEAM contract.

## Fix 1 — heat-input → MWh proxy (`src/market_sim/data/campd.py`)

`fill_heatinput_proxy` reconstructs the hourly **net** MW of a grossLoad-blank
coal unit from its measured `heatInput` and an EIA-923-anchored effective heat
rate:

- **Heat rate** `HR = Σ(EIA-923 combustion netgen) / Σ(CAMPD heatInput)` per
  plant-year — measured, not fit. Validated: Virginia City 11.4, St Nicholas
  15.8, Seward 11.7 MMBtu/MWh (physical CFB / steam-extraction rates).
- **LEVEL** anchored to EIA-923 netgen, **SHAPE** to the hourly heatInput:
  `gross_mw[h] = heat_mmbtu[h] / HR`. Because HR is built from *net* generation
  the series is already net, so the proxy plants carry a parasitic factor of 1.0.
- **Gate** (`heatinput_proxy_report`, `recon_wmae`): a plant is reconstructed
  only when its monthly reconstruction reconciles to EIA-923 monthly netgen
  within a net-generation-weighted 15% and the heat rate is physical (6–40) and
  coal dominates (≥50% of combustion netgen). This accepts the pure CFB / culm
  fleet (Seward, Virginia City, Grant Town, Panther Creek, Scrubgrass, St
  Nicholas, John B Rich, Mayo, TES Filer City — 10 plants, ~7.3 TWh in 2024) and
  **rejects** partial-coverage multi-fuel hosts where CAMPD heat covers only part
  of the plant-year (Eastman: CAMPD heat May–Sep only vs year-round EIA netgen).
- A `mw_source` column (`measured` / `heat_proxy`) flags every row; existing
  `grossLoad` rows are byte-identical. PJM-gated in `_campd_hourly_frame`.

The proxy does **not** inflate the benchmark: it feeds the CAMPD net series
(`campd_active`, the per-plant hourly correlation); the class benchmark stays on
EIA-923, and the CAMPD backfill only fires for plants EIA-923 under-reports
(< 50 GWh) — none of the proxy plants qualify.

## Fix 2 — coal cogen through the existing CHP/BTM holdout (`fleet.py`, `_btm_frame`)

`coal_chp_overrides(iso, year)` detects coal cogens as **coal-generating PJM
plants whose EIA-860 `Sector` is a CHP host** (IPP CHP 3, Commercial CHP 5,
Industrial CHP 7 — `_EIA860_CHP_SECTORS`). This cleanly separates the cogens
(Eastman, St Nicholas, John B Rich, Covington, Pixelle) from utility/merchant
coal that EIA-923 also flags chp=Y but which is *not* a steam host — Spurlock
(6041, sector 1) and the merchant CFB/culm fleet (Seward, Virginia City, … —
sector 1/2) **stay economic grid generators**.

For a detected coal cogen the dispatch (`bins_to_fleet`) routes the coal bin
through the SAME machinery the gas cogens use — no new constants:

- **(a)** host self-supply held out of the LP at the sector's
  `CHP_BTM_PCT_BY_SECTOR` share (industrial/commercial 50%, IPP/merchant 35%),
  booked under the coal class in `btm.parquet` and subtracted from `classFull`
  on both sides by `render_calibration_html`;
- **(b)** the grid remainder carries a **steam-following must-run floor** — the
  plant's minimum monthly coal-class CF (EIA-923, scaled 0.85 / capped 75%, the
  same measure `derive_thermal_tranches` uses for CEMS-invisible cogens) — so it
  is must-run, not a price-following economic tranche.

## 2024 gate (vs pjm_39, same config — `_pjm_coalfidelity_run.py`)

| metric | pjm_39 | pjm_40 |
|---|---|---|
| gas | 372.06 (+4.9%) | 372.44 (+5.0%) |
| COAL_BIT model / resid | 114.21 / +1.8% | 113.94 / +2.0% |
| COAL_WC model | 5.64 | 5.18 |
| coal-tot resid | +2.2% | +2.4% |
| LMP (load-wtd) | ~27.1 | 27.11 |
| `btm.parquet` coal | — | COAL_BIT 0.465, COAL_WC 0.453 TWh |
| in-tolerance fails (2024) | 1 | 1 |

The predicted structural effect lands exactly: the coal cogen leaves the
economic stack (model COAL_BIT/WC drop), `btm.parquet` carries coal CHP, the
benchmark is slightly lower (host self-supply removed both sides), LMP is
unchanged and no new tolerance fails appear. The coal-tot residual is
MAE-neutral (+0.2 TWh: the benchmark drops marginally more than the model, since
removing capacity from cheap baseload coal sheds less than the generation-based
benchmark holdout). This is a faithfulness fix — coal cogen is now modeled as a
host-steam must-run rather than economic price-following coal — not an MAE win.

## Reproduce

```bash
python scripts/probes/_pjm_coalfidelity_run.py 2024 results/calibration/pjm_40_2024
python scripts/probes/_pjm_aswh_merge.py results/calibration/pjm_40 \
    results/calibration/pjm_40_2024
python scripts/probes/_pjm_score.py pjm_40
```
