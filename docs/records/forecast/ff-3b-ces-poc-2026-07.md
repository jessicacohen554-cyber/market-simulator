# FF-3B — T1-scale CES POC findings (ERCOT 2026-2030)

**Session:** FF-3B (Opus). **HEAD:** branch `claude/ces-w3r-readiness-poc-x4s903` on
`origin/main` `415df68`; POC solved on the session-start tree `57ed9fc` (the mid-session
capacity-cost/reserve intake does not touch the CES path — see the readiness doc). Companion
to `docs/handoffs/ces-w3r-readiness-2026-07.md` (the W3-R GO/NO-GO — **NO-GO**).

## Verdict: **CES campaign machinery is POC-proven** (configs + seams + reporting execute
## end-to-end); **3 findings surfaced**, all fixed-at-POC-scale or routed — exactly the class
## of defect the POC exists to catch before a 10-hour run does.

The whole W4 campaign pipeline ran bug-free at T1 cost:
`matrix_configs` → `run_scenario_iso` (per-leg, per-year cache) → **`market-sim matrix`
CLI** (bundle from cache) → **`report_ces_campaign.py`** (full CES table set) →
**`register_forecast_baseline.py --kind ces-poc`** (3 sidecars on the forecast-validation
namespace). Every leg solved 5/5 years; the federal-CES resolver demonstrably moves the
**entire** reporting surface (below). No premium-ladder conclusions are drawn from a 5-year
window (FF-3B item 2); the runs register as `kind="ces-poc"`, never campaign results.

## What ran

| | |
|---|---|
| ISO / window | ERCOT 2026-2030 (5 solve-years — §2.1b cap) |
| Ladder | BAU + CES-20 + CES-40, `clean_capture` (`configs/ces_premium_matrix_poc.yaml`) |
| Base config | `configs/scenarios/ercot_ces_poc_2026_2030.yaml` (HEAD defaults + `entry_screen_diagnostics`) |
| Posture | Forecast HEAD defaults: `datacenter_load_path=mid`, `correlated_forced_outage=True`, `entry_lookahead_reprice=True`, `retirement_rule=legacy`, `capacity_market_clearing=False` |
| Cache keys | BAU `9acbcee84538e384` / CES-20 `22de38d3c406571c` / CES-40 `b482f81b6d4dd7ee` |
| Registered | `frontend/data/hindcast/ercot-2026-2030-ces-poc-{bau,ces20,ces40}.json` (`kind=ces-poc`) |

## Machinery proof — the premium moves the full surface

Every credited-resource mechanism the campaign report exists to measure responds correctly
to the premium (final cached year 2030, deltas vs BAU):

| Metric (2030) | BAU | CES-20 | CES-40 | reads as |
|---|---|---|---|---|
| clean_share | 0.400 | 0.492 | 0.506 | credited resources dispatch more |
| negative_price_hours | 0 | 1017 | 1111 | premium deepens neg/zero-price epochs (§6-1) |
| avg_price ($/MWh) | 57.52 | 54.39 | 53.02 | price cannibalization (§6-3) |
| solar build (GW, ledger) | 9 | 19 | 20 | premium pulls VRE entry (§6-4) |
| wind build (GW, ledger) | 5 | 13 | 17 | " |
| solar captured price ($/MWh) | 30.02 | 11.89 | 1.36 | self-cannibalization at depth (§6-3) |
| wind captured price ($/MWh) | 50.43 | 40.74 | 30.36 | " |
| premium_capture_rate | 0.801 | 0.877 | 0.872 | delivered/potential; curtailment erodes ~13-20% (§6-2) |

This is the §6 saturation/cannibalization story reproduced structurally, not asserted: the
premium bids credited resources down (offer side), deepens negative-price hours, pulls entry,
and cannibalizes captured energy prices (solar's captured price collapses to ~$1/MWh at
CES-40 — its revenue is then almost entirely the $40 premium, exactly the CES dynamic). The
report also emits `capacity_by_fuel_deltas`, `curtailment_by_tech`, `evolution_deltas`,
`captured_price_by_tech`, `premium_capture`, and `clean_share_vs_premium` — all populated.

