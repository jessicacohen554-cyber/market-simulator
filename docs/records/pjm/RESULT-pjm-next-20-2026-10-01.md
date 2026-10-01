# RESULT — PJM-NEXT-20: the low-end price gap is not what moves 2019–21 coal; the miss is in-merit loading (zero LP)

**Keeper unchanged:** `2026-09-30-pjm-next16-ovec` (bundle `pjmnext16_A_span`). Run-level, training tier 2023–2025 and ISO (v3.13) all read **NOT-YET**. Same 10 failing cells.

**Solves:** none. No PRECOMMIT (card 3 not reached). All numbers are read from the keeper's committed `hourly/unit_marginal_<y>.parquet`, `system_<y>.parquet`, the C1 bench (CAMPD profile rescaled to EIA-923), CAMPD unit-level gross load and PJM actual RT.

| probe | artifact | card |
|---|---|---|
| `scripts/probes/_pjmnext20_coal_price_response.py` | `results/phase0/pjm/_pjmnext20_coal_price_response.json` | 1 |
| `scripts/probes/_pjmnext20_coal_ladder_at_rt.py` | `results/phase0/pjm/_pjmnext20_coal_ladder_at_rt.json` | 1 |
| `scripts/probes/_pjmnext20_coal_unit_loading.py` | `results/phase0/pjm/_pjmnext20_coal_unit_loading.json` | 1 |
| `scripts/probes/_pjmnext20_ua_census.py` | `results/phase0/pjm/_pjmnext20_ua_census.json` | 2 |

## 1. Card 1 — does the same low-end price gap move more coal in 2019–21?

**Hypothesis (NEXT-19 §2).** The keeper's price is too high in sub-$25 hours in every year. In 2019–21 coal and CC costs sit within ~$3, so the same gap would move more coal.

**Test.** Per coal plant-hour: the plant's MW-weighted keeper offer vs PJM actual RT. A plant-hour is **underwater** when actual RT is below that offer, i.e. at the actual price the model's own coal offer would not clear. The over-run is model − bench (EIA-923 net).

| TWh unless stated | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| C1 COAL_BIT over-run (keeper) | +18.7 | +11.9 | +17.1 | +6.8 | +0.3 | +0.9 | +11.3 |
| model zone price − RT, coal-MW-weighted median ($) | 3.5 | 4.5 | 5.1 | 4.8 | 4.8 | 3.5 | 4.3 |
| over-run, **underwater** plant-hours | +1.4 | −1.7 | +0.4 | +0.2 | −2.9 | −1.4 | +0.8 |
| over-run, **above-water** plant-hours | +12.8 | +11.4 | +16.3 | +8.9 | +1.6 | −1.1 | +13.1 |
| … of which the real plant was **on** | +9.6 | +9.6 | +13.6 | +5.8 | +0.8 | −1.7 | +11.6 |
| model coal MWh from tranches priced above actual RT | 40.3 | 40.0 | 35.1 | 19.8 | 22.9 | 26.1 | 24.9 |

The split covers the keeper coal plants the C1 bench carries a CAMPD profile for (97–100 % of keeper coal energy), so its rows do not sum to the C1 row exactly.

**Reading.**
- The price gap itself is the same size in every year ($3.5–5.1). The hypothesis's premise holds.
- But the over-run is **not** in hours where actual RT would have pushed the model's coal out of merit: underwater plant-hours carry ≈ 0 in every year.
- It sits in plant-hours where actual RT is **above** the model's own coal offer, and mostly where the real plant was online.
- The price-gap volume (last row) orders 2019–21 above 2023/24, but **2025 breaks it**: 24.9 TWh, like the fit years, and an +11.3 over-run. 2020 has the largest volume and the smallest over-run of the three miss years.

### 1b. The loading curve: real coal vs the keeper, by margin

Net loading on the model's available capacity, plant-hours with the real plant on (bench = EIA-923 net). Margin = actual RT − the plant's keeper offer.

| margin ($/MWh) | | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|
| 0–5 | model / real | .77 / .67 | .74 / .65 | .83 / .72 | .73 / .66 | .70 / .64 | .70 / .67 | .78 / .69 |
| 5–15 | model / real | .85 / .81 | .84 / .79 | .89 / .81 | .78 / .69 | .73 / .71 | .72 / .73 | .87 / .77 |
| > 15 | model / real | .96 / .94 | .92 / .90 | .95 / .89 | .82 / .80 | .77 / .80 | .79 / .82 | .94 / .87 |
| keeper econ-ladder spread within plant ($, median) | | 5.3 | 5.4 | 8.1 | 21.4 | 9.1 | 9.2 | 11.4 |

- **Real coal's curve is close to the same every year:** 0.64–0.72 at $0–5, rising to 0.80–0.94 above $15. Unit grain (CAMPD): 72–84 % of unit capacity on, and on-unit loading rising from ~0.6 to ~0.9 with margin, in every year.
- **The keeper's curve is steeper in the miss years.** At $0–15 margin it sits +0.04 to +0.11 above real in 2019–21 and 2025, against −0.01 to +0.06 in 2023/24.
- The keeper's econ ladder is narrowest in 2019/20 ($5.3–5.4), which fits a steep response. But 2021 ($8.1) is close to 2023/24 ($9.1–9.2), and 2025 is wider ($11.4). **The ladder width does not order the years either.**

**Verdict, card 1.** The hypothesis is **refuted as framed**. The low-end price gap is real but is not what moves 2019–21 coal. The over-run is the keeper's **in-merit loading response** (NEXT-10 "response, not price"; NEXT-17 "econ-band loading"), now located at hour grain: $0–15 of margin, real plant online, all four miss years. No admissible, year-discriminating, zero-DOF mechanism. **OPEN, not a limit.**

The card's second half (real coal's own-curve output at actual vs model price) was not re-run: NEXT-17 §3 measured it on the full 84-month offers corpus (price-level term +31 / +47 / +25 / +5 / +19 / +14 / +13 TWh, not year-ordered), and the corpus is gitignored raw that is not in this container.

## 2. Card 2 — U_a, 2023 → 2024

_Pending (section written when the census lands)._

## 3. Card 3

Not reached.

## 4. Next (NEXT-21)

_Pending._

**Retrievability:** no bundles. Probe JSONs are committed under `results/phase0/pjm/`.
