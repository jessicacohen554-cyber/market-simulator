# FINDING — miso-285 phase 0: the MISO night overshoot is price formation at matched quantities. No admissible structural lever closes it. No solve earned.

```
LANE    : miso-285 (queue item 3 after the miso-283/284 owner rulings)
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), unchanged
LP      : none. Keeper committed P1 hourly sidecars, measured ILLINOIS/MINN hub RT, EIA-930, CAMPD,
          and fleet-only rebuilds (P0 offer stack), 2019-2025
PROBES  : scripts/probes/_miso285_night_supply_identity.py   price, EIA-930 fuel mix, bands, reserve duals
          scripts/probes/_miso285_night_class_census.py      night MW by class, model vs CAMPD
          scripts/probes/_miso285_night_stack.py             P0 stack clear at model Q + counterfactuals
OUTPUTS : results/calibration/_miso285_{night_supply_identity,night_class_census,night_stack}.json
CELL    : diurnal_price_amplitude stays G (raised, not re-opened)
```

## 1. Answer

At night (h0–5), the model dispatches about the **same MW by class as CAMPD** but clears **$4–10/MWh
higher** (median). The overshoot is a **level shift of the whole night distribution**, not a missing
negative tail. It sits in the **base (P0) offer stack**, and the stack puts 12–18 GW of flexible supply
between the hub price and the model price. None of the four candidate causes is a structural,
rule-13-admissible lever that closes more than about half of the gap.

| candidate | verdict | evidence |
|---|---|---|
| Reserve holding | **No** | Every reserve-family dual is $0.00 at night, every year |
| P1 startup markup | **No** (5 of 7 years) | The P0 stack cleared at the model's own night Q reproduces P1 to ±$0.3 median. 2022 (+$5.1) and 2025 (+$1.9) carry a P1 residual |
| Seam / interchange | **Not the level** | Model West = Illinois exactly at night (fully coupled). The hub West–IL spread is small except in 2022 (routed C3a) |
| Commitment floors forcing a dearer marginal | **No** | Coal sits at must-run + committed and its econ is backed down. CC econ tranches set the price |
| Offer level at the margin | **Yes: this is the object** | CC_REGULAR gap tranches sit at measured HR × delivered gas + VOM with zero markup (`rest` ≈ +0.07). Real night LMP is below that cost |

## 2. Night price, model vs hub (MISO-Illinois vs ILLINOIS.HUB RT, h0–5, $/MWh)

| year | mean m / h | median m / h | p10 m / h | share < $5 m / h |
|---|---|---|---|---|
| 2019 | 24.2 / 19.0 | 23.7 / 18.9 | 20.9 / 13.9 | 0.000 / 0.015 |
| 2020 | 20.5 / 15.5 | 19.9 / 15.8 | 17.4 / 8.9 | 0.000 / 0.059 |
| 2021 | 31.1 / 28.6 | 29.5 / 23.4 | 25.0 / 17.0 | 0.000 / 0.020 |
| 2022 | 50.6 / 43.0 | 48.1 / 42.7 | 38.2 / 18.6 | 0.000 / 0.043 |
| 2023 | 27.4 / 20.4 | 27.1 / 19.4 | 21.6 / 12.0 | 0.000 / 0.029 |
| 2024 | 25.2 / 17.9 | 23.8 / 17.3 | 19.0 / 8.2 | 0.000 / 0.056 |
| 2025 | 35.8 / 26.9 | 34.7 / 24.2 | 27.5 / 16.2 | 0.000 / 0.031 |

