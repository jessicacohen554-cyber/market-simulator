# CAISO-99 handoff — storage charter EXECUTED; keeper = caiso-99 storage shape

**Session 2026-07-19 (CAISO-99) outcome:** Mechanism A closed as ALREADY-LIVE
(the caiso-98 dead-flag root cause falsified — no runner.py wiring made);
Mechanism B (measured NG:OTH p95 dispatch-shape envelope) built, solved, and
**PROMOTED**: CAISO keeper = `2026-07-19-caiso-99-storage-shape` (NOT-YET,
fail {C3a-2025 +10.8%, C3c, C4, C5a w/ 2024 CAVEAT}; C1 12/12, C2/C3b/C6/C7/C8
PASS). Belly λ resid +10.9/+9.0/+8.4 → +7.7/+7.6/+6.3, no overshoot; C5a
improves all years. Full record: FINDING-caiso99-storage-shape-2026-07-18.md
(§1 the falsification trace, §6 the A/B), the 2026-07-19 calibration-log
entry, and the CORRECTION block in FINDING-caiso98 §11.

## What CAISO-99 established (do not re-derive)

- **The backcast storage fleet was NEVER flat.** `solve_and_persist` →
  `run_calibration.run_year:3297` → `load_eia860_storage(iso, year, config)`;
  `backcast_config.py:1350` arms `storage_vintage_ramp=True` for
  CAISO/ERCOT/NEISO. The keeper dispatches the measured COD-ramped EIA-860
  fleet (8.1/11.7/15.4 GW year-end). `runner.py:587`/`build_default_storage`
  is the FORECAST orchestrator only. Keeper meta's `storage_vintage_ramp:
  False` is the kwarg echo, not the solve config (recorder defect, ercot-65
  pattern reversed — open cosmetic fix).
- **The belly/evening storage masses are dispatch-INTENSITY/SHAPE, not fleet
  size** — and the measured envelope closes the SHAPE part: battery Chg/Dis
  now capped at env_p95[year,hod] × power_cap (EIA-930 NG:OTH ÷ EIA-860
  monthly fleet; `caiso_storage_shape_anchor`, rule-19-exclusive with the
  probe-inert caiso-74 AS reservation, rule-23 derivation
  `data/raw/reference/caiso-storage-shape-envelope.csv`).
- **The residual belly (+7.7/+7.6/+6.3) is charge-side ECONOMICS inside the
  envelope:** the LP charges AT the p95 cap in ~every economic hour, while the
  measured fleet's MEAN belly rate is ~half its own p95 (day-to-day
  selectivity: DA-spread bidding thresholds, cited cycling/degradation cost —
  the caiso-74 disposition's queued lead). A sub-p95 cap would be
  residual-fitting (rule 25) — the next mechanism must price WHY reality skips
  marginal-spread days, not shrink the envelope.

## Paste-ready next-session prompt

```
<<<CAISO-100 — BELLY CHARGE-ECONOMICS CHARTER (derive-first, owner-gated) + WP-3>>>
MODEL ASSIGNMENT: Opus or Fable (core-infra scope possible; CLAUDE.md rule 26).

