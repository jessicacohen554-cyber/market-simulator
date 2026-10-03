# FINDING closeout-SOCO-3 phase 0 — the owner's take-or-pay coal hypothesis (R-45), zero LP

Lane `claude/closeout-soco-3`, 2026-10-03. Keeper `2026-10-03-closeout-soco-2-nuclear`
(`results/calibration/closeout_soco_2_span`) is the control and is unchanged. **No LP, no shard, no `src/` edit.**
Readings were fixed ex ante in `PRECOMMIT-phase0-closeout-soco-3-2026-10-03.md` (pushed at `085abe1b` before any
number was computed).

Probes (all zero LP, all reading committed files):
- `scripts/probes/_closeout_soco3_takeorpay_census.py` — C-A/C-B/C-C census → `census_plant_month.csv`, `census_plant_year.csv`
- `scripts/probes/_closeout_soco3_budget_reach.py`, `_closeout_soco3_c1_reach.py` — the owner's offer form at full magnitude → `budget_reach.csv`, `c1_reach.csv`
- `scripts/probes/_closeout_soco3_pile_reach.py [prior|all]` — the existing take-or-pay pile family on SOCO → `pile_reach_plant_year{,_smax_all}.csv`, `pile_c1_reach{,_smax_all}.csv`

## 0. Prior adjudication (rule 28): the owner's words alone are not new evidence

**Sequencing.** The desk's addendum asked for this section *before* the census. It reached the lane only after
steps 1–4 had been reported, so it is recorded here, ahead of the findings.

**What already closes take-or-pay for SOCO:**
- **The DO-NOT-REDO list.** `docs/mechanism-testing-matrix.md` §5.8 header: *"DO-NOT-REDO: take-or-pay, CT start,
  gas bridge, CC incremental HR, gas level."*
- **`coal_takeorpay_committed` G (soco-74, Page 5 corpus 2017–24).** *"Purchase Type C/NC is a >=1-yr price term
  with an expiration date; no minimum-quantity field exists, QUANTITY is ex-post delivery … contracted coal was
  AVOIDED in the C4-failing year … a contract-tonnage floor would be same-year burn (rule-13 answer key). Reopens
  only on a plant-grain contractual minimum-quantity source."*
- **`coal_fuel_inventory_take_floor` G (soco-80).** It refused the annual Y−1 contract-tons floor: *"the
  renewal-at-Y-1-volume premise is FALSE for SOCO"*.

**Is each part of the owner's hypothesis new?**

| Element of R-45 | New against the closure? |
|---|---|
| vertically integrated / cost-of-service ownership | **No.** soco-74 tested the `_regulated` variant; every SOCO coal plant is regulated |
| EIA-923 contract-type receipts as the measured basis | **No.** It is the same Page 5 corpus, still with no quantity term; §1 re-reads it monthly, adds 2025, and refutes again |
| a sunk-fuel energy budget rather than an offer haircut | **No**, against soco-74 §4 and soco-80. The contract-MMBtu budget (§3a) is the named answer key |

**What survives.** The price form and the annual floor stay closed; neither was re-tested by solve. The one live
object is the **untested** SOCO cell `coal_monthly_pile_measured_receipts` (U), sized in §3b.

**What arming it would involve.** The chain needs `coal_fuel_inventory_take_floor` (G) as a prerequisite. The
measured arm removes soco-80's Y−1 premise but **not** soco-74's objection that same-year contract tonnage ≈ burn.
Option 1 below therefore needs an explicit owner ruling that the same-year measured overlay (admitted for NWPP at
NEXT-9) answers that objection for SOCO. Options 2 and 3 are the choices consistent with DO-NOT-REDO.

## Verdict in one paragraph

