# FINDING — soco-80: the registered coal TAKE floor is not an admissible carrier for SOCO (zero LP, no solve)

**Keeper unchanged:** `2026-09-27-soco76-egrid-identity-hr`. **Failing rows unchanged:** 2019 C1 COAL_BIT −4.16 pp,
2020 C4 coal NRMSE 0.301.

## 0. Housekeeping and scope

- PR #6788 (soco-79) is on main at `3969fe8b`. The parent session `session_015i2oqoYMpbxLKGF2E9J9rp` is archived.
- Unmerged SOCO refs on origin: only `claude/soco-79-fr22-gap` (`bba87fe6`). Its patch is the same content as
  `3969fe8b` on main, so nothing needs salvaging. The `claude/soco76-<year>` leg refs **no longer exist on origin**
  (rule 33(f)(1)), so this lane worked from the committed payload, the `soco76_span` hourlies and measured inputs only.
- No owner ruling on soco-75 (two-sided coal HR bound) or soco-77 (tranche start amortization), so the zero-LP task ran.
- The lever queue's take-or-pay row is already `G` (soco-74, `coal_takeorpay_committed`: Purchase Type is a price
  term). The remaining untested member of that family is **`coal_fuel_inventory_take_floor`** (NWPP-NEXT-7, owner
  rulings Q1–Q5). It is annual, per coal yard, and built only from Y−1 data. It is the one registered carrier that can
  lift coal **econ** energy (soco-73's object) without an adder.

## 1. The carrier, reproduced (rule 13 test)

`build_coal_take_floor`: `take_net = max(0, C_{Y−1} + S_dec,Y−1 − S_max,≤Y−1) × hc_{Y−1}`. Here C is the
EIA-923 Page-5 contract tons (C/NC/T), S is the Page-2 month-end stock, and hc is the heat content. Every operand
predates the solved year, and the construction regenerates forward. That passes the first half of rule 13. The
second half ("would it respond to changed conditions") rests on estimator B's premise that **contracts renew at the
Y−1 volume**. The probe reproduces the arithmetic per SOCO coal plant (SOCO has no shared yards). It converts tons to
MWh at the keeper's own applied net heat rate.

## 2. Floor vs the keeper vs EIA-923 (TWh; `soco80_take_floor.csv`)

| year | model | actual | floor | lift over model | floor **above actual** |
|---|---:|---:|---:|---:|---:|
| 2019 | 45.39 | 55.06 | 40.40 | 5.72 | 0.25 |
| 2020 | 31.17 | 38.77 | 48.05 | 16.92 | **9.90** |
| 2021 | 51.58 | 48.86 | 29.33 | 2.14 | 0.00 |
| 2022 | 54.10 | 44.66 | 19.88 | 0.00 | 0.00 |
| 2023 | 30.92 | 37.49 | 26.98 | 2.76 | 0.29 |
| 2024 | 33.06 | 40.33 | 38.41 | 5.88 | **1.73** |
| 2025 | 48.27 | 43.46 | 29.36 | 0.00 | 0.00 |

Fleet sums over SOCO's eight coal plants. The per-plant rows are in the CSV.

- **2019 BIT:** the floor lifts Barry (model 0.09 → floor 3.67, actual 4.18) and Crist (1.00 → 2.92, actual 2.67).
  Both land at or just under actual.
- **2020:** Scherer's floor is **13.15 TWh against 5.63 actual (2.3×)**, and Crist's is 2.48 against 1.10. SOCO
  cut its contracted deliveries 28.87 → 19.76 Mt (−32 %) that year (soco-74). The renewal premise fails in exactly the
  C4-failing year.
- **2024:** Barry's floor is 2.43 against 0.70 actual (3.5×).

## 3. Scorer-exact greedy (`soco80_take_floor_greedy.csv`)

Construction: an annual floor's dual is a flat discount on the yard's offers, so the lift fills the plant's
highest-price hours at full headroom. Headroom is nameplate minus model MW, decoded on the scorer's own basis. The
same MW are displaced from CC_REGULAR. Outage windows are not visible in the payload, so this is an upper bound on
how well the lift lands in shape. Scored with `calibration_verdict.score_fuelmix` and the `_soco73_phase0.c4_coal`
construction.

| year | row | keeper | floor arm |
|---|---|---|---|
| 2019 | C1 COAL_BIT | −4.16 pp FAIL | −2.61 pp **PASS** |
| 2019 | C4 coal r / NRMSE | 0.872 / 0.250 | 0.841 / 0.230 |
| 2020 | C1 CC_REGULAR | +2.25 pp PASS | −4.23 pp **FAIL** |
| 2020 | C1 COAL_PRB | −0.16 pp PASS | +3.89 pp **FAIL** |
| 2020 | C4 coal r / NRMSE | 0.925 / 0.301 FAIL | 0.734 / 0.514 FAIL |
| 2021 | C4 coal | 0.876 / 0.208 | 0.855 / 0.244 |
| 2023 | C4 coal | 0.905 / 0.267 | 0.854 / 0.238 |
| 2024 | C4 coal | 0.848 / 0.254 PASS | 0.671 / 0.381 **FAIL** |
| 2022 / 2025 | — | no lift | unchanged |

## 4. Verdict: `G` (refused on structure, not on fit)

- **Rule 20 / C8 provenance:** a floor that forces Scherer to 2.3× and Barry to 3.5× their measured energy has a
  level that does not match reality. That is the "forcing variables are wrong" signal, independent of the residual.
- **Rule 13:** the forward premise (renewal at Y−1 volume) is falsified by SOCO's own Page-5 record in 2020. The
  admissible alternative would read Y's contracts, and that is an outcome.
- **Rule 1:** a scope that keeps only 2019 or only the BIT cyclers would be selecting a mechanism by the criterion
  it passes, so it is refused.
- **Gating:** arming for SOCO would also need `coal_fuel_inventory` (+ `_plant_grain`), which raises outside MISO,
  plus `COAL_TAKE_FLOOR_ISOS` (NWPP). None of those gates was lifted.

## 5. What this leaves

With take-or-pay (soco-74, G), take floor (this, G), incremental HR (soco-75, I), campaign floors (soco-73,
refused), the gas merit order (soco-76, K) and the family vintage (soco-79, inert), the coal side has no remaining
**unilateral** admissible carrier. The two open owner questions are still the only built candidates with greedy
evidence:

- soco-75 two-sided HR bound: 2020 C4 → 0.289/0.294 PASS; 2019 COAL_BIT −4.01/−4.18 (FAIL).
- soco-77 start amortization: 2020 C4 → 0.236 PASS; 2019 COAL_BIT −3.52 (FAIL).

Neither closes 2019 COAL_BIT. On every measured instrument so far, that row is the cyclers (Barry/Crist/Wansley)
not being started in 2019. In 2019 the floor's lift for Barry/Crist lands at actual, which says the energy is real. What the model lacks is a forward-regenerating reason for it.

## 6. Retrievability

No solve was run, so nothing is promotable. The probe and CSVs are committed.
