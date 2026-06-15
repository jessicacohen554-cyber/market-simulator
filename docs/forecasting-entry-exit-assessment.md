# Is this model fit to forecast ERCOT retirements and new entry?

> **Update 2026-06-15 — partial fix implemented (see `docs/ordc-overlay.md`).**
> Two of the gaps below are now addressed: (1) a **reliability-deployment
> overlay** (`ordc_reliability_deployment_mw`, the RTORDPA analogue) restores
> stress-year scarcity — at the recommended 2,500 MW the 2023 monthly LMP MAE
> drops 32.5 → 12.3 and 2023 scarcity rent for the tail rises ~10× (CT_PEAKER
> net 12 → 109 $/kW-yr, ST_GAS 21 → 127, COAL_PRB 22 → 143), dispatch
> byte-identical; (2) **legacy gas steam (`gas_st`) is now in the retirement
> screen** (it was absent → immortal). Still open: AS *revenue* (below), the
> entry-side fixes (CONE hurdle, `gas_ct`/storage candidates, price-duration
> expected revenue), and the build-side reserve-margin constraint. The verdict
> table below is unchanged in structure but the peaker/steam-gas *retirement*
> calls are now materially better in stress years.



**Question.** The ERCOT energy-only LP backcast (keeper
`results/calibration/run115b_ccduct_prb73_relief06`) reproduces dispatch
volumes well but is materially off on prices, and badly off on the scarcity
tail. Retirement and new-build decisions hinge on **net revenue** (energy
margin + AS + scarcity rents) versus going-forward fixed cost (exit) or
annualized CONE (entry). Can a model that nails MWh but misses the spike tail
legitimately drive entry/exit forecasts?

**Verdict (one line).** **No — not as it stands for the technologies whose
entry/exit actually turns on net revenue (peakers, storage, and any new build
screened against CONE).** It *is* defensible for the *relative ranking* of the
dispatchable fleet and for the retire/keep verdict on clearly-inframarginal
baseload (nuclear, efficient CC, most coal). The decisive
annual-scarcity-rent reconciliation **fails**: the overlay does not put "the
right total money in the wrong hours" — for peakers and storage it puts in
**~1–6 % of the right total money**. The fix is not better hourly prices; it
is a deliberately *calibrated annual* scarcity + AS rent and a reserve-margin
constraint, which is how the field actually does this (§4, §5).

Every model number below is reproduced from the keeper with
`scripts/derive_ordc_overlay.py … --revenue-report` (gross energy revenue) and
a net-margin reconstruction that applies the *exact* retirement-screen cost
basis — `assemble_mc(fleet_arrays, resolve_fuel_prices(...), …)`, the same
`mc_cost` the runner hands to `capacity.apply_economic_retirements`
(`runner.py:402`, `capacity.py:226`). External figures are cited inline.

---

## 1. Net-revenue decomposition per technology (the keeper's own numbers)

The retirement/entry screens do **not** work on gross energy revenue; they work
on **net inframarginal margin** `Σ_t (price[z,t] + adder[t] − mc[g,t]) ·
dispatch[g,t]` (`capacity.py:317-327`). So the decision-relevant decomposition
is *net* margin, split into the base energy margin (energy-only LP duals) and
the ORDC scarcity-adder rent. Per class, with installed capacity from the
solved fleet (`fleet_arrays.pmax`):

### Net revenue, $/kW-yr (energy margin + scarcity rent)

| class | cap GW | CF % | 2023 base | 2023 scar | 2023 **net** | 2024 **net** | 2025 **net** |
|---|--:|--:|--:|--:|--:|--:|--:|
| nuclear     | 5.0  | 88–95 | 160.9 | 14.2 | **175.0** | 130.0 | 241.2 |
| CC_REGULAR  | 33.1 | 48–52 | 31.1  | 11.6 | **42.7**  | 28.5  | 43.2 |
| CC_CHP      | 6.4  | 57–61 | 29.4  | 11.6 | **40.9**  | 28.7  | 41.1 |
| COAL_PRB    | 11.4 | 39–47 | 9.7   | 12.1 | **21.7**  | −1.4  | 42.9 |
| ST_GAS      | 12.3 | 14–17 | 10.6  | 10.5 | **21.1**  | 8.2   | 11.9 |
| COAL_LIGNITE| 2.6  | 58–73 | −20.5 | 12.6 | **−7.9**  | −28.3 | 29.5 |
| **CT_PEAKER** | 8.5 | 7–8 | **2.3** | **10.1** | **12.3** | **1.7** | **0.8** |
| CT_CHP      | 1.3  | 56–58 | −8.6  | 11.4 | **2.8**   | −5.3  | −12.2 |
| **STORAGE** | 4.0+ | — | 2.5 (arb) | 7.6 | **10.1** | 3.2 | 7.6 |

