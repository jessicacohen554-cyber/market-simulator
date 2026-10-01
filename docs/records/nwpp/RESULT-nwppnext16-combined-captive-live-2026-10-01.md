# RESULT — NWPP-NEXT-16: arms C / D / E, 2019–2025 (C promoted to keeper #20)

PRECOMMIT: `PRECOMMIT-nwppnext16-combined-captive-live-2019-2025-2026-10-01.md`. Pin `33014efc`, 21 year-isolated shards
(rule 36), every leg on the `requirements.txt` libraries (highspy 1.14.0 / pandas 3.0.3 / pyarrow 24.0.0 / pydantic 2.13.4).
Scorer: rubric v3.13. Owner card 2026-10-01: **"Promote C, prune #19"**; NEXT-17 lever **"Bridger seasonal offer"**.

## Outcome

| arm | keys vs #19 | determination | status changes | C4 coal 2023 r / NRMSE | C1 closer / farther |
|---|---|---|---:|---|---|
| #19 (control, committed bundle) | — | NOT-YET {dispatch_corr} | — | 0.670 / 0.317 | — |
| **C → keeper #20** | fuel split → vintage denominator | NOT-YET {dispatch_corr} | **0** vs #19 | 0.669 / 0.313 | 22 / 13 vs #19 |
| D | C + captive-mine price | NOT-YET {dispatch_corr} | 0 vs C | **0.650 / 0.346** | 14 / 23 vs C |
| E | C + live-capacity coal WEFOR | NOT-YET {dispatch_corr} | **4 new FAILs** vs C | 0.672 / 0.334 | 12 / 37 vs C |

- **C** is promoted on structure (rules 14 / 19), not on the residual. It ties #19: every C4 record moves by ≤0.008. It is one
  repair where #19 had a special case, and it also fixes North Valmy 8224's must-run (212.45 → 127.89 MW). The per-unit
  fuel-split composition is **deleted** (rule 26).
- **D regresses the failing record.** Bridger's 2023 coal rises 8.52 → 9.73 TWh, but mostly in Nov–Dec (C: 0.80 / 0.78 →
  D: 1.36 / 1.37 TWh), not in the Jun–Oct window where CEMS shows Bridger running. A cheaper econ tranche does not undo the
  LP spending the take floor in dear-gas Q1. C1 COAL_PRB error +1.6 TWh (2021), +1.1 TWh (2023).
- **E adds four C4 FAILs**: coal 2019 0.720 → 0.679, coal 2022 0.712 → 0.668, coal 2025 0.712 → 0.674, gas 2019 0.731 →
  0.688. Zeroing statistical WEFOR on screened coal makes coal flatter (more baseload) than CEMS. C1 COAL_PRB 2020 error
  +2.2 TWh.

## Regressions of C vs #19, at full magnitude

- C4 (all PASS except coal 2023): coal 2019 0.728 → 0.720; coal 2022 0.719 → 0.712; gas 2022 0.871 → 0.864; coal 2024
  0.745 → 0.741; gas 2024 0.896 → 0.894; NRMSE moves ≤ +0.004.
- C1 (all PASS): COAL_BIT 2024 error 0.82 → 1.30 TWh; CC_REGULAR 2024 6.27 → 6.60; CC_REGULAR 2020 1.50 → 1.67;
  COAL_BIT 2019 0.58 → 0.69.

## Corrections to the handoff

- **Keeper #19 was NOT off-pin.** Its `run_config_<Y>.json` record highspy 1.14.0 / pandas 3.0.3 / pyarrow 24.0.0 /
  pydantic 2.13.4, written from `importlib.metadata` at solve time. The off-pin solve was NEXT-15's unmerged run. So
  C vs #19 is a clean A/B. The PRECOMMIT §3 "Libraries: LIVE" line was wrong, and the owner's "No control" choice cost nothing.
- **Shard prompts need `pip install --ignore-installed pyyaml==6.0.3` first.** Without it `pip install -r
  requirements.txt` fails on the Debian PyYAML in the container.
- **D 2021 shard** ran `legitimacy_diagnostics.py` itself, saw exit 1, and stopped to ask. It had already pushed its bundle;
  a relaunch was archived before it solved. Future shard prompts should say legitimacy is the parent's job.

## Bytes and provenance (rules 33 d / 34 e)

- **On `main`:** keeper #20's bundle `results/calibration/nwppnext16c_span` (slim set: hourly sidecars, run configs,
  attestation, legitimacy, metrics), its sidecar and run payload. Its `dispatch/` is gitignored repo-wide. #19, D and E are
  pruned (rule 35); every number cited for them is in this doc.
- Leg provenance (not a recovery route; any leg not on `main` is a re-solve, ~40–150 min per year):
  - C: 2019 `1e4bd215` · 2020 `aa60aa43` · 2021 `3b38fefe` · 2022 `11bb59fb` · 2023 `a54c7b97` · 2024 `91f0bc29` · 2025 `1a41ba51`
  - D: 2019 `6f3b6b8f` · 2020 `951f60c9` · 2021 `6ced8fde` · 2022 `9367b3d0` · 2023 `875d999c` · 2024 `702b3765` · 2025 `842e9593`
  - E: 2019 `c0c987ee` · 2020 `26cdd6f7` · 2021 `28559348` · 2022 `0aae94d9` · 2023 `9ea57032` · 2024 `b96580f0` · 2025 `19ae5f8d`

## Bridger 2023, keeper #20 (TWh by month)

| Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.37 | 1.32 | 0.94 | 0.61 | 0.19 | 0.25 | 0.36 | 1.37 | 0.31 | 0.21 | 0.80 | 0.78 |

This is NEXT-17's object: the Jun–Oct trough (FINDING-nwppnext14 §1).
