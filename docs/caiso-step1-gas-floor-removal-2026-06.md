# CAISO shape-first overhaul — Step 1 (Lever A): remove the measured gas floor, add the RA must-offer commitment

**Date:** 2026-06-27  **Mode:** mechanism change + shape verification (no dashboard keeper — that is Step 6)
**Branch:** `claude/caiso-shape-calibration-step-1-x8p7a7` (gated together with Step D, solar curtailment)
**Audit:** `docs/caiso-lever-audit-2026-06.md` (Lever A)  **Gate:** `scripts/caiso_shape_probe.py` (PR #963)

---

## What changed

**Removed (defaulted OFF):** `caiso_gas_commitment_floor`. The
`inject_caiso_gas_commitment_floor` slab pinned the CC/CT gas fleet over h9–16
to **0.80 × the measured EIA-930 NG:NG** profile — a measured-**outcome** overlay
(returns `None` for forecast years) that held `CC_REGULAR` ~2× above the real
midday duck-belly and manufactured the ~$0 midday LMP by forcing gas long. It
failed CLAUDE.md #1/#11 (price reached by a non-real mechanism; pinned to
measured generation). The inject function is kept and re-armable with
`--caiso-gas-commitment-floor` for A/B baselines, but is no longer a default.

**Added (default ON for CAISO):** `caiso_ra_mustoffer` — a forward-derivable RA
must-offer **commitment**, not an energy floor. Through the existing P2 pass
(runner P0→P1→P2; `model.commitment.caiso_ra_mustoffer_min_gen`) it holds each
merchant gas CC/CT unit that the economic P1 dispatch runs **before *and* after**
a midday idle gap **shorter than its physical minimum-down time**
(`CC_COMMITMENT_PARAMS` / `CT_COMMITMENT_PARAMS`) at `caiso_ra_min_load_frac`
(0.40) × available capacity across the gap — it cannot economically cycle off and
restart for the evening ramp, so its RA commitment keeps it online at minimum
stable load. The unit is **online at min-load and free to dispatch down to it**,
not pinned to measured output.

- **Forward-derivable / condition-responsive:** the bridge is read off the
  model's own run pattern + the unit's physical min-down time — no measured
  generation enters. A forecast year produces the same structure from its own
  dispatch.
- **Only merchant CC/CT** (`CC_REGULAR` / `CT_PEAKER`) are bridged; cogens
  (`*_CHP`) keep their steam-host must-run, coal/nuclear/non-thermal are never
  RA-bridged. CTs (min-down 1 h) never bridge a multi-hour glut, so in practice
  the floor lands on the combined-cycle fleet — the class the energy-only LP
  over-cycles midday.

Non-CAISO ISOs are byte-identical (`caiso_ra_mustoffer=False`,
`caiso_gas_commitment_floor=False` everywhere except CAISO; the P2 RA branch is
gated on `iso == "CAISO"`).

---

## Shape verification (fixed Step-0 gate, all 3 years)

Two per-plant multi-zone 3-year solves, identical flags except the levers:

- **A — keeper-candidate:** floor OFF + RA must-offer ON (the new CAISO default).
  Scored on **P2** (RA-applied).
- **B — isolation probe:** floor OFF + RA OFF (`--no-caiso-ra-mustoffer`). Scored
  on **P1**. Reproduces the audit's `no_gasfloor` probe exactly (2024 midday LMP
  $36.66 / 7 % ≤$0).

Both flags otherwise: `--priced-interchange --negative-renewable-offers
--caiso-import-gas-coupling --caiso-per-hub-intertie --caiso-corridor-flow-limit
--gas-hub-basis-overlay`.

**`CC_REGULAR` (CAMPD — the reliable primary gate):**

| year | run | hourly r | band× | h10 trough (MW) | model TWh | meas TWh |
|------|-----|---------:|------:|----------------:|----------:|---------:|
| 2024 | **baseline (floor ON)** | 0.79 | 1.15 | **6353** | 57.37 | 45.75 |
| 2024 | **A (floor OFF + RA)** | **0.88** | **1.06** | **4063** | 52.33 | 45.75 |
| 2024 | B (floor OFF, RA off) | 0.87 | 1.09 | 4277 | 53.40 | 45.75 |
| 2023 | A (floor OFF + RA) | 0.85 | 1.08 | 4658 | 58.77 | 50.55 |
| 2025 | A (floor OFF + RA) | 0.83 | 1.29 | 4553 | 53.97 | 37.92 |