STATE (main, 2026-07-19): CAISO keeper = 2026-07-19-caiso-99-storage-shape
(caiso-97 recipe + caiso_storage_shape_anchor), NOT-YET, fail {C3a-2025 +10.8%,
C3c, C4, C5a(2024 CAVEAT)}; C1 12/12, C2/C3b/C6/C7/C8 PASS. CAISO-99 proved the
measured COD-ramped EIA-860 fleet was ALWAYS live (FINDING-caiso99 §1 — caiso-98
§11's runner.py root cause is falsified/corrected) and landed the measured
NG:OTH p95 envelope (belly +10.9/+9.0/+8.4 → +7.7/+7.6/+6.3, evening −5.3/−4.4/
−2.3, C5a-2024 FAIL→CAVEAT). RESIDUAL BELLY = charge-side economics INSIDE the
envelope: the LP charges at cap in ~every economic hour; the measured fleet's
mean belly rate is ~half its own p95 (day-selectivity from DA-spread bidding /
cycling cost — the caiso-74 disposition's queued SOC-trajectory/cycling lead).

DO (priority):
1. DERIVE-FIRST (no LP): from the caiso99_shape_B repro (re-solve
   scripts/probes/_caiso99_repro_A.py + _caiso99_shape_B.py if the container is
   fresh — same-machine protocol) + EIA-930 NG:OTH + actual RT LMP: measure the
   marginal spread at which the model charges vs the measured fleet's realized
   charge-day spread distribution. Identify the MEASURED anchor for a
   charge-economics mechanism: (a) a cited Li-ion cycling/degradation cost
   ($/MWh throughput, literature/NREL — enters battery vom/dispatch adder,
   registered knob battery_dispatch_adder, rule 24), and/or (b) a DA-spread
   charging threshold measured from the NG:OTH charge-weighted spread. NO
   residual-tuned scalar (rule 25); pre-register bands + gates in the FINDING
   BEFORE any B-leg (caiso-98/99 discipline).
2. File the owner ask for the chosen mechanism (or execute if this prompt's
   carrier rules it); if built: single-delta A/B vs a fresh caiso100_repro_A,
   2023-2025 one bundle (rule 16), SEQUENTIAL solves, score
   scripts/probes/_caiso92_report.py <A> <B> + _caiso_storage_timing.py <B>.
   Gates: C1 12/12 holds; overnight/evening no new under-price; belly falls w/o
   overshoot; C5a improves/holds; C7/C8 PASS. Register whatever the result
   (rule 15); promote only on no-status-regression.
3. WP-3 CT_CHP steam-floor rule-23 derive if ruled (ask PENDING from CAISO-98,
   docs/handoffs/caiso-wp3-ctchp-steam-floor-ask-2026-07-18.md).

GUARDRAILS: all 3 years one bundle (rule 16); NO twin (rule 21); SEQUENTIAL
solves (~30 min/leg, 15 GB box OOMs on 2 concurrent); solves IN-SESSION only
(billed CI). Step 0 fresh container: .venv/bin/python scripts/regenerate_clean.py
(~10 min), confirm data/clean/confirmed-retirements/CAISO/ exists. CAISO
retention 14/15 — the NEXT registration must prune to top-15.

DO NOT REDO (CAISO-99 + prior): tightening the shape envelope below p95 or
sweeping its quantile (rule 25 — the envelope is frozen rule-23 derivation);
re-arming caiso_storage_as_reservation (caiso-74 probe-inert; its holdback is
EMBEDDED in the envelope, validator-enforced); any storage_vintage_ramp
flag/wiring work (ALREADY LIVE — FINDING-caiso99 §1; the runner.py edit is a
forecast-lane item, not a backcast lever); the caiso-94/96/97/99 mechanisms or
derive gates (frozen); widening/re-triggering caiso-87; a season/calendar gate
on any import tranche; re-open the evening import excess via the trimmed
tranche; more CC commitment forcing (caiso-96); a CT_PEAKER floor/mustrun
(caiso-91b); cutting CC offer costs (caiso-92, rule 23); a new STACKED storage
floor (rule 19); throttling measured clean import for CO2 (rule 1); any year
outside 2023-2025 (rule 22 — no CAISO calibration-complete marker).

GIT: main advances fast → git fetch origin main + rebase BEFORE push (expect the
calibration-log append-append conflict; keep BOTH entries). ls-remote the
designated branch before push, recreate from rebased local if gone. git push
WORKS on this machine class (caiso-98/99, ercot-82) — API create_branch first if
the branch is missing; blob-verify every pushed source ≥300 lines by SHA
(rule 27).
<<<END>>>
```

## Open cosmetic item

The `meta.json` top-level `storage_vintage_ramp`/calibration-flags echo records
the `solve_and_persist` KWARG, not the solve config's `backcast_config` base —
the exact recorder-vs-solve divergence class ercot-65 fixed for the wtx driver.
A future infra session should make the calibration-flags echo read the RESOLVED
config (or annotate the echo as kwarg-only) so the next reader is not misled
the way FINDING-caiso98 §11 was.
