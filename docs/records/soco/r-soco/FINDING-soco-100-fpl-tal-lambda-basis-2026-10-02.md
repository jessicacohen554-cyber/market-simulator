# FINDING soco-100: the FPL and TAL FERC-714 lambda basis (2026-10-02)

**Lane.** soco-100. Zero LP, research only. Owner card (2026-10-02): **"FPL + TAL lambda basis"**. SOCO stays at
NOT-YET (7/4/0/3/0); keeper `2026-09-30-soco96-measured-oil-burn` is unchanged. Everything here is a
**forecast-lane input, inert in every backcast** (§6).

## 1. Verdict

| Respondent | Question | Answer | Owner ruling (card, 2026-10-02) |
|---|---|---|---|
| FPL (171) | Is the ~40 % gap a basis/definition difference? | **No. It is real economics.** FPL uses the same Sch. 6 definition as its peers (a Lagrange incremental fuel cost). The level is its all-CC, coal-free fleet's incremental cost. | **Anchor 6 years, refuse 2021** |
| FPL (171) | Is every year a measurement? | **2021 is not.** The filing re-files 2019 (§2). | (same card) |
| TAL (140) | Is a sub-CC implied HR real? | **Yes.** The soco-99 flag compared an *incremental* λ with an *average* HR. TAL's CCs measure 5.5–6.1 incremental (§4). | **Confirm 2019–25 cells** |

## 2. FPL 2021 is a re-filing of FPL 2019

- **All 8,760 hours match.** Aligned by hour, FPL's 2021 Sch. 6 series equals its 2019 series rounded to whole
  dollars in every hour (share 1.000, r 0.998). At a ±1 h shift the share drops to 0.47.
- **No other respondent-year shares even 0.30** with any other year (TAL, FPC and JEA were checked pairwise for
  2019–25).
- **It is FPL's only 2021 XBRL filing** (`Florida_Power_&_Light_Company_form714_Q4_1654026868`). FPL's **first** 2022
  filing (`…_1685127913`) carried the same copy (mean 17.29, first hours 19/19/21/17/16). FPL then resubmitted
  (`…_1685543020`, mean 38.37), which is the one the extract uses. FPL never corrected 2021.
- **What this explains.** The "2021" monthly λ stays flat at $15–19 while HH rose from $2.6 to $5.5 and FPL's own
  delivered gas rose from $4.2 to $7.7. Those are 2019's values.

**Guard.** `derive_neighbor_hr_by_year.py::duplicate_filing_of` refuses any respondent-year that matches an earlier
year's hourly series at whole-dollar rounding in ≥ 99 % of hours (`DUPLICATE_FILING_SHARE`). The guard is generic: it
never moves a value, it only refuses a non-measurement, and it is reported in the derive output. Today it fires only on
FPL 2021, and every other registered cell is byte-identical. The rows stay in the extract as filed.

## 3. Each respondent's own description of its lambda

Source: Sch. 6 "Description of how Respondent calculates System Lambda". This is the CSV `Part 2 Schedule 6 - System
Lambda Description.csv` for 2015–20 and XBRL `DisclosureOfHowRespondentCalculatesSystemLambdaTextBlock` for 2021–25,
both from Zenodo record 21738524. The wording is unchanged in every year.

| Respondent | What it says | Components |
|---|---|---|
| FPL | ED "among the committed units to minimize **fuel** production costs … method of LaGrange multipliers" | incremental fuel only |
| FPC (DEF) | ED every 2 min, "minimize generator fuel costs **and transmission MW losses** … LaGrange multiplier" | fuel + loss penalty |
| JEA | "incremental heat rate of the marginal unit × its fuel cost, **or** the purchase energy rate" | fuel, or purchases |
| TAL | "Kirchmayer, *Economic Operation of Power Systems*, ch. 2" (classical equal-incremental-cost λ) | incremental fuel |
| SOCO | λ = [(2aP+b)(FC+EC) + VOM + FH] × TPF | fuel, emissions, VOM, handling, losses |

All five are the same quantity: an incremental (dF/dP) cost, not an average cost. FPL and TAL leave out VOM and losses.
That is worth a few $/MWh at most and cannot produce a 30–40 % gap.

## 4. The level: λ/HH against measured incremental heat rates

**Fuel basis.** EIA-923 delivered gas for all four Florida utilities runs $1.4–1.8 above HH, while their λ/delivered
ratios (FPL 3.3–4.7) are physically impossible. The delivered price carries **fixed** firm-pipeline reservation
charges, which no incremental dispatch cost includes. λ/HH is the comparable ratio, consistent with the registry's
`gas_basis = 0.0` on the Florida seams. Monthly λ tracks HH at lag 0 for every respondent (r 0.90–0.95, falling
monotonically with lag).

