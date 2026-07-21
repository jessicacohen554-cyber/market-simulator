# FF-3F — CES campaign infrastructure hardening (T1 scale, L-CES)

**Session:** FF-3F (Opus). **HEAD:** branch `claude/ces-campaign-infra-hardening-khyee5` off
`origin/main` `e2ada84`. **Companion to** `docs/handoffs/ff-3b-ces-poc-2026-07.md` (the FF-3B
POC that first proved the pipeline and found gap F-3) and
`docs/handoffs/ces-w3r-readiness-2026-07.md` (the W3-R NO-GO).

## Verdict: the CES campaign MACHINERY is hardened and re-proven at T1

Machinery/plumbing proof ONLY — **no premium-ladder conclusions are drawn**, and none can be:
the full 2026–2050 premium-ladder campaign stays deferred behind the forecast program's §2.1b
full-solve authorization gate (CLAUDE.md rules 1/6; plan §2.1b). This session builds and hardens
the campaign machinery at T1 scale (ERCOT 2026–2030, ≤5 solve-years/invocation) and confirms it
reproduces FF-3B's premium→surface signal. The forward capacity numbers below are **structural
smoke, not results** — the report itself stamps every table "deterministic scenario range — NOT a
probability band".

## What is now runnable (that wasn't)

### F-3 fixed — `scripts/generate_financial_reports.py` runs on a fresh checkout
FF-3B F-3: the script required `--eia860-path` / `--ownership-map` pointing at a hand-laid
`data/fleet/*.xlsx` + `data/ownership/*.parquet` layout a fresh clone does not have, so the
report's plant/company revenue-delta tables silently degraded to empty. FF-3F:

- Both inputs now resolve through the **on-disk path registry** by default (no flags needed):
  the EIA-860 fleet + ownership schedules come from the committed `data/raw/eia-860` partition
  (`config.paths.active_eia860_dir`, vintage `fleet.EIA860_OPERABLE_VINTAGE`). The parent-company
  map is built **in-process** from the committed EIA-860 ownership schedules
  (`ownership.load_eia860_ownership` → `build_parent_mapping`) — no pre-built parquet.
- Both resolvers are **fail-loud** (`_require_input`; rules 5/13): a missing input is refused with
  a named remedy, never silently skipped into a structurally-wrong report. No hardcoded path
  literals, no tuning (rule 5).
- Trivial no-solve test `tests/test_generate_financial_reports.py` (7 cases) proves the
  fresh-checkout resolution + fail-loud behaviour. **Validated end-to-end on the real T1 caches:**
  the report built the parent map from the registry (28,297 generators, 4,011 in EIA-860 Schedule
  4) with no flags, and wrote plant/company parquets for all five years per leg.

### Hardened premium-ladder harness — `scripts/run_ces_leg.py` (new)
The premium ladder is already a config LIST (`configs/ces_premium_matrix*.yaml`, `cases`-mode
`SweepDefinition`) expanded onto a base forecast config through `matrix.matrix_configs` — a
campaign is **data, not code**. FF-3B ran the whole ladder through one `market-sim matrix`
invocation (3 cases × 5 years = 15 solve-years in one process) and produced its per-leg
`full_horizon_summary.json` sidecars with a **throwaway driver**. FF-3F makes the per-leg path
first-class and §2.1b-clean:

- `run_ces_leg.py --case NAME` solves **exactly one** ladder leg per invocation, so a full campaign
  is N independent ≤5-solve-year invocations (the §2.1b window cap, enforced by the reused
  `run_full_horizon.assert_schedulable`; rule-12 years-sequential inside each leg). It reuses the
  instrumented solve engine `run_full_horizon.solve_and_summarize` (factored out this session), so
  each leg writes the SAME `full_horizon_summary.json` that `register_forecast_baseline.py` consumes
  (`--kind ces-poc`) — per-year wall/RSS, the honest I1–I14 invariant list, the headline trajectory,
  plus a CES-provenance block (case / premium / crediting / campaign).
- Legs solve into the DEFAULT `results/` cache (`redirect_cache=False`), so the report and the
  bundle assemble every leg by its `cache_key`.
