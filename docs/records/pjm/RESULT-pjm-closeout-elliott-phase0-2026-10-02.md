# RESULT — PJM close-out Elliott phase 0 (E0a–E0e): the PRECOMMIT does not clear phase 0

Lane `closeout-PJM` (branch `claude/closeout-pjm-elliott`), 2026-10-02. **Zero LP.** Executes `PRECOMMIT-pjm-closeout-elliott-cold-outage-2026-10-02.md` §3 against its pre-fixed readings. Probe `scripts/probes/_pjmco_e0_elliott_phase0.py` → `results/phase0/pjm/_pjmco_e0_elliott_phase0.json`, `_pjmco_e0_footprint.csv`, `_pjmco_e0_headroom_hourly.csv`. The ERCOT derive method (`scripts/data/derive_correlated_outage_curve.py`) is reproduced for PJM inside the probe; the derive script itself is untouched.

## Verdict

| step | reading | result | verdict |
|---|---|---|---|
| E0a | ≥ 2 certified windows other than Dec 2022 | 2 (2019-01-25..02-02, 2025-01-19..25) of 37 cold windows | PASS, but hollow: Elliott itself is **not** certified (peak net load 0.985 × the 2022 p99) |
| E0b | leave-one-out moves 24–25 Dec ≤ 30 % | 0.0 % | PASS by construction (Dec 2022 was never in the fit) |
| E0c | no nonzero-residual day outside Dec–Feb | 6 days outside (2019-03-04..07, 2019-11-13, 2022-03-13) of 97 | **FAIL** (construction defect: the curve has no season gate) |
| E0d | model rise 24/25 Dec within [0.7, 1.3] × published rise | 0.64 / 0.35 | **FAIL** |
| E0e | hours below `pjm_primary` requirement, 23–26 Dec (reported) | 0 of 96; min headroom 10.6 GW (23 Dec HE19) | — (no shortfall formed) |

**Kill rule applies: no build, no solve.** Readings are not re-read.

## Curve (2 certified points per class, one era)

| class | slope /°C | cap | 2019 excess | 2025 excess |
|---|---|---|---|---|
| COAL (pooled) | 0 | 0 | 0 | 0 |
| CC_REGULAR | 0.0177 | 0.260 | 0.260 | 0.088 |
| CT_PEAKER | 0.0338 | 0.490 | 0.490 | 0.175 |
| ST_GAS | 0.0345 | 0.469 | 0.469 | 0.214 |

Elliott by day (curve / overlay already captured / residual, MW): 23 Dec 15,642 / 3,589 / 12,052; 24 Dec 14,670 / 7,548 / 8,199; 25 Dec 7,711 / 8,296 / 4,479; 26 Dec 6,262 / 9,138 / 3,540. With the residual the 24 Dec model rise is 12,972 MW vs the published 20,273 MW.

## What it teaches (for the re-charter, owner/desk call)

1. **The certificate is the wrong gate for a December event.** The in-merit certificate (net load ≥ the year's p99) was written for ERCOT summer-peaking years; PJM's annual p99 is a summer peak, so a winter emergency at 98.5 % of it fails while the 2019 and 2025 polar-vortex days pass. A winter-season p99 (or PJM's own emergency-procedure postings as the certificate) would admit Elliott — but then E0b's leave-one-out becomes a real test.
2. **The instrument is biased high.** On warm certified days the best-mustered fraction already sits 0.06–0.37 below 1 − EFORd (CT 0.63–0.81, ST 0.56–0.77, CC 0.80–0.88), so part of the "cold excess" exists with no cold; netting it out leaves the 2025 excess ≈ 0.01–0.05. The ERCOT curve carries the same bias; the PJM lane only measured it.
3. **Even generously, the curve under-recovers Elliott** (0.64 / 0.35) and forms no reserve shortfall (min headroom 10.6 GW). A TMIN hinge does not capture the 25 Dec peak, when PJM's forced outage was highest while the temperature had begun to recover — the event's gas-supply leg lags the cold.
4. **Coal shows no cold excess** in the instrument, consistent with PJM's report that ~70 % of December forced outages were gas units.

A re-charter needs, before any build: a season gate (Dec–Feb) and a winter certificate written ex ante; a de-biased instrument (excess over the same class's warm-certified-day muster, not over 1 − EFORd); and a gas-supply term keyed to a measured gas-system driver (pipeline OFOs / critical-day notices or daily delivered gas), since temperature alone lags the event. Each is a new ex-ante PRECOMMIT; none is attempted here.

## Status

Cell `correlated_forced_outage` PJM stays `.` / fc `I` (nothing built or solved; rule 28 records a test only when a mechanism is tested — this is a pre-build phase-0 refusal, recorded here). Solves remain held for the post-W0 PJM keeper.