real CC_REGULAR midday trough ≈ **3091 MW** at h10 (2024 CAMPD).

**Every ACCEPT criterion met:**
- midday h10 trough **deepens** 6353 → 4063 (2024), toward real ~3091;
- CAMPD hourly r **rises above 0.79** every year (0.88 / 0.85 / 0.83);
- midday band× **falls toward 1.0** (1.15 → 1.06 in 2024);
- the old gas-floor-forced fraction is **~0** (the slab is off; the RA floor is
  class-neutral — see below);
- `CC_REGULAR` TWh **drops toward real** (57.4 → 52.3, real 45.8) — the
  discovered bug for Steps 3/D to absorb on merit, never re-buried in a floor.

**Gas total** (EIA-930) still under-runs every year (2024 model 67.3 vs measured
85.2 TWh) — expected and unchanged in character from the audit; the floor was
*mis-allocating* a short gas envelope into a flat midday slab, not padding a gas
total.

---

## The RA must-offer floor is *live but class-neutral*

Comparing A's P1 (pre-RA economic) with A's P2 (RA-applied) and with B:

- **165 CC/CT units** carry ≥1 midday bridge gap (~7,400 unit-hours, ~0.2 TWh of
  min-load commitment reallocated at the **unit** level in 2023).
- Yet the **class-level** `CC_REGULAR` diurnal is unchanged to within LP
  tie-breaking noise (2023 h10: A_P1 4656 vs A_P2 4658 MW; 2024 A 4063 vs B
  4277, the latter a fresh-cold-resolve difference, not the floor binding up).

So the commitment holds genuinely-RA units online at min-load (real market
structure) **without** inflating the midday class total/shape the measured slab
did — the P2 re-solve just reshuffles *which* RA units hold min-load. This is
exactly the intended "gas-floor-forced fraction ≈ 0": the RA floor is the latent
backstop that begins to bind once Step D removes the midday oversupply and the
economic dispatch would otherwise drive these units cold.

## The midday ~$0 price now comes from oversupply, not the slab

| 2024 midday (h9–15) | LMP mean | ≤$0 share |
|---|---:|---:|
| baseline (floor ON) | $29.78 | 13 % |
| A (floor OFF + RA) | $35.59 | 8 % |
| B (floor OFF, RA off) | $36.66 | 7 % |

With the slab gone the midday LMP rises and the ≤$0 share shrinks — confirming
the audit's finding that the floor *manufactured* the cheap midday by forcing gas
long. The real ~$0 midday must now be produced by genuine oversupply (solar +
imports), i.e. **Step D** (fix solar under-curtailment). The residual midday-gas
over-run (4063 vs 3091 MW) and the persistence of a positive midday LMP are the
discovered bug Step D / Step 3 must close **on merit** — they must never be
re-buried in a floor (CLAUDE.md #1/#11).

---

## Not a keeper yet

This pass produces **no dashboard keeper** by design (that is Step 6, after
Steps D/3/etc. land). It removes the forbidden measured-outcome slab and installs
the structurally-correct, forward-derivable RA must-offer commitment in its
place, verified on dispatch *shape* (hourly r + diurnal band/trough), not annual
class-total MAE.

Reproduction (per-plant multi-zone, ~12 min each; cap 2 concurrent):

```
# A — keeper-candidate (new CAISO default: floor off, RA must-offer on)
.venv/bin/python scripts/run_calibration_full.py --iso CAISO --year 2023 2024 2025 \
  --priced-interchange --negative-renewable-offers \
  --no-caiso-gas-commitment-floor --caiso-ra-mustoffer \
  --caiso-import-gas-coupling --caiso-per-hub-intertie \
  --caiso-corridor-flow-limit --gas-hub-basis-overlay --out-dir <dirA>

# B — isolation probe (floor off, RA off): reproduces the audit no_gasfloor probe
#   add --no-caiso-ra-mustoffer to the above.

# score (CC_REGULAR is the primary gate; A on P2, B on P1)
.venv/bin/python scripts/caiso_shape_probe.py <dirA> --year 2023 2024 2025 --pass P2
```