- `run_ces_leg.py --assemble` builds the matrix bundle (`meta.json` + trajectory tables) from the
  solved legs with **NO solve** — reading each leg's **real** `cache_key` from its summary (the
  runner resolves the policy bundle + ISO overrides before hashing the config, so a naive
  `config.cache_key()` in a fresh process does **not** reproduce the solved key; the summary is the
  single source of truth). Cache-only: it never crosses the §2.1b window cap.
- Trivial no-solve tests `tests/test_run_ces_leg.py` (7 cases): ladder expansion, leg provenance,
  fail-loud case selection, real-key bundle assembly.

### `report_ces_campaign.py` — consumes the ladder + financial reports (no code change needed)
Ran end-to-end over the T1 bundle and emitted the full per-ISO CES table set — clean-share vs
premium, capacity/generation by fuel, curtailment, premium capture, captured price by tech, and
(with the F-3-fixed financial reports present) plant/company revenue deltas. No fail-loud plumbing
gap surfaced; the plant-financials schema (`plant_code/generator_id/zone/fuel_type/revenue/
generation_mwh/net_operating_income/attribute_revenue`, `parent_company/owned_revenue/
owned_attribute_revenue`) matches what the report reads end-to-end.

## What ran (T1)

| | |
|---|---|
| ISO / window | ERCOT 2026–2030 (5 solve-years — §2.1b cap; each leg its OWN invocation) |
| Ladder | BAU + CES-20 + CES-40, `clean_capture` (`configs/ces_premium_matrix_poc.yaml`) |
| Base config | `configs/scenarios/ercot_ces_poc_2026_2030.yaml` (HEAD defaults + `entry_screen_diagnostics`) |
| Cache keys | BAU `31675a6e21393f4d` / CES-20 `965f311ed9af6c99` / CES-40 `ad55835ead426c85` |
| Per-leg cost | ~11.0 min wall, ~3.6–3.8 GB peak RSS (matches FF-3B's ~11 min / 3.7–4.2 GB ledger) |
| Solved | 5/5 years each, no errors |
| Registered | `frontend/data/hindcast/ercot-2026-2030-ces-poc-{bau,ces20,ces40}.json` (`kind=ces-poc`) |

Every leg's invariants are honestly recorded in its sidecar (per FF-3B F-2, these are **structural
forecast physics, not CES-machinery bugs**): BAU FAIL `I3` / WARN `I12,I14`; CES-20 & CES-40 FAIL
`I3,I9,I12` / WARN `I14`. `I3`/`I12`/`I14` appear in BAU (no premium) — the known weak-entry /
legacy-retirement ERCOT trajectory (readiness NO-GO R1/R2). **`I9` appears only under the premium**
— a *positive* machinery signal: the resolver moves dispatch enough (more credited VRE/storage) to
trip the known penetration-scaling storage ε-degeneracy invariant.

## Premium → surface response reproduced at T1 (final cached year 2030)

The federal-CES resolver moves the **entire** reporting surface in the expected direction — the
§6 saturation/cannibalization story reproduced structurally, not asserted:

| Metric (2030) | BAU | CES-20 | CES-40 | reads as |
|---|---|---|---|---|
| clean_share | 0.413 | 0.494 | 0.506 | credited resources dispatch more |
| negative_price_hours (zone-avg) | 0 | 1045 | 1094 | premium deepens neg/zero-price epochs |
| avg_price ($/MWh) | 67.8 | 64.9 | 62.6 | price cannibalization |
| solar captured price ($/MWh) | 31.99 | 16.92 | 6.98 | solar self-cannibalization at depth |
| wind captured price ($/MWh) | 60.16 | 48.02 | 38.02 | " |
| solar capacity (GW) | 52 | 57 | 57 | premium pulls VRE entry |
| wind capacity (GW) | 47 | 57 | 59 | " |
| premium_capture_rate | 0.803 | 0.868 | 0.877 | delivered/potential; curtailment erodes ~12–20% |

