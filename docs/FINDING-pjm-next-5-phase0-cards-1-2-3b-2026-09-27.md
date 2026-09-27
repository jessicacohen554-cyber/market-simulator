# FINDING — PJM-NEXT-5 phase 0: cards 1, 2 and 3(b) (zero LP) (2026-09-27)

Keeper `2026-09-26-pjm-next-4-midcurve2019` (bundle `results/calibration/pjmnext4_c1_span`). **Zero LP.** Fleet-only
rebuilds of the keeper recipe through `replay_keeper.run_year_kwargs` (`pjm_da_virtual_bids` off: demand-side, inert
for fleet, fuel and offers). None of the three cards reaches a solve. Card 3(a), the F2 re-derive, is the session's
solve: `docs/PRECOMMIT-pjm-next-5-card3a-f2-rederive-2026-09-27.md`.

Probes: `scripts/probes/pjm_next5_card1_cc_phase0.py`, `pjm_next5_card1_rows.py`,
`pjm_next5_card3b_retiree_cap_phase0.py`. Artifacts: `results/calibration/_pjm_next5_card1_cc_phase0.json`,
`_pjm_next5_card1_rows_{2019,2024}.parquet`, `_pjm_next5_card3b_*.json`.

## Card 1 — the model's CC econ bid against PJM's own CC offers

**Method.** For every CC_REGULAR econ tranche row, the measured target is read with the model's own surface helpers
(`_pjm_midcurve_context` / `_pjm_midcurve_row_target`) at the row's own within-plant share. That target is PJM's
measured offer in $/MWh: the deriver divides by `gas_day` and the helper multiplies back by it, so the gas index
cancels. Weights are `pmax × availability`, over hours with a finite target. Every bid is `mc_base`, so the P1
startup amortization (which needs P0, an LP) is excluded and every gap below is a **lower bound**.

**Answer: the model's CC econ bid sits $7–10.5/MWh above PJM's own CC offers at matched share, in 72–97 % of
hours, every year.**

| year | CC econ model | CC measured | gap | hours above | COAL_BIT econ model | coal measured |
|---|---|---|---|---|---|---|
| 2019 | 27.12 | 20.08 | **+7.0** | 96 % | 21.80 | 24.06 |
| 2020 | 23.50 | 15.19 | +8.3 | 97 % | 20.11 | 21.79 |
| 2021 | 36.18 | 26.49 | +9.7 | 96 % | 27.71 | 30.50 |
| 2022 | 57.11 | 48.43 | +8.7 | 72 % | 40.92 | 60.20 |
| 2023 | 27.43 | 19.13 | +8.3 | 88 % | 34.68 | 30.96 |
| 2024 | 26.85 | 19.21 | **+7.6** | 87 % | 32.95 | 29.63 |
| 2025 | 37.26 | 26.73 | +10.5 | 81 % | 36.47 | 32.92 |

- **The 2019–2022 merit-order inversion is on the gas side, as the handoff suspected.** PJM's own offers put CC ahead
  of coal in every pre-2023 year (2019: CC $20.1 < coal $24.1). The model puts coal ahead (2019: coal $25.05 after the
  floor < CC $27.12).
- **The model's coal econ bid is *below* measured before 2023.** That is why the floor binds on most coal hours.

**Where the gap sits, by rung (cap-weighted, $/MWh):**

| rung | share | 2019 model | 2019 meas | gap | 2024 model | 2024 meas | gap |
|---|---|---|---|---|---|---|---|
| committed | 0.28 | 21.7 | 18.6 | +3.1 | 19.7 | 15.4 | +4.4 |
| econc00 | 0.34–0.41 | 22.9 | 18.7 | +4.3 | 22.9 | 15.4 | +7.5 |
| econc01 | 0.52 | 24.4 | 18.8 | +5.6 | 24.4 | 15.8 | +8.6 |
| econc02 | 0.61–0.64 | 25.6 | 19.0 | +6.6 | 25.7 | 16.5 | +9.2 |
| econc03 | 0.71–0.73 | 27.8 | 19.8 | +8.0 | 27.6 | 18.2 | +9.3 |
| econc04 | 0.80 | 30.6 | 21.3 | +9.3 | 30.1 | 22.1 | +8.0 |
| econc05 | 0.89 | 33.6 | 24.0 | +9.6 | 32.8 | 30.7 | +2.1 |

