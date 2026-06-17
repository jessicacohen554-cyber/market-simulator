# CAISO "everything out of tolerance" — root-cause diagnosis (2026-06-17)

Branch: `claude/caiso-model-diagnostics-qcc173`. Trigger: the CAISO dashboard
shows ~every resource class out of tolerance, large volume errors, and LMP far
off. This doc separates **benchmark/framework artifacts** (most of the red) from
**genuine model error** (one item), with live numbers from a fresh on-`main`
run.

## TL;DR

The model on current `main` is **not** broken for the generation mix. The
"all-classes-out-of-tolerance" view is mostly:

1. **A broken 2025 calibration reference** (incomplete EIA-923 vintage) used as
   the dashboard per-class benchmark, and
2. **A systematic EIA-923 vs EIA-930 wind under-count** in the per-class
   benchmark every year (the model is right, the benchmark is low), and
3. **A stale, pre-fix dashboard bundle** for the older CAISO runs.

The **one genuine, large model error is the LMP** (over-priced midday floor:
mean $57 vs $33, min $28 vs −$58, zero negative hours) — already diagnosed in
`AUDIT-caiso-structural.md` and fixed-but-default-off (`caiso-5-ra-floor`).

## Evidence

### Fresh run on current `main` (2024, `--commitment --priced-interchange`, no extra flags)

| class | model TWh | EIA-923 ref | EIA-930 (e930) | verdict |
|---|---|---|---|---|
| gas (cc+ct+st) | **67.95** | 67.68 | 85.4¹ | **<0.5% vs 923 — PASS** |
| gas_cc | 58.22 | 59.16 | — | ok |
| gas_ct | 6.63 | 8.37 | — | mild under |
| gas_st | 3.09 | 0.15 | — | **over (real, small)** |
| nuclear | 18.20 | 18.38 | 18.35 | PASS |
| solar | 47.91 | 49.46 | 44.64 | between the two refs — ok |
| wind | 20.29 | 15.42 | 20.06 | **matches 930; 923 ref is low** |
| import | 35.65 | (≈30.8) | — | mild over (+4.9) |

¹ EIA-930 `NG: NG` silently absorbs ~11 TWh geo+bio (CISO reports neither); the
correct gas benchmark is EIA-923 67.68 — which the model matches. (Established in
`AUDIT-caiso-structural.md`; re-confirmed here.)

So on `main`, 2024 mix is in tolerance against the *right* benchmarks. The
dashboard's red is not coming from the model.

### Root cause 1 — the 2025 reference is an incomplete vintage (framework bug)

`scripts/build_calibration_reference.py::_eia923_generation()` sums whatever rows
exist in `inputs/raw-data/f923_<year>*.zip` with **no completeness guard**. The
2025 zip is the early-release monthly survey:

| f923 vintage | CISO plant-rows | total net gen |
|---|---|---|
| 2024 | 1,814 | 185.7 TWh |
| **2025** | **542** | **136.6 TWh** |

So the 2025 `generation_twh` reference reads **wind 4.24, solar 39.76, hydro
12.42, CT_PEAKER 2.14, gas_ct 4.90, biomass 1.23** — every class *drops*
year-over-year while demand is full (224 TWh), which is physically impossible.
This is the reference stored in `calibration_reference.json` **and** copied into
the dashboard per-class benchmark `frontend/data/backcast/bench/CAISO/2025.json.gz`
(`classFull`). Scoring any 2025 run against it manufactures the headline errors
(wind +367%, gas_st +2500%, solar +25%, hydro). The *same* bench file already
carries sane `e930` totals (wind 19.82, solar 49.7, gas 79.03) — the model
matches those.

### Root cause 2 — EIA-923 CISO wind is under-reported every year