**As asked ("price contracted coal as sunk"), the hypothesis is REFUTED on SOCO's own data.** Night coal shortfall
does not concentrate at high-contract plants (ρ = −0.09), contract deliveries fell below burn in most shortfall
plant-years, and the coal yards had room (median 0.67 of their maximum) so contracted coal could be stored and kept a
positive opportunity cost. A blanket sunk-fuel offer is a cliff, not a lever (CC 2019 +3.4 → −12.2 pp). **But the
owner's economics — "pay for the contracted coal whether you burn it or not" — already exists in the code as a
quantity mechanism, not a price**: NWPP's coal-yard family with same-year measured receipts
(`coal_monthly_pile_measured_receipts`, SOCO cell **U**). Its soft floor is a take-or-pay row whose shortfall is paid
at the yard's delivered coal price. Reproduced on SOCO at zero LP it reaches the CC_REGULAR 2019 bar at upper bound
(3.42 F → 1.61 P; full-history yard-size sensitivity 2.31 P) and COAL_BIT 2019 (−4.25 F → −2.26 P; sensitivity
−2.95 F), with no PASS→FAIL in CC / COAL_BIT / COAL_PRB in any year. This was found **after** the ex-ante REFUTE and is
a step-3 design reading, not a gate. Any solve needs its own PRECOMMIT.

## 1. Census (step 1) — the ex-ante reading is REFUTE

| Reading | Bar (ex ante) | Measured | Result |
|---|---|---|---|
| S1 ρ(night shortfall fraction, contract MMBtu share), plant-years with ≥ 100 GWh actual night energy | SUPPORT ≥ +0.5; REFUTE ≤ +0.2 | **−0.093** (n = 43, p = 0.55) | **REFUTE** |
| S1b share of positive night shortfall at contract-share ≥ 0.9 plants | ≥ 2/3 | 0.70 | passes, but uninformative: almost all SOCO coal is ≥ 0.9 contract |
| S2 median within-plant monthly corr(contract tons, burn tons), 2019–24 | SUPPORT ≤ 0.3; REFUTE ≥ 0.5 | **0.32** (Barry 0.39, Gaston 0.33, Crist 0.82, Bowen 0.23, Miller 0.10, Wansley −0.17, Daniel 0.31, Scherer 0.41) | in between |
| S2b contract tons / burn in shortfall plant-years | ≥ 1 | 0.5–0.95 in 30 of 38 | fails |
| S3 stock / plant max in shortfall plant-months | SUPPORT ≥ 0.85; REFUTE ≤ 0.7 | **median 0.665**, shortfall-weighted 0.68; 30 % of shortfall MWh at ≥ 0.85 | **REFUTE** |
| S4 minimum-take source | quantity term identifiable | none on disk; Page 5 carries price-term C/NC/S and expiry only (soco-74 §1, re-read) | fails |

Night = lowest two system-load deciles of each year (keeper P1 demand). Actual = CAMPD coal-unit gross × the plant's
EIA-923 coal net/gross. Contract horizon (tonnage-weighted months to expiry): 16.7 / 17.5 / 12.5 / 16.2 / 12.9 / 9.1 /
9.0 for 2019–2025. Contract vs spot $/MMBtu: equal where both exist (Bowen 2019–21, Miller 2021–23); spot 2–5× contract
in 2022–23. Contract coal is a **price term**, as soco-74 found.

**What the census does show.** SOCO's coal deficit is plant-grain and runs across all hours, not just nights. 2019
model vs actual TWh:

| Plant | Model | Actual |
|---|---|---|
| Barry 3 | 0.07 | 4.18 |
| Crist 641 | 0.69 | 2.57 |
| Wansley 6052 | 0.13 | 1.81 |
| Gaston 26 | 1.59 | 2.79 |
| Bowen 703 | 8.80 | 10.96 |
| Miller 6002 | 18.96 | 18.24 |
| Scherer 6257 | 12.38 | 12.07 |

The deficit is the cyclers. Their econ tranches are offered at $36–37/MWh, against a 2019 median price of $30.9 and a
night median of $24.4. Their committed tranches carry the $60–137 start markup (soco-73).

## 2. What already floors or prices SOCO coal (step 2, rule 19 D-2)

From the keeper's `run_config_2019.json`:

| Mechanism | State | Scope |
|---|---|---|
| `coal_mustrun_per_plant` + `coal_mustrun_requires_measured_row` (soco-69, K) | on | $4.50/MWh must-run slabs at measured-row plants only: Bowen, Miller, Scherer, Daniel, Gaston |
| `coal_warm_committed` (SOCO-58) | on | committed tranches; the start markup still lands on cyclers with no must-run (Barry, Crist, Wansley) |
| `coal_econ_marginal_hr_two_sided` (soco-81, K) | on | committed + econ at CEMS incremental heat rate on the 5 must-run plants; cyclers at average |
| `coal_plant_monthly_pricing`, `coal_supply_repricing` | on | F923 plant-month delivered coal price |
| `coal_prb_passthrough_sigmoid` (tiered) | on | PRB plants' coal price vs gas |
| `offer_curve_by_group` coal bands | 1.0 | channel closed for SOCO (gate G5) |
| outage windows (`campd_dark_unit_year_windows`, short windows, per-unit) | on | availability |
| `coal_takeorpay_from_data`, `coal_bit_committed_takeorpay`, `coal_committed_takeorpay_{all,regulated,sunk_fixed}` | off | per-hour take-or-pay discounts — `coal_takeorpay_committed` **G** (soco-74) |
| `coal_fuel_inventory` → `_plant_grain` → `_take_floor` → `_monthly_pile` → `coal_monthly_pile_measured_receipts` | off | yard ceiling + take floor — cells U / U / **G** (soco-80) / U / U |
| `tranche_startup_amortization` | off | G (soco-73/77/92) |

The candidate below **replaces nothing and stacks on nothing**:
- `resolve_coal_take_floor` raises if any per-hour take-or-pay discount is armed (owner ruling Q5).
- `reconcile_floors_to_yard_budget` scales must-run floors that would draw more coal than the yard holds.
- On the floor side, the yard floor and the must-run slab overlap only at Gaston (2019 +0.43–0.83 TWh). The floor
  adds nothing over the keeper at Bowen, Miller, Scherer or Daniel in 2019.

## 3. Design (step 3)

### 3a. The owner's form, sized: refused

`_closeout_soco3_c1_reach.py` re-scores C1 with `score_fuelmix`. Added coal displaces CC_REGULAR one-for-one.

| Form | 2019 CC_REGULAR | 2019 COAL_BIT | Other years |
|---|---|---|---|
| keeper | +3.42 F | −4.25 F | — |
| blanket sunk-fuel offer (all available coal at VOM) | **−12.18 F** | +5.77 F | CC fails 2020–24; COAL_PRB fails 2019/20/21/23/24 |
| contract-MMBtu energy budget at VOM | −1.62 F (volume) | −0.89 P | passes, **but** the budget is converted at same-year generation and contract ≈ burn: the rule-13 answer key soco-74 §4 named; 31 plant-months forced > 1.1 × actual in 2019 |

Neither form is admissible.

### 3b. The candidate: the existing take-or-pay pile with same-year measured receipts

The field identity is from `data/coal_fuel_inventory.py::build_coal_monthly_pile`, verified in code. With the
measured arm, the same-year contract lots **replace** the Y−1 tonnage that soco-80 refused. For month-end m of year Y:

```
max(0, (S_dec − S_max)·hc + cumContract_Y(m))  ≤  cumulative coal burn (+ shortfall)  ≤  S_dec·hc + cumReceipts_Y(m)
```

Where:
- S_dec = Dec(Y−1) stock;
- S_max = max month-end stock through Y−1;
- hc = Y−1 heat content.

The floor is **soft**: each yard row carries a shortfall column priced at the yard's own delivered coal cost. In an LP
that is exactly take-or-pay. The contracted coal is paid for whether burned or not, so burning it costs only VOM up to
the floor. The **price** form (§1) asked whether coal is sunk at the hourly margin, and S3 says no. The **quantity**
form says something narrower: a year's contract deliveries cannot all be stockpiled. It binds once cumulative
contract receipts exceed the January headroom.

**Zero-LP reach on the keeper** (`_closeout_soco3_pile_reach.py`). Upper bound: hard floor, no capacity clip, and the
net change displaces CC one-for-one. Field construction (S_max through Y−1; the stock corpus starts in 2018):