(Storage net = energy arbitrage `disch·p − chg·p` plus scarcity on discharge,
from `storage.parquet`; capacity ~4/5.5/8 GW across 2023–25.)

### What fraction of each technology's margin is the scarcity tail?

- **CT_PEAKER: 82 % of 2023 net revenue is scarcity rent** (10.1 of 12.3
  $/kW-yr); 54 % in 2024; 0 % in 2025.
- **STORAGE: 75 % of 2023 net** is the scarcity adder; the energy-arbitrage
  spread alone is only ~$2.5/kW-yr.
- **The inframarginal classes are the mirror image.** Nuclear's scarcity
  share is 8 % (2023) and <1 % (2024–25); CC_REGULAR 27 %/2 %/0 %. Their
  margin lives in the *body* of the dispatch stack, not the tail.

This confirms the brief's smoking gun and sharpens it: the technologies whose
entry/exit you care about (CT, storage) earn the **majority** of their thin
margin in exactly the few hundred hours the model gets wrong, while the units
whose margin the model captures well (baseload) are the ones whose retire/keep
status is never in doubt anyway.

> **A second, quieter problem the net basis exposes:** the going-forward FOM
> thresholds the retirement screen compares against are **far below reality** —
> `fixed_om_gas_ct 8`, `fixed_om_gas_cc 12`, `fixed_om_coal 40×1.3 = 52`
> $/kW-yr (`scenarios.py`), versus NREL ATB-class values of roughly
> $21 / $30 / $45. So the model has **two compensating errors**: it understates
> peaker revenue *and* understates the bar that revenue must clear. They do not
> net out (§3), but they mean the model is not "conservative" in any clean
> direction — it is wrong on both sides of the inequality.

---

## 2. Level vs shape: which does the model preserve?

**Shape (relative ranking): preserved.** Ranking the dispatchable fleet by
net $/kW-yr gives, every year, nuclear ≫ efficient CC ≈ CC_CHP > PRB coal >
ST_GAS > CT_PEAKER, with lignite and CT_CHP at/below break-even. That is the
correct ERCOT merit-order-by-profitability and it is stable across 2023–25. A
retirement *screen* that only needs "rank the fleet and cut from the bottom"
gets a sensible ordering.

**Level (absolute net revenue): not preserved, and the error is
technology-correlated.** The price miss is not confined to the >$200 tail. The
2023 monthly demand-weighted LMP MAE is **$32.5/MWh energy-only, $30.1 with the
overlay** (`--revenue-report`), spread across summer hours — so the model
shaves inframarginal margins broadly *and* misses the tail entirely. The
understatement therefore grows monotonically with a unit's tail-dependence:
small for baseload, ~5× for mid-merit CC (§3), and 1–2 orders of magnitude for
peakers/storage.

**Consequence.** Retirement screening that needs only *ranking + a fixed
threshold* is partly salvageable; **new-build screening, which needs absolute
net revenue vs CONE, is not** — the level is the whole question there and the
level is wrong.

---

## 3. The decisive test: does the ANNUAL scarcity rent reconcile?

The crux hypothesis was: even if hourly placement is wrong, maybe the overlay
injects approximately the *right annual total* scarcity rent per technology. If
so, the model could support entry/exit on an annual basis despite bad hourly
prices. **It does not.** Measured against the canonical published benchmark —
the ERCOT IMM/Potomac Economics **Peaker Net Margin (PNM)**, which is by
construction the annual net revenue a hypothetical new gas peaker earns in the
**real-time energy market** (the cleanest possible comparator to the model's
energy margin + scarcity adder, since both are energy-only and exclude AS):

### CT_PEAKER — model energy+scarcity net vs ERCOT PNM ($/kW-yr)

| year | model | ERCOT PNM (actual) | model as % of actual |
|---|--:|--:|--:|
| 2023 | 12.3 | **197** | **6 %** |
| 2024 | 1.7  | **~100** | **2 %** |
| 2025 | 0.8  | lower (mild yr; no SOM yet) | ~1 % |

PNM history: 2021 ≈ $760/kW-yr (Uri), 2022 $167, 2023 **$197**, 2024 **~$100**;
administrative CONE/PNM threshold **$105/kW-yr** (Brattle's 2024 ERCOT study
updates the Frame-CT reference CONE to **$162/kW-yr**, Aero CT $280–293).

### STORAGE — model net vs IMM realized battery revenue ($/kW-yr)

| year | model (energy+scarcity, no AS) | actual ERCOT battery (incl AS) | model % |
|---|--:|--:|--:|
| 2023 | 10.1 | **$193** | 5 % |
| 2024 | 3.2  | **$56**  | 6 % |
| 2025 | 7.6  | **~$29** | 26 % |

