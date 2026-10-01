# FINDING — NWPP-NEXT-11: where the COAL_PRB C1 gap and the C4 coal 2023 miss actually live (ZERO LP)

Keeper #16 (`2026-09-29-nwppnext10-exit-month-routing`) stands. Nothing was solved, registered, promoted or pruned.
Every number below comes from committed artifacts: the keeper payload
(`frontend/data/backcast/runs/<id>.js`), the NWPP bench parts (`frontend/data/backcast/bench/NWPP/<y>.json.gz`), the
keeper's `hourly/class_hourly_<y>.parquet`, EIA-923 via `scripts/run_calibration_full._eia923_frame`, EIA-930 via
`_eia930_frame`, and CAMPD unit-level parquets.

## 1. Lever 1 (COAL_PRB 2020 +4.20 TWh): mostly a benchmark-basis effect, not a plant over-run

C1's class actual (`classFull`) is the EIA-923 class total put through `render_calibration_html.reconcile_vintage_classes`,
which scales **every** fossil class by ONE factor so gas + coal matches EIA-930 gas + coal.

| year | k (coal, CC, ST, CT) | 923 coal raw | EIA-930 coal cell | classFull coal |
|---|---|---|---|---|
| 2019 | 0.869 | 64.9 | 54.6 | 56.5 |
| 2020 | 0.917 | 52.3 | 51.9 | 48.0 |
| 2021 | 0.887 | 53.6 | 50.1 | 47.7 |
| 2022 | 0.892–0.897 | 52.8 | 49.4 | 47.3 |
| 2023 | 0.900 / BIT 0.947 | 44.1 | 42.3 | 40.4 |
| 2024 | 0.912 | 37.7 | 38.3 | 34.4 |

(2025 is a preliminary vintage and scales up; CC_CHP additionally carries its BTM subtraction.)

- EIA-930's own coal cell sits within 1 % of 923 coal in 2020 and 2024, and 1.8–10 TWh below it in the other years
  (2019 is the widest). The 2020 down-scale (~8 %) therefore comes from the gas side: 930 gas sits well below 923 grid
  gas, and the uniform factor charges that gas shortfall to coal too. Which side is right is exactly the question
  the docstring says a per-class 930 reconcile cannot answer.
- Coal WC totals in the table are approximate (under 0.65 TWh).
- **The 2020 COAL_PRB miss decomposes as +1.73 TWh model vs raw EIA-923 plus +2.47 TWh from the reconcile factor.**
- The per-plant 2020 over-run against EIA-923 net is small and spread out:
  - Dave Johnston 4158: +0.66
  - Boardman 6106: +0.60. This is all Apr–Jun: the unit's CEMS opTime is 0 in those months, but the model runs it.
    Boardman is single-unit, so the standard extract detects no window there.
  - Wyodak 6101: +0.44
  - Colstrip, Bridger and Naughton are each within ±0.05.