The gap has two halves, with different operands.

1. **Level (committed rung, +3.1 / +4.4).** This is the plant's measured CAMPD heat rate (7.0–7.1 net, which matches
   the census within 1 %, pjm-h21) × its delivered gas, plus VOM $2.0 and RGGI where it applies. The operand is the
   **delivered gas level**: EIA-923 plant or N3045 state *average* delivered cost, against the marginal commodity cost
   that PJM cost-based offers use.
   - By zone, 2024 econ gap: Central PA +1.5, AEP +2.7, ComEd +5.0, ATSI +5.6, Dominion +8.3, EMAAC +15.6 (RGGI
     +$10.1), SWMAAC +20.1 (RGGI +$9.2, MD gas +$0.95 over HH).
   - RGGI is structurally correct (`K`). The measured ladder is RTO-wide, because DataMiner offers are unit-masked, so
     a RGGI zone reading above it is expected and does not identify a defect.
   - **Can it be measured? No.** EIA-923 Page 5 does carry a purchase type (spot / contract), but for the keeper's CC
     plants **82–83 % of gas receipts are cost-withheld** (2019: 18 % reported; 2024: 17 %). The reported ones are
     utility plants (Dominion, SWMAAC) whose spot cost the model already uses (Dominion 2019: $3.43 = $3.43). No
     admissible free series for the merchant fleet's marginal gas exists. **Data-blocked.** A licensed hub index is
     the owner's call, and the owner ruled no sourcing now.
2. **Shape (econ rungs c00–c03, a further +1 to +6.5).** The econ rungs are `base_hr × mult`, with `mult` rising
   `econ_low 0.96 → econ_high 1.5` (`offer_curve_by_group` CC_REGULAR, ledgered `identification: residual`). PJM's own
   ladder stays nearly flat to share ~0.65 and rises at the top. The floor form cannot lower a rung.

**The admissible correction exists, and it is the owner's design decision, not a lane default.** pjm-h21 §3 already
named it: apply the measured curve's *shape* to each plant's *own* cost (`rung = plant cost × m(s)/m(s_committed)`,
with the gas index cancelling inside the ratio). It keeps the plant gas basis and heat rate that the level form
erased. It has zero free parameters, and it would retire the residual-identified CC econ multipliers (rule 14 over a
rule-1 carve-out channel).

Static read, no redispatch, indicative only:

| | keeper econ bid | shape form | measured |
|---|---|---|---|
| 2019 | 27.12 | **24.16** | 20.08 |
| 2024 | 26.85 | 27.24 | 19.21 |

- **2019:** the CC econ bid falls below coal's floored $25.05, which reverses the inversion.
- **2024:** it does **not** help the training-span failure. The lower rungs fall $0.3–2 and the top rung rises +$9.
  Dominion, EMAAC and SWMAAC get *more* expensive.

So the shape form addresses the pre-2023 coal/CC ordering. It would not close C1 CC_REGULAR 2024, whose excess is
the level half (data-blocked).

**Card-1 verdict: no measured operand is ready for a solve.** The shape form goes to the owner (question 1 below).
Do not re-arm the level form as-is (pjm-h21).

## Card 2 — the coal side's unadjudicated levers

- **`coal_offer_net_revenue_margin` (U): stays U, instrument-blocked, no new evidence.** Its identification needs
  unit-resolved offers (ERCOT 60-Day SCED). PJM DataMiner offers are unit-masked (pjm-146, PJM-NUC-1b).