The reconciliation fails decisively for both tail-dependent technologies. Three
findings fall out of it:

1. **The overlay's annual rent is itself a ~10× under-count, not just
   mis-placed.** It credits CT_PEAKER $10.1/kW-yr of scarcity in 2023 but
   recovers only **17 of 181** actual >$200 hours and **7 of 104** >$500 hours
   (`--revenue-report`). The "right money, wrong hours" defense requires the
   *total* to be right; here the total is ~6 % of PNM.
2. **2025 is the clincher.** The overlay credits **$0** scarcity to every class
   in 2025, yet 2025 still had 31 actual >$200 hours. Any spike-dependent
   unit's 2025 scarcity component is entirely missing.
3. **AS revenue — unmodeled — is the larger half of the miss for storage and a
   material slice for CTs.** The model has **zero** AS *revenue* in the
   capacity economics: `apply_economic_retirements` net revenue = energy
   margin + EAC/RPS attribute + capacity payment (0 for energy-only ERCOT) —
   there is no AS term (`capacity.py`). AS-*aware* volume/cost layers do exist
   (the `--ct-deployment` out-of-merit floor captures the AS/RUC-deployment
   effect on CT *volumes*; `battery_dispatch_adder` folds in the AS
   opportunity cost) — but no AS market *revenue* is credited to any unit.
   ERCOT batteries earned the *majority* of 2023–24 revenue from
   RRS/ECRS/Reg/non-spin, not energy. So even a perfectly calibrated energy
   scarcity rent would leave storage and peaker revenue badly short.

**Even the inframarginal level is low.** The IMM reports 2024 CT *and* CC
market revenue at **20–25 % below CONE**; with CC reference CONE ~$210/kW-yr
that implies real CC net revenue ~$160/kW-yr, versus the model's CC_REGULAR
**$28/kW-yr** in 2024 — a ~5–6× gap (part is new-vs-existing-fleet and AS, but
the shaved summer LMP is the bulk). The model understates net revenue *across
the board*; it is merely least wrong for baseload.

---

## 4. Is decoupling dispatch accuracy from revenue accuracy normal?

**Yes — it is the textbook "missing money" problem of energy-only markets, and
the standard practice is precisely to NOT trust an LP's hourly duals for
revenue.** How practitioners actually forecast entry/exit:

- **Capacity-expansion models (NREL ReEDS, EIA NEMS/EMM).** These do *not*
  derive adequacy from hourly scarcity prices. They impose a **planning
  reserve-margin constraint** and assign each resource a **firm-capacity credit
  / ELCC**; new entry is priced against **full annualized cost**, and the
  "missing money" is supplied by the reserve-margin constraint's shadow price,
  not by getting the price tail right. Adequacy is *structural*, not
  price-formation-dependent.
- **Production-cost models (PLEXOS, Aurora).** When used for revenue, operators
  add an explicit **ORDC/scarcity adder and AS co-optimization**, and routinely
  **calibrate annual scarcity rents to historicals** — they treat raw LP duals
  as a known under-count of the tail, exactly the failure documented here.
- **ERCOT's own adequacy process is the CDR** — a reserve-margin accounting,
  not a price/revenue model. The PNM is a *monitoring* metric, not the
  adequacy mechanism.

So the model's instinct — own the volumes with the LP, own the price tail with
a post-solve overlay (`docs/ordc-overlay.md`) — is the *right architecture*.
The problem is execution: the overlay is honestly anchored to defensible ORDC
parameters and therefore recovers only ~7–12 % of the 2023 summer scarcity gap
(the rest is documented as RTORDPA/ECRS deployment pricing and the unverified
σ — `docs/ordc-overlay.md` §Validation), AS is absent, and the only thing
standing between the under-counted revenue and mass over-retirement is the
**15 % reliability floor** in `apply_economic_retirements` — which makes
retirements *reliability-driven, not economic*, defeating the purpose of an
economic signal. Using raw LP duals (no overlay) for ERCOT capacity economics
is a known, documented over-retirement bias (`runner.py:529-569`,
`docs/ordc-overlay.md` §Forecast-mode revenue wiring).

---

## 5. Verdict and what it would take to make it fit

### Fitness, stated plainly

| Use case | Fit? | Why |
|---|---|---|
| **Retire/keep — baseload (nuclear, efficient CC, most coal)** | **Yes** | Net revenue dominated by base energy margin the model captures; clears the (low) going-forward bar by a wide margin in both model and reality. Verdict robust even though level is understated. |
| **Retire/keep — peakers, storage, marginal steamers** | **No** | Net revenue is 1–2 orders of magnitude understated; model says "retire" where PNM ($100–197/kW) says "comfortably solvent." **Systematic over-retirement bias.** |
| **New build — vs CONE, any technology** | **No** | Absolute net revenue understated ~5× (CC) to ~16–50× (CT); peakers (`gas_ct`) and storage handled weakly or absent as entry candidates; expected revenue uses flat CF × *mean* price, ignoring the price shape that defines peaker/storage value. **Systematic under-build.** |
| **Relative ranking of the dispatchable fleet** | **Yes** | Merit-order-by-profitability is correct and stable across years. |