- The reconcile's docstring already names this limitation: "a CAMPD-per-class target … is the follow-up refinement".
  It is a cross-ISO scorer question (every ISO's C1 would move), so it is routed to the owner. It is not an NWPP lever.
- The same factor explains the "per-plant CC sum ≠ classFull" gap NEXT-7 routed (FINDING-nwppnext7 §4).
- **Effect on the determination: none.** C1 passes in every year either way. C4's r is scale-invariant, and C4 reads
  the EIA-930 coal hourly, not `classFull`.

## 2. C4 coal 2023 (r 0.695): a real model miss, and it is Jim Bridger

| year | r(model, 930) | r(model, CEMS) | r(CEMS, 930) |
|---|---|---|---|
| 2019 | 0.733 | 0.779 | 0.966 |
| 2020 | 0.772 | 0.821 | 0.953 |
| 2021 | 0.792 | 0.818 | 0.984 |
| 2022 | 0.741 | 0.700 | 0.972 |
| **2023** | **0.695** | **0.691** | **0.989** |
| 2024 | 0.739 | 0.797 | 0.973 |
| 2025 | 0.721 | 0.726 | 0.979 |

- In 2023, EIA-930 and CEMS agree in shape (r 0.989). **The benchmark is not the problem.**
- Swap test: replace one plant's model hourly with its CEMS hourly, then re-score fleet r against 930.

  | Plant, 2023 | Δr from swap | Plant r (model vs CEMS) | Model TWh | CEMS TWh |
  |---|---|---|---|---|
  | **Jim Bridger 8066** | **+0.145** (fleet → 0.84) | **0.07** | 9.19 | 9.11 |
  | Centralia | +0.065 | | | |
  | Hunter | +0.061 | | | |
  | Colstrip | +0.033 | | | |

- **Bridger 2023, monthly mean MW:**

  | | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|
  | Actual (CEMS) | 1228 | 615 | 376 | 234 | 476 | 938 | 1589 | 1564 | 1234 | 1714 | 1219 | 1292 |
  | Model | 1879 | 1815 | 1256 | 444 | 755 | 930 | 937 | 993 | 931 | 837 | 880 | 929 |

  Annual energy matches (9.19 vs 9.11 TWh). The **timing** is inverted.
- Unit-level CEMS: all four units stay **on-line** Feb–May at 110–150 MW gross (about a quarter of rating; BW73 is out in
  April). That is the signature of fuel conservation: hold units warm at minimum and save coal for summer.
- The model spends the same annual energy in Jan–Mar, when 2022–23 winter gas is dear. A perfect-foresight LP does
  exactly that. The operator could not, because the pile was at a record low (NEXT-9 §2).
- This is the inventory-management behaviour already routed, and every form with a public identification is closed
  (NEXT-9 measured receipts R, S_min refuted, days-of-burn target redacted). The unit-level signature adds evidence;
  it adds no identification. Pinning monthly burn or stock to measured values would be an outcome pin (rule 13).

## 3. Lever 3 (lay-up booked as outage): the guard exists but covers little

- The standard extract books whole spring months at zero availability (Centralia 2020 Mar–Jul; North Valmy 2020
  Jan–Jun, which are peer-online windows). It books nothing at single-unit Boardman.
- `campd-unit-outages-layup-NWPP.csv` (the merit-guard companion) has 17 rows, all 2023–2025:
  - Bridger BW73 2023-03-21..05-14
  - Hunter 3, Apr 2023
  - North Valmy 2023–25
  - TS Power 2023–25
- No 2019–2022 window is reclassified, and there is no `-perunitmerit-NWPP` family for
  `campd_outage_merit_order_guard` to select.
- Arming the guard therefore needs a new per-unit merit extract (a rule-23 data derivation) before any solve. On
  Bridger 2023 it would **add** spring availability, which does not bind (model April burn 444 MW against 871 MW
  available). So it cannot move C4 2023.

## 4. Routed

1. **C4 coal 2023 stays the only failing record.** No NWPP-side structural arm with a measured identification exists.
   The remaining routes are owner decisions:
   - an owner-sourced inventory target; or
   - a governance ruling on how to treat a supply-shock conservation year.
2. **Benchmark fossil reconcile:** a CEMS-anchored per-family coal target, cross-ISO. This is an owner question.
3. **Fidelity levers that do not move the determination:**
   - lever 3: derive the NWPP per-unit merit extract, then test the guard;
   - Boardman's single-unit spring shutdowns;
   - lever 2 (coal availability below measured generation).

## 5. Owner rulings (decision cards, 2026-09-29)

- **C4 2023 → "Fidelity levers".** Keeper #16 stands and C4 coal 2023 stays open. NWPP-NEXT-12 derives the NWPP
  per-unit merit-guard extract, then tests lay-up (lever 3) and coal availability (lever 2). Neither is expected to
  clear C4 2023.
- **Benchmark reconcile → "Route to scorer lane".** A separate cross-ISO lane designs a CEMS-anchored coal target.
  NWPP changes nothing now. Handoff: `docs/records/misc/HANDOFF-scorer-coal-reconcile-2026-09-29.md`.