| Year | Added (TWh) | Cut (TWh) | Net | Floor > actual (TWh) | Ceiling < actual (TWh) | CC_REGULAR pp | COAL_BIT pp | COAL_PRB pp |
|---|---|---|---|---|---|---|---|---|
| 2019 | 5.39 (Barry 2.98, Crist 1.58, Gaston 0.83) | 0.94 (Hammond 0.49, Miller 0.44) | +4.45 | 0.00 | 0.07 | 3.42 F → **1.61 P** | −4.25 F → **−2.26 P** | 0.88 → 0.70 P |
| 2020 | 5.35 | 0.12 | +5.22 | **1.55** (Scherer 0.78, Miller 0.42, Bowen 0.28) | 0.17 | 2.29 → 0.04 P | −2.47 → −0.92 P | 0.01 → 0.71 P |
| 2021 | 1.69 | 0.29 | +1.40 | 0.31 | 0.64 | 2.74 → 2.15 P | −1.98 → −1.27 P | 0.87 → 0.75 P |
| 2022 | 0.00 | 6.58 (Scherer 3.21, Daniel 1.20, Gaston 1.10, Barry 0.81) | −6.58 | 0.00 | 0.80 | −0.82 → 1.86 P | 0.92 → 0.03 P | 2.70 → 0.91 P |
| 2023 | 1.62 | 0.00 | +1.62 | 0.00 | 0.00 | 2.55 → 1.88 P | −2.07 → −1.45 P | −0.54 → −0.49 P |
| 2024 | 2.11 | 0.00 | +2.11 | 0.03 | 0.00 | 2.49 → 1.65 P | −1.46 → −1.19 P | −1.17 → −0.60 P |
| 2025 | 0.20 | 2.08 (Barry) | −1.87 | 0.00 | 0.00 | 0.26 → 1.00 (SKIPPED, preliminary 923) | −0.18 → −0.92 P | 1.32 P |

**Sensitivity: full-history yard size** (S_max = max over 2018–2024, reading the future; it stands in for the
missing 2015–2017 stocks):
- 2019 net +2.74 TWh. CC 2.31 **P**; COAL_BIT −2.95 **F** (0.05 pp short).
- 2020 net +2.06. The floor exceeds actual in **no** plant-year of any year.
- Every other year is within ±0.1 pp of the table above.

What the CC 2019 bar needs:
- **CC displaced.** It clears with 1.03 TWh of CC displaced, i.e. **23 %** of the added coal (field construction) or
  **38 %** (full history).
- **Where the added coal lands.** It sits at the cyclers. In SOCO the price-setter is CC in most non-peak hours
  (closeout-SOCO-2 §b), so a majority CC share is the expected case. One-for-one is still an upper bound.

**Other criteria: direction only, not sized.**
- **C3a, 2019/2020.** Keeper `score_price_mean` reads +10.9 / +11.0 % against Southern's λ, both FAIL by under
  1 pp. Added coal lowers prices, so these move toward pass.
- **C3a, 2022.** It reads −14.8 % (FAIL). The ceiling cut raises 2022 prices, again toward pass.
- **C3a, 2021 / 2023 / 2024.** They read −5.8 / +1.0 / −4.8 % (all PASS). Added coal moves them down; 2021 and 2024
  are the ones to watch.
- **C4 coal hourly shape.** This is the named risk, and it is NWPP-NEXT-9's rejection mode: a perfect-foresight LP
  places forced coal in the dearest hours of each month. SOCO 2020 C4 coal NRMSE is 0.285, thin against 0.30. Real
  Barry ran nearly flat: 17 % of its energy in 20 % of the hours (the night deciles).
- **Rule 20 forced budget.** In 2019 about 5.4 of 16.7 TWh of model COAL_BIT would sit at the floor (≈ 32 % > 30 %).
  It passes only conditionally, via D-4: the floor must bind only in months after cumulative contract receipts exceed
  the January headroom, which is its declared window.