### Concrete next steps to make it fit (in priority order)

1. **Calibrate the *annual* scarcity rent per class to a published anchor.**
   Scale the overlay so each technology's annual $/kW-yr matches the historical
   PNM (CT), IMM net-revenue figures (CC/steam), and the battery-revenue
   benchmark (storage) — distributed across the top price hours. This converts
   the overlay from "honest but ~10× short" to "deliberately calibrated total,
   acknowledged wrong hours," which is what production-cost practice does. The
   plumbing exists (`scarcity_prices`, `econ_prices = prices + adder`); it needs
   an annual-rent calibration target, not just defensible ORDC parameters.
2. **Add an AS-revenue module** (Reg-Up/Down, RRS, ECRS, non-spin). Today it is
   exactly zero and it is the *majority* of real battery income and a material
   slice of CT income. Without it, storage/peaker net revenue cannot reconcile
   no matter how good the energy price is.
3. **Add a per-technology CONE benchmark** as the new-entry hurdle (Brattle
   ERCOT: Frame CT $162, Aero $280–293, CC ~$210/kW-yr), and **add `gas_ct` and
   storage as first-class new-entry candidates** — `_NEW_ENTRY_TECHS` is only
   {wind, solar, gas_cc, nuclear_smr}, so the model literally cannot forecast
   new simple-cycle peaker entry. Replace flat-CF × mean-price expected revenue
   (`estimate_expected_revenue`) with a price-duration-curve dot product so
   tail value is counted.
4. **Impose a planning-reserve-margin constraint on the expansion loop** (the
   ReEDS/NEMS/CDR approach). This is the robust adequacy backstop that does
   *not* depend on getting hourly scarcity prices exactly right, and it lets
   retirements be screened economically without the 15 % floor doing all the
   work.
5. **Use realistic going-forward FOM** ($/kW-yr ≈ CT 21, CC 30, coal 45) so the
   exit threshold is honest rather than accidentally offsetting the revenue
   under-count.

### The loop, once those exist

```
solve dispatch (LP — volumes, validated)
  → net revenue per unit = energy margin (duals)
                         + CALIBRATED annual scarcity rent   (new: anchored to PNM/IMM)
                         + AS revenue                         (new: module)
  → retire if net revenue < going-forward FOM for N years    (realistic FOM)
  → build  if net revenue > annualized CONE                  (new: CONE + gas_ct/storage candidates)
  → subject to planning-reserve-margin constraint            (new: adequacy backstop)
  → re-solve next year
```

**Bottom line.** The model is a validated *volumes/emissions* engine with a
*structurally correct but quantitatively under-calibrated* revenue overlay and
no AS. For ERCOT entry/exit it is usable today only for baseload retire/keep
calls and relative ranking. Driving peaker/storage retirement or any new-build
forecast off it would systematically over-predict retirements and under-predict
entry for exactly the marginal, tail-dependent resources the analysis is meant
to be about — until the annual scarcity rent and AS revenue are calibrated to
the published net-revenue benchmarks above.

---

### Sources

Model: keeper `results/calibration/run115b_ccduct_prb73_relief06`;
`scripts/derive_ordc_overlay.py --revenue-report`; `src/market_sim/model/capacity.py`,
`src/market_sim/runner.py`, `src/market_sim/data/fleet.py`,
`src/market_sim/config/{scenarios,constants}.py`; `docs/ordc-overlay.md`,
`docs/calibration-best-so-far.md`.

External (accessed 2026-06-15):
- ERCOT IMM / Potomac Economics, 2023 & 2024 State of the Market Reports
  (PNM $197k/2023, ~$100k/2024; CONE $105k; CT/CC 20–25 % below CONE in 2024;
  battery $192–193/kW in 2023): potomaceconomics.com; ercot.com IMM postings;
  energychoicematters.com (2023-05-30).
- Brattle Group, *ERCOT CONE for 2026* (2024): Frame CT $162/kW-yr, Aero CT
  $280–293/kW-yr — brattle.com.
- Modo Energy, ERCOT battery revenue benchmarks (2024 $56/kW; 2025 ~$29/kW;
  AS revenue −90 % YoY) — modoenergy.com; pv-magazine-usa.com (2025-11-21).
- NREL ATB 2024 (FOM / cost references) — already cited in `constants.py`.
</content>
</invoke>
