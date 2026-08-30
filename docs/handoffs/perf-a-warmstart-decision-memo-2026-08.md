# PERF-A owner decision memo — `forecast_xyear_warmstart` default (plan §6 decision 1)

**STATUS: CLOSED — OVERTAKEN BY EVENTS, ACKNOWLEDGED BY THE OWNER 2026-08-26**
(program-director sitting, card 10). The owner acknowledged decision-1 as
CLOSED-OVERTAKEN per §3 option (A) — the decision was made at K.3 (D-9 flipped
the default, D-10 disarmed the forecast lane; no flip ships) — and dropped it
from the owner decision queue after twenty-one director cycles. A records
acknowledgement only: no code, no config, no determination changed. Queue
removals: plan §6 item 1 + §8 ledger, director-board item 6. Record:
`docs/FINDING-holdout-governance-2026-08-26.md`.

*Original header:* **STATUS: DECISION INPUT — for the owner at gate G1.**
Written 2026-08-15 by PERF-A (`claude/ci-infrastructure-blocker-bp3zv3`), chartered by
`docs/model-audit-release-plan-2026-08.md` §3/WS3 item 4: *"Write the owner decision memo
for flipping `forecast_xyear_warmstart` default ON … the owner declined pre-authorization
(2026-08-13, plan §6 decision 1); your memo's bundle-diff evidence IS the decision basis
at G1, so make the A/B concrete."*

## 1. The decision the plan holds open was already adjudicated — the other way

The audit plan's §1 survey (2026-08-13) carried this item as an open wallclock lever. The
artifact record says otherwise, in two layers:

1. **D-9 (2026-07-26): the default WAS flipped ON**, on exactly the bundle-diff evidence
   the plan asks this memo to produce. `ScenarioConfig.forecast_xyear_warmstart = True`
   at HEAD (`src/market_sim/config/scenarios.py:11646`), registered in
   `_CACHE_KEY_OPTIONAL_FIELDS` with declared default `"True"` (`scenarios.py:648,1152`).
   Evidence on record (`docs/handoffs/wallclock-baseline-2026-07.md` §H3/§H3b):
   - ERCOT 2026–2050 full horizon, cold vs warm arms: **capacity trajectory bit-identical
     in all 25 years** (`total_cap_mw`, per-fuel capacity, builds, retirements, peak,
     reserve margin, `max_hourly_price` all 0.000e+00); largest non-capacity residual
     `lw_price` 2.5e-05 — three orders of magnitude inside the golden bands. Wall 51.1
     min → 25.1 min (**2.04×**, conservative under the contention caveat).
   - NEISO and NYISO full horizon: same guardrail, **identical trajectories**, 1.83× and
     1.88×; all six ISOs green at the 168 h pre-screen. (CAISO cold arm stopped 22/25 by
     owner call — "3 ISOs is enough"; PJM/MISO never launched; recorded so it is not
     re-run.)
2. **D-10 (2026-08-04, sitting Addendum K.3): DISARMED on the forecast lane.** Every
   shipped forecast runner passes `False` explicitly through the ONE reader
   `scripts/lib/forecast_posture.shipped_forecast_xyear_warmstart()` — verified at HEAD:
   `run_full_horizon.reference_config`, `run_capacity_hindcast.build_config`,
   `ff_readiness_battery.golden_posture_config` all wire through it. The field default
   stays `True` deliberately (a default flip would have collided every forecast cache key
   with its warm predecessor and moved all six backcast keeper keys — measured both ways
   in `docs/handoffs/ffr-3t-warmstart-off-2026-08-04.md`; cache epoch 2026-08-04).

**Why D-10 overrode D-9.** FFR-3M (`ffr-3m-kill-resume-verdict-2026-08-04.md`) measured
a defect D-9's guardrail could not see, because D-9 compared two *uninterrupted* runs: a
**killed-and-resumed** forecast loads its earlier years from cache, a cache-loaded year
exports no basis, so the first freshly-solved year after a resume runs cold while the
same year in an uninterrupted run runs warm — two different vertices of a degenerate
optimal face. **A resumed forecast was not reproducible from its own cache.** The drill
was causal: FAIL at the default; two independent no-kill controls byte-identical (ruling
out run-to-run nondeterminism); GREEN with the flag off. The cold answer was adjudicated
canonical. Pinning a basis to make warm and cold agree was put to the owner and
**refused** (a pinned vertex would let a solver setting select which marginal units
retire). The K.3 record states the ~2.3× P0 speedup is an **accepted cost** and "is not
to be recovered by re-arming, tie-breaking or ordering freezes."

## 2. Why PERF-A did not run a new A/B

The concrete A/B the plan asks for **exists and is cited above** (H3/H3b: full-horizon
bundle diffs; FFR-3M: the kill-resume drill). Running a fresh uninterrupted-bundle A/B
would reproduce H3's clean result — identical trajectory, ~2× wall — and would be
**misleading as decision evidence**, because the case that decided D-10 is the resume
drill, which an uninterrupted A/B is structurally blind to. Re-running recorded
experiments is also barred by this lane's own charter ("context you must not re-derive")
and by the wallclock baseline's do-not-re-run discipline.

## 3. Options for the owner at G1

- **(A) RECOMMENDED — Close plan §6 decision 1 as overtaken by events.** The decision
  was made at K.3 with solve-measured evidence; nothing has changed since. The forecast
  lane stays cold-only; the backcast lane keeps its own warm-start (default ON in the
  calibration CLIs, `--no-xyear-warmstart` opt-out — untouched by D-10). PERF-B strikes
  the "~2.3× on warm P0 years" line from its expected-wins list.
- **(B) Re-open K.3.** Only coherent if the resume-reproducibility defect is solved
  first. The two known routes were both considered and refused in the K.3 record:
  persisting/pinning bases so a resumed run reproduces the warm trajectory (refused —
  solver setting selects retirements), or accepting non-reproducible resumes (refused —
  FFR-3M's premise). A third route — invalidating the whole cache chain on any resume so
  every run is uninterrupted-or-restarted — trades the speedup for full re-solves on
  every kill, i.e. it spends the win it recovers. PERF-A found no new fact that
  weakens the K.3 reasoning.

## 4. Verified-at-HEAD checklist (2026-08-15, main @ c447199)

| Claim | Where verified |
|---|---|
| Field default `True` | `src/market_sim/config/scenarios.py:11646` |
| Registered + declared default `"True"` | `scenarios.py:648` / `:1152` |
| One-reader disarm exists, documented D-10 | `scripts/lib/forecast_posture.py:103` |
| All three shipped forecast runners wire through it | grep: `run_full_horizon.py`, `run_capacity_hindcast.py`, `ff_readiness_battery.py` |
| Backcast CLIs keep xyear warm-start ON (opt-out flag) | `scripts/run_calibration_full.py:7928` |
| Pinning tests hold both layers | `tests/unit/pipeline/test_forecast_bundle_xyear_warmstart.py` (lane OFF); `scenarios.py:11644` comment (default flip guard) |
| Doc of record agrees | `docs/cross-year-warmstart.md` header + "Status update (D-10)" |
