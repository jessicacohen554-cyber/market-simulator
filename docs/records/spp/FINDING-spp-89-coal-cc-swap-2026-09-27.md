# FINDING — SPP-89: the 2021–22 coal/CC swap is not a fuel-input defect. It splits into two known dead objects.

**Lane** SPP-89 · **ZERO LP** · keeper `2026-09-26-spp-86-coal-extract` (bundle `spp86_arm_span`, basis_sha `d72e5f10`)
· probes `scripts/probes/_spp89_stack_dump.py` (fleet_only rebuild, one year per process) +
`scripts/probes/_spp89_coal_cc_swap.py` · records `results/calibration/_spp89_coal_cc_swap.json`,
`_spp89_gas_offer_sensitivity.json`. Nothing solved, nothing registered, keeper unchanged, no promotion question (rule 31).

## 1. Method

Per year, per hour, for CC_REGULAR and coal (PRB + lignite):

- **A** — actual: CAMPD CEMS gross MW of the model's own plants (gross basis, ~5 % above net).
- **M** — keeper P1 generation (net).
- **I** — the keeper's own offered MW with `mc_base ≤` the **actual** system RT LMP. This tests whether the keeper's
  offers are consistent with the price SPP actually cleared.

## 2. Where the CC shortfall sits (M − A, TWh, gross basis)

| year | actual LMP < $30 | ≥ $30 |
|---|---|---|
| 2019 | +0.92 | −0.16 |
| 2020 | −2.09 | −0.17 |
| **2021** | **−8.92** | −1.93 |
| **2022** | **−7.31** | **−4.49** |
| 2023 | −3.67 | −0.85 |
| 2024 | −4.15 | −0.59 |
| 2025 | −4.97 | −1.20 |

- **2021:** ~82 % of the shortfall is in hours below $30. Real CCs ran 13.8 TWh in $15–30 hours (median LMP $20.9)
  while the keeper's CC offers were $27–47/MWh; only 3.95 TWh of CC was offered at or below the real price. That is
  CC held on through hours below its own cost — SPP-75/77's DA-commitment object (88 % of CC starts are SPP DA
  commitments). No admissible driver; routed as model-class.
- **2022:** ~62 % below $30 (the same object), ~38 % at ≥ $30 (§3).

## 3. The ≥ $30 half: the model loads coal harder than SPP did

Share of the keeper's available MW actually run, hours with actual LMP ≥ $30:

| year | coal actual (gross) | coal keeper | CC actual (gross) | CC keeper | CC offered ≤ actual price |
|---|---|---|---|---|---|
| 2019 | 0.89 | 0.83 | 0.91 | 0.89 | 0.99 |
| 2020 | 0.85 | 0.77 | 0.89 | 0.86 | 0.99 |
| **2021** | 0.92 | **0.96** | 0.83 | 0.73 | 0.72 |
| **2022** | 0.88 | **0.96** | 0.75 | 0.62 | 0.65 |
| 2023 | 0.88 | 0.87 | 0.89 | 0.84 | 0.96 |
| 2024 | 0.83 | 0.83 | 0.93 | 0.89 | 0.94 |
| 2025 | 0.87 | 0.93 | 0.89 | 0.83 | 0.93 |

- **The real coal fleet's in-the-money loading is flat, 0.83–0.92 (gross), in every year.** The keeper's rises to
  **0.96** when gas is expensive, because every coal MW is then far below price. Net-basis actual is ~0.05 lower.
- In 2022 the actual median LMP in $30–60 hours was **$41.7**. Keeper coal cost ≈ **$21**; MMU 2022 coal markup
  **$21.12** (SPP-41 §2.5). Cost + markup ≈ the clearing price. The real market priced coal like gas that year;
  the keeper prices it at cost.
- This is **SPP-44's object** (2022 coal delivery reliability, expressed as a markup). It has no forward-admissible
  driver in EIA-923; reopening needs a delivery-reliability dataset (owner procurement). Not built.

## 4. The four candidates

| # | candidate | measured | verdict |
|---|---|---|---|
| 1 | Gas fuel input | CC offer fuel ≈ Henry Hub monthly within ~$0.3 except Dec-21–Feb-22 (+$1.4–2.7, the lagged Uri true-up / MO reference, SPP-77: +0.08 TWh). Premium over Panhandle Eastern (MMU: HH−PEPL $0.37 in both 2022 and 2023) is ~$0.6–0.8 in **2022, 2023 and 2024 alike** | **Not the object.** No 2022-specific error |
| 1b | Sensitivity: every gas offer −$1/MMBtu (merit proxy, sizing only) | CC **+0.68 TWh in 2022**, +5.3 in 2021; coal **−24 to −34 TWh in 2019/2023/2024** | **Inverted.** It barely moves the failing year and wrecks the passing ones. Any gas-level lever is dead |
| 2 | CC availability | Keeper CC avail 6.8–7.0 GW in 2021–22 vs 6.7–7.4 GW other years. Real CC ran a **lower** share of it in 2021–22 (0.75–0.83 vs 0.89–0.93) | **Not the object.** CC is offered, and out of merit |
| 3 | Merit order | Coal–CC mc spread 2022: $19–39/MWh by month vs ≤ $3 in 2023–24. Real price in 2022 ≥ $30 hours ≈ coal cost + MMU markup | Confirms §3 |
| 4 | Fixed-price / hedged gas | F923 delivered cost already includes contract pricing and tracks spot. Financial hedges do not change the MMU reference cost (daily index). F923 contract-type split **not measured** | **Not supported.** No evidence CCs dispatched below spot |

## 5. Verdict and routing

- **No admissible, material input change. No PRECOMMIT, no shard, no G-DRIFT.**
- The 2021–22 CC_REGULAR C1 failure = **(a)** the DA-commitment low side (SPP-75/77, model-class) — all of 2021, ~60 %
  of 2022 — plus **(b)** the 2022 coal markup / delivery reliability (SPP-44, procurement-blocked) — ~40 % of 2022.
  Both are already on the dead list. The residual is ledgerable on the rung; rule 30(c) keeps it from decertifying.
- **One new measurement for a successor:** the real coal fleet's in-the-money loading is price-invariant (0.83–0.92
  gross of keeper-available); the keeper's is gas-driven (0.77–0.96). This does **not** reopen SPP-41's "no coal
  ceiling" line (that was about LEVEL; this is loading conditioned on being in the money). Any successor must derive
  its driver from measured unit conduct (partial derates, ramp, ambient) and prove it is forward-reproducible, not
  from the residual (rules 1, 13, 19 — it would sit on the SPP-84/85/86 coal-outage family, never beside it).
- Do not re-tune the 0.93 multipliers (rule 1(c)).
