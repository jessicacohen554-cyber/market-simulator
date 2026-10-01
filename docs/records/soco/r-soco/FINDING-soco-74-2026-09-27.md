# FINDING — soco-74: SOCO's EIA-923 contract type does not identify a sunk coal share; the take-or-pay family is refused ex ante (zero LP, no solve)

Lane soco-74, 2026-09-27. Keeper `2026-09-26-soco72-gas-basis-window` (bundle `soco72_span`) is **unchanged**. There
is no PRECOMMIT, no shard and no registration. Task 1's identification test fails, so the lane stops as its handoff
instructs.

- **Probe:** `scripts/probes/_soco74_contract_identification.py`. It reads the committed `data/raw/coal-receipts`
  (EIA-923 Page 5, Purchase Type) and `data/raw/coal-stocks` corpora, 2017–2024. The corpus has no 2025 release.
- **Question** (from the soco-73 handoff): does SOCO's own Schedule-5 contract type support a measured sunk/avoidable
  split for Bowen, Scherer, Daniel, Gaston, Barry, Crist and Wansley under rules 13 / 14 / 21? And is "contract"
  minimum-take (sunk), or only price-fixed (still avoidable)?

## Answer: NOT IDENTIFIABLE. In SOCO's own record, "contract" means price-term, not minimum-take.

### 1. The data has no quantity obligation to read

- **What the form records.** Page 5 gives each delivery a Purchase Type (C/NC = term ≥ 1 yr, S = spot, T = tolling)
  and a `Contract Expiration Date`. That is the only contract attribute in the corpus.
- **What is missing.** No field records a minimum or contracted quantity. `QUANTITY` is tons delivered, i.e. an
  ex-post outcome.
- **Consequence.** `contract_share` measures the fraction of deliveries made under a term contract. It does not measure
  the fraction of fuel the plant was obliged to take.
- **Scope of this point.** It is a property of the form, re-read here from SOCO's own corpus rather than transferred
  from MISO's verdict (rule 25).

### 2. SOCO's contracted tonnage moved with burn in the year the model misses

Fleet total, eight plants, Mt:

| year | contract (C/NC/T) | spot | implied burn (receipts − Δ stock) |
|---|---|---|---|
| 2019 | 28.87 | 3.70 | 29.51 |
| **2020** | **19.76** | 0.68 | **20.70** |
| 2021 | 16.85 | 5.95 | 25.93 |
| 2022 | 21.30 | 3.32 | 24.97 |
| 2023 | 23.29 | 1.28 | 19.89 |
| 2024 | 19.74 | 0.21 | 21.46 |

- **2019 → 2020.** Contracted deliveries fell by **9.1 Mt (−32 %)**, against a burn drop of 8.8 Mt.
- **By plant, 2019 → 2020:**

  | plant | contract Mt, 2019 → 2020 |
  |---|---|
  | Scherer | 9.05 → 3.97 (−56 %) |
  | Bowen | 3.37 → 2.51 |
  | Gaston | 1.26 → 0.59 |
  | Crist | 1.25 → 0.31 |

- **What a binding minimum take would look like.** Receipts would hold and stock would build.
- **What SOCO's record shows.** In 2020 contract tons ran at 0.74–1.04× burn at every plant but one: Bowen 0.74,
  Daniel 0.76, Gaston 0.94, Miller 1.02, Scherer 1.04. Contracted coal was avoided at the annual scale in exactly the
  year that fails C4.
- **Delta test** (year-on-year Δ contract tons vs Δ burn, 30 plant-years): r = 0.43. Contracted tonnage moves with
  burn rather than sitting fixed.
- **The one exception, recorded rather than smoothed over.** Barry's contract tons held flat (1.64 → 1.58 Mt) while
  its burn fell. Contract tons were 1.15× burn, and stock days rose from 123 to 238. This is one plant-year and fits a
  take held above burn. The form carries no quantity term that would let it be identified as an obligation rather
  than, say, a stocking decision.
- **Not read as take-or-pay.** The 2023 fleet stock build (contract 23.3 vs burn 19.9 Mt) follows the 2022
  rail-shortage stock drawdown. It is ambiguous, and it is not read either way.

### 3. Contract coal was not priced below spot

Delivered $/MMBtu, contract vs spot, wherever both exist in the same plant-year:

