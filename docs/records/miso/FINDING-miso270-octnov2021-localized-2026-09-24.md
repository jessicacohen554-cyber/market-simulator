# FINDING — miso-270: Oct–Nov 2021 localized at zero LP. No solve earned.

Keeper `2026-09-24-miso-268-coal-yard` (`results/calibration/miso268_yard_span`), confirmed on
`origin/main`. **Zero LP** (rule 32(a)). Nothing solved, registered, promoted or deleted.

**Why Task C only.** No owner ruling exists on either miso-269 decision (D1 storm-month gas
construction; D2 thin extreme-event prints) — not in the handoff, `docs/calibration-log/miso.md`,
or the matrix. F2's MISO short-gas FINDING (`cf7e068a`,
`docs/handoffs/FINDING-f2-campd-outage-coverage-2026-09-24.md`) is an outage-data intake. It lands
an unarmed `shortgas-MISO` file and flags drift in the armed `unitroute-MISO` / `short-MISO` extracts,
routed to R-MISO; the committed files are untouched. It does **not** change miso-269 §1/§2, which are
gas-price objects.

Instrument: `scripts/probes/_miso270_octnov2021_phase0.py` → `results/calibration/_miso270_octnov2021_phase0.json`.
Scorer basis reproduced first: 2021 C3b NRMSE on bench `rt_lw_mon` = **0.3086** (registered 0.309).

## 1. Localization table (2021; Sep and Dec are the adjacent controls)

| leg | Sep | **Oct** | **Nov** | Dec | verdict |
|---|---:|---:|---:|---:|---|
| LW price model / bench ($/MWh) | 39.5 / 48.0 | **48.2 / 59.8** | **47.5 / 67.0** | 42.4 / 42.5 | — |
| share of C3b SSE | 3.8 % | **7.2 %** | **20.1 %** | 0.0 % | Oct+Nov 27.3 % |
| coal, model − CAMPD (TWh) | +1.47 | **+1.19** | **+1.22** | +0.10 | **over-runs** (Jan–Aug: −1.2 to −4.4) |
| CC_REGULAR, model − CAMPD | −2.97 | −2.00 | −1.93 | −1.07 | under (Mar–Aug: +0.6 to +1.4) |
| CT_PEAKER, model − CAMPD | −0.17 | **−0.97** | **−0.86** | −0.24 | under |
| ST_GAS, model − CAMPD | −0.69 | −0.82 | −0.79 | −0.23 | under |
| import, model − EIA-930 net | +0.58 | **+0.74** | **+0.87** | +0.42 | over (Mar–Jun: −0.6 to −1.3) |
| wind, model − EIA-930 | +0.32 | +0.35 | +0.47 | +0.46 | +0.2–0.47 every month: **not fall-specific** |
| nuclear, model − EIA-930 | −0.14 | −0.03 | −1.08 | −1.23 | wrong sign to explain a low price |
| setter share gas / coal (matched MWh) | 56 / 43 % | 76 / 21 % | 77 / 23 % | 70 / 27 % | gas sets, but CC econ at **$45–49** |
| econ mc CC / CT_PEAKER / ST_GAS | 42 / 71 / 68 | 45 / 76 / 74 | 43 / 74 / 68 | 38 / 64 / 72 | actual ~$60–67 needs the steam/CT tier |
| north 5-zone price spread, model / actual | 0.4 / 5.6 | 0.2 / 7.2 | **0.1 / 23.5** | 0.1 / 8.5 | no north congestion in model (Nov: Indiana $67.5 vs West $43.9) |
| reserve duals, shortfall, slack, dump | 0 | 0 | 0 | 0 | **not reserves / scarcity** |
| model gas fuel, CC cap-wtd ($/MMBtu) | 5.13 | 5.57 | 5.22 | 4.44 | above hub (miso-269): **not gas** |

Hour of day: the Oct–Nov gap is daytime (HE5–HE18, −9 to −28 $/MWh); overnight error ≈ 0.
Zone: the gap is entirely the five northern zones (South is near actual).

## 2. What it is

A **northern-zone, daytime merit-depth object.** Against measured volumes, the model serves roughly
2 TWh/month more from coal (+1.2) and imports (+0.7–0.9) in Oct–Nov. The gas stack therefore stops at
CCs ($45–49), where the real system cleared into steam gas and CTs ($60–76 mc). In November a missing
north congestion (Indiana/East) comes on top of that.

## 3. What it is NOT (checked, at zero LP)

* **Gas price:** model gas sits above the hub (miso-269).
* **Reserves / scarcity:** every reserve family dual is 0 and shortfall is 0 in every month of 2021.
* **Coal outage overlay:** at plant grain, model coal in-service energy ≈ CAMPD burn (CAMPD / in-service
  0.88–1.00 Sep–Dec). Only one plant (Erickson, 146 MW) is CAMPD-dark while the model keeps it in service.
* **The coal budget:** the miso-259 flat monthly rows (23.0 TWh-equiv each at the cap-weighted HR 11.92)
  **bind in Jun–Sep**. Model coal is pinned at 24.1–24.6 TWh/mo there, while CAMPD burned 28.5 / 29.0 in
  Jul / Aug. In Oct–Nov the rows are **loose** (model/cap 0.88 / 0.74). The HR is approximate: the sidecar
  carries MW, not MMBtu.
* **The named SOC-carry successor (miso-259):** it would not bind in fall 2021. With zero minimum stock,
  the cumulative allowance (opening 63.2 + receipts rate 212.8 TWh-equiv/yr × m/12) keeps at least
  **16.6 TWh-equiv** of headroom through October **on CAMPD's own burn path** (33.0 on the model's). A carry
  would lift the summer clip, which is a different object and would lower summer price. By itself it
  cannot touch Oct–Nov.

## 4. Routed, not absorbed (no lever proposed; none is admissible without a ruling or data)

1. **Fall coal over-run (+1.2 TWh/mo).** Its real-world counterpart is fuel-scarcity behaviour
   (conservation) when stocks are low. In this LP it can only enter as the dual of a *binding* stock row.
   That needs a **minimum operating stock from a cited days-of-burn source** (miso-259's "second lever";
   never set from the residual). This is a data ask, not a solve. The only other channel is the owner's
   rule-1 coal band multiplier (ex ante, year-invariant, never swept).
2. **Fall import excess (+0.6–0.9 TWh/mo; sign flips vs Mar–Jun).** It sits on the measured seam ladders
   (`seam_neighbour_hourly_ladder`, K). Successor: split by seam (PJM / SPP / South) against EIA-930
   interchange.
3. **North congestion absent** (model 5-zone spread ≤ 0.4 $/MWh all year; actual 23.5 in Nov). This is a
   topology / transmission object. It is outside every open MISO lever.

Held-out years never downgrade the ISO (rule 30(c)). MISO's train tier stays CALIBRATED.
