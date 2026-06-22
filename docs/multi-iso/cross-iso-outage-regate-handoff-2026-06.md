# Cross-ISO outage re-gating — per-ISO session handoffs (2026-06)

**Date:** 2026-06-21
**Trigger branch:** `claude/ercot-scarcity-tuning-handoff-nl1y3m`, commit
`b0c41cb` (`outages: apply net-load filter cross-ISO`).

> **Update 2026-06-22 (`claude/ercot-outage-sensitivity-j6a0p5`):** the
> high-load band described below was a *single annual* net-load percentile, which
> over-cut — it deleted genuine multi-week CCGT **shoulder** maintenance outages
> (they never span an annual-top hour). `high_load_mask` now measures the
> percentile over a **centered rolling ± `WINDOW_DAYS` (30) window** (the LOCAL /
> seasonal band; `--high-load-window-days 0` restores the annual band). ERCOT was
> regenerated on it (CC outage GW-days 2906 → 5997, still −36 % vs unfiltered,
> short economic-idle still dropped, summer preserved). Every per-ISO re-gate
> below now picks up the local band automatically on regen. See
> `docs/ercot-outage-sensitivity-middle-ground-2026-06.md`.

> **DONE 2026-06-22 (`claude/cross-iso-outage-local-band-yhyu1f`): all five
> non-ERCOT ISOs re-gated onto the LOCAL band.** All outage CSVs regenerated on
> the default local band (PJM facility + unit; CAISO/NYISO/NEISO/MISO unit). Each
> keeper re-solved byte-faithfully (only the outage input changed):
> - **PJM** → new keeper **pjm 39** (supersedes pjm 38). STRICT improvement on
>   every axis: coal-tot resid +17.3/+13.9/+22.8% → +11.4/+3.0/+11.1%, net-export
>   +69/+65/+204% → +31/+17.5/+93%, hourly MAE 8.12/10.49/15.82 → 7.94/9.75/13.37,
>   in-tol fails 11→7; LMP firmer toward actual; tail (hrs>$200 0/0/0) unchanged.
> - **NEISO** → new keeper **neiso 24** (supersedes neiso 23). Near-no-op
>   (keeper headroom): CC_REGULAR/gas/LMP ~identical, tail 0/0/13 preserved.
>   CALIBRATED-WITH-CAVEATS (attestation carried forward).
> - **CAISO** → **caiso 19** (correct forward input; right-structure-first
>   keeper). Wash vs caiso 18: body firms marginally 41.17→41.45 (recovered
>   outages, gas body), neg tail 407 preserved, no scarcity over-fire, mix
>   marginally better (CC_REGULAR 53.03→52.68). Stays NOT-YET on the documented
>   body/midday COMMITMENT overprice (orthogonal to outages).
> - **NYISO** → **nyiso 17** (local-band re-solve of the nyiso-16 daily-Transco
>   config; keeper ambiguity resolved with the user to the nyiso-16 lineage).
>   Near-equivalent (keeper headroom): canonical gate vs actual RT 2023 +6.16
>   (documented winter/shoulder over, fix #1(b) data-blocked), 2024 +1.60 (Dec
>   -27.18 = the mechanism-B RCPF winter tail), 2025 +0.46; model hrs>$200
>   1/0/57. NOT-YET, same structural class as nyiso-16. **Keeper-of-record
>   nyiso 11 still stands**; this run carries the forward-correct local-band
>   outage CSV into the daily-Transco lineage. A byte-clean A/B vs nyiso-16 is
>   basis-limited (its bundle parquets are gitignored), so reported on absolute
>   gate.
> - **MISO** → CSV regenerated only (no keeper; forward input).
>
> All registered on the dashboard (top-15 per ISO honoured). The shared
> `high_load_mask` change is the same for every ISO; the magnitude of the
> re-gate scales with each keeper's dispatch headroom (large for PJM, near-zero
> for NEISO).

## What changed (read first)

The **revealed-availability (high-NET-LOAD) outage filter** that fixed ERCOT's
2024/25 shoulder/winter over-fire was committed in the shared derivation scripts
(`scripts/derive_campd_outages.py` / `derive_campd_unit_outages.py`,
`high_load_mask`) but, until now, **only ERCOT's outage CSVs had been
regenerated on it.** Commit `b0c41cb`:

1. Made `high_load_mask` schema-robust. It hardcoded ERCOT's reconciled EIA-930
   columns (`Adjusted demand` / `Adjusted WND Gen` / `Adjusted SUN Gen`); every
   other BA `hourly.parquet` extract carries only the raw `Demand` / `NG: WND` /
   `NG: SUN` columns, so the mask **crashed on every non-ERCOT ISO**. It now
   falls back `Adjusted → raw`, so net load = demand − wind − solar resolves for
   all six BAs (no-op guard when demand is absent).