classFull/EIA-923 wind = 13.94 / 15.42 / 4.24; EIA-930 wind = 16.4 / 20.06 /
19.82. The model (≈16.5 / 20.3 / 19.8) matches EIA-930. The per-class dashboard
gate scores wind against the low EIA-923 number → "+19% / +32% / +367% wind"
that is a benchmark artifact, not a model error. (Solar shows the mirror image:
EIA-930 grid solar nets BTM and sits ~5 TWh *below* EIA-923 whole-fleet; the
model sits between them.)

### Root cause 3 — stale, pre-fix dashboard bundle

The committed older CAISO dashboard data (`caiso-2-priced-ix`, 2026-06-12)
predates the border-carbon-per-tranche-EF fix now on `main`, so it over-imports
massively (2023 import 61.65 TWh, gas −41%). The fresh on-`main` run cuts 2024
import 49.3 → 35.7 TWh and lifts gas 54.5 → 67.95. The keeper improvements (RA
must-offer floor `caiso-5-ra-floor`, 2025 hydro repin) live only in **gitignored
scratch bundles** (`/results/calibration/caiso_floor*`, `caiso_tune*`) that do
not survive a fresh container — so re-runs regress to the worst old data unless
the keeper is regenerated.

### The one genuine large error — LMP floor (2024, load-weighted system)

| | mean | min | p1 | p5 | neg hrs |
|---|---|---|---|---|---|
| model (`main`) | 57.43 | 28.00 | 36.00 | 38.82 | 0 |
| actual RT | 32.94 | −57.84 | −40.40 | −14.02 | many |

The midday floor never decommits below ~$28 and never goes negative. Fully
diagnosed in `AUDIT-caiso-structural.md` (longness / marginal-offer problem) and
`RESULTS-caiso-ra-mustoffer-floor.md` (RA floor collapses min 28→0); pushing the
belly negative is Session B (`NEGRENEW-caiso-findings.md`). Both built,
default-off, not yet a committed keeper.

### Minor genuine items

- **gas_st over-run** +3 TWh vs ~0.1 (CA gas-steam is nearly retired). ST_GAS is
  clearing too cheap / staying committed; small, merit-order.
- **biomass over-run** ~5.4 vs ~3 (kept as LP units that over-run).
- **2023 over-import** +14.5 TWh in the cheap-gas year (static import tranche
  prices sit below domestic gas at $2.54 Henry Hub; no per-year ladder).

## Resolution plan (prioritized)

**P0 — make scoring honest (framework, surgical, clearly correct; unblocks
everything):**

1. **Guard `_eia923_generation` against incomplete vintages.** Detect a partial
   f923 release (e.g. CISO net gen < ~90% of demand, or plant-row count well
   below the prior year) and, for that year, fall back to the EIA-930 grid
   totals (already loaded) for the affected classes rather than emitting a
   silently-truncated reference. Rebuild `calibration_reference.json` and the
   CAISO `bench/*.json.gz`. Add a regression test on the 2025 vintage.
2. **Score CAISO wind/solar against EIA-930 grid totals** (the model is
   grid-side), not the under-reported EIA-923 CISO wind. Either switch the
   per-class gate's renewable benchmark to `e930` or document the 923/930 split
   and widen the renewable tolerance accordingly. (Mirrors the existing
   gas→EIA-923, 2025-gas→EIA-930 conventions in `_session_score.py`.)

**P1 — refresh the dashboard so it reflects `main`:**

3. Regenerate and commit a current CAISO keeper bundle (RA must-offer floor
   `--caiso-gas-commitment-floor 0.80` + `--hydro-backfill-year 2024
   --hydro-eia930-monthly`, 3 years) via the `calibration-report` skill, so the
   live dashboard stops showing the stale pre-fix over-import state.

**P2 — the genuine model fix (LMP floor):**

4. Promote the **RA must-offer floor + negative renewable offers** (Sessions A/B,
   already built and tested, default-off) to the committed CAISO keeper config in
   `scripts/run_calibration.py::_calibration_config`. This collapses the $28 floor
   toward $0/negative and reproduces CAISO's negative midday prices — the real
   structural fix, validated against EIA-923 gas (watch that the surplus
   exports/curtails, not pads gas).