**These are NOT results.** The forward capacity numbers are unvalidated (see Finding F-2 and
the readiness NO-GO); the report itself stamps every table
"deterministic scenario range — NOT a probability band" and notes "treat capacity-evolution
deltas produced before [W3-R] GO as structural smoke, not results". The POC proves the
plumbing carries the signal; the readiness gate governs whether the signal is trustworthy.

## Findings

### F-1 — the documented W4 run command crashes on a fresh checkout (fixed-at-POC-scale: docs; coupling routed)

`market-sim matrix --config … --matrix …` as written in the CES plan §8 W4 command **fails
twice** on a fresh checkout, both times because the **W2-E/G12 fail-loud guards fire
correctly** (they refuse to silently degrade the confirmed-exit channel — rules 5/13):

1. **Missing clean partition.** `data/clean/confirmed-retirements` is derived + gitignored,
   so a fresh checkout has none → `load_confirmed_exits` raises. Fix: run
   `PYTHONPATH=. python scripts/data/curate_confirmed_retirements.py` first (documented
   prerequisite G12; this session ran it — ERCOT 2 live rows).
2. **`scripts.lib.clean_io` unimportable.** Even with the partition present, the
   **`market-sim` console entry point puts only the installed `market_sim` (src/) on
   `sys.path`**, but `src/market_sim/data/confirmed_retirements.py:145` does
   `from scripts.lib.clean_io import read_clean` — a **src→scripts import** that only
   resolves with the repo root on the path. So the console command needs a `PYTHONPATH=.`
   prefix. (`run_full_horizon.py` dodges this by adding `_ROOT` to `sys.path` itself; the
   console script does not.)

**Working command (verified — wrote a 3-case bundle):**
```
PYTHONPATH=. market-sim matrix --config configs/scenarios/<iso>_ces_base_2026_2050.yaml \
    --matrix configs/ces_premium_matrix.yaml --workers 1
# (after: PYTHONPATH=. python scripts/data/curate_confirmed_retirements.py)
```

- **Fixed at POC scale (docs):** the CES plan §8 W4-A/W4-B run command and the
  `configs/ces_premium_matrix.yaml` header are updated to prepend `PYTHONPATH=.` and cite the
  curation prerequisite — so the next W4 session does not lose the first minutes of a
  multi-hour run to a crash the POC already caught.
