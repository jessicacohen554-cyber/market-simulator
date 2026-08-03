# FFR-3C lane record — run outputs here are **gitignored and unregistered**

This directory is the `--out-dir` root for the FFR-3C collapse-attribution lane
(2026-08-03, owner blocker 0 from FFR-3A; sitting Addendum D.1/D.2 — *"HOLD PROMOTION,
FIND ROOT CAUSE"*). Everything under it except this file is **gitignored**, matching
`/results/ffr3a/`, `/results/ffr1a/`, `/results/full-horizon/` and every other forecast
lane: forecast legs are registered to `frontend/data/forecast/` via
`scripts/register_forecast_run.py`, **never** as tracked bundles here (CLAUDE.md rule 15).

**Nothing in this directory is a registered result, and nothing here is promotable.** Every
leg is HOLD, by the owner's standing instruction — this lane was commissioned to produce
*attribution*, not a promotion candidate. The findings live in
`docs/handoffs/ffr-3c-collapse-attribution-2026-08-03.md`.

## The two arms

Paired MISO T1-F legs over 2026–2030 (5 solve-years, the FFR-3A window), `--golden-posture`
so MISO resolves **curve-ON** = its shipped arm (FFR-3A §4.3):

| arm | flags | cache key |
|---|---|---|
| `miso-treatment` | shipped post-decision defaults (`retirement_rule=pipeline`, both entry dampers armed) | `b3d33a1955c7854d` |
| `miso-control` | `--retirement-rule legacy --no-entry-rate-limits --no-entry-commissioning-lag` | `3a0061377cba3d34` |

The keys were verified **distinct before either arm was solved** (FFR-3A §3.1 separability —
explicit-`legacy` control arms hash distinctly even though a *default* flip does not move the
key). A delta between arms is therefore a real scenario difference, not cache reuse.

## Rule 12 posture

MISO is a solo ISO: peak RSS measured **9.31 GB** on the treatment arm (FC-8 CAVEAT, ≥ 8.6 GB
no-co-run threshold). The two arms were run **sequentially**, never concurrently, and years
run sequentially within each invocation.

## Reading a leg's output without being misled

Key on `n_solved_years` in `full_horizon_summary.json`, **never** the console
`invariants: N FAIL, N WARN` line — invariant scoring over a zero-year run passes trivially,
so a hard failure reads as a clean gate at a glance (FFR-3A §6.1, blocker 5, still open).

The per-year evolution ledgers are **not** in this directory's root: `run_full_horizon`
rebases the cache root under `--out-dir`, so they live at
`<out-dir>/MISO/<cache_key>/evolution_<year>.json`.
