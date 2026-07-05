# Fix Plan: Closing Wiring & ISO Coverage Gaps

**Date:** 2026-06-29  
**Companion:** `gap-inventory.md` (gap definitions), `prompt-pack/` (execution prompts)

**Status 2026-07 — 15/16 items LANDED.** Verified against current `runner.py` /
`run_calibration.py` by `docs/handoffs/orchestrator-unification-plan-2026-07.md` §2.1;
see that table for per-item proof. **Do not re-fix any landed item below.** The one
remaining open item, **A5 (ERCOT single-product reserve supply cap)**, is absorbed into
the unification plan's **Stage 2** (`reserve_config._ercot_design`) — do **not** execute
`prompt-pack/w2-ercot-supply-cap.md` as written; it targets `runner.py` directly, which
is superseded by the shared-`reserve_config` fix. The **CAISO bidirectional
intertie/solar-shape/gas-coupling** and **NEISO cold-snap derate** overlays flagged as
post-inventory drift (unification plan §2.2) are owned by unification **Stages 5/6**
(interchange and fleet unification, respectively) — **per-mechanism patching of them is
retired**; do not open a new prompt for any of the four. See the unification plan for
the current staged migration and its regression-gate status.

## Sequencing Principles

1. **Structure before tuning** — wire the LP mechanism first; calibrate coefficients later.
2. **High-severity first** — CRITICAL/HIGH gaps before MEDIUM/LOW.
3. **Independence** — each wave's items can be executed in parallel across sessions.
4. **Within-wave order** — items within a wave share no dependency; solve in any order.
5. **Model tier** — each prompt specifies Sonnet (mechanical wiring) or Opus (structural design decisions).

---

## Wave 1 — CRITICAL: Missing LP Structure (parallel, Opus)

These gaps change the LP's feasible region or objective. Each is a standalone fix.

| Task | Gap ID | Model | Est. lines | Depends on |
|------|--------|-------|-----------|------------|
| Wire hydro budget into forecast | A1 | Opus | ~80 | — |
| Wire NEISO reserve co-opt into runner.py | A2 | Sonnet | ~60 | — |
| Wire PJM reserve supply cap + online gating into runner.py | A3 + A4 | Sonnet | ~30 | — |
| Wire reference-price interface into runner.py | A7 | Opus | ~120 | — |

**Why Opus for A1:** The hydro fleet builder (`_hydro_fleet`) currently lives in `run_calibration.py` as a local function. Wiring it into the forecast path requires a structural decision: extract it to a shared module (e.g. `data/hydro.py`) or duplicate a thin wrapper in runner.py. The forecast path needs `forecast_budget=True` with the `hydro_year` lever, NOT the measured EIA-930 monthly pin.

**Why Opus for A7:** The reference-price interface wiring touches import-node construction (branching on `config.reference_price_interface`), mc injection post-assembly (`inject_reference_price_mc`), and firm-export flooring. Multiple code paths interact (CAISO per-hub vs generic vs fitted tranches). Requires understanding the builder topology.

**Prompt files:** `prompt-pack/w1-hydro-budget.md`, `prompt-pack/w1-neiso-reserve.md`, `prompt-pack/w1-pjm-reserve-caps.md`, `prompt-pack/w1-reference-price.md`

---

## Wave 2 — HIGH: Silently Neutered ScenarioConfig Flags (parallel, Sonnet)

Each is a straightforward wiring task: the mechanism is already implemented, the runner just doesn't call it.

| Task | Gap ID | Model | Est. lines | Depends on |
|------|--------|-------|-----------|------------|
| Wire negative renewable offer floor into runner.py | A6 | Sonnet | ~10 | — |
| Wire ERCOT single-product reserve supply cap | A5 | Sonnet | ~10 | — |
| Wire CAISO RA must-offer P2 trigger into runner.py | A10 | Sonnet | ~15 | — |
| Wire MISO reserve co-opt into calibration _run_dispatch | A13 | Sonnet | ~50 | — |

**Prompt files:** `prompt-pack/w2-negative-offers.md`, `prompt-pack/w2-ercot-supply-cap.md`, `prompt-pack/w2-caiso-ra-p2.md`, `prompt-pack/w2-miso-reserve-cal.md`

---

## Wave 3 — MEDIUM: Forward-Native Fleet Mechanisms (parallel, Sonnet/Opus)

| Task | Gap ID | Model | Est. lines | Depends on |
|------|--------|-------|-----------|------------|
| Wire CT/ST netload drag floors into runner.py | A8 | Sonnet | ~30 | — |
| Wire CAISO solar deliverability derate into runner.py | A9 | Sonnet | ~20 | — |
| Wire NYISO import node reconciliation (forecast mode) | A11 | Opus | ~40 | W1/A7 (reference-price interface must be wired first) |
| Add pumped storage to forecast storage builder | C2 | Opus | ~60 | — |

**Why Opus for A11:** The import-node reconciliation in forecast mode targets `config.nyiso_forward_net_import_twh` shaped by forecast load — requires understanding how the band constraint interacts with the reference-price seam that Wave 1 wires.

**Why Opus for C2:** Pumped storage in the forecast requires a design decision about whether to source from EIA-860 (like backcast) or from a parameterized PS fleet (like batteries). PS has fixed capacity (no growth), so EIA-860 is likely correct — but the interaction with `build_default_storage` and `storage_units_to_arrays` needs care.

**Prompt files:** `prompt-pack/w3-netload-drag.md`, `prompt-pack/w3-caiso-solar.md`, `prompt-pack/w3-nyiso-import-recon.md`, `prompt-pack/w3-pumped-storage.md`

---

## Wave 4 — LOW / Cross-ISO: Topology & Coverage (sequential, Sonnet)

| Task | Gap ID | Model | Est. lines | Depends on |
|------|--------|-------|-----------|------------|
| Wire gas offer curve (split_gas_tranches) into runner.py non-CAMPD path | A12 | Sonnet | ~10 | — |
| Bake NYISO upgraded TTC into iso_configs.py topology | B4 | Sonnet | ~5 | — |
| Wire storage_vintage_ramp + storage_cap_profiles into runner.py | C3 | Sonnet | ~25 | — |

**Prompt files:** `prompt-pack/w4-gas-offer-curve.md`, `prompt-pack/w4-nyiso-ttc.md`, `prompt-pack/w4-storage-vintage.md`

---

## Deferred (requires calibration work, not wiring)

| Task | Gap ID | Notes |
|------|--------|-------|
| Calibrate PJM reliability floor coefficients | B2 | Needs PJM CAMPD regression (CT CF vs temperature/net-load) |
| Calibrate SPP offer curves | B1 | Needs SPP calibration run |
| Extend storage_vintage_ramp to PJM/MISO/NYISO/SPP | B3 | Needs per-ISO EIA-860 storage COD data validation |

---

## Execution Notes

- **Each prompt is self-contained.** It includes the gap description, file locations, what to change, what NOT to change, and acceptance criteria.
- **No prompt modifies source files beyond its scope.** Each is scoped to the minimum diff.
- **Every prompt requires a test.** At minimum: construct a trivial config with the flag on, verify the mechanism fires (log message, dispatch_kwargs key present, or LP constraint count changes).
- **CLAUDE.md rules apply.** Every prompt reminds the session of rule #1 (structure first), #11 (no measured-outcome pins), and #12 (measured-data admissibility test).
