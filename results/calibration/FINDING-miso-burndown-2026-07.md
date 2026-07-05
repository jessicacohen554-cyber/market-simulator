# FINDING — MISO honest-rubric burndown (2026-07-05)

**Thread:** MISO is the weakest ISO on the honest rubric (keeper `miso-39-reserve-pergen`
scores 7/9 in-sample, 9/9 under statistical mode — "fails everything scored",
`docs/statistical-mode-results-2026-07.md` §MISO).
**Question (task step 1):** take the three worst failing criteria and adjudicate their root
causes with single-year throwaway diagnostic solves + SRMC-ladder / dispatch-profile evidence.
Specifically: are MISO's committed-band offers (neutral 1.0 after the miso-40 de-leakage)
consistent with a ≥1.0× SRMC floor, and does MISO need its own grounded bands (CAMPD
heat-rate spreads) rather than neutral 1.0s? Does any class show a C7 flat-floor / drag-artifact
signature?

## Method

- **Single-year diagnostic P1 solve** reproducing the current `main` MISO recipe (post-deleak
  default offer curve; `--miso-reserve-pergen` + zonal reserves + priced interchange + seam
  limits + coal sigmoids) for **2024 only** (`results/calibration/miso_diag_2024_baseline`,
  `--year 2024`). Throwaway per rule 15 — **NOT dashboard-registered.** Ran solo with a 12 GB
  swap file (rule-12 memory tier).
- **`fleet_only` SRMC ladder** (no LP): per-class per-tranche band-scaled heat rate → $/MWh,
  and the CT_PEAKER reliability-floor `min_gen` diurnal profile
  (`scratchpad_miso_srmc.py`).
- **Marginal-class attribution + coal measured SRMC** from the solved 2024 P1 dispatch parquet
  (`scratchpad_miso_dispatch.py`): the coal fleet's *measured* undiscounted SRMC is
  reconstructed from the F923 delivered coal cost (`resolve_fuel_prices` +
  `apply_plant_monthly_fuel_prices`, no sigmoid) and overlaid on the model LMP.
- Actual benchmark: MISO 2024 RT mean LMP **$30.80** (`frontend/data/backcast/bench/MISO/2024`).

## The three worst failing criteria (honest rubric, keeper miso-39)

| # | criterion | keeper status | keeper magnitude |
|---|---|---|---|
| 1 | **C1 fuel-mix** | FAIL | CC_REGULAR +19.8 TWh (statmode); COAL_BIT/PRB flip to +30–36 TWh over-run |
| 2 | **C3a mean LMP** | FAIL | −8.5 / −13.6 / −16.9 % (2023/24/25), prices systematically too LOW |
| 3 | **C3c price tail** | FAIL | **0 modelled scarcity hours all 3 years** vs actual 30 / 37 / 88 |

Cross-cutting hard-gate failure: **D-4 off-window binding** — `reliability_floor × CT_PEAKER`
binds 68–70 % of its floored MWh outside its justified window h15-21 (all 3 years).

## Evidence 1 — the gas offer bands are degenerate-FLAT but IMMATERIAL (attribution)

The post-deleak MISO gas classes offer at neutral 1.0 (each unit at its own base heat rate).
The `fleet_only` per-plant tranche ladder (2024, gas $2.19) shows two of them are **fully flat**
— committed = econ_low = econ_high (identical eff-HR):

