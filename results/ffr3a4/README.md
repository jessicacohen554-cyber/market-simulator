# results/ffr3a4/ — FFR-3A-4 lane record

Fourth and closing pass at FFR-3A. Two jobs, neither of them tuning:

1. **Measure the one leg the battery never got** — MISO T1-X (2023–2027
   crossover, vintage 2023), which FFR-3A-3 launched twice and lost twice to
   OOM and correctly left as a null board cell rather than a stale value
   (`docs/handoffs/ffr-3a3-battery-close-2026-08-04.md` §6.1).
2. **Close the instrument debt** FFR-3A-3 left: the strict
   `ScenarioConfig.from_yaml` that strands every bundle older than a rule-26
   field deletion, the unguarded run-id collision in the hindcast registration
   path, and the rule-28(b) mechanism-matrix citations for the D-1/D-2 cells
   FFR-3A-3 re-measured.

**Nothing is promoted and nothing is tuned.** Owner Addendum D.1 (*HOLD
PROMOTION, FIND ROOT CAUSE*; D-1 and D-2 stay armed) and Addendum G.1 (D-8
`exit_rate_limits` ships default-OFF) are honoured throughout.

## What is tracked here

The solver output under this directory is **gitignored** (`/results/ffr3a4/`,
same class as `/results/ffr3a3/`): forecast legs are registered to
`frontend/data/hindcast/` via `scripts/register_forecast_run.py`, never as
tracked bundles (CLAUDE.md rule 15). These files are the lane's *record* rather
than solver output and are tracked with `git add -f`:

| file | what it is |
|---|---|
| `README.md` | this file |
| `PREREG-miso-t1x-2026-08-04.md` | the MISO T1-X prediction, committed **before** the bundle existed |
| `RESULT-miso-t1x-2026-08-04.md` | the measured outcome, scored against that PREREG |

## Predecessors

* `docs/handoffs/ffr-3a2-battery-close-2026-08-03.md` — the 14-leg battery and
  its provenance ceiling.
* `docs/handoffs/ffr-3a3-battery-close-2026-08-04.md` — the six-leg post-fix
  re-measurement that corrects it.
* `docs/handoffs/ffr-3a4-miso-t1x-instrument-debt-2026-08-04.md` — this lane.