**This matches FF-3B's expected signal.** FF-3B cited `clean_share 0.400 → 0.506` (BAU → CES-40) and
`solar captured-price $30 → $1.4`. FF-3F reproduces `clean_share 0.413 → 0.506` and the solar
captured-price collapse `$32.0 → $7.0` (a ~78% fall). The exact CES-40 solar floor differs from
FF-3B's ~$1.4 because HEAD's `ScenarioConfig` defaults advanced since FF-3B (the cache keys differ:
FF-3B BAU `9acbcee8…` vs FF-3F `31675a6e…`) — the **direction and near-collapse are the signal**,
and they hold. The clean-share, negative-price-hour, avg-price cannibalization, VRE-entry pull and
premium-capture channels all reproduce.

## What only the full 2026–2050 campaign can exercise (stays §2.1b-gated)

The machinery is proven; the following are **out of reach at T1 by construction** and remain
deferred behind the §2.1b per-ISO authorization gate (owner sign-off, plan §2.1b(d)) — do NOT
launch from the CES plan §8 W4:

- **The premium ladder as a conclusion.** No clean-share-vs-premium *curve*, revenue decomposition,
  or emissions-trajectory result may be drawn from a 5-year window (FF-3B item 2). The T1 legs
  register `kind="ces-poc"`, never campaign results.
- **Equilibrium capacity evolution.** The interesting CES capacity story (retirement acceleration,
  long-horizon VRE/storage entry saturation, CCS-retrofit economics, the ELCC-tilt toward
  long-duration storage) plays out over 2031–2050; the T1 window sees only the first entry waves,
  and those sit on the **known-weak ERCOT screens** the W3-R NO-GO (R1/R2) flags as unvalidated.
- **The first-campaign ladder + crediting variants.** The real campaign runs `{10, 20, 30}` (and the
  parked `cesa_ci` variant, `configs/ces_premium_matrix_ci.yaml`) over 2026–2050
  (`configs/ces_premium_matrix.yaml`) — each leg one owner-authorized 25-year invocation
  (`run_ces_leg.py --case … --full-solve-authorized`).
- **Company-level revenue attribution granularity.** The plant→parent rollup is coarse for the
  ERCOT merchant fleet (the report consumes the financial reports and emits the delta tables — the
  machinery works — but meaningful company deltas want the plant-code crosswalk W4-B tracks). A
  data-layout item, not a machinery gap.

## Reproduce

```
# G12 prerequisite (confirmed-retirements clean partition is gitignored):
PYTHONPATH=. python scripts/data/curate_confirmed_retirements.py

# one leg per invocation (rule 12 years-sequential; §2.1b ≤5-year cap):
for CASE in BAU CES-20 CES-40; do
  PYTHONPATH=. MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
    python scripts/run_ces_leg.py \
      --config configs/scenarios/ercot_ces_poc_2026_2030.yaml \
      --matrix configs/ces_premium_matrix_poc.yaml \
      --case "$CASE" --out-dir "results/ff-ces-t1/$CASE"
done

# assemble the bundle from the solved legs (cache-only, no solve):
PYTHONPATH=. python scripts/run_ces_leg.py \
  --config configs/scenarios/ercot_ces_poc_2026_2030.yaml \
  --matrix configs/ces_premium_matrix_poc.yaml \
  --assemble --out-dir results/ff-ces-t1/bundle --legs-dir results/ff-ces-t1

# per-leg financial reports (fresh-checkout runnable now — registry defaults):
for KEY in 31675a6e21393f4d 965f311ed9af6c99 ad55835ead426c85; do
  PYTHONPATH=. python scripts/generate_financial_reports.py \
    --results-dir "results/ERCOT/$KEY" --iso ERCOT \
    --output-dir results/ff-ces-t1/reports --years 2026-2030
done

# the CES campaign report set:
PYTHONPATH=. python scripts/report_ces_campaign.py \
  --matrix-dir results/ff-ces-t1/bundle \
  --financial-reports-root results/ff-ces-t1/reports --years 2026-2030

# register each leg on the forecast-validation namespace (kind=ces-poc):
PYTHONPATH=. python scripts/register_forecast_baseline.py \
  --summary results/ff-ces-t1/BAU/full_horizon_summary.json \
  --kind ces-poc --label ces-poc-bau --no-page \
  --extra-meta '{"case":"BAU","premium_usd_per_mwh":0.0,"campaign":"ff-ces-infra-t1","federal_ces_crediting":"clean_capture"}'
# … CES-20 (--label ces-poc-ces20), CES-40 (--label ces-poc-ces40) …
```