### 3c. Data contract, gates, forward story, cells, cost

- **Data.** No new datatype. `coal-receipts` (Page 5, 2017–2025) and `coal-stocks` (Page 2, 2018–2024) are already
  curated and national, read through `build_coal_plant_budget` / `build_coal_measured_receipts`.
- **One gap: stocks start in 2018.** S_max for 2019 is therefore one year deep, which is why 2019's floor is the
  tightest. Intaking EIA-923 Page 2 for 2015–2017 (free bulk workbook, same route as the README; data-intake skill)
  gives 2019 the multi-year yard history later years have.
- **2025 has receipts but no Page 2 stocks.** The 2025 leg reads Dec-2024 stock, which is on disk.
- **`src`/`scripts` change (Opus).** Admit SOCO to `COAL_PLANT_GRAIN_ISOS`, `COAL_TAKE_FLOOR_ISOS` and the
  `coal_fuel_inventory` ISO gate (rule 25: SOCO's own census, this FINDING). Check that every SOCO yard gets a
  `floor_parts` entry when its Y−1 contract tonnage is zero (Wansley 2019). No new `ScenarioConfig` field, so no new
  matrix row.
- **Forward story.** Backcast-only, like R-3 and NWPP-NEXT-9; the forecast never reads it. The forward analogue is the
  contract delivery rate. Page-5 expiry dates give a 9–17-month contracted horizon, so a forecast year past that reads
  the rate, not a schedule.
- **D-4 window.** The months in which cumulative contract receipts exceed (S_max − S_dec)·hc.
- **Cells touched (SOCO shard):**
  - `coal_monthly_pile_measured_receipts` U (the lever);
  - `coal_fuel_inventory_monthly_pile` U and `coal_fuel_inventory_plant_grain` U (prerequisites);
  - `coal_fuel_inventory` U (the ceiling half);
  - `coal_fuel_inventory_take_floor` **G**.
- **Why the take_floor G needs new evidence, and what it is.** soco-80 refused the *annual Y−1* floor because the
  renewal premise was false (2020 floor 9.90 TWh above actual). The measured arm removes that premise. On SOCO the
  same-year floor sits 1.55 TWh above actual in 2020 under the field's S_max, and 0 under full history.
  `coal_takeorpay_committed` stays **G** and is not reopened: the per-hour price form is refuted again here.
- **LP cost.** 7 year-isolated shards. Phase 1 is zero LP and comes first: the 2015–2017 stock intake, then this
  probe re-run on it.

## 4. Owner card (sent to the desk)

**SOCO coal: is take-or-pay the fix for the last FAIL (CC_REGULAR 2019)?**

1. **(Recommended, if the owner rules that the same-year measured overlay answers soco-74's answer-key objection;
   see §0) Charter the existing take-or-pay pile for SOCO, data first.** Intake the free EIA-923 coal stocks
   for 2015–2017, then re-run this zero-LP reach with the bars pre-registered:
   - CC 2019 clears at ≤ 50 % CC displacement;
   - no plant-year floor above actual burn by > 0.5 TWh;
   - no C1 PASS→FAIL.

   If those clear: lift the SOCO gates and solve 7 shards with a C4-coal kill gate (2020 ≤ 0.30). It is NWPP's
   mechanism, unchanged, with zero fitted parameters.
2. **Refute and keep the ledger.** The contract-price form is refuted (contract share does not explain the shortfall;
   the yards had room). CC 2019 stays the mirror of the ledgered 2019 coal self-commitment, and SOCO stays NOT-YET.
3. **Data-limited until a minimum-take source exists.** Pull Georgia PSC / Alabama PSC fuel testimony (plan §3.8
   row 4) before any floor. A same-year delivery is not a contractual obligation.
4. **Do it as asked: price contracted coal at VOM.** Not recommended. It is a cliff: CC 2019 +3.4 → −12.2 pp, and
   COAL_PRB fails in five years.

## Retrievability

No solve and nothing to promote. The keeper is unchanged; the CSVs and probes in this lane are the whole record.
