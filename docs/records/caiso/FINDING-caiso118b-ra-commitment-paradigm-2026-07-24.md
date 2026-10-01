# FINDING — caiso-118b STRUCTURAL: CAISO is modeled with the wrong commitment paradigm. The model commits gas by ECONOMIC detection (its own P0 belly duals), which under-commits to ~1.5 GW because it prices commitment on a belly LMP the model itself over-imported into — a self-fulfilling under-commitment. Reality commits ~15.6 GW of RA MUST-OFFER gas by OBLIGATION (funded by RA capacity payments, independent of the hourly LMP), running ~10 GW at min-load as price-takers. The published obligation quantity (`CAISO_RA_MUSTOFFER_GAS_MW` = 19.1/15.6/15.6 GW, DMM Annual Report) is already in the codebase but wired only as a CAP (`quantity_gate`, off), never as the commitment DRIVER; the keeper further under-commits via `min_load_frac=0.26` (physical ~0.40–0.57). The 9 ON import mechanisms (esp. the 4 `dsw_*_clean` tranches) are compensation: the model substitutes ~2–3 GW of economic belly import for the gas it won't commit. NO SOLVE, nothing registered (2026-07-24)

**Structural diagnosis, measurement-only, register nothing.** Companion to
`FINDING-caiso118-belly-price-undercommit-2026-07-24.md` (the belly derive that
led here). Reproduction: `scripts/probes/_caiso118b_ra_paradigm_audit.py` +
`scripts/probes/_caiso118_belly_price_derive.py` (no LP). Keeper
`2026-07-19-caiso-102-hourfix` UNCHANGED.

---

## The error in one sentence

**CAISO is a bilateral-RA-capacity market where the gas fleet is committed by
must-offer obligation and runs as a price-taker with the energy market clearing
the residual; the model instead treats the fleet as fully economic (merchant
merit-order), so it commits too little gas, substitutes imports, and lets
merchant MC set a belly price the residual clearing should set.**

## The three grounded facts (audit `_caiso118b_ra_paradigm_audit.py`)

### A. The measured commitment DRIVER exists and is unused