**P3 — minor / cleanup:**

5. CAISO per-year import ladder (`IMPORT_TRANCHES_BY_YEAR`) to fix the cheap-gas
   2023 over-import (mechanism already supports `year`).
6. gas_st / biomass over-run: investigate ST_GAS commitment & biomass must-run
   level (inject biomass as must-run at EIA-923 level, like geothermal).

## Reproduce

```
python scripts/run_calibration_full.py --iso CAISO --year 2024 \
  --commitment --priced-interchange --out-dir results/calibration/diag_2024
# gas total 67.95 (EIA-923 67.68); LMP mean 57.4 min 28 p5 38.8, 0 neg hrs
```

Run single-year (~9 min); two concurrent CAISO solves OOM a 15 GB box (per
`claude.md` rule 11 caveat) — the parallel 2023 leg was OOM-killed, run it alone.

## Resolution status (implemented this session)

- **P0 — DONE.** `actuals_source` routes wind (and solar) to EIA-930; the
  renderer scores wind against EIA-930 (was omitted); `build_calibration_reference`
  guards incomplete vintages (per-fuel wind/solar→EIA-930 below 80%, whole-vintage
  `eia923_incomplete` flag below 90%). `calibration_reference.json` patched
  surgically (CAISO 2024 wind 15.42→20.06, all-ISO 2025 wind→EIA-930; 2023 and
  non-CAISO 2024 byte-identical). Tests: `test_calibration_reference_guard.py`,
  updated `test_calibration.py`.
- **P1 — DONE.** Dashboard keeper refreshed: `caiso-6-floor-negrenew` replaces the
  stale `caiso-2-priced-ix` over-import bundle (then `caiso-7` after the P3 gas_st
  fix). Run report scores wind vs EIA-930.
- **P2 — DONE.** `_calibration_config` defaults the RA must-offer floor (frac 0.80)
  + negative renewable offers ON for CAISO (other ISOs byte-identical); the CLI
  flags are tri-state (`--no-…` for a baseline probe); `run_config.json` now records
  the effective config. Validated 3-yr: 2024 gas 71.3 vs EIA-923 67.7 (+5.3%),
  LMP min 28→0 every year. Test: `test_caiso_keeper_defaults.py`.
- **P3 (partial) — DONE.** The RA floor is scoped to gas_cc/gas_ct; the
  near-retired gas_st boilers (real ~0.15 TWh) are excluded (they were inflated
  1.72→3.66 TWh by the floor). Test: `test_gas_steam_is_excluded_from_the_floor`.

### P3 — deferred (with rationale)

- **Per-year import ladder (`IMPORT_TRANCHES_BY_YEAR["CAISO"]`)** for the 2023
  over-import (+14.5 TWh): the mechanism exists, but a defensible ladder must be
  derived without the bundle-mode **circularity** the audit flags (the deriver
  anchors to the model's own — miscalibrated — price duration curve), and it
  needs a 3-yr re-validation. Larger than a surgical fix; left for a dedicated
  import-calibration pass.
- **Residual gas_st (~1.7 TWh) and biomass (~5.4 vs ~3) over-run:** both are
  merit-order / offer-curve level, which the structural docs (`AUDIT-…`,
  `NEXT-…`) explicitly defer to a separate offer-curve phase — not changed here
  to avoid chasing the fit through an unvalidated merit-order move
  (`claude.md` rule #1). Biomass-as-must-run (like geothermal) is the candidate
  but shifts merit order, so it belongs in that phase with its own validation.
- **Mean LMP level (~$54 vs ~$33):** the floor fixed the midday *floor* (min→0);
  the remaining level gap is the broad offer-curve calibration, out of scope for
  a structural diagnosis.
