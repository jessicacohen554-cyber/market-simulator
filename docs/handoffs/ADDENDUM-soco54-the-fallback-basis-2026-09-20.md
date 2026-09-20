# ADDENDUM to PRECOMMIT-soco-54 — what the arm actually falls back to, and the one imprecision it inherits

**Written BEFORE the arm legs landed** (pinned PRECOMMIT SHA `d85e0c47567b0ae8258a99920d512fd3fe8fe1df`),
so it cannot be written to fit a result. Rule 29 `[R-SCREEN]` (b)'s "recorded in the PRECOMMIT or
its addendum before the arm is solved".

## 1. The fall-back is MEASURED → MEASURED, not measured → assumed

PRECOMMIT §4 said the arm's single gas series is "built on the run's `gas_price_override = 2.54`,
the realized 2023 Henry Hub annual average, plus the model's delivery basis". Traced to source,
that basis is itself a SOCO measurement, registered by lane SOCO-20 on 2026-09-14
(`config/fuel_trajectories.py:397–412`):

> `GAS_BASIS_DIFFERENTIAL["SOCO"] = 0.64` — *"the EIA-923 delivered-gas basis, the PJM/NYISO
> construction — quantity-weighted Schedule-5 delivered gas cost to the SOCO balancing
> authority's gas plants … minus the Henry Hub annual mean: **+$0.49 (2023: 3.029 vs 2.536),
> +$0.64 (2024: 2.832 vs 2.192), +$0.65 (2025: 4.183 vs 3.529)**."*

$2.54 + $0.64 = **$3.18**, which reproduces the $3.179/MMBtu annual mean the `fleet_only` rebuild
reports for every SOCO gas unit under the arm, to the third decimal.

**This sharpens the rule 14 `[R-ACCURATE]` argument rather than weakening it.** The arm does not
replace a measured input with a modelled one. It replaces a **per-plant contract print** with a
**footprint-wide quantity-weighted delivered price built from the SAME EIA-923 Schedule-2
receipts** — measured → measured, re-aggregated to the grain at which a marginal dispatch
decision is actually made. That is verbatim rule 14's misalignment clause: *"prefer a
reconciled version of the real data over a pure guess."*

## 2. THE IMPRECISION, DECLARED AT FULL MAGNITUDE

`GAS_BASIS_DIFFERENTIAL["SOCO"]` is a **single scalar, 0.64, which is the 2024 value**, applied
to every year. The measured per-year basis is **+0.49 / +0.64 / +0.65**. So under the arm:

| year | measured basis | applied | error | at ~11 MMBtu/MWh |
|---|---|---|---|---|
| 2023 | +0.49 | 0.64 | **+0.15** | **≈ +$1.65/MWh on every gas unit** |
| 2024 | +0.64 | 0.64 | 0.00 | 0 |
| 2025 | +0.65 | 0.64 | −0.01 | ≈ −$0.11/MWh |

**And the constant's own comment says it was registered for a different job**: *"Forward-year /
fallback value only — the SOCO backcast prices gas per plant off EIA-923 monthly delivered cost
like PJM/NYISO."* This arm promotes a declared **fallback** constant onto SOCO's **primary
backcast** gas-pricing path. That is a real change in the constant's role and it is stated here
rather than discovered later.

**Why it does not change the lever's sign, and is not swept.** The error is a **uniform level
shift applied identically to every gas unit** — it adds ≈$1.65/MWh to all of them in 2023 — so it
moves the gas block against **coal and hydro**, not `CT_PEAKER` against `ST_GAS`. The merit-order
inversion this lane is testing is a *relative* ordering inside the gas block, and a common adder
cannot touch it. Concretely: PRECOMMIT §4's 2023 reordering (Hartwell $27.15 → $40.06, Yates
$44.59 → $38.32) is unchanged by any common basis, because both legs carry it.

What it CAN do is push the gas block up against coal in 2023 — which is why PRECOMMIT P8 bands
`COAL_PRB` / `COAL_BIT` at < 1.0 TWh rather than at zero, and that band stands.

## 3. ROUTED, NOT TAKEN HERE

**Making `GAS_BASIS_DIFFERENTIAL["SOCO"]` per-year (+0.49 / +0.64 / +0.65) is a rule 23
`[R-FROZEN-DERIVE]` re-derivation cited to SOURCE DATA — the three years' own receipts, already
computed and committed in the constant's own comment — and never to a residual.** It is NOT
taken in this lane, for two reasons, both stated before the solve:

1. It would make this a **two-delta** arm, and the composer asserts a single delta.
2. Taking it *after* seeing the arm's 2023 result would be selecting a parameter on the outcome,
   which rule 1 `[R-STRUCT]` forbids however it is motivated.

A successor takes it as its own single-delta change, on the source-data citation, whatever this
lane's result turns out to be.
