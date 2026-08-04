# FFR-3A-3 — post-FFR-3F re-measurement of the T1-H / T1-X halves (lane record)

This directory is the `--out-dir` root for the FFR-3A-3 re-measurement.

**Why it exists.** FFR-3A-2 measured the full 14-leg T1 battery, then recorded a
**provenance ceiling** on its own results: the rebase brought in FFR-3F's G3
cap-grain fix (`2adfb49`), which is **unconditional** and changes the admitted
exit set — the same economic-retirement screen every T1-H finding rests on. Its
banner names §3.7 (NYISO), §3.8 (PJM) and §3.9 (MISO) as the findings most
exposed and says they *"should be re-measured at the post-FFR-3F HEAD before
being relied on."* This lane does that.

**Scope, and what it deliberately excludes.** The four T1-H curve legs and the
three T1-X crossover legs are re-solved at the post-FFR-3F HEAD, all six
solve-affecting flags **omitted** so each inherits the shipped default
(`retirement_rule=pipeline`, D-1/D-2 armed, the C.4(c) un-pin on,
`exit_rate_limits` **off** per Addendum G.1). **T1-F is NOT re-run** — it does
not turn on the exit screen's grain — so the §2.1b scorecard is deliberately
**mixed-provenance** and says so: see `scripts/build_ffr3a3_scorecard.py`, whose
carried-forward values each keep the sha their own artifact recorded and render
with a `^`.

**Nothing is promoted and nothing is tuned.** No `ScenarioConfig` default moved,
no band widened, no damper unarmed. Addendum D.1 — *HOLD PROMOTION, FIND ROOT
CAUSE* — is honoured; criterion (d) stays the owner's.

**Everything under here except this README and `scorecard/` is gitignored**
(`.gitignore`, the `/results/ffr3a3/` rule) — same class as `results/ffr3a2/`.
Forecast-family legs are registered to `frontend/data/forecast/` via
`scripts/register_forecast_run.py`, never as tracked bundles here (CLAUDE.md
rule 15). The committed record is that registration plus the readout in
`docs/handoffs/ffr-3a3-battery-close-2026-08-04.md`.

Layout (FFR-3C blocker 10 — read this before looking for a ledger):

    results/ffr3a3/<tier>/<leg>/<ISO>/<cache_key>/evolution_<year>.json

The evolution ledgers live under `<out-dir>/<ISO>/<cache_key>/`, **not** the
out-dir root, and `load_ledgers_for_run` returns `{}` rather than raising, so a
wrong path reads as "no evolution happened" instead of failing loudly.