- **Routed (not fixed — beyond POC scope):** the underlying **`src → scripts.lib.clean_io`
  architectural coupling** (an installed package reaching into the repo's `scripts/` tree).
  The clean fix relocates `clean_io` into `src/market_sim/` and rewires every
  `scripts/…/curate_*` + data-intake caller — a data-contract refactor for the data-intake /
  architecture lane, not a POC-scale edit. Logged here as the real root of F-1.

### F-2 — the invariant FAILs are structural forecast physics, NOT CES machinery (finding, no fix)

The invariant gate ran on every leg (W4 requirement) and is honestly recorded in each
sidecar. It FAILs — and that is the readiness NO-GO surfacing in a forward run, not a POC
defect:

| Leg | FAIL | WARN | reads as |
|---|---|---|---|
| BAU | I3, I12 | I14 | ERCOT de-firm: unserved 0.03-0.05%, reserve margin 10.7-13.4% (< 13.8% floor), high LW price |
| CES-20 / CES-40 | I3, I9, I12 | I14 | same **+ I9** storage ε-degeneracy (premium raises storage throughput → trips the ε-tiebreak, frontier §1.2-8) |

- **I3/I12/I14** are the "de-firm to ~2035 / ERCOT chronic shortage" trajectory (frontier
  §1.2-4) driven by the same weak-entry/legacy-retirement screens behind the R1/R2 blockers.
  They appear in **BAU** (no premium), so they are not premium-induced.
- **I9 appears only under the premium** — which is itself a *positive* machinery signal: the
  resolver changes the dispatch enough (more credited storage/VRE) to trip the known
  penetration-scaling storage-degeneracy invariant (frontier §1.2-8, FF-3C's beat). Peak RSS
  rises with the premium too (3.69 → 4.24 GB) for the same reason.
- **Attribution:** the CES layer is orthogonal to these — it runs cleanly *on top of*
  known-weak ERCOT screens. No I-FAIL is a CES-machinery bug. (ERCOT does **not** show the
  A1/I4 multi-year leak the readiness doc routes for PJM; that stays a PJM/other-ISO item.)

### F-3 — `generate_financial_reports.py` is not runnable on a fresh checkout (finding, W4-B prerequisite)

`report_ces_campaign.py` ran fully and gracefully degraded the plant/company revenue-delta
tables to empty, noting the absence — because `generate_financial_reports.py` needs
`--eia860-path data/fleet/eia860_2024.xlsx` + `--ownership-map data/ownership/…parquet`,
neither of which is laid out on a fresh checkout (the EIA-860 parquets exist under
`data/raw/eia-860/` but not the expected `data/fleet/*.xlsx` path). The CES-specific tables
(clean-share, capacity, captured-price, curtailment, premium-capture) need none of this and
are complete. **Routed:** W4-B's revenue-decomposition step needs the financial-report input
layout resolved (data-intake) before it can emit plant/company deltas; not a POC blocker.

## Wall / RSS ledger (§2.4 — feeds FF-3E's full-horizon projection)

Measured per-year, ERCOT per-plant CAMPD bins, `--workers 1` (one solve at a time),
`MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1`:

| Leg | per-year wall (s) | leg total | avg s/yr | global peak RSS |
|---|---|---|---|---|
| BAU | 159/129/136/133/127 | 11.4 min | 137 | 3.69 GB |
| CES-20 | 148/128/127/128/129 | 11.0 min | 132 | 4.21 GB |
| CES-40 | 148/127/126/133/130 | 11.1 min | 133 | 4.24 GB |

- **~132-137 s/yr, 3.7-4.2 GB** for ERCOT CES at T1 (2026-2030). The first year carries
  ~20-30 s of fleet-load setup; steady-state is ~127-130 s/yr. The premium adds RSS
  (bigger LP: more VRE/storage) but not wall time.
- **CAUTION for FF-3E — this is NOT a linear 25-year basis.** 2026-2030 are the *cheap early
  years*; late-horizon LPs grow super-linearly with the accreting entry fleet (frontier
  §1.2-9: PJM 2045-2050 ≈ 30-40 min/yr). A naive 25 × 132 s ≈ 55 min would under-project a
  real 2026-2050 CES leg badly. FF-3E's projection must apply the late-year growth curve to
  this early-year anchor, not extrapolate it flat. The measured early-year ERCOT CES cost
  (~2.2 min/yr, ≤4.3 GB) is a firm *lower bound* and a good check on the front of the curve.

## Registration

3 sidecars on the forecast-validation namespace (`frontend/data/hindcast/`, **never** the
backcast registry — plan §2.3), `kind="ces-poc"`, each carrying `meta.per_year_perf`
(FF-3E's ledger source), the honest invariant list, `meta.premium_usd_per_mwh` / `case` /
`campaign="ff-3b-ces-poc"`. The forecast-validation page is rebuilt from sidecars by the
Pages deploy (`register_hindcast.py --page-only`) — the committed deliverable is the
sidecars, not the regenerated HTML (FF-0B T1-F convention).

## Correction back to the readiness doc

The GO/NO-GO doc's "Relationship to the POC" section predicted "ERCOT VRE entry is ~0 in
[the POC] too" (reasoning from `retirement_rule=legacy`). That is **wrong for forward mode**:
the forward POC builds **9 GW BAU solar** (→ 19-20 GW under the premium). The correction
*strengthens* R1: forward ERCOT entry builds solar, but the R1 hindcast — the *validation*
instrument — shows the same entry mechanism yields **0** against realized 2021-2025 prices.
The forward solar is therefore exactly the **unvalidated forward entry** R1 flags (it clears
only because forward DC-load/demand-growth/fuel inflate the price signal, not because the
mechanism reproduces reality). The readiness doc is corrected to say so.

## Reproduce

```
PYTHONPATH=. python scripts/data/curate_confirmed_retirements.py        # G12 prerequisite
# solve (per-leg per-year wall/RSS + invariants) — throwaway driver, or just the CLI below:
PYTHONPATH=. MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  market-sim matrix --config configs/scenarios/ercot_ces_poc_2026_2030.yaml \
  --matrix configs/ces_premium_matrix_poc.yaml --workers 1 --out-dir results/ces-poc/bundle
PYTHONPATH=. python scripts/report_ces_campaign.py --matrix-dir results/ces-poc/bundle \
  --output-dir results/ces-poc/bundle/ces_report --years 2026-2030
```
