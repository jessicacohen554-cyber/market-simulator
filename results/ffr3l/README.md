# FFR-3L — ERCOT T1-X price-2025 regression, paired control

Out-dir root for this lane's paired T1-X crossover arms. **The bundles under
here are gitignored** (`/results/ffr3l/` in `.gitignore`) — they are transient
LP caches of the same class as `/results/ffr3a2/` and `/results/ffr3a3/`, and
the legs are registered to `frontend/data/hindcast/` via
`scripts/register_forecast_run.py --bundle`, never tracked as bundles here
(CLAUDE.md rule 15). This README is the lane's record, not solver output, so it
stays tracked.

## What this lane measures

FFR-3A-2 blocker 7 / §4.2: on the re-measured T1-X crossover, ERCOT price 2025
regressed **8.6 % PASS → 22.5 % FAIL**, and ERCOT is the **sole regressor**
among the three legs (ercot / pjm / miso). FFR-3A-2 recorded it as an open
regression, not a claim, because **no T1-X control arm was run**.

This lane runs that control.

## The arms

Both: `--iso ERCOT --crossover --vintage 2023 --start-year 2023 --end-year 2027`
(5 solve-years; 2023–2025 realized inputs, 2026–2027 pure forward drivers,
solved but never scored — rule 22).

| arm | out-dir | flags off the shipped default | resolved cache key |
|---|---|---|---|
| **A — shipped (treatment)** | `t1x/ercot-2023-2027-crossover-ffr3l-shipped` | none (all omitted ⇒ inherit shipped) | `d0d1e9713593b6a9` |
| **B — pre-decision control** | `t1x/ercot-2023-2027-crossover-ffr3l-control` | `--retirement-rule legacy --no-entry-rate-limits --no-entry-commissioning-lag` | `298cb8e2aa559c70` |

**Pairing checks, run BEFORE either arm was read** (the FFR-3F §5 protocol):

* The two configs differ in **exactly three fields** — `retirement_rule`
  (pipeline → legacy, owner decision D-1), `entry_rate_limits` and
  `entry_commissioning_lag` (True → False, owner decision D-2).
* The resolved on-disk cache keys are **distinct**. Read from the runner's own
  `run_scenario_iso start:` line, not from a request-side `cache_key()` — those
  are different objects (FFR-3A-2 §1.2, which retracted its own finding for
  exactly this).
* `MARKET_SIM_DATA_ROOT` is unset in both arms, so neither key is shifted by the
  data-root seam (the FFR-3F §5 hazard).
* Arm A's resolved key `d0d1e9713593b6a9` is **identical** to the committed
  FFR-3A-2 T1-X sidecar's key (`frontend/data/hindcast/ercot-2023-2027-crossover-ffr3a2.json`),
  so the treatment reproduces that leg rather than approximating it.

## What the pair does NOT separate

`correlated_forced_outage` and `entry_lookahead_reprice` resolve **True in both
arms** — the control does not revert the C.4(c) un-pin. This pair separates
{D-1, D-2} from everything else; it does not separate everything-else into
parts. Full accounting in the deliverable.

## Deliverable

`docs/handoffs/ffr-3l-ercot-t1x-attribution-2026-08-04.md`.