2. Fixed the facility-level out-path default (`inputs/raw-data/` → `RAW_DATA_DIR`
   = `data/raw/`, where the model reads and the unit-level script already wrote).
3. Regenerated, on the net-load filter:
   - `data/raw/campd-outages-PJM.csv` (facility-level — **PJM only**; no other
     non-ERCOT ISO has a facility-level file)
   - `data/raw/campd-unit-outages-{PJM,CAISO,NYISO,NEISO,MISO}.csv` (unit-level)

**Validated A/B (filter on vs off, current detector):** summer binding outages
preserved (PJM Jul −728 outage-hrs; MISO Jul 0%, Aug 1.6%); shoulder/winter
economic-idle mass cut (PJM Apr −68k / Oct −63k outage-hrs; MISO Apr 73%, Mar
69%, Nov 61%). Capacity-weighted outage GW-days drop **32–47%** vs the pre-fix
files (PJM −46%, MISO −47%, NYISO −32%, NEISO −34%, CAISO −37%).

**Why each keeper needs re-gating:** every ISO's current keeper was scored
against the **pre-fix (over-stated) outages**. Fewer outages ⇒ more available
coal/CC in the reserve/energy stack ⇒ **expect cooler shoulder/winter prices**.
This should *help* any ISO whose keeper ran hot in shoulder months (e.g. CAISO's
structural LMP overage) and must be re-confirmed not to *under*-fire the summer.

## Rules (non-negotiable, same as the ERCOT keeper)

- **No fitting to price residuals**; no pinning to actuals. The outage filter
  keys on **exogenous net load** (a backcast input), not the LMP — keep it that
  way.
