# INTAKE SPEC — nyiso-193: the delivered-gas basis of the NYC steam fleet (Ravenswood 2500, Astoria 8906, Arthur Kill 2490) — OWNER-EXECUTABLE intake; the lane writes the spec only

**Filed:** 2026-09-05, session nyiso-193 (`backcast-calibration` lane). **Zero solve.**
**Nothing armed, changed or promoted by this document.** Keeper
`2026-09-05-nyiso-189-steam-identity` unchanged.

## 1. The object, measured (nyiso-192)

`docs/FINDING-nyiso192-frontier-adjudication-2026-09-05.md` §3 /
`results/calibration/_nyiso192_stgas_zonal_decomp.json`: the model's NYC `ST_GAS` over-run
(+4.26 / +2.24 / +0.41 TWh in 2023 / 2024 / 2025 on the keeper; +4.60 / +1.31 / −0.07 on the
Astoria-panel arm) is carried by the **zonal delivered-gas basis**, not by price formation
(the model's NYC price is at or below actual) and no longer by the heat rate (Ravenswood's
basis closed at nyiso-185). NYC steam buys at the **Transco Z6 NY hub** — 1.97 / 2.07 / 3.86
$/MMBtu — against Iroquois Z2 for LI / CH steam (3.28 / 2.77 / 5.06). On the Iroquois
reference basis the NYC committed tranches' in-merit share falls from 0.31–0.53 to 0.04–0.12,
level with LI / CH. **None of the three plants files EIA-923 Schedule-5 gas receipts** (0
rows 2018–2026; the NY filers are 2493 / 2511 / 2516 / 2517 / 56196), so the plant-specific
delivered basis is UNMEASURED in the repository. The only in-repo alternative — the KEDNY
SC-22 LDC-delivered daily index the `CT_PEAKER` leg uses (4.53 / 4.90 / 7.66) — was refused
ex ante: +$34–53/MWh drives NYC steam to 0.4–1.3 % in-merit, ~100 % floor-forced, C8 by
construction (matrix cell `nyiso_downstate_ct_gas_basis`). The truth sits between the hub and
the CT index and is a tariff fact, not a residual.

## 2. What the owner is asked to fetch (the intake)

| item | plants | source (public) | form |
|---|---|---|---|
| **Gas transportation service class and rate** for electric generation, monthly 2023–2025 | Ravenswood 2500, Astoria 8906 (Con Edison gas territory: Queens) | Con Edison PSC No. 9 — Gas, the electric-generation / interruptible transportation service classification (SC 9 / SC 20 family), rate sheets by month | $/Dth transport charge by month, plus the firm/interruptible designation of each plant's contract |
| same | Arthur Kill 2490 (National Grid NY / KEDNY territory: Staten Island) | KEDNY gas tariff, SC-22 (the class the repo already carries in `data/raw/gas-prices/nyiso_downstate_ldc_transport_monthly.csv`) — CONFIRM the plant's class; a firm-transport class would price differently | as above |
| **Commodity index each plant nominates on** | all three | plant fuel-supply disclosure where public (NYISO MMU reference-level filings are confidential; EIA-923 Schedule 5 is blank for these plants) — the owner may know the counterparty basis | hub name (Transco Z6 NY vs Iroquois Z2 vs a mix) |
| Optional corroboration | all three | NYISO State-of-the-Market Figure A-6 delivered-fuel footnotes; EIA-176 (annual, plant-level receipts by pipeline) | annual cross-check only |

## 3. The rule-14 / rule-13 test the intake must pass before it is armed

1. **Admissibility (rule 13):** a tariff rate series regenerates for a forward year (rate cases
   step; commodity is the hub) and responds to changed conditions — PASS by construction,
   the same argument the CT leg carries.
2. **Accuracy (rule 14):** the delivered price implied for each plant (hub + transport, on the
   plant's actual class) must be checked against an INDEPENDENT measured anchor before any
   solve: the statewide EIA delivered-to-electric series (`nyiso_downstate_ct_gas_basis_monthly.csv`
   `delivered_electric_usd_mmbtu`) as an upper-side sanity bound, and — if the plants' F923
   rows ever fill — the plant's own Schedule-5 receipts. A basis that lands ABOVE the CT
   index for a steam plant fails the sanity check and is not armed.
3. **Representation (rule 14 exception):** if the plants nominate on a MIX of hubs, use the
   reconciled measured mix, never a single-hub guess.

## 4. The pre-registered A/B that follows (not run here)

* Construction: a per-plant delivered basis for `ST_GAS` units at LDC-served NYC plants =
  the plant's commodity hub (daily) + its tariff transport rate (monthly), applied in the
  fuel pipeline at the same seam as `apply_nyiso_downstate_ct_gas_daily`. Scope by a RULE
  (LDC-served, no own F923 receipt), never a plant list (rule 24). One new `ScenarioConfig`
  field, default off, with its matrix row in the same PR (rule 28c).
* Phase 0 (no LP): the offer shift per plant; the committed-tranche in-merit share on the
  keeper's own prices; the floor energy the class would retain — the nyiso-192 computation
  re-run on the measured rate.
* Screen (rule 29): one year, the year of largest measured footprint from phase 0, on the
  keeper's committed bundle as control (G-DRIFT audit, no control solve).
* Bars: G-DELTA exactly the new field; B1 engagement (the NYC `ST_GAS` fuel series equals hub +
  rate); B2 prediction stated from phase 0; B3 rejected iff C2 / C3a / C3b / C8 flips; a C1
  flip goes to the owner at full magnitude. Expected direction, stated now: NYC steam
  dispatch falls toward measured; the fill lands on `CC_REGULAR` (cell G's absence) — so the
  arm is likely to reproduce the nyiso-192 C1-2024 pattern, which is why the tariff rate
  (not the CT index) must be the input.

## 5. What this spec does NOT claim

No lever is proposed; no number here is a residual fit; cell G is not re-opened (the market's
NYC steam dispatch remains out-of-market commitment whatever basis is adopted); the LI / CH
`ST_GAS` basis is untouched (nyiso-145 R, F923-grounded).
