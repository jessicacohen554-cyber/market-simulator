# Handoff — NYISO downstate synchronised-reserve (path A probe → path B scope)

> **Status (2026-06-25): PATH A TESTED — REJECTED PROBE. The online-only
> synchronised-reserve mechanism is CONFIRMED (it lifts CT_PEAKER and relieves
> the CC over-run) but is INSUFFICIENT for the scarcity tail (C3c unchanged,
> C3a slightly worse), exactly as PR #877 predicted. Keeper stays
> `nyiso 27 cc-offer` (`keepers.json[NYISO]` unchanged). The path-A lever
> (`--nyiso-synchronised-reserve`) is REVERTED on the branch; this doc scopes
> path B.**

Run: `nyiso 29 synch-reserve [probe]` (id `2026-06-25-nyiso-29-synch-reserve`,
bundle `results/calibration/nyiso_29_synch-reserve`). Registered on the
dashboard as a rejected probe. The full path-A implementation is preserved in
the bundle's `model_changes.diff`.

## What path A did (the LP-linear online proxy, PR #877 recommendation #2)

A NYISO-only, default-off lever `--nyiso-synchronised-reserve` adds, behind the
`nyiso_synchronised_reserve` config flag:

- A **NYC 10-minute spinning sub-requirement** = `NYISO_SPIN_FRACTION × NYC
  10-min total` = `0.5 × 500 = 250 MW`. The fraction `0.5` is the published
  NYISO rule (10-min spinning = ½ largest contingency; the same ½ rule that
  fixes `nyca_10min_spin = 655 MW`), a measured market-design constant — **not**
  fitted to any residual.
- A **third reserve class** (the quick-start subset again) that is
  **online-bounded**: `dispatch._build_reserve_rows` adds a per-zone row
  `R[c,z] ≤ Σ_g P[g,t]` for the spinning class, so only already-generating
  capacity supplies spin. Combined with the standard headroom row
  (`Σ P + R ≤ Σ cap`), the effective bound is `R ≤ min(P, cap − P)` — an idle
  peaker (P = 0) now contributes **zero** spin, so to hold the 250 MW the NYC
  quick-start fleet must commit (generate ≥ the spin).

This directly attacks PR #877's confirmed root cause: the pure-ED LP credits an
idle peaker's full pmax as deliverable reserve (`P = 0 ⇒ R = cap`), so the
downstate families never bind.

Wiring: `results.scarcity.nyiso_reserve_coopt_inputs` (returns the third
eligibility row + `online_class_mask`), `dispatch._build_reserve_rows`
(`online_class_mask` → online block, inserted **between** the headroom and
balance blocks so the balance-row dual slice is unaffected), threaded through
`build_constraints` / `DispatchModel` / `solve_dispatch`, the
`nyiso_synchronised_reserve` `ScenarioConfig` field, and the
`--nyiso-synchronised-reserve` CLI flag in `run_calibration_full.py` /
`run_calibration.py`. All other ISOs are byte-identical (`online_class_mask` is
`None` everywhere except NYISO with the flag on).

## Result vs the `nyiso 27 cc-offer` keeper

| metric | keeper (27) | probe (29) | read |
|---|---|---|---|
| C1 CT_PEAKER 2023 | −1.30 TWh | **−0.92** | ↑ toward 0 (mechanism works) |
| C1 CT_PEAKER 2024 | −1.51 TWh | **−1.05** | ↑ toward 0 |
| C1 CC_REGULAR 2023 | +1.65 | **+1.36** | over-run ↓ (predicted) |
| C1 CC_REGULAR 2024 | +2.00 | **+1.43** | over-run ↓ |
| C1 ST_GAS 2024 | −4.17 | −4.30 | ~flat (slightly worse) |
| C3a mean LMP 2024 | −9.7% | **−11.0%** | **regressed −1.3 pp** |
| C3c >$300 (23/24/25) | 1/0/8 | **1/0/8** | **unchanged — tail did not fire** |

**Diagnosis (PR #877's exact prediction).** The grounded 250 MW NYC spin is
small enough that the online quick-start fleet covers it **cheaply** — the
spinning family clears at a low reserve price and never reaches the >$300 RCPF
step — so the scarcity tail (C3c) does not move. The peakers that commit for
spin add low-cost pmin energy in **non-scarce** hours, which dilutes the mean
(the small C3a dip). Online-only spin on the small grounded **sub**-requirement
therefore moves the **energy** frontier (CT_PEAKER / CC) but not the **scarcity**
tail. Inflating the spin fraction above the published 0.5 to manufacture the
tail is forbidden (rule #12), so path A is spent at its grounded landing.

A 4-unit end-to-end LP confirms the mechanism in isolation: with ample
quick-start so every other family is slack, turning the lever on drives the NYC
peaker to exactly the 250 MW spin requirement (idle → 250 MW) and lifts the
reserve price > 0; off, it stays idle. (See the probe commit's test
`test_synchronised_reserve_adds_online_nyc_spin_family` for the input-assembly
checks.)

## Scope for path B (the real fix — PR #877 recommendation #1)

Path A proves the **direction** but not the **magnitude**. The gap is that A
prices only a 250 MW spin sub-slice on an otherwise-slack family. Path B must
make the **full downstate reserve stack bind on committed-only headroom**:

1. **Committed-only satisfaction, not a sub-requirement.** Extend the P2
   commitment screen (`model/commitment.py`, `commitment_enabled`, currently a
   heuristic post-P1 screen with no in-LP online binary) into a **zonal/family**
   formulation where the downstate NYC/SENY 10-min **and** 30-min families are
   satisfiable only by **committed** units — i.e. the entire downstate reserve
   requirement (not just the 250 MW spin) draws on online headroom. Then the
   family binds against genuine online headroom in tight hours and the RCPF dual
   stacks into the NYC LMP (C3c ↑, C3a ↑), with peakers committing across the
   whole stack (CT_PEAKER ↑ further).
2. **Zonal/family, not per-gen.** Per-gen reserve+commitment columns OOM at
   per-plant fleet scale; keep the formulation zonal/family and concurrency-cap
   the heavy multi-zone LPs (~2 at once, CLAUDE.md rule #14). Memory is the
   primary risk (PR #877: "memory ↑↑").
3. **Calibrate the committed fraction to the MEASURED spin requirement**, not a
   residual fit (the `0.5` fraction and the `nyca_10min_spin = 655 MW` /
   `nyc_10min_total = 500 MW` anchors are the grounded inputs to reuse).
4. **Re-use the path-A online block** (`dispatch._build_reserve_rows`
   `online_class_mask`) as the in-LP coupling between commitment state and
   reserve — the diff is in `results/calibration/nyiso_29_synch-reserve/
   model_changes.diff`.

## Guardrails carried forward (unchanged)

- NYISO-only, default-off; all other ISOs byte-identical.
- The spinning/online fraction is the **measured** NYISO market-design rule, not
  a residual fit. The tail must emerge **endogenously** from a binding reserve
  requirement — never a CEMS pin, a tail price-adder, or a steepened curve
  (rules #1/#11/#12). The `nyiso-25 rcpf-steep` probe already refuted
  curve-steepening; PR #877 Finding 4 already refuted import/interface
  tightening. Neither is the lever.
- 2024/25 gas-TOTAL deficit + downstream CO2 stay the EIA-930/EIA-923 basis floor
  (`docs/nyiso-td-loss-resolution-2026-06.md`; `td_loss_factor = 0`).