| plant-year | contract | spot |
|---|---|---|
| Bowen 2019 | 2.89 | 2.82 |
| Bowen 2020 | 2.86 | 2.86 |
| Bowen 2021 | 2.84 | 2.80 |
| Miller 2021 | 1.81 | 1.84 |
| Miller 2022 | 2.18 | 2.21 |

- **No sub-market cost to read.** The data offers no avoidable cost below the F923 average delivered price the model
  already uses.
- **Where the prices do diverge, they diverge both ways.**
  - Contract below spot: Barry 2019 (3.03 vs 3.48) and Daniel 2019 (2.89 vs 3.64).
  - Contract above spot: Gaston 2019 (4.20 vs 2.37).
  - Spot 2–5× contract in 2022–2024 (Bowen 2023: $16.59 vs $4.92). That is the post-2021 price spike, and it says
    contract fixed a price, not a quantity.
- **Why none of it helps.** The model's F923 average already blends both purchase types. A contract price is the
  avoidable cost of a contracted ton unless a minimum take makes the ton sunk, and §1–§2 find no such obligation.

### 4. Even an identified share could not reach the object

- **What the family can touch.** It acts through `campd_tranche_fuel_frac` on two bands only: `_mustrun` and
  `_committed`.
  - **`_mustrun`.** SOCO's default already treats it as 100 % sunk. `coal_takeorpay_from_data` can therefore only
    *raise* must-run bids (measured shares 0.31–1.0), which moves 2019 COAL_BIT the wrong way, or leave them unchanged.
  - **`_committed`** (`coal_bit_committed_takeorpay` / `_all` / `_regulated`; every SOCO coal plant is regulated). The
    discount prices the band at about VOM in all 8,760 h. That is the miso-96 no-window defect (rule 17
    `[R-FLOOR-WINDOW]`), and `_sunk_fixed` exists to remove it. It would also add energy to the soco-73 over-runs
    (Wansley 2021 +5.0 TWh, Barry 2022 +2.0 TWh).
- **What the object is.** soco-73 §5 names it: the **econ** tranches, offered at $33–49/MWh against a $26.40 median
  price in H2 2020. No field in this family touches `_econ*` (the docstring states it is full delivered cost by
  construction).
- **The only form that could reach it.** A tonnage floor or period budget set from contract deliveries. §2 shows that
  would be same-year burn (C/burn ≈ 1): a rule-13 answer key, the construction miso-103/127 already proved dead for
  that reason.

## Verdict and actions

- **Matrix, `coal_takeorpay_committed` (SOCO shard): U → G.** Refused ex ante under rules 13 / 14 / 21. No quantity
  obligation is observable, SOCO's contracted tons tracked burn in 2020, and the family's scope misses the econ-tranche
  object. No LP was built.
  - **What would reopen it:** a plant-grain contractual minimum-quantity source for Georgia Power / Alabama Power /
    Mississippi Power / Gulf Power, of the kind MISO's standing ask `docs/records/miso/miso-coal-contract-tonnage-data-ask-2026-07.md`
    describes. Georgia PSC fuel-case filings are the obvious lead to check. That is a data intake, not a solve.
- **Not greedied.** Task 1 says to stop if the split is not identifiable. The thinnest-row table was not produced
  because no field was admitted.
- **Levers still excluded:** offer bands (SOCO has no price reference), any adder / offset / haircut, and re-deriving
  F923 or CAMPD against the residual (rule 23).

## What remains open (for the next lane)

- **2019 C1 COAL_BIT −4.24 pp and 2020 C4 coal 0.304 stand, both unchanged.**
- **Still admissible from soco-73.** The cost-based-start re-amortization (sized at ≤ +0.19 TWh, closes neither row;
  owner's call).
- **One measured structure not yet scoped for SOCO's econ object:**
  - **The gap.** Coal econ tranches are priced at an average CAMPD heat rate. The cost of the marginal MWh above
    minimum load is the *incremental* heat rate, which for a coal boiler sits below the average.
  - **Registry status.** No ScenarioConfig field or matrix row covers it (grep `incremental_heat` finds nothing).
  - **Identifiability.** It is measurable from each plant's own CAMPD hourly heat input vs gross load, a
    rule-13-admissible physical input.
  - **Next step.** A zero-LP identification (per-plant heat-input-vs-load slope, 2019–2025, stability across years)
    is the next step. It must be scoped before any build. It is named here as a candidate, not as a result.

## Retrievability

No solve was run and nothing is promotable. There are no shards.