| class | committed | econ_low | econ_high | peak | shape |
|---|---|---|---|---|---|
| CC_CHP (plant 7991) | 8.00 | 8.00 | 8.00 | 18.00 | **flat**, no part-load premium |
| CT_CHP (plant 10195) | 5.69 | 5.69 | 5.69 | 5.69 | **flat**, no scarcity band at all |
| CC_REGULAR (plant 991) | 5.99 | 6.25 | 6.96→ | 14.65 | grounded ramp (keeper's 1.20/0.95/1.08) |

So the neutral-1.0 committed bands sit **AT** the 1.0× SRMC floor — *not below it* — so there is
**no rule-17 sub-SRMC violation** on the gas bands. What they lack is the physical part-load
premium (a running unit's min-load $/MWh is ~20-40 % above its full-load SRMC — the exact reason
CC_REGULAR's committed was grounded to 1.20).

**But grounding the gas bands would not move the failing criteria, because gas is never
marginal.** Marginal-class attribution over the solved 2024 P1 dispatch (highest-cost dispatching
tranche per hour):

| marginal class | hours | share |
|---|---|---|
| **COAL** | **8228** | **93.9 %** |
| CC_REGULAR | 503 | 5.7 % |
| CC_CHP | 29 | 0.3 % |
| CT_PEAKER / CT_CHP / ST_GAS | **0** | **0 %** |

MISO 2024 runs CC as cheap baseload (CC_REGULAR 187 TWh; gas $2.19 → CC SRMC ~$16-19) and
**coal is the swing / price-setting fuel in ~94 % of hours**. The CT/CHP/ST_GAS classes the task
asked about are small (CT_PEAKER 17.5, CT_CHP 10.9, ST_GAS 6.0 TWh) and inframarginal — their
offer bands never set the LMP.

## Evidence 2 — C3a/C1 root cause: coal is offered BELOW its measured F923 SRMC

Coal's *measured, undiscounted* SRMC (F923 delivered cost, no sigmoid / take-or-pay discount):

| coal tranche | delivered $/MMBtu | measured SRMC $/MWh |
|---|---|---|
| committed | 2.39 | **28.3** |
| mustrun | 2.37 | 29.2 |
| econ_body | 2.35 | **30.4** |
| peak | 2.37 | 41.9 |
| **fleet cap-wt** | | **29.5** |

Overlay:

- **Actual RT mean $30.8 ≈ coal econ_body measured SRMC $30.4** — the real market prices the
  marginal coal MWh at its true delivered cost.
- **Model LMP mean $25.9 / p50 $24.8 sits BELOW even the coal *committed* measured SRMC ($28.3)**
  — the gas-keyed coal passthrough sigmoids (DOF C-1, the audit's largest weakly-identified
  fitted surface) + the sub-1.0 coal band multipliers (COAL committed 0.90, **COAL_PRB econ_low
  0.77**) offer coal ~$4-5/MWh **below its measured delivered cost**.

This single lever explains two of the three failures at once: cheap-below-cost coal
**over-dispatches** (C1 coal over-run, C2 2025 coal +10.4 %) *and* **depresses the marginal
LMP ~16 %** (C3a). Modelled max LMP is $47 with **0 hours > $75** — the coal offer ceiling,
with no scarcity adder above it → **C3c 0-hour tail**.

## Evidence 3 — C7 signature: the CT_PEAKER reliability floor binds all 24 h

The one class carrying a C7 flat-floor artifact is **not** an offer band — it is the
`reliability_floor × CT_PEAKER` limb. Its `min_gen` diurnal profile (2024) is a **constant
38 MW in every hour 00:00–23:59**:

```
hod MW: 00:38 01:38 … 05:38 … 14:38 15:38 … 20:38 21:38 22:38 23:38   (flat)
in-window[15,21] share: 29.2 %   → 70.8 % OFF-WINDOW
```

Root cause: only one CT_PEAKER limb is enabled (MISO-Indiana, `tmax` hot-day driver,
32.2 °C). A hot-day *cooling-load* driver is an afternoon-evening phenomenon, but the registry
engine (`transmission.inject_reliability_floor`) floors **all 24 h of a flagged day** unless the
limb carries a `start_hour`/`end_hour` window — and the MISO CSV had none. So a summer-afternoon
driver floors CT peakers overnight, when their own CF evidence says they are offline (rule 13:
"a floor binding in hours its own driver evidence says the class is offline is a bug by
definition"). CAISO's CT limbs already carry the `[15,21]` window; MISO/ERCOT/NEISO/PJM did not.

## Candidate adjudication

- **(A) "neutral-1.0 gas committed bands are sub-SRMC" — REJECTED.** They sit *at* the 1.0×
  SRMC floor, not below it (Evidence 1). No rule-17 violation. They *are* degenerate-flat
  (missing the part-load premium), but that is immaterial to the failing criteria because gas is
  never marginal in MISO (93.9 % coal). **MISO does NOT primarily need grounded gas bands.**
- **(B) COAL offered below measured SRMC — CONFIRMED as the C1+C3a driver.** The model marginal
  price ($25.9) is below the coal fleet's cheapest *measured* tranche ($28.3); the actual market
  clears at the coal econ_body measured cost ($30.4 ≈ $30.8). The discount is applied by the
  gas-keyed passthrough sigmoids on top of the F923-measured delivered cost. A *committed*
  take-or-pay discount is defensible (contracted fuel is partly sunk), but discounting the
  **marginal (econ_body) tranche** below the measured incremental delivered cost has no
  physical basis — the marginal coal MWh burns fuel bought at market.
- **(C) missing scarcity mechanism — CONFIRMED as the C3c driver.** Modelled max $47, 0 h > $75;
  the reserve co-optimisation (`miso_reserve_pergen`) delivers reserve but no scarcity *price*
  (no RDC/ELMP demand curve). Structural, separate lever — consistent with the miso-39
  scarcity-tail diagnosis (`docs/multi-iso/miso-scarcity-tail-diagnosis.md`).
- **(D) CT_PEAKER reliability floor off-window (C7 / D-4) — CONFIRMED, and fixed.** Flat 24 h
  floor from an afternoon driver (Evidence 3).

## Answers to the task's key questions

1. *Are MISO's neutral-1.0 committed bands consistent with a ≥1.0× SRMC floor?* **Yes** — they
   sit exactly at 1.0× measured SRMC, not below. No sub-SRMC violation. (They lack the part-load
   premium, but see #2.)
2. *Does MISO need its own grounded bands rather than neutral 1.0s?* **Not as the burndown lever.**
   The gas classes that would carry grounded bands are never marginal; grounding them is a
   structural-faithfulness nicety, not a fix for C1/C3a/C3c. The band that is both sub-cost **and**
   marginal is **COAL**, governed by the passthrough-sigmoid surface, not the gas de-leak.
3. *Does any class show a C7 flat-floor / drag-artifact signature?* **Yes — the CT_PEAKER
   reliability floor** (flat 24 h, 71 % off-window). No offer-band drag artifact.

## Fix implemented this session (evidence-indicted, non-floor)

**CT_PEAKER reliability-floor diurnal window** — added `start_hour=15, end_hour=21` to the MISO
CT_PEAKER limbs (`data/raw/reference/reliability_floor_coeffs_MISO.csv`), matching the D-4
justified window `[15,22)` and the existing CAISO CT limbs. Grounded as the afternoon-evening
cooling / net-load ramp footprint of the hot-day driver — a **structural shape parameter, not a
fitted coefficient** (identical across ISOs, physically the peak driver's diurnal shape). The
derive script (`scripts/derive_reliability_coeffs.py`) now emits the window for CT_PEAKER limbs
so a legitimate re-derive preserves it (`_CT_EVENING_WINDOW`). Verified: the CT floor is now
**100 % in-window (h15-21), 0 MW overnight** → D-4 CT_PEAKER passes. Reduces off-window forced
energy without adding a floor (rule 13 compliance). DOF ledger: the reliability-floor coeff
entry gains the window as a structural (non-DOF) shape parameter; no new free parameter.

## Root-cause items LOGGED (not fixed — no residual tuning, no floor; rules #1/#11)

1. **Coal offered below measured F923 SRMC (C1 + C3a).** The gas-keyed coal passthrough sigmoids
   (`COAL_SIGMOID_DEFAULTS[MISO]`, DOF C-1) discount the *marginal* coal tranche below its
   measured delivered cost. The grounded fix is to bound the marginal (econ) coal offer at
   ≥1.0× the plant's measured F923 incremental delivered SRMC — leaving the committed/mustrun
   base free to carry the *contracted* take-or-pay discount — sourced from a published MISO
   take-or-pay / coal-contract fraction, **not** re-tuned to the price residual. This is a
   data-intake + structural task (a coal-SRMC bound is disallowed as a "floor" under the current
   task scope, so it is logged, not applied here).
2. **Missing RDC/ELMP scarcity pricing (C3c).** No admissible supply-side reserve structure
   prices the >$200 tail at hourly resolution (miso-39 gate-4 closed-negative); needs the
   reserve-demand-curve / commitment-posture workstream.

## Files

- `results/calibration/miso_diag_2024_baseline/` — single-year P1 diagnostic bundle (rule 15,
  NOT registered).
- `scratchpad_miso_srmc.py`, `scratchpad_miso_dispatch.py` — SRMC-ladder + dispatch-profile
  extraction.
- Fix: `data/raw/reference/reliability_floor_coeffs_MISO.csv` (+ `start_hour`/`end_hour`),
  `scripts/derive_reliability_coeffs.py` (`_CT_EVENING_WINDOW`).
- Promotion candidate (de-leaked default + CT window, 3-year):
  `results/calibration/MISO/miso_41_ct_evening_window`.