The median is off by +4.1 to +10.5, and the distribution is also too narrow (the model's p10 is only ~$3
below its median; the hub's is $5–24). Against MINN.HUB the model West is the same number, because the
footprint is coupled at night.

## 3. Quantities match; the price does not (night MW, model − CAMPD)

| year | coal | CC_REGULAR | CHP (3 classes) | ST_GAS | OTHER |
|---|---:|---:|---:|---:|---:|
| 2019 | +778 | +501 | −3,030 | −936 | +1,355 |
| 2020 | +1,572 | +227 | −2,915 | −848 | +683 |
| 2021 | −683 | −252 | −2,379 | −617 | +1,413 |
| 2022 | +213 | +177 | −2,658 | −461 | +1,392 |
| 2023 | −156 | −445 | −2,799 | +239 | +1,146 |
| 2024 | +153 | +530 | −2,875 | −636 | +915 |
| 2025 | −1,007 | +1,361 | −2,288 | −580 | +666 |

- Coal and CC_REGULAR are within about ±1 GW of CAMPD in most years. That is under 5 % of each.
- The CHP gap is flat day and night. It is the known basis dispute (the bench carries the host-steam
  add-back, miso-116), so it is not read as a level.
- OTHER is the C1 re-bucketing of mixed plants (Ninemile 1403).
- The EIA-930 comparison shows model coal +1.7 to +3.7 GW. That is a net-vs-CAMPD basis gap (930 coal
  sits ~2.6 GW below CAMPD in 2023). CAMPD is the C1 basis and is what the table uses.

So the real system runs about the model's night dispatch and clears it lower. The overshoot is **price
formation**, not merit or quantity.

## 4. The stack (P0 offers, fleet-only rebuild, night medians, $/MWh)

| year | hub | P1 | P0 stack at model Q | CF1 | CF2 | CF3 | GW in gap | GW within ±$2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2019 | 18.95 | 23.67 | 23.59 | 22.89 | 21.02 | 23.26 | 12.9 | 9.3 |
| 2020 | 15.80 | 19.88 | 20.16 | 19.20 | 17.59 | 19.88 | 12.0 | 8.9 |
| 2021 | 23.41 | 29.52 | 29.65 | 27.71 | 25.58 | 29.40 | 12.9 | 8.4 |
| 2022 | 42.68 | 48.09 | 42.99 | 36.65 | 34.38 | 42.73 | 12.3 | 4.6 |
| 2023 | 19.35 | 27.12 | 27.11 | 26.01 | 23.97 | 27.04 | 16.4 | 7.7 |
| 2024 | 17.31 | 23.76 | 23.76 | 23.18 | 21.73 | 23.63 | 16.4 | 8.4 |
| 2025 | 24.20 | 34.69 | 32.83 | 32.20 | 30.93 | 32.69 | 17.9 | 6.7 |

Counterfactuals are **sizing only**, cleared at the model's own night Q:

- **CF1:** every available CC_REGULAR/CC_INTERMEDIATE committed MW becomes a price-taker. This is the
  commitment non-convexity: in MISO, EcoMin energy of a committed non-fast-start unit does not set LMP.
- **CF2:** the same for every gas committed band, CHP and ST_GAS included.
- **CF3:** CC econ tranches −$1/MWh.

All three are upper bounds, because they floor units that would not all be committed.

What is in the gap (2023, GW): CC_REGULAR econ 4.9 and committed 4.7, COAL_PRB econ 0.9, CC_CHP
committed 0.6, seam bands ~3.

Offer decomposition of the gap tranches:

| class | MW-weighted offer | components | markup |
|---|---|---|---|
| CC_REGULAR | $22.09 | HR 7.25 × $2.77 gas + $2.00 VOM | +0.07 |
| COAL_PRB | $22.62 | HR 11.95 × $1.92 + $4.50 VOM | −4.66 (take-or-pay sigmoid) |

**Reading:**
- The upper-bound structural counterfactual (CF2) closes $1.9–3.1 of a $4.1–10.5 median gap in the
  unrouted years (2019, 2020, 2023–2025), i.e. under half. It would also put more gas and less coal on at night, which moves
  quantities *away* from CAMPD, where they currently match.
- CF1 alone closes $0.6–1.9.
- The band-multiplier channel has nothing to act on for CC: the markup is ~0 and the offers are already
  at the measured basis (miso-275, miso-283). A coal econ multiplier would raise coal night generation
  above CAMPD, which is a wrong-mechanism fit (rule 1).

## 5. Routing and verdict

- **No solve.** No admissible structural lever sized here closes the object. The largest structural
  candidate, "committed EcoMin as price-taker while online", is real MISO design. Its machinery exists:
  `caiso_ra_mustoffer_min_gen(floor_online_hours=True)` over a P0 run pattern. But at its upper bound it
  closes under half the gap and it breaks the quantity match. As a floor it would need a rule-17 window,
  driver and forward story, and a D-2/rule-19 reconciliation against the existing coal must-run/committed
  floors.
- **The remaining half is the level of the real night offer book** at matched position. It is already
  adjudicated: miso-145 measured the real book $8–15 cheaper (universe-contaminated), and
  `measured_offer_surface` is R (miso-151). Nothing here is new evidence against that R.
- The two miso-130 successors are **both already in the keeper**: `miso_reserve_online_gated` (miso-169,
  K) and CC_REGULAR committed at 1.005 = phys. Neither is open.
- **Cell:** `diurnal_price_amplitude` stays **G**, now with the price-formation attribution and the
  counterfactual sizing recorded.
- **Rubric:** unchanged. The train tier is CALIBRATED. The full span is NOT-YET on the three routed misses.
  **No frontier.**
- **Side observations, not chartered:**
  - P1 sits $5.1 above the P0 stack in 2022 and $1.9 above it in 2025 at the same Q. That is a P1-pass
    effect (startup markup or network) in those two years only.
  - The model has zero night hours below $5 against 1.5–12 % at the hubs (West wind congestion is absent
    at night because the footprint is coupled).

## 6. Owner ruling (2026-09-29)

*"Charter EcoMin price-taker build"*. `diurnal_price_amplitude` is re-opened **G → O** (rule 28(a): the
owner card is the re-open instrument; the new evidence is §3–§4). The build is chartered in
`docs/records/miso/CHARTER-miso285-ecomin-price-taker-2026-09-29.md` for the successor lane. **Admissible scope is
merchant CC only** (rule 18 physics, rule 19): CHP classes carry their own host-steam must-run and ST_GAS its
p25/OOM floors, so the arm's upper bound is **CF1, −$0.6 to −1.9** night median, not CF2.