- **`coal_fuel_inventory` (U): stays U. It cannot reach the named over-run.** EIA-923 PJM-BA coal stocks (clean
  `coal-stocks`), Mt:

  | | Jan | Apr | Jul | Oct | Dec |
  |---|---|---|---|---|---|
  | 2020 | 23.6 | 25.0 | 21.0 | 21.4 | 20.9 |
  | 2021 | 21.0 | 19.3 | 13.9 | 12.1 | 14.2 |
  | 2022 | 11.2 | 11.9 | 10.0 | 12.7 | 12.8 |

  Stocks were ample through 2020 and H1 2021, when the over-run was already present: COAL_BIT 2020 +10.5 TWh, and
  2021 H1 +8.8 ≈ H2 +9.0 (pjm-next-3). A fuel-inventory constraint cannot bind on a full stockpile. At most it touches
  2022 (+8.1). The field also RAISES outside MISO, so arming it is a code change.
- **Card-2 verdict: no admissible coal-side lever.** Both findings are consistent with card 1: the pre-2023 over-run
  is the CC bid, not the coal rung.

## Card 3(b) — `retiree_cems_cap`: recommendation DELETE (owner rules; no model change made)

**What it is.** Each within-window retiree plant's availability is capped to its monthly CAMPD peak gross load over
nameplate, and to zero in months it did not run (`outages._plant_cems_envelope`). Armed in the PJM keeper only; no
other ISO's bundle arms it.

**What it touches on the keeper: nothing, in any year.**
- 2019–2024: the in-run call returns **0 plants**. Under `eia860_vintage_tracks_solve_year` (backcast default),
  `load_retired_within_window` returns empty for a year-matched vintage.
- **2025:** there is no `vintage_2025/`, so 2025 falls through to the canonical snapshot and the in-run call returns
  101 plants (440 fleet rows, 19.0 GW). The measurement corrects pjm-next-2, which said it was inert in every year.
- A counterfactual 2025 rebuild with the flag **off** moves **0 rows**: the COD-ramp aging already zeroes those
  retirees. So the cap is inert in 2025 as well.

**Admissibility.**
- **Rule 13 `[R-MEASURED]`: fails the forward test.** A retiring unit's monthly demonstrated peak output is a dispatch
  *outcome*, and it has no forward analogue: it cannot be produced for a forecast year. Its own comment calls it
  "the out-of-market retirement economics the merit order cannot see", which describes a proxy.
- **Rule 26 `[R-DELETE]`.** It is armed in the keeper recipe, inert only because another flag currently empties its
  input, and large if that input returns. With the vintage flag off, the canonical footprint is ~100 plants /
  19.2–19.4 GW, and paper capacity-hours removed are 96 TWh (2019) to 170 TWh (2025), 65–75 % of them COAL_BIT. That
  makes it a re-armable answer key.
- **Rule 24:** it is registered, so there is no rule-24 finding.

**Why delete, not repair.** The physical signal it approximated is now carried by measured, regenerable inputs:
- which units exist in each year: the year-matched EIA-860 vintage plus the COD ramp;
- when a surviving unit is dark: the CAMPD outage windows, membership-repaired since PJM-NEXT-2 for pre-exit
  whole-plant retirees such as Zimmer, Avon Lake and Cheswick.

A repaired form would have to become one of those, so it would be a duplicate mechanism (rule 19).

**What moves if deleted:** zero rows on the PJM keeper in every year. That is measured, not inferred.

**Deletion mechanics (for the successor, on the owner's ruling):**
- Remove the field, its `arrays.py` branch, `retiree_availability_caps` / `_plant_cems_envelope` if they have no
  other consumer, and the CLI and `backcast_config` plumbing.
- Add a rule-26 deletion-registry entry so `replay_keeper` still replays the keeper's recorded `retiree_cems_cap: true`.
- Update the matrix row.

## Owner questions

1. **Card 1 shape form:** build `pjm_offer_midcurve` "measured shape on own cost" (retiring the CC econ `econ_low` /
   `econ_high` multipliers) and screen it on the full span? Expected: it helps 2019–2022 ordering, it does not close
   CC 2024, and it adds zero DOF.
2. **Card 3(b):** delete `retiree_cems_cap` per the mechanics above?