`CAISO_RA_MUSTOFFER_GAS_MW` (CAISO DMM Annual Report, "Must-Offer: Gas-fired
generators" — the literal 24×7 bid-inserted must-offer fleet): **2023 19,130 MW,
2024/25 15,566 MW.** At physical CC min-load (~0.5) that is **~8–10 GW committed
at min-load = the ~8.5–10.5 GW belly gas reality runs** (caiso-118 INV5). The
model commits **~1/3** of it (~1.5 GW, D-2 `ra_mustoffer_bridge` 3.2 TWh/yr).
The quantity is rule-13-clean (published, forward-reproducible) — but it is wired
only as a *cap* on the economic bridge (`caiso_ra_mustoffer_quantity_gate`, off),
never as the commitment floor.

### B. The flag stack: 9 import ON, 0 obligation-commitment ON

| category | ON | flags |
|---|---|---|
| **Import** (shape/floor/price) | **9** | `corridor_flow_limit`, `firm_import_shape`, `firm_import_selfschedule`, `perhub_firm_base`, `per_hub_intertie`, `dsw_surplus_clean`, `dsw_overnight_clean`, `dsw_daytime_clean`, `dsw_daytime_evening_trim` |
| **Obligation-commitment** | **0** | `gas_commitment_floor`, `ra_mustoffer_quantity_gate`, `lcr_commitment_credit`, `commitment_posture` — **all off** |
| Economic-detection commit | 6 | `ra_mustoffer` + startup/decommit bridges; **`min_load_frac=0.26`** (code default 0.40, ERCOT-measured 0.574) |

The single largest ON category is import machinery; the obligation-commitment
category is entirely off. `min_load_frac` lowered to 0.26 (below the physical
turn-down) is a fit-to-shrink-forced-energy smell (rule 11-adjacent) that deepens
the under-commitment.

### C. The over-import is economic substitution for uncommitted gas

| year | firm self-sched floor (belly) | actual net-import | model total import | **economic over-import** |
|---|---|---|---|---|
| 2023 | 890 MW | 651 | 3,075 | **~2,185** |
| 2024 | 1,245 MW | 1,341 | 3,889 | **~2,644** |
| 2025 | 1,355 MW | 1,766 | 3,757 | **~2,402** |

The firm self-schedule floor (~1 GW belly) is *correct* — it matches actual
belly net-import. The **~2–3 GW above it is economic import** the LP chooses
because belly gas MC ($26) > the cheap DSW-hub import ($10). The four
`dsw_*_clean` tranches exist precisely to supply that cheap belly/overnight
import depth — i.e. to fill the belly the uncommitted gas vacates.

## Why economic detection can never fix this (the circularity)

The `caiso_ra_mustoffer` bridge holds a unit committed only if
`startup_cost > (MC − LMP_gap) × min_load × gap_hours`, pricing the belly gap at
**the model's OWN P0 belly LMP**. But that belly LMP is low *because the model
over-imports* — so `MC − LMP` is large, the bridge concludes "gas should
decommit," imports fill in, and the loop closes. **Economic detection priced on a
belly the model itself mis-cleared is a self-fulfilling under-commitment.** Only
an *exogenous* obligation-driven commitment (independent of the model's own LMP)
breaks it — which is exactly what RA must-offer is in reality.

## The reframe (caiso-119) and its falsifiable test

Wire `CAISO_RA_MUSTOFFER_GAS_MW` as an **obligation commitment floor** (not a cap
on economic detection): commit the RA fleet at its published quantity at physical
min-load as price-takers, and restore `min_load_frac` to its physical value
(~0.5). Rule-13-clean (published DMM quantity), rule-1 (right structure first),
and the capacity payment is the funding that makes it legitimate rather than a
forced floor.

**The test that it is the right structure, not another patch:**
1. belly gas → ~10 GW, belly price → ~$15 (C3a-belly);
2. economic belly import collapses to the firm floor ~1 GW → C5a fixes **without**
   the import patches;
3. **delete** `dsw_surplus_clean` / `overnight_clean` / `daytime_clean` /
   `daytime_evening_trim` (and relax `corridor_flow_limit`) and the fit holds or
   improves.

If committing the RA fleet retires 3–4 import mechanisms, that is rule-1/rule-15
confirmation the import stack was compensation. If it needs all the patches kept,
the thesis is wrong.

**Guardrail (rule 14):** ~10 GW committed gas is well over the forced-energy
budget, so it rides the v2.2 grounded-above-budget path — but it *is* grounded
(published RA obligation, reality's exact dispatch), so it passes on D-4 window +
D-1 shape, scored not asserted. **KILL** if the committed level is fitted to the
price/volume residual rather than set to the published quantity (rule 13), if
`min_load_frac` is tuned below physical to manage forcing (rule 11), or if it
breaks the evening.

## DO-NOT-REDO / carry-forward

- The economic-detection bridge (`caiso_ra_mustoffer` + startup/decommit) as the
  SOLE commitment channel — self-fulfilling under-commitment (this finding). Keep
  it as the marginal/economic layer ABOVE the obligation floor, not the driver.
- The measured-NG:NG generation pin (`caiso_gas_commitment_floor`, the original
  floor) — a measured-OUTCOME pin (rule 11), already retired; the fix is the
  published RA *quantity*, not the measured generation.
- Carried from caiso-118: solar rung inert (98% absorbed); import-hub reprice is a
  volume lever (coupled). Neither is the belly-price lever — the commitment STATE
  is.

Reproduction: `scripts/probes/_caiso118b_ra_paradigm_audit.py` (A/B/C above) +
`scripts/probes/_caiso118_belly_price_derive.py` (the belly derive).
