# FINDING — NYISO-NEXT-18 phase 0: what sets Upstate_West's price, and the missing Indian Point 3 — 2026-09-30

- **Session:** NYISO-NEXT-18 (orchestrator; zero LP in this container, rule 32 (a)).
- **Queue item:** 1 — 2021 C3a +11.1 % (the owner's block on `complete`).
- **Probes (zero LP):**
  - `scripts/probes/nyisonext18_phase0.py` → `results/phase0/nyiso/_nyisonext18_phase0.json`
  - `scripts/probes/nyisonext18_fleet_census.py` → `results/calibration/_nyisonext18_census_<year>.json`
- **Inputs:** only committed artifacts — the NEXT-16 keeper's P1 hourlies and registered run payloads, the NYISO bench (CAMPD hourly), the measured DA zonal proxy, NYISO's RT fuel mix, and the curated CENTRAL EAST flows.

## 1. The owner's question: loose link, or upstate stack priced too high?

**Answer: the link.** Upstate quantities match the market; only the price does not.

### 1.1 In CE-binding hours (measured CE ≥ 0.85 of its posted limit), the quantities match

| 2021, CE-binding hours (6,356 h) | model | measured |
|---|---|---|
| NYCA hydro, MW | 2,983 | 3,062 |
| NYCA wind, MW | 520 | 530 |
| NYCA gas + dual fuel, MW | 6,402 | 6,046 |
| NYCA nuclear, MW | 3,250 | **3,664** (see §2) |
| Upstate_West gas, CAMPD-matched plants, MW | 549 | 419 |
| Eastward transfer (NEXT-17 DESIGN §1), MW | 3,618 | 3,677 |

- The model's upstate gas runs 130 MW over CAMPD. That is small next to a 3,600 MW transfer.
- The same holds in 2022–2025: hydro, wind and nuclear are within 1–3 % of the fuel mix in CE-binding hours.

### 1.2 The prices do not match

| CE-binding hours | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| Upstate_West $, model / measured | 38.1 / 24.0 | 73.1 / 47.7 | 33.6 / 23.6 | 54.3 / 54.6 | 78.8 / 75.6 |
| Capital − Upstate spread $, model / measured | 2.1 / 19.1 | 4.7 / 48.0 | 1.8 / 17.7 | 3.7 / 21.4 | 6.1 / 35.9 |
| Hours with Upstate_West < $15, model / measured | **0 % / 29 %** | 0 % / 8 % | 0 % / 24 % | 0 % / 1 % | 0 % / 1 % |

- In 90 % of all hours the model's Capital/Upstate price ratio is 1.03–1.08, which is the loss surface alone. The model's Upstate_West price is the eastern price carried back over a link that is not binding.
- The model's Upstate_West price never falls below about $20 in any year. Measured Upstate_West sits below $15 in up to 29 % of CE-binding hours.

### 1.3 The upstate stack is exhausted at the model price

2021 fleet-only rebuild of the keeper recipe, CE-binding hours:

| Upstate_West gas | MW |
|---|---|
| available | 1,239 |
| priced below the Upstate_West model price | 657 |
| dispatched (bench-matched plants) | 711 |

- Every upstate gas MW cheaper than the Upstate_West price already runs.
- The rest (about 580 MW) sits on `peak` tranches at $57–81 and on the Oswego oil units. The LP is at a consistent optimum with the link slack.

**Reading.** The model and the market move the same volume east, and they produce it from the same upstate mix. The market's CENTRAL EAST binds at that volume and the market prices Upstate_West off its own marginal resource. The model's single UW→CH link sits at the TOTAL EAST envelope, above that volume, so it never binds. The residual is a missing CENTRAL EAST shadow price. Lowering upstate offers to close it would fit a supply-side knob to a transmission residual; rules 1 and 19 forbid that. NEXT-14, NEXT-16 and NEXT-17 have already tested the transport-cap routes (matrix cells `nyiso_total_east_cutset_ttc` K, `nyiso_fg_split` R; distribution-factor and one-link designs failed ex ante). **No new lever for this object is proposed here.**

### 1.4 The other supply-side candidates the brief named

| Candidate | Measured | Sets the 2021 Upstate_West price? |
|---|---|---|
| Upstate_West gas basis | Tenn Z4 200L $3.38 (2021 SOM); model fuel price $3.37 | No. Correct, and upstate gas is inframarginal. |
| IESO / HQ import pricing | Static rungs: HQ $10.6, IESO $12.2, PJM shoulder $16.1. Measured IESO NY-intertie in CE-binding hours: $17.3. | No. The rungs sit **below** the measured neighbour price. |
| Nuclear offer floor | $2.5, must-run | No. |
| Hydro floor | Niagara + St. Lawrence minimum 1,721 of 3,341 MW; the flexible half prices at its budget dual | Not independently: while the link is slack, the water value is the coupled system price. |

## 2. What phase 0 found instead: Indian Point 3 is missing from Jan–Apr 2021

| NYCA nuclear, MW | Jan | Feb | Mar | Apr | May–Dec |
|---|---|---|---|---|---|
| NYISO fuel mix | 4,399 | 4,370 | 4,143 | 3,933 | matches |
| keeper | 3,341 | 3,312 | 3,126 | 3,106 | within 1 % |
| gap | **−1,058** | **−1,058** | **−1,017** | **−827** | — |

- The gap is Indian Point 3 (EIA 8907; 1,039 MW; Westchester County, zone H; retired 2021-04-30). About 2.85 TWh of zero-cost downstate supply is missing.
- **Why:** the keeper arms `eia860_vintage_tracks_solve_year`. The 2021-matched EIA-860 vintage moved IP3 to its Retired sheet, so it is in neither sheet the retiree channel reads. That is the SPP-47 hole, and `mid_vintage_exit_carry` (SPP-48, default off) closes exactly that. The SPP-48 census note in this ISO's matrix row reads "INERT AT HEAD (NYISO does not arm `eia860_vintage_tracks_solve_year`)". That is no longer true, and the census counted CAMPD fossil only, so it could not see a nuclear unit.
- **Where the over-pricing sits.** Against the measured DA proxy, 2021's model is +2.11 $/MWh. **Jan–Apr carries +1.84 of it (88 %).** Jan–Apr is exactly IP3's window.
- Every other year's nuclear matches the fuel mix within about 1 % in every month.

## 3. The repair uses three existing flags, all default-off, zero DOF, cell U in this ISO

| Flag | What it does here | Needed because |
|---|---|---|
| `mid_vintage_exit_carry` (SPP-48) | Injects the plants the solve year's own vintage drops because they retired during that year | IP3 is otherwise absent |
| `fleet_zone_vintage_coords` (PJM-NEXT) | Zones a plant eGRID 2023 lacks from the active EIA-860 vintage's coordinates | Without it, IP3 lands in **Upstate_West** (the pinned default zone). That would add 1 GW of cheap supply upstate, the wrong place. |
| `retiree_vintage_status_scope` (miso-188) | Drops a retiree unit its own contemporaneous vintage marks non-OP | Without it, Dunkirk (2554; status OS since 2016) enters Jan–Apr 2022 as 200 MW of upstate coal |

### 3.1 Census: arm vs keeper, fleet-only rebuild of every year

| year | units added | available GWh added | units removed / re-zoned | demand identical |
|---|---|---|---|---|
| 2021 | IP3 → **Lower_Hudson** (2,894.7); Iola 62424 (14.6); Nassau Energy 52056 re-zoned UW → NYC | 3,208.3 incl. the re-zone | 9 (Nassau's UW rows); Hilton 58815 re-zoned UW → NYC | yes |
| 2022 | Hudson Avenue GT3/GT5 (NYC, 199.1); Nassau → NYC | 448.6 incl. the re-zone | 1 | yes |
| 2023 | Astoria Gas Turbines 55243 (NYC CT, 415.6 MW, to May 2023) | 1,304.4 | 0 | yes |
| 2024 | South Cairo GT1 2485 (Capital_Hudson) | 41.4 | 0 | yes |
| 2025 | none | 0 | 12 phantom rows (Dunkirk, Astoria GT 11, 51035), all at **0.0 GWh** available | yes |

- IP3's injected availability (2,894.7 GWh) matches the measured Jan–Apr nuclear gap (about 2,849 GWh) within 2 %.
- **Declared misalignments (rule 14):**
  - IP3 takes the upstate fleet's monthly nuclear CF (`NUCLEAR_MONTHLY_CF`, constants), not its own metered shape. The existing caveat is recorded there.
  - Nassau Energy (Garden City, Nassau County, zone K) is zoned NYC by the coordinate backstop's longitude cut, instead of Long_Island. The keeper puts it in Upstate_West. It is 55 MW, retired 2022-07.
  - The keeper's 2025 phantom rows carry zero availability, so removing them changes no 2025 dispatch.

## 4. What this does and does not claim

- **Does:** it restores a measured plant in its measured zone for its measured operating months (rule 14). It removes a plant EIA itself marks out of service. No parameter is fitted.
- **Does not:** it does not address the CENTRAL EAST object in §1. The Capital − Upstate spread in CE-binding hours is not expected to move, because IP3 is downstate.
- **Direction expected:** 2021 Jan–Apr system prices fall. The size is an LP question and is **not** a gate. The pre-registration is `docs/records/nyiso/PRECOMMIT-nyiso-next18-retiree-carry-2026-09-30.md`.
