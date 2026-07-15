# pjm-112 — measured unit-availability completion (C3c summer-tail solve) — 2026-07-15

**Run id:** `2026-07-15-pjm-112-unit-availability` · **ISO:** PJM · **years:** 2023 2024 2025
**Determination:** NOT-YET (deciding criterion C3c price_tail) — **NOT-YET CANDIDATE, not a keeper.**
**Keeper stays `2026-07-15-pjm-111-cc-reconcile`.**

*(This is the durable per-run record; the canonical `docs/calibration-log.md`
append is pending a git-push-capable context — the 890 KB log exceeds the
`push_files` inline-content limit, per the session charter. The dashboard
sidecar + `calibration_attestation.json` + `docs/DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md`
§8.1 carry the full result.)*

## Mechanism (pre-committed by the Fable design session; no redesign, no constant touched)

Completed the measured unit-availability overlay family for PJM at **unit grain**
— one phenomenon (measured unit availability the ≥5-day zero-run extract cannot
see), two window shapes, zero fitted scalars:

- **LEG A** — `ScenarioConfig.unit_outage_short_windows=True`. The short (<5-day)
  baseload-coal full-stop deriver's `SHORT_BASELOAD_CF` (0.55, unchanged) guard
  basis changed from **raw-annual CF → WHEN-OPERABLE CF** (mean gross over hours
  outside the unit's own ≥5-day standard windows). Identification correction
  cited to diagnosis §7 (event-unit when-operable CF 0.58–0.72 vs raw-annual
  0.09–0.36), NOT to a price residual. Re-derived `campd-unit-outages-short-PJM.csv`
  (290 windows, 37 plants). The coal-only detector, 1–5-day cap and in-merit
  filter are UNCHANGED; PJM-only re-derive (MISO short extract untouched, rule 24).
- **LEG B** — `ScenarioConfig.unit_partial_outage_windows=True` (new tier-3 bool,
  default off). Unit-grain partial-derate plateaus emitted to
  `campd-partial-outages-PJM.csv` (76 windows, 21 plants), detected on each unit's
  CEMS gross with the plant-level partial deriver's constants VERBATIM
  (`_MIN_DAYS=5`, `_SMOOTH_DAYS=7`, `_CEILING_FRAC=0.65`, `_RUN_FLOOR_CF=0.06`) +
  the same when-operable guard + in-merit filter; unit derates aggregated to the
  plant exactly like `unit_outage_derate_factors` (unit-capacity share, concurrent
  units summed, clipped at full). The plant-grain partial detector (measured to
  over-fire ~43 TWh/yr on PJM) stays ERCOT-scoped.

Both overlays fired (2023: short 206 plant-tranches, partial 134). `run_config`
records both flags True (the prb_overrides channel; ERCOT-65 recorder check done).

## Build-time provenance (gate #4, verified before the solve)

`scripts/probes/_pjm112_provenance_check.py`: the two derived extracts recover
**1502 MW** mean across the 22 summer 2025 DA-tail hours (short 1314 + partial
188), ≥ 800 MW required. **PASS.**

## Pre-committed gate (diagnosis §8) — all five adjudicated together

| gate | test | result |
|---|---|---|
| **1** | C3c-2025 model tail (`ordc.hoursGt200.model`, any-zone energy-only) ∈ [26, 102] h | **MISS — 18 h** (pjm-111 was 17; +1 h) |
| 2 | 2023 tail ≤ 18 / 2024 tail ≤ 12 | HOLD (1 / 1) |
| 3 | no currently-PASS criterion flips (C1 16/16, C2, C3a, C3b, C4, C5a, C6, C7, C8) | HOLD (every criterion PASS, matches pjm-111) |
| 4 | provenance ≥ 800 MW | HOLD (1502 MW) |
| 5 | LOYO within 2023–2025 (no year regressing on 1–3) | HOLD |

**Outcome (1): gate #1 misses, gates 2–5 hold → NOT-YET candidate; the summer
tail is a QUANTIFIED DISCLOSED BOUNDARY.** The mechanism is measured and on-target
(1502 MW of the +3.0 GW coal phantom removed in the tail hours) yet moves the
marginal price rung past $200 in only 1 additional hour. The boundary is (a) the
~1.7 GW of 3–4-day event partial derates invisible to the 7-day-median plateau
detector (§7) and (b) the **flat zonal congestion surface (§5) — the binding
residual**: cheap western/ComEd energy flows east unconstrained + import
backfill absorb the removed coal, so system-wide shortage is still needed to
clear $200. Fixing the surface is a topology/interface charter of its own, not
this lane. Per rules 1/11/23/26, no constant/window/threshold was revisited.

## Owner sign-offs requested with this bundle

1. The **when-operable guard-basis change** (LEG A identification correction).
2. **Leg-B unit-grain partial admissibility** (rule 13 — the new datatype).
3. Keeper promotion is **NOT** requested (gate #1 missed). The measured overlay
   stays in as the structurally-faithful, zero-DOF availability model; it does
   not on its own close C3c, now disclosed as congestion-surface-bound.

DOF ledger: pjm-111's 15 entries carried VERBATIM + 2 zero-DOF measured entries
(the short and partial PJM extracts; CAMPD source, re-derive on vintage change
only, rule 23). n_entries 15 → 17, n_residual unchanged (6). No ablation twin
(rule 20).