**Measured incremental HR.** For each utility's gas CCs, hourly CAMPD heat input is fit against gross load by a
quadratic per commitment state, and dF/dP is taken at median load. That incremental/average shape is then levelled to
EIA-923 fuel ÷ net, because CAMPD reports some CCs on CT-only gross load. The values are approximate (±0.5).

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **FPL λ/HH** | 6.78 | 6.77 | *(2019 copy)* | 5.90 | 6.06 | 6.45 | 5.98 |
| FPL CC incremental HR | 6.54 | 6.65 | — | 6.45 | 6.43 | 6.80 | 6.62 |
| FPL CC average HR (EIA-923) | 6.97 | 6.92 | 6.93 | 6.93 | 6.89 | 6.94 | 6.95 |
| **TAL λ/HH** | 5.68 | 5.78 | 6.02 | 6.90 | 7.56 | 7.67 | 7.24 |
| TAL CC incremental HR | 6.08 | 5.88 | — | 5.62 | 5.64 | 5.64 | 5.54 |
| TAL CC average HR (EIA-923) | 7.90 | 7.85 | 7.85 | 7.85 | 7.78 | 7.76 | 7.80 |
| FPC λ/HH | 8.41 | 8.05 | 8.04 | 9.14 | 8.72 | 9.58 | 8.77 |
| JEA λ/HH | 8.95 | 9.67 | 8.36 | 9.18 | 9.51 | 10.74 | 8.79 |
| SOCO λ/HH | 10.11 | 10.32 | 9.67 | 11.32 | 11.60 | 12.70 | 10.92 |

(2021 CAMPD was not fit for the incremental HR, which is why that column shows "—".)

**Fleet mix (EIA-923 net generation share)**

| | Gas | Nuclear | Coal |
|---|---:|---:|---:|
| FPL | 67–75 % | 21–23 % | 0 |
| FPC | 83–90 % | 0 | 7–12 % |
| JEA | 77–91 % | 0 | 2–8 % (Northside steam units) |
| TAL | 100 % | 0 | 0 |
| SOCO | 37–42 % | 27–36 % | 23–29 % |

**Reading.**
- **FPL.** The λ sits on its own CC fleet's incremental cost at HH, within ±0.5 in every valid year. A CC is almost
  always FPL's marginal unit.
- **FPC / JEA / SOCO.** Their λ sits above their CC incremental HR (FPC 6.2–6.6, JEA 4.9–6.3) because coal and steam
  units, CTs, losses (FPC) and VOM/emissions (SOCO) set their margins more often.
- **TAL.** The 2019–21 λ equals its two CCs' incremental cost. In 2022–25 it sits between that cost and its CTs' cost.

The gap is fleet composition, not filing basis.

## 5. Registry (owner ruling)

| Seam | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| SOCO_FPL (new) | 6.75 | 6.73 | — (refused, structural 11.6) | 5.98 | 6.06 | 6.55 | 5.96 |
| SOCO_TAL (confirmed, unchanged) | 5.68 | 5.78 | 5.97 | 6.93 | 7.60 | 7.69 | 7.22 |

The registry is the producer's output (`tests/iso/soco/test_soco_lambda_anchors.py::test_registry_is_the_producer_output`).
`SOCO_SCEG` is now the only unanchored SOCO seam. No SOCO `_HR_GAS_ELASTIC` fit exists, so FPL 2021 resolves to
`marginal_heat_rate` 11.6.

## 6. Inertness (zero LP, G-DRIFT)

- **Not on the solve surface.** `model/interchange/spec.py` is outside `SURFACE_MODULES` (`config/solve_surface.py`
  scope note), and the derive script is not on the solve path.
- **Cache keys.** I re-computed `cache_key()` for every committed `results/calibration/*/run_config.json` that
  reconstructs on HEAD (5 of 11; the other 6 name retired fields). All 5 are identical before and after.
- **No solve reads the change.** The SOCO blocks stay default-off (`reference_price_interface` /
  `priced_interchange`, asserted by the test). Matrix cells `priced_interchange` / `reference_price_interface` stay `U`.
- **Unrelated red tests.** `tests/unit/data/test_gas_offer_zonal_anchor_vintage.py` (2 failures, NYISO Upstate_West)
  is red on `main` and untouched here.

## 7. Owner ruling recorded, not implemented here

**Forward HR for the SOCO seams = the seam-own flat mean** (card, 2026-10-02). This replaces both the FINDING-soco-98
§3 elasticity fits and the 11.6 flat. It is for a later forecast-lane session.

With this lane's inputs, the means over registered cells are:
- FPL **6.34** (6 years, 2021 excluded)
- TAL **6.70** (7 years)
- FPC **8.71** (7 years)

## 8. Records

- `soco100_lambda_vs_gas_monthly.{py,csv}`: monthly λ, EIA-923 delivered gas and HH per respondent.
- `soco100_cc_incremental_hr.{py,csv}`: the CAMPD/EIA-923 CC incremental heat rates.

Both read committed data only (soco hydrate profile). The XBRL description and duplicate check reads the Zenodo
archives that `fetch_ferc714_system_lambda.py` already pins.