- **Gate every re-solve vs actuals for ALL years the ISO can score, AND watch
  the tail** (don't collapse it or re-inflate an over-fire). Report mean,
  demand/load-weighted MAE, and hours>$200 (or the ISO's tail metric) per year,
  old-keeper vs new.
- **Re-solve byte-faithfully:** read the keeper bundle's `run_config.json` and
  reproduce its flags exactly — change *only* the outage input (which is picked
  up automatically from `data/raw/`, no flag change needed). Do not re-tune
  offers/curves in the same step; isolate the outage effect first.
- **Register on the dashboard** via the `calibration-report` skill, top-15
  retention per ISO (prune oldest only when >15). Update
  `docs/calibration-best-so-far*.md` only if the re-solve becomes the new keeper.
- Co-opt/commitment LPs are memory-heavy: **run years sequentially**, one solve
  at a time (a 2nd concurrent LP risks OOM at 4 cores / 16 GB).

---

## Per-ISO prompts (copy one into a fresh session)

> In every prompt below, **first confirm the ISO's current keeper** from
> `docs/calibration-best-so-far*.md` and the most recent non-PROBE entry in
> `frontend/data/backcast/registry/` — the bundle names here are current as of
> 2026-06-21 but the registry is the source of truth.

### PJM

```
Re-gate the PJM keeper on the net-load-filtered outages (branch
claude/ercot-scarcity-tuning-handoff-nl1y3m, commit b0c41cb). Read
docs/multi-iso/cross-iso-outage-regate-handoff-2026-06.md first.

PJM consumes BOTH regenerated files: data/raw/campd-outages-PJM.csv (facility)
and data/raw/campd-unit-outages-PJM.csv (unit) — capacity-weighted outage
GW-days fell ~46% vs pre-fix, concentrated in shoulder months (Apr/Oct), summer
preserved.

Current keeper: pjm-35 ("cc-steam"), bundle results/calibration/pjm_35
(confirm vs registry/best-so-far). Re-solve byte-faithfully from
results/calibration/pjm_35/run_config.json (driver scripts/run_calibration_full.py,
--iso PJM --year 2023 2024 2025), changing ONLY the outage input (auto picked up).
Gate the new solve vs actuals all 3 years AND the tail; compare old-keeper vs new
(mean, load-wtd MAE, hrs>$200). Note PJM's structural coal over-run is a separate
issue — don't chase it here. Register on the dashboard (calibration-report skill);
make it the keeper only if it gates clean. Push to a PJM feature branch.
```

### CAISO

```
Re-gate the CAISO keeper on the net-load-filtered outages (branch
claude/ercot-scarcity-tuning-handoff-nl1y3m, commit b0c41cb). Read
docs/multi-iso/cross-iso-outage-regate-handoff-2026-06.md first.

CAISO consumes data/raw/campd-unit-outages-CAISO.csv (unit-level only; no
facility-level CAISO file). Outage GW-days fell ~37% vs pre-fix. CAISO's keeper
runs structurally HOT (mean ~$54 vs actual ~$33) on a midday-import/solar-glut
gap — the cooler outages should narrow that, so confirm the direction and
magnitude.

Current keeper: caiso-13 ("voll-ccsteam"), bundle
results/calibration/caiso13_voll_ccsteam (confirm vs registry/best-so-far).
Re-solve byte-faithfully from results/calibration/caiso13_voll_ccsteam/run_config.json
(driver scripts/run_calibration_full.py, --iso CAISO, with --commitment
--priced-interchange --interchange-shaping-export-only --caiso-gas-floor-frac
etc. — take them from run_config.json), changing ONLY the outage input.
NOTE: there is no actual CAISO RTM LMP for 2023, so LMP gating is 2024/2025 only
(fuel-mix gating is all 3 years). Compare old vs new; register on the dashboard
(calibration-report skill). Push to a CAISO feature branch.
```

### NYISO

```
Re-gate the NYISO keeper on the net-load-filtered outages (branch
claude/ercot-scarcity-tuning-handoff-nl1y3m, commit b0c41cb). Read
docs/multi-iso/cross-iso-outage-regate-handoff-2026-06.md AND
docs/calibration-best-so-far-nyiso.md first.

NYISO consumes data/raw/campd-unit-outages-NYISO.csv (unit-level only). Outage
GW-days fell ~32% vs pre-fix.

Current keeper: confirm from docs/calibration-best-so-far-nyiso.md and the latest
non-PROBE registry entry (as of 2026-06-21 the newest NYISO runs are
nyiso-13-citygate-gas and nyiso-14-som-anchored-gas; pick whichever is the
accepted keeper). Re-solve byte-faithfully from that bundle's run_config.json
(driver scripts/run_calibration_full.py, --iso NYISO), changing ONLY the outage
input. NYISO YEAR COVERAGE IS LIMITED: 2023 scores; 2024 has historically been
data-blocked (unit-level CEMS / renewable-capacity gaps — verify current state);
2025 became available 2026-06-12. Gate every year you can, plus the tail. Compare
old vs new; register on the dashboard (calibration-report skill). Push to a NYISO
feature branch.
```

### NEISO

```
Re-gate the NEISO keeper on the net-load-filtered outages (branch
claude/ercot-scarcity-tuning-handoff-nl1y3m, commit b0c41cb). Read
docs/multi-iso/cross-iso-outage-regate-handoff-2026-06.md first.

NEISO consumes data/raw/campd-unit-outages-NEISO.csv (unit-level only). Outage
GW-days fell ~34% vs pre-fix.

Current keeper: neiso-22 ("ccsteam-keeper"), bundle
results/calibration/neiso_ccsteam_keeper_3yr (confirm vs registry/best-so-far).
Re-solve byte-faithfully from
results/calibration/neiso_ccsteam_keeper_3yr/run_config.json (driver
scripts/run_calibration_full.py, --iso NEISO --year 2023 2024 2025, with
--commitment --ct-deployment --gas-hub-basis-overlay etc. — take them from
run_config.json), changing ONLY the outage input. Mind the 2025 EIA-923
benchmark-incompleteness auto-scaling already in the keeper. Gate all 3 years +
tail; compare old vs new; register on the dashboard (calibration-report skill).
Push to a NEISO feature branch.
```

### MISO

```
MISO has NO calibration keeper yet (no benchmarked bundle as of 2026-06-21). The
net-load-filtered data/raw/campd-unit-outages-MISO.csv is regenerated and ready
(commit b0c41cb; outage GW-days fell ~47% vs the prior file, summer preserved),
so there is nothing to RE-gate — it will simply be the correct outage input
whenever a MISO baseline is first established.

If you are starting MISO calibration: read docs/multi-iso/00-iso-addition-protocol.md
and 05-backcast-playbook.md, then bring up a baseline with
scripts/run_calibration_full.py --iso MISO --year 2023 2024 2025, gate fuel mix
vs EIA-923 and net load/renewables vs EIA-930, and iterate per the playbook.
Otherwise no action is needed — the outage input is already in place.
```

---

## Notes / open per-ISO caveats

- **PJM** is the only non-ERCOT ISO with a *facility-level* `campd-outages-PJM.csv`
  in addition to the unit-level file; both were regenerated. The other four ISOs
  use unit-level outages only.
- **MISO** has no keeper — its regenerated CSV is forward-looking, not a re-gate.
- **NYISO** keeper named by an earlier handoff (`nyiso_smoke_2023`) is **not in
  `results/`**; use the live registry/best-so-far doc to identify the current
  keeper.
- Pre/post-fix capacity-weighted outage GW-days (unit-level), for reference:

  | ISO   | pre GW-days | post GW-days | cut |
  |-------|-------------|--------------|-----|
  | PJM   | 37,889      | 20,304       | 46% |
  | CAISO | 6,025       | 3,774        | 37% |
  | NYISO | 11,275      | 7,652        | 32% |
  | NEISO | 6,150       | 4,049        | 34% |
  | MISO  | 27,987      | 14,720       | 47% |
</content>
</invoke>
